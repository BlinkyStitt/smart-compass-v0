"""Bare pads and source geometry remain mandatory for the selected carrier."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import blackpill_mount
import blackpill_sense


class BlackPillMountTests(unittest.TestCase):
    def test_selected_source_board_and_cage_inputs(self):
        data=blackpill_mount.geometry()
        self.assertEqual(len(data['bodies']),130)
        self.assertEqual(len(data['pins']),21)
        self.assertEqual(len(blackpill_mount.PRODUCT_NAMES),25)
        self.assertEqual(len(blackpill_mount.PRINTED_PARTS),6)
        self.assertEqual(data['retainer_slot_mm'],1.85)
        self.assertEqual([row[0] for row in data['stations_mm']],[9.5,31,43.3,43.3])
        self.assertEqual(data['nut_entry_axes'],[[1,0],[-1,0],[1,0],[1,0]])
        self.assertNotEqual(data['pcb_thickness_target_mm'],data['source_pcb_thickness_mm'])

    def test_installed_headers_or_flash_are_not_the_selected_variant(self):
        for omitted in (['U3'],['P1','P2','P3'],['U3','P1','P2']):
            design=copy.deepcopy(blackpill_mount.definition());design['module_rework']['BLACKPILL.do_not_install']=omitted
            with self.subTest(omitted=omitted),self.assertRaisesRegex(ValueError,'bare BlackPill'):blackpill_mount.geometry(design)

    def test_changed_functional_pcb_and_missing_component_bounds_fail(self):
        source=blackpill_mount.HERE/'sources/blackpill-v31'
        for filename,raw in [('pcb.brep',b'changed functional PCB'),('component-bounds.json',b'{"bodies": []}')]:
            with tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);target=root/'sources/blackpill-v31';shutil.copytree(source,target);(target/filename).write_bytes(raw)
                with self.subTest(filename=filename),self.assertRaisesRegex(ValueError,'coordinate facts'):blackpill_mount.geometry(directory=root)

    def test_sense_loom_keeps_source_lead_tolerances_and_stock_length(self):
        data=blackpill_sense.geometry()
        self.assertLess(data['cap_lead_stock_required_mm'],7)
        self.assertGreater(data['lacing_finished_space_mm'][0],data['lacing_stock_max_mm'][0])
        self.assertGreater(data['lacing_finished_space_mm'][1],data['lacing_stock_max_mm'][1])
        self.assertEqual(set(data['parts']),{'R_SENSE_TOP','R_SENSE_BOTTOM','C_SENSE'})
        self.assertTrue(blackpill_sense.CHECK_NAMES<=blackpill_mount.CHECK_NAMES)

    def test_missing_or_changed_passive_source_limits_fail(self):
        for part,key,value in (('C_SENSE','lead_diameter_mm',[.5,.5]),
                               ('C_SENSE','lead_length_min_mm',None),
                               ('C_SENSE','lead_pitch_mm',[2.54,2.54]),
                               ('R_SENSE_TOP','lead_diameter_nominal_mm',None),
                               ('R_SENSE_BOTTOM','body_max_mm',[3.5,1.5]),
                               ('R_SENSE_TOP','loaded_envelope_mm',[12,3,3])):
            design=copy.deepcopy(blackpill_mount.definition());design['parts'][part][key]=value
            with self.subTest(part=part,key=key),self.assertRaises(ValueError):blackpill_sense.geometry(design)

    def test_unreviewed_source_pose_fails(self):
        for z,rotation in ((6,0),(8,180),(9,90)):
            with self.assertRaisesRegex(ValueError,'PCB height'):blackpill_mount.envelope(z,rotation)


if __name__=='__main__':unittest.main()
