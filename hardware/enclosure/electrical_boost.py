"""Bind PowerBoost current leads to its optional3.5mm terminal footprints.

The retained PCB supplies pad locations and nets. Nominal footprints and vendor
ratings do not qualify supplied parts, completed joints or enclosed operation.
"""

import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from electrical_board import extract

HERE=Path(__file__).resolve().parent
SOURCE='sources/powerboost-1000-basic'
REVISION='493d06d70537ce418355b395bb251a661d683150'
FILES={
    'Adafruit PowerBoost 1000 Basic.brd':'8a93f4cd2b3bb6e656248b63e64b1d1cce134ed9cd31ff40d18467c01b0bc11f',
    'Adafruit PowerBoost 1000 Basic.sch':'374791ee72acf98377f213186cab2ae64005c73896af35d3f43552039eb068cf',
}
BINDINGS={'BAT':('X2.2','VBAT'),'INPUT_GND':('X2.1','GND'),
          'OUT':('X1.2','5.0V'),'OUTPUT_GND':('X1.1','GND'),
          'TRIP':('R20.2','N$6')}
TERMINAL_SOURCE='sources/powerboost-terminals'
TERMINAL_FILES={
    '2444.html':'864d5a3227d249ccab1f3b02d749b3d1fab56c196b3f779193042d48b9703ef8',
    '2444-dimension.jpg':'dc31713da9cc1360727748d06752e70a156697b7643cccbeccf1dd9350d366ef',
}


def terminal_blocks(part,directory=HERE):
    """Check the selected clamp interfaces against retained seller records."""
    selected=part.get('wire_terminals',{})
    expected={'part':'Pololu2444 two-pin3.5mm side-entry screw terminal block','quantity':2,
              'positions':['X1','X2'],'source':'https://www.pololu.com/product/2444',
              'source_record':TERMINAL_SOURCE+'/index.json','wire_awg_range':[24,18],
              'published_current_a':10,'strip_target_mm':5,'wires_per_clamp':1,
              'nominal_body_mm':[7.96,6.8,8.4],'nominal_pin_diameter_mm':.8,
              'pin_length_mm':[3.4,4.0],
              'wire_groups':{'X2.1':'main','X2.2':'main','X1.1':'branches','X1.2':'branches'}}
    if (any(selected.get(key)!=value for key,value in expected.items())
            or type(selected.get('quantity')) is not int
            or type(selected.get('wires_per_clamp')) is not int
            or not all(selected.get(key) for key in ('current_basis','contact_resistance_basis','retention','fit_boundary'))):
        raise ValueError('Use two selected3.5mm clamps with one18AWG input or22AWG output lead per terminal')
    index={row['file']:row for row in json.loads((Path(directory)/TERMINAL_SOURCE/'index.json').read_text())}
    for name,digest in TERMINAL_FILES.items():
        raw=(Path(directory)/TERMINAL_SOURCE/name).read_bytes();row=index.get(name,{})
        if row.get('sha256')!=digest or row.get('bytes')!=len(raw) or hashlib.sha256(raw).hexdigest()!=digest:
            raise ValueError('PowerBoost terminal source hash mismatch: '+name)
    return selected


def terminals(part,directory=HERE):
    """Return the actual component-side coordinates used by the assembly plan."""
    if (part.get('board_revision')!=REVISION or part.get('source_record')!=SOURCE+'/index.json'
            or part.get('terminal_bindings')!={key:value[0] for key,value in BINDINGS.items()}):
        raise ValueError('Select the pinned PowerBoost and its complete terminal map')
    index={row['file']:row for row in json.loads((Path(directory)/SOURCE/'index.json').read_text())}
    sources={}
    for name,digest in FILES.items():
        raw=(Path(directory)/SOURCE/name).read_bytes();row=index.get(name,{})
        if (hashlib.sha256(raw).hexdigest()!=digest or row.get('sha256')!=digest
                or row.get('revision')!=REVISION or row.get('bytes')!=len(raw)):
            raise ValueError('PowerBoost manufacturer source hash mismatch: '+name)
        sources[Path(name).suffix]=raw
    schematic=extract(sources['.sch'])
    board=ET.fromstring(sources['.brd']).find('./drawing/board')
    elements={row.get('name'):row for row in board.findall('./elements/element')}
    libraries={row.get('name'):row for row in board.findall('./libraries/library')}
    nets={ref.get('element')+'.'+ref.get('pad'):net.get('name')
          for net in board.findall('./signals/signal') for ref in net.findall('contactref')}
    result={}
    for name,(physical,net) in BINDINGS.items():
        device,pin=physical.split('.')
        logical=next((key for key,pads in schematic[device]['pads'].items() if pads==[pin]),None)
        if logical is None or schematic[device]['nets'].get(logical)!=net or nets.get(physical)!=net:
            raise ValueError('PowerBoost schematic/board terminal mismatch: '+physical)
        element=elements[device]
        package=next(row for row in libraries[element.get('library')].findall('./packages/package')
                     if row.get('name')==element.get('package'))
        pad=next(row for tag in ('pad','smd') for row in package.findall(tag) if row.get('name')==pin)
        rotation=element.get('rot','R0')
        if rotation not in {'R0','R90','R180','R270'}:raise ValueError('Unreviewed PowerBoost pad rotation')
        angle=math.radians(float(rotation[1:]));x,y=(float(pad.get(axis)) for axis in ('x','y'))
        xy=[float(element.get('x'))+x*math.cos(angle)-y*math.sin(angle),
            float(element.get('y'))+x*math.sin(angle)+y*math.cos(angle)]
        result[name]={'pad':physical,'board_net':net,'board_xy_mm':xy,
                      'drill_mm':float(pad.get('drill')) if pad.tag=='pad' else None}
    return result
