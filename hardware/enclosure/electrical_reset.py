"""Analytical upper envelope for disconnected, passively coupled RC rails.

This is not a switching-converter simulator. An unknown capacitance, ingress or
isolation condition returns no discharge time. In particular, a conducting
LM66100 is not an open circuit, and an enabled boost is not a passive coupling.
"""

import heapq
import math


def capacitor_nodes(candidate):
    """Resolve every declared/discrete capacitor from both pins, once.

    Internal device storage is deliberately outside this inventory. A nominal
    value, missing part, or unspecified capacitor does not supply a bound.
    Only capacitors to the common return are supported by the energy model.
    """
    pins = {}
    for node, members in candidate['nets'].items():
        for pin in members:
            if pin in pins:
                raise ValueError('Duplicate capacitor-netlist pin: ' + pin)
            pins[pin] = node
    declared = candidate['capacitors_nominal_f']
    names = set(declared) | {pin.split('.')[0] for pin in pins if pin.startswith('C_')}
    result = {}
    for name in sorted(names):
        if {pin for pin in pins if pin.startswith(name + '.')} != {name + '.1', name + '.2'}:
            raise ValueError('Missing or extra capacitor terminals: ' + name)
        first, second = pins.get(name + '.1'), pins.get(name + '.2')
        if first is None or second is None or first == second:
            raise ValueError('Missing or shorted capacitor terminals: ' + name)
        if second != 'GND':
            raise ValueError('Storage model requires grounded capacitor return: ' + name)
        nominal = declared.get(name)
        if nominal is not None:
            _number(nominal, 'nominal capacitance', positive=True)
        result[name] = {'node': first, 'nominal_f': nominal}
    return result


def storage_envelope(nodes, resistors, target_v, elapsed_s, *,
                     sources_disconnected, passive_transfer_only, complete_storage):
    """Conservative energy bound for grounded capacitors and resistive drains.

    For each node choose a resistor path to GND, with resistance upper bound R_i.
    Cauchy-Schwarz gives V_i² <= R_i * P, where P is total resistor heat.
    Hence E <= tau*P/2, tau=sum(Cmax_i*R_i). Also |V_i| <= sqrt(2E/Cmin_i).
    For bounded ingress, k=sum(Imax_i/sqrt(Cmin_i)), x=sqrt(2E) satisfies
    dx/dt <= -x/tau+k. Unknown/isolated storage must never be omitted.

    This covers additional passive dissipative coupling, not hidden energy,
    inductors, active conversion or capacitance that changes with time. The
    supplied capacitance intervals must bound differential capacitance over
    voltage, with no hysteretic/absorption state outside the node inventory.
    It is intentionally looser than off_envelope, which needs a direct drain
    at every node. No numerical integration or assumed time step is involved.
    """
    _number(target_v, 'target voltage', positive=True)
    _number(elapsed_s, 'elapsed time')
    if not nodes or 'GND' in nodes:
        raise ValueError('Storage needs non-ground nodes')
    missing = []
    for name, value in [('sources_disconnected', sources_disconnected),
                        ('passive_transfer_only', passive_transfer_only),
                        ('complete_storage', complete_storage)]:
        if value is not None and type(value) is not bool:
            raise ValueError(name + ' must be boolean or unknown')
        if value is not True:
            missing.append(name)
    for name, row in nodes.items():
        for field in ('capacitance_min_f', 'capacitance_max_f', 'incoming_max_a', 'initial_max_v'):
            value = row.get(field)
            if value is None:
                missing.append(name + '.' + field)
            else:
                _number(value, name + '.' + field, positive=field.startswith('capacitance'))
        low, high = row.get('capacitance_min_f'), row.get('capacitance_max_f')
        if low is not None and high is not None and low > high:
            raise ValueError('Reversed storage capacitance: ' + name)
    graph = {name: [] for name in {*nodes, 'GND'}}
    for name, resistor in resistors.items():
        ends = resistor['ends']
        if (not isinstance(ends, list) or len(ends) != 2 or ends[0] == ends[1]
                or any(node not in graph for node in ends)):
            raise ValueError('Invalid discharge path: ' + name)
        resistance = resistor['resistance_max_ohm']
        if resistance is None:
            # An unknown optional parallel drain cannot improve the bound.
            continue
        _number(resistance, 'discharge resistance', positive=True)
        first, second = ends
        graph[first].append((second, resistance))
        graph[second].append((first, resistance))
    distance, queue = {'GND': 0.0}, [(0.0, 'GND')]
    while queue:
        resistance, node = heapq.heappop(queue)
        if resistance != distance[node]:
            continue
        for other, edge in graph[node]:
            total = _number(resistance + edge, 'summed discharge path', positive=True)
            if other not in distance or total < distance[other]:
                distance[other] = total
                heapq.heappush(queue, (total, other))
    paths = {node: distance.get(node) for node in nodes}
    missing.extend(node + '.ground_path' for node in nodes if node not in distance)
    if missing:
        return {'status': 'unbounded', 'missing': sorted(missing),
                'ground_path_max_ohm': paths, 'required_off_s': None,
                'voltage_upper_v': None, 'below_target': False}
    tau = _number(sum(row['capacitance_max_f'] * paths[node] for node, row in nodes.items()),
                  'energy decay time constant', positive=True)
    initial_energy = _number(sum(.5 * row['capacitance_max_f'] * row['initial_max_v'] * row['initial_max_v']
                                 for row in nodes.values()), 'initial stored energy')
    ingress = _number(sum(row['incoming_max_a'] / math.sqrt(row['capacitance_min_f'])
                          for row in nodes.values()), 'energy ingress coefficient')
    floor = _number(ingress * tau, 'energy floor')
    initial = _number(max(math.sqrt(2 * initial_energy), floor), 'initial energy amplitude')
    target = min(target_v * math.sqrt(row['capacitance_min_f']) for row in nodes.values())
    _number(target, 'energy target', positive=True)
    upper = floor + (initial - floor) * math.exp(-elapsed_s / tau)
    if floor >= target:
        required = None
    elif initial < target:
        required = 0.0
    else:
        required = _number(tau * (math.log(initial - floor) - math.log(target - floor)),
                           'required energy discharge time')
    return {'status': 'bounded-passive-energy-model', 'missing': [],
            'ground_path_max_ohm': paths, 'time_constant_s': tau,
            'initial_energy_max_j': initial_energy, 'required_off_s': required,
            'voltage_upper_v': {node: _number(upper / math.sqrt(row['capacitance_min_f']), 'voltage bound')
                                for node, row in nodes.items()},
            'below_target': required is not None and (initial < target or elapsed_s > required)}


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
