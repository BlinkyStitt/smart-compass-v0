"""Check the active review boundary and destructive wiring perturbations."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

from electrical_design import assess, off_service_isolation

HERE = Path(__file__).resolve().parent


class PrototypeDesignTests(unittest.TestCase):
    def setUp(self):
        self.design = json.loads((HERE / 'electrical-design.json').read_text())

    def reviewed_fixture(self):
        # Destructive test copies use the actual complete selected record.
        # They never invent assembly evidence or clear a real design gate.
        return copy.deepcopy(self.design)

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

    def test_selected_complete_route_contract_passes_without_physical_claim(self):
        report=assess(self.design)
        self.assertTrue(report['digital_design_pass'],report['failures'])
        self.assertEqual(report['fitted_harness']['route_count'],92)
        self.assertEqual(report['fitted_harness']['splice_count'],12)
        self.assertEqual(report['physical_acceptance'],'unmeasured')
        self.assertFalse(report['safe_to_wear_claim'])
        self.assertEqual(self.design['parts']['IMU']['part'],'Adafruit LSM9DS1 classic breakout PID 3387, VIN=3.3 V')
        self.assertIn('WTP-2812-2020-120-0405',self.design['parts']['RING1']['part'])

    def test_missing_routes_cannot_pass_by_clearing_open_items(self):
        design=self.reviewed_fixture();design['open_design_items']=[]
        actual=Path.read_text
        def read(path,*args,**kwargs):
            if path==HERE/'harness-routing.json':raise FileNotFoundError('Required selected route record missing')
            return actual(path,*args,**kwargs)
        with patch.object(Path,'read_text',read):report=assess(design)
        self.assertFalse(report['digital_design_pass'])
        self.assertIn('fitted-harness',{row['id'] for row in report['failures']})

    def test_reduced_wire_diameter_or_mass_cannot_create_a_pass(self):
        for key in ['maximum_od_mm','nominal_mass_g_m','maximum_resistance_ohm_m_at_20c']:
            design=self.reviewed_fixture();design['wiring']['stock_limits']['branches'][key]*=.5
            with self.subTest(key=key):self.assertIn('fitted-harness',self.failure_ids(design))

    def test_pcb_contact_and_unreviewed_contact_source_fail(self):
        for name in ('CONTACT_P', 'CONTACT_N'):
            design = self.reviewed_fixture()
            design['parts'][name]['part'] = 'Mill-Max 0850-0-15-20-83-14-11-0'
            self.assertIn('selected-part:' + name, self.failure_ids(design))
            design = self.reviewed_fixture()
            design['parts'][name]['source'] = 'unreviewed replacement sheet'
            self.assertIn('contact-source:' + name, self.failure_ids(design))

    def test_capacitor_source_corners_and_pressure_valve_space_are_required(self):
        for key,value in [('minimum_vent_clearance_mm',0),('body_diameter_mm',[10,10]),('lead_pitch_mm',[5,5])]:
            design=self.reviewed_fixture();design['parts']['C_OUT'][key]=value
            with self.subTest(key=key):
                self.assertIn('capacitor-source-and-fit',self.failure_ids(design))

    def test_gps_and_radio_pad_swaps_or_unreviewed_sources_fail(self):
        for module,pin,pad in [('GPS','TX','JP3.1'),('GPS','3V','JP4.7'),('RADIO','G0','JP1.1'),('RADIO','ANT','X1.P')]:
            design=self.reviewed_fixture();design['parts'][module]['terminal_bindings'][pin]=pad
            with self.subTest(module=module,pin=pin):
                self.assertIn(module.lower()+'-terminal-binding',self.failure_ids(design))

    def test_calculator_and_bench_scenario_cannot_drift(self):
        design = self.reviewed_fixture()
        design['operating_plan']['path_estimate_ohm'] = .085
        self.assertIn('planning-model-agreement', self.failure_ids(design))

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

    def test_off_contact_isolation_is_separate_from_reset_timing(self):
        design=self.reviewed_fixture()
        self.assertTrue(all(off_service_isolation(design).values()))
        design['nets']['LOAD_5V'].append('S1.1')
        self.assertFalse(off_service_isolation(design)['LOAD_5V'])
        self.assertIn('off-contact-isolation',self.failure_ids(design))

    def test_each_isolated_rail_has_its_own_drain(self):
        for net, pin in [('BOOST_OUT','R_BOOST.1'), ('LOAD_5V','R_LOAD.1'),
                         ('FIB_5V','R_OUT.1'), ('FIB_5V','C_OUT.P')]:
            with self.subTest(net=net, pin=pin):
                design = self.reviewed_fixture()
                design['nets'][net].remove(pin)
                self.assertIn('net:'+net, self.failure_ids(design))
        design = self.reviewed_fixture()
        design['parts']['F_FIB']['part'] = 'Littelfuse 0459001.UR, 1 A'
        self.assertIn('selected-part:F_FIB', self.failure_ids(design))

    def test_start_uses_opposite_contact_groups(self):
        design = self.reviewed_fixture()
        self.assertIn('START.3', design['nets']['GND'])
        design['nets']['GND'].remove('START.3')
        design['nets']['GND'].append('START.2')
        self.assertIn('net:GND', self.failure_ids(design))
        self.assertIn('unreviewed-connections', self.failure_ids(design))

    def test_existing_buttons_and_sense_filter_cannot_disappear(self):
        for net,pin in [('MODE','BLACKPILL.PB13'),('ACTION','ACTION.1'),
                        ('GND','MODE.3'),('GND','ACTION.3'),
                        ('SENSE','C_SENSE.1'),('GND','C_SENSE.2')]:
            design=self.reviewed_fixture();design['nets'][net].remove(pin)
            with self.subTest(net=net,pin=pin):
                self.assertIn('net:'+net,self.failure_ids(design))
        for name in ('MODE','ACTION'):
            design=self.reviewed_fixture()
            design['nets']['GND'].remove(name+'.3')
            design['nets']['GND'].append(name+'.2')
            self.assertIn('unreviewed-connections',self.failure_ids(design))
        design=self.reviewed_fixture();del design['parts']['C_SENSE']
        self.assertIn('bom-coverage',self.failure_ids(design))

    def test_switch_hardware_requires_the_selected_thread(self):
        design = self.reviewed_fixture()
        design['parts']['S1_NUT']['part'] = 'Unreviewed 1/4-20 nut'
        self.assertIn('selected-part:S1_NUT', self.failure_ids(design))

    def test_start_selection_cannot_revert_to_short_actuator(self):
        design = self.reviewed_fixture()
        design['parts']['START']['part'] = 'Pololu 1400'
        self.assertIn('selected-part:START', self.failure_ids(design))

    def test_optional_blackpill_flash_cannot_share_battery_sense(self):
        design=self.reviewed_fixture();design['module_rework']['BLACKPILL.do_not_install']=[]
        self.assertIn('blackpill-flash-conflict',self.failure_ids(design))
        design=self.reviewed_fixture();design['parts']['BLACKPILL']['part']='WeAct board with U3 flash fitted'
        self.assertIn('selected-part:BLACKPILL',self.failure_ids(design))

    def test_factory_led_clamps_require_supported_wire_and_single_leads(self):
        for key,value in [('wire_group','main'),('signal_wire_group','main'),
                          ('wires_per_clamp',4),('wires_per_clamp',True),('wire_awg_range',[18,26]),
                          ('published_current_a',6),('retention','')]:
            design=self.reviewed_fixture()
            design['parts']['SPARKLE']['led_terminals'][key]=value
            with self.subTest(key=key):
                self.assertIn('sparkle-led-terminations',self.failure_ids(design))
        design=self.reviewed_fixture()
        design['wiring']['stock_limits']['branches']['stock']='M22759/16-18'
        self.assertIn('sparkle-led-terminations',self.failure_ids(design))
        design=self.reviewed_fixture()
        design['parts']['SPARKLE']['part']='A different controller or terminal assembly'
        self.assertIn('selected-part:SPARKLE',self.failure_ids(design))

    def test_source_controls_and_unused_inputs_remain_checked(self):
        for key, value in [('BOOST.remove', []), ('LATCH.leave_open', []),
                           ('BOOST.do_not_install', []), ('SPARKLE.usb_pd_v', 20),
                           ('BOOST.install', {}), ('BOOST.leave_open', ['JP1.3','JP1.4']),
                           ('BOOST.nominal_output_v', 5.0)]:
            with self.subTest(key=key):
                design = self.reviewed_fixture()
                design['module_rework'][key] = value
                self.assertFalse(assess(design)['digital_design_pass'])
        design = self.reviewed_fixture()
        design['source_record']['sha256'] = '0' * 64
        self.assertIn('module-source-hash', self.failure_ids(design))

    def test_boost_current_cannot_return_to_the_small_header_pads(self):
        for net,selected,old in [('B','BOOST.X2.2','BOOST.JP1.1'),
                                 ('BOOST_OUT','BOOST.X1.2','BOOST.JP1.6'),
                                 ('GND','BOOST.X2.1','BOOST.JP1.2')]:
            design=self.reviewed_fixture()
            design['nets'][net].remove(selected);design['nets'][net].append(old)
            with self.subTest(net=net):self.assertIn('net:'+net,self.failure_ids(design))
        design=self.reviewed_fixture();design['nets']['GND'].remove('BOOST.X1.1')
        self.assertIn('net:GND',self.failure_ids(design))
        design=self.reviewed_fixture();design['wiring']['stock_limits']['main']['stock']='M22759/16-22'
        self.assertIn('boost-wire-gauges',self.failure_ids(design))

    def test_latch_upper_b_and_unreviewed_clamps_cannot_reuse_the_review(self):
        design=self.reviewed_fixture()
        design['parts']['LATCH']['terminal_bindings']['A']=[13.97,6.35]
        self.assertIn('latch-terminal-binding',self.failure_ids(design))
        design=self.reviewed_fixture()
        design['parts']['LATCH']['wire_terminals']['part']='Unreviewed smaller clamp'
        self.assertIn('latch-terminal-binding',self.failure_ids(design))

    def test_unsupported_part_substitution_cannot_reuse_wiring_checks(self):
        design = self.reviewed_fixture()
        design['parts']['LATCH']['part'] = 'Pololu SV switch, minimum 4.5 V'
        self.assertIn('module-selection', self.failure_ids(design))
        design = self.reviewed_fixture()
        design['parts']['F1']['part'] = 'Unreviewed 20 A fuse'
        self.assertIn('selected-part:F1', self.failure_ids(design))

    def test_peripheral_budget_and_crossed_sensor_signal_fail(self):
        design = self.reviewed_fixture()
        design['supply_allocation']['external_3v3_peak_a']['RADIO'] = 0.5
        self.assertIn('peripheral-current-budget', self.failure_ids(design))
        design = self.reviewed_fixture()
        design['nets']['GPS_TX'].remove('BLACKPILL.PA3')
        design['nets']['GPS_TX'].append('BLACKPILL.PA2')
        self.assertIn('duplicate-pin', self.failure_ids(design))
        self.assertIn('net:GPS_TX', self.failure_ids(design))

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

    def test_cli_checks_complete_design_and_keeps_physical_boundary(self):
        result = subprocess.run([sys.executable, str(HERE / 'electrical.py'), 'check'],
                                capture_output=True, text=True)
        report, _ = json.JSONDecoder().raw_decode(result.stdout)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(report['scope'], 'digital-prototype-design-review')
        self.assertEqual(report['physical_acceptance'], 'unmeasured')
        self.assertIn('Digital design review only.', result.stdout)
        self.assertNotIn('ELECTRICAL DESIGN CHECK FAILED',result.stdout)
        self.assertTrue(report['digital_design_pass'])
        self.assertEqual(report['fitted_harness']['route_count'],92)
        self.assertNotIn('NaN', result.stdout)


if __name__ == '__main__':
    unittest.main()
