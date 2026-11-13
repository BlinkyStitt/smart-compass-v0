"""Integrated contact seats and disconnect protection for the Rev A print kit."""

import math
from itertools import product

import FreeCAD as App
import Part

from native import box, cylinder, harness_plan, intersections, require_solid
from solid_clearance import bounds

# Acceptance datums for the two revised front clamps. Allow both released
# terminals to slide past the complete positive guard during withdrawal.
KEYED_TIP_GAP_MM = (74.12, 74.20)
KEYED_NEGATIVE_STOP_MM = (1.82, 1.90)
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


def positive_contact_key(battery, shapes):
    """Recess the positive plunger in the front clamp without adding a print."""
    contact, cell = battery["contact"], battery["cell"]
    cx, cy = battery["designs"]["narrow"]["cell_centre_xy_mm"]
    z = battery["cradle"]["cell_axis_z_mm"]
    stock = shapes["BatteryContactPFront"]
    tip_x = cx + sum(contact["unloaded_tip_gap_mm"]) / 4
    face = tip_x - .51
    end = stock.BoundBox.XMin + .5
    aperture = 6.2
    outer = 8.5
    axis = App.Vector(1, 0, 0)

    def round_end(radius, start, finish, y=cy, height=z):
        return Part.makeCylinder(radius, finish - start, App.Vector(start, y, height), axis)

    # A complete ring blocks the edge of a flat terminal even if the cell
    # is offset toward the hatch during insertion. The cell clears the ring
    # axially when pushed against the revised negative stop.
    guard = round_end(outer, face, end).cut(
        round_end(aperture, face - .1, end + .1)
    )
    clamp = stock.fuse(guard).removeSplitter()
    require_solid("Keyed positive contact clamp", clamp)
    added = clamp.cut(stock)
    obstacles = {name: shape for name, shape in shapes.items()
                 if name.startswith("Battery")
                 and name not in {"BatteryCell", "BatteryContactP", "BatteryContactPFront"}}
    collisions = intersections({"PositiveContactKey": added}, obstacles)
    if collisions:
        raise ValueError(f"Positive contact key interference: {collisions}")

    # These are assembly acceptance limits. The cell maker does not tolerance
    # the button diameter, height or concentricity on its public drawing.
    recess = (.42, .56)
    height = (1.0, 1.6)
    diameter = (5.0, 9.0)
    offset = 1.0  # Total radial offset, including button concentricity.
    reverse_protrusion = .27  # Maximum centre lead over the stop bearing face.
    minimum_release = battery["removal"]["positive_end_release_gap_mm"]
    stroke = contact["full_stroke_mm"] - contact["full_stroke_tolerance_mm"]
    results = []
    for length, gap, stop, key_depth, button_height in product(
        cell["length_mm"], contact["unloaded_tip_gap_mm"],
        contact["negative_stop_compression_mm"], recess, height,
    ):
        compression = length - gap
        positive_stop = button_height - key_depth
        negative_release = gap + stop - length
        shoulder_release = negative_release + positive_stop
        if not (compression > 0 and 0 < positive_stop < stroke
                and compression < stop < stroke and negative_release - key_depth >= .05
                and shoulder_release > minimum_release):
            raise ValueError("Keyed contact travel fails at an assembly tolerance corner")
        results.append((positive_stop, negative_release, shoulder_release))

    # The insertion/removal plane is ahead of the complete ring. No
    # positive terminal material, even at the maximum accepted diameter,
    # reaches the guard while the cell moves toward or away from the hatch.
    released_gap = min(row[1] for row in results)
    withdrawal_gap = released_gap - recess[1]
    clearance = min(row[2] for row in results)
    pin_radius = contact["drawing"]["tip_diameter_mm"] / 2
    if (aperture - diameter[1] / 2 - offset < .15
            or diameter[0] / 2 - offset <= pin_radius):
        raise ValueError("A correctly oriented button fails the radial fit")

    # A flat end that could touch the tip must span the circular guard.
    # Check the aligned and lateral grazing cases, using the smallest cell
    # and the farthest offset where its face could still cover the pin.
    reverse_gap = recess[0] - reverse_protrusion
    flat_radius = cell["diameter_mm"][0] / 2
    for radial in (0, offset, flat_radius + pin_radius):
        flat_end = round_end(flat_radius, face, face + .05, cy, z - radial)
        bearing_area = flat_end.common(added).Volume / .05
        if bearing_area < 25 or reverse_gap <= 0:
            raise ValueError("Reversed flat-end dummy can bypass the positive guard")
    return clamp, added, {
        "button_diameter_mm": diameter,
        "button_height_mm": height,
        "recess_acceptance_mm": recess,
        "maximum_radial_button_offset_mm": offset,
        "maximum_reverse_end_centre_lead_mm": reverse_protrusion,
        "reverse_tip_clearance_min_mm": reverse_gap,
        "button_release_min_mm": released_gap,
        "shoulder_release_min_mm": clearance,
        "button_clearance_ahead_of_guard_min_mm": withdrawal_gap,
        "axial_tolerance_corners": len(results),
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
