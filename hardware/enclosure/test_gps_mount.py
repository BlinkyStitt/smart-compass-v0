"""Reject a substituted mechanical source or a different GPS electrical layout."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import gps_mount


class GpsMountTests(unittest.TestCase):
    def test_mounts_use_outline_holes_not_internal_antenna_hole(self):
        data=gps_mount.geometry()
        self.assertEqual([row['drill'] for row in data['mounts']],[2.54,2.54,2.5,2.5])
        self.assertNotIn([37.123,11.93],[row['xy'] for row in data['mounts']])
        self.assertEqual(len(gps_mount.PRODUCT_NAMES),9)
        self.assertEqual(gps_mount.envelope(9),{'size':[22.86,50.8,8],'z':9})
        self.assertEqual(gps_mount.envelope(6),{'size':[50.8,22.86,8],'z':6})

    def test_wrong_mechanical_data_and_pcb_bindings_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp)
            for name in ('gps-featherwing','gps-featherwing-mechanical'):
                shutil.copytree(gps_mount.HERE/'sources'/name,directory/'sources'/name)
            part=gps_mount.definition();part['terminal_bindings']['RX']='JP3.2'
            with self.assertRaisesRegex(ValueError,'complete source pad map'):gps_mount.geometry(part,directory)
            index=directory/gps_mount.SOURCE/'index.json'
            rows=json.loads(index.read_text());rows[0]['repository_revision']='unreviewed'
            index.write_text(json.dumps(rows))
            with self.assertRaisesRegex(ValueError,'mechanical source hash/revision'):gps_mount.geometry(directory=directory)
            shutil.copyfile(gps_mount.HERE/gps_mount.SOURCE/'index.json',index)
            with (directory/gps_mount.SOURCE/'3133.step').open('ab') as output:output.write(b'changed')
            with self.assertRaisesRegex(ValueError,'mechanical source hash/revision'):gps_mount.geometry(directory=directory)

    def test_unreviewed_height_and_rotation_fail(self):
        for height,rotation in ((6,90),(9,180),(7,90)):
            with self.assertRaisesRegex(ValueError,'post height'):gps_mount.envelope(height,rotation)


if __name__=='__main__':unittest.main()
