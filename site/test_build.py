"""Keep assembly and rainbow media validation distinct and strict."""

import json
from pathlib import Path
import unittest
from unittest.mock import patch

from build import Movie, verify_movie


class MovieTests(unittest.TestCase):
    def probe(self, frames=576, seconds=24):
        return json.dumps({"streams": [{"width": 1280, "height": 720,
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


if __name__ == "__main__":
    unittest.main()
