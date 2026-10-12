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

VIEWS = ('front', 'steep', 'edge', 'rear')
LIGHTS = ('night', 'indoor', 'overcast', 'sun')
BLINKS = tuple(f'infinity-{style}.gif' for style in ('rainbow', 'pulse', 'colour'))
CAPTURES = tuple(f'demo-{view}-{light}.png' for view in VIEWS for light in LIGHTS)


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
    with tempfile.TemporaryDirectory(prefix='amulet-optics-') as tmp:
        reference = Path(tmp)/'reference.json'
        optics = json.loads((ROOT/cad.EXPORTS/'scene.json').read_text())['optics']
        reference.write_text(json.dumps(cases(optics)))
        godot('--', '--gpu-check', '--reference', str(reference), *extra, marker='DEMO GPU OPTICS PASS')


def capture():
    check(build=True)
    output = ROOT/cad.EXPORTS
    with tempfile.TemporaryDirectory(prefix='amulet-capture-') as tmp:
        frames = Path(tmp)
        godot('--', '--capture', str(frames), '--build-validation', marker='DEMO CAPTURE PASS')
        for view in VIEWS:
            for light, name in enumerate(LIGHTS):
                command = ['ffmpeg', '-y', '-loglevel', 'error']
                filters = []
                for row, on in enumerate(('on','off')):
                    for version in range(3):
                        index = row*3+version
                        command += ['-i', str(frames/f'{view}-light{light}-{on}-v{version}.png')]
                        filters.append(f"[{index}:v]scale=640:360[v{index}]")
                filters.append(''.join(f'[v{i}]' for i in range(6))+'xstack=inputs=6:layout=0_0|640_0|1280_0|0_360|640_360|1280_360[out]')
                subprocess.run(command+['-filter_complex',';'.join(filters),'-map','[out]','-frames:v','1',str(output/f'demo-{view}-{name}.png')],check=True)
        subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','24','-i',str(frames/'movie-%04d.png'),
                        '-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(output/'amulet-demo.mp4')],check=True)
        subprocess.run(['ffmpeg','-y','-loglevel','error','-ss','24','-i',str(output/'amulet-demo.mp4'),'-t','12',
                        '-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(output/'lighting-demo.mp4')],check=True)
        subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(output/'amulet-demo.mp4'),'-t','24',
                        '-filter_complex','fps=12,scale=800:450,split[a][b];[a]palettegen[p];[b][p]paletteuse',
                        '-loop','0',str(output/'turntable.gif')],check=True)
        for style in ('rainbow','pulse','colour'):
            subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','24','-i',str(frames/f'blink-{style}-%04d.png'),
                            '-filter_complex','fps=12,scale=800:450,split[a][b];[a]palettegen[p];[b][p]paletteuse',
                            '-loop','0',str(output/f'infinity-{style}.gif')],check=True)
        shutil.copyfile(frames/'movie-0000.png',output/'turntable-poster.png')
    for name in (*CAPTURES,*BLINKS,'lighting-demo.mp4','amulet-demo.mp4','turntable.gif','turntable-poster.png'):
        file = output/name
        probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(file)],text=True))['streams'][0]
        size=(800,450) if name.endswith('.gif') else ((1920,720) if name in CAPTURES else (1280,720))
        assert (probe['width'],probe['height'])==size
        if name.endswith('.mp4'):
            seconds=52 if name=='amulet-demo.mp4' else 12
            assert int(probe['nb_frames'])==seconds*24 and abs(float(probe['duration'])-seconds)<.01
        if name.endswith('.gif'):
            seconds=16 if name in BLINKS else 24
            assert int(probe['nb_frames'])==seconds*12 and abs(float(probe['duration'])-seconds)<.1
            assert b'NETSCAPE2.0\x03\x01\x00\x00' in file.read_bytes(), 'GIF must repeat forever'
        subprocess.run(['ffmpeg','-v','error','-xerror','-i',str(file),'-f','null','-'],check=True)
    print('DEMO MEDIA PASS: all comparisons and video decoded',flush=True)


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
