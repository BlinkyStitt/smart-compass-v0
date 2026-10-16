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

EXPORTS = HERE / "exports"
MANIFEST = HERE / "exports-manifest.json"
SHARED = (
    "hardware/enclosure/acrylic-optics.json",
    "hardware/enclosure/baffle.py",
    "hardware/enclosure/geometry.py",
    "hardware/enclosure/demo_export.py",
    "hardware/enclosure/hardware_spec.py",
    "hardware/enclosure/component-inventory.json",
    "hardware/enclosure/fibonacci256-layout.json",
    "hardware/enclosure/vendor/evilgeniuslabs-fibonacci256/Fibonacci256voronoi.stl",
    "hardware/enclosure/vendor/evilgeniuslabs-fibonacci256/LICENSE.txt",
    "hardware/enclosure/vendor/evilgeniuslabs-fibonacci256/SOURCE.md",
    "demo/mannequin.gd",
    "demo/main.gd",
    "demo/assets/playa-night.png",
    "demo/ring_diffusion.gdshaderinc",
    "demo/package.gdshader",
    "hardware/enclosure/exports/scene.json",
)
EXPECTED = frozenset(
    {
        "amulet.glb",
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
    for style in ("rainbow", "ocean", "sunset")
    for suffix in (".mp4", ".gif")
)


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
    return sorted({*own, *(ROOT / p for p in SHARED)})


def hashes(paths):
    return {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}


def check(staged=False):
    record = json.loads(MANIFEST.read_text())
    if record.get("format_version") != 1:
        raise RuntimeError("Unsupported compact manifest")
    current_inputs = hashes(inputs())
    current_exports = hashes(EXPORTS / p for p in EXPECTED)
    if {p.name for p in EXPORTS.iterdir() if p.is_file()} != EXPECTED:
        raise RuntimeError("Missing or unexpected compact export")
    if current_inputs != record["inputs"] or current_exports != record["exports"]:
        raise RuntimeError(
            "Compact sources or exports are stale. Run the compact build."
        )
    if staged:
        for name, wanted in {**current_inputs, **current_exports}.items():
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


def execute(command, *, env=None, log=None):
    result = subprocess.run(
        command,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=1800,
        check=False,
    )
    if log:
        log.write_text(result.stdout)
    if result.returncode:
        print(result.stdout[-18000:], flush=True)
        raise RuntimeError("Command failed: " + str(command[0]))
    return result.stdout


def prepare_preview():
    destination = HERE / ".build/preview"
    shutil.copytree(HERE / "preview", destination, dirs_exist_ok=True)
    for name in ("mannequin.gd", "ring_diffusion.gdshaderinc", "package.gdshader"):
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
    output = execute(command, log=HERE / ".build/godot-last.log")
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
    for style in ("rainbow", "ocean", "sunset"):
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
        ) != (1280, 720, "384", "24/1"):
            raise RuntimeError("Invalid matched movie dimensions or timing")
    comparison = {
        "reference_commit": subprocess.check_output(
            ["git", "log", "-1", "--format=%H", "--", "hardware/enclosure", "demo"],
            cwd=ROOT,
            text=True,
        ).strip(),
        "reference_design": "hardware/enclosure/exports",
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
            "pattern_time_s": 16 * 95 / 96,
        },
        "closeup": {
            "distance_m": 0.46,
            "pitch_deg": -12,
            "yaw_formula": "65*cos(2*pi*frame/384)",
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
                log=HERE / ".build/native.log",
            )
            if not complete.exists() or not json.loads(complete.read_text()).get(
                "complete"
            ):
                raise RuntimeError("Native CAD did not complete")
            print(output[-1000:], flush=True)
            preview_check(out)
            capture(out, stage)
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
                "inputs": initial,
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
            backup = HERE / ".build/previous-exports"
            if backup.exists():
                shutil.rmtree(backup)
            if EXPORTS.exists():
                EXPORTS.rename(backup)
            out.rename(EXPORTS)
            temporary = HERE / ".build/manifest.json"
            temporary.write_text(json.dumps(record, indent=2) + "\n")
            os.replace(temporary, MANIFEST)
        check()
        print(
            "STACKED BUILD COMPLETE: checked CAD and separate matched renders; first design unchanged",
            flush=True,
        )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("build", "check", "test", "preview", "preview-check")
    )
    parser.add_argument("--staged", action="store_true")
    args = parser.parse_args()
    if args.command == "build":
        build()
    elif args.command == "check":
        check(args.staged)
    elif args.command == "test":
        test()
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
