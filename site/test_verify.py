"""Real HTTP provenance failures must stop before launching browser probes."""
import json
from html.parser import HTMLParser
from pathlib import Path
import shutil
import tempfile
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch

import publication
import verify


class StudyFixtureTests(unittest.TestCase):
    def test_fixture_matches_the_shipped_comparison_player_contract(self):
        class PlayerElements(HTMLParser):
            def __init__(self):
                super().__init__()
                self.primary = False
                self.videos = 0
                self.elements = {}

            def handle_starttag(self, tag, attributes):
                attrs = dict(attributes)
                if attrs.get('id') == 'films':
                    self.primary = True
                if self.primary and tag == 'video':
                    self.videos += 1
                if attrs.get('id') in ('films', 'play-both', 'replay-both', 'play-status', 'assembly-video'):
                    self.elements[attrs['id']] = attrs

            def handle_endtag(self, tag):
                if tag == 'section':
                    self.primary = False

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            samples = root / '.build/energy-samples'
            samples.mkdir(parents=True)
            (samples / 'manifest.json').write_text('{"sets": []}')
            for name in ('hardware/enclosure/exports/infinity-rainbow.mp4',
                         'hardware/enclosure/exports/infinity-rainbow-silver.mp4',
                         'designs/stacked/exports/infinity-rainbow.mp4'):
                source = root / name
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_bytes(b'fixture clip')
            output = root / 'study'
            output.mkdir()
            with patch.object(verify, 'ROOT', root):
                verify.fixture(output)
            for markup in ((output / 'index.html').read_text(), (verify.HERE / 'index.html').read_text()):
                parser = PlayerElements()
                parser.feed(markup)
                self.assertEqual(parser.videos, 2)
                for element, attribute in (('films', 'data-comparison'), ('films', 'data-autoplay'),
                                           ('play-both', 'data-play-both'), ('replay-both', 'data-replay-both')):
                    self.assertIn(attribute, parser.elements[element])
                self.assertIn('play-status', parser.elements['play-status']['class'].split())
                self.assertIn('assembly-video', parser.elements)


class LiveVerificationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.expected = Path(temporary.name) / 'expected'
        self.expected.mkdir()
        (self.expected / 'index.html').write_text('complete fixture')
        (self.expected / 'estimates.json').write_text('{"hours":2.61664}')
        (self.expected / '.nojekyll').touch()
        publication.seal(self.expected, {'commit': 'a' * 40, 'inputs': {'fixture': 'source hash'}})
        self.remote = Path(temporary.name) / 'remote'
        shutil.copytree(self.expected, self.remote)

    def test_exact_remote_bytes_reach_browser_and_server_closes(self):
        with verify.server(self.remote) as url, patch.object(verify, 'probe') as probe, patch('builtins.print'):
            verify.live(url, self.expected)
            probe.assert_called_once_with(url, self.expected)
        with self.assertRaises(urllib.error.URLError):
            urllib.request.urlopen(url, timeout=2)

    def test_stale_revision_rejected_before_browser(self):
        record = json.loads((self.remote / 'build-info.json').read_text())
        record['commit'] = 'b' * 40
        (self.remote / 'build-info.json').write_text(json.dumps(record))
        with verify.server(self.remote) as url, patch.object(verify, 'probe') as probe:
            with self.assertRaisesRegex(RuntimeError, 'revision, provenance or file inventory differs'):
                verify.live(url, self.expected)
        probe.assert_not_called()

    def test_media_ranges_and_unsatisfiable_range(self):
        data = b'0123456789'
        (self.remote / 'clip.mp4').write_bytes(data)
        with verify.server(self.remote) as url:
            for request_range, expected, content_range in (
                ('bytes=2-5', b'2345', 'bytes 2-5/10'),
                ('bytes=8-', b'89', 'bytes 8-9/10'),
                ('bytes=-3', b'789', 'bytes 7-9/10'),
            ):
                request = urllib.request.Request(url + 'clip.mp4', headers={'Range': request_range})
                with urllib.request.urlopen(request, timeout=2) as response:
                    self.assertEqual(response.status, 206)
                    self.assertEqual(response.headers['Content-Range'], content_range)
                    self.assertEqual(response.read(), expected)
            request = urllib.request.Request(url + 'clip.mp4', headers={'Range': 'bytes=10-'})
            with self.assertRaises(urllib.error.HTTPError) as failure:
                urllib.request.urlopen(request, timeout=2)
            self.assertEqual(failure.exception.code, 416)

    def test_mixed_estimates_rejected_before_browser(self):
        (self.remote / 'estimates.json').write_text('{"hours":5}')
        with verify.server(self.remote) as url, patch.object(verify, 'probe') as probe:
            with self.assertRaisesRegex(RuntimeError, 'stale/mixed: estimates.json'):
                verify.live(url, self.expected)
        probe.assert_not_called()
