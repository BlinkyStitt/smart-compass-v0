"""Selected discharge parts and joint stations must stay complete."""
import copy
import unittest
import blackpill_mount
import blackpill_drains


class DischargeLoomTests(unittest.TestCase):
    def test_all_six_selected_drains_have_two_fixed_ends(self):
        data=blackpill_drains.geometry()
        self.assertEqual(set(data['stations_source_xy_mm']),{'R_A','R_B','R_OUT','R_OFF','R_BOOST','R_LOAD'})
        self.assertEqual(len(blackpill_drains.PRODUCT_NAMES),19)
        self.assertEqual(len(blackpill_drains.REFERENCE_NAMES),6)
        self.assertTrue(blackpill_drains.PRODUCT_NAMES<=blackpill_mount.PRODUCT_NAMES)
        self.assertTrue(blackpill_drains.REFERENCE_NAMES<=blackpill_mount.REFERENCE_NAMES)
        self.assertEqual(data['axis_z_above_pcb_bottom_mm'],16)
        self.assertEqual(data['lacing_blank_mm'],[70]*12)
        ports=blackpill_drains.source_ports()
        self.assertEqual(len(ports),12)
        for name,(x,y) in blackpill_drains.STATIONS.items():
            self.assertEqual(ports[name+'.1'],[x,y,16])
            self.assertEqual(ports[name+'.2'],[x+12,y,16])

    def test_wrong_resistor_or_unsupported_source_limits_fail(self):
        for name in blackpill_drains.STATIONS:
            for key,value in [('part','A different part'),('body_max_mm',[3.5,1.5]),
                              ('lead_length_min_mm',None),('loaded_envelope_mm',[10,3,3]),
                              ('source_sha256','unknown')]:
                design=copy.deepcopy(blackpill_mount.definition());design['parts'][name][key]=value
                with self.subTest(part=name,key=key),self.assertRaisesRegex(ValueError,'MRS16 source facts'):
                    blackpill_drains.geometry(design)


if __name__=='__main__':unittest.main()
