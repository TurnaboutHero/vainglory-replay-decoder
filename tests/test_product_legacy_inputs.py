import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.product_report_cases import write_replay
from tests.test_product_duration_provenance import replay_bytes
from vg.analysis import final_screen_comparison
from vg.core.batch_result import PartialBatchError
from vg.core.replay_extractor import ReplayExtractor
from vg.core.unified_decoder import UnifiedDecoder
from vg.core.vgr_parser import VGRParser, scan_replay_folders


class ProductLegacyInputs(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.replay = write_replay(self.root / 'nested' / 'selected', 'sample')
        self.replay.write_bytes(replay_bytes())
        self.replay.with_name('sample.1.vgr').write_bytes(replay_bytes())
        self.truth = self.root / 'explicit.json'
        self.truth.write_text(json.dumps({'replay_name': 'sample', 'players': {},
                                        'match_info': {'duration_seconds': 0}}))

    def command(self, module, path, *args, cwd=None):
        environment = os.environ | {'PYTHONPATH': str(Path(__file__).resolve().parents[1])}
        return subprocess.run([sys.executable, '-B', '-m', module, str(path), *map(str, args)],
                              cwd=cwd or self.root, env=environment, capture_output=True, text=True)

    def test_legacy_inputs_happy(self):
        write_replay(self.root / 'outside', 'other')
        for module in ('vg.core.vgr_parser', 'vg.core.replay_extractor', 'vg.core.unified_decoder'):
            result = self.command(module, self.root / 'nested')
            self.assertEqual(result.returncode, 0, result.stderr)
            value = json.loads(result.stdout)
            self.assertEqual(Path(value.get('replay_file', value.get('replay_path'))), self.replay)
            self.assertEqual(value.get('total_frames', value.get('frame_count')), 2)
        row = {'replay_name': 'sample', 'players': {}, 'match_info': {'duration_seconds': 0}}
        for envelope in (row, {'matches': [row]}, {'matches': {'sample': row}}):
            self.truth.write_text(json.dumps(envelope))
            self.assertEqual(VGRParser(str(self.replay), truth_path=str(self.truth)).parse()
                             ['match_info']['duration_seconds'], 0)
            self.assertEqual(ReplayExtractor(str(self.replay)).extract_with_truth(str(self.truth)).duration_seconds, 0)
            self.assertEqual(UnifiedDecoder(str(self.replay)).decode_with_truth(str(self.truth)).duration_seconds, 0)
        markdown = self.root / 'MATCH_DATA_sample.md'
        markdown.write_text('0분 0초\n## Blue Team\n| PlayerOne | Inara | 0 | 0 | 0 | 0 | 0 |\n')
        for loader in (lambda: VGRParser(str(self.replay), truth_path=str(markdown)).parse()['truth_source'],
                       lambda: ReplayExtractor(str(self.replay)).extract_with_truth(str(markdown)).truth_source,
                       lambda: UnifiedDecoder(str(self.replay)).decode_with_truth(str(markdown)).duration_provenance['source']):
            self.assertEqual(loader(), str(markdown))
        result = self.command('vg.core.vgr_parser', self.replay)
        self.assertEqual(result.returncode, 0, result.stderr)
        value = json.loads(result.stdout)
        self.assertEqual(value['truth_source'], str(markdown))
        self.assertEqual(value['truth_provenance']['status'], 'supplied_truth')
        self.assertTrue(value['truth_provenance']['attempts'])
        output = self.root / 'report.json'
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in (self.replay, self.truth, markdown)}
        result = self.command('vg.core.vgr_parser', self.replay, '-o', output)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(output.read_text())['replay_name'], 'sample')
        self.assertEqual(before, {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in before})

    def test_legacy_inputs_failure(self):
        bad = self.root / 'bad.0.vgr'
        empty = self.root / 'empty.0.vgr'
        bad.write_bytes(b'random bytes')
        empty.touch()
        invalid = (self.root / 'missing', bad, empty, self.replay.with_name('sample.1.vgr'), self.root)
        for module in ('vg.core.vgr_parser', 'vg.core.replay_extractor', 'vg.core.unified_decoder'):
            for path in invalid:
                with self.subTest(module=module, path=path):
                    result = self.command(module, path)
                    self.assertEqual(result.returncode, 2, result)
                    self.assertIn(str(path), result.stderr)
                    self.assertNotIn('Traceback', result.stderr)
                    self.assertEqual(result.stdout, '')
            for payload in ('{', '[]', '{"matches":[{"replay_name":"other"}]}'):
                self.truth.write_text(payload)
                truth_args = (str(self.truth),) if module.endswith('replay_extractor') else ('--truth', str(self.truth))
                result = self.command(module, self.replay, *truth_args)
                self.assertEqual(result.returncode, 2, result)
                self.assertIn(str(self.truth), result.stderr)
                self.assertNotIn('Traceback', result.stderr)
        self.truth.write_text('{"replay_name":"sample","players":{}}')
        automatic = self.root / 'MATCH_DATA_sample.md'
        automatic.write_text('0분 0초\n## Blue Team\n| PlayerOne | Inara | 0 | 0 | 0 | 0 | 0 |\n')
        linked = self.root / 'section.json'
        os.link(self.replay, linked)
        future = self.replay.with_name('sample.999.vgr')
        for module in ('vg.core.vgr_parser', 'vg.core.unified_decoder'):
            for output in (self.truth, linked, future):
                before = self.replay.read_bytes(), self.truth.read_bytes()
                result = self.command(module, self.replay, '--truth', self.truth, '-o', output)
                self.assertEqual(result.returncode, 2, result)
                self.assertNotIn('Traceback', result.stderr)
                self.assertEqual(before, (self.replay.read_bytes(), self.truth.read_bytes()))
            self.assertFalse(future.exists())
        original = automatic.read_bytes()
        result = self.command('vg.core.vgr_parser', self.replay, '-o', automatic)
        self.assertEqual(result.returncode, 2, result)
        self.assertEqual(automatic.read_bytes(), original)

    def test_legacy_inputs_failure_scan_is_accounted(self):
        (self.root / 'bad.0.vgr').write_bytes(b'not a replay')
        with self.assertRaises(PartialBatchError) as error:
            scan_replay_folders(str(self.root), auto_truth=False)
        self.assertEqual(error.exception.report['discovered'], 2)
        self.assertEqual(error.exception.report['failed'], 1)
        result = self.command('vg.core.vgr_parser', self.root, '--batch', '--no-auto-truth')
        self.assertEqual(result.returncode, 1, result)
        self.assertEqual(json.loads(result.stdout)['failed'], 1)

    def test_legacy_inputs_happy_scoped_truth_and_metadata(self):
        other = write_replay(self.root / 'other', 'sample')
        rows = [{'replay_name': 'sample', 'replay_file': str(path),
                 'match_info': {'duration_seconds': value}, 'players': {}}
                for path, value in ((self.replay, 7), (other, 42))]
        self.truth.write_text(json.dumps({'matches': rows}))
        self.assertEqual(VGRParser(str(self.replay), truth_path=str(self.truth)).parse()
                         ['match_info']['duration_seconds'], 7)
        self.assertEqual(ReplayExtractor(str(self.replay)).extract_with_truth(str(self.truth)).duration_seconds, 7)
        self.assertEqual(UnifiedDecoder(str(self.replay)).decode_with_truth(str(self.truth)).duration_seconds, 7)
        self.assertEqual(VGRParser(str(other), auto_truth=False).parse()['frame_count'], 2)
        self.assertEqual(ReplayExtractor(str(other)).extract().total_frames, 2)
        (self.root / 'truth-invalid.json').write_text('{')
        result = self.command('vg.core.vgr_parser', self.replay)
        self.assertEqual(result.returncode, 0, result.stderr)
        provenance = json.loads(result.stdout)['truth_provenance']
        self.assertEqual(provenance['status'], 'unmatched_automatic')
        self.assertEqual(provenance['attempts'][0]['status'], 'truth_invalid')

    def test_legacy_inputs_failure_truth_changes_during_parse(self):
        original = VGRParser._apply_truth_data

        def change_truth(parser, truth, players, info):
            original(parser, truth, players, info)
            self.truth.write_text('{"replay_name":"sample","players":{},"changed":true}')

        output = self.root / 'prior.json'
        output.write_text('prior report')
        with patch.object(VGRParser, '_apply_truth_data', change_truth):
            from vg.core.vgr_parser import main
            with contextlib.redirect_stderr(io.StringIO()):
                code = main([str(self.replay), '--truth', str(self.truth), '-o', str(output)])
        self.assertEqual(code, 2)
        self.assertEqual(output.read_text(), 'prior report')

    def test_legacy_inputs_failure_final_comparison_late_alias(self):
        screenshot = self.root / 'screen.png'
        screenshot.write_bytes(b'pixels')
        output = self.root / 'comparison.json'
        for source in (self.truth, screenshot):
            output.write_bytes(b'prior report')
            original = source.read_bytes()

            def compare(*args):
                output.unlink()
                os.link(source, output)
                return {'comparison_status': 'matched'}

            with patch.object(final_screen_comparison, 'compare_final_screen', side_effect=compare):
                with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
                    final_screen_comparison.main([str(self.replay), '--observation', str(self.truth),
                                                  '--screenshot', str(screenshot), '-o', str(output)])
            self.assertEqual(error.exception.code, 2)
            self.assertEqual(source.read_bytes(), original)
            output.unlink()
