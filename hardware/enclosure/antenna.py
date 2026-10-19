"""The two fixed internal-wire installations, in mm. No RF performance model.

ANT is JP2 at (21.590, 24.511) on Adafruit's board, relative to outline
centre (12.954, 14.605). See antenna-placement.md for revision and assumptions.
The path includes the stripped end, vertical feed, quarter-circle and straight.
"""

import math
from dataclasses import dataclass
from xml.sax.saxutils import escape


@dataclass(frozen=True)
class Installation:
    design: str
    feed: tuple
    direction: int
    rise: float
    bend: float
    straight: float
    radius: float
    tolerance: float
    metal_gap: float
    plastic_gap: float
    relief: float
    restraints: tuple
    length: float
    stripped: float
    case_radius: float

    @property
    def envelope(self):
        return self.radius + self.tolerance

    @property
    def top(self):
        return self.feed[2] + self.rise

    def point(self, distance):
        """Position on the horizontal run, measured from the bend's end."""
        x, y, _ = self.feed
        return (x, y + self.direction * (self.bend + distance), self.top)

    def points(self):
        """Arc chords with a known <0.004 mm sagitta, for conservative host checks."""
        x, y, z = self.feed
        count = max(8, math.ceil(math.pi / (4 * math.acos(1 - .003 / self.bend))))
        points = [self.feed]
        for i in range(count + 1):
            angle = i * math.pi / (2 * count)
            points.append((x, y + self.direction * self.bend * (1 - math.cos(angle)),
                           z + self.rise - self.bend + self.bend * math.sin(angle)))
        return points + [self.point(self.straight)]


def installation(p, compact=False):
    design = '200 mm compact' if compact else '250 mm original'
    values = {k[8:]: v for k, v in p.items() if k.startswith('antenna_')}
    required = ('length', 'wire_diameter', 'position_tolerance', 'feed_x', 'feed_y',
                'rotation_deg', 'rise', 'bend_radius', 'stripped_length',
                'conductor_clearance', 'plastic_clearance', 'feed_relief_radius',
                'first_restraint', 'second_restraint')
    for key in required:
        v = values.get(key)
        if isinstance(v, bool) or not isinstance(v, (float, int)) or not math.isfinite(v):
            raise ValueError(f'{design} antenna: {key} must be finite')
        if key != 'rotation_deg' and v <= 0:
            raise ValueError(f'{design} antenna: {key} must be positive')
    rotation = 0 if compact else 180
    if values['rotation_deg'] != rotation:
        raise ValueError(f'{design} antenna: board rotation must be {rotation} degrees')
    if not math.isclose(values['length'], 78, abs_tol=1e-8):
        raise ValueError(f'{design} antenna: total cut length must be 78 mm including feed')
    if (values['feed_x'], values['feed_y']) != (8.636, 9.906):
        raise ValueError(f'{design} antenna: ANT datum differs from sourced JP2')
    if compact:
        radio = next(e for e in p['electronics'] if e['name'] == 'Radio')
        x, y = radio['centre']
        z = radio['z']
        w, length, height = radio['size']
    else:
        x, y, w, length, height = [p['radio_' + s] for s in ('x', 'y', 'width', 'length', 'height')]
        z = p['rear_thickness'] + 4
    if not all(math.isfinite(v) for v in (x, y, z, w, length, height)) or min(w, length, height) <= 0:
        raise ValueError(f'{design} antenna: invalid Radio envelope')
    if w < 25.4 or length < 29.21 or height < 1.6:
        raise ValueError(f'{design} antenna: Radio envelope cannot contain the sourced board')
    sign = 1 if compact else -1
    radius = values['wire_diameter'] / 2
    envelope = radius + values['position_tolerance']
    bend = values['bend_radius']
    rise = values['rise']
    straight = values['length'] - rise + bend - math.pi * bend / 2
    first, second = values['first_restraint'], values['second_restraint']
    if not 1.6 <= values['stripped_length'] <= 2:
        raise ValueError(f'{design} antenna: stripped feed must be 1.6–2 mm')
    if radius > .5 or bend < max(3, 3 * values['wire_diameter']) or rise - bend < values['stripped_length']:
        raise ValueError(f'{design} antenna: wire/drill, bend or feed dimensions invalid')
    if not 6 <= first < second - 8 < straight - 8 or second + 3 >= straight:
        raise ValueError(f'{design} antenna: restraints must lie on the straight run')
    if values['feed_relief_radius'] < envelope + values['conductor_clearance'] or values['feed_relief_radius'] > 3.2:
        raise ValueError(f'{design} antenna: feed relief exceeds its bounded pad allowance')
    if rise < height + envelope + values['conductor_clearance']:
        raise ValueError(f'{design} antenna: riser does not clear Radio components')
    return Installation(design, (x + sign * values['feed_x'], y + sign * values['feed_y'], z),
                        sign, rise, bend, straight, radius, values['position_tolerance'],
                        values['conductor_clearance'], values['plastic_clearance'],
                        values['feed_relief_radius'], (first, second), values['length'], values['stripped_length'], p['case_diameter']/2)


def box_distance(a, b, lo, hi):
    """Exact minimum segment-to-AABB distance (piecewise convex quadratic)."""
    breaks = {0., 1.}
    delta = [q - v for v, q in zip(a, b)]
    for v, d, lower, upper in zip(a, delta, lo, hi):
        if d:
            breaks.update(t for edge in (lower, upper) if 0 < (t := (edge - v) / d) < 1)
    breaks = sorted(breaks)
    candidates = list(breaks)
    for left, right in zip(breaks, breaks[1:]):
        middle = (left + right) / 2
        terms = []
        for v, d, lower, upper in zip(a, delta, lo, hi):
            q = v + middle * d
            if q < lower or q > upper:
                terms.append((v - (lower if q < lower else upper), d))
        denominator = sum(d * d for _, d in terms)
        if denominator:
            candidates.append(max(left, min(right, -sum(v * d for v, d in terms) / denominator)))
    return min(math.sqrt(sum(max(lower - (v + t*d), 0, v + t*d - upper)**2
                             for v, d, lower, upper in zip(a, delta, lo, hi))) for t in candidates)


def check_boxes(route, obstacles, removal=0):
    """Named reserved volumes; removal extends each obstacle through the full lift.

    The wire travels along -Z. Extending a stationary box along +Z checks all
    relative positions, including obstacles strictly between sampled positions.
    Native checks additionally use every actual part, screw, coating and seal.
    """
    points = route.points()
    gaps = {}
    for name, lo, hi, gap in obstacles:
        if not all(math.isfinite(v) for v in (*lo, *hi, gap, removal)) or gap < 0 or removal < 0 or any(a >= b for a, b in zip(lo, hi)):
            raise ValueError(f'{route.design} antenna: invalid obstacle {name}')
        upper = (hi[0], hi[1], hi[2] + removal)
        distance = min(box_distance(a, b, lo, upper) for a, b in zip(points, points[1:]))
        clear = distance - route.envelope - .003
        if clear < gap - 1e-7:
            motion = ' removal' if removal else ''
            raise ValueError(f'{route.design} antenna{motion}: {name} clearance {clear:.3f} < {gap:g} mm')
        gaps[name] = clear
    return gaps


def reservations(p, compact=False):
    """Explicit harness and removable-seal reservations; assembly must respect them."""
    if compact:
        return [('LED/power harness', (-12, -5, 23.5), (12, 60, 25.5), p['antenna_conductor_clearance'])]
    return [('LED/power harness', (-12, -5, 18), (12, 60, 21), p['antenna_conductor_clearance'])]


def component_boxes(p, compact=False, include_radio=False):
    route = installation(p, compact)
    if compact:
        electronics = p['electronics']
    else:
        electronics = [dict(name=key, centre=[p[key+'_x'], p[key+'_y']],
                            size=[p[key+'_width'], p[key+'_length'], p[key+'_height']],
                            z=p['rear_thickness'] + (1.5 if key == 'battery' else 4))
                       for key in ('battery', 'sparkle', 'blackpill', 'gps', 'imu', 'sense', 'power', 'radio')]
    boxes = []
    for e in electronics:
        if e['name'].lower() == 'radio' and not include_radio:
            continue  # Only native radio checks can apply the local pad aperture.
        x, y = e['centre']; w, length, height = e['size']; z = e['z']
        boxes.append((e['name'], (x-w/2, y-length/2, z), (x+w/2, y+length/2, z+height), route.metal_gap))
    return boxes + reservations(p, compact)


def validate(p, compact=False):
    route = installation(p, compact)
    check_boxes(route, component_boxes(p, compact))
    return route


def diagram(route, obstacles, gaps, out):
    """Annotated projection generated from the checked native installation."""
    x, y, z = route.feed
    points = route.points()
    lines = [f'<svg xmlns="http://www.w3.org/2000/svg" width="900" height="650" viewBox="0 0 900 650"><title>{escape(route.design)} antenna placement</title>',
             '<rect width="900" height="650" fill="white"/>',
             '<g font-family="sans-serif" fill="#111" font-size="16">',
             f'<text x="24" y="28">{escape(route.design)} — 915 MHz internal wire; mechanical allowances only</text>',
             '<text x="24" y="54">Open rear: +X left, +Y up / necklace; +Z toward front, away from body</text>']
    def project(pt):
        return (180 - 1.15 * pt[0], 300 - 1.15 * pt[1])
    lines.append(f'<circle cx="180" cy="300" r="{1.15*route.case_radius}" fill="none" stroke="#999"/>')
    for name, lo, hi, _ in obstacles:
        left, top = project((hi[0], hi[1], 0))
        lines.append(f'<rect x="{left}" y="{top}" width="{1.15*(hi[0]-lo[0])}" height="{1.15*(hi[1]-lo[1])}" fill="none" stroke="#999"/>')
        lines.append(f'<text x="{left+2}" y="{top+10}" font-size="9">{escape(name)}</text>')
    coords = ' '.join(f'{a},{b}' for a, b in map(project, points))
    lines += [f'<polyline points="{coords}" fill="none" stroke="#0072b2" stroke-width="4"/>',
              '<path d="M 60,140 V 90 l -6,10 m 6,-10 l 6,10" stroke="#111" fill="none"/>',
              '<text x="28" y="80">UP +Y</text>']
    a, b = project(route.feed)
    lines.append(f'<circle cx="{a}" cy="{b}" r="5" fill="#111"/><text x="{a+12}" y="{b}">ANT</text>')
    for i, distance in enumerate(route.restraints, 1):
        a, b = project(route.point(distance))
        lines.append(f'<rect x="{a-8}" y="{b-6}" width="16" height="12" fill="white" stroke="#111"/><text x="{a+14}" y="{b+5}">Tie {i}</text>')
    side = ' '.join(f'{65+2*route.direction*(pt[1]-y)},{595-3*(pt[2]-z)}' for pt in points)
    lines.extend(['<text x="24" y="510" font-size="13">Side: +Z toward front (up); body behind feed</text>',
                  f'<polyline points="{side}" fill="none" stroke="#0072b2" stroke-width="3"/>',
                  '<text x="24" y="620" font-size="13">Form riser and bend before soldering into ANT.</text>'])
    notes = [f'Cut {route.length:g} mm TOTAL; includes {route.stripped:g} mm stripped end.',
             f'ANT XYZ: ({x:.3f}, {y:.3f}, {z:g}) mm.',
             f'Feed rises {route.rise:g} mm; bend radius {route.bend:g} mm.',
             f'Straight after bend: {route.straight:.3f} mm at Z{route.top:g}.',
             f'Tip XYZ: ({route.point(route.straight)[0]:.3f}, {route.point(route.straight)[1]:.3f}, {route.top:g}).',
             f'Wire OD {2*route.radius:g}; placement tolerance ±{route.tolerance:g} mm.',
             'Tie saddles locate the run; release ties before radio removal.',
             'Gap values below include insulation + placement tolerance:',
             *[f'{name}: {value:.2f} mm' for name, value in sorted(gaps.items(), key=lambda i: i[1])[:8]],
             'Feed pad / saddle contacts are bounded exceptions.',
             'CAD checks do not establish RF range or installed tuning.']
    for i, note in enumerate(notes):
        lines.append(f'<text x="370" y="{95+26*i}" font-size="14">{escape(note)}</text>')
    lines.append('</g></svg>')
    out.write_text('\n'.join(lines) + '\n')
