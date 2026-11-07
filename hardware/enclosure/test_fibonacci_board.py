"""Keep the original board, DI direction and evidence boundary in the circuit."""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from electrical_design import assess
from fibonacci_board import FILES, SOURCE, terminals

HERE = Path(__file__).resolve().parent


class FibonacciTerminalTests(unittest.TestCase):
    def setUp(self):
        self.design = json.loads((HERE / 'electrical-design.json').read_text())
        self.part = self.design['parts']['FIBONACCI']

    def test_rear_labels_are_mirrored_in_the_front_routing_frame(self):
        pads = terminals(self.part)
        self.assertEqual(set(pads), {'5V', 'DIN', 'GND'})
        self.assertEqual(pads['DIN']['pad'], 'IN.DI')
        self.assertEqual(pads['DIN']['board_xy_mm'], [0, -81.9])
        self.assertLess(pads['5V']['board_xy_mm'][0], 0)
        self.assertGreater(pads['GND']['board_xy_mm'][0], 0)
        for pad in pads.values():
            self.assertLess(pad['board_xy_mm'][1], -80)
            self.assertEqual(pad['coordinate_kind'], 'photo-estimated nominal')
            self.assertEqual(pad['physical_acceptance'], 'unmeasured')

    def test_do_wrong_board_and_crossed_power_pads_fail_the_circuit(self):
        for name, pad in [('DIN', 'OUT.DO'), ('5V', 'IN.GND'), ('GND', 'IN.5V')]:
            design = copy.deepcopy(self.design)
            design['parts']['FIBONACCI']['terminal_bindings'][name] = pad
            with self.subTest(name=name):
                self.assertIn('fibonacci-terminal-binding',
                              {row['id'] for row in assess(design)['failures']})
        for key, value in [('board_revision', '75mm'),
                           ('part', 'Fibonacci256 HDR Pixelblaze'),
                           ('source_record', 'unreviewed/index.json')]:
            part = copy.deepcopy(self.part)
            part[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                terminals(part)

    def test_missing_input_cannot_silently_remove_a_wire(self):
        del self.part['terminal_bindings']['GND']
        with self.assertRaises(ValueError):
            terminals(self.part)

    def test_photo_map_and_index_bytes_are_required(self):
        for changed in FILES:
            with self.subTest(changed=changed), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                folder = root / SOURCE
                folder.mkdir(parents=True)
                for name in FILES:
                    (folder / name).write_bytes((HERE / SOURCE / name).read_bytes())
                path = folder / changed
                path.write_bytes(path.read_bytes() + b'changed')
                with self.assertRaisesRegex(ValueError, 'source hash mismatch'):
                    terminals(self.part, root)
                path.unlink()
                with self.assertRaises(FileNotFoundError):
                    terminals(self.part, root)

    def test_pad_evidence_does_not_claim_a_fitted_harness(self):
        actual=Path.read_text
        def read(path,*args,**kwargs):
            if path==HERE/'harness-routing.json':raise FileNotFoundError('Required selected route record missing')
            return actual(path,*args,**kwargs)
        with patch.object(Path,'read_text',read):report=assess(self.design)
        self.assertEqual({row['id'] for row in report['failures']}, {'fitted-harness'})
        self.assertEqual(report['fibonacci_source_terminals'], terminals(self.part))
        self.assertEqual(report['physical_acceptance'], 'unmeasured')
        self.assertFalse(report['safe_to_wear_claim'])


if __name__ == '__main__':
    unittest.main()
