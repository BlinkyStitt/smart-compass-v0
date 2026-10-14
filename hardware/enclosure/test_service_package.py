"""Check supplier quantities, process settings, archive integrity and self-contained links."""
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
        self.parts = {
            'parameters_for_inventory': json.loads((HERE/'parameters.json').read_text()),
            'stl_files': ['HaloRing.stl', 'NecklaceLink0.stl', 'OpticalDeck.stl'],
            'fit_samples': [{'file': 'FitRingHalo.stl', 'source_part': 'HaloRing'},
                            {'file': 'FitSuspensionBracketLeft.stl', 'source_part': 'NecklaceLink0'}],
            'components': [{'cad_part': name, 'installed_quantity': 1,
                            'material': 'Prusament PETG Ultraglow Green' if name == 'HaloRing' else 'Opaque PETG',
                            'mass_formula': 'glow_petg_volume' if name == 'HaloRing' else 'petg_volume'}
                           for name in ('HaloRing', 'NecklaceLink0', 'OpticalDeck')],
        }
        self.save_parts()
        for name in slicing.project_names(self.parts):
            (self.exports/name).write_bytes(('mesh '+name).encode())
            with zipfile.ZipFile((self.exports/name).with_suffix('.3mf'), 'w') as archive:
                profile = slicing.settings(self.spec, name)
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
        path = self.exports/service_package.ARCHIVE
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
