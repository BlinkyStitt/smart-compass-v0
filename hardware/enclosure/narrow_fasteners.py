"""Source-backed narrow cap-screw selection; mass allowance factors stay fixed."""
import hashlib,json,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
DIRECTORY=HERE.parents[1]/'designs/stacked'
SOURCE_HASHES={'accu-m2-8-datasheet.pdf': '25f0d7baf7302436a0448fef665fce99561794015071af8455c8d92700bef65a', 'accu-m2-16-datasheet.pdf': 'ee8929c940ac03f0616418a37b66562db8ecc70fc04313e60b0a9d4d7e75b96e', 'accu-m2-20-datasheet.pdf': 'd8d187cbf7a8086dfbd0e0b6c75a703209a7935f7d49551ff54da41fd39278e2', 'ampg.pdf': 'edd73cdb08452be9152d2b76fd8f0640a4a8a2a54e453f8ee2de2b4127893d8c', 'timet.pdf': '824684f7d5603af19e0d0862e1af1289f4ea64ae7fac7f54e649ae0f80040822'}


def load(directory=DIRECTORY):
    directory=Path(directory);data=json.loads((directory/'fasteners.json').read_text())
    if data.get('material')!='ASTMGrade5 Ti-6Al-4V, natural finish' or data.get('nominal_density_g_cm3')!=4.42 or data.get('mass_factors')!=[.65,1.5] or data.get('physical_acceptance')!='unmeasured':raise ValueError('Review the selected narrow screw material and retain the mass allowances')
    source=directory/'sources/fasteners';index=json.loads((source/'index.json').read_text())
    if {row['file']:row['sha256'] for row in index}!=SOURCE_HASHES:raise ValueError('Selected screw source index changed')
    for row in index:
        raw=(source/row['file']).read_bytes()
        if len(raw)!=row['bytes'] or hashlib.sha256(raw).hexdigest()!=SOURCE_HASHES[row['file']]:raise ValueError('Selected screw source bytes changed '+row['file'])
    parts=data['parts'];names=[row['name'] for row in parts]
    if len(names)!=52 or len(names)!=len(set(names)) or any('Screw' not in name for name in names):raise ValueError('Narrow titanium cap-screw census changed')
    for row in parts:
        size=row['thread_diameter_mm'];length=row['finished_under_head_length_target_mm'];stock=row['stock_under_head_length_mm']
        if size not in [2,3] or isinstance(length,bool) or not isinstance(length,(float,int)) or not math.isfinite(length) or not 0<length<=stock:raise ValueError('Invalid selected screw finish target')
        if size==2 and stock==20 and length<16:raise ValueError('Use fully threaded short stock for the shorter clamp stacks')
        if row['source_file'] not in SOURCE_HASHES:raise ValueError('Missing selected screw source')
        expected=('SSCF-M2-'+str(stock)+'-TI5') if size==2 and stock in [8,16] else 'SSC-M2-20-TI5' if size==2 and stock==20 else 'ZS755M3X'+str(stock) if size==3 and stock in [6,10] else None
        if expected is None or row['stock_part']!=expected or [row['head_diameter_mm'],row['head_height_mm']]!=([3.8,2] if size==2 else [5.5,3]):raise ValueError('Screw envelope differs from the published selected stock')
    return data,{row['name']:row for row in parts}


def selected_mass(product,data,selection):
    row=selection.get(product['name'])
    if row is None:return None
    radius=row['thread_diameter_mm']/2
    expected=(math.pi*radius**2*row['finished_under_head_length_target_mm']+math.pi*(row['head_diameter_mm']/2)**2*row['head_height_mm'])/1000
    if abs(product['volume_cm3']-expected)>1e-8:raise ValueError('Narrow selected screw CAD envelope changed '+product['name'])
    nominal=product['volume_cm3']*data['nominal_density_g_cm3']
    return row,nominal,[nominal*v for v in data['mass_factors']]
