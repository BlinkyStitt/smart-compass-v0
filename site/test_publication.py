"""Exercise real directory replacement, interrupted processes and source races."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import publication


def render(directory, value='new'):
    (directory/'index.html').write_text(value)
    (directory/'estimates.json').write_text(json.dumps({'value': value}))
    (directory/'.nojekyll').touch()
    publication.seal(directory, {'commit': 'fixture', 'value': value})


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        # publish() resolves parent symlinks before replacing directories. macOS
        # exposes its temporary directory through /var -> /private/var, so the
        # failure hooks must compare the same canonical path as the publisher.
        self.output = (Path(self.temporary.name)/'pages').resolve()
        publication.publish(self.output, lambda directory: render(directory, 'old'), lambda: None)
        self.before = {p.relative_to(self.output): p.read_bytes() for p in self.output.rglob('*') if p.is_file()}

    def assertPrevious(self):
        self.assertEqual(self.before, {p.relative_to(self.output): p.read_bytes()
                                     for p in self.output.rglob('*') if p.is_file()})
        publication.verify(self.output)

    def test_complete_release_replaces_all_files(self):
        publication.publish(self.output, render, lambda: None)
        self.assertEqual((self.output/'index.html').read_text(), 'new')
        self.assertEqual(publication.verify(self.output)['value'], 'new')
        self.assertFalse((self.output.parent/'.pages.previous').exists())
        self.assertFalse((self.output.parent/'.pages.transaction.json').exists())

    def test_explicit_whole_artifact_rollback_restores_values_and_provenance(self):
        publication.publish(self.output, render, lambda: None)
        self.assertEqual(json.loads((self.output/'estimates.json').read_text())['value'], 'new')
        def restore(stage):
            for name, data in self.before.items():
                (stage/name).parent.mkdir(parents=True, exist_ok=True)
                (stage/name).write_bytes(data)
        publication.publish(self.output, restore, lambda: None)
        self.assertPrevious()
        self.assertEqual(json.loads((self.output/'estimates.json').read_text())['value'], 'old')

    def test_render_failure_does_not_touch_previous(self):
        def fail(directory):
            (directory/'index.html').write_text('partial')
            raise RuntimeError('render failed')
        with self.assertRaisesRegex(RuntimeError, 'render failed'):
            publication.publish(self.output, fail, lambda: None)
        self.assertPrevious()

    def test_changed_sources_do_not_publish(self):
        with self.assertRaisesRegex(RuntimeError, 'source changed'):
            publication.publish(self.output, render, lambda: (_ for _ in ()).throw(RuntimeError('source changed')))
        self.assertPrevious()

    def test_replacement_exception_rolls_back(self):
        original = publication.os.replace
        def fail(source, target):
            if '.stage-' in Path(source).name and Path(target) == self.output:
                raise OSError('injected directory replacement failure')
            return original(source, target)
        with patch.object(publication.os, 'replace', side_effect=fail):
            with self.assertRaisesRegex(OSError, 'injected'):
                publication.publish(self.output, render, lambda: None)
        self.assertPrevious()

    def test_process_death_before_and_after_install_recovers_previous(self):
        for after in (False, True):
            with self.subTest(after_install=after):
                code = '''
import os
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
import publication
from test_publication import render
output = Path(sys.argv[2])
original = os.replace
def interrupt(source, target):
    if '.stage-' in Path(source).name and Path(target) == output:
        if sys.argv[3] == 'True': original(source, target)
        os._exit(73)
    return original(source, target)
publication.os.replace = interrupt
publication.publish(output, render, lambda: None)
'''
                child = subprocess.run([sys.executable, '-c', code, str(Path(__file__).parent),
                                        str(self.output), str(after)], capture_output=True, text=True, timeout=10)
                self.assertEqual(child.returncode, 73, child.stderr)
                self.assertTrue((self.output.parent/'.pages.previous').is_dir())
                with self.assertRaisesRegex(RuntimeError, 'next render stopped'):
                    publication.publish(self.output, lambda _: (_ for _ in ()).throw(RuntimeError('next render stopped')), lambda: None)
                self.assertPrevious()
                self.assertFalse((self.output.parent/'.pages.transaction.json').exists())

    def test_concurrent_publisher_is_rejected(self):
        code = '''
from pathlib import Path
import sys
sys.path.insert(0, sys.argv[1])
import publication
try:
    with publication.lock(Path(sys.argv[2])): pass
except RuntimeError as exc:
    print(exc)
    raise SystemExit(0)
raise SystemExit(1)
'''
        with publication.lock(self.output):
            child = subprocess.run([sys.executable, '-c', code, str(Path(__file__).parent), str(self.output)],
                                   text=True, capture_output=True, timeout=10)
        self.assertEqual(child.returncode, 0, child.stderr)
        self.assertIn('Another Pages build', child.stdout)
        self.assertPrevious()

    def test_unowned_directory_and_symlink_are_preserved(self):
        other = self.output.parent/'unrelated'
        other.mkdir()
        (other/'notes.txt').write_text('keep')
        with self.assertRaisesRegex(RuntimeError, 'unowned'):
            publication.publish(other, render, lambda: None)
        self.assertEqual((other/'notes.txt').read_text(), 'keep')
        link = self.output.parent/'link'
        link.symlink_to(self.output, target_is_directory=True)
        with self.assertRaisesRegex(RuntimeError, 'symlink'):
            publication.publish(link, render, lambda: None)
        self.assertPrevious()

    def test_unexpected_file_or_changed_bytes_invalidate_inventory(self):
        (self.output/'extra').write_text('unexpected')
        with self.assertRaisesRegex(RuntimeError, 'inventory/hash mismatch'):
            publication.verify(self.output)
        (self.output/'extra').unlink()
        (self.output/'index.html').write_text('changed')
        with self.assertRaisesRegex(RuntimeError, 'inventory/hash mismatch'):
            publication.verify(self.output)

    def test_pointer_cannot_be_sealed(self):
        (self.output/'index.html').write_text('version https://git-lfs.github.com/spec/v1\noid sha256:fake\n')
        with self.assertRaisesRegex(RuntimeError, 'Unmaterialized'):
            publication.seal(self.output, {})


if __name__ == '__main__':
    unittest.main()
