"""Check the active review boundary and destructive wiring perturbations."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from electrical_design import assess

HERE = Path(__file__).resolve().parent


class PrototypeDesignTests(unittest.TestCase):
    def setUp(self):
        self.design = json.loads((HERE / 'electrical-design.json').read_text())

    def reviewed_fixture(self):
        # Contract fixture only: not evidence that these remaining assembly
        # decisions or physical tests have been completed.
        design = copy.deepcopy(self.design)
        design['open_design_items'] = []
        for part in design['parts'].values():
            if 'unresolved' in part['part'].lower():
                part['part'] = 'Selected fixture part; not assembly evidence'
        return design

    def failure_ids(self, design):
        return {item['id'] for item in assess(design)['failures']}

    def test_no_permanent_failure_or_physical_acceptance_gate(self):
        report = assess(self.reviewed_fixture())
        self.assertEqual(report['failures'], [])
        self.assertTrue(report['digital_design_pass'])
        self.assertEqual(report['physical_acceptance'], 'unmeasured')
        self.assertFalse(report['safe_to_wear_claim'])
        self.assertTrue(all(item['status'] == 'unmeasured'
                            for item in report['physical_qualification'].values()))

    def test_real_remaining_design_work_still_fails(self):
        report = assess(self.design)
        self.assertFalse(report['digital_design_pass'])
        self.assertIn('fitted-harness', self.failure_ids(self.design))
        self.assertIn('exact-peripheral-and-strip-stock', self.failure_ids(self.design))

    def test_direct_low_battery_to_enable_is_rejected(self):
        design = self.reviewed_fixture()
        design['nets']['LATCH_OFF'].remove('BOOST.R20.2')
        design['nets']['LATCH_OFF'] += ['BOOST.JP1.4', 'BOOST.JP1.3']
        self.assertIn('net:LATCH_OFF', self.failure_ids(design))
        self.assertIn('unreviewed-connections', self.failure_ids(design))

    def test_bypassing_either_physical_switch_pole_is_rejected(self):
        for pin, source, destination in [
            ('LATCH.VIN', 'A', 'FUSED_CELL'),
            ('SPARKLE.X7.PWR', 'LOAD_5V', 'BOOST_OUT'),
            ('GPS.3V', 'AUX_3V3', 'LOAD_5V'),
        ]:
            with self.subTest(pin=pin):
                design = self.reviewed_fixture()
                design['nets'][source].remove(pin)
                design['nets'][destination].append(pin)
                self.assertFalse(assess(design)['digital_design_pass'])

    def test_missing_return_or_branch_fuse_cannot_pass(self):
        design = self.reviewed_fixture()
        design['nets']['GND'].remove('RADIO.GND')
        self.assertIn('net:GND', self.failure_ids(design))
        design = self.reviewed_fixture()
        design['nets']['FIB_5V'].remove('F_FIB.2')
        design['nets']['FIB_5V'].append('F_FIB.1')
        self.assertIn('duplicate-pin', self.failure_ids(design))

    def test_source_controls_and_unused_inputs_remain_checked(self):
        for key, value in [('BOOST.remove', []), ('LATCH.leave_open', []),
                           ('BOOST.do_not_install', []), ('SPARKLE.usb_pd_v', 20),
                           ('BOOST.nominal_output_v', 5.0)]:
            with self.subTest(key=key):
                design = self.reviewed_fixture()
                design['module_rework'][key] = value
                self.assertFalse(assess(design)['digital_design_pass'])
        design = self.reviewed_fixture()
        design['source_record']['sha256'] = '0' * 64
        self.assertIn('module-source-hash', self.failure_ids(design))

    def test_unsupported_part_substitution_cannot_reuse_wiring_checks(self):
        design = self.reviewed_fixture()
        design['parts']['LATCH']['part'] = 'Pololu SV switch, minimum 4.5 V'
        self.assertIn('module-selection', self.failure_ids(design))
        design = self.reviewed_fixture()
        design['parts']['F1']['part'] = 'Unreviewed 20 A fuse'
        self.assertIn('selected-part:F1', self.failure_ids(design))

    def test_no_procedure_or_boolean_can_create_physical_evidence(self):
        design = self.reviewed_fixture()
        design['physical_qualification']['thermal']['status'] = 'passed'
        self.assertIn('unverified-physical-claim:thermal', self.failure_ids(design))
        design = self.reviewed_fixture()
        del design['physical_qualification']['short_and_reversal']
        self.assertIn('qualification-coverage', self.failure_ids(design))
        design = self.reviewed_fixture()
        design['service']['off_dwell_s'] = 5
        self.assertIn('unverified-dwell', self.failure_ids(design))

    def test_invalid_operating_conditions_are_errors(self):
        for value in [float('nan'), float('inf'), True, 0, -1]:
            design = self.reviewed_fixture()
            design['operating_plan']['brightness'] = value
            self.assertFalse(assess(design)['digital_design_pass'])
        design = self.reviewed_fixture()
        design['operating_plan']['cell_v'] = [1.5, 4.2]
        self.assertIn('cell-operating-range', self.failure_ids(design))

    def test_cli_checks_selected_design_and_keeps_failure_visible(self):
        result = subprocess.run([sys.executable, str(HERE / 'electrical.py'), 'check'],
                                capture_output=True, text=True)
        report, _ = json.JSONDecoder().raw_decode(result.stdout)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(report['scope'], 'digital-prototype-design-review')
        self.assertEqual(report['physical_acceptance'], 'unmeasured')
        self.assertIn('ELECTRICAL DESIGN CHECK FAILED', result.stdout)
        self.assertNotIn('NaN', result.stdout)


if __name__ == '__main__':
    unittest.main()
