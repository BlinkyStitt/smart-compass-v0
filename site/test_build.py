"""Keep assembly and rainbow media validation distinct and strict."""

import hashlib
import json
import subprocess
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import build
from build import MEDIA, NARROW, WIDE, Movie, verify_movie


class MovieTests(unittest.TestCase):
    def probe(self, frames=576, seconds=24):
        return json.dumps({"streams": [{"width": 1280, "height": 720,
                                       "r_frame_rate": "24/1", "avg_frame_rate": "24/1",
                                       "nb_frames": str(frames), "duration": str(seconds)}]})

    @patch("build.verify_rainbow_motion")
    @patch("build.subprocess.run")
    @patch("build.subprocess.check_output")
    def test_assembly_accepts_24_seconds_and_checks_decoding(self, probe, run, rainbow):
        probe.return_value = self.probe()
        verify_movie(Movie(Path("assembly.mp4"), 24, poster_time=12))
        self.assertIn("-xerror", run.call_args.args[0])
        rainbow.assert_not_called()

    @patch("build.subprocess.run")
    @patch("build.subprocess.check_output")
    def test_shortened_assembly_is_rejected(self, probe, run):
        for frames, seconds in ((384, 24), (576, 16)):
            with self.subTest(frames=frames, seconds=seconds):
                probe.return_value = self.probe(frames, seconds)
                with self.assertRaises(RuntimeError):
                    verify_movie(Movie(Path("assembly.mp4"), 24))
        run.assert_not_called()

    @patch("build.verify_rainbow_motion", side_effect=RuntimeError("Static rainbow"))
    @patch("build.subprocess.run")
    @patch("build.subprocess.check_output")
    def test_rainbow_motion_failure_still_blocks_build(self, probe, run, rainbow):
        probe.return_value = self.probe(384, 16)
        with self.assertRaisesRegex(RuntimeError, "Static rainbow"):
            verify_movie(Movie(Path("rainbow.mp4"), 16, rainbow_scene=Path("scene.json")))

    def test_native_dark_media_registration(self):
        movies = {key: value for key, value in MEDIA.items() if isinstance(value, Movie)}
        self.assertEqual(len(movies), 11)
        for style in ("sectors", "spirals", "diagonals"):
            for design, folder in (("wide", WIDE), ("narrow", NARROW)):
                movie = movies[f"{design}_dark_{style}_movie"]
                self.assertEqual(movie.source, folder / f"infinity-rainbow-dark-{style}.mp4")
                self.assertEqual(movie.rainbow_scene, folder / "scene.json")
                self.assertEqual((movie.seconds, movie.masked_style), (16, style))
        self.assertEqual(sum(m.masked_style is None and m.rainbow_scene is not None
                             for m in movies.values()), 4)

    @patch("build.verify_masked_motion", side_effect=RuntimeError("mask mismatch"))
    @patch("build.verify_rainbow_motion")
    @patch("build.subprocess.run")
    @patch("build.subprocess.check_output")
    def test_mask_failure_blocks_build_without_using_canonical_rotation(self, probe, run, rainbow, masked):
        probe.return_value = self.probe(384, 16)
        with self.assertRaisesRegex(RuntimeError, "mask mismatch"):
            verify_movie(Movie(Path("dark.mp4"), 16, rainbow_scene=Path("scene.json"), masked_style="sectors"))
        masked.assert_called_once_with(Path("dark.mp4"), Path("scene.json"), "sectors")
        rainbow.assert_not_called()

    @patch("build.subprocess.run")
    @patch("build.subprocess.check_output")
    def test_bad_dimensions_and_frame_rates_are_rejected(self, probe, run):
        for field, value in (("width", 640), ("height", 360), ("r_frame_rate", "30/1"),
                             ("avg_frame_rate", "12/1")):
            with self.subTest(field=field):
                data = json.loads(self.probe(384, 16))
                data["streams"][0][field] = value
                probe.return_value = json.dumps(data)
                with self.assertRaises(RuntimeError):
                    verify_movie(Movie(Path("dark.mp4"), 16))
        run.assert_not_called()

    def test_missing_and_lfs_pointer_media_block_build(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "missing.mp4"
            with patch("build.MEDIA", {"wide_dark_sectors_movie": Movie(source, 16)}):
                with self.assertRaises(FileNotFoundError):
                    build.render_media(Path(directory), {})
                source.write_bytes(b"version https://git-lfs.github.com/spec/v1\noid sha256:missing\n")
                with patch("build.ROOT", Path(directory)):
                    with self.assertRaisesRegex(RuntimeError, "Git LFS media is missing"):
                        build.render_media(Path(directory), {})

    def test_movie_rules_and_posters_use_captured_media_and_scene(self):
        for seconds, poster_time, scene_name, style in (
            (24, 12, None, None),
            (16, 0, 'native/scene.json', None),
            (16, 0, 'native/scene.json', 'sectors'),
        ):
            with self.subTest(seconds=seconds, style=style), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / 'site-assets/clip.mp4'
                source.parent.mkdir()
                source.write_bytes(b'captured movie')
                scene = root / scene_name if scene_name else None
                if scene:
                    scene.parent.mkdir()
                    scene.write_bytes(b'captured scene')
                provenance = {path.relative_to(root).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                              for path in (source, scene) if path}
                output = root / 'stage'
                output.mkdir()
                movie = Movie(source, seconds, poster_time, scene, style)

                def inspect(captured):
                    self.assertNotEqual(captured.source, source)
                    self.assertEqual((captured.seconds, captured.poster_time, captured.masked_style),
                                     (seconds, poster_time, style))
                    source.write_bytes(b'concurrent source edit')
                    self.assertEqual(captured.source.read_bytes(), b'captured movie')
                    if scene:
                        self.assertNotEqual(captured.rainbow_scene, scene)
                        scene.write_bytes(b'concurrent scene edit')
                        self.assertEqual(captured.rainbow_scene.read_bytes(), b'captured scene')
                    else:
                        self.assertIsNone(captured.rainbow_scene)

                with patch.object(build, 'ROOT', root), patch.object(build, 'MEDIA', {'clip_movie': movie}), \
                        patch.object(build, 'verify_movie', side_effect=inspect) as verify, \
                        patch.object(build.subprocess, 'run') as run:
                    values, records = build.render_media(output, provenance)
                captured = verify.call_args.args[0]
                command = run.call_args.args[0]
                self.assertEqual(command[command.index('-i') + 1], str(captured.source))
                self.assertEqual(command[command.index('-ss') + 1], str(poster_time))
                self.assertEqual(records['clip_movie']['sha256'], provenance['site-assets/clip.mp4'])
                self.assertEqual(output / values['clip_movie'], captured.source)
                self.assertFalse(list(output.glob('.*-scene.json')))


class BuildInputTests(unittest.TestCase):
    def test_control_revision_is_a_required_hashed_release_input(self):
        relative = 'hardware/enclosure/electrical-control-revision.json'
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            revision = root / relative
            revision.parent.mkdir(parents=True)
            revision.write_bytes(b'first control revision')

            def read(path):
                if path == revision:
                    return path.read_bytes()
                if path.name == 'exports-manifest.json':
                    return b'{"inputs": {}, "exports": {}}'
                return b'other input'

            with patch.object(build, 'ROOT', root), patch.object(build, 'SITE', root/'site'), \
                    patch.object(build, 'checked_bytes', side_effect=read):
                first = build.source_snapshot(include_samples=False)
                self.assertEqual(first[relative], hashlib.sha256(revision.read_bytes()).hexdigest())
                revision.write_bytes(b'changed control revision')
                self.assertNotEqual(first[relative], build.source_snapshot(include_samples=False)[relative])
                revision.unlink()
                with self.assertRaises(FileNotFoundError):
                    build.source_snapshot(include_samples=False)

    def test_changed_input_is_rejected_at_read_time(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(build, 'ROOT', Path(directory)):
            path = Path(directory)/'source.json'
            path.write_bytes(b'old')
            provenance = {'source.json': hashlib.sha256(b'old').hexdigest()}
            self.assertEqual(build.read_input(path, provenance), b'old')
            path.write_bytes(b'new')
            with self.assertRaisesRegex(RuntimeError, 'Input changed before use'):
                build.read_input(path, provenance)

    def test_missing_lfs_input_fails(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(build, 'ROOT', Path(directory)):
            path = Path(directory)/'asset.mp4'
            path.write_text('version https://git-lfs.github.com/spec/v1\n')
            with self.assertRaisesRegex(RuntimeError, 'Git LFS media is missing'):
                build.checked_bytes(path)

    def test_both_native_checks_precede_publication(self):
        with patch.object(build, 'source_snapshot', return_value={'generation': 'a'}), \
                patch.object(build.subprocess, 'run') as run, patch.object(build, 'publish') as publish, patch('builtins.print'):
            build.build(Path('/unused-pages-fixture'))
        self.assertEqual([Path(call.args[0][1]).relative_to(build.ROOT).as_posix()
                          for call in run.call_args_list],
                         ['hardware/enclosure/electrical.py', 'hardware/enclosure/cad.py', 'designs/stacked/run.py', 'site/sample.py', 'site/energy.mjs'])
        self.assertTrue(all(call.kwargs['check'] for call in run.call_args_list))
        publish.assert_called_once()

    def test_failed_native_freshness_never_reaches_publication(self):
        with patch.object(build, 'source_snapshot', return_value={'generation': 'a'}), \
                patch.object(build.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'native check')), \
                patch.object(build, 'publish') as publish:
            with self.assertRaises(subprocess.CalledProcessError):
                build.build(Path('/unused-pages-fixture'))
        publish.assert_not_called()

    def test_source_change_across_native_checks_is_rejected(self):
        with patch.object(build, 'source_snapshot', side_effect=[{'generation': 'a'}, {'generation': 'b'}]), \
                patch.object(build.subprocess, 'run'), patch.object(build, 'publish') as publish:
            with self.assertRaisesRegex(RuntimeError, 'Sources changed'):
                build.build(Path('/unused-pages-fixture'))
        publish.assert_not_called()

    def test_output_cannot_replace_source(self):
        for output in (build.ROOT, build.SITE, build.SITE/'generated', build.SITE/'../site/generated'):
            with self.subTest(output=output), self.assertRaisesRegex(RuntimeError, 'outside the site source'):
                build.build(output)


if __name__ == '__main__':
    unittest.main()
