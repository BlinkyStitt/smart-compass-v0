import unittest
import tempfile
from pathlib import Path
from capacitor_mount import HERE,SOURCE,FILES
from capacitor_mount import definition,geometry,PRODUCT_NAMES,REFERENCE_NAMES
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
