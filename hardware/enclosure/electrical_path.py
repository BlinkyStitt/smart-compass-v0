"""Two-conductor DC harness audit, separate from converter/transient qualification.

Paths list physical segments in source-to-load order, then load-to-source return
order. Currents add on shared segments before voltage drop or I²R is calculated.
An unknown current or resistance propagates to every affected path. Catalogue
20°C wire resistance is never promoted to an enclosed-temperature rating.
"""

import math


def number(value, name, *, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0 or (positive and value == 0)):
        raise ValueError(name + ' must be finite and ' + ('positive' if positive else 'nonnegative'))
    return value


def wire_resistance(part, length_mm):
    """Use the unrounded imperial maximum, not the rounded metric column."""
    length = number(length_mm, 'cut length', positive=True)
    dcr = number(part['max_ohm_per_1000ft_at_20c'], 'maximum conductor DCR', positive=True)
    if part['reference_temperature_c'] != 20 or part['resistance_kind'] != 'maximum':
        raise ValueError('Wire requires a maximum DCR at 20°C')
    # The international foot is exactly 0.3048 m; lengths include both stripped ends.
    return dcr * length / 304800


def converted_current(output_currents, bounds):
    """Bound source current by output power, efficiency and local input demand.

    Output voltage is measured at the converter, so its power already includes
    downstream conductor dissipation. Local current covers all other board
    demand including quiescent current; it must exclude the named output loads.
    A DC efficiency does not establish an instantaneous PWM/inrush bound: the
    separate applicability premise must cover the particular demand class.
    """
    fields = {'input_min_v', 'output_max_v', 'efficiency_min', 'local_max_a',
              'conditions_covered'}
    if set(bounds) != fields or not output_currents:
        raise ValueError('Conversion needs complete voltage, efficiency, local demand and conditions')
    if bounds['conditions_covered'] is not None and type(bounds['conditions_covered']) is not bool:
        raise ValueError('Conversion applicability must be boolean or unknown')
    for name in fields - {'conditions_covered'}:
        if bounds[name] is not None:
            number(bounds[name], name, positive=name != 'local_max_a')
    if bounds['efficiency_min'] is not None and bounds['efficiency_min'] > 1:
        raise ValueError('Conversion efficiency must not exceed one')
    for name, current in output_currents.items():
        if current is not None:
            number(current, name + '.output_current')
    missing = sorted([name for name in fields - {'conditions_covered'} if bounds[name] is None]
                     + [name + '.output_current' for name, value in output_currents.items() if value is None])
    if bounds['conditions_covered'] is not True:
        missing.append('conditions_covered')
    current = power = None
    if not missing:
        power = number(math.fsum(output_currents.values()) * bounds['output_max_v'], 'output power')
        current = number(power / bounds['efficiency_min'] / bounds['input_min_v']
                         + bounds['local_max_a'], 'converted current')
    return {'input_max_a': current, 'output_max_w': power, 'missing': missing}


def supply_currents(currents, conversion):
    """Propagate external 3.3 V loads through Sparkle and every 5 V load to U4.

    `sparkle` is LOCAL board input demand; the returned Sparkle current also
    supplies peripherals. U4 input is derived, never an independent scenario
    number that can remain zero while downstream loads are running.
    """
    peripherals = {'blackpill', 'gps', 'imu', 'radio'}
    five_volt = {'circle', 'led_group1', 'led_group2', 'led_group3', 'sparkle'}
    if (set(currents) != peripherals | five_volt | {'controller', 'battery_sense'}
            or set(conversion) != {'sparkle', 'boost'}):
        raise ValueError('Supply dependencies must include every load and derive boost input')
    for name, current in currents.items():
        if current is not None:
            number(current, name + '.current')
    # The local board current has one owner: do not add it both here and in a
    # converter quiescent-current field supplied by the caller.
    sparkle = dict(conversion['sparkle'])
    if 'local_max_a' in sparkle:
        raise ValueError('Sparkle local current belongs only to the scenario')
    sparkle['local_max_a'] = currents['sparkle']
    peripheral = converted_current({name: currents[name] for name in sorted(peripherals)}, sparkle)
    resolved = dict(currents, sparkle=peripheral['input_max_a'])
    boost = converted_current({name: resolved[name] for name in sorted(five_volt)}, conversion['boost'])
    resolved['boost_input'] = boost['input_max_a']
    return resolved, {'sparkle': peripheral, 'boost': boost}


def analyze(segments, paths, currents):
    """Audit a passive radial network at prescribed load-current maxima.

    This is not a constant-power solution, an AC impedance model, or a source
    fault calculation. Independent nonnegative current maxima may coincide.
    Cycles, opposite traversal and orphan segments need a different solver.
    """
    if not segments or not paths or set(currents) != set(paths):
        raise ValueError('Each path needs exactly one current, possibly unknown')
    owners = {name: set() for name in segments}
    directions = {}
    used_paths = {}
    for name, segment in segments.items():
        if (not isinstance(segment['ends'], list) or len(segment['ends']) != 2
                or not all(isinstance(node, str) and node for node in segment['ends'])
                or segment['ends'][0] == segment['ends'][1]):
            raise ValueError('Invalid segment endpoints: ' + name)
        resistance = segment['resistance_max_ohm']
        if resistance is not None:
            number(resistance, 'segment resistance')
    for name, path in paths.items():
        current = currents[name]
        if current is not None:
            number(current, 'path current')
        used, nodes = [], set()
        for leg, ends in (('supply', path['supply_ends']), ('return', path['return_ends'])):
            if len(ends) != 2 or ends[0] == ends[1] or not path[leg]:
                raise ValueError('Both conductors must be explicit: ' + name)
            node = ends[0]
            if node in nodes:
                raise ValueError('Supply/return short: ' + name)
            nodes.add(node)
            for edge in path[leg]:
                if edge not in segments or edge in used:
                    raise ValueError('Missing or repeated physical segment: ' + edge)
                start, stop = segments[edge]['ends']
                if node == start:
                    destination, direction = stop, 1
                elif node == stop:
                    destination, direction = start, -1
                else:
                    raise ValueError('Disconnected ' + leg + ' path: ' + name)
                if destination in nodes:
                    raise ValueError('Cycle or supply/return short: ' + name)
                nodes.add(destination)
                if edge in directions and directions[edge] != direction:
                    raise ValueError('Opposite current paths require a network solver: ' + edge)
                directions[edge] = direction
                owners[edge].add(name)
                used.append(edge)
                node = destination
            if node != ends[1]:
                raise ValueError('Wrong ' + leg + ' terminal: ' + name)
        used_paths[name] = used
    if any(not uses for uses in owners.values()):
        raise ValueError('Unaccounted physical segment')
    # Reject parallel/alternate conducting routes as well as cycles within a path.
    parent = {}

    def root(node):
        parent.setdefault(node, node)
        while parent[node] != node:
            node = parent[node]
        return node

    for segment in segments.values():
        a, b = (root(node) for node in segment['ends'])
        if a == b:
            raise ValueError('Non-radial network requires a network solver')
        parent[a] = b

    edge_results = {}
    for edge, uses in owners.items():
        missing = [name + '.current_max_a' for name in sorted(uses) if currents[name] is None]
        current = None if missing else math.fsum(currents[name] for name in sorted(uses))
        resistance = segments[edge]['resistance_max_ohm']
        if resistance is None:
            missing.append(edge + '.resistance_max_ohm')
        bounded = current is not None and resistance is not None
        edge_results[edge] = {
            'current_max_a': current,
            'drop_max_v': current * resistance if bounded else None,
            'loss_max_w': current * current * resistance if bounded else None,
            'missing': missing,
        }
    path_results = {}
    for name, used in used_paths.items():
        missing = sorted({item for edge in used for item in edge_results[edge]['missing']})
        path_results[name] = {
            'drop_max_v': None if missing else math.fsum(edge_results[edge]['drop_max_v'] for edge in used),
            'missing': missing,
        }
    return {'segments': edge_results, 'paths': path_results,
            'loss_max_w': (math.fsum(row['loss_max_w'] for row in edge_results.values())
                           if all(row['loss_max_w'] is not None for row in edge_results.values()) else None)}


def harness_study(definition, candidate, limits):
    """Bind planned wires to the composed protection netlist and audit both designs."""
    if definition['schema_version'] != 2:
        raise ValueError('Unsupported harness schema')
    pins = {pin: net for net, members in candidate['nets'].items() for pin in members}
    if len(pins) != sum(len(members) for members in candidate['nets'].values()):
        raise ValueError('Duplicate pin ownership in protection netlist')
    if set(pins) & set(definition['junction_nets']):
        raise ValueError('Harness junction shadows a component pin')
    for pin, net in {'U4.VOUT': 'FIVE_V', 'U4.GND': 'GND',
                     'loads.supply': 'FIVE_V', 'loads.return': 'GND'}.items():
        if pins.get(pin) != net:
            raise ValueError('Output distribution disagrees with protection netlist')
    load_ports = definition['load_ports']
    required_loads = {'circle', 'led_group1', 'led_group2', 'led_group3',
                      'sparkle', 'blackpill', 'gps', 'imu', 'radio'}
    if set(load_ports) != required_loads or set(definition['paths']) != required_loads | {
            'boost_input', 'controller', 'battery_sense'}:
        raise ValueError('Harness must account for every power load')
    peripherals = {'blackpill', 'gps', 'imu', 'radio'}
    peak_limit = definition['peripheral_peak_limit_a']
    if peak_limit != .5 or isinstance(peak_limit, bool):
        raise ValueError('Sparkle external rail requires the published 0.5 A peak limit')
    for name, port in load_ports.items():
        path = definition['paths'][name]
        supply, ret, voltage = (('sparkle.3V3', 'sparkle.RETURN.PORT', 3.3)
                                if name in peripherals else ('U4.VOUT', 'U4.GND', 5))
        if (path['supply_ends'] != [supply, port['supply']]
                or path['return_ends'] != [port['return'], ret]
                or port['nominal_v'] != voltage):
            raise ValueError('Load must preserve its supply voltage and return terminals: ' + name)
    parts = definition['wire_parts']
    designs = definition['designs']
    if set(designs) != {'wide', 'narrow'}:
        raise ValueError('Both harness designs are required')
    if set(definition['scenarios']) != {'continuous', 'pwm_radio_peak', 'inrush'}:
        raise ValueError('Continuous, PWM/radio peak and inrush bounds are required')
    if set(definition['conversion_bounds']) != set(designs):
        raise ValueError('Separate converter bounds are required for each design')
    results = {}
    for design, lengths in designs.items():
        wire_ids = {key for key, row in definition['segments'].items() if row['kind'] == 'wire'}
        if set(lengths) != wire_ids:
            raise ValueError('Missing or extra per-design wire lengths: ' + design)
        segments, cutlist = {}, []
        for name, record in definition['segments'].items():
            ends = record['ends']
            if record['kind'] == 'wire':
                part = parts[record['wire_part']]
                # A fixed harness wire must stay on its declared logical net.
                # Intermediate junctions must be explicitly bound to that net.
                for endpoint in ends:
                    net = pins.get(endpoint, definition['junction_nets'].get(endpoint))
                    if net != record['net']:
                        raise ValueError('Wire bypasses protection or has an unowned endpoint: ' + name)
                resistance = wire_resistance(part, lengths[name])
                cutlist.append({'id': name, 'part': part['part'], 'length_mm': lengths[name],
                                'ends': ends, 'resistance_max_ohm_at_20c': resistance})
            elif record['kind'] == 'unbounded':
                resistance = None
            else:
                raise ValueError('Unsupported harness segment kind')
            segments[name] = {'ends': ends, 'resistance_max_ohm': resistance}
        cases = {}
        if set(definition['conversion_bounds'][design]) != set(definition['scenarios']):
            raise ValueError('Each converter needs continuous, peak and inrush applicability')
        for name, local_currents in definition['scenarios'].items():
            currents, conversion = supply_currents(local_currents, definition['conversion_bounds'][design][name])
            result = analyze(segments, definition['paths'], currents)
            peripheral_peak = (None if any(currents[key] is None for key in peripherals)
                               else math.fsum(currents[key] for key in sorted(peripherals)))
            cases[name] = {
                'loss_max_w': result['loss_max_w'],
                'paths': result['paths'],
                'resolved_current_max_a': currents,
                'conversion': conversion,
                'external_3v3_current_a': peripheral_peak,
                'within_published_peak_limit': (None if peripheral_peak is None
                                               else peripheral_peak <= peak_limit),
            }
        wire_paths = {
            name: math.fsum(segments[edge]['resistance_max_ohm']
                            for edge in path['supply'] + path['return'] if edge in wire_ids)
            for name, path in definition['paths'].items()
        }
        power = number(candidate['reference_output_w'], 'reference power', positive=True)
        efficiency = number(candidate['reference_efficiency'], 'reference efficiency', positive=True)
        if efficiency > 1:
            raise ValueError('Efficiency must be at most one')
        boost_min = number(limits['boost_min_input_v'], 'boost input minimum', positive=True)
        reference_current = power / efficiency / boost_min
        r_wire = wire_paths['boost_input']
        results[design] = {
            'cutlist': cutlist,
            'total_conductor_length_mm': sum(row['length_mm'] for row in cutlist),
            'wire_only_path_ohm_at_20c': wire_paths,
            'reference_boost_wires_only': {
                'load_current_a': reference_current,
                'drop_v': reference_current * r_wire,
                'loss_w': reference_current**2 * r_wire,
                'conditions': '20 C wires, declared reference load/efficiency at boost minimum input. '
                              'Excludes controller/sense currents, contacts, joints, PCB, switch, fuse '
                              'and eFuse. Neither total path loss nor a peak-current bound.',
            },
            'cases': cases,
        }
    return {
        'revision': definition['revision'], 'defect_id': definition['defect_id'],
        'qualified': False, 'status': 'specified-wire-harness-with-unbounded-assembly',
        'reference_temperature_c': 20, 'designs': results,
        'remaining_evidence': definition['remaining_evidence'],
    }
