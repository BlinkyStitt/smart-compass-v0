"""Compact layout in millimetres. Shared assets remain owned by design one."""

import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def parameters():
    p = json.loads((HERE / "parameters.json").read_text())
    acrylic = json.loads((ROOT / "hardware/enclosure/acrylic-optics.json").read_text())[
        "materials"
    ]
    for face, material in (("front", "two_way_mirror"), ("rear", "black_mirror")):
        for quantity in ("reflectance", "transmission"):
            p[face + "_" + quantity] = acrylic[material][quantity]
    p["rear_external_reflectance"] = acrylic["black_mirror"]["reverse_reflectance"]
    return p


def dimensions(p):
    baffle_z = (
        p["circle_back_z"]
        + p["circle_pcb_thickness"]
        + p["led_height"]
        + p["led_baffle_gap"]
    )
    rear_bottom = baffle_z + p["baffle_thickness"] + p["stencil_mirror_gap"]
    rear_z = rear_bottom + p["rear_black_acrylic_thickness"]
    source_z = rear_z  # Thin-sheet equivalent source at the cavity-facing coating.
    front_z = rear_z + p["mirror_gap"]
    pitch_radius = (
        p["inner_count"] * 1000 / p["strip_density"] + p["ring_seam_gap"]
    ) / math.tau
    inner_outer = (
        pitch_radius
        - p["strip_thickness"] / 2
        - p["ring_led_depth"]
        - p["ring_diffuser_led_gap"]
    )
    side_radius = (
        p["side_count"] * 1000 / p["strip_density"] + p["ring_seam_gap"]
    ) / math.tau
    return {
        "baffle_z": baffle_z,
        "source_z": source_z,
        "rear_bottom": rear_bottom,
        "rear_z": rear_z,
        "front_z": front_z,
        "depth": front_z + p["front_mirror_thickness"] + p["bezel_thickness"],
        "pitch_radius": pitch_radius,
        "side_radius": side_radius,
        "side_height": p["side_rows"] * p["strip_width"],
        "side_row_z": [
            p["side_bottom_z"] + (row + 0.5) * p["strip_width"]
            for row in range(p["side_rows"])
        ],
        "inner_outer": inner_outer,
        "wall_radius": inner_outer - p["ring_diffuser_thickness"],
        "ring_z": (rear_z + front_z) / 2,
    }


def validate(p):
    if not isinstance(p["side_rows"], int) or p["side_rows"] < 1:
        raise ValueError("Side band needs a positive whole number of strips")
    d = dimensions(p)
    if not math.isfinite(p["side_axial_scatter_mm"]) or p["side_axial_scatter_mm"] <= 0:
        raise ValueError("Side diffuser needs a finite positive axial scatter scale")
    if (
        p["side_bottom_z"] < 14
        or p["side_bottom_z"] + d["side_height"] > d["rear_bottom"] - 1.8
    ):
        raise ValueError("Side strips block the suspension slots or mirror frame seat")
    if not p["circle_diameter"] < p["case_diameter"] < 250:
        raise ValueError("Body must fit the 166 mm board and remain below 250 mm")
    if d["wall_radius"] - p["circle_diameter"] / 2 < 0.5:
        raise ValueError("Inner ring blocks the full Fibonacci source")
    if not math.isfinite(p["mirror_gap"]) or p["mirror_gap"] - p["strip_width"] < 2:
        raise ValueError("Strip needs clearance between both mirror planes")
    if d["pitch_radius"] + p["strip_thickness"] / 2 + 1.8 >= p["case_diameter"] / 2:
        raise ValueError("Insufficient inner-ring carrier wall")
    if p["front_aperture_radius"] <= d["wall_radius"]:
        raise ValueError("Bezel blocks the inward diffuser")
    if (
        p["mirror_radius"] <= d["wall_radius"]
        or p["mirror_radius"] >= p["case_diameter"] / 2 - 2
    ):
        raise ValueError("Mirror does not fit its seat")
    side_face = d["side_radius"] + p["strip_thickness"] / 2 + p["ring_led_depth"]
    if p["case_diameter"] / 2 - p["side_diffuser_thickness"] - side_face < 1:
        raise ValueError("Side diffuser blocks its LED packages")
    for side in ("front", "rear"):
        r, t = p[side + "_reflectance"], p[side + "_transmission"]
        if min(r, t) < 0 or r + t > 1:
            raise ValueError("Mirror reflection plus transmission must be at most one")
    for e in p["electronics"]:
        x, y = e["centre"]
        w, l, h = e["size"]
        if (
            max(
                math.hypot(x + sx * w / 2, y + sy * l / 2)
                for sx in (-1, 1)
                for sy in (-1, 1)
            )
            > 84
        ):
            raise ValueError(e["name"] + " exceeds the electronics bay")
        if e["z"] + h > p["circle_back_z"] - 2:
            raise ValueError(e["name"] + " blocks the board support")
    return d
