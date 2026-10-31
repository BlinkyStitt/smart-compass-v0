"""Exact KILL-filter response to a falling rail; not a whole-circuit simulator."""

import itertools
import math


def number(value, name, *, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0 or (positive and value == 0)):
        raise ValueError(name + ' must be finite and ' + ('positive' if positive else 'nonnegative'))
    return value


def ramp_crossing(top_ohm, bottom_ohm, capacitance_f, leakage_a,
                  threshold_v, initial_v, final_v, fall_s):
    """First downward KILL crossing, starting at the initial DC equilibrium.

    The supply falls linearly, then stays at final_v indefinitely. Constant
    leakage is positive out of the pin. The resistors retain their correlation
    in gain, time constant and leakage offset. No sampled-time crossing test.
    """
    for name, value in (('top', top_ohm), ('bottom', bottom_ohm),
                        ('capacitance', capacitance_f), ('threshold', threshold_v),
                        ('fall time', fall_s)):
        number(value, name, positive=True)
    number(initial_v, 'initial supply')
    number(final_v, 'final supply')
    if final_v >= initial_v:
        raise ValueError('Supply must fall strictly')
    if isinstance(leakage_a, bool) or not isinstance(leakage_a, (int, float)) or not math.isfinite(leakage_a):
        raise ValueError('Leakage must be finite and signed')
    gain = bottom_ohm / (top_ohm + bottom_ohm)
    resistance = top_ohm * gain
    tau = number(resistance * capacitance_f, 'filter time constant', positive=True)
    initial_pin = gain * initial_v - resistance * leakage_a
    final_pin = gain * final_v - resistance * leakage_a
    if min(initial_pin, final_pin) < 0 or not all(math.isfinite(v) for v in (initial_pin, final_pin)):
        raise ValueError('Filter operating point outside nonnegative pin model')
    slope = number((initial_v - final_v) / fall_s, 'falling slew', positive=True)

    def pin_at(time):
        # t - tau*(1-exp(-t/tau)); use its series near zero to avoid cancellation.
        x = time / tau
        ramp_time = (time * x * (0.5 - x / 6 + x*x / 24) if x < 1e-4
                     else time + tau * math.expm1(-x))
        return initial_pin - gain * slope * ramp_time

    at_end = pin_at(fall_s)
    if initial_pin <= threshold_v:
        crossing = 0.0
    elif final_pin >= threshold_v:
        crossing = None  # Equality is approached asymptotically, never crossed.
    elif at_end > threshold_v:
        crossing = fall_s + tau * math.log((at_end - final_pin) / (threshold_v - final_pin))
    else:
        lo, hi = 0.0, fall_s
        for _ in range(80):
            mid = (lo + hi) / 2
            if pin_at(mid) > threshold_v:
                lo = mid
            else:
                hi = mid
        crossing = hi
    if crossing is not None:
        number(crossing, 'crossing time')
    return {'crossing_s': crossing, 'tau_s': tau, 'pin_at_ramp_end_v': at_end,
            'rail_at_crossing_v': None if crossing is None else
            max(final_v, initial_v - slope * crossing)}


def cutoff_order_bound(kill_min_v, backup_max_v, tau_max_s, slew_max_v_per_s,
                       initial_excess_v, response_max_s, blanking_remaining_s):
    """Sufficient ordering condition for a continuous, nonincreasing supply.

    An input-referred first-order filter error is <= initial_excess + slew*tau.
    Subsequent rail loss is <= slew*(blanking + response). Response must cover
    the complete controller-to-eFuse path. Unknown inputs cannot yield a pass.
    Steps, bias changes, backfeed and arbitrary initial storage are excluded.
    """
    values = dict(kill_min_v=kill_min_v, backup_max_v=backup_max_v, tau_max_s=tau_max_s,
                  slew_max_v_per_s=slew_max_v_per_s, initial_excess_v=initial_excess_v,
                  response_max_s=response_max_s, blanking_remaining_s=blanking_remaining_s)
    for name, value in values.items():
        if value is not None:
            number(value, name)
    missing = [name for name, value in values.items() if value is None]
    loss = margin = None
    if not missing:
        loss = number(initial_excess_v + slew_max_v_per_s *
                      (tau_max_s + response_max_s + blanking_remaining_s), 'dynamic rail loss')
        margin = kill_min_v - backup_max_v - loss
    return {'missing': missing, 'dynamic_loss_max_v': loss, 'margin_v': margin,
            'conditional_pass': not missing and margin > 0}


def control_ramp_study(revision, limits, resistances, kill, backup, *, driver_within_limits):
    """Bind the dynamic calculation to the same divider as the static study.

    The nominal-capacitor examples assume zero downstream buffer delay and
    applicability of the controller's 7 V timing test. They expose ordering
    sensitivity, never fill missing assembly inputs with these assumptions.
    """
    definition = revision['ramp_study']
    cap = number(revision['capacitors']['C_KILL']['nominal_f'], 'nominal C_KILL', positive=True)
    top, bottom = resistances['R_KILL_TOP'], resistances['R_KILL_BOTTOM']
    parallel_max = top[1] * bottom[1] / (top[1] + bottom[1])
    timing = definition['controller_timing']
    delay = number(timing['kill_propagation_max_s'], 'controller delay', positive=True)
    pulse = number(timing['kill_minimum_pulse_s'], 'KILL low pulse', positive=True)
    profiles = {}
    for name, profile in definition['profiles'].items():
        blanking = number(profile['blanking_remaining_s'], 'remaining blanking')
        if blanking > limits['kill_blanking_s'][1]:
            raise ValueError('Remaining blanking exceeds controller maximum')
        crossings, releases, margins = [], [], []
        missed = 0
        for rt, rb, threshold, leakage in itertools.product(
                top, bottom, limits['kill_falling_v'], limits['kill_leakage_a']):
            row = ramp_crossing(rt, rb, cap, leakage, threshold,
                                profile['initial_v'], profile['final_v'], profile['fall_s'])
            if row['crossing_s'] is None:
                missed += 1
                continue
            # Conservatively wait a full pulse and propagation interval after
            # blanking, rather than inferring any credit for time spent blanked.
            release = max(row['crossing_s'], blanking) + pulse + delay
            voltage = max(profile['final_v'], profile['initial_v'] -
                          (profile['initial_v'] - profile['final_v']) * release / profile['fall_s'])
            crossings.append(row['crossing_s'])
            releases.append(release)
            margins.append(voltage - backup[1])
        profiles[name] = {
            'corners_without_crossing': missed,
            'kill_crossing_s': [min(crossings), max(crossings)] if crossings else None,
            'controller_release_upper_s': max(releases) if releases else None,
            'rail_minus_backup_max_v': min(margins) if margins else None,
            'conditional_order_pass': driver_within_limits and missed == 0 and bool(margins) and min(margins) > 0,
        }
    if set(definition['designs']) != {'wide', 'narrow'}:
        raise ValueError('Both control ramp design records are required')
    designs = {}
    for name, row in definition['designs'].items():
        capacitance = row['kill_capacitance_max_f']
        tau = None if capacitance is None else number(capacitance, 'assembly C_KILL', positive=True) * parallel_max
        designs[name] = cutoff_order_bound(kill[0], backup[1], tau,
            row['slew_max_v_per_s'], row['initial_excess_v'],
            row['response_max_s'], row['blanking_remaining_s'])
        designs[name]['conditional_pass'] &= driver_within_limits
    return {'qualified': False, 'nominal_capacitance_tau_max_s': cap * parallel_max,
            'static_driver_limits_pass': driver_within_limits,
            'conditional_profiles': profiles, 'assembly_order_bounds': designs,
            'scope': definition['scope'], 'remaining_evidence': definition['remaining_evidence']}
