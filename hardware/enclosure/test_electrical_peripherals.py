import copy
import json
from pathlib import Path
import tempfile
import unittest
from electrical_peripherals import HERE,BOARDS,terminals
class PeripheralTerminalTests(unittest.TestCase):
 def setUp(self):self.parts=json.loads((HERE/'electrical-design.json').read_text())['parts']
 def test_gps_power_uart_and_enable_use_the_source_headers(self):
  pads=terminals('GPS',self.parts['GPS'])
  expected={'3V':('JP4.9',[8.255,3.81]),'GND':('JP4.7',[13.335,3.81]),
            'RX':('JP3.1',[49.657,6.985]),'TX':('JP3.2',[47.117,6.985]),
            'PPS':('JP1.3',[28.448,11.43]),'EN':('JP1.4',[28.448,8.89])}
  self.assertEqual(set(pads),set(expected))
  for name,(pad,xy) in expected.items():
   self.assertEqual(pads[name]['pad'],pad)
   for a,b in zip(pads[name]['board_xy_mm'],xy):self.assertAlmostEqual(a,b)
   self.assertEqual(pads[name]['drill_mm'],1)
 def test_radio_normalizes_the_actual_outline_origin(self):
  pads=terminals('RADIO',self.parts['RADIO'])
  self.assertEqual(pads['G0']['pad'],'JP3.4')
  self.assertEqual(pads['G0']['board_net'],'DIO0')
  self.assertAlmostEqual(pads['VIN']['cad_xy_mm'][0],2.54)
  self.assertAlmostEqual(pads['VIN']['board_xy_mm'][0],2.286)
  self.assertEqual(pads['ANT']['board_xy_mm'],[21.336,24.511])
  self.assertEqual(pads['MISO']['board_net'],'MISO_3V')
  self.assertEqual(pads['SCK']['board_net'],'SCK_5V')
 def test_crossed_power_uart_dio_and_antenna_pads_fail(self):
  for module,name,pad in [('GPS','3V','JP4.7'),('GPS','TX','JP3.1'),('GPS','EN','JP1.3'),
                          ('RADIO','VIN','JP3.2'),('RADIO','G0','JP1.1'),('RADIO','ANT','X1.P')]:
   part=copy.deepcopy(self.parts[module]);part['terminal_bindings'][name]=pad
   with self.subTest(module=module,name=name),self.assertRaises(ValueError):terminals(module,part)
 def test_changed_source_and_unreviewed_revision_fail(self):
  for module in ('GPS','RADIO'):
   part=copy.deepcopy(self.parts[module]);part['board_revision']='unreviewed'
   with self.subTest(module=module),self.assertRaises(ValueError):terminals(module,part)
   part=copy.deepcopy(self.parts[module]);part['part']='unreviewed replacement'
   with self.subTest(module=module),self.assertRaises(ValueError):terminals(module,part)
   selected=BOARDS[module]
   with tempfile.TemporaryDirectory() as temporary:
    root=Path(temporary);target=root/selected['source'];target.mkdir(parents=True)
    for name in (*selected['files'],'index.json'):(target/name).write_bytes((HERE/selected['source']/name).read_bytes())
    terminals(module,self.parts[module],root)
    filename=next(n for n in selected['files'] if n.endswith('.brd'))
    (target/filename).write_bytes(b'changed source')
    with self.assertRaisesRegex(ValueError,'hash mismatch'):terminals(module,self.parts[module],root)
if __name__=='__main__':unittest.main()
