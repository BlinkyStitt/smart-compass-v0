"""Failure and raw-length tests for the specified round-wire route contract."""
import math
import unittest
import harness_route as route

class RouteTests(unittest.TestCase):
    def test_quarter_bend_tangent_and_length(self):
        rows=route.segments([[0,0,0],[10,0,0],[10,10,0]],2)
        self.assertEqual([r['kind'] for r in rows],['line','arc','line'])
        expected=[[8,0,0],[8+2/math.sqrt(2),2-2/math.sqrt(2),0],[10,2,0]]
        for actual,want in zip(rows[1]['points'],expected):
            for a,b in zip(actual,want):self.assertAlmostEqual(a,b,places=12)
        self.assertAlmostEqual(math.fsum(r['length_mm'] for r in rows),16+math.pi,places=12)

    def test_arbitrary_plane_and_oblique_bend(self):
        rows=route.segments([[0,0,0],[10,0,0],[20,0,10]],2)
        arc=rows[1];self.assertAlmostEqual(arc['length_mm'],math.pi/2)
        a,m,b=arc['points']
        # The three points lie on the declared circle; no XY-only shortcut.
        centre=[10-2*math.tan(math.pi/8),0,2]
        for point in [a,m,b]:self.assertAlmostEqual(route.norm(route.sub(point,centre)),2)

    def test_insufficient_distance_between_bends_rejected(self):
        with self.assertRaisesRegex(ValueError,'Insufficient'):
            route.segments([[0,0,0],[5,0,0],[5,3,0],[10,3,0]],2)

    def test_internal_jacket_overlap_and_continuous_contact_segment_count_once(self):
        wire={'strip_ends_mm':[4,5],'insertion_ends_mm':[6,5],'existing_segment_cut_mm':42.25,'blank_trim_allowance_mm':20}
        record=route.cut_record(wire,[[0,0,0],[20,0,0]],4)
        self.assertEqual(record['finished_cut_target_mm'],73.25)
        self.assertEqual(record['blank_cut_target_mm'],93.25)
        self.assertEqual(record['strip_ends_mm'],[4,5])

    def test_reversal_duplicate_or_nonfinite_rejected(self):
        for points in [[[0,0,0],[0,0,0]],[[0,0,0],[5,0,0],[0,0,0]],[[0,0,0],[math.nan,0,0]]]:
            with self.subTest(points=points),self.assertRaises(ValueError):route.segments(points,2)

    def test_cut_accounts_both_strips_once_and_blank_separately(self):
        wire={'strip_ends_mm':[2.5,5],'blank_trim_allowance_mm':20,'id':'W001'}
        row=route.cut_record(wire,[[0,0,0],[13.123456789,0,0]],2)
        self.assertEqual(row['insulated_length_mm'],13.123456789)
        self.assertAlmostEqual(row['finished_cut_target_mm'],20.623456789,places=12)
        self.assertAlmostEqual(row['blank_cut_target_mm'],40.623456789,places=12)
        self.assertEqual(row['physical_acceptance'],'unmeasured')

if __name__=='__main__':unittest.main()
