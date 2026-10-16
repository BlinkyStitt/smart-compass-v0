"""Behavior checks for compact fit and a separately derived optical reference."""

import json
import unittest

from layout import ROOT, dimensions, parameters, validate
from optics import reference


class FitTests(unittest.TestCase):
    def test_full_board_and_both_strips_fit(self):
        p = parameters()
        d = validate(p)
        self.assertAlmostEqual(p["case_diameter"], 190)
        self.assertGreater(d["wall_radius"] - 83, 0.5)
        self.assertAlmostEqual(d["front_z"] - d["rear_z"], 20)
        self.assertLess(p["side_bottom_z"] + p["strip_width"], d["rear_bottom"])
        self.assertAlmostEqual(d["depth"], 72.6)

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
        self.point = [0, 0, self.o["front_z"]]

    def test_head_on_is_two_transmissions_and_round_trip_series(self):
        measured = reference(self.point, [0, 0, -1], self.o)
        # R=.5, T=.5: five non-negligible round trips at a .001 path cutoff.
        actual = reference(self.point, [0, 0, -1], self.o, 0.5, 0.5, 0.5, 0.5)
        expected = sum(0.25 * 0.25**n for n in range(5))
        self.assertAlmostEqual(actual[0], expected)
        self.assertEqual(actual[1], 0)
        self.assertGreater(measured[0], 0.25 * 0.25)
        self.assertLess(measured[0], 0.25 * 0.25 / (1 - 0.65 * 0.65))

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
        self.assertAlmostEqual(result[1], 0.25)
        self.assertEqual(result[2], 0)

    def test_reflection_cap_terminates_low_loss_case(self):
        result = reference(self.point, [0, 0, -1], self.o, 0.999, 0.001, 0.999, 0.001)
        self.assertEqual(
            result[2], 1
        )  # weight drops below cutoff after the first rear encounter
        result = reference(self.point, [0, 0, -1], self.o, 0.99, 0.01, 0.99, 0.01)
        self.assertEqual(result[2], 32)


if __name__ == "__main__":
    unittest.main()
