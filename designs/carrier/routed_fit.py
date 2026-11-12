"""Check the Rev A carrier with mated harness connectors in FreeCAD."""

import json
from itertools import combinations
from pathlib import Path

import FreeCAD as App
from native import (
    BASELINE,
    battery_access,
    box,
    cylinder,
    harness_plan,
    intersections,
    model,
    read_layout,
    require_solid,
)

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


def pigtail_panel(rear):
    # Heyco M4448 on the rear face, with the elbow pointing down.
    centre = (75, -44)
    vent_points = harness_plan.parameters()["rear_vents_xy_mm"]
    for xy in vent_points:
        rear = rear.fuse(cylinder(3.3, 0, 2, xy))
    reinforcement = cylinder(11.3, 0, 2.4, centre)
    bore = cylinder(6, -0.1, 2.5, centre)
    rear = rear.fuse(reinforcement).cut(bore).removeSplitter()
    require_solid("Pigtail rear cover", rear)

    for xy in vent_points:
        if cylinder(3, 0, 2, xy).cut(rear).Volume > 0.001:
            raise ValueError(f"Rear vent is still open at {xy}")
    seal_land = cylinder(8.5, 0, 2.4, centre).cut(bore)
    if seal_land.cut(rear).Volume > 0.001:
        raise ValueError("Cordgrip needs a continuous flat bearing land")

    # The 38.8 mm overall length includes 8.1 mm of mounting thread.
    # Allow 33 mm behind the cover for the elbow body and its tolerance.
    x, y = centre
    envelopes = {
        "PigtailThreadAndLocknut": cylinder(11.1, 2.4, 8.1, centre),
        "DownwardPigtailCordgrip": box(([x - 10, y - 12, -33], [x + 10, y + 12, 0])),
    }
    return rear, envelopes


def check(output):
    baseline = App.openDocument(str(BASELINE / "stacked-fibonacci.FCStd"))
    try:
        layout = read_layout()
        products, fixed, _ = model(baseline, layout)
        parts = component_envelopes(layout["board_top_z_mm"])
        rear, pigtail = pigtail_panel(fixed["CarrierRearPanel"])
        fixed["CarrierRearPanel"] = rear
        obstacles = {**fixed, **products}
        obstacles.pop("Carrier")  # The parts sit on the carrier's top face.
        parts["WallChargerEnvelope"] = box(([-14, -95, 3.5], [10, -67, 9.5]))
        parts.update(pigtail)
        collisions = intersections(parts, obstacles)
        collisions.extend(intersections({"PigtailRearCover": rear}, products))
        for a, b in combinations(parts, 2):
            collisions.extend(intersections({a: parts[a]}, {b: parts[b]}))
        if collisions:
            raise ValueError(f"Rev A carrier interference: {collisions}")
        print(f"REV A CLOSED FIT PASS ({len(parts)} installed envelopes)", flush=True)
        rear.exportStep(str(output.with_name("pigtail-rear-cover.step")))
        battery = battery_access.definition()
        motion = battery_access.native_check(
            battery,
            "narrow",
            battery_access.native_shapes(battery, "narrow"),
            surroundings=[
                ("RearCover", fixed["CarrierRearPanel"]),
                *products.items(),
                *parts.items(),
            ],
        )
        output.write_text(
            json.dumps(
                {"closed_collisions": collisions, "battery_motion": motion}, indent=2
            )
            + "\n"
        )
        print("REV A BATTERY MOTION PASS", flush=True)
    finally:
        App.closeDocument(baseline.Name)
