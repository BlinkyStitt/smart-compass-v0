"""Host checks for the physical mask contract, independent of OpenCASCADE."""
import json
import math
from pathlib import Path
import unittest

from geometry import contains, led_centres, mask_cells, optical_dimensions, ring_pixel, ring_radius, strip_bottom

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
        for n in (self.p['halo_count'], self.p['inner_count'], self.p['outer_count']):
            self.assertAlmostEqual(math.tau * ring_radius(n, self.p), n*1000/120 + 3)

    def test_inner_emits_toward_circle_and_outer_emits_outward(self):
        for count,outward in ((self.p['halo_count'],True),(self.p['inner_count'],False),(self.p['outer_count'],True)):
            for i in range(count):
                (x,y),(nx,ny) = ring_pixel(count,i,outward,self.p)
                dot = x*nx+y*ny
                self.assertGreater(dot if outward else -dot,0)
                self.assertAlmostEqual(math.hypot(nx,ny),1)
                if i == 0:
                    self.assertGreater(y,0)

    def test_mirror_gap_and_edge_clearance_have_room(self):
        d = optical_dimensions(self.p)
        self.assertGreaterEqual(d['visible_mirror_width'],20)
        self.assertGreaterEqual(d['circle_to_inner_led'],20)
        self.assertGreaterEqual(d['mirror_separation'],self.p['strip_width']+.4)
        self.assertGreaterEqual(d['outer_led_clearance'],.5)

    def test_outer_row_stays_centered_when_case_depth_changes(self):
        for depth in (45,48,52):
            p = dict(self.p,case_depth=depth)
            rear,front = p['edge_bottom_z'],depth-p['front_bezel_thickness']
            self.assertAlmostEqual(strip_bottom('Outer',p)+p['strip_width']/2,(rear+front)/2)
            self.assertEqual(strip_bottom('Inner',p),p['strip_bottom_z'])
            self.assertEqual(strip_bottom('Halo',p),p['strip_bottom_z'])

    def test_halo_fits_around_circle_inside_the_mirror_gap(self):
        r = ring_radius(self.p['halo_count'],self.p)
        self.assertGreater(r-self.p['strip_thickness']/2,self.p['circle_diameter']/2+1)
        halo_face = r+self.p['strip_thickness']/2+self.p['ring_led_depth']
        inner_face = ring_radius(self.p['inner_count'],self.p)-self.p['strip_thickness']/2-self.p['ring_led_depth']
        self.assertGreaterEqual(inner_face-halo_face,20)

    def test_excessive_web_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Web removes LED'):
            mask_cells(self.centres, self.p['mask_edge_radius'], 20)


if __name__ == '__main__':
    unittest.main()
