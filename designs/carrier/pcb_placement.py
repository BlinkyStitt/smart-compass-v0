"""Export the checked outline and source header positions as an unrouted board."""

import argparse
import json
from pathlib import Path

from layout import DOCK_HEADERS, read_layout, schedule

SOCKET_DRILL_MM = .92
CARRIER_MOUNT_DRILL_MM = 2.2


def pcb_coordinates(x, y):
    return x + 100, 100 - y


def pcb_text(spec, rows):
    socket_rows = [row for row in rows if row["connection"] == "dock socket"]
    net_names = sorted({row["baseline_net"] for row in socket_rows if row["baseline_net"]})
    nets = {name: index for index, name in enumerate(net_names, start=1)}
    lines = [
        "(kicad_pcb (version 20240108) (generator smart_compass_carrier)",
        f'  (general (thickness {spec["board_thickness_mm"]}))',
        '  (paper "A4")',
        '  (layers (0 "F.Cu" signal) (1 "In1.Cu" power) (2 "In2.Cu" signal)',
        '          (31 "B.Cu" signal) (37 "F.SilkS" user "F.Silkscreen")',
        '          (38 "B.Mask" user) (39 "F.Mask" user) (44 "Edge.Cuts" user)',
        '          (46 "Dwgs.User" user "User.Drawings"))',
        '  (setup (pad_to_mask_clearance 0))',
        '  (net 0 "")',
    ]
    lines.extend(f"  (net {number} {json.dumps(name)})" for name, number in nets.items())
    outline = spec["outline_xy_mm"]
    for start, end in zip(outline, outline[1:] + outline[:1], strict=True):
        x, y = pcb_coordinates(*start)
        ex, ey = pcb_coordinates(*end)
        lines.append(f'  (gr_line (start {x:g} {y:g}) (end {ex:g} {ey:g}) '
                     '(stroke (width 0.05) (type default)) (layer "Edge.Cuts"))')
    lines.append('  (gr_text "UNROUTED CARRIER - MECHANICAL FIT ONLY" (at 100 95) '
                 '(layer "Dwgs.User") (effects (font (size 2 2) (thickness 0.25))))')
    for module in DOCK_HEADERS:
        x, y = pcb_coordinates(*spec["modules"][module]["datum_xy_mm"])
        lines.extend([
            f'  (footprint "SmartCompass:{module}_dock" (layer "F.Cu") (at {x:g} {y:g})',
            f'    (fp_text reference "{module}" (at 0 0) (layer "F.SilkS") '
            '(effects (font (size 1 1) (thickness 0.15))))',
            f'    (fp_text value "{module} dock" (at 0 2) (layer "Dwgs.User") '
            '(effects (font (size 1 1) (thickness 0.15))))',
        ])
        for row in socket_rows:
            if row["module"] != module:
                continue
            px, py = pcb_coordinates(row["x_mm"], row["y_mm"])
            name = row["baseline_net"]
            net = f" (net {nets[name]} {json.dumps(name)})" if name else ""
            lines.append(
                f'    (pad "{row["source_pad"]}" thru_hole circle (at {px-x:.6f} {py-y:.6f}) '
                f'(size 1.8 1.8) (drill {SOCKET_DRILL_MM}) (layers "*.Cu" "*.Mask"){net})'
            )
        lines.append("  )")
    for index, xy in enumerate(spec["mount_xy_mm"], start=1):
        x, y = pcb_coordinates(*xy)
        drill = CARRIER_MOUNT_DRILL_MM
        lines.extend([
            f'  (footprint "SmartCompass:Carrier_mount" (layer "F.Cu") (at {x:g} {y:g})',
            f'    (fp_text reference "H{index}" (at 0 2) (layer "Dwgs.User") '
            '(effects (font (size 1 1) (thickness 0.15))))',
            f'    (pad "" np_thru_hole circle (at 0 0) (size {drill} {drill}) '
            f'(drill {drill}) (layers "*.Cu" "*.Mask"))',
            "  )",
        ])
    return "\n".join(lines + [")", ""])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    arguments = parser.parse_args()
    spec = read_layout()
    arguments.output.write_text(pcb_text(spec, schedule(spec)))
