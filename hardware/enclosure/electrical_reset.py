"""Analytical upper envelope for disconnected, passively coupled RC rails.

This is not a switching-converter simulator. An unknown capacitance, ingress or
isolation condition returns no discharge time. In particular, a conducting
LM66100 is not an open circuit, and an enabled boost is not a passive coupling.
"""

import math


def _number(value, name, *, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (float, int))
            or not math.isfinite(value) or value < 0 or (positive and value == 0)):
        raise ValueError(name + ' must be finite and ' + ('positive' if positive else 'nonnegative'))
    return value


def off_envelope(rails, target_v, elapsed_s, *, sources_disconnected, passive_transfer_only):
    """Bound ALL rail voltages even with arbitrary passive inter-rail conduction.

    At the highest-voltage rail, passive transfer cannot add current. Set
    floor=max(R_i*I_i), tau=max(R_i*C_i), and initial=max(V_i, floor). Then
    u(t)=floor+(initial-floor)*exp(-t/tau) bounds every rail for all t >= 0.
    R and C are upper bounds; I is *external* ingress, not internal transfer.
    A zero-impedance connection is covered by the passive limiting case.

    Requires nonnegative rails, positive differential capacitance, no hidden
    energy storage, and no active conversion. Unknown/false premises cannot
    produce a finite required time. This is sufficient, not a necessary bound.
    """
    _number(target_v, 'target voltage', positive=True)
    _number(elapsed_s, 'OFF elapsed time')
    if not rails:
        raise ValueError('At least one rail is required')
    missing = []
    for name, value in [('sources_disconnected', sources_disconnected),
                        ('passive_transfer_only', passive_transfer_only)]:
        if value is not None and type(value) is not bool:
            raise ValueError(name + ' must be boolean or unknown')
        if value is not True:
            missing.append(name)
    values = []
    for name, rail in rails.items():
        row = []
        for key in ('resistance_max_ohm', 'capacitance_max_f', 'incoming_max_a', 'initial_max_v'):
            value = rail.get(key)
            if value is None:
                missing.append(name + '.' + key)
            else:
                _number(value, name + '.' + key, positive=key in ('resistance_max_ohm', 'capacitance_max_f'))
            row.append(value)
        values.append(row)
    if missing:
        return {'status': 'unbounded', 'missing': missing, 'required_off_s': None,
                'voltage_upper_v': None, 'below_target': False}
    floor = max(r * i for r, c, i, v in values)
    tau = max(r * c for r, c, i, v in values)
    initial = max(floor, max(v for r, c, i, v in values))
    _number(floor, 'computed leakage floor')
    _number(tau, 'computed time constant', positive=True)
    voltage = floor + (initial - floor) * math.exp(-elapsed_s / tau)
    # Strictly below: a target at the leakage equilibrium is not attained in
    # finite time, even if floating-point exponential underflow hides the tail.
    if floor >= target_v:
        required = None
    elif initial < target_v:
        required = 0.0
    else:
        required = tau * math.log((initial - floor) / (target_v - floor))
        _number(required, 'computed discharge time')
    return {'status': 'bounded-passive-model', 'missing': [], 'floor_v': floor,
            'time_constant_s': tau, 'voltage_upper_v': voltage,
            'required_off_s': required,
            'below_target': required is not None and (initial < target_v or elapsed_s > required)}


def continuous_off_seconds(events, end_s):
    """Evaluate a supplied event fixture; no hardware debounce claim.

    ON, an unknown switch state, or an external source invalidates accumulated
    OFF time. A repeated OFF observation preserves its start. Times are strictly
    increasing; the most recent interval must end with all sources absent.
    """
    _number(end_s, 'end time')
    since, previous = None, -1.0
    for event in events:
        time = _number(event['time_s'], 'event time')
        if time <= previous or time > end_s:
            raise ValueError('Event times must increase and not exceed the end time')
        state = event['switch']
        source = event['external_source']
        if state not in ('OFF', 'ON', 'unknown') or type(source) is not bool:
            raise ValueError('Invalid switch/source event')
        if state == 'OFF' and not source:
            if since is None:
                since = time
        else:
            since = None
        previous = time
    return 0.0 if since is None else end_s - since
