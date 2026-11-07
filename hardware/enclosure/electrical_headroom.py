"""Regulator-input undervoltage clamp and conditional charge/hold-up bounds.

The upstream divider's DC equilibrium does not bound B during a load step.
U7 senses B at U4 and can pull ENABLE low independently of U6/PG. Its sourced
delay has test conditions, not a guarantee for arbitrary ramps or output loads.
Unknown assembly conditions remain unknown; no nominal value certifies a rail.
"""

import copy
import math


def number(value, name, *, positive=False):
    if (isinstance(value, bool) or not isinstance(value, (int, float))
            or not math.isfinite(value) or value < 0 or (positive and value == 0)):
        raise ValueError(name + ' must be finite and ' + ('positive' if positive else 'nonnegative'))
    return value


def headroom_netlist(candidate, definition):
    """Add an independent open-drain clamp; preserve U6 and the depletion latch."""
    expected = {'B': ['U7.2'], 'GND': ['U7.3'], 'BOOST_ENABLE': ['U7.1']}
    if (definition['schema_version'] != 1 or definition['supervisor'] != 'TPS3840DL35DBVR'
            or definition['nets'] != expected or definition['open_pins'] != ['U7.4', 'U7.5']):
        raise ValueError('Unsupported B-rail headroom clamp topology')
    result = copy.deepcopy(candidate)
    nets = result['nets']
    for name, pins in {'B': {'U4.VIN', 'U6.4', 'C_U6.1'},
                       'GND': {'U4.GND', 'U6.2', 'C_U6.2'},
                       'BOOST_ENABLE': {'U4.ENABLE', 'U6.6'}}.items():
        if not pins <= set(nets.get(name, [])):
            raise ValueError('Headroom clamp requires local supply, return and bypass: ' + name)
    for name, pins in expected.items():
        nets[name].extend(pins)
    result['open_pins'].extend(definition['open_pins'])
    pins = [pin for members in nets.values() for pin in members] + result['open_pins']
    if len(pins) != len(set(pins)):
        raise ValueError('Duplicate pin in headroom clamp netlist')
    result['U7'] = definition['supervisor']
    return result


def hold_up(start_v, minimum_v, capacitance_min_f, deficit_max_a,
            series_max_ohm, delay_max_s, additional_drop_max_v):
    """Comparison bound V >= start - I*R - drop - I*t/C until shutdown.

I bounds TOTAL capacitor discharge (load, leakage, reverse escape, bleeders),
not average load or eFuse input current. C is minimum differential capacitance
throughout the voltage/temperature range. Series drop includes ESR and both
conductors; inductive/other instantaneous losses have their own bound.
This model requires no helpful upstream current and takes no credit for it.
"""
    number(start_v, 'start voltage', positive=True)
    number(minimum_v, 'minimum voltage', positive=True)
    values = {'capacitance_min_f': capacitance_min_f, 'deficit_max_a': deficit_max_a,
              'series_max_ohm': series_max_ohm, 'delay_max_s': delay_max_s,
              'additional_drop_max_v': additional_drop_max_v}
    for name, value in values.items():
        if value is not None:
            number(value, name, positive=name == 'capacitance_min_f')
    missing = [name for name, value in values.items() if value is None]
    if missing:
        return {'voltage_lower_v': None, 'margin_v': None,
                'required_capacitance_min_f': None, 'pass': False, 'missing': missing}
    initial = start_v - deficit_max_a * series_max_ohm - additional_drop_max_v
    available = initial - minimum_v
    charge = deficit_max_a * delay_max_s
    voltage = initial - charge / capacitance_min_f
    # None distinguishes an impossible instantaneous-drop budget from zero charge.
    required = (charge / available if available > 0
                else 0.0 if available == 0 and charge == 0 else None)
    for name, value in [('voltage', voltage), ('margin', voltage - minimum_v),
                        ('charge', charge), ('required capacitance', required)]:
        if value is not None and not math.isfinite(value):
            raise ValueError('Hold-up arithmetic overflow: ' + name)
    return {'voltage_lower_v': voltage, 'margin_v': voltage - minimum_v,
            'required_capacitance_min_f': required,
            'instantaneous_margin_v': available,
            'charge_deficit_c': charge, 'pass': voltage >= minimum_v, 'missing': []}


def headroom_study(spec, candidate, definition):
    """Compose the proposed clamp and expose its remaining assembly premises."""
    candidate = headroom_netlist(candidate, definition)
    limits = definition['limits']
    for name, value in limits.items():
        number(value, name, positive=True)
    if not 0 < limits['threshold_error_fraction'] < 1 or not 0 < limits['timing_overdrive_fraction'] < 1:
        raise ValueError('Threshold error and timing overdrive must lie in (0,1)')
    if limits['hysteresis_min_v'] > limits['hysteresis_max_v']:
        raise ValueError('Reversed hysteresis limits')
    falling = [limits['threshold_nominal_v'] * (1 - limits['threshold_error_fraction']),
               limits['threshold_nominal_v'] * (1 + limits['threshold_error_fraction'])]
    rising = [falling[0] + limits['hysteresis_min_v'], falling[1] + limits['hysteresis_max_v']]
    # Budget from the lower voltage at the datasheet's 10% overdrive, THEN allow
    # the entire falling delay again. Do not start a 30 us clock at an arbitrary
    # barely-crossed comparator threshold. This does not generalize the fixture.
    timing_start = falling[0] * (1 - limits['timing_overdrive_fraction'])
    minimum = spec['limits']['boost_min_input_v']
    cases = {}
    for design, bounds in definition['assembly_bounds'].items():
        fields = {'capacitance_min_f', 'deficit_max_a', 'series_max_ohm',
                  'boost_shutdown_max_s', 'additional_drop_max_v', 'enable_source_max_a'}
        if set(bounds) != fields | {'premises'}:
            raise ValueError('Missing/extra headroom bound: ' + design)
        for name in fields:
            if bounds[name] is not None:
                number(bounds[name], name, positive=name == 'capacitance_min_f')
        premises = bounds['premises']
        if set(premises) != {'timing_test_conditions_covered', 'all_current_paths_covered',
                             'local_voltage_and_temperature_covered', 'startup_rebound_covered'}:
            raise ValueError('Missing headroom applicability premise: ' + design)
        if any(value is not None and type(value) is not bool for value in premises.values()):
            raise ValueError('Headroom premises must be boolean or unknown')
        unresolved = [name for name, value in premises.items() if value is not True]
        delay = bounds['boost_shutdown_max_s']
        delay = None if delay is None else delay + limits['falling_delay_max_s']
        envelope = hold_up(timing_start, minimum, bounds['capacitance_min_f'],
                           bounds['deficit_max_a'], bounds['series_max_ohm'], delay,
                           bounds['additional_drop_max_v'])
        source = bounds['enable_source_max_a']
        clamp = (source is not None and source <= limits['reset_sink_test_a']
                 and limits['reset_low_max_v'] < spec['limits']['boost_disable_below_v'])
        cases[design] = {'hold_up': envelope, 'conditional_clamp_pass': clamp,
                         'unresolved_premises': unresolved,
                         'pass': envelope['pass'] and clamp and not unresolved}
    if set(cases) != {'wide', 'narrow'}:
        raise ValueError('Both designs require headroom bounds')
    reference = definition['reference_case']
    # Optimistic example only: reference power/efficiency is not a peak rating.
    current = spec['candidate']['reference_output_w'] / spec['candidate']['reference_efficiency'] / minimum
    reference_envelope = hold_up(timing_start, minimum, reference['capacitance_f'], current,
                                reference['series_ohm'], limits['falling_delay_max_s'], 0)
    return {
        'revision': definition['revision'], 'defect_id': definition['defect_id'],
        'qualified': False, 'candidate_nets': candidate['nets'],
        'candidate_open_pins': candidate['open_pins'],
        'falling_threshold_v': falling, 'rising_threshold_v': rising,
        'timing_budget_start_v': timing_start,
        'reference_current_a': current, 'reference_hold_up': reference_envelope,
        'reference_scope': reference['scope'], 'designs': cases,
        'remaining_evidence': definition['remaining_evidence'],
    }
