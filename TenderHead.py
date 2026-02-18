import os

# =====================================================
# ASETTELU
# =====================================================

COLS = 4
ROWS = 4

CELL_WIDTH = 130
CELL_HEIGHT = 160

SVG_WIDTH = COLS * CELL_WIDTH
SVG_HEIGHT = ROWS * CELL_HEIGHT


# =====================================================
# YHDEN PÄÄN PIIRTO
# =====================================================

def generate_head_group(offset_x, offset_y, show_points):

    # -------------------------------------------------
    # PERUSMITAT
    # -------------------------------------------------

    FACE_HEIGHT = 120
    HEAD_TOP = 20
    HEAD_BOTTOM = HEAD_TOP + FACE_HEIGHT

    CENTER_X = CELL_WIDTH / 2

    HEAD_WIDTH = FACE_HEIGHT * 0.65
    HALF_WIDTH = HEAD_WIDTH / 2

    # -------------------------------------------------
    # TUKIPISTEET
    # -------------------------------------------------

    top_x = CENTER_X
    top_y = HEAD_TOP

    chin_x = CENTER_X
    chin_y = HEAD_BOTTOM

    ear_top_y = HEAD_TOP + FACE_HEIGHT * 0.3
    ear_bottom_y = HEAD_TOP + FACE_HEIGHT * 0.55

    ear_left_x = CENTER_X - HALF_WIDTH
    ear_right_x = CENTER_X + HALF_WIDTH

    jaw_y = HEAD_TOP + FACE_HEIGHT * 0.75
    jaw_offset = HALF_WIDTH * 0.85
    jaw_left_x = CENTER_X - jaw_offset
    jaw_right_x = CENTER_X + jaw_offset

    chin_side_y = HEAD_TOP + FACE_HEIGHT * 0.88
    chin_side_offset = HALF_WIDTH * 0.45
    chin_side_left_x = CENTER_X - chin_side_offset
    chin_side_right_x = CENTER_X + chin_side_offset

    # -------------------------------------------------
    # RELATIIVISET DELTAT (OIKEA)
    # -------------------------------------------------

    m_x = top_x
    m_y = top_y

    c1_dx = HALF_WIDTH * 0.5
    c1_dy = 0

    c2_dx = ear_right_x - top_x
    c2_dy = (ear_top_y - 40) - top_y

    end1_dx = ear_right_x - top_x
    end1_dy = ear_top_y - top_y

    l1_dx = 0
    l1_dy = ear_bottom_y - ear_top_y

    l2_dx = jaw_right_x - ear_right_x
    l2_dy = jaw_y - ear_bottom_y

    l3_dx = chin_side_right_x - jaw_right_x
    l3_dy = chin_side_y - jaw_y

    l4_dx = chin_x - chin_side_right_x
    l4_dy = chin_y - chin_side_y

    # -------------------------------------------------
    # RELATIIVISET DELTAT (VASEN)
    # -------------------------------------------------

    c1_dx_l = -HALF_WIDTH * 0.5
    c1_dy_l = 0

    c2_dx_l = ear_left_x - top_x
    c2_dy_l = (ear_top_y - 40) - top_y

    end1_dx_l = ear_left_x - top_x
    end1_dy_l = ear_top_y - top_y

    l2_dx_l = jaw_left_x - ear_left_x
    l3_dx_l = chin_side_left_x - jaw_left_x
    l4_dx_l = chin_x - chin_side_left_x

    # -------------------------------------------------
    # TUKIPISTEET SVG (OPTIONAALINEN)
    # -------------------------------------------------

    points_svg = ""
    if show_points:
        points_svg = f"""
    <circle cx="{top_x}" cy="{top_y}" r="3" fill="red"/>
    <circle cx="{chin_x}" cy="{chin_y}" r="3" fill="red"/>

    <circle cx="{ear_left_x}" cy="{ear_top_y}" r="3" fill="red"/>
    <circle cx="{ear_right_x}" cy="{ear_top_y}" r="3" fill="red"/>

    <circle cx="{ear_left_x}" cy="{ear_bottom_y}" r="3" fill="red"/>
    <circle cx="{ear_right_x}" cy="{ear_bottom_y}" r="3" fill="red"/>

    <circle cx="{jaw_left_x}" cy="{jaw_y}" r="3" fill="red"/>
    <circle cx="{jaw_right_x}" cy="{jaw_y}" r="3" fill="red"/>

    <circle cx="{chin_side_left_x}" cy="{chin_side_y}" r="3" fill="red"/>
    <circle cx="{chin_side_right_x}" cy="{chin_side_y}" r="3" fill="red"/>
"""

    # -------------------------------------------------
    # GROUP
    # -------------------------------------------------

    return f"""
<g transform="translate({offset_x},{offset_y})">

    <path d="
        m {m_x} {m_y}
        c {c1_dx} {c1_dy}
          {c2_dx} {c2_dy}
          {end1_dx} {end1_dy}
        l {l1_dx} {l1_dy}
        l {l2_dx} {l2_dy}
        l {l3_dx} {l3_dy}
        l {l4_dx} {l4_dy}
    " stroke="black" fill="transparent"/>

    <path d="
        m {m_x} {m_y}
        c {c1_dx_l} {c1_dy_l}
          {c2_dx_l} {c2_dy_l}
          {end1_dx_l} {end1_dy_l}
        l {l1_dx} {l1_dy}
        l {l2_dx_l} {l2_dy}
        l {l3_dx_l} {l3_dy}
        l {l4_dx_l} {l4_dy}
    " stroke="black" fill="transparent"/>

    {points_svg}

</g>
"""


# =====================================================
# KOKO SVG
# =====================================================

def generate_svg(show_points):

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="{SVG_WIDTH}" height="{SVG_HEIGHT}"
     viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}"
     xmlns="http://www.w3.org/2000/svg">

<rect width="100%" height="100%" fill="white"/>
"""

    for row in range(ROWS):
        for col in range(COLS):
            offset_x = col * CELL_WIDTH
            offset_y = row * CELL_HEIGHT
            svg += generate_head_group(offset_x, offset_y, show_points)

    svg += "\n</svg>"
    return svg


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    svg_content = generate_svg(show_points=False)

    with open("heads_grid.svg", "w") as f:
        f.write(svg_content)
