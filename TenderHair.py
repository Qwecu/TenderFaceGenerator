from genes import Genome
from TenderHead import CENTER_X, VIEW_H

# Hair is the only part that reaches outside the head, so it is the only part
# that can leave the canvas — keep this much clear at the top and bottom.
CANVAS_MARGIN = 2.0


# =====================================================
# HAIR GENES  (indices 180–199)
# =====================================================
#  0 (180): darkness      black → platinum                       (dominant)
#  1 (181): warmth        ash ← → auburn/red                     (blended)
#  2 (182): hairline      how far down the forehead it starts    (0.15–0.85)
#  3 (183): peak          widow's peak depth / temple recession
#  4 (184): peak_sharp    0 = sharp V at centre, 1 = rounded arc
#  5 (185): volume        how far the mass puffs past the skull
#  6 (186): top_lift      height of the hair above the crown
#  7 (187): length        how far down the sides the mass hangs
#  8 (188): crown_arch    width of the dome's flat top
#  9 (189): bottom_curve  curve of the mass's lower edge
# 10 (190): side_flare    how much the mass widens towards the bottom
# 11–19 (191–199): spare
#
# Darkness is a true dominant: whichever allele is darker is the one that
# shows (get_gene_low_dominant), rather than the coin-flip that get_gene's
# random dominance value would give.  Two carriers therefore throw about
# 3 dark : 1 fair, which is visible directly in the parent/child view.
# Warmth blends instead, so auburn and ash average out.
#
# Shape invariants:
#   * the hairline always sits clear above the brows
#   * the hair mass always encloses the skull it sits on, following the real
#     head silhouette via half_width_at() rather than a fixed oval
#   * the dome apex keeps a horizontal tangent, so the crown is never a spike

GENE_BASE = 180

HAIR_PALETTE = [
    (24,  19,  18),    # black
    (56,  37,  28),    # dark brown
    (92,  58,  34),    # brown
    (134, 86,  44),    # light brown
    (178, 132, 66),    # dark blonde
    (216, 178, 108),   # blonde
    (238, 219, 172),   # platinum
]


def _clamp255(v):
    return max(0, min(255, int(v)))


class TenderHair:
    """
    Hair drawn as two pieces that sandwich the head:

        back  — the full mass, drawn BEHIND the head.  Only its outer rim,
                its dome above the crown and the lengths falling beside the
                face are visible; the head hides the rest.
        front — the cap over the top of the skull, drawn ON TOP of the head
                and bounded below by the hairline.

    Both share the same outer silhouette, so together they read as one shape
    with the face showing through below the hairline.
    """

    def __init__(self, genome=None):
        self.genome = genome if genome is not None else Genome(num_genes=200)
        self._geo = None

    # =====================================================
    # GENE HELPERS
    # =====================================================

    def _g(self, offset, lo, hi):
        """Gene at GENE_BASE+offset mapped linearly into [lo, hi]."""
        return lo + (self.genome.get_gene(GENE_BASE + offset) / 255.0) * (hi - lo)

    def get_hair_color(self):
        """
        Hair colour interpolated across HAIR_PALETTE, then shifted by warmth.

        Darkness takes the darker of the two alleles.  That is what makes dark
        hair dominant, but it also piles the population up at the dark end —
        the minimum of two draws has density 2(1-t), so nearly half of all
        faces come out black.  The exponent spreads the expressed colour back
        across the palette while leaving the inheritance untouched: the
        mapping is monotonic, so a dark allele still reads dark.
        """
        t = (self.genome.get_gene_low_dominant(GENE_BASE) / 255.0) ** 0.55
        t *= (len(HAIR_PALETTE) - 1)

        i0 = int(t)
        i1 = min(i0 + 1, len(HAIR_PALETTE) - 1)
        f  = t - i0

        r0, g0, b0 = HAIR_PALETTE[i0]
        r1, g1, b1 = HAIR_PALETTE[i1]
        r = r0 + (r1 - r0) * f
        g = g0 + (g1 - g0) * f
        b = b0 + (b1 - b0) * f

        # Warmth blends across both chromosomes: +red / -blue is auburn,
        # the reverse is ash.
        w = (self.genome.get_gene_avg(GENE_BASE + 1) / 255.0) - 0.5
        return (_clamp255(r + w * 48), _clamp255(g + w * 6), _clamp255(b - w * 30))

    # =====================================================
    # GEOMETRY
    # =====================================================

    def geometry(self, head, brow_top_y):
        """
        Resolve the hair outline against a specific head.

        `brow_top_y` is the topmost pixel the brows reach; the hairline is
        kept clear above it so hair never grows into the eyebrows.

        The dome is the SKULL'S OWN outline, widened about the centre line and
        stretched upward about the hairline.  Sampling the skull at a few fixed
        heights instead draws a cone: just below the crown the head is still
        very narrow, so the hair runs to a point there and only flares lower
        down.  Borrowing the skull's curve means the hair domes exactly as the
        head does, whatever shape that head is.
        """
        if self._geo is not None:
            return self._geo

        hg       = head.geometry()
        cx       = CENTER_X
        head_top = hg['head_top']
        chin_y   = hg['chin_y']
        cheek_y  = hg['cheek_y']
        jaw_y    = hg['jaw_y']
        max_hw   = hg['max_hw']
        head_h   = chin_y - head_top

        swell    = self._g(5, 1.07, 1.22)      # how far the mass sits proud
        top_lift = max_hw * self._g(6, 0.06, 0.30)
        flare    = self._g(10, 0.0, 0.22)

        # ---- Hairline, always clear of the brows ----
        # The centre dip is sized FIRST and its room reserved, then the
        # hairline is placed in what is left.  Choosing the line first and
        # clamping the dip afterwards flattens it to nothing on every face
        # whose hairline happens to sit low — which is what makes a hairline
        # read as a ruler-straight wig edge.
        hl_lo   = head_top + head_h * 0.10
        hl_roof = brow_top_y - head_h * 0.05

        peak = max_hw * self._g(3, 0.12, 0.45)
        peak = max(0.0, min(peak, (hl_roof - hl_lo) * 0.45))

        hl_hi = hl_roof - peak
        hairline_y = hl_lo + max(0.0, hl_hi - hl_lo) * self._g(2, 0.15, 0.85)

        y_top = max(CANVAS_MARGIN, head_top - top_lift)
        # Vertical stretch that pins the hairline and lifts the crown to y_top.
        sy = (y_top - hairline_y) / (head_top - hairline_y)

        # ---- Right-hand outer boundary, apex → hairline → length ----
        top_pts = []
        STEPS = 26
        for i in range(STEPS + 1):
            ys = head_top + (hairline_y - head_top) * (i / STEPS)
            w  = head.half_width_at(ys)
            top_pts.append((cx + w * swell,
                            hairline_y + (ys - hairline_y) * sy))

        # Short end sits around the top of the ear (a crop showing plenty of
        # cheek); long end falls past the chin.
        hair_top_end = head_top + head_h * 0.30
        hair_bottom  = hair_top_end + self._g(7, 0.0, 1.0) * (
            (chin_y + head_h * 0.12) - hair_top_end)

        # The lower edge bulges below hair_bottom, so its depth comes out of
        # the canvas budget before the length is clamped.
        bulge = max_hw * self._g(9, 0.06, 0.42)
        hair_bottom = min(hair_bottom, VIEW_H - CANVAS_MARGIN - bulge)

        # A high hairline can otherwise sit BELOW where the mass stops, which
        # runs the sides upward and hangs two tabs off the cap.
        hair_bottom = max(hair_bottom, hairline_y + head_h * 0.10)

        # Below the jaw the head tapers sharply to the chin.  Hair does not
        # follow that in, but holding it at a fixed jaw width instead draws
        # parallel vertical sides and a flat base — a helmet.  Hold most of
        # the width, then let it draw gradually inwards.
        w_jaw = head.half_width_at(jaw_y)
        side_pts = []
        SIDE = 14
        for i in range(1, SIDE + 1):
            t = i / SIDE
            y = hairline_y + (hair_bottom - hairline_y) * t
            w = head.half_width_at(y)
            if y > jaw_y:
                below = (y - jaw_y) / max(hair_bottom - jaw_y, 1e-6)
                w = max(w, w_jaw * (0.94 - 0.30 * below))

            # Over the last third the mass tucks back inside the face edge.
            # Left proud, the bottom corner juts out past the cheek and stops
            # dead, hanging a squared-off tab on the side of the head; tucked
            # in, the mass is drawn behind the head and the corner simply
            # disappears.  Below the jaw `w` is held near jaw width, so long
            # hair still falls clear of the chin.
            s = swell + flare * t
            if t > 0.65:
                u = (t - 0.65) / 0.35
                s = s * (1.0 - u) + 0.97 * u
            side_pts.append((cx + w * s, y))

        self._geo = {
            'cx': cx, 'y_top': y_top, 'hairline_y': hairline_y, 'peak': peak,
            'hair_bottom': hair_bottom, 'max_hw': max_hw,
            'top_pts': top_pts, 'side_pts': side_pts,
            'peak_sharp': self._g(4, 0.0, 1.0),
            # Always bulges downward — a straight lower edge reads as a cut-out.
            'bulge': bulge,
        }
        return self._geo

    # =====================================================
    # PATH BUILDING
    # =====================================================

    @staticmethod
    def _down_right(pts):
        """Trace the sampled right-hand boundary downward."""
        return "".join(f"L {x:.2f} {y:.2f} " for x, y in pts)

    @staticmethod
    def _up_left(pts, cx):
        """The same boundary mirrored and reversed, running back to the apex."""
        return "".join(f"L {2*cx - x:.2f} {y:.2f} "
                       for x, y in reversed(pts))

    def _hairline_path(self, g):
        """
        Hairline traversed right → centre → left.

        peak_sharp collapses the centre-side control point onto the centre
        point, turning the smooth arch into a cusp — a widow's peak.
        """
        cx     = g['cx']
        y      = g['hairline_y']
        peak   = g['peak']
        smooth = 1.0 - g['peak_sharp']
        hx     = g['top_pts'][-1][0] - cx      # half span at hairline level

        # Only the middle of this span is visible — the ends run out past the
        # face — so the curve has to descend across its whole width rather
        # than staying level and dimpling at the last moment.
        return (
            f"C {cx + hx * 0.62:.2f} {y + peak * 0.32:.2f} "
            f"  {cx + hx * 0.24 * smooth:.2f} {y + peak:.2f} "
            f"  {cx:.2f} {y + peak:.2f} "
            f"C {cx - hx * 0.24 * smooth:.2f} {y + peak:.2f} "
            f"  {cx - hx * 0.62:.2f} {y + peak * 0.32:.2f} "
            f"  {cx - hx:.2f} {y:.2f} "
        )

    def _style(self, color):
        return (f'fill="rgb{color}" stroke="black" stroke-width="0.5"'
                f' stroke-linejoin="round"')

    # =====================================================
    # THE TWO LAYERS
    # =====================================================

    def generate_back(self, head, brow_top_y):
        """The full hair mass — draw this BEFORE the head."""
        g    = self.geometry(head, brow_top_y)
        cx   = g['cx']
        side = g['top_pts'] + g['side_pts']

        bx, by = side[-1]
        bulge  = g['bulge']

        d  = f"M {cx:.2f} {g['y_top']:.2f} "
        d += self._down_right(side)
        # Lower edge, swept across to the mirrored corner.
        d += (f"C {cx + (bx - cx) * 0.45:.2f} {by + bulge:.2f} "
              f"  {cx - (bx - cx) * 0.45:.2f} {by + bulge:.2f} "
              f"  {2*cx - bx:.2f} {by:.2f} ")
        d += self._up_left(side, cx)
        d += "Z"

        return f'<path d="{d}" {self._style(self.get_hair_color())}/>'

    def generate_front(self, head, brow_top_y):
        """The cap over the skull, cut off at the hairline — draw AFTER the head."""
        g  = self.geometry(head, brow_top_y)
        cx = g['cx']

        d  = f"M {cx:.2f} {g['y_top']:.2f} "
        d += self._down_right(g['top_pts'])
        d += self._hairline_path(g)
        d += self._up_left(g['top_pts'], cx)
        d += "Z"

        return (f'<path d="{d}" {self._style(self.get_hair_color())}/>\n'
                f'{self._ctrl_points_group(g)}')

    # =====================================================
    # CONTROL-POINT VISUALIZATION
    # =====================================================

    def _ctrl_points_group(self, g):
        cx = g['cx']

        def pt(x, y, color="red"):
            return (f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2"'
                    f' fill="{color}" stroke="none"/>')

        out = '<g class="ctrl-points" style="display:none">\n'
        for kx, ky in (g['top_pts'][::6] + g['side_pts'][::4]):
            out += pt(kx, ky)
            if abs(kx - cx) > 0.5:
                out += pt(2 * cx - kx, ky)
        out += pt(cx, g['y_top'])
        out += pt(cx, g['hairline_y'] + g['peak'], "blue")
        return out + '</g>\n'
