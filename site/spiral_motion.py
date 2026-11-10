"""Require a travelling light wave, beyond global rainbow hue changes."""
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'demo'))
from media import SAMPLE_FRAMES, _points, _sample_rgb, _colour_bounds


def wave_level(spatial, frame):
    crest = .5 + .5 * math.cos(math.tau * (spatial - frame / 96))
    return .45 + .55 * crest ** 3


def wave_report(fields, region):
    bounds = _colour_bounds(fields)
    expected, observed = [], []
    for frame in fields:
        for rgb, level in frame:
            expected.append(level)
            observed.append(max((rgb[k] - bounds[0][k]) / (bounds[1][k] - bounds[0][k]) for k in range(3)))
    ex, ob = statistics.mean(expected), statistics.mean(observed)
    variance = sum((x - ex) ** 2 for x in expected) * sum((y - ob) ** 2 for y in observed)
    correlation = sum((x - ex) * (y - ob) for x, y in zip(expected, observed)) / math.sqrt(variance) if variance else 0
    if correlation < .5:
        raise RuntimeError(f'{region} has no travelling spiral light wave: correlation={correlation:.3f}')
    return correlation


def verify_spiral_wave(movie, scene):
    metadata = json.loads(Path(scene).read_text())
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(movie),
        '-vf', "select='not(mod(n,8))+eq(n,383)',scale=640:360", '-frames:v', '49',
        '-fps_mode', 'vfr', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
    size = 640 * 360 * 3
    if len(raw) != size * len(SAMPLE_FRAMES):
        raise RuntimeError('Incomplete travelling spiral samples')
    report = {}
    for region in ('board', 'outer'):
        fields = []
        for i, number in enumerate(SAMPLE_FRAMES):
            pixels = memoryview(raw)[i * size:(i + 1) * size]
            samples = _sample_rgb(pixels, _points(metadata, number)[region])
            fields.append([(rgb, wave_level(base, number)) for rgb, base in samples])
        report[region] = wave_report(fields, region)
    print('TRAVELLING SPIRAL PASS:', Path(movie).name, report, flush=True)
    return report
