"""Top-side PTH exit contract; native source-body fit remains a separate check."""
import copy,json,math,unittest
from pathlib import Path
from unittest.mock import patch
import blackpill_sense,harness_plan,harness_ports,ring_harness

class TopPortTests(unittest.TestCase):
    def test_new_supports_preserve_the_source_side_window(self):
        p=harness_plan.parameters();inner,bottom,top=ring_harness.side_window(p)
        self.assertAlmostEqual(inner,93.16784829954798)
        self.assertEqual((bottom,top),(14,34))
        changed=copy.deepcopy(p);changed['side_bottom_z']+=1
        self.assertEqual(ring_harness.side_window(changed),(inner,bottom+1,top+1))

    def test_inner_passage_tracks_the_whole_formed_joint(self):
        ports=harness_plan.definition()['ports'];top=ring_harness.inner_passage_top(ports)
        for pin,row in ports.items():
            if not pin.startswith('RING1.'):continue
            for point in row['joint_path_points_mm']:
                self.assertGreaterEqual(top-point[2]-row['joint_diameter_target_mm']/2
                                        -ring_harness.JOINT_ENVELOPE_ALLOWANCE_MM,.25)
        # Interface perturbation only, not assembly evidence. An unchanged
        # jacket endpoint must not hide a higher formed joint.
        changed=copy.deepcopy(ports)
        for point in changed['RING1.5V']['joint_path_points_mm'][:-1]:point[2]+=2
        self.assertAlmostEqual(ring_harness.inner_passage_top(changed),top+2)
        self.assertEqual(changed['RING1.5V']['wire_end_mm'],ports['RING1.5V']['wire_end_mm'])

    def test_sense_fixture_owns_capacitor_joint_coordinates(self):
        # Interface regression only. This altered input is not fit evidence.
        p=harness_plan.parameters();before=harness_ports.terminals(p)
        source=blackpill_sense.source_ports()
        for pin in ['C_SENSE.1','C_SENSE.2']:source[pin][0]+=3
        with patch.object(blackpill_sense,'source_ports',return_value=source):
            after=harness_ports.terminals(p)
        for pin,row in before.items():
            if pin.startswith('C_SENSE.'):
                for key in ['terminal_mm','wire_end_mm']:
                    delta=[b-a for a,b in zip(row[key],after[pin][key])]
                    for actual,target in zip(delta,[0,3,0]):self.assertAlmostEqual(actual,target)
                self.assertEqual(row['axis'],after[pin]['axis'])
                self.assertEqual(row['strip_mm'],after[pin]['strip_mm'])
            else:self.assertEqual(row,after[pin])

    def test_selected_bare_module_leads_exit_component_face(self):
        p=harness_plan.parameters();ports=harness_ports.terminals(p);entries={e['name']:e for e in p['electronics']}
        for prefix,name in [('IMU.','IMU'),('GPS.','GPS'),('BLACKPILL.','BlackPill'),('RADIO.','Radio'),('SPARKLE.','SparkleMotion')]:
            rows=[row for pin,row in ports.items() if pin.startswith(prefix) and row['kind']=='solder']
            self.assertTrue(rows,prefix)
            thickness=1.57 if name in ['GPS','SparkleMotion'] else 1.6
            for row in rows:
                self.assertEqual(row['axis'],[0,0,1])
                self.assertAlmostEqual(row['terminal_mm'][2],entries[name]['pcb_bottom_z_mm']+thickness)
                self.assertAlmostEqual(row['wire_end_mm'][2]-row['terminal_mm'][2],.8)
                self.assertAlmostEqual(row['barrel_mm'],thickness)
                self.assertAlmostEqual(row['barrel_mm']+row['far_face_projection_mm']+row['joint_length_mm'],row['strip_mm'])
                self.assertGreaterEqual(row['far_face_projection_mm'],0)
        for pin in ['5V','DIN','GND']:
            self.assertEqual(ports['FIBONACCI.'+pin]['axis'],[0,0,-1])
            self.assertEqual(ports['FIBONACCI.'+pin]['terminal_mm'][2],p['circle_back_z'])

    def test_rim_passages_reject_nonfinite_bool_or_reversed_coordinates(self):
        original=ring_harness.rim_passages()
        for bad in [True,float('nan'),float('inf'),'12']:
            record=copy.deepcopy(original);record['openings'][0]['bounds_mm'][0][0]=bad
            with self.subTest(value=bad),patch.object(Path,'read_text',return_value=json.dumps(record)),self.assertRaisesRegex(ValueError,'Invalid rim'):ring_harness.rim_passages()
        record=copy.deepcopy(original);record['openings'][0]['bounds_mm'][0].reverse()
        with patch.object(Path,'read_text',return_value=json.dumps(record)),self.assertRaisesRegex(ValueError,'Invalid rim'):ring_harness.rim_passages()

if __name__=='__main__':unittest.main()
