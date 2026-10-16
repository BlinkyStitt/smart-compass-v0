"""Behavior checks for compact fit and a separately derived optical reference."""

import json
import math
import unittest

from layout import ROOT, dimensions, parameters, validate
from optics import reference, side_weight


class FitTests(unittest.TestCase):
    def test_full_board_inner_ring_and_three_side_strips_fit(self):
        p = parameters()
        d = validate(p)
        self.assertAlmostEqual(p["case_diameter"], 190)
        self.assertGreater(d["wall_radius"] - 83, 0.5)
        self.assertAlmostEqual(d["front_z"] - d["rear_z"], 20)
        self.assertEqual(p["side_rows"], 3)
        self.assertAlmostEqual(d["side_height"], 30)
        self.assertEqual(d["side_row_z"], [19, 29, 39])
        self.assertLess(p["side_bottom_z"] + d["side_height"], d["rear_bottom"] - 0.8)
        self.assertAlmostEqual(d["depth"], 73.6)

    def test_side_strip_limits_preserve_slots_and_mirror_seat(self):
        p = parameters()
        self.assertEqual(validate(dict(p, side_rows=2))["side_height"], 20)
        for change in (
            {"side_rows": 4},
            {"side_rows": 0},
            {"side_bottom_z": 13},
            {"side_axial_scatter_mm": 0},
        ):
            with self.assertRaises(ValueError):
                validate(dict(p, **change))

    def test_electronics_keep_original_dimensions(self):
        old = json.loads((ROOT / "hardware/enclosure/parameters.json").read_text())
        names = {
            "Battery": "battery",
            "SparkleMotion": "sparkle",
            "BlackPill": "blackpill",
            "GPS": "gps",
            "IMU": "imu",
            "Radio": "radio",
            "BatterySense": "sense",
            "Boost5V": "power",
        }
        for e in parameters()["electronics"]:
            key = names[e["name"]]
            expected = sorted(
                [old[key + "_width"], old[key + "_length"], old[key + "_height"]]
            )
            self.assertEqual(sorted(e["size"]), expected, e["name"])

    def test_reject_blocked_source_and_invalid_coating(self):
        p = parameters()
        with self.assertRaisesRegex(ValueError, "blocks"):
            validate(dict(p, inner_count=64))
        with self.assertRaisesRegex(ValueError, "at most one"):
            validate(dict(p, rear_transmission=0.8))
        with self.assertRaisesRegex(ValueError, "below 250"):
            validate(dict(p, case_diameter=250))
        with self.assertRaisesRegex(ValueError, "clearance"):
            validate(dict(p, mirror_gap=10))


class OpticalTests(unittest.TestCase):
    def setUp(self):
        d = dimensions(parameters())
        self.o = {
            k: d[k] / 1000 for k in ("front_z", "rear_z", "wall_radius", "ring_z")
        }
        self.o["diffusion"] = 0.65
        self.o["side_axial_scatter"] = parameters()["side_axial_scatter_mm"] / 1000
        self.point = [0, 0, self.o["front_z"]]

    def test_head_on_is_two_transmissions_and_round_trip_series(self):
        measured = reference(self.point, [0, 0, -1], self.o)
        # R=.5, T=.5: five non-negligible round trips at a .001 path cutoff.
        actual = reference(self.point, [0, 0, -1], self.o, 0.5, 0.5, 0.5, 0.5)
        expected = sum(0.25 * 0.25**n for n in range(5))
        self.assertAlmostEqual(actual[0], expected)
        self.assertEqual(actual[1], 0)
        # Coated black rear T9 and clear front T30: 2.7% first image; 49% per round trip.
        # Eight rear encounters remain above the unchanged .001 path cutoff.
        self.assertAlmostEqual(measured[0], sum(0.027 * 0.49**n for n in range(8)))
        self.assertEqual(measured[2], 16)

    def test_no_reflection_gives_one_source_image(self):
        self.assertEqual(
            reference(self.point, [0, 0, -1], self.o, 0, 1, 0, 1), [1, 0, 1]
        )

    def test_opaque_front_and_outward_rays_emit_nothing(self):
        for direction in ([0, 0, 1], [1, 0, 0]):
            self.assertEqual(reference(self.point, direction, self.o), [0, 0, 0])
        self.assertEqual(
            reference(self.point, [0, 0, -1], self.o, 1, 0, 0.5, 0.5), [0, 0, 0]
        )

    def test_ring_at_mid_gap_has_unit_axial_profile(self):
        gap = self.o["front_z"] - self.o["rear_z"]
        slope = self.o["wall_radius"] / (gap / 2)
        result = reference(self.point, [slope, 0, -1], self.o)
        self.assertAlmostEqual(result[0], 0)
        self.assertAlmostEqual(result[1], 0.30)
        self.assertEqual(result[2], 0)

    def test_side_sleeve_blends_the_gaps_without_more_source_power(self):
        step = 0.010
        values = [
            sum(side_weight(z * step / 100, row * step, self.o) for row in range(3))
            for z in range(50, 151)
        ]
        self.assertGreater(min(values) / max(values), 0.95)
        # The new profile retains the narrow profile's integrated source light.
        dz = 0.0001
        integrated = sum(
            side_weight(i * dz, 0, self.o) * dz for i in range(-1000, 1001)
        )
        original = 0.005 + math.sqrt(math.pi) * (
            0.00015 + 0.00285 * self.o["diffusion"]
        )
        self.assertAlmostEqual(integrated, original, places=8)
        self.assertLess(side_weight(0.040, 0, self.o), 1e-10)

    def test_reflection_cap_terminates_low_loss_case(self):
        result = reference(self.point, [0, 0, -1], self.o, 0.999, 0.001, 0.999, 0.001)
        self.assertEqual(
            result[2], 1
        )  # weight drops below cutoff after the first rear encounter
        result = reference(self.point, [0, 0, -1], self.o, 0.99, 0.01, 0.99, 0.01)
        self.assertEqual(result[2], 32)


if __name__ == "__main__":
    unittest.main()
