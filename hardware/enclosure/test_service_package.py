"""Check supplier quantities, process settings, archive integrity and self-contained links."""
from copy import deepcopy
import csv
import io
import json
from pathlib import Path
import re
import tempfile
import unittest
import zipfile

import cad
import service_package
import slicing

HERE = Path(__file__).resolve().parent


class ServicePackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.directory = self.root/cad.CAD
        self.exports = self.root/cad.EXPORTS
        self.exports.mkdir(parents=True)
        self.spec = json.loads((HERE/'print-spec.json').read_text())
        (self.directory/'print-spec.json').write_text(json.dumps(self.spec))
        (self.directory/'service-guide.html').write_bytes((HERE/'service-guide.html').read_bytes())
        source=self.directory/'vendor/evilgeniuslabs-fibonacci256'
        source.mkdir(parents=True)
        for name in ('LICENSE.txt','SOURCE.md'):
            (source/name).write_bytes((HERE/'vendor/evilgeniuslabs-fibonacci256'/name).read_bytes())
        self.parts = {
            'parameters_for_inventory': json.loads((HERE/'parameters.json').read_text()),
            'stl_files': ['HaloRing.stl', 'NecklaceLink0.stl', 'OpticalDeck.stl'],
            'fit_samples': [{'file': 'FitRingHalo.stl', 'source_part': 'HaloRing'},
                            {'file': 'FitSuspensionBracketLeft.stl', 'source_part': 'NecklaceLink0'}],
            'components': [{'cad_part': name, 'installed_quantity': 1,
                            'material': 'Prusament PETG Ultraglow Green' if name == 'HaloRing' else 'Opaque black PETG',
                            'mass_formula': 'ring_petg_volume' if name == 'HaloRing' else 'petg_volume'}
                           for name in ('HaloRing', 'NecklaceLink0', 'OpticalDeck')],
        }
        self.parts['material_variants']={key:{'components':deepcopy(self.parts['components'])} for key in self.spec['ring_materials']}
        self.parts['components']=self.parts['material_variants']['glow']['components']
        for row in self.parts['material_variants']['silver']['components']:
            if row['mass_formula']=='ring_petg_volume': row['material']='Extrudr PETG Silver'
        self.save_parts()
        for name,project,material in slicing.project_jobs(self.parts,self.spec):
            (self.exports/name).write_bytes(('mesh '+name).encode())
            with zipfile.ZipFile(self.exports/project, 'w') as archive:
                profile = slicing.settings(self.spec, name, material)
                archive.writestr('Metadata/Slic3r_PE.config', ''.join(f'; {key} = {value}\n' for key, value in profile.items()))
        for name in service_package.REFERENCES:
            (self.exports/name).write_bytes(('reference '+name).encode())

    def save_parts(self):
        (self.exports/'parts.json').write_text(json.dumps(self.parts))

    def test_quantities_stages_materials_and_local_links(self):
        files = service_package.shipment(self.root)
        rows = list(csv.DictReader(io.StringIO(files['ORDER.csv'].decode())))
        self.assertEqual(len(rows), 5)
        self.assertEqual(sum(int(row['quantity']) for row in rows if row['stage'].startswith('01-')), 2)
        self.assertEqual(sum(int(row['quantity']) for row in rows if row['stage'].startswith('02-')), 3)
        ring = next(row for row in rows if row['file'].endswith('/HaloRing.3mf'))
        self.assertEqual((ring['material'], ring['infill'], ring['perimeters']), ('Prusament PETG Ultraglow Green', '0%', '2'))
        bracket = next(row for row in rows if row['file'].endswith('/FitSuspensionBracketLeft.3mf'))
        self.assertEqual((bracket['infill'], bracket['perimeters']), ('100%', '6'))
        deck = next(row for row in rows if row['file'].endswith('/OpticalDeck.3mf'))
        self.assertEqual((deck['layer_mm'], deck['top_layers']), ('0.1', '10'))
        for row in rows:
            self.assertEqual(files[row['file']], (self.exports/Path(row['file']).name).read_bytes())
        guide = files['START-HERE.html'].decode()
        for link in re.findall(r'(?:href|src)="([^"]+)"', guide):
            self.assertIn(link, files)
        self.assertFalse(any(name.endswith(('.mp4', '.gif', '.glb')) for name in files))

    def test_archive_is_reproducible_and_rejects_changed_or_extra_contents(self):
        service_package.generate(self.root)
        path = self.exports/service_package.archive_name('glow')
        original = path.read_bytes()
        service_package.generate(self.root)
        self.assertEqual(path.read_bytes(), original)
        expected = service_package.shipment(self.root)
        service_package.verify(path, expected)
        expected['ORDER.csv'] += b'changed'
        with self.assertRaisesRegex(cad.CadError, 'content differs: ORDER.csv'):
            service_package.verify(path, expected)
        with zipfile.ZipFile(path, 'a') as archive:
            archive.writestr('unlisted.stl', b'not ordered')
        with self.assertRaisesRegex(cad.CadError, 'inventory differs'):
            service_package.verify(path, service_package.shipment(self.root))

    def test_silver_package_uses_silver_profiles_and_its_own_acceptance(self):
        files=service_package.shipment(self.root,'silver')
        rows=list(csv.DictReader(io.StringIO(files['ORDER.csv'].decode())))
        ring=next(row for row in rows if row['file'].endswith('/HaloRing.3mf'))
        self.assertEqual(ring['material'],'Extrudr PETG Silver')
        with zipfile.ZipFile(io.BytesIO(files[ring['file']])) as archive:
            profile=slicing.configuration(archive.read('Metadata/Slic3r_PE.config').decode())
        self.assertEqual(float(profile['filament_density']),1.29)
        guide=files['START-HERE.html'].decode()
        self.assertIn('Silver PETG print service handoff',guide)
        self.assertIn('If the silver is opaque',guide)
        self.assertNotIn('Record green afterglow immediately',guide)
        self.assertEqual(files['03-STL-ALTERNATIVES/02-FULL-PARTS-HOLD/HaloRing.stl'],
                         service_package.shipment(self.root,'glow')['03-STL-ALTERNATIVES/02-FULL-PARTS-HOLD/HaloRing.stl'])

    def test_both_packages_keep_structural_parts_black_and_rings_distinct(self):
        for material,colour in (('glow','#CCD6A8'),('silver','#94999E')):
            files=service_package.shipment(self.root,material)
            rows=list(csv.DictReader(io.StringIO(files['ORDER.csv'].decode())))
            for row in rows:
                ring=Path(row['file']).stem in ('HaloRing','FitRingHalo')
                if not ring:
                    self.assertEqual(row['material'],'Opaque black PETG')
                with zipfile.ZipFile(io.BytesIO(files[row['file']])) as archive:
                    profile=slicing.configuration(archive.read('Metadata/Slic3r_PE.config').decode())
                self.assertEqual(profile['filament_colour'],colour if ring else '#000000')
            for guide in ('START-HERE.html','START-HERE.txt'):
                self.assertIn('opaque black PETG',files[guide].decode())
            self.assertIn('Reject light transmission through the black parts.',files['START-HERE.html'].decode())

    def test_wrong_delivered_profile_cannot_enter_package(self):
        path = self.exports/'HaloRing.3mf'
        with zipfile.ZipFile(path, 'w') as archive:
            profile = dict(slicing.settings(self.spec, 'HaloRing.stl'), fill_density='25%')
            archive.writestr('Metadata/Slic3r_PE.config', ''.join(f'; {key} = {value}\n' for key, value in profile.items()))
        with self.assertRaisesRegex(cad.CadError, 'fill_density'):
            service_package.shipment(self.root)

    def test_bad_quantity_and_unsafe_names_are_rejected(self):
        self.parts['components'][0]['installed_quantity'] = 1.5
        self.save_parts()
        with self.assertRaisesRegex(cad.CadError, 'quantity'):
            service_package.shipment(self.root)
        self.parts['components'][0]['installed_quantity'] = 1
        self.parts['stl_files'][0] = '../HaloRing.stl'
        self.save_parts()
        with self.assertRaisesRegex(cad.CadError, 'Unsafe'):
            service_package.shipment(self.root)


if __name__ == '__main__':
    unittest.main()
