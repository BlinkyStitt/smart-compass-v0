"""Check the Rev A carrier with mated harness connectors in FreeCAD."""

import json
from itertools import combinations
from pathlib import Path

import FreeCAD as App
from native import BASELINE, battery_access, box, intersections, model, read_layout

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


def check(output):
    baseline = App.openDocument(str(BASELINE / "stacked-fibonacci.FCStd"))
    try:
        layout = read_layout()
        products, fixed, _ = model(baseline, layout)
        parts = component_envelopes(layout["board_top_z_mm"])
        obstacles = {**fixed, **products}
        obstacles.pop("Carrier")  # The parts sit on the carrier's top face.
        parts["WallChargerEnvelope"] = box(([-12, -95, 3.5], [12, -67, 9.5]))
        collisions = intersections(parts, obstacles)
        # The future USB recess provides passage through the lower shell wall.
        outside_plug = box(([-6.5, -116, 4.5], [6.5, -95, 13]))
        collisions.extend(
            intersections(
                {"WallPlugEnvelope": outside_plug},
                {
                    name: shape
                    for name, shape in obstacles.items()
                    if name != "ElectronicsShell"
                },
            )
        )
        for a, b in combinations(parts, 2):
            collisions.extend(intersections({a: parts[a]}, {b: parts[b]}))
        if collisions:
            raise ValueError(f"Rev A carrier interference: {collisions}")
        print(f"REV A CLOSED FIT PASS ({len(parts)} installed envelopes)", flush=True)
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
