"""Analytical DC fixtures, topology mutations and real harness source checks."""

import copy
import json
from pathlib import Path
import unittest

from electrical import reset_netlist
from electrical_path import analyze, harness_study, wire_resistance


class PathTests(unittest.TestCase):
    def setUp(self):
        # Independent hand calculation: two loads share 1 ohm on each rail.
        # A: 2 A, 2 ohm per branch conductor. B: 3 A, 3 ohm per conductor.
        self.segments = {
            'p': {'ends': ['P', 'PS'], 'resistance_max_ohm': 1},
            'n': {'ends': ['NS', 'N'], 'resistance_max_ohm': 1},
            'ap': {'ends': ['PS', 'AP'], 'resistance_max_ohm': 2},
            'an': {'ends': ['AN', 'NS'], 'resistance_max_ohm': 2},
            'bp': {'ends': ['PS', 'BP'], 'resistance_max_ohm': 3},
            'bn': {'ends': ['BN', 'NS'], 'resistance_max_ohm': 3},
        }
        self.paths = {
            'a': {'supply': ['p', 'ap'], 'return': ['an', 'n'],
                  'supply_ends': ['P', 'AP'], 'return_ends': ['AN', 'N']},
            'b': {'supply': ['p', 'bp'], 'return': ['bn', 'n'],
                  'supply_ends': ['P', 'BP'], 'return_ends': ['BN', 'N']},
        }
        self.currents = {'a': 2, 'b': 3}

    def calculate(self):
        return analyze(self.segments, self.paths, self.currents)

    def test_shared_supply_and_return_use_sum_before_squaring(self):
        result = self.calculate()
        self.assertEqual(result['paths']['a']['drop_max_v'], 18)
        self.assertEqual(result['paths']['b']['drop_max_v'], 28)
        # 2 * 5² * 1 + 2 * 2² * 2 + 2 * 3² * 3 = 120 W.
        self.assertEqual(result['loss_max_w'], 120)
        # Energy balance: sum of each load current times its round-trip drop.
        self.assertEqual(result['loss_max_w'], 2 * 18 + 3 * 28)

    def test_unknown_load_contaminates_shared_supply_and_return(self):
        self.currents['b'] = None
        result = self.calculate()
        for edge in ('p', 'n', 'bp', 'bn'):
            self.assertIsNone(result['segments'][edge]['current_max_a'])
        self.assertEqual(result['segments']['ap']['current_max_a'], 2)
        self.assertIsNone(result['paths']['a']['drop_max_v'])
        self.assertIn('b.current_max_a', result['paths']['a']['missing'])
        self.assertIsNone(result['loss_max_w'])

    def test_unknown_branch_resistance_does_not_contaminate_other_branch(self):
        self.segments['bn']['resistance_max_ohm'] = None
        result = self.calculate()
        self.assertEqual(result['paths']['a']['drop_max_v'], 18)
        self.assertIsNone(result['paths']['b']['drop_max_v'])
        self.assertEqual(result['paths']['b']['missing'], ['bn.resistance_max_ohm'])

    def test_zero_current_is_not_missing_evidence(self):
        self.currents = {'a': 0, 'b': 0}
        self.assertEqual(self.calculate()['loss_max_w'], 0)
        # A zero study current still cannot qualify a missing conductor bound.
        self.segments['bn']['resistance_max_ohm'] = None
        self.assertIsNone(self.calculate()['paths']['b']['drop_max_v'])

    def test_both_legs_must_connect_to_the_declared_terminals(self):
        for leg, value in [('return', []), ('return', ['an']), ('supply', ['ap', 'p'])]:
            with self.subTest(leg=leg, value=value):
                changed = copy.deepcopy(self.paths)
                changed['a'][leg] = value
                with self.assertRaises(ValueError):
                    analyze(self.segments, changed, self.currents)

    def test_a_return_terminal_cannot_move_to_a_nearer_ground_junction(self):
        self.paths['a']['return_ends'][1] = 'NS'
        with self.assertRaisesRegex(ValueError, 'Wrong return terminal'):
            self.calculate()

    def test_deleted_duplicate_or_unaccounted_segments_fail(self):
        self.paths['a']['supply'].append('p')
        with self.assertRaisesRegex(ValueError, 'repeated'):
            self.calculate()
        self.setUp()
        del self.segments['ap']
        with self.assertRaisesRegex(ValueError, 'Missing'):
            self.calculate()
        self.setUp()
        self.segments['unused'] = {'ends': ['Q', 'R'], 'resistance_max_ohm': 0}
        with self.assertRaisesRegex(ValueError, 'Unaccounted'):
            self.calculate()

    def test_parallel_return_routes_require_a_real_network_solver(self):
        self.segments['n2'] = {'ends': ['NS', 'N'], 'resistance_max_ohm': 1}
        self.paths['b']['return'] = ['bn', 'n2']
        with self.assertRaisesRegex(ValueError, 'Non-radial'):
            self.calculate()

    def test_zero_resistance_is_distinct_from_unknown(self):
        self.segments['p']['resistance_max_ohm'] = 0
        self.assertEqual(self.calculate()['paths']['a']['drop_max_v'], 13)

    def test_numeric_errors_and_unlisted_currents_cannot_pass(self):
        for value in (True, -1, float('inf'), float('nan')):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    analyze(self.segments, self.paths, {'a': value, 'b': 3})
        for currents in ({'a': 2}, {'a': 2, 'b': 3, 'c': 0}):
            with self.assertRaises(ValueError):
                analyze(self.segments, self.paths, currents)


class HarnessTests(unittest.TestCase):
    def setUp(self):
        here = Path(__file__).parent
        def read(name):
            return json.loads((here / name).read_text())
        self.definition = read('electrical-harness.json')
        spec = read('electrical-review.json')
        self.candidate = reset_netlist(spec, read('electrical-control-revision.json'),
                                      read('electrical-boost-interlock.json'),
                                      read('electrical-reset-revision.json'))
        self.limits = spec['limits']

    def calculate(self):
        return harness_study(self.definition, self.candidate, self.limits)

    def test_catalogue_maximum_conversion_uses_both_conductors_once(self):
        part = self.definition['wire_parts']['18_red']
        self.assertEqual(part['max_ohm_per_1000ft_at_20c'], 6.23)
        self.assertAlmostEqual(wire_resistance(part, 304800), 6.23)
        result = self.calculate()
        wide = result['designs']['wide']
        narrow = result['designs']['narrow']
        # Five 100 mm main conductors; no automatic round-trip doubling.
        self.assertAlmostEqual(wide['wire_only_path_ohm_at_20c']['boost_input'], .5 * 6.23 / 304.8)
        self.assertAlmostEqual(narrow['wire_only_path_ohm_at_20c']['boost_input'], .4 * 6.23 / 304.8)
        self.assertAlmostEqual(wide['reference_boost_wires_only']['load_current_a'], 6.25 / .85 / 2.9)
        self.assertFalse(result['qualified'])

    def test_return_length_perturbation_changes_only_its_design(self):
        before = self.calculate()
        self.definition['designs']['narrow']['boost_return'] += 100
        after = self.calculate()
        self.assertEqual(before['designs']['wide'], after['designs']['wide'])
        resistance = after['designs']['narrow']['wire_only_path_ohm_at_20c']['boost_input']
        self.assertAlmostEqual(resistance, .5 * 6.23 / 304.8)

    def test_all_three_demand_classes_remain_unbounded(self):
        for design in self.calculate()['designs'].values():
            for case in design['cases'].values():
                self.assertIsNone(case['loss_max_w'])
                self.assertTrue(all(row['missing'] for row in case['paths'].values()))
        del self.definition['scenarios']['inrush']
        with self.assertRaisesRegex(ValueError, 'inrush bounds'):
            self.calculate()

    def test_wire_cannot_bypass_efuse_or_use_an_unowned_ground(self):
        for node in ('U1.IN', 'unknown_ground'):
            with self.subTest(node=node):
                self.definition['segments']['boost_supply']['ends'][0] = node
                with self.assertRaisesRegex(ValueError, 'bypasses protection'):
                    self.calculate()

    def test_junction_cannot_override_component_pin_ownership(self):
        self.definition['junction_nets']['U1.IN'] = 'B'
        with self.assertRaisesRegex(ValueError, 'shadows'):
            self.calculate()

    def test_missing_length_or_load_cannot_omit_its_accounting(self):
        del self.definition['designs']['narrow']['cell_return']
        with self.assertRaisesRegex(ValueError, 'wire lengths'):
            self.calculate()
        self.setUp()
        del self.definition['paths']['radio']
        with self.assertRaisesRegex(ValueError, 'every power load'):
            self.calculate()

    def test_nominal_resistance_and_wrong_temperature_are_not_maxima(self):
        part = copy.deepcopy(self.definition['wire_parts']['18_red'])
        part['resistance_kind'] = 'nominal'
        with self.assertRaises(ValueError):
            wire_resistance(part, 100)
        part['resistance_kind'] = 'maximum'
        part['reference_temperature_c'] = 85
        with self.assertRaises(ValueError):
            wire_resistance(part, 100)

    def test_claiming_zero_load_does_not_fill_unknown_component_bounds(self):
        for case in self.definition['scenarios'].values():
            for key in case:
                case[key] = 0
        result = self.calculate()
        for design in result['designs'].values():
            self.assertIsNone(design['cases']['continuous']['loss_max_w'])
        self.assertFalse(result['qualified'])

    def test_peripherals_cannot_move_to_the_five_volt_led_rail(self):
        for name in ('blackpill', 'gps', 'imu', 'radio'):
            with self.subTest(name=name):
                changed = copy.deepcopy(self.definition)
                changed['paths'][name]['supply_ends'][0] = 'U4.VOUT'
                with self.assertRaisesRegex(ValueError, 'supply voltage'):
                    harness_study(changed, self.candidate, self.limits)
        self.definition['load_ports']['gps']['nominal_v'] = 5
        with self.assertRaisesRegex(ValueError, 'supply voltage'):
            self.calculate()

    def test_peripheral_peak_budget_adds_all_loads_and_includes_unknowns(self):
        def peak():
            return self.calculate()['designs']['wide']['cases']['pwm_radio_peak']
        self.assertIsNone(peak()['within_published_peak_limit'])
        case = self.definition['scenarios']['pwm_radio_peak']
        for name in ('blackpill', 'gps', 'imu', 'radio'):
            case[name] = .125
        self.assertEqual(peak()['external_3v3_current_a'], .5)
        self.assertTrue(peak()['within_published_peak_limit'])
        case['radio'] = .126
        self.assertFalse(peak()['within_published_peak_limit'])
        self.assertFalse(self.calculate()['qualified'])

    def test_peak_rating_cannot_be_raised_to_fit_the_load(self):
        self.definition['peripheral_peak_limit_a'] = 1
        with self.assertRaisesRegex(ValueError, 'published'):
            self.calculate()


if __name__ == '__main__':
    unittest.main()
