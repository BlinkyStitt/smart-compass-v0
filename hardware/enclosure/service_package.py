"""Build a self-contained, sample-first print-service shipment from checked exports."""
import csv
import hashlib
import html
import io
import json
from pathlib import Path
from string import Template
from types import MappingProxyType
import zipfile

import cad
import slicing

def archive_name(material):
    return 'smart-compass-'+material+'-print-service.zip'
LABELS = MappingProxyType({
    'OpticalDeck': 'Front optical deck', 'BarrelFrame': 'Main barrel frame',
    'RearPlate': 'Removable rear plate', 'NecklaceLink0': 'Left necklace bracket',
    'NecklaceLink1': 'Right necklace bracket', 'ServiceCover': 'USB service cover',
    'HaloRing': 'Halo light ring', 'InnerRing': 'Inner light ring',
    'EdgeDiffuser': 'Outside light ring',
    **{f'VentGuard{i}': f'Vent guard {i+1}' for i in range(4)},
    **{f'CircleRimFoot{i}': f'Centre rim spacer {i+1}' for i in range(3)},
})
REFERENCES = ('assembly.png', 'exploded.png', 'assembly-section.svg', 'smart-compass.step')


def shipment(root, material='glow'):
    root = Path(root)
    directory = root/cad.CAD
    exports = root/cad.EXPORTS
    parts = json.loads((exports/'parts.json').read_text())
    spec = json.loads((directory/'print-spec.json').read_text())
    parameters = parts['parameters_for_inventory']
    choice = spec['ring_materials'][material]
    components = {row['cad_part']: row for row in parts['material_variants'][material]['components']
                  if row.get('mass_formula') in ('petg_volume', 'ring_petg_volume')}
    rows, files = [], {}
    groups = [('01-SAMPLES-PRINT-FIRST', [(name['file'], name['source_part']) for name in parts['fit_samples']]),
              ('02-FULL-PARTS-HOLD', [(name, Path(name).stem) for name in parts['stl_files']])]
    for stage, names in groups:
        for name, source in names:
            if Path(name).name != name or not name.endswith('.stl') or '\\' in name:
                raise cad.CadError('Unsafe service part name: '+name)
            component = components[source]
            quantity = 1 if stage.startswith('01-') else component['installed_quantity']
            if not isinstance(quantity, (int, float)) or quantity != int(quantity) or quantity <= 0:
                raise cad.CadError('Invalid service part quantity: '+name)
            profile = slicing.settings(spec, name, material)
            project = Path(name).with_suffix('.3mf').name
            data = (exports/slicing.project_filename(name,material)).read_bytes()
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                slicing.verify_settings(slicing.configuration(archive.read('Metadata/Slic3r_PE.config').decode()), profile, project)
            path = stage+'/'+project
            fallback = '03-STL-ALTERNATIVES/'+stage+'/'+name
            if path in files or fallback in files:
                raise cad.CadError('Duplicate service part: '+name)
            files[path] = data
            files[fallback] = (exports/name).read_bytes()
            rows.append({'stage': stage, 'file': path, 'description': LABELS.get(source, source)+(' fit sample' if stage.startswith('01-') else ''),
                         'quantity': int(quantity), 'material': component['material'],
                         'layer_mm': profile['layer_height'], 'perimeters': profile['perimeters'],
                         'infill': profile['fill_density'], 'infill_pattern': profile['fill_pattern'],
                         'path_mm': profile['extrusion_width'], 'first_path_mm': profile['first_layer_extrusion_width'],
                         'top_layers': profile['top_solid_layers'], 'bottom_layers': profile['bottom_solid_layers']})
    for name in REFERENCES:
        files['04-REFERENCE-DO-NOT-PRINT/'+name] = (exports/name).read_bytes()
    output = io.StringIO(newline='')
    writer = csv.DictWriter(output, fieldnames=list(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    files['ORDER.csv'] = output.getvalue().encode()
    # A content identifier avoids misleading Git revisions inside isolated builds.
    template = (directory/'service-guide.html').read_text()
    identifier = hashlib.sha256(template.encode()+b''.join(name.encode()+hashlib.sha256(data).digest()
                                         for name, data in sorted(files.items()))).hexdigest()[:16]
    def table(stage):
        result = []
        for row in rows:
            if row['stage'] != stage:
                continue
            cells = [f'<a href="{html.escape(row["file"])}">{html.escape(Path(row["file"]).name)}</a>',
                     html.escape(row['description']), str(row['quantity']), html.escape(row['material']),
                     f'{row["layer_mm"]} mm / {row["perimeters"]}',
                     f'{row["infill"]} {row["infill_pattern"]}',
                     f'{row["path_mm"]} / {row["first_path_mm"]} mm',
                     f'{row["top_layers"]} / {row["bottom_layers"]}']
            result.append('<tr>'+''.join('<td>'+cell+'</td>' for cell in cells)+'</tr>')
        return '\n'.join(result)
    counts = {stage: sum(row['quantity'] for row in rows if row['stage'] == stage) for stage, names in groups}
    values = dict(material_label=choice['label'], material_name=choice['filament'],
                  nozzle_instructions=choice['nozzle'], evidence=choice['evidence'], optical_acceptance=choice['acceptance'],
                  package_id=identifier, samples=counts[groups[0][0]], products=counts[groups[1][0]],
                  sample_rows=table(groups[0][0]), product_rows=table(groups[1][0]),
                  cavity_wall=f'{parameters["ring_diffuser_thickness"]:.1f}',
                  outside_wall=f'{parameters["edge_diffuser_thickness"]:.1f}',
                  mirror_separation=f'{parameters["front_plane_z"]-parameters["mirror_back_z"]-parameters["rear_acrylic_thickness"]:.1f}',
                  cavity_paths=spec['ring_cavity']['perimeters'], cavity_path=spec['ring_cavity']['extrusion_width'],
                  outside_paths=spec['ring_outside']['perimeters'], outside_path=spec['ring_outside']['extrusion_width'],
                  outside_first_path=spec['ring_outside']['first_layer_extrusion_width'],
                  brim=spec['common']['brim_width'], brim_gap=spec['common']['brim_separation'],
                  foot=spec['common']['elefant_foot_compensation'],
                  deck_layer=spec['optical_deck']['layer_height'], deck_top=spec['optical_deck']['top_solid_layers'],
                  deck_bottom=spec['optical_deck']['bottom_solid_layers'], first_layer=spec['common']['first_layer_height'])
    guide = Template(template).substitute(values)
    files['START-HERE.html'] = guide.encode()
    files['START-HERE.txt'] = (f'SMART COMPASS - {choice["label"]} - PRINT SERVICE HANDOFF\nPackage {identifier}\n\n'
        'Unzip this entire package, then open START-HERE.html in a web browser.\n'
        f'Quote both stages. Print only the {values["samples"]} samples in 01-SAMPLES-PRINT-FIRST first.\n'
        f'Hold the {values["products"]} full parts in 02-FULL-PARTS-HOLD until the customer releases the order.\n'
        'ORDER.csv gives the quantities and settings. Each 3MF file contains one part.\n'
        'STL files are alternatives to the matching 3MF files, not extra parts.\n'
        'Keep dimensions and supplied orientation. Use millimetres for STL import.\n'
        'Reference images and the assembly STEP are not print jobs.\n'
        '300 x 300 mm printer required. Do not split or scale the circles.\n'
        f'Use the specified opaque PETG and {choice["filament"]}.\n'
        'Projects omit heater setpoints and machine start/end programs; select your real machine/filament presets.\n'
        'CAD and slicing passed. Physical print, fit, strength and optics acceptance remain pending.\n').encode()
    files['CHECKSUMS.sha256'] = ''.join(hashlib.sha256(data).hexdigest()+'  '+name+'\n'
                                      for name, data in sorted(files.items())).encode()
    return files


def verify(path, expected):
    with zipfile.ZipFile(path) as archive:
        if len(archive.namelist()) != len(expected) or set(archive.namelist()) != set(expected):
            raise cad.CadError('Service package file inventory differs')
        for name, data in expected.items():
            if archive.read(name) != data:
                raise cad.CadError('Service package content differs: '+name)


def generate(root):
    root = Path(root)
    spec=json.loads((root/cad.CAD/'print-spec.json').read_text())
    for material in spec['ring_materials']:
        files = shipment(root,material)
        target = root/cad.EXPORTS/archive_name(material)
        with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            for name, data in sorted(files.items()):
                entry = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
                entry.compress_type = zipfile.ZIP_DEFLATED
                entry.external_attr = 0o100644 << 16
                archive.writestr(entry, data)
        verify(target, files)
        print('PRINT SERVICE PACKAGE PASS: '+str(target), flush=True)
