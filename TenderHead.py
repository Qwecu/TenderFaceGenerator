from genes import Genome

# =====================================================
# VIEWPORT
# =====================================================

VIEW_W   = 130
VIEW_H   = 160
CENTER_X = 65

# Head height and vertical origin are gene-driven per face — see geometry().
# There is deliberately no FACE_HEIGHT / HEAD_TOP constant: every face has its
# own, and a fixed one here would only invite callers to assume otherwise.

# =====================================================
# HEAD SHAPE GENES  (indices 120–139)
# =====================================================
#  0 (120): hw_ratio         cheek half-width / face_height        (0.300–0.385)
#  1 (121): fore_ratio       forehead width / cheek width          (0.62–0.95)
#  2 (122): cheek_y          cheekbone vertical position           (0.30–0.46)
#  3 (123): jaw_ratio        jaw-angle width / cheek width         (0.56–0.92)
#  4 (124): chin_floor_ratio chin-floor width / chin-body width    (0.52–0.82)
#  5 (125): temple_y         temple vertical position              (0.09–0.21)
#  6 (126): jaw_y            jaw-angle vertical position           (0.62–0.74)
#  7 (127): chin_drop        chin tip BELOW the jaw, frac of len   (0.16–0.26)
#  8 (128): crown_arch       crown horizontal spread               (0.30–0.85)
#  9 (129): chin_curve       0 = pointed/sharp, 1 = round/flat     (0.0–1.0)
# 10 (130): jaw_tension      jaw-angle sharpness                   (0.22–0.55)
# 11 (131): chin_body_ratio  chin-body width / JAW width           (0.62–0.88)
# 12 (132): chin_body_y      chin-body y between jaw and chin      (0.32–0.58)
# 13 (133): face_length      overall head height in px             (106–134)
# 14 (134): cheek_fullness   cheekbone curve tension               (0.30–0.55)
# 15–19 (135–139): spare
#
# Shape invariants enforced below (these are what keep silhouettes plausible):
#   * the cheekbone is always the widest point of the head
#   * width tapers monotonically from cheek → jaw → chin_body → chin_floor,
#     and each step is a bounded fraction of the step above it, so the lower
#     face can never pinch in abruptly
#   * keypoint y-positions are strictly ordered crown < temple < cheek < jaw
#     < chin_body < chin
#   * the chin's length is tied to how far it narrows: a chin that pulls
#     sharply inward is kept short, since narrow AND long is the shape that
#     reads as a lobe dangling off the jaw
#   * width and length are loosely coupled, so the head can be long-narrow or
#     short-wide but never a sliver or a pancake

GENE_BASE = 120


# =====================================================
# CURVE HELPERS  (shared with TenderHair)
# =====================================================

def clamp_handles(handles, keypoints):
    """Clamp each control point to the bounding box of its segment."""
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


def catmull_rom_handles(pts, tension=0.40):
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


def bezier_point(p0, c1, c2, p1, t):
    """Evaluate a cubic bezier at parameter t."""
    mt = 1.0 - t
    a, b = mt * mt * mt, 3 * mt * mt * t
    c, d = 3 * mt * t * t, t * t * t
    return (a * p0[0] + b * c1[0] + c * c2[0] + d * p1[0],
            a * p0[1] + b * c1[1] + c * c2[1] + d * p1[1])


def path_from_handles(K, H, close=False):
    """Serialise keypoints + Catmull-Rom handles into an SVG path string."""
    d = f"M {K[0][0]:.2f} {K[0][1]:.2f} "
    for (c1, c2), (kx, ky) in zip(H, K[1:]):
        d += f"C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {kx:.2f} {ky:.2f} "
    return d + ("Z" if close else "")


# =====================================================
# MINIMAL HEAD GENOME
# =====================================================

class MinimalHeadGenome:

    def __init__(self, genome=None):
        self.genome = genome if genome is not None else Genome(num_genes=200)
        self._geo = None

    # =====================================================
    # HELPERS
    # =====================================================

    def _g(self, offset, lo, hi):
        """Gene at GENE_BASE+offset mapped linearly into [lo, hi]."""
        return lo + (self.genome.get_gene(GENE_BASE + offset) / 255.0) * (hi - lo)

    def get_skin_color(self):
        return self.genome.get_skin_color()

    # =====================================================
    # GEOMETRY  (computed once, cached)
    # =====================================================

    def geometry(self):
        """
        All head geometry in one dict, computed once per genome.

        Keys:
            face_height, head_top, chin_y, max_hw   — overall metrics
            K, H                                    — keypoints + bezier handles
            profile                                 — sampled right-side outline
            jaw_y, chin_body_y, jaw_w, chin_body_w  — lower-face anchors
            temple_y, cheek_y, fore_w, cheek_w      — upper-face anchors
        """
        if self._geo is not None:
            return self._geo

        cx = CENTER_X

        # ---- Overall size: length and width vary semi-independently ----
        # hw_ratio keeps the aspect inside the plausible human band
        # (head width / head height lands roughly in 0.60–0.77).
        face_height = self._g(13, 106.0, 134.0)
        head_top    = (VIEW_H - face_height) / 2.0
        max_hw      = face_height * self._g(0, 0.300, 0.385)

        # ---- Widths: the cheek is the widest point, everything tapers ----
        cheek_w = max_hw
        fore_w  = max_hw * self._g(1, 0.62, 0.95)
        # A very narrow jaw under a wide cheek funnels the lower face into a
        # spout, so the jaw keeps a decent share of the cheek width.
        jaw_w   = max_hw * self._g(3, 0.56, 0.92)

        # Chin body never bulges past the jaw — that bulge is what reads as a
        # lumpy, deformed lower face.
        # The chin body tapers from the JAW, not from the cheek.  Measured
        # against the cheek it can land at a third of the cheek width while
        # the jaw is still at nine tenths, necking the face in over one short
        # step and leaving the chin hanging below as a separate lobe.
        # The absolute floor keeps enough width for the mouth to sit on.
        chin_body_w = jaw_w * self._g(11, 0.62, 0.88)
        chin_body_w = min(jaw_w * 0.95, max(chin_body_w, max_hw * 0.32))

        # The chin floor is a fraction of the chin body, never merely a hair
        # narrower.  Two nearly-equal widths stacked vertically draw a pair of
        # parallel sides ending in a flat edge, which reads as a neck stump
        # rather than a chin.
        chin_floor_w = chin_body_w * self._g(4, 0.52, 0.82)

        # ---- Vertical anchors (ranges are disjoint, so order is guaranteed) ----
        temple_y = head_top + face_height * self._g(5, 0.09, 0.21)
        cheek_y  = head_top + face_height * self._g(2, 0.30, 0.46)
        jaw_y    = head_top + face_height * self._g(6, 0.62, 0.74)

        # The chin is measured DOWN FROM THE JAW, not from the crown.  Setting
        # both independently lets a low jaw and a low chin compound into a chin
        # that dangles a third of the face below the jawline.
        #
        # Length is also tied to how much the chin narrows: a chin that pulls
        # sharply inward AND runs long is exactly the shape that reads as a
        # lobe hanging off the jaw, so the more it narrows the shorter it runs.
        narrowing  = 1.0 - chin_floor_w / jaw_w
        chin_drop  = self._g(7, 0.16, 0.26) * (1.0 - narrowing * 0.45)
        chin_y     = jaw_y + face_height * chin_drop
        chin_y     = max(head_top + face_height * 0.86,
                         min(chin_y, head_top + face_height * 0.98))

        # The chin body sits nearer the middle of the jaw-to-chin span.  Placed
        # right under the jaw it applies the narrow chin width for the whole
        # drop, which is the other half of the hanging-lobe shape.
        chin_body_y = jaw_y + (chin_y - jaw_y) * self._g(12, 0.32, 0.58)

        crown_arch     = self._g(8,  0.30, 0.85)
        chin_curve     = self._g(9,  0.0,  1.0)
        jaw_tension    = self._g(10, 0.22, 0.55)
        cheek_fullness = self._g(14, 0.30, 0.55)

        # ---- Right-side keypoints (crown → chin, top to bottom) ----
        #   K[0] crown  K[1] temple  K[2] cheek  K[3] jaw
        #   K[4] chin_body  K[5] chin_floor
        K = [
            (cx,                head_top),
            (cx + fore_w,       temple_y),
            (cx + cheek_w,      cheek_y),
            (cx + jaw_w,        jaw_y),
            (cx + chin_body_w,  chin_body_y),
            (cx + chin_floor_w, chin_y),
        ]

        H = catmull_rom_handles(K, tension=0.40)

        # Crown: force a horizontal tangent so the top of the skull is a dome
        # rather than a peak.
        H[0] = ((cx + fore_w * crown_arch, head_top), H[0][1])

        # Cheek approach / departure — controls round vs. angular cheekbones.
        H_cheek = catmull_rom_handles(K, tension=cheek_fullness)
        H[1] = H_cheek[1]

        # Jaw segments — sharper or softer jaw angle.
        H_jaw = catmull_rom_handles(K, tension=jaw_tension)
        H[2] = H_jaw[2]   # cheek → jaw arrival
        H[3] = H_jaw[3]   # jaw → chin_body departure

        # Chin approach.
        H_chin = catmull_rom_handles(K, tension=0.25 + chin_curve * 0.30)
        H[4] = H_chin[4]

        # Clamp handles to their segment bounding boxes — prevents bezier loops
        # where the path reverses direction (the cheek is an x-maximum, so its
        # tangent points inward and can otherwise push a handle outside the
        # silhouette).
        H = clamp_handles(H, K)

        # Clamping can drop H[4]'s c2 onto K[5]'s x, which makes the outline
        # arrive at the chin floor vertically and reads as a hard corner.
        # Force a minimum horizontal clearance.
        c1_4, c2_4 = H[4]
        span  = chin_body_w - chin_floor_w
        h_gap = min(max(2.0, span * 0.45), span) if span > 0 else 2.0
        H[4]  = (c1_4, (max(c2_4[0], K[5][0] + h_gap), c2_4[1]))

        self._geo = {
            'face_height': face_height,
            'head_top':    head_top,
            'max_hw':      max_hw,
            'cx':          cx,
            'K': K, 'H': H,
            'fore_w': fore_w, 'cheek_w': cheek_w, 'jaw_w': jaw_w,
            'chin_body_w': chin_body_w, 'chin_floor_w': chin_floor_w,
            'temple_y': temple_y, 'cheek_y': cheek_y, 'jaw_y': jaw_y,
            'chin_body_y': chin_body_y, 'chin_y': chin_y,
            'chin_curve': chin_curve,
            'profile': self._build_profile(K, H),
        }
        return self._geo

    # =====================================================
    # SILHOUETTE SAMPLING
    # =====================================================

    @staticmethod
    def _build_profile(K, H, steps=28):
        """
        Sample the right-hand outline into a list of (x, y) with y ascending.

        Handles are clamped to their segment bounding boxes, so y is already
        monotonic; the running max below is belt-and-braces so the binary
        search in half_width_at() can never misbehave.
        """
        prof = []
        for i, (c1, c2) in enumerate(H):
            p0, p1 = K[i], K[i + 1]
            for s in range(steps + 1):
                if i > 0 and s == 0:
                    continue            # skip the duplicated segment join
                prof.append(bezier_point(p0, c1, c2, p1, s / steps))

        out, ymax = [], prof[0][1]
        for x, y in prof:
            ymax = max(ymax, y)
            out.append((x, ymax))
        return out

    def half_width_at(self, y):
        """
        Half-width of the actual head silhouette at height y.

        This is what lets the face layout guarantee that eyes, brows and mouth
        sit inside the outline instead of estimating from keypoints and hoping.
        """
        prof = self.geometry()['profile']
        cx   = CENTER_X

        if y <= prof[0][1]:
            return max(0.0, prof[0][0] - cx)
        if y >= prof[-1][1]:
            return max(0.0, prof[-1][0] - cx)

        lo, hi = 0, len(prof) - 1
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if prof[mid][1] <= y:
                lo = mid
            else:
                hi = mid

        (x0, y0), (x1, y1) = prof[lo], prof[hi]
        u = 0.0 if y1 == y0 else (y - y0) / (y1 - y0)
        return max(0.0, (x0 + (x1 - x0) * u) - cx)

    def get_half_width(self):
        """Widest half-width of the head (at the cheekbone)."""
        return self.geometry()['max_hw']

    # =====================================================
    # GROUP GENERATION
    # =====================================================

    def generate_group(self):

        g    = self.geometry()
        cx   = g['cx']
        K, H = g['K'], g['H']
        skin = self.genome.get_skin_color()

        chin_floor_w = g['chin_floor_w']
        chin_y       = g['chin_y']
        max_hw       = g['max_hw']

        # ---- Right half: crown → chin floor ----
        d = f"M {cx:.2f} {g['head_top']:.2f} "
        for (c1, c2), (kx, ky) in zip(H, K[1:]):
            d += f"C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {kx:.2f} {ky:.2f} "

        # ---- Chin bottom: a curve, scaled to the CHIN's own width ----
        # chin_curve = 0 → pointed (deeper dip);  1 → round/flat (shallow).
        # Scaling this to head width instead gives a narrow chin a deep drop,
        # which draws a pendulous teardrop spout hanging off the jaw.
        chin_drop = chin_floor_w * (0.25 + (1.0 - g['chin_curve']) * 0.45)
        d += (f"C {cx + chin_floor_w * 0.35:.2f} {chin_y + chin_drop:.2f} "
              f"  {cx - chin_floor_w * 0.35:.2f} {chin_y + chin_drop:.2f} "
              f"  {cx - chin_floor_w:.2f} {chin_y:.2f} ")

        # ---- Left half: mirror and reverse ----
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
            pts_svg += dline(ax, ay, c1[0], c1[1])
            pts_svg += dline(kx, ky, c2[0], c2[1])
            pts_svg += pt(c1[0], c1[1], "blue")
            pts_svg += pt(c2[0], c2[1], "blue")
            lax = 2*cx - ax;  lkxm = 2*cx - kx
            lc1x = 2*cx - c1[0];  lc2x = 2*cx - c2[0]
            pts_svg += dline(lax, ay, lc1x, c1[1])
            pts_svg += dline(lkxm, ky, lc2x, c2[1])
            pts_svg += pt(lc1x, c1[1], "blue")
            pts_svg += pt(lc2x, c2[1], "blue")

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
    CELL_WIDTH  = VIEW_W
    CELL_HEIGHT = VIEW_H

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
