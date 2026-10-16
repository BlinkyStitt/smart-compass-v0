"""Independent unfolded-ray reference; distances in metres.

Each rear encounter transmits source light. Front/rear round trips attenuate it.
The side wall terminates a ray; its folded Z determines the ring-band weight.
"""

import math

MAX_REFLECTIONS = 32
MIN_WEIGHT = 0.001


def reference(
    point, direction, o, front_r=0.70, front_t=0.30, rear_r=0.70, rear_t=0.09
):
    x, y, _z = point
    dx, dy, dz = direction
    if dz >= -1e-8 or math.hypot(x, y) >= o["wall_radius"]:
        return [0.0, 0.0, 0]
    gap = o["front_z"] - o["rear_z"]
    a = dx * dx + dy * dy
    wall_depth = math.inf
    if a > 1e-14:
        b = x * dx + y * dy
        t = (
            -b + math.sqrt(max(0, b * b - a * (x * x + y * y - o["wall_radius"] ** 2)))
        ) / a
        wall_depth = t * -dz
    total = 0.0
    weight = front_t
    reflections = 0
    for bounce in range(MAX_REFLECTIONS):
        if weight < MIN_WEIGHT:
            break
        next_depth = gap * (bounce + 1)
        if wall_depth < next_depth:
            local = wall_depth % (2 * gap)
            hit_z = o["front_z"] - local if local <= gap else o["rear_z"] + local - gap
            spread = 0.00015 + (0.003 - 0.00015) * o.get("diffusion", 0.65)
            axial = math.exp(
                -((max(0, abs(hit_z - o["ring_z"]) - 0.0025) / spread) ** 2)
            )
            return [total, weight * axial, reflections]
        if bounce % 2 == 0:
            total += weight * rear_t
            weight *= rear_r
        else:
            weight *= front_r
        reflections += 1
    return [total, 0.0, reflections]


def cases(o):
    samples = []
    for point in (
        [0, 0, o["front_z"]],
        [0.05, 0, o["front_z"]],
        [o["wall_radius"] + 0.001, 0, o["front_z"]],
    ):
        for direction in (
            [0, 0, -1],
            [0.2, 0, -1],
            [1, 0, -1],
            [3, 0, -1],
            [1, 0, 0],
            [0, 0, 1],
        ):
            for coefficients in (
                (0.70, 0.30, 0.70, 0.09),
                (0, 1, 0, 1),
                (1, 0, 0.70, 0.09),
                (0.99, 0.01, 0.99, 0.01),
                (0.70, 0.30, 0, 1),
            ):
                samples.append(
                    {
                        "point": point,
                        "direction": direction,
                        "coefficients": coefficients,
                        "expected": reference(point, direction, o, *coefficients),
                    }
                )
    return samples


def side_weight(z, source_z, o):
    """Unit-source profile with conserved axial flux through the broad sleeve."""
    sigma = math.hypot(0.005 / math.sqrt(12), o["side_axial_scatter"] * o["diffusion"])
    area = 0.005 + math.sqrt(math.pi) * (0.00015 + 0.00285 * o["diffusion"])
    return (
        area
        * math.exp(-0.5 * ((z - source_z) / sigma) ** 2)
        / (math.sqrt(math.tau) * sigma)
    )


def side_cases(o):
    """Check additive sources, row colour mixing, gaps and stored glow."""
    first = o["side_first_z"]
    step = o["side_pitch"]
    angle = (0.003 / 2 + (1 / 120) / 2) / o["side_radius"]
    samples = []
    for rows in (1, o["side_rows"]):
        colours = [[1.0, 1.0, 1.0]] * rows
        palettes = [colours, [[0.0, 0.0, 0.0]] * rows]
        if rows > 1:
            palettes += [
                [
                    [int(channel == row % 3) for channel in range(3)]
                    for row in range(rows)
                ],
                [[int(row == 1)] * 3 for row in range(rows)],
            ]
        for z in (
            first - step / 2,
            first,
            first + step / 2,
            first + step,
            first + 1.5 * step,
            first + 2 * step,
            first + 2.5 * step,
        ):
            for palette in palettes:
                lit = any(any(rgb) for rgb in palette)
                expected = (
                    [
                        0.25
                        * sum(
                            rgb[channel] * side_weight(z, first + row * step, o)
                            for row, rgb in enumerate(palette)
                        )
                        for channel in range(3)
                    ]
                    if lit
                    else [0.16 * 0.072, 0.072, 0.025 * 0.072]
                )
                samples.append(
                    {
                        "point": [0.094 * math.sin(angle), 0.094 * math.cos(angle), z],
                        "rows": rows,
                        "lit": lit,
                        "row_colours": palette,
                        "expected": expected,
                    }
                )
    return samples
