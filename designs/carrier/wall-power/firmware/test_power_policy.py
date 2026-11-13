import json
import math
from pathlib import Path
import unittest

from export_layout import ordered_positions
from power_policy import (
    BATTERY_BUDGET, PIXEL_COUNTS, WALL_BRANCH_BUDGETS, WALL_BUDGET, rainbow_frame,
)


def current_255(frame):
    return len(frame) * 255 + 20 * sum(sum(rgb) for rgb in frame)


class PowerPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path = Path(__file__).resolve().parents[3] / "stacked/exports/scene.json"
        scene = json.loads(path.read_text())
        cls.phases = [
            [math.atan2(x, y) / math.tau + (2 * math.hypot(x, y) / .0795 if i == 0 else 0)
             for x, y in group]
            for i, group in enumerate(ordered_positions(scene))
        ]

    def test_limits_and_visible_motion_over_full_cycle(self):
        previous = rainbow_frame(self.phases, 0, True)
        peak_wall = 0
        peak_battery = 0
        for step in range(512):
            elapsed = step / 64
            wall = rainbow_frame(self.phases, elapsed, True)
            battery = rainbow_frame(self.phases, elapsed, False)
            self.assertEqual(tuple(map(len, wall)), PIXEL_COUNTS)
            for branch, cap in zip(wall, WALL_BRANCH_BUDGETS):
                self.assertLessEqual(current_255(branch), cap * 255)
                self.assertTrue(all(max(rgb) > 0 for rgb in branch))
            wall_current = sum(map(current_255, wall))
            battery_current = sum(map(current_255, battery))
            self.assertLessEqual(wall_current, WALL_BUDGET * 255)
            self.assertLessEqual(battery_current, BATTERY_BUDGET * 255)
            peak_wall = max(peak_wall, wall_current)
            peak_battery = max(peak_battery, battery_current)
        self.assertNotEqual(previous, rainbow_frame(self.phases, 0.5, True))
        self.assertEqual(previous, rainbow_frame(self.phases, 8, True))
        self.assertGreater(peak_wall, 2.5 * peak_battery)

    def test_all_pixels_at_peak_channel_sum(self):
        yellow = [[1 / 6] * count for count in PIXEL_COUNTS]
        for wall, budget in ((False, BATTERY_BUDGET), (True, WALL_BUDGET)):
            frame = rainbow_frame(yellow, 0, wall)
            self.assertLessEqual(sum(map(current_255, frame)), budget * 255)
            self.assertTrue(all(max(rgb) > 0 for branch in frame for rgb in branch))
        for branch, budget in zip(rainbow_frame(yellow, 0, True), WALL_BRANCH_BUDGETS):
            self.assertLessEqual(current_255(branch), budget * 255)


if __name__ == "__main__":
    unittest.main()
