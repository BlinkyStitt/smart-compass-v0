"""Reject stale, incomplete, or internally inconsistent Rev A deliveries."""

import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from layout import PRINT_PARTS
import print_inputs


class PrintInputTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.carrier = self.root / 'designs/carrier'
        self.baseline = self.root / 'designs/stacked/exports'
        self.carrier.mkdir(parents=True)
        self.baseline.mkdir(parents=True)
        self.native = self.root / 'hardware/enclosure/spec.json'
        self.native.parent.mkdir(parents=True)
        self.native.write_text('{}')
        for name in ('native.py', 'print_inputs.py', 'print_package.py', 'README.md'):
            (self.carrier / name).write_text(name)
        board = self.carrier / 'wall-power/board.kicad_pcb'
        board.parent.mkdir()
        board.write_text('board')
        exports = {}
        for name in ('stacked-fibonacci.FCStd', 'parts.json', 'loom-check.json',
                     'EGLStencil.stl', 'InnerDiffuser.stl', 'SideDiffuser.stl'):
            path = self.baseline / name
            path.write_text(name)
            exports[path.relative_to(self.root).as_posix()] = print_inputs.digest(path)
        manifest = {'inputs': {self.native.relative_to(self.root).as_posix(): print_inputs.digest(self.native)},
                    'exports': exports}
        (self.baseline.parent / 'exports-manifest.json').write_text(json.dumps(manifest))
        for name, value in (('ROOT', self.root), ('CARRIER', self.carrier), ('BASELINE', self.baseline)):
            context = patch.object(print_inputs, name, value)
            context.start()
            self.addCleanup(context.stop)

    def contents(self):
        parts = [{'file': name + '.stl', 'source_part': name} for name in sorted(PRINT_PARTS)]
        samples = [{'file': name + '.stl', 'source_part': parent}
                   for name, parent in print_inputs.FIT_SAMPLES.items()]
        files = {}
        projects = []
        for row in parts + samples:
            files[row['file']] = row['file'].encode()
            row['sha256'] = hashlib.sha256(files[row['file']]).hexdigest()
            choices = ('glow', 'silver') if row['source_part'] in {'InnerDiffuser', 'SideDiffuser'} else ('opaque-petg',)
            for material in choices:
                name = Path(row['file']).stem + ('-silver' if material == 'silver' else '') + '.3mf'
                files[name] = name.encode()
                projects.append({'project': name, 'material': material,
                                 'source_stl_sha256': row['sha256'], 'toolpath_mass_g': 1.5})
        files['parts.json'] = json.dumps({'print_parts': parts, 'fit_samples': samples,
                                         'stl_files': [row['file'] for row in parts]}).encode()
        files['slicer-check.json'] = json.dumps({'projects': projects}).encode()
        files['routed-fit.json'] = json.dumps({'inputs': print_inputs.fit_inputs()}).encode()
        files['README.md'] = b'First fit guidance'
        return files

    def archive(self, files=None, *, inputs=None, corrupt=False):
        files = files if files is not None else self.contents()
        manifest = {'revision': 'Rev A', 'inputs': inputs if inputs is not None else print_inputs.package_inputs(),
                    'files': {name: hashlib.sha256(data).hexdigest() for name, data in files.items()}}
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as archive:
            for name, data in files.items():
                archive.writestr(name, data + b'changed' if corrupt and name == 'README.md' else data)
            archive.writestr(print_inputs.MANIFEST_NAME, json.dumps(manifest))
        return buffer.getvalue()

    def test_complete_archive_has_all_parts_samples_and_projects(self):
        inventory, sliced = print_inputs.verify_archive(self.archive())
        self.assertEqual(len(inventory['print_parts']), 12)
        self.assertEqual(len(inventory['fit_samples']), 3)
        self.assertEqual(len(sliced['projects']), 17)

    def test_stale_native_inputs_and_exports_block_fingerprinting(self):
        for path in (self.native, self.baseline / 'loom-check.json', self.baseline / 'InnerDiffuser.stl'):
            with self.subTest(path=path):
                original = path.read_bytes()
                path.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'differs from its native manifest'):
                    print_inputs.fit_inputs()
                path.write_bytes(original)

    def test_package_builder_and_nested_carrier_changes_invalidate_archive(self):
        for path in (self.carrier / 'print_package.py', self.carrier / 'wall-power/board.kicad_pcb'):
            with self.subTest(path=path):
                data = self.archive()
                original = path.read_bytes()
                path.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'archive is stale'):
                    print_inputs.verify_archive(data)
                path.write_bytes(original)

    def test_lfs_pointer_is_not_a_materialized_input(self):
        path = self.carrier / 'native.py'
        path.write_bytes(b'version https://git-lfs.github.com/spec/v1\n')
        with self.assertRaisesRegex(ValueError, 'Materialize'):
            print_inputs.fit_inputs()

    def test_corrupted_member_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'checksum differs'):
            print_inputs.verify_archive(self.archive(corrupt=True))

    def test_rehashed_incomplete_or_inconsistent_reports_still_fail(self):
        cases = ('part', 'sample', 'project', 'material', 'mesh', 'mass', 'fit', 'extra', 'missing_project_file')
        for case in cases:
            with self.subTest(case=case):
                files = self.contents()
                inventory = json.loads(files['parts.json'])
                sliced = json.loads(files['slicer-check.json'])
                if case == 'part': inventory['print_parts'].pop()
                elif case == 'sample': inventory['fit_samples'].pop()
                elif case == 'project': sliced['projects'].pop()
                elif case == 'material': sliced['projects'][0]['material'] = 'wrong-material'
                elif case == 'mesh': files[inventory['print_parts'][0]['file']] = b'wrong mesh'
                elif case == 'mass': sliced['projects'][0]['toolpath_mass_g'] = float('nan')
                elif case == 'fit': files['routed-fit.json'] = b'{"inputs": {}}'
                elif case == 'extra': files['unexpected.txt'] = b'extra'
                elif case == 'missing_project_file': del files[sliced['projects'][0]['project']]
                files['parts.json'] = json.dumps(inventory).encode()
                files['slicer-check.json'] = json.dumps(sliced).encode()
                with self.assertRaises(ValueError):
                    print_inputs.verify_archive(self.archive(files))


if __name__ == '__main__':
    unittest.main()
