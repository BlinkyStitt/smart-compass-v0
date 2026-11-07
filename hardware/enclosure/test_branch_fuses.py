"""Selected protection and finished assembly spaces remain one contract."""
import copy
import json
import unittest
import branch_fuses


class BranchFuseTests(unittest.TestCase):
    def test_every_selected_branch_has_two_distinct_joint_exits(self):
        for design in ('wide','narrow'):
            data=branch_fuses.geometry(design);ports=branch_fuses.ports(design);length=16.8 if design=='narrow' else 20
            self.assertEqual(len(ports),10)
            self.assertEqual({key.rsplit('.',1)[0] for key in ports},set(branch_fuses.PARTS))
            for name in branch_fuses.PARTS:
                a,b=ports[name+'.1'],ports[name+'.2']
                self.assertAlmostEqual(sum((x-y)**2 for x,y in zip(a,b)),length**2)
            self.assertEqual(data['assembly_target_mm'],[length,5,5])
            self.assertEqual(data['physical_acceptance'],'unmeasured')
            self.assertGreaterEqual((length-data['fuse_body_length_nominal_mm'])/2-data['solder_overlap_target_mm'],data['body_to_solder_clearance_target_mm'])
            self.assertEqual(data['hand_solder_iron_c'],{'target':350,'tolerance':5,'maximum_heating_seconds':5})

    def test_fuse_substitutions_and_smaller_finished_spaces_require_review(self):
        original=json.loads((branch_fuses.HERE/'electrical-design.json').read_text())
        for name in branch_fuses.PARTS:
            for key,value in (('part','unreviewed substitute'),('loaded_envelope_mm',[20,4,4]),('source_revision','old source')):
                electrical=copy.deepcopy(original);electrical['parts'][name][key]=value
                with self.subTest(name=name,key=key),self.assertRaisesRegex(ValueError,'changed branch fuse'):
                    branch_fuses.geometry(electrical=electrical)

    def test_undeclared_enclosure_design_fails(self):
        with self.assertRaisesRegex(ValueError,'carrier design'):branch_fuses.geometry('other')


if __name__=='__main__':unittest.main()
