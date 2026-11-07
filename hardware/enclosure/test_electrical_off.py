"""Physical service-OFF pole, including its return conductor and unknown states."""

import copy
import json
from pathlib import Path
import unittest

from electrical import (boost_interlock_study, interlock_netlist, physical_off_state,
                        reset_netlist, reset_storage_study)
from electrical_headroom import headroom_netlist
from electrical_thermal import heat_ownership


class PhysicalOffTests(unittest.TestCase):
    def setUp(self):
        def read(name):
            return json.loads((Path(__file__).parent / name).read_text())
        self.spec = read('electrical-review.json')
        self.control = read('electrical-control-revision.json')
        self.revision = read('electrical-boost-interlock.json')
        self.reset = read('electrical-reset-revision.json')
        self.headroom = read('electrical-headroom.json')
        self.harness = read('electrical-harness.json')
        # Analytical fixture, not claimed switch/wiring/module specifications.
        self.bounds = {'source_max_a': .0004, 'open_voltage_max_v': 5,
                       'contact_max_ohm': 1, 'enable_lead_max_ohm': .1,
                       'return_lead_max_ohm': .2, 'return_offset_max_v': .01,
                       'contact_conditions_covered': True}

    def state(self, closed=True):
        return physical_off_state(closed, self.bounds,
                                  self.revision['physical_off']['limits'], .4)

    def test_switch_replacement_preserves_power_pole_and_uses_a_dedicated_off_shunt(self):
        before = copy.deepcopy(self.spec)
        candidate = interlock_netlist(self.spec, self.revision)
        self.assertEqual(self.spec, before)
        self.assertEqual(candidate['S1'], 'C&K 7201SYZGE')
        self.assertEqual(candidate['switch_terminal_numbers']['CLAMP_COMMON'], 5)
        self.assertEqual(candidate['switch_positions']['OFF'], [[2, 1], [5, 4]])
        self.assertEqual(candidate['switch_positions']['ON'], [[2, 3], [5, 6]])
        for net, pin in [('BOOST_ENABLE', 'S1.CLAMP_COMMON'), ('GND', 'S1.CLAMP_OFF'),
                         ('FUSED', 'S1.ON'), ('A', 'S1.COMMON'), ('OFF_DRAIN', 'S1.OFF')]:
            self.assertIn(pin, candidate['nets'][net])
        self.assertIn('S1.CLAMP_OPEN', candidate['open_pins'])
        self.assertIn('U1.PG', candidate['nets']['PG_SENSE'])
        self.assertNotIn('U1.PG', candidate['nets']['BOOST_ENABLE'])

    def test_wrong_contact_material_pinout_and_power_pole_fail(self):
        for field, value in [('switch', 'C&K 7201SYZQE'),
                             ('terminal_numbers', {'CLAMP_COMMON': 2}),
                             ('positions', {'OFF': [[2, 3], [5, 6]]}),
                             ('nets', {'B': ['S1.CLAMP_COMMON'], 'GND': ['S1.CLAMP_OFF']}),
                             ('open_pins', [])]:
            with self.subTest(field=field):
                revision = copy.deepcopy(self.revision)
                revision['physical_off'][field] = value
                with self.assertRaisesRegex(ValueError, 'Physical OFF switch'):
                    interlock_netlist(self.spec, revision)
        self.spec['candidate']['nets']['A'].remove('S1.COMMON')
        with self.assertRaisesRegex(ValueError, 'power pole'):
            interlock_netlist(self.spec, self.revision)

    def test_unused_on_contact_may_not_hide_a_connection(self):
        self.spec['candidate']['nets']['B'].append('S1.CLAMP_OPEN')
        with self.assertRaisesRegex(ValueError, 'duplicate pin'):
            interlock_netlist(self.spec, self.revision)

    def test_kcl_includes_both_leads_and_local_ground_offset(self):
        result = self.state()
        # KVL from U4 ENABLE through 0.1 + 1 + 0.2 ohm to a ground 10 mV higher.
        self.assertAlmostEqual(result['enable_upper_v'], .01052)
        self.assertTrue(result['settled_off_clamp_pass'])
        self.bounds['return_lead_max_ohm'] += 1000
        result = self.state()
        self.assertAlmostEqual(result['enable_upper_v'], .41052)
        self.assertFalse(result['settled_off_clamp_pass'])

    def test_exact_disable_boundary_fails_strict_under_point_four_volts(self):
        self.bounds.update(contact_max_ohm=1000, enable_lead_max_ohm=0,
                           return_lead_max_ohm=0, return_offset_max_v=0)
        self.assertEqual(self.state()['enable_upper_v'], .4)
        self.assertFalse(self.state()['settled_off_clamp_pass'])

    def test_on_bounce_and_unknown_contact_do_not_claim_shutdown(self):
        for closed in (False, None):
            with self.subTest(closed=closed):
                result = self.state(closed)
                self.assertIsNone(result['enable_upper_v'])
                self.assertFalse(result['settled_off_clamp_pass'])
                self.assertIn('closed_off_contact', result['missing'])

    def test_missing_bounds_and_uncovered_contact_conditions_fail(self):
        original = copy.deepcopy(self.bounds)
        for field in self.bounds:
            with self.subTest(field=field):
                self.bounds = {**original, field: None}
                self.assertFalse(self.state()['settled_off_clamp_pass'])
        self.bounds = {**original, 'contact_conditions_covered': False}
        self.assertFalse(self.state()['settled_off_clamp_pass'])

    def test_open_voltage_and_contact_rating_are_independent_requirements(self):
        self.bounds.update(contact_max_ohm=0, enable_lead_max_ohm=0,
                           return_lead_max_ohm=0, return_offset_max_v=0)
        self.bounds['open_voltage_max_v'] = 21
        self.assertFalse(self.state()['settled_off_clamp_pass'])
        self.bounds.update(open_voltage_max_v=5, source_max_a=.081)
        self.assertEqual(self.state()['enable_upper_v'], 0)
        self.assertFalse(self.state()['within_contact_rating'])

    def test_numeric_and_schema_errors_are_rejected(self):
        original = copy.deepcopy(self.bounds)
        for field in original.keys() - {'contact_conditions_covered'}:
            for value in (True, -1, float('nan'), float('inf')):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.bounds = {**original, field: value}
                    self.state()
        self.bounds = original
        del self.bounds['return_lead_max_ohm']
        with self.assertRaisesRegex(ValueError, 'both conductors'):
            self.state()

    def test_real_designs_remain_unqualified_and_independent(self):
        def study():
            return boost_interlock_study(self.spec, self.control, self.revision)
        before = study()
        for design in ('wide', 'narrow'):
            self.assertFalse(before['physical_off']['designs'][design]['settled_off_clamp_pass'])
        self.revision['physical_off']['assembly_bounds']['wide'] = self.bounds
        after = study()
        self.assertEqual(before['physical_off']['designs']['narrow'], after['physical_off']['designs']['narrow'])
        self.assertTrue(after['physical_off']['designs']['wide']['settled_off_clamp_pass'])
        self.assertFalse(after['qualified'])
        self.assertEqual(after['unsupported_retained_en']['state'], 'unqualified')
        del self.revision['physical_off']['assembly_bounds']['narrow']
        with self.assertRaisesRegex(ValueError, 'wide/narrow'):
            study()

    def test_composed_circuit_preserves_supervisors_storage_and_single_switch_ownership(self):
        candidate = reset_netlist(self.spec, self.control, self.revision, self.reset)
        candidate = headroom_netlist(candidate, self.headroom)
        self.assertTrue({'U6.6', 'U7.1', 'S1.CLAMP_COMMON'} <= set(candidate['nets']['BOOST_ENABLE']))
        self.assertIn('U3.EN', candidate['nets']['CONTROLLER_EN'])
        storage = reset_storage_study(candidate, self.spec, self.control, self.reset)
        self.assertFalse(storage['qualified'])
        self.assertIsNone(storage['assembly']['required_off_s'])
        owners = heat_ownership(candidate, self.harness)
        self.assertEqual(sum(group.count('part:S1') for group in owners.values()), 1)


if __name__ == '__main__':
    unittest.main()
