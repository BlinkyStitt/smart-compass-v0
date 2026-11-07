"""Independent RC solutions and dynamic cutoff-order regressions."""

import copy
import json
import math
from pathlib import Path
import unittest

from electrical import schmitt_control_study
from electrical_control import cutoff_order_bound, ramp_crossing


class KillRampTests(unittest.TestCase):
    def test_ramp_crossing_matches_independent_nodal_integration(self):
        # Rtop=Rbottom=2, C=1: dV/dt = U/2 - V - I. Integrate the
        # circuit equation, independently of the closed-form crossing solver.
        result = ramp_crossing(2, 2, 1, .1, .9, 4, 1, 3)
        voltage, elapsed, dt = 1.9, 0.0, .0001
        def derivative(t, v):
            return max(1, 4-t)/2 - v - .1
        while voltage > .9:
            a = derivative(elapsed, voltage)
            b = derivative(elapsed + dt/2, voltage + dt*a/2)
            c = derivative(elapsed + dt/2, voltage + dt*b/2)
            d = derivative(elapsed + dt, voltage + dt*c)
            voltage += dt*(a + 2*b + 2*c + d)/6
            elapsed += dt
        self.assertLessEqual(abs(result['crossing_s'] - elapsed), dt)
        self.assertAlmostEqual(result['tau_s'], 1)

    def test_crossing_after_ramp_uses_exponential_tail(self):
        result = ramp_crossing(2, 2, 1, 0, .6, 4, 1, .1)
        end = .5 + 15 * (1-math.exp(-.1))
        self.assertAlmostEqual(result['pin_at_ramp_end_v'], end)
        self.assertAlmostEqual(result['crossing_s'], .1 + math.log((end-.5)/.1))
        self.assertEqual(result['rail_at_crossing_v'], 1)

    def test_rapid_fall_retains_charge_and_does_not_become_dc(self):
        result = ramp_crossing(2, 2, 1, 0, 1, 4, 1, 1e-12)
        self.assertAlmostEqual(result['pin_at_ramp_end_v'], 2)
        self.assertAlmostEqual(result['crossing_s'], math.log(3), places=10)
        slow = ramp_crossing(2, 2, 1, 0, 1, 4, 1, 1e6)
        self.assertAlmostEqual(slow['rail_at_crossing_v'], 2 - 3e-6, places=9)

    def test_leakage_direction_and_capacitance_change_crossing(self):
        baseline = ramp_crossing(2, 2, 1, 0, 1, 4, 1, 1)['crossing_s']
        self.assertGreater(ramp_crossing(2, 2, 2, 0, 1, 4, 1, 1)['crossing_s'], baseline)
        self.assertGreater(ramp_crossing(2, 2, 1, -.1, 1, 4, 1, 1)['crossing_s'], baseline)
        self.assertLess(ramp_crossing(2, 2, 1, .1, 1, 4, 1, 1)['crossing_s'], baseline)

    def test_asymptotic_equality_is_not_a_crossing(self):
        self.assertIsNone(ramp_crossing(2, 2, 1, 0, .5, 4, 1, 1)['crossing_s'])
        self.assertEqual(ramp_crossing(2, 2, 1, 0, 2, 4, 1, 1)['crossing_s'], 0)

    def test_invalid_operating_points_and_nonfinite_inputs_fail(self):
        args = [2, 2, 1, 0, 1, 4, 1, 1]
        for index in range(len(args)):
            for value in (True, float('nan'), float('inf')):
                changed = args.copy()
                changed[index] = value
                with self.subTest(index=index, value=value), self.assertRaises(ValueError):
                    ramp_crossing(*changed)
        for index in (0, 1, 2, 4, 7):
            changed = args.copy()
            changed[index] = 0
            with self.assertRaises(ValueError):
                ramp_crossing(*changed)
        with self.assertRaises(ValueError):
            ramp_crossing(2, 2, 1, 1, 1, 4, 1, 1)
        with self.assertRaises(ValueError):
            ramp_crossing(2, 2, 1, 0, 1, 4, 4, 1)

    def test_order_bound_includes_filter_charge_response_and_blanking(self):
        result = cutoff_order_bound(4, 3, .1, 2, .1, .2, .1)
        self.assertAlmostEqual(result['dynamic_loss_max_v'], .9)
        self.assertAlmostEqual(result['margin_v'], .1)
        self.assertTrue(result['conditional_pass'])
        self.assertFalse(cutoff_order_bound(4, 3, .1, 2, .1, .2, .2)['conditional_pass'])
        # Equality offers no guaranteed ordering margin.
        self.assertFalse(cutoff_order_bound(4, 3, 1, 1, 0, 0, 0)['conditional_pass'])

    def test_missing_bound_is_not_zero_even_with_no_decline(self):
        for index in range(7):
            args = [4, 3, .1, 0, 0, 0, 0]
            args[index] = None
            result = cutoff_order_bound(*args)
            self.assertFalse(result['conditional_pass'])
            self.assertIsNone(result['margin_v'])
        with self.assertRaises(ValueError):
            cutoff_order_bound(4, 3, 1e308, 1e308, 0, 0, 0)


class ComposedControlRampTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        self.spec = json.loads((root/'electrical-review.json').read_text())
        self.control = json.loads((root/'electrical-control-revision.json').read_text())

    def calculate(self):
        return schmitt_control_study(self.spec, self.control)

    def test_static_order_is_insufficient_for_fast_and_blanked_falls(self):
        result = self.calculate()
        self.assertTrue(result['conditional_cutoff_order_pass'])
        ramp = result['ramp_response']
        profiles = ramp['conditional_profiles']
        self.assertTrue(profiles['slow_decline']['conditional_order_pass'])
        self.assertFalse(profiles['fast_decline']['conditional_order_pass'])
        self.assertFalse(profiles['startup_decline']['conditional_order_pass'])
        self.assertLess(profiles['fast_decline']['rail_minus_backup_max_v'], 0)
        self.assertGreater(profiles['startup_decline']['controller_release_upper_s'], .72)
        self.assertFalse(ramp['qualified'])
        for row in ramp['assembly_order_bounds'].values():
            self.assertFalse(row['conditional_pass'])
            self.assertEqual(len(row['missing']), 5)

    def test_design_bounds_are_independent_and_do_not_inherit_example_values(self):
        self.control['ramp_study']['designs']['wide'] = dict(
            kill_capacitance_max_f=1e-8, slew_max_v_per_s=1, initial_excess_v=0,
            response_max_s=.001, blanking_remaining_s=0)
        result = self.calculate()
        rows = result['ramp_response']['assembly_order_bounds']
        self.assertTrue(rows['wide']['conditional_pass'])
        self.assertFalse(rows['narrow']['conditional_pass'])
        self.assertFalse(result['qualified'])
        self.assertFalse(result['ramp_response']['qualified'])

    def test_part_values_are_consumed_without_silent_nominal_fallback(self):
        baseline = self.calculate()['ramp_response']
        self.control['capacitors']['C_KILL']['nominal_f'] *= 10
        larger = self.calculate()['ramp_response']
        self.assertAlmostEqual(larger['nominal_capacitance_tau_max_s'],
                               10 * baseline['nominal_capacitance_tau_max_s'])
        self.assertLess(larger['conditional_profiles']['fast_decline']['rail_minus_backup_max_v'],
                        baseline['conditional_profiles']['fast_decline']['rail_minus_backup_max_v'])
        self.control['capacitors']['C_KILL']['nominal_f'] = None
        with self.assertRaises(ValueError):
            self.calculate()

    def test_overloaded_driver_cannot_inherit_dynamic_order_pass(self):
        for name, part in [('R_UV_TOP', 'TNPW06035K11BEEA'), ('R_UV_BOTTOM', 'TNPW06032K55BEEA')]:
            self.control['resistors'][name]['ohm'] /= 10
            self.control['resistors'][name]['part'] = part
        result = self.calculate()['ramp_response']
        self.assertFalse(result['static_driver_limits_pass'])
        self.assertTrue(all(not row['conditional_order_pass']
                            for row in result['conditional_profiles'].values()))

    def test_missing_design_and_excess_blanking_fail(self):
        saved = copy.deepcopy(self.control)
        del self.control['ramp_study']['designs']['wide']
        with self.assertRaises(ValueError):
            self.calculate()
        self.control = saved
        self.control['ramp_study']['profiles']['startup_decline']['blanking_remaining_s'] = 1.4
        with self.assertRaises(ValueError):
            self.calculate()
