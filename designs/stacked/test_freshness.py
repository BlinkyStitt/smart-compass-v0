"""Reject mixed antenna and upstream lighting generations after integration."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import run


class FreshnessTests(unittest.TestCase):
    def setUp(self):
        source_paths = [p.relative_to(run.ROOT) for p in run.inputs()]
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        here = self.root / "designs/stacked"
        exports = here / "exports"
        exports.mkdir(parents=True)
        for name in source_paths:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("source fixture: " + str(name))
        for name in run.EXPECTED:
            (exports / name).write_text("export fixture: " + name)
        patcher = patch.multiple(run, ROOT=self.root, HERE=here, EXPORTS=exports,
                                 MANIFEST=here / "exports-manifest.json")
        patcher.start()
        self.addCleanup(patcher.stop)
        run.MANIFEST.write_text(json.dumps({
            "format_version": 1,
            "inputs": run.hashes(run.inputs()),
            "exports": run.hashes(exports / name for name in run.EXPECTED),
        }))

    def test_complete_combined_snapshot_passes(self):
        run.check()

    def test_mixed_antenna_and_lighting_generations_fail(self):
        paths = (
            "hardware/enclosure/antenna.py",
            "hardware/enclosure/antenna_native.py",
            "hardware/enclosure/exports/scene.json",
            "designs/stacked/parameters.json",
            "designs/stacked/antenna_view.py",
            "designs/stacked/exports/antenna-placement.svg",
            "demo/patterns.gd",
            "demo/pattern_checks.gd",
            *("designs/stacked/exports/infinity-rainbow-dark-" + style + ".mp4"
              for style in ("sectors", "spirals", "diagonals")),
        )
        for name in paths:
            with self.subTest(path=name):
                path = self.root / name
                original = path.read_bytes()
                path.write_bytes(original + b"changed generation")
                try:
                    with self.assertRaisesRegex(RuntimeError, "stale"):
                        run.check()
                finally:
                    path.write_bytes(original)
