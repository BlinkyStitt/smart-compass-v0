"""Source geometry and selected unpopulated connector variant are mandatory."""
import copy
import unittest
import electrical_design
import radio_mount


class RadioMountTests(unittest.TestCase):
    def test_complete_source_pad_and_footprint_census(self):
        data=radio_mount.geometry()
        self.assertEqual(len(data['through_pads']),15)
        self.assertEqual(len(data['terminals']),9)
        self.assertEqual({row['element'] for row in data['footprint_bounds']},radio_mount.PHYSICAL_ELEMENTS)
        self.assertEqual(len(radio_mount.PRODUCT_NAMES),11)
        self.assertEqual(data['terminals']['ANT']['board_xy_mm'],[21.336,24.511])
        self.assertEqual(data['edge_overlap_mm'],.6)
        self.assertEqual(data['nut_entry_axes'],[[1,0],[1,0],[-1,0]])
        for body in data['footprint_bounds']:
            self.assertGreater(body['min_mm'][1],.6)
            self.assertLess(body['max_mm'][1],radio_mount.W-.6)

    def test_headers_external_antenna_and_unused_wires_fail(self):
        for key,value in [('RADIO.do_not_install',['JP1','JP2','JP3']),('RADIO.leave_open',['JP3.3'])]:
            design=copy.deepcopy(radio_mount.definition());design['module_rework'][key]=value
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'bare radio pads'):radio_mount.geometry(design)
            failures=electrical_design.assess(design)['failures']
            self.assertTrue(any(row['id']=='radio-bare-pads' for row in failures))

    def test_unreviewed_pose_and_height_fail(self):
        for z,rotation in ((6,0),(8,180),(9,0)):
            with self.assertRaisesRegex(ValueError,'PCB height'):radio_mount.envelope(z,rotation)
        self.assertEqual(radio_mount.envelope(8,0),{'size':[25.4,29.21,10.1],'z':5.9})


if __name__=='__main__':unittest.main()
