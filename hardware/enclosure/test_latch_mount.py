"""Check source identity, lower A pad and actual PCB clamp targets."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from electrical_latch import terminals,FILES,SOURCE
from latch_mount import definition,placement,PRODUCT_NAMES

HERE=Path(__file__).resolve().parent
class LatchMountTests(unittest.TestCase):
 def test_source_pinout_uses_lower_a_and_component_side_view(self):
  pads=terminals(definition())
  self.assertEqual(pads['A']['board_xy_mm'],[13.97,3.81])
  self.assertEqual(pads['OFF']['board_xy_mm'],[1.27,3.81])
  self.assertEqual(pads['VIN']['board_xy_mm'],[1.27,16.51])
  self.assertEqual(pads['VOUT']['board_xy_mm'],[13.97,16.51])
  self.assertEqual(pads['GND']['board_xy_mm'],[1.27,8.89])
 def test_mirrored_power_or_upper_b_instead_of_a_fail(self):
  for key,xy in [('VIN',[13.97,16.51]),('A',[13.97,6.35])]:
   part=definition();part['terminal_bindings'][key]=xy
   with self.subTest(key=key),self.assertRaises(ValueError):terminals(part)
 def test_changed_or_missing_primary_source_fails(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);target=root/SOURCE;target.mkdir(parents=True)
   for name in (*FILES,'index.json'):(target/name).write_bytes((HERE/SOURCE/name).read_bytes())
   self.assertEqual(set(terminals(definition(),root)),{'VIN','VOUT','GND','A','OFF'})
   (target/'pololu-2808.step').write_bytes(b'changed source model')
   with self.assertRaisesRegex(ValueError,'hash mismatch'):terminals(definition(),root)
 def test_alternate_clamp_and_two_wires_in_one_position_fail(self):
  for key,value in [('part','Pololu2493'),('quantity',1),('mount_side','component-side'),
                    ('wires_per_clamp',2),('published_ul_current_a',10),('nominal_body_mm',[10.62,6.2,5.1])]:
   part=definition();part['wire_terminals'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):terminals(part)
 def test_actual_board_edges_and_full_terminal_height_have_clearance(self):
  result=placement(definition())
  self.assertGreaterEqual(result['terminal_floor_clearance_mm'],.25)
  self.assertGreaterEqual(result['minimum_specified_lip_bearing_mm2'],.5)
  self.assertEqual(len(result['stations']),4)
  self.assertEqual(len(PRODUCT_NAMES),24)
 def test_low_board_thin_carrier_or_floating_clamp_are_rejected(self):
  for key,value in [('pcb_bottom_z_mm',11),('floor_thickness_mm',1),
                    ('finished_screw_length_mm',16),('finished_screw_length_mm',18),
                    ('post_radius_mm',2.4),('lip_inner_x_mm',7.3),('lip_inner_x_mm',6.6),
                    ('clamp_thickness_mm',1),('post_x_mm',float('nan'))]:
   part=definition();part['mount'][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):placement(part)
if __name__=='__main__':unittest.main()
