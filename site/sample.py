"""Export deterministic electrical study samples from the shared Godot functions.

The native scenes remain geometry-owned. Generated study data stays under .build
until the electrical and fitted-access gates permit a canonical publication.
"""

import argparse
import hashlib
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERNS = ('rainbow', 'dark-sectors', 'dark-spirals', 'dark-diagonals')
SCENES = {'wide': 'hardware/enclosure/exports/scene.json',
          'narrow': 'designs/stacked/exports/scene.json'}
SOURCES = ('demo/patterns.gd', 'site/sample_patterns.gd', 'site/sample.py',
           'site/energy.mjs', 'site/sample_check.mjs', 'site/electrical-inputs.json',
           *SCENES.values())


def digest(path):
    data = path.read_bytes()
    if data.startswith(b'version https://git-lfs.github.com/spec/v1'):
        raise ValueError('Missing LFS content: ' + str(path))
    return hashlib.sha256(data).hexdigest()


def snapshot():
    return {path: digest(ROOT / path) for path in SOURCES}


def generate(output):
    godot = shutil.which('godot')
    node = shutil.which('node')
    if not godot or not node:
        raise RuntimeError('Required sample tools missing from PATH: godot and node')
    output = output.resolve()
    if ROOT / '.build' not in output.parents:
        raise ValueError('Study output must be a child of this checkout/.build')
    output.parent.mkdir(parents=True, exist_ok=True)
    before = snapshot()
    with tempfile.TemporaryDirectory(prefix='pattern-study-', dir=ROOT / '.build') as temp:
        stage = Path(temp)
        project = stage / 'project'
        project.mkdir()
        (project / 'project.godot').write_text('[application]\nconfig/name="Electrical sampler"\n')
        for source, destination in [('demo/patterns.gd', 'patterns.gd'),
                                    ('site/sample_patterns.gd', 'sample.gd')]:
            shutil.copyfile(ROOT / source, project / destination)
        record = {'schema_version': 1, 'sources': before, 'sets': [],
                  'tools': {'godot': subprocess.check_output([godot, '--version'], text=True).strip()},
                  'status': 'parameter-study-only; no physical/runtime qualification'}
        steps = 512
        while True:
            for design, scene_path in SCENES.items():
                scene = json.loads((ROOT / scene_path).read_text())
                prefix = stage / f'{design}-{steps}'
                command = [godot, '--headless', '--path', str(project), '--script',
                           'res://sample.gd', '--', str(ROOT / scene_path), str(prefix), str(steps)]
                # Repeat identical sampling and compare bytes, not rounded averages.
                previous = None
                for repeat in range(2):
                    result = subprocess.run(command, capture_output=True, text=True, timeout=180, check=True)
                    if 'PATTERN SAMPLE COMPLETE:' not in result.stdout or 'ERROR:' in result.stdout + result.stderr:
                        raise RuntimeError('Godot sample failed: ' + result.stdout + result.stderr)
                    current = {pattern: digest(Path(str(prefix) + '-' + pattern + '.f32')) for pattern in PATTERNS}
                    if repeat and current != previous:
                        raise RuntimeError('Nondeterministic shared pattern samples: ' + design)
                    previous = current
                for pattern in PATTERNS:
                    path = Path(str(prefix) + '-' + pattern + '.f32')
                    record['sets'].append({'design': design, 'pattern': pattern, 'steps': steps,
                                           'period_s': 8, 'file': path.name, 'sha256': current[pattern],
                                           'leds': [{'group': led['group'], 'index': led['index']} for led in scene['leds']]})
                print(f'SAMPLE REPEATABILITY PASS: {design}, {steps} steps', flush=True)
            (stage / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
            if steps >= 1024:
                result = subprocess.run([node, str(ROOT / 'site/sample_check.mjs'), str(stage / 'manifest.json')],
                                        capture_output=True, text=True, check=False)
                if result.returncode == 0:
                    print(result.stdout, end='', flush=True)
                    record['convergence'] = json.loads(result.stdout)
                    break
                if result.returncode != 2 or steps >= 8192:
                    raise RuntimeError('Sample convergence failed: ' + result.stdout + result.stderr)
            steps *= 2
        if snapshot() != before:
            raise RuntimeError('Inputs changed during sampling; study not published')
        record['accepted_steps'] = steps
        (stage / 'manifest.json').write_text(json.dumps(record, indent=2) + '\n')
        # Only our owned scratch directory is replaceable, never arbitrary output.
        if output.exists():
            old = json.loads((output / 'manifest.json').read_text())
            if old.get('schema_version') != 1 or not old.get('sets'):
                raise RuntimeError('Refusing unowned sample directory')
            shutil.rmtree(output)
        project_files = stage / 'project'
        shutil.rmtree(project_files)
        shutil.copytree(stage, output)
        print('PATTERN STUDY COMPLETE: ' + str(output), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '.build/energy-samples')
    generate(parser.parse_args().output)
