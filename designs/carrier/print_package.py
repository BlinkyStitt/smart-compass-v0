"""Build the Rev A print package from a completed routed-fit run."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile

from layout import BASELINE, HARDWARE, PRINT_PARTS, REVISED_PRINTS, ROOT

sys.path.insert(0, str(ROOT / "designs/stacked"))
import prints


def slice_projects(directory, inventory, spec):
    # Organic supports carry the inverted cover and the retainer toes.
    # Keep the inherited cradle and optical profiles separate.
    reports = []
    for supported in (False, True):
        rows = [row for row in inventory["print_parts"]
                if (row["source_part"] in {"CarrierRetainer", "RearCover"}) == supported]
        subset = {**inventory, "print_parts": rows, "stl_files": [row["file"] for row in rows]}
        profile = spec
        if supported:
            common = spec["common"] | {
                "support_material": "1",
                "support_material_style": "organic",
                "support_material_buildplate_only": "0",
            }
            profile = spec | {"common": common}
        prints.generate(directory, subset, profile)
        reports.append(prints.check(directory, subset, profile))
    return {**reports[0], "projects": reports[0]["projects"] + reports[1]["projects"]}


def build(fit, destination):
    report = json.loads((fit / "routed-fit.json").read_text())
    revised = {row["source_part"]: row for row in report["print_parts"]}
    if revised.keys() != REVISED_PRINTS:
        raise ValueError("Rev A fit must supply every revised print solid")
    if (report["closed_collisions"] or report["battery_motion"]["closed_interference_mm3"]
            or report["battery_hatch"]["closed_and_withdrawal_interference_mm3"]
            or report["carrier_retainer"]["collision_mm3"]
            or set(report["battery_contacts"]["integrated_seats"]) != {
                "BatteryContactNBack", "BatteryContactPBack",
            }
            or report["battery_polarity"]["reverse_tip_clearance_min_mm"] <= 0
            or report["disconnect_guard"]["former_bores_open"]):
        raise ValueError("Complete the Rev A fit check before packaging")

    baseline = json.loads((BASELINE / "parts.json").read_text())
    original = {row["source_part"]: row for row in baseline["print_parts"]}
    by_name = original | revised
    rows = [by_name[name] for name in sorted(PRINT_PARTS)]
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
        results = slice_projects(package, inventory, spec)
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
