"""Real primary wire data cannot be reduced to force a fit or mass pass."""
import copy,json,unittest
from pathlib import Path
from unittest.mock import patch
from harness_stock import validate_limits
HERE=Path(__file__).resolve().parent

class WireStockTests(unittest.TestCase):
    def setUp(self):self.limits=json.loads((HERE/'electrical-design.json').read_text())['wiring']['stock_limits']

    def test_selected_source_data_retains_nominal_mass_boundary(self):
        proof=validate_limits(self.limits)
        self.assertIn('nominal',proof['mass_kind'])
        self.assertEqual(proof['physical_acceptance'],'unmeasured')
        self.assertEqual(proof['resistance_temperature_c'],20)

    def test_reduced_or_nonfinite_values_cannot_reuse_the_source(self):
        for key in ['maximum_od_mm','nominal_mass_g_m','maximum_resistance_ohm_m_at_20c']:
            for value in [0,True,float('nan'),float('inf')]:
                limits=copy.deepcopy(self.limits);limits['branches'][key]=value
                with self.subTest(key=key,value=value),self.assertRaises(ValueError):validate_limits(limits)
        limits=copy.deepcopy(self.limits);limits['main']['stock']='M22759/17-18'
        with self.assertRaisesRegex(ValueError,'stock changed'):validate_limits(limits)

    def test_changed_primary_bytes_are_rejected(self):
        actual=Path.read_bytes
        def read(path):
            raw=actual(path)
            return raw+b'changed' if path.name=='amphenol-m22759.pdf' else raw
        with patch.object(Path,'read_bytes',read),self.assertRaisesRegex(ValueError,'primary source changed'):validate_limits(self.limits)

    def test_missing_primary_data_is_an_error(self):
        actual=Path.read_bytes
        def read(path):
            if path.name=='amphenol-m22759.pdf':raise FileNotFoundError('Required wire source missing')
            return actual(path)
        with patch.object(Path,'read_bytes',read),self.assertRaises(FileNotFoundError):validate_limits(self.limits)

if __name__=='__main__':unittest.main()
