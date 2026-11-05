"""Reject board-revision and pad errors before installed wire routing."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from electrical_design import assess
from electrical_imu import FILES, SOURCE, terminals

HERE = Path(__file__).resolve().parent


class ImuTerminalTests(unittest.TestCase):
    def setUp(self):
        self.design = json.loads((HERE / 'electrical-design.json').read_text())
        self.part = self.design['parts']['IMU']

    def test_actual_rev_a_endpoints_and_reverse_header_direction(self):
        pads = terminals(self.part)
        self.assertEqual(pads['VIN']['pad'], 'JP4.9')
        self.assertEqual(pads['VIN']['board_net'], 'VIN')
        self.assertAlmostEqual(pads['VIN']['board_xy_mm'][0], 6.35)
        self.assertAlmostEqual(pads['VIN']['board_xy_mm'][1], 2.54)
        self.assertEqual(pads['VIN']['drill_mm'], 1.0)
        self.assertEqual(pads['SDOM']['board_xy_mm'], [26.67, 2.54])
        self.assertEqual(pads['DRDY']['pad'], 'JP2.4')
        self.assertEqual(pads['DRDY']['board_xy_mm'], [19.05, 17.78])
        self.assertEqual(set(pads), set(self.part['terminal_bindings']))

    def test_rev_c_and_its_different_ready_pad_fail(self):
        for key, value in [('board_revision', 'C'), ('source_record', 'sources/rev-c/index.json')]:
            part = copy.deepcopy(self.part)
            part[key] = value
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, 'Rev A'):
                terminals(part)
        self.part['terminal_bindings']['DRDY'] = 'JP2.5'
        self.assertIn('imu-terminal-binding', {row['id'] for row in assess(self.design)['failures']})

    def test_regulator_output_and_crossed_chip_selects_fail(self):
        for name, pad in [('VIN', 'JP4.8'), ('CSAG', 'JP4.3'), ('SDOAG', 'JP4.1'), ('GND', 'JP4.9')]:
            part = copy.deepcopy(self.part)
            part['terminal_bindings'][name] = pad
            with self.subTest(name=name), self.assertRaises(ValueError):
                terminals(part)

    def test_missing_binding_cannot_silently_omit_wire(self):
        del self.part['terminal_bindings']['INT1']
        with self.assertRaises(ValueError):
            terminals(self.part)

    def test_changed_primary_source_fails(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / SOURCE).mkdir(parents=True)
            for filename in FILES:
                (root / SOURCE / filename).write_bytes((HERE / SOURCE / filename).read_bytes())
            (root / SOURCE / 'index.json').write_bytes((HERE / SOURCE / 'index.json').read_bytes())
            board = root / SOURCE / 'Adafruit LSM9DS1 Rev A.brd'
            board.write_bytes(board.read_bytes().replace(b'JP4', b'JP9'))
            with self.assertRaisesRegex(ValueError, 'source hash mismatch'):
                terminals(self.part, root)


if __name__ == '__main__':
    unittest.main()
