import unittest
import tempfile
from pathlib import Path
from capacitor_mount import HERE,SOURCE,FILES
from capacitor_mount import definition,geometry,mounting,PRODUCT_NAMES,REFERENCE_NAMES
class CapacitorMountTests(unittest.TestCase):
 def test_published_corners_and_vent_requirement_stay_visible(self):
  part=definition();data=geometry()
  self.assertEqual(part['body_diameter_mm'],[9.5,10.5])
  self.assertEqual(part['body_length_mm'],[14.5,17.5])
  self.assertEqual(part['lead_diameter_mm'],[.55,.65])
  self.assertEqual(part['lead_pitch_mm'],[4.5,5.5])
  self.assertGreaterEqual(data['vent_target_mm']-data['maximum_accepted_axial_motion_mm'],part['minimum_vent_clearance_mm'])
  self.assertGreaterEqual(data['lead_channel_radius_mm']-(.65/2+.5/2),.2)
  self.assertEqual(len(PRODUCT_NAMES),8);self.assertEqual(len(REFERENCE_NAMES),3)
 def test_compact_stations_clear_leads_and_keep_the_vent_open(self):
  data=mounting('narrow')
  self.assertEqual(data['post_xy_mm'],[[.5,-9.5],[4.25,19]])
  self.assertEqual(data['floor_width_mm'],7)
  # The nearest screw shaft stays outside the full lead-corner envelope.
  self.assertGreater(2.5-.5-1.1-(.65/2+.5/2),.3)
  self.assertGreater(19-data['post_radius_mm'],12.5+data['vent_target_mm'])
  self.assertEqual(mounting('wide')['post_xy_mm'],[[-10,8.5],[10,8.5]])
  self.assertGreaterEqual(data['cover_ear_thickness_mm']-data['lead_channel_radius_mm'],1.35)
  self.assertEqual(data['finished_screw_length_mm'],7.6)
  self.assertEqual(data['entry_lengths_mm'],[12,9])
  from hardware_spec import nut_dimensions
  import math
  flats,_=nut_dimensions('M2',pocket=True)
  self.assertGreaterEqual(data['post_flat_width_mm']/2-flats/2,1.35)
  self.assertGreaterEqual(data['post_radius_mm']-flats/math.sqrt(3),1.35)
  with self.assertRaises(ValueError):mounting('unreviewed design')
 def test_narrow_lead_turn_fits_stock_and_clears_retained_screw(self):
  import math,harness_ports,harness_route
  data=mounting('narrow');z=data['axis_z_mm'];turn=data['formed_lead_turn_y_mm'];end=data['formed_lead_exit_z_mm']
  length=math.fsum(row['length_mm'] for row in harness_route.segments([[-2.5,-5,z],[-2.5,turn,z],[-2.5,turn,end]],data['formed_lead_radius_target_mm']))
  self.assertAlmostEqual(data['finished_lead_mm'],11.942477796076938)
  self.assertAlmostEqual(data['finished_lead_mm'],length)
  self.assertEqual(mounting('wide')['finished_lead_mm'],9.5)
  self.assertNotIn('finished_lead_mm',geometry())
  self.assertLessEqual(length,data['source_minimum_lead_mm'])
  self.assertGreater(end-3.5-(z+data['formed_lead_radius_target_mm']),.4)
  x,y=data['post_xy_mm'][0]
  self.assertGreater(math.hypot(2.5-x,turn-y)-1.9-1.5,.25)
  ports=harness_ports.terminals()
  for pin in ['C_OUT.P','C_OUT.N']:
   self.assertEqual(ports[pin]['axis'],[0,0,1])
   self.assertEqual(ports[pin]['wire_end_mm'][2],end)
 def test_changed_primary_source_is_rejected(self):
  with tempfile.TemporaryDirectory() as temporary:
   root=Path(temporary);target=root/SOURCE;target.mkdir(parents=True)
   for name in (*FILES,'index.json'):(target/name).write_bytes((HERE/SOURCE/name).read_bytes())
   geometry(definition(),root)
   p=target/'panasonic-safety-2025.pdf';p.write_bytes(p.read_bytes()+b'changed')
   with self.assertRaisesRegex(ValueError,'hash mismatch'):geometry(definition(),root)
 def test_incorrect_parts_typical_dimensions_and_blocked_vent_fail(self):
  for key,value in [('part','different capacitor'),('body_diameter_mm',[10,10]),('minimum_vent_clearance_mm',0),('lead_pitch_mm',[5,5])]:
   part=definition();part[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):geometry(part)
if __name__=='__main__':unittest.main()
