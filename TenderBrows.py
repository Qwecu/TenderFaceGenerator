from genes import Genome


# =====================================================
# EYEBROW GENERATION
# =====================================================
#
# Coordinate space: normalised to eye width = 1.0  (same scale as TenderEyes).
# x : 0 (inner corner) → 1 (outer corner)
# y : 0 is the brow reference line placed at brow_y in face space;
#     negative y = upward (toward forehead).
#
# Shape model
# -----------
# The brow is a filled closed bezier shape built from NUM_SEGS = 3 segments.
# Each segment has a center-line cubic bezier.  The upper and lower edges are
# derived by offsetting that center-line by ±half_width, which tapers linearly
# from a gene-controlled inner width down to 0 at the outer tip.
#
# Arch variation (driven by center-line Δy genes)
# -----------------------------------------------
#   Δy[0]  inner segment  range (-0.14,  0.00)   usually rises (negative = up)
#   Δy[1]  middle segment range (-0.04,  0.05)   can continue rising or start falling
#   Δy[2]  outer segment  range ( 0.02,  0.14)   usually descends back toward reference
#
#   → Classic arched brow : Δy ≈ (-0.12, +0.02, +0.10)  — rises then falls
#   → Straight / ascending: Δy ≈ (-0.04, -0.03, +0.07)  — gentle monotone slope
#   → Very arched          : Δy ≈ (-0.14, +0.04, +0.14)  — pronounced arch
#
# Genes used (via Genome.get_brow_*_gene):
#   dx gene    0–2 → Δx per segment  (normalised, sum forced to 1)
#   dy gene    0–2 → center-line Δy per segment
#   width gene 0–2 → half-width at keypoints 0, 1, 2  (keypoint 3 = tip = 0)
#   tension gene 0–2 → cubic bezier curviness per segment  (-1 … +1)
# =====================================================

NUM_SEGS      = 3
TENSION_RATIO = 0.25   # same convention as TenderEyes

CENTER_DY_RANGES = [
    (-0.14,  0.00),   # seg 0: inner portion — mostly rises
    (-0.04,  0.05),   # seg 1: arch peak region — can go either way
    ( 0.02,  0.14),   # seg 2: outer portion — mostly descends
]

# Half-width (± from center-line) at each keypoint.
# Keypoint 3 (outer tip) is always 0 — produces the pointed tail.
HALF_WIDTH_RANGES = [
    (0.08, 0.18),   # keypoint 0: inner end  (widest)
    (0.05, 0.12),   # keypoint 1: after seg 0
    (0.01, 0.05),   # keypoint 2: after seg 1
    # keypoint 3: 0  (always)
]


class TenderBrows:

    def __init__(self, genome=None):
        self.genome = genome if genome is not None else Genome()

    # =====================================================
    # GEOMETRY COMPUTATION
    # =====================================================

    def _lerp(self, a, b, t):
        return a + (b - a) * t

    def compute_dx(self):
        raw = [max(1, self.genome.get_brow_dx_gene(i)) for i in range(NUM_SEGS)]
        total = sum(raw)
        return [r / total for r in raw]

    def compute_center_dy(self):
        result = []
        for i in range(NUM_SEGS):
            norm = self.genome.get_brow_dy_gene(i) / 255.0
            lo, hi = CENTER_DY_RANGES[i]
            result.append(lo + norm * (hi - lo))
        return result

    def compute_half_widths(self):
        w = []
        for i in range(NUM_SEGS):   # 3 interior keypoints
            norm = self.genome.get_brow_width_gene(i) / 255.0
            lo, hi = HALF_WIDTH_RANGES[i]
            w.append(lo + norm * (hi - lo))
        w.append(0.0)               # outer tip always tapers to a point
        return w

    def compute_tensions(self):
        return [
            (self.genome.get_brow_tension_gene(i) / 127.5) - 1.0
            for i in range(NUM_SEGS)
        ]

    def get_half_widths(self):
        """Expose computed half-widths so TenderFace.py can query hw[0] for overlap clamping."""
        return self.compute_half_widths()

    # =====================================================
    # PATH BUILDING
    # =====================================================

    def generate_group(self):
        """
        Returns SVG markup for one eyebrow (filled shape + hidden ctrl-points group)
        in normalised (0–1) space.
        The caller (TenderFace.py) applies translate / scale / mirror transforms.
        """
        dx       = self.compute_dx()
        dy       = self.compute_center_dy()
        hw       = self.compute_half_widths()
        tensions = self.compute_tensions()

        # Accumulate center-line keypoints
        cx = [0.0]
        cy = [0.0]
        for i in range(NUM_SEGS):
            cx.append(cx[-1] + dx[i])
            cy.append(cy[-1] + dy[i])

        # --------------------------------------------------
        # Filled shape: upper edge (inner→outer) then lower edge (outer→inner)
        # --------------------------------------------------
        d = f"M {cx[0]:.4f} {cy[0] - hw[0]:.4f} "

        # Collect control-point coordinates for the visualization group
        cp_upper = []   # list of (c1, c2) tuples per segment, upper edge
        cp_lower = []   # same for lower edge
        cp_center = []  # center-line control points

        for i in range(NUM_SEGS):
            t           = tensions[i]
            ctrl_offset = t * dx[i] * TENSION_RATIO

            c1x = cx[i] + dx[i] * 0.25
            c1y_ctr = cy[i] + dy[i] * 0.25 + ctrl_offset

            c2x = cx[i] + dx[i] * 0.75
            c2y_ctr = cy[i] + dy[i] * 0.75 + ctrl_offset

            c1y_up  = c1y_ctr - self._lerp(hw[i], hw[i + 1], 0.25)
            c2y_up  = c2y_ctr - self._lerp(hw[i], hw[i + 1], 0.75)
            c1y_lo  = c1y_ctr + self._lerp(hw[i], hw[i + 1], 0.25)
            c2y_lo  = c2y_ctr + self._lerp(hw[i], hw[i + 1], 0.75)

            ex = cx[i + 1]
            ey = cy[i + 1] - hw[i + 1]

            d += f"C {c1x:.4f} {c1y_up:.4f} {c2x:.4f} {c2y_up:.4f} {ex:.4f} {ey:.4f} "

            cp_upper.append(((c1x, c1y_up),  (c2x, c2y_up)))
            cp_lower.append(((c1x, c1y_lo),  (c2x, c2y_lo)))
            cp_center.append(((c1x, c1y_ctr), (c2x, c2y_ctr)))

        # Lower edge: outer tip → inner (reversed cubics: swap c1↔c2)
        for i in range(NUM_SEGS - 1, -1, -1):
            (lc1x, lc1y), (lc2x, lc2y) = cp_lower[i]
            ex = cx[i]
            ey = cy[i] + hw[i]
            d += f"C {lc2x:.4f} {lc2y:.4f} {lc1x:.4f} {lc1y:.4f} {ex:.4f} {ey:.4f} "

        d += "Z"

        # --------------------------------------------------
        # Control-point visualization group
        # --------------------------------------------------
        r  = 0.025   # dot radius in normalised units
        sw = 0.005   # line stroke-width

        def dot(x, y, color="red"):
            return f'<circle cx="{x:.4f}" cy="{y:.4f}" r="{r}" fill="{color}" stroke="none"/>'

        def dash(x1, y1, x2, y2):
            return (f'<line x1="{x1:.4f}" y1="{y1:.4f}" x2="{x2:.4f}" y2="{y2:.4f}"'
                    f' stroke="red" stroke-width="{sw}" stroke-dasharray="0.04 0.02"/>')

        cp_svg = '<g class="ctrl-points" style="display:none">\n'

        for i in range(NUM_SEGS):
            (c1x, c1y_ctr), (c2x, c2y_ctr) = cp_center[i]

            # Dashed lines: keypoint → control point (center-line handles)
            cp_svg += dash(cx[i],     cy[i],     c1x, c1y_ctr)
            cp_svg += dash(cx[i + 1], cy[i + 1], c2x, c2y_ctr)

            # Blue center-line control point dots
            cp_svg += dot(c1x, c1y_ctr, "blue")
            cp_svg += dot(c2x, c2y_ctr, "blue")

        # Red anchor dots: center-line keypoints + upper/lower edge endpoints
        for i in range(NUM_SEGS + 1):
            cp_svg += dot(cx[i], cy[i])                  # center-line
            cp_svg += dot(cx[i], cy[i] - hw[i])          # upper edge
            if hw[i] > 0:                                 # skip tip (upper == lower)
                cp_svg += dot(cx[i], cy[i] + hw[i])      # lower edge

        cp_svg += '</g>'

        return f'<path d="{d}" fill="black" stroke="none"/>\n{cp_svg}'
