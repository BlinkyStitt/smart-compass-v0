"""Build the Rev A print package from a completed routed-fit run."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

from layout import BASELINE, HARDWARE, RETAINED_PRINTS, REVISED_PRINTS, ROOT

sys.path.insert(0, str(ROOT / "designs/stacked"))
import prints


def build(fit, destination):
    report = json.loads((fit / "routed-fit.json").read_text())
    if report["closed_collisions"] or report["battery_motion"]["closed_interference_mm3"]:
        raise ValueError("Complete the Rev A fit check before packaging")
    revised = {row["source_part"]: row for row in report["print_parts"]}
    if revised.keys() != REVISED_PRINTS:
        raise ValueError("Rev A fit must supply the revised cover, shell, door and keeper")

    baseline = json.loads((BASELINE / "parts.json").read_text())
    original = {row["source_part"]: row for row in baseline["print_parts"]}
    rows = [revised.get(name, original[name]) for name in sorted(RETAINED_PRINTS)]
    inventory = {
        "print_parts": rows,
        "stl_files": [row["file"] for row in rows],
        "fit_samples": [],
    }
    spec = json.loads((HARDWARE / "print-spec.json").read_text())
    spec["reference_machine"]["bed_shape"] = "0x0,220x0,220x220,0x220"
    spec["common"]["skirts"] = "0"

    if destination.exists():
        raise FileExistsError(f"Use a new package directory: {destination}")
    with tempfile.TemporaryDirectory(prefix="rev-a-", dir=destination.parent) as temporary:
        package = Path(temporary) / "package"
        package.mkdir()
        for row in rows:
            source = (fit if row["source_part"] in revised else BASELINE) / row["file"]
            if hashlib.sha256(source.read_bytes()).hexdigest() != row["sha256"]:
                raise ValueError(f"STL checksum differs from its fit inventory: {source}")
            shutil.copyfile(source, package / row["file"])
        prints.generate(package, inventory, spec)
        results = prints.check(package, inventory, spec)
        (package / "parts.json").write_text(json.dumps(inventory, indent=2) + "\n")
        (package / "slicer-check.json").write_text(json.dumps(results, indent=2) + "\n")
        shutil.copyfile(fit / "routed-fit.json", package / "routed-fit.json")
        shutil.copyfile(Path(__file__).with_name("printing.md"), package / "README.md")
        package.rename(destination)
    print(f"REV A PRINT PACKAGE PASS ({len(rows)} installed parts, {len(results['projects'])} projects)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fit", type=Path, help="Output directory from RunRoutedFit.FCMacro")
    parser.add_argument("destination", type=Path, help="New directory for the verified print package")
    arguments = parser.parse_args()
    build(arguments.fit.resolve(), arguments.destination.resolve())
