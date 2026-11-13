"""One removable carrier retainer with insulated PCB contacts."""

import math

import FreeCAD as App
import Part

from native import MODULE_OBJECTS, at_pose, box, cylinder, harness_plan, intersections, require_solid

TOP = 28.8
RAIL = 27.55
FOOT = 4.9
ANCHORS = ((-83, 28), (45, 31), (60, -1.5), (0, -18), (-82, 10))
ROUND_CONTACTS = {
    "IMU": ((-71.12, 40.47),),
    "GPS": ((-28.86, 82.89),),
    "SPARKLE": ((-16.86, 58.97), (28.86, 31.03)),
    "BOOST": ((-76.065, -18.89),),
}
# Edge pad centre, pad half width, and stem location.
EDGE_CONTACTS = {
    "RADIO": ((43.5, -17.30), (1.5, .22), (43.5, -19.7)),
    "BLACKPILL": ((-40.48, 23.5), (.30, 1.6), (-42.68, 23.5)),
    "Latch": ((-7.36, 7.5), (.21, 1), (-12.2, 7.5)),
}
RAILS = (
    ((-76.065, -18.89), (-82, 10)),
    ((-82, 10), (-83, 28)),
    ((-83, 28), (-71.12, 40.47)),
    ((-71.12, 40.47), (-42.68, 23.5)),
    ((-71.12, 40.47), (-34, 69)),
    ((-34, 69), (-28.86, 82.89)),
    ((-34, 69), (-16.86, 58.97)),
    ((-16.86, 58.97), (28.86, 31.03)),
    ((28.86, 31.03), (45, 31)),
    ((45, 31), (60, -1.5)),
    ((60, -1.5), (43.5, -19.7)),
    ((43.5, -19.7), (0, -18)),
    ((0, -18), (-12.2, 7.5)),
    ((-12.2, 7.5), (-42.68, 23.5)),
)


def rail(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    # The GPS branch tapers into its small PCB-hole pad beside the shell.
    reach = math.hypot(dx, dy)
    end_width, end_extra = (1.4, .5) if b == ROUND_CONTACTS["GPS"][0] else (3, 3)
    corners = [App.Vector(x, y, RAIL) for x, y in
               ((-3, -3), (reach + end_extra, -end_width),
                (reach + end_extra, end_width), (-3, 3))]
    shape = Part.Face(Part.makePolygon(corners + corners[:1])).extrude(
        App.Vector(0, 0, TOP - RAIL)
    )
    shape.rotate(App.Vector(), App.Vector(0, 0, 1), math.degrees(math.atan2(dy, dx)))
    shape.translate(App.Vector(*a, 0))
    return shape


def rect(xy, halves, low, high):
    x, y = xy
    dx, dy = halves
    return box(([x - dx, y - dy, low], [x + dx, y + dy, high]))


def edge_toe(xy, halves, stem, z):
    """Bridge from the stem to the unpopulated edge of the board."""
    x, y = xy
    dx, dy = halves
    sx, sy = stem
    return box(([min(x - dx, sx), min(y - dy, sy), z + .8],
                [max(x + dx, sx), max(y + dy, sy), z + 2.5]))


def build(baseline, spec, products, obstacles, rear):
    entries = {row["name"]: row for row in harness_plan.parameters()["electronics"]}
    z = spec["module_bottom_z_mm"]
    pcb = {
        name: at_pose(baseline.getObject(objects[1]).Shape, entries[objects[0]], spec["modules"][name], z)
        for name, objects in MODULE_OBJECTS.items()
    }
    pcb["SPARKLE"] = max(products["SPARKLE"].Solids, key=lambda shape: shape.Volume)
    pcb["Latch"] = products["Latch"]
    pieces = [rail(a, b) for a, b in RAILS]
    pads = {}
    bearing = {}
    for name, points in ROUND_CONTACTS.items():
        top = pcb[name].BoundBox.ZMax
        bearing[name] = []
        for index, xy in enumerate(points):
            pieces.append(cylinder(1.9, top + .8, TOP, xy))
            pads[f"{name}{index}"] = cylinder(1.9, top, top + .8, xy)
            bearing[name].append(cylinder(1.9, top - .05, top, xy).common(pcb[name]).Volume / .05)

    for name, (xy, half, stem) in EDGE_CONTACTS.items():
        top = z + 1.016 if name == "Latch" else pcb[name].BoundBox.ZMax
        # The BlackPill envelope includes a 0.05 mm conservative PCB
        # skin at bare edges. Prove contact on the actual source PCB.
        test_base = top + .06 if name == "BLACKPILL" else top
        pads[name] = rect(xy, half, test_base, top + .8)
        bearing[name] = [rect(xy, half, top - .05, top).common(pcb[name]).Volume / .05]
        lower = (-8.9, xy[1]) if name == "Latch" else stem
        pieces.append(edge_toe(xy, half, lower, top))
        if name == "Latch":
            pieces.append(cylinder(1.55, top + .8, 21.1, lower))
            pieces.append(box(([-12.2, 6.5, 19.4], [-8.9, 8.5, 21.1])))
            pieces.append(cylinder(1.55, 19.4, TOP, stem))
        else:
            pieces.append(cylinder(1.55, top + .8, TOP, stem))

    if min(area for module in bearing.values() for area in module) < .75:
        raise ValueError(f"Retainer contact misses its PCB bearing area: {bearing}")

    feet = [cylinder(3, FOOT, TOP, xy) for xy in ANCHORS]
    clearance = [cylinder(1.4, FOOT - .1, TOP + .1, xy) for xy in ANCHORS]
    heads = [cylinder(2.35, 27, TOP + .1, xy) for xy in ANCHORS]
    frame = pieces[0].multiFuse(pieces[1:] + feet).cut(
        Part.makeCompound(clearance + heads)
    ).removeSplitter()
    require_solid("Carrier retainer", frame)

    bosses = Part.makeCompound([cylinder(3, .55, FOOT, xy) for xy in ANCHORS])
    taps = Part.makeCompound([cylinder(1.025, 1.4, FOOT + .1, xy) for xy in ANCHORS])
    rear = rear.fuse(bosses).cut(taps).removeSplitter()
    require_solid("Retainer mounting bosses", rear)
    collisions = intersections({"CarrierRetainer": frame, **pads}, obstacles)
    collisions.extend(intersections({"CarrierRetainer": frame}, {"RearCover": rear}))
    collisions.extend(intersections({"RetainerFeet": bosses}, obstacles))
    if collisions:
        locations = intersections(
            {str(index): shape for index, shape in enumerate(pieces + feet)}, obstacles
        )
        raise ValueError(f"Carrier retainer interference: {collisions}; features: {locations}")
    return rear, frame, {"anchors_xy_mm": ANCHORS, "pad_bearing_mm2": bearing,
                         "collision_mm3": 0, "nominal_pad_thickness_mm": .8}
