import random

# =====================================================
# GENOME (TWO CHROMOSOMES)
# =====================================================

class Genome:
    """
    Simple genome with two chromosomes.
    Each chromosome is a list of tuples: (dominance, gene_value).
    Dominance: higher value wins.
    Gene_value: 0–255
    """

    def __init__(self, num_genes=128):
        """
        Creates two chromosomes with random genes.
        """
        self.chromosome1 = [
            (random.randint(0, 255), random.randint(0, 255))
            for _ in range(num_genes)
        ]

        self.chromosome2 = [
            (random.randint(0, 255), random.randint(0, 255))
            for _ in range(num_genes)
        ]

        self.num_genes = num_genes

    # =====================================================
    # BASIC GETTER
    # =====================================================

    def get_gene(self, index):
        """
        Returns the gene value at `index`.
        Compares dominance across chromosomes.
        """
        if index < 0 or index >= self.num_genes:
            raise IndexError("Gene index out of range")

        dom1, val1 = self.chromosome1[index]
        dom2, val2 = self.chromosome2[index]

        return val1 if dom1 >= dom2 else val2

    def get_gene_avg(self, index):
        """
        Returns the gene value at `index`.
        No dominance comparison — returns the average of both genes.
        """
        if index < 0 or index >= self.num_genes:
            raise IndexError("Gene index out of range")

        dom1, val1 = self.chromosome1[index]
        dom2, val2 = self.chromosome2[index]

        return (val1 + val2) / 2

    # -----------------------------------------------------
    # DELTA-Y GENES
    # -----------------------------------------------------

    def get_upper_y_gene(self, index):
        """
        Returns the y-gene for the upper eyelid at the given segment index.
        """
        return self.get_gene(index)

    def get_lower_y_gene(self, index):
        """
        Returns the y-gene for the lower eyelid at the given segment index.
        """
        return self.get_gene(index + 4)

    # -----------------------------------------------------
    # ΔX GENES
    # -----------------------------------------------------

    def get_width_gene(self, segment, gene_index):
        """
        Returns the Δx gene value for `segment` and `gene_index`.
        """
        idx = segment * 4 + gene_index + 8
        return self.get_gene(idx)

    # -----------------------------------------------------
    # SEGMENT TYPE (WEIGHTED, NOT RANDOM)
    # -----------------------------------------------------

    def get_segment_type(
        self,
        segment,
        segment_types,
        weights,
        upper=True
    ):
        """
        Returns the segment type according to the given weight distribution.

        segment_types : list of types, e.g. ["L","C","Q","S","T"]
        weights       : list of weights in the same order
        upper         : True = upper eyelid, False = lower eyelid
        """

        # Gene indices:
        # 24–27 = upper segment types
        # 28–31 = lower segment types
        base_idx = 24 if upper else 28
        gene_value = self.get_gene(base_idx + segment)

        # Convert weights to a cumulative distribution
        total_weight = sum(weights)
        cumulative = []
        running = 0

        for w in weights:
            running += w
            cumulative.append(running / total_weight)

        # Scale gene value 0–255 -> 0–1
        normalized = gene_value / 255.0

        # Deterministically select type
        for i, threshold in enumerate(cumulative):
            if normalized <= threshold:
                return segment_types[i]

        # fallback
        return segment_types[-1]

    # -----------------------------------------------------
    # TENSION GENES
    # -----------------------------------------------------

    def get_tension(self, segment, upper=True):
        """
        Returns the tension value in the range [-1, 1].
        """
        base_idx = 32 if upper else 36
        val = self.get_gene(base_idx + segment)

        return (val / 127.5) - 1.0  # scale 0–255 -> -1..1


    # -----------------------------------------------------
    # IRIS COLOR GENES
    # -----------------------------------------------------

    def get_iris_color(self):
        """
        Returns the iris color as an RGB triple.
        Each channel is the average of four genes.
        """
        r = (self.get_gene(40) + self.get_gene(41)  + self.get_gene(42) + self.get_gene(43)) // 4
        g = (self.get_gene(44) + self.get_gene(45)  + self.get_gene(46) + self.get_gene(47)) // 4
        b = (self.get_gene(48) + self.get_gene(49)  + self.get_gene(50) + self.get_gene(51)) // 4

        return (r, g, b)

    def get_iris_highlight_color(self):
        """
        Returns the iris highlight color as an RGB triple.
        Each channel is the average of three genes.
        """
        r = (self.get_gene(40) + self.get_gene(41)  + self.get_gene(42)) // 3
        g = (self.get_gene(44) + self.get_gene(45)  + self.get_gene(46)) // 3
        b = (self.get_gene(48) + self.get_gene(49)  + self.get_gene(50)) // 3

        return (r, g, b)

    def get_iris_highlight_multiplier(self):
        return self.get_gene(52) / 255.0

    # -----------------------------------------------------
    # SEGMENTED EYEBROW GENES  (indices 96–119)
    # 3 segments × 4 gene types, 12 spare (108–119):
    #   96– 98 : Δx per segment
    #   99–101 : center-line Δy per segment
    #  102–104 : half-width at inner keypoint and two interior keypoints
    #  105–107 : tension per segment
    #  108–119 : spare
    # -----------------------------------------------------

    def get_brow_dx_gene(self, segment):
        """Δx gene for brow segment 0–2."""
        return self.get_gene(96 + segment)

    def get_brow_dy_gene(self, segment):
        """Center-line Δy gene for brow segment 0–2."""
        return self.get_gene(99 + segment)

    def get_brow_width_gene(self, keypoint):
        """Half-width gene for brow keypoints 0–2 (outer tip is always 0)."""
        return self.get_gene(102 + keypoint)

    def get_brow_tension_gene(self, segment):
        """Tension gene for brow segment 0–2."""
        return self.get_gene(105 + segment)

    # -----------------------------------------------------
    # SKIN COLOR
    # -----------------------------------------------------

    def get_skin_color(self):
        """
        Returns an RGB triple interpolated smoothly across SKIN_PALETTE.
        """
        SKIN_PALETTE = [
        (117, 58, 15),   # darkest brown
        (145, 75, 50),   # dark brown
        (182, 107, 62),  # medium brown
        (195, 124, 77),  # light brown
        (210, 153, 108), # very light brown
        (245, 204, 171), # near fair
        (249, 213, 202)  # pinkish fair
        ]

        gene_value = 1 - (self.get_gene_avg(53) / 255) * (self.get_gene_avg(54) / 255)
        t = gene_value  * (len(SKIN_PALETTE) - 1)

        # Compute lower and upper palette indices
        idx0 = int(t)
        idx1 = min(idx0 + 1, len(SKIN_PALETTE) - 1)
        f = t - idx0  # fractional blend

        r0, g0, b0 = SKIN_PALETTE[idx0]
        r1, g1, b1 = SKIN_PALETTE[idx1]

        # Linear interpolation
        r = int(r0 + (r1 - r0) * f)
        g = int(g0 + (g1 - g0) * f)
        b = int(b0 + (b1 - b0) * f)

        return (r, g, b)
