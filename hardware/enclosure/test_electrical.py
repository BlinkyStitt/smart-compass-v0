"""Independent numerical checks and regressions for candidate rejection."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from electrical import (control_study, discharge_time, divider_thresholds, driven_divider_edges,
                        loaded_voltage, resistor_bounds, review, schmitt_control_study)


class ElectricalReviewTests(unittest.TestCase):
    def setUp(self):
        self.spec = json.loads((Path(__file__).parent/'electrical-review.json').read_text())

    def test_divider_kcl_and_leakage_sign(self):
        self.assertEqual(divider_thresholds(2000, 1000, 0, [1, 1], [0, 0]), [3, 3])
        self.assertEqual(divider_thresholds(2000, 1000, 0, [1, 1], [.001, .001]), [5, 5])
        self.assertEqual(divider_thresholds(2000, 1000, 0, [1, 1], [-.001, -.001]), [1, 1])

    def test_resistor_extrema_are_not_rounded(self):
        values = divider_thresholds(2000, 1000, .1, [1, 1], [0, 0])
        self.assertAlmostEqual(values[0], 1+1800/1100)
        self.assertAlmostEqual(values[1], 1+2200/900)

    def test_constant_power_quadratic_conserves_power(self):
        voltage = loaded_voltage(4, .1, 5)
        current = 5/voltage
        self.assertAlmostEqual(4-current*.1, voltage)
        self.assertAlmostEqual(current*4, 5+current**2*.1)
        self.assertEqual(loaded_voltage(4, 0, 5), 4)
        self.assertIsNone(loaded_voltage(1, 1, 1))

    def test_invalid_values_fail(self):
        for value in [float('nan'), float('inf'), -1, True]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                loaded_voltage(value, .1, 5)
        with self.assertRaises(ValueError):
            divider_thresholds(1, 1, 1, [1, 1], [0, 0])
        with self.assertRaises(ValueError):
            divider_thresholds(1, 1, 0, [2, 1], [0, 0])
        for value in [float('nan'), float('inf'), 0, -1, True]:
            changed = copy.deepcopy(self.spec)
            changed['candidate']['reference_efficiency'] = value
            with self.subTest(efficiency=value), self.assertRaises(ValueError):
                review(changed)

    def test_proposal_reproduces_known_corners(self):
        result = review(self.spec)
        values = result['calculated']
        self.assertAlmostEqual(values['reference_runtime_h'], 2.61664)
        self.assertAlmostEqual(values['kill_threshold_c_v'][0], 3.2012963198801208)
        self.assertAlmostEqual(values['kill_threshold_c_v'][1], 3.583264848648648)
        self.assertAlmostEqual(values['conditional_backup_uvlo_c_v'][0], 2.935884886733267)
        self.assertLess(values['conditional_boost_input_at_uvlo_v'], 2.82)
        self.assertGreater(values['conditional_boost_input_at_uvlo_v'], 2.81)
        ids = {failure['id'] for failure in result['failures']}
        self.assertIn('startup-boost-headroom', ids)
        self.assertIn('unpowered-pg-disable', ids)
        self.assertIn('fault-energy-coordination', ids)
        self.assertIn('reset-and-recovery', ids)

    def test_threshold_change_cannot_approve_unmodeled_circuit(self):
        changed = copy.deepcopy(self.spec)
        changed['candidate']['resistors_ohm']['R_EN_TOP'] = 19600
        result = review(changed)
        self.assertGreater(result['calculated']['conditional_boost_input_at_uvlo_v'], 2.9)
        self.assertEqual(result['status'], 'rejected-before-compartment-freeze')
        self.assertIn('state-and-thermal-qualification', {r['id'] for r in result['failures']})

    def test_cli_rejects_candidate_even_when_calculations_run(self):
        result = subprocess.run([sys.executable, str(Path(__file__).with_name('electrical.py')), 'check'],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('ELECTRICAL CHECK FAILED', result.stdout)
        self.assertNotIn('NaN', result.stdout)

    def test_discharge_includes_leakage_and_unreachable_targets(self):
        import math
        self.assertAlmostEqual(discharge_time(5, .1, 1000, .001, 0), math.log(50))
        self.assertGreater(discharge_time(5, .1, 1000, .001, .00001), math.log(50))
        self.assertIsNone(discharge_time(5, .1, 1000, .001, .0001))
        self.assertEqual(discharge_time(.1, .1, 1000, .001, 0), 0)
        for value in [float('nan'), float('inf'), -1]:
            with self.assertRaises(ValueError):
                discharge_time(5, .1, 1000, .001, value)

    def test_isolated_divider_repairs_static_boundary_but_not_dynamic_gate(self):
        study = json.loads((Path(__file__).parent/'electrical-control-study.json').read_text())
        result = control_study(self.spec, study)
        self.assertTrue(result['static_headroom_pass'])
        self.assertTrue(result['static_cutoff_order_pass'])
        self.assertFalse(result['buffer_transition_pass'])
        self.assertGreater(result['optimistic_buffer_input_transition_s_per_v'], 3e-8)
        self.assertFalse(result['off_dwell_qualified'])
        self.assertGreater(result['conditional_discharge']['FIVE_V']['decay_plus_lockout_s'], 5)
        self.assertAlmostEqual(result['additional_c_bleeder_a_at_nominal_c'], .0037)
        self.assertAlmostEqual(result['additional_c_bleeder_wh_per_day_at_nominal_c'], .32856)

    def test_discharge_study_cannot_qualify_dwell_by_editing_a_capacitor(self):
        study = json.loads((Path(__file__).parent/'electrical-control-study.json').read_text())
        study['discharge_candidate']['rails']['FIVE_V']['nominal_f'] = .000001
        result = control_study(self.spec, study)
        self.assertLess(result['conditional_discharge']['FIVE_V']['decay_plus_lockout_s'], 5)
        self.assertFalse(result['off_dwell_qualified'])


class SchmittControlRevisionTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        self.spec = json.loads((root/'electrical-review.json').read_text())
        self.revision = json.loads((root/'electrical-control-revision.json').read_text())

    def calculate(self):
        return schmitt_control_study(self.spec, self.revision)

    def test_driver_drop_is_added_after_divider_not_multiplied_by_gain(self):
        self.assertEqual(driven_divider_edges([2000, 2000], [1000, 1000], [1, 1],
                                              [0, 0], [0, .1]), [3, 3.1])
        self.assertEqual(driven_divider_edges([2000, 2000], [1000, 1000], [1, 1],
                                              [-.001, .001], [0, .1]), [1, 5.1])

    def test_temperature_and_absolute_drift_terms_widen_resistance_bounds(self):
        model = self.revision['resistor_model']
        # 0.4825% (including 65 K from the 20 C reference) plus 0.04 ohm.
        self.assertEqual(resistor_bounds(10000, model), [9951.71, 10048.29])
        fresh = dict(model, film_temperature_c=[20, 20], endurance_relative=0,
                     endurance_absolute_ohm=0, solder_relative=0,
                     solder_absolute_ohm=0, humidity_relative=0, humidity_absolute_ohm=0)
        self.assertEqual(resistor_bounds(10000, fresh), [9990, 10010])

    def test_control_corners_include_output_error_and_all_resistor_allowances(self):
        result = self.calculate()
        self.assertAlmostEqual(result['conditional_uvlo_falling_c_v'][0], 3.2064216491036404)
        self.assertAlmostEqual(result['conditional_uvlo_falling_c_v'][1], 3.479202114934923)
        self.assertAlmostEqual(result['conditional_kill_c_v'][0], 3.505529286308437)
        self.assertAlmostEqual(result['conditional_boost_input_v'], 2.957829158368792)
        self.assertTrue(result['conditional_headroom_pass'])
        self.assertTrue(result['conditional_cutoff_order_pass'])
        # The remaining static margin is small; do not imply a transient proof.
        self.assertLess(result['conditional_cutoff_order_margin_v'], .027)
        self.assertGreater(result['conditional_cutoff_order_margin_v'], .026)
        self.assertFalse(result['qualified'])

    def test_legacy_controller_pullup_does_not_affect_revised_divider(self):
        result = self.calculate()
        self.spec['limits']['controller_en_pullup_a_at_zero_v'] = [0, .01]
        self.assertEqual(self.calculate(), result)

    def test_driver_loading_cannot_be_ignored_by_preserving_divider_ratio(self):
        for name, part in [('R_UV_TOP', 'TNPW06035K11BEEA'), ('R_UV_BOTTOM', 'TNPW06032K55BEEA')]:
            self.revision['resistors'][name]['ohm'] /= 10
            self.revision['resistors'][name]['part'] = part
        result = self.calculate()
        self.assertGreater(result['buffer_load_max_a'], .0001)
        self.assertFalse(result['buffer_load_within_characterized_current'])
        self.assertFalse(result['conditional_headroom_pass'])
        self.assertFalse(result['conditional_cutoff_order_pass'])
        self.assertFalse(result['conditional_disabled_efuse_pass'])

    def test_pullup_can_overload_controller_even_with_working_divider(self):
        self.revision['resistors']['R_EN_PULLUP'] = {'ohm': 1000, 'part': 'TNPW06031K00BEEA'}
        result = self.calculate()
        self.assertGreater(result['external_controller_pullup_max_a_at_zero_v'], .001)
        self.assertFalse(result['controller_external_pullup_rule_pass'])

    def test_rated_output_current_and_low_level_are_both_checked(self):
        result = self.calculate()
        self.assertTrue(result['buffer_load_within_characterized_current'])
        self.assertLess(result['buffer_load_max_a'], .000057)
        self.assertTrue(result['controller_external_pullup_rule_pass'])
        self.assertLess(result['conditional_disabled_efuse_en_max_v'], .036)
        self.assertTrue(result['conditional_disabled_efuse_pass'])
        self.revision['buffer_limits']['low_max_v'] = 4
        self.assertFalse(self.calculate()['conditional_disabled_efuse_pass'])

    def test_logic_table_does_not_hide_low_supply_failure_or_interpolate(self):
        rows = self.calculate()['tabulated_logic_margins']
        self.assertEqual([row['supply_v'] for row in rows], [1.65, 2.3, 3.0, 4.5, 5.5])
        self.assertFalse(rows[0]['pass'])
        self.assertAlmostEqual(rows[0]['low_margin_v'], -.05)
        self.assertTrue(all(row['pass'] for row in rows[1:]))
        self.revision['buffer_limits']['input_leakage_abs_a'] = .001
        self.assertTrue(all(not row['pass'] for row in self.calculate()['tabulated_logic_margins']))

    def test_reconnecting_controller_or_bypassing_divider_fails_model_binding(self):
        for pin, old, new in [('U3.EN', 'CONTROLLER_EN', 'EFUSE_EN'),
                              ('U5.4', 'BUFFER_OUT', 'EFUSE_EN'),
                              ('R_UV_TOP.1', 'BUFFER_OUT', 'C')]:
            with self.subTest(pin=pin):
                revision = copy.deepcopy(self.revision)
                revision['nets'][old].remove(pin)
                revision['nets'][new].append(pin)
                with self.assertRaisesRegex(ValueError, 'netlist disagrees'):
                    schmitt_control_study(self.spec, revision)
        self.revision['nets']['EFUSE_EN'].append('U1.EN_UVLO')
        with self.assertRaisesRegex(ValueError, 'netlist disagrees'):
            self.calculate()

    def test_wrong_logic_polarity_cannot_reuse_corner_equations(self):
        self.revision['controller'] = 'LTC2955ITS8-2#TRMPBF'
        with self.assertRaisesRegex(ValueError, 'topology'):
            self.calculate()

    def test_value_changes_require_a_matching_bom(self):
        self.revision['resistors']['R_UV_TOP']['ohm'] = 1000
        with self.assertRaisesRegex(ValueError, 'disagrees with BOM'):
            self.calculate()

    def test_resistance_budget_matches_independent_required_voltage_equation(self):
        result = self.calculate()
        budget = result['post_sense_resistance_budget_ohm_at_reference']
        current = (6.25/.85)/2.9
        self.assertAlmostEqual(2.9 + current * budget, result['conditional_uvlo_falling_c_v'][0])
        self.revision['conditional_path']['post_sense_resistance_ohm'] = budget + .001
        self.assertFalse(self.calculate()['conditional_headroom_pass'])

    def test_resistor_only_fix_never_certifies_startup_or_system(self):
        self.revision['conditional_path']['post_sense_resistance_ohm'] = 0
        self.revision['unqualified'] = []
        result = self.calculate()
        self.assertFalse(result['qualified'])
        # Historical rejection remains; no partial study can change the gate.
        self.assertIn('reset-and-recovery', {row['id'] for row in review(self.spec)['failures']})

    def test_malformed_numeric_inputs_cannot_produce_a_passing_result(self):
        for value in [float('nan'), float('inf'), True, -1]:
            with self.subTest(value=value):
                revision = copy.deepcopy(self.revision)
                revision['resistor_model']['tcr_per_k'] = value
                with self.assertRaises(ValueError):
                    schmitt_control_study(self.spec, revision)
        self.revision['resistor_model']['initial_tolerance'] = 1
        with self.assertRaises(ValueError):
            self.calculate()


if __name__ == '__main__':
    unittest.main()
