"""Stored-charge coverage and independent analytical discharge solutions."""

import copy
import json
import math
from pathlib import Path
import unittest

from electrical import reset_netlist, reset_storage_study
from electrical_headroom import headroom_netlist
from electrical_reset import capacitor_nodes, storage_envelope


def node(capacitance=1, voltage=1, incoming=0):
    return dict(capacitance_min_f=capacitance, capacitance_max_f=capacitance,
                initial_max_v=voltage, incoming_max_a=incoming)


def drain(first, second, resistance):
    return dict(ends=[first, second], resistance_max_ohm=resistance)


class StorageEnvelopeTests(unittest.TestCase):
    def bound(self, nodes, resistors, time=5, target=.1, **overrides):
        assumptions = dict(sources_disconnected=True, passive_transfer_only=True, complete_storage=True)
        assumptions.update(overrides)
        return storage_envelope(nodes, resistors, target, time, **assumptions)

    def test_one_node_matches_exact_rc_with_ingress(self):
        result = self.bound({'C': node(.001, 5, .00001)}, {'R': drain('C', 'GND', 1000)}, time=4)
        self.assertAlmostEqual(result['initial_energy_max_j'], .0125)
        self.assertAlmostEqual(result['voltage_upper_v']['C'], .01 + 4.99 * math.exp(-4))
        self.assertAlmostEqual(result['required_off_s'], math.log(4.99 / .09))
        self.assertFalse(result['below_target'])

    def test_indirect_drain_bounds_exact_two_node_transient(self):
        # C1=C2=1 F, R12=R2G=1 ohm, initial V1=1 and V2=0.
        # Eigenvalues of the independent nodal ODE are (-3 +/- sqrt(5))/2.
        nodes = {'control': node(), 'rail': node(voltage=0)}
        resistors = {'link': drain('control', 'rail', 1), 'bleed': drain('rail', 'GND', 1)}
        for time in (0, .01, .5, 1, 5, 20):
            with self.subTest(time=time):
                result = self.bound(nodes, resistors, time=time)
                scale = math.exp(-1.5 * time)
                cosh, sinh = math.cosh(math.sqrt(5) * time / 2), math.sinh(math.sqrt(5) * time / 2)
                exact_control = scale * (cosh + sinh / math.sqrt(5))
                exact_rail = scale * 2 * sinh / math.sqrt(5)
                self.assertGreaterEqual(result['voltage_upper_v']['control'], exact_control)
                self.assertGreaterEqual(result['voltage_upper_v']['rail'], exact_rail)
                self.assertEqual(result['ground_path_max_ohm'], {'control': 2, 'rail': 1})
                self.assertEqual(result['time_constant_s'], 3)
        # An initially empty rail can charge from the control-node capacitor.
        self.assertGreater(exact_rail, 0)

    def test_capacitance_intervals_bound_each_exact_single_rail_corner(self):
        row = dict(node(.001, 5), capacitance_max_f=.002)
        for time in (0, .1, 1, 10):
            result = self.bound({'C': row}, {'R': drain('C', 'GND', 1000)}, time=time)
            for capacitance in (.001, .0015, .002):
                self.assertGreaterEqual(result['voltage_upper_v']['C'], 5 * math.exp(-time/(1000*capacitance)))

    def test_isolated_or_unknown_node_cannot_be_omitted(self):
        nodes = {'rail': node(), 'DVDT': node(.0000000047, 1)}
        resistors = {'bleed': drain('rail', 'GND', 1), 'internal': drain('DVDT', 'GND', None)}
        result = self.bound(nodes, resistors, time=1e9)
        self.assertIn('DVDT.ground_path', result['missing'])
        self.assertIsNone(result['required_off_s'])
        self.assertFalse(result['below_target'])
        resistors['internal']['resistance_max_ohm'] = 1e9
        self.assertIsNotNone(self.bound(nodes, resistors)['required_off_s'])
        nodes['DVDT']['capacitance_max_f'] = None
        self.assertIn('DVDT.capacitance_max_f', self.bound(nodes, resistors)['missing'])

    def test_extra_passive_path_can_improve_bound_without_changing_inventory(self):
        nodes = {'C': node()}
        resistors = {'slow': drain('C', 'GND', 10)}
        old = self.bound(nodes, resistors)
        resistors['fast'] = drain('C', 'GND', 1)
        self.assertLess(self.bound(nodes, resistors)['required_off_s'], old['required_off_s'])
        resistors['unknown'] = drain('C', 'GND', None)
        self.assertEqual(self.bound(nodes, resistors)['time_constant_s'], 1)

    def test_leakage_floor_equal_to_target_never_passes(self):
        result = self.bound({'C': node(incoming=.1)}, {'R': drain('C', 'GND', 1)}, time=1e9)
        self.assertIsNone(result['required_off_s'])
        self.assertFalse(result['below_target'])
        self.assertEqual(result['voltage_upper_v']['C'], .1)

    def test_exact_crossing_and_initially_empty_cases(self):
        resistors = {'R': drain('C', 'GND', 1)}
        result = self.bound({'C': node()}, resistors)
        self.assertFalse(self.bound({'C': node()}, resistors, time=result['required_off_s'])['below_target'])
        self.assertTrue(self.bound({'C': node()}, resistors, time=result['required_off_s']+.001)['below_target'])
        self.assertTrue(self.bound({'C': node(voltage=0)}, resistors, time=0)['below_target'])
        self.assertFalse(self.bound({'C': node(voltage=0, incoming=1)}, resistors, time=0)['below_target'])

    def test_missing_premises_and_malformed_data_never_produce_a_bound(self):
        for premise in ('sources_disconnected', 'passive_transfer_only', 'complete_storage'):
            for value in (None, False):
                result = self.bound({'C': node()}, {'R': drain('C', 'GND', 1)}, **{premise: value})
                self.assertIn(premise, result['missing'])
                self.assertFalse(result['below_target'])
            with self.assertRaises(ValueError):
                self.bound({'C': node()}, {'R': drain('C', 'GND', 1)}, **{premise: 1})
        for field in node():
            for value in (float('inf'), float('nan'), -1, True):
                with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                    self.bound({'C': dict(node(), **{field: value})}, {}, complete_storage=None)
        for invalid in (drain('C', 'C', 1), drain('C', 'missing', 1), drain('C', 'GND', 0)):
            with self.assertRaises(ValueError):
                self.bound({'C': node()}, {'R': invalid})
        with self.assertRaises(ValueError):
            self.bound({'C': dict(node(), capacitance_max_f=.1)}, {})
        with self.assertRaises(ValueError):
            self.bound({'C': node(voltage=1e308)}, {'R': drain('C', 'GND', 1)})


class ResetStorageTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).parent
        def read(name):
            return json.loads((root / name).read_text())
        self.spec = read('electrical-review.json')
        self.control = read('electrical-control-revision.json')
        self.revision = read('electrical-reset-revision.json')
        self.candidate = headroom_netlist(
            reset_netlist(self.spec, self.control, read('electrical-boost-interlock.json'), self.revision),
            read('electrical-headroom.json'))

    def calculate(self):
        return reset_storage_study(self.candidate, self.spec, self.control, self.revision)

    def test_real_inventory_cannot_claim_a_finite_dwell(self):
        result = self.calculate()
        self.assertEqual(set(result['nodes']), {'A', 'B', 'C', 'FIVE_V', 'KILL', 'DVDT'})
        self.assertIn('C_B_CERAMIC', result['external_capacitors'])
        self.assertIsNone(result['external_capacitors']['C_B_CERAMIC']['nominal_f'])
        self.assertIn('internal_storage.U7', result['assembly']['missing'])
        self.assertIn('internal_storage.loads', result['assembly']['missing'])
        self.assertIn('DVDT.ground_path', result['assembly']['missing'])
        self.assertFalse(result['qualified'])
        self.assertIsNone(result['assembly']['required_off_s'])

    def test_four_aggregate_rail_bounds_do_not_cover_internal_charge(self):
        self.revision['assembly_bounds'] = copy.deepcopy(self.revision['reference_case'])
        self.revision['storage_audit']['complete_storage'] = True
        result = self.calculate()['assembly']
        self.assertIsNone(result['required_off_s'])
        self.assertIn('KILL.capacitance_max_f', result['missing'])
        self.assertIn('DVDT.capacitance_max_f', result['missing'])
        self.assertIn('internal_storage.U4', result['missing'])

    def test_capacitor_inventory_matches_both_pins_and_catches_orphan_nominals(self):
        for edit in ('missing_return', 'third_pin', 'orphan_nominal', 'floating_return', 'duplicate'):
            changed = copy.deepcopy(self.candidate)
            if edit == 'missing_return':
                changed['nets']['GND'].remove('C_KILL.2')
            elif edit == 'third_pin':
                changed['nets']['GND'].append('C_KILL.3')
            elif edit == 'orphan_nominal':
                changed['capacitors_nominal_f']['C_ORPHAN'] = 1e-6
            elif edit == 'floating_return':
                changed['nets']['GND'].remove('C_KILL.2')
                changed['nets']['C'].append('C_KILL.2')
            else:
                changed['nets']['C'].append('C_KILL.1')
            with self.subTest(edit=edit), self.assertRaises(ValueError):
                capacitor_nodes(changed)

    def test_missing_capacitor_or_module_row_is_an_error(self):
        for category, name in [('external_capacitance_f', 'C_KILL'), ('internal_capacitance_f', 'U7')]:
            with self.subTest(category=category):
                original = self.revision['storage_audit'][category].pop(name)
                with self.assertRaisesRegex(ValueError, 'ownership'):
                    self.calculate()
                self.revision['storage_audit'][category][name] = original
        self.candidate['nets']['C'].append('U8.VIN')
        with self.assertRaisesRegex(ValueError, 'inventory'):
            self.calculate()

    def test_new_storage_requires_explicit_owner_and_node_bounds(self):
        self.candidate['nets']['CONTROLLER_EN'].append('C_EN.1')
        self.candidate['nets']['GND'].append('C_EN.2')
        with self.assertRaisesRegex(ValueError, 'ownership'):
            self.calculate()
        self.revision['storage_audit']['external_capacitance_f']['C_EN'] = {
            'capacitance_min_f': None, 'capacitance_max_f': None}
        with self.assertRaisesRegex(ValueError, 'Every stored-charge node'):
            self.calculate()

    def test_storage_is_summed_by_node_and_unknown_is_not_zero(self):
        caps = self.revision['storage_audit']['external_capacitance_f']
        for name in ('C_B_BULK', 'C_B_CERAMIC', 'C_U6'):
            caps[name] = {'capacitance_min_f': 1e-6, 'capacitance_max_f': 2e-6}
        result = self.calculate()
        self.assertAlmostEqual(result['nodes']['B']['capacitance_max_f'], 6e-6)
        caps['C_U6']['capacitance_max_f'] = None
        self.assertIsNone(self.calculate()['nodes']['B']['capacitance_max_f'])
        caps['C_U6']['capacitance_min_f'] = -1
        with self.assertRaises(ValueError):
            self.calculate()

    def test_drain_and_internal_storage_cannot_move_without_reanalysis(self):
        self.candidate['nets']['KILL'].remove('R_KILL_BOTTOM.1')
        self.candidate['nets']['C'].append('R_KILL_BOTTOM.1')
        with self.assertRaisesRegex(ValueError, 'KILL discharge resistor moved'):
            self.calculate()
        self.setUp()
        self.revision['storage_audit']['internal_capacitance_f']['U4'] = {}
        with self.assertRaisesRegex(ValueError, 'explicit node contributions'):
            self.calculate()
        self.revision['storage_audit']['internal_capacitance_f']['U4'] = {'KILL': {}}
        with self.assertRaisesRegex(ValueError, 'not connected to owner'):
            self.calculate()


if __name__ == '__main__':
    unittest.main()
