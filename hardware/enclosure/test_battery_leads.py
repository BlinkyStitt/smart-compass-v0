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
            expected=56-(73.9/2+15.2146)+math.pi*6+(22.5/math.cos(math.radians(11.6))-12)+5
            self.assertAlmostEqual(data['routed_centreline_mm'],expected)
            self.assertAlmostEqual(data['finished_cut_target_mm'],expected+7)
            self.assertLess(data['finished_cut_target_mm'],50)
            self.assertAlmostEqual(data['final_offset_y_mm'],-22.5)
            self.assertAlmostEqual(data['final_offset_z_mm'],-22.5*math.tan(math.radians(11.6)))
            self.assertAlmostEqual(data['wire_radius_mm'],1.8542/2)
            self.assertGreaterEqual(data['fuse_exit_radius_mm']-1.5,
                                    self.spec['removal']['noncontact_clearance_mm'])
            self.assertGreaterEqual(data['fuse_exit_wall_mm'],1.35)

    def test_thicker_stock_does_not_keep_old_clearance_or_bend(self):
        for od in (.9,2.1,3,True,float('nan')):
            electrical=copy.deepcopy(self.electrical)
            electrical['wiring']['stock_limits']['main']['maximum_od_mm']=od
            with self.subTest(od=od),self.assertRaises(ValueError):
                layout(self.spec,'wide',electrical)

    def test_short_blank_tight_bend_and_thin_insulation_fail(self):
        for key,value in [('blank_length_mm',35),('individual_bend_radius_mm',5),
                          ('conduit_outer_radius_mm',2.5),('bend_start_x_from_cell_mm',50),
                          ('conduit_start_x_from_cell_mm',51),('conduit_start_x_from_cell_mm',45),
                          ('conduit_inner_radius_mm',1.5),('cup_collar_inner_radius_mm',1.5),
                          ('cup_collar_end_x_from_cell_mm',53),('cup_collar_outer_radius_mm',2.8)]:
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
        for key in ('CONTACT_P','CONTACT_N'):
            electrical=copy.deepcopy(self.electrical)
            electrical['parts'][key]['part']='Mill-Max 0850-0-15-20-83-14-11-0'
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'same wire-mount part'):
                layout(self.spec,'wide',electrical)
        self.electrical['wiring']['stock_limits']['main']['stock']='another wire'
        with self.assertRaises(ValueError):layout(self.spec,'wide',self.electrical)

    def test_descent_must_keep_the_rear_bearing_brace(self):
        for value in (True,float('nan'),-1,45,20):
            spec=copy.deepcopy(self.spec);spec['contact_leads']['route_descent_deg']=value
            with self.subTest(value=value),self.assertRaises(ValueError):layout(spec,'narrow',self.electrical)

    def test_contact_leads_fuse_and_both_ties_are_required_in_the_compartment_census(self):
        from battery_access import PART_NAMES, WIRE_PARTS, PROTECTION_PARTS
        self.assertEqual(len(PART_NAMES),57)
        self.assertEqual(WIRE_PARTS,{'BatteryLeadP','BatteryLeadN'})
        self.assertEqual(PROTECTION_PARTS,{'BatteryMainFuse','BatteryMainFuseLacing0','BatteryMainFuseLacing1'})
        self.assertTrue(WIRE_PARTS|PROTECTION_PARTS <= PART_NAMES)

    def test_missing_loop_or_changed_stock_space_fails(self):
        for key,value in [('quantity',1),('quantity',True),('part','Another tape'),
                          ('finished_loop_section_mm',[1.5,.4]),('knot_side','positiveY'),
                          ('source','Another source'),('knot_x_offsets_mm',[0,2]),
                          ('knot_x_offsets_mm',[0,True])]:
            spec=copy.deepcopy(self.spec);spec['contact_leads']['main_fuse_lacing'][key]=value
            with self.subTest(key=key,value=value),self.assertRaisesRegex(ValueError,'both selected main-fuse'):
                layout(spec,'wide',self.electrical)


    def test_ties_cannot_bear_on_the_body_or_leave_the_end_gauges(self):
        for stations in ([-3,8],[-8,10],[-8,-6],[-8,True],[8],[-8,float('nan')]):
            spec=copy.deepcopy(self.spec);spec['contact_leads']['main_fuse_lacing']['stations_from_fuse_centre_mm']=stations
            with self.subTest(stations=stations),self.assertRaisesRegex(ValueError,'insulated lead regions'):
                layout(spec,'narrow',self.electrical)



if __name__=='__main__':unittest.main()
