import math
import unittest
from fastener_access import entry_dimensions,_hull
from hardware_spec import nut_dimensions,hexagon
class FastenerAccessTests(unittest.TestCase):
 def test_entry_clears_nut_corners_and_leaves_room_to_lower_the_nut(self):
  flats,_=nut_dimensions('M2')
  for length,minimum in ((8,3.1),(9,3.9),(12,6.85),(18,12.85)):
   data=entry_dimensions(length=length)
   self.assertGreater(data['width'],2*flats/math.sqrt(3))
   self.assertGreater(data['travel']-flats/math.sqrt(3),minimum)
 def test_convex_sweep_encloses_both_end_positions(self):
  points=hexagon(0,0,4);hull=_hull(points+[(x+5,y) for x,y in points])
  self.assertEqual(len(hull),8)
  self.assertAlmostEqual(max(x for x,y in hull)-min(x for x,y in hull),9)
  self.assertAlmostEqual(max(y for x,y in hull)-min(y for x,y in hull),8/math.sqrt(3))
 def test_unreviewed_entry_lengths_fail(self):
  for size,length in (('M3',8),('M2',4),('M2',True)):
   with self.subTest(size=size,length=length),self.assertRaises(ValueError):entry_dimensions(size,length)
if __name__=='__main__':unittest.main()
