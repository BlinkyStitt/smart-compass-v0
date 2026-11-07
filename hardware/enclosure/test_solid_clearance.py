"""Check conservative pruning, including obstacles at coincident bounds."""
import math
from copy import deepcopy
from unittest.mock import patch
from types import SimpleNamespace
import unittest

from solid_clearance import bounds, box_distance, distance, FixedObstacles


def box(x0,x1,y0=0,y1=1,z0=0,z1=1):
    return SimpleNamespace(XMin=x0,XMax=x1,YMin=y0,YMax=y1,ZMin=z0,ZMax=z1)


class Solid:
    def __init__(self, bounds, exact=0):
        self.BoundBox=bounds
        self.exact=exact
        self.calls=0
    def copy(self):
        return deepcopy(self)
    def optimalBoundingBox(self,useTriangulation,useShapeTolerance):
        assert useTriangulation is False and useShapeTolerance is True
        return self.true_bounds if hasattr(self,"true_bounds") else self.BoundBox
    def distToShape(self,other):
        other.calls+=1
        return (other.exact,)


class ClearanceTests(unittest.TestCase):
    def test_box_distance_uses_all_axes_and_overlap(self):
        self.assertEqual(box_distance(box(0,1),box(.5,2)),0)
        self.assertEqual(box_distance(box(0,1),box(4,5,5,6)),5)
        self.assertEqual(box_distance(box(4,5,5,6),box(0,1)),5)

    def test_far_box_is_pruned_after_near_exact_distance(self):
        near=Solid(box(1.1,2),.2)
        far=Solid(box(4,5),3.5)
        self.assertEqual(distance(Solid(box(0,1)),[far,near]),.2)
        self.assertEqual((near.calls,far.calls),(1,0))

    def test_overlapping_boxes_cannot_hide_thin_obstacle(self):
        decoy=Solid(box(-1,2),.8)
        thin=Solid(box(.99,1.01),0)
        self.assertEqual(distance(Solid(box(0,1)),[decoy,thin]),0)
        self.assertEqual(thin.calls,1)

    def test_wide_empty_space_in_box_is_not_exact_clearance(self):
        a=Solid(box(-5,5),8)
        b=Solid(box(2,3),2)
        self.assertEqual(distance(Solid(box(0,1)),[a,b]),2)
        self.assertEqual(b.calls,1)

    def test_equal_lower_bound_is_checked(self):
        first=Solid(box(1,2),.5)
        second=Solid(box(1.5,2),.5)
        self.assertEqual(distance(Solid(box(0,1)),[first,second]),.5)
        self.assertEqual(second.calls,1)

    def test_display_mesh_bounds_cannot_hide_a_closer_curved_obstacle(self):
        # Synthetic failure test for the observed ActionBackplate serialization
        #difference. It does not supply assembly or physical acceptance data.
        decoy=Solid(box(1.2,2),.4)
        curved=Solid(box(3,4),.1)
        curved.true_bounds=box(1.05,4)
        self.assertEqual(distance(Solid(box(0,1)),[decoy,curved]),.1)
        self.assertEqual(curved.calls,1)

    def test_fixed_query_keeps_its_source_pose_and_exact_nearest_obstacle(self):
        decoy=Solid(box(1.2,2),.4)
        curved=Solid(box(3,4),.1)
        curved.true_bounds=box(1.05,4)
        query=FixedObstacles([decoy,curved])
        moving=Solid(box(0,1))
        self.assertEqual(query.distance(moving),distance(moving,[decoy,curved]))
        # Later changes belong to a different fixed assembly pose. The owned
        #snapshot remains unchanged; a fresh query sees the new obstruction.
        curved.true_bounds=box(.9,4)
        curved.exact=0
        self.assertEqual(query.distance(moving),.1)
        self.assertEqual(distance(moving,[decoy,curved]),0)

    def test_fixed_bounds_are_reused_but_moving_bounds_are_refreshed(self):
        near=Solid(box(1.1,2),.2)
        far=Solid(box(4,5),3.5)
        with patch('solid_clearance.bounds',wraps=bounds) as measured:
            query=FixedObstacles([near,far])
            self.assertEqual(measured.call_count,2)
            self.assertEqual(query.distance(Solid(box(0,1))),.2)
            self.assertEqual(query.distance(Solid(box(.05,1.05))),.2)
            self.assertEqual(measured.call_count,4)

    def test_fixed_query_rejects_missing_and_invalid_clearance(self):
        with self.assertRaises(ValueError):FixedObstacles([])
        for invalid in (-1,math.inf,math.nan):
            query=FixedObstacles([Solid(box(1,2),invalid)])
            with self.subTest(value=invalid),self.assertRaises(ValueError):
                query.distance(Solid(box(0,1)))

    def test_empty_and_invalid_distances_fail(self):
        with self.assertRaises(ValueError):distance(Solid(box(0,1)),[])
        for invalid in (-1,math.inf,math.nan):
            with self.subTest(value=invalid),self.assertRaises(ValueError):
                distance(Solid(box(0,1)),[Solid(box(1,2),invalid)])


if __name__=='__main__':unittest.main()
