"""Seal seats and the removable, gasketed Rev A battery hatch."""

import FreeCAD as App
import Part

from native import box, cylinder, intersections, require_solid

HATCH_SCREWS = ((-42, -14), (42, -14), (-32, -77.5), (32, -77.5))
LEGACY_HINGE = frozenset({
    "BatteryHingePin", "BatteryHingeNut", "BatteryHingeWasher0", "BatteryHingeWasher1",
})


def annulus(inner, outer, bottom, top):
    return cylinder(outer, bottom, top, (0, 0)).cut(
        cylinder(inner, bottom - .1, top + .1, (0, 0))
    )


def require_material(name, probe, solid):
    missing = probe.cut(solid).Volume
    if missing > .001:
        raise ValueError(f"Interrupted {name} ({missing:.4f} mm³ missing)")


def front_seals(baseline, shell):
    bezel = baseline.getObject("FrontBezel").Shape
    lens = baseline.getObject("FrontMirror").Shape
    diffuser = baseline.getObject("SideDiffuser").Shape
    # Keep the 0.8 mm seal seat on the acrylic face as the optical stack moves.
    # The seal is outside the 89.5 mm viewing aperture.
    lens_face = lens.BoundBox.ZMax
    groove_floor = lens_face + .8
    lens_groove = annulus(90.8, 92.2, lens_face - .01, groove_floor)
    require_material("front mirror bearing land", annulus(90.8, 92.2, lens_face - .05, lens_face), lens)
    require_material("front bezel groove stock", annulus(90.8, 92.2, lens_face, groove_floor), bezel)
    bezel = bezel.cut(lens_groove).removeSplitter()
    require_material("front bezel groove floor", annulus(90.8, 92.2, groove_floor, groove_floor + .1), bezel)

    # The sealant is confined to the two end faces, outside the lit window.
    for z, side in ((14, -1), (34, 1)):
        inside = z + side * .4
        cut_bottom, cut_top = sorted((z - side * .01, inside))
        body_bottom, body_top = sorted((z, inside))
        ring = annulus(98.8, 99.45, body_bottom, body_top)
        require_material("glow band shell shoulder", ring, shell)
        lip_bottom, lip_top = sorted((z, z - side * .05))
        require_material("glow band mating face", annulus(98.8, 99.45, lip_bottom, lip_top), diffuser)
        shell = shell.cut(annulus(98.8, 99.45, cut_bottom, cut_top))
    require_solid("Sealed front bezel", bezel)
    require_solid("Sealed electronics shell", shell)
    return bezel, shell


def rounded_box(x0, y0, x1, y1, radius, bottom, top):
    pieces = [
        box(([x0 + radius, y0, bottom], [x1 - radius, y1, top])),
        box(([x0, y0 + radius, bottom], [x1, y1 - radius, top])),
    ]
    pieces.extend(cylinder(radius, bottom, top, (x, y))
                  for x in (x0 + radius, x1 - radius)
                  for y in (y0 + radius, y1 - radius))
    return pieces[0].multiFuse(pieces[1:]).removeSplitter()


def hatch(battery, rear):
    """Build the one-piece cap, blind rear bosses and conservative withdrawal envelope."""
    bottom, roof = -9.6, -7.6

    def outline(inset, low, high):
        return rounded_box(-63 + inset, -73.5 + inset, 63 - inset,
                           -17.4 - inset, 5 - inset, low, high)

    def wall(low, high):
        return outline(0, low, high).cut(outline(2.6, low - .1, high + .1))

    def groove(low, high):
        return outline(.8, low, high).cut(outline(2.0, low - .1, high + .1))

    # A 1 mm cord sits 0.8 mm deep. A 0.05 mm probe proves that the
    # continuous seat is outside all existing rear openings.
    require_material("battery gasket rear land", groove(0, .05), rear)
    require_material("battery gasket flange", groove(-.9, 0), wall(roof, 0))
    lid = outline(0, bottom, 0).cut(outline(2.6, roof, .1))
    lid = lid.cut(groove(-.8, .1))
    # Keep the four cradle screw heads inside the gasket perimeter.
    cradle = battery["cradle"]
    cy = battery["designs"]["narrow"]["cell_centre_xy_mm"][1]
    head_relief = Part.makeCompound([
        cylinder(2.85, roof, .1, (x, y))
        for x in (-cradle["mount_x_mm"], cradle["mount_x_mm"])
        for y in (cy - cradle["mount_y_offset_mm"], cy + cradle["mount_y_offset_mm"])
    ])
    lid = lid.cut(head_relief)
    require_material("battery hatch groove floor", groove(-.9, -.8), lid)

    boss = Part.makeCompound([cylinder(3.7, .55, 4.95, xy) for xy in HATCH_SCREWS])
    pilots = Part.makeCompound([cylinder(1.25, -.1, 4.1, xy) for xy in HATCH_SCREWS])
    rear = rear.fuse(boss).cut(pilots).removeSplitter()
    ears = [cylinder(5.7, bottom, 0, xy) for xy in HATCH_SCREWS]
    screw_holes = Part.makeCompound([cylinder(1.7, bottom - .1, .1, xy) for xy in HATCH_SCREWS])
    lid = lid.multiFuse(ears).cut(screw_holes)

    # Keep the stock two seating saddles at their original installed height.
    # Extend them to the roof of the new hatch.
    cell_z = battery["cradle"]["cell_axis_z_mm"]
    cell_radius = battery["cell"]["diameter_mm"][1] / 2
    saddles = []
    for x in (-14, 14):
        relief = Part.makeCylinder(cell_radius + .3, 8, App.Vector(x - 4, cy, cell_z),
                                  App.Vector(1, 0, 0))
        saddle = box(([x - 2, cy - 4.5, roof - .1], [x + 2, cy + 4.5, 2.3])).cut(relief)
        saddles.append(saddle)
    lid = lid.multiFuse(saddles).removeSplitter()
    require_solid("Gasketed battery hatch", lid)
    require_solid("Rear panel with hatch pilots", rear)

    # Closed cap and 16 mm of straight withdrawal. The walls and ears are
    # vertical. The saddle recess widens upward at the cell-facing tip, so
    # moving outward only adds material below its initial bottom plane.
    travel = 16
    sweep = Part.makeCompound([
        outline(0, bottom - travel, roof),
        wall(roof - travel, 0).cut(head_relief),
        *(cylinder(5.7, bottom - travel, 0, xy) for xy in HATCH_SCREWS),
        *saddles,
    ])
    return lid, rear, sweep


def check_hatch(battery, lid, sweep, fixed):
    collisions = intersections({"BatteryHatch": lid}, fixed)
    collisions.extend(intersections({"BatteryHatchWithdrawal": sweep}, fixed))
    if collisions:
        raise ValueError(f"Battery hatch interference: {collisions}")
    radius = battery["cell"]["diameter_mm"][0] / 2
    length = battery["cell"]["length_mm"][0]
    _, cy = battery["designs"]["narrow"]["cell_centre_xy_mm"]
    z = battery["cradle"]["cell_axis_z_mm"] - 1
    cell = Part.makeCylinder(radius, length, App.Vector(-length / 2, cy, z), App.Vector(1, 0, 0))
    blocked = lid.common(cell).Volume
    if blocked <= .001:
        raise ValueError("Battery hatch closes over an unseated cell")
    return {"withdrawal_mm": 16, "closed_and_withdrawal_interference_mm3": 0,
            "one_mm_unseated_cell_interference_mm3": blocked}
