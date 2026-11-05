"""Source-bound component-side latch pads and selected wire clamps."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
SOURCE='sources/latch-2808'
FILES={
 'pololu-2808.step':'9e3718142701cf853fd2b2be9e70452a1d4ef040858a043e921c965aeca33707',
 'pololu-2808-pinout.jpg':'e7d8ff74be20e5cac0f734d9c3780224d812232379ca8bedf3d481a17a17ddec',
 'pololu-2808-dimensions.pdf':'979a919222b689527ba594015811845a753c71a5a14d5a52ba62a4192eb1ddbc',
 'camblock-plus-catalogue-15a.pdf':'65aa67b64623952918f0ee75f9af6ac8fdcc90fd7bfd035ff3c9084c4fe5f1d3',
}
# Maker component-side pinout, origin at the nominal PCB lower-left corner.
# A is the LOWER right control pad. B is above it; do not exchange them.
BINDINGS={'VIN':[1.27,16.51],'VOUT':[13.97,16.51],
          'GND':[1.27,8.89],'A':[13.97,3.81],'OFF':[1.27,3.81]}


def terminals(part,directory=HERE):
    if (part.get('board_revision')!='psw03a' or part.get('source_record')!=SOURCE+'/index.json'
            or part.get('terminal_bindings')!=BINDINGS):
        raise ValueError('Select psw03a and the maker component-side pad map; START uses lower A, not upper B')
    index={row['file']:row for row in json.loads((Path(directory)/SOURCE/'index.json').read_text())}
    for name,digest in FILES.items():
        raw=(Path(directory)/SOURCE/name).read_bytes();row=index.get(name,{})
        if row.get('sha256')!=digest or row.get('bytes')!=len(raw) or hashlib.sha256(raw).hexdigest()!=digest:
            raise ValueError('Latch manufacturer source hash mismatch: '+name)
    selected=part.get('wire_terminals',{})
    expected={'part':'CamdenBoss CTBP2054/4, four-position2.54mm rising-clamp PCB terminal block',
              'quantity':2,'mount_side':'underside','wire_awg_range':[26,18],
              'published_ul_current_a':6,'published_iec_current_a':8,
              'maximum_contact_resistance_ohm':.020,'nominal_body_mm':[10.62,6.2,8.5],
              'nominal_pin_section_mm':[.8,.5],'pin_length_mm':[3.2,3.8],
              'published_torque_nm':.1,'wires_per_clamp':1,'strip_target_mm':4.5,
              'connections':{'VIN.upper':'18AWG','VOUT.upper':'18AWG','VIN.lower_GND':'26AWG'}}
    if (any(selected.get(key)!=value for key,value in expected.items())
            or any(type(selected.get(key)) is not int for key in ('quantity','wires_per_clamp'))
            or not all(selected.get(key) for key in ('strip_basis','unused','source','limits'))):
        raise ValueError('Use two selected underside four-position clamps with one supported lead per used clamp')
    return {name:{'board_xy_mm':xy,'view':'component-side','drill_diameter_mm':1.02,
                  'drill_basis':'Nominal diameter. Published+/-0.1mm applies to LOCATION; no diameter tolerance supplied.'}
            for name,xy in BINDINGS.items()}
