"""Slice every manufactured STL and reject reported print stability defects.

Temporary G-code checks geometry with a generic 0.4 mm nozzle. It is not a
machine program for the user's printer and is not delivered as a print file.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

import cad


def check(root, fresh=True):
    root=Path(root)
    if fresh:
        cad.check_freshness(cad.Snapshot(root))
    executable=shutil.which('prusa-slicer') or '/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer'
    if not Path(executable).is_file():
        raise cad.CadError('Install PrusaSlicer: brew install --cask prusaslicer')
    directory=root/cad.CAD
    inventory=json.loads((root/cad.EXPORTS/'parts.json').read_text())
    basis=inventory['print_basis']
    total=0.0
    with tempfile.TemporaryDirectory(prefix='compass-slice-', dir=root.parent) as temporary:
        for name in inventory['stl_files']:
            output=Path(temporary)/(name+'.gcode')
            x,y=basis['bed_mm']
            command=[executable,'--load',str(directory/'print-settings.ini'),
                     '--bed-shape',f'0x0,{x}x0,{x}x{y},0x{y}',
                     '--nozzle-diameter','0.4','--filament-diameter','1.75','--filament-density','1.27','--filament-type','PETG',
                     '--export-gcode','--output',str(output)]
            if name.startswith('NecklaceLink'):
                command += ['--perimeters','6','--fill-density','100%','--fill-pattern','rectilinear']
            result=subprocess.run(command+[str(root/cad.EXPORTS/name)],text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
            if result.returncode or re.search(r'warning|error|empty layer',result.stdout,re.I):
                raise cad.CadError('Slicer rejected '+name+':\n'+result.stdout)
            gcode=output.read_text()
            layers=gcode.count(';LAYER_CHANGE')
            mass=re.search(r'; filament used \[g\] = ([\d.]+)',gcode)
            if not mass or layers<2 or ';TYPE:External perimeter' not in gcode or ';TYPE:Support material' in gcode:
                raise cad.CadError('Missing or unsupported toolpaths: '+name)
            total+=float(mass[1])
            print(f'SLICE PASS: {name}, {layers} layers, {mass[1]} g including brim',flush=True)
    version=subprocess.check_output([executable,'--help'],text=True).splitlines()[0]
    print(f'SLICER PASS: {len(inventory["stl_files"])} parts; {total:.2f} g including brims. '
          'No reported print warnings. Physical printing and fit remain untested.',flush=True)
    return version


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    try:
        check(cad.ROOT)
    except (cad.CadError,OSError,subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc))
