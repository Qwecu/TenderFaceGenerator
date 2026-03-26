from genes import Genome


# =====================================================
# GLOBAL PARAMETERS
# =====================================================

# Coordinate system: height = 1.0, centered at x = 0.
# y = 0 is the top of the nose (bridge, near eye level).
# y = 1 is the ala / nostril level.
# x is symmetric: left side is negative, right side positive.
# The nose group is placed with translate(center_x, nose_top_y) scale(h, h).

# Gene indices used by nose (70–79)
GENE_BASE = 70


# =====================================================
# TENDER NOSE
# =====================================================

class TenderNose:

    def __init__(self, genome=None):
        self.genome = genome if genome is not None else Genome(num_genes=100)

    def _gene(self, offset):
        """Returns gene at GENE_BASE + offset, normalised to 0–1."""
        return self.genome.get_gene(GENE_BASE + offset) / 255.0

    # =====================================================
    # PATH CONSTRUCTION
    # =====================================================

    def build_bridge_line(self, bridge_x, ala_x, ctrl_top, ctrl_bot):
        """
        Left bridge line: flows from the narrow bridge at the top
        (−bridge_x, 0) outward and downward to the ala (−ala_x, 1.0).

        Two control points pull the curve outward, giving it the
        characteristic J / fishhook shape of the reference illustration.

        The right bridge line is obtained by mirroring around x=0.
        """
        return (
            f"M {-bridge_x:.4f} 0 "
            f"C {-bridge_x - ctrl_top:.4f} 0.30 "
            f"  {-ala_x - ctrl_bot:.4f} 0.72 "
            f"  {-ala_x:.4f} 1.0"
        )

    def build_bottom_arch(self, ala_x, arch_depth, arch_ctrl):
        """
        Shallow arch connecting the two ala points at y = 1.0.
        Bows slightly downward at center to suggest the rounded nose tip.
        """
        return (
            f"M {-ala_x:.4f} 1.0 "
            f"C {-ala_x + arch_ctrl:.4f} {1.0 + arch_depth:.4f} "
            f"  {ala_x - arch_ctrl:.4f} {1.0 + arch_depth:.4f} "
            f"  {ala_x:.4f} 1.0"
        )

    # =====================================================
    # GROUP GENERATION
    # =====================================================

    def generate_group(self):
        """
        Returns SVG group content in a height-normalised coordinate space
        (height = 1.0, centered at x = 0).

        Caller should apply:
            translate(center_x, nose_top_y) scale(nose_height_px, nose_height_px)
        """

        # --- Gene-driven parameters (all fractions of nose height) ---

        # Half-width of the bridge at the very top (narrow gap between lines)
        bridge_x   = 0.09 + self._gene(0) * 0.10   # 0.09 – 0.19

        # Half-width at the ala / nostril level (wider)
        ala_x      = 0.23 + self._gene(1) * 0.13   # 0.23 – 0.36

        # Outward pull of the upper control point
        ctrl_top   = 0.04 + self._gene(2) * 0.10   # 0.04 – 0.14

        # Outward pull of the lower control point (subtle extra flare)
        ctrl_bot   = 0.01 + self._gene(3) * 0.06   # 0.01 – 0.07

        # Downward depth of the bottom arch at center
        arch_depth = 0.03 + self._gene(4) * 0.07   # 0.03 – 0.10

        # Horizontal extent of the bottom arch control points
        arch_ctrl  = 0.12 + self._gene(5) * 0.14   # 0.12 – 0.26

        # Stroke width relative to nose height
        stroke_w   = 0.018 + self._gene(6) * 0.012  # 0.018 – 0.030

        bridge_path = self.build_bridge_line(bridge_x, ala_x, ctrl_top, ctrl_bot)
        arch_path   = self.build_bottom_arch(ala_x, arch_depth, arch_ctrl)

        return f"""
<!-- Left bridge line -->
<path d="{bridge_path}"
      fill="none" stroke="black" stroke-width="{stroke_w:.4f}"
      stroke-linecap="round"/>

<!-- Right bridge line (mirror) -->
<g transform="scale(-1,1)">
  <path d="{bridge_path}"
        fill="none" stroke="black" stroke-width="{stroke_w:.4f}"
        stroke-linecap="round"/>
</g>

<!-- Nose base arch -->
<path d="{arch_path}"
      fill="none" stroke="black" stroke-width="{stroke_w:.4f}"
      stroke-linecap="round"/>
"""
