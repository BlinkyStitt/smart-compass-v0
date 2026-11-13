"""Write KiCad connection schematics from the checked board pin maps."""

import argparse
import json
import re
from pathlib import Path

from board_design import BOARDS, design_uuid, pin_map
from pd60_design import LAYOUT as PD_LAYOUT, PIN_NAMES as PD_PIN_NAMES

PIN_NAMES = {
    **PD_PIN_NAMES,
    "charger": {
        "U1": [
            "VAC",
            "ACDRV",
            "D+",
            "D-",
            "STAT",
            "OTG",
            "PG",
            "ILIM",
            "CE",
            "ICHG",
            "TS",
            "VSET",
            "BAT",
            "BAT",
            "SYS",
            "SYS",
            "PGND",
            "PGND",
            "SW",
            "SW",
            "BTST",
            "REGN",
            "PMID",
            "VBUS",
            "EP",
        ],
    },
    "usb-pigtail": {
        "U1": [
            "CC1DB",
            "CC1",
            "NU",
            "CC2",
            "CC2DB",
            "RESET",
            "SCL",
            "SDA",
            "DISCH",
            "GND",
            "ATTACH",
            "ADDR0",
            "ADDR1",
            "RP_1A5",
            "GPIO",
            "VBUS_EN_SNK",
            "A_B_SIDE",
            "VBUS_VS_DISCH",
            "ALERT",
            "RP_3A",
            "VREG_1V2",
            "VSYS",
            "VREG_2V7",
            "VDD",
            "EP",
        ],
        "U2": ["dVdt", "EN", "IN", "IN", "OUT", "FLT", "ILM", "GND", "EP"],
        "Q1": ["S", "S", "S", "G", "D", "D", "D", "D"],
        "Q2": ["B", "E", "C"],
        "D1": ["K1", "K2", "A"],
        "D2": ["K", "A"],
    },
}

# The left two columns group the active power blocks. The right columns
# carry the labelled passives, test points and harness ends.
LAYOUT = {
    **PD_LAYOUT,
    "charger": [
        ("U1",),
        ("L1", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"),
        ("R1", "R2", "R3", "R4", "R5", "R6"),
        ("W1", "W2", "W3", "W4", "W5", "W6"),
        ("TP1", "TP2", "TP3", "TP4", "TP5", "TP6", "TP7", "H1", "H2"),
    ],
    "usb-pigtail": [
        ("U1",),
        ("J1", "Q1", "U2"),
        ("Q2", "D1", "D2", "C1", "C2", "C3"),
        ("C4", "C5", "C6", "R1", "R2", "R3", "R4", "R5", "R6"),
        ("R7", "R8", "W1", "W2", "TP1", "TP2", "TP3", "TP4", "H1", "H2"),
    ],
}


def quote(value):
    return json.dumps(value, ensure_ascii=False)


def uid(name):
    return quote(design_uuid(name))


def position(x, y):
    return f"{x:.5f} {y:.5f}"


def property_(field, value, x, y, hidden=False):
    hide = "(hide yes)" if hidden else ""
    return (
        f'(property "{field}" {quote(value)} (at {position(x, y)} 0) '
        f"(effects (font (size 1.27 1.27)) {hide}))"
    )


def symbol_lib(key, ref, value, names, width, levels):
    in_bom = "no" if ref.startswith(("H", "TP")) else "yes"
    prefix = re.match(r"[A-Z]+", ref)[0]
    edge = max((abs(y) for y in levels), default=0) + 1.27
    body = (
        f"(rectangle (start {-width} {edge}) (end {width} {-edge}) "
        "(stroke (width 0.254) (type default)) (fill (type background)))"
    )
    pins = []
    for (number, name), y in zip(names.items(), levels):
        pins.append(
            f"(pin passive line (at {-width - 5.08} {-y} 0) (length 5.08) "
            f"(name {quote(name)} (effects (font (size 1.016 1.016)))) "
            f"(number {quote(number)} (effects (font (size 1.016 1.016)))))"
        )
    return (
        f"(symbol {quote('WallPower:' + key)} (pin_names (offset 0.75)) "
        f"(exclude_from_sim yes) (in_bom {in_bom}) (on_board yes) "
        f"{property_('Reference', prefix, 0, edge + 5.08)} "
        f"{property_('Value', value, 0, edge + 2.54)} "
        f"(symbol {quote(key + '_0_1')} {body}) "
        f"(symbol {quote(key + '_1_1')} {' '.join(pins)}))"
    )


def instance(board, key, ref, value, footprint, pins, levels, width, x, y):
    namespace = f"{board}/{ref}"
    top = min(levels, default=0)
    in_bom = "no" if ref.startswith(("H", "TP")) else "yes"
    items = [
        (
            f"(symbol (lib_id {quote('WallPower:' + key)}) (at {position(x, y)} 0) (unit 1) "
            f"(exclude_from_sim yes) (in_bom {in_bom}) (on_board yes) (dnp no) (uuid {uid(namespace)})"
        ),
        property_("Reference", ref, x, y + top - 6.35),
        property_("Value", value, x, y + top - 3.81),
        property_("Footprint", footprint, x, y, hidden=True),
    ]
    for number in pins:
        items.append(f"(pin {quote(number)} (uuid {uid(namespace + '/' + number)}))")
    items.append(
        f"(instances (project {quote(board)} (path {quote('/' + json.loads(uid(board)))} "
        f"(reference {quote(ref)}) (unit 1)))))"
    )
    for (number, net), level in zip(pins.items(), levels):
        token = f"{namespace}/{number}"
        pad = position(x - width - 5.08, y + level)
        if net == "-":
            items.append(f"(no_connect (at {pad}) (uuid {uid(token + '/nc')}))")
            continue
        end = position(x - width - 17.78, y + level)
        items.append(
            f"(wire (pts (xy {pad}) (xy {end})) "
            f"(stroke (width 0) (type default)) (uuid {uid(token + '/wire')}))"
        )
        items.append(
            f"(label {quote(net)} (at {end} 0) (effects "
            f"(font (size 1.016 1.016)) (justify left bottom)) (uuid {uid(token + '/label')}))"
        )
    return "\n".join(items)


def schematic(name, output):
    parts = BOARDS[name][0]
    names = PIN_NAMES[name]
    refs = [ref for column in LAYOUT[name] for ref in column]
    if set(refs) != set(parts) or len(refs) != len(parts):
        raise ValueError(f"{name}: schematic placement does not cover the board")
    libraries = []
    instances = []
    for index, column in enumerate(LAYOUT[name]):
        x = 44.45 + 69.85 * index
        y = 24.13
        for ref in column:
            value, footprint, _, pin_list = parts[ref]
            pins = pin_map(pin_list)
            if ref in names:
                pin_names = dict(zip(pins, names[ref]))
            else:
                pin_names = {number: "" for number in pins}
            if set(pin_names) != set(pins):
                raise ValueError(f"{name}: missing schematic pin names for {ref}")
            levels = [
                2.54 * (level - (len(pins) - 1) / 2) for level in range(len(pins))
            ]
            width = 13.97 if ref in names or ref == "J1" else 7.62
            libraries.append(symbol_lib(ref, ref, value, pin_names, width, levels))
            instances.append(
                instance(
                    name,
                    ref,
                    ref,
                    value,
                    footprint,
                    pins,
                    levels,
                    width,
                    x,
                    y - min(levels, default=0),
                )
            )
            y += max(0, len(pins) - 1) * 2.54 + 16.51
    title = {"charger": "Wall charger", "usb-pigtail": "USB-C pigtail",
             "usb-pd60": "60 W USB-C power", "led-power": "LED power selector"}[name]
    paper = "A2" if name in PD_LAYOUT else "A3"
    revision = "B" if name == "led-power" else "A"
    lines = [
        '(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")',
        f'(uuid {uid(name)}) (paper "{paper}") (title_block (title "Smart Compass - {title}") (rev "{revision}"))',
        "(lib_symbols",
        *libraries,
        ")",
        *instances,
        '(sheet_instances (path "/" (page "1")))',
        ")",
        "",
    ]
    output.write_text("\n".join(lines))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", choices=BOARDS)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    schematic(args.name, args.output)


if __name__ == "__main__":
    main()
