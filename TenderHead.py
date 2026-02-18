def generate_head_svg():

    # =====================================================
    # PERUSMITAT
    # =====================================================

    CENTER_X = 200

    HEAD_TOP = 60
    HEAD_BOTTOM = 420

    FACE_HEIGHT = HEAD_BOTTOM - HEAD_TOP

    # Leveys suhteessa korkeuteen
    HEAD_WIDTH = FACE_HEIGHT * 0.65
    HALF_WIDTH = HEAD_WIDTH / 2

    # =====================================================
    # TUKIPISTEET
    # =====================================================

    # Päälaen korkein
    top_x = CENTER_X
    top_y = HEAD_TOP

    # Leuan kärki
    chin_x = CENTER_X
    chin_y = HEAD_BOTTOM

    # Korvien yläkohta (25% korkeudesta)
    ear_top_y = HEAD_TOP + FACE_HEIGHT * 0.25
    ear_left_x = CENTER_X - HALF_WIDTH
    ear_right_x = CENTER_X + HALF_WIDTH

    # Korvien alakohta (55% korkeudesta)
    ear_bottom_y = HEAD_TOP + FACE_HEIGHT * 0.55

    # Leukaluun reuna (75%)
    jaw_y = HEAD_TOP + FACE_HEIGHT * 0.75
    jaw_offset = HALF_WIDTH * 0.85
    jaw_left_x = CENTER_X - jaw_offset
    jaw_right_x = CENTER_X + jaw_offset

    # Leuan sivut (88%)
    chin_side_y = HEAD_TOP + FACE_HEIGHT * 0.88
    chin_side_offset = HALF_WIDTH * 0.45
    chin_side_left_x = CENTER_X - chin_side_offset
    chin_side_right_x = CENTER_X + chin_side_offset

    # =====================================================
    # SVG
    # =====================================================

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg width="400" height="500" viewBox="0 0 400 500"
     xmlns="http://www.w3.org/2000/svg">

    <rect width="100%" height="100%" fill="white"/>

    <!-- Keskilinja -->
    <line x1="{CENTER_X}" y1="0" x2="{CENTER_X}" y2="500"
          stroke="#eeeeee" stroke-width="1"/>

    <!-- PÄÄN OIKEA REUNA -->
    <path d="
        M {top_x} {top_y}
        C {top_x + HALF_WIDTH*0.5} {top_y}
          {ear_right_x} {ear_top_y - 40}
          {ear_right_x} {ear_top_y}

        L {ear_right_x} {ear_bottom_y}
        L {jaw_right_x} {jaw_y}
        L {chin_side_right_x} {chin_side_y}
        L {chin_x} {chin_y}
    "
    stroke="black" fill="transparent"/>

    <!-- VASEN REUNA -->
    <path d="
        M {top_x} {top_y}
        C {top_x - HALF_WIDTH*0.5} {top_y}
          {ear_left_x} {ear_top_y - 40}
          {ear_left_x} {ear_top_y}

        L {ear_left_x} {ear_bottom_y}
        L {jaw_left_x} {jaw_y}
        L {chin_side_left_x} {chin_side_y}
        L {chin_x} {chin_y}
    "
    stroke="black" fill="transparent"/>

    <!-- TUKIPISTEET -->

    <circle cx="{top_x}" cy="{top_y}" r="5" fill="red"/>
    <circle cx="{chin_x}" cy="{chin_y}" r="5" fill="red"/>

    <circle cx="{ear_left_x}" cy="{ear_top_y}" r="5" fill="red"/>
    <circle cx="{ear_right_x}" cy="{ear_top_y}" r="5" fill="red"/>

    <circle cx="{ear_left_x}" cy="{ear_bottom_y}" r="5" fill="red"/>
    <circle cx="{ear_right_x}" cy="{ear_bottom_y}" r="5" fill="red"/>

    <circle cx="{jaw_left_x}" cy="{jaw_y}" r="5" fill="red"/>
    <circle cx="{jaw_right_x}" cy="{jaw_y}" r="5" fill="red"/>

    <circle cx="{chin_side_left_x}" cy="{chin_side_y}" r="5" fill="red"/>
    <circle cx="{chin_side_right_x}" cy="{chin_side_y}" r="5" fill="red"/>

</svg>
"""
    return svg


# Kirjoitetaan tiedostoon
with open("head_base.svg", "w") as f:
    f.write(generate_head_svg())
