"""Build the Pages site from canonical media, with content-addressed asset URLs."""

import argparse
from dataclasses import dataclass, replace
import hashlib
import html
import json
from pathlib import Path
import re
import subprocess
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
WIDE = ROOT / "hardware/enclosure/exports"
NARROW = ROOT / "designs/stacked/exports"
sys.path.insert(0, str(ROOT / "demo"))
from media import DARK_STYLES, verify_rainbow_motion, verify_masked_motion
from estimates import estimate_masses
from publication import publish, seal
from spiral_motion import verify_pride_motion
from explosion import CAPTURE_INPUTS, FRAMES as ASSEMBLY_FRAMES, SECONDS as ASSEMBLY_SECONDS, verify_capture


@dataclass(frozen=True)
class Movie:
    source: Path
    seconds: int
    poster_time: int = 0
    rainbow_scene: Path = None
    masked_style: str = None
    travelling_spiral: bool = False


MEDIA = {
    "app_script": SITE / "app.js",
    "narrow_movie": Movie(SITE / "assets/rainbow-spiral.mp4", 16,
                          rainbow_scene=NARROW / "scene.json", travelling_spiral=True),
    "silver_narrow_movie": Movie(NARROW / "infinity-rainbow-silver.mp4", 16, rainbow_scene=NARROW / "scene.json"),
    "assembly_movie": Movie(SITE / "assets/exploded-assembly.mp4", ASSEMBLY_SECONDS, poster_time=8),
    "narrow_worn": NARROW / "night-mannequin.png",
    "narrow_side": NARROW / "night-side.png",
    **{
        f"{design}_dark_{style}_movie": Movie(
            folder / f"infinity-rainbow-dark-{style}.mp4", 16,
            rainbow_scene=folder / "scene.json", masked_style=style,
        )
        for style in DARK_STYLES
        for design, folder in (("narrow", NARROW),)
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
    elif movie.travelling_spiral:
        verify_pride_motion(movie.source, movie.rainbow_scene)
    elif movie.rainbow_scene:
        verify_rainbow_motion(movie.source, movie.rainbow_scene)


def verify_assembly_motion(source):
    """Reject a still, missing opening, or a loop that does not close again."""
    frames = subprocess.check_output([
        "ffmpeg", "-v", "error", "-i", str(source),
        "-vf", rf"select=eq(n\,0)+eq(n\,192)+eq(n\,{ASSEMBLY_FRAMES - 1}),scale=160:90",
        "-fps_mode", "passthrough", "-pix_fmt", "rgb24", "-f", "rawvideo", "-",
    ])
    size = 160 * 90 * 3
    if len(frames) != size * 3:
        raise RuntimeError("Assembly must include closed, open and reclosed frames")
    first, middle, last = [frames[i * size:(i + 1) * size] for i in range(3)]
    difference = lambda a, b: sum(abs(x - y) for x, y in zip(a, b)) / size
    opening = difference(first, middle)
    if opening < 3 or difference(middle, last) < 3 or difference(first, last) > opening * .1:
        raise RuntimeError("Assembly animation must open and return to the closed pose")


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
            if key == "assembly_movie":
                verify_assembly_motion(destination)
                proof = json.loads(read_input(SITE / 'assets/exploded-assembly.json', provenance))
                inputs = {name: hashlib.sha256(read_input(ROOT / name, provenance)).hexdigest()
                          for name in CAPTURE_INPUTS}
                scene = json.loads(read_input(NARROW / 'scene.json', provenance))
                verify_capture(proof, scene, digest, inputs)
                records[key]['fitted_cad_parts'] = proof['fitted_cad_parts']
                records[key]['separate_units'] = proof['separate_units']
    return values, records


def render_diagrams(output, provenance):
    """Rasterize captured CAD at build time; phones never decode native SVGs."""
    values, records = {}, {}
    for name in ('service-guide', 'assembly-dimensions'):
        source = NARROW / (name + '.svg')
        data = read_input(source, provenance)
        png = subprocess.check_output(['node', str(SITE / 'render_diagram.mjs')], input=data)
        if len(png) < 24 or png[:16] != b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR':
            raise RuntimeError('Diagram renderer did not produce a PNG: ' + name)
        width, height = struct.unpack('>II', png[16:24])
        if width != 1600 or not 0 < height <= 1600 or len(png) > 2_000_000:
            raise RuntimeError('Diagram preview exceeds its image budget: ' + name)
        digest = hashlib.sha256(png).hexdigest()
        url = 'assets/' + name + '-' + digest[:12] + '.png'
        (output / url).write_bytes(png)
        key = name.replace('-', '_')
        values[key] = url
        records[key] = {'source': source.relative_to(ROOT).as_posix(),
                        'source_sha256': hashlib.sha256(data).hexdigest(),
                        'sha256': digest, 'url': url}
    return values, records


def render(output, provenance):
    output = output.resolve()
    # Render only into the private staging directory supplied by publish().
    output.mkdir(parents=True, exist_ok=True)
    values, records = render_media(output, provenance)
    diagrams, diagram_records = render_diagrams(output, provenance)
    values.update(diagrams)
    records.update(diagram_records)
    dimensions = {}
    for name, folder in (("wide", WIDE), ("narrow", NARROW)):
        metadata = json.loads(read_input(folder / "scene.json", provenance))
        dimensions[name] = metadata["dimensions_m"]
        for label, field in (("width", "diameter"), ("depth", "body_depth")):
            values[name + "_" + label] = f"{metadata['dimensions_m'][field] * 1000:.1f}".removesuffix(".0")
        values[name + "_leds"] = str(len(metadata["leds"]))
        gap = (metadata["optics"]["front_z"] - metadata["optics"]["rear_z"]) * 1000
        values[name + "_gap"] = f"{gap:.1f}".removesuffix(".0")
    parts=json.loads(read_input(NARROW/'parts.json',provenance))
    variants=estimate_masses(parts);mass=variants['glow']['mass_estimate'];cell=next(row for row in variants['glow']['components'] if row['id']=='cell')
    study=subprocess.run(['node',str(SITE/'sample_check.mjs'),str(SAMPLES/'manifest.json')],text=True,capture_output=True,check=True)
    energy=json.loads(study.stdout)
    if not energy['converged']:raise RuntimeError('Pattern energy estimates have not converged')
    rainbow=next(row for row in energy['convergence'] if row['design']=='narrow' and row['pattern']=='rainbow')
    values['narrow_weight']=f"{mass['complete_pendant']['nominal_g']/1000:.2f}"
    values['narrow_worn_weight']=f"{mass['total_worn']['nominal_g']/1000:.2f}"
    values['narrow_worn_g']=f"{mass['total_worn']['nominal_g']:.1f}"
    values['narrow_worn_lb']=f"{mass['total_worn']['nominal_g']/453.59237:.3f}"
    values['narrow_upper_g']=f"{mass['upper_worn_g']:.1f}"
    values['narrow_margin_g']=f"{mass['margin_g']:.1f}"
    values['narrow_margin_target']='met' if mass['margin_target_pass'] else 'not met'
    values['narrow_weight_range']='–'.join(f"{n:.1f}" for n in mass['total_worn']['range_g'])
    values['battery_weight']=f"{cell['mass_g_per_unit']:.1f}"
    values['battery_upper_g']=f"{cell['mass_range_g_per_unit'][1]:.1f}"
    values['runtime']=f"{rainbow['runtime']['hours']:.2f}"
    values['narrow_closed_depth']=f"{parts['dimensions_mm']['closed_depth']:.1f}"
    values['narrow_closed_size']=' × '.join(f"{parts['dimensions_mm'][key]:.1f}" for key in ['closed_width','closed_height','closed_depth'])
    values['narrow_service_size']=' × '.join(f'{value:.1f}' for value in parts['service_clearance']['width_height_depth_mm'])
    values['narrow_silver_upper_g']=f"{variants['silver']['mass_estimate']['upper_worn_g']:.1f}"
    (output/'estimates.json').write_text(json.dumps({'active_design':'narrow','masses':{'narrow':mass},'material_variants':{key:value['mass_estimate'] for key,value in variants.items()},'runtime_assumptions':json.loads(read_input(SITE/'electrical-inputs.json',provenance)),
        'patterns':[row for row in energy['convergence'] if row['design']=='narrow'],'calculated_hours':rainbow['runtime']['hours'],
        'narrow_basis':'Complete narrow native census, explicit source records, fixed loom cuts, one installed protected cell and sewn necklace. Engineering allowances and physical acceptance remain unmeasured.','wide_status':'Inactive archived reference; no SKI-1230 removable-cell or current mass/runtime acceptance.'},indent=2)+'\n')
    for name in ['service-guide.svg','assembly-dimensions.svg','prototype-service.zip','parts.json','inventory.md']:
        (output/name).write_bytes(read_input(NARROW/name,provenance))
    template = read_input(SITE / "index.html", provenance).decode()
    rendered = re.sub(r"{{(\w+)}}", lambda match: html.escape(values[match[1]], quote=True), template)
    if "{{" in rendered:
        raise RuntimeError("Unresolved site template values")
    (output / "index.html").write_text(rendered)
    for name in ("styles.css", "icon.svg", "calculator.js", "energy.mjs", "electrical-inputs.json"):
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
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    seal(output, {"commit": commit, "media": records, "dimensions_m": dimensions,
                  "inputs": provenance})


def source_snapshot(*, include_samples=True):
    """Hash both native generations and all site/model/docs inputs, rejecting LFS pointers."""
    paths = set()
    for relative in ("designs/stacked/exports-manifest.json",):
        path = ROOT / relative
        manifest = json.loads(checked_bytes(path))
        paths.add(path)
        for name in (*manifest["inputs"], *manifest["exports"], *manifest.get("documents",{})):
            if Path(name).is_absolute() or ".." in Path(name).parts:
                raise RuntimeError("Unsafe native manifest input: " + name)
            paths.add(ROOT / name)
    # Preserve the wide release as a pinned archive. Its original input
    #hashes remain historical; current prototype freshness is owned by narrow.
    archive_path=ROOT/'hardware/enclosure/exports-manifest.json';archive=json.loads(checked_bytes(archive_path));paths.add(archive_path)
    for name,expected in archive['exports'].items():
        if Path(name).is_absolute() or '..' in Path(name).parts:raise RuntimeError('Unsafe archived export path')
        path=ROOT/name
        if hashlib.sha256(checked_bytes(path)).hexdigest()!=expected:raise RuntimeError('Archived wide artifact changed: '+name)
        paths.add(path)
    paths.update(path for path in SITE.rglob("*") if path.is_file()
                 and not set(path.relative_to(SITE).parts) & {"__pycache__", ".build", "node_modules"})
    paths.update(ROOT / name for name in (
        "hardware/enclosure/battery-options.md", "hardware/enclosure/electrical-review.json",
        "hardware/enclosure/electrical-design.json", "hardware/enclosure/electrical_design.py",
        "hardware/enclosure/electrical-design.md", "hardware/enclosure/qualification-plan.md",
        "hardware/enclosure/electrical_imu.py",
        "hardware/enclosure/fibonacci_board.py",
        "hardware/enclosure/sources/fibonacci256-166/index.json",
        "hardware/enclosure/sources/fibonacci256-166/nominal-terminals.json",
        "hardware/enclosure/sources/fibonacci256-166/README.md",
        "hardware/enclosure/sources/fibonacci256-166/fnqNrNl.png",
        "hardware/enclosure/sources/fibonacci256-166/ISnaLBD.png",
        "hardware/enclosure/electrical_peripherals.py",
        "hardware/enclosure/sources/gps-featherwing/Adafruit Ultimate GPS FeatherWing.brd",
        "hardware/enclosure/sources/gps-featherwing/Adafruit Ultimate GPS FeatherWing.sch",
        "hardware/enclosure/sources/gps-featherwing/README.md",
        "hardware/enclosure/sources/gps-featherwing/index.json",
        "hardware/enclosure/sources/gps-featherwing/license.txt",
        "hardware/enclosure/sources/gps-featherwing/upstream-README.md",
        "hardware/enclosure/sources/rfm-lora/Adafruit RFM+LoRa Breakout.brd",
        "hardware/enclosure/sources/rfm-lora/Adafruit RFM+LoRa Breakout.sch",
        "hardware/enclosure/sources/rfm-lora/README.md",
        "hardware/enclosure/sources/rfm-lora/index.json",
        "hardware/enclosure/sources/rfm-lora/license.txt",
        "hardware/enclosure/sources/rfm-lora/upstream-README.md",
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
