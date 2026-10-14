"""Host checks for the physical mask contract, independent of OpenCASCADE."""
import json
import math
from pathlib import Path
import unittest

from geometry import cavity_diffusers, contains, led_centres, mask_cells, optical_dimensions, ring_pixel, ring_radius, ring_locating_angles, ring_movement_limit, ring_led_clearances, strip_bottom, top_light_shields

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
        for depth in (35,45,48,52):
            p = dict(self.p,front_plane_z=depth)
            rear,front = p['edge_bottom_z'],depth
            self.assertAlmostEqual(strip_bottom('Outer',p)+p['strip_width']/2,(rear+front-p['ring_front_clearance'])/2)
            self.assertEqual(strip_bottom('Inner',p),p['strip_bottom_z'])
            self.assertEqual(strip_bottom('Halo',p),p['strip_bottom_z'])

    def test_halo_fits_around_circle_inside_the_mirror_gap(self):
        r = ring_radius(self.p['halo_count'],self.p)
        self.assertGreater(r-self.p['strip_thickness']/2,self.p['circle_diameter']/2+1)
        halo_face = r+self.p['strip_thickness']/2+self.p['ring_led_depth']
        inner_face = ring_radius(self.p['inner_count'],self.p)-self.p['strip_thickness']/2-self.p['ring_led_depth']
        self.assertGreaterEqual(inner_face-halo_face,20)

    def test_diffusers_keep_led_clearance_and_an_open_mirror_cavity(self):
        self.assertNotIn('ring_diffuser_end_gap',self.p)
        self.assertNotIn('ring_diffuser_seam_gap',self.p)
        self.assertAlmostEqual(self.p['ring_bottom_clearance'],.1)
        bands = cavity_diffusers(self.p)
        halo_face = ring_radius(self.p['halo_count'],self.p)+self.p['strip_thickness']/2+self.p['ring_led_depth']
        inner_face = ring_radius(self.p['inner_count'],self.p)-self.p['strip_thickness']/2-self.p['ring_led_depth']
        self.assertAlmostEqual(bands['Halo']['inner']-halo_face,self.p['ring_diffuser_led_gap'])
        self.assertAlmostEqual(inner_face-bands['Inner']['outer'],self.p['ring_diffuser_led_gap'])
        self.assertGreaterEqual(min(ring_led_clearances(self.p).values())-ring_movement_limit(self.p,self.p['ring_radial_error_budget'])+1e-9,.5)
        self.assertGreaterEqual(self.p['ring_cuff_height']-.8+1e-9,.4)
        self.assertGreaterEqual(bands['Inner']['inner']-bands['Halo']['outer'],18)
        for band in bands.values():
            self.assertLess(band['bottom'],self.p['strip_bottom_z'])
            self.assertGreater(band['bottom']+band['height'],self.p['strip_bottom_z']+self.p['strip_width'])

    def test_opaque_shields_cover_exposed_led_edges_without_trapping_rings(self):
        shields=top_light_shields(self.p)
        self.assertEqual(set(shields),{'Halo','Inner','Outer'})
        for name,dim in shields.items():
            count=int(self.p[name.lower()+'_count'])
            for i in range(count):
                (x,y),_=ring_pixel(count,i,name!='Inner',self.p)
                self.assertLess(dim['inner'],math.hypot(x,y))
                self.assertGreater(dim['outer'],math.hypot(x,y))
            self.assertGreaterEqual(dim['bottom']-strip_bottom(name,self.p)-self.p['strip_width']+1e-9,.1)
            self.assertGreaterEqual(self.p['front_plane_z']-dim['bottom']-dim['height'],.4)
            if name != 'Outer':
                band=cavity_diffusers(self.p)[name]
                self.assertAlmostEqual(dim['bottom'],band['bottom']+band['height'])
            else:
                self.assertAlmostEqual(dim['bottom'],self.p['edge_bottom_z']+33)

    def test_ring_movement_uses_locator_geometry_and_package_corners(self):
        self.assertEqual(len(ring_locating_angles(self.p)),8)
        self.assertGreater(ring_movement_limit(self.p),self.p['ring_seat_play'])
        self.assertLess(ring_movement_limit(self.p),.217)
        self.assertLess(ring_movement_limit(self.p,.2),.434)
        six=dict(self.p,ring_station_count=6)
        self.assertLess(self.p['strip_thickness']+self.p['light_shield_edge_clearance']-ring_movement_limit(six,.2),.04)
        old=dict(self.p,ring_station_count=3,ring_seat_play=.3)
        self.assertGreater(ring_movement_limit(old),.59)
        self.assertLess(ring_led_clearances(self.p)['Halo'],self.p['ring_diffuser_led_gap'])
        self.assertGreaterEqual(min(ring_led_clearances(self.p).values())-ring_movement_limit(self.p,.2),.53)

    def test_excessive_web_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Web removes LED'):
            mask_cells(self.centres, self.p['mask_edge_radius'], 20)


if __name__ == '__main__':
    unittest.main()
