"""Conditional temperature envelopes, not an enclosure or circuit simulator.

For a passive linear thermal network, nonnegative impulse responses give
T_i <= max(T_boundary, T_initial) + sum_j Z_ij * P_j. Z must bound each
source-to-observer DC transfer over the actual assembly/environment. P must
bound instantaneous local heat, including faults and stored-energy release.
This deliberately takes no credit for pulse duration, optical escape or cooling
between swaps. Unknown coefficients, powers and premises cannot pass.
"""

import math


def number(value, name, *, nonnegative=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or (nonnegative and value < 0)):
        raise ValueError(name + ' must be finite' + (' and nonnegative' if nonnegative else ''))
    return value


def temperature_envelope(powers, transfer, limits, boundary_c, initial_c):
    """Evaluate an all-time upper envelope under the module's stated premises.

    Each observer needs every source coefficient, even when local power is
    zero: a missing cross term is not evidence of thermal isolation. The initial
    bound covers ALL thermal nodes, including unobserved storage in the shell.
    """
    if not powers or not limits or set(transfer) != set(limits):
        raise ValueError('Every thermal observer needs a limit and a transfer row')
    missing = []
    for name, value in (('boundary_c', boundary_c), ('initial_c', initial_c)):
        if value is None:
            missing.append(name)
        else:
            number(value, name)
    for source, power in powers.items():
        if power is None:
            missing.append(source + '.heat_upper_w')
        else:
            number(power, source + '.heat_upper_w', nonnegative=True)
    base = None if boundary_c is None or initial_c is None else max(boundary_c, initial_c)
    rows = {}
    for observer, coefficients in transfer.items():
        if set(coefficients) != set(powers):
            raise ValueError('Every observer needs every heat source: ' + observer)
        absent, terms = list(missing), []
        for source, coefficient in coefficients.items():
            if coefficient is None:
                absent.append(observer + '.' + source + '.k_per_w')
            else:
                number(coefficient, observer + '.' + source + '.k_per_w', nonnegative=True)
                if powers[source] is not None:
                    terms.append(number(coefficient * powers[source], 'temperature rise', nonnegative=True))
        try:
            temperature = None if absent else number(base + math.fsum(terms), 'temperature upper bound')
        except OverflowError as exc:
            raise ValueError('Temperature upper bound overflow') from exc
        limit = limits[observer]
        if limit is None:
            absent.append(observer + '.limit_c')
        else:
            number(limit, observer + '.limit_c')
        rows[observer] = {
            'upper_c': temperature,
            'margin_c': None if temperature is None or limit is None else limit - temperature,
            'pass': not absent and temperature <= limit,
            'missing': absent,
        }
    return {'observers': rows, 'pass': all(row['pass'] for row in rows.values())}


def heat_ownership(candidate, harness):
    """Partition physical losses; transported converter power is not local heat.

    Harness segments already include some devices. Co-own those assets in ONE
    heat source, so U1/F1/S1/contact losses cannot also be counted as devices.
    Ownership does not establish a resistance, current or heat bound.
    """
    pins = [pin for members in candidate['nets'].values() for pin in members]
    pins += candidate['open_pins']
    if len(pins) != len(set(pins)):
        raise ValueError('Duplicate component pin in thermal input netlist')
    parts = {pin.split('.')[0] for pin in pins} - {'loads'}
    parts.update(harness['load_ports'])
    parts.add('cell')
    groups = {f'segment:{name}': [f'segment:{name}'] for name in harness['segments']}
    shared = {
        'F1': 'f1', 'S1': 's1', 'U1': 'efuse_b_copper',
        'positive_contact': 'positive_contact', 'negative_contact': 'negative_contact',
        'BatterySense': 'sense_joints',
    }
    for part, segment in shared.items():
        if part not in parts or segment not in harness['segments']:
            raise ValueError('Missing combined device/harness heat owner: ' + part)
        groups['segment:' + segment].append('part:' + part)
    for part in sorted(parts - shared.keys()):
        groups['part:' + part] = ['part:' + part]
    assets = [asset for group in groups.values() for asset in group]
    expected = {'part:' + part for part in parts} | {'segment:' + key for key in harness['segments']}
    if len(assets) != len(set(assets)) or set(assets) != expected:
        raise ValueError('Heat ownership must cover every physical asset exactly once')
    return groups


def reference_heat(spec):
    """Reference power arithmetic only; no reference value is an assembly bound."""
    output = number(spec['candidate']['reference_output_w'], 'reference output', nonnegative=True)
    efficiency = number(spec['candidate']['reference_efficiency'], 'reference efficiency')
    if not 0 < efficiency <= 1:
        raise ValueError('Reference efficiency must be in (0,1]')
    voltage = number(spec['limits']['boost_min_input_v'], 'reference input voltage')
    resistance = number(spec['limits']['efuse_ron_max_ohm_at_3a'], 'reference eFuse R', nonnegative=True)
    if voltage <= 0:
        raise ValueError('Reference input voltage must be positive')
    current = output / efficiency / voltage
    return {
        'output_assigned_to_heat_w': output,
        'boost_conversion_heat_w': output * (1 / efficiency - 1),
        'input_power_w': output / efficiency,
        'reference_boost_input_a': current,
        'efuse_conduction_sensitivity_w': current**2 * resistance,
        'scope': '6.25 W/85% reference, not instantaneous maxima or a full heat budget. '
                 'No optical cooling credit. eFuse 45 mOhm is specified at 3 A; using it '
                 'at the reference current is a sensitivity calculation. Excludes cell, '
                 'contacts, harness, control, added bleeders and other unbounded losses.',
    }


def thermal_study(definition, spec, candidate, harness):
    """Enforce complete per-design/state coverage without inventing missing data."""
    if definition['schema_version'] != 1:
        raise ValueError('Unsupported thermal schema')
    states = {
        'normal', 'pwm_radio_peak', 'startup', 'absent_cell', 'depleted_cell',
        'reversed_cell', 'contact_bounce', 'voltage_rebound', 'rapid_replacement',
        'charged_capacitors', 'overload', 'short', 'cleared_fault', 'usb_service',
    }
    if set(definition['states']) != states or set(definition['designs']) != {'wide', 'narrow'}:
        raise ValueError('All required circuit states and both thermal designs are required')
    ownership = heat_ownership(candidate, harness)
    sources = sorted(ownership)
    # Observe every component and conductor hot spot, plus both touch surfaces.
    # Combined heat owners still need separate member temperature limits.
    observers = sorted({asset for group in ownership.values() for asset in group}
                       | {'front_surface', 'rear_skin_surface'})
    limits = dict.fromkeys(observers)
    if definition['efuse_operating_max_c'] != 125:
        raise ValueError('TPS25947 operating junction maximum must retain the sourced 125 C')
    limits['part:U1'] = definition['efuse_operating_max_c']
    results = {}
    for design, assembly in definition['designs'].items():
        if set(assembly['states']) != states:
            raise ValueError('Missing/extra thermal state: ' + design)
        transfer = assembly['transfer_upper_k_per_w']
        if transfer is None:
            transfer = {observer: dict.fromkeys(sources) for observer in observers}
        local_limits = dict(limits)
        for name, value in assembly['temperature_limits_c'].items():
            if name not in observers:
                raise ValueError('Unknown temperature observer: ' + name)
            if value is not None:
                number(value, name + '.limit_c')
            if local_limits[name] is not None and (value is None or value > local_limits[name]):
                raise ValueError('Cannot relax a sourced operating temperature limit')
            local_limits[name] = value
        cases = {}
        for state, bounds in assembly['states'].items():
            powers = bounds['heat_upper_w']
            if powers is None:
                powers = dict.fromkeys(sources)
            if set(powers) != set(sources):
                raise ValueError('State must include every local heat source: ' + state)
            envelope = temperature_envelope(powers, transfer, local_limits,
                                            assembly['boundary_upper_c'], bounds['initial_upper_c'])
            premises = bounds['premises']
            if set(premises) != {'passive_linear_transfer', 'instantaneous_heat_bounds',
                                 'complete_circuit_state', 'temperature_range_covered'}:
                raise ValueError('Missing thermal/circuit applicability premise: ' + state)
            if any(value is not None and type(value) is not bool for value in premises.values()):
                raise ValueError('Thermal premises must be boolean or unknown')
            unresolved = [name for name, value in premises.items() if value is not True]
            rows = envelope['observers']
            # Keep the report bounded; do not print thousands of identical null terms.
            cases[state] = {
                'bounded_temperature_upper_c': {name: row['upper_c'] for name, row in sorted(rows.items())
                                                if row['upper_c'] is not None},
                'bounded_temperature_margin_c': {name: row['margin_c'] for name, row in sorted(rows.items())
                                                 if row['margin_c'] is not None},
                'unbounded_temperature_count': sum(row['upper_c'] is None for row in rows.values()),
                'bounded_heat_upper_w': {name: value for name, value in sorted(powers.items()) if value is not None},
                'unbounded_heat_count': sum(value is None for value in powers.values()),
                'missing_boundary': assembly['boundary_upper_c'] is None,
                'missing_initial_temperature': bounds['initial_upper_c'] is None,
                'unresolved_premises': unresolved,
                'pass': envelope['pass'] and not unresolved,
            }
        results[design] = {
            'missing_transfer_coefficients': sum(value is None for row in transfer.values() for value in row.values()),
            'missing_temperature_limits': sorted(name for name, value in local_limits.items() if value is None),
            'cases': cases,
        }
    return {
        'revision': definition['revision'], 'defect_id': definition['defect_id'],
        'conditional_pass': all(case['pass'] for design in results.values() for case in design['cases'].values()),
        'heat_ownership': dict(sorted(ownership.items())),
        'reference': reference_heat(spec), 'designs': results,
        'remaining_evidence': definition['remaining_evidence'],
    }
