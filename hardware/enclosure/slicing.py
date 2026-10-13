"""Generate and slice the delivered PrusaSlicer projects from one specification.

Reference projects have no heater setpoints or start/end machine program.
The print service must select its actual machine and PETG filament profile.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

import cad


def executable():
    path = shutil.which('prusa-slicer') or '/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer'
    if not Path(path).is_file():
        raise cad.CadError('Install PrusaSlicer: brew install --cask prusaslicer')
    return path


def settings(spec, name):
    bracket = name.startswith(('NecklaceLink', 'FitSuspensionBracket'))
    return spec['reference_machine'] | spec['common'] | (spec['bracket'] if bracket else {})


def project_names(inventory):
    return inventory['stl_files'] + [sample['file'] for sample in inventory['fit_samples']]


def configuration(text):
    return dict(re.findall(r'^;?\s*([a-z][a-z_0-9]*) = (.*)$', text, re.M))


def verify_settings(actual, expected, name):
    for key, value in expected.items():
        if actual.get(key) != value:
            raise cad.CadError(f'{name}: effective {key}={actual.get(key)!r}, required {value!r}')


def generate(root):
    root = Path(root)
    spec = json.loads((root/cad.CAD/'print-spec.json').read_text())
    inventory = json.loads((root/cad.EXPORTS/'parts.json').read_text())
    with tempfile.TemporaryDirectory(prefix='compass-project-', dir=root.parent) as temporary:
        for name in project_names(inventory):
            config = Path(temporary)/'settings.ini'
            config.write_text(''.join(f'{k} = {v}\n' for k,v in settings(spec,name).items()))
            output = (root/cad.EXPORTS/name).with_suffix('.3mf')
            expanded = Path(temporary)/'expanded.ini'
            result = subprocess.run([executable(), '--load', str(config), '--export-3mf',
                                     '--save', str(expanded), '--output', str(output), str(root/cad.EXPORTS/name)],
                                    text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            if result.returncode:
                raise cad.CadError('Project export failed: '+result.stdout)
            # PrusaSlicer 2.9 CLI exports geometry but omits the project config.
            # Write its own expanded config in its native project member.
            embedded=''.join('; '+line+'\n' for line in expanded.read_text().splitlines()
                             if re.match(r'^[a-z][a-z_0-9]* = ',line))
            with zipfile.ZipFile(output,'a',compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('Metadata/Slic3r_PE.config',embedded)


def check(root, fresh=True):
    root = Path(root)
    if fresh:
        cad.check_freshness(cad.Snapshot(root))
    spec = json.loads((root/cad.CAD/'print-spec.json').read_text())
    inventory = json.loads((root/cad.EXPORTS/'parts.json').read_text())
    total = sample_total = 0.0
    sample_names = [sample['file'] for sample in inventory['fit_samples']]
    masses = {}
    with tempfile.TemporaryDirectory(prefix='compass-slice-', dir=root.parent) as temporary:
        for name in project_names(inventory):
            project = (root/cad.EXPORTS/name).with_suffix('.3mf')
            expected = settings(spec,name)
            with zipfile.ZipFile(project) as archive:
                verify_settings(configuration(archive.read('Metadata/Slic3r_PE.config').decode()), expected, project.name)
            output = Path(temporary)/(name+'.gcode')
            # Slice the delivered project alone. No private settings or transforms.
            result = subprocess.run([executable(),'--export-gcode','--output',str(output),str(project)],
                                    text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            if result.returncode or re.search(r'warning|error|empty layer',result.stdout,re.I):
                raise cad.CadError('Slicer rejected '+name+':\n'+result.stdout)
            gcode = output.read_text()
            verify_settings(configuration(gcode), expected, name)
            layers = gcode.count(';LAYER_CHANGE')
            mass = re.search(r'; filament used \[g\] = ([\d.]+)',gcode)
            if not mass or layers<2 or ';TYPE:External perimeter' not in gcode or ';TYPE:Support material' in gcode:
                raise cad.CadError('Missing or unsupported toolpaths: '+name)
            if name in sample_names:
                sample_total += float(mass[1])
            else:
                total += float(mass[1])
                masses[Path(name).stem] = float(mass[1])
            print(f'SLICE PASS: {project.name}, {layers} layers, {mass[1]} g including brim',flush=True)
    if not fresh:
        inventory['slicer_mass_g_including_brim'] = masses
        (root/cad.EXPORTS/'parts.json').write_text(json.dumps(inventory,indent=2)+'\n')
    version = subprocess.check_output([executable(),'--help'],text=True).splitlines()[0]
    print(f'SLICER PASS: {len(masses)} products, {total:.2f} g including brims; '
          f'{len(sample_names)} disposable samples, {sample_total:.2f} g separately. '
          'Physical printing and fit remain untested.',flush=True)
    return version


if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        check(cad.ROOT)
    except (cad.CadError,OSError,subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc))
