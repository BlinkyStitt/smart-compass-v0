"""Reject a frozen field and the former hue-only gradient, even with a moving camera."""
import colorsys
import unittest
from pride import pride_frames
from spiral_motion import colour_report


class PrideTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.frames = pride_frames([256, 70, 70, 70])

    def fields(self, mode):
        result = []
        for frame in range(0, 384, 8):
            samples = []
            for index in range(0, 256, 4):
                target = self.frames[frame][0][index]
                if mode == 'moving':
                    actual = target
                elif mode == 'frozen':
                    actual = self.frames[0][0][index]
                else:
                    actual = colorsys.hsv_to_rgb((index / 64 - frame / 192) % 1, 1, 1)
                samples.append((actual, target))
            result.append(samples)
        return result

    def test_indexed_chase_passes(self):
        self.assertGreater(min(colour_report(self.fields('moving'), 'board')), .99)

    def test_frozen_and_hue_only_fields_fail(self):
        for mode in ('hue-only', 'frozen'):
            with self.subTest(mode=mode), self.assertRaisesRegex(RuntimeError, 'no indexed Pride chase'):
                colour_report(self.fields(mode), 'board')

    def test_every_led_stays_lit_and_frames_keep_physical_order(self):
        self.assertEqual(len(self.frames), 384)
        for frame in self.frames:
            self.assertEqual([len(row) for row in frame], [256, 70, 70, 70])
            self.assertTrue(all(.10 < max(rgb) <= 1 for row in frame for rgb in row))

    def test_loop_join_has_no_colour_jump(self):
        def difference(a, b):
            return sum(abs(x - y) for ar, br in zip(a, b) for ap, bp in zip(ar, br)
                       for x, y in zip(ap, bp)) / (466 * 3)
        typical = sorted(difference(a, b) for a, b in zip(self.frames, self.frames[1:]))[192]
        self.assertLess(difference(self.frames[-1], self.frames[0]), typical * 1.5)
