"""Source-backed floorplan for the plug-in electronics carrier."""

import csv
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
HARDWARE = ROOT / "hardware/enclosure"
BASELINE = ROOT / "designs/stacked/exports"
sys.path.insert(0, str(HARDWARE))
import blackpill_mount
import electrical_blackpill
import electrical_boost
import electrical_imu
import electrical_peripherals


def transform(xy, origin, pose):
    x, y = (coordinate - datum for coordinate, datum in zip(xy, origin, strict=True))
    angle = math.radians(pose["rotation_deg"])
    cosine, sine = math.cos(angle), math.sin(angle)
    dx, dy = pose["datum_xy_mm"]
    return [round(dx + x * cosine - y * sine, 6), round(dy + x * sine + y * cosine, 6)]


def component_sources(circuit):
    parts = circuit["parts"]
    return {
        "IMU": ([16.51, 10.16], electrical_imu.terminals(parts["IMU"])),
        "BLACKPILL": (blackpill_mount.DATUM, electrical_blackpill.terminals(parts["BLACKPILL"])),
        "GPS": ([25.4, 11.43], electrical_peripherals.terminals("GPS", parts["GPS"])),
        "RADIO": ([12.7, 14.605], electrical_peripherals.terminals("RADIO", parts["RADIO"])),
        "SPARKLE": ([25.4, 16.51], electrical_peripherals.terminals("SPARKLE", parts["SPARKLE"])),
        "BOOST": ([14.605, 11.43], electrical_boost.terminals(parts["BOOST"])),
    }


DOCK_HEADERS = {
    "IMU": ("JP2", "JP4"),
    "BLACKPILL": ("P1", "P2"),
    "GPS": ("JP1", "JP3", "JP4"),
    "RADIO": ("JP3",),
    "SPARKLE": ("JP3",),
}


def dock_pads(module):
    """Reserve all holes in each stock strip, including unconnected contacts."""
    if module == "BLACKPILL":
        facts = electrical_blackpill.source_facts()
        for header in DOCK_HEADERS[module]:
            row = facts["headers"][header]
            for index in range(len(row["nets"])):
                xy = [facts["first_x_mm"] + facts["pitch_x_mm"] * index, row["y_mm"]]
                yield f"{header}.{index + 1}", xy, facts["nominal_cad_hole_diameter_mm"]
        return
    if module == "IMU":
        folder = electrical_imu.SOURCE
        files = electrical_imu.FILES
        origin = [0, 0]
    else:
        source = electrical_peripherals.BOARDS[module]
        folder, files, origin = (source[key] for key in ("source", "files", "origin_mm"))
    name = next(name for name in files if name.endswith(".brd"))
    board = ET.parse(HARDWARE / folder / name).find("./drawing/board")
    for header in DOCK_HEADERS[module]:
        element = board.find(f'./elements/element[@name="{header}"]')
        library = board.find(f'./libraries/library[@name="{element.get("library")}"]')
        package = library.find(f'./packages/package[@name="{element.get("package")}"]')
        pose = {
            "datum_xy_mm": [float(element.get(axis)) - offset for axis, offset in zip(("x", "y"), origin)],
            "rotation_deg": float(element.get("rot", "R0").removeprefix("R")),
        }
        for pad in package.findall("pad"):
            xy = transform([float(pad.get(axis)) for axis in ("x", "y")], [0, 0], pose)
            yield f"{header}.{pad.get('name')}", xy, float(pad.get("drill"))


def schedule(spec):
    circuit = json.loads((HARDWARE / "electrical-design.json").read_text())
    pin_net = {pin: net for net, pins in circuit["nets"].items() for pin in pins}
    rows = []
    for module, (origin, terminals) in component_sources(circuit).items():
        selected_pads = {terminal["pad"] for terminal in terminals.values()}
        for name, terminal in terminals.items():
            pad = terminal["pad"]
            pin = f"{module}.{pad if module in ('SPARKLE', 'BOOST') else name}"
            if module == "BOOST":
                connection = "power interface pending" if name == "TRIP" else "power lead"
            elif module == "SPARKLE" and not pad.startswith("JP3."):
                connection = "stock jack or clamp"
            elif module == "RADIO" and name == "ANT":
                connection = "module antenna"
            else:
                connection = "dock socket"
            net = pin_net.get(pin)
            if pin == "SPARKLE.JP3.1":
                net = "GND"
            if connection == "dock socket" and (not net or not terminal["drill_mm"]):
                raise ValueError(f"Missing source connection for {pin}")
            x, y = transform(terminal["board_xy_mm"], origin, spec["modules"][module])
            rows.append({
                "module": module, "terminal": name, "source_pad": pad, "baseline_net": net,
                "connection": connection, "x_mm": x, "y_mm": y,
                "module_drill_mm": terminal["drill_mm"],
            })
        if module not in DOCK_HEADERS:
            continue
        for pad, xy, drill in dock_pads(module):
            x, y = transform(xy, origin, spec["modules"][module])
            if pad in selected_pads:
                match = next(row for row in rows if row["module"] == module and row["source_pad"] == pad)
                if math.dist([x, y], [match["x_mm"], match["y_mm"]]) > .001:
                    raise ValueError(f"Dock disagrees with reviewed terminal coordinates: {module}.{pad}")
                continue
            rows.append({
                "module": module, "terminal": "", "source_pad": pad, "baseline_net": None,
                "connection": "dock socket", "x_mm": x, "y_mm": y, "module_drill_mm": drill,
            })
    return rows


def read_layout():
    spec = json.loads((HERE / "layout.json").read_text())
    if spec["board_thickness_mm"] > 1.57 or spec["socket_stack_mm"] != 3.94:
        raise ValueError("Check the selected socket stack against its drawing")
    spec["board_top_z_mm"] = spec["board_bottom_z_mm"] + spec["board_thickness_mm"]
    spec["module_bottom_z_mm"] = spec["board_top_z_mm"] + spec["socket_stack_mm"]
    return spec


def write_schedule(output, rows):
    with output.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    write_schedule(args.output, schedule(read_layout()))
