"""Own the compact concept build, atomic exports, freshness and Godot checks."""

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

from layout import HERE, ROOT
from optics import cases, side_cases
import prints
import service
import inventory_doc

sys.path.insert(0, str(ROOT / "hardware/enclosure"))
import native_publication

sys.path.insert(0, str(ROOT / "demo"))
from media import DARK_STYLES, verify_rainbow_motion, verify_masked_motion

EXPORTS = HERE / "exports"
MANIFEST = HERE / "exports-manifest.json"
SHARED = (
    "justfile", "validation.just", ".githooks/pre-commit", "design-v2.md",
    "site/electrical-inputs.json", ".github/workflows/pages.yml",
    "hardware/enclosure/acrylic-optics.json",
    "hardware/enclosure/baffle.py",
    "hardware/enclosure/geometry.py",
    "hardware/enclosure/antenna.py",
    "hardware/enclosure/antenna_native.py",
    "hardware/enclosure/antenna-placement.md",
    "hardware/enclosure/demo_export.py",
    "hardware/enclosure/hardware_spec.py",
    "hardware/enclosure/component-inventory.json",
    "hardware/enclosure/native_publication.py",
    "hardware/enclosure/fibonacci256-layout.json",
    "hardware/enclosure/vendor/evilgeniuslabs-fibonacci256/Fibonacci256voronoi.stl",
    "hardware/enclosure/vendor/evilgeniuslabs-fibonacci256/LICENSE.txt",
    "hardware/enclosure/vendor/evilgeniuslabs-fibonacci256/SOURCE.md",
    "demo/run.py",
    "demo/mannequin.gd",
    "demo/main.gd",
    "demo/patterns.gd",
    "demo/pattern_checks.gd",
    "demo/check_patterns.gd",
    "demo/capture_view.gd",
    "demo/playa.gd",
    "demo/media.py",
    "demo/assets/playa-night.png",
    "demo/ring_diffusion.gdshaderinc",
    "demo/centre_diffusion.gdshaderinc",
    "demo/package.gdshader",

)
EXPECTED = frozenset(
    {
        "amulet.glb",
        "antenna-placement.svg",
        "cell-map.png",
        "scene.json",
        "stacked-fibonacci.FCStd",
        "stacked-fibonacci.step",
        "night-mannequin.png",
        "night-front.png",
        "night-angled.png",
        "night-side.png",
        "night-inner-off.png",
        "night-leds-off.png",
        "exploded.png",
        "comparison.json",
    }
)
EXPECTED = EXPECTED | frozenset(
    "infinity-" + style + suffix
    for style in ("rainbow",)
    for suffix in (".mp4", ".gif")
)

EXPECTED |= frozenset(f"infinity-rainbow-dark-{style}.mp4" for style in DARK_STYLES)

# The wide design remains an archived reference. It is no longer a native
# build dependency of the selected narrow prototype.
EXPECTED |= prints.required_exports(json.loads((ROOT/'hardware/enclosure/print-spec.json').read_text()))
EXPECTED |= frozenset({'parts.json','installed-fit-check.json','antenna-service-check.json','loom-check.json','necklace-fit-check.json','end-support-check.json','case-structure-check.json','inventory.md','slicing-check.json','service-guide.svg','assembly-dimensions.svg','service-guide.json','prototype-service.zip','infinity-rainbow-silver.mp4'})


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inputs():
    own = [
        p
        for p in HERE.rglob("*")
        if p.is_file()
        and p.suffix
        in (
            ".py",
            ".json",
            ".gd",
            ".gdshader",
            ".gdshaderinc",
            ".tscn",
            ".godot",
            ".FCMacro",
            ".md",
        )
        and not set(p.relative_to(HERE).parts)
        & {".build", "exports", "__pycache__", ".godot"}
        and p != MANIFEST
    ]
    hardware=ROOT/'hardware/enclosure'
    retained=[p for p in hardware.rglob('*') if p.is_file() and not set(p.relative_to(hardware).parts)&{'exports','.build','__pycache__'} and p.suffix in {'.py','.json','.md','.brd','.sch','.step','.stp','.pdf','.png','.jpg','.jpeg','.svg','.stl','.brep','.html','.FCMacro','.txt'} and p.name!='exports-manifest.json']
    return sorted({*own,*retained,*(ROOT/p for p in SHARED)})


def hashes(paths):
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}


def check(staged=False, *, publishing=False):
    if not publishing and native_publication.pending(HERE / '.build/publication'):
        raise RuntimeError('Interrupted compact publication; rebuild to restore the prior complete release')
    record = json.loads(MANIFEST.read_text())
    if record.get("format_version") != 1:
        raise RuntimeError("Unsupported compact manifest")
    current_inputs = hashes(inputs())
    current_exports = hashes(EXPORTS / p for p in EXPECTED)
    current_documents = hashes([ROOT/"design-v2.md"])
    if {p.name for p in EXPORTS.iterdir() if p.is_file()} != EXPECTED:
        raise RuntimeError("Missing or unexpected compact export")
    if current_inputs != record["inputs"] or current_exports != record["exports"] or current_documents != record.get("documents"):
        raise RuntimeError(
            "Compact sources or exports are stale. Run the compact build."
        )
    if staged:
        for name, wanted in {**current_inputs, **current_exports, **current_documents}.items():
            data = subprocess.check_output(
                ["git", "cat-file", "--filters", ":" + name], cwd=ROOT
            )
            if hashlib.sha256(data).hexdigest() != wanted:
                raise RuntimeError("Partially staged compact input/export: " + name)
        data = subprocess.check_output(
            ["git", "show", ":" + str(MANIFEST.relative_to(ROOT))], cwd=ROOT
        )
        if json.loads(data) != record:
            raise RuntimeError("Partially staged compact manifest")
    print("STACKED FRESHNESS PASS" + (" (staged)" if staged else ""))


@contextmanager
def build_lock():
    (HERE / ".build").mkdir(exist_ok=True)
    with (HERE / ".build/lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("Another compact build is running") from exc
        yield


def execute(command, *, env=None, log=None, timeout=1800):
    if log:
        # Stream the actual command log to disk so long native work remains
        # observable. Read it only after completion for the marker checks.
        with log.open('w') as stream:
            result=subprocess.run(command,cwd=ROOT,env=env,text=True,
                stdout=stream,stderr=subprocess.STDOUT,timeout=timeout,check=False)
        output=log.read_text()
    else:
        result=subprocess.run(command,cwd=ROOT,env=env,text=True,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout,check=False)
        output=result.stdout
    if result.returncode:
        print(output[-18000:], flush=True)
        raise RuntimeError("Command failed: " + str(command[0]))
    return output


def prepare_preview():
    destination = HERE / ".build/preview"
    shutil.copytree(HERE / "preview", destination, dirs_exist_ok=True)
    for name in (
        "mannequin.gd",
        "patterns.gd",
        "pattern_checks.gd",
        "check_patterns.gd",
        "capture_view.gd",
        "playa.gd",
        "ring_diffusion.gdshaderinc",
        "centre_diffusion.gdshaderinc",
        "package.gdshader",
    ):
        shutil.copyfile(ROOT / "demo" / name, destination / name)
    (destination / "assets").mkdir(exist_ok=True)
    shutil.copyfile(
        ROOT / "demo/assets/playa-night.png", destination / "assets/playa-night.png"
    )
    return destination


def godot(project, assets, *arguments, headless=False):
    command = [
        shutil.which("godot") or "godot",
        "--path",
        str(project),
        "--log-file",
        str(HERE / ".build/godot-engine.log"),
    ]
    if headless:
        command += ["--headless", "--quit-after", "600"]
    elif "--gpu-check" in arguments:
        command += ["--quit-after", "7200"]
    command += ["--", "--assets", str(assets), *map(str, arguments)]
    # Four loops retain the original 1800-second per-loop capture budget.
    output = execute(command, log=HERE / ".build/godot-last.log",
                     timeout=7200 if "--capture" in arguments else 1800)
    if "SCRIPT ERROR:" in output or "ERROR:" in output:
        raise RuntimeError(output[-14000:])
    print(output.strip(), flush=True)
    return output


def preview_check(assets=EXPORTS):
    project = prepare_preview()
    output = godot(project, assets, "--check", headless=True)
    if "STACKED SCENE PASS" not in output:
        raise RuntimeError("Compact scene check did not finish")
    reference = HERE / ".build/reference.json"
    optics = json.loads((assets / "scene.json").read_text())["optics"]
    reference.write_text(
        json.dumps({"cavity": cases(optics), "side": side_cases(optics)})
    )
    output = godot(project, assets, "--gpu-check", "--reference", reference)
    if "STACKED GPU OPTICS PASS" not in output:
        raise RuntimeError("Compact GPU check did not finish")


def test():
    subprocess.run(
        [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(HERE),
            "-p",
            "test_*.py",
            "-v",
        ],
        cwd=ROOT,
        check=True,
    )


def capture(assets, stage):
    project = prepare_preview()
    frames = stage / "frames"
    frames.mkdir()
    output = godot(project, assets, "--capture", frames)
    if "STACKED CAPTURE PASS" not in output:
        raise RuntimeError("Compact capture did not finish")
    for name in EXPECTED:
        if name.endswith(".png") and name != "cell-map.png":
            shutil.copyfile(frames / name, assets / name)
    for style in ("rainbow", *("rainbow-dark-" + name for name in DARK_STYLES)):
        source = str(frames / f"gradient-{style}-%04d.png")
        execute(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-framerate",
                "24",
                "-i",
                source,
                "-c:v",
                "libx264",
                "-pix_fmt",
                "yuv420p",
                "-crf",
                "20",
                "-movflags",
                "+faststart",
                str(assets / f"infinity-{style}.mp4"),
            ]
        )
        if style == "rainbow":
            execute(
                [
                    "ffmpeg",
                    "-y",
                    "-loglevel",
                    "error",
                    "-i",
                    str(assets / f"infinity-{style}.mp4"),
                    "-filter_complex",
                    "fps=12,scale=800:450,split[a][b];[a]palettegen[p];[b][p]paletteuse",
                    "-loop",
                    "0",
                    str(assets / f"infinity-{style}.gif"),
                ]
            )
        probe = json.loads(
            subprocess.check_output(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-show_streams",
                    "-of",
                    "json",
                    str(assets / f"infinity-{style}.mp4"),
                ]
            )
        )
        stream = probe["streams"][0]
        if (
            stream["width"],
            stream["height"],
            stream["nb_frames"],
            stream["r_frame_rate"],
        ) != (1280, 720, "384", "24/1") or abs(float(stream["duration"]) - 16) > .01:
            raise RuntimeError("Invalid matched movie dimensions or timing")
        execute(
            [
                "ffmpeg",
                "-v",
                "error",
                "-xerror",
                "-i",
                str(assets / f"infinity-{style}.mp4"),
                "-f",
                "null",
                "-",
            ]
        )
        if style == "rainbow":
            verify_rainbow_motion(assets / f"infinity-{style}.mp4", assets / "scene.json")
        else:
            verify_masked_motion(assets / f"infinity-{style}.mp4", assets / "scene.json", style.removeprefix("rainbow-dark-"))
    silver_frames=stage/'silver-frames';silver_frames.mkdir()
    output=execute([shutil.which('godot') or 'godot','--path',str(project),'--script',str(HERE/'render_silver.gd'),'--','--assets',str(assets),'--material-scene',str(assets/'scene.json'),'--frames',str(silver_frames)],log=HERE/'.build/silver-capture.log',timeout=1800)
    if 'SITE SILVER CAPTURE PASS' not in output or 'ERROR:' in output:raise RuntimeError('Narrow silver capture did not complete')
    movie=assets/'infinity-rainbow-silver.mp4'
    execute(['ffmpeg','-y','-v','error','-framerate','24','-i',str(silver_frames/'silver-%04d.png'),'-frames:v','384','-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(movie)])
    stream=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(movie)]))['streams'][0]
    if (stream['width'],stream['height'],stream['nb_frames'],stream['r_frame_rate'])!=(1280,720,'384','24/1') or abs(float(stream['duration'])-16)>.01:raise RuntimeError('Narrow silver loop dimensions or timing differ')
    execute(['ffmpeg','-v','error','-xerror','-i',str(movie),'-f','null','-'])
    verify_rainbow_motion(movie,assets/'scene.json')
    comparison = {
        "reference_commit": subprocess.check_output(
            ["git", "log", "-1", "--format=%H", "--", "hardware/enclosure/exports-manifest.json"],
            cwd=ROOT,
            text=True,
        ).strip(),
        "reference_design": "hardware/enclosure/exports",
        "reference_manifest_sha256":digest(ROOT/"hardware/enclosure/exports-manifest.json"),
        "reference_status":"Inactive wide archive; export bytes preserved",
        "separate_files": True,
        "width_px": 1280,
        "height_px": 720,
        "source_brightness": 2.0,
        "exposure": 1.0,
        "pattern_formula": "Shared spatial gradients; eight-second colour cycles",
        "world_target_z_m": 0.0367,
        "camera_fov_deg": 38.0,
        "camera_near_m": 0.005,
        "camera_far_m": 30.0,
        "full_pose": {
            "distance_m": 3.5,
            "target_y_m": -0.1,
            "pitch_deg": -3,
            "pattern_time_s": 2.0,
        },
        "closeup": {
            "distance_m": 0.46,
            "yaw_formula": "35*sin(2*pi*frame/384)-15*sin(2*pi*frame/384)^2",
            "pitch_formula": "20*sin(4*pi*frame/384)",
            "background": "World-space 210-degree curved playa at 20 m, with stationary ground",
            "fps": 24,
            "frames": 384,
        },
        "backdrop_sha256": digest(ROOT / "demo/assets/playa-night.png"),
        "pose_source_sha256": digest(ROOT / "demo/mannequin.gd"),
        "pose_changes": "Only the final webbing segments meet the compact rear anchors; body pose unchanged",
        "optics_status": "Clear outer mirror: supplier-nominal R70/T30. Coated black inner mirror: complete-sheet estimate cavity R70/T9/absorption21, reverse R10/T9. Same black-mirror estimate in the wide front. No separate black filter or brightness compensation. Custom coatings, RGB and scattering remain unmeasured.",
    }
    (assets / "comparison.json").write_text(json.dumps(comparison, indent=2) + "\n")


def build():
    with build_lock():
        native_publication.recover(ROOT, HERE / '.build/publication')
        execute([sys.executable,str(ROOT/'hardware/enclosure/electrical.py'),'check'])
        test()
        initial = hashes(inputs())
        original = hashes(
            p for p in (ROOT / "hardware/enclosure/exports").iterdir() if p.is_file()
        )
        with tempfile.TemporaryDirectory(
            prefix="build-", dir=HERE / ".build"
        ) as directory:
            stage = Path(directory)
            out = stage / "exports"
            out.mkdir()
            complete = stage / "native-complete.json"
            env = dict(
                os.environ,
                STACKED_SOURCE=str(HERE),
                STACKED_OUTPUT=str(out),
                STACKED_RESULT=str(complete),
            )
            freecad = (
                shutil.which("freecad")
                or "/Applications/FreeCAD.app/Contents/Resources/bin/freecad"
            )
            output = execute(
                [freecad, str(HERE / "Run.FCMacro")],
                env=env,
                log=HERE / ".build/native.log", timeout=None,
            )
            if not complete.exists() or not json.loads(complete.read_text()).get(
                "complete"
            ):
                print(output[-18000:], flush=True)
                raise RuntimeError("Native CAD did not complete")
            print(output[-1000:], flush=True)
            native_record=json.loads(complete.read_text())
            if 'STACKED CAD PASS:' not in output:raise RuntimeError('Narrow native completion marker missing')
            parts=json.loads((out/'parts.json').read_text());spec=json.loads((ROOT/'hardware/enclosure/print-spec.json').read_text())
            document=inventory_doc.update((ROOT/'design-v2.md').read_text(),parts)
            (out/'inventory.md').write_text(inventory_doc.section(parts,'')+'\n')
            prints.generate(out,parts,spec)
            (out/'slicing-check.json').write_text(json.dumps(prints.check(out,parts,spec),indent=2)+'\n')
            preview_check(out)
            capture(out, stage)
            service.package(out,parts,spec,[ROOT/'hardware/enclosure'/name for name in ['battery-access.md','electrical-design.md','electrical-design.json','harness-routing.json','harness-splices.json','necklace.json','qualification-plan.md','harness-assembly.md','control-mounts.md','latch-mounts.md','boost-mounts.md','capacitor-mounts.md','branch-fuses.md','sparkle-mounts.md','blackpill-mounts.md','gps-mounts.md','imu-mounts.md','radio-mounts.md','sources/fibonacci256-166/README.md','vendor/evilgeniuslabs-fibonacci256/LICENSE.txt']]+[HERE/'fasteners.json',HERE/'print-layout.json'])
            if initial != hashes(inputs()):
                raise RuntimeError("Source changed during compact build")
            if original != hashes(
                p
                for p in (ROOT / "hardware/enclosure/exports").iterdir()
                if p.is_file()
            ):
                raise RuntimeError("First design changed during compact build")
            if {p.name for p in out.iterdir()} != EXPECTED:
                raise RuntimeError("Incomplete compact output set")
            record = {
                "format_version": 1,
                "inputs": {**initial,"design-v2.md":hashlib.sha256(document.encode()).hexdigest()},
                "documents": {"design-v2.md":hashlib.sha256(document.encode()).hexdigest()},
                "exports": hashes(out / p for p in EXPECTED),
                "tools": {
                    "freecad": json.loads(complete.read_text())["freecad"],
                    "godot": execute(["godot", "--version"]).strip(),
                },
            }
            # Staging paths are not manifest paths.
            record["exports"] = {
                str((EXPORTS / Path(k).name).relative_to(ROOT)): v
                for k, v in record["exports"].items()
            }
            files = {str((EXPORTS / name).relative_to(ROOT)): (out / name).read_bytes()
                     for name in EXPECTED}
            files["design-v2.md"]=document.encode()
            manifest_name = str(MANIFEST.relative_to(ROOT))
            files[manifest_name] = (json.dumps(record, indent=2) + '\n').encode()
            retired = {str(path.relative_to(ROOT)) for path in EXPORTS.iterdir()
                       if path.is_file() and path.name not in EXPECTED} if EXPORTS.exists() else set()
            native_publication.publish(ROOT, HERE / '.build/publication', files, retired,
                                       manifest_name, lambda: check(publishing=True))
        check()
        print(
            "STACKED BUILD COMPLETE: checked CAD and separate matched renders; first design unchanged",
            flush=True,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("build", "check", "test", "preview", "preview-check", "print-check")
    )
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    if args.command == "build":
        build()
    elif args.command == "check":
        check(args.staged)
    elif args.command == "test":
        test()
    elif args.command == 'print-check':
        check()
        parts=json.loads((EXPORTS/'parts.json').read_text())
        spec=json.loads((ROOT/'hardware/enclosure/print-spec.json').read_text())
        result=prints.check(EXPORTS,parts,spec)
        if result!=json.loads((EXPORTS/'slicing-check.json').read_text()):raise RuntimeError('Delivered narrow slicing evidence differs')
        print('NARROW SLICER PASS: exact delivered projects and source triangles')
    elif args.command == "preview-check":
        check()
        preview_check()
    else:
        check()
        project = prepare_preview()
        subprocess.run(
            ["godot", "--path", str(project), "--", "--assets", str(EXPORTS)],
            cwd=ROOT,
            check=True,
        )


if __name__ == "__main__":
    main()
