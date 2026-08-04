from genes import Genome

# =====================================================
# CONSTANTS  (mirrored in TenderFace.py for layout)
# =====================================================

FACE_HEIGHT = 120
HEAD_TOP    = 20

# =====================================================
# HEAD SHAPE GENES  (indices 120–133)
# =====================================================
# 120: face_width      max half-width as fraction of FACE_HEIGHT    (0.28–0.42)
# 121: fore_ratio      forehead width / max_hw                      (0.65–0.92)
# 122: cheek_ratio     cheekbone width / max_hw                     (0.88–1.06)
# 123: jaw_ratio       jaw-angle width / max_hw                     (0.50–0.90)
# 124: chin_floor_ratio chin-floor half-width / max_hw               (0.14–0.48)
# 125: cheek_y         cheekbone vertical position                  (0.28–0.48)
# 126: jaw_y           jaw-angle vertical position                  (0.60–0.78)
# 127: chin_y          chin tip vertical position                   (0.87–0.97)
# 128: temple_y        temple vertical position                     (0.08–0.22)
# 129: crown_arch      crown horizontal spread                      (0.30–0.85)
# 130: chin_curve      0 = pointed/sharp, 1 = round/flat            (0.0–1.0)
# 131: jaw_tension     jaw-angle sharpness (low=sharp, high=soft)   (0.25–0.55)
# 132: chin_body_ratio chin-body width / max_hw (always >= chin_tip)(0.28–0.65)
# 133: chin_body_y     chin-body y position between jaw and chin    (0.20–0.55)

GENE_BASE = 120


# =====================================================
# MINIMAL HEAD GENOME
# =====================================================

class MinimalHeadGenome:

    def __init__(self, genome=None):
        self.genome = genome if genome is not None else Genome(num_genes=200)

    # =====================================================
    # HELPERS
    # =====================================================

    def _g(self, offset, lo, hi):
        """Gene at GENE_BASE+offset mapped linearly into [lo, hi]."""
        return lo + (self.genome.get_gene(GENE_BASE + offset) / 255.0) * (hi - lo)

    def get_skin_color(self):
        return self.genome.get_skin_color()

    def get_half_width(self):
        """Actual computed half-width; used by TenderFace.py for layout."""
        return FACE_HEIGHT * self._g(0, 0.28, 0.42)

    def get_chin_region(self):
        """
        Returns (jaw_y, chin_body_y, jaw_w, chin_body_w) —
        the jaw and chin-body keypoint y-positions and half-widths —
        for mouth placement and width calculation.
        """
        max_hw       = self.get_half_width()
        jaw_y        = HEAD_TOP + FACE_HEIGHT * self._g(6, 0.60, 0.78)
        chin_y       = HEAD_TOP + FACE_HEIGHT * self._g(7, 0.87, 0.97)
        chin_body_y  = jaw_y + (chin_y - jaw_y) * self._g(13, 0.20, 0.55)
        jaw_w        = max_hw * self._g(3, 0.50, 0.90)
        chin_body_w  = max_hw * self._g(12, 0.28, 0.65)
        return jaw_y, chin_body_y, jaw_w, chin_body_w

    @staticmethod
    def _clamp_handles(handles, keypoints):
        """
        Clamp each control point to the bounding box of its segment's endpoints.
        Prevents bezier loops that arise when Catmull-Rom tangents overshoot on
        paths that reverse direction (e.g. cheekbone is the x-maximum, so the
        tangent there points inward and can push the arriving handle outside the
        face silhouette).
        """
        out = []
        for i, (c1, c2) in enumerate(handles):
            x0, y0 = keypoints[i]
            x1, y1 = keypoints[i + 1]
            xlo, xhi = min(x0, x1), max(x0, x1)
            ylo, yhi = min(y0, y1), max(y0, y1)
            out.append((
                (max(xlo, min(xhi, c1[0])), max(ylo, min(yhi, c1[1]))),
                (max(xlo, min(xhi, c2[0])), max(ylo, min(yhi, c2[1]))),
            ))
        return out

    @staticmethod
    def _catmull_cp(pts, tension=0.40):
        """
        Convert a polyline to cubic bezier control points using Catmull-Rom.
        Boundary ghosts use reflected endpoints so end tangents stay natural.
        Returns list of (c1, c2) per segment (len = len(pts) - 1).
        """
        n = len(pts)
        out = []
        for i in range(n - 1):
            p0 = pts[i]
            p1 = pts[i + 1]
            pm = pts[i - 1] if i > 0 else (2*p0[0] - p1[0], 2*p0[1] - p1[1])
            pn = pts[i + 2] if i + 2 < n else (2*p1[0] - p0[0], 2*p1[1] - p0[1])
            c1 = (p0[0] + (p1[0] - pm[0]) * tension,
                  p0[1] + (p1[1] - pm[1]) * tension)
            c2 = (p1[0] - (pn[0] - p0[0]) * tension,
                  p1[1] - (pn[1] - p0[1]) * tension)
            out.append((c1, c2))
        return out

    # =====================================================
    # GROUP GENERATION
    # =====================================================

    def generate_group(self):

        cx   = 65          # CENTER_X (matches TenderFace.py)
        ty   = HEAD_TOP
        skin = self.genome.get_skin_color()

        # ---- Gene-driven dimensions ----
        max_hw     = self.get_half_width()

        fore_w      = max_hw * self._g(1, 0.65, 0.92)   # forehead half-width
        cheek_w     = max_hw * self._g(2, 0.88, 1.06)   # cheekbone half-width (widest)
        jaw_w       = max_hw * self._g(3, 0.50, 0.90)   # jaw-angle half-width
        chin_body_w  = max_hw * self._g(12, 0.28, 0.65)  # chin body half-width
        chin_floor_w = min(chin_body_w,                  # floor <= body (always tapers)
                           max_hw * self._g(4, 0.14, 0.48))

        temple_y    = ty + FACE_HEIGHT * self._g(8,  0.08, 0.22)
        cheek_y     = ty + FACE_HEIGHT * self._g(5,  0.28, 0.48)
        jaw_y       = ty + FACE_HEIGHT * self._g(6,  0.60, 0.78)
        chin_y      = ty + FACE_HEIGHT * self._g(7,  0.87, 0.97)
        chin_body_y = jaw_y + (chin_y - jaw_y) * self._g(13, 0.20, 0.55)

        crown_arch  = self._g(9,  0.30, 0.85)
        chin_curve  = self._g(10, 0.0,  1.0)
        jaw_tension = self._g(11, 0.25, 0.55)

        # ---- Right-side keypoints (crown → chin, top-to-bottom) ----
        #   K[0]  crown       center top
        #   K[1]  temple      forehead edge
        #   K[2]  cheek       widest point
        #   K[3]  jaw         jaw angle
        #   K[4]  chin_body   chin block (maintains width before floor)
        #   K[5]  chin_floor  right chin floor corner  (left mirror added separately)
        K = [
            (cx,                ty),
            (cx + fore_w,       temple_y),
            (cx + cheek_w,      cheek_y),
            (cx + jaw_w,        jaw_y),
            (cx + chin_body_w,  chin_body_y),
            (cx + chin_floor_w, chin_y),
        ]

        # ---- Catmull-Rom handles, default tension ----
        H = self._catmull_cp(K, tension=0.40)

        # Override 1: Crown — force horizontal tangent so arch is smooth at top
        _c1, c2 = H[0]
        H[0] = ((cx + fore_w * crown_arch, ty), c2)

        # Override 2: Jaw segments — use jaw_tension for sharper or softer angle
        H_jaw = self._catmull_cp(K, tension=jaw_tension)
        H[2] = H_jaw[2]   # cheek → jaw arrival
        H[3] = H_jaw[3]   # jaw → chin_body departure

        # chin_curve controls the approach to the chin floor (H[4])
        # low = more angular descent, high = softer curve
        H_chin = self._catmull_cp(K, tension=0.25 + chin_curve * 0.30)
        H[4] = H_chin[4]

        # Clamp all handles to their segment bounding boxes — prevents loops
        H = self._clamp_handles(H, K)

        # After clamping, H[4]'s c2 can end up at K[5][0] (when chin_floor_w ≈
        # chin_body_w the Catmull tangent falls outside the bbox and gets clipped
        # to the edge, producing a nearly-vertical arrival at the chin floor).
        # Enforce a minimum horizontal clearance so the curve always arrives at
        # an angle.
        c1_4, c2_4 = H[4]
        h_gap = max(2.0, (chin_body_w - chin_floor_w) * 0.45)
        h_gap = min(h_gap, chin_body_w - chin_floor_w) if chin_body_w > chin_floor_w else 2.0
        H[4] = (c1_4, (max(c2_4[0], K[5][0] + h_gap), c2_4[1]))

        # ---- Build SVG path ----
        # Right half: K[0] → … → K[5] (chin floor right corner)
        d = f"M {cx:.2f} {ty:.2f} "
        for (c1, c2), (kx, ky) in zip(H, K[1:]):
            d += f"C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {kx:.2f} {ky:.2f} "

        # Curved chin bottom: bezier from right to left, dipping at centre
        # chin_curve=0 (pointed) → deeper dip; chin_curve=1 (round/flat) → shallower
        chin_drop = 1.5 + (1.0 - chin_curve) * 5.0
        d += (f"C {cx + chin_floor_w * 0.35:.2f} {chin_y + chin_drop:.2f} "
              f"  {cx - chin_floor_w * 0.35:.2f} {chin_y + chin_drop:.2f} "
              f"  {cx - chin_floor_w:.2f} {chin_y:.2f} ")

        # Left half: mirror and reverse — traverse K[4]→K[3]→…→K[0]
        # For segment K[i]→K[i+1] with handles (c1, c2):
        #   reversed & mirrored: C mirror(c2)  mirror(c1)  mirror(K[i])
        for i in range(len(H) - 1, -1, -1):
            c1, c2 = H[i]
            lkx = 2 * cx - K[i][0]
            lky = K[i][1]
            lc1 = (2 * cx - c2[0], c2[1])
            lc2 = (2 * cx - c1[0], c1[1])
            d += f"C {lc1[0]:.2f} {lc1[1]:.2f} {lc2[0]:.2f} {lc2[1]:.2f} {lkx:.2f} {lky:.2f} "

        d += "Z"

        # ---- Control-point visualization ----
        def pt(x, y, color="red"):
            return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2"'
                    f' fill="{color}" stroke="none"/>')

        def dline(x1, y1, x2, y2):
            return (f'<line x1="{x1:.1f}" y1="{y1:.1f}"'
                    f' x2="{x2:.1f}" y2="{y2:.1f}"'
                    f' stroke="red" stroke-width="0.5" stroke-dasharray="2 1"/>')

        pts_svg = '<g class="ctrl-points" style="display:none">\n'

        for i, ((c1, c2), (kx, ky)) in enumerate(zip(H, K[1:])):
            ax, ay = K[i]
            # Right-side handle lines + blue dots
            pts_svg += dline(ax, ay, c1[0], c1[1])
            pts_svg += dline(kx, ky, c2[0], c2[1])
            pts_svg += pt(c1[0], c1[1], "blue")
            pts_svg += pt(c2[0], c2[1], "blue")
            # Left-side (mirrored)
            lax = 2*cx - ax;  lkxm = 2*cx - kx
            lc1x = 2*cx - c1[0];  lc2x = 2*cx - c2[0]
            pts_svg += dline(lax, ay, lc1x, c1[1])
            pts_svg += dline(lkxm, ky, lc2x, c2[1])
            pts_svg += pt(lc1x, c1[1], "blue")
            pts_svg += pt(lc2x, c2[1], "blue")

        # Anchor dots (skip mirroring for center-axis points: crown and chin)
        for kx, ky in K:
            pts_svg += pt(kx, ky)
            if abs(kx - cx) > 0.5:
                pts_svg += pt(2*cx - kx, ky)

        pts_svg += '</g>\n'

        return (f'<path d="{d}"\n'
                f'      fill="rgb{skin}"\n'
                f'      stroke="black"\n'
                f'      stroke-width="0.5"/>\n'
                f'{pts_svg}')


# =====================================================
# HEAD GRID (for standalone testing)
# =====================================================

def generate_head_grid():

    COLS = 4
    ROWS = 4
    CELL_WIDTH  = 130
    CELL_HEIGHT = 160

    svg_content = ""
    for row in range(ROWS):
        for col in range(COLS):
            head = MinimalHeadGenome()
            tx = col * CELL_WIDTH
            ty = row * CELL_HEIGHT
            svg_content += (f'<g transform="translate({tx},{ty})">\n'
                            f'{head.generate_group()}\n</g>\n')

    total_w = COLS * CELL_WIDTH
    total_h = ROWS * CELL_HEIGHT
    return (f'<svg xmlns="http://www.w3.org/2000/svg"'
            f' viewBox="0 0 {total_w} {total_h}">\n'
            f'{svg_content}</svg>\n')


if __name__ == "__main__":
    svg_output = generate_head_grid()
    with open("genetic_head_grid.svg", "w") as f:
        f.write(svg_output)
    print("SVG created: genetic_head_grid.svg")
