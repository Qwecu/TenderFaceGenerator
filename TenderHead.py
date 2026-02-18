from genes import Genome

# =====================================================
# GLOBAALIT MITAT (EI GENEETTISET VIELÄ)
# =====================================================

FACE_HEIGHT = 120
HEAD_TOP = 20

HEAD_WIDTH_RATIO = 0.65


# =====================================================
# MINIMAALINEN PÄÄGENOMI
# =====================================================

class MinimalHeadGenome:

    def __init__(self):
        # Luodaan genomi samalla tavalla kuin silmässä
        self.genome = Genome(num_genes=100)

    # =====================================================
    # IHONVÄRI
    # =====================================================

    def get_skin_color(self):
        """
        Haetaan ihonväri Genome-luokan kautta.
        Oletetaan että genes.py sisältää:
            get_skin_color()
        joka palauttaa (r, g, b)
        """
        return self.genome.get_skin_color()

    # =====================================================
    # GROUP GENEROINTI
    # =====================================================

    def generate_group(self, show_points=False):

        skin_color = self.get_skin_color()

        CENTER_X = 65
        HEAD_BOTTOM = HEAD_TOP + FACE_HEIGHT

        HEAD_WIDTH = FACE_HEIGHT * HEAD_WIDTH_RATIO
        HALF_WIDTH = HEAD_WIDTH / 2

        # --- TUKIPISTEET ---

        top_x = CENTER_X
        top_y = HEAD_TOP

        chin_x = CENTER_X
        chin_y = HEAD_BOTTOM

        ear_top_y = HEAD_TOP + FACE_HEIGHT * 0.3
        ear_bottom_y = HEAD_TOP + FACE_HEIGHT * 0.55

        ear_left_x  = CENTER_X - HALF_WIDTH
        ear_right_x = CENTER_X + HALF_WIDTH

        jaw_y = HEAD_TOP + FACE_HEIGHT * 0.75
        jaw_offset = HALF_WIDTH * 0.85
        jaw_left_x  = CENTER_X - jaw_offset
        jaw_right_x = CENTER_X + jaw_offset

        chin_side_y = HEAD_TOP + FACE_HEIGHT * 0.88
        chin_side_offset = HALF_WIDTH * 0.45
        chin_side_left_x  = CENTER_X - chin_side_offset
        chin_side_right_x = CENTER_X + chin_side_offset


        # =====================================================
        # SULKEVAN KAAREN RELATIIVISET DELTAT (SYMMETRISET)
        # =====================================================

        # Lähtöpiste sulkevassa kaaressa:
        # (ear_left_x, ear_top_y)

        # Absoluuttisesti symmetriset kontrollipisteet:
        # CP1_left_abs = (ear_left_x, ear_top_y - 40)
        # CP2_left_abs = (CENTER_X - HALF_WIDTH*0.5, HEAD_TOP)
        # End_abs      = (top_x, top_y)

        close_c1_dx = 0
        close_c1_dy = -40

        close_c2_dx = (CENTER_X - HALF_WIDTH * 0.5) - ear_left_x
        close_c2_dy = HEAD_TOP - ear_top_y

        close_end_dx = top_x - ear_left_x
        close_end_dy = top_y - ear_top_y


        # =====================================================
        # RELATIIVINEN PATH (TÄYSIN SYMMETRINEN)
        # =====================================================

        d = f"""
        m {top_x} {top_y}

        c {HALF_WIDTH*0.5} 0
        {HALF_WIDTH} {ear_top_y - 40 - top_y}
        {HALF_WIDTH} {ear_top_y - top_y}

        l 0 {ear_bottom_y - ear_top_y}

        l {jaw_right_x - ear_right_x} {jaw_y - ear_bottom_y}

        l {chin_side_right_x - jaw_right_x} {chin_side_y - jaw_y}

        l {chin_x - chin_side_right_x} {chin_y - chin_side_y}

        l {chin_side_left_x - chin_x} {chin_side_y - chin_y}

        l {jaw_left_x - chin_side_left_x} {jaw_y - chin_side_y}

        l {ear_left_x - jaw_left_x} {ear_bottom_y - jaw_y}

        l 0 {ear_top_y - ear_bottom_y}

        c {close_c1_dx} {close_c1_dy}
        {close_c2_dx} {close_c2_dy}
        {close_end_dx} {close_end_dy}
        """


        # --- TUKIPISTEET OPTIONAALISESTI ---

        points_svg = ""
        if show_points:
            points_svg = f"""
<circle cx="{top_x}" cy="{top_y}" r="3" fill="red"/>
<circle cx="{chin_x}" cy="{chin_y}" r="3" fill="red"/>
"""

        return f"""
<path d="{d}"
      fill="rgb{skin_color}"
      stroke="black"
      stroke-width="1.5"/>
{points_svg}
"""

def generate_head_grid():

    COLS = 4
    ROWS = 4

    CELL_WIDTH = 130
    CELL_HEIGHT = 160

    total_width = COLS * CELL_WIDTH
    total_height = ROWS * CELL_HEIGHT

    svg_content = ""

    for row in range(ROWS):
        for col in range(COLS):

            head = MinimalHeadGenome()

            tx = col * CELL_WIDTH
            ty = row * CELL_HEIGHT

            svg_content += f"""
<g transform="translate({tx},{ty})">
{head.generate_group(show_points=False)}
</g>
"""

    return f"""
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {total_width} {total_height}">
{svg_content}
</svg>
"""

if __name__ == "__main__":

    svg_output = generate_head_grid()

    with open("genetic_head_grid.svg", "w") as f:
        f.write(svg_output)

    print("SVG created: genetic_head_grid.svg")
