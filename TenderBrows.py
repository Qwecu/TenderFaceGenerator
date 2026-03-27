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
#   dx gene   0–2  → Δx per segment  (normalised, sum forced to 1)
#   dy gene   0–2  → center-line Δy per segment
#   width gene 0–2 → half-width at keypoints 0, 1, 2  (keypoint 3 = tip = 0)
#   tension gene 0–2 → cubic bezier curviness per segment  (-1 … +1)
# =====================================================

NUM_SEGS     = 3
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

    # =====================================================
    # PATH BUILDING
    # =====================================================

    def generate_group(self):
        """
        Returns SVG markup for one eyebrow filled shape in normalised (0–1) space.
        The caller (TenderFace.py) applies translate / scale / mirror transforms.
        """
        dx      = self.compute_dx()
        dy      = self.compute_center_dy()
        hw      = self.compute_half_widths()   # half-widths at 4 keypoints
        tensions = self.compute_tensions()

        # Accumulate center-line keypoints
        cx = [0.0]
        cy = [0.0]
        for i in range(NUM_SEGS):
            cx.append(cx[-1] + dx[i])
            cy.append(cy[-1] + dy[i])

        # --------------------------------------------------
        # Upper edge: inner (x=0) → outer tip (x=1)
        # --------------------------------------------------
        d = f"M {cx[0]:.4f} {cy[0] - hw[0]:.4f} "

        for i in range(NUM_SEGS):
            t            = tensions[i]
            ctrl_offset  = t * dx[i] * TENSION_RATIO

            c1x = cx[i] + dx[i] * 0.25
            c1y = (cy[i] + dy[i] * 0.25 + ctrl_offset
                   - self._lerp(hw[i], hw[i + 1], 0.25))

            c2x = cx[i] + dx[i] * 0.75
            c2y = (cy[i] + dy[i] * 0.75 + ctrl_offset
                   - self._lerp(hw[i], hw[i + 1], 0.75))

            ex  = cx[i + 1]
            ey  = cy[i + 1] - hw[i + 1]   # = cy[-1] when hw[-1] == 0

            d += f"C {c1x:.4f} {c1y:.4f} {c2x:.4f} {c2y:.4f} {ex:.4f} {ey:.4f} "

        # --------------------------------------------------
        # Lower edge: outer tip → inner, traversed in reverse.
        # Reversing a cubic  C CP1 CP2 P  →  C CP2 CP1 (start)
        # --------------------------------------------------
        for i in range(NUM_SEGS - 1, -1, -1):
            t            = tensions[i]
            ctrl_offset  = t * dx[i] * TENSION_RATIO

            # Control points in forward order, then swapped for the reverse pass
            lc1x = cx[i] + dx[i] * 0.25
            lc1y = (cy[i] + dy[i] * 0.25 + ctrl_offset
                    + self._lerp(hw[i], hw[i + 1], 0.25))

            lc2x = cx[i] + dx[i] * 0.75
            lc2y = (cy[i] + dy[i] * 0.75 + ctrl_offset
                    + self._lerp(hw[i], hw[i + 1], 0.75))

            ex   = cx[i]
            ey   = cy[i] + hw[i]

            # Reversed cubic: swap c1 ↔ c2
            d += f"C {lc2x:.4f} {lc2y:.4f} {lc1x:.4f} {lc1y:.4f} {ex:.4f} {ey:.4f} "

        d += "Z"

        return f'<path d="{d}" fill="black" stroke="none"/>'
