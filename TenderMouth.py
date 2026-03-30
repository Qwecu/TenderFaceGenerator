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
# 87: peak_dy      midline inner segment peak: always rises, −0.09w…−0.01w
# 88: valley_offset midline center offset: negative = rises above peaks, positive = dips below
# 89: corner_lift   mouth corner y-offset: negative = upturned (happy), positive = downturned
# 90: outer raw width  } all three normalised so 2*outer + 2*inner + mid = 1.0
# 91: inner raw width  }
# 92: mid   raw width  }
# 93: inner_arch    upward bow of inner segments; activates top 30% of gene range (0…−0.04w)
GENE_BASE = 80


# =====================================================
# MIDLINE SEGMENT PROPORTIONS
# =====================================================
# All three segment widths are gene-driven (genes 10–12).
# Raw values are normalised so 2*outer + 2*inner + mid = 1.0.
# The resulting normalised path is then scaled to mouth_width at face level.


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
        # Genes 10–12: raw widths for outer, inner, mid segments.
        # Floor at 0.04 to prevent degenerate zero-width segments.
        raw_outer = max(0.04, self._gene(10))
        raw_inner = max(0.04, self._gene(11))
        raw_mid   = max(0.18, self._gene(12))
        total     = 2 * raw_outer + 2 * raw_inner + raw_mid
        outer_w = w * raw_outer / total
        inner_w = w * raw_inner / total

        # Keypoint x positions
        x1 = outer_w
        x2 = outer_w + inner_w
        x4 = w - outer_w - inner_w   # = w - x2
        x5 = w - outer_w              # = w - x1

        # Gene 6: corner y deviation  (−0.03 … +0.03 of w)
        corner_y = w * (-0.03 + self._gene(6) * 0.06)

        # Gene 7: inner segment peak — always rises (negative y)
        # Range: −0.09w (pronounced rise) … −0.01w (nearly flat)
        peak_y = -w * (0.01 + self._gene(7) * 0.08)

        # Gene 13: inner arch — upward bow of inner segments' bezier control points
        # Activates only for top 30% of gene range; 0…−0.04w upward bow
        inner_arch = -w * max(0.0, (self._gene(13) - 0.7) / 0.3) * 0.04

        # Gene 8: center offset relative to peaks — negative rises above peaks, positive dips below
        # Range: −0.03w (center arches up) … +0.07w (center dips down, classic Cupid's bow)
        valley_y = peak_y + w * (-0.03 + self._gene(8) * 0.10)

        # Gene 9: corner lift — shifts both mouth endpoints up or down
        # Range: −0.05w (upturned / happy) … +0.04w (downturned / sad)
        corner_lift = w * (-0.05 + self._gene(9) * 0.09)

        return dict(x1=x1, x2=x2, x4=x4, x5=x5,
                    corner_y=corner_y, peak_y=peak_y, valley_y=valley_y,
                    corner_lift=corner_lift, inner_arch=inner_arch)

    # =====================================================
    # LOW-LEVEL BEZIER HELPERS
    # =====================================================

    def _seg_ctrl(self, x0, y0, x1, y1, t=0.35, arch=0):
        """Returns (cp1x, cp1y, cp2x, cp2y) matching _seg_fwd."""
        dx, dy = x1 - x0, y1 - y0
        return (x0 + dx*t, y0 + dy*t + arch, x1 - dx*t, y1 - dy*t + arch)

    def _mid_ctrl(self, x0, x1, vy, t=0.35):
        """Returns (cp1x, cp1y, cp2x, cp2y) matching _mid_fwd (y0==y1, dips to vy)."""
        span = x1 - x0
        return (x0 + span*t, vy, x1 - span*t, vy)

    def _seg_fwd(self, x0, y0, x1, y1, t=0.35, arch=0):
        """Cubic bezier from (x0,y0) → (x1,y1) with symmetric tension t.
        arch offsets both control points' y (negative = bow upward)."""
        dx, dy = x1 - x0, y1 - y0
        return (f"C {x0+dx*t:.4f} {y0+dy*t+arch:.4f} "
                f"{x1-dx*t:.4f} {y1-dy*t+arch:.4f} "
                f"{x1:.4f} {y1:.4f} ")

    def _seg_rev(self, x0, y0, x1, y1, t=0.35, arch=0):
        """Same segment traversed backwards: (x1,y1) → (x0,y0)."""
        dx, dy = x1 - x0, y1 - y0
        return (f"C {x1-dx*t:.4f} {y1-dy*t+arch:.4f} "
                f"{x0+dx*t:.4f} {y0+dy*t+arch:.4f} "
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
        """5-segment midline path from left corner to right corner, shifted by corner_lift."""
        g = self._midline_geometry(w)
        x1, x2, x4, x5 = g['x1'], g['x2'], g['x4'], g['x5']
        cl = g['corner_lift']
        ia = g['inner_arch']
        cy, py, vy = g['corner_y'] + cl, g['peak_y'] + cl, g['valley_y'] + cl

        d = f"M 0.0000 {cl:.4f} "
        d += self._seg_fwd(0,  cl, x1, cy)                # outer_left
        d += self._seg_fwd(x1, cy, x2, py, arch=ia)       # inner_left
        d += self._mid_fwd(x2, py, x4, py, vy)            # mid (dips to valley)
        d += self._seg_fwd(x4, py, x5, cy, arch=ia)       # inner_right
        d += self._seg_fwd(x5, cy, w,  cl)                # outer_right
        return d

    def _midline_rev(self, w):
        """Same midline traversed right → left, shifted by corner_lift."""
        g = self._midline_geometry(w)
        x1, x2, x4, x5 = g['x1'], g['x2'], g['x4'], g['x5']
        cl = g['corner_lift']
        ia = g['inner_arch']
        cy, py, vy = g['corner_y'] + cl, g['peak_y'] + cl, g['valley_y'] + cl

        d = f"M {w:.4f} {cl:.4f} "
        d += self._seg_rev(x5, cy, w,  cl)                # outer_right reversed
        d += self._seg_rev(x4, py, x5, cy, arch=ia)       # inner_right reversed
        d += self._mid_rev(x2, py, x4, py, vy)            # mid reversed
        d += self._seg_rev(x1, cy, x2, py, arch=ia)       # inner_left reversed
        d += self._seg_rev(0,  cl, x1, cy)                # outer_left reversed
        return d

    def _strip_move(self, path_d):
        """Strip the leading 'M x y' token from a path d-string."""
        tokens = path_d.split()
        return " ".join(tokens[3:])   # skip 'M', x, y

    # =====================================================
    # LIP PATH CONSTRUCTION
    # =====================================================

    def build_upper_lip(self, w, bow_h, valley_h, bow_x, ctrl, corner_lift):
        """
        Upper lip: Cupid's bow on top, midline as base.
        All y values offset by corner_lift so the lip follows the corner position.
        """
        cx   = w * 0.5
        lp_x = w * bow_x
        rp_x = w * (1 - bow_x)
        cl   = corner_lift

        seg1 = (f"C {ctrl:.4f} {cl - bow_h*0.5:.4f} "
                f"{lp_x-ctrl:.4f} {cl - bow_h:.4f} "
                f"{lp_x:.4f} {cl - bow_h:.4f} ")
        seg2 = (f"C {lp_x+ctrl:.4f} {cl - bow_h:.4f} "
                f"{cx-ctrl:.4f} {cl - valley_h:.4f} "
                f"{cx:.4f} {cl - valley_h:.4f} ")
        seg3 = (f"C {cx+ctrl:.4f} {cl - valley_h:.4f} "
                f"{rp_x-ctrl:.4f} {cl - bow_h:.4f} "
                f"{rp_x:.4f} {cl - bow_h:.4f} ")
        seg4 = (f"C {rp_x+ctrl:.4f} {cl - bow_h:.4f} "
                f"{w-ctrl:.4f} {cl - bow_h*0.5:.4f} "
                f"{w:.4f} {cl:.4f} ")

        midline_base = self._strip_move(self._midline_rev(w))

        return f"M 0.0000 {cl:.4f} {seg1}{seg2}{seg3}{seg4}{midline_base} Z"

    def build_lower_lip(self, w, lower_h, l_ctrl, corner_lift):
        """
        Lower lip: midline as top edge, lower arc as base.
        Arc control points sit lower_h below the (lifted) corners.
        """
        midline_top = self._strip_move(self._midline_fwd(w))
        cl  = corner_lift
        arc_y = cl + lower_h   # arc bottom is lower_h below the corners

        lower_arc_rev = (f"C {w-l_ctrl:.4f} {arc_y:.4f} "
                         f"{l_ctrl:.4f} {arc_y:.4f} "
                         f"0.0000 {cl:.4f} ")

        return f"M 0.0000 {cl:.4f} {midline_top} {lower_arc_rev} Z"

    # =====================================================
    # CONTROL-POINT VISUALIZATION
    # =====================================================

    def _ctrl_points_group(self, w, bow_h, valley_h, bow_x, ctrl, lower_h, l_ctrl):
        """
        Hidden SVG group (class="ctrl-points") showing all bezier handles.
        Red  = anchor points on the path.
        Blue = cubic bezier control points.
        """
        g   = self._midline_geometry(w)
        mx1, mx2, mx4, mx5 = g['x1'], g['x2'], g['x4'], g['x5']
        cl  = g['corner_lift']
        ia  = g['inner_arch']
        mcy, mpy, mvy = g['corner_y'] + cl, g['peak_y'] + cl, g['valley_y'] + cl

        cx   = w * 0.5
        lp_x = w * bow_x
        rp_x = w * (1 - bow_x)

        r  = 0.020
        sw = 0.005

        def dot(x, y, color="red"):
            return f'<circle cx="{x:.4f}" cy="{y:.4f}" r="{r}" fill="{color}" stroke="none"/>'

        def dash(x1, y1, x2, y2):
            return (f'<line x1="{x1:.4f}" y1="{y1:.4f}" x2="{x2:.4f}" y2="{y2:.4f}"'
                    f' stroke="red" stroke-width="{sw}" stroke-dasharray="0.04 0.02"/>')

        out = '<g class="ctrl-points" style="display:none">\n'

        # ---- Midline: 5 segments ----
        midline_anchors = [(0, cl), (mx1, mcy), (mx2, mpy), (mx4, mpy), (mx5, mcy), (w, cl)]
        midline_segs = [
            self._seg_ctrl(0,   cl,  mx1, mcy),
            self._seg_ctrl(mx1, mcy, mx2, mpy, arch=ia),   # inner_left
            (*self._mid_ctrl(mx2, mx4, mvy),),              # mid: same y both ends, dips to mvy
            self._seg_ctrl(mx4, mpy, mx5, mcy, arch=ia),   # inner_right
            self._seg_ctrl(mx5, mcy, w,   cl),
        ]
        for (ax, ay), (c1x, c1y, c2x, c2y), (bx, by) in zip(
                midline_anchors, midline_segs, midline_anchors[1:]):
            out += dash(ax, ay, c1x, c1y)
            out += dash(bx, by, c2x, c2y)
            out += dot(c1x, c1y, "blue")
            out += dot(c2x, c2y, "blue")
        for ax, ay in midline_anchors:
            out += dot(ax, ay)

        # ---- Upper lip: anchor points only ----
        for ax, ay in [(0, cl), (lp_x, cl - bow_h), (cx, cl - valley_h), (rp_x, cl - bow_h), (w, cl)]:
            out += dot(ax, ay)

        # ---- Lower lip: anchor points only ----
        # (corners already drawn above; just add the implicit bottom center)
        out += dot(w * 0.5, cl + lower_h)

        out += '</g>'
        return out

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

        corner_lift = self._midline_geometry(w)['corner_lift']

        upper   = self.build_upper_lip(w, bow_h, valley_h, bow_x, ctrl, corner_lift)
        lower   = self.build_lower_lip(w, lower_h, l_ctrl, corner_lift)
        midline = self._midline_fwd(w)
        cp_group = self._ctrl_points_group(w, bow_h, valley_h, bow_x, ctrl, lower_h, l_ctrl)

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

{cp_group}
"""
