"""One datum owns each source board; stale dimensions cannot mask its envelope."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import antenna
import geometry

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('source_board_compact_layout',ROOT/'designs/stacked/layout.py')
compact=importlib.util.module_from_spec(spec);spec.loader.exec_module(compact)

class SourceBoardParameterTests(unittest.TestCase):
    def test_radio_feed_uses_narrow_pcb_z_and_source_datum(self):
        data=compact.parameters();route=antenna.installation(data,True)
        for actual,target in zip(route.feed,(51.936,6.906,8)):self.assertAlmostEqual(actual,target)
        self.assertEqual(route.restraints,(13.5,50))
        radio=next(row for row in data['electronics'] if row['name']=='Radio')
        self.assertEqual(radio['z'],5.9)
        radio['z']=8
        with self.assertRaisesRegex(ValueError,'Radio resolved'):compact.validate(data)

    def test_compact_rejects_legacy_envelope_and_resolved_datum_drift(self):
        raw=json.loads((ROOT/'designs/stacked/parameters.json').read_text())
        next(row for row in raw['electronics'] if row['name']=='GPS')['size']=[22.86,50.8,8]
        with tempfile.TemporaryDirectory() as temporary:
            folder=Path(temporary);(folder/'parameters.json').write_text(json.dumps(raw))
            with patch.object(compact,'HERE',folder),self.assertRaisesRegex(ValueError,'source-fixture derived'):compact.parameters()
        data=compact.parameters();compact.validate(data)
        board=next(row for row in data['electronics'] if row['name']=='BlackPill')
        self.assertEqual(board['centre'],[-27,5.8]);self.assertEqual(board['z'],7)
        self.assertEqual(board['size'][2],13)
        board['z']=8
        with self.assertRaisesRegex(ValueError,'BlackPill resolved'):compact.validate(data)
        data=compact.parameters()
        next(row for row in data['electronics'] if row['name']=='SparkleMotion')['centre'][0]+=.1
        with self.assertRaisesRegex(ValueError,'source datum'):compact.validate(data)

if __name__=='__main__':unittest.main()
