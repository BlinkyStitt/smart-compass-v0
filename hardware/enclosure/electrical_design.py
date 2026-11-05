"""Review the selected prototype circuit; keep physical acceptance separate.

This checks connection and documentation invariants. It does not simulate the
modules, certify their fault behavior, or turn a bench procedure into a result.
"""

import hashlib
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent

# These are circuit connections, not success flags supplied by a JSON fixture.
# Changing the circuit requires reviewing this binding and its failure tests.
REQUIRED_CONNECTIONS = {
    'CONTACT_P': {'CONTACT_P.tail', 'F1.1'},
    'FUSED_CELL': {'F1.2', 'S1.1'},
    'A': {'S1.2', 'LATCH.VIN'},
    'A_DRAIN': {'S1.3', 'R_A.1'},
    'B': {'LATCH.VOUT', 'BOOST.JP1.1', 'R_B.1', 'R_SENSE_TOP.1'},
    'BOOST_OUT': {'BOOST.JP1.6', 'S1.4'},
    'LOAD_5V': {'S1.5', 'C_OUT.P', 'R_OUT.1', 'SPARKLE.X7.PWR'},
    'OUTPUT_OFF': {'S1.6'},
    'LATCH_OFF': {'BOOST.R20.2', 'LATCH.OFF', 'R_OFF.1'},
    'START': {'LATCH.A', 'START.1'},
    'SENSE': {'R_SENSE_TOP.2', 'R_SENSE_BOTTOM.1', 'BLACKPILL.PA4'},
    'LED_DISTRIBUTION': {'SPARKLE.JP1.9', 'F_FIB.1', 'F_RING1.1', 'F_RING2.1', 'F_RING3.1'},
    'FIB_5V': {'F_FIB.2', 'FIBONACCI.5V'},
    'RING1_5V': {'F_RING1.2', 'RING1.5V'},
    'RING2_5V': {'F_RING2.2', 'RING2.5V'},
    'RING3_5V': {'F_RING3.2', 'RING3.5V'},
    'AUX_SOURCE': {'SPARKLE.JP3.2', 'F_AUX.1'},
    'AUX_3V3': {'F_AUX.2', 'BLACKPILL.3V3', 'GPS.3V', 'IMU.3V3', 'RADIO.VIN'},
    'LED_DATA1': {'SPARKLE.JP1.8', 'FIBONACCI.DIN'},
    'LED_DATA2': {'SPARKLE.JP1.5', 'RING1.DIN'},
    'LED_DATA3': {'SPARKLE.JP1.2', 'RING2.DIN'},
    'LED_DATA4': {'SPARKLE.JP3.6', 'RING3.DIN'},
    'GND': {'CONTACT_N.tail', 'LATCH.GND', 'BOOST.JP1.2', 'C_OUT.N',
            'R_A.2', 'R_B.2', 'R_OUT.2', 'R_OFF.2', 'START.2',
            'R_SENSE_BOTTOM.2', 'SPARKLE.X7.GND', 'BLACKPILL.GND',
            'GPS.GND', 'IMU.GND', 'RADIO.GND', 'FIBONACCI.GND',
            'RING1.GND', 'RING2.GND', 'RING3.GND'},
}
REQUIRED_BENCH_TESTS = frozenset({
    'startup_and_pulses', 'latch_and_rebound', 'off_and_replacement',
    'short_and_reversal', 'thermal', 'runtime', 'fit_and_worn_mass',
})
CRITICAL_PARTS = {
    'CELL': 'XTAR protected INR21700-50E 5000 mAh',
    'CONTACT_P': 'Mill-Max 0850-0-15-20-83-14-11-0',
    'CONTACT_N': 'Mill-Max 0850-0-15-20-83-14-11-0',
    'F1': 'Littelfuse 0459004.UR, 4 A',
    'S1': 'C&K 7201SYZQE, DPDT ON-ON, 5 A at 28 VDC',
    'C_OUT': 'Panasonic EEUFR1A102, 1000 uF 10 V +/-20%, 10 x 16 mm body',
    'F_AUX': 'Littelfuse 0459.500UR, 0.5 A',
    **{name: 'Littelfuse 0459001.UR, 1 A'
       for name in ('F_FIB', 'F_RING1', 'F_RING2', 'F_RING3')},
}


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def assess(design, directory=HERE):
    """Return actual design errors separately from unexecuted physical tests."""
    if design.get('schema_version') != 1:
        raise ValueError('Unsupported module-prototype design schema')
    failures = []

    def require(condition, name, detail):
        if not condition:
            failures.append({'id': name, 'detail': detail})

    require(bool(design.get('revision')) and bool(design.get('acceptance')),
            'review-identity', 'Name the revision and the digital/physical proof boundary.')
    nets = design.get('nets', {})
    pins = [pin for members in nets.values() for pin in members]
    require(len(pins) == len(set(pins)), 'duplicate-pin', 'A terminal cannot belong to two nets.')
    for name, expected in REQUIRED_CONNECTIONS.items():
        require(expected <= set(nets.get(name, [])), 'net:' + name,
                'Missing or incorrect connection at ' + name)
    # Undocumented extra connections can bypass OFF, protection or branch fuses.
    require(set(nets) == set(REQUIRED_CONNECTIONS)
            and all(set(nets.get(name, [])) == expected
                    for name, expected in REQUIRED_CONNECTIONS.items()),
            'unreviewed-connections', 'Additional, missing or bypass connections need a circuit review.')
    owners = {pin.split('.')[0] for pin in pins} | {'CELL'}
    parts = design.get('parts', {})
    require(owners <= parts.keys(), 'bom-coverage', 'Every connected component needs a BOM entry.')
    for name, part in parts.items():
        require(bool(part.get('part')) and bool(part.get('source')), 'bom:' + name,
                'Missing exact part/source for ' + name)
        require('unresolved' not in part.get('part', '').lower(), 'part-selection:' + name,
                'An unresolved component is not a selected assembly part.')
    for name, selected in CRITICAL_PARTS.items():
        require(parts.get(name, {}).get('part') == selected, 'selected-part:' + name,
                'Changed protection, cell or capacitor selection requires a circuit review.')
    require(parts.get('BOOST', {}).get('part') == 'Adafruit PowerBoost 1000 Basic, PID 2030'
            and parts.get('LATCH', {}).get('part') == 'Pololu 2808 Mini Pushbutton Power Switch LV',
            'module-selection', 'Connection checks apply only to the reviewed boost/latch pair.')
    require(design.get('switch_positions') == {
        'OFF': [['S1.2', 'S1.3'], ['S1.5', 'S1.6']],
        'ON': [['S1.2', 'S1.1'], ['S1.5', 'S1.4']],
    }, 'physical-off', 'OFF must disconnect both cell feed and boost-to-load output.')
    rework = design.get('module_rework', {})
    require(rework.get('BOOST.remove') == ['R20'] and rework.get('BOOST.tap') == 'R20.2',
            'low-battery-inversion', 'Remove the LED resistor and use its T1-collector pad, not LBO or EN.')
    require(rework.get('BOOST.nominal_output_v') == 5.2,
            'regulated-output', 'Retain the stock nominal 5.2 V module setting for the reviewed barrel-feed path.')
    require(rework.get('BOOST.leave_open') == ['JP1.3', 'JP1.4']
            and rework.get('LATCH.leave_open') == ['B', 'ON', 'CTRL'],
            'latch-controls', 'No continuously asserted ON, direct LBO-to-EN or unreviewed control source.')
    require(rework.get('BOOST.do_not_install') == ['B1', 'CN1', 'X1', 'X2']
            and rework.get('SPARKLE.usb_pd_v') == 5,
            'external-power-paths', 'Keep unused connectors absent and USB service at 5 V.')
    record = design.get('source_record', {})
    source_path = Path(record.get('path', ''))
    if source_path.is_absolute() or '..' in source_path.parts:
        raise ValueError('Unsafe module source path')
    raw = (Path(directory) / source_path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == record.get('sha256'),
            'module-source-hash', 'Pinned source connectivity changed.')
    source = json.loads(raw)
    require(source.get('revision') == record.get('upstream_commit'),
            'module-source-revision', 'Pin the same reviewed upstream revision.')
    require({'T1.C', 'R20.2'} <= set(source['nets']['N$6'])
            and {'U1.LBO', 'T1.B', 'JP1.4'} <= set(source['nets']['LBO'])
            and {'U1.EN', 'R13.2', 'JP1.3'} <= set(source['nets']['ENABLE'])
            and source['parts']['R13']['value'] == '200K',
            'module-source-topology', 'Low-battery inversion/pin map differs from the reviewed board.')
    operating = design.get('operating_plan', {})
    for name in ('brightness', 'non_led_budget_w', 'efficiency_estimate',
                 'path_estimate_ohm', 'battery_current_review_a'):
        require(finite(operating.get(name)) and operating[name] > 0,
                'operating:' + name, 'Declare a finite positive planning value.')
    require(finite(operating.get('brightness')) and 0 < operating['brightness'] <= 1
            and finite(operating.get('efficiency_estimate'))
            and 0 < operating['efficiency_estimate'] <= 1,
            'operating-range', 'Brightness and efficiency must be fractions in (0,1].')
    cell_range = operating.get('cell_v', [])
    require(len(cell_range) == 2 and all(finite(v) for v in cell_range)
            and 2.2 <= cell_range[0] < cell_range[1] <= 4.2,
            'cell-operating-range', 'Declare a one-cell range within both module input ratings.')
    for item in design.get('open_design_items', []):
        failures.append({'id': item['id'], 'detail': item['detail']})
    qualification = design.get('physical_qualification', {})
    require(set(qualification) == REQUIRED_BENCH_TESTS, 'qualification-coverage',
            'Do not omit a required physical procedure.')
    physical = {}
    for name, test in qualification.items():
        require(bool(test.get('procedure')), 'procedure:' + name, 'Describe the physical test.')
        # Physical result ingestion is deliberately not implemented by a flag.
        # It needs revision/conditions/measurements and a separate acceptance review.
        require(test.get('status') == 'unmeasured' and test.get('results') == [],
                'unverified-physical-claim:' + name,
                'No physical evidence is installed; keep this outcome unmeasured.')
        physical[name] = {'status': 'unmeasured', 'procedure': test.get('procedure')}
    require(design.get('service', {}).get('off_dwell_s') is None,
            'unverified-dwell', 'A proposed wait is not a qualified discharge/reset time.')
    return {
        'revision': design['revision'],
        'scope': 'digital-prototype-design-review',
        'digital_design_pass': not failures,
        'physical_qualification': physical,
        'physical_acceptance': 'unmeasured',
        'safe_to_wear_claim': False,
        'failures': failures,
        'operating_plan': operating,
        'service': design.get('service', {}),
        'historical_recovery': design.get('historical_recovery'),
    }
