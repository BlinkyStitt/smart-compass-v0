"""Pride2015 on physical LED indices, adapted from Mark Kriegsman's FastLED example.

This floating-point, fixed-step preview follows the original colour/brightness
oscillators and RGB trail blend. It is not bit-exact FastLED firmware. See
PRIDE-LICENSE.txt and README.md for sources and preview-only loop blending.
"""
import colorsys
import math

FPS = 24
TICKS = 120
FRAMES = 384


def beat(bpm88, low, high, seconds):
    return low + (high - low) * (.5 + .5 * math.sin(math.tau * seconds * bpm88 / (256 * 60)))


def pride_frames(counts):
    """Return one seamless 16-second loop; no LED is masked or switched off."""
    colours = [[[.2, .2, .2] for _ in range(count)] for count in counts]
    pseudo, hue = 0.0, 0.0
    raw = []
    # One second of warm-up, then an extra second preceding the clip. The
    # preceding frames form a moving crossfade at the loop join.
    for tick in range((FRAMES + 48) * (TICKS // FPS)):
        seconds = tick / TICKS
        pseudo += 1000 / TICKS * beat(147, 23, 60, seconds)
        hue += 1000 / TICKS * beat(400, 5, 9, seconds)
        saturation = beat(87, 220, 250, seconds) / 255
        depth = beat(341, 96, 224, seconds) / 255
        theta_increment = beat(203, 25 * 256, 40 * 256, seconds)
        hue_increment = beat(113, 1, 3000, seconds)
        for row in colours:
            for index in range(len(row)):
                # The original sketch writes its strip in reverse order.
                step = len(row) - index
                theta = math.tau * (pseudo + step * theta_increment) / 65536
                pulse = (.5 + .5 * math.sin(theta)) ** 2
                value = (1 - depth) + depth * pulse
                target = colorsys.hsv_to_rgb(((hue + step * hue_increment) / 65536) % 1,
                                            saturation, value)
                row[index] = [old * .75 + new * .25 for old, new in zip(row[index], target)]
        if tick >= TICKS and (tick + 1) % (TICKS // FPS) == 0:
            raw.append([[rgb[:] for rgb in row] for row in colours])
    output = raw[24:24 + FRAMES]
    for frame in range(FRAMES - 24, FRAMES):
        weight = (frame - (FRAMES - 24)) / 24
        weight = weight * weight * (3 - 2 * weight)
        previous = raw[frame - (FRAMES - 24)]
        output[frame] = [[[a * (1 - weight) + b * weight for a, b in zip(rgb, previous[g][i])]
                          for i, rgb in enumerate(row)] for g, row in enumerate(output[frame])]
    return output
