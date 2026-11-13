"""Load as code.py on the full Adafruit Sparkle Motion."""

import json
import math
import time

import board
import digitalio
import neopixel

from power_policy import PIXEL_COUNTS, rainbow_frame

wall_status = digitalio.DigitalInOut(board.D18)
wall_status.switch_to_input(pull=digitalio.Pull.UP)

with open("/led-layout.json") as stream:
    layout = json.load(stream)

if tuple(map(len, layout)) != PIXEL_COUNTS:
    raise ValueError("LED map does not match the four Rev A harness outputs")

phases = [
    [math.atan2(x, y) / (2 * math.pi)
     + (2 * math.sqrt(x * x + y * y) / 0.0795 if group == 0 else 0)
     for x, y in xy]
    for group, xy in enumerate(layout)
]
outputs = [
    neopixel.NeoPixel(pin, count, auto_write=False, pixel_order=neopixel.GRB)
    for pin, count in zip((board.SIG1, board.SIG2, board.SIG3, board.D23), PIXEL_COUNTS)
]
# Keep battery limits until wall power has been stable for 250 ms. Fall
# back on the first high reading and check again before each strip write.
wall_since = None
start = time.monotonic()
while True:
    now = time.monotonic()
    if wall_status.value:
        wall_since = None
    elif wall_since is None:
        wall_since = now
    wall = wall_since is not None and now - wall_since >= 0.25
    colors = rainbow_frame(phases, now - start, wall)
    for pixels, frame in zip(outputs, colors):
        if wall and wall_status.value:
            wall_since = None
            break
        pixels[:] = frame
        pixels.show()
    time.sleep(0.01)
