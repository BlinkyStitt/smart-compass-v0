"""Extract pinned manufacturer connectivity and audit the Sparkle power ports.

Connectivity proves neither diode leakage nor converter/transient behavior. The
forward-path graph is deliberately limited to the two input feeds and PTC; data
pins, common ground and reverse leakage remain separate qualification work.
"""

import argparse
from collections import deque
import hashlib
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
SOURCES = HERE / 'sources' / 'sparkle-motion'
COMMIT = '7a45f900d6ce0c1d60d67a9efbbba6dbd55ef31a'
FILES = {
    'A': ('Adafruit Sparkle Motion WLED Friend.sch',
          'afd13602a71467809ec14da7e0e05a57195fea23a556b6a3562d81a8059683ac'),
    'D': ('Adafruit Sparkle Motion WLED Friend_Rev D.sch',
          '63245b5f0b24baffc181f28b3735ccd80d124e612f0d36b782db7d4a76d69c35'),
}


def extract(data):
    """Retain every packaged part and its connected logical pins/physical pads."""
    schematic = ET.fromstring(data).find('./drawing/schematic')
    if schematic is None or schematic.find('./modules/module') is not None:
        raise ValueError('Expected a flat Eagle schematic')
    libraries = {row.get('name'): row for row in schematic.findall('./libraries/library')}
    parts = {}
    for row in schematic.findall('./parts/part'):
        library = libraries[row.get('library')]
        deviceset = next(ds for ds in library.findall('./devicesets/deviceset')
                         if ds.get('name') == row.get('deviceset'))
        device = next(dev for dev in deviceset.findall('./devices/device')
                      if dev.get('name') == row.get('device'))
        if device.get('package') is None:
            continue  # Supply symbols, frames and fiducial-less virtual gates.
        pads = {c.get('gate') + '.' + c.get('pin'): c.get('pad').split()
                for c in device.findall('./connects/connect')}
        name = row.get('name')
        if name in parts:
            raise ValueError('Duplicate board part: ' + name)
        parts[name] = {'value': row.get('value', row.get('deviceset')),
                       'deviceset': row.get('deviceset'), 'package': device.get('package'),
                       'pads': dict(sorted(pads.items())), 'nets': {}}
    for net in schematic.findall('./sheets/sheet/nets/net'):
        for ref in net.findall('./segment/pinref'):
            name = ref.get('part')
            if name not in parts:
                continue
            pin = ref.get('gate') + '.' + ref.get('pin')
            part = parts[name]
            if pin not in part['pads']:
                raise ValueError('Connected physical pin has no pad: ' + name + '.' + pin)
            if pin in part['nets'] and part['nets'][pin] != net.get('name'):
                raise ValueError('Board pin belongs to multiple nets: ' + name + '.' + pin)
            part['nets'][pin] = net.get('name')
    for part in parts.values():
        part['nets'] = dict(sorted(part['nets'].items()))
    return dict(sorted(parts.items()))


def from_sources(directory):
    boards = {}
    for revision, (filename, digest) in FILES.items():
        data = (directory / filename).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise ValueError('Manufacturer source hash mismatch: ' + filename)
        boards[revision] = {'source_file': filename, 'sha256': digest, 'parts': extract(data)}
    return {'schema_version': 1, 'upstream_commit': COMMIT,
            'repository': 'https://github.com/adafruit/Adafruit-Sparkle-Motion-PCB',
            'license': 'CC-BY-SA-3.0; see license.txt and upstream-README.md',
            'boards': boards}


def forward_path(edges, start, end):
    """Return a shortest possible forward-conduction route, or None."""
    queue = deque([(start, [])])
    visited = {start}
    while queue:
        node, route = queue.popleft()
        if node == end:
            return route
        for name, a, b in edges:
            if a == node and b not in visited:
                visited.add(b)
                queue.append((b, route + [name]))
    return None


def board_study(record, harness):
    """Bind generic harness ports to real pads in both documented board revisions."""
    if (record['schema_version'] != 1 or record['upstream_commit'] != COMMIT
            or set(record['boards']) != set(FILES)):
        raise ValueError('Unreviewed Sparkle schematic revision')
    binding = harness['sparkle_board_ports']
    expected = {
        'supply': ['X7', 'G$1.PWR'], 'return': ['X7', 'G$1.GND'],
        'peripheral_supply': ['JP3', 'G$1.2'], 'peripheral_return': ['JP3', 'G$1.1'],
    }
    if binding != expected:
        raise ValueError('Sparkle harness must use the barrel input and separate 3.3 V header')
    result = {}
    for revision, board in record['boards'].items():
        filename, digest = FILES[revision]
        if board['source_file'] != filename or board['sha256'] != digest:
            raise ValueError('Sparkle source provenance disagrees')
        parts = board['parts']

        def net(part, pin):
            return parts[part]['nets']['G$1.' + pin]

        for part, value in {'D1': 'PMEG3050', 'D2': 'PMEG3050',
                            'Q1': 'AONR21307', 'PTC1': '2920L500/30GR',
                            'U$10': 'TPS54202', 'U2': 'NCP718ASN500T1G'}.items():
            if parts[part]['value'] != value:
                raise ValueError('Unreviewed Sparkle power component: ' + part)
        usb, barrel, rail = net('X5', 'VBUS'), net('X7', 'PWR'), net('U$10', 'VIN')
        if (net('Q1', 'S') != usb or net('Q1', 'D') != net('D1', 'A')
                or net('D1', 'C') != net('D2', 'C') or net('D2', 'A') != barrel
                or net('PTC1', '2') != net('D1', 'C') or net('PTC1', '1') != rail
                or net('U2', 'IN') != rail):
            raise ValueError('Sparkle input feed topology changed')
        edges = [('Q1:on', usb, net('Q1', 'D')),
                 ('D1:forward', net('D1', 'A'), net('D1', 'C')),
                 ('D2:forward', barrel, net('D2', 'C')),
                 ('PTC1', net('PTC1', '2'), rail), ('PTC1', rail, net('PTC1', '2'))]
        terminals = [parts['JP1']['nets']['A.' + pin] for pin in ('3', '6', '9')]
        if any(n != rail for n in terminals):
            raise ValueError('Sparkle LED power terminals must retain common input rail')
        if (net('JP3', '2') != '3.3V' or net('JP3', '1') != 'GND'
                or net('X7', 'GND') != 'GND' or net('X5', 'GND') != 'GND'):
            raise ValueError('Sparkle external supply/return voltages disagree')
        if net('X5', 'D+') != net('IC1', 'D+') or net('X5', 'D-') != net('IC1', 'D-'):
            raise ValueError('USB data no longer connects directly to the serial bridge')
        if harness['paths']['sparkle']['supply_ends'][1] != 'sparkle.SUPPLY':
            raise ValueError('Unbound Sparkle harness input')
        result[revision] = {
            'barrel_to_board': forward_path(edges, barrel, rail),
            'usb_to_led_power_terminals': forward_path(edges, usb, rail),
            'usb_to_selected_barrel_feed': forward_path(edges, usb, barrel),
            'ports': {name: {'part': part, 'pin': pin, 'net': parts[part]['nets'][pin],
                             'pads': parts[part]['pads'][pin]} for name, (part, pin) in binding.items()},
            'usb_data_direct_to_ch343': True,
            'shared_usb_and_load_ground': True,
            'buck_minimum_input_v': 4.5,
            'source': 'https://www.ti.com/lit/ds/symlink/tps54202.pdf (SLVSD26C, section 5.3)',
        }
    return {'defect_id': harness['defect_id'], 'qualified': False, 'boards': result,
            'scope': 'Forward topology with Q1 ON only. No zero-leakage, voltage-drop, '
                     'USB/signal isolation, cold-start, reversal, thermal or assembly claim.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['extract', 'check'])
    parser.add_argument('--source-directory', required=True, type=Path)
    parser.add_argument('--fetch', action='store_true', help='download and hash-check the pinned manufacturer sources')
    args = parser.parse_args()
    if args.fetch:
        args.source_directory.mkdir(parents=True, exist_ok=True)
        for filename, digest in FILES.values():
            url = ('https://raw.githubusercontent.com/adafruit/Adafruit-Sparkle-Motion-PCB/'
                   + COMMIT + '/' + quote(filename))
            with urlopen(url, timeout=30) as response:
                data = response.read()
            if hashlib.sha256(data).hexdigest() != digest:
                raise ValueError('Downloaded manufacturer source hash mismatch: ' + filename)
            (args.source_directory / filename).write_bytes(data)
    output = SOURCES / 'connectivity.json'
    record = from_sources(args.source_directory)
    if args.command == 'extract':
        output.write_text(json.dumps(record, indent=2) + '\n')
        print('SPARKLE CONNECTIVITY EXTRACTED: pinned revisions A and D')
    elif json.loads(output.read_text()) != record:
        raise ValueError('Stored Sparkle connectivity does not match pinned schematics')
    else:
        print('SPARKLE SOURCE CHECK PASS: both source hashes and complete extracts match')


if __name__ == '__main__':
    main()
