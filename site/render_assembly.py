"""Render the site's grey-background exploded loop from the current Godot scene."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "demo"))
sys.path.insert(0, str(ROOT / "designs/stacked"))
from run import execute, prepare_preview
from explosion import CAPTURE_INPUTS, FRAMES, capture_record, layout


def render(frames, preview=False):
    frames = frames.resolve()
    frames.mkdir(parents=True, exist_ok=False)
    inputs = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in CAPTURE_INPUTS}
    project = prepare_preview()
    scene = ROOT / 'designs/stacked/exports/scene.json'
    plan = layout(json.loads(scene.read_text()))
    (frames / 'layout.json').write_text(json.dumps(plan, sort_keys=True))
    result = execute([
        "godot", "--path", str(project), "--script", str(ROOT / "site/render_assembly.gd"),
        "--", "--assets", str(ROOT / "designs/stacked/exports"), "--frames", str(frames), *(["--preview"] if preview else []),
    ], log=frames / "capture.log", timeout=900)
    if "SITE ASSEMBLY CAPTURE PASS" not in result or "ERROR:" in result:
        raise RuntimeError("Narrow assembly capture failed: " + result[-4000:])
    if inputs != {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in CAPTURE_INPUTS}:
        raise RuntimeError('Assembly inputs changed during capture')
    if preview:
        print("ASSEMBLY PREVIEW PASS:", frames)
        return
    output = ROOT / "site/assets/exploded-assembly.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-framerate", "24",
        "-i", str(frames / "assembly-%04d.png"), "-frames:v", str(FRAMES),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
        "-movflags", "+faststart", str(output),
    ], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-xerror", "-i", str(output),
                    "-f", "null", "-"], check=True)
    proof = capture_record(plan, hashlib.sha256(output.read_bytes()).hexdigest(), inputs)
    output.with_suffix('.json').write_text(json.dumps(proof, indent=2) + '\n')
    print("SITE ASSEMBLY MEDIA PASS:", output, proof)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--frames", type=Path, required=True,
                        help="New external-drive directory for rendered PNG frames")
    parser.add_argument("--preview", action="store_true", help="Capture overview and every detail without replacing the movie")
    args = parser.parse_args()
    render(args.frames, args.preview)
