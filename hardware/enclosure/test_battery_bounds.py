"""Synthetic native-gate regression only; no assembly/physical evidence."""
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import battery_access as subject

def box(lo,hi):
    return SimpleNamespace(XMin=lo,XMax=hi,YMin=0,YMax=1,ZMin=0,ZMax=1)

class Shape:
    def __init__(self,name,display,actual):
        self.name=name;self.BoundBox=display;self.actual=actual;self.Volume=1;self.Solids=[self]
    def isValid(self):return True
    def optimalBoundingBox(self,triangulation,tolerance):
        assert triangulation is False and tolerance is True
        return self.actual
    def common(self,other):
        collision={self.name,other.name}=={'BatteryCell','BatteryCradle'}
        return SimpleNamespace(Volume=.1 if collision else 0)

class ClosedBoundsTests(unittest.TestCase):
    def test_display_bounds_cannot_hide_closed_component_collision(self):
        shapes={name:Shape(name,box(100+10*i,101+10*i),box(100+10*i,101+10*i))
                for i,name in enumerate(sorted(subject.PART_NAMES))}
        shapes['BatteryCell']=Shape('BatteryCell',box(0,1),box(0,1))
        shapes['BatteryCradle']=Shape('BatteryCradle',box(2,3),box(.9,1.9))
        shapes['rear_interface']=Shape('rear_interface',box(10000,10001),box(10000,10001))
        # Stop if the closed gate misses the known overlap. Motion/physical
        #behavior is outside this intentionally synthetic negative test.
        with patch.dict(sys.modules,{'FreeCAD':SimpleNamespace(),'Part':SimpleNamespace()}), \
             patch.object(subject,'_released_door',side_effect=RuntimeError('Closed collision was missed')):
            with self.assertRaisesRegex(ValueError,'Battery closed-position interference: BatteryCell/BatteryCradle'):
                subject.native_check({},'narrow',shapes)

if __name__=='__main__':unittest.main()
