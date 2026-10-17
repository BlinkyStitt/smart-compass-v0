"""Render the Narrow silver PETG loop with the Wide model's material response."""

import argparse
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "demo"))
from media import verify_rainbow_motion


def render(frames):
    subprocess.run([sys.executable, str(ROOT / "hardware/enclosure/cad.py"), "check"], check=True)
    sys.path.insert(0, str(ROOT / "designs/stacked"))
    spec = importlib.util.spec_from_file_location("stacked_run", ROOT / "designs/stacked/run.py")
    stacked = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stacked)
    stacked.check()
    project = stacked.prepare_preview()
    frames = frames.resolve()
    frames.mkdir(parents=True, exist_ok=False)
    result = subprocess.run([
        shutil.which("godot") or "godot", "--path", str(project),
        "--script", str(ROOT / "site/render_silver.gd"), "--", "--assets", str(stacked.EXPORTS),
        "--material-scene", str(ROOT / "hardware/enclosure/exports/scene.json"),
        "--frames", str(frames),
    ], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=660)
    print(result.stdout, end="", flush=True)
    result.check_returncode()
    if "ERROR:" in result.stdout or "SITE SILVER CAPTURE PASS" not in result.stdout:
        raise RuntimeError("Godot did not render the Narrow silver PETG clip")
    output = ROOT / "site/assets/narrow-silver.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-framerate", "24",
        "-i", str(frames / "silver-%04d.png"), "-frames:v", "384",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
        "-movflags", "+faststart", str(output),
    ], check=True)
    verify_rainbow_motion(output, stacked.EXPORTS / "scene.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=Path, required=True,
                        help="New external-drive directory for rendered PNG frames")
    render(parser.parse_args().frames)
