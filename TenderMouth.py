from genes import Genome


# =====================================================
# GLOBAL PARAMETERS
# =====================================================

MOUTH_WIDTH = 100
# Base coordinate space width (normalized to 1.0 via normalize=True).

# Gene indices used by mouth (80–95)
# 80: bow_h        upper lip Cupid's bow height
# 81: valley_h     upper lip center valley (relative to bow_h)
# 82: lower_h      lower lip arc depth
# 83: bow_x        Cupid's bow peak x position (fraction)
# 84: ctrl         upper lip bezier tension
# 85: l_ctrl       lower lip bezier tension
# 86: outer_dy     midline corner deviation (small ±)
# 87: peak_dy      midline Cupid's bow peak height
# 88: valley_offset midline center offset: negative = rises above peaks, positive = dips below
GENE_BASE = 80


# =====================================================
# MIDLINE SEGMENT PROPORTIONS (fixed)
# =====================================================
# The 5 segments share the mouth width as follows:
#   outer × 2 + inner × 2 + mid = 1.0
OUTER_FRAC = 0.14   # each outer (corner) segment
INNER_FRAC = 0.16   # each inner (slope) segment
# mid_frac  = 1.0 - 2*(0.14 + 0.16) = 0.40


# =====================================================
# TENDER MOUTH
# =====================================================

class TenderMouth:

    def __init__(self, genome=None):
        self.genome = genome if genome is not None else Genome(num_genes=100)

    # =====================================================
    # GENE HELPERS
    # =====================================================

    def _gene(self, offset):
        """Returns gene at GENE_BASE + offset, normalised to 0–1."""
        return self.genome.get_gene(GENE_BASE + offset) / 255.0

    # =====================================================
    # LIP COLOR
    # =====================================================

    def get_lip_color(self):
        r, g, b = self.genome.get_skin_color()
        lr = min(255, int(r * 0.92 + 28))
        lg = max(0,   int(g * 0.78))
        lb = max(0,   int(b * 0.78))
        return (lr, lg, lb)

    # =====================================================
    # MIDLINE GEOMETRY
    # =====================================================

    def _midline_geometry(self, w):
        """
        Compute midline keypoint positions from genes.

        The 5-segment midline (left → right):
          outer_left  : short corner segment, slight y deviation
          inner_left  : slope up to Cupid's bow peak
          mid         : from left peak to right peak, dipping to valley at center
          inner_right : mirror of inner_left
          outer_right : mirror of outer_left

        Returns a dict of named x/y coordinates.
        """
        outer_w = w * OUTER_FRAC
        inner_w = w * INNER_FRAC

        # Keypoint x positions
        x1 = outer_w
        x2 = outer_w + inner_w
        x4 = w - outer_w - inner_w   # = w - x2
        x5 = w - outer_w              # = w - x1

        # Gene 6: corner y deviation  (−0.03 … +0.03 of w)
        corner_y = w * (-0.03 + self._gene(6) * 0.06)

        # Gene 7: midline Cupid's bow peak height (0.01 … 0.09 of w, upward = negative y)
        peak_y = -w * (0.01 + self._gene(7) * 0.08)

        # Gene 8: center offset relative to peaks — negative rises above peaks, positive dips below
        # Range: −0.03w (center arches up) … +0.07w (center dips down, classic Cupid's bow)
        valley_y = peak_y + w * (-0.03 + self._gene(8) * 0.10)

        return dict(x1=x1, x2=x2, x4=x4, x5=x5,
                    corner_y=corner_y, peak_y=peak_y, valley_y=valley_y)

    # =====================================================
    # LOW-LEVEL BEZIER HELPERS
    # =====================================================

    def _seg_fwd(self, x0, y0, x1, y1, t=0.35):
        """Cubic bezier from (x0,y0) → (x1,y1) with symmetric tension t."""
        dx, dy = x1 - x0, y1 - y0
        return (f"C {x0+dx*t:.4f} {y0+dy*t:.4f} "
                f"{x1-dx*t:.4f} {y1-dy*t:.4f} "
                f"{x1:.4f} {y1:.4f} ")

    def _seg_rev(self, x0, y0, x1, y1, t=0.35):
        """Same segment traversed backwards: (x1,y1) → (x0,y0)."""
        dx, dy = x1 - x0, y1 - y0
        return (f"C {x1-dx*t:.4f} {y1-dy*t:.4f} "
                f"{x0+dx*t:.4f} {y0+dy*t:.4f} "
                f"{x0:.4f} {y0:.4f} ")

    def _mid_fwd(self, x0, y0, x1, y1, vy, t=0.35):
        """
        Mid segment forward: both endpoints share y0=y1 (the peak_y),
        but the bezier dips to vy at the center.
        """
        span = x1 - x0
        return (f"C {x0+span*t:.4f} {vy:.4f} "
                f"{x1-span*t:.4f} {vy:.4f} "
                f"{x1:.4f} {y1:.4f} ")

    def _mid_rev(self, x0, y0, x1, y1, vy, t=0.35):
        """Mid segment reversed: (x1,y1) → (x0,y0), same internal dip."""
        span = x1 - x0
        return (f"C {x1-span*t:.4f} {vy:.4f} "
                f"{x0+span*t:.4f} {vy:.4f} "
                f"{x0:.4f} {y0:.4f} ")

    # =====================================================
    # MIDLINE PATHS
    # =====================================================

    def _midline_fwd(self, w):
        """5-segment midline path from left corner (0,0) to right corner (w,~0)."""
        g = self._midline_geometry(w)
        x1, x2, x4, x5 = g['x1'], g['x2'], g['x4'], g['x5']
        cy, py, vy = g['corner_y'], g['peak_y'], g['valley_y']

        d = "M 0.0000 0.0000 "
        d += self._seg_fwd(0,  0,  x1, cy)          # outer_left
        d += self._seg_fwd(x1, cy, x2, py)           # inner_left
        d += self._mid_fwd(x2, py, x4, py, vy)       # mid (dips to valley)
        d += self._seg_fwd(x4, py, x5, cy)           # inner_right
        d += self._seg_fwd(x5, cy, w,  0)            # outer_right
        return d

    def _midline_rev(self, w):
        """Same midline traversed right → left: from (w,~0) back to (0,0)."""
        g = self._midline_geometry(w)
        x1, x2, x4, x5 = g['x1'], g['x2'], g['x4'], g['x5']
        cy, py, vy = g['corner_y'], g['peak_y'], g['valley_y']

        d = f"M {w:.4f} 0.0000 "
        d += self._seg_rev(x5, cy, w,  0)            # outer_right reversed
        d += self._seg_rev(x4, py, x5, cy)           # inner_right reversed
        d += self._mid_rev(x2, py, x4, py, vy)       # mid reversed
        d += self._seg_rev(x1, cy, x2, py)           # inner_left reversed
        d += self._seg_rev(0,  0,  x1, cy)           # outer_left reversed
        return d

    def _strip_move(self, path_d):
        """Strip the leading 'M x y' token from a path d-string."""
        tokens = path_d.split()
        return " ".join(tokens[3:])   # skip 'M', x, y

    # =====================================================
    # LIP PATH CONSTRUCTION
    # =====================================================

    def build_upper_lip(self, w, bow_h, valley_h, bow_x, ctrl):
        """
        Upper lip: Cupid's bow on top, midline as base.

        Path: M 0 0 → [Cupid's bow, left to right] → (w, 0)
                    → [midline reversed, right to left] → (0, 0)  → Z
        """
        cx   = w * 0.5
        lp_x = w * bow_x
        rp_x = w * (1 - bow_x)

        seg1 = (f"C {ctrl:.4f} {-bow_h*0.5:.4f} "
                f"{lp_x-ctrl:.4f} {-bow_h:.4f} "
                f"{lp_x:.4f} {-bow_h:.4f} ")
        seg2 = (f"C {lp_x+ctrl:.4f} {-bow_h:.4f} "
                f"{cx-ctrl:.4f} {-valley_h:.4f} "
                f"{cx:.4f} {-valley_h:.4f} ")
        seg3 = (f"C {cx+ctrl:.4f} {-valley_h:.4f} "
                f"{rp_x-ctrl:.4f} {-bow_h:.4f} "
                f"{rp_x:.4f} {-bow_h:.4f} ")
        seg4 = (f"C {rp_x+ctrl:.4f} {-bow_h:.4f} "
                f"{w-ctrl:.4f} {-bow_h*0.5:.4f} "
                f"{w:.4f} 0.0000 ")

        midline_base = self._strip_move(self._midline_rev(w))

        return f"M 0.0000 0.0000 {seg1}{seg2}{seg3}{seg4}{midline_base} Z"

    def build_lower_lip(self, w, lower_h, l_ctrl):
        """
        Lower lip: midline as top edge, lower arc as base.

        Path: M 0 0 → [midline forward, left to right] → (w, 0)
                    → [lower arc reversed, right to left] → (0, 0)  → Z
        """
        midline_top = self._strip_move(self._midline_fwd(w))

        lower_arc_rev = (f"C {w-l_ctrl:.4f} {lower_h:.4f} "
                         f"{l_ctrl:.4f} {lower_h:.4f} "
                         f"0.0000 0.0000 ")

        return f"M 0.0000 0.0000 {midline_top} {lower_arc_rev} Z"

    # =====================================================
    # GROUP GENERATION
    # =====================================================

    def generate_group(self, normalize=False):

        w = 1.0 if normalize else MOUTH_WIDTH

        # Upper lip parameters
        bow_h    = w * (0.10 + self._gene(0) * 0.12)
        valley_h = bow_h * (0.20 + self._gene(1) * 0.50)
        bow_x    = 0.22 + self._gene(3) * 0.16
        ctrl     = w * (0.06 + self._gene(4) * 0.08)

        # Lower lip parameters
        lower_h  = w * (0.09 + self._gene(2) * 0.13)
        l_ctrl   = w * (0.20 + self._gene(5) * 0.20)

        lip_color = self.get_lip_color()
        stroke_w  = w * 0.008

        upper   = self.build_upper_lip(w, bow_h, valley_h, bow_x, ctrl)
        lower   = self.build_lower_lip(w, lower_h, l_ctrl)
        midline = self._midline_fwd(w)

        return f"""
<!-- Upper lip -->
<path d="{upper}"
      fill="rgb{lip_color}"
      stroke="rgb{lip_color}"
      stroke-width="{stroke_w:.4f}"
      stroke-linejoin="round"/>

<!-- Lower lip -->
<path d="{lower}"
      fill="rgb{lip_color}"
      stroke="rgb{lip_color}"
      stroke-width="{stroke_w:.4f}"
      stroke-linejoin="round"/>

<!-- Mouth midline -->
<path d="{midline}"
      fill="none"
      stroke="black"
      stroke-width="{stroke_w:.4f}"
      stroke-linecap="round"
      stroke-linejoin="round"/>
"""
