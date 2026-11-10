"""Capture a visibly travelling, always-lit rainbow spiral on the current CAD."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'demo'))
sys.path.insert(0, str(ROOT / 'designs/stacked'))
from run import execute, prepare_preview


def render(frames):
    frames = frames.resolve()
    frames.mkdir(parents=True, exist_ok=False)
    project = prepare_preview()
    shutil.copyfile(ROOT / 'site/rainbow_spiral.gd', project / 'site_spiral.gd')
    result = execute(['godot', '--path', str(project), '--script', str(ROOT / 'site/render_rainbow.gd'),
                      '--', '--assets', str(ROOT / 'designs/stacked/exports'), '--frames', str(frames)],
                     log=frames / 'capture.log', timeout=900)
    if 'SITE RAINBOW SPIRAL CAPTURE PASS' not in result or 'ERROR:' in result:
        raise RuntimeError('Rainbow spiral capture failed: ' + result[-4000:])
    output = ROOT / 'site/assets/rainbow-spiral.mp4'
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-framerate', '24',
                    '-i', str(frames / 'rainbow-%04d.png'), '-frames:v', '384',
                    '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20',
                    '-movflags', '+faststart', str(output)], check=True)
    print('SITE RAINBOW SPIRAL MEDIA PASS:', output)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--frames', type=Path, required=True, help='New external-drive capture directory')
    render(parser.parse_args().frames)
