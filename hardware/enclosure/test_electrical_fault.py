"""Independent fault-energy oracles and protection-path mutation checks."""

import copy
import json
import math
from pathlib import Path
import unittest

from electrical_fault import (capacitor_pulse, combine_pulses, fault_study,
                              prospective_current, withstand)


class FaultNumericsTests(unittest.TestCase):
    def test_prospective_current_counts_both_conductors(self):
        self.assertEqual(prospective_current(4, {'positive': .02, 'return': .03}), 80)
        self.assertEqual(prospective_current(4, {'known': .05, 'unknown': None}), 80)
        self.assertIsNone(prospective_current(4, {'unknown': None, 'ideal': 0}))
        self.assertEqual(prospective_current(0, {'unknown': None}), 0)

    def test_rc_energy_matches_independent_midpoint_integration(self):
        capacitance, voltage, resistance = .002, 5, .2
        result = capacitor_pulse(capacitance, voltage, resistance)
        tau = resistance * capacitance
        dt = tau / 1000
        numerical = sum((voltage / resistance * math.exp(-(i + .5)*dt/tau))**2 * dt
                        for i in range(20000))
        self.assertAlmostEqual(result['i2t_a2s'], numerical, delta=1e-7)
        self.assertEqual(result['peak_a'], 25)
        self.assertAlmostEqual(result['stored_j'], .025)
        self.assertAlmostEqual(result['i2t_a2s'] * resistance, result['stored_j'])

    def test_capacitor_known_energy_does_not_bound_peak_without_resistance(self):
        for resistance in (None, 0):
            with self.subTest(resistance=resistance):
                pulse = capacitor_pulse(.001, 5, resistance)
                self.assertEqual(pulse['stored_j'], .0125)
                self.assertIsNone(pulse['i2t_a2s'])
                self.assertIsNone(pulse['peak_a'])
        self.assertEqual(capacitor_pulse(0, 5, None)['i2t_a2s'], 0)
        self.assertIsNone(capacitor_pulse(None, 5, .1)['i2t_a2s'])

    def test_overlap_keeps_cross_terms_and_conservatively_bounds_shifted_pulses(self):
        # Two coincident unit rectangular pulses: integral((1+1)^2)=4, not 2.
        pulse = {'peak_a': 1, 'i2t_a2s': 1}
        self.assertEqual(combine_pulses([pulse, pulse]), {'peak_a': 2, 'i2t_a2s': 4})
        # Shift one by half its duration: .5*1 + .5*4 + .5*1 = 3 <= 4.
        self.assertGreaterEqual(combine_pulses([pulse, pulse])['i2t_a2s'], 3)
        a = capacitor_pulse(.002, 5, .2)
        b = capacitor_pulse(.001, 5, .4)
        # Equal time constants make Minkowski equality exact for these pulses.
        self.assertAlmostEqual(combine_pulses([a, b])['i2t_a2s'], (25+12.5)**2*.0004/2)
        self.assertIsNone(combine_pulses([pulse, {'peak_a': None, 'i2t_a2s': None}])['i2t_a2s'])

    def test_peak_and_total_energy_are_independent_withstand_requirements(self):
        pulse = {'peak_a': 10, 'i2t_a2s': 2}
        self.assertTrue(withstand(pulse, {'peak_a': 10, 'i2t_a2s': 2})['pass'])
        for limits in ({'peak_a': 9, 'i2t_a2s': 3}, {'peak_a': 11, 'i2t_a2s': 1},
                       {'peak_a': 11, 'i2t_a2s': None}):
            self.assertFalse(withstand(pulse, limits)['pass'])

    def test_invalid_numbers_and_empty_source_sets_fail(self):
        for bad in (float('nan'), float('inf'), -1, True, '1'):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    prospective_current(4, {'bad': bad})
                with self.assertRaises(ValueError):
                    capacitor_pulse(.001, bad, .01)
                with self.assertRaises(ValueError):
                    combine_pulses([{'peak_a': bad, 'i2t_a2s': 1}])
        with self.assertRaises(ValueError):
            prospective_current(4, {})
        with self.assertRaises(ValueError):
            combine_pulses([])
        with self.assertRaises(ValueError):
            prospective_current(5, {'too_small': 1e-320})


class HarnessFaultTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        self.spec = json.loads((root/'electrical-review.json').read_text())
        self.harness = json.loads((root/'electrical-harness.json').read_text())
        self.revision = json.loads((root/'electrical-fault-coordination.json').read_text())

    def calculate(self):
        return fault_study(self.spec, self.harness, self.revision)

    def synthetic_bounds(self):
        # Solver fixture ONLY: none of these numbers are hardware evidence.
        for minima in self.revision['designs'].values():
            for name in minima:
                minima[name] = .01
        for limits in self.revision['withstand'].values():
            limits.update(peak_a=1000, i2t_a2s=10000)
        for row in self.revision['capacitor_sources'].values():
            row.update(capacitance_max_f=.001, voltage_max_v=5, resistance_min_ohm=1)
        self.revision['fuse']['total_clearing_max_s'] = .1
        self.revision['conditions'] = dict.fromkeys(self.revision['conditions'], True)

    def test_actual_candidate_stays_unbounded_in_both_designs(self):
        report = self.calculate()
        self.assertFalse(report['qualified'])
        self.assertAlmostEqual(report['required_nonfuse_loop_min_ohm_for_interrupt_rating'], 4.3/300)
        self.assertEqual(set(report['designs']), {'wide', 'narrow'})
        for design in report['designs'].values():
            self.assertEqual(len(design), 12)
            self.assertTrue(all(not row['conditional_pass'] for row in design.values()))
            for row in design.values():
                if row['battery_connected']:
                    self.assertIsNone(row['battery']['peak_a'])
                self.assertIsNone(row['all_sources_overlap']['i2t_a2s'])

    def test_fuse_resistance_melting_i2t_and_efuse_limit_cannot_bound_backup(self):
        report = self.calculate()
        self.spec['limits']['fuse_cold_resistance_ohm_nominal'] = 100
        self.spec['limits']['fuse_melting_i2t_a2s_nominal'] = .00001
        self.spec['limits']['efuse_current_formula_a_ohm'] = .01
        self.harness['wire_parts']['18_red']['max_ohm_per_1000ft_at_20c'] = 10000
        self.revision['fuse']['catalog_only']['melting_i2t_nominal_a2s'] = .00001
        self.assertEqual(report, self.calculate())

    def test_prefuse_fault_has_no_fuse_and_fused_wire_is_live_in_off(self):
        self.synthetic_bounds()
        cases = self.calculate()['designs']['wide']
        for state in ('ON', 'OFF'):
            row = cases['before_f1:' + state]
            self.assertFalse(row['f1_in_battery_path'])
            self.assertFalse(row['f1_rating_comparison'])
            self.assertIsNone(row['battery']['i2t_a2s'])
            self.assertFalse(row['conditional_pass'])
            self.assertTrue(cases['switch_input:' + state]['battery_connected'])
        row = cases['a_to_ground:OFF']
        self.assertFalse(row['battery_connected'])
        self.assertEqual(row['battery']['i2t_a2s'], 0)
        self.assertGreater(row['all_sources_overlap']['i2t_a2s'], 0)

    def test_rating_overrun_and_missing_conditions_cannot_pass(self):
        self.synthetic_bounds()
        self.assertTrue(self.calculate()['designs']['wide']['after_f1:ON']['conditional_pass'])
        self.revision['designs']['wide'] = dict.fromkeys(self.revision['designs']['wide'], .0001)
        row = self.calculate()['designs']['wide']['after_f1:ON']
        self.assertGreater(row['battery']['peak_a'], 300)
        self.assertFalse(row['f1_rating_comparison'])
        self.assertFalse(row['conditional_pass'])
        self.assertTrue(self.calculate()['designs']['narrow']['after_f1:ON']['conditional_pass'])
        self.revision['conditions']['clearing_bound_covers_fault_range'] = None
        self.assertFalse(self.calculate()['designs']['narrow']['after_f1:ON']['conditional_pass'])

    def test_return_lead_and_both_contacts_are_owned_and_change_result(self):
        self.synthetic_bounds()
        before = self.calculate()['designs']['wide']['a_to_ground:ON']
        self.assertIn('positive_contact', before['battery_loop'])
        self.assertIn('negative_contact', before['battery_loop'])
        self.assertIn('cell_return', before['battery_loop'])
        self.assertNotIn('f1', before['battery_loop'])
        self.assertNotIn('efuse_b_copper', before['battery_loop'])
        self.revision['designs']['wide']['cell_return'] *= 2
        after = self.calculate()['designs']['wide']['a_to_ground:ON']
        self.assertLess(after['battery']['peak_a'], before['battery']['peak_a'])
        self.assertAlmostEqual(after['battery']['i2t_a2s'], after['battery']['peak_a']**2*.1)

    def test_missing_clearing_or_withstand_keeps_failure(self):
        self.synthetic_bounds()
        self.revision['fuse']['total_clearing_max_s'] = None
        row = self.calculate()['designs']['wide']['after_f1:ON']
        self.assertTrue(row['f1_rating_comparison'])
        self.assertFalse(row['conditional_pass'])
        self.revision['fuse']['total_clearing_max_s'] = .1
        self.revision['withstand']['negative_contact']['peak_a'] = None
        self.assertFalse(self.calculate()['designs']['wide']['after_f1:ON']['conditional_pass'])

    def test_omitted_return_rewired_endpoint_or_missing_ledger_fails(self):
        original = copy.deepcopy(self.harness)
        self.harness['paths']['boost_input']['return'].remove('cell_return')
        with self.assertRaisesRegex(ValueError, 'Disconnected fault loop'):
            self.calculate()
        self.harness = original
        self.harness['segments']['s1']['ends'][1] = 'WRONG'
        with self.assertRaisesRegex(ValueError, 'Disconnected fault loop'):
            self.calculate()
        self.harness = copy.deepcopy(original)
        self.harness['segments']['s1']['ends'][1] = 'S1.COMMON'
        del self.revision['withstand']['negative_contact']
        with self.assertRaisesRegex(ValueError, 'ledger'):
            self.calculate()

    def test_missing_design_capacitor_or_condition_is_rejected(self):
        for field, key in (('designs', 'narrow'), ('capacitor_sources', 'B'),
                           ('conditions', 'no_external_or_inductive_sources')):
            original = copy.deepcopy(self.revision)
            del self.revision[field][key]
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.calculate()
            self.revision = original


if __name__ == '__main__':
    unittest.main()
