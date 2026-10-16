"""Launch, validate, or reproduce fixed Godot comparisons from canonical CAD."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'hardware/enclosure'))
import cad
from reference import cases
from media import verify_rainbow_motion



def godot(*args, headless=False, marker=None):
    executable = shutil.which('godot')
    if not executable:
        raise RuntimeError('Install Godot: brew install --cask godot')
    command = [executable, '--path', str(ROOT/'demo')]
    if headless:
        command.extend(['--headless', '--quit-after', '600'])
    result = subprocess.run(command+list(args), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, end='', flush=True)
    result.check_returncode()
    if 'SCRIPT ERROR:' in result.stdout or 'ERROR:' in result.stdout:
        raise RuntimeError('Godot reported an error')
    if marker and marker not in result.stdout:
        raise RuntimeError('Godot did not complete '+marker)
    return result.stdout


def check(build=False):
    if not build:
        cad.check_freshness(cad.Snapshot(ROOT))
    subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(ROOT/'demo'), '-p', 'test_*.py', '-v'], check=True)
    godot('--editor', '--import', '--quit', headless=True)
    extra = ['--build-validation'] if build else []
    godot('--', '--check', *extra, headless=True, marker='DEMO SCENE PASS')
    with tempfile.TemporaryDirectory(prefix='amulet-optics-', dir=ROOT.parent) as tmp:
        reference = Path(tmp)/'reference.json'
        optics = json.loads((ROOT/cad.EXPORTS/'scene.json').read_text())['optics']
        reference.write_text(json.dumps(cases(optics)))
        godot('--', '--gpu-check', '--reference', str(reference), *extra, marker='DEMO GPU OPTICS PASS')


def capture():
    check(build=True)
    output = ROOT/cad.EXPORTS
    with tempfile.TemporaryDirectory(prefix='amulet-capture-', dir=ROOT.parent) as tmp:
        frames = Path(tmp)
        godot('--', '--capture', str(frames), '--build-validation', marker='DEMO CAPTURE PASS')
        shutil.copyfile(frames/'night-mannequin.png',output/'night-mannequin.png')
        for suffix in ('','-silver'):
            movie=output/('infinity-rainbow'+suffix+'.mp4')
            gif=movie.with_suffix('.gif')
            subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','24','-i',str(frames/('gradient-rainbow'+suffix+'-%04d.png')),
                            '-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(movie)],check=True)
            subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(movie),
                            '-filter_complex','fps=12,scale=800:450,split[a][b];[a]palettegen[p];[b][p]paletteuse',
                            '-loop','0',str(gif)],check=True)
    for name in ('night-mannequin.png','infinity-rainbow.mp4','infinity-rainbow-silver.mp4','infinity-rainbow.gif','infinity-rainbow-silver.gif'):
        file = output/name
        probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(file)],text=True))['streams'][0]
        size=(800,450) if name.endswith('.gif') else (1280,720)
        assert (probe['width'],probe['height'])==size
        if name.endswith('.mp4'):
            assert int(probe['nb_frames'])==384 and abs(float(probe['duration'])-16)<.01
        if name.endswith('.gif'):
            assert int(probe['nb_frames'])==192 and abs(float(probe['duration'])-16)<.1
            assert b'NETSCAPE2.0\x03\x01\x00\x00' in file.read_bytes(), 'GIF must repeat forever'
        subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(file),'-f','null','-'],check=True)
        if name.endswith('.mp4'):
            verify_rainbow_motion(file)
    print('DEMO MEDIA PASS: matched rainbow loops decoded',flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command',choices=('launch','check','capture','benchmark'))
    args = parser.parse_args()
    if args.command=='capture':
        capture()
    elif args.command=='check':
        check()
    else:
        cad.check_freshness(cad.Snapshot(ROOT))
        if args.command=='benchmark':
            godot('--','--benchmark',marker='DEMO BENCHMARK')
        else:
            subprocess.run([shutil.which('godot') or 'godot','--path',str(ROOT/'demo')],check=True)


if __name__=='__main__':
    try:
        main()
    except (cad.CadError, RuntimeError, OSError, subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc))
