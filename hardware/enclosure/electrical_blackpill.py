"""Selected V3.1 header pads from original manufacturer CAD and schematic facts."""
import hashlib
import json
from pathlib import Path
from urllib.parse import quote

HERE=Path(__file__).resolve().parent
SOURCE='sources/blackpill-v31'
REVISION='6a7f7d434a9d6361f91590d4cdd16b4a70ce7513'
FACTS_SHA256='f412530ba182d36083a792e03667292f4576e4128875d5b734321f23f772b571'
PART='WeAct BlackPill V3.1 STM32F411CEU6, optional U3 flash not installed, 3.3 V input'
UPSTREAM={'mechanical':'e713074f681a8ee3d1c54ae5419c8165c01b16e5abb54afae9252521651cb594',
          'schematic':'4ba1ee95b1d49f6a2dd3441f6910bc1b29be45d0431638368d56bfb59e08e565',
          'release_notes':'5ec3e20b6a6d11f5db7590d3b2fcb0b4a6682d62b0d6bc1666a7d5e4747b48db'}
PATHS={'mechanical':'Hardware/MiniF4x1Cx_V31_3D.step',
       'schematic':'Hardware/MiniF4x1Cx_V31 SchDoc.pdf','release_notes':'Hardware/README.md'}
SIZES={'mechanical':5095700,'schematic':190443,'release_notes':1820}
BINDINGS={'3V3':('P1.3','3.3V'),'GND':('P1.2','GND'),
          'PA0':('P1.15','PA0'),'PA10':('P2.7','PA10'),'PA2':('P1.13','PA2'),
          'PA3':('P1.12','PA3'),'PA4':('P1.11','PA4'),'PA5':('P1.10','PA5'),
          'PA6':('P1.9','PA6'),'PA7':('P1.8','PA7'),'PA8':('P2.5','PA8'),
          'PA9':('P2.6','PA9'),'PB0':('P1.7','PB0'),'PB1':('P1.6','PB1'),
          'PB10':('P1.4','PB10'),'PB12':('P2.1','PB12'),'PB13':('P2.2','PB13'),
          'PB14':('P2.3','PB14'),'PB5':('P2.13','PB5'),'PB6':('P2.14','PB6'),
          'PB7':('P2.15','PB7')}


def source_facts(directory=HERE):
    folder=Path(directory)/SOURCE;raw=(folder/'ports.json').read_bytes();index=json.loads((folder/'index.json').read_text())
    if not isinstance(index,dict):raise ValueError('BlackPill source index must be an object')
    records=index.get('files',[])
    if (index.get('schema_version')!=1 or index.get('revision')!=REVISION or not isinstance(records,list)
            or len(records)!=1 or not isinstance(records[0],dict)
            or records[0].get('file')!='ports.json' or records[0].get('bytes')!=len(raw)
            or records[0].get('sha256')!=FACTS_SHA256 or hashlib.sha256(raw).hexdigest()!=FACTS_SHA256):
        raise ValueError('BlackPill original-source coordinate facts differ')
    sources=index.get('sources',{})
    base='https://raw.githubusercontent.com/WeActStudio/WeActStudio.MiniSTM32F4x1/'+REVISION+'/'
    if (not isinstance(sources,dict) or set(sources)!=set(UPSTREAM)
            or any(not isinstance(sources[name],dict) or sources[name].get('sha256')!=digest
                   or sources[name].get('revision')!=REVISION or sources[name].get('upstream_path')!=PATHS[name]
                   or sources[name].get('url')!=base+quote(PATHS[name]) or sources[name].get('bytes')!=SIZES[name]
                   for name,digest in UPSTREAM.items())):
        raise ValueError('BlackPill pinned manufacturer source identities differ')
    facts=json.loads(raw)
    if (facts.get('revision')!=REVISION or facts.get('coordinate_source_sha256')!=UPSTREAM['mechanical']
            or facts.get('schematic_source_sha256')!=UPSTREAM['schematic']):
        raise ValueError('BlackPill coordinate and schematic revisions disagree')
    return facts


def terminals(part,directory=HERE):
    if (part.get('part')!=PART or part.get('board_revision')!=REVISION
            or part.get('source_record')!=SOURCE+'/index.json'
            or part.get('source_sha256')!=UPSTREAM['schematic']
            or part.get('terminal_bindings')!={name:row[0] for name,row in BINDINGS.items()}):
        raise ValueError('Select the original V3.1 BlackPill and its complete manufacturer header map')
    facts=source_facts(directory);result={}
    for name,(pad,net) in BINDINGS.items():
        header,pin=pad.split('.');number=int(pin);row=facts['headers'][header]
        if row['nets'][number-1]!=net:raise ValueError('BlackPill schematic/header pin differs: '+pad)
        x=round(facts['first_x_mm']+facts['pitch_x_mm']*(number-1),6)
        result[name]={'pad':pad,'board_net':net,'board_xy_mm':[x,row['y_mm']],
                      'drill_mm':facts['nominal_cad_hole_diameter_mm'],'view':facts['view'],
                      'conditions':'Nominal original CAD hole, not a finished-hole minimum; supplied fit and joints remain unmeasured.'}
    return result
