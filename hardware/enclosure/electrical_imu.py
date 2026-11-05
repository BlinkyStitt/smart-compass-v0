"""Bind the selected classic IMU to its actual Rev A header pads.

Board coordinates identify routing endpoints. They do not prove soldered-wire
fit, strain relief, assembled dimensions, or electrical performance.
"""

import hashlib
import json
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from electrical_board import extract

HERE = Path(__file__).resolve().parent
SOURCE = 'sources/lsm9ds1-classic'
FILES = {
    'Adafruit LSM9DS1 Rev A.brd': 'ae642906f132b2325c28e44a443ca20c16864d0d7d9a5bc5ef471942dbf59e7d',
    'Adafruit LSM9DS1 Rev A.sch': '0f874bd4ad47097c65cc6447382cf7d90cdcc704e3cc88f26ec4e604c50429d2',
}
# Logical assembly terminal: (physical header pad, manufacturer net).
BINDINGS = {
    'VIN': ('JP4.9', 'VIN'), 'GND': ('JP4.7', 'GND'),
    'SCL': ('JP4.6', 'SCL_5V'), 'SDA': ('JP4.5', 'SDA_5V'),
    'SDOAG': ('JP4.2', 'SDO_AG'), 'SDOM': ('JP4.1', 'SDO_M'),
    'CSAG': ('JP4.4', 'CS_AG_5V'), 'CSM': ('JP4.3', 'CS_M_5V'),
    'INT1': ('JP2.3', 'INT1_AG'), 'DRDY': ('JP2.4', 'DRDY_M'),
}


def terminals(part, directory=HERE):
    """Return source-derived component-side XY, net, and drill for every lead."""
    expected = {name: pad for name, (pad, _) in BINDINGS.items()}
    if (part.get('board_revision') != 'A'
            or part.get('source_record') != SOURCE + '/index.json'
            or part.get('terminal_bindings') != expected):
        raise ValueError('Select classic IMU Rev A and its complete reviewed header map')
    sources = {}
    index = {row['file']: row for row in json.loads((Path(directory) / SOURCE / 'index.json').read_text())}
    for name, digest in FILES.items():
        raw = (Path(directory) / SOURCE / name).read_bytes()
        row = index.get(name, {})
        if (hashlib.sha256(raw).hexdigest() != digest or row.get('sha256') != digest
                or row.get('bytes') != len(raw)
                or row.get('revision') != '9f6db79a66ae599aa410a2a14b161e26216e8bd4'):
            raise ValueError('IMU manufacturer source hash mismatch: ' + name)
        sources[Path(name).suffix] = raw
    schematic = extract(sources['.sch'])
    board = ET.fromstring(sources['.brd']).find('./drawing/board')
    elements = {row.get('name'): row for row in board.findall('./elements/element')}
    libraries = {row.get('name'): row for row in board.findall('./libraries/library')}
    nets = {ref.get('element') + '.' + ref.get('pad'): net.get('name')
            for net in board.findall('./signals/signal') for ref in net.findall('contactref')}
    result = {}
    for name, (physical, net) in BINDINGS.items():
        header, pin = physical.split('.')
        logical = 'A.' + pin
        if (schematic[header]['pads'][logical] != [pin]
                or schematic[header]['nets'][logical] != net or nets[physical] != net):
            raise ValueError('IMU schematic/board terminal mismatch: ' + physical)
        element = elements[header]
        package = next(row for row in libraries[element.get('library')].findall('./packages/package')
                       if row.get('name') == element.get('package'))
        pad = next(row for row in package.findall('pad') if row.get('name') == pin)
        # These selected top-side headers use R180 and R0, with no mirroring.
        rotation = element.get('rot', 'R0')
        if rotation not in {'R0', 'R180'}:
            raise ValueError('Unreviewed IMU header rotation: ' + rotation)
        sign = -1 if rotation == 'R180' else 1
        xy = [float(element.get(axis)) + sign * float(pad.get(axis)) for axis in ('x', 'y')]
        drill = float(pad.get('drill'))
        if not all(math.isfinite(value) for value in xy + [drill]) or drill <= 0:
            raise ValueError('Invalid IMU source coordinates: ' + physical)
        result[name] = {'pad': physical, 'board_net': net, 'board_xy_mm': xy, 'drill_mm': drill}
    return result
