from genes import Genome

import math

# =====================================================
# GLOBAALIT PARAMETRIT
# =====================================================

EYE_WIDTH = 140      
# Silmän kokonaisleveys pikseleinä.
# Δx-segmentit skaalataan niin, että niiden summa on tämä arvo.

FOLD_RATIO = 0.06    
# Luomiraon korkeus suhteessa silmän leveyteen.
# Fold-offset = EYE_WIDTH * FOLD_RATIO.

TENSION_RATIO = 0.25 
# Maksimijännityksen suhde segmentin pituuteen.
# Määrittää kuinka voimakkaasti Bezier-kontrollipiste
# voi poiketa suorasta linjasta.

IRIS_RADIUS = 36    
# Iiriksen säde pikseleinä.

PUPIL_RADIUS = 16    
# Pupillin säde pikseleinä.


# -----------------------------------------------------
# SEGMENTTITYYPPIEN TODENNÄKÖISYYDET
# -----------------------------------------------------
# Painotettu jakauma SVG-pathin segmenttikomennoille.
# Arvot eivät ole todennäköisyyksiä vaan suhteellisia painoja.

SEGMENT_TYPE_WEIGHTS = {
    "L": 0.25,  # Line (suora segmentti)
    "C": 0.35,  # Cubic Bezier
    "Q": 0.20,  # Quadratic Bezier
    "S": 0.10,  # Smooth cubic Bezier
    "T": 0.10   # Smooth quadratic Bezier
}

SEGMENT_TYPES = list(SEGMENT_TYPE_WEIGHTS.keys())
SEGMENT_WEIGHTS = list(SEGMENT_TYPE_WEIGHTS.values())


# =====================================================
# DELTA-Y RANGET
# =====================================================
# Jokainen arvo on RELATIIVINEN y-muutos (Δy) kyseiselle segmentille.
# Arvot määrittelevät biologisen "liikealueen" segmenttikohtaisesti.

UPPER_DY_RANGES = [
    (-41, -23),
    (-14, 10),
    (-10, 20),
    (-16, 35)
]

LOWER_DY_RANGES = [
    (10, 24),
    (-4, 12),
    (-6, 16),
    (4, 16)
]


# =====================================================
# MINIMAALINEN SILMÄ
# =====================================================

class MinimalEyeGenome:

    def __init__(self, genome=None, stroke_ratio=140):
        """
        stroke_ratio:
            Kuinka monta kertaa stroke mahtuu EYE_WIDTHiin.
            Oletus 140 → stroke = 1px kun EYE_WIDTH = 140
        """
        self.genome = genome if genome is not None else Genome(num_genes=120)
        self.stroke_ratio = stroke_ratio



    # =====================================================
    # ΔX
    # =====================================================

    def compute_dx(self):
        raw = []

        # Keskiarvo neljästä geenistä per segmentti
        for seg in range(4):
            vals = [self.genome.get_width_gene(seg, i) for i in range(4)]
            raw.append(max(1, sum(vals) / 4))

        # Skaalataan niin, että segmenttien summa = EYE_WIDTH
        scale = EYE_WIDTH / sum(raw)
        return [r * scale for r in raw]

    # =====================================================
    # ΔY
    # =====================================================

    def compute_dy(self):

        upper = []
        lower = []

        # --- YLÄLUOMI ---
        for i in range(4):
            norm = self.genome.get_upper_y_gene(i) / 255
            mn, mx = UPPER_DY_RANGES[i]
            upper.append(mn + norm * (mx - mn))

        # --- ALALUOMI ---
        for i in range(4):
            norm = self.genome.get_lower_y_gene(i) / 255
            mn, mx = LOWER_DY_RANGES[i]
            lower.append(mn + norm * (mx - mn))

        # Oikean kulman vakiointi:
        # jaa erotus kolmelle ja laita
        # kaksi kolmasosaa viimeiselle ala-p:lle
        # yksi kolmasosa toiseksi viimeiselle

        diff = sum(lower) - sum(upper)
        lower[-2] -= diff / 3
        lower[-1] -= 2 * diff / 3

        return upper, lower

    # =====================================================
    # PATH RAKENNUS
    # =====================================================

    def build_path(self, dx_list, dy_list, seg_types, tensions):

        x = 0
        y = 0

        d = f"M {x:.2f} {y:.2f} "

        for i in range(4):

            dx = dx_list[i]
            dy = dy_list[i]
            t = seg_types[i]
            tension = tensions[i]

            x_next = x + dx
            y_next = y + dy

            ctrl_offset = tension * dx * TENSION_RATIO

            if t == "L":
                d += f"L {x_next:.2f} {y_next:.2f} "

            elif t == "C":
                c1x = x + dx * 0.25
                c1y = y + dy * 0.25 + ctrl_offset

                c2x = x + dx * 0.75
                c2y = y + dy * 0.75 + ctrl_offset

                d += (
                    f"C {c1x:.2f} {c1y:.2f} "
                    f"{c2x:.2f} {c2y:.2f} "
                    f"{x_next:.2f} {y_next:.2f} "
                )

            elif t == "Q":
                cx = x + dx * 0.5
                cy = y + dy * 0.5 + ctrl_offset

                d += (
                    f"Q {cx:.2f} {cy:.2f} "
                    f"{x_next:.2f} {y_next:.2f} "
                )

            elif t == "S":
                c2x = x + dx * 0.75
                c2y = y + dy * 0.75 + ctrl_offset

                d += (
                    f"S {c2x:.2f} {c2y:.2f} "
                    f"{x_next:.2f} {y_next:.2f} "
                )

            elif t == "T":
                d += f"T {x_next:.2f} {y_next:.2f} "

            x = x_next
            y = y_next

        return d


    # =====================================================
    # VÄRIN MUUNNOS
    # =====================================================

    def lighten(self, color, factor=0.45):
        """
        Vaaleampi versio väristä.
        """
        r, g, b = color
        return (
            int(r + (255 - r) * factor),
            int(g + (255 - g) * factor),
            int(b + (255 - b) * factor),
        )

    # =====================================================
    # IIRIKSEN POLYGONI
    # =====================================================

    def build_iris_polygon(self, cx, cy, radius, color):

        """
        Luo vaalea monikulmio iiriksen sisälle.
        """

        points = []
        sides = 12
        poly_radius = radius * (0.55 + 0.15 * self.genome.get_iris_highlight_multiplier())

        for i in range(sides):
            angle = 2 * math.pi * i / sides
            x = cx + poly_radius * math.cos(angle)
            y = cy + poly_radius * math.sin(angle)
            points.append(f"{x:.2f},{y:.2f}")

        return f"""
<polygon points="{' '.join(points)}"
         fill="rgb{color}"/>
"""

   # -------------------------------------------------
    # PALAUTTAA VAIN GROUPIN SISÄLLÖN
    # -------------------------------------------------

    def generate_group(self, clip_id, normalize=False):

        dx_list = self.compute_dx()
        upper_dy, lower_dy = self.compute_dy()
        

        # =====================================================
        # NORMALISOINTI 0–1 KOORDINAATISTOON (valinnainen)
        # =====================================================

        scale = 1.0
        radius_scale = 1.0
        stroke_width = EYE_WIDTH / self.stroke_ratio

        if normalize:
            scale = 1.0 / EYE_WIDTH
            radius_scale = scale
            stroke_width *= scale

            dx_list = [dx * scale for dx in dx_list]
            upper_dy = [dy * scale for dy in upper_dy]
            lower_dy = [dy * scale for dy in lower_dy]


        # Segmenttityypit ja jännitykset geeneistä
        upper_seg_type = [
            self.genome.get_segment_type(
                i,
                SEGMENT_TYPES,
                SEGMENT_WEIGHTS,
                upper=True
            )
            for i in range(4)
        ]

        lower_seg_type = [
            self.genome.get_segment_type(
                i,
                SEGMENT_TYPES,
                SEGMENT_WEIGHTS,
                upper=False
            )
            for i in range(4)
        ]

        upper_tension = [
            self.genome.get_tension(i, upper=True)
            for i in range(4)
        ]

        lower_tension = [
            self.genome.get_tension(i, upper=False)
            for i in range(4)
        ]

        upper_path = self.build_path(
            dx_list, upper_dy,
            upper_seg_type, upper_tension
        )

        lower_path = self.build_path(
            dx_list, lower_dy,
            lower_seg_type, lower_tension
        )

        fold_offset = (EYE_WIDTH * FOLD_RATIO) * scale
        fold_dy = [dy - fold_offset for dy in upper_dy]

        fold_path = self.build_path(
            dx_list, fold_dy,
            upper_seg_type, upper_tension
        )

        # Iiriksen keskipiste
        iris_center_x = sum(dx_list[:2])
        iris_center_y = (sum(upper_dy[0:3]) + sum(lower_dy[0:3])) / 2

        base_color = self.genome.get_iris_color()
        highlight_color = self.genome.get_iris_highlight_color()

        iris_polygon = self.build_iris_polygon(
            iris_center_x,
            iris_center_y,
            IRIS_RADIUS * radius_scale,
            highlight_color
        )


        return f"""
<defs>
  <clipPath id="{clip_id}" clipPathUnits="userSpaceOnUse">
    <path d="{upper_path}" />
    <path d="{lower_path}" />
  </clipPath>
</defs>

<circle cx="{iris_center_x:.2f}"
        cy="{iris_center_y:.2f}"
        r="{IRIS_RADIUS * radius_scale}"
        fill="rgb{base_color}"
        clip-path="url(#{clip_id})"/>

{iris_polygon.replace('<polygon ', f'<polygon clip-path="url(#{clip_id})" ')}

<circle cx="{iris_center_x:.2f}"
        cy="{iris_center_y:.2f}"
        r="{PUPIL_RADIUS * radius_scale}"
        fill="black"
        clip-path="url(#{clip_id})"/>

<path d="{upper_path}" fill="none" stroke="black" stroke-width="{stroke_width}"/>
<path d="{fold_path}" fill="none" stroke="black" stroke-width="{stroke_width}"/>
<path d="{lower_path}" fill="none" stroke="black" stroke-width="{stroke_width}""/>
"""

# =====================================================
# 4x4 GRID
# =====================================================

def generate_eye_grid():

    COLS = 4
    ROWS = 4

    CELL_WIDTH = 200
    CELL_HEIGHT = 100

    total_width = COLS * CELL_WIDTH
    total_height = ROWS * CELL_HEIGHT

    svg_content = ""

    for row in range(ROWS):
        for col in range(COLS):

            eye = MinimalEyeGenome()
            clip_id = f"eyeClip_{row}_{col}"

            tx = col * CELL_WIDTH
            ty = row * CELL_HEIGHT

            svg_content += f"""
<g transform="translate({tx},{ty})">
{eye.generate_group(clip_id)}
</g>
"""

    return f"""
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {total_width} {total_height}">
{svg_content}
</svg>
"""


# =====================================================
# AJETAAN
# =====================================================

if __name__ == "__main__":

    svg_output = generate_eye_grid()

    with open("genetic_eye_grid.svg", "w") as f:
        f.write(svg_output)

    print("SVG created: genetic_eye_grid.svg")
