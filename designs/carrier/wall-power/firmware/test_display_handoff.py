"""Run the CircuitPython entry point with a clock and GPIO/LED test doubles."""

from contextlib import ExitStack
import io
import json
from pathlib import Path
import runpy
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from export_layout import ordered_positions
from power_policy import BATTERY_DRIVE, WALL_DRIVE

HERE = Path(__file__).resolve().parent


class DisplayHandoffTests(unittest.TestCase):
    def test_wall_loss_during_frame_and_requalification(self):
        scene = HERE.parents[2] / "stacked/exports/scene.json"
        layout = ordered_positions(json.loads(scene.read_text()))
        pins = ("SIG1", "SIG2", "SIG3", "D23")
        board = SimpleNamespace(D18="D18", **{pin: pin for pin in pins})
        samples = []
        frames = []
        now = 0
        wall_present = False

        class Finished(Exception):
            pass

        class Input:
            def __init__(self, pin):
                if pin != board.D18:
                    raise ValueError(f"Unexpected wall status pin: {pin}")

            def switch_to_input(self, *, pull):
                if pull != "up":
                    raise ValueError("An open wall status lead must select battery mode")

            @property
            def value(self):
                return not wall_present

        class Pixels:
            def __init__(self, pin, count, *, auto_write, pixel_order):
                self.pin = pin
                self.count = count
                if auto_write or pixel_order != "GRB":
                    raise ValueError("Unexpected NeoPixel setup")

            def __setitem__(self, key, colors):
                if key != slice(None) or len(colors) != self.count:
                    raise ValueError("Expected one complete strip frame")
                self.colors = colors

            def show(self):
                nonlocal wall_present
                drive = max(max(pixel) for pixel in self.colors)
                samples.append((self.pin, drive))
                if now == 1.25 and self.pin == pins[0]:
                    wall_present = False

        # Use binary-exact timestamps on either side of the 250 ms boundary.
        inputs = iter([
            (1, True), (1.2490234375, True), (1.25, True), (1.265625, False),
            (2, True), (2.2490234375, True), (2.25, True),
        ])

        def advance(_seconds):
            nonlocal now, wall_present
            frames.append(samples.copy())
            samples.clear()
            try:
                now, wall_present = next(inputs)
            except StopIteration:
                raise Finished from None

        digitalio = SimpleNamespace(DigitalInOut=Input, Pull=SimpleNamespace(UP="up"))
        neopixel = SimpleNamespace(NeoPixel=Pixels, GRB="GRB")
        with ExitStack() as stack:
            stack.enter_context(patch.dict(sys.modules, board=board, digitalio=digitalio,
                                           neopixel=neopixel))
            stack.enter_context(patch("time.monotonic", lambda: now))
            stack.enter_context(patch("time.sleep", advance))
            open_layout = stack.enter_context(
                patch("builtins.open", return_value=io.StringIO(json.dumps(layout)))
            )
            with self.assertRaises(Finished):
                runpy.run_path(str(HERE / "code.py"))
            open_layout.assert_called_once_with("/led-layout.json")

        battery = [(pin, BATTERY_DRIVE) for pin in pins]
        wall = [(pin, WALL_DRIVE) for pin in pins]
        self.assertEqual(frames, [battery, battery, battery, wall[:1],
                                  battery, battery, battery, wall])
