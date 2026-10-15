"""Resolve the single component inventory into installed mass and design tables."""
from copy import deepcopy
import json
import math
from pathlib import Path, PurePosixPath

from hardware_spec import body_bolt_length
from slicing import project_filename

BEGIN = '<!-- BEGIN GENERATED BUILD INVENTORY -->'
END = '<!-- END GENERATED BUILD INVENTORY -->'


def resolve(spec, volumes, p, ring_material):
    rows = deepcopy(spec['components'])
    geometry = {v['name']:v for v in volumes}
    for row in rows:
        formula = row.get('mass_formula')
        if formula:
            if formula not in ('petg_volume','ring_petg_volume','acrylic_volume','finished_body_screw'):
                raise ValueError('Unknown mass formula: '+str(formula))
            if 'mass_g_per_unit' in row or 'mass_range_g_per_unit' in row:
                raise ValueError('A component must specify a mass formula or a literal mass, not both: '+row['id'])
        if formula=='finished_body_screw':
            length=body_bolt_length(p)
            # Scale published stock mass by the same nominal head/shank envelope.
            # Socket, threads and the small finished chamfer remain estimates.
            head_equivalent=(5.5/3)**2*3
            mass=row['stock_mass_g_per_unit']*(length+head_equivalent)/(p['body_bolt_stock_length']+head_equivalent)
            row['mass_g_per_unit']=mass
            row['mass_range_g_per_unit']=[mass*.65,mass*1.5]
            row['dimensions']=(f"M3, finish to {length:.3f} mm under head from {p['body_bolt_stock_length']:g} mm stock; "
                               f"{p['body_bolt_tip_projection']:g} mm nominal nut projection, "
                               f"{p['body_bolt_tip_chamfer']:g} mm tip chamfer; measure actual clamp stack")
        elif formula:
            volume = geometry[row['cad_part']]['volume_cm3']
            density = ring_material['density_g_cm3'] if formula=='ring_petg_volume' else 1.27 if formula in ('petg_volume','ring_petg_volume') else 1.19
            if formula=='ring_petg_volume':
                row['material']=ring_material['filament']
                row['source']=str(PurePosixPath(row['source']).with_name(project_filename(row['cad_part']+'.stl',ring_material['id'])))
                row['mass_basis']=f"CAD net solid volume x {density:g} g/cm3; {ring_material['density_basis']}; verify printed mass"
                row['stock_sources']=[{'label':ring_material['filament'],'url':ring_material['source']}]
            mass = volume*density
            row['mass_g_per_unit'] = mass
            row['mass_range_g_per_unit'] = ([mass*.70,mass*1.08] if formula in ('petg_volume','ring_petg_volume')
                                           else [mass*.9,mass*1.1])
            if 'bounds_mm' in geometry[row['cad_part']]:
                row['dimensions'] += '; CAD bounds '+ ' x '.join(f'{v:.2f}' for v in geometry[row['cad_part']]['bounds_mm'])+' mm'
        if row.get('length_parameter'):
            row['installed_quantity'] = p[row['length_parameter']]/p['strip_density']
            row['unit'] = 'm fitted strip'
            row['dimensions'] = f"{int(p[row['length_parameter']])} pixels, {row['installed_quantity']*1000:.3f} mm cut length; CAD back 10 x 0.3 mm, package depth 2 mm"
        if row['id']=='battery':
            row['mass_g_per_unit'] = p['battery_mass_g']
            row['mass_range_g_per_unit'] = [p['battery_mass_g']*.9474,p['battery_mass_g']*1.1053]
        q = row['installed_quantity']
        row['installed_mass_g'] = round(q*row['mass_g_per_unit'],4)
        row['installed_mass_range_g'] = [round(q*v,4) for v in row['mass_range_g_per_unit']]
    validate(rows, volumes)
    return rows


def validate(rows, volumes=None):
    if len({r['id'] for r in rows}) != len(rows):
        raise ValueError('Duplicate component ID')
    for r in rows:
        q=r['installed_quantity']; low,high=r['mass_range_g_per_unit']; m=r['mass_g_per_unit']
        if not all(math.isfinite(v) and v>0 for v in (q,low,m,high)) or not low<=m<=high:
            raise ValueError('Missing/nonpositive mass allowance or invalid range: '+r['id'])
        if r['mass_kind'] not in ('published','calculated','estimated','measured'):
            raise ValueError('Unknown mass basis: '+r['id'])
        for key in ('source','dimensions','material','mass_basis','status','purchase_quantity'):
            if not r.get(key):
                raise ValueError('Incomplete inventory '+r['id']+': '+key)
    if volumes is not None:
        printed={v['name'] for v in volumes if v['printed']}
        accounted={r['cad_part'] for r in rows if r.get('mass_formula') in ('petg_volume','ring_petg_volume')}
        if printed != accounted:
            raise ValueError('Printed inventory differs from manufactured geometry')


def totals(rows):
    def sum_rows(selected):
        return {'nominal_g':round(sum(r['installed_mass_g'] for r in selected),1),
                'range_g':[round(sum(r['installed_mass_range_g'][i] for r in selected),1) for i in (0,1)]}
    pendant=[r for r in rows if r['group']=='pendant']
    necklace=[r for r in rows if r['group']=='necklace']
    external=[r for r in rows if r['group']=='external']
    pack=next(r for r in rows if r['id']=='battery')
    external_pendant=[r for r in pendant if r['id'] not in ('battery','blank')]+[r for r in external if r['id']=='gland']
    belt=[pack]+[r for r in external if r['id']!='gland']
    result={name:sum_rows(selected) for name,selected in (
        ('complete_pendant',pendant),('necklace',necklace),('total_worn',pendant+necklace),
        ('external_battery_pendant',external_pendant),('external_belt_and_lead',belt),
        ('external_total_worn',external_pendant+necklace+belt))}
    result['basis']='Complete installed-component estimate; independent low/high allowances summed, not a confidence interval. Printed PETG uses CAD solid-volume ceiling; fit samples, brims, retail stock, spares and charger excluded.'
    result['outstanding_measurements']=[r['id'] for r in rows if r['group']!='tool']
    return result


def markdown(rows, mass):
    def link(source,label):
        return f'[{label}]({source})'
    lines=['## Complete build parts list and mass estimate','',
           'Generated from [component-inventory.json](hardware/enclosure/component-inventory.json). '
           'Source review: 2026-10-12. These are selected baseline parts and explicit unresolved allowances. '
           'Supply status can change. An incompatible candidate does not authorize a substitution or a CAD resize.','',
           '| Assembly | Estimated installed mass | Allowance range |',
           '| --- | ---: | ---: |']
    for label,key in [('Complete pendant, internal battery','complete_pendant'),('Necklace','necklace'),('Total worn, internal battery','total_worn'),('Optional external-battery pendant','external_battery_pendant'),('Optional belt pack, carrier and lead','external_belt_and_lead'),('Total worn, external option','external_total_worn')]:
        v=mass[key];lines.append(f"| {label} | {v['nominal_g']:.1f} g | {v['range_g'][0]:.1f}–{v['range_g'][1]:.1f} g |")
    lines+=['',mass['basis'],'',
            'No component mass is measured. Published values describe supplier parts. Calculated values use net geometry '
            'and stated density. Estimated values include every unresolved item. Weigh populated boards once, finished '
            'printed parts after brim removal, each cut strip, the harness, finished optics, and all fittings. '
            'Then weigh the complete pendant, necklace and optional belt assembly. Replace the allowances with those measurements.','',
            '| Component / exact variant or unresolved requirement | Installed | Purchase quantity | Dimensions / material | Installed mass, range | Basis / fit and supply status |',
            '| --- | --- | --- | --- | ---: | --- |']
    for r in rows:
        low,high=r['installed_mass_range_g']; sources=link(r['source'],r['label'])
        for extra in r.get('stock_sources',[]):
            sources+='; '+link(extra['url'],extra['label'])
        lines.append(f"| {sources} ({r['group']}) | {r['installed_quantity']:.4g} {r['unit']} | {r['purchase_quantity']} | {r['dimensions']}; {r['material']} | {r['installed_mass_g']:.2f} g ({low:.2f}–{high:.2f}) | **{r['mass_kind']}**: {r['mass_basis']}. {r['status']} |")
    lines+=['', 'Fit samples are disposable and do not enter the assembly or mass total. '
            'The external charger is a tool. The external option moves the same protected pack off the pendant, '
            'replaces the entry blank with a gland, and adds the carrier and cable; it does not add a second pack.','',
            'Release tests remain unverified: print fit, flatness, layer strength, hardware retention, sustained load, '
            'repeated load, optical fit, heat and dust. Use the upper total-worn mass bound for provisional load checks '
            'until measured mass is available. See the [service and suspension requirements](hardware/enclosure/README.md#service-inspection-and-suspension-release).','']
    return '\n'.join(lines)


def export(root):
    root=Path(root); directory=root/'hardware/enclosure'
    parts_path=directory/'exports/parts.json'
    parts=json.loads(parts_path.read_text())
    spec=json.loads((directory/'component-inventory.json').read_text())
    p=parts['parameters_for_inventory']
    print_spec=json.loads((directory/'print-spec.json').read_text())
    variants={}
    for name,material in print_spec['ring_materials'].items():
        rows=resolve(spec,parts['volumes'],p,material)
        variants[name]={'filament':material['filament'],'components':rows,'mass_estimate':totals(rows)}
    parts['material_variants']=variants
    selected=variants[print_spec['default_ring_material']]
    rows,mass=selected['components'],selected['mass_estimate']
    parts['components']=rows;parts['mass_estimate']=mass
    parts_path.write_text(json.dumps(parts,indent=2)+'\n')
    doc=root/'design-v2.md';text=doc.read_text(); section=BEGIN+'\n'+markdown(rows,mass)+'\n### Ring material options\n\nBoth versions share the same '+str(len(parts['stl_files']))+' printed parts and 2.0 mm outside wall. Qualify each filament with production samples. Optical values remain unmeasured.\n\n| Ring filament | Pendant estimate | Total worn estimate |\n| --- | ---: | ---: |\n'+''.join(f"| {v['filament']} | {v['mass_estimate']['complete_pendant']['nominal_g']:.1f} g | {v['mass_estimate']['total_worn']['nominal_g']:.1f} g |\n" for v in variants.values())+END
    if BEGIN in text:
        start=text.index(BEGIN);stop=text.index(END,start)+len(END)
        text=text[:start]+section+text[stop:]
    else:
        marker='## System structure'
        text=text.replace(marker,section+'\n\n'+marker)
    doc.write_text(text)
