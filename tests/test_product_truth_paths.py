import json
import os
from pathlib import Path
import tempfile
import unittest

from vg.core.truth_input import TruthInputError, load_truth_matches, select_truth_match
from vg.decoder_v2.report_inputs import load_research_truth, truth_reference_key, truth_replay_files


class ProductTruthPathTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name).resolve()
        self.truth = self.root / 'truth.json'
        self.replay = self.root / 'a' / 'match.0.vgr'
        self.replay.parent.mkdir()
        self.replay.write_bytes(b'replay-source')

    def write_truth(self, reference):
        self.truth.write_text(json.dumps({'replay_name': 'match', 'replay_file': reference}), encoding='utf-8')

    def test_forward_relative_reference_resolves_against_truth_parent(self):
        self.write_truth('a/match.0.vgr')
        rows = load_research_truth(self.truth)
        self.assertEqual(Path(rows[0]['replay_file']), self.replay)
        self.assertEqual(truth_replay_files(rows, self.truth), (self.replay,))
        self.assertEqual(truth_reference_key('a/match.0.vgr', self.truth), truth_reference_key(str(self.replay), self.truth))
        self.assertEqual(select_truth_match(load_truth_matches(self.truth), self.truth, replay_file=self.replay)['replay_name'], 'match')
        self.assertEqual(rows[0]['players'], {})
        self.assertEqual(rows[0]['match_info'], {})

    def test_backslash_relative_reference_uses_native_platform_semantics(self):
        reference = 'a\\match.0.vgr'
        self.write_truth(reference)
        rows = load_research_truth(self.truth)
        if os.name == 'nt':
            self.assertEqual(Path(rows[0]['replay_file']), self.replay)
            self.assertEqual(truth_replay_files(rows, self.truth), (self.replay,))
            self.assertEqual(truth_reference_key(reference, self.truth), truth_reference_key(str(self.replay), self.truth))
            self.assertEqual(select_truth_match(load_truth_matches(self.truth), self.truth, replay_file=self.replay)['replay_name'], 'match')
            self.truth.write_text(json.dumps({'matches': [{'replay_file': reference}, {'replay_file': str(self.replay).upper()}]}), encoding='utf-8')
            with self.assertRaisesRegex(TruthInputError, 'truth_ambiguous'):
                load_truth_matches(self.truth)
        else:
            self.assertEqual(rows[0]['replay_file'], reference)
            with self.assertRaisesRegex(TruthInputError, 'truth_unreadable'):
                truth_replay_files(rows, self.truth)

    def test_windows_absolute_metadata_keys_preserve_scope(self):
        for reference in ('Z:\\Archive\\Match.0.vgr', '\\\\server\\share\\Archive\\Match.0.vgr'):
            with self.subTest(reference=reference):
                self.write_truth(reference)
                rows = load_research_truth(self.truth)
                self.assertEqual(rows[0]['replay_file'], reference)
                self.assertEqual(truth_reference_key(reference, self.truth), truth_reference_key(reference.replace('\\', '/').lower(), self.truth))
                self.assertEqual(select_truth_match(load_truth_matches(self.truth), self.truth, replay_file=reference.replace('\\', '/').lower())['replay_name'], 'match')
                if os.name != 'nt':
                    with self.assertRaisesRegex(TruthInputError, 'truth_unreadable'):
                        truth_replay_files(rows, self.truth)

    def test_explicit_invalid_players_remain_invalid(self):
        self.truth.write_text(json.dumps({'replay_file': 'a/match.0.vgr', 'players': []}), encoding='utf-8')
        with self.assertRaisesRegex(TruthInputError, 'truth_invalid'):
            load_research_truth(self.truth)


if __name__ == '__main__':
    unittest.main()
