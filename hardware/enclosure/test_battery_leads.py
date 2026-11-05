"""Check selected fixed contact leads and reject unsupported route changes."""
import copy
import json
import math
from pathlib import Path
import unittest

from battery_access import definition
from battery_leads import layout


class BatteryLeadTests(unittest.TestCase):
    def setUp(self):
        self.spec=definition()
        self.electrical=json.loads(Path(__file__).with_name('electrical-design.json').read_text())

    def test_cut_list_includes_both_joints_and_uses_raw_route_length(self):
        for design in ('wide','narrow'):
            data=layout(self.spec,design,self.electrical)
            expected=51-(73.9/2+10.0076)+math.pi*6+10.5
            self.assertAlmostEqual(data['routed_centreline_mm'],expected)
            self.assertAlmostEqual(data['finished_cut_target_mm'],expected+6)
            self.assertLess(data['finished_cut_target_mm'],42)
            self.assertEqual(data['final_offset_y_mm'],-22.5)
            self.assertAlmostEqual(data['wire_radius_mm'],1.8542/2)

    def test_thicker_stock_does_not_keep_old_clearance_or_bend(self):
        for od in (.9,2.1,3,True,float('nan')):
            electrical=copy.deepcopy(self.electrical)
            electrical['wiring']['stock_limits']['main']['maximum_od_mm']=od
            with self.subTest(od=od),self.assertRaises(ValueError):
                layout(self.spec,'wide',electrical)

    def test_short_blank_tight_bend_and_thin_insulation_fail(self):
        for key,value in [('blank_length_mm',35),('individual_bend_radius_mm',5),
                          ('conduit_outer_radius_mm',2.5),('bend_start_x_from_cell_mm',50),
                          ('conduit_start_x_from_cell_mm',51)]:
            spec=copy.deepcopy(self.spec);spec['contact_leads'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):layout(spec,'wide',self.electrical)

    def test_nonfinite_or_nonpositive_target_fails(self):
        for key in ('individual_bend_radius_mm','blank_length_mm','strip_each_end_mm'):
            for value in (0,-1,True,float('nan'),float('inf')):
                spec=copy.deepcopy(self.spec);spec['contact_leads'][key]=value
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):layout(spec,'narrow',self.electrical)

    def test_changed_fuse_or_wire_requires_geometry_review(self):
        for section,key,value in [('F1','loaded_envelope_mm',[20,6,5]),('F1','part','another fuse')]:
            electrical=copy.deepcopy(self.electrical);electrical['parts'][section][key]=value
            with self.assertRaises(ValueError):layout(self.spec,'wide',electrical)
        self.electrical['wiring']['stock_limits']['main']['stock']='another wire'
        with self.assertRaises(ValueError):layout(self.spec,'wide',self.electrical)

    def test_three_new_parts_are_required_in_the_compartment_census(self):
        from battery_access import PART_NAMES, WIRE_PARTS, PROTECTION_PARTS
        self.assertEqual(len(PART_NAMES),55)
        self.assertEqual(WIRE_PARTS,{'BatteryLeadP','BatteryLeadN'})
        self.assertEqual(PROTECTION_PARTS,{'BatteryMainFuse'})
        self.assertTrue(WIRE_PARTS|PROTECTION_PARTS <= PART_NAMES)


if __name__=='__main__':unittest.main()
