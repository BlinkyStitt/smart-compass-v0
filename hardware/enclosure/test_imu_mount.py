"""Verify the source mounting holes and retain the larger loaded reservation."""
import unittest
from imu_mount import definition,geometry,PRODUCT_NAMES,REFERENCE_NAMES

class ImuMountTests(unittest.TestCase):
    def test_source_has_four_real_holes_and_all_header_drills(self):
        data=geometry()
        self.assertEqual(data['mount_xy_mm'],[[2.54,2.54],[30.48,2.54],[30.48,17.78],[2.54,17.78]])
        self.assertEqual(data['mount_drill_mm'],2.5)
        self.assertAlmostEqual(data['keepout_radius_mm'],2.016)
        self.assertGreater(len(data['through_pads']),14)
        self.assertEqual(len(PRODUCT_NAMES),9)
        self.assertEqual(REFERENCE_NAMES,{'IMUComponents'})
    def test_reducing_reservation_or_changing_source_map_is_rejected(self):
        part=definition();part['loaded_envelope_mm']=[33.02,20.32,3]
        with self.assertRaisesRegex(ValueError,'full IMU loaded'):geometry(part)
        part=definition();part['terminal_bindings']['DRDY']='JP2.5'
        with self.assertRaises(ValueError):geometry(part)
if __name__=='__main__':unittest.main()
