from genes import Genome


# =====================================================
# GLOBAL PARAMETERS
# =====================================================

MOUTH_WIDTH = 100
# Base coordinate space width (normalized to 1.0 via normalize=True).

# Gene indices used by mouth (60–69, safely away from eye/skin genes)
GENE_BASE = 60


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
        """
        Derives lip color from the shared skin color.
        Lips are warmer and slightly darker than the surrounding skin.
        """
        r, g, b = self.genome.get_skin_color()
        lr = min(255, int(r * 0.92 + 28))
        lg = max(0,   int(g * 0.78))
        lb = max(0,   int(b * 0.78))
        return (lr, lg, lb)

    # =====================================================
    # PATH CONSTRUCTION
    # =====================================================

    def build_upper_lip(self, w, bow_h, valley_h, bow_x, ctrl):
        """
        Builds a closed path for the upper lip (Cupid's bow).

        Key points (y is negative = upward on screen):
          left corner  (0, 0)
          left peak    (bow_x * w, -bow_h)
          center valley (w/2, -valley_h)   where valley_h < bow_h
          right peak   ((1-bow_x) * w, -bow_h)
          right corner (w, 0)

        Closes back along y=0 (the mouth line).
        """
        cx      = w * 0.5
        lp_x    = w * bow_x          # left bow peak x
        rp_x    = w * (1 - bow_x)    # right bow peak x

        # Corner → left peak
        # Start going right and up; arrive horizontally at peak
        seg1 = (
            f"C {ctrl:.4f} {-bow_h * 0.5:.4f} "
            f"{lp_x - ctrl:.4f} {-bow_h:.4f} "
            f"{lp_x:.4f} {-bow_h:.4f} "
        )

        # Left peak → center valley
        # Leave peak horizontally; arrive at valley
        seg2 = (
            f"C {lp_x + ctrl:.4f} {-bow_h:.4f} "
            f"{cx - ctrl:.4f} {-valley_h:.4f} "
            f"{cx:.4f} {-valley_h:.4f} "
        )

        # Center valley → right peak (mirror of seg2)
        seg3 = (
            f"C {cx + ctrl:.4f} {-valley_h:.4f} "
            f"{rp_x - ctrl:.4f} {-bow_h:.4f} "
            f"{rp_x:.4f} {-bow_h:.4f} "
        )

        # Right peak → right corner (mirror of seg1)
        seg4 = (
            f"C {rp_x + ctrl:.4f} {-bow_h:.4f} "
            f"{w - ctrl:.4f} {-bow_h * 0.5:.4f} "
            f"{w:.4f} 0 "
        )

        return f"M 0 0 {seg1}{seg2}{seg3}{seg4}Z"

    def build_lower_lip(self, w, lower_h, ctrl):
        """
        Builds a closed path for the lower lip (single arc).
        Closes back along y=0.
        """
        return (
            f"M 0 0 "
            f"C {ctrl:.4f} {lower_h:.4f} "
            f"{w - ctrl:.4f} {lower_h:.4f} "
            f"{w:.4f} 0 Z"
        )

    # =====================================================
    # GROUP GENERATION
    # =====================================================

    def generate_group(self, normalize=False):

        w = 1.0 if normalize else MOUTH_WIDTH

        # --- Gene-driven parameters ---

        # Cupid's bow height (relative to w)
        bow_h    = w * (0.10 + self._gene(0) * 0.12)

        # Center valley height — always shallower than the bow peaks
        valley_h = bow_h * (0.20 + self._gene(1) * 0.50)

        # Lower lip depth
        lower_h  = w * (0.09 + self._gene(2) * 0.13)

        # Bow peak x position as fraction of w (0.22–0.38)
        bow_x    = 0.22 + self._gene(3) * 0.16

        # Horizontal control point offset — controls lip fullness
        ctrl     = w * (0.06 + self._gene(4) * 0.08)

        # Lower lip control offset — controls lower lip breadth
        l_ctrl   = w * (0.20 + self._gene(5) * 0.20)

        lip_color = self.get_lip_color()
        stroke_w  = w * 0.008

        upper = self.build_upper_lip(w, bow_h, valley_h, bow_x, ctrl)
        lower = self.build_lower_lip(w, lower_h, l_ctrl)

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

<!-- Mouth line -->
<line x1="0" y1="0" x2="{w:.4f}" y2="0"
      stroke="black"
      stroke-width="{stroke_w:.4f}"
      stroke-linecap="round"/>
"""
