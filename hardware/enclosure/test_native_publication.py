"""Real multi-file publication failures, including process death and recovery."""

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import native_publication as publication


class NativePublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.transaction = self.root / '.build/publication'
        self.files = {'exports/shape.step': b'old shape', 'model.FCStd': b'old native',
                      'design.md': b'old table', 'manifest.json': b'old manifest'}
        for name, data in self.files.items():
            publication.atomic_write(self.root / name, data)
        self.new = {name: data.replace(b'old', b'new') for name, data in self.files.items()}
        self.new['exports/added.stl'] = b'new part'

    def assertPrevious(self):
        for name, data in self.files.items():
            self.assertEqual((self.root / name).read_bytes(), data)
        self.assertFalse((self.root / 'exports/added.stl').exists())
        self.assertFalse(publication.pending(self.transaction))

    def publish(self, validate=lambda: None):
        publication.publish(self.root, self.transaction, self.new, set(), 'manifest.json', validate)

    def test_success_and_validation_failure(self):
        def fail():
            self.assertTrue(publication.pending(self.transaction))
            raise RuntimeError('injected validation failure')
        with self.assertRaisesRegex(RuntimeError, 'injected'):
            self.publish(fail)
        self.assertPrevious()
        self.publish()
        for name, data in self.new.items():
            self.assertEqual((self.root / name).read_bytes(), data)
        self.assertFalse(publication.pending(self.transaction))

    def test_replace_failure_restores_retired_and_added_parts(self):
        original = publication.atomic_write
        def fail(path, data):
            if path == self.root / 'manifest.json' and data == b'new manifest':
                raise OSError('injected manifest failure')
            original(path, data)
        new = {name: data for name, data in self.new.items() if name != 'design.md'}
        with patch.object(publication, 'atomic_write', side_effect=fail):
            with self.assertRaisesRegex(OSError, 'injected'):
                publication.publish(self.root, self.transaction, new, {'design.md'}, 'manifest.json', lambda: None)
        self.assertPrevious()

    def test_process_death_during_export_and_manifest_replacement(self):
        script = '''
import os, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import native_publication as p
root = Path(sys.argv[2])
original = p.atomic_write
def crash(path, data):
    original(path, data)
    if path == root / sys.argv[3]: os._exit(73)
p.atomic_write = crash
files = {'exports/shape.step': b'new shape', 'model.FCStd': b'new native',
         'design.md': b'new table', 'manifest.json': b'new manifest', 'exports/added.stl': b'new part'}
p.publish(root, root / '.build/publication', files, set(), 'manifest.json', lambda: None)
'''
        for name in ('exports/shape.step', 'manifest.json'):
            with self.subTest(point=name):
                result = subprocess.run([sys.executable, '-c', script, str(Path(publication.__file__).parent),
                                         str(self.root), name], capture_output=True, timeout=10)
                self.assertEqual(result.returncode, 73, result.stderr)
                self.assertTrue(publication.pending(self.transaction))
                publication.recover(self.root, self.transaction)
                self.assertPrevious()
                publication.recover(self.root, self.transaction)
                self.assertPrevious()

    def test_unsafe_target_does_not_mutate_release(self):
        for name in ('../outside', '/absolute', 'exports\\outside'):
            with self.subTest(name=name), self.assertRaisesRegex(RuntimeError, 'Unsafe'):
                publication.publish(self.root, self.transaction, {**self.new, name: b'x'}, set(), 'manifest.json', lambda: None)
            self.assertPrevious()


if __name__ == '__main__':
    unittest.main()
