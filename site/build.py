"""Build the Pages site from canonical media, with content-addressed asset URLs."""

import argparse
from dataclasses import dataclass, replace
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
WIDE = ROOT / "hardware/enclosure/exports"
NARROW = ROOT / "designs/stacked/exports"
sys.path.insert(0, str(ROOT / "demo"))
from media import DARK_STYLES, verify_rainbow_motion, verify_masked_motion
from estimates import estimate_masses, runtime_hours
from publication import publish, seal


@dataclass(frozen=True)
class Movie:
    source: Path
    seconds: int
    poster_time: int = 0
    rainbow_scene: Path = None
    masked_style: str = None


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
    **{
        f"{design}_dark_{style}_movie": Movie(
            folder / f"infinity-rainbow-dark-{style}.mp4", 16,
            rainbow_scene=folder / "scene.json", masked_style=style,
        )
        for style in DARK_STYLES
        for design, folder in (("wide", WIDE), ("narrow", NARROW))
    },
}
SAMPLES = ROOT / '.build/energy-samples'


def verify_movie(movie):
    stream = json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_streams", "-of", "json", str(movie.source)
    ], text=True))["streams"][0]
    if (stream["width"], stream["height"], int(stream["nb_frames"])) != (1280, 720, movie.seconds * 24):
        raise RuntimeError(f"Unexpected clip dimensions or frame count: {movie.source}")
    if stream["r_frame_rate"] != "24/1" or stream["avg_frame_rate"] != "24/1":
        raise RuntimeError(f"Unexpected clip frame rate: {movie.source}")
    if abs(float(stream["duration"]) - movie.seconds) > 0.01:
        raise RuntimeError(f"Unexpected clip duration: {movie.source}")
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(movie.source),
                    "-f", "null", "-"], check=True)
    if movie.masked_style:
        verify_masked_motion(movie.source, movie.rainbow_scene, movie.masked_style)
    elif movie.rainbow_scene:
        verify_rainbow_motion(movie.source, movie.rainbow_scene)


def checked_bytes(source):
    data = source.read_bytes()
    if data.startswith(b"version https://git-lfs.github.com/spec/v1"):
        raise RuntimeError(f"Git LFS media is missing: {source.relative_to(ROOT)}")
    return data


def read_input(source, provenance):
    data = checked_bytes(source)
    name = source.relative_to(ROOT).as_posix()
    if hashlib.sha256(data).hexdigest() != provenance[name]:
        raise RuntimeError("Input changed before use: " + name)
    return data


def render_media(output, provenance):
    """Validate the captured bytes with each movie's duration and motion rules."""
    assets = output / "assets"
    assets.mkdir(exist_ok=True)
    values, records = {}, {}
    for key, media in MEDIA.items():
        source = media.source if isinstance(media, Movie) else media
        data = read_input(source, provenance)
        digest = hashlib.sha256(data).hexdigest()
        filename = key.replace("_", "-") + "-" + digest[:12] + source.suffix
        destination = assets / filename
        destination.write_bytes(data)
        values[key] = "assets/" + filename
        records[key] = {"source": source.relative_to(ROOT).as_posix(), "sha256": digest, "url": values[key]}
        if isinstance(media, Movie):
            scene_copy = None
            if media.rainbow_scene:
                scene_copy = output / ("." + key + "-scene.json")
                scene_copy.write_bytes(read_input(media.rainbow_scene, provenance))
            try:
                verify_movie(replace(media, source=destination, rainbow_scene=scene_copy))
            finally:
                if scene_copy:
                    scene_copy.unlink()
            poster = destination.with_suffix(".jpg")
            subprocess.run([
                "ffmpeg", "-y", "-v", "error", "-ss", str(media.poster_time), "-i", str(destination),
                "-frames:v", "1", "-q:v", "3", str(poster)
            ], check=True)
            values[key.replace("movie", "poster")] = "assets/" + poster.name
    return values, records


def render(output, provenance):
    output = output.resolve()
    # Render only into the private staging directory supplied by publish().
    output.mkdir(parents=True, exist_ok=True)
    values, records = render_media(output, provenance)
    dimensions = {}
    for name, folder in (("wide", WIDE), ("narrow", NARROW)):
        metadata = json.loads(read_input(folder / "scene.json", provenance))
        dimensions[name] = metadata["dimensions_m"]
        for label, field in (("width", "diameter"), ("depth", "body_depth")):
            values[name + "_" + label] = f"{metadata['dimensions_m'][field] * 1000:.1f}".removesuffix(".0")
        values[name + "_leds"] = str(len(metadata["leds"]))
        gap = (metadata["optics"]["front_z"] - metadata["optics"]["rear_z"]) * 1000
        values[name + "_gap"] = f"{gap:.1f}".removesuffix(".0")
    wide_parts = json.loads(read_input(WIDE / "parts.json", provenance))
    narrow_scene = json.loads(read_input(NARROW / "scene.json", provenance))
    narrow_parameters = json.loads(read_input(ROOT / "designs/stacked/parameters.json", provenance))
    material = json.loads(read_input(WIDE / "scene.json", provenance))["ring_materials"]["glow"]
    masses = estimate_masses(wide_parts, narrow_scene, narrow_parameters, material)
    # Legacy pouch calculation. SKI-1230 cell/model migration remains incomplete.
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
    template = read_input(SITE / "index.html", provenance).decode()
    rendered = re.sub(r"{{(\w+)}}", lambda match: html.escape(values[match[1]], quote=True), template)
    if "{{" in rendered:
        raise RuntimeError("Unresolved site template values")
    (output / "index.html").write_text(rendered)
    for name in ("styles.css", "app.js", "icon.svg", "calculator.js", "energy.mjs", "electrical-inputs.json"):
        (output / name).write_bytes(read_input(SITE / name, provenance))
    sample_manifest = read_input(SAMPLES / 'manifest.json', provenance)
    (output / 'pattern-samples.json').write_bytes(sample_manifest)
    (output / 'pattern-data').mkdir()
    for record in json.loads(sample_manifest)['sets']:
        (output / 'pattern-data' / record['file']).write_bytes(read_input(SAMPLES / record['file'], provenance))
    for reference in re.findall(r'(?:src|href|poster)="([^"]+)"', rendered):
        if reference.startswith(("https://", "http://", "#")):
            continue
        if not (output / reference).is_file():
            raise RuntimeError("Missing site asset: " + reference)
    (output / ".nojekyll").touch()
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    seal(output, {"commit": commit, "media": records, "dimensions_m": dimensions,
                  "inputs": provenance})


def source_snapshot(*, include_samples=True):
    """Hash both native generations and all site/model/docs inputs, rejecting LFS pointers."""
    paths = set()
    for relative in ("hardware/enclosure/exports-manifest.json", "designs/stacked/exports-manifest.json"):
        path = ROOT / relative
        manifest = json.loads(checked_bytes(path))
        paths.add(path)
        for name in (*manifest["inputs"], *manifest["exports"]):
            if Path(name).is_absolute() or ".." in Path(name).parts:
                raise RuntimeError("Unsafe native manifest input: " + name)
            paths.add(ROOT / name)
    paths.update(path for path in SITE.rglob("*") if path.is_file()
                 and not set(path.relative_to(SITE).parts) & {"__pycache__", ".build", "node_modules"})
    paths.update(ROOT / name for name in (
        "hardware/enclosure/battery-options.md", "hardware/enclosure/electrical-review.json",
        "hardware/enclosure/electrical-design.json", "hardware/enclosure/electrical_design.py",
        "hardware/enclosure/electrical-design.md",
        "hardware/enclosure/electrical_imu.py",
        "hardware/enclosure/imu_mount.py", "hardware/enclosure/imu-mounts.md",
        "hardware/enclosure/boost_mount.py", "hardware/enclosure/boost-mounts.md",
        "hardware/enclosure/BoostMountCheck.FCMacro",
        "hardware/enclosure/fastener_access.py",
        "hardware/enclosure/FastenerAccessCheck.FCMacro",
        "hardware/enclosure/capacitor_mount.py",
        "hardware/enclosure/capacitor-mounts.md",
        "hardware/enclosure/CapacitorMountCheck.FCMacro",
        "hardware/enclosure/sources/capacitor-fr-a/index.json",
        "hardware/enclosure/sources/capacitor-fr-a/README.md",
        "hardware/enclosure/sources/capacitor-fr-a/panasonic-fr-a-2025.pdf",
        "hardware/enclosure/sources/capacitor-fr-a/panasonic-safety-2025.pdf",
        "hardware/enclosure/sources/capacitor-fr-a/rs-pro-770787.pdf",
        "hardware/enclosure/electrical_boost.py",
        "hardware/enclosure/electrical_latch.py", "hardware/enclosure/latch_mount.py",
        "hardware/enclosure/latch-mounts.md",
        "hardware/enclosure/sources/latch-2808/index.json",
        "hardware/enclosure/sources/latch-2808/pololu-2808.step",
        "hardware/enclosure/sources/latch-2808/pololu-2808-pinout.jpg",
        "hardware/enclosure/sources/latch-2808/pololu-2808-dimensions.pdf",
        "hardware/enclosure/sources/latch-2808/camblock-plus-catalogue-15a.pdf",
        "hardware/enclosure/sources/powerboost-1000-basic/Adafruit PowerBoost 1000 Basic.brd",
        "hardware/enclosure/sources/powerboost-1000-basic/Adafruit PowerBoost 1000 Basic.sch",
        "hardware/enclosure/sources/powerboost-terminals/index.json",
        "hardware/enclosure/sources/powerboost-terminals/README.md",
        "hardware/enclosure/sources/powerboost-terminals/2444.html",
        "hardware/enclosure/sources/powerboost-terminals/2444-dimension.jpg",
        "hardware/enclosure/battery_access.py", "hardware/enclosure/battery_leads.py",
        "hardware/enclosure/battery-compartment.json", "hardware/enclosure/battery-access.md",
        "hardware/enclosure/sources/battery-contact-0854/index.json",
        "hardware/enclosure/sources/battery-contact-0854/mill-max-0854-2024.pdf",
        "hardware/enclosure/sources/lsm9ds1-classic/Adafruit LSM9DS1 Rev A.brd",
        "hardware/enclosure/sources/lsm9ds1-classic/Adafruit LSM9DS1 Rev A.sch",
        "hardware/enclosure/sources/lsm9ds1-classic/index.json",
        "hardware/enclosure/sources/lsm9ds1-classic/README.md",
        "hardware/enclosure/sources/lsm9ds1-classic/license.txt",
        "hardware/enclosure/sources/powerboost-1000-basic/extracted-connectivity.json",
        "hardware/enclosure/sources/powerboost-1000-basic/index.json",
        "hardware/enclosure/sources/powerboost-1000-basic/README.md",
        "hardware/enclosure/sources/powerboost-1000-basic/license.txt",
        "hardware/enclosure/electrical-control-study.json",
        "hardware/enclosure/electrical-control-revision.json",
        "hardware/enclosure/electrical_control.py",
        "hardware/enclosure/electrical-boost-interlock.json",
        "hardware/enclosure/electrical-headroom.json", "hardware/enclosure/electrical_headroom.py",
        "hardware/enclosure/electrical-reset-revision.json", "hardware/enclosure/electrical_reset.py",
        "hardware/enclosure/electrical-harness.json", "hardware/enclosure/electrical_path.py",
        "hardware/enclosure/electrical_board.py",
        "hardware/enclosure/sources/sparkle-motion/connectivity.json",
        "hardware/enclosure/sources/sparkle-motion/license.txt",
        "hardware/enclosure/sources/sparkle-motion/upstream-README.md",
        "hardware/enclosure/electrical-fault-coordination.json", "hardware/enclosure/electrical_fault.py",
        "hardware/enclosure/electrical-thermal.json", "hardware/enclosure/electrical_thermal.py",
        "hardware/enclosure/electrical-review.md", "hardware/enclosure/electrical.py",
        "hardware/enclosure/component-inventory.json", "hardware/enclosure/README.md",
        "designs/stacked/README.md", "demo/README.md", "design-v2.md",
    ))
    if include_samples:
        paths.add(SAMPLES / 'manifest.json')
        for record in json.loads(checked_bytes(SAMPLES / 'manifest.json'))['sets']:
            name = record['file']
            if Path(name).name != name or '\\' in name:
                raise RuntimeError('Unsafe pattern sample filename')
            paths.add(SAMPLES / name)
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(checked_bytes(path)).hexdigest()
            for path in sorted(paths)}


def build(output):
    if output.is_symlink():
        raise RuntimeError("Refusing a symlink as the Pages output directory")
    output = output.resolve()
    # Keep generated output out of the input tree; otherwise it would become a
    # recursive input and publication could overwrite the source checkout.
    if output == ROOT or output == SITE or SITE in output.parents:
        raise RuntimeError("Pages output must be outside the site source directory")
    source_before = source_snapshot(include_samples=False)
    for command in ("hardware/enclosure/electrical.py", "hardware/enclosure/cad.py", "designs/stacked/run.py"):
        subprocess.run([sys.executable, str(ROOT / command), "check"], cwd=ROOT, check=True)
    # Native owners may have regenerated scenes since a preliminary model check.
    # Generate samples from the complete, checked pair before freezing Pages inputs.
    subprocess.run([sys.executable, str(SITE / 'sample.py')], cwd=ROOT, check=True)
    subprocess.run(['node', str(SITE / 'energy.mjs'), '--check'], cwd=ROOT, check=True)
    before = source_snapshot()
    sample_prefix = SAMPLES.relative_to(ROOT).as_posix() + '/'
    if {name: value for name, value in before.items() if not name.startswith(sample_prefix)} != source_before:
        raise RuntimeError('Sources changed during Pages checks; previous release retained')
    def unchanged():
        if source_snapshot() != before:
            raise RuntimeError("Sources changed during Pages build; previous release retained")
    unchanged()
    publish(output, lambda stage: render(stage, before), unchanged)
    print(f"SITE BUILD PASS: {output}; complete artifact published with source and file hashes")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    build(parser.parse_args().output)
