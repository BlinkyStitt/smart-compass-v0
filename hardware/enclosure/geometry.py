"""Millimetre geometry shared by the FreeCAD builder and its checks."""
import math


def clip_polygon(polygon, nx, ny, limit):
    """Clip a convex polygon to nx*x + ny*y <= limit."""
    out = []
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        da, db = nx * a[0] + ny * a[1] - limit, nx * b[0] + ny * b[1] - limit
        if da <= 1e-9:
            out.append(a)
        if (da < 0 < db) or (db < 0 < da):
            fraction = da / (da - db)
            out.append((a[0] + fraction * (b[0] - a[0]), a[1] + fraction * (b[1] - a[1])))
    return out


def led_centres(layout, p):
    points = [(x - 127.5, y - 127.5) for x, y in layout['xy_u8']]
    scale = p['led_map_radius'] / max(math.hypot(x, y) for x, y in points)
    angle = math.radians(p['map_rotation_deg'])
    c, s = math.cos(angle), math.sin(angle)
    result = []
    for x, y in points:
        x *= -1 if p['map_mirror_x'] else 1
        y *= -1 if p['map_mirror_y'] else 1
        result.append((scale * (x * c - y * s), scale * (x * s + y * c)))
    return result


def mask_cells(centres, radius, web):
    """Inset each LED's Voronoi cell to retain a connected wood web."""
    boundary = [(radius * math.cos(i * math.tau / 192), radius * math.sin(i * math.tau / 192)) for i in range(192)]
    result = []
    for i, (x, y) in enumerate(centres):
        cell = boundary[:]
        for j, (a, b) in enumerate(centres):
            if i != j:
                cell = clip_polygon(cell, a - x, b - y, (a * a + b * b - x * x - y * y) / 2)
                if not cell:
                    raise ValueError(f'Empty cell {i}')
        opening = cell[:]
        for a, b in zip(cell, cell[1:] + cell[:1]):
            # The cell is counterclockwise: the right-hand normal points out.
            nx, ny = b[1] - a[1], a[0] - b[0]
            opening = clip_polygon(opening, nx, ny, nx * a[0] + ny * a[1] - web * math.hypot(nx, ny) / 2)
        if len(opening) < 3 or not contains(opening, (x, y)):
            raise ValueError(f'Web removes LED {i}')
        result.append(opening)
    return result


def contains(polygon, point):
    x, y = point
    return all((b[0] - a[0]) * (y - a[1]) - (b[1] - a[1]) * (x - a[0]) >= -1e-7 for a, b in zip(polygon, polygon[1:] + polygon[:1]))


def ring_radius(count, p):
    return (count * 1000 / p['strip_density'] + p['ring_seam_gap']) / math.tau


def ring_windows(inner, outer):
    # Eight broad windows, joined by bridges between the cardinal markers.
    paths = []
    gap = 1.8 / inner
    for i in range(8):
        a, b = (i - .5) * math.tau / 8 + gap / 2, (i + .5) * math.tau / 8 - gap / 2
        paths.append([(outer * math.cos(a + (b - a) * j / 24), outer * math.sin(a + (b - a) * j / 24)) for j in range(25)] + [(inner * math.cos(b - (b - a) * j / 24), inner * math.sin(b - (b - a) * j / 24)) for j in range(25)])
    return paths


def mounting_points(p):
    return [(p['fastener_radius'] * math.cos(math.radians(30 + 60 * i)), p['fastener_radius'] * math.sin(math.radians(30 + 60 * i))) for i in range(6)]
