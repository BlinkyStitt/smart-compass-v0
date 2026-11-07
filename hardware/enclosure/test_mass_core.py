import itertools
import math
import unittest
from mass_core import WORN_LIMIT_G,totals,balance,coordinate_extreme


def row(name,mass,group='pendant',quantity=1,position=None):
    return {'id':name,'group':group,'installed_quantity':quantity,'mass_g_per_unit':mass,
            'mass_range_g_per_unit':[mass,mass],'mass_centre_mm':position or [0,-10,5]}


class MassArithmeticTests(unittest.TestCase):
    def test_raw_ceiling_decision_precedes_display_rounding(self):
        for delta,expected in [(-.00001,True),(0,True),(.00001,False)]:
            rows=[row('case',WORN_LIMIT_G-76-10+delta),row('cell',76),row('necklace',10,'necklace')]
            result=totals(rows)
            self.assertEqual(result['ceiling_pass'],expected)
            self.assertAlmostEqual(result['margin_g'],-delta,places=10)

    def test_each_installed_part_and_necklace_enters_once(self):
        rows=[row('case',100),row('cell',76),row('contacts',.5,quantity=2),row('necklace',10,'necklace'),row('charger',200,'tool')]
        self.assertEqual(totals(rows)['upper_worn_g'],187)
        for r in rows[:-1]:
            old=totals(rows)['upper_worn_g'];r['installed_quantity']+=1
            self.assertEqual(totals(rows)['upper_worn_g']-old,r['mass_g_per_unit']);r['installed_quantity']-=1
        rows[-1]['installed_quantity']=10
        self.assertEqual(totals(rows)['upper_worn_g'],187)

    def test_duplicate_or_invalid_rows_fail(self):
        with self.assertRaises(ValueError):totals([row('cell',76),row('cell',76)])
        for bad in (0,-1,math.nan,math.inf,True):
            with self.subTest(value=bad),self.assertRaises(ValueError):totals([row('bad',bad)])

    def test_center_extrema_match_every_brute_force_corner(self):
        items=[([x,x/2,z],a,b) for x,z,a,b in [(-30,1,2,4),(10,20,5,9),(4,12,1,6),(-3,-2,8,10),(20,4,3,7)]]
        for axis in range(3):
            corners=[sum(p[axis]*m for (p,_,_),m in zip(items,masses))/sum(masses)
                     for masses in itertools.product(*[(a,b) for _,a,b in items])]
            self.assertAlmostEqual(coordinate_extreme(items,axis,True),min(corners),places=12)
            self.assertAlmostEqual(coordinate_extreme(items,axis,False),max(corners),places=12)

    def test_necklace_weight_does_not_move_pendant_center(self):
        rows=[row('left',10,position=[-5,-10,4]),row('right',10,position=[5,-10,6]),row('neck',100,'necklace',position=[0,100,0])]
        result=balance(rows,[[-20,50,2],[20,50,2]])
        self.assertEqual(result['centre_mm'],[0,-10,5])
        self.assertEqual(result['left_right_load_fraction'],[.5,.5])
        self.assertTrue(result['positive_two_point_support_for_mass_range'])

    def test_missing_center_and_unstable_hanging_are_visible(self):
        data=row('wrong',20,position=[30,60,4])
        result=balance([data],[[-20,50,2],[20,50,2]])
        self.assertFalse(result['positive_two_point_support_for_mass_range'])
        self.assertIsNone(result['nominal_tilt_deg'])
        del data['mass_centre_mm']
        with self.assertRaises(ValueError):balance([data],[[-20,50,2],[20,50,2]])

if __name__=='__main__':unittest.main()
