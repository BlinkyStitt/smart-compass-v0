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

    def test_outside_ring_sample_uses_the_same_four_path_wall(self):
        spec=json.loads((HERE/'print-spec.json').read_text())
        outside=slicing.settings(spec,'EdgeDiffuser.stl')
        self.assertEqual(slicing.settings(spec,'FitRingOutside.stl'),outside)
        self.assertEqual((outside['perimeters'],outside['extrusion_width']),('4','0.53'))
        self.assertEqual(outside['first_layer_extrusion_width'],'0.46')
        self.assertEqual((outside['layer_height'],outside['nozzle_diameter']),('0.2','0.4'))
        cavity=slicing.settings(spec,'HaloRing.stl')
        self.assertEqual((cavity['perimeters'],cavity['extrusion_width']),('2','0.5'))

    def test_silver_and_glow_keep_same_paths_but_use_correct_material_settings(self):
        spec=json.loads((HERE/'print-spec.json').read_text())
        for name in ('HaloRing.stl','InnerRing.stl','EdgeDiffuser.stl','FitRingHalo.stl','FitRingInner.stl','FitRingOutside.stl'):
            glow=slicing.settings(spec,name,'glow')
            silver=slicing.settings(spec,name,'silver')
            self.assertEqual(float(glow.pop('filament_density')),spec['ring_materials']['glow']['density_g_cm3'])
            self.assertEqual(float(silver.pop('filament_density')),spec['ring_materials']['silver']['density_g_cm3'])
            self.assertEqual(glow.pop('filament_colour'),'#CCD6A8')
            self.assertEqual(silver.pop('filament_colour'),'#94999E')
            self.assertEqual(glow,silver)
            self.assertNotEqual(slicing.project_filename(name,'glow'),slicing.project_filename(name,'silver'))
        for name in ('RearPlate.stl','NecklaceLink0.stl'):
            self.assertEqual(slicing.settings(spec,name,'glow'),slicing.settings(spec,name,'silver'))
        component=json.loads((HERE/'component-inventory.json').read_text())
        p=json.loads((HERE/'parameters.json').read_text())
        volumes=[{'name':r['cad_part'],'volume_cm3':1,'printed':r['mass_formula'] in ('petg_volume','ring_petg_volume')}
                 for r in component['components'] if r.get('mass_formula') in ('petg_volume','ring_petg_volume','acrylic_volume')]
        masses=[]
        for material in ('glow','silver'):
            rows=inventory.resolve(component,volumes,p,spec['ring_materials'][material])
            ring=next(r for r in rows if r['id']=='EdgeDiffuser')
            self.assertEqual(ring['material'],spec['ring_materials'][material]['filament'])
            masses.append(ring['mass_g_per_unit'])
        self.assertGreater(masses[0],masses[1])

    def test_original_baffle_profile_keeps_thin_walls_dense_and_flat(self):
        spec=json.loads((HERE/'print-spec.json').read_text())
        for name in ('FibonacciBaffle.stl','FitFibonacciBaffle.stl'):
            profile=slicing.settings(spec,name)
            self.assertEqual(profile['layer_height'],'0.1')
            self.assertEqual(profile['extrusion_width'],'0.4')
            self.assertEqual(profile['perimeters'],'2')
            self.assertEqual(profile['fill_density'],'100%')
            self.assertEqual(profile['filament_colour'],'#000000')
            self.assertEqual(profile['top_solid_layers'],'10')
            self.assertEqual(profile['bottom_solid_layers'],'10')

    def test_structural_products_and_samples_require_opaque_black_petg(self):
        spec=json.loads((HERE/'print-spec.json').read_text())
        rows,_=self.resolved()
        structural=[r for r in rows if r.get('mass_formula')=='petg_volume']
        self.assertEqual(len(structural),14)
        for row in structural:
            self.assertEqual(row['material'],'Opaque black PETG')
            profile=slicing.settings(spec,row['cad_part']+'.stl')
            self.assertEqual(profile['filament_colour'],'#000000')
        for sample in ('FitSuspensionBracketLeft','FitSuspensionBracketRight','FitControllerMount','FitDeck','FitOptics'):
            profile=slicing.settings(spec,sample+'.stl')
            self.assertEqual(profile['filament_colour'],'#000000')
        with self.assertRaisesRegex(cad.CadError,'filament_colour'):
            slicing.verify_settings(dict(profile,filament_colour='#29B2B2'),profile,'wrong structural colour')

    def test_bed_check_includes_brims_and_extrusion_width(self):
        spec=json.loads((HERE/'print-spec.json').read_text())
        bed=slicing.bed_bounds(spec)
        self.assertEqual(bed,[0,0,300,300])
        good="G0 X10 Y10\n;LAYER_CHANGE\n;TYPE:Skirt/Brim\n;WIDTH:0.4\nG1 X20 Y10 E1\n"
        slicing.verify_bed(slicing.perimeter_layers(good),bed,'safe')
        for bad in (good.replace('X20','X0.1'),good.replace('X20','X300')):
            with self.assertRaisesRegex(cad.CadError,'outside reference bed'):
                slicing.verify_bed(slicing.perimeter_layers(bad),bed,'bad brim')

    def test_perimeter_measurement_ignores_brims_travel_and_retraction(self):
        gcode="""M82
G92 E0
;LAYER_CHANGE
;TYPE:Skirt/Brim
;WIDTH:0.8
G1 X100 Y100 E5
;TYPE:External perimeter
;WIDTH:0.46
G1 X103 Y104 E6
G1 X103 Y110
G1 X100 Y114 E7
G1 X110 Y114 E6
G92 E0
;LAYER_CHANGE
;TYPE:Perimeter
;WIDTH:0.53
G1 X113 Y118 E1
M83
G1 X116 Y122 E1
;TYPE:Internal infill
;WIDTH:0.9
G1 X200 Y200 E10
"""
        layers=slicing.perimeter_layers(gcode)
        self.assertEqual([layer['length_mm'] for layer in layers],[10,10])
        self.assertEqual([layer['widths_mm'] for layer in layers],[{.46},{.53}])

    def resolved(self):
        spec=json.loads((HERE/'component-inventory.json').read_text())
        p=json.loads((HERE/'parameters.json').read_text())
        volumes=[{'name':r['cad_part'],'volume_cm3':1,'printed':r['mass_formula'] in ('petg_volume','ring_petg_volume')}
                 for r in spec['components'] if r.get('mass_formula') in ('petg_volume','ring_petg_volume','acrylic_volume')]
        return inventory.resolve(spec,volumes,p,json.loads((HERE/'print-spec.json').read_text())['ring_materials']['glow']),volumes

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
            inventory.resolve(spec,[],p,json.loads((HERE/'print-spec.json').read_text())['ring_materials']['glow'])
        del spec['components'][0]['mass_g_per_unit']
        spec['components'][0]['mass_formula']='unknown_density'
        with self.assertRaisesRegex(ValueError,'Unknown mass formula'):
            inventory.resolve(spec,[],p,json.loads((HERE/'print-spec.json').read_text())['ring_materials']['glow'])

    def test_body_bolts_follow_the_measured_stack_and_full_nut_engagement(self):
        p=json.loads((HERE/'parameters.json').read_text())
        for front_thickness in (2.7,3.0,3.3):
            changed=dict(p,case_depth=p['front_plane_z']+front_thickness+p['front_washer_compressed_height'])
            body=[station for station in hardware_spec.stations(changed) if station[0].startswith('Body')]
            for name,size,x,y,seat,direction,length,nut_z in body:
                nut_end=p['rear_thickness']-hardware_spec.WASHERS['M3']['thickness']-hardware_spec.NUTS['M3']['thickness']
                self.assertAlmostEqual(nut_end-(seat-length),p['body_bolt_tip_projection'])
                self.assertGreater(p['body_bolt_tip_projection']-p['body_bolt_tip_chamfer'],.099)
                self.assertLess(length,p['body_bolt_stock_length'])
        rows,_=self.resolved()
        finished=next(r for r in rows if r['id']=='body_screws')
        self.assertLess(finished['mass_g_per_unit'],finished['stock_mass_g_per_unit'])

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
