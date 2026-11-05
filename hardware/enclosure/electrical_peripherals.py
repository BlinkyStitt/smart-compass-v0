"""Pinned GPS/LoRa source pads. Nominal coordinates do not qualify joints."""
import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET
from electrical_board import extract

HERE=Path(__file__).resolve().parent
BOARDS={'GPS': {'part':'Adafruit Ultimate GPS FeatherWing, 3V input', 'source': 'sources/gps-featherwing',
         'revision': '1b15a4f782c555903c0cfd7174d0616d2e128887',
         'origin_mm': [0, 0],
         'files': {'Adafruit Ultimate GPS FeatherWing.brd': '596f8011123a17f05256addc81aab901ea85b127cf3f73de2bf59c3f5e743894',
                   'Adafruit Ultimate GPS FeatherWing.sch': 'e963167e65d1e0a404e20a6e7bfd678c3e19ad0f3bd6d557e4e7eb7f52a7ffac'},
         'bindings': {'3V': ['JP4.9', '3V'],
                      'GND': ['JP4.7', 'GND'],
                      'RX': ['JP3.1', 'RX'],
                      'TX': ['JP3.2', 'TX'],
                      'PPS': ['JP1.3', '1PPS'],
                      'EN': ['JP1.4', 'ENABLE']}},
 'RADIO': {'part':'Adafruit 3072 RFM95W, VIN=3.3 V', 'source': 'sources/rfm-lora',
           'revision': '3ad6bed6e1b407afa7119ae548b5c2f1b107c6b1',
           'origin_mm': [0.254, 0],
           'files': {'Adafruit RFM+LoRa Breakout.brd': '7c1436eaafa74ed13a5871eb45f9e25420dd3151dfacd0a81cd1246867e30ca8',
                     'Adafruit RFM+LoRa Breakout.sch': '592011501f4b5f4f383d98c4215fda1fe5e63f814c71037611e34209229eb89a'},
           'bindings': {'VIN': ['JP3.1', 'VIN'],
                        'GND': ['JP3.2', 'GND'],
                        'G0': ['JP3.4', 'DIO0'],
                        'SCK': ['JP3.5', 'SCK_5V'],
                        'MISO': ['JP3.6', 'MISO_3V'],
                        'MOSI': ['JP3.7', 'MOSI_5V'],
                        'CS': ['JP3.8', 'CS_5V'],
                        'RST': ['JP3.9', 'RST_5V'],
                        'ANT': ['JP2.1', 'N$1']}}}


def terminals(module,part,directory=HERE):
    if module not in BOARDS:raise ValueError('Select the reviewed GPS or RADIO source')
    selected=BOARDS[module];expected={name:row[0] for name,row in selected['bindings'].items()}
    if (part.get('part')!=selected['part'] or part.get('board_revision')!=selected['revision'] or part.get('source_record')!=selected['source']+'/index.json'
            or part.get('terminal_bindings')!=expected):raise ValueError('Select the pinned '+module+' layout and its complete source pad map')
    index={row['file']:row for row in json.loads((Path(directory)/selected['source']/'index.json').read_text())};sources={}
    for filename,digest in selected['files'].items():
        raw=(Path(directory)/selected['source']/filename).read_bytes();row=index.get(filename,{})
        if hashlib.sha256(raw).hexdigest()!=digest or row.get('sha256')!=digest or row.get('bytes')!=len(raw) or row.get('revision')!=selected['revision']:
            raise ValueError(module+' manufacturer source hash mismatch: '+filename)
        sources[Path(filename).suffix]=raw
    schematic=extract(sources['.sch']);board=ET.fromstring(sources['.brd']).find('./drawing/board')
    elements={row.get('name'):row for row in board.findall('./elements/element')}
    libraries={row.get('name'):row for row in board.findall('./libraries/library')}
    nets={ref.get('element')+'.'+ref.get('pad'):net.get('name') for net in board.findall('./signals/signal') for ref in net.findall('contactref')}
    result={}
    for name,(physical,net) in selected['bindings'].items():
        header,pin=physical.split('.');logical=next((key for key,pads in schematic[header]['pads'].items() if pads==[pin]),None)
        if logical is None or schematic[header]['nets'].get(logical)!=net or nets.get(physical)!=net:
            raise ValueError(module+' schematic/board pad mismatch: '+physical)
        element=elements[header];package=next(row for row in libraries[element.get('library')].findall('./packages/package') if row.get('name')==element.get('package'))
        pad=next(row for row in package.findall('pad') if row.get('name')==pin);rotation=element.get('rot','R0')
        if rotation not in {'R0','R90','R180','R270'}:raise ValueError('Unreviewed '+module+' header rotation')
        a=math.radians(float(rotation[1:]));px,py=(float(pad.get(key)) for key in ('x','y'))
        cad=[float(element.get('x'))+px*math.cos(a)-py*math.sin(a),float(element.get('y'))+px*math.sin(a)+py*math.cos(a)]
        drill=float(pad.get('drill'))
        if not all(math.isfinite(v) for v in cad+[drill]) or drill<=0:raise ValueError('Invalid '+module+' source coordinates')
        xy=[v-origin for v,origin in zip(cad,selected['origin_mm'])]
        result[name]={'pad':physical,'board_net':net,'board_xy_mm':xy,'cad_xy_mm':cad,'drill_mm':drill,'view':'component-side; XY from outline lower-left'}
    return result
