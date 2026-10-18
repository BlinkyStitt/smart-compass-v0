"""Keep assembly and rainbow media validation distinct and strict."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from build import MEDIA, NARROW, WIDE, Movie, build, verify_movie


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
                    build(Path(directory) / "pages")
                source.write_bytes(b"version https://git-lfs.github.com/spec/v1\noid sha256:missing\n")
                with patch("build.ROOT", Path(directory)):
                    with self.assertRaisesRegex(RuntimeError, "Git LFS media is missing"):
                        build(Path(directory) / "pages")


if __name__ == "__main__":
    unittest.main()
