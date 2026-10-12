"""Rebuild all CAD outputs, or check their working-tree/staged freshness."""

import argparse
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CAD = 'hardware/enclosure'
MASTER = CAD + '/smart-compass.FCStd'
EXPORTS = CAD + '/exports'
MANIFEST = CAD + '/exports-manifest.json'
INPUTS = (
    'justfile',
    *(CAD + '/' + name for name in (
        'cad.py', 'build.py', 'check.py', 'geometry.py',
        'Run.FCMacro', 'Build.FCMacro', 'Check.FCMacro',
        'parameters.json', 'fibonacci256-layout.json', 'smart-compass.FCStd',
        'test_geometry.py', 'test_cad.py', 'demo_export.py',
    )),
    *('demo/' + name for name in (
        'project.godot', 'main.tscn', 'main.gd', 'optics.gdshader',
        'sleeve.gdshader', 'cell.gdshader', 'centre.gdshader', 'cavity_trace.gdshaderinc',
        'diagnostic.gdshader', 'run.py', 'reference.py', 'test_demo.py',
    )),
)
FIXED_EXPORTS = frozenset('''
amulet-demo.mp4 assembly-section.svg assembly.png circle-alignment-overlay.svg
diffusers.png edge-diffuser.svg edge.png electronics.png
exploded.png front-acrylic.svg front-mirror.svg
front.png halo-ring-diffuser.svg inner-ring-diffuser.svg outer-black-acrylic.svg
parts.json rear-mirror.svg rear.png smart-compass.step turntable-poster.png
turntable.gif wood-fibonacci-mask.svg
amulet.glb scene.json single-sheet-section.svg lighting-demo.mp4
infinity-rainbow.gif infinity-pulse.gif infinity-colour.gif
'''.split()) | frozenset(f'demo-{view}-{light}.png'
                        for view in ('front', 'steep', 'edge', 'rear')
                        for light in ('night', 'indoor', 'overcast', 'sun'))
GENERATED_SUFFIXES = {'.stl', '.step', '.svg', '.png', '.gif', '.mp4', '.json', '.glb'}


class CadError(Exception):
    pass


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Snapshot:
    def __init__(self, root, staged=False):
        self.root = Path(root)
        self.staged = staged

    def read(self, path):
        if self.staged:
            result = subprocess.run(['git', 'show', ':' + path], cwd=self.root,
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode:
                raise CadError('Missing staged file: ' + path)
            return result.stdout
        try:
            return (self.root / path).read_bytes()
        except OSError as exc:
            raise CadError('Cannot read ' + path + ': ' + str(exc)) from exc

    def export_paths(self):
        if self.staged:
            output = subprocess.check_output(
                ['git', 'ls-files', '-z', '--', EXPORTS + '/'], cwd=self.root)
            paths = [p.decode() for p in output.split(b'\0') if p]
        else:
            paths = [p.relative_to(self.root).as_posix()
                     for p in (self.root / EXPORTS).rglob('*') if p.is_file()]
        return {p for p in paths if PurePosixPath(p).suffix.lower() in GENERATED_SUFFIXES}


def load_json(snapshot, path):
    try:
        return json.loads(snapshot.read(path))
    except (ValueError, UnicodeError) as exc:
        raise CadError('Invalid JSON: ' + path) from exc


def required_exports(snapshot):
    parts = load_json(snapshot, EXPORTS + '/parts.json')
    names = parts.get('stl_files') if isinstance(parts, dict) else None
    if not isinstance(names, list) or not names:
        raise CadError('parts.json must list the generated STL files')
    for name in names:
        if (not isinstance(name, str) or not name.endswith('.stl')
                or PurePosixPath(name).name != name or '\\' in name):
            raise CadError('Unsafe STL filename in parts.json: ' + repr(name))
    if len(set(names)) != len(names):
        raise CadError('Duplicate STL filename in parts.json')
    return {EXPORTS + '/' + name for name in FIXED_EXPORTS.union(names)}


def hashes(snapshot, paths):
    result = {}
    for path in sorted(paths):
        data = snapshot.read(path)
        if not data:
            raise CadError('Empty CAD file: ' + path)
        result[path] = digest(data)
    return result


def validate_inventory(snapshot):
    expected = required_exports(snapshot)
    actual = snapshot.export_paths()
    if expected != actual:
        details = (['Missing export: ' + p for p in sorted(expected - actual)]
                   + ['Unexpected export: ' + p for p in sorted(actual - expected)])
        raise CadError('\n'.join(details))
    return expected


def check_freshness(snapshot):
    manifest = load_json(snapshot, MANIFEST)
    if not isinstance(manifest, dict) or manifest.get('format_version') != 1:
        raise CadError('Unsupported CAD freshness manifest')
    exports = validate_inventory(snapshot)
    changed = []
    for group, paths in (('inputs', set(INPUTS)), ('exports', exports)):
        recorded = manifest.get(group)
        if not isinstance(recorded, dict) or set(recorded) != paths:
            raise CadError('CAD manifest has an incomplete ' + group + ' inventory')
        current = hashes(snapshot, paths)
        changed.extend(path for path in current if recorded[path] != current[path])
    if changed:
        raise CadError('CAD files differ from the last complete build:\n'
                       + '\n'.join(changed))


@contextmanager
def build_lock(root):
    # Keep the lock file: unlinking a held lock can let two builds run at once.
    name = 'smart-compass-cad-' + digest(str(root.resolve()).encode())[:20] + '.lock'
    with (Path(tempfile.gettempdir()) / name).open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CadError('A CAD rebuild is already running for this checkout') from exc
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '-', dir=path.parent)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
        os.replace(temporary, path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def ensure_unchanged(root, original):
    current = hashes(Snapshot(root), INPUTS)
    changed = [path for path in current if original[path] != current[path]]
    if changed:
        raise CadError('Source changed during the build; no results were copied back:\n'
                       + '\n'.join(changed))


def native_stage(freecad, directory, stage):
    result = directory.parent / (stage + '-complete.json')
    env = dict(os.environ, SC_CAD_DIR=str(directory), SC_CAD_STAGE=stage,
               SC_CAD_RESULT=str(result))
    print('CAD: native ' + stage, flush=True)
    subprocess.run([freecad, str(directory / 'Run.FCMacro')], env=env, check=True)
    # FreeCAD can return zero after a macro exception. Require explicit success.
    try:
        record = json.loads(result.read_text())
    except (OSError, ValueError) as exc:
        raise CadError('Native ' + stage + ' did not finish; inspect FreeCAD output') from exc
    if record.get('stage') != stage or not record.get('freecad_version'):
        raise CadError('Invalid native completion record for ' + stage)
    return record['freecad_version']


def publish(root, staged, original, tools):
    exports = validate_inventory(staged)
    manifest = {
        'format_version': 1,
        'tools': tools,
        'inputs': hashes(staged, INPUTS),
        'exports': hashes(staged, exports),
    }
    try:
        previous_stls = {p for p in required_exports(Snapshot(root)) if p.endswith('.stl')}
    except CadError:
        # Missing/damaged generated output must not prevent a rebuild. Without
        # its inventory, do not delete old meshes; the final check rejects orphans.
        previous_stls = set()
    ensure_unchanged(root, original)
    # Replace each file atomically. Write the manifest last so an interrupted
    # publication cannot pass the freshness check with mixed generations.
    for path in sorted(exports | {MASTER}):
        atomic_write(root / path, staged.read(path))
    for path in sorted(previous_stls - exports):
        (root / path).unlink(missing_ok=True)
    atomic_write(root / MANIFEST, (json.dumps(manifest, indent=2, sort_keys=True) + '\n').encode())
    check_freshness(Snapshot(root))


def rebuild(root):
    freecad = shutil.which('freecad') or '/Applications/FreeCAD.app/Contents/Resources/bin/freecad'
    ffmpeg, ffprobe = shutil.which('ffmpeg'), shutil.which('ffprobe')
    godot = shutil.which('godot')
    if not Path(freecad).is_file() or not (ffmpeg and ffprobe and godot):
        raise CadError('Install the build tools: brew install just ffmpeg; brew install --cask freecad godot')
    with build_lock(root), tempfile.TemporaryDirectory(prefix='smart-compass-cad-') as temporary:
        source = Snapshot(root)
        staged = Snapshot(Path(temporary))
        original = {}
        for path in INPUTS:
            data = source.read(path)
            original[path] = digest(data)
            target = staged.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        directory = staged.root / CAD
        subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', str(directory),
                        '-p', 'test_*.py', '-v'], cwd=staged.root, check=True)
        version = native_stage(freecad, directory, 'build')
        native_stage(freecad, directory, 'check')
        native_stage(freecad, directory, 'demo')
        print('CAD: validate and capture interactive lighting comparisons', flush=True)
        subprocess.run([sys.executable, str(staged.root / 'demo/run.py'), 'capture'], check=True)
        tools = {'freecad': version}
        tools['godot'] = subprocess.check_output([godot, '--version'], text=True).strip()
        for name, executable in (('ffmpeg', ffmpeg), ('ffprobe', ffprobe)):
            tools[name] = subprocess.check_output([executable, '-version'], text=True).splitlines()[0]
        publish(root, staged, original, tools)
        mass = load_json(Snapshot(root), EXPORTS + '/parts.json')['mass_estimate']
        print('CAD BUILD COMPLETE: model and all exports checked; freshness manifest written.', flush=True)
        print(f"Partial mass: {mass['mechanical_subset_g']} g mechanical; "
              f"{mass['internal_pack_subset_g']} g with candidate battery. "
              'Electronics, LEDs, wiring and hardware remain excluded.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'check'))
    parser.add_argument('--staged', action='store_true', help='Check the Git index, not working files')
    args = parser.parse_args()
    if args.staged and args.command != 'check':
        parser.error('--staged only applies to check')
    try:
        if args.command == 'build':
            rebuild(ROOT)
        else:
            check_freshness(Snapshot(ROOT, staged=args.staged))
            print('CAD FRESHNESS PASS: ' + ('staged files' if args.staged else 'working files'))
    except (CadError, OSError, subprocess.CalledProcessError) as exc:
        print('CAD ERROR: ' + str(exc), file=sys.stderr)
        print('Save and close the model, then run `just cad`.', file=sys.stderr)
        if args.staged:
            print('Stage the model, build sources, exports and manifest together.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
