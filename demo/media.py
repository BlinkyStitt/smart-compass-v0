"""Verify spatial rainbow rotation on the board and outside ring in saved clips."""

import colorsys
import json
import math
from pathlib import Path
import statistics
import subprocess

WIDTH, HEIGHT = 640, 360
DARK_STYLES = ("sectors", "spirals", "diagonals")
SAMPLE_FRAMES = tuple(range(0, 384, 8)) + (383,)


def _rotation_report(readings, region):
    if len(readings) < 16 or readings[-1]["frame"] - readings[0]["frame"] < 288:
        raise RuntimeError(f"Incomplete {region} rainbow observations")
    for start in (0, 96, 192, 288):
        if sum(start <= r["frame"] < start + 96 for r in readings) < 3:
            raise RuntimeError(f"Incomplete {region} rainbow observations in quarter {start // 96}")
    coherence = statistics.mean(r["coherence"] for r in readings)
    spread = statistics.mean(r["spread"] for r in readings)
    if coherence < 0.65 or spread < 0.015:
        raise RuntimeError(f"{region} has no coherent spatial rainbow")
    residual = [r["phase"] + r["frame"] / 192 for r in readings]
    real = statistics.mean(math.cos(math.tau * p) for p in residual)
    imaginary = statistics.mean(math.sin(math.tau * p) for p in residual)
    offset = math.atan2(imaginary, real) / math.tau
    errors = [(p - offset + 0.5) % 1 - 0.5 for p in residual]
    error = math.sqrt(statistics.mean(e * e for e in errors))
    static_fit = math.hypot(
        statistics.mean(math.cos(math.tau * r["phase"]) for r in readings),
        statistics.mean(math.sin(math.tau * r["phase"]) for r in readings),
    )
    moving_fit = math.hypot(real, imaginary)
    if error > 0.125 or moving_fit < static_fit + 0.3:
        raise RuntimeError(
            f"{region} rainbow did not rotate continuously: "
            f"phase error={error:.3f}, moving fit={moving_fit:.3f}, "
            f"static fit={static_fit:.3f}"
        )
    # Unwrap only after the independent circular fit rejects a stationary field.
    # This handles views where the outside sleeve is briefly hidden by the bezel.
    phases = [
        r["phase"] - round(r["phase"] + r["frame"] / 192 - offset)
        for r in readings
    ]
    times = [r["frame"] / 24 for r in readings]
    mean_time, mean_phase = statistics.mean(times), statistics.mean(phases)
    slope = sum(
        (t - mean_time) * (p - mean_phase) for t, p in zip(times, phases)
    ) / sum((t - mean_time) ** 2 for t in times)
    turns = -16 * slope
    if not 1.8 <= turns <= 2.2:
        raise RuntimeError(f"{region} rainbow did not rotate twice: {turns:.3f} turns")
    return {
        "turns": turns, "coherence": coherence, "spread": spread,
        "phase_error_turns": error, "observations": len(readings),
    }


def _points(metadata, frame, masked_style=None):
    # Register actual CAD locations through the shared figure-eight camera. The widest
    # luminous sleeve is the outside ring in either enclosure.
    sleeves = [p for p in metadata["parts"] if p["role"] in ("side", "sleeve")]
    sleeve = max(sleeves, key=lambda p: p["bounds_m"][1][0])
    radius = sleeve["bounds_m"][1][0]
    z = (sleeve["bounds_m"][0][2] + sleeve["bounds_m"][1][2]) / 2
    group = max(int(led["group"]) for led in metadata["leds"])
    source_z = metadata["optics"].get("source_z", metadata["optics"]["front_z"])
    phase = math.tau * frame / 384
    side = math.sin(phase)
    az = math.radians(35.0 * side - 15.0 * side * side)
    el = math.radians(20 * math.sin(2 * phase))
    camera = (
        0.46 * math.sin(az) * math.cos(el),
        0.46 * math.sin(el),
        0.0367 + 0.46 * math.cos(az) * math.cos(el),
    )
    right = (math.cos(az), 0, -math.sin(az))
    up = (
        -math.sin(az) * math.sin(el), math.cos(el), -math.cos(az) * math.sin(el)
    )
    forward = (
        -math.sin(az) * math.cos(el), -math.sin(el), -math.cos(az) * math.cos(el)
    )
    result = {"board": [], "outer": []}
    for led in metadata["leds"]:
        x, y, _ = led["position_m"]
        r = math.hypot(x, y)
        if int(led["group"]) == 0 and 0.020 < r < 0.070:
            region = "board"
            point = (x, y, source_z)
            base = math.atan2(x, y) / math.tau + 2 * r / 0.0795
        elif int(led["group"]) == group:
            region = "outer"
            point = (x / r * radius, y / r * radius, z)
            view = tuple(a - b for a, b in zip(camera, point))
            facing = (point[0] * view[0] + point[1] * view[1]) / (
                radius * math.sqrt(sum(v * v for v in view))
            )
            if facing < 0.15:
                continue
            base = math.atan2(x, y) / math.tau
        else:
            continue
        delta = tuple(a - b for a, b in zip(point, camera))
        depth = sum(a * b for a, b in zip(delta, forward))
        scale = HEIGHT / (2 * depth * math.tan(math.radians(19)))
        px = round(WIDTH / 2 + sum(a * b for a, b in zip(delta, right)) * scale)
        py = round(HEIGHT / 2 - sum(a * b for a, b in zip(delta, up)) * scale)
        if 1 <= px < WIDTH - 1 and 1 <= py < HEIGHT - 1:
            if masked_style:
                # Independent reference to the documented position/time masks;
                # compare brightness intent, allowing fixed stored-glow offsets.
                angle = math.atan2(x, y) / math.tau
                qx, qy = (x / .0795, y / .0795) if region == "board" else (x / r, y / r)
                t = frame / 192
                phase = {"sectors": 2 * angle - t,
                         "spirals": 3 * angle - 2 * math.hypot(qx, qy) + t,
                         "diagonals": .75 * (qx + qy) - t}[masked_style]
                edge = max(0, min(1, (abs((phase + .5) % 1 - .5) - .18) / .08))
                base = edge * edge * (3 - 2 * edge)
            result[region].append((px, py, base))
    return result


def _sample_rgb(frame, points):
    return [
        ([
            sum(
                frame[((py + dy) * WIDTH + px + dx) * 3 + k]
                for dy in (-1, 0, 1) for dx in (-1, 0, 1)
            ) / 9 / 255
            for k in range(3)
        ], base)
        for px, py, base in points
    ]


def _colour_bounds(samples):
    # Fixed absorption and phosphor emission shift each channel's range.
    # Recover the observed rainbow gamut without using any timestamps or
    # expected phases. Raw output HSV would mistake filtered magenta for peach.
    colours = [rgb for frame in samples for rgb, _ in frame]
    if not colours:
        raise RuntimeError("No visible rainbow samples")
    low = [min(rgb[k] for rgb in colours) for k in range(3)]
    high = [max(rgb[k] for rgb in colours) for k in range(3)]
    if min(b - a for a, b in zip(low, high)) < 0.02:
        raise RuntimeError("Insufficient rainbow channel range")
    return low, high


def _read_phase(samples, bounds):
    low, high = bounds
    values = []
    for rgb, base in samples:
        colour = [(rgb[k] - low[k]) / (high[k] - low[k]) for k in range(3)]
        hue, saturation, value = colorsys.rgb_to_hsv(*colour)
        if saturation < 0.15 or value < 0.12:
            continue
        values.append((hue, hue - base, saturation * value))
    if len(values) < 3:
        raise RuntimeError("Too few visible rainbow samples")
    total = sum(w for _, _, w in values)
    real = sum(w * math.cos(math.tau * phase) for _, phase, w in values)
    imaginary = sum(w * math.sin(math.tau * phase) for _, phase, w in values)
    colour_real = sum(w * math.cos(math.tau * hue) for hue, _, w in values)
    colour_imaginary = sum(w * math.sin(math.tau * hue) for hue, _, w in values)
    return {
        "phase": math.atan2(imaginary, real) / math.tau,
        "coherence": math.hypot(real, imaginary) / total,
        "spread": 1 - math.hypot(colour_real, colour_imaginary) / total,
        "samples": len(values),
    }


def verify_rainbow_motion(movie, scene):
    """Track each spatial rainbow through the actual moving camera views."""
    metadata = json.loads(Path(scene).read_text())
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(movie),
        "-vf", "select='not(mod(n,8))+eq(n,383)',scale=640:360", "-frames:v", "49",
        "-fps_mode", "vfr", "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])
    size = WIDTH * HEIGHT * 3
    if len(raw) != size * len(SAMPLE_FRAMES):
        raise RuntimeError("Incomplete rainbow motion samples: " + str(movie))
    frames = [
        memoryview(raw)[i * size:(i + 1) * size]
        for i in range(len(SAMPLE_FRAMES))
    ]
    report = {}
    for region in ("board", "outer"):
        readings = []
        samples = [
            _sample_rgb(frame, _points(metadata, number)[region])
            for number, frame in zip(SAMPLE_FRAMES, frames)
        ]
        bounds = _colour_bounds(samples)
        for number, colours in zip(SAMPLE_FRAMES, samples):
            if len(colours) < 3:
                continue
            try:
                reading = _read_phase(colours, bounds)
            except RuntimeError:
                continue
            if reading["coherence"] < 0.65:
                continue
            readings.append(dict(reading, frame=number))
        report[region] = _rotation_report(readings, region)
        print(
            f"MOVIE ROTATION PASS: {Path(movie).name}; {region}: "
            f"{report[region]['turns']:.3f} turns; "
            f"spatial coherence {report[region]['coherence']:.3f}; "
            f"phase error {report[region]['phase_error_turns']:.3f}",
            flush=True,
        )
    return report


def _masked_report(samples, region):
    """Require the moving dark shape in registered CAD locations, not black pixels."""
    low, high = _colour_bounds(samples)
    expected, observed = [], []
    for colours in samples:
        for rgb, mask in colours:
            expected.append(mask)
            observed.append(max((rgb[k] - low[k]) / (high[k] - low[k]) for k in range(3)))
    mx, my = statistics.mean(expected), statistics.mean(observed)
    variance = sum((x - mx) ** 2 for x in expected) * sum((y - my) ** 2 for y in observed)
    correlation = (sum((x - mx) * (y - my) for x, y in zip(expected, observed)) /
                   math.sqrt(variance)) if variance else 0
    if correlation < .45:
        raise RuntimeError(f"{region} moving dark mask mismatch: correlation={correlation:.3f}")
    return correlation


def verify_masked_motion(movie, scene, style):
    """Check mask identity/motion on board and outside ring, plus the cycle join.

    Source-level Godot checks cover exact-black intent and every mapped row.
    Rendered samples include diffusion and stored glow; they need not be black.
    Canonical rainbow rotation remains a separate, unchanged validation path.
    """
    if style not in DARK_STYLES:
        raise RuntimeError("Unknown dark rainbow style: " + style)
    metadata = json.loads(Path(scene).read_text())
    raw = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(movie),
        "-vf", "select='not(mod(n,8))+eq(n,383)',scale=640:360", "-frames:v", "49",
        "-fps_mode", "vfr", "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ])
    size = WIDTH * HEIGHT * 3
    if len(raw) != size * len(SAMPLE_FRAMES):
        raise RuntimeError("Incomplete masked motion samples: " + str(movie))
    frames = [memoryview(raw)[i * size:(i + 1) * size] for i in range(len(SAMPLE_FRAMES))]
    report = {}
    for region in ("board", "outer"):
        samples = [_sample_rgb(frame, _points(metadata, n, style)[region])
                   for n, frame in zip(SAMPLE_FRAMES, frames)]
        report[region] = _masked_report(samples, region)
    # A one-frame join should be smaller than a normal eight-frame motion step.
    difference = lambda a, b: statistics.mean(abs(x - y) for x, y in zip(a, b))
    join = difference(frames[0], frames[-1])
    step = statistics.mean(difference(a, b) for a, b in zip(frames[:-2], frames[1:-1]))
    if join > max(2, step):
        raise RuntimeError(f"Discontinuous masked loop boundary: {movie}; {join:.3f} > {step:.3f}")
    print(f"MOVIE MASK PASS: {Path(movie).name}; {report}; join={join:.3f}", flush=True)
    return report
