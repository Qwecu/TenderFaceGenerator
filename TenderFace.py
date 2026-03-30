from genes import Genome
from TenderHead import MinimalHeadGenome
from TenderEyes import MinimalEyeGenome
from TenderBrows import TenderBrows
from TenderMouth import TenderMouth
from TenderNose import TenderNose


# =====================================================
# FACE PROPORTIONS
# =====================================================

EYE_WIDTH_RATIO = 0.28   # eye width relative to head width (fixed)


def _layout_gene(genome, index, lo, hi):
    """Map gene at index linearly into [lo, hi]."""
    return lo + (genome.get_gene(index) / 255.0) * (hi - lo)


# =====================================================
# FULL FACE GENERATION
# =====================================================

def generate_face_svg(face_id="0"):

    # -------------------------------------------------
    # 1. SHARED GENOME
    # -------------------------------------------------

    genome = Genome(num_genes=200)

    head      = MinimalHeadGenome(genome)
    right_eye = MinimalEyeGenome(genome)
    brows     = TenderBrows(genome)
    mouth     = TenderMouth(genome)
    nose      = TenderNose(genome)

    # -------------------------------------------------
    # 2. HEAD SVG
    # -------------------------------------------------

    head_svg = head.generate_group()

    # -------------------------------------------------
    # 3. HEAD DIMENSIONS (same as in TenderHead.py)
    # -------------------------------------------------

    FACE_HEIGHT = 120
    HEAD_TOP = 20
    HEAD_WIDTH_RATIO = 0.65

    HEAD_BOTTOM = HEAD_TOP + FACE_HEIGHT
    HEAD_WIDTH = FACE_HEIGHT * HEAD_WIDTH_RATIO
    HALF_WIDTH = HEAD_WIDTH / 2
    CENTER_X = 65

    # Face structural anchors (mirror TenderHead.py)
    ear_top_y    = HEAD_TOP + FACE_HEIGHT * 0.30
    ear_bottom_y = HEAD_TOP + FACE_HEIGHT * 0.55
    jaw_y        = HEAD_TOP + FACE_HEIGHT * 0.75

    # -------------------------------------------------
    # 4. EYE PLACEMENT  (genes 55–56)
    # -------------------------------------------------

    eye_width = HEAD_WIDTH * EYE_WIDTH_RATIO
    eye_scale = eye_width  # normalised eye has width 1

    # Gene 64: eye vertical position — middle third of ear_top..ear_bottom span
    eye_y = _layout_gene(genome, 64,
                         ear_top_y + (ear_bottom_y - ear_top_y) * 0.30,
                         ear_top_y + (ear_bottom_y - ear_top_y) * 0.65)

    # Gene 65: eye center-to-center half-spacing — as fraction of HEAD_WIDTH
    eye_spacing_ratio = _layout_gene(genome, 65, 0.16, 0.22)
    spacing = HEAD_WIDTH * eye_spacing_ratio

    left_eye_x = CENTER_X - spacing - eye_width / 2
    right_eye_x = CENTER_X + spacing - eye_width / 2

    # Gene 69: brow lift — how far above eye_y the brow sits (gene range 0.40–0.75)
    brow_lift_raw = eye_scale * _layout_gene(genome, 69, 0.40, 0.75)

    # Gene 70: brow horizontal scale relative to eye width (0.85–1.15)
    brow_x_ratio = _layout_gene(genome, 70, 0.85, 1.15)
    brow_width   = eye_width * brow_x_ratio   # actual pixel width of brow
    brow_scale_x = brow_width                 # normalised brow x spans 0→1

    # Centre the brow on the same centre as its eye
    left_brow_x  = left_eye_x  + (eye_width - brow_width) / 2
    right_brow_x = right_eye_x + (eye_width - brow_width) / 2

    # -------------------------------------------------
    # 5. EYE SVG (normalised)
    # -------------------------------------------------

    right_eye_svg = right_eye.generate_group(
        clip_id=f"rightEyeClip_{face_id}",
        normalize=True
    )

    left_eye_svg = right_eye.generate_group(
        clip_id=f"leftEyeClip_{face_id}",
        normalize=True
    )

    brow_svg = brows.generate_group()

    # Clamp brow_y so the brow never overlaps the eye.
    # Upper eyelid peak can reach up to ~0.30 eye_scale above eye_y (conservative bound).
    # The brow's lowest point (inner end lower edge) sits at brow_y + eye_scale * hw[0].
    UPPER_EYE_EXCURSION = 0.30   # normalised units
    BROW_EYE_GAP        = 0.06   # minimum clearance in normalised units
    brow_hw0   = brows.get_half_widths()[0]
    min_lift   = eye_scale * (brow_hw0 + UPPER_EYE_EXCURSION + BROW_EYE_GAP)
    brow_lift  = max(brow_lift_raw, min_lift)
    brow_y     = eye_y - brow_lift

    # -------------------------------------------------
    # 6. NOSE PLACEMENT  (genes 58–59)
    # -------------------------------------------------

    # Nose uses a height-normalised, center-origin coordinate space.
    # The group is placed at (CENTER_X, nose_y) and scaled by nose_h.

    # Gene 68: nose height — includes shorter noses
    nose_h = FACE_HEIGHT * _layout_gene(genome, 68, 0.18, 0.27)

    # Gene 67: nose top — just below eyes, small variation
    nose_y = _layout_gene(genome, 67,
                          eye_y + FACE_HEIGHT * 0.02,
                          eye_y + FACE_HEIGHT * 0.07)

    # Constraint: nose bridge top must not be wider than the inner eye gap
    max_bridge_x_top = max(0.04, (spacing - eye_width / 2) / nose_h)

    nose_svg = nose.generate_group(max_bridge_x_top=max_bridge_x_top)

    # -------------------------------------------------
    # 7. MOUTH PLACEMENT  (gene 57)
    # -------------------------------------------------

    # Genes 71+72 averaged → bell-curve distribution, extremes are rarer
    mouth_width_norm  = (genome.get_gene(71) + genome.get_gene(72)) / 2 / 255.0
    mouth_width_ratio = 0.28 + mouth_width_norm * 0.20   # 0.28–0.48 of HEAD_WIDTH
    mouth_width = HEAD_WIDTH * mouth_width_ratio
    mouth_x     = CENTER_X - mouth_width / 2

    # Gene 66: mouth vertical — upper jaw area; clamped to never overlap nose
    mouth_y = _layout_gene(genome, 66,
                           jaw_y - FACE_HEIGHT * 0.08,
                           jaw_y + FACE_HEIGHT * 0.01)
    # Upper lip extends upward from mouth_y by up to mouth_width * 0.22 (max bow_h)
    mouth_y = max(mouth_y, nose_y + nose_h + mouth_width * 0.32 + 3)

    mouth_svg = mouth.generate_group(normalize=True)

    # -------------------------------------------------
    # 8. COMPOSITE
    # -------------------------------------------------

    return f"""
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 130 160">

    <!-- HEAD -->
    {head_svg}

    <!-- LEFT EYE -->
    <g transform="translate({left_eye_x + eye_width},{eye_y}) scale(-{eye_scale},{eye_scale})">
        {left_eye_svg}
    </g>

    <!-- RIGHT EYE -->
    <g transform="translate({right_eye_x},{eye_y}) scale({eye_scale},{eye_scale})">
        {right_eye_svg}
    </g>

    <!-- LEFT BROW -->
    <g transform="translate({left_brow_x + brow_width},{brow_y}) scale(-{brow_scale_x},{eye_scale})">
        {brow_svg}
    </g>

    <!-- RIGHT BROW -->
    <g transform="translate({right_brow_x},{brow_y}) scale({brow_scale_x},{eye_scale})">
        {brow_svg}
    </g>

    <!-- NOSE -->
    <g transform="translate({CENTER_X},{nose_y}) scale({nose_h},{nose_h})">
        {nose_svg}
    </g>

    <!-- MOUTH -->
    <g transform="translate({mouth_x},{mouth_y}) scale({mouth_width},{mouth_width})">
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
