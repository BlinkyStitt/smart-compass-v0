"""Publish the narrow native inventory through its one installed-mass owner."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'hardware/enclosure'))
sys.path.insert(0,str(ROOT/'designs/stacked'))
import battery_access,battery_leads,harness_contract,narrow_inventory
import layout


def estimate_masses(parts):
    """Recompute all source allowances and reject a mixed or incomplete ledger."""
    parameters=layout.parameters()
    if harness_contract.numeric_record(parts['parameters_for_inventory'])!=harness_contract.numeric_record(parameters):raise ValueError('Narrow mass parameters differ from the selected native layout')
    cell=battery_access.definition();lead=battery_leads.layout(cell,'narrow');loom=harness_contract.load()
    result={}
    for material in ('glow','silver'):
        current=narrow_inventory.resolve(parts['products'],parameters,loom,{name:lead for name in ['BatteryLeadP','BatteryLeadN']},material)
        saved=parts['material_variants'][material]
        for key in ['components','cad_owners','mass_estimate']:
            if harness_contract.numeric_record(saved[key])!=harness_contract.numeric_record(current[key]):raise ValueError('Narrow native mass ledger is stale: '+material+'/'+key)
        if not current['mass_estimate']['ceiling_pass']:raise ValueError('Narrow worn mass exceeds the approved ceiling: '+material)
        result[material]=current
    return result
