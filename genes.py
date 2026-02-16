import random

# =====================================================
# GENOMI (KAKSI KROMOSOMIA)
# =====================================================

class Genome:
    """
    Yksinkertainen genomi kahdella kromosomilla.
    Jokainen kromosomi on lista tupleja: (dominance, gene_value).
    Dominance: suurempi arvo voittaa.
    Gene_value: 0–255
    """

    def __init__(self, num_genes=128):
        """
        Luo kaksi kromosomia satunnaisilla geeneillä.
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
    # PERUS GETTER
    # =====================================================

    def get_gene(self, index):
        """
        Palauttaa geenin arvon indeksillä `index`.
        Verrataan dominanssia kromosomeissa.
        """
        if index < 0 or index >= self.num_genes:
            raise IndexError("Gene index out of range")

        dom1, val1 = self.chromosome1[index]
        dom2, val2 = self.chromosome2[index]

        return val1 if dom1 >= dom2 else val2

    # -----------------------------------------------------
    # DELTA-Y GEENIT
    # -----------------------------------------------------

    def get_upper_y_gene(self, index):
        """
        Palauttaa y-geenin yläluomelle tietyn segmentin indeksiin.
        """
        return self.get_gene(index)

    def get_lower_y_gene(self, index):
        """
        Palauttaa y-geenin alaluomelle tietyn segmentin indeksiin.
        """
        return self.get_gene(index + 4)

    # -----------------------------------------------------
    # ΔX GEENIT
    # -----------------------------------------------------

    def get_width_gene(self, segment, gene_index):
        """
        Palauttaa Δx-geenin arvon segmentissä `segment` ja geenin `gene_index`.
        """
        idx = segment * 4 + gene_index + 8
        return self.get_gene(idx)
# -----------------------------------------------------
    # SEGMENTTITYYPPI (PAINOTETTU, EI SATUNNAINEN)
    # -----------------------------------------------------

    def get_segment_type(
        self,
        segment,
        segment_types,
        weights,
        upper=True
    ):
        """
        Palauttaa segmenttityypin annetun painojakauman mukaan.

        segment_types : lista tyypeistä, esim ["l","c","q","s","t"]
        weights       : lista painoista samassa järjestyksessä
        upper         : True = yläluomi, False = alaluomi
        """

        # Geenien indeksit:
        # 24–27 = ylä segmenttityypit
        # 28–31 = ala segmenttityypit
        base_idx = 24 if upper else 28
        gene_value = self.get_gene(base_idx + segment)

        # Muutetaan painot kumulatiiviseksi jakaumaksi
        total_weight = sum(weights)
        cumulative = []
        running = 0

        for w in weights:
            running += w
            cumulative.append(running / total_weight)

        # Skaalataan geenin arvo 0–255 -> 0–1
        normalized = gene_value / 255.0

        # Valitaan tyyppi deterministisesti
        for i, threshold in enumerate(cumulative):
            if normalized <= threshold:
                return segment_types[i]

        # fallback (varmuuden vuoksi)
        return segment_types[-1]
    
    # -----------------------------------------------------
    # TENSION GEENIT
    # -----------------------------------------------------

    def get_tension(self, segment, upper=True):
        """
        Palauttaa jännitysarvon [-1, 1].
        """
        base_idx = 32 if upper else 36
        val = self.get_gene(base_idx + segment)

        return (val / 127.5) - 1.0  # skaalataan 0-255 -> -1..1


    # -----------------------------------------------------
    # IIRIKSEN VÄRIGEENIT
    # -----------------------------------------------------

    def get_iris_color(self):
        """
        Palauttaa iiriksen värin RGB-triplena.
        Kukin kanava neljän geenin keskiarvona.
        """


        r = (self.get_gene(40) + self.get_gene(41)  + self.get_gene(42) + self.get_gene(43)) // 4
        g = (self.get_gene(44) + self.get_gene(45)  + self.get_gene(46) + self.get_gene(47)) // 4
        b = (self.get_gene(48) + self.get_gene(49)  + self.get_gene(50) + self.get_gene(51)) // 4

        return (r, g, b)
    
    def get_iris_highlight_color(self):
        """
        Palauttaa iiriksen värin RGB-triplena.
        Kukin kanava kolmen geenin keskiarvona.
        """

        r = (self.get_gene(40) + self.get_gene(41)  + self.get_gene(42)) // 3
        g = (self.get_gene(44) + self.get_gene(45)  + self.get_gene(46)) // 3
        b = (self.get_gene(48) + self.get_gene(49)  + self.get_gene(50)) // 3

        return (r, g, b)

    def get_iris_highlight_multiplier(self):
        return self.get_gene(52) / 255.0
