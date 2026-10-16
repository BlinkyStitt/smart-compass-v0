"""Build the Pages site from canonical media, with content-addressed asset URLs."""

import argparse
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

MEDIA = {
    "wide_movie": WIDE / "infinity-rainbow.mp4",
    "narrow_movie": NARROW / "infinity-rainbow.mp4",
    "silver_movie": WIDE / "infinity-rainbow-silver.mp4",
    "wide_worn": WIDE / "night-mannequin.png",
    "narrow_worn": NARROW / "night-mannequin.png",
    "narrow_exploded": NARROW / "exploded.png",
    "narrow_side": NARROW / "night-side.png",
    "size_comparison": SITE / "assets/size-comparison.png",
}


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
    for key, source in MEDIA.items():
        data = checked_bytes(source)
        digest = hashlib.sha256(data).hexdigest()
        filename = key.replace("_", "-") + "-" + digest[:12] + source.suffix
        destination = assets / filename
        destination.write_bytes(data)
        values[key] = "assets/" + filename
        records[key] = {"source": source.relative_to(ROOT).as_posix(), "sha256": digest, "url": values[key]}
        if source.suffix == ".mp4":
            stream = json.loads(subprocess.check_output([
                "ffprobe", "-v", "error", "-show_streams", "-of", "json", str(source)
            ], text=True))["streams"][0]
            if (stream["width"], stream["height"], int(stream["nb_frames"])) != (1280, 720, 384):
                raise RuntimeError(f"Unexpected clip dimensions or frame count: {source}")
            if abs(float(stream["duration"]) - 16) > 0.01:
                raise RuntimeError(f"Unexpected clip duration: {source}")
            verify_rainbow_motion(source, source.parent / "scene.json")
            poster = destination.with_suffix(".jpg")
            subprocess.run([
                "ffmpeg", "-y", "-v", "error", "-i", str(source),
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
    print(f"SITE BUILD PASS: {output}; three verified MP4 loops and five comparison images")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
