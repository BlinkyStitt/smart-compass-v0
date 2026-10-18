"""Reject the animation failures that a small central RGB difference misses."""
import colorsys
import unittest
from media import SAMPLE_FRAMES, _masked_report, _colour_bounds, _read_phase, _rotation_report


class RotationTests(unittest.TestCase):
    def samples(self, speed=1, spread=0.3):
        return [
            {"frame": frame, "phase": (0.2 - speed * frame / 24 / 8) % 1,
             "coherence": 0.9, "spread": spread}
            for frame in SAMPLE_FRAMES
        ]

    def test_two_complete_rotations_and_wrap(self):
        self.assertAlmostEqual(_rotation_report(self.samples(), "board")["turns"], 2)

    def test_frozen_outside_ring_cannot_pass(self):
        with self.assertRaisesRegex(RuntimeError, "outer.*did not rotate"):
            _rotation_report(self.samples(speed=0), "outer")

    def test_slow_hue_change_is_not_a_complete_turn(self):
        with self.assertRaisesRegex(RuntimeError, "did not rotate"):
            _rotation_report(self.samples(speed=0.25), "board")

    def test_wrong_direction_is_not_the_shared_rotation(self):
        with self.assertRaisesRegex(RuntimeError, "did not rotate"):
            _rotation_report(self.samples(speed=-1), "outer")

    def test_uniform_colour_cycling_is_not_a_spatial_rainbow(self):
        with self.assertRaisesRegex(RuntimeError, "no coherent spatial rainbow"):
            _rotation_report(self.samples(spread=0), "board")


class MaterialPhaseTests(unittest.TestCase):
    def tinted_field(self, frame, speed=1, uniform=False):
        samples = []
        for i in range(64):
            base = i / 64
            hue = ((0 if uniform else base) + 0.2 - speed * frame / 192) % 1
            rgb = colorsys.hsv_to_rgb(hue, 1, 1)
            # Green phosphor and unequal channel transmission distort raw HSV.
            observed = [offset + gain * c for c, offset, gain in
                        zip(rgb, (0.2, 0.45, 0.1), (0.6, 0.5, 0.55))]
            samples.append((observed, base))
        return samples

    def readings(self, speed=1, uniform=False):
        fields = [self.tinted_field(n, speed, uniform) for n in SAMPLE_FRAMES]
        bounds = _colour_bounds(fields)
        return [dict(_read_phase(field, bounds), frame=n)
                for field, n in zip(fields, SAMPLE_FRAMES)]

    def test_filtered_rainbow_recovers_source_phase(self):
        readings = self.readings()
        for sample in readings:
            expected = 0.2 - sample["frame"] / 192
            error = (sample["phase"] - expected + 0.5) % 1 - 0.5
            self.assertLess(abs(error), 0.001)
        self.assertAlmostEqual(_rotation_report(readings, "outer")["turns"], 2)

    def test_material_normalization_cannot_make_a_frozen_field_move(self):
        with self.assertRaisesRegex(RuntimeError, "did not rotate"):
            _rotation_report(self.readings(speed=0), "outer")

    def test_material_normalization_rejects_uniform_colour_cycling(self):
        readings = self.readings(uniform=True)
        self.assertTrue(all(r["coherence"] < 0.65 for r in readings))
        with self.assertRaisesRegex(RuntimeError, "no coherent spatial rainbow"):
            _rotation_report(readings, "outer")


class MaskTests(unittest.TestCase):
    def fields(self, wrong=False, canonical=False):
        fields = []
        for frame in range(48):
            colours = []
            for led in range(64):
                mask = float((led + frame) % 8 >= 4)
                actual = (1 - mask) if wrong else mask
                if canonical:
                    actual = 1
                rgb = colorsys.hsv_to_rgb((led / 64 - frame / 24) % 1, 1, 1)
                colours.append(([.15 + .6 * c * actual for c in rgb], mask))
            fields.append(colours)
        return fields

    def test_stored_glow_offset_allows_correct_mask(self):
        self.assertGreater(_masked_report(self.fields(), "board"), .9)

    def test_wrong_shape_and_unmasked_rainbow_fail(self):
        for fields in (self.fields(wrong=True), self.fields(canonical=True)):
            with self.assertRaisesRegex(RuntimeError, "dark mask mismatch"):
                _masked_report(fields, "outer")

    def test_frozen_field_fails(self):
        fields = self.fields()
        frozen = [[(fields[0][i][0], mask) for i, (_, mask) in enumerate(field)] for field in fields]
        with self.assertRaisesRegex(RuntimeError, "dark mask mismatch"):
            _masked_report(frozen, "board")
