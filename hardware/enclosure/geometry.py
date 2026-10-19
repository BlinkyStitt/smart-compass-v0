"""Millimetre geometry shared by the FreeCAD builder and its checks."""
import math
import json
import antenna
from pathlib import Path


def resolve_parameters(p):
    """Derive the optical stack from the reflecting-plane gap in millimetres."""
    p = dict(p)
    if not math.isfinite(p["mirror_gap"]) or p["mirror_gap"] <= 0:
        raise ValueError("mirror_gap must be finite and positive")
    p["front_plane_z"] = p["rear_mirror_front_z"] + p["mirror_gap"]
    p["circle_back_z"] = (p["front_plane_z"] - p["circle_pcb_thickness"]
                          - p["led_height"] - p["led_baffle_gap"]
                          - p["baffle_thickness"] - p["baffle_to_sheet_gap"])
    p["mirror_back_z"] = p["rear_mirror_front_z"] - p["rear_acrylic_thickness"]
    p["strip_bottom_z"] = p["rear_mirror_front_z"] + (p["mirror_gap"] - p["strip_width"]) / 2
    p["front_washer_compressed_height"] = p["front_washer_free_thickness"] * p["front_washer_compression_ratio"]
    p["case_depth"] = p["front_plane_z"] + p["front_acrylic_thickness"] + p["front_washer_compressed_height"]
    antenna.validate(p)
    return p


def load_parameters():
    """JSON is the sole input owner; the CAD spreadsheet records this stack."""
    return resolve_parameters(json.loads((Path(__file__).resolve().parent / "parameters.json").read_text()))


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


def pixel_regions(centres, radius):
    """Voronoi partitions for the preview only; the original baffle clips them."""
    boundary = [(radius * math.cos(i * math.tau / 192), radius * math.sin(i * math.tau / 192)) for i in range(192)]
    result = []
    for i, (x, y) in enumerate(centres):
        cell = boundary[:]
        for j, (a, b) in enumerate(centres):
            if i != j:
                cell = clip_polygon(cell, a-x, b-y, (a*a+b*b-x*x-y*y)/2)
        if len(cell)<3 or not contains(cell,(x,y)):
            raise ValueError(f'Empty optical partition {i}')
        result.append(cell)
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
    front = p['front_plane_z']
    rear = p['rear_mirror_front_z']
    return {
        'inner_radius': inner,
        'outer_radius': outer,
        'circle_to_inner_led': inner - p['strip_thickness']/2 - p['ring_led_depth'] - p['circle_diameter']/2,
        'visible_mirror_width': p['mirror_view_outer_radius'] - p['mirror_view_inner_radius'],
        'mirror_separation': front - rear,
        'outer_led_clearance': p['edge_diffuser_radius'] - outer - p['strip_thickness']/2 - p['ring_led_depth'],
        'halo_radius': ring_radius(p['halo_count'], p),
        'edge_height': p['front_plane_z'] - p['edge_bottom_z'],
        'outer_strip_centre_z': strip_bottom('Outer', p) + p['strip_width']/2,
        'diffuser_gap': cavity_diffusers(p)['Inner']['inner']-cavity_diffusers(p)['Halo']['outer'],
    }


def strip_bottom(name, p):
    """Centre the outer row in the side diffuser; mirror rows share one Z."""
    if name == 'Outer':
        return (p['edge_bottom_z'] + p['front_plane_z'] - p['ring_front_clearance'] - p['strip_width']) / 2
    return p['strip_bottom_z']


def mounting_points(p):
    return [(p['fastener_radius'] * math.cos(math.radians(p['fastener_phase_deg'] + 60 * i)), p['fastener_radius'] * math.sin(math.radians(p['fastener_phase_deg'] + 60 * i))) for i in range(6)]


def battery_centres(p):
    """Separate interchangeable packs, never a combined electrical pack."""
    return [(p['battery_x'] + (i-(p['battery_count']-1)/2)*p['battery_spacing'], p['battery_y']) for i in range(int(p['battery_count']))]


def necklace_anchors(p, side):
    eye = (side*84, 64)
    primary = min(mounting_points(p), key=lambda point: math.dist(point, eye))
    return eye, primary, (side*97, 51)


def cavity_diffusers(p):
    """Whole printed rings on the emitting side of both mirror-cavity strips."""
    halo_face = ring_radius(p['halo_count'],p)+p['strip_thickness']/2+p['ring_led_depth']
    inner_face = ring_radius(p['inner_count'],p)-p['strip_thickness']/2-p['ring_led_depth']
    thickness,gap = p['ring_diffuser_thickness'],p['ring_diffuser_led_gap']
    bottom = p['mirror_back_z']+p['rear_acrylic_thickness']+p['ring_bottom_clearance']
    top = p['front_plane_z']-p['ring_front_clearance']
    return {'Halo':{'inner':halo_face+gap,'outer':halo_face+gap+thickness,'bottom':bottom,'height':top-bottom},
            'Inner':{'inner':inner_face-gap-thickness,'outer':inner_face-gap,'bottom':bottom,'height':top-bottom}}


def ring_locating_angles(p, phase=30):
    return tuple(phase+i*360/int(p['ring_station_count']) for i in range(int(p['ring_station_count'])))


def ring_movement_limit(p, radial_error=0):
    """Conservative centre-motion bound from the actual circular contact radii.

    Ignore each pad's finite angular width, which only reduces movement. The
    worst direction lies midway between adjacent radial restraints. Assign the
    combined radial error to the contact clearance, where geometry amplifies
    its effect more than the same error at an LED face.
    """
    bands=cavity_diffusers(p)
    gap=p['ring_seat_play']+radial_error
    cosine=math.cos(math.pi/int(p['ring_station_count']))
    sine_squared=1-cosine*cosine
    inside=[]
    for radius in (bands['Halo']['inner'],p['edge_diffuser_radius']):
        contact=radius-gap
        inside.append(math.sqrt(radius*radius-contact*contact*sine_squared)-contact*cosine)
    radius=bands['Inner']['outer']
    contact=radius+gap
    outside=contact*cosine-math.sqrt(radius*radius-contact*contact*sine_squared)
    return max(*inside,outside)


def ring_led_clearances(p):
    """Minimum nominal gap to the complete 5 mm wide LED packages."""
    bands=cavity_diffusers(p)
    halo_face=ring_radius(p['halo_count'],p)+p['strip_thickness']/2+p['ring_led_depth']
    outer_face=ring_radius(p['outer_count'],p)+p['strip_thickness']/2+p['ring_led_depth']
    inner_face=ring_radius(p['inner_count'],p)-p['strip_thickness']/2-p['ring_led_depth']
    return {'Halo':bands['Halo']['inner']-math.hypot(halo_face,2.5),
            'Inner':inner_face-bands['Inner']['outer'],
            'Outer':p['edge_diffuser_radius']-math.hypot(outer_face,2.5)}


def outside_front_overlap(p):
    """Continuous radial band below the sheet at every permitted ring offset."""
    return min(p['edge_diffuser_thickness'], p['case_diameter']/2-p['edge_diffuser_radius']
               -ring_movement_limit(p,p['ring_radial_error_budget']))


def top_light_shields(p):
    """Opaque tape covers the exposed axial LED edges and ring end faces."""
    bands = cavity_diffusers(p)
    halo_strip_outer = ring_radius(p['halo_count'], p) + p['strip_thickness']/2
    inner_strip_inner = ring_radius(p['inner_count'], p) - p['strip_thickness']/2
    clearance = p['light_shield_edge_clearance']
    return {
        'Halo': {'inner': halo_strip_outer + clearance, 'outer': bands['Halo']['outer'],
                 'bottom': bands['Halo']['bottom'] + bands['Halo']['height'],
                 'height': p['light_shield_thickness']},
        'Inner': {'inner': bands['Inner']['inner'], 'outer': inner_strip_inner - clearance,
                  'bottom': bands['Inner']['bottom'] + bands['Inner']['height'],
                  'height': p['light_shield_thickness']},
        'Outer': {'inner': ring_radius(p['outer_count'], p) + p['strip_thickness']/2 + clearance,
                  'outer': p['edge_diffuser_radius'] + p['edge_diffuser_thickness'],
                  'bottom': p['front_plane_z'] - p['ring_front_clearance'],
                  'height': p['light_shield_thickness']},
    }


def rear_mounting_points(p):
    """Rear-cover screws are independent of the six optical-stack bolts."""
    return [(112.5*math.cos(math.radians(0+60*i)),112.5*math.sin(math.radians(0+60*i))) for i in range(6)]


def baffle_bottom(p):
    return p['front_plane_z']-p['baffle_to_sheet_gap']-p['baffle_thickness']
