"""Check the Rev A carrier with mated harness connectors in FreeCAD."""

import hashlib
import json
from itertools import combinations
from pathlib import Path

import FreeCAD as App
import MeshPart
import Part
from layout import REVISED_PRINTS
from native import (
    BASELINE,
    BUTTONS,
    BUTTON_CUTOUT_HALF_WIDTH,
    BUTTON_PANEL_RADIUS,
    battery_access,
    box,
    button_opening,
    cylinder,
    harness_plan,
    intersections,
    model,
    read_layout,
    require_solid,
)

from prints import normalize_stl_bed, orientation
from solid_clearance import bounds
from integrated_parts import BACK_PLATES, contact_cradle, disconnect_guard
from seals import LEGACY_HINGE, check_hatch, front_seals, hatch
from retainer import build as build_retainer
from usb_bay import power_bay

# Pitch, end overhang, cross-row bounds and mated height, in millimeters.
# These reservations include housing tolerance. The first cable build must
# check the installed crimps, lead exits and access to the locking tab.
MATED_ENVELOPES = {
    "VH": (3.96, 2.05, -5.0, 4.0, 16.5),
    "XH": (2.5, 1.55, -3.55, 2.6, 12),
    "PH": (2.0, 1.55, -2.9, 2.4, 10),
}


def component_envelopes(z):
    spec = json.loads(Path(__file__).with_name("routed-components.json").read_text())
    parts = {}
    for ref, (_, family, (x, y, angle), nets) in spec["connectors"].items():
        pitch, end, ymin, ymax, height = MATED_ENVELOPES[family]
        shape = box(
            ([-end, ymin, z], [(len(nets) - 1) * pitch + end, ymax, z + height])
        )
        shape.rotate(App.Vector(), App.Vector(0, 0, 1), angle)
        shape.translate(App.Vector(x, y, 0))
        parts[ref] = shape

    for ref, (_, _, (x, y, angle), _) in spec["parts"].items():
        if ref.startswith("F"):
            bounds = ([x + 1.35, y - 1.45, z], [x + 8.81, y + 1.45, z + 3.2])
        else:
            dx, dy = (1.7, 1.6) if ref.startswith(("Q", "U")) else (1.35, 0.85)
            if angle % 180:
                dx, dy = dy, dx
            bounds = ([x - dx, y - dy, z], [x + dx, y + dy, z + 1.3])
        parts[ref] = box(bounds)
    return parts


def close_rear_vents(rear):
    vent_points = harness_plan.parameters()["rear_vents_xy_mm"]
    for xy in vent_points:
        rear = rear.fuse(cylinder(3.3, 0, 2, xy))
        if cylinder(3, 0, 2, xy).cut(rear).Volume > 0.001:
            raise ValueError(f"Rear vent is still open at {xy}")
    return rear.removeSplitter()


def fit_battery(battery, rear):
    shapes = battery_access.native_shapes(battery, "narrow")
    x, y, z = shapes["hinge_axis"]
    # Provide a local recess above the three moving knuckles. Preserve the
    # fixed outer knuckles, battery mounts, and the positive door catch.
    direction = App.Vector(1, 0, 0)
    radius = battery["door"]["hinge_radius_mm"] + 0.45
    relief = Part.makeCompound([
        Part.makeCylinder(radius, 12.8, App.Vector(x + offset - 6.4, y, z), direction)
        for offset in (-26, 0, 26)
    ])
    rear = rear.cut(relief).removeSplitter()
    shapes["rear_interface"] = shapes["rear_interface"].cut(relief).removeSplitter()
    bore = Part.makeCylinder(1.8, 110, App.Vector(x - 55, y, z), direction)
    shapes["BatteryDoor"] = shapes["BatteryDoor"].cut(bore).removeSplitter()
    pivot = shapes["keeper_axis"][:2]
    shapes["BatteryKeeper"] = shapes["BatteryKeeper"].cut(
        cylinder(1.8, -1, 2, pivot)
    ).removeSplitter()
    return rear, shapes


def rear_seal(rear, shell):
    # Keep a 0.55 mm outer lip. The 0.8 mm depth gives 20 percent nominal
    # compression on a 1 mm silicone cord against the existing shell face.
    def ring(bottom, top):
        return cylinder(99.45, bottom, top, (0, 0)).cut(
            cylinder(98.05, bottom - .1, top + .1, (0, 0))
        )

    # Bridge the interrupted lower shell seat below the suspension eyelets.
    # The added ring stays within the 200 mm perimeter and below the straps.
    shell_seat = cylinder(100, 2, 3.5, (0, 0)).cut(
        cylinder(97.9, 1.9, 3.6, (0, 0))
    )
    shell = shell.fuse(shell_seat)
    require_solid("Rear seal shell", shell)

    groove = ring(1.2, 2)
    contact = ring(2, 2.05)
    if groove.cut(rear).Volume > 0.001 or contact.cut(shell).Volume > 0.001:
        raise ValueError("Rear seal needs a continuous groove and shell bearing face")
    rear = rear.cut(ring(1.2, 2.1)).removeSplitter()
    floor = ring(1.1, 1.2)
    if floor.cut(rear).Volume > 0.001:
        raise ValueError("Rear seal groove has an interrupted floor")
    return rear, shell


def control_seals(rear):
    # The APEM O-ring seats under the 17.5 mm flange. Require the full land.
    for xy in BUTTONS.values():
        land = cylinder(8.75, 0, 0.2, xy).cut(
            button_opening(xy, BUTTON_PANEL_RADIUS, BUTTON_CUTOUT_HALF_WIDTH, -.1, .3)
        )
        if land.cut(rear).Volume > 0.001:
            raise ValueError(f"Missing button seal land at {xy}")
    params = harness_plan.parameters()
    xy = params["control_switch_x"], params["control_switch_y"]
    # C&K 759D02000 on the stock 7201SYZQE. The boot replaces its outer
    # hex nut. This outer reservation includes room for the flexible skirt.
    seat = cylinder(6.65, 0, .2, xy).cut(cylinder(3.4, -.1, .3, xy))
    if seat.cut(rear).Volume > 0.001:
        raise ValueError("Missing disconnect boot seal land")
    return cylinder(6.65, -3.5, 0, xy).fuse(
        cylinder(8.4, -16.7, -3.5, xy)
    )


def export_print(directory, name, shape):
    require_solid(name, shape)
    solid = shape.copy()
    # Put the bezel groove, retainer toes and rear guard above the bed.
    axis, angle = ([1, 0, 0], 180) if name in {"CarrierRetainer", "FrontBezel", "RearCover"} else orientation(name)
    if angle:
        solid.rotate(App.Vector(), App.Vector(*axis), angle)
    bb = bounds(solid)
    solid.translate(App.Vector(-bb.XMin, -bb.YMin, -bb.ZMin))
    mesh = MeshPart.meshFromShape(
        Shape=solid, LinearDeflection=0.02, AngularDeflection=0.08, Relative=False
    )
    if not mesh.isSolid() or mesh.countComponents() != 1:
        raise ValueError(f"{name} must produce one watertight mesh")
    path = directory / f"{name}.stl"
    mesh.write(str(path))
    normalize_stl_bed(path)
    return {
        "file": path.name,
        "source_part": name,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "print_bounds_mm": [bb.XLength, bb.YLength, bb.ZLength],
    }


def check(output):
    output.unlink(missing_ok=True)
    baseline = App.openDocument(str(BASELINE / "stacked-fibonacci.FCStd"))
    try:
        layout = read_layout()
        products, fixed, _ = model(baseline, layout)
        parts = component_envelopes(layout["board_top_z_mm"])
        rear = close_rear_vents(fixed["CarrierRearPanel"])
        stock_shell = fixed["ElectronicsShell"]
        rear, shell = rear_seal(rear, stock_shell)
        rear_seat = shell.cut(stock_shell)
        bezel, shell = front_seals(baseline, shell)
        fixed["ElectronicsShell"] = shell
        seal_clearance = {
            name: baseline.getObject(name).Shape
            for name in ("NecklaceAttachmentReturn0", "NecklaceAttachmentReturn1")
        }
        collisions = intersections({"ElectronicsShell": shell}, seal_clearance)
        collisions.extend(intersections({"ElectronicsShell": shell}, products))
        battery = battery_access.definition()
        rear, battery_shapes = fit_battery(battery, rear)
        lid, rear, lid_sweep = hatch(battery, rear)
        cradle, cradle_joins, contact_fit = contact_cradle(battery, battery_shapes)
        rear, guard, guard_fit = disconnect_guard(rear)
        rear, power_parts, wall_cable, install_paths = power_bay(rear)
        fixed["CarrierRearPanel"] = rear
        fixed["BatteryCradle"] = cradle
        for name in BACK_PLATES:
            del fixed[name]
        del fixed["SwitchGuard"]
        for name in ("BatteryDoor", "BatteryKeeper"):
            fixed[name] = battery_shapes[name]
        obstacles = {**fixed, **products}
        obstacles.pop("Carrier")  # The parts sit on the carrier's top face.
        parts["WallChargerEnvelope"] = box(([-14, -95, 3.5], [10, -67, 9.5]))
        # 28 × 28 mm selector, including PCB, flat leads and insulating mount.
        parts["WallLedPowerEnvelope"] = box(([-58, 33, 3.5], [-30, 61, 9]))
        parts.update(power_parts)
        collisions.extend(intersections(power_parts, {"RearCover": rear}))
        collisions.extend(intersections({"USBWallCable": wall_cable}, {
            "RearCover": rear, "InstalledBatteryHatch": lid,
        }))
        parts["DisconnectBoot"] = control_seals(rear)
        disconnect = obstacles.pop("PowerDisconnect")
        collisions.extend(intersections(parts, obstacles))
        collisions.extend(intersections(
            {name: shape for name, shape in parts.items() if name != "DisconnectBoot"},
            {"PowerDisconnect": disconnect},
        ))
        collisions.extend(intersections({"RearCover": rear}, products))
        collisions.extend(intersections({"DisconnectGuard": guard}, {
            **parts, "PowerDisconnect": disconnect, **products,
        }))
        collisions.extend(intersections({"CradleRoofJoins": cradle_joins},
                                        {**parts, **products, "ElectronicsShell": shell}))
        for a, b in combinations(parts, 2):
            collisions.extend(intersections({a: parts[a]}, {b: parts[b]}))
        hatch_obstacles = {name: shape for name, shape in {**fixed, **products, **parts}.items()
                           if name not in LEGACY_HINGE | {"BatteryDoor"}}
        hatch_obstacles.update({f"RearScrew{i}": baseline.getObject(f"RearScrew{i}").Shape
                                for i in range(6)})
        hatch_fit = check_hatch(battery, lid, lid_sweep, hatch_obstacles)
        retainer_obstacles = {name: shape for name, shape in hatch_obstacles.items()
                              if name != "CarrierRearPanel"}
        rear, retainer, retainer_fit = build_retainer(
            baseline, layout, products, retainer_obstacles, rear
        )
        collisions.extend(intersections(install_paths, {"RearCover": rear}))
        if collisions:
            raise ValueError(f"Rev A carrier interference: {collisions}")
        print(f"REV A CLOSED FIT PASS ({len(parts)} installed envelopes)", flush=True)
        step_path = output.with_name("usb-c-rear-cover.step")
        rear.exportStep(str(step_path))
        reopened = Part.read(str(step_path))
        require_solid("USB-C rear cover STEP", reopened)
        step_collisions = intersections(install_paths, {"RearCoverSTEP": reopened})
        if step_collisions:
            raise ValueError(f"USB-C board installation in STEP: {step_collisions}")
        print_solids = {**fixed, "RearCover": rear, "FrontBezel": bezel,
                        "BatteryHatch": lid, "CarrierRetainer": retainer}
        print_parts = [export_print(output.parent, name, print_solids[name])
                       for name in sorted(REVISED_PRINTS)]
        motion = battery_access.native_check(
            battery,
            "narrow",
            battery_shapes,
            surroundings=[
                ("RearCover", rear),
                ("RearSealShellSeat", rear_seat),
                ("CarrierRetainer", retainer),
                ("CradleRoofJoins", cradle_joins),
                *products.items(),
                *parts.items(),
            ],
        )
        if min(motion["door_continuous_clearance_mm"],
               motion["keeper_continuous_clearance_mm"]) < 0.15:
            raise ValueError(f"Rev A battery motion clearance is below 0.15 mm: {motion}")
        output.write_text(
            json.dumps(
                {
                    "closed_collisions": collisions,
                    "battery_motion": motion,
                    "battery_motion_scope": (
                        "Keeper and cell checks include the reference hinged door as an extra "
                        "obstacle. The installed hatch has its own withdrawal check."
                    ),
                    "battery_hatch": hatch_fit,
                    "battery_contacts": contact_fit,
                    "disconnect_guard": guard_fit,
                    "carrier_retainer": retainer_fit,
                    "integrated_usb_c": {
                        "closed_wall_cable_interference_mm3": 0,
                        "rear_bay_depth_mm": 21,
                        "board_installation_paths": list(install_paths),
                        "port_access_envelope": "24 x 11 mm plug and 4 mm cable",
                    },
                    "print_parts": print_parts,
                },
                indent=2,
            )
            + "\n"
        )
        print("REV A BATTERY MOTION PASS", flush=True)
    finally:
        App.closeDocument(baseline.Name)
