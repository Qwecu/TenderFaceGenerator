import random

# =====================================================
# GLOBAALIT PARAMETRIT
# =====================================================

EYE_WIDTH = 100
BASE_Y = 72
FOLD_RATIO = 0.06
TENSION_RATIO = 0.25

IRIS_RADIUS = 22
PUPIL_RADIUS = 10

# -----------------------------------------------------
# SEGMENTTITYYPPIEN TODENNÄKÖISYYDET
# -----------------------------------------------------

SEGMENT_TYPE_WEIGHTS = {
    "l": 0.25,
    "c": 0.35,
    "q": 0.20,
    "s": 0.10,
    "t": 0.10
}

SEGMENT_TYPES = list(SEGMENT_TYPE_WEIGHTS.keys())
SEGMENT_WEIGHTS = list(SEGMENT_TYPE_WEIGHTS.values())

# =====================================================
# DELTA-Y RANGET
# =====================================================

UPPER_DY_RANGES = [
    (-21, -12),
    (-7, 5),
    (-5, 10),
    (-8, 15)
]

LOWER_DY_RANGES = [
    (5, 12),
    (-2, 6),
    (-3, 5),
    (2, 8)
]

# =====================================================
# APUFUNKTIOT
# =====================================================

def rand_gene():
    return random.randint(0, 255)

def weighted_segment_type():
    return random.choices(SEGMENT_TYPES, weights=SEGMENT_WEIGHTS, k=1)[0]

def rand_tension():
    return random.uniform(-1.0, 1.0)

# =====================================================
# GENOMI
# =====================================================

class MinimalEyeGenome:

    def __init__(self):
        self.width_genes = [[rand_gene() for _ in range(4)] for _ in range(4)]
        self.upper_y_genes = [rand_gene() for _ in range(4)]
        self.lower_y_genes = [rand_gene() for _ in range(4)]

        self.upper_seg_type = [weighted_segment_type() for _ in range(4)]
        self.lower_seg_type = [weighted_segment_type() for _ in range(4)]

        self.upper_tension = [rand_tension() for _ in range(4)]
        self.lower_tension = [rand_tension() for _ in range(4)]

    # =====================================================
    # ΔX
    # =====================================================

    def compute_dx(self):
        raw = [max(1, sum(self.width_genes[i]) / 4) for i in range(4)]
        scale = EYE_WIDTH / sum(raw)
        return [r * scale for r in raw]

    # =====================================================
    # ΔY
    # =====================================================

    def compute_dy(self):
        upper = []
        lower = []

        for i in range(4):
            norm = self.upper_y_genes[i] / 255
            mn, mx = UPPER_DY_RANGES[i]
            upper.append(mn + norm * (mx - mn))

        for i in range(4):
            norm = self.lower_y_genes[i] / 255
            mn, mx = LOWER_DY_RANGES[i]
            lower.append(mn + norm * (mx - mn))
        # Oikean kulman vakiointi
        diff = sum(lower) - sum(upper)
        lower[-2] -= diff / 3
        lower[-1] -= 2 * diff / 3

        return upper, lower

    # =====================================================
    # PATH RAKENNUS
    # =====================================================

    def build_path(self, dx_list, dy_list, seg_types, tensions):

        d = f"m 0 {BASE_Y:.2f} "

        prev_type = None

        for i in range(4):
            dx = dx_list[i]
            dy = dy_list[i]
            t = seg_types[i]
            tension = tensions[i]

            ctrl_offset = tension * dx * TENSION_RATIO

            # ---------------------------------
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
