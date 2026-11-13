"""Prepare the KiCad carrier or import a Specctra routing session.

Use KiCad's Python to run this script. Generate the seed with pcb_placement.py.
"""

import argparse
import json
from pathlib import Path

import pcbnew

HERE = Path(__file__).resolve().parent
CONNECTOR_FOOTPRINTS = {
    "VH": ("JST_VH_B{count}P-VH", "3.96"),
    "XH": ("JST_XH_B{count}B-XH-A", "2.50"),
    "PH": ("JST_PH_B{count}B-PH-K", "2.00"),
}


def vector(x_mm, y_mm):
    return pcbnew.VECTOR2I(pcbnew.FromMM(x_mm), pcbnew.FromMM(y_mm))


def add_part(board, libraries, reference, value, library_id, pose, pins):
    library, name = library_id.split(":")
    folder = HERE if library == "SmartCompass" else libraries
    footprint = pcbnew.FootprintLoad(str(folder / (library + ".pretty")), name)
    if footprint is None:
        raise ValueError("Missing footprint " + library_id)
    footprint.SetFPID(pcbnew.LIB_ID(library, name))
    footprint.SetReference(reference)
    footprint.SetValue(value)
    x, y, angle = pose
    footprint.SetPosition(vector(x + 100, 100 - y))
    footprint.SetOrientationDegrees(angle)
    footprint.Value().SetVisible(False)
    footprint.Reference().SetVisible(False)
    board.Add(footprint)
    if reference.startswith("J"):
        centre = footprint.GetPosition()
        pads = list(footprint.Pads())
        first, last = (
            min(pads, key=lambda pad: pad.GetNumber()),
            max(pads, key=lambda pad: pad.GetNumber()),
        )
        centre.x = (first.GetPosition().x + last.GetPosition().x) // 2
        centre.y = (first.GetPosition().y + last.GetPosition().y) // 2
        offset = vector(2.6, 0) if angle == 90 else vector(0, -2.6)
        text = pcbnew.PCB_TEXT(board)
        text.SetText(reference)
        text.SetPosition(centre + offset)
        text.SetLayer(pcbnew.B_SilkS)
        text.SetMirrored(True)
        text.SetTextSize(vector(0.8, 0.8))
        text.SetTextThickness(pcbnew.FromMM(0.12))
        board.Add(text)
    available = {pad.GetNumber() for pad in footprint.Pads()}
    expected = {str(i) for i in range(1, len(pins) + 1)}
    if expected != available:
        raise ValueError(f"{reference} pad names differ from terminal map: {available}")
    for pad in footprint.Pads():
        net = pins[int(pad.GetNumber()) - 1]
        if net:
            pad.SetNet(board.FindNet(net))


def add_ground(board, outline, via_positions):
    ground = board.FindNet("GND")
    zone = pcbnew.ZONE(board)
    zone.SetLayer(pcbnew.In1_Cu)
    zone.SetNet(ground)
    zone.SetZoneName("GROUND")
    zone.SetLocalClearance(pcbnew.FromMM(0.25))
    zone.SetMinThickness(pcbnew.FromMM(0.25))
    zone.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
    zone.SetThermalReliefGap(pcbnew.FromMM(0.25))
    zone.SetThermalReliefSpokeWidth(pcbnew.FromMM(0.5))
    polygon = zone.Outline()
    polygon.NewOutline()
    for x, y in outline:
        polygon.Append(vector(x + 100, 100 - y))
    board.Add(zone)
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.GetNetname() != "GND" or pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD:
                continue
            target = vector(*via_positions[footprint.GetReference()])
            track = pcbnew.PCB_TRACK(board)
            track.SetNet(ground)
            track.SetLayer(pcbnew.F_Cu)
            track.SetStart(pad.GetPosition())
            track.SetEnd(target)
            track.SetWidth(pcbnew.FromMM(0.3))
            board.Add(track)
            via = pcbnew.PCB_VIA(board)
            via.SetNet(ground)
            via.SetPosition(target)
            via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
            via.SetWidth(pcbnew.FromMM(0.6))
            via.SetDrill(pcbnew.FromMM(0.3))
            board.Add(via)


def fill_zones(board):
    board.BuildConnectivity()
    if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()):
        raise RuntimeError("KiCad failed to fill the ground plane")


def route_classes(dsn, power_widths):
    # KiCad's exported DSN puts the unassigned nets into one default class.
    text = dsn.read_text()
    start = text.index("    (class kicad_default")
    end = text.index("\n  )\n  (wiring", start)
    nets = text[start:end].split("(circuit")[0].split()[2:]
    signal_via = "Via[0-3]_600:300_um"
    power_via = "Via[0-3]_1100:550_um"
    signals = [net for net in nets if net not in power_widths]
    classes = [("signals", 280, signal_via, signals)]
    classes.extend(
        (f"power_{net}", round(width * 1000), power_via, [net])
        for net, width in power_widths.items()
    )
    rules = "\n".join(
        f"    (class {name} {' '.join(members)}\n"
        f'      (circuit (use_via "{via}"))\n'
        f"      (rule (width {width}) (clearance 230))\n"
        "    )"
        for name, width, via, members in classes
    )
    text = text[:start] + rules + text[end:]
    start = text.index(f'    (padstack "{signal_via}"')
    end = text.index("\n  )\n  (network", start)
    padstack = text[start:end].replace(signal_via, power_via).replace(" 600)", " 1100)")
    text = text[:end] + "\n" + padstack + text[end:]
    text = text.replace(
        f'    (via "{signal_via}")', f'    (via "{signal_via}" "{power_via}")'
    )
    text = text.replace(
        "(clearance 50 (type smd_smd))", "(clearance 230 (type smd_smd))"
    )
    dsn.write_text(text)


def prepare(seed, output, libraries, spec):
    board = pcbnew.LoadBoard(str(seed))
    layers = board.GetEnabledLayers()
    for layer in (pcbnew.F_Paste, pcbnew.B_SilkS, pcbnew.F_Fab):
        layers.AddLayer(layer)
    board.SetEnabledLayers(layers)
    for item in list(board.GetDrawings()):
        if isinstance(item, pcbnew.PCB_TEXT):
            board.Remove(item)
    for footprint in board.GetFootprints():
        footprint.Reference().SetVisible(False)

    new_nets = {
        net
        for parts in (spec["connectors"], spec["parts"])
        for _, _, _, pins in parts.values()
        for net in pins
        if net
    }
    for name in sorted(new_nets):
        if board.FindNet(name) is None:
            board.Add(pcbnew.NETINFO_ITEM(board, name))

    for reference, (label, family, pose, pins) in spec["connectors"].items():
        pattern, pitch = CONNECTOR_FOOTPRINTS[family]
        count = len(pins)
        series = pattern.format(count=count)
        library_id = f"Connector_JST:{series}_1x{count:02}_P{pitch}mm_Vertical"
        add_part(board, libraries, reference, label, library_id, pose, pins)
    for reference, (value, library_id, pose, pins) in spec["parts"].items():
        add_part(board, libraries, reference, value, library_id, pose, pins)

    text = pcbnew.PCB_TEXT(board)
    text.SetText("SMART COMPASS CARRIER A")
    text.SetPosition(vector(45, 118.5))
    text.SetLayer(pcbnew.F_SilkS)
    text.SetTextSize(vector(1, 1))
    text.SetTextThickness(pcbnew.FromMM(0.15))
    board.Add(text)
    outline = json.loads((HERE / "layout.json").read_text())["outline_xy_mm"]
    add_ground(board, outline, spec["ground_vias_kicad_mm"])
    fill_zones(board)
    if not pcbnew.SaveBoard(str(output), board):
        raise RuntimeError("KiCad failed to write the carrier")
    dsn = output.with_suffix(".dsn")
    if not pcbnew.ExportSpecctraDSN(board, str(dsn)):
        raise RuntimeError("KiCad failed to export the routing job")
    route_classes(dsn, spec["wide_nets_mm"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--footprints", type=Path)
    group.add_argument("--session", type=Path)
    args = parser.parse_args()
    if args.footprints:
        spec = json.loads((HERE / "routed-components.json").read_text())
        prepare(args.input, args.output, args.footprints, spec)
    else:
        board = pcbnew.LoadBoard(str(args.input))
        if not pcbnew.ImportSpecctraSES(board, str(args.session)):
            raise RuntimeError("KiCad failed to import the routing session")
        if not list(board.GetTracks()):
            raise ValueError("Routing session did not add copper")
        fill_zones(board)
        if not pcbnew.SaveBoard(str(args.output), board):
            raise RuntimeError("KiCad failed to save the routed board")


if __name__ == "__main__":
    main()
