"""Mechanical contract regressions; RF range is deliberately not asserted."""

import json
import math
from pathlib import Path
import unittest
import tempfile
import xml.etree.ElementTree as ET

import antenna


class AntennaTests(unittest.TestCase):
    def setUp(self):
        self.p = json.loads((Path(__file__).parent/'parameters.json').read_text())
        self.route = antenna.validate(self.p)

    def test_open_rear_view_mirrors_x_and_keeps_necklace_up(self):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory)/'antenna.svg'
            antenna.diagram(self.route, [], {}, out)
            root = ET.fromstring(out.read_text())
            circles = root.findall('.//{http://www.w3.org/2000/svg}circle')
            # The original's negative-X ANT appears on the right when opening
            # the rear; positive Y must stay above the case centre.
            self.assertGreater(float(circles[1].get('cx')), float(circles[0].get('cx')))
            self.assertLess(float(circles[1].get('cy')), float(circles[0].get('cy')))
            self.assertIn('Open rear: +X left', out.read_text())

    def test_total_includes_feed_bend_and_straight(self):
        r = self.route
        self.assertAlmostEqual(r.rise-r.bend + math.pi*r.bend/2 + r.straight, 78)
        self.assertEqual(r.feed, (-85.636, 16.094, 6.0))
        self.assertEqual(r.direction, -1)
        self.assertEqual(r.top, 17)
        self.assertEqual(r.envelope, .7)

    def test_invalid_dimensions_and_nonfinite_coordinates(self):
        for key in (k for k in self.p if k.startswith('antenna_')):
            for value in (float('nan'), float('inf'), None, True):
                with self.subTest(key=key, value=value):
                    p = dict(self.p, **{key: value})
                    with self.assertRaisesRegex(ValueError, '250 mm original antenna'):
                        antenna.validate(p)
        for key in ('antenna_wire_diameter', 'antenna_rise', 'antenna_bend_radius', 'antenna_position_tolerance'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                antenna.validate(dict(self.p, **{key: 0}))
        with self.assertRaisesRegex(ValueError, 'Radio envelope'):
            antenna.validate(dict(self.p, radio_x=float('nan')))

    def test_extension_wrong_datum_and_restraints_are_rejected(self):
        for key, value in [('antenna_length',80), ('antenna_feed_x',9), ('antenna_rotation_deg',90),
                           ('antenna_stripped_length',4), ('antenna_second_restraint',77),
                           ('antenna_feed_relief_radius',20), ('radio_width',24)]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                antenna.validate(dict(self.p, **{key: value}))

    def test_thin_obstacle_between_route_vertices_fails(self):
        x, y, z = self.route.point(31.37)
        obstacle = ('M3 screw', (x-.01,y-.01,z-.01), (x+.01,y+.01,z+.01), .5)
        with self.assertRaisesRegex(ValueError, '250 mm original antenna: M3 screw'):
            antenna.check_boxes(self.route, [obstacle])

    def test_insulation_and_position_tolerance_both_count(self):
        x, y, z = self.route.point(30)
        obstacle = ('LED lead', (x+.65,y-1,z-1), (x+.8,y+1,z+1), 0)
        with self.assertRaisesRegex(ValueError, 'LED lead'):
            antenna.check_boxes(self.route, [obstacle])
        obstacle = ('LED lead', (x+2.71,y-1,z-1), (x+3,y+1,z+1), 2)
        self.assertGreater(antenna.check_boxes(self.route, [obstacle])['LED lead'],2)

    def test_removal_finds_obstruction_between_sample_positions(self):
        x, y, z = self.route.point(30)
        obstacle = ('seal lip', (x-.01,y-.01,z-7.2), (x+.01,y+.01,z-7.19), .5)
        antenna.check_boxes(self.route, [obstacle])
        with self.assertRaisesRegex(ValueError, 'antenna removal: seal lip'):
            antenna.check_boxes(self.route, [obstacle], removal=40)

    def test_component_movement_blocks_route(self):
        x, y, _ = self.route.point(30)
        p = dict(self.p, battery_x=x, battery_y=y)
        with self.assertRaisesRegex(ValueError, 'battery'):
            antenna.validate(p)

    def test_distance_includes_endcaps_and_diagonal_minimum(self):
        self.assertAlmostEqual(antenna.box_distance((0,0,0),(10,10,0),(4,0,0),(6,1,1)), 3/math.sqrt(2))
        self.assertAlmostEqual(antenna.box_distance((0,0,0),(1,0,0),(2,-1,-1),(3,1,1)), 1)

    def test_invalid_obstacle_fails_with_its_name(self):
        for lo, hi in [((0,0,0),(0,1,1)), ((0,0,0),(math.inf,1,1))]:
            with self.assertRaisesRegex(ValueError, 'invalid obstacle bad seal'):
                antenna.check_boxes(self.route, [('bad seal', lo, hi, .5)])


if __name__ == '__main__':
    unittest.main()
