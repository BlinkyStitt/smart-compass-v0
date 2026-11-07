"""A second raw cell/pack definition cannot replace the selected shared source."""
import copy,json,unittest
from pathlib import Path
import battery_access
import importlib.util
spec=importlib.util.spec_from_file_location('single_cell_narrow_layout',Path(__file__).resolve().parents[2]/'designs/stacked/layout.py')
layout=importlib.util.module_from_spec(spec);spec.loader.exec_module(layout)

class SingleCellParameterTests(unittest.TestCase):
    def test_selected_shared_cell_is_the_only_narrow_battery_source(self):
        spec=battery_access.definition();battery_access.validate(spec,'narrow')
        self.assertEqual(spec['cell']['quantity'],1)
        p=layout.parameters();layout.validate(p)
        self.assertNotIn('battery_count',p)
        self.assertNotIn('BatterySense',{e['name'] for e in p['electronics']})

    def test_raw_legacy_pack_runtime_and_duplicate_values_are_rejected(self):
        import tempfile
        from unittest.mock import patch
        raw=json.loads((layout.HERE/'parameters.json').read_text())
        for key,value in [('battery_count',1),('battery_count',2),('battery_mass_g',76),('battery_width',75.3),('battery_spacing',100),('runtime_hours',4),('assumed_efficiency',.85)]:
            changed=copy.deepcopy(raw);changed[key]=value
            with tempfile.TemporaryDirectory() as temporary:
                folder=Path(temporary);(folder/'parameters.json').write_text(json.dumps(changed))
                with patch.object(layout,'HERE',folder),self.subTest(key=key,value=value),self.assertRaisesRegex(ValueError,'shared selected cell'):
                    layout.parameters()

if __name__=='__main__':unittest.main()
