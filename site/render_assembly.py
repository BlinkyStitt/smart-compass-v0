"""Render the site's grey-background exploded loop from the current Godot scene."""

import argparse
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "demo"))
sys.path.insert(0, str(ROOT / "designs/stacked"))
from run import execute, prepare_preview


def render(frames):
    frames = frames.resolve()
    frames.mkdir(parents=True, exist_ok=False)
    project = prepare_preview()
    result = execute([
        "godot", "--path", str(project), "--script", str(ROOT / "site/render_assembly.gd"),
        "--", "--assets", str(ROOT / "designs/stacked/exports"), "--frames", str(frames),
    ], log=frames / "capture.log", timeout=900)
    if "SITE ASSEMBLY CAPTURE PASS" not in result or "ERROR:" in result:
        raise RuntimeError("Narrow assembly capture failed: " + result[-4000:])
    output = ROOT / "site/assets/exploded-assembly.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-framerate", "24",
        "-i", str(frames / "assembly-%04d.png"), "-frames:v", "576",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
        "-movflags", "+faststart", str(output),
    ], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(output),
                    "-f", "null", "-"], check=True)
    print("SITE ASSEMBLY MEDIA PASS:", output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=Path, required=True,
                        help="New external-drive directory for rendered PNG frames")
    render(parser.parse_args().frames)
