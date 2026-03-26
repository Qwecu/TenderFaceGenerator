from genes import Genome
from TenderHead import MinimalHeadGenome
from TenderEyes import MinimalEyeGenome
from TenderMouth import TenderMouth
from TenderNose import TenderNose


# =====================================================
# FACE PROPORTIONS
# =====================================================

EYE_WIDTH_RATIO = 0.28     # eye width relative to head width
EYE_Y_RATIO = 0.42         # eye vertical position relative to face height
EYE_SPACING_RATIO = 0.18   # eye center spacing relative to head width

MOUTH_WIDTH_RATIO = 0.38   # mouth width relative to head width
MOUTH_Y_RATIO = 0.76       # mouth vertical position relative to face height

NOSE_HEIGHT_RATIO = 0.27   # nose height relative to face height
NOSE_Y_RATIO = 0.43        # nose top (bridge) relative to face height


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
    # 6. NOSE PLACEMENT
    # -------------------------------------------------

    # Nose uses a height-normalised, center-origin coordinate space.
    # The group is placed at (CENTER_X, nose_top_y) and scaled by nose_h.
    nose_h = FACE_HEIGHT * NOSE_HEIGHT_RATIO
    nose_y = HEAD_TOP + FACE_HEIGHT * NOSE_Y_RATIO

    nose_svg = nose.generate_group()

    # -------------------------------------------------
    # 7. MOUTH PLACEMENT
    # -------------------------------------------------

    mouth_width = HEAD_WIDTH * MOUTH_WIDTH_RATIO
    mouth_x     = CENTER_X - mouth_width / 2
    mouth_y     = HEAD_TOP + FACE_HEIGHT * MOUTH_Y_RATIO

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
