"""Charge conservation, load-step boundaries and independent local UVLO wiring."""

import copy
import json
from pathlib import Path
import unittest

from electrical import reset_netlist
from electrical_headroom import headroom_netlist, headroom_study, hold_up


class HoldUpTests(unittest.TestCase):
    def test_charge_conservation_and_instantaneous_series_drop(self):
        # 1 mF from 4 V, 2 A for 100 us: 0.2 V charge loss plus 0.1 V ESR.
        result = hold_up(4, 2.9, .001, 2, .05, .0001, .03)
        self.assertAlmostEqual(result['voltage_lower_v'], 3.67)
        self.assertAlmostEqual(result['charge_deficit_c'], .0002)
        self.assertAlmostEqual(.001 * (4 - .1 - .03 - result['voltage_lower_v']), .0002)

    def test_variable_pulses_and_no_source_are_bounded_by_coincident_maximum(self):
        voltage = 4.0
        minimum = voltage
        dt = 1e-7
        for sample in range(1000):
            current = 2 if sample % 13 < 9 else .3
            voltage -= current * dt / .001
            minimum = min(minimum, voltage - current * .05)
        result = hold_up(4, 2.9, .001, 2, .05, 1000 * dt, 0)
        self.assertGreaterEqual(minimum, result['voltage_lower_v'])

    def test_exact_capacitance_boundary_and_monotonicity(self):
        result = hold_up(4, 3, .001, 2, 0, .0005, 0)
        self.assertTrue(result['pass'])
        self.assertAlmostEqual(result['required_capacitance_min_f'], .001)
        for args in [(4, 3, .00099, 2, 0, .0005, 0),
                     (4, 3, .001, 2.01, 0, .0005, 0),
                     (4, 3, .001, 2, .01, .0005, 0),
                     (4, 3, .001, 2, 0, .00051, 0),
                     (4, 3, .001, 2, 0, .0005, .01)]:
            with self.subTest(args=args):
                self.assertFalse(hold_up(*args)['pass'])

    def test_more_capacitance_cannot_repair_an_instantaneous_collapse(self):
        result = hold_up(3, 2.9, 100, 2, .1, .00003, 0)
        self.assertFalse(result['pass'])
        self.assertIsNone(result['required_capacitance_min_f'])

    def test_unknowns_never_become_zero_even_when_another_input_is_zero(self):
        args = [4, 2.9, .001, 0, 0, 0, 0]
        for index in range(2, len(args)):
            unknown = list(args)
            unknown[index] = None
            with self.subTest(index=index):
                result = hold_up(*unknown)
                self.assertFalse(result['pass'])
                self.assertIsNone(result['voltage_lower_v'])
                self.assertTrue(result['missing'])
        self.assertTrue(hold_up(*args)['pass'])
        self.assertEqual(hold_up(*args)['required_capacitance_min_f'], 0)

    def test_invalid_inputs_and_overflow_are_errors(self):
        args = [4, 2.9, .001, 2, .05, .00003, 0]
        for index in range(len(args)):
            for value in (True, -1, float('nan'), float('inf')):
                invalid = list(args)
                invalid[index] = value
                with self.subTest(index=index, value=value), self.assertRaises(ValueError):
                    hold_up(*invalid)
        with self.assertRaises(ValueError):
            hold_up(4, 2.9, 0, 2, 0, 0, 0)
        with self.assertRaisesRegex(ValueError, 'overflow'):
            hold_up(4, 2.9, .001, 1e308, 1e308, .01, 0)


class LocalHeadroomTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        def read(name):
            return json.loads((root / name).read_text())
        self.spec = read('electrical-review.json')
        self.definition = read('electrical-headroom.json')
        self.candidate = reset_netlist(self.spec, read('electrical-control-revision.json'),
                                      read('electrical-boost-interlock.json'),
                                      read('electrical-reset-revision.json'))

    def calculate(self):
        return headroom_study(self.spec, self.candidate, self.definition)

    def test_local_clamp_preserves_pg_interlock_and_latching_controller(self):
        original = copy.deepcopy(self.candidate)
        result = headroom_netlist(self.candidate, self.definition)
        self.assertEqual(self.candidate, original)
        self.assertEqual(set(result['nets']['BOOST_ENABLE']), {'U4.ENABLE', 'U6.6', 'U7.1'})
        for name in ('PG_SENSE', 'KILL', 'CONTROLLER_EN', 'EFUSE_EN'):
            self.assertEqual(result['nets'][name], original['nets'][name])
        self.assertIn('U7.2', result['nets']['B'])
        self.assertIn('U7.3', result['nets']['GND'])
        self.assertTrue({'U7.4', 'U7.5'} <= set(result['open_pins']))

    def test_duplicate_pins_wrong_rail_and_removed_bypass_are_rejected(self):
        for pin in ('U7.1', 'U7.2', 'U7.3', 'U7.4', 'U7.5'):
            changed = copy.deepcopy(self.candidate)
            changed['nets']['A'].append(pin)
            with self.subTest(pin=pin), self.assertRaisesRegex(ValueError, 'Duplicate pin'):
                headroom_netlist(changed, self.definition)
        for name, pin in [('B', 'U4.VIN'), ('GND', 'U4.GND'), ('B', 'C_U6.1')]:
            changed = copy.deepcopy(self.candidate)
            changed['nets'][name].remove(pin)
            with self.subTest(pin=pin), self.assertRaisesRegex(ValueError, 'local supply'):
                headroom_netlist(changed, self.definition)
        self.definition['supervisor'] = 'TPS3840PL35DBVR'
        with self.assertRaisesRegex(ValueError, 'topology'):
            self.calculate()

    def test_overdrive_and_threshold_tolerance_precede_charge_budget(self):
        result = self.calculate()
        self.assertAlmostEqual(result['falling_threshold_v'][0], 3.4475)
        self.assertAlmostEqual(result['rising_threshold_v'][1], 3.7775)
        self.assertAlmostEqual(result['timing_budget_start_v'], 3.10275)
        self.assertFalse(result['reference_hold_up']['pass'])
        self.assertGreater(result['reference_hold_up']['required_capacitance_min_f'], .0004)
        self.assertFalse(result['qualified'])

    def test_missing_assembly_data_stays_unbounded_for_both_designs(self):
        for row in self.calculate()['designs'].values():
            self.assertFalse(row['pass'])
            self.assertFalse(row['conditional_clamp_pass'])
            self.assertIsNone(row['hold_up']['voltage_lower_v'])
            self.assertEqual(len(row['unresolved_premises']), 4)

    def test_numeric_headroom_cannot_replace_timing_startup_or_clamp_evidence(self):
        bounds = self.definition['assembly_bounds']['wide']
        bounds.update(capacitance_min_f=.001, deficit_max_a=1, series_max_ohm=.01,
                      boost_shutdown_max_s=.00002, additional_drop_max_v=0,
                      enable_source_max_a=.0001)
        result = self.calculate()['designs']['wide']
        self.assertTrue(result['hold_up']['pass'])
        self.assertFalse(result['pass'])
        for premise in bounds['premises']:
            bounds['premises'][premise] = True  # Synthetic fixture only.
        self.assertTrue(self.calculate()['designs']['wide']['pass'])
        # Independent narrow assembly cannot inherit the wide fixture's result.
        self.assertFalse(self.calculate()['designs']['narrow']['pass'])
        self.assertFalse(self.calculate()['qualified'])
        bounds['enable_source_max_a'] = .002001
        self.assertFalse(self.calculate()['designs']['wide']['pass'])
        bounds['enable_source_max_a'] = .0001
        bounds['boost_shutdown_max_s'] = .001
        self.assertFalse(self.calculate()['designs']['wide']['pass'])

    def test_missing_design_and_invalid_premise_are_input_errors(self):
        del self.definition['assembly_bounds']['narrow']
        with self.assertRaisesRegex(ValueError, 'Both designs'):
            self.calculate()
        self.setUp()
        self.definition['assembly_bounds']['wide']['premises']['startup_rebound_covered'] = 1
        with self.assertRaisesRegex(ValueError, 'boolean or unknown'):
            self.calculate()


if __name__ == '__main__':
    unittest.main()
