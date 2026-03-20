from genes import Genome
from TenderHead import MinimalHeadGenome
from TenderEyes import MinimalEyeGenome


# =====================================================
# FACE PROPORTIONS
# =====================================================

EYE_WIDTH_RATIO = 0.28     # eye width relative to head width
EYE_Y_RATIO = 0.42         # eye vertical position relative to face height
EYE_SPACING_RATIO = 0.18   # eye center spacing relative to head width


# =====================================================
# FULL FACE GENERATION
# =====================================================

def generate_face_svg(face_id="0"):

    # -------------------------------------------------
    # 1. SHARED GENOME
    # -------------------------------------------------

    genome = Genome(num_genes=200)

    head = MinimalHeadGenome(genome)
    right_eye = MinimalEyeGenome(genome)

    # -------------------------------------------------
    # 2. HEAD SVG
    # -------------------------------------------------

    head_svg = head.generate_group(show_points=False)

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

    # -------------------------------------------------
    # 4. EYE PLACEMENT
    # -------------------------------------------------

    eye_width = HEAD_WIDTH * EYE_WIDTH_RATIO
    eye_scale = eye_width  # normalised eye has width 1

    eye_y = HEAD_TOP + FACE_HEIGHT * EYE_Y_RATIO

    spacing = HEAD_WIDTH * EYE_SPACING_RATIO

    left_eye_x = CENTER_X - spacing - eye_width / 2
    right_eye_x = CENTER_X + spacing - eye_width / 2

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

    # -------------------------------------------------
    # 6. COMPOSITE
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
