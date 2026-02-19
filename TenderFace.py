from genes import Genome
from TenderHead import MinimalHeadGenome
from TenderEyes import MinimalEyeGenome


# =====================================================
# KASVON MITOITUSSUHTEET
# =====================================================

EYE_WIDTH_RATIO = 0.28     # silmän leveys suhteessa pään leveyteen
EYE_Y_RATIO = 0.42         # silmien pystysijainti suhteessa pään korkeuteen
EYE_SPACING_RATIO = 0.18   # silmien keskipisteiden väli suhteessa pään leveyteen


# =====================================================
# KOKO KASVON GENEROINTI
# =====================================================

def generate_face_svg():

    # -------------------------------------------------
    # 1. YHTEINEN GENOMI
    # -------------------------------------------------

    genome = Genome(num_genes=200)

    head = MinimalHeadGenome(genome)
    right_eye = MinimalEyeGenome(genome)

    # -------------------------------------------------
    # 2. PÄÄN SVG
    # -------------------------------------------------

    head_svg = head.generate_group(show_points=False)

    # -------------------------------------------------
    # 3. PÄÄN MITAT (samat kuin TenderHead.py:ssä)
    # -------------------------------------------------

    FACE_HEIGHT = 120
    HEAD_TOP = 20
    HEAD_WIDTH_RATIO = 0.65

    HEAD_BOTTOM = HEAD_TOP + FACE_HEIGHT
    HEAD_WIDTH = FACE_HEIGHT * HEAD_WIDTH_RATIO
    HALF_WIDTH = HEAD_WIDTH / 2
    CENTER_X = 65

    # -------------------------------------------------
    # 4. SILMIEN SIJOITTELU
    # -------------------------------------------------

    eye_width = HEAD_WIDTH * EYE_WIDTH_RATIO
    eye_scale = eye_width  # koska normalisoitu silmä = leveys 1

    eye_y = HEAD_TOP + FACE_HEIGHT * EYE_Y_RATIO

    spacing = HEAD_WIDTH * EYE_SPACING_RATIO

    left_eye_x = CENTER_X - spacing - eye_width / 2
    right_eye_x = CENTER_X + spacing - eye_width / 2

    # -------------------------------------------------
    # 5. SILMIEN SVG (normalisoitu)
    # -------------------------------------------------


    right_eye_svg = right_eye.generate_group(
        clip_id="rightEyeClip",
        normalize=True
    )

    # -------------------------------------------------
    # 6. KOOSTE
    # -------------------------------------------------

    return f"""
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 130 160">

    <!-- PÄÄ -->
    {head_svg}

    <!-- VASEN SILMÄ -->
    <g transform="translate({left_eye_x + eye_width},{eye_y}) scale(-{eye_scale},{eye_scale})">
        {right_eye_svg}
    </g>

    <!-- OIKEA SILMÄ -->
    <g transform="translate({right_eye_x},{eye_y}) scale({eye_scale},{eye_scale})">
        {right_eye_svg}
    </g>

</svg>
"""


# =====================================================
# AJETAAN
# =====================================================

if __name__ == "__main__":

    svg_output = generate_face_svg()

    with open("tender_face.svg", "w") as f:
        f.write(svg_output)

    print("SVG created: tender_face.svg")
