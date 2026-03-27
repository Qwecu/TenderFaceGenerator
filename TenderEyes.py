from genes import Genome

import math

# =====================================================
# GLOBAL PARAMETERS
# =====================================================

EYE_WIDTH = 140
# Total eye width in pixels.
# Δx segments are scaled so their sum equals this value.

FOLD_RATIO = 0.06
# Eyelid crease height relative to eye width.
# Fold offset = EYE_WIDTH * FOLD_RATIO.

TENSION_RATIO = 0.25
# Maximum tension as a fraction of segment length.
# Controls how far a Bezier control point can deviate from a straight line.

IRIS_RADIUS = 36
# Iris radius in pixels.

PUPIL_RADIUS = 16
# Pupil radius in pixels.


# -----------------------------------------------------
# SEGMENT TYPE PROBABILITIES
# -----------------------------------------------------
# Weighted distribution for SVG path segment commands.
# Values are relative weights, not probabilities.

SEGMENT_TYPE_WEIGHTS = {
    "L": 0.25,  # Line (straight segment)
    "C": 0.35,  # Cubic Bezier
    "Q": 0.20,  # Quadratic Bezier
    "S": 0.10,  # Smooth cubic Bezier
    "T": 0.10   # Smooth quadratic Bezier
}

SEGMENT_TYPES = list(SEGMENT_TYPE_WEIGHTS.keys())
SEGMENT_WEIGHTS = list(SEGMENT_TYPE_WEIGHTS.values())


# =====================================================
# DELTA-Y RANGES
# =====================================================
# Each value is a RELATIVE y-change (Δy) for the given segment.
# Values define the biological "range of motion" per segment.

UPPER_DY_RANGES = [
    (-41, -23),
    (-14, 10),
    (-10, 20),
    (-16, 35)
]

LOWER_DY_RANGES = [
    (10, 24),
    (-4, 12),
    (-6, 16),
    (4, 16)
]


# =====================================================
# MINIMAL EYE
# =====================================================

class MinimalEyeGenome:

    def __init__(self, genome=None, stroke_ratio=140):
        """
        stroke_ratio:
            How many times the stroke fits into EYE_WIDTH.
            Default 140 → stroke = 1px when EYE_WIDTH = 140
        """
        self.genome = genome if genome is not None else Genome(num_genes=120)
        self.stroke_ratio = stroke_ratio


    # =====================================================
    # ΔX
    # =====================================================

    def compute_dx(self):
        raw = []

        # Average of four genes per segment
        for seg in range(4):
            vals = [self.genome.get_width_gene(seg, i) for i in range(4)]
            raw.append(max(1, sum(vals) / 4))

        # Scale so the sum of segments equals EYE_WIDTH
        scale = EYE_WIDTH / sum(raw)
        return [r * scale for r in raw]

    # =====================================================
    # ΔY
    # =====================================================

    def compute_dy(self):

        upper = []
        lower = []

        # --- UPPER EYELID ---
        for i in range(4):
            norm = self.genome.get_upper_y_gene(i) / 255
            mn, mx = UPPER_DY_RANGES[i]
            upper.append(mn + norm * (mx - mn))

        # --- LOWER EYELID ---
        for i in range(4):
            norm = self.genome.get_lower_y_gene(i) / 255
            mn, mx = LOWER_DY_RANGES[i]
            lower.append(mn + norm * (mx - mn))

        # Corner correction:
        # distribute the difference across the last two lower segments
        # so the path closes at the right corner

        diff = sum(lower) - sum(upper)
        lower[-2] -= diff / 3
        lower[-1] -= 2 * diff / 3

        return upper, lower

    # =====================================================
    # SEGMENT DATA
    # =====================================================

    def build_segments(self, dx_list, dy_list, seg_types, tensions, y_start=0.0):
        """
        Compute absolute control point coordinates for each segment.

        Returns a list of dicts, each with:
            cmd        : 'L', 'C', or 'Q'
            x0, y0     : segment start
            x1, y1     : segment end
            c1, c2     : cubic control points (C only)
            c          : quadratic control point (Q only)
        """
        x, y = 0.0, y_start
        last_ctrl_x, last_ctrl_y = x, y
        segments = []

        for i in range(4):
            dx = dx_list[i]
            dy = dy_list[i]
            t = seg_types[i]
            tension = tensions[i]

            x_next = x + dx
            y_next = y + dy
            ctrl_offset = tension * dx * TENSION_RATIO

            seg = {'x0': x, 'y0': y, 'x1': x_next, 'y1': y_next}

            if t == "L":
                seg['cmd'] = 'L'
                last_ctrl_x, last_ctrl_y = x_next, y_next

            elif t == "C":
                c1x = x + dx * 0.25;  c1y = y + dy * 0.25 + ctrl_offset
                c2x = x + dx * 0.75;  c2y = y + dy * 0.75 + ctrl_offset
                seg.update({'cmd': 'C', 'c1': (c1x, c1y), 'c2': (c2x, c2y)})
                last_ctrl_x, last_ctrl_y = c2x, c2y

            elif t == "Q":
                cx = x + dx * 0.5;  cy = y + dy * 0.5 + ctrl_offset
                seg.update({'cmd': 'Q', 'c': (cx, cy)})
                last_ctrl_x, last_ctrl_y = cx, cy

            elif t == "S":
                # Smooth cubic → explicit C with reflected first control point
                rc1x = 2 * x - last_ctrl_x;  rc1y = 2 * y - last_ctrl_y
                c2x  = x + dx * 0.75;        c2y  = y + dy * 0.75 + ctrl_offset
                seg.update({'cmd': 'C', 'c1': (rc1x, rc1y), 'c2': (c2x, c2y)})
                last_ctrl_x, last_ctrl_y = c2x, c2y

            elif t == "T":
                # Smooth quadratic → explicit Q with reflected control point
                rcx = 2 * x - last_ctrl_x;  rcy = 2 * y - last_ctrl_y
                seg.update({'cmd': 'Q', 'c': (rcx, rcy)})
                last_ctrl_x, last_ctrl_y = rcx, rcy

            segments.append(seg)
            x, y = x_next, y_next

        return segments

    def segments_to_path(self, segments, reverse=False):
        """
        Serialise a list of segments to an SVG path string.

        reverse=True traverses the list backwards, reversing each curve so
        the path runs from the last segment's end point back to the first
        segment's start point.  Useful for building closed eye shapes.
        """
        if not reverse:
            d = f"M {segments[0]['x0']:.2f} {segments[0]['y0']:.2f} "
            for s in segments:
                if s['cmd'] == 'L':
                    d += f"L {s['x1']:.2f} {s['y1']:.2f} "
                elif s['cmd'] == 'C':
                    c1, c2 = s['c1'], s['c2']
                    d += f"C {c1[0]:.2f} {c1[1]:.2f} {c2[0]:.2f} {c2[1]:.2f} {s['x1']:.2f} {s['y1']:.2f} "
                elif s['cmd'] == 'Q':
                    c = s['c']
                    d += f"Q {c[0]:.2f} {c[1]:.2f} {s['x1']:.2f} {s['y1']:.2f} "
        else:
            d = f"M {segments[-1]['x1']:.2f} {segments[-1]['y1']:.2f} "
            for s in reversed(segments):
                if s['cmd'] == 'L':
                    d += f"L {s['x0']:.2f} {s['y0']:.2f} "
                elif s['cmd'] == 'C':
                    # Reverse cubic: swap c1/c2 and swap start/end
                    c1, c2 = s['c1'], s['c2']
                    d += f"C {c2[0]:.2f} {c2[1]:.2f} {c1[0]:.2f} {c1[1]:.2f} {s['x0']:.2f} {s['y0']:.2f} "
                elif s['cmd'] == 'Q':
                    # Reverse quadratic: same control point, swap start/end
                    c = s['c']
                    d += f"Q {c[0]:.2f} {c[1]:.2f} {s['x0']:.2f} {s['y0']:.2f} "
        return d

    def build_closed_eye_path(self, upper_segs, lower_segs):
        """
        Returns a single closed path that outlines the eye opening:
        upper eyelid forward (left → right) then lower eyelid reversed
        (right → left), closed with Z.
        """
        upper_fwd = self.segments_to_path(upper_segs, reverse=False)
        lower_rev = self.segments_to_path(lower_segs, reverse=True)

        # lower_rev starts with "M ex ey" (same point upper_fwd ends at),
        # so we strip that "M x y " prefix before appending.
        lower_commands = " ".join(lower_rev.split()[3:])  # skip "M", x, y

        return upper_fwd + lower_commands + " Z"

    # =====================================================
    # COLOR UTILITY
    # =====================================================

    def lighten(self, color, factor=0.45):
        """
        Returns a lighter version of the given color.
        """
        r, g, b = color
        return (
            int(r + (255 - r) * factor),
            int(g + (255 - g) * factor),
            int(b + (255 - b) * factor),
        )

    # =====================================================
    # IRIS POLYGON
    # =====================================================

    def build_iris_polygon(self, cx, cy, radius, color):
        """
        Creates a light polygon inside the iris for a highlight effect.
        """
        points = []
        sides = 12
        poly_radius = radius * (0.55 + 0.15 * self.genome.get_iris_highlight_multiplier())

        for i in range(sides):
            angle = 2 * math.pi * i / sides
            x = cx + poly_radius * math.cos(angle)
            y = cy + poly_radius * math.sin(angle)
            points.append(f"{x:.2f},{y:.2f}")

        return f"""
<polygon points="{' '.join(points)}"
         fill="rgb{color}"/>
"""

    # -------------------------------------------------
    # RETURNS ONLY THE GROUP CONTENT
    # -------------------------------------------------

    def generate_group(self, clip_id, normalize=False):

        dx_list = self.compute_dx()
        upper_dy, lower_dy = self.compute_dy()

        # =====================================================
        # NORMALISE TO 0–1 COORDINATE SPACE (optional)
        # =====================================================

        scale = 1.0
        radius_scale = 1.0
        stroke_width = EYE_WIDTH / self.stroke_ratio

        if normalize:
            scale = 1.0 / EYE_WIDTH
            radius_scale = scale
            stroke_width *= scale

            dx_list  = [dx * scale for dx in dx_list]
            upper_dy = [dy * scale for dy in upper_dy]
            lower_dy = [dy * scale for dy in lower_dy]

        # Segment types and tensions from genes
        upper_seg_type = [
            self.genome.get_segment_type(i, SEGMENT_TYPES, SEGMENT_WEIGHTS, upper=True)
            for i in range(4)
        ]
        lower_seg_type = [
            self.genome.get_segment_type(i, SEGMENT_TYPES, SEGMENT_WEIGHTS, upper=False)
            for i in range(4)
        ]
        upper_tension = [self.genome.get_tension(i, upper=True)  for i in range(4)]
        lower_tension = [self.genome.get_tension(i, upper=False) for i in range(4)]

        # Build segment data (absolute coords + control points)
        upper_segs = self.build_segments(dx_list, upper_dy, upper_seg_type, upper_tension)
        lower_segs = self.build_segments(dx_list, lower_dy, lower_seg_type, lower_tension)

        # Individual stroke paths (for drawing the eyelid lines)
        upper_path = self.segments_to_path(upper_segs)
        lower_path = self.segments_to_path(lower_segs)

        # Closed eye-opening shape (used for clip + sclera fill)
        eye_shape = self.build_closed_eye_path(upper_segs, lower_segs)

        # Eyelid crease (fold): starts above the inner eye corner, arcs up, then
        # converges back toward the upper lid at the outer corner.
        fold_offset = (EYE_WIDTH * FOLD_RATIO) * scale
        start_extra = fold_offset  # fold origin sits above the inner eye corner

        # Desired gap (fold above upper lid) at each of the 5 keypoints
        # (inner corner + after each of the 4 segments).
        # Kept roughly uniform so the fold stays equidistant from the lid
        # across its whole width (gentle arch, not a steep convergence):
        desired_gaps = [
            fold_offset,         # inner corner
            fold_offset * 1.4,   # gentle peak
            fold_offset * 1.2,   # middle
            fold_offset * 0.9,   # slight descent
            fold_offset * 0.7,   # outer corner — still above lid
        ]
        d_gaps = [desired_gaps[i + 1] - desired_gaps[i] for i in range(4)]
        fold_dy = [dy - dg for dy, dg in zip(upper_dy, d_gaps)]
        fold_segs = self.build_segments(dx_list, fold_dy, upper_seg_type, upper_tension,
                                        y_start=-start_extra)
        fold_path = self.segments_to_path(fold_segs)

        # Iris center
        iris_center_x = sum(dx_list) / 2
        iris_center_y = (sum(upper_dy[0:3]) + sum(lower_dy[0:3])) / 2

        base_color      = self.genome.get_iris_color()
        highlight_color = self.genome.get_iris_highlight_color()

        iris_polygon = self.build_iris_polygon(
            iris_center_x, iris_center_y,
            IRIS_RADIUS * radius_scale,
            highlight_color
        )

        return f"""
<defs>
  <clipPath id="{clip_id}" clipPathUnits="userSpaceOnUse">
    <path d="{eye_shape}" />
  </clipPath>
</defs>

<!-- Sclera (eye white) -->
<path d="{eye_shape}" fill="white" stroke="none"/>

<!-- Iris -->
<circle cx="{iris_center_x:.2f}"
        cy="{iris_center_y:.2f}"
        r="{IRIS_RADIUS * radius_scale}"
        fill="rgb{base_color}"
        clip-path="url(#{clip_id})"/>

{iris_polygon.replace('<polygon ', f'<polygon clip-path="url(#{clip_id})" ')}

<!-- Pupil -->
<circle cx="{iris_center_x:.2f}"
        cy="{iris_center_y:.2f}"
        r="{PUPIL_RADIUS * radius_scale}"
        fill="black"
        clip-path="url(#{clip_id})"/>

<!-- Eyelid lines -->
<path d="{upper_path}" fill="none" stroke="black" stroke-width="{stroke_width}"/>
<path d="{fold_path}"  fill="none" stroke="black" stroke-width="{stroke_width}"/>
<path d="{lower_path}" fill="none" stroke="black" stroke-width="{stroke_width}"/>
"""

# =====================================================
# 4x4 GRID
# =====================================================

def generate_eye_grid():

    COLS = 4
    ROWS = 4

    CELL_WIDTH = 200
    CELL_HEIGHT = 100

    total_width = COLS * CELL_WIDTH
    total_height = ROWS * CELL_HEIGHT

    svg_content = ""

    for row in range(ROWS):
        for col in range(COLS):

            eye = MinimalEyeGenome()
            clip_id = f"eyeClip_{row}_{col}"

            tx = col * CELL_WIDTH
            ty = row * CELL_HEIGHT

            svg_content += f"""
<g transform="translate({tx},{ty})">
{eye.generate_group(clip_id)}
</g>
"""

    return f"""
<svg xmlns="http://www.w3.org/2000/svg"
     viewBox="0 0 {total_width} {total_height}">
{svg_content}
</svg>
"""


# =====================================================
# ENTRY POINT
# =====================================================

if __name__ == "__main__":

    svg_output = generate_eye_grid()

    with open("genetic_eye_grid.svg", "w") as f:
        f.write(svg_output)

    print("SVG created: genetic_eye_grid.svg")
