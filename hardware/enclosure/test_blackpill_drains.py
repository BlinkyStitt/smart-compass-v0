"""Selected discharge parts and joint stations must stay complete."""
import copy
import unittest
from unittest.mock import patch
import blackpill_mount
import blackpill_drains


class DischargeLoomTests(unittest.TestCase):
    def test_opposed_exits_leave_room_for_both_jacket_cuffs(self):
        # Each axial solder lap retains a 2mm, 3mm-OD jacket cuff in
        # harness_finish.apply. Opposed exits must reserve both cuffs.
        ports=blackpill_drains.source_ports()
        for lower,upper in [('R_A','R_B'),('R_OUT','R_OFF'),('R_BOOST','R_LOAD')]:
            a,b=ports[lower+'.2'],ports[upper+'.1']
            with self.subTest(pair=(lower,upper)):
                self.assertEqual(a[1:],b[1:])
                self.assertGreater(b[0]-a[0],4)

    def test_old_opposed_spacing_is_rejected(self):
        for name in ['R_B','R_OFF','R_LOAD']:
            x,y=blackpill_drains.STATIONS[name]
            with self.subTest(part=name),patch.dict(blackpill_drains.STATIONS,{name:(29,y)}):
                with self.assertRaisesRegex(ValueError,'both2mm jacket cuffs'):
                    blackpill_drains.geometry()

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
