"""Review the selected prototype circuit; keep physical acceptance separate.

This checks connection and documentation invariants. It does not simulate the
modules, certify their fault behavior, or turn a bench procedure into a result.
"""

import hashlib
import json
import math
from pathlib import Path

import electrical_imu
import electrical_boost
import electrical_latch
import capacitor_mount
import electrical_peripherals
import electrical_blackpill
import fibonacci_board
from battery_access import contact_source

HERE = Path(__file__).resolve().parent

# These are circuit connections, not success flags supplied by a JSON fixture.
# Changing the circuit requires reviewing this binding and its failure tests.
REQUIRED_CONNECTIONS = {
    'CONTACT_P': {'CONTACT_P.tail', 'F1.1'},
    'FUSED_CELL': {'F1.2', 'S1.1'},
    'A': {'S1.2', 'LATCH.VIN'},
    'A_DRAIN': {'S1.3', 'R_A.1'},
    'B': {'LATCH.VOUT', 'BOOST.X2.2', 'R_B.1', 'R_SENSE_TOP.1'},
    'BOOST_OUT': {'BOOST.X1.2', 'S1.4', 'R_BOOST.1'},
    'LOAD_5V': {'S1.5', 'R_LOAD.1', 'SPARKLE.X7.PWR'},
    'OUTPUT_OFF': {'S1.6'},
    'LATCH_OFF': {'BOOST.R20.2', 'LATCH.OFF', 'R_OFF.1'},
    'START': {'LATCH.A', 'START.1'},
    'SENSE': {'R_SENSE_TOP.2', 'R_SENSE_BOTTOM.1', 'BLACKPILL.PA4', 'C_SENSE.1'},
    'LED_DISTRIBUTION': {'SPARKLE.JP1.9', 'F_FIB.1', 'F_RING1.1', 'F_RING2.1', 'F_RING3.1'},
    'FIB_5V': {'F_FIB.2', 'FIBONACCI.5V', 'C_OUT.P', 'R_OUT.1'},
    'RING1_5V': {'F_RING1.2', 'RING1.5V'},
    'RING2_5V': {'F_RING2.2', 'RING2.5V'},
    'RING3_5V': {'F_RING3.2', 'RING3.5V'},
    'AUX_SOURCE': {'SPARKLE.JP3.2', 'F_AUX.1'},
    'AUX_3V3': {'F_AUX.2', 'BLACKPILL.3V3', 'GPS.3V', 'IMU.VIN', 'RADIO.VIN'},
    'LED_DATA1': {'SPARKLE.JP1.8', 'FIBONACCI.DIN'},
    'LED_DATA2': {'SPARKLE.JP1.5', 'RING1.DIN'},
    'LED_DATA3': {'SPARKLE.JP1.2', 'RING2.DIN'},
    'LED_DATA4': {'SPARKLE.JP3.6', 'RING3.DIN'},
    'SPARKLE_TX': {'SPARKLE.JP3.3', 'BLACKPILL.PA10'},
    'SPARKLE_RX': {'BLACKPILL.PB6', 'SPARKLE.JP3.4'},
    'GPS_TX': {'BLACKPILL.PA3', 'GPS.TX'},
    'GPS_RX': {'BLACKPILL.PA2', 'GPS.RX'},
    'SPI_CLOCK': {'IMU.SCL', 'RADIO.SCK', 'BLACKPILL.PA5'},
    'SPI_MOSI': {'IMU.SDA', 'BLACKPILL.PA7', 'RADIO.MOSI'},
    'SPI_MISO': {'RADIO.MISO', 'IMU.SDOAG', 'IMU.SDOM', 'BLACKPILL.PA6'},
    'IMU_AG_SELECT': {'BLACKPILL.PA8', 'IMU.CSAG'},
    'IMU_M_SELECT': {'IMU.CSM', 'BLACKPILL.PA9'},
    'RADIO_SELECT': {'BLACKPILL.PB0', 'RADIO.CS'},
    'RADIO_INTERRUPT': {'BLACKPILL.PB5', 'RADIO.G0'},
    'RADIO_RESET': {'RADIO.RST', 'BLACKPILL.PB12'},
    'IMU_AG_READY': {'IMU.INT1', 'BLACKPILL.PB10'},
    'IMU_M_READY': {'IMU.DRDY', 'BLACKPILL.PB1'},
    'GPS_PPS': {'GPS.PPS', 'BLACKPILL.PA0'},
    'GPS_ENABLE': {'BLACKPILL.PB7', 'GPS.EN'},
    'MODE': {'BLACKPILL.PB13','MODE.1'},
    'ACTION': {'BLACKPILL.PB14','ACTION.1'},
    'GND': {'CONTACT_N.tail', 'LATCH.GND', 'BOOST.X2.1', 'BOOST.X1.1', 'C_OUT.N',
            'R_A.2', 'R_B.2', 'R_OUT.2', 'R_BOOST.2', 'R_LOAD.2', 'R_OFF.2', 'START.3',
            'R_SENSE_BOTTOM.2', 'C_SENSE.2', 'MODE.3', 'ACTION.3', 'SPARKLE.X7.GND', 'BLACKPILL.GND',
            'GPS.GND', 'IMU.GND', 'RADIO.GND', 'FIBONACCI.GND',
            'RING1.GND', 'RING2.GND', 'RING3.GND'},
}
REQUIRED_BENCH_TESTS = frozenset({
    'startup_and_pulses', 'latch_and_rebound', 'off_and_replacement',
    'short_and_reversal', 'thermal', 'runtime', 'fit_and_worn_mass',
})
CRITICAL_PARTS = {
    'CELL': 'XTAR protected 21700 6000 mAh button-top',
    'SPARKLE': 'Adafruit Sparkle Motion, board revision D',
    'BLACKPILL': 'WeAct BlackPill V3.1 STM32F411CEU6, optional U3 flash not installed, 3.3 V input',
    'CONTACT_P': 'Mill-Max 0854-0-15-20-82-14-11-0',
    'CONTACT_N': 'Mill-Max 0854-0-15-20-82-14-11-0',
    'F1': 'Littelfuse 0251004.NRT1L, 4 A, axial',
    'S1': 'C&K 7201SYZQE, DPDT ON-ON, 5 A at 28 VDC',
    'S1_NUT': 'C&K 700201201, 1/4-40 UNS open hex mounting nut, nickel-plated brass',
    'S1_WASHER': 'C&K 700303202, internal-tooth lockwasher for 1/4-40 bushing, nickel-plated steel',
    'START': 'C&K PTS645SL70-2 LFS, normally-open SPST, 7 mm round actuator, through-hole',
    **{name: 'C&K PTS645SL70-2 LFS, normally-open SPST, 7 mm round actuator, through-hole'
       for name in ('MODE','ACTION')},
    'C_SENSE': 'KEMET C315C104K5R5TA, 100 nF 50 V +/-10%, X7R radial',
    'C_OUT': 'Panasonic EEUFR1A102, 1000 uF 10 V +/-20%, 10 x 16 mm body',
    'F_AUX': 'Littelfuse 0251.500NRT1L, 0.5 A, axial',
    'F_FIB': 'Littelfuse 0251002.NRT1L, 2 A, axial',
    **{name: 'Littelfuse 0251001.NRT1L, 1 A, axial'
       for name in ('F_RING1', 'F_RING2', 'F_RING3')},
    **{name: 'Vishay MRS16000C1001FCT00, 1 kohm 1% 0.4 W, axial'
       for name in ('R_A','R_B','R_OUT','R_BOOST','R_LOAD')},
    **{name: 'Vishay MRS16000C1003FCT00, 100 kohm 1% 0.4 W, axial'
       for name in ('R_OFF','R_SENSE_TOP','R_SENSE_BOTTOM')},
}


def finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def off_service_isolation(design):
    """Conservative OFF topology, with every module internally conductive.

    This does not certify a supplied switch, insulation or a faulted assembly.
    It separates ordinary contact isolation from an unknown reset/decay time.
    """
    graph = {}
    def join(pins):
        for a in pins:
            graph.setdefault(a, set()).update(set(pins)-{a})
    for pins in design.get('nets', {}).values():
        join(pins)
    for name in ('F1','F_FIB','F_RING1','F_RING2','F_RING3','F_AUX'):
        join([name+'.1',name+'.2'])
    for name in ('BOOST','LATCH','SPARKLE','BLACKPILL','GPS','IMU','RADIO',
                 'FIBONACCI','RING1','RING2','RING3'):
        join([pin for pin in graph if pin.startswith(name+'.')])
    for name in ('R_A','R_B','R_OUT','R_BOOST','R_LOAD','R_OFF','R_SENSE_TOP','R_SENSE_BOTTOM'):
        join([name+'.1',name+'.2'])
    for pins in design.get('switch_positions', {}).get('OFF', []):
        join(pins)
    reached, pending = set(), ['CONTACT_P.tail']
    while pending:
        pin=pending.pop()
        if pin not in reached:
            reached.add(pin)
            pending.extend(graph.get(pin, set())-reached)
    rails=('A','B','BOOST_OUT','LOAD_5V','FIB_5V')
    return {name: not bool(set(design.get('nets',{}).get(name,[])) & reached)
            for name in rails}


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
    try:
        contact = contact_source(directory)
        for name in ('CONTACT_P', 'CONTACT_N'):
            require(parts.get(name, {}).get('source') == contact['source'],
                    'contact-source:' + name, 'Use the retained wire-mount contact sheet.')
    except (ValueError, OSError) as error:
        require(False, 'contact-source', str(error))
    try:
        capacitor_targets=capacitor_mount.geometry(parts.get('C_OUT',{}),directory)
    except (ValueError,OSError) as error:
        capacitor_targets={}
        require(False,'capacitor-source-and-fit',str(error))
    terminals = parts.get('SPARKLE', {}).get('led_terminals', {})
    require(terminals.get('assembly') == 'Factory-installed JP1 nine-position 2.54mm screw terminal strip on Sparkle Motion Rev D'
            and terminals.get('wire_group') == 'branches'
            and terminals.get('signal_wire_group') == 'signals'
            and type(terminals.get('wires_per_clamp')) is int and terminals['wires_per_clamp'] == 1
            and terminals.get('wire_awg_range') == [20,26]
            and terminals.get('published_current_a') == 5
            and terminals.get('strip_target_mm') == 3.2
            and design.get('wiring', {}).get('stock_limits', {}).get('branches', {}).get('stock') == 'M22759/16-22'
            and design.get('wiring', {}).get('stock_limits', {}).get('signals', {}).get('stock') == 'M22759/18-26'
            and bool(terminals.get('source')) and bool(terminals.get('assembly_source'))
            and bool(terminals.get('current_basis')) and bool(terminals.get('retention')),
            'sparkle-led-terminations', 'Use the stock JP1 clamps with one supported22AWG power or26AWG data lead; retain strain relief and the unmeasured pulse/thermal boundary.')
    fibonacci_terminals = {}
    try:
        fibonacci_terminals = fibonacci_board.terminals(parts.get('FIBONACCI', {}), directory)
    except (ValueError, OSError) as error:
        require(False, 'fibonacci-terminal-binding', str(error))
    imu_terminals = {}
    try:
        imu_terminals = electrical_imu.terminals(parts.get('IMU', {}), directory)
    except (ValueError, OSError) as error:
        require(False, 'imu-terminal-binding', str(error))
    peripheral_terminals={}
    for module in ('GPS','RADIO','SPARKLE'):
        try:
            peripheral_terminals[module]=electrical_peripherals.terminals(module,parts.get(module,{}),directory)
        except (ValueError,OSError) as error:
            require(False,module.lower()+'-terminal-binding',str(error))
    blackpill_terminals={}
    try:
        blackpill_terminals=electrical_blackpill.terminals(parts.get('BLACKPILL',{}),directory)
    except (ValueError,OSError) as error:
        require(False,'blackpill-terminal-binding',str(error))
    boost_terminals = {}
    try:
        boost_terminals = electrical_boost.terminals(parts.get('BOOST', {}), directory)
        electrical_boost.terminal_blocks(parts.get('BOOST', {}), directory)
        require(design.get('wiring', {}).get('stock_limits', {}).get('main', {}).get('stock') == 'M22759/16-18'
                and design.get('wiring', {}).get('stock_limits', {}).get('branches', {}).get('stock') == 'M22759/16-22',
                'boost-wire-gauges', 'Use18AWG input and22AWG output wires in the selected clamps.')
    except (ValueError, OSError) as error:
        require(False, 'boost-terminal-binding', str(error))
    latch_terminals = {}
    try:
        latch_terminals = electrical_latch.terminals(parts.get('LATCH', {}), directory)
    except (ValueError, OSError) as error:
        require(False, 'latch-terminal-binding', str(error))
    require(parts.get('BOOST', {}).get('part') == 'Adafruit PowerBoost 1000 Basic, PID 2030'
            and parts.get('LATCH', {}).get('part') == 'Pololu 2808 Mini Pushbutton Power Switch LV',
            'module-selection', 'Connection checks apply only to the reviewed boost/latch pair.')
    require(design.get('switch_positions') == {
        'OFF': [['S1.2', 'S1.3'], ['S1.5', 'S1.6']],
        'ON': [['S1.2', 'S1.1'], ['S1.5', 'S1.4']],
    }, 'physical-off', 'OFF must disconnect both cell feed and boost-to-load output.')
    isolation = off_service_isolation(design)
    require(all(isolation.values()), 'off-contact-isolation',
            'Stored-charge rails must have no conducting OFF path to the positive cell contact.')
    rework = design.get('module_rework', {})
    require(rework.get('BOOST.remove') == ['R20'] and rework.get('BOOST.tap') == 'R20.2',
            'low-battery-inversion', 'Remove the LED resistor and use its T1-collector pad, not LBO or EN.')
    require(rework.get('BOOST.nominal_output_v') == 5.2,
            'regulated-output', 'Retain the stock nominal 5.2 V module setting for the reviewed barrel-feed path.')
    require(rework.get('BOOST.leave_open') == ['JP1.' + str(i) for i in range(1, 7)]
            and rework.get('LATCH.leave_open') == ['B', 'ON', 'CTRL'],
            'latch-controls', 'No continuously asserted ON, direct LBO-to-EN or unreviewed control source.')
    require(rework.get('BOOST.do_not_install') == ['B1', 'CN1']
            and rework.get('BOOST.install') == {'X1':'Pololu2444','X2':'Pololu2444'}
            and rework.get('SPARKLE.usb_pd_v') == 5,
            'external-power-paths', 'Keep unused connectors absent and USB service at 5 V.')
    require(isinstance(rework.get('BLACKPILL.do_not_install'),list) and 'U3' in rework['BLACKPILL.do_not_install'],
            'blackpill-flash-conflict', 'Optional V3.1 U3 flash shares the PA4 battery-sense input; select the unpopulated variant.')
    require(rework.get('BLACKPILL.do_not_install') == ['U3','P1','P2','P3'],
            'blackpill-bare-pads', 'Leave optional flash and all header parts absent; fit fixed wires to the selected PCB pads.')
    require(rework.get('RADIO.do_not_install') == ['JP1','JP2','JP3','X1']
            and rework.get('RADIO.leave_open') == ['JP1.1','JP1.2','JP1.3','JP1.4','JP1.5','JP3.3'],
            'radio-bare-pads', 'Use fixed source-pad wires and the internal wire antenna; leave unused headers and optional antenna connectors absent.')
    require(rework.get('SPARKLE.remove') == ['X7']
            and rework.get('SPARKLE.retain') == ['D2','PTC1']
            and rework.get('SPARKLE.leave_open') == ['X7.GNDBREAK'],
            'sparkle-input-termination', 'Remove only the barrel jack for the fixed X7 PWR/GND wires; retain D2/PTC1 and leave GNDBREAK open.')
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
    model = json.loads((Path(directory).parents[1] / 'site/electrical-inputs.json').read_text())
    defaults = model['defaults']
    require(operating.get('model_record') == 'site/electrical-inputs.json#defaults'
            and all(operating.get(plan) == defaults.get(key) for plan, key in (
                ('brightness', 'brightness'), ('non_led_budget_w', 'non_led_w'),
                ('efficiency_estimate', 'efficiency'), ('path_estimate_ohm', 'path_ohm'))),
            'planning-model-agreement', 'Bench planning and calculator defaults must use the same declared scenario.')
    cell_range = operating.get('cell_v', [])
    require(len(cell_range) == 2 and all(finite(v) for v in cell_range)
            and 2.2 <= cell_range[0] < cell_range[1] <= 4.2,
            'cell-operating-range', 'Declare a one-cell range within both module input ratings.')
    allocation = design.get('supply_allocation', {})
    current = allocation.get('external_3v3_peak_a', {})
    require(set(current) == {'BLACKPILL', 'GPS', 'IMU', 'RADIO'}
            and all(finite(v) and v > 0 for v in current.values())
            and sum(current.values()) <= 0.5
            and allocation.get('external_3v3_published_peak_a') == 0.5,
            'peripheral-current-budget', 'Declare all external loads within the published 500 mA peak supply.')
    require(bool(allocation.get('basis')) and bool(design.get('signal_basis', {}).get('sources')),
            'signal-and-budget-evidence', 'Retain pin-map sources and the estimation/test boundary.')
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
        'off_positive_contact_isolation': isolation,
        'imu_source_terminals': imu_terminals,
        'fibonacci_source_terminals': fibonacci_terminals,
        'peripheral_source_terminals':peripheral_terminals,
        'blackpill_source_terminals':blackpill_terminals,
        'boost_source_terminals': boost_terminals,
        'latch_source_terminals': latch_terminals,
        'bulk_capacitor_targets':capacitor_targets,
        'historical_recovery': design.get('historical_recovery'),
    }
