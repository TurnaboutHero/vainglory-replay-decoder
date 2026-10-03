import contextlib
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.product_report_cases import ReportCase, assert_report_failures, assert_report_happy, run_report, write_replay
from vg.core.truth_input import TruthInputError
from vg.decoder_v2 import truth_audit, truth_capture_pack, truth_inventory, truth_labeling_queue, truth_source_priority, truth_stubs
from vg.decoder_v2.report_inputs import load_research_truth, require_truth_match


class ProductTruthResearch(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.base = self.root / 'replays'
        self.covered = write_replay(self.base, 'covered')
        self.uncovered = write_replay(self.base, 'uncovered')
        self.image = self.base / 'result.png'
        self.image.write_bytes(b'metadata fixture, not decoded pixels')
        self.manifest = self.base / 'replayManifest-uncovered.txt'
        self.manifest.write_text('11111111-1111-1111-1111-111111111111-22222222-2222-2222-2222-222222222222')
        self.truth, self.ocr = self.root / 'truth.json', self.root / 'ocr.json'
        match = {'replay_name': 'covered', 'replay_file': str(self.covered), 'players': {'PlayerOne': {'kills': 0, 'gold': None}}}
        self.truth.write_text(json.dumps({'matches': [match, {'replay_name': 'truth_only', 'replay_file': r'C:\missing\truth.0.vgr'}]}))
        self.ocr.write_text(json.dumps({'matches': [match, {'replay_name': 'ocr_only', 'replay_file': r'C:\missing\ocr.0.vgr'}]}))
        all_sources = (self.truth, self.covered, self.covered.with_name('covered.1.vgr'),
                       self.uncovered, self.uncovered.with_name('uncovered.1.vgr'), self.image, self.manifest)
        args = ('--base', str(self.base), '--truth', str(self.truth))
        self.cases = [ReportCase(module, builder, args, all_sources, (self.covered, self.uncovered), self.root / 'report.json')
                      for module, builder in ((truth_inventory, 'build_truth_inventory'), (truth_stubs, 'build_truth_stub_report'),
                                              (truth_capture_pack, 'build_truth_capture_pack'), (truth_labeling_queue, 'build_truth_labeling_queue'),
                                              (truth_source_priority, 'build_truth_source_priority'))]
        self.cases.append(ReportCase(truth_audit, 'audit_truth', ('--truth', str(self.truth), '--ocr', str(self.ocr)),
                                    (self.truth, self.ocr, self.covered, self.covered.with_name('covered.1.vgr')),
                                    (self.covered,), self.root / 'report.json'))

    def test_research_happy(self) -> None:
        for case in self.cases:
            with self.subTest(module=case.module.__name__):
                assert_report_happy(self, case)
        inventory = truth_inventory.build_truth_inventory(str(self.base), str(self.truth))
        self.assertEqual((inventory['total_families'], inventory['covered_families'], inventory['missing_families']), (2, 1, 1))
        self.assertEqual(inventory['total_replay_directories'], 1)
        self.assertEqual(inventory['schema_version'], 'decoder_v2.truth_inventory.v2')
        stubs = truth_stubs.build_truth_stub_report(str(self.base), str(self.truth))['stubs']
        self.assertEqual(len(stubs), 1)
        self.assertEqual(stubs[0]['manifest']['manifest_path'], str(self.manifest))
        pack = truth_capture_pack.build_truth_capture_pack(str(self.base), str(self.truth))
        item = pack['items'][0]
        self.assertIsNone(item['truth_stub']['match_info']['winner'])
        self.assertFalse(item['queue_entry']['withheld_fields']['winner']['accepted_for_index'])
        self.assertNotIn('winner_accepted', item['queue_entry']['priority_tags'])
        self.assertNotIn('kda_accepted', item['queue_entry']['priority_tags'])
        self.assertNotIn('winner/KDA already accepted', item['capture_reason'])
        self.assertNotIn('accepted winner/KDA', item['capture_reason'])
        complete_reason = truth_capture_pack._capture_reason({**item['queue_entry'],
                            'completeness_status': 'complete_confirmed', 'game_mode': 'GameMode_5v5_Ranked'})
        self.assertNotIn('winner/KDA already accepted', complete_reason)
        self.assertNotIn('accepted winner/KDA', complete_reason)
        self.assertEqual(truth_audit.audit_truth(str(self.truth), str(self.ocr))['audited_matches'], 1)

    def test_research_failure(self) -> None:
        for case in self.cases:
            with self.subTest(module=case.module.__name__):
                assert_report_failures(self, case)
        original = self.truth.read_bytes()
        for malformed in (b'{', b'[]', b'{"matches":[{"players":[]}]}'):
            self.truth.write_bytes(malformed)
            for case in self.cases:
                with self.subTest(module=case.module.__name__, malformed=malformed), patch(f'{case.module.__name__}.{case.builder}') as builder:
                    self.assertEqual(run_report(case, case.output).code, 2)
                    builder.assert_not_called()
        self.truth.write_bytes(original)
        self.ocr.write_text('{"matches":[{"replay_name":"covered","players":[]}]}')
        with patch('vg.decoder_v2.truth_audit.decode_match') as decode:
            self.assertEqual(run_report(self.cases[-1], self.root / 'report.json').code, 2)
            decode.assert_not_called()
        with self.assertRaises(TruthInputError) as error:
            require_truth_match(load_research_truth(self.truth), self.truth, 'absent')
        self.assertEqual(error.exception.code, 'truth_no_match')

    def test_manifest_ambiguity_and_exact_association(self) -> None:
        self.manifest.rename(self.base / 'replayManifest-unrelated.txt')
        (self.base / 'replayManifest-other.txt').write_text('unrelated content')
        result = truth_stubs.build_truth_stub_report(str(self.base), str(self.truth))['stubs'][0]
        self.assertIsNone(result['manifest'])
        self.assertEqual(result['manifest_reason'], 'manifest_ambiguous')
        self.manifest.write_text('exact manifest')
        with patch('vg.decoder_v2.truth_stubs.parse_replay_manifest', wraps=truth_stubs.parse_replay_manifest) as parse:
            result = truth_stubs.build_truth_stub_report(str(self.base), str(self.truth))['stubs'][0]
        parse.assert_called_once_with(str(self.manifest))
        self.assertEqual(result['manifest_reason'], 'exact_family_association')

    def test_nested_duplicate_names_and_metadata_filtering(self) -> None:
        write_replay(self.base / 'nested', 'covered')
        write_replay(self.base / '__MACOSX', 'hidden')
        (self.base / '._noise.0.vgr').write_bytes(b'ignored')
        report = truth_inventory.build_truth_inventory(str(self.base), str(self.truth))
        self.assertEqual((report['total_families'], report['covered_families']), (3, 1))
        self.assertEqual(len({row['replay_file'] for row in report['covered'] + report['missing']}), 3)

    def test_missing_explicit_roots_and_duplicate_selectors(self) -> None:
        for case in self.cases[:-1]:
            args = tuple(str(self.root / 'missing') if value == str(self.base) else value for value in case.args)
            missing = ReportCase(case.module, case.builder, args, case.sources, case.replays, case.output)
            self.assertEqual(run_report(missing, case.output).code, 2)
        rows = [{'replay_name': 'same', 'replay_file': 'a.0.vgr'}, {'replay_name': 'same', 'replay_file': 'b.0.vgr'}]
        with self.assertRaises(TruthInputError) as error:
            require_truth_match(rows, self.truth, 'same')
        self.assertEqual(error.exception.code, 'truth_ambiguous')

    def test_windows_inventory_coverage_uses_canonical_scoped_keys(self) -> None:
        references = [r'C:\Replay Library\SeriesA\match.0.vgr',
                      r'\\Server\Share\SeriesB\match.0.vgr',
                      r'C:\Replay Library\SeriesC\match.0.vgr']
        rows = [{'directory': reference.rsplit('\\', 1)[0], 'replay_file': reference,
                 'replay_name': 'match', 'replay_file_count': 1,
                 'has_result_image': False, 'has_manifest': False} for reference in references]
        self.truth.write_text(json.dumps({'matches': [
            {'replay_name': 'match', 'replay_file': 'c:/replay library/seriesa/MATCH.0.VGR'},
            {'replay_name': 'match', 'replay_file': '//server/share/seriesb/MATCH.0.VGR'},
        ]}))
        before = hashlib.sha256(self.truth.read_bytes()).hexdigest()
        with patch.object(truth_inventory, 'scan_replay_directories', return_value=rows), patch.object(
            Path, 'read_bytes', side_effect=AssertionError('Metadata inventory must not open replay bytes')
        ):
            report = truth_inventory.build_truth_inventory(str(self.base), str(self.truth))
        self.assertEqual((report['total_families'], report['covered_families'], report['missing_families']), (3, 2, 1))
        self.assertEqual([row['replay_file'] for row in report['covered']], references[:2])
        self.assertEqual([row['replay_file'] for row in report['missing']], references[2:])
        after = hashlib.sha256(self.truth.read_bytes()).hexdigest()
        self.assertEqual(after, before)
        print(json.dumps({'scenario': 'windows_metadata_identity', 'covered': references[:2],
                          'missing': references[2:], 'truth_sha256_before': before, 'truth_sha256_after': after}))


if __name__ == '__main__':
    unittest.main()
