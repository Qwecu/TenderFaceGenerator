import random

# =====================================================
# GLOBAALIT PARAMETRIT
# =====================================================

EYE_WIDTH = 100      # kokonaisleveys silmälle
BASE_Y = 72          # lähtötaso y
FOLD_RATIO = 0.06    # luomiraon korkeus suhteessa leveyteen
TENSION_RATIO = 0.25 # Bezier-jännityksen maksimi suhteessa segmenttiin

# =====================================================
# DELTA-Y RANGET (RELATIIVISET MUUTOKSET, pikseleinä)
# =====================================================

UPPER_DY_RANGES = [
    (-20, -12),   # p0 -> p1: nousee
    (-5, 5),     # p1 -> p2: tasainen
    (-5, 10),      # p2 -> p3: voi nousta
    (-8, 15)     # p3 -> p4: laskee loppua kohden
]

LOWER_DY_RANGES = [
    (5, 12),      # p0 -> p1: laskee
    (-2, 6),      # p1 -> p2: tasainen
    (-3, 5),      # p2 -> p3: hieman nousee
    (2, 8)        # p3 -> p4: loppu
]

# =====================================================
# APUFUNKTIOT
# =====================================================

def rand_gene():
    return random.randint(0, 255)

def rand_bool():
    return random.randint(0, 1)

def rand_tension():
    return random.uniform(-1.0, 1.0)

# =====================================================
# GENOMI
# =====================================================

class MinimalEyeGenome:

    def __init__(self):
        # 4 segmenttiä × 4 geeniä per segmentti (Δx)
        self.width_genes = [[rand_gene() for _ in range(4)] for _ in range(4)]

        # Δy-geenit (relatiiviset muutokset)
        self.upper_y_genes = [rand_gene() for _ in range(4)]
        self.lower_y_genes = [rand_gene() for _ in range(4)]

        # Segmenttityypit ja jännitys
        self.upper_seg_type = [rand_bool() for _ in range(4)]
        self.lower_seg_type = [rand_bool() for _ in range(4)]

        self.upper_tension = [rand_tension() for _ in range(4)]
        self.lower_tension = [rand_tension() for _ in range(4)]

    # =====================================================
    # RELATIIVISET ΔX
    # =====================================================

    def compute_dx(self):
        # keskiarvo neljästä geenistä per segmentti
        raw = [max(1, sum(self.width_genes[i]) / 4) for i in range(4)]
        total = sum(raw)
        scale = EYE_WIDTH / total
        dx_list = [s * scale for s in raw]
        return dx_list  # dx0..dx3

    # =====================================================
    # RELATIIVISET ΔY
    # =====================================================

    def compute_dy(self):
        upper_dy = []
        lower_dy = []

        # --- YLÄLUOMI ---
        for i in range(4):
            norm = self.upper_y_genes[i] / 255
            dy_min, dy_max = UPPER_DY_RANGES[i]
            dy = dy_min + norm * (dy_max - dy_min)
            upper_dy.append(dy)

        # --- ALALUOMI ---
        for i in range(4):
            norm = self.lower_y_genes[i] / 255
            dy_min, dy_max = LOWER_DY_RANGES[i]
            dy = dy_min + norm * (dy_max - dy_min)
            lower_dy.append(dy)

        # --- OIKEAN KULMAN VAKIOINTI: jaetaan erotus kahdelle viimeiselle segmentille ---
        diff = sum(lower_dy) - sum(upper_dy)
        lower_dy[-2] -= diff / 3    # toiseksi viimeinen segmentti
        lower_dy[-1] -= 2 * diff / 3  # viimeinen segmentti

        return upper_dy, lower_dy

    # =====================================================
    # PATH (RELATIIVISET KOMENNOT)
    # =====================================================

    def build_path(self, dx_list, dy_list, seg_types, tensions):
        d = f"m 0 {BASE_Y:.2f} "  # lähtöpiste absoluuttisesti

        for i in range(4):
            dx = dx_list[i]
            dy = dy_list[i]

            if seg_types[i] == 0:
                d += f"l {dx:.2f} {dy:.2f} "
            else:
                tension_offset = tensions[i] * dx * TENSION_RATIO
                cx1x = dx * 0.25
                cx1y = dy * 0.25 + tension_offset
                cx2x = dx * 0.75
                cx2y = dy * 0.75 + tension_offset
                d += f"c {cx1x:.2f} {cx1y:.2f} {cx2x:.2f} {cx2y:.2f} {dx:.2f} {dy:.2f} "

        return d

    # =====================================================
    # SVG GENEROINTI
    # =====================================================

    def generate_svg(self):
        dx_list = self.compute_dx()
        upper_dy, lower_dy = self.compute_dy()

        upper_path = self.build_path(dx_list, upper_dy, self.upper_seg_type, self.upper_tension)
        lower_path = self.build_path(dx_list, lower_dy, self.lower_seg_type, self.lower_tension)

        fold_offset = EYE_WIDTH * FOLD_RATIO
        fold_dy = [dy - fold_offset for dy in upper_dy]
        fold_path = self.build_path(dx_list, fold_dy, self.upper_seg_type, self.upper_tension)

        clip_path = upper_path + lower_path.replace("m 0 {:.2f} ".format(BASE_Y), "") + "z"

        svg = f"""
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 220 140">
  <defs>
    <clipPath id="eyeClip">
      <path d="{clip_path}" />
    </clipPath>
  </defs>

  <!-- YLÄLUOMI -->
  <path d="{upper_path}" fill="none" stroke="black"/>
  <!-- LUOMIRAKO -->
  <path d="{fold_path}" fill="none" stroke="black"/>
  <!-- ALALUOMI -->
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
