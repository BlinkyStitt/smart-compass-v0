"""Test freshness, partial staging and failed-build protection with small fixtures."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from types import SimpleNamespace
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
        for name in cad.required_exports(self.snapshot):
            if not (self.root / name).exists():
                self.write(name, b'project fixture')
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
                 cad.EXPORTS + '/front.png', cad.EXPORTS + '/infinity-rainbow.mp4',
                 cad.EXPORTS + '/Part.stl', 'demo/main.gd',
                 cad.EXPORTS + '/amulet.glb', cad.EXPORTS + '/scene.json',
                 cad.EXPORTS + '/night-mannequin.png',
                 cad.EXPORTS + '/infinity-rainbow.gif', cad.EXPORTS + '/infinity-rainbow-silver.mp4',
                 cad.EXPORTS + '/smart-compass-glow-print-service.zip', cad.CAD + '/service-guide.html')
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

    def test_staged_lfs_content_and_partial_staging(self):
        def git(*args):
            return subprocess.run(['git', *args], cwd=self.root, check=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout

        git('init', '-q')
        git('lfs', 'install', '--local')
        self.write('.gitattributes', b'*.FCStd filter=lfs diff=lfs merge=lfs -text\n')
        git('add', '.')
        pointer = git('show', ':' + cad.MASTER)
        self.assertTrue(pointer.startswith(b'version https://git-lfs.github.com/spec/v1\n'))
        staged = cad.Snapshot(self.root, staged=True)
        self.assertEqual(staged.read(cad.MASTER), self.snapshot.read(cad.MASTER))
        cad.check_freshness(staged)
        self.write(cad.MASTER, b'new LFS model')
        self.record()
        git('add', cad.MASTER)
        with self.assertRaisesRegex(cad.CadError, cad.MASTER):
            cad.check_freshness(staged)
        git('add', cad.MANIFEST)
        cad.check_freshness(staged)
        oid = git('show', ':' + cad.MASTER).decode().split('oid sha256:')[1].splitlines()[0]
        (self.root / '.git/lfs/objects' / oid[:2] / oid[2:4] / oid).unlink()
        with self.assertRaisesRegex(cad.CadError, cad.MASTER):
            staged.read(cad.MASTER)

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
            self.write(cad.EXPORTS + '/Obsolete.3mf', b'old project')
            for path in cad.RETIRED_EXPORTS:
                self.write(path, b'old forming template')
            self.write(cad.EXPORTS + '/parts.json',
                       json.dumps({'stl_files': ['Part.stl', 'Obsolete.stl']}).encode())
            original = cad.hashes(self.snapshot, cad.INPUTS)
            cad.publish(self.root, staged, original, {'freecad': ['test']})
            self.assertFalse((self.root / cad.EXPORTS / 'Obsolete.stl').exists())
            self.assertFalse((self.root / cad.EXPORTS / 'Obsolete.3mf').exists())
            self.assertTrue(all(not (self.root / path).exists() for path in cad.RETIRED_EXPORTS))
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

    def test_build_lock_spans_processes_and_tempdirs_without_files(self):
        script = """import sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import cad
try:
    with cad.build_lock(Path(sys.argv[2])):
        print('acquired')
except cad.CadError:
    print('busy')
"""
        def child():
            result = subprocess.run(
                [sys.executable, '-c', script, str(Path(cad.__file__).parent), str(self.root)],
                env=dict(os.environ, TMPDIR=str(self.root)), check=True,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            return result.stdout.strip()
        before = set(self.root.iterdir())
        with cad.build_lock(self.root):
            self.assertEqual(child(), 'busy')
        self.assertEqual(child(), 'acquired')
        self.assertEqual(set(self.root.iterdir()), before)

    def test_build_lock_releases_after_failure_and_allows_other_checkouts(self):
        other = self.root/'other-checkout'
        other.mkdir()
        with self.assertRaisesRegex(RuntimeError, 'failed build'):
            with cad.build_lock(self.root):
                with cad.build_lock(other):
                    raise RuntimeError('failed build')
        with cad.build_lock(self.root):
            with cad.build_lock(other):
                pass


class NativeMacroExitTests(unittest.TestCase):
    def test_native_macros_close_unsaved_documents_on_success_and_failure(self):
        for macro in ('hardware/enclosure/Run.FCMacro',):
            for fails in (False, True):
                with self.subTest(macro=macro, fails=fails), tempfile.TemporaryDirectory() as tmp:
                    documents = {'saved-model': object(), 'temporary-export': object()}
                    exited = []
                    def build(*args):
                        if fails:
                            raise RuntimeError('native build failed')
                    def quit_application():
                        self.assertFalse(documents, 'Unsaved documents would open a modal save prompt')
                        exited.append(True)
                    app = SimpleNamespace(Version=lambda: ['1', '1', '4'],
                                          listDocuments=lambda: documents,
                                          closeDocument=lambda name: documents.pop(name))
                    qt = SimpleNamespace(QTimer=SimpleNamespace(singleShot=lambda delay, fn: fn()),
                                         QCoreApplication=SimpleNamespace(quit=quit_application))
                    modules = {'FreeCAD': app, 'PySide': SimpleNamespace(QtCore=qt),
                               'build': SimpleNamespace(build=build), 'native': SimpleNamespace(build=build)}
                    result = Path(tmp)/'result.json'
                    env = {'SC_CAD_DIR': tmp, 'SC_CAD_STAGE': 'build', 'SC_CAD_RESULT': str(result),
                           'STACKED_SOURCE': str(Path(tmp)/'designs/stacked'),
                           'STACKED_OUTPUT': tmp, 'STACKED_RESULT': str(result)}
                    with patch.dict(sys.modules, modules), patch.dict(os.environ, env), \
                            patch.object(sys, 'path', list(sys.path)), patch('traceback.print_exc'):
                        exec(compile((cad.ROOT/macro).read_text(), macro, 'exec'), {})
                    self.assertEqual(exited, [True])
                    self.assertEqual(result.exists(), not fails)


if __name__ == '__main__':
    unittest.main()
