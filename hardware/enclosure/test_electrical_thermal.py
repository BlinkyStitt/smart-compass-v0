"""Independent heat-balance/transient oracles and assembly rejection checks."""

import json
import math
from pathlib import Path
import unittest

from electrical import reset_netlist
from electrical_thermal import (heat_ownership, reference_heat, temperature_envelope,
                                temperature_interval, thermal_study)


class TemperatureEnvelopeTests(unittest.TestCase):
    def test_cooling_bound_matches_independent_rc_solution(self):
        interval = temperature_interval({'cell': 2}, {'cell': 1}, {'cell': {'cell': 4}},
                                        {'cell': 20}, {'cell': 35}, 25, 25, 25, 25)
        self.assertTrue(interval['pass'])
        self.assertEqual(interval['lower_c']['cell'], 21)
        self.assertEqual(interval['cold']['observers']['cell']['margin_c'], 1)
        self.assertEqual(interval['hot']['observers']['cell']['upper_c'], 33)
        # C=3 J/K, R=4 K/W; exact response to constant -1 W local heat.
        for t in (0, .01, 1, 10, 100, 1000):
            actual = 25 - 4 * (1 - math.exp(-t / 12))
            self.assertGreaterEqual(actual, interval['lower_c']['cell'])

    def test_signed_pulses_and_cross_cooling_stay_inside_both_bounds(self):
        z = {'a': {'a': 1.25 / .875, 'b': 1 / .875},
             'b': {'a': 1 / .875, 'b': 1.5 / .875}}
        interval = temperature_interval({'a': 3, 'b': 1}, {'a': 1, 'b': 2}, z,
                                        {'a': -40, 'b': -40}, {'a': 100, 'b': 100},
                                        20, 25, 15, 60)
        a, b = 60., 15.
        # Independent numerical circuit integration with positive Euler weights.
        for i in range(15000):
            pa, pb = (3 if i % 79 < 40 else -1), (1 if i % 67 < 30 else -2)
            ambient = 20 if i % 109 < 50 else 25
            da = (pa - .5 * (a - ambient) - (a - b)) * .01
            db = (pb - .25 * (b - ambient) - (b - a)) * .01 / 2
            a, b = a + da, b + db
            for key, actual in (('a', a), ('b', b)):
                self.assertGreaterEqual(actual, interval['lower_c'][key])
                self.assertLessEqual(actual, interval['hot']['observers'][key]['upper_c'])

    def test_inverted_temperature_ranges_and_missing_cooling_owners_are_errors(self):
        for low, high in ((26, 25), (True, 25), (0, math.nan)):
            with self.subTest(low=low, high=high), self.assertRaises(ValueError):
                temperature_interval({'p': 1}, {'p': 0}, {'p': {'p': 1}},
                                     {'p': -40}, {'p': 100}, low, high, 25, 25)
        with self.assertRaises(ValueError):
            temperature_interval({'p': 1}, {}, {'p': {'p': 1}},
                                 {'p': -40}, {'p': 100}, 25, 25, 25, 25)
        with self.assertRaises(ValueError):
            temperature_interval({'p': 1}, {'p': 0}, {'p': {'p': 1}},
                                 {'p': 40}, {'p': 35}, 25, 25, 25, 25)

    def test_single_node_matches_steady_heat_balance_and_bounds_rc_history(self):
        result = temperature_envelope({'heater': 2}, {'case': {'heater': 4}},
                                      {'case': 40}, 25, 25)
        upper = result['observers']['case']['upper_c']
        self.assertEqual(upper, 33)
        self.assertEqual(result['observers']['case']['margin_c'], 7)
        self.assertTrue(result['pass'])
        # Independent exact solution, C=3 J/K, R=4 K/W, from ambient.
        for t in [0, .01, 1, 10, 100, 1000]:
            actual = 25 + 8 * (1 - math.exp(-t / 12))
            self.assertLessEqual(actual, upper)

    def test_cross_heating_matches_two_node_kirchhoff_balance(self):
        # Boundary conductances 0.5/0.25 W/K, inter-node conductance 1 W/K.
        # Inverse of [[1.5,-1],[-1,1.25]], derived independently by hand.
        z = {'a': {'a': 1.25 / .875, 'b': 1 / .875},
             'b': {'a': 1 / .875, 'b': 1.5 / .875}}
        result = temperature_envelope({'a': 3, 'b': 1}, z, {'a': 40, 'b': 40}, 25, 25)
        a, b = (result['observers'][key]['upper_c'] for key in ('a', 'b'))
        self.assertAlmostEqual(.5 * (a - 25) + (a - b), 3)
        self.assertAlmostEqual(.25 * (b - 25) + (b - a), 1)
        self.assertAlmostEqual(.5 * (a - 25) + .25 * (b - 25), 4)
        isolated = temperature_envelope({'a': 0, 'b': 1}, z, {'a': 40, 'b': 40}, 25, 25)
        self.assertGreater(isolated['observers']['a']['upper_c'], 25)

    def test_bounded_peaks_cover_repeated_pulses_and_hot_restart(self):
        z = {'a': {'a': 1.25 / .875, 'b': 1 / .875},
             'b': {'a': 1 / .875, 'b': 1.5 / .875}}
        result = temperature_envelope({'a': 3, 'b': 1}, z, {'a': 70, 'b': 70}, 25, 60)
        a, b = 60., 55.
        # Independently integrate the passive RC network; diagonal heat
        # capacities 1 and 2 J/K. Euler step is far inside positivity limits.
        for i in range(15000):
            pa = 3 if i % 79 < 40 else 0
            pb = 1 if i % 67 < 30 else 0
            da = (pa - .5 * (a - 25) - (a - b)) * .01
            db = (pb - .25 * (b - 25) - (b - a)) * .01 / 2
            a, b = a + da, b + db
            self.assertLessEqual(a, result['observers']['a']['upper_c'])
            self.assertLessEqual(b, result['observers']['b']['upper_c'])
        self.assertFalse(temperature_envelope({'a': 0}, {'a': {'a': 1}}, {'a': 40}, 25, 60)['pass'])

    def test_missing_cross_term_cannot_be_treated_as_isolation(self):
        with self.assertRaises(ValueError):
            temperature_envelope({'a': 0, 'b': 1}, {'a': {'a': 1}}, {'a': 40}, 25, 25)
        result = temperature_envelope({'a': 0, 'b': 1}, {'a': {'a': 1, 'b': None}}, {'a': 40}, 25, 25)
        self.assertFalse(result['pass'])
        self.assertIsNone(result['observers']['a']['upper_c'])

    def test_unknown_power_and_temperature_do_not_produce_zero_or_pass(self):
        for p, z, limit, boundary, initial in [(None, 1, 40, 25, 25), (1, None, 40, 25, 25),
                                             (1, 1, None, 25, 25), (1, 1, 40, None, 25),
                                             (1, 1, 40, 25, None)]:
            with self.subTest(values=(p, z, limit, boundary, initial)):
                result = temperature_envelope({'p': p}, {'c': {'p': z}}, {'c': limit}, boundary, initial)
                self.assertFalse(result['pass'])
                self.assertTrue(result['observers']['c']['missing'])

    def test_limits_include_equality_and_overtemperature(self):
        self.assertTrue(temperature_envelope({'p': 2}, {'c': {'p': 5}}, {'c': 35}, 25, 25)['pass'])
        result = temperature_envelope({'p': 2.01}, {'c': {'p': 5}}, {'c': 35}, 25, 25)
        self.assertFalse(result['pass'])
        self.assertLess(result['observers']['c']['margin_c'], 0)

    def test_invalid_bounds_reject_bool_nonfinite_negative_power_and_overflow(self):
        for value in [True, '1', -1, math.nan, math.inf]:
            for kind in ['power', 'transfer']:
                with self.subTest(value=value, kind=kind), self.assertRaises(ValueError):
                    temperature_envelope({'p': value if kind == 'power' else 1},
                                         {'c': {'p': value if kind == 'transfer' else 1}}, {'c': 40}, 25, 25)
        with self.assertRaises(ValueError):
            temperature_envelope({'p': 1e308}, {'c': {'p': 1e308}}, {'c': 40}, 25, 25)
        for value in [True, math.nan, math.inf]:
            with self.assertRaises(ValueError):
                temperature_envelope({'p': 1}, {'c': {'p': 1}}, {'c': value}, 25, 25)
        with self.assertRaises(ValueError):
            temperature_envelope({}, {}, {}, 25, 25)


class ThermalAssemblyTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent

        def read(name):
            return json.loads((root / name).read_text())

        self.spec = read('electrical-review.json')
        self.candidate = reset_netlist(self.spec, read('electrical-control-revision.json'),
                                      read('electrical-boost-interlock.json'), read('electrical-reset-revision.json'))
        self.harness = read('electrical-harness.json')
        self.definition = read('electrical-thermal.json')

    def study(self):
        return thermal_study(self.definition, self.spec, self.candidate, self.harness)

    def test_reference_conserves_energy_without_double_counting_converter_input(self):
        result = reference_heat(self.spec)
        self.assertAlmostEqual(result['input_power_w'], 7.352941176470588)
        self.assertAlmostEqual(result['boost_conversion_heat_w'], 1.102941176470588)
        self.assertAlmostEqual(result['output_assigned_to_heat_w'] + result['boost_conversion_heat_w'],
                               result['input_power_w'])
        self.assertAlmostEqual(result['efuse_conduction_sensitivity_w'], 140625 / 486098)

    def test_all_netlist_parts_and_harness_segments_have_unique_heat_owners(self):
        groups = heat_ownership(self.candidate, self.harness)
        owned = [asset for assets in groups.values() for asset in assets]
        self.assertEqual(len(owned), len(set(owned)))
        self.assertEqual(set(self.harness['segments']),
                         {item.removeprefix('segment:') for item in owned if item.startswith('segment:')})
        self.assertEqual(groups['segment:efuse_b_copper'], ['segment:efuse_b_copper', 'part:U1'])
        for key in ['R_B_BLEED', 'R_C_BLEED', 'R_OUT', 'C_OUT', 'U4', 'U5', 'U6', 'cell', 'radio', 'sparkle']:
            self.assertIn('part:' + key, owned)
        self.assertNotIn('part:loads', owned)

    def test_new_devices_and_conductors_add_unknown_heat_instead_of_disappearing(self):
        count = len(self.study()['heat_ownership'])
        self.candidate['nets']['B'].append('C_EXTRA.1')
        self.candidate['nets']['GND'].append('C_EXTRA.2')
        self.harness['segments']['extra_return'] = {'kind': 'unbounded', 'ends': ['X', 'GND']}
        result = self.study()
        self.assertEqual(len(result['heat_ownership']), count + 2)
        self.assertEqual(result['designs']['wide']['cases']['normal']['unbounded_heat_count'], count + 2)
        self.assertFalse(result['conditional_pass'])

    def test_all_28_assembly_cases_remain_unqualified_without_temperature_results(self):
        result = self.study()
        self.assertFalse(result['conditional_pass'])
        for design in ('wide', 'narrow'):
            self.assertEqual(len(result['designs'][design]['cases']), 14)
            self.assertGreater(result['designs'][design]['missing_transfer_coefficients'], 0)
            for case in result['designs'][design]['cases'].values():
                self.assertFalse(case['pass'])
                self.assertEqual(case['bounded_temperature_upper_c'], {})
                self.assertGreater(case['unbounded_heat_count'], 0)
                self.assertIn('complete_circuit_state', case['unresolved_premises'])

    def test_reference_and_premise_edits_cannot_fill_missing_assembly_evidence(self):
        self.spec['candidate']['reference_output_w'] = 0
        for design in self.definition['designs'].values():
            for case in design['states'].values():
                case['premises'] = dict.fromkeys(case['premises'], True)
        self.assertFalse(self.study()['conditional_pass'])

    def test_missing_states_designs_and_part_ownership_are_errors(self):
        for edit in ['state', 'design', 'duplicate', 'combined']:
            with self.subTest(edit=edit):
                self.setUp()
                if edit == 'state':
                    del self.definition['designs']['narrow']['states']['reversed_cell']
                elif edit == 'design':
                    del self.definition['designs']['wide']
                elif edit == 'duplicate':
                    self.candidate['nets']['GND'].append('U4.VIN')
                else:
                    del self.harness['segments']['s1']
                with self.assertRaises(ValueError):
                    self.study()

    def test_heat_and_matrix_dimensions_cannot_omit_a_part(self):
        for edit in ['power', 'row', 'coefficient']:
            with self.subTest(edit=edit):
                self.setUp()
                groups = heat_ownership(self.candidate, self.harness)
                if edit == 'power':
                    self.definition['designs']['wide']['states']['normal']['heat_upper_w'] = {'part:U4': 1}
                else:
                    observers = {asset for group in groups.values() for asset in group}
                    z = {key: dict.fromkeys(groups) for key in [*observers, 'front_surface', 'rear_skin_surface']}
                    if edit == 'row':
                        del z['rear_skin_surface']
                    else:
                        del z['rear_skin_surface']['part:U4']
                    self.definition['designs']['wide']['transfer_upper_k_per_w'] = z
                with self.assertRaises(ValueError):
                    self.study()

    def test_sourced_temperature_limit_cannot_be_relaxed_or_removed(self):
        for value in [None, 126, 150]:
            with self.subTest(value=value):
                self.definition['designs']['wide']['temperature_limits_c']['part:U1'] = value
                with self.assertRaises(ValueError):
                    self.study()

    def synthetic_bounds(self):
        groups = heat_ownership(self.candidate, self.harness)
        # Synthetic complete matrix and power bounds exercise the gate only.
        # These values are not supplied to the assembly definition on disk.
        for assembly in self.definition['designs'].values():
            assembly['boundary_upper_c'] = 25
            assembly['boundary_lower_c'] = 25
            observers = {asset for group in groups.values() for asset in group}
            assembly['transfer_upper_k_per_w'] = {
                key: dict.fromkeys(groups, 1) for key in [*observers, 'front_surface', 'rear_skin_surface']}
            assembly['temperature_limits_c'] = dict.fromkeys(assembly['transfer_upper_k_per_w'], 100)
            assembly['temperature_min_limits_c'] = dict.fromkeys(assembly['transfer_upper_k_per_w'], -40)
            for bounds in assembly['states'].values():
                bounds['initial_upper_c'] = 25
                bounds['initial_lower_c'] = 25
                bounds['heat_upper_w'] = dict.fromkeys(groups, .01)
                bounds['cooling_upper_w'] = dict.fromkeys(groups, 0)
                bounds['premises'] = dict.fromkeys(bounds['premises'], True)

    def test_thermal_prediction_does_not_prove_circuit_state(self):
        self.synthetic_bounds()
        self.assertTrue(self.study()['conditional_pass'])
        self.definition['designs']['narrow']['states']['charged_capacitors']['premises']['complete_circuit_state'] = None
        self.assertFalse(self.study()['conditional_pass'])

    def test_cold_start_cannot_pass_only_because_it_is_below_hot_limit(self):
        self.synthetic_bounds()
        assembly = self.definition['designs']['narrow']
        assembly['boundary_lower_c'] = -45
        assembly['states']['startup']['initial_lower_c'] = -45
        case = self.study()['designs']['narrow']['cases']['startup']
        self.assertFalse(case['pass'])
        self.assertEqual(case['bounded_temperature_lower_c']['part:U1'], -45)
        self.assertEqual(case['bounded_temperature_lower_margin_c']['part:U1'], -5)
        assembly['boundary_lower_c'] = -40
        assembly['states']['startup']['initial_lower_c'] = -40
        self.assertTrue(self.study()['designs']['narrow']['cases']['startup']['pass'])

    def test_unknown_cooling_cannot_be_assumed_zero(self):
        self.synthetic_bounds()
        self.definition['designs']['wide']['states']['normal']['cooling_upper_w']['part:cell'] = None
        self.assertFalse(self.study()['conditional_pass'])

    def test_missing_cold_boundary_initial_or_part_limit_fails(self):
        for field in ('boundary_lower_c', 'initial_lower_c', 'temperature_min_limits_c'):
            with self.subTest(field=field):
                self.synthetic_bounds()
                assembly = self.definition['designs']['wide']
                if field == 'initial_lower_c':
                    assembly['states']['normal'][field] = None
                elif field == 'temperature_min_limits_c':
                    del assembly[field]['part:cell']
                else:
                    assembly[field] = None
                self.assertFalse(self.study()['conditional_pass'])

    def test_sourced_minimum_operating_temperature_cannot_be_relaxed(self):
        self.synthetic_bounds()
        for value in (None, -41):
            with self.subTest(value=value):
                self.definition['designs']['wide']['temperature_min_limits_c']['part:U1'] = value
                with self.assertRaises(ValueError):
                    self.study()
