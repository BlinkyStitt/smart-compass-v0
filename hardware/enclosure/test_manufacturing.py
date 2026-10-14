"""Behavior checks for supplied print settings and installed mass accounting."""
import json
from pathlib import Path
import unittest

import cad
import hardware_spec
import inventory
import slicing

HERE=Path(__file__).resolve().parent


class ManufacturingTests(unittest.TestCase):
    def test_same_nut_allowances_and_entrance_widths(self):
        self.assertEqual(hardware_spec.nut_dimensions('M3',True),(5.9,2.7))
        self.assertEqual(hardware_spec.nut_dimensions('M2',True),(4.4,1.9))
        for size in ('M2','M3'):
            nominal=hardware_spec.nut_dimensions(size)
            pocket=hardware_spec.nut_dimensions(size,True)
            self.assertAlmostEqual(pocket[0]-nominal[0],.4)
            self.assertAlmostEqual(pocket[1]-nominal[1],.3)

    def test_delivered_bracket_and_sample_use_same_solid_settings(self):
        spec=json.loads((HERE/'print-spec.json').read_text())
        main=slicing.settings(spec,'RearPlate.stl')
        bracket=slicing.settings(spec,'NecklaceLink0.stl')
        self.assertEqual((main['perimeters'],main['fill_density'],main['fill_pattern']),('5','25%','gyroid'))
        self.assertEqual((bracket['perimeters'],bracket['fill_density'],bracket['fill_pattern']),('6','100%','rectilinear'))
        self.assertEqual(bracket,slicing.settings(spec,'FitSuspensionBracket.stl'))
        with self.assertRaisesRegex(cad.CadError,'perimeters'):
            slicing.verify_settings(main,bracket,'wrong delivered bracket')
        with self.assertRaisesRegex(cad.CadError,'filament_type'):
            slicing.verify_settings(dict(main,filament_type='PLA'),main,'wrong material')

    def test_optical_fit_samples_use_production_deck_settings(self):
        spec=json.loads((HERE/'print-spec.json').read_text())
        production=slicing.settings(spec,'OpticalDeck.stl')
        self.assertEqual(production['layer_height'],'0.1')
        for sample in ('FitDeck.stl','FitOptics.stl'):
            self.assertEqual(slicing.settings(spec,sample),production)

    def resolved(self):
        spec=json.loads((HERE/'component-inventory.json').read_text())
        p=json.loads((HERE/'parameters.json').read_text())
        volumes=[{'name':r['cad_part'],'volume_cm3':1,'printed':r['mass_formula'] in ('petg_volume','glow_petg_volume')}
                 for r in spec['components'] if r.get('mass_formula')]
        return inventory.resolve(spec,volumes,p),volumes

    def test_installed_strip_lengths_and_single_populated_boards(self):
        rows,_=self.resolved(); byid={r['id']:r for r in rows}
        self.assertAlmostEqual(sum(byid[k+'_strip']['installed_quantity'] for k in ('halo','inner','outer')),238/120)
        self.assertAlmostEqual(sum(byid[k+'_strip']['installed_mass_g'] for k in ('halo','inner','outer')),238/120*25,places=3)
        for id in ('circle','sparkle','blackpill','gps','imu','radio','boost','sense','battery'):
            self.assertEqual(byid[id]['installed_quantity'],1)
        self.assertFalse(any('Components' in r.get('cad_part','') for r in rows))

    def test_complete_totals_include_necklace_and_external_hardware(self):
        rows,_=self.resolved(); mass=inventory.totals(rows)
        self.assertAlmostEqual(mass['total_worn']['nominal_g'],mass['complete_pendant']['nominal_g']+mass['necklace']['nominal_g'],delta=.11)
        self.assertGreater(mass['external_total_worn']['nominal_g'],mass['total_worn']['nominal_g'])
        self.assertEqual(len([r for r in rows if r['id']=='battery']),1)
        for key in ('complete_pendant','necklace','total_worn','external_battery_pendant','external_total_worn'):
            lo,hi=mass[key]['range_g'];self.assertLess(lo,mass[key]['nominal_g']);self.assertGreater(hi,mass[key]['nominal_g'])
        self.assertNotIn('charger',mass['outstanding_measurements'])

    def test_missing_or_duplicate_mass_cannot_pass(self):
        rows,volumes=self.resolved()
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            inventory.validate(rows+[rows[0]])
        rows[0]['mass_g_per_unit']=0
        with self.assertRaisesRegex(ValueError,'mass allowance'):
            inventory.validate(rows)
        rows,_=self.resolved()
        with self.assertRaisesRegex(ValueError,'Printed inventory'):
            inventory.validate(rows,volumes+[{'name':'MissingPrint','printed':True}])

    def test_mass_formula_has_no_conflicting_literal_or_unknown_density(self):
        spec=json.loads((HERE/'component-inventory.json').read_text())
        p=json.loads((HERE/'parameters.json').read_text())
        spec['components'][0]['mass_g_per_unit']=1
        with self.assertRaisesRegex(ValueError,'formula or a literal mass'):
            inventory.resolve(spec,[],p)
        del spec['components'][0]['mass_g_per_unit']
        spec['components'][0]['mass_formula']='unknown_density'
        with self.assertRaisesRegex(ValueError,'Unknown mass formula'):
            inventory.resolve(spec,[],p)

    def test_fastener_quantities_match_modeled_joints(self):
        rows,_=self.resolved(); quantities={r['id']:r['installed_quantity'] for r in rows}
        p=json.loads((HERE/'parameters.json').read_text())
        stations=hardware_spec.stations(p)
        m3=[r for r in stations if r[1]=='M3'];m2=[r for r in stations if r[1]=='M2']
        self.assertEqual(len(m3),quantities['body_screws']+quantities['anchor_screws']+quantities['rear_screws'])
        self.assertEqual(len(m2),quantities['service_screws']+quantities['sparkle_mount_hardware'])
        self.assertEqual(len(m3),quantities['M3_washers'])
        self.assertEqual(6,quantities['M3_front_washers'])
        self.assertEqual(sum(r[-1] is not None for r in m3)+6,quantities['M3_nuts'])
        self.assertEqual(len(m2),quantities['M2_nuts'])
        self.assertEqual(len(m2),quantities['M2_washers'])
