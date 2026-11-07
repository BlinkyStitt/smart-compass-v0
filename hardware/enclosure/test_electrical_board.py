"""Manufacturer connectivity, pad binding and USB feed-route regressions."""

import copy
import json
from pathlib import Path
import unittest

from electrical_board import board_study, extract, forward_path


class BoardTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        self.record = json.loads((root / 'sources/sparkle-motion/connectivity.json').read_text())
        self.harness = json.loads((root / 'electrical-harness.json').read_text())

    def calculate(self):
        return board_study(self.record, self.harness)

    def test_both_manufacturer_revisions_bind_barrel_feed_behind_d2(self):
        result = self.calculate()
        self.assertFalse(result['qualified'])
        self.assertEqual(set(result['boards']), {'A', 'D'})
        for row in result['boards'].values():
            self.assertEqual(row['barrel_to_board'], ['D2:forward', 'PTC1'])
            self.assertEqual(row['usb_to_led_power_terminals'], ['Q1:on', 'D1:forward', 'PTC1'])
            self.assertIsNone(row['usb_to_selected_barrel_feed'])
            self.assertTrue(row['shared_usb_and_load_ground'])
            self.assertTrue(row['usb_data_direct_to_ch343'])
            self.assertEqual(row['ports']['peripheral_supply']['net'], '3.3V')
            self.assertEqual(row['ports']['supply']['pads'], ['PWR'])
            self.assertEqual(row['buck_minimum_input_v'], 4.5)

    def test_feed_cannot_move_to_usb_fed_led_terminals(self):
        self.harness['sparkle_board_ports']['supply'] = ['JP1', 'A.3']
        with self.assertRaisesRegex(ValueError, 'barrel input'):
            self.calculate()

    def test_reverse_or_bypassed_diode_cannot_retain_old_path_claim(self):
        for edit in ('reverse', 'short'):
            with self.subTest(edit=edit):
                self.setUp()
                part = self.record['boards']['D']['parts']['D2']['nets']
                if edit == 'reverse':
                    part['G$1.A'], part['G$1.C'] = part['G$1.C'], part['G$1.A']
                else:
                    part['G$1.C'] = part['G$1.A']
                with self.assertRaisesRegex(ValueError, 'topology changed'):
                    self.calculate()

    def test_grounds_and_usb_data_are_not_assumed_isolated(self):
        for part, pin in [('X5', 'G$1.GND'), ('X5', 'G$1.D+'), ('JP3', 'G$1.2')]:
            with self.subTest(part=part, pin=pin):
                self.setUp()
                self.record['boards']['A']['parts'][part]['nets'][pin] = 'ISOLATED'
                with self.assertRaises(ValueError):
                    self.calculate()

    def test_substitution_and_unpinned_source_fail(self):
        self.record['boards']['A']['parts']['D2']['value'] = 'ideal diode'
        with self.assertRaisesRegex(ValueError, 'Unreviewed'):
            self.calculate()
        self.setUp()
        self.record['upstream_commit'] = 'main'
        with self.assertRaisesRegex(ValueError, 'revision'):
            self.calculate()

    def test_graph_direction_and_cycles_do_not_create_reverse_conduction(self):
        edges = [('a', 'usb', 'bus'), ('b', 'barrel', 'bus'),
                 ('c', 'bus', 'load'), ('c', 'load', 'bus')]
        self.assertIsNone(forward_path(edges, 'usb', 'barrel'))
        self.assertEqual(forward_path(edges, 'barrel', 'load'), ['b', 'c'])
        self.assertEqual(forward_path(edges + [('short', 'bus', 'barrel')], 'usb', 'barrel'),
                         ['a', 'short'])

    def test_extractor_resolves_gate_pins_to_physical_pads(self):
        # Small independent Eagle fixture: resistor-pack gate ownership must
        # survive extraction even when several gates reuse logical pin '1'.
        data = b'''<eagle><drawing><schematic><libraries><library name="lib">
        <devicesets><deviceset name="R"><devices><device name="" package="PACK">
        <connects><connect gate="A" pin="1" pad="1"/><connect gate="B" pin="1" pad="3 4"/>
        </connects></device></devices></deviceset></devicesets></library></libraries>
        <parts><part name="R1" library="lib" deviceset="R" device="" value="10K"/></parts>
        <sheets><sheet><nets><net name="one"><segment><pinref part="R1" gate="A" pin="1"/>
        </segment></net><net name="two"><segment><pinref part="R1" gate="B" pin="1"/>
        </segment></net></nets></sheet></sheets></schematic></drawing></eagle>'''
        result = extract(data)
        self.assertEqual(result['R1']['nets'], {'A.1': 'one', 'B.1': 'two'})
        self.assertEqual(result['R1']['pads']['B.1'], ['3', '4'])
        with self.assertRaisesRegex(ValueError, 'multiple nets'):
            extract(data.replace(b'gate="B" pin="1"/>\n        </segment>',
                                 b'gate="A" pin="1"/>\n        </segment>'))
        with self.assertRaisesRegex(ValueError, 'no pad'):
            extract(data.replace(b'<pinref part="R1" gate="B"', b'<pinref part="R1" gate="C"'))

    def test_study_does_not_mutate_source_record_or_harness(self):
        original = copy.deepcopy((self.record, self.harness))
        self.calculate()
        self.assertEqual((self.record, self.harness), original)


if __name__ == '__main__':
    unittest.main()
