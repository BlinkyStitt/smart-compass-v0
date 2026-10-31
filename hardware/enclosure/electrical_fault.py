"""Conservative fault-current requirements, not a cell or fuse qualification.

The battery bound replaces the fuse with a short. Capacitor bounds describe
isolated passive RC discharges; active conversion/backfeed needs another model.
Unknown resistance minima are conservatively zero, never catalogue maxima.
"""

import math


def nonnegative(value, name):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0):
        raise ValueError(name + ' must be finite and nonnegative')
    return value


def prospective_current(voltage_max_v, resistance_min_ohm):
    """Passive DC source bound; R excludes the fuse and includes both conductors.

    Missing individual minima contribute zero, which is conservative for a
    passive resistance. A positive, independently supported subtotal suffices;
    an entirely zero/unknown loop cannot bound a nonzero source's current.
    """
    voltage = nonnegative(voltage_max_v, 'source voltage')
    if not resistance_min_ohm:
        raise ValueError('Fault loop must name its series elements')
    minimum = math.fsum(nonnegative(r, name) for name, r in resistance_min_ohm.items()
                        if r is not None)
    if voltage == 0:
        return 0.0
    return nonnegative(voltage / minimum, 'calculated current') if minimum > 0 else None


def capacitor_pulse(capacitance_max_f, voltage_max_v, resistance_min_ohm):
    """RC discharge peak, stored energy and integral(i**2 dt) to infinity.

    E=CV²/2 and integral(i² dt)=E/R. Resistance includes ESR and the entire
    discharge loop. This has no fuse-clearing credit, and is not an RLC model.
    """
    values = (capacitance_max_f, voltage_max_v, resistance_min_ohm)
    for name, value in zip(('capacitance', 'voltage', 'resistance'), values):
        if value is not None:
            nonnegative(value, name)
    energy = (None if capacitance_max_f is None or voltage_max_v is None else
              capacitance_max_f * voltage_max_v**2 / 2)
    if energy is not None:
        nonnegative(energy, 'calculated energy')
    if energy == 0:
        return {'peak_a': 0.0, 'i2t_a2s': 0.0, 'stored_j': 0.0}
    peak = (None if voltage_max_v is None or not resistance_min_ohm else
            voltage_max_v / resistance_min_ohm)
    i2t = None if energy is None or not resistance_min_ohm else energy / resistance_min_ohm
    for value in (peak, i2t):
        if value is not None:
            nonnegative(value, 'calculated pulse bound')
    return {'peak_a': peak, 'i2t_a2s': i2t, 'stored_j': energy}


def combine_pulses(pulses):
    """Worst overlap: Minkowski gives ||sum i||₂ <= sum ||i||₂.

    Summing I²t alone drops cross terms. Sum absolute peaks and squared sums
    of L2 norms instead. Do not infer direction, timing or disjoint paths.
    """
    if not pulses:
        raise ValueError('At least one source pulse is required')
    for pulse in pulses:
        for field in ('peak_a', 'i2t_a2s'):
            if pulse[field] is not None:
                nonnegative(pulse[field], field)
    result = {
        'peak_a': None if any(p['peak_a'] is None for p in pulses)
        else math.fsum(p['peak_a'] for p in pulses),
        'i2t_a2s': None if any(p['i2t_a2s'] is None for p in pulses)
        else math.fsum(math.sqrt(p['i2t_a2s']) for p in pulses)**2,
    }
    for value in result.values():
        if value is not None:
            nonnegative(value, 'calculated overlap bound')
    return result


def withstand(pulse, limits):
    """Require BOTH peak and total I²t withstand; unknown is never a pass."""
    if set(limits) != {'peak_a', 'i2t_a2s'}:
        raise ValueError('Withstand needs peak current and total I2t')
    for value in (*limits.values(), *pulse.values()):
        if value is not None:
            nonnegative(value, 'withstand')
    checks = {}
    for field in ('peak_a', 'i2t_a2s'):
        actual, allowed = pulse[field], limits[field]
        checks[field] = None if actual is None or allowed is None else actual <= allowed
    return {'checks': checks, 'pass': all(value is True for value in checks.values())}


def fault_study(spec, harness, revision):
    """Audit F1 backup faults in the existing fixed-contact harness topology.

    The six locations are a deliberately bounded subset of the complete state
    model. A downstream short assumes U1 failed conducting: its programmed
    current limit cannot be used to size the independent F1 backup.
    """
    if revision['schema_version'] != 2:
        raise ValueError('Unsupported fault coordination schema')
    fuse = revision['fuse']
    if fuse['part'] != spec['candidate']['F1'] or fuse['part'] != 'Littelfuse 0459004.UR':
        raise ValueError('Fault model does not match F1')
    for field, source in (('interrupt_a', 'fuse_interrupt_a'), ('rating_a', 'fuse_rating_a')):
        if fuse[field] != spec['limits'][source]:
            raise ValueError('F1 rating disagrees with electrical definition')
    for field in ('interrupt_a', 'rating_a', 'voltage_max_v'):
        if nonnegative(fuse[field], field) == 0:
            raise ValueError('F1 ratings must be positive')
    if fuse['voltage_max_v'] != 125:
        raise ValueError('F1 must retain its sourced 125 VDC rating')
    terminal_voltage = fuse['terminal_voltage_max_v']
    if terminal_voltage is not None:
        nonnegative(terminal_voltage, 'F1 terminal voltage')
    voltage = nonnegative(spec['limits']['cell_charge_upper_v_dated_spec'], 'cell upper voltage')
    segments = harness['segments']
    paths = harness['paths']
    # Prefix endpoints and return endpoints are verified below. F1 is retained
    # for path ownership, but its resistance is omitted for prospective current.
    definitions = {
        'before_f1': (['positive_contact'], ['negative_contact']),
        'after_f1': (['positive_contact', 'f1'], ['negative_contact']),
        'switch_input': (paths['boost_input']['supply'][:3], ['cell_return', 'negative_contact']),
        'a_to_ground': (paths['boost_input']['supply'][:6], ['cell_return', 'negative_contact']),
        'controller_input': (paths['controller']['supply'], paths['controller']['return']),
        'b_with_u1_failed_short': (paths['boost_input']['supply'], paths['boost_input']['return']),
    }
    endpoints = {
        'before_f1': ('F1.1', 'negative_contact'),
        'after_f1': ('F1.2', 'negative_contact'),
        'switch_input': ('S1.ON', 'PROTECTION_GND'),
        'a_to_ground': ('U1.IN', 'PROTECTION_GND'),
        'controller_input': ('U2.VIN', 'U2.GND'),
        'b_with_u1_failed_short': ('U4.VIN', 'U4.GND.PORT'),
    }
    owners = {'cell_internal'} | {s for supply, ret in definitions.values() for s in supply + ret}
    owners.remove('f1')
    if set(revision['withstand']) != owners:
        raise ValueError('Fault withstand ledger must cover every non-fuse loop element once')
    if set(revision['designs']) != set(harness['designs']):
        raise ValueError('Fault audit must cover both harness designs')
    if set(revision['capacitor_sources']) != {'A', 'B', 'C', 'FIVE_V'}:
        raise ValueError('Fault audit must retain all charged rails')
    cap_pulses = {rail: capacitor_pulse(**row) for rail, row in revision['capacitor_sources'].items()}
    cap_total = combine_pulses(list(cap_pulses.values()))
    clearing = fuse['total_clearing_max_s']
    if clearing is not None:
        nonnegative(clearing, 'total clearing time')
        if clearing == 0:
            raise ValueError('Total clearing time must be positive')
    conditions = revision['conditions']
    required_conditions = {'passive_dc_source_bound', 'fuse_dc_conditions_covered',
                           'clearing_bound_covers_fault_range', 'capacitors_isolated_passive_rc',
                           'no_external_or_inductive_sources', 'withstand_conditions_covered',
                           'fuse_terminal_stress_covered'}
    if set(conditions) != required_conditions or any(
            value is not None and not isinstance(value, bool) for value in conditions.values()):
        raise ValueError('Fault study requires explicit model conditions')
    conditions_pass = all(value is True for value in conditions.values())
    results = {}
    for design, minima in revision['designs'].items():
        if set(minima) != owners:
            raise ValueError('Resistance minima must name both conductors and every series element')
        for name, value in minima.items():
            if value is not None:
                nonnegative(value, name)
        results[design] = {}
        for location, (supply, ret) in definitions.items():
            def follow(names, start, end):
                node = start
                if len(names) != len(set(names)):
                    raise ValueError('Duplicate fault-loop element')
                for name in names:
                    a, b = segments[name]['ends']
                    if a != node:
                        raise ValueError('Disconnected fault loop: ' + name)
                    node = b
                if node != end:
                    raise ValueError('Fault loop ends at the wrong terminal')
            high, low = endpoints[location]
            follow(supply, 'CELL.P', high)
            follow(ret, low, 'CELL.N')
            members = ['cell_internal'] + [s for s in supply + ret if s != 'f1']
            if len(members) != len(set(members)):
                raise ValueError('Duplicate fault-loop ownership')
            has_fuse = 'f1' in supply
            current = prospective_current(voltage, {name: minima[name] for name in members})
            for switch in ('ON', 'OFF'):
                connected = switch == 'ON' or 's1' not in supply
                peak = current if connected else 0.0
                # OFF removes only this battery path, never charged capacitors.
                i2t = (0.0 if not connected else None if current is None or clearing is None
                       or not has_fuse else current**2 * clearing)
                if i2t is not None:
                    nonnegative(i2t, 'calculated battery I2t')
                battery = {'peak_a': peak, 'i2t_a2s': i2t}
                combined = combine_pulses([battery, cap_total])
                # A battery-only comparison is insufficient: charged rails may
                # feed F1 in either direction. Until their paths are bounded,
                # take the sum of absolute source peaks with no cancellation or
                # OFF-state isolation credit. The new premise must establish
                # that these pulse bounds also cover every path THROUGH F1.
                # Source charge voltage alone does not bound recovery voltage
                # across an opening fuse (opposed rails, switching and ringing).
                fuse_checks = {
                    'battery_path_protected': not connected or has_fuse,
                    'peak_a': None if combined['peak_a'] is None else
                    combined['peak_a'] <= fuse['interrupt_a'],
                    'voltage_v': None if terminal_voltage is None else
                    terminal_voltage <= fuse['voltage_max_v'],
                }
                interruption = (False if any(value is False for value in fuse_checks.values())
                                else None if any(value is None for value in fuse_checks.values())
                                else True)
                checks = {name: withstand(combined, revision['withstand'][name]) for name in members}
                results[design][location + ':' + switch] = {
                    'fault_bridge': [high, low], 'battery_connected': connected,
                    'battery_loop': members, 'f1_in_battery_path': has_fuse,
                    'battery': battery, 'all_sources_overlap': combined,
                    'f1_prospective_peak_upper_a': combined['peak_a'],
                    'f1_terminal_voltage_upper_v': terminal_voltage,
                    'f1_rating_checks': fuse_checks,
                    'f1_rating_comparison': interruption,
                    'withstand': checks,
                    'conditional_pass': conditions_pass and interruption is True
                    and all(row['pass'] for row in checks.values()),
                }
    return {
        'revision': revision['revision'], 'defect_id': revision['defect_id'],
        'qualified': False, 'scope': revision['scope'],
        'source_voltage_v': voltage,
        'required_nonfuse_loop_min_ohm_for_interrupt_rating': voltage / fuse['interrupt_a'],
        'capacitor_pulses': cap_pulses, 'capacitor_overlap': cap_total,
        'conditions': conditions, 'designs': results,
        'remaining_evidence': revision['remaining_evidence'],
    }
