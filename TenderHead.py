from genes import Genome

# =====================================================
# GLOBAL DIMENSIONS (NOT GENETIC YET)
# =====================================================

FACE_HEIGHT = 120
HEAD_TOP = 20

HEAD_WIDTH_RATIO = 0.65


# =====================================================
# MINIMAL HEAD GENOME
# =====================================================

class MinimalHeadGenome:

    def __init__(self, genome=None):
        # If a genome is provided → use it
        # Otherwise create a new one (preserves old behaviour)
        self.genome = genome if genome is not None else Genome(num_genes=100)


    # =====================================================
    # SKIN COLOR
    # =====================================================

    def get_skin_color(self):
        """
        Fetches skin color via the Genome class.
        Assumes genes.py exposes get_skin_color() returning (r, g, b).
        """
        return self.genome.get_skin_color()

    # =====================================================
    # GROUP GENERATION
    # =====================================================

    def generate_group(self):

        skin_color = self.get_skin_color()

        CENTER_X = 65
        HEAD_BOTTOM = HEAD_TOP + FACE_HEIGHT

        HEAD_WIDTH = FACE_HEIGHT * HEAD_WIDTH_RATIO
        HALF_WIDTH = HEAD_WIDTH / 2

        # --- ANCHOR POINTS ---

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
        # ABSOLUTE PATH (FULLY SYMMETRIC)
        # =====================================================

        d = f"""
        M {top_x} {top_y}

        C {top_x + HALF_WIDTH*0.5} {top_y}
        {ear_right_x} {ear_top_y - 40}
        {ear_right_x} {ear_top_y}

        L {ear_right_x} {ear_bottom_y}

        L {jaw_right_x} {jaw_y}

        L {chin_side_right_x} {chin_side_y}

        L {chin_x} {chin_y}

        L {chin_side_left_x} {chin_side_y}

        L {jaw_left_x} {jaw_y}

        L {ear_left_x} {ear_bottom_y}

        L {ear_left_x} {ear_top_y}

        C {ear_left_x} {ear_top_y - 40}
        {top_x - HALF_WIDTH*0.5} {top_y}
        {top_x} {top_y}
        """



        # Bezier control points for the top curves
        ctrl_top_right_x = top_x + HALF_WIDTH * 0.5
        ctrl_top_right_y = top_y
        ctrl_ear_right_x = ear_right_x
        ctrl_ear_right_y = ear_top_y - 40

        ctrl_ear_left_x  = ear_left_x
        ctrl_ear_left_y  = ear_top_y - 40
        ctrl_top_left_x  = top_x - HALF_WIDTH * 0.5
        ctrl_top_left_y  = top_y

        def pt(cx, cy, color="red"):
            return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="2" fill="{color}"/>'

        def ctrl_line(x1, y1, x2, y2):
            return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="red" stroke-width="0.4" stroke-dasharray="1.5 1"/>'

        points_svg = f"""
<g class="ctrl-points" style="display:none">
  {ctrl_line(top_x, top_y, ctrl_top_right_x, ctrl_top_right_y)}
  {ctrl_line(ear_right_x, ear_top_y, ctrl_ear_right_x, ctrl_ear_right_y)}
  {ctrl_line(top_x, top_y, ctrl_top_left_x, ctrl_top_left_y)}
  {ctrl_line(ear_left_x, ear_top_y, ctrl_ear_left_x, ctrl_ear_left_y)}
  {pt(top_x, top_y)}
  {pt(ear_right_x, ear_top_y)}
  {pt(ear_right_x, ear_bottom_y)}
  {pt(jaw_right_x, jaw_y)}
  {pt(chin_side_right_x, chin_side_y)}
  {pt(chin_x, chin_y)}
  {pt(chin_side_left_x, chin_side_y)}
  {pt(jaw_left_x, jaw_y)}
  {pt(ear_left_x, ear_bottom_y)}
  {pt(ear_left_x, ear_top_y)}
  {pt(ctrl_top_right_x, ctrl_top_right_y, "blue")}
  {pt(ctrl_ear_right_x, ctrl_ear_right_y, "blue")}
  {pt(ctrl_top_left_x, ctrl_top_left_y, "blue")}
  {pt(ctrl_ear_left_x, ctrl_ear_left_y, "blue")}
</g>"""

        return f"""
<path d="{d}"
      fill="rgb{skin_color}"
      stroke="black"
      stroke-width="0.5"/>
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
