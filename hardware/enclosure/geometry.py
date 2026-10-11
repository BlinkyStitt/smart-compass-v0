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


def ring_pixel(count, index, outward, p):
    """Return a pixel centre and its radial emission unit vector, front view."""
    r = ring_radius(count, p)
    pitch = 1000 / p['strip_density']
    angle = (p['ring_seam_gap'] / 2 + (index + .5) * pitch) / r
    ux, uy = math.sin(angle), math.cos(angle)
    sign = 1 if outward else -1
    centre_radius = r + sign * (p['strip_thickness'] / 2 + p['ring_led_depth'] / 2)
    return (centre_radius * ux, centre_radius * uy), (sign * ux, sign * uy)


def optical_dimensions(p):
    inner = ring_radius(p['inner_count'], p)
    outer = ring_radius(p['outer_count'], p)
    front = p['case_depth'] - p['front_bezel_thickness'] - p['acrylic_thickness']
    rear = p['mirror_back_z'] + p['mirror_back_thickness']
    return {
        'inner_radius': inner,
        'outer_radius': outer,
        'circle_to_inner_led': inner - p['strip_thickness']/2 - p['ring_led_depth'] - p['circle_diameter']/2,
        'visible_mirror_width': p['mirror_view_outer_radius'] - p['mirror_view_inner_radius'],
        'mirror_separation': front - rear,
        'outer_led_clearance': p['edge_diffuser_radius'] - outer - p['strip_thickness']/2 - p['ring_led_depth'],
    }


def mounting_points(p):
    return [(p['fastener_radius'] * math.cos(math.radians(p['fastener_phase_deg'] + 60 * i)), p['fastener_radius'] * math.sin(math.radians(p['fastener_phase_deg'] + 60 * i))) for i in range(6)]
