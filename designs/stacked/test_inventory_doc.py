"""Generated inventory must preserve the surrounding design and raw decisions."""
import unittest
import inventory_doc


class InventoryDocumentTests(unittest.TestCase):
    def parts(self):
        mass={'complete_pendant':{'nominal_g':1000},'necklace':{'nominal_g':5},
              'total_worn':{'nominal_g':1005,'range_g':[900,1133.98092]},
              'margin_g':.000005,'margin_target_pass':False}
        return {'mass_estimate':mass,'dimensions_mm':{'diameter':200,'body_depth':60.6,'closed_width':200,'closed_height':200,'closed_depth':80.6},
                'material_variants':{key:{'mass_estimate':mass,'components':[
                  {'label':'one cell','installed_quantity':1,'mass_g_per_unit':72,'mass_range_g_per_unit':[68,76],'mass_basis':'published upper; physical result unmeasured'}]} for key in ('glow','silver')}}

    def test_replaces_only_owned_block_and_keeps_separate_margin_target(self):
        before='Firmware and protocol stay intact.\n';after='\nUnchanged optical coefficients.\n'
        text=before+inventory_doc.BEGIN+'old wide rows'+inventory_doc.END+after
        result=inventory_doc.update(text,self.parts())
        self.assertTrue(result.startswith(before+inventory_doc.BEGIN))
        self.assertTrue(result.endswith(inventory_doc.END+after))
        self.assertNotIn('old wide rows',result)
        self.assertIn('1133.980925g',result)
        self.assertIn('not met',result)
        self.assertIn('not confidence intervals',result)
        self.assertIn('Physical fit, strength, heat, electrical recovery and worn mass remain unmeasured.',result)
        self.assertEqual(result.count('| one cell |'),1)

    def test_missing_or_duplicate_ownership_markers_reject_publication(self):
        for text in ('no block',inventory_doc.BEGIN+inventory_doc.END+inventory_doc.END):
            with self.subTest(document=text),self.assertRaises(ValueError):inventory_doc.update(text,self.parts())

if __name__=='__main__':unittest.main()
