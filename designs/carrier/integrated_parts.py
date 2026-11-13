"""Integrated contact seats and disconnect protection for the Rev A print kit."""

import math

import Part

from native import box, cylinder, harness_plan, intersections, require_solid
from solid_clearance import bounds

BACK_PLATES = ("BatteryContactNBack", "BatteryContactPBack")


def contact_cradle(battery, shapes):
    """Retain the original contact datums and join the fixed plates to the roof."""
    cradle = shapes["BatteryCradle"]
    _, cy = battery["designs"]["narrow"]["cell_centre_xy_mm"]
    plates = [shapes[name] for name in BACK_PLATES]
    ribs = []
    for plate in plates:
        plate_box = plate.BoundBox
        # Keep the join above the contact, wire exit and M2 screw axes.
        ribs.append(box(([plate_box.XMin, cy - 5, 20], [plate_box.XMax, cy + 5, 25.35])))
    unified = cradle.multiFuse(plates + ribs).removeSplitter()
    require_solid("Battery cradle with integral contact seats", unified)
    original = Part.makeCompound([cradle, *plates])
    if original.cut(unified).Volume > .001:
        raise ValueError("Integrated cradle lost an original contact seat or bearing face")
    added = unified.cut(original).removeSplitter()
    if added.Volume <= 0:
        raise ValueError("Integrated cradle is missing its roof joins")

    # Cell withdrawal, both service motions and the front clamp insertion
    # stay below or inboard of these roof joins. Use the original exact sweep
    # for the original solids and bound the added material independently.
    cx, _ = battery["designs"]["narrow"]["cell_centre_xy_mm"]
    length = battery["cell"]["length_mm"][1]
    cell_shift = max(battery["contact"]["negative_stop_compression_mm"])
    protected_cell_x = length / 2 + cell_shift
    join_bounds = [bounds(shape) for shape in added.Solids]
    clearance = min(max(bb.XMin - cx, cx - bb.XMax) for bb in join_bounds) - protected_cell_x
    if clearance < battery["removal"]["noncontact_clearance_mm"]:
        raise ValueError("A cradle roof join enters the cell withdrawal region")
    if added.BoundBox.ZMin < 21 or added.BoundBox.ZMax > 25.36:
        raise ValueError("A cradle roof join leaves the free upper contact pocket")

    fixed = {name: shape for name, shape in shapes.items()
             if name.startswith("Battery") and name not in {*BACK_PLATES, "BatteryCradle"}}
    collisions = intersections({"CradleRoofJoins": added}, fixed)
    if collisions:
        raise ValueError(f"Cradle roof join interference: {collisions}")
    return unified, added, {
        "integrated_seats": list(BACK_PLATES),
        "cell_withdrawal_lower_bound_mm": clearance,
        "join_volume_mm3": added.Volume,
    }


def disconnect_guard(rear):
    """Put the two open-ended protective ribs on the sealed rear cover."""
    params = harness_plan.parameters()
    sx, sy = params["control_switch_x"], params["control_switch_y"]
    if params["control_switch_rotation_deg"]:
        raise ValueError("Review the integrated guard for a rotated disconnect")
    # Close the two former guard fastener bores. The 3 mm ribs grow from
    # the original panel lands and retain the original 26 mm finger channel.
    offset = params["control_guard_mount_offset"]
    plugs = [cylinder(1.4, 0, 2, (sx + side * 14.5, sy + offset))
             for side in (-1, 1)]
    rear = rear.multiFuse(plugs).removeSplitter()
    for side in (-1, 1):
        bore = cylinder(1.1, 0, 2, (sx + side * 14.5, sy + offset))
        if bore.cut(rear).Volume > .001:
            raise ValueError("Former guard fastener hole is still open")

    rails = [box(([x - 1.5, sy - 9, -19], [x + 1.5, sy + 9, .35]))
             for x in (sx - 14.5, sx + 14.5)]
    guard = Part.makeCompound(rails)
    # Use both switch endpoints and the same 24 mm finger probe as the
    # stock guard. The opening stays clear along the entire throw.
    throw = 10.67 * math.sin(math.radians(25))
    access = cylinder(12, -45.5, -15.5, (sx, sy - throw)).multiFuse([
        cylinder(12, -45.5, -15.5, (sx, sy + throw)),
        box(([sx - 12, sy - throw, -45.5], [sx + 12, sy + throw, -15.5])),
    ])
    if guard.common(access).Volume > .001:
        raise ValueError("Integrated guard blocks disconnect access")
    rear = rear.multiFuse(rails).removeSplitter()
    require_solid("Rear cover with integral disconnect guard", rear)
    return rear, guard, {
        "former_bores_open": False,
        "finger_channel_mm": 26,
        "guard_projection_mm": 19,
    }
