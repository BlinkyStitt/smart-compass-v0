"""Build the Rev A print package from a completed routed-fit run."""

import argparse
import json
from pathlib import Path
import shutil
import sys
import tempfile
import zipfile

from layout import BASELINE, HARDWARE, PRINT_PARTS, REVISED_PRINTS, ROOT
from print_inputs import FIT_SAMPLES, MANIFEST_NAME, digest, fit_inputs, package_inputs

FIRST_FIT = '''
## Interface test pieces

Print the three Fit projects in opaque PETG with the same printer, profile,
and orientation as the installed parts. These samples are separate from the
12 installed parts.

- FitBatterySeatPositive and FitBatterySeatNegative reproduce the fixed
  contact seats. Use the actual contacts and the two production front clamps
  to check bore finishing, seating, and plunger movement before making the
  full cradle. Check assembled contact spacing, keeper retention, and reverse
  isolation on the full cradle with a nonconductive dummy cell. The separate
  samples check local fit.
- FitUSBPort reproduces the socket opening and gasket pocket. Fit the real
  socket, gasket, and plug. Check the specified opening and pocket dimensions
  after finishing. Check seating and compression before printing the rear cover.
  Use the production cover for board alignment and completed seal tests.
'''

sys.path.insert(0, str(ROOT / "designs/stacked"))
import prints


def slice_projects(directory, inventory, spec):
    # Organic supports carry the inverted cover and the retainer toes.
    # Keep the inherited cradle and optical profiles separate.
    reports = []
    for supported in (False, True):
        subset = {
            field: [row for row in inventory[field]
                    if (row["source_part"] in {"CarrierRetainer", "RearCover"}) == supported]
            for field in ("print_parts", "fit_samples")
        }
        subset["stl_files"] = [row["file"] for row in subset["print_parts"]]
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
    inputs = package_inputs()
    if report.get("inputs") != fit_inputs():
        raise ValueError("Rev A routed-fit inputs differ from this checkout. Rerun the fit check.")
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
    samples = report["fit_samples"]
    if {row["file"]: row["source_part"] for row in samples} != {
        f"{name}.stl": parent for name, parent in FIT_SAMPLES.items()
    } or len(samples) != len(FIT_SAMPLES):
        raise ValueError("Rev A fit must supply all interface test pieces")
    inventory = {
        "print_parts": rows,
        "stl_files": [row["file"] for row in rows],
        "fit_samples": samples,
    }
    spec = json.loads((HARDWARE / "print-spec.json").read_text())
    spec["reference_machine"]["bed_shape"] = "0x0,220x0,220x220,0x220"
    spec["common"]["skirts"] = "0"
    # The shared generator uses this value for structural projects only.
    spec["default_ring_material"] = "opaque-petg"

    if destination.exists():
        raise FileExistsError(f"Use a new package directory: {destination}")
    with tempfile.TemporaryDirectory(prefix="rev-a-", dir=destination.parent) as temporary:
        package = Path(temporary) / "package"
        package.mkdir()
        for row in rows + samples:
            source = (fit if row["source_part"] in revised else BASELINE) / row["file"]
            if digest(source) != row["sha256"]:
                raise ValueError(f"STL checksum differs from its fit inventory: {source}")
            shutil.copyfile(source, package / row["file"])
        results = slice_projects(package, inventory, spec)
        (package / "parts.json").write_text(json.dumps(inventory, indent=2) + "\n")
        (package / "slicer-check.json").write_text(json.dumps(results, indent=2) + "\n")
        shutil.copyfile(fit / "routed-fit.json", package / "routed-fit.json")
        guide = Path(__file__).with_name("printing.md").read_text()
        (package / "README.md").write_text(guide + FIRST_FIT)
        if inputs != package_inputs():
            raise ValueError("Rev A inputs changed while packaging")
        files = {path.name: digest(path) for path in sorted(package.iterdir())}
        manifest = {"revision": "Rev A", "inputs": inputs, "files": files}
        (package / MANIFEST_NAME).write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        package.rename(destination)
    print(f"REV A PRINT PACKAGE PASS ({len(rows)} installed parts, {len(samples)} fit samples, "
          f"{len(results['projects'])} projects)")


def write_archive(package, destination):
    with tempfile.TemporaryDirectory(prefix="rev-a-zip-", dir=destination.parent) as temporary:
        path = Path(temporary) / destination.name
        with zipfile.ZipFile(path, "w") as archive:
            for source in sorted(package.iterdir()):
                archive.writestr(zipfile.ZipInfo(source.name), source.read_bytes(), zipfile.ZIP_DEFLATED)
        path.replace(destination)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("fit", type=Path, help="Output directory from RunRoutedFit.FCMacro")
    parser.add_argument("destination", type=Path, help="New directory for the verified print package")
    parser.add_argument("--archive", type=Path, help="Write a ZIP of the verified package")
    arguments = parser.parse_args()
    package = arguments.destination.resolve()
    build(arguments.fit.resolve(), package)
    if arguments.archive:
        write_archive(package, arguments.archive.resolve())
