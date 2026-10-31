"""OFF-envelope and circuit ownership regressions; no physical qualification."""

import copy
import json
import math
from pathlib import Path
import unittest

from electrical import reset_netlist, reset_study
from electrical_reset import continuous_off_seconds, off_envelope


def rail(resistance=1000, capacitance=.001, incoming=0, initial=5):
    return dict(resistance_max_ohm=resistance, capacitance_max_f=capacitance,
                incoming_max_a=incoming, initial_max_v=initial)


class OffEnvelopeTests(unittest.TestCase):
    def bound(self, rails, seconds, target=.1, **kwargs):
        settings = dict(sources_disconnected=True, passive_transfer_only=True)
        settings.update(kwargs)
        return off_envelope(rails, target, seconds, **settings)

    def test_single_rail_matches_exact_rc_solution_with_ingress(self):
        result = self.bound({'supply': rail(incoming=.00001)}, 4)
        self.assertAlmostEqual(result['floor_v'], .01)
        self.assertAlmostEqual(result['voltage_upper_v'], .01 + 4.99 * math.exp(-4))
        self.assertAlmostEqual(result['required_off_s'], math.log(4.99/.09))
        self.assertFalse(result['below_target'])
        self.assertTrue(self.bound({'supply': rail(incoming=.00001)}, 4.1)['below_target'])

    def test_charge_transfer_into_small_capacitor_cannot_use_its_isolated_decay(self):
        rails = {'retained': rail(), 'controller': rail(1000, .000001, initial=0)}
        # Short the two rails at t=0: charge is conserved, then both resistors
        # drain the combined capacitance. This is an independent exact solution.
        joined_initial = .001 * 5 / .001001
        joined_tau = 500 * .001001
        for time in (.001, .01, .1, 1, 3, 5):
            with self.subTest(time=time):
                exact = joined_initial * math.exp(-time / joined_tau)
                self.assertLessEqual(exact, self.bound(rails, time)['voltage_upper_v'])
        self.assertGreater(joined_initial * math.exp(-.1 / joined_tau), 4)
        # The controller's initially empty capacitor does not imply reset while
        # a retained rail can replenish it.
        self.assertFalse(self.bound(rails, .1)['below_target'])

    def test_different_rail_can_set_each_extremum(self):
        rails = {'slow': rail(2000, .003, initial=2),
                 'leaky': rail(5000, .000001, incoming=.00001, initial=0),
                 'charged': rail(100, .00001, initial=6)}
        result = self.bound(rails, 7)
        self.assertEqual(result['time_constant_s'], 6)
        self.assertEqual(result['floor_v'], .05)
        self.assertAlmostEqual(result['voltage_upper_v'], .05 + 5.95 * math.exp(-7/6))

    def test_leakage_equilibrium_at_target_is_unreachable_even_after_underflow(self):
        result = self.bound({'supply': rail(incoming=.0001)}, 1e9)
        self.assertIsNone(result['required_off_s'])
        self.assertFalse(result['below_target'])
        self.assertEqual(result['voltage_upper_v'], .1)

    def test_initially_discharged_rail_can_be_recharged_by_ingress(self):
        result = self.bound({'supply': rail(incoming=.001, initial=0)}, 0)
        self.assertIsNone(result['required_off_s'])
        self.assertFalse(result['below_target'])
        self.assertEqual(result['voltage_upper_v'], 1)

    def test_exact_threshold_is_not_strictly_below(self):
        rails = {'supply': rail(initial=.1)}
        self.assertFalse(self.bound(rails, 0)['below_target'])
        self.assertTrue(self.bound(rails, .001)['below_target'])
        rails['supply']['initial_max_v'] = .09
        self.assertTrue(self.bound(rails, 0)['below_target'])

    def test_longer_time_does_not_certify_unknown_or_active_paths(self):
        for premise in ('sources_disconnected', 'passive_transfer_only'):
            for value in (None, False):
                with self.subTest(premise=premise, value=value):
                    result = self.bound({'supply': rail()}, 1e6, **{premise: value})
                    self.assertEqual(result['status'], 'unbounded')
                    self.assertIn(premise, result['missing'])
                    self.assertIsNone(result['required_off_s'])
                    self.assertFalse(result['below_target'])
        for key in rail():
            changed = rail()
            changed[key] = None
            result = self.bound({'supply': changed}, 1e6)
            self.assertIn('supply.' + key, result['missing'])
            self.assertIsNone(result['voltage_upper_v'])

    def test_unknown_does_not_mask_invalid_data(self):
        for key in rail():
            for value in (-1, True, float('nan'), float('inf')):
                with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                    self.bound({'supply': dict(rail(), **{key: value})}, 5,
                               sources_disconnected=None)
        for key in ('resistance_max_ohm', 'capacitance_max_f'):
            with self.assertRaises(ValueError):
                self.bound({'supply': dict(rail(), **{key: 0})}, 5)
        with self.assertRaises(ValueError):
            self.bound({}, 5)
        with self.assertRaises(ValueError):
            self.bound({'supply': rail()}, 5, passive_transfer_only=1)

    def test_bounce_and_usb_reset_continuous_dwell_without_summing_intervals(self):
        off = lambda time: dict(time_s=time, switch='OFF', external_source=False)
        events = [off(0), dict(time_s=3, switch='ON', external_source=False), off(3.01)]
        self.assertAlmostEqual(continuous_off_seconds(events, 5), 1.99)
        self.assertFalse(self.bound({'supply': rail()}, continuous_off_seconds(events, 5))['below_target'])
        events += [off(4), dict(time_s=4.1, switch='OFF', external_source=True), off(4.2)]
        self.assertAlmostEqual(continuous_off_seconds(events, 5), .8)
        events += [dict(time_s=4.9, switch='unknown', external_source=False)]
        self.assertEqual(continuous_off_seconds(events, 5), 0)
        self.assertEqual(continuous_off_seconds([off(0), off(4)], 5), 5)
        for invalid in ([off(1), off(1)], [off(2), off(1)], [off(6)]):
            with self.assertRaises(ValueError):
                continuous_off_seconds(invalid, 5)


class ResetRevisionTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        self.spec, self.control, self.interlock, self.revision = (
            json.loads((root / name).read_text()) for name in (
                'electrical-review.json', 'electrical-control-revision.json',
                'electrical-boost-interlock.json', 'electrical-reset-revision.json'))

    def calculate(self):
        return reset_study(self.spec, self.control, self.interlock, self.revision)

    def test_composed_candidate_keeps_both_repairs_and_all_unrelated_branches(self):
        original = copy.deepcopy(self.spec)
        candidate = reset_netlist(self.spec, self.control, self.interlock, self.revision)
        self.assertEqual(self.spec, original)
        nets = candidate['nets']
        self.assertEqual(set(nets['BOOST_ENABLE']), {'U6.6', 'U4.ENABLE', 'S1.CLAMP_COMMON'})
        self.assertIn('U1.PG', nets['PG_SENSE'])
        self.assertEqual(set(nets['CONTROLLER_EN']), {'U3.EN', 'U5.2', 'R_EN_PULLUP.2'})
        self.assertEqual(set(nets['EFUSE_EN']), {'R_UV_TOP.2', 'R_UV_BOTTOM.1', 'U1.EN_UVLO'})
        self.assertIn('U2.CE', nets['GND'])
        self.assertIn('R_C_BLEED.1', nets['C'])
        self.assertIn('R_B_BLEED.1', nets['B'])
        self.assertIn('C_U6.1', nets['B'])
        for name in ('CELL_POS', 'FUSED', 'A', 'ILM', 'DVDT', 'PGTH', 'FIVE_V', 'OFF_DRAIN'):
            self.assertEqual(nets[name], original['candidate']['nets'][name])
        self.assertIn('BatterySense.supply', nets['B'])
        self.assertIn('BatterySense.return', nets['GND'])
        pins = [pin for group in nets.values() for pin in group] + candidate['open_pins']
        self.assertEqual(len(pins), len(set(pins)))
        self.assertFalse(any(pin.startswith(('R_EN_TOP.', 'R_EN_BOTTOM.')) for pin in pins))
        self.assertEqual(candidate['resistors_ohm']['R_OUT'], 470)

    def test_bypassing_switch_moving_drain_or_duplicating_pin_fails(self):
        for pin, old, new in (('S1.OFF', 'OFF_DRAIN', 'FUSED'), ('U2.CE', 'GND', 'C')):
            changed = copy.deepcopy(self.spec)
            changed['candidate']['nets'][old].remove(pin)
            changed['candidate']['nets'][new].append(pin)
            with self.subTest(pin=pin), self.assertRaisesRegex(ValueError, 'power connection'):
                reset_netlist(changed, self.control, self.interlock, self.revision)
        self.spec['candidate']['nets']['B'].append('U3.EN')
        with self.assertRaisesRegex(ValueError, 'duplicate pin'):
            self.calculate()
        self.setUp()
        self.revision['nets']['C'].remove('R_C_BLEED.1')
        self.revision['nets']['B'].append('R_C_BLEED.1')
        with self.assertRaisesRegex(ValueError, 'netlist disagrees'):
            self.calculate()

    def test_reference_drains_but_real_assembly_remains_unbounded(self):
        result = self.calculate()
        self.assertAlmostEqual(result['reference_case']['required_off_s'], 2.735660391108557)
        self.assertTrue(result['reference_case']['below_target'])
        self.assertTrue(all(row['within_p70'] for row in result['reference_bleeder_power'].values()))
        self.assertIsNone(result['assembly']['required_off_s'])
        self.assertFalse(result['qualified'])
        self.assertEqual(result['controller_uvlo_falling_min_v'], .8)
        self.assertEqual(result['startup_lockout_after_reapplication_s'], [.6, 1.4])
        self.assertAlmostEqual(result['added_c_bleeder_a_at_nominal_c'], 3.7/4700)
        self.assertAlmostEqual(result['added_c_bleeder_wh_per_day_at_nominal_c'], 3.7**2/4700*24)

    def test_more_capacitance_or_ingress_can_invalidate_five_seconds(self):
        self.revision['reference_case']['rails']['FIVE_V']['capacitance_max_f'] = .004
        self.assertFalse(self.calculate()['reference_case']['below_target'])
        self.setUp()
        self.revision['reference_case']['rails']['C']['incoming_max_a'] = .0001
        self.assertIsNone(self.calculate()['reference_case']['required_off_s'])
        self.assertFalse(self.calculate()['reference_case']['below_target'])

    def test_restart_lockout_cannot_be_spent_while_power_is_absent(self):
        before = self.calculate()
        self.revision['controller']['startup_lockout_s'] = [2, 3]
        after = self.calculate()
        self.assertEqual(after['reference_case'], before['reference_case'])
        self.assertEqual(after['startup_lockout_after_reapplication_s'], [2, 3])

    def test_capacitor_ownership_includes_control_nodes_and_unknown_reservoir(self):
        caps = self.calculate()['external_capacitors']
        self.assertEqual(set(caps), {'C_A', 'C_B_CERAMIC', 'C_B_BULK', 'C_C', 'C_OUT',
                                     'C_KILL', 'C_DVDT', 'C_U5', 'C_U6'})
        self.assertEqual(caps['C_KILL']['node'], 'KILL')
        self.assertEqual(caps['C_DVDT']['node'], 'DVDT')
        self.assertIsNone(caps['C_B_CERAMIC']['nominal_f'])
        self.assertEqual(self.calculate()['output_reservoir_initial_max_f'], .0012)

    def test_source_part_changes_cannot_silently_reuse_original_bounds(self):
        self.revision['resistors']['R_OUT']['ohm'] = 100
        with self.assertRaisesRegex(ValueError, 'BOM/model mismatch'):
            self.calculate()
        self.setUp()
        self.spec['candidate']['capacitors_nominal_f']['C_OUT'] = .002
        with self.assertRaisesRegex(ValueError, 'nominal capacitance'):
            self.calculate()
        self.setUp()
        self.revision['reference_case']['rails']['FIVE_V']['capacitance_max_f'] = .001
        with self.assertRaisesRegex(ValueError, 'omits part'):
            self.calculate()

    def test_missing_required_inputs_cannot_be_deleted_to_claim_recovery(self):
        self.revision['remaining_evidence'] = []
        self.assertFalse(self.calculate()['qualified'])
        self.assertIsNone(self.calculate()['assembly']['required_off_s'])
        del self.revision['assembly_bounds']['rails']['C']
        with self.assertRaisesRegex(ValueError, 'all four rails'):
            self.calculate()


if __name__ == '__main__':
    unittest.main()
