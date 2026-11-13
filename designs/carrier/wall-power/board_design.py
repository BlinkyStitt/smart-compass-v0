"""Generate and verify the two wall-power PCBs with KiCad's pcbnew Python."""

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pcbnew

HERE = Path(__file__).resolve().parent
QFN = "Package_DFN_QFN:QFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm"
RTW = "Package_DFN_QFN:Texas_RTW_WQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm"
DSG = "Package_SON:Texas_DSG0008A_WSON-8-1EP_2x2mm_P0.5mm_EP0.9x1.6mm"
RES = "Resistor_SMD:R_0603_1608Metric"
CAP = "Capacitor_SMD:C_0603_1608Metric"
CAP8 = "Capacitor_SMD:C_0805_2012Metric"
CAP12 = "Capacitor_SMD:C_1206_3216Metric"
WIRE = "WallPower:Lead_22AWG"
TP = "TestPoint:TestPoint_Pad_D1.0mm"
HOLE = "MountingHole:MountingHole_2.2mm_M2"
G = "GND"

# Order of each pin list is the data-sheet pin number, starting at 1.
# A dash is intentionally unconnected. Duplicate shell pads share one net.
CHARGER = {
    "U1": (
        "BQ25616RTWR",
        RTW,
        (12, 12, 90),
        [
            "VBUS",
            "-",
            "-",
            "-",
            "STAT",
            G,
            "PG",
            "ILIM",
            G,
            "ICHG",
            "TS",
            "-",
            "BAT",
            "BAT",
            "SYS",
            "SYS",
            G,
            G,
            "SW",
            "SW",
            "BTST",
            "REGN",
            "PMID",
            "VBUS",
            G,
        ],
    ),
    "L1": (
        "XFL4020-102MEC",
        "Inductor_SMD:L_Coilcraft_XxL4020",
        (5.2, 8.9, 180),
        ["SW", "SYS"],
    ),
    "C1": ("1uF 50V X7R", CAP8, (10.7, 16.8, 270), ["VBUS", G]),
    "C2": ("10uF 25V X7R", CAP12, (6.9, 14.9, 180), ["PMID", G]),
    "C3": ("10uF 25V X7R", CAP12, (6.9, 17.35, 180), ["PMID", G]),
    "C4": ("4.7uF 16V X7R", CAP8, (5.4, 12.25, 180), ["REGN", G]),
    "C5": ("47nF 16V X7R", CAP, (8.5, 10.48, 270), ["SW", "BTST"]),
    "C6": ("22uF 16V X7R", CAP12, (17.5, 8.7, 180), ["BAT", G]),
    "C7": ("22uF 16V X7R", CAP12, (7.7, 5.3, 180), ["SYS", G]),
    "C8": ("22uF 16V X7R", CAP12, (12.5, 5.3, 0), ["SYS", G]),
    "R1": ("205R 1%", RES, (16.5, 14.35, 180), ["ILIM", G]),
    "R2": ("562R 1%", RES, (18.0, 12.5, 180), ["ICHG", G]),
    "R3": ("5.30k 1%", RES, (16.9, 16.6, 0), ["REGN", "TS"]),
    "R4": ("31.1k 1%", RES, (17.4, 18.8, 180), ["TS", G]),
    "R5": ("10k", RES, (16.0, 21.2, 0), ["PG", "SYS"]),
    "R6": ("10k", RES, (11.0, 21.1, 0), ["STAT", "SYS"]),
    "W1": ("USB +5V", WIRE, (5.4, 22.8, 0), ["VBUS"]),
    "W2": ("USB GND", WIRE, (8.2, 22.8, 0), [G]),
    "W3": ("VH 1 CELL+", WIRE, (22, 7.8, 0), ["BAT"]),
    "W4": ("VH 2 GND", WIRE, (22, 10.6, 0), [G]),
    "W5": ("VH 3 SYS", WIRE, (22, 13.4, 0), ["SYS"]),
    "W6": ("VH 4 NTC", WIRE, (22, 16.2, 0), ["TS"]),
    "TP1": ("VBUS", TP, (4.1, 19.6, 0), ["VBUS"]),
    "TP2": ("BAT", TP, (20.8, 5.6, 0), ["BAT"]),
    "TP3": ("SYS", TP, (21.5, 19.1, 0), ["SYS"]),
    "TP4": ("TS", TP, (14.55, 18.7, 0), ["TS"]),
    "TP5": ("PG", TP, (17.6, 23.2, 0), ["PG"]),
    "TP6": ("STAT", TP, (12.7, 23.2, 0), ["STAT"]),
    "TP7": ("GND", TP, (8.45, 19.5, 0), [G]),
    "H1": ("M2", HOLE, (2.0, 2.0, 0), []),
    "H2": ("M2", HOLE, (22.0, 24.0, 0), []),
}

PIGTAIL = {
    "J1": (
        "USB4736-GF-A",
        "WallPower:USB4736-GF-A",
        (14, 31, 0),
        {
            "B12": G,
            "B9": "RAW",
            "A5": "CC1",
            "B5": "CC2",
            "A9": "RAW",
            "A12": G,
            "SH": G,
        },
    ),
    "U1": (
        "STUSB4500LQTR",
        QFN,
        (10, 18, 90),
        [
            "CC1",
            "CC1",
            G,
            "CC2",
            "CC2",
            G,
            "-",
            "-",
            "DISCH",
            G,
            "-",
            G,
            G,
            "-",
            "-",
            "ATTACH_N",
            "-",
            "SENSE",
            "-",
            "RP3_N",
            "V1V2",
            G,
            "V2V7",
            "RAW",
            G,
        ],
    ),
    "U2": (
        "TPS259531DSGR",
        DSG,
        (21.4, 10.1, 90),
        [
            "SLEW",
            "ENABLE",
            "VSNK",
            "VSNK",
            "USB_OUT",
            "-",
            "LIMIT",
            G,
            G,
        ],
    ),
    "Q1": (
        "DMP2022LSS-13",
        "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        (23.0, 19.95, 90),
        ["RAW", "RAW", "RAW", "GATE", "VSNK", "VSNK", "VSNK", "VSNK"],
    ),
    "Q2": (
        "MMBT3906LT1G",
        "Package_TO_SOT_SMD:SOT-23",
        (13.3, 10.0, 0),
        ["BASE", "VSNK", "ENABLE"],
    ),
    "D1": (
        "ESDA25W",
        "Package_TO_SOT_SMD:SOT-323_SC-70",
        (7.35, 22.25, 270),
        ["CC1", "CC2", G],
    ),
    "D2": (
        "ESDA25P35-1U1M",
        "WallPower:ST_QFN-2L_1.6x1mm",
        (21.5, 25.35, 180),
        ["RAW", G],
    ),
    "C1": ("1uF 50V X7R", CAP8, (5.5, 19.45, 180), ["RAW", G]),
    "C2": ("1uF 16V X7R", CAP, (5.3, 17.45, 180), ["V2V7", G]),
    "C3": ("1uF 16V X7R", CAP, (5.25, 15.2, 180), ["V1V2", G]),
    "C4": ("1uF 50V X7R", CAP8, (23.7, 14.0, 0), ["VSNK", G]),
    "C5": ("10nF 16V X7R", CAP, (18.1, 6.8, 180), ["SLEW", G]),
    "C6": ("1uF 25V X7R", CAP8, (24.4, 5.9, 180), ["USB_OUT", G]),
    "R1": ("1k", RES, (16.15, 21.35, 180), ["RAW", "SENSE"]),
    "R2": ("1k", RES, (14.1, 15.0, 0), ["DISCH", "VSNK"]),
    "R3": ("100k", RES, (25.9, 25.15, 0), ["RAW", "GATE"]),
    "R4": ("20k", RES, (15.3, 17.6, 90), ["ATTACH_N", "GATE"]),
    "R5": ("47k", RES, (9, 10.7, 180), ["RP3_N", "BASE"]),
    "R6": ("100k", RES, (12.4, 6.6, 180), ["VSNK", "BASE"]),
    "R7": ("100k", RES, (15.8, 3.2, 0), ["ENABLE", G]),
    "R8": ("750R 1%", RES, (25.8, 9.9, 90), ["LIMIT", G]),
    "W1": ("5V OUT", WIRE, (20.8, 2.1, 0), ["USB_OUT"]),
    "W2": ("GND OUT", WIRE, (24.0, 2.1, 0), [G]),
    "TP1": ("RAW", TP, (4.3, 23.2, 0), ["RAW"]),
    "TP2": ("VSNK", TP, (19.0, 15.5, 0), ["VSNK"]),
    "TP3": ("RP3_N", TP, (5.6, 10.0, 0), ["RP3_N"]),
    "TP4": ("5V OUT", TP, (19.0, 4.2, 0), ["USB_OUT"]),
    "H1": ("M2", HOLE, (2.0, 2.0, 0), []),
    "H2": ("M2", HOLE, (25.8, 28.8, 0), []),
}

BOARDS = {
    "charger": (CHARGER, 24, 26, 1.6),
    "usb-pigtail": (PIGTAIL, 28, 31, 1.2),
}


def design_uuid(name):
    return str(uuid5(NAMESPACE_URL, f"smart-compass/wall-power/{name}"))


def vector(x, y):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(y))


def pin_map(pins):
    if isinstance(pins, dict):
        return pins
    return {str(i): net for i, net in enumerate(pins, 1)}


def add_outline(board, points):
    for start, end in zip(points, points[1:] + points[:1]):
        line = pcbnew.PCB_SHAPE(board)
        line.SetShape(pcbnew.SHAPE_T_SEGMENT)
        line.SetStart(vector(*start))
        line.SetEnd(vector(*end))
        line.SetLayer(pcbnew.Edge_Cuts)
        line.SetWidth(pcbnew.FromMM(0.05))
        board.Add(line)


def add_track(board, name, width, points, layer=pcbnew.F_Cu):
    for start, end in zip(points, points[1:]):
        track = pcbnew.PCB_TRACK(board)
        track.SetNet(board.FindNet(name))
        track.SetLayer(layer)
        track.SetWidth(pcbnew.FromMM(width))
        track.SetStart(vector(*start))
        track.SetEnd(vector(*end))
        track.SetLocked(True)
        board.Add(track)


def add_via(board, name, point, diameter, drill):
    via = pcbnew.PCB_VIA(board)
    via.SetNet(board.FindNet(name))
    via.SetPosition(vector(*point))
    via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
    via.SetWidth(pcbnew.FromMM(diameter))
    via.SetDrill(pcbnew.FromMM(drill))
    via.SetLocked(True)
    board.Add(via)


def power_link(board, name, width, vias, points):
    for point in vias:
        add_via(board, name, point, 0.70, 0.32)
    add_track(board, name, width, points, pcbnew.In2_Cu)


def seed_copper(board, name):
    if name == "charger":
        # Keep the switching node and its bootstrap connection on the top.
        add_track(
            board, "SW", 0.65, [(6.385, 8.9), (7.695, 8.9), (8.5, 9.705), (9.5, 10.705)]
        )
        add_track(
            board,
            "SW",
            0.30,
            [(9.5, 10.705), (9.9925, 10.705), (10.0375, 10.75), (10.0375, 11.25)],
        )
        add_track(
            board,
            "BTST",
            0.20,
            [(8.5, 11.255), (8.955, 11.255), (9.45, 11.75), (10.0375, 11.75)],
        )
        add_track(board, "REGN", 0.20, [(6.35, 12.25), (9.4, 12.25), (10.0375, 12.25)])
        add_track(
            board,
            "PMID",
            0.45,
            [
                (8.375, 17.35),
                (8.375, 14.9),
                (8.375, 13.7),
                (9.1, 12.975),
                (9.155, 12.975),
            ],
        )
        add_track(
            board, "PMID", 0.27, [(9.155, 12.975), (9.38, 12.75), (10.0375, 12.75)]
        )
        add_track(
            board,
            "SYS",
            0.75,
            [
                (4.015, 8.9),
                (3.6, 8.9),
                (3.6, 5.5),
                (5.55, 3.55),
                (8.8, 3.55),
                (9.175, 3.925),
                (9.175, 5.3),
                (11.025, 5.3),
            ],
        )
        add_track(board, "SYS", 0.55, [(11.025, 5.3), (11.025, 7.175), (12.0, 8.15)])
        add_track(
            board,
            "SYS",
            0.30,
            [
                (12, 8.15),
                (12, 9.7875),
                (11.75, 10.0375),
                (12.25, 10.0375),
                (12.25, 9.95),
            ],
        )
        power_link(
            board,
            "SYS",
            0.95,
            [(11.55, 7.7), (12, 8.15)],
            [(12, 8.15), (15, 8.15), (20.25, 13.4), (22, 13.4)],
        )
        add_track(
            board,
            "SYS",
            0.30,
            [(22, 13.4), (20.7, 14.7), (20.7, 18.3), (21.5, 19.1)],
            pcbnew.In2_Cu,
        )
        add_via(board, "SYS", (21.5, 19.1), 0.55, 0.25)
        add_via(board, "SYS", (16.825, 21.2), 0.55, 0.25)
        add_via(board, "SYS", (11.825, 21.1), 0.55, 0.25)
        add_track(
            board,
            "SYS",
            0.30,
            [
                (21.5, 19.1),
                (20.0, 20.6),
                (17.425, 20.6),
                (16.825, 21.2),
                (11.925, 21.2),
                (11.825, 21.1),
            ],
            pcbnew.In2_Cu,
        )
        add_track(
            board, "BAT", 0.30, [(12.75, 10.0375), (13.25, 10.0375), (13.25, 9.4)]
        )
        add_track(
            board,
            "BAT",
            0.75,
            [
                (13.25, 9.4),
                (13.25, 8.4),
                (15.0, 6.65),
                (18.25, 6.65),
                (18.975, 7.375),
                (18.975, 8.7),
                (21.1, 8.7),
                (22, 7.8),
            ],
        )
        add_track(
            board,
            "VBUS",
            0.70,
            [
                (5.4, 22.8),
                (5.4, 20.65),
                (6.6, 19.45),
                (9.2, 19.45),
                (10.7, 17.95),
                (10.7, 15.85),
            ],
            pcbnew.In2_Cu,
        )
        add_via(board, "VBUS", (10.7, 15.85), 0.70, 0.32)
        add_track(
            board,
            "VBUS",
            0.30,
            [(10.7, 15.85), (10.7, 14.0125), (10.75, 13.9625), (10.0375, 13.25)],
        )
        add_track(board, "BAT", 0.25, [(18.25, 6.65), (19.75, 6.65), (20.8, 5.6)])
        add_via(board, "REGN", (7.4, 12.25), 0.55, 0.25)
        add_via(board, "REGN", (16.075, 16.6), 0.55, 0.25)
        add_track(
            board,
            "REGN",
            0.20,
            [
                (7.4, 12.25),
                (8.95, 13.8),
                (13.275, 13.8),
                (16.075, 16.6),
                (16.075, 16.6),
            ],
            pcbnew.B_Cu,
        )
        for x in (11.25, 12.0, 12.75):
            for y in (11.25, 12.0, 12.75):
                add_via(board, G, (x, y), 0.50, 0.25)
    else:
        add_track(
            board, "RAW", 0.70, [(21.095, 22.425), (22.365, 22.425), (23.635, 22.425)]
        )
        add_track(
            board,
            "VSNK",
            0.70,
            [(21.095, 17.475), (22.365, 17.475), (23.635, 17.475), (24.905, 17.475)],
        )
        add_track(board, "VSNK", 0.20, [(21.65, 11.05), (22.15, 11.05)])
        add_track(
            board,
            "VSNK",
            0.55,
            [
                (22.15, 11.05),
                (22.15, 12.1),
                (22.75, 12.7),
                (22.75, 14.0),
                (22.75, 17.09),
                (22.365, 17.475),
            ],
        )
        add_track(board, "USB_OUT", 0.24, [(22.15, 9.15), (22.15, 8.45)])
        add_track(
            board,
            "USB_OUT",
            0.60,
            [(22.15, 8.45), (22.15, 7.55), (21.3, 6.7), (21.3, 2.60), (20.8, 2.1)],
        )
        power_link(
            board,
            "RAW",
            1.0,
            [(12.48, 25.08), (15.52, 25.08), (22.365, 23.5)],
            [
                (12.48, 25.08),
                (15.52, 25.08),
                (17.95, 25.08),
                (19.53, 23.5),
                (22.365, 23.5),
            ],
        )
        add_track(board, "RAW", 0.70, [(22.365, 22.425), (22.365, 23.5)])
        add_via(board, G, (10, 18), 0.55, 0.25)
        add_via(board, G, (21.4, 10.1), 0.50, 0.20)
        add_track(
            board,
            "ENABLE",
            0.18,
            [
                (21.15, 11.05),
                (21.15, 11.79),
                (20.69, 12.25),
                (16.4875, 12.25),
                (14.2375, 10.0),
            ],
        )


def label(board, value, point, size=0.85):
    text = pcbnew.PCB_TEXT(board)
    text.SetText(value)
    text.SetPosition(vector(*point))
    text.SetLayer(pcbnew.F_SilkS)
    text.SetTextSize(vector(size, size))
    text.SetTextThickness(pcbnew.FromMM(0.12))
    board.Add(text)


def mark_board(board, name):
    if name == "charger":
        label(board, "SC CHARGER A", (12, 2))
        label(board, "5V", (5.4, 24.6))
        label(board, "GND", (8.2, 24.6))
        for text, y in [("BAT", 7.8), ("GND", 10.6), ("SYS", 13.4), ("NTC", 16.2)]:
            label(board, text, (22, y + 1.45))
    else:
        label(board, "SC USB-C A", (8, 2))
        label(board, "5V", (20.8, 3.85))
        label(board, "GND", (24, 3.85))


def fill_ground(board, name):
    _, width, length, _ = BOARDS[name]
    for layer in (pcbnew.In1_Cu, pcbnew.B_Cu, pcbnew.F_Cu):
        zone = pcbnew.ZONE(board)
        zone.SetLayer(layer)
        zone.SetNet(board.FindNet(G))
        zone.SetZoneName("GND")
        zone.SetLocalClearance(pcbnew.FromMM(0.20))
        zone.SetMinThickness(pcbnew.FromMM(0.19))
        zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL)
        polygon = zone.Outline()
        polygon.NewOutline()
        for point in [(0, 0), (width, 0), (width, length), (0, length)]:
            polygon.Append(vector(*point))
        board.Add(zone)
    board.BuildConnectivity()
    if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()):
        raise RuntimeError("KiCad failed to fill the ground planes")


def finish(name, source, session, netlist, output):
    board = pcbnew.LoadBoard(str(source))
    if not pcbnew.ImportSpecctraSES(board, str(session)):
        raise RuntimeError("KiCad failed to import the routing session")
    for footprint in board.GetFootprints():
        path = pcbnew.KIID_PATH()
        path.push_back(pcbnew.KIID(design_uuid(f"{name}/{footprint.GetReference()}")))
        footprint.SetPath(path)
    fill_ground(board, name)
    verify_pins(board, name)
    link_schematic_nets(board, netlist)
    pcbnew.SaveBoard(str(output), board)


def link_schematic_nets(board, path):
    for net in ET.parse(path).findall("./nets/net"):
        name = net.attrib["name"]
        pcb_net = board.FindNet(name.lstrip("/"))
        if pcb_net is not None:
            pcb_net.SetNetname(name)
            continue
        if not name.startswith("unconnected-"):
            raise ValueError(f"Schematic net {name} has no PCB copper")
        pcb_net = pcbnew.NETINFO_ITEM(board, name)
        board.Add(pcb_net)
        for pin in net.findall("node"):
            footprint = board.FindFootprintByReference(pin.attrib["ref"])
            next(
                pad for pad in footprint.Pads() if pad.GetNumber() == pin.attrib["pin"]
            ).SetNet(pcb_net)


def prepare(name, output, libraries):
    parts, width, length, thickness = BOARDS[name]
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(4)
    settings = board.GetDesignSettings()
    settings.SetBoardThickness(pcbnew.FromMM(thickness))
    add_outline(board, [(0, 0), (width, 0), (width, length), (0, length)])
    nets = {net for part in parts.values() for net in pin_map(part[3]).values()} - {"-"}
    for net in sorted(nets):
        board.Add(pcbnew.NETINFO_ITEM(board, net))
    for ref, (value, lib_id, (x, y, angle), pins) in parts.items():
        library, footprint_name = lib_id.split(":")
        directory = HERE if library == "WallPower" else libraries
        footprint = pcbnew.FootprintLoad(
            str(directory / (library + ".pretty")), footprint_name
        )
        if footprint is None:
            raise RuntimeError(f"Missing footprint {lib_id}")
        footprint.SetFPID(pcbnew.LIB_ID(library, footprint_name))
        footprint.SetReference(ref)
        footprint.SetValue(value)
        footprint.SetPosition(vector(x, y))
        footprint.SetOrientationDegrees(angle)
        footprint.Value().SetVisible(False)
        footprint.Reference().SetVisible(False)
        board.Add(footprint)
        mapping = pin_map(pins)
        for pad in footprint.Pads():
            number = pad.GetNumber()
            if number and mapping[number] != "-":
                pad.SetNet(board.FindNet(mapping[number]))
    verify_pins(board, name)
    seed_copper(board, name)
    mark_board(board, name)
    pcbnew.SaveBoard(str(output), board)
    dsn = output.with_suffix(".dsn")
    pcbnew.ExportSpecctraDSN(board, str(dsn))
    dsn.write_text(dsn.read_text().replace("(width 200)", "(width 175)"))


def verify_pins(board, name):
    parts, _, _, thickness = BOARDS[name]
    actual = {fp.GetReference(): fp for fp in board.GetFootprints()}
    if set(actual) != set(parts):
        raise ValueError(f"{name}: different reference designators")
    for ref, (value, _, _, pins) in parts.items():
        expected = pin_map(pins)
        pads = [p for p in actual[ref].Pads() if p.GetNumber()]
        if actual[ref].GetValue() != value or {p.GetNumber() for p in pads} != set(
            expected
        ):
            raise ValueError(f"{name}: {ref} package or pin mismatch")
        for pad in pads:
            actual_net = pad.GetNetname().lstrip("/")
            if not actual_net or actual_net.startswith("unconnected-"):
                actual_net = "-"
            if actual_net != expected[pad.GetNumber()]:
                raise ValueError(f"{name}: {ref} pad {pad.GetNumber()} net mismatch")
    if pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness()) != thickness:
        raise ValueError(f"{name}: unexpected board thickness")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("name", choices=BOARDS)
    parser.add_argument("board", type=Path)
    parser.add_argument("--footprints", type=Path)
    parser.add_argument("--session", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--netlist", type=Path)
    args = parser.parse_args()
    if args.footprints:
        prepare(args.name, args.board, args.footprints)
    elif args.session:
        if args.netlist is None or args.output is None:
            parser.error("--session requires --netlist and --output")
        finish(args.name, args.board, args.session, args.netlist, args.output)
    else:
        verify_pins(pcbnew.LoadBoard(str(args.board)), args.name)


if __name__ == "__main__":
    main()
