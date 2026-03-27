from genes import Genome
from TenderHead import MinimalHeadGenome
from TenderEyes import MinimalEyeGenome
from TenderBrows import TenderBrows
from TenderMouth import TenderMouth
from TenderNose import TenderNose


# =====================================================
# FACE PROPORTIONS
# =====================================================

EYE_WIDTH_RATIO   = 0.28   # eye width relative to head width (fixed)
MOUTH_WIDTH_RATIO = 0.38   # mouth width relative to head width (fixed)


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

    # Gene 55: eye vertical position — middle third of ear_top..ear_bottom span
    eye_y = _layout_gene(genome, 55,
                         ear_top_y + (ear_bottom_y - ear_top_y) * 0.30,
                         ear_top_y + (ear_bottom_y - ear_top_y) * 0.65)

    # Gene 56: eye center-to-center half-spacing — as fraction of HEAD_WIDTH
    eye_spacing_ratio = _layout_gene(genome, 56, 0.16, 0.22)
    spacing = HEAD_WIDTH * eye_spacing_ratio

    left_eye_x = CENTER_X - spacing - eye_width / 2
    right_eye_x = CENTER_X + spacing - eye_width / 2

    # Gene 64: brow lift — how far above eye_y the brow sits (35–55 % of eye_scale)
    brow_lift = eye_scale * _layout_gene(genome, 64, 0.35, 0.55)
    brow_y = eye_y - brow_lift

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

    # -------------------------------------------------
    # 6. NOSE PLACEMENT  (genes 58–59)
    # -------------------------------------------------

    # Nose uses a height-normalised, center-origin coordinate space.
    # The group is placed at (CENTER_X, nose_y) and scaled by nose_h.

    # Gene 59: nose height — includes shorter noses
    nose_h = FACE_HEIGHT * _layout_gene(genome, 59, 0.18, 0.27)

    # Gene 58: nose top — just below eyes, small variation
    nose_y = _layout_gene(genome, 58,
                          eye_y + FACE_HEIGHT * 0.02,
                          eye_y + FACE_HEIGHT * 0.07)

    # Constraint: nose bridge top must not be wider than the inner eye gap
    max_bridge_x_top = max(0.04, (spacing - eye_width / 2) / nose_h)

    nose_svg = nose.generate_group(max_bridge_x_top=max_bridge_x_top)

    # -------------------------------------------------
    # 7. MOUTH PLACEMENT  (gene 57)
    # -------------------------------------------------

    mouth_width = HEAD_WIDTH * MOUTH_WIDTH_RATIO
    mouth_x     = CENTER_X - mouth_width / 2

    # Gene 57: mouth vertical — upper jaw area; clamped to never overlap nose
    mouth_y = _layout_gene(genome, 57,
                           jaw_y - FACE_HEIGHT * 0.04,
                           jaw_y + FACE_HEIGHT * 0.06)
    # Upper lip extends upward from mouth_y by up to mouth_width * 0.22 (max bow_h)
    mouth_y = max(mouth_y, nose_y + nose_h + mouth_width * 0.22 + 2)

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
    <g transform="translate({left_eye_x + eye_width},{brow_y}) scale(-{eye_scale},{eye_scale})">
        {brow_svg}
    </g>

    <!-- RIGHT BROW -->
    <g transform="translate({right_eye_x},{brow_y}) scale({eye_scale},{eye_scale})">
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
