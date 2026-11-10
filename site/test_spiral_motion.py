"""A hue cycle or a frozen bright spiral must not satisfy travelling-light checks."""
import colorsys
import unittest
from spiral_motion import wave_level, wave_report


class TravellingWaveTests(unittest.TestCase):
    def fields(self, mode):
        result = []
        for frame in range(0, 384, 8):
            samples = []
            for index in range(64):
                spatial = index / 64
                expected = wave_level(spatial, frame)
                actual = 1 if mode == 'hue-only' else wave_level(spatial, 0 if mode == 'frozen' else frame)
                samples.append((colorsys.hsv_to_rgb((spatial - frame / 192) % 1, 1, actual), expected))
            result.append(samples)
        return result

    def test_travelling_spiral_passes(self):
        self.assertGreater(wave_report(self.fields('moving'), 'board'), .99)

    def test_hue_only_and_frozen_light_fields_fail(self):
        for mode in ('hue-only', 'frozen'):
            with self.subTest(mode=mode), self.assertRaisesRegex(RuntimeError, 'no travelling spiral'):
                wave_report(self.fields(mode), 'board')

    def test_every_section_stays_lit(self):
        levels = [wave_level(spatial / 64, frame) for spatial in range(64) for frame in range(96)]
        self.assertGreaterEqual(min(levels), .45)
        self.assertLessEqual(max(levels), 1)
