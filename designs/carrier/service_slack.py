"""Reserve installed length and volume for the removable carrier harnesses."""

from collections import Counter
import json
import math

from layout import HARDWARE, HERE
from harness_stock import validate_limits


def plan(spec):
    circuit = json.loads((HARDWARE / "electrical-design.json").read_text())
    stock = circuit["wiring"]["stock_limits"]
    validate_limits(stock)
    definition = json.loads((HERE / "service-slack.json").read_text())
    opening = definition["supported_cover_opening_mm"]
    release = definition["plug_handling_reserve_mm"]
    runs = []
    counts = Counter()
    for name, run in definition["runs"].items():
        strands = run["strands"]
        quantities = sum(strands.values())
        counts[run["group"]] += quantities
        diameter = max(stock[kind]["maximum_od_mm"] for kind in strands)
        radius = 3 * diameter
        slack = run["minimum_slack_mm"]
        if run["group"] == "pixels" and slack < opening + release:
            raise ValueError(f"Insufficient cover service slack for {name}")
        if slack < 20:
            raise ValueError(f"Insufficient connector handling slack for {name}")
        # A flat U stores its two straight legs and semicircle minus the
        # chord between its mouths. Adjacent wires bend independently.
        straight = (slack - (math.pi - 2) * radius) / 2
        outer = radius + (quantities - 1) * diameter
        width = 2 * outer + diameter + 1
        length = outer + straight + diameter + 1
        height = diameter + 1
        if run["turn_deg"] == 90:
            width, length = length, width
        elif run["turn_deg"] != 0:
            raise ValueError(f"Invalid service fold axis for {name}")
        x, y, z = run["centre_xy_bottom_z_mm"]
        bounds = [[x - width / 2, y - length / 2, z],
                  [x + width / 2, y + length / 2, z + height]]
        if bounds[1][2] > 30:
            raise ValueError(f"Service fold enters optical clearance for {name}")
        # Budget every wire at the longest reserve inside the slot. Exact
        # cuts and insertion lengths depend on the selected connector route.
        maximum_slack = 2 * straight + (math.pi - 2) * outer
        mass = sum(stock[kind]["nominal_mass_g_m"] * qty * maximum_slack / 1000
                   for kind, qty in strands.items())
        runs.append({"name": name, **run, "conductors": quantities,
                     "minimum_centreline_bend_radius_mm": radius,
                     "maximum_slack_mm": maximum_slack,
                     "storage_bounds_mm": bounds, "wire_mass_allowance_g": mass})
    if counts != spec["external_harnesses"]:
        raise ValueError("Service slack must cover the complete off-board harness census")
    return {"supported_cover_opening_mm": opening, "plug_handling_reserve_mm": release,
            "added_wire_mass_allowance_g": sum(run["wire_mass_allowance_g"] for run in runs),
            "scope": "Installed slack allowances and reserved spaces. Final routing and cut lengths depend on connector selection.",
            "runs": runs}
