"""Independent numerical checks and regressions for candidate rejection."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from electrical import control_study, discharge_time, divider_thresholds, loaded_voltage, review


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


if __name__ == '__main__':
    unittest.main()
