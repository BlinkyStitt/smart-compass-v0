"""Selected published stock and actual CAD volumes own the Ti mass estimate."""
import copy,json,math,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import narrow_fasteners as owner

class NarrowFastenerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data,cls.parts=owner.load()

    def test_every_selected_cap_uses_unchanged_allowances_and_source(self):
        self.assertEqual(len(self.parts),52)
        for name,row in self.parts.items():
            volume=math.pi*((row['thread_diameter_mm']/2)**2*row['finished_under_head_length_target_mm']+(row['head_diameter_mm']/2)**2*row['head_height_mm'])/1000
            selected,nominal,interval=owner.selected_mass({'name':name,'volume_cm3':volume},self.data,self.parts)
            self.assertEqual(selected,row)
            self.assertAlmostEqual(nominal,volume*4.42)
            self.assertEqual(interval,[nominal*.65,nominal*1.5])
        for retained in ['BatteryKeeperScrew','BatteryHingeScrew','BlackPillScrew2','BlackPillScrew3']:
            self.assertNotIn(retained,self.parts)

    def test_actual_installed_screw_geometry_cannot_drift(self):
        name=next(iter(self.parts))
        with self.assertRaisesRegex(ValueError,'CAD envelope changed'):
            owner.selected_mass({'name':name,'volume_cm3':.001},self.data,self.parts)
        self.assertIsNone(owner.selected_mass({'name':'UnselectedSteelScrew'},self.data,self.parts))

    def checked_mutation(self,mutate):
        data=copy.deepcopy(self.data);mutate(data)
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary);(directory/'fasteners.json').write_text(json.dumps(data))
            (directory/'sources').mkdir();(directory/'sources/fasteners').symlink_to(owner.DIRECTORY/'sources/fasteners',target_is_directory=True)
            return owner.load(directory)

    def test_narrower_mass_allowance_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'mass allowances'):
            self.checked_mutation(lambda d:d.update(mass_factors=[.8,1.1]))

    def test_duplicate_missing_and_wrong_head_stock_are_rejected(self):
        for mutate,message in [(lambda d:d['parts'].pop(),'census'),(lambda d:d['parts'].__setitem__(1,d['parts'][0]),'census'),(lambda d:d['parts'][0].update(head_height_mm=1.65),'published selected stock')]:
            with self.subTest(message=message),self.assertRaisesRegex(ValueError,message):self.checked_mutation(mutate)

    def test_partially_threaded_stock_cannot_supply_shorter_finish(self):
        def change(data):
            row=next(p for p in data['parts'] if p['stock_part']=='SSC-M2-20-TI5');row['finished_under_head_length_target_mm']=15
        with self.assertRaisesRegex(ValueError,'fully threaded short stock'):self.checked_mutation(change)

    def test_changed_primary_source_bytes_are_rejected(self):
        actual=Path.read_bytes
        def read(path):
            raw=actual(path)
            return raw+b'changed' if path.name=='timet.pdf' else raw
        with patch.object(Path,'read_bytes',read),self.assertRaisesRegex(ValueError,'source bytes changed'):owner.load()

if __name__=='__main__':unittest.main()
