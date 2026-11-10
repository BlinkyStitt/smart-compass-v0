"""Check complete fitted-part separation against the current exported CAD."""
import json
from pathlib import Path
import unittest
from explosion import BOARDS, REFERENCES, layout


class ExplosionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.metadata = json.loads((Path(__file__).resolve().parents[1] / 'designs/stacked/exports/scene.json').read_text())
        cls.plan = layout(cls.metadata)

    def test_every_cad_part_appears_once_and_moves(self):
        names = [name for unit in self.plan['units'] for name in unit['parts']]
        self.assertEqual(sorted(names), sorted(p['name'] for p in self.metadata['parts'] if p['name'] not in REFERENCES))
        self.assertEqual(len(names), len(set(names)))
        self.assertTrue(all(sum(x * x for x in unit['offset']) > .000001 for unit in self.plan['units']))

    def test_only_soldered_board_parts_share_a_move(self):
        boards = {name: list(parts) for name, parts in BOARDS}
        for unit in self.plan['units']:
            self.assertEqual(unit['parts'], boards.get(unit['name'], [unit['name']]))

    def test_no_components_overlap_in_the_open_view(self):
        units = self.plan['units']
        for i, a in enumerate(units):
            for b in units[i + 1:]:
                ar, br = a['target'], b['target']
                self.assertFalse(ar[0] < br[2] and br[0] < ar[2] and ar[1] < br[3] and br[1] < ar[3],
                                 f"{a['name']} obscures {b['name']}")

    def test_each_component_has_a_framed_detail_view(self):
        for unit in self.plan['units']:
            view = next(v for v in self.plan['views'] if v['label'] == unit['category'])['bounds']
            rect = unit['target']
            self.assertTrue(view[0] < rect[0] < rect[2] < view[2])
            self.assertTrue(view[1] < rect[1] < rect[3] < view[3])

    def test_capture_manifest_rejects_old_movie_layout_or_sources(self):
        from explosion import capture_record, verify_capture
        inputs = {'scene': 'current', 'capture': 'current'}
        proof = capture_record(self.plan, 'current-movie', inputs)
        verify_capture(proof, self.metadata, 'current-movie', inputs)
        for changes in ({'movie_hash': 'old-movie'}, {'inputs': {'scene': 'old'}}):
            with self.subTest(changes=changes), self.assertRaisesRegex(RuntimeError, 'Assembly recording is stale'):
                verify_capture(proof, self.metadata, changes.get('movie_hash', 'current-movie'),
                               changes.get('inputs', inputs))
        incomplete = {**proof, 'fitted_cad_parts': proof['fitted_cad_parts'] - 1}
        with self.assertRaisesRegex(RuntimeError, 'complete fitted-part coverage'):
            verify_capture(incomplete, self.metadata, 'current-movie', inputs)
