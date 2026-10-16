"""Reuse the installed-component inventory for the two site mass estimates."""

from copy import deepcopy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "hardware/enclosure"))
from inventory import resolve, totals


def estimate_masses(wide, narrow, parameters, material):
    geometry_formulas = {"petg_volume", "ring_petg_volume", "acrylic_volume"}
    strip_ids = {"halo_strip", "inner_strip", "outer_strip"}
    # The narrow design has no completed fitting BOM. Preserve the wide
    # electronics, harness and fitting allowances as an explicit estimate.
    common = [deepcopy(row) for row in wide["components"]
              if row.get("mass_formula") not in geometry_formulas
              and row["id"] not in strip_ids]
    for row in common:
        row.pop("mass_formula", None)
        row.pop("length_parameter", None)
    prototypes = {formula: next(row for row in wide["components"]
                               if row.get("mass_formula") == formula)
                  for formula in geometry_formulas}
    bodies = {"RearCover", "ElectronicsShell", "FrontBezel", "BatteryCradle", "EGLStencil"}
    bodies.update("BoardEdgeClip" + str(i) for i in range(3))
    bodies.update(e["name"] + "Shelf" for e in parameters["electronics"]
                  if e["name"] != "Battery")
    electronics = {e["name"] for e in parameters["electronics"]} | {"FibonacciPCB"}
    volumes, rows = [], common
    found_bodies = set()
    for part in narrow["parts"]:
        name, role = part["name"], part["role"]
        if name in bodies:
            formula = "petg_volume"
            found_bodies.add(name)
        elif role in ("side", "inner"):
            formula = "ring_petg_volume"
        elif role in ("mirror", "rear_mirror"):
            formula = "acrylic_volume"
        else:
            if role == "solid" and name not in electronics and not name.endswith("Strip"):
                raise ValueError("Unclassified narrow solid: " + name)
            continue
        volume = {"name": name, "volume_cm3": part["volume_cm3"],
                  "printed": formula != "acrylic_volume"}
        volumes.append(volume)
        row = deepcopy(prototypes[formula])
        for key in ("mass_g_per_unit", "mass_range_g_per_unit", "length_parameter"):
            row.pop(key, None)
        row.update(id=name, cad_part=name, installed_quantity=1,
                   source="designs/stacked/exports/stacked-fibonacci.step",
                   dimensions="Narrow CAD geometry", mass_formula=formula)
        rows.append(row)
    if found_bodies != bodies:
        raise ValueError("Missing narrow manufactured parts: " + str(bodies - found_bodies))
    strip = next(row for row in wide["components"] if row["id"] == "inner_strip")
    for i, count in enumerate(narrow["counts"][1:]):
        row = deepcopy(strip)
        row.pop("length_parameter", None)
        row.update(id="narrow_strip_" + str(i), installed_quantity=count / parameters["strip_density"])
        rows.append(row)
    # The existing resolver owns densities, battery mass and uncertainty ranges.
    resolved = resolve({"components": rows}, volumes, wide["parameters_for_inventory"], material)
    return {"wide": wide["mass_estimate"], "narrow": totals(resolved)}


def runtime_hours(cell_wh, efficiency, total_amps, volts=5.0):
    if cell_wh <= 0 or not 0 < efficiency <= 1 or total_amps <= 0 or volts <= 0:
        raise ValueError("Invalid battery energy or load")
    return cell_wh * efficiency / (volts * total_amps)
