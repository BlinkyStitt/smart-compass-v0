"""Check that the placement preserves the complete socket and signal map."""

import math
import unittest

from layout import DOCK_HEADERS, read_layout, schedule
from pcb_placement import pcb_coordinates, pcb_text


class LayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = read_layout()
        cls.rows = schedule(cls.spec)
        cls.dock = [row for row in cls.rows if row["connection"] == "dock socket"]

    def test_full_socket_headers_include_unused_positions(self):
        expected = {"BLACKPILL": 40, "GPS": 16, "IMU": 14, "RADIO": 9, "SPARKLE": 6}
        actual = {module: sum(row["module"] == module for row in self.dock)
                  for module in DOCK_HEADERS}
        self.assertEqual(actual, expected)
        self.assertEqual(len(self.dock), len({(row["module"], row["source_pad"])
                                              for row in self.dock}))
        for row in self.dock:
            self.assertEqual(bool(row["baseline_net"]), bool(row["terminal"]))

    def test_key_polarities_and_radio_power(self):
        terminals = {(row["module"], row["source_pad"]): row["baseline_net"] for row in self.rows}
        self.assertEqual(terminals["GPS", "JP4.9"], "AUX_3V3")
        self.assertEqual(terminals["RADIO", "JP3.1"], "AUX_3V3")
        self.assertEqual(terminals["SPARKLE", "JP3.1"], "GND")
        self.assertEqual(terminals["SPARKLE", "X7.PWR"], "LOAD_5V")
        self.assertEqual(terminals["SPARKLE", "JP1.9"], "LED_DISTRIBUTION")

    def test_board_keeps_the_cad_datum_and_pin_spacing(self):
        self.assertEqual(pcb_coordinates(-12, 40), (88, 60))
        locations = [(row["x_mm"], row["y_mm"]) for row in self.dock]
        self.assertGreaterEqual(min(math.dist(a, b) for i, a in enumerate(locations)
                                    for b in locations[i + 1:]), 2.539)
        board = pcb_text(self.spec, self.rows)
        self.assertEqual(board.count(" thru_hole circle "), len(self.dock))
        self.assertEqual(board.count(" np_thru_hole circle "), len(self.spec["mount_xy_mm"]))
        self.assertEqual(board.count('(layer "Edge.Cuts")'), len(self.spec["outline_xy_mm"]))
        self.assertNotIn("(segment ", board)
        self.assertNotIn("(via ", board)


if __name__ == "__main__":
    unittest.main()
