"""Nominal rear-wire endpoints for the original 166 mm Fibonacci256.

The retained maker photographs establish the pad labels and nominal locations.
They do not establish supplied tolerances, assembled fit or physical acceptance.
This local frame must be placed with the board; it is not the pixel-map frame.
"""

import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = 'sources/fibonacci256-166'
FILES = {
    'index.json': '41fa4a3dc352fdbc8612fc431a112708e3bfc454ce8226666780c2e6c3a78128',
    'nominal-terminals.json': '68440330f57a2a8bb3762576c20dc66daaf5fa73079b4e55a52badd05c70b6d4',
    'fnqNrNl.png': '5610a1bf1e1d0542bd8cd25df445e93cc1483e36bc89dfe2d09d1629f18409d1',
    'ISnaLBD.png': '4fc3ddf4059876bbd9bf60b3599c2393d83e7513fd4009ab2c23759ebe5d950a',
}
BINDINGS = {'5V': 'IN.5V', 'DIN': 'IN.DI', 'GND': 'IN.GND'}


def terminals(part, directory=HERE):
    """Return front-view nominal XY in the documented input-at-bottom frame.

    Do not infer installed rotation from map_rotation_deg. That parameter belongs
    to the separately registered optical pattern. Do not use the output DO pad
    as an alias for DI. All three output pads remain unused in this design.
    """
    if (part.get('part') != 'Original Evil Genius Labs Fibonacci256'
            or part.get('board_revision') != 'v0.1-166mm'
            or part.get('source_record') != SOURCE + '/index.json'
            or part.get('terminal_bindings') != BINDINGS):
        raise ValueError('Select the original 166mm v0.1 board and its input pad map')
    sources = {}
    for name, digest in FILES.items():
        raw = (Path(directory) / SOURCE / name).read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('Fibonacci source hash mismatch: ' + name)
        sources[name] = raw
    index = json.loads(sources['index.json'])
    for row in index['photos']:
        raw = sources[row['file']]
        if row['bytes'] != len(raw) or row['sha256'] != FILES[row['file']]:
            raise ValueError('Fibonacci photograph index mismatch: ' + row['file'])
    record = json.loads(sources['nominal-terminals.json'])
    return {
        name: {
            'pad': pad,
            'board_net': record['pads'][pad]['net'],
            'board_xy_mm': record['pads'][pad]['front_xy_mm'],
            'coordinate_kind': record['coordinate_kind'],
            'frame': record['frame'],
            'physical_acceptance': record['physical_acceptance'],
        }
        for name, pad in BINDINGS.items()
    }
