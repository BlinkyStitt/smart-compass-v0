"""Check placement inputs and the complete selected rear-control census."""
import math
import unittest

from control_fixture import placement, PRINTED_PARTS, HARDWARE_PARTS, PRODUCT_NAMES


class ControlFixtureTests(unittest.TestCase):
    def test_three_separate_buttons_preserve_their_mount_hardware(self):
        self.assertEqual(len(PRODUCT_NAMES),43)
        self.assertEqual(len(PRINTED_PARTS),13)
        self.assertEqual(len(HARDWARE_PARTS),24)
        for prefix in ('Start','Mode','Action'):
            self.assertIn(prefix+'Switch',PRODUCT_NAMES)
            for i in range(2):
                for kind in ('Screw','Nut','Washer'):
                    self.assertIn(prefix+'Mount'+kind+str(i),HARDWARE_PARTS)
                self.assertIn(prefix+'Compression'+str(i),PRINTED_PARTS)

    def test_all_four_control_locations_are_explicit(self):
        result=placement((79,-18),(-5,7.5),(-51,-8),(5,-16))
        self.assertEqual(result['mode_xy'],(-51,-8))
        self.assertEqual(result['action_xy'],(5,-16))
        self.assertAlmostEqual(result['start_tip_z_mm'][0],-3.45)
        self.assertAlmostEqual(result['start_tip_z_mm'][1],-3.25)

    def test_no_control_can_have_nonfinite_location_or_wrong_clamp_land(self):
        for i in range(4):
            for value in (True,float('inf'),float('nan')):
                points=[(79,-18),(-5,7.5),(-51,-8),(5,-16)]
                points[i]=(value,0)
                with self.subTest(index=i,value=value),self.assertRaises(ValueError):placement(*points)
        for rear in (1,.8,True,float('nan')):
            with self.assertRaises(ValueError):placement((79,-18),(-5,7.5),(-51,-8),(5,-16),rear)


if __name__=='__main__':unittest.main()
