"""Verify the indexed Pride colour chase in decoded CAD frames."""
import json
import math
from pathlib import Path
import statistics
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'demo'))
from media import SAMPLE_FRAMES, _points, _sample_rgb
from pride import pride_frames


def colour_report(fields, region):
    correlations = []
    for channel in range(3):
        expected = [target[channel] for frame in fields for _, target in frame]
        observed = [rgb[channel] for frame in fields for rgb, _ in frame]
        ex, ob = statistics.mean(expected), statistics.mean(observed)
        variance = sum((x - ex) ** 2 for x in expected) * sum((y - ob) ** 2 for y in observed)
        correlations.append(sum((x - ex) * (y - ob) for x, y in zip(expected, observed)) /
                            math.sqrt(variance) if variance else 0)
    if min(correlations) < .45 or statistics.mean(correlations) < .65:
        raise RuntimeError(f'{region} has no indexed Pride chase: RGB correlations={correlations}')
    return correlations


def verify_pride_motion(movie, scene):
    metadata = json.loads(Path(scene).read_text())
    expected = pride_frames(metadata['counts'])
    # The shared camera registration returns the canonical position phase.
    # Recover physical LED identity from that unique phase, without changing
    # the canonical engineering renderer or its own rainbow validation.
    identities = {'board': {}, 'outer': {}}
    for led in metadata['leds']:
        group, index = int(led['group']), int(led['index'])
        x, y, _ = led['position_m']
        if group == 0:
            region = 'board'
            phase = math.atan2(x, y) / math.tau + 2 * math.hypot(x, y) / .0795
        elif group == len(metadata['counts']) - 1:
            region = 'outer'
            phase = math.atan2(x, y) / math.tau
        else:
            continue
        key = round(phase, 9)
        if key in identities[region]:
            raise RuntimeError('Ambiguous registered LED identity')
        identities[region][key] = (group, index)
    raw = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(movie),
        '-vf', "select='not(mod(n,8))+eq(n,383)',scale=640:360", '-frames:v', '49',
        '-fps_mode', 'vfr', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'])
    size = 640 * 360 * 3
    if len(raw) != size * len(SAMPLE_FRAMES):
        raise RuntimeError('Incomplete Pride samples')
    report = {}
    for region in ('board', 'outer'):
        fields = []
        for i, number in enumerate(SAMPLE_FRAMES):
            pixels = memoryview(raw)[i * size:(i + 1) * size]
            samples = _sample_rgb(pixels, _points(metadata, number)[region])
            frame = []
            for rgb, phase in samples:
                group, index = identities[region][round(phase, 9)]
                frame.append((rgb, expected[number][group][index]))
            fields.append(frame)
        report[region] = colour_report(fields, region)
    print('PRIDE CHASE PASS:', Path(movie).name, report, flush=True)
    return report
