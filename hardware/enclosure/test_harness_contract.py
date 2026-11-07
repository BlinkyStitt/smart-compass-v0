"""Synthetic contract perturbations. These are not assembly fit evidence."""
import copy,unittest
import harness_contract as contract
import harness_route

class HarnessContractTests(unittest.TestCase):
    def setUp(self):
        self.wire={'id':'W001','net':'B','ends':['A','B'],'wire_group':'main','stock':'selected18AWG','maximum_od_mm':2,'strip_ends_mm':[3,4],'blank_trim_allowance_mm':20}
        self.plan={'wires':[self.wire],'ports':{'A':{'wire_end_mm':[0.0,0,0],'axis':[1,0,0]},'B':{'wire_end_mm':[30,0,0],'axis':[-1,0,0]}},'splices':{},'insulated_unused_terminals':['S1.6']}
        self.record={'definition_sha256':contract.fingerprint(self.plan),'routes':{'W001':harness_route.cut_record(self.wire,[[0,0,0],[30,0,0]],6)},'splices':{},'insulated_unused_terminals':['S1.6'],'physical_acceptance':'unmeasured'}

    def test_complete_raw_cut_contract(self):
        self.assertEqual(contract.validate(self.record,self.plan)['finished_wire_m'],.037)

    def test_libm_roundoff_does_not_change_definition_or_cut_binding(self):
        changed=copy.deepcopy(self.plan);changed['ports']['A']['wire_end_mm'][0]=1e-13
        self.assertEqual(contract.fingerprint(changed),contract.fingerprint(self.plan))
        self.record['routes']['W001']['strip_ends_mm']=[3+1e-13,4-1e-13]
        contract.validate(self.record,self.plan)
        self.record['routes']['W001']['strip_ends_mm'][0]+=.0001
        with self.assertRaisesRegex(ValueError,'binding/stock'):contract.validate(self.record,self.plan)

    def test_missing_wire_cannot_pass(self):
        self.record['routes'].clear()
        with self.assertRaisesRegex(ValueError,'Missing'):contract.validate(self.record,self.plan)

    def test_changed_stock_endpoint_or_cut_cannot_pass(self):
        for name,value in [('stock','smaller wire'),('points_mm',[[1,0,0],[30,0,0]]),('finished_cut_target_mm',30),('bend_radius_target_mm',5.9)]:
            record=copy.deepcopy(self.record);record['routes']['W001'][name]=value
            with self.subTest(name=name),self.assertRaises(ValueError):contract.validate(record,self.plan)

    def test_terminal_and_net_definition_changes_invalidate_routes(self):
        self.plan['ports']['A']['wire_end_mm'][0]=.1
        with self.assertRaisesRegex(ValueError,'definition changed'):contract.validate(self.record,self.plan)

    def test_cap_and_physical_boundary_required(self):
        self.record['insulated_unused_terminals']=[]
        with self.assertRaisesRegex(ValueError,'insulation'):contract.validate(self.record,self.plan)
        self.record['insulated_unused_terminals']=['S1.6'];self.record['physical_acceptance']='pass'
        with self.assertRaisesRegex(ValueError,'physical'):contract.validate(self.record,self.plan)

if __name__=='__main__':unittest.main()
