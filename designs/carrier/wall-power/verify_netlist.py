"""Compare the exported KiCad schematic connectivity with the routed PCB."""

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

import pcbnew


def verify(board_path, netlist_path):
    schematic = ET.parse(netlist_path)
    board = pcbnew.LoadBoard(str(board_path))
    schematic_parts = {
        component.attrib["ref"]: (
            component.findtext("value"),
            component.findtext("footprint"),
        )
        for component in schematic.findall("./components/comp")
    }
    board_parts = {
        fp.GetReference(): (
            fp.GetValue(),
            f"{fp.GetFPID().GetLibNickname()}:{fp.GetFPID().GetLibItemName()}",
        )
        for fp in board.GetFootprints()
    }
    if board_parts != schematic_parts:
        raise ValueError("The PCB and schematic have different parts")

    schematic_nets = {
        (node.attrib["ref"], node.attrib["pin"]): net.attrib["name"]
        for net in schematic.findall("./nets/net")
        for node in net.findall("node")
    }
    board_nets = {
        (fp.GetReference(), pad.GetNumber()): pad.GetNetname()
        for fp in board.GetFootprints()
        for pad in fp.Pads()
        if pad.GetNetname()
    }
    if board_nets != schematic_nets:
        differing = set(board_nets.items()) ^ set(schematic_nets.items())
        raise ValueError(f"PCB and schematic nets differ: {sorted(differing)}")
    print(
        f"{board_path.name}: {len(board_parts)} references, {len(board_nets)} assigned pads"
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("board", type=Path)
    parser.add_argument("netlist", type=Path)
    args = parser.parse_args()
    verify(args.board, args.netlist)


if __name__ == "__main__":
    main()
