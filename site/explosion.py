"""A complete exploded layout of the fitted CAD, with soldered boards kept intact."""
import math
import re

SECONDS = 48
FPS = 24
FRAMES = SECONDS * FPS
YAW = math.radians(35)
PITCH = math.radians(-20)
RIGHT = (math.cos(YAW), 0, -math.sin(YAW))
UP = (-math.sin(YAW) * math.sin(PITCH), math.cos(PITCH), -math.cos(YAW) * math.sin(PITCH))
BOARDS = (
    ('Fibonacci', ('FibonacciPCB', 'CircleLEDs')),
    ('Inner LED strip', ('InnerStrip', 'InnerLEDs')),
    ('Side LED strip 1', ('Side0Strip', 'Side0LEDs')),
    ('Side LED strip 2', ('Side1Strip', 'Side1LEDs')),
    ('IMU', ('IMUPCB', 'IMUComponents')),
    ('GPS', ('GPSPCB', 'GPSComponents')),
    ('Sparkle Motion', ('SparklePCB', 'SparkleComponents', 'SparkleUnderboard')),
    ('PowerBoost', ('BoostPCB', 'BoostComponents', 'BoostTerminalX1', 'BoostTerminalX2')),
    ('BlackPill', ('BlackPillPCB', 'BlackPillLoadedReservation', 'BlackPillUnderboardReservation')),
    ('Radio', ('RadioPCB', 'RadioLoadedReservation', 'RadioUnderboardReservation')),
    ('Power latch', ('LatchModule', 'LatchTerminalVIN', 'LatchTerminalVOUT')),
)
CATEGORIES = ('Case & optics', 'Battery', 'Electronics', 'Controls', 'Fasteners',
              'Connections & insulation', 'Wires 1–46', 'Wires 47–92')
REFERENCES = {'CapacitorVentClearance'}  # Air-space gauge, not a fitted component.
OPTICS = {'RearCover', 'ElectronicsShell', 'FrontBezel', 'SideDiffuser', 'InnerDiffuser',
          'EGLStencil', 'FrontMirror', 'RearCouplingMirror'}


def dot(point, axis):
    return sum(a * b for a, b in zip(point, axis))


def project(parts):
    points = []
    for part in parts:
        bounds = part['bounds_m']
        for corner in range(8):
            p = [bounds[(corner >> k) & 1][k] for k in range(3)]
            points.append((dot(p, RIGHT), dot(p, UP)))
    return [min(p[0] for p in points), min(p[1] for p in points),
            max(p[0] for p in points), max(p[1] for p in points)]


def pack(rectangles, gap):
    """Shelf-pack projected CAD bounds, preserving physical size and orientation."""
    ordered = sorted(rectangles, key=lambda r: (-r[2], -r[1], r[0]))
    minimum = max(w for _, w, _ in rectangles)
    maximum = max(minimum, math.sqrt(sum((w + gap) * (h + gap) for _, w, h in rectangles) * 16 / 9) * 2)
    candidates = []
    for step in range(65):
        width = minimum + (maximum - minimum) * step / 64
        result, x, y, row_height = {}, 0.0, 0.0, 0.0
        for key, w, h in ordered:
            if x and x + w > width:
                x, y, row_height = 0.0, y + row_height + gap, 0.0
            result[key] = [x, y, x + w, y + h]
            x += w + gap
            row_height = max(row_height, h)
        bounds = [0, 0, max(r[2] for r in result.values()), y + row_height]
        candidates.append((max(bounds[3], bounds[2] * 9 / 16), result, bounds))
    _, result, bounds = min(candidates, key=lambda c: c[0])
    return result, bounds


def category(name):
    if name in OPTICS or name in ('Fibonacci', 'Inner LED strip', 'Side LED strip 1', 'Side LED strip 2'):
        return CATEGORIES[0]
    if re.fullmatch(r'W\d{3}', name):
        return CATEGORIES[6 if int(name[1:]) <= 46 else 7]
    if re.search(r'Nut|Screw|Bolt|Washer|Spacer|Shim|Compression|HingePin|EdgeClip|Retainer', name):
        return CATEGORIES[4]
    if name.startswith('Battery'):
        return CATEGORIES[1]
    if name.startswith(('Action', 'Mode', 'Start', 'Guard', 'SwitchGuard', 'PowerDisconnect')):
        return CATEGORIES[3]
    if name.startswith(('Harness', 'Necklace', 'RingSideLacing', 'RingInnerLacing', 'SwitchLugBoot')) or 'Lacing' in name:
        return CATEGORIES[5]
    return CATEGORIES[2]


def layout(metadata):
    parts = {p['name']: p for p in metadata['parts'] if p['name'] not in REFERENCES}
    assigned, units = set(), []
    for name, members in BOARDS:
        if not set(members) <= parts.keys():
            raise ValueError('Incomplete soldered board: ' + name)
        units.append({'name': name, 'parts': list(members)})
        assigned.update(members)
    units.extend({'name': name, 'parts': [name]} for name in sorted(parts.keys() - assigned))
    for unit in units:
        unit['category'] = category(unit['name'])
        unit['source'] = project([parts[name] for name in unit['parts']])
    groups, local = {}, {}
    for label in CATEGORIES:
        members = [u for u in units if u['category'] == label]
        positions, bounds = pack([(u['name'], u['source'][2] - u['source'][0],
                                   u['source'][3] - u['source'][1]) for u in members], .006)
        local.update(positions)
        groups[label] = bounds
    locations, overview = pack([(label, b[2] + .04, b[3] + .04) for label, b in groups.items()], .04)
    views = []
    for label in CATEGORIES:
        b, origin = groups[label], locations[label]
        bounds = [origin[0], origin[1], origin[0] + b[2] + .04, origin[1] + b[3] + .04]
        views.append({'label': label, 'bounds': bounds})
    for unit in units:
        r, origin, source = local[unit['name']], locations[unit['category']], unit['source']
        target = [r[0] + origin[0] + .02, r[1] + origin[1] + .02,
                  r[2] + origin[0] + .02, r[3] + origin[1] + .02]
        du = (target[0] + target[2] - source[0] - source[2]) / 2
        dv = (target[1] + target[3] - source[1] - source[3]) / 2
        unit['offset'] = [du * RIGHT[k] + dv * UP[k] for k in range(3)]
        unit['target'] = target
    return {'units': units, 'views': views, 'overview': overview,
            'closed': project(metadata['parts']), 'seconds': SECONDS,
            'right': RIGHT, 'up': UP, 'references': sorted(REFERENCES)}


CAPTURE_INPUTS = ('site/explosion.py', 'site/render_assembly.py', 'site/render_assembly.gd',
                  'designs/stacked/exports/scene.json', 'designs/stacked/exports/amulet.glb')


def capture_record(plan, movie_hash, inputs):
    return {'movie_sha256': movie_hash, 'inputs': inputs,
            'fitted_cad_parts': sum(len(u['parts']) for u in plan['units']),
            'separate_units': len(plan['units']), 'seconds': SECONDS,
            'detail_frames': [258, 342, 426, 510, 594, 678, 762, 846]}


def verify_capture(record, metadata, movie_hash, inputs):
    if record != capture_record(layout(metadata), movie_hash, inputs):
        raise RuntimeError('Assembly recording is stale or lacks complete fitted-part coverage; render it again')
