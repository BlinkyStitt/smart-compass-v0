"""Reject wrong power terminals and changed manufacturer board sources."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from electrical_boost import terminals, terminal_blocks, BINDINGS, REVISION, FILES, SOURCE, TERMINAL_FILES, TERMINAL_SOURCE

HERE=Path(__file__).resolve().parent

class BoostTerminalTests(unittest.TestCase):
    def setUp(self):
        self.part=json.loads((HERE/'electrical-design.json').read_text())['parts']['BOOST']

    def test_ground_is_pin_one_on_both_blocks(self):
        pads=terminals(self.part)
        self.assertEqual(pads['BAT']['pad'],'X2.2')
        self.assertEqual(pads['INPUT_GND']['pad'],'X2.1')
        self.assertEqual(pads['OUT']['pad'],'X1.2')
        self.assertEqual(pads['OUTPUT_GND']['pad'],'X1.1')
        for name in ('BAT','INPUT_GND','OUT','OUTPUT_GND'):
            self.assertEqual(pads[name]['drill_mm'],1)
        self.assertAlmostEqual(pads['OUT']['board_xy_mm'][0],27.051)
        self.assertAlmostEqual(pads['BAT']['board_xy_mm'][1],13.13)
        self.assertEqual(pads['TRIP']['board_xy_mm'],[6.699,4.624])
        self.assertIsNone(pads['TRIP']['drill_mm'])
        self.assertEqual(pads['OUT']['board_net'],'5.0V')

    def test_input_and_output_swaps_and_wrong_collector_fail(self):
        for name,pad in [('BAT','X2.1'),('OUT','X1.1'),('TRIP','R20.1'),('BAT','JP1.1')]:
            part=copy.deepcopy(self.part);part['terminal_bindings'][name]=pad
            with self.subTest(name=name),self.assertRaises(ValueError):terminals(part)

    def test_missing_wire_endpoint_and_unreviewed_revision_fail(self):
        part=copy.deepcopy(self.part);del part['terminal_bindings']['OUTPUT_GND']
        with self.assertRaises(ValueError):terminals(part)
        part=copy.deepcopy(self.part);part['board_revision']='new revision'
        with self.assertRaises(ValueError):terminals(part)

    def test_selected_clamps_gauges_and_insulation_process_remain_bound(self):
        self.assertEqual(terminal_blocks(self.part)['quantity'],2)
        for key,value in [('positions',['X1']),('wire_awg_range',[26,20]),
                          ('quantity',2.0),
                          ('published_current_a',6),('wires_per_clamp',2),
                          ('wires_per_clamp',True),('strip_target_mm',3),('retention','')]:
            part=copy.deepcopy(self.part);part['wire_terminals'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):terminal_blocks(part)

    def test_changed_terminal_drawing_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);target=root/TERMINAL_SOURCE;target.mkdir(parents=True)
            for name in (*TERMINAL_FILES,'index.json'):(target/name).write_bytes((HERE/TERMINAL_SOURCE/name).read_bytes())
            self.assertEqual(terminal_blocks(self.part,root)['positions'],['X1','X2'])
            (target/'2444-dimension.jpg').write_bytes(b'changed drawing')
            with self.assertRaisesRegex(ValueError,'hash mismatch'):terminal_blocks(self.part,root)

    def test_changed_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);target=root/SOURCE;target.mkdir(parents=True)
            for name in (*FILES,'index.json'):(target/name).write_bytes((HERE/SOURCE/name).read_bytes())
            self.assertEqual(set(terminals(self.part,root)),set(BINDINGS))
            board=target/'Adafruit PowerBoost 1000 Basic.brd'
            board.write_bytes(board.read_bytes().replace(b'X2',b'X9'))
            with self.assertRaisesRegex(ValueError,'hash mismatch'):terminals(self.part,root)

if __name__=='__main__':unittest.main()
