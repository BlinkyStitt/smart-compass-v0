"""Host checks for the physical mask contract, independent of OpenCASCADE."""
import json
import math
from pathlib import Path
import unittest

from geometry import contains, led_centres, mask_cells, ring_radius

HERE = Path(__file__).resolve().parent


class GeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.p = json.loads((HERE / 'parameters.json').read_text())
        cls.layout = json.loads((HERE / 'fibonacci256-layout.json').read_text())
        cls.centres = led_centres(cls.layout, cls.p)
        cls.cells = mask_cells(cls.centres, cls.p['mask_edge_radius'], cls.p['mask_web'])

    def test_every_pixel_has_one_opening_and_no_other_pixel(self):
        self.assertEqual(len(self.centres), 256)
        self.assertEqual(len(self.cells), 256)
        for i, cell in enumerate(self.cells):
            contained = [j for j, centre in enumerate(self.centres) if contains(cell, centre)]
            self.assertEqual(contained, [i])

    def test_openings_leave_the_specified_web_between_neighbour_cells(self):
        # Every opening stays at least half a web inside each Voronoi bisector.
        for i, ((x, y), cell) in enumerate(zip(self.centres, self.cells)):
            for j, (a, b) in enumerate(self.centres):
                if i == j:
                    continue
                separation = math.hypot(a - x, b - y)
                limit = (a*a + b*b - x*x - y*y) / 2
                for vx, vy in cell:
                    self.assertGreaterEqual((limit - (a-x)*vx - (b-y)*vy) / separation + 1e-7, self.p['mask_web']/2)

    def test_rotation_and_mirror_preserve_pixel_identity(self):
        p = dict(self.p, map_rotation_deg=90, map_mirror_x=True)
        for (x, y), (a, b) in zip(self.centres, led_centres(self.layout, p)):
            self.assertAlmostEqual(a, -y)
            self.assertAlmostEqual(b, -x)

    def test_ring_circumference_includes_one_seam_gap(self):
        for n in (72, 80):
            self.assertAlmostEqual(math.tau * ring_radius(n, self.p), n*1000/120 + 3)

    def test_excessive_web_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Web removes LED'):
            mask_cells(self.centres, self.p['mask_edge_radius'], 20)


if __name__ == '__main__':
    unittest.main()
