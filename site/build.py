"""Build the Pages site from canonical media, with content-addressed asset URLs."""

import argparse
from dataclasses import dataclass
import hashlib
import html
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
WIDE = ROOT / "hardware/enclosure/exports"
NARROW = ROOT / "designs/stacked/exports"
sys.path.insert(0, str(ROOT / "demo"))
from media import verify_rainbow_motion
from estimates import estimate_masses, runtime_hours


@dataclass(frozen=True)
class Movie:
    source: Path
    seconds: int
    poster_time: int = 0
    rainbow_scene: Path = None


MEDIA = {
    "wide_movie": Movie(WIDE / "infinity-rainbow.mp4", 16, rainbow_scene=WIDE / "scene.json"),
    "narrow_movie": Movie(NARROW / "infinity-rainbow.mp4", 16, rainbow_scene=NARROW / "scene.json"),
    "silver_movie": Movie(WIDE / "infinity-rainbow-silver.mp4", 16, rainbow_scene=WIDE / "scene.json"),
    "silver_narrow_movie": Movie(SITE / "assets/narrow-silver.mp4", 16, rainbow_scene=NARROW / "scene.json"),
    "assembly_movie": Movie(SITE / "assets/exploded-assembly.mp4", 24, poster_time=12),
    "wide_worn": SITE / "assets/wide-worn.png",
    "narrow_worn": SITE / "assets/narrow-worn.png",
    "narrow_side": NARROW / "night-side.png",
    "size_comparison": SITE / "assets/size-comparison.png",
}


def verify_movie(movie):
    stream = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_streams", "-of", "json", str(movie.source)
    ], text=True))["streams"][0]
    if (stream["width"], stream["height"], int(stream["nb_frames"])) != (1280, 720, movie.seconds * 24):
        raise RuntimeError(f"Unexpected clip dimensions or frame count: {movie.source}")
    if abs(float(stream["duration"]) - movie.seconds) > 0.01:
        raise RuntimeError(f"Unexpected clip duration: {movie.source}")
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(movie.source),
                    "-f", "null", "-"], check=True)
    if movie.rainbow_scene:
        verify_rainbow_motion(movie.source, movie.rainbow_scene)


def checked_bytes(source):
    data = source.read_bytes()
    if data.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise RuntimeError(f"Git LFS media is missing: {source.relative_to(ROOT)}")
    return data


def build(output):
    output = output.resolve()
    # Never delete a directory chosen by the caller. Replace owned files only.
    output.mkdir(parents=True, exist_ok=True)
    assets = output / "assets"
    assets.mkdir(exist_ok=True)
    values, records = {}, {}
    for key, media in MEDIA.items():
        source = media.source if isinstance(media, Movie) else media
        data = checked_bytes(source)
        digest = hashlib.sha256(data).hexdigest()
        filename = key.replace("_", "-") + "-" + digest[:12] + source.suffix
        destination = assets / filename
        destination.write_bytes(data)
        values[key] = "assets/" + filename
        records[key] = {"source": source.relative_to(ROOT).as_posix(), "sha256": digest, "url": values[key]}
        if isinstance(media, Movie):
            verify_movie(media)
            poster = destination.with_suffix(".jpg")
            subprocess.run([
                "ffmpeg", "-y", "-v", "error", "-ss", str(media.poster_time), "-i", str(source),
                "-frames:v", "1", "-q:v", "3", str(poster)
            ], check=True)
            values[key.replace("movie", "poster")] = "assets/" + poster.name
    dimensions = {}
    for name, folder in (("wide", WIDE), ("narrow", NARROW)):
        metadata = json.loads((folder / "scene.json").read_text())
        dimensions[name] = metadata["dimensions_m"]
        for label, field in (("width", "diameter"), ("depth", "body_depth")):
            values[name + "_" + label] = f"{metadata['dimensions_m'][field] * 1000:.1f}".removesuffix(".0")
        values[name + "_leds"] = str(len(metadata["leds"]))
        gap = (metadata["optics"]["front_z"] - metadata["optics"]["rear_z"]) * 1000
        values[name + "_gap"] = f"{gap:.1f}".removesuffix(".0")
    wide_parts = json.loads((WIDE / "parts.json").read_text())
    narrow_scene = json.loads((NARROW / "scene.json").read_text())
    narrow_parameters = json.loads((ROOT / "designs/stacked/parameters.json").read_text())
    material = json.loads((WIDE / "scene.json").read_text())["ring_materials"]["glow"]
    masses = estimate_masses(wide_parts, narrow_scene, narrow_parameters, material)
    # Sizing assumptions from hardware/enclosure/battery-options.md.
    battery = {"cell_wh": 37.0, "efficiency": 0.85, "total_amps": 1.25, "volts": 5.0}
    hours = runtime_hours(**battery)
    for name, mass in masses.items():
        values[name + "_weight"] = f"{mass['complete_pendant']['nominal_g'] / 1000:.2f}"
        values[name + "_worn_weight"] = f"{mass['total_worn']['nominal_g'] / 1000:.2f}"
        values[name + "_weight_range"] = "–".join(f"{n / 1000:.2f}" for n in mass["complete_pendant"]["range_g"])
    pack = next(row for row in wide_parts["components"] if row["id"] == "battery")
    values["battery_weight"] = f"{pack['installed_mass_g']:.0f}"
    values["runtime"] = f"{hours:.1f}"
    (output / "estimates.json").write_text(json.dumps({
        "masses": masses, "runtime_assumptions": battery, "calculated_hours": hours,
        "narrow_basis": "Narrow CAD materials and strip lengths; wide electronics, harness and fitting allowances transferred provisionally",
    }, indent=2) + "\n")
    template = (SITE / "index.html").read_text()
    rendered = re.sub(r"{{(\w+)}}", lambda match: html.escape(values[match[1]], quote=True), template)
    if "{{" in rendered:
        raise RuntimeError("Unresolved site template values")
    (output / "index.html").write_text(rendered)
    for name in ("styles.css", "app.js", "icon.svg"):
        shutil.copyfile(SITE / name, output / name)
    for reference in re.findall(r'(?:src|href|poster)="([^"]+)"', rendered):
        if reference.startswith(("https://", "http://", "#")):
            continue
        if not (output / reference).is_file():
            raise RuntimeError("Missing site asset: " + reference)
    (output / ".nojekyll").touch()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    (output / "build-info.json").write_text(json.dumps({"commit": commit, "media": records, "dimensions_m": dimensions}, indent=2) + "\n")
    print(f"SITE BUILD PASS: {output}; five verified MP4 loops and four comparison images")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
