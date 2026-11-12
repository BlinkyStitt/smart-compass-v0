"""Check a mechanical fit model against the existing narrow enclosure solids."""

import itertools
import json
from pathlib import Path
import sys

import FreeCAD as App
import MeshPart
import Part

from layout import BASELINE, RETAINED_PRINTS, ROOT, read_layout, schedule, write_schedule

sys.path.insert(0, str(ROOT / "designs/stacked"))
import battery_access
import control_fixture
import harness_plan
from led_retention import board_washers
from pcb_placement import CARRIER_MOUNT_DRILL_MM, SOCKET_DRILL_MM, pcb_text
import rear_cover
import sparkle_mount
from service_slack import plan as service_slack_plan

Vector = App.Vector
Z_AXIS = Vector(0, 0, 1)
MODULE_OBJECTS = {
    "IMU": ("IMU", "IMUPCB", "IMUComponents"),
    "BLACKPILL": ("BlackPill", "BlackPillPCB", "BlackPillUnderboardReservation", "BlackPillLoadedReservation"),
    "GPS": ("GPS", "GPSPCB", "GPSComponents"),
    "RADIO": ("Radio", "RadioPCB", "RadioUnderboardReservation", "RadioLoadedReservation"),
    "BOOST": ("Boost5V", "BoostPCB", "BoostComponents", "BoostTerminalX1", "BoostTerminalX2"),
}
BUTTONS = {"Start": (72, 22), "Mode": (-72, -39), "Action": (73, 2.5)}
BUTTON_PANEL_RADIUS = 6.8
BUTTON_CUTOUT_HALF_WIDTH = 6.45


def box(bounds):
    lower, upper = bounds
    return Part.makeBox(*(b - a for a, b in zip(lower, upper)), Vector(*lower))


def cylinder(radius, bottom, top, xy):
    return Part.makeCylinder(radius, top - bottom, Vector(*xy, bottom))


def button_opening(xy, radius, half_width, bottom, top):
    x, y = xy
    flat_limit = box(([x - half_width, y - radius, bottom],
                      [x + half_width, y + radius, top]))
    return cylinder(radius, bottom, top, xy).common(flat_limit)


def panel_button(xy):
    """APEM ICP3FAD2, with a wrench/nut and flying-lead reservation."""
    face = cylinder(8.75, -5, 0, xy)
    collar = button_opening(xy, 6.75, 6.4, 0, 2)
    nut_and_tool = cylinder(9.5, 2, 4.5, xy)
    body = cylinder(6, 4.5, 14, xy)
    exit = cylinder(5.4, 14, 23, xy)
    return Part.makeCompound([face, collar, nut_and_tool, body, exit])


def at_pose(shape, entry, pose, z):
    old = entry.get("mount_datum", entry.get("centre"))
    shape = shape.copy()
    shape.translate(Vector(-old[0], -old[1], -entry["pcb_bottom_z_mm"]))
    shape.rotate(Vector(), Z_AXIS, pose["rotation_deg"] - entry["rotation_deg"])
    shape.translate(Vector(*pose["datum_xy_mm"], z))
    return shape


def require_solid(label, shape):
    if not shape.isValid() or len(shape.Solids) != 1 or shape.Volume <= 0:
        raise ValueError(f"{label} must be a single valid solid")


def intersections(moving, fixed):
    hits = []
    for a, a_shape in moving.items():
        for b, b_shape in fixed.items():
            if not a_shape.BoundBox.intersect(b_shape.BoundBox):
                continue
            overlap = a_shape.common(b_shape).Volume
            if overlap > 0.001:
                hits.append([a, b, round(overlap, 5)])
    return hits


def make_board(spec, pads):
    z = spec["board_bottom_z_mm"]
    top = spec["board_top_z_mm"]
    points = [Vector(*xy, z) for xy in spec["outline_xy_mm"]]
    blank = Part.Face(Part.makePolygon(points + points[:1])).extrude(Vector(0, 0, top - z))
    require_solid("Carrier outline", blank)
    drills = []
    for row in pads:
        xy = row["x_mm"], row["y_mm"]
        # Reserve one full 2.54 mm socket housing per populated position.
        if not blank.isInside(Vector(*xy, (z + top) / 2), .01, False):
            raise ValueError(f"Socket outside carrier outline: {row}")
        x, y = xy
        margin = box(([x - 1.27, y - 1.27, z], [x + 1.27, y + 1.27, top]))
        if margin.cut(blank).Volume > .001:
            raise ValueError(f"Incomplete socket footprint: {row}")
        drills.append(cylinder(SOCKET_DRILL_MM / 2, z - .1, top + .1, xy))
    for xy in spec["mount_xy_mm"]:
        if cylinder(2.6, z, top, xy).cut(blank).Volume > .001:
            raise ValueError(f"Mount washer outside carrier: {xy}")
        if any((Vector(*xy, 0) - Vector(row["x_mm"], row["y_mm"], 0)).Length < 3.8
               for row in pads):
            raise ValueError(f"Mount enters socket footprint: {xy}")
        drills.append(cylinder(CARRIER_MOUNT_DRILL_MM / 2, z - .1, top + .1, xy))
    board = blank.cut(Part.makeCompound(drills))
    require_solid("Drilled carrier gauge", board)
    return board


def add_part(doc, name, shape, color, transparency=0):
    item = doc.addObject("Part::Feature", name)
    item.Shape = shape
    item.ViewObject.ShapeColor = color
    item.ViewObject.Transparency = transparency
    return item


def model(baseline, spec):
    ports = schedule(spec)
    sockets = [row for row in ports if row["connection"] == "dock socket"]
    p = harness_plan.parameters()
    entries = {row["name"]: row for row in p["electronics"]}
    z = spec["module_bottom_z_mm"]
    module_shapes = {}
    for module, (entry, *objects) in MODULE_OBJECTS.items():
        pose = spec["modules"][module]
        module_shapes[module] = Part.makeCompound([
            at_pose(baseline.getObject(name).Shape, entries[entry], pose, z) for name in objects
        ])
    sparkle, _ = sparkle_mount.source_module()
    pose = spec["modules"]["SPARKLE"]
    sparkle.translate(Vector(-25.4, -16.51, 0))
    sparkle.rotate(Vector(), Z_AXIS, pose["rotation_deg"])
    sparkle.translate(Vector(*pose["datum_xy_mm"], z))
    module_shapes["SPARKLE"] = sparkle

    latch = baseline.getObject("LatchModule").Shape.copy()
    # The original latch is centred at (0, -77), with PCB underside at 12.2 mm.
    latch.translate(Vector(0, 81, z - 12.2))
    module_shapes["Latch"] = latch
    for name, xy in BUTTONS.items():
        module_shapes[f"{name}Button"] = panel_button(xy)
    board = make_board(spec, sockets)
    bottom = spec["board_bottom_z_mm"]
    stock_battery = battery_access.native_shapes(battery_access.definition(), "narrow")
    old_controls = control_fixture.native_shapes(
        *((p["control_" + key + "_x"], p["control_" + key + "_y"])
          for key in ("switch", "start", "mode", "action")),
        switch_rotation_deg=p["control_switch_rotation_deg"],
        guard_mount_offset_mm=p["control_guard_mount_offset"], design="narrow",
    )
    # The legacy button stacks leave with their three panel apertures. Keep
    # the actual disconnect land and the existing battery bay cut.
    screw_centres = [baseline.getObject(f"RearScrew{i}").Shape.BoundBox.Center for i in range(6)]
    rear_points = [(centre.x, centre.y) for centre in screw_centres]
    rear = rear_cover.native_blank(p["case_diameter"] / 2, rear_points, p["rear_vents_xy_mm"],
                                  stock_battery, old_controls)
    # Replace the obsolete button mounts with direct sealed panel mounts.
    for key in ("start", "mode", "action"):
        xy = (p[f"control_{key}_x"], p[f"control_{key}_y"])
        rear = rear.fuse(cylinder(11, 0, 2, xy))
    # Preserve the previous rib pattern under the new panel. Keep a
    # continuous 0.8 mm skin and full-thickness lands at the new mounts.
    ribs = rear.common(baseline.getObject("RearCover").Shape)
    skin = rear.common(box(([-101, -101, 0], [101, 101, .8])))
    rear = ribs.fuse(skin)
    supports = [cylinder(2.7, .7, bottom, xy) for xy in spec["mount_xy_mm"]]
    supports.extend(cylinder(11, .7, 2, xy) for xy in BUTTONS.values())
    rear = rear.fuse(Part.makeCompound(supports))
    # M2 tap pilots open to the inside. Keep 1 mm of material to close
    # each fastener path through the rear cover.
    holes = [cylinder(.8, 1, bottom + .1, xy) for xy in spec["mount_xy_mm"]]
    holes.extend(button_opening(xy, BUTTON_PANEL_RADIUS, BUTTON_CUTOUT_HALF_WIDTH, -.1, 2.1)
                 for xy in BUTTONS.values())
    rear = rear.cut(Part.makeCompound(holes)).removeSplitter()
    require_solid("Carrier rear panel", rear)

    # Keep all battery geometry in the collision test. Use the original
    # radio's routed antenna as a clearance obstacle until RF is reviewed.
    names = (set(battery_access.part_names("narrow")) |
             {"ElectronicsShell", "FibonacciPCB", "RadioAntenna", "PowerDisconnect", "SwitchGuard"})
    fixed = {name: baseline.getObject(name).Shape for name in sorted(names)}
    fixed["CarrierRearPanel"] = rear
    # Reserve the two stock Sparkle exits independently. These clearances
    # constrain connector selection; a particular cable still needs a fit check.
    exits = {
        "SparkleBarrelExit": box(([34.26, 46, 13], [49.26, 55, 22])),
        "SparkleTerminalExit": box(([-32, 32.6, 13], [-17.5, 55, 21])),
    }
    products = {"Carrier": board, **module_shapes, **exits}
    overlaps = intersections(products, fixed)
    overlaps.extend(intersections(exits, {name: shape for name, shape in module_shapes.items()
                                          if name != "SPARKLE"}))
    for a, b in itertools.combinations(module_shapes, 2):
        overlaps.extend(intersections({a: module_shapes[a]}, {b: module_shapes[b]}))
    slack = {row["name"] + "ServiceFold": box(row["storage_bounds_mm"])
             for row in service_slack_plan(spec)["runs"]}
    overlaps.extend(intersections(slack, {**products, **fixed}))
    for a, b in itertools.combinations(slack, 2):
        overlaps.extend(intersections({a: slack[a]}, {b: slack[b]}))
    if overlaps:
        raise ValueError("Carrier floorplan collisions: " + json.dumps(overlaps))
    products.update(slack)

    for name, shape in products.items():
        if shape.BoundBox.ZMax > 30:
            raise ValueError(f"{name} enters the optical PCB clearance")
    return products, fixed, ports


def mass_budget(board, rear, spec):
    inventory = json.loads((BASELINE / "parts.json").read_text())
    prints = {row["source_part"] for row in inventory["print_parts"]}
    if not RETAINED_PRINTS <= prints:
        raise ValueError("Retained print census disagrees with baseline")
    removed = prints - RETAINED_PRINTS
    components = {row["id"]: row for row in inventory["components"]}

    def mass(name):
        row = components[name]
        return row["mass_g_per_unit"] * row["installed_quantity"]

    loom = {row["id"] for row in json.loads((BASELINE / "loom-check.json").read_text())["cut_list"]}
    loom.update(name for name in components if name.startswith((
        "splice_", "HarnessSpliceTie", "HarnessSpliceTape",
    )))
    substrate = board.Volume * spec["laminate_density_g_cm3"] / 1000
    # Four completely filled 35 um copper layers bound the copper allowance
    # at that stack-up. Plating, sockets and other parts are accounted below.
    copper = board.Volume / spec["board_thickness_mm"] * 4 * .035 * 8.96 / 1000
    panel_delta = rear.Volume * 1.27 / 1000 - mass("RearCover")
    removed_mass = sum(mass(name) for name in sorted(removed | loom))
    slack_mass = service_slack_plan(spec)["added_wire_mass_allowance_g"]
    return {
        "baseline_worn_g": inventory["mass_estimate"]["total_worn"]["nominal_g"],
        "retained_baseline_prints": len(RETAINED_PRINTS),
        "prints_replaced_by_carrier_and_direct_mounts": len(removed),
        "old_loom_and_mounts_g": removed_mass,
        "carrier_laminate_g": substrate,
        "carrier_copper_allowance_g": copper,
        "rear_panel_change_g": panel_delta,
        "service_slack_wire_allowance_g": slack_mass,
        "break_even_allowance_for_new_harness_hardware_and_parts_g":
            removed_mass - substrate - copper - panel_delta - slack_mass,
    }


def build(destination):
    spec = read_layout()
    baseline = App.openDocument(str(BASELINE / "stacked-fibonacci.FCStd"))
    try:
        products, fixed, ports = model(baseline, spec)
        washers, washer_bearing = board_washers(baseline)
        rear = fixed["CarrierRearPanel"]
        battery = battery_access.definition()
        battery_fit = battery_access.native_check(
            battery, "narrow", battery_access.native_shapes(battery, "narrow"),
            surroundings=[("RearCover", rear), *products.items()],
        )
        doc = App.newDocument("PlugInCarrier")
        try:
            items = []
            for name, shape in products.items():
                if name.endswith("ServiceFold"):
                    items.append(add_part(doc, name, shape, (.20, .57, .82), 75))
                else:
                    transparency = 70 if name.endswith(("Exit", "Button")) else 0
                    items.append(add_part(doc, name, shape, (.22, .56, .36), transparency))
            for name, shape in washers.items():
                items.append(add_part(doc, name, shape, (.8, .8, .68)))
            for name in ("CarrierRearPanel", "BatteryCradle", "BatteryDoor", "ElectronicsShell", "FibonacciPCB"):
                item = add_part(doc, name, fixed[name], (.32, .37, .4), 75 if name != "BatteryCradle" else 35)
                items.append(item)
                if name in ("ElectronicsShell", "FibonacciPCB"):
                    item.Visibility = False
            doc.recompute()
            Gui.activeDocument().activeView().viewTop()
            Gui.activeDocument().activeView().fitAll()
            doc.saveAs(str(destination / "carrier-fit.FCStd"))
            Part.export(items, str(destination / "carrier-fit.step"))
            gauge = products["Carrier"].copy()
            gauge.translate(Vector(0, 0, -spec["board_bottom_z_mm"]))
            MeshPart.meshFromShape(Shape=gauge, LinearDeflection=.05, AngularDeflection=.1,
                                   Relative=False).write(str(destination / "carrier-fit-gauge.stl"))
            write_schedule(destination / "terminal-schedule.csv", ports)
            (destination / "carrier-placement.kicad_pcb").write_text(pcb_text(spec, ports))
            result = {
                "scope": "Mechanical fit pilot with nominal module envelopes and drill gauge",
                "body_depth_mm": json.loads((BASELINE / "parts.json").read_text())["dimensions_mm"]["body_depth"],
                "carrier_bounds_mm": [gauge.BoundBox.XLength, gauge.BoundBox.YLength, gauge.BoundBox.ZLength],
                "mass_budget": mass_budget(gauge, rear, spec),
                "module_top_z_mm": {name: shape.BoundBox.ZMax for name, shape in products.items()},
                "carrier_loom_conductors_target": sum(spec["external_harnesses"].values()),
                "service_slack": service_slack_plan(spec),
                "socket_pin_positions": sum(row["connection"] == "dock socket" for row in ports),
                "closed_collisions": [],
                "led_washer_minimum_nominal_bearing_mm2": min(washer_bearing),
                "battery_motion": {
                    "door_clearance_mm": battery_fit["door_continuous_clearance_mm"],
                    "keeper_clearance_mm": battery_fit["keeper_continuous_clearance_mm"],
                    "minimum_cell_clearance_mm": min(battery_fit["cell_continuous_clearance_mm"].values()),
                    "mount_bearing": battery_fit["mount_bearing"],
                },
                "status": "Fit model only. Cable selection, circuit routing and physical checks remain open.",
            }
            (destination / "fit-check.json").write_text(json.dumps(result, indent=2) + "\n")
        finally:
            App.closeDocument(doc.Name)
    finally:
        App.closeDocument(baseline.Name)
