"""Reproduce electrical candidate counterexamples; reject an unqualified path.

This is a corner audit, not a transient simulator. A passing unit test proves the
calculation/rejection behavior, never the safety of the proposed assembly.
"""

import argparse
import itertools
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def finite(value, name, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(name + ' must be a finite number')
    if not math.isfinite(value) or (positive and value <= 0):
        raise ValueError(name + ' must be finite' + (' and positive' if positive else ''))
    return value


def interval(values, name):
    if not isinstance(values, list) or len(values) != 2:
        raise ValueError(name + ' needs two ordered finite limits')
    low, high = (finite(value, name) for value in values)
    if low > high:
        raise ValueError(name + ' limits are reversed')
    return low, high


def divider_thresholds(top, bottom, tolerance, thresholds, pin_current):
    """Supply voltage at a comparator edge; positive pin current sinks to GND.

    KCL: V_supply = V_pin * (1 + R_top/R_bottom) + I_pin * R_top.
    Exhaust all independent resistance, comparator and leakage corners.
    """
    finite(top, 'top resistance', positive=True)
    finite(bottom, 'bottom resistance', positive=True)
    finite(tolerance, 'resistor tolerance')
    if not 0 <= tolerance < 1:
        raise ValueError('resistor tolerance must be in [0,1)')
    voltages = interval(thresholds, 'comparator voltage')
    currents = interval(pin_current, 'pin current')
    results = []
    for v, rt, rb, current in itertools.product(
        voltages, (top * (1-tolerance), top * (1+tolerance)),
        (bottom * (1-tolerance), bottom * (1+tolerance)), currents,
    ):
        results.append(v * (1 + rt/rb) + current * rt)
    return [min(results), max(results)]


def loaded_voltage(supply_v, resistance_ohm, input_power_w):
    """High-voltage equilibrium of a constant-power load behind series R.

    V_load = V_supply - R * P/V_load. No transient or stability claim.
    None means there is no positive real equilibrium.
    """
    finite(supply_v, 'supply voltage', positive=True)
    for name, value in [('resistance', resistance_ohm), ('input power', input_power_w)]:
        finite(value, name)
        if value < 0:
            raise ValueError(name + ' must be nonnegative')
    discriminant = supply_v**2 - 4 * resistance_ohm * input_power_w
    if discriminant < 0:
        return None
    return (supply_v + math.sqrt(discriminant))/2


def discharge_time(initial_v, target_v, resistance_ohm, capacitance_f, incoming_a):
    """Exact RC solution with constant worst-case current INTO a disconnected rail.

    None means the target is unreachable: leakage maintains too high a voltage.
    No assumption of reverse isolation, capacitor tolerance or zero leakage.
    """
    for name, value in [('initial voltage', initial_v), ('target voltage', target_v),
                        ('resistance', resistance_ohm), ('capacitance', capacitance_f)]:
        finite(value, name, positive=True)
    finite(incoming_a, 'incoming current')
    if incoming_a < 0:
        raise ValueError('incoming current must be nonnegative')
    if initial_v <= target_v:
        return 0.0
    equilibrium = incoming_a * resistance_ohm
    if equilibrium >= target_v:
        return None
    return resistance_ohm * capacitance_f * math.log(
        (initial_v - equilibrium) / (target_v - equilibrium))


def control_study(spec, study):
    """Evaluate a concrete alternative and reject its unsupported boundaries.

    This calculation deliberately does not select the new buffer: its transition
    specification fails even using typical, rather than maximum, capacitance.
    """
    if study.get('schema_version') != 1:
        raise ValueError('Unsupported control-study schema')
    c, d, limits = study['control_candidate'], study['discharge_candidate'], spec['limits']
    r = c['resistors_ohm']
    leak = interval(c['buffer_output_leakage_a'], 'buffer leakage')
    uvlo = divider_thresholds(r['R_UV_TOP'], r['R_UV_BOTTOM'], c['divider_tolerance'],
                             limits['efuse_uvlo_falling_v'],
                             [leak[0] + limits['efuse_en_leakage_a'][0],
                              leak[1] + limits['efuse_en_leakage_a'][1]])
    kill = divider_thresholds(r['R_KILL_TOP'], r['R_KILL_BOTTOM'], c['divider_tolerance'],
                             limits['kill_falling_v'], limits['kill_leakage_a'])
    power = spec['candidate']['reference_output_w'] / spec['candidate']['reference_efficiency']
    voltage = loaded_voltage(uvlo[0], c['post_sense_path_resistance_ohm_study'], power)
    # Charge a typical 5 pF input between 30% and 70% of C at C=3.3 V.
    # Include the MAXIMUM controller pullup as an optimistic rise-time aid.
    supply = 3.3
    tau = r['R_EN_PULLUP'] * c['buffer_input_capacitance_typ_f']
    final_v = supply + r['R_EN_PULLUP'] * limits['controller_en_pullup_a_at_zero_v'][1]
    transition = tau * math.log((final_v - .3 * supply) / (final_v - .7 * supply)) / (.4 * supply)
    worst_r = d['resistance_ohm'] * (1 + d['resistance_tolerance']
              + d['temperature_coefficient_per_k'] * d['maximum_temperature_distance_k']
              + d['resistance_aging_allowance'])
    discharge = {}
    for rail, values in d['rails'].items():
        seconds = discharge_time(values['initial_v'], d['target_v_study'], worst_r,
                                 values['nominal_f'] * (1 + d['capacitance_tolerance_study']),
                                 d['incoming_leakage_a_study'])
        discharge[rail] = {'decay_s': seconds,
                           'decay_plus_lockout_s': None if seconds is None else seconds + d['lockout_s']}
    # Budget requirements, not fabricated guarantees for missing board data.
    added_drain = limits['cell_nominal_v'] / r['R_C_BLEED']
    return {'status': 'rejected-control-revision',
            'conditional_uvlo_c_v': uvlo, 'conditional_kill_c_v': kill,
            'conditional_boost_input_v': voltage,
            'static_headroom_pass': voltage is not None and voltage >= limits['boost_min_input_v'],
            'static_cutoff_order_pass': kill[0] > uvlo[1],
            'optimistic_buffer_input_transition_s_per_v': transition,
            'buffer_transition_limit_s_per_v': c['buffer_input_transition_max_s_per_v'],
            'buffer_transition_pass': transition <= c['buffer_input_transition_max_s_per_v'],
            'conditional_discharge': discharge,
            'additional_c_bleeder_a_at_nominal_c': added_drain,
            'additional_c_bleeder_wh_per_day_at_nominal_c': added_drain * limits['cell_nominal_v'] * 24,
            'off_dwell_qualified': False,
            'reason': 'Buffer dynamic limit and complete capacitance/leakage/USB bounds remain unsupported. '
                      'The static repair and added bleeders cannot qualify the power path.'}


def review(spec):
    if spec.get('schema_version') != 1:
        raise ValueError('Unsupported electrical-review schema')
    p, limits = spec['candidate'], spec['limits']
    for name, value in limits.items():
        if isinstance(value, list):
            interval(value, name)
        else:
            finite(value, name, positive=True)
    resistors = p['resistors_ohm']
    for name, value in resistors.items():
        finite(value, name, positive=True)
    for name, value in p['capacitors_nominal_f'].items():
        finite(value, name, positive=True)
    efficiency = finite(p['reference_efficiency'], 'reference efficiency', positive=True)
    if efficiency > 1:
        raise ValueError('reference efficiency must be at most 1')
    output_w = finite(p['reference_output_w'], 'reference output power', positive=True)
    tolerance = p['threshold_resistor_tolerance']
    kill = divider_thresholds(resistors['R_KILL_TOP'], resistors['R_KILL_BOTTOM'],
                              tolerance, limits['kill_falling_v'], limits['kill_leakage_a'])
    # Conditional reconstruction of the proposed calculation: the controller
    # datasheet specifies this pull-up current at EN=0 V, not at the UVLO edge.
    # Do not quietly promote that condition into a guaranteed 1.1 V bound.
    pullup = limits['controller_en_pullup_a_at_zero_v']
    leakage = limits['efuse_en_leakage_a']
    en_current = [leakage[0]-pullup[1], leakage[1]-pullup[0]]
    uvlo = divider_thresholds(resistors['R_EN_TOP'], resistors['R_EN_BOTTOM'],
                              tolerance, limits['efuse_uvlo_falling_v'], en_current)
    nominal_i = limits['efuse_current_formula_a_ohm']/resistors['R_ILM']
    current_error = limits['efuse_current_relative_error']
    if not 0 <= current_error < 1:
        raise ValueError('efuse current relative error must be in [0,1)')
    currents = [nominal_i*(1-current_error)/(1+tolerance),
                nominal_i*(1+current_error)/(1-tolerance)]
    reference_input_w = output_w/efficiency
    boost_v = loaded_voltage(uvlo[0], limits['efuse_ron_max_ohm_at_3a'], reference_input_w)
    # Omits ALL other positive drops and assumes C=A. Even this optimistic
    # reconstruction cannot certify the stated 2.9 V minimum during blanking.
    result = {
        'revision': spec['revision'],
        'status': 'rejected-before-compartment-freeze',
        'calculated': {
            'kill_threshold_c_v': kill,
            'conditional_backup_uvlo_c_v': uvlo,
            'programmed_current_a': currents,
            'conditional_boost_input_at_uvlo_v': boost_v,
            'reference_input_w': reference_input_w,
            'reference_runtime_h': limits['cell_nominal_v']*limits['cell_capacity_ah']/reference_input_w,
            'kill_startup_blanking_s': limits['kill_blanking_s'],
        },
        'failures': [],
    }
    failures = result['failures']
    if boost_v is None or boost_v < limits['boost_min_input_v']:
        failures.append({
            'id': 'startup-boost-headroom',
            'detail': f'Conditional backup corner gives {boost_v!r} V at boost input; '
                      f'requires >= {limits["boost_min_input_v"]} V. KILL can be blanked for '
                      f'{limits["kill_blanking_s"][1]} s. Other path drops are omitted.',
        })
    if limits['efuse_unpowered_pg_highest_specified_low_v'] >= limits['boost_disable_below_v']:
        failures.append({
            'id': 'unpowered-pg-disable',
            'detail': 'PG has no active pull-down with U1 unpowered. Its specified low can '
                      'reach 1 V at the tabulated pull-up currents, whereas U4 requires '
                      'ENABLE <0.4 V. Charged B/USB paths cannot be certified OFF by this net.',
        })
    # These are unimplemented engineering proofs, not user questions or a list
    # of physical tests to gate delivery. They must not disappear if a resistor
    # edit removes one of the counterexamples above.
    failures.extend([
        {'id': 'en-pullup-operating-point', 'detail': 'Bound U3 EN source current at the '
         'actual divider voltage. Its 0 V test point is only a conditional estimate here.'},
        {'id': 'fault-energy-coordination', 'detail': 'No sourced minimum loop resistance, '
         'prospective short-current bound or maximum total clearing I2t/withstand '
         'coordination. F1 nominal 19.7 mOhm and 2.35 A2s are not guaranteed bounds.'},
        {'id': 'loaded-path-and-branches', 'detail': 'Exact PCB/copper, terminals, wire gauges, '
         'branch fuses, loaded envelopes and USB/sense/return/backfeed circuits remain undesigned. '
         'Reference average load is not a continuous/PWM/radio/inrush peak rating.'},
        {'id': 'reset-and-recovery', 'detail': 'No worst-case discharge/leakage/lockout model '
         'for A/B/C/5V, bounce or rapid swaps. Five-second OFF dwell is a proposal. '
         'CE=GND on LM66100 provides RPP, not the CE=VOUT reverse-current-blocking configuration.'},
        {'id': 'state-and-thermal-qualification', 'detail': 'Absent/depleted/reversed/bouncing '
         'cells, rebound, charged capacitors, overload/short, cleared faults and USB '
         'states lack a complete circuit model. Enclosed temperature bounds remain open.'},
    ])
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['check', 'report'])
    args = parser.parse_args()
    try:
        spec = json.loads((HERE/'electrical-review.json').read_text())
        result = review(spec)
        result['control_revision_study'] = control_study(
            spec, json.loads((HERE/'electrical-control-study.json').read_text()))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('ELECTRICAL INPUT ERROR: ' + str(exc))
        return 1
    print(json.dumps(result, indent=2, allow_nan=False))
    if args.command == 'check' and result['failures']:
        print('ELECTRICAL CHECK FAILED: candidate is not qualified; do not freeze compartment.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
