"""Perturb the delivered narrow census and its real source allowances.

These are accounting regression tests, not measurements or assembly acceptance.
"""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from estimates import estimate_masses
import narrow_inventory,harness_contract,battery_access,battery_leads,layout

ROOT=Path(__file__).resolve().parents[1]

class EstimateTests(unittest.TestCase):
    def setUp(self):
        self.parts=json.loads((ROOT/'designs/stacked/exports/parts.json').read_text())
        self.parameters=layout.parameters();self.loom=harness_contract.load();cell=battery_access.definition();lead=battery_leads.layout(cell,'narrow')
        self.leads={name:lead for name in ['BatteryLeadP','BatteryLeadN']}

    def resolve(self,parts=None,material='glow'):
        return narrow_inventory.resolve((parts or self.parts)['products'],self.parameters,self.loom,self.leads,material)

    def test_native_ledger_and_all_accounting_owners_agree(self):
        result=estimate_masses(self.parts)
        self.assertEqual(set(result),{'glow','silver'})
        for material,ledger in result.items():
            self.assertEqual(set(ledger['cad_owners']),{p['name'] for p in self.parts['products']})
            names=[name for row in ledger['components'] for name in row['cad_parts']]
            self.assertEqual(len(names),len(set(names)))
            self.assertTrue(ledger['mass_estimate']['ceiling_pass'])
            self.assertEqual(next(row for row in ledger['components'] if row['id']=='cell')['installed_quantity'],1)

    def test_cell_source_mass_is_counted_once_in_pendant_and_worn_totals(self):
        before=self.resolve()['mass_estimate'];records=deepcopy(narrow_inventory.module_records())
        records['cell']['nominal_g']+=50;records['cell']['range_g']=[mass+50 for mass in records['cell']['range_g']]
        with patch.object(narrow_inventory,'module_records',return_value=records):after=self.resolve()['mass_estimate']
        for assembly in ['complete_pendant','total_worn']:
            self.assertAlmostEqual(after[assembly]['nominal_g']-before[assembly]['nominal_g'],50)
            for i in [0,1]:self.assertAlmostEqual(after[assembly]['range_g'][i]-before[assembly]['range_g'][i],50)
        self.assertEqual(after['necklace'],before['necklace'])

    def test_cell_and_antenna_envelopes_do_not_become_printed_mass(self):
        before=self.resolve()['mass_estimate'];changed=deepcopy(self.parts)
        for name in ['BatteryCell','RadioAntenna']:next(p for p in changed['products'] if p['name']==name)['volume_cm3']*=10
        self.assertEqual(self.resolve(changed)['mass_estimate'],before)

    def test_case_volume_uses_structural_density_once(self):
        before=self.resolve()['mass_estimate'];changed=deepcopy(self.parts)
        next(p for p in changed['products'] if p['name']=='RearCover')['volume_cm3']+=100
        after=self.resolve(changed)['mass_estimate']
        self.assertAlmostEqual(after['total_worn']['nominal_g']-before['total_worn']['nominal_g'],127)
        with self.assertRaisesRegex(ValueError,'stale'):estimate_masses(changed)

    def test_silver_changes_only_ring_material_mass(self):
        glow=self.resolve()['mass_estimate'];silver=self.resolve(material='silver')['mass_estimate']
        volume=sum(p['volume_cm3'] for p in self.parts['products'] if p['name'] in ['InnerDiffuser','SideDiffuser'])
        self.assertAlmostEqual(glow['total_worn']['nominal_g']-silver['total_worn']['nominal_g'],volume*(1.5-1.29))
        self.assertEqual(glow['necklace'],silver['necklace'])

    def test_continuous_negative_lead_has_one_full_cut_and_one_owner(self):
        ledger=self.resolve();wire=next(w for w in self.loom['routes'].values() if w.get('continuous_existing_part')=='BatteryLeadN')
        row=next(row for row in ledger['components'] if row['id']==wire['id'])
        self.assertEqual(set(row['cad_parts']),{'BatteryLeadN',wire['id']})
        stock=json.loads((ROOT/'hardware/enclosure/electrical-design.json').read_text())['wiring']['stock_limits']['main']
        self.assertAlmostEqual(row['mass_g_per_unit'],wire['finished_cut_target_mm']/1000*stock['nominal_mass_g_m'])
        self.assertFalse(any(row['id']=='BatteryLeadN' for row in ledger['components']))

    def test_missing_duplicate_or_unowned_parts_cannot_pass(self):
        for mode in ['missing','duplicate','unknown']:
            changed=deepcopy(self.parts)
            if mode=='missing':changed['products']=[p for p in changed['products'] if p['name']!='BatteryCell']
            elif mode=='duplicate':changed['products'].append(deepcopy(changed['products'][0]))
            else:changed['products'].append({'name':'UnreviewedElectronics','group':'Electronics','volume_cm3':1,'centre_mm':[0,0,0]})
            with self.subTest(mode=mode),self.assertRaises(ValueError):self.resolve(changed)

    def test_changed_native_mass_record_is_rejected(self):
        changed=deepcopy(self.parts);changed['material_variants']['glow']['mass_estimate']['upper_worn_g']-=1
        with self.assertRaisesRegex(ValueError,'stale'):estimate_masses(changed)

if __name__=='__main__':unittest.main()
