"""Test freshness, partial staging and failed-build protection with small fixtures."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import cad


class CadWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.snapshot = cad.Snapshot(self.root)
        for path in cad.INPUTS:
            self.write(path, ('fixture: ' + path).encode())
        for name in cad.FIXED_EXPORTS | {'Part.stl'}:
            self.write(cad.EXPORTS + '/' + name, ('export: ' + name).encode())
        self.write(cad.EXPORTS + '/parts.json', json.dumps({'stl_files': ['Part.stl']}).encode())
        self.record()

    def write(self, path, data):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    def record(self):
        manifest = {'format_version': 1, 'tools': {},
                    'inputs': cad.hashes(self.snapshot, cad.INPUTS),
                    'exports': cad.hashes(self.snapshot, cad.required_exports(self.snapshot))}
        self.write(cad.MANIFEST, json.dumps(manifest).encode())

    def test_complete_snapshot_passes_and_finder_file_is_ignored(self):
        self.write(cad.EXPORTS + '/.DS_Store', b'finder')
        cad.check_freshness(self.snapshot)

    def test_source_and_export_changes_fail(self):
        paths = (cad.MASTER, cad.CAD + '/build.py', cad.CAD + '/fibonacci256-layout.json',
                 cad.EXPORTS + '/front.png', cad.EXPORTS + '/amulet-demo.mp4',
                 cad.EXPORTS + '/Part.stl', 'demo/main.gd',
                 cad.EXPORTS + '/amulet.glb', cad.EXPORTS + '/scene.json',
                 cad.EXPORTS + '/demo-front-indoor.png',
                 cad.EXPORTS + '/exploded.gif', cad.EXPORTS + '/exploded.mp4')
        for path in paths:
            with self.subTest(path=path):
                original = self.snapshot.read(path)
                self.write(path, original + b'changed')
                with self.assertRaisesRegex(cad.CadError, path):
                    cad.check_freshness(self.snapshot)
                self.write(path, original)

    def test_missing_and_extra_exports_fail(self):
        path = cad.EXPORTS + '/front.png'
        original = self.snapshot.read(path)
        (self.root / path).unlink()
        with self.assertRaisesRegex(cad.CadError, 'Missing export'):
            cad.check_freshness(self.snapshot)
        self.write(path, original)
        self.write(cad.EXPORTS + '/obsolete.stl', b'obsolete')
        with self.assertRaisesRegex(cad.CadError, 'Unexpected export'):
            cad.check_freshness(self.snapshot)

    def test_manifest_cannot_omit_a_source_or_output(self):
        for group, path in (('inputs', cad.MASTER), ('exports', cad.EXPORTS + '/front.png')):
            with self.subTest(group=group):
                manifest = cad.load_json(self.snapshot, cad.MANIFEST)
                del manifest[group][path]
                self.write(cad.MANIFEST, json.dumps(manifest).encode())
                with self.assertRaisesRegex(cad.CadError, 'incomplete ' + group):
                    cad.check_freshness(self.snapshot)
                self.record()

    def test_unsafe_and_duplicate_stl_paths_fail(self):
        for names in (['../outside.stl'], ['/outside.stl'], ['sub/part.stl'],
                      ['sub\\part.stl'], ['Part.stl', 'Part.stl']):
            with self.subTest(names=names):
                self.write(cad.EXPORTS + '/parts.json', json.dumps({'stl_files': names}).encode())
                with self.assertRaises(cad.CadError):
                    cad.required_exports(self.snapshot)

    def test_staged_check_uses_index_and_rejects_partial_staging(self):
        def git(*args):
            subprocess.run(['git', *args], cwd=self.root, check=True,
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        git('init', '-q')
        git('add', '.')
        staged = cad.Snapshot(self.root, staged=True)
        # Unstaged edits do not change what the hook checks.
        self.write(cad.MASTER, b'new model')
        cad.check_freshness(staged)
        with self.assertRaises(cad.CadError):
            cad.check_freshness(self.snapshot)
        self.write(cad.EXPORTS + '/front.png', b'new render')
        self.record()
        cad.check_freshness(self.snapshot)
        git('add', cad.MASTER)
        with self.assertRaisesRegex(cad.CadError, cad.MASTER):
            cad.check_freshness(staged)
        git('add', '.')
        cad.check_freshness(staged)
        git('rm', '--cached', cad.EXPORTS + '/front.png')
        with self.assertRaisesRegex(cad.CadError, 'Missing export'):
            cad.check_freshness(staged)

    def test_zero_exit_without_native_completion_is_failure(self):
        with patch.object(cad.subprocess, 'run'):
            with self.assertRaisesRegex(cad.CadError, 'did not finish'):
                cad.native_stage('freecad', self.root / cad.CAD, 'build')

    def test_source_edit_during_build_prevents_publication(self):
        original = cad.hashes(self.snapshot, cad.INPUTS)
        old_outputs = {p: self.snapshot.read(p) for p in cad.required_exports(self.snapshot)}
        old_manifest = self.snapshot.read(cad.MANIFEST)
        self.write(cad.MASTER, b'new user edit')
        with self.assertRaisesRegex(cad.CadError, 'Source changed during the build'):
            cad.publish(self.root, self.snapshot, original, {})
        self.assertEqual(self.snapshot.read(cad.MASTER), b'new user edit')
        self.assertEqual(self.snapshot.read(cad.MANIFEST), old_manifest)
        self.assertEqual({p: self.snapshot.read(p) for p in old_outputs}, old_outputs)

    def test_failed_native_build_preserves_saved_files(self):
        paths = set(cad.INPUTS) | cad.required_exports(self.snapshot) | {cad.MANIFEST}
        original = {p: self.snapshot.read(p) for p in paths}
        with patch.object(cad.shutil, 'which', return_value=sys.executable), \
                patch.object(cad.subprocess, 'run'), \
                patch.object(cad, 'native_stage', side_effect=cad.CadError('native failure')):
            with self.assertRaisesRegex(cad.CadError, 'native failure'):
                cad.rebuild(self.root)
        self.assertEqual({p: self.snapshot.read(p) for p in paths}, original)

    def test_publish_replaces_outputs_and_removes_only_old_listed_meshes(self):
        with tempfile.TemporaryDirectory() as directory:
            shutil.copytree(self.root, directory, dirs_exist_ok=True)
            staged = cad.Snapshot(Path(directory))
            (staged.root / cad.MASTER).write_bytes(b'rebuilt model')
            self.write(cad.EXPORTS + '/Obsolete.stl', b'old mesh')
            self.write(cad.EXPORTS + '/parts.json',
                       json.dumps({'stl_files': ['Part.stl', 'Obsolete.stl']}).encode())
            original = cad.hashes(self.snapshot, cad.INPUTS)
            cad.publish(self.root, staged, original, {'freecad': ['test']})
            self.assertFalse((self.root / cad.EXPORTS / 'Obsolete.stl').exists())
            self.assertEqual(self.snapshot.read(cad.MASTER), b'rebuilt model')
            cad.check_freshness(self.snapshot)

    def test_publish_can_recover_missing_generated_inventory(self):
        with tempfile.TemporaryDirectory() as directory:
            shutil.copytree(self.root, directory, dirs_exist_ok=True)
            original = cad.hashes(self.snapshot, cad.INPUTS)
            (self.root / cad.EXPORTS / 'parts.json').unlink()
            cad.publish(self.root, cad.Snapshot(Path(directory)), original, {})
            cad.check_freshness(self.snapshot)

    def test_duplicate_build_is_rejected(self):
        with cad.build_lock(self.root):
            with self.assertRaisesRegex(cad.CadError, 'already running'):
                with cad.build_lock(self.root):
                    self.fail('A second build acquired the lock')


if __name__ == '__main__':
    unittest.main()
