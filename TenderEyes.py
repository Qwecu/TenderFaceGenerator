import random

# =====================================================
# GLOBAALIT PARAMETRIT
# =====================================================

EYE_WIDTH = 100      
# Silmän kokonaisleveys pikseleinä.
# Δx-segmentit skaalataan niin, että niiden summa on tämä arvo.

BASE_Y = 72          
# Silmän vasemman kulman lähtökoordinaatti y-suunnassa.
# Kaikki pathit alkavat pisteestä (0, BASE_Y).

FOLD_RATIO = 0.06    
# Luomiraon korkeus suhteessa silmän leveyteen.
# Fold-offset = EYE_WIDTH * FOLD_RATIO.

TENSION_RATIO = 0.25 
# Maksimijännityksen suhde segmentin pituuteen.
# Määrittää kuinka voimakkaasti Bezier-kontrollipiste
# voi poiketa suorasta linjasta.

IRIS_RADIUS = 22     
# Iiriksen säde pikseleinä.

PUPIL_RADIUS = 10    
# Pupillin säde pikseleinä.


# -----------------------------------------------------
# SEGMENTTITYYPPIEN TODENNÄKÖISYYDET
# -----------------------------------------------------
# Painotettu jakauma SVG-pathin segmenttikomennoille.
# Arvot eivät ole todennäköisyyksiä vaan suhteellisia painoja.

SEGMENT_TYPE_WEIGHTS = {
    "l": 0.25,  # Line (suora segmentti)
    "c": 0.35,  # Cubic Bezier
    "q": 0.20,  # Quadratic Bezier
    "s": 0.10,  # Smooth cubic Bezier
    "t": 0.10   # Smooth quadratic Bezier
}

SEGMENT_TYPES = list(SEGMENT_TYPE_WEIGHTS.keys())
SEGMENT_WEIGHTS = list(SEGMENT_TYPE_WEIGHTS.values())


# =====================================================
# DELTA-Y RANGET
# =====================================================
# Jokainen arvo on RELATIIVINEN y-muutos (Δy) kyseiselle segmentille.
# Arvot määrittelevät biologisen "liikealueen" segmenttikohtaisesti.

UPPER_DY_RANGES = [
    (-21, -12),  # p0 -> p1: yläluomi nousee selvästi
    (-7, 5),     # p1 -> p2: melko tasainen
    (-5, 10),    # p2 -> p3: voi hieman nousta
    (-8, 15)     # p3 -> p4: loppuosa, usein laskee
]

LOWER_DY_RANGES = [
    (5, 12),     # p0 -> p1: alaluomi laskee
    (-2, 6),     # p1 -> p2: tasaisempi
    (-3, 5),     # p2 -> p3: pieni nousu mahdollinen
    (2, 8)       # p3 -> p4: loppuosa
]


# =====================================================
# APUFUNKTIOT
# =====================================================

def rand_gene():
    # 8-bittinen geeni (0–255)
    return random.randint(0, 255)

def weighted_segment_type():
    # Palauttaa segmenttityypin globaalien painojen perusteella
    return random.choices(SEGMENT_TYPES, weights=SEGMENT_WEIGHTS, k=1)[0]

def rand_tension():
    # Jännitysarvo väliltä [-1, 1]
    return random.uniform(-1.0, 1.0)


# =====================================================
# GENOMI
# =====================================================

class MinimalEyeGenome:

    def __init__(self):
        # 4 segmenttiä × 4 geeniä per segmentti (Δx)
        # Fenotyyppi = geenien keskiarvo
        self.width_genes = [[rand_gene() for _ in range(4)] for _ in range(4)]

        # Δy-geenit (relatiiviset muutokset segmenttikohtaisesti)
        self.upper_y_genes = [rand_gene() for _ in range(4)]
        self.lower_y_genes = [rand_gene() for _ in range(4)]

        # Segmenttityypit arvotaan painotetusti
        self.upper_seg_type = [weighted_segment_type() for _ in range(4)]
        self.lower_seg_type = [weighted_segment_type() for _ in range(4)]

        # Bezier-jännitykset segmenttikohtaisesti
        self.upper_tension = [rand_tension() for _ in range(4)]
        self.lower_tension = [rand_tension() for _ in range(4)]

    # =====================================================
    # ΔX
    # =====================================================

    def compute_dx(self):
        # Keskiarvo neljästä geenistä per segmentti
        raw = [max(1, sum(self.width_genes[i]) / 4) for i in range(4)]

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
            norm = self.upper_y_genes[i] / 255
            mn, mx = UPPER_DY_RANGES[i]
            upper.append(mn + norm * (mx - mn))

        # --- ALALUOMI ---
        for i in range(4):
            norm = self.lower_y_genes[i] / 255
            mn, mx = LOWER_DY_RANGES[i]
            lower.append(mn + norm * (mx - mn))

        # Oikean kulman vakiointi:
        # jaetaan ylä- ja alaluomen päätepisteiden erotus
        # kahdelle viimeiselle alaluomen segmentille (1/3 + 2/3)
        diff = sum(lower) - sum(upper)
        lower[-2] -= diff / 3
        lower[-1] -= 2 * diff / 3

        return upper, lower

    # =====================================================
    # PATH RAKENNUS
    # =====================================================

    def build_path(self, dx_list, dy_list, seg_types, tensions):

        # Lähtöpiste absoluuttisesti (m), sen jälkeen kaikki relatiivista
        d = f"m 0 {BASE_Y:.2f} "

        prev_type = None

        for i in range(4):
            dx = dx_list[i]
            dy = dy_list[i]
            t = seg_types[i]
            tension = tensions[i]

            ctrl_offset = tension * dx * TENSION_RATIO

            if t == "l":
                d += f"l {dx:.2f} {dy:.2f} "

            elif t == "c":
                d += (
                    f"c {dx*0.25:.2f} {dy*0.25 + ctrl_offset:.2f} "
                    f"{dx*0.75:.2f} {dy*0.75 + ctrl_offset:.2f} "
                    f"{dx:.2f} {dy:.2f} "
                )

            elif t == "q":
                d += (
                    f"q {dx*0.5:.2f} {dy*0.5 + ctrl_offset:.2f} "
                    f"{dx:.2f} {dy:.2f} "
                )

            elif t == "s":
                d += (
                    f"s {dx*0.75:.2f} {dy*0.75 + ctrl_offset:.2f} "
                    f"{dx:.2f} {dy:.2f} "
                )

            elif t == "t":
                d += f"t {dx:.2f} {dy:.2f} "

            prev_type = t

        return d

    # =====================================================
    # SVG
    # =====================================================

    def generate_svg(self):

        dx_list = self.compute_dx()
        upper_dy, lower_dy = self.compute_dy()

        upper_path = self.build_path(
            dx_list, upper_dy,
            self.upper_seg_type, self.upper_tension
        )

        lower_path = self.build_path(
            dx_list, lower_dy,
            self.lower_seg_type, self.lower_tension
        )

        fold_offset = EYE_WIDTH * FOLD_RATIO
        fold_dy = [dy - fold_offset for dy in upper_dy]

        fold_path = self.build_path(
            dx_list, fold_dy,
            self.upper_seg_type, self.upper_tension
        )

        iris_center_x = sum(dx_list) / 2
        iris_center_y = BASE_Y

        svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 140">

  <defs>
    <clipPath id="eyeClip" clipPathUnits="userSpaceOnUse">
      <path d="{upper_path} l 0 1" />
      <path d="{lower_path} l 0 -1" />
    </clipPath>
  </defs>

  <circle cx="{iris_center_x:.2f}"
          cy="{iris_center_y:.2f}"
          r="{IRIS_RADIUS}"
          fill="#88aaff"
          clip-path="url(#eyeClip)"/>

  <circle cx="{iris_center_x:.2f}"
          cy="{iris_center_y:.2f}"
          r="{PUPIL_RADIUS}"
          fill="black"
          clip-path="url(#eyeClip)"/>

  <path d="{upper_path}" fill="none" stroke="black"/>
  <path d="{fold_path}" fill="none" stroke="black"/>
  <path d="{lower_path}" fill="none" stroke="black"/>

</svg>
"""
        return svg


# =====================================================
# AJETAAN
# =====================================================

if __name__ == "__main__":
    eye = MinimalEyeGenome()
    svg_output = eye.generate_svg()

    with open("genetic_eye.svg", "w") as f:
        f.write(svg_output)

    print("SVG created: genetic_eye.svg")
