"""Check source-sized cell clearance and required assembly contact settings."""
import unittest
from pathlib import Path
import tempfile

from battery_access import definition, contact_travel, validate, contact_source


class BatteryAccessTests(unittest.TestCase):
    def test_both_designs_use_source_maximum_cell_and_positive_travel_margin(self):
        spec = definition()
        self.assertEqual(spec['cell']['diameter_mm'][1], 22.1)
        self.assertEqual(spec['cell']['length_mm'][1], 75.3)
        for design in ('wide', 'narrow'):
            result = validate(spec, design)
            self.assertAlmostEqual(result['initial_total_min_mm'], .3)
            self.assertAlmostEqual(result['initial_total_max_mm'], 1.5)
            self.assertEqual(result['individual_initial_compression_mm'], [0, result['initial_total_max_mm']])
            self.assertAlmostEqual(result['released_gap_min_mm'], .27)
            self.assertAlmostEqual(result['compressed_max_mm'], 1.87)
            self.assertAlmostEqual(result['available_stroke_min_mm'], 2.159)
        self.assertIn('not measured or guaranteed', spec['contact']['datum_basis'])

    def test_longer_cell_small_gap_or_excessive_shift_is_rejected(self):
        for section, key, value in [('cell', 'length_mm', [74, 76]),
                                    ('contact', 'unloaded_tip_gap_mm', [71.5, 71.7]),
                                    ('removal', 'positive_end_release_gap_mm', .6)]:
            with self.subTest(key=key):
                spec = definition()
                spec[section][key] = value
                with self.assertRaisesRegex(ValueError, 'Contact travel'):
                    validate(spec, 'wide')

    def test_insufficient_shift_does_not_release_contact(self):
        spec = definition()
        spec['contact']['negative_stop_compression_mm'] = [1.5,1.6]
        with self.assertRaisesRegex(ValueError, 'release'):
            validate(spec, 'narrow')

    def test_second_bay_and_overwide_cell_are_rejected(self):
        spec = definition()
        spec['cell']['quantity'] = 2
        with self.assertRaisesRegex(ValueError, 'one selected cell'):
            validate(spec, 'wide')
        spec = definition()
        spec['cell']['diameter_mm'] = [29, 30]
        with self.assertRaisesRegex(ValueError, 'radial'):
            validate(spec, 'narrow')

    def test_thin_ceiling_or_reversed_bounds_do_not_pass(self):
        spec = definition()
        spec['cradle']['top_z_mm'] = 25
        with self.assertRaisesRegex(ValueError, 'ceiling'):
            validate(spec, 'wide')
        spec = definition()
        spec['cell']['length_mm'] = [75.3, 74.3]
        with self.assertRaisesRegex(ValueError, 'ordered'):
            validate(spec, 'wide')

    def test_missing_or_nonfinite_contact_settings_cannot_pass(self):
        for name in ('unloaded_tip_gap_mm','negative_stop_compression_mm'):
            for bad in ([1,float('nan')],[1,float('inf')],[True,2],[2,1],[0,1]):
                spec=definition()
                spec['contact'][name]=bad
                with self.subTest(name=name,bad=bad):
                    with self.assertRaises(ValueError): validate(spec,'wide')
        for section,key in (('contact','full_stroke_mm'),('removal','positive_end_release_gap_mm'),
                            ('cradle','cell_axis_z_mm')):
            spec=definition()
            spec[section][key]=float('nan')
            with self.assertRaises(ValueError): validate(spec,'narrow')

    def test_selected_wire_cup_source_and_tolerance_cannot_be_inflated(self):
        for key,value in [('full_stroke_tolerance_mm',.01),('source_length_tolerance_mm',.01),
                          ('part','Mill-Max 0850-0-15-20-83-14-11-0')]:
            spec=definition();spec['contact'][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):validate(spec,'wide')
        for key in ('cup_hole_diameter_mm','cup_depth_mm','total_height_mm'):
            spec=definition();spec['contact']['drawing'][key]+=1
            with self.subTest(key=key),self.assertRaisesRegex(ValueError,'source drawing'):validate(spec,'wide')

    def test_finished_clamp_holes_retain_clearance_and_flange_bearing(self):
        for key,value in [('front_plate_bore_radius_mm',1.5),('front_plate_bore_radius_mm',1.2),
                          ('back_plate_bore_radius_mm',1.5),('back_plate_bore_radius_mm',1.1),
                          ('back_plate_bore_radius_mm',float('nan'))]:
            spec=definition();spec['contact']['drawing'][key]=value
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):validate(spec,'narrow')

    def test_rear_plate_must_pass_the_source_maximum_solder_cup(self):
        spec=definition()
        drawing=spec['contact']['drawing']
        self.assertGreater(2*drawing['back_plate_bore_radius_mm']-.05,
                           drawing['cup_outer_diameter_mm']+.0508+.1)
        drawing['back_plate_bore_radius_mm']=1.275
        with self.assertRaisesRegex(ValueError,'cannot pass'):
            validate(spec,'wide')

    def test_missing_and_changed_contact_sheet_cannot_pass(self):
        source=Path(__file__).parent/'sources/battery-contact-0854'
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(OSError):contact_source(temporary)
            target=Path(temporary)/'sources/battery-contact-0854'
            target.mkdir(parents=True)
            for name in ('index.json','mill-max-0854-2024.pdf'):
                (target/name).write_bytes((source/name).read_bytes())
            self.assertEqual(contact_source(temporary)['part'],'0854-0-15-20-82-14-11-0')
            (target/'mill-max-0854-2024.pdf').write_bytes(b'changed primary sheet')
            with self.assertRaisesRegex(ValueError,'source changed'):contact_source(temporary)

    def test_inflating_source_stroke_or_removing_cell_does_not_create_clearance(self):
        spec=definition()
        spec['contact']['full_stroke_mm']=20
        with self.assertRaisesRegex(ValueError,'source/stroke'): validate(spec,'wide')
        for bad in (True,0,2):
            spec=definition()
            spec['cell']['quantity']=bad
            with self.assertRaises(ValueError): validate(spec,'narrow')

    def test_mount_hardware_is_in_the_required_census(self):
        from battery_access import PART_NAMES, MOUNT_PARTS
        self.assertEqual(len(MOUNT_PARTS),12)
        self.assertTrue(MOUNT_PARTS <= PART_NAMES)
        self.assertEqual(definition()['cradle']['mount_bottom_z_mm'],2)

    def test_pull_tape_uses_stock_maximum_and_published_mass_limit(self):
        tape=definition()['ribbon']
        self.assertAlmostEqual(tape['thickness_mm'][1],.025*25.4)
        self.assertAlmostEqual(tape['width_mm'][1],(.375+1/32)*25.4)
        grams=tape['max_oz_per_yard']*28.349523125*tape['cut_length_mm']/914.4
        self.assertLess(grams,.373)


if __name__ == '__main__':
    unittest.main()
