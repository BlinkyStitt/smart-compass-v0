"""Write the narrow scene's indexed LED positions to a Sparkle Motion drive."""

import argparse
import json
from pathlib import Path

from power_policy import PIXEL_COUNTS


def ordered_positions(scene):
    groups = [[None] * count for count in PIXEL_COUNTS]
    for led in scene["leds"]:
        group, index = led["group"], led["index"]
        if not 0 <= group < len(groups) or not 0 <= index < PIXEL_COUNTS[group]:
            raise ValueError(f"Invalid LED group or index {group}, {index}")
        if groups[group][index] is not None:
            raise ValueError(f"Duplicate LED {group}, {index}")
        groups[group][index] = led["position_m"][:2]
    if any(None in group for group in groups):
        raise ValueError("Missing narrow LED positions")
    return groups


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scene", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    positions = ordered_positions(json.loads(args.scene.read_text()))
    args.output.write_text(json.dumps(positions, separators=(",", ":")) + "\n")
