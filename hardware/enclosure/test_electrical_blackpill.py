"""Reject wrong header rows, alternate power pads and modified source facts."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

import electrical_blackpill
from electrical_design import assess

HERE=Path(__file__).resolve().parent


class BlackPillTerminalTests(unittest.TestCase):
    def setUp(self):self.design=json.loads((HERE/'electrical-design.json').read_text())

    def test_manufacturer_p1_p2_rows_and_pa4_flash_conflict(self):
        pins=electrical_blackpill.terminals(self.design['parts']['BLACKPILL'])
        self.assertEqual(pins['3V3']['pad'],'P1.3')
        self.assertEqual(pins['GND']['pad'],'P1.2')
        self.assertEqual(pins['PA4']['pad'],'P1.11')
        self.assertEqual(pins['PA4']['board_xy_mm'],[26.797,18.009])
        self.assertEqual(pins['PB13']['board_xy_mm'],[3.937,2.794])
        self.assertEqual(pins['PA10']['pad'],'P2.7')
        self.assertEqual(pins['PB6']['pad'],'P2.14')
        # The later carrier footprint uses 15.24mm row spacing. The original
        # module STEP has 15.215mm: do not substitute the carrier geometry.
        self.assertAlmostEqual(pins['PA4']['board_xy_mm'][1]-pins['PB13']['board_xy_mm'][1],15.215)
        self.assertEqual({name for name in pins},{p.split('.',1)[1] for members in self.design['nets'].values() for p in members if p.startswith('BLACKPILL.')})

    def test_power_uart_and_adc_pad_changes_fail(self):
        for name,pad in [('3V3','P2.20'),('GND','P1.3'),('PA4','P2.1'),('PA10','P1.7')]:
            design=copy.deepcopy(self.design);design['parts']['BLACKPILL']['terminal_bindings'][name]=pad
            with self.subTest(name=name):
                self.assertIn('blackpill-terminal-binding',{row['id'] for row in assess(design)['failures']})

    def test_modified_coordinates_or_upstream_revision_fail(self):
        part=self.design['parts']['BLACKPILL']
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);target=root/electrical_blackpill.SOURCE
            shutil.copytree(HERE/electrical_blackpill.SOURCE,target)
            electrical_blackpill.terminals(part,root)
            path=target/'ports.json';data=json.loads(path.read_text());data['headers']['P1']['y_mm']=18.034
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'coordinate facts'):electrical_blackpill.terminals(part,root)
            shutil.copyfile(HERE/electrical_blackpill.SOURCE/'ports.json',path)
            path=target/'index.json';data=json.loads(path.read_text());data['sources']['mechanical']['url']='https://example.invalid/unreviewed.step'
            path.write_text(json.dumps(data))
            with self.assertRaisesRegex(ValueError,'source identities'):electrical_blackpill.terminals(part,root)
        part=copy.deepcopy(part);part['board_revision']='unreviewed'
        with self.assertRaisesRegex(ValueError,'original V3.1'):electrical_blackpill.terminals(part)


if __name__=='__main__':unittest.main()
