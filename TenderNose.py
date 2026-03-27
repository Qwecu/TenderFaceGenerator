from genes import Genome


# =====================================================
# COORDINATE SYSTEM
# =====================================================
#
# Height-normalised, center-origin space:
#   y = 0    → top of nose (bridge, near eye level)
#   y = 1.0  → bottom of nose (arch level)
#   x = 0    → center of nose (axis of symmetry)
#   x > 0    → right side;   x < 0 → left side
#
# Placed in TenderFace via:
#   translate(CENTER_X, nose_top_y) scale(nose_h, nose_h)


# Gene indices used by the nose: 70 – 84
GENE_BASE = 70


# =====================================================
# TENDER NOSE
# =====================================================

class TenderNose:
    """
    Three-path nose matching the reference illustration style:

      Path 1 – left bridge+nostril outline
      Path 2 – right bridge+nostril outline (mirror of path 1)
      Path 3 – bottom arch connecting the two nostril bases

    Control point layout (left side shown; right is x-mirrored):

        y = 0              -bridge_x_top          ← top of bridge (narrowest)
                           -bridge_x_1             ← bridge width at y ≈ 0.25
        y = bridge_mid_y   -bridge_x_2             ← bridge width at y ≈ 0.50
        y = bridge_end_y   -bridge_x_3             ← bridge/nostril transition (widest bridge point)
                            ↘ flares outward
        y = ala_y          -ala_x                  ← nostril tip (widest overall)
                            ↙ curves back inward
        y = 1.0            -arch_end_x             ← base of nostril / arch endpoint

    Bottom arch (floating, decoupled from bridge endpoints):
        (-arch_span_x, arch_y) ── dips to center ── (arch_span_x, arch_y)
    """

    STROKE = 0.005   # stroke width in normalised coords (matches eye line weight at face scale)

    def __init__(self, genome=None):
        self.genome = genome if genome is not None else Genome(num_genes=200)

    def _gene(self, offset, lo, hi):
        """Map gene at GENE_BASE+offset linearly into [lo, hi]."""
        return lo + (self.genome.get_gene(GENE_BASE + offset) / 255.0) * (hi - lo)

    # =====================================================
    # CONTROL POINTS
    # =====================================================

    def get_control_points(self):
        """
        Returns all named control points as a dict.
        Values are in height-normalised, center-origin coords.

        Gene map:
          0  bridge_x_top    half-width at y = 0           (narrowest)
          1  bridge_x_1      half-width at y ≈ 0.25        (upper bridge)
          2  bridge_x_2      half-width at y ≈ 0.50        (mid bridge)
          3  bridge_x_3      half-width at bridge_end_y    (lower bridge)
          4  bridge_end_y    y where bridge transitions to nostril flare
          5  ala_x           half-width at nostril tip     (widest point)
          6  ala_y           y of the nostril tip
          7  arch_end_x      half-width of bridge P4 (stays at y=1.0)
          8  tip_dip         center-dip of the arch below ala_y
          9  arch_span_x     x half-span of the arch (independent of arch_end_x)
          (arch_y is derived: equals ala_y, so the arch sits on the same horizontal line as the ala tips)
        """
        return {
            # Bridge widths – each slightly wider than the one above
            'bridge_x_top': self._gene(0, 0.07, 0.14),   # y = 0
            'bridge_x_1':   self._gene(1, 0.09, 0.17),   # y ≈ 0.25
            'bridge_x_2':   self._gene(2, 0.12, 0.22),   # y ≈ 0.50
            'bridge_x_3':   self._gene(3, 0.16, 0.28),   # y = bridge_end_y

            # Where the bridge transitions into the nostril flare
            'bridge_end_y': self._gene(4, 0.50, 0.70),

            # Nostril tip (ala): outermost + lowest point of each bridge line
            'ala_x':        self._gene(5, 0.27, 0.43),
            'ala_y':        self._gene(6, 0.78, 0.93),

            # Bridge P4: where each bridge line terminates (stays at y=1.0)
            'arch_end_x':   self._gene(7, 0.14, 0.26),

            # Floating nose-tip arch — arch_y is derived as ala_y (same horizontal line)
            'tip_dip':      self._gene(8, 0.02, 0.06),   # center dip below ala_y
            'arch_span_x':  self._gene(9, 0.18, 0.32),   # x half-span of arch
        }

    # =====================================================
    # PATH BUILDERS
    # =====================================================

    @staticmethod
    def _f(x, y):
        """Format a coordinate pair."""
        return f"{x:.4f},{y:.4f}"

    def _bridge_path(self, cp, side):
        """
        Four-segment path for one bridge+nostril outline.

        side = +1 → right side (x positive)
        side = -1 → left side  (x negative)

        Segments:
          1. Bridge top  → bridge mid      (upper half of bridge, gradual widening)
          2. Bridge mid  → bridge end      (lower half of bridge, continues widening)
          3. Bridge end  → ala tip         (nostril flares outward)
          4. Ala tip     → arch endpoint   (nostril curves back inward to base)
        """
        s   = side
        f   = self._f

        bxt = cp['bridge_x_top']
        bx1 = cp['bridge_x_1']
        bx2 = cp['bridge_x_2']
        bx3 = cp['bridge_x_3']
        bey = cp['bridge_end_y']
        ax  = cp['ala_x']
        ay  = cp['ala_y']
        aex = cp['arch_end_x']

        # Derived y positions for the intermediate bridge widths
        bmy = bey * 0.50   # y of bridge_x_2 (midpoint of bridge)
        buy = bey * 0.25   # y of bridge_x_1 (quarter-point of bridge)

        # Anchor points — the curve passes through every one of these
        P0 = (s * bxt, 0.0)    # top of bridge
        PA = (s * bx1, buy)    # upper bridge width (now a true anchor, not just a handle)
        P1 = (s * bx2, bmy)    # mid bridge
        P2 = (s * bx3, bey)    # bridge end / nostril start
        P3 = (s * ax,  ay)     # ala tip (outermost point)
        P4 = (s * aex, 1.0)    # arch endpoint

        # --- Segment 1a: P0 → PA (bridge top to upper marker) ---
        s1a_c1 = (s * bxt, buy * 0.40)
        s1a_c2 = (s * bx1, buy * 0.70)

        # --- Segment 1b: PA → P1 (upper marker to bridge mid) ---
        s1b_c1 = (s * bx1, buy + (bmy - buy) * 0.30)
        s1b_c2 = (s * bx2, buy + (bmy - buy) * 0.70)

        # --- Segment 2: P1 → P2 (bridge mid to bridge end) ---
        s2_c1 = (s * bx2, bmy + (bey - bmy) * 0.30)
        s2_c2 = (s * bx3, bmy + (bey - bmy) * 0.70)

        # --- Segment 3: P2 → P3 (nostril flares outward toward ala) ---
        fh = ay - bey
        s3_c1 = (s * ax, bey + fh * 0.28)
        s3_c2 = (s * ax, bey + fh * 0.68)

        # --- Segment 4: P3 → P4 (nostril curves back inward to base) ---
        rh = 1.0 - ay
        s4_c1 = (s * (ax - (ax - aex) * 0.22), ay + rh * 0.30)
        s4_c2 = (s * aex,                       ay + rh * 0.70)

        return (
            f"M {f(*P0)} "
            f"C {f(*s1a_c1)} {f(*s1a_c2)} {f(*PA)} "
            f"C {f(*s1b_c1)} {f(*s1b_c2)} {f(*P1)} "
            f"C {f(*s2_c1)}  {f(*s2_c2)}  {f(*P2)} "
            f"C {f(*s3_c1)}  {f(*s3_c2)}  {f(*P3)} "
            f"C {f(*s4_c1)}  {f(*s4_c2)}  {f(*P4)}"
        )

    def _arch_path(self, cp):
        """
        Two symmetric cubic beziers forming the nose-tip arch.
        Floats at arch_y — fully decoupled from the bridge P4 endpoints.
        The two halves meet at (0, arch_y + tip_dip), a slight center dip
        that reads as the columella base.

        Left half:  (-arch_span_x, arch_y) → (0, arch_y + tip_dip)
        Right half: (0, arch_y + tip_dip)  → (arch_span_x, arch_y)
        """
        asx   = cp['arch_span_x']
        ay    = cp['ala_y']    # arch sits on the same horizontal line as the ala tips
        td    = cp['tip_dip']
        tip_y = ay + td

        f = self._f

        lc1 = (-asx * 0.45, ay + td * 0.5)
        lc2 = (-asx * 0.10, ay + td * 0.9)
        rc1 = ( asx * 0.10, ay + td * 0.9)
        rc2 = ( asx * 0.45, ay + td * 0.5)

        return (
            f"M {f(-asx, ay)} "
            f"C {f(*lc1)} {f(*lc2)} {f(0.0, tip_y)} "
            f"C {f(*rc1)} {f(*rc2)} {f(asx, ay)}"
        )

    # =====================================================
    # GROUP GENERATION
    # =====================================================

    def _ctrl_points_group(self, cp):
        """
        Hidden group (class="ctrl-points") showing all named anchor points.
        Toggled visible by the UI without regenerating the SVG.

        Red  = anchor points on the path
        Blue = y-level guide lines (show the horizontal slice at each bridge width)
        """
        bxt   = cp['bridge_x_top']
        bx1   = cp['bridge_x_1']
        bx2   = cp['bridge_x_2']
        bx3   = cp['bridge_x_3']
        bey   = cp['bridge_end_y']
        ax    = cp['ala_x']
        ala_y = cp['ala_y']
        aex   = cp['arch_end_x']
        arch_y = ala_y   # derived: arch sits on the ala horizontal line
        asx    = cp['arch_span_x']

        # Derived y positions matching _bridge_path()
        buy = bey * 0.25
        bmy = bey * 0.50

        r  = 0.030   # anchor point radius
        sw = 0.004   # guide line stroke

        def dot(x, y, color="red"):
            return f'<circle cx="{x:.4f}" cy="{y:.4f}" r="{r}" fill="{color}" stroke="none"/>'

        def hline(x, y):
            """Dashed horizontal guide between the two symmetric bridge points."""
            return (
                f'<line x1="{-x:.4f}" y1="{y:.4f}" x2="{x:.4f}" y2="{y:.4f}"'
                f' stroke="blue" stroke-width="{sw}" stroke-dasharray="0.03 0.02"/>'
            )

        return f"""
<g class="ctrl-points" style="display:none">
  <!-- y-level guide lines (blue dashes) -->
  {hline(bxt, 0.0)}
  {hline(bx1, buy)}
  {hline(bx2, bmy)}
  {hline(bx3, bey)}
  {hline(ax,  ala_y)}
  {hline(aex, 1.0)}
  {hline(asx, arch_y)}

  <!-- left anchor points -->
  {dot(-bxt, 0.0)}
  {dot(-bx1, buy)}
  {dot(-bx2, bmy)}
  {dot(-bx3, bey)}
  {dot(-ax,  ala_y)}
  {dot(-aex, 1.0)}
  {dot(-asx, arch_y)}

  <!-- right anchor points (mirrored) -->
  {dot(bxt, 0.0)}
  {dot(bx1, buy)}
  {dot(bx2, bmy)}
  {dot(bx3, bey)}
  {dot(ax,  ala_y)}
  {dot(aex, 1.0)}
  {dot(asx, arch_y)}
</g>"""

    def generate_group(self, max_bridge_x_top=None):
        cp = self.get_control_points()

        if max_bridge_x_top is not None:
            cp['bridge_x_top'] = min(cp['bridge_x_top'], max_bridge_x_top)
            # keep bridge widths monotonically non-decreasing
            cp['bridge_x_1'] = max(cp['bridge_x_1'], cp['bridge_x_top'])

        left_path  = self._bridge_path(cp, side=-1)
        right_path = self._bridge_path(cp, side=+1)
        arch_path  = self._arch_path(cp)
        ctrl_svg   = self._ctrl_points_group(cp)

        sw = self.STROKE
        attr = f'fill="none" stroke="black" stroke-width="{sw}" stroke-linecap="round"'

        return f"""
<!-- Left bridge + nostril -->
<path d="{left_path}"  {attr}/>

<!-- Right bridge + nostril -->
<path d="{right_path}" {attr}/>

<!-- Nose base arch -->
<path d="{arch_path}"  {attr}/>

{ctrl_svg}
"""
