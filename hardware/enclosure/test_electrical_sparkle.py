"""Reject bypassed input protection and mismatched controller input/data pads."""
import copy
import json
from pathlib import Path
import unittest

from electrical_design import assess
from electrical_peripherals import terminals

HERE=Path(__file__).resolve().parent


class SparkleTerminalTests(unittest.TestCase):
    def setUp(self):self.design=json.loads((HERE/'electrical-design.json').read_text())

    def test_fixed_input_uses_pads_before_diode_and_ptc(self):
        pads=terminals('SPARKLE',self.design['parts']['SPARKLE'])
        self.assertEqual(pads['INPUT']['board_xy_mm'],[10.239,10.922])
        self.assertEqual(pads['INPUT_GND']['board_xy_mm'],[4.339,10.922])
        self.assertEqual(pads['INPUT']['drill_mm'],.9)
        self.assertEqual(pads['INPUT']['board_net'],'N$9')
        self.assertEqual(pads['LED_RAIL']['board_net'],'+24V')
        self.assertEqual(pads['DATA1']['pad'],'JP1.8')
        self.assertEqual(pads['DATA4']['pad'],'JP3.6')

    def test_terminal_bypass_or_uart_swap_fails(self):
        for key,pad in [('INPUT','JP1.9'),('INPUT_GND','X7.GNDBREAK'),('TX','JP3.4'),('DATA1','JP1.9')]:
            part=copy.deepcopy(self.design['parts']['SPARKLE']);part['terminal_bindings'][key]=pad
            with self.subTest(key=key),self.assertRaises(ValueError):terminals('SPARKLE',part)

    def test_missing_jack_rework_or_removed_protection_fails(self):
        for key,value in [('SPARKLE.remove',[]),('SPARKLE.remove',['X7','D2']),
                          ('SPARKLE.retain',['PTC1']),('SPARKLE.leave_open',[])]:
            design=copy.deepcopy(self.design);design['module_rework'][key]=value
            with self.subTest(key=key,value=value):
                self.assertIn('sparkle-input-termination',{row['id'] for row in assess(design)['failures']})


if __name__=='__main__':unittest.main()
