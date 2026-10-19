"""Generate and slice the delivered PrusaSlicer projects from one specification.

Reference projects have no heater setpoints or start/end machine program.
The print service must select its actual machine and PETG filament profile.
"""
import argparse
import json
import math
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


def is_ring(name):
    return name.startswith(('HaloRing','InnerRing','EdgeDiffuser','FitRing'))


def project_filename(name, material):
    stem=Path(name).stem
    return stem+('-'+material if material!='glow' and is_ring(name) else '')+'.3mf'


def settings(spec, name, material='glow'):
    bracket = name.startswith(('NecklaceLink', 'FitSuspensionBracket'))
    ring = is_ring(name)
    rear = name in {'RearPlate.stl', 'FitRear.stl', 'FitService.stl', 'FitController.stl', 'FitSuspensionRear.stl'}
    profile = spec['rear_plate'] if rear else spec['baffle'] if name.startswith(('FibonacciBaffle','FitFibonacciBaffle')) else spec['ring_outside'] if name.startswith(('EdgeDiffuser','FitRingOutside')) else spec['ring_cavity'] if ring else spec['optical_deck'] if name.startswith(('OpticalDeck','FitDeck','FitOptics')) else {}
    material_profile={'filament_density':str(spec['ring_materials'][material]['density_g_cm3']),
                      'filament_colour':spec['ring_materials'][material]['filament_colour']} if ring else {}
    return spec['reference_machine'] | spec['common'] | (spec['bracket'] if bracket else {}) | profile | material_profile


def project_names(inventory):
    return inventory['stl_files'] + [sample['file'] for sample in inventory['fit_samples']]


def project_jobs(inventory, spec):
    for material in spec['ring_materials']:
        for name in project_names(inventory):
            if material==spec['default_ring_material'] or is_ring(name):
                yield name, project_filename(name,material), material


def configuration(text):
    return dict(re.findall(r'^;?\s*([a-z][a-z_0-9]*) = (.*)$', text, re.M))


def verify_settings(actual, expected, name):
    for key, value in expected.items():
        if actual.get(key) != value:
            raise cad.CadError(f'{name}: effective {key}={actual.get(key)!r}, required {value!r}')


def bed_bounds(spec):
    points=[tuple(map(float,point.split('x'))) for point in spec['reference_machine']['bed_shape'].split(',')]
    return [min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]


def verify_bed(layers, bed, name):
    for index,layer in enumerate(layers,1):
        bounds=layer['extrusion_bounds_mm']
        if bounds is None:
            raise cad.CadError(f'Missing extrusion on layer {index}: '+name)
        if any(bounds[i]<bed[i]-.001 for i in (0,1)) or any(bounds[i]>bed[i]+.001 for i in (2,3)):
            raise cad.CadError(f'Extrusion outside reference bed on layer {index}: {name}: {bounds}')


def perimeter_layers(gcode):
    """Measure perimeter travel/widths and all extruded bounds, including brims and infill."""
    layers=[]
    width=None
    x=y=e=0.0
    relative_e=False
    role=''
    for line in gcode.splitlines():
        if line == ';LAYER_CHANGE':
            layers.append({'length_mm':0.0,'widths_mm':set(),'extrusion_bounds_mm':None})
        elif line.startswith(';TYPE:'):
            role=line[6:]
        elif line.startswith(';WIDTH:'):
            width=float(line[7:])
        command=line.split(';',1)[0].strip()
        if not command:
            continue
        words=command.split()
        values={key:float(value) for key,value in re.findall(r'([XYE])([-+]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))',command)}
        if words[0] in ('M82','M83'):
            relative_e=words[0]=='M83'
        elif words[0]=='G92':
            x,y,e=values.get('X',x),values.get('Y',y),values.get('E',e)
        elif words[0] in ('G0','G1'):
            nx,ny=values.get('X',x),values.get('Y',y)
            ne=e+(values.get('E',0.0)) if relative_e else values.get('E',e)
            travel=math.hypot(nx-x,ny-y)
            if layers and ne>e and travel>0:
                radius=(width or 0)/2
                bounds=[min(x,nx)-radius,min(y,ny)-radius,max(x,nx)+radius,max(y,ny)+radius]
                previous=layers[-1]['extrusion_bounds_mm']
                layers[-1]['extrusion_bounds_mm']=bounds if previous is None else [min(previous[i],bounds[i]) if i<2 else max(previous[i],bounds[i]) for i in range(4)]
            if layers and role in ('External perimeter','Perimeter') and ne>e and travel>0:
                layers[-1]['length_mm']+=travel
                if width is not None:
                    layers[-1]['widths_mm'].add(width)
            x,y,e=nx,ny,ne
    return layers


def generate(root):
    root = Path(root)
    spec = json.loads((root/cad.CAD/'print-spec.json').read_text())
    inventory = json.loads((root/cad.EXPORTS/'parts.json').read_text())
    bed=bed_bounds(spec)
    centre=f'{(bed[0]+bed[2])/2:g},{(bed[1]+bed[3])/2:g}'
    with tempfile.TemporaryDirectory(prefix='compass-project-', dir=root.parent) as temporary:
        for name, project_name, material in project_jobs(inventory,spec):
            config = Path(temporary)/'settings.ini'
            config.write_text(''.join(f'{k} = {v}\n' for k,v in settings(spec,name,material).items()))
            output = root/cad.EXPORTS/project_name
            expanded = Path(temporary)/'expanded.ini'
            result = subprocess.run([executable(), '--load', str(config), '--center', centre, '--export-3mf',
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
    masses = {name:{} for name in spec['ring_materials']}
    sample_masses = {name:{} for name in spec['ring_materials']}
    sample_names = [sample['file'] for sample in inventory['fit_samples']]
    with tempfile.TemporaryDirectory(prefix='compass-slice-', dir=root.parent) as temporary:
        for name, project_name, material in project_jobs(inventory,spec):
            project = root/cad.EXPORTS/project_name
            expected = settings(spec,name,material)
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
            perimeter=perimeter_layers(gcode)
            verify_bed(perimeter,bed_bounds(spec),name)
            if name.startswith(('HaloRing','InnerRing','EdgeDiffuser','FitRing')):
                # Cavity rings use two paths; the stronger outside wall uses four.
                # Both must remain continuous perimeter walls without gap fill.
                if len(perimeter)!=layers or any(f';TYPE:{kind}' in gcode for kind in ('Internal infill','Gap fill','Solid infill')):
                    raise cad.CadError('Ring wall needs continuous perimeter paths without infill: '+name)
                for layer, measured in enumerate(perimeter):
                    widths=measured['widths_mm']
                    nominal=float(expected['first_layer_extrusion_width' if layer==0 else 'extrusion_width'])
                    if not widths or min(widths)<nominal-.04 or max(widths)>nominal+.04:
                        raise cad.CadError(f'Ring wall deviates from nominal perimeter width on layer {layer+1}: '+name)
                if name=='EdgeDiffuser.stl':
                    p=json.loads((root/cad.CAD/'parameters.json').read_text())
                    circumference=math.tau*(p['edge_diffuser_radius']+p['edge_diffuser_thickness']/2)
                    # Total perimeter travel distinguishes four full circular
                    # paths from a missing path, double pass or partial wall.
                    paths=[layer['length_mm']/circumference for layer in perimeter]
                    if len(paths)!=layers or any(abs(count-4)>.1 for count in paths):
                        raise cad.CadError('Outside ring does not have four complete paths on every layer: '+name)
            if name in sample_names:
                sample_masses[material][Path(name).stem] = float(mass[1])
            else:
                masses[material][Path(name).stem] = float(mass[1])
            print(f'SLICE PASS: {project.name}, {layers} layers, {mass[1]} g including brim',flush=True)
    default=spec['default_ring_material']
    combined={name:masses[default] | mass for name,mass in masses.items()}
    combined_samples={name:sample_masses[default] | mass for name,mass in sample_masses.items()}
    if not fresh:
        inventory['slicer_mass_g_including_brim'] = combined[default]
        inventory['slicer_mass_by_ring_material'] = combined
        (root/cad.EXPORTS/'parts.json').write_text(json.dumps(inventory,indent=2)+'\n')
    version = subprocess.check_output([executable(),'--help'],text=True).splitlines()[0]
    for material in spec['ring_materials']:
        print(f'SLICER PASS: {material}: {len(combined[material])} products, {sum(combined[material].values()):.2f} g including brims; '
              f'{len(combined_samples[material])} disposable samples, {sum(combined_samples[material].values()):.2f} g separately. '
              'Physical printing and fit remain untested.',flush=True)
    return version


if __name__=='__main__':
    argparse.ArgumentParser(description=__doc__).parse_args()
    try:
        check(cad.ROOT)
    except (cad.CadError,OSError,subprocess.CalledProcessError) as exc:
        raise SystemExit(str(exc))
