"""Render both wearing-scale stills with the same soft front fill."""

import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


def render():
    # Use each design's owning freshness check and native preview setup.
    subprocess.run([sys.executable, str(ROOT / "hardware/enclosure/cad.py"), "check"], check=True)
    sys.path.insert(0, str(ROOT / "designs/stacked"))
    spec = importlib.util.spec_from_file_location("stacked_run", ROOT / "designs/stacked/run.py")
    stacked = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(stacked)
    stacked.check()
    project = stacked.prepare_preview()
    for name, project, assets in (
        ("wide", ROOT / "demo", ROOT / "hardware/enclosure/exports"),
        ("narrow", project, stacked.EXPORTS),
    ):
        result = subprocess.run([
            shutil.which("godot") or "godot", "--path", str(project),
            "--script", str(ROOT / "site/render_worn.gd"), "--", "--assets", str(assets),
            "--output", str(ROOT / f"site/assets/{name}-worn.png"),
        ], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
        print(result.stdout, end="", flush=True)
        result.check_returncode()
        if "ERROR:" in result.stdout or "SITE WEARING SCALE CAPTURE PASS" not in result.stdout:
            raise RuntimeError(f"Godot did not render the {name} wearing-scale image")


if __name__ == "__main__":
    render()
