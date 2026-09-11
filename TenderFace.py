from genes import Genome
from TenderHead import (MinimalHeadGenome, CENTER_X, VIEW_W, VIEW_H)
from TenderEyes import MinimalEyeGenome
from TenderBrows import TenderBrows
from TenderMouth import TenderMouth
from TenderNose import TenderNose


# =====================================================
# FACE LAYOUT GENES  (indices 160–179)
# =====================================================
#  0 (160): eye_w_ratio      eye width / head width            (0.205–0.265)
#  1 (161): eye_gap_ratio    gap between eyes / eye width      (0.72–1.28)
#  2 (162): mouth_w_ratio    mouth width / head width          (0.30–0.46)
#  3 (163): brow_w_ratio     brow width / eye width            (0.90–1.20)
#  4 (164): brow_line        band top, frac of head height     (0.37–0.43)
#  5 (165): chin_gap         band bottom above chin, frac      (0.09–0.14)
#  6 (166): w_gap_brow_eye   vertical slack weight
#  7 (167): w_gap_eye_nose   vertical slack weight
#  8 (168): w_nose           vertical slack weight
#  9 (169): w_gap_nose_mouth vertical slack weight
# 10 (170): w_gap_mouth_chin vertical slack weight
# 11–19 (171–179): spare

LAYOUT_BASE = 160

# ---- Layout invariants -------------------------------------------------
# Every face satisfies these regardless of genes:
#   * features stack brow → eye → nose → mouth with a positive gap between
#     each, so nothing ever overlaps
#   * the nose is guaranteed at least MIN_NOSE_FRAC of the feature band, so
#     it can never be squeezed into a speck by its neighbours
#   * every feature sits inside the real head silhouette, sampled from the
#     actual outline bezier rather than estimated from keypoints
#   * if the band genuinely cannot hold the features, ALL of them shrink by
#     one shared factor — the face gets smaller features, never a collapsed
#     single part

MIN_GAP_PX    = 1.5    # absolute floor for each inter-feature gap
MIN_NOSE_FRAC = 0.20   # nose floor, as a fraction of the feature band
MIN_NOSE_ABS  = 0.11   # nose floor, as a fraction of face height
# Two floors, because either alone leaves a hole: the band-relative one lets a
# short band shrink the nose to a speck, and the height-relative one alone
# would not scale with a roomy band.

# Fraction of the local half-width a feature may occupy before it is pulled in
FIT_EYE   = 0.94
FIT_BROW  = 0.96
FIT_MOUTH = 0.86
FIT_NOSE  = 0.62


def _lg(genome, index, lo, hi):
    """Map gene at `index` linearly into [lo, hi]."""
    return lo + (genome.get_gene(index) / 255.0) * (hi - lo)


def _layout_gene(genome, offset, lo, hi):
    """Map layout gene at LAYOUT_BASE+offset linearly into [lo, hi]."""
    return _lg(genome, LAYOUT_BASE + offset, lo, hi)


# =====================================================
# VERTICAL SOLVER
# =====================================================

def _stack_vertically(band_top, band, ext, eye_w, mouth_w, weights, nose_floor):
    """
    Place brow / eye / nose / mouth down the feature band.

    brow, eye and mouth have intrinsic heights (their shapes are tied to their
    widths).  The nose and the four gaps share whatever is left, split by
    gene-driven `weights` on top of hard minimums.

    Returns (positions dict, scale) where `scale` is the shared shrink factor
    applied to the width-driven features (1.0 when everything fitted).
    """
    brow_top_n, brow_bot_n = ext['brow']
    eye_top_n,  eye_bot_n  = ext['eye']
    mouth_top_n, mouth_bot_n = ext['mouth']

    brow_h  = (brow_bot_n - brow_top_n) * eye_w
    eye_h   = (eye_bot_n - eye_top_n) * eye_w
    mouth_h = (mouth_bot_n - mouth_top_n) * mouth_w

    fixed    = brow_h + eye_h + mouth_h
    reserved = 4 * MIN_GAP_PX + nose_floor

    # If the intrinsic features cannot leave room for the nose and the gaps,
    # shrink them all by one shared factor.  A uniform shrink still reads as a
    # natural face; collapsing one feature does not.
    scale = 1.0
    max_fixed = band - reserved
    if fixed > max_fixed and fixed > 0:
        scale = max_fixed / fixed
        eye_w   *= scale
        mouth_w *= scale
        brow_h  *= scale
        eye_h   *= scale
        mouth_h *= scale
        fixed = max_fixed

    remainder = max(0.0, band - fixed - reserved)
    total_w   = sum(weights)
    share     = [remainder * w / total_w for w in weights]

    gap_be = MIN_GAP_PX + share[0]
    gap_en = MIN_GAP_PX + share[1]
    nose_h = nose_floor + share[2]
    gap_nm = MIN_GAP_PX + share[3]
    gap_mc = MIN_GAP_PX + share[4]

    # Walk down the band.  Each feature's reference line is offset so that its
    # topmost drawn pixel lands exactly on the running cursor.
    y = band_top
    brow_y = y - brow_top_n * eye_w
    y += brow_h + gap_be

    eye_y = y - eye_top_n * eye_w
    y += eye_h + gap_en

    nose_y = y
    y += nose_h + gap_nm

    mouth_y = y - mouth_top_n * mouth_w
    y += mouth_h

    return {
        'brow_y': brow_y, 'eye_y': eye_y, 'nose_y': nose_y, 'mouth_y': mouth_y,
        'nose_h': nose_h, 'eye_w': eye_w, 'mouth_w': mouth_w,
        'brow_h': brow_h, 'eye_h': eye_h, 'mouth_h': mouth_h,
        'gap_mouth_chin': gap_mc,
        'eye_top_y':   eye_y + eye_top_n * eye_w,
        'eye_bot_y':   eye_y + eye_bot_n * eye_w,
        'brow_top_y':  brow_y + brow_top_n * eye_w,
        'mouth_bot_y': mouth_y + mouth_bot_n * mouth_w,
    }, scale


# =====================================================
# FULL LAYOUT
# =====================================================

def compute_layout(genome):
    """
    Resolve every placement decision for one genome.

    Split out from rendering so the layout can be measured and tested without
    parsing SVG.
    """
    head  = MinimalHeadGenome(genome)
    eye   = MinimalEyeGenome(genome)
    brows = TenderBrows(genome)
    mouth = TenderMouth(genome)
    nose  = TenderNose(genome)

    hg          = head.geometry()
    face_height = hg['face_height']
    head_top    = hg['head_top']
    chin_y      = hg['chin_y']
    head_w      = hg['max_hw'] * 2

    ext = {
        'brow':  brows.vertical_extent(),
        'eye':   eye.vertical_extent(),
        'mouth': mouth.vertical_extent(),
    }

    # ---- Feature band ----
    # The band is measured against the ACTUAL crown-to-chin height, not the
    # nominal face height.  Anchored to face_height instead, the chin's own
    # variation swings the band by a further 12% and can starve the features.
    #
    # The fractions place the brow and the mouth near the standard head canon
    # (brow ~0.42 of head height, mouth centre ~0.82); the band also stops
    # short of the chin tip, where the outline has tapered too far in for a
    # mouth to sit without being crushed.
    head_h      = chin_y - head_top
    band_top    = head_top + head_h * _layout_gene(genome, 4, 0.37, 0.43)
    band_bottom = chin_y - head_h * _layout_gene(genome, 5, 0.09, 0.14)
    band        = band_bottom - band_top
    nose_floor  = max(band * MIN_NOSE_FRAC, face_height * MIN_NOSE_ABS)

    # ---- Widths, sized from head width ----
    eye_w   = head_w * _layout_gene(genome, 0, 0.205, 0.265)
    eye_gap = eye_w * _layout_gene(genome, 1, 0.72, 1.28)
    mouth_w = head_w * _layout_gene(genome, 2, 0.30, 0.46)
    brow_r  = _layout_gene(genome, 3, 0.90, 1.20)

    weights = [
        _layout_gene(genome,  6, 0.06, 0.16),   # gap brow → eye
        _layout_gene(genome,  7, 0.02, 0.08),   # gap eye → nose
        _layout_gene(genome,  8, 0.40, 0.58),   # nose
        _layout_gene(genome,  9, 0.07, 0.19),   # gap nose → mouth
        _layout_gene(genome, 10, 0.10, 0.24),   # gap mouth → chin
    ]

    # ---- Two passes: solve, fit widths to the real outline, solve again ----
    # Fitting only ever shrinks, so the second pass always converges.
    pos, scale = _stack_vertically(band_top, band, ext, eye_w, mouth_w, weights, nose_floor)

    eye_w   = pos['eye_w']
    mouth_w = pos['mouth_w']
    eye_gap = min(eye_gap, eye_w * 1.28) * scale

    # Eyes: the outer corner must sit inside the outline across the eye's
    # whole vertical span (the face narrows towards the top).
    hw_eye = min(head.half_width_at(pos['eye_top_y']),
                 head.half_width_at(pos['eye_bot_y']))
    outer = eye_gap / 2 + eye_w
    if outer > hw_eye * FIT_EYE:
        budget = hw_eye * FIT_EYE
        # Close the eyes towards the nose first, then narrow them.
        eye_gap = max(eye_w * 0.55, 2 * (budget - eye_w))
        if eye_gap / 2 + eye_w > budget:
            eye_w = max(1.0, budget - eye_gap / 2)

    # Brow: centred on the eye but sitting higher, where the face is narrower.
    brow_w = eye_w * brow_r
    hw_brow = head.half_width_at(pos['brow_top_y'])
    brow_outer = eye_gap / 2 + eye_w / 2 + brow_w / 2
    if brow_outer > hw_brow * FIT_BROW:
        brow_w = max(1.0, 2 * (hw_brow * FIT_BROW - eye_gap / 2 - eye_w / 2))

    # Mouth: clamp to the outline at its widest drawn point.
    hw_mouth = head.half_width_at(pos['mouth_bot_y'])
    mouth_w = min(mouth_w, hw_mouth * 2 * FIT_MOUTH)

    pos, _ = _stack_vertically(band_top, band, ext, eye_w, mouth_w, weights, nose_floor)
    eye_w, mouth_w = pos['eye_w'], pos['mouth_w']

    # ---- Nose: clamp its width, which for a uniformly scaled nose means
    # clamping its height.  Freed vertical space just widens the gap below.
    ala_x  = nose.get_control_points()['ala_x']
    nose_h = pos['nose_h']
    hw_nose = head.half_width_at(pos['nose_y'] + nose_h)
    if nose_h * ala_x > hw_nose * FIT_NOSE:
        nose_h = max(4.0, hw_nose * FIT_NOSE / ala_x)

    # The bridge must not be wider than the gap between the eyes.
    max_bridge_x_top = max(0.04, (eye_gap / 2) / max(nose_h, 1e-6))

    left_eye_x  = CENTER_X - eye_gap / 2 - eye_w
    right_eye_x = CENTER_X + eye_gap / 2

    return {
        'head': head, 'eye': eye, 'brows': brows, 'mouth': mouth, 'nose': nose,
        'eye_w': eye_w, 'eye_gap': eye_gap, 'brow_w': brow_w,
        'mouth_w': mouth_w, 'nose_h': nose_h,
        'left_eye_x': left_eye_x, 'right_eye_x': right_eye_x,
        'left_brow_x':  left_eye_x + (eye_w - brow_w) / 2,
        'right_brow_x': right_eye_x + (eye_w - brow_w) / 2,
        'mouth_x': CENTER_X - mouth_w / 2,
        'eye_y': pos['eye_y'], 'brow_y': pos['brow_y'],
        'nose_y': pos['nose_y'], 'mouth_y': pos['mouth_y'],
        'max_bridge_x_top': max_bridge_x_top,
        'band_top': band_top, 'band_bottom': band_bottom,
        'chin_y': chin_y, 'face_height': face_height, 'head_top': head_top,
        # measured boundaries, for validation
        'eye_top_y': pos['eye_top_y'], 'eye_bot_y': pos['eye_bot_y'],
        'brow_top_y': pos['brow_top_y'], 'mouth_bot_y': pos['mouth_bot_y'],
        'brow_bot_y': pos['brow_top_y'] + pos['brow_h'],
        'nose_bot_y': pos['nose_y'] + nose_h,
        'mouth_top_y': pos['mouth_y'] + ext['mouth'][0] * mouth_w,
    }


# =====================================================
# FULL FACE GENERATION
# =====================================================

def generate_face_svg(face_id="0", genome=None):

    if genome is None:
        genome = Genome(num_genes=200)

    L = compute_layout(genome)

    head_svg  = L['head'].generate_group()
    brow_svg  = L['brows'].generate_group()
    mouth_svg = L['mouth'].generate_group(normalize=True)
    nose_svg  = L['nose'].generate_group(max_bridge_x_top=L['max_bridge_x_top'])

    right_eye_svg = L['eye'].generate_group(clip_id=f"rightEyeClip_{face_id}",
                                            normalize=True)
    left_eye_svg  = L['eye'].generate_group(clip_id=f"leftEyeClip_{face_id}",
                                            normalize=True)

    eye_w   = L['eye_w']
    brow_w  = L['brow_w']
    mouth_w = L['mouth_w']
    nose_h  = L['nose_h']

    return f"""
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {VIEW_W} {VIEW_H}">

    <!-- HEAD -->
    {head_svg}

    <!-- LEFT EYE -->
    <g transform="translate({L['left_eye_x'] + eye_w},{L['eye_y']}) scale(-{eye_w},{eye_w})">
        {left_eye_svg}
    </g>

    <!-- RIGHT EYE -->
    <g transform="translate({L['right_eye_x']},{L['eye_y']}) scale({eye_w},{eye_w})">
        {right_eye_svg}
    </g>

    <!-- LEFT BROW -->
    <g transform="translate({L['left_brow_x'] + brow_w},{L['brow_y']}) scale(-{brow_w},{eye_w})">
        {brow_svg}
    </g>

    <!-- RIGHT BROW -->
    <g transform="translate({L['right_brow_x']},{L['brow_y']}) scale({brow_w},{eye_w})">
        {brow_svg}
    </g>

    <!-- NOSE -->
    <g transform="translate({CENTER_X},{L['nose_y']}) scale({nose_h},{nose_h})">
        {nose_svg}
    </g>

    <!-- MOUTH -->
    <g transform="translate({L['mouth_x']},{L['mouth_y']}) scale({mouth_w},{mouth_w})">
        {mouth_svg}
    </g>

</svg>
"""


# =====================================================
# ENTRY POINT
# =====================================================

if __name__ == "__main__":

    svg_output = generate_face_svg()

    with open("tender_face.svg", "w") as f:
        f.write(svg_output)

    print("SVG created: tender_face.svg")
