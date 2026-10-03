import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from vg.core.batch_result import batch_report, PartialBatchError
from vg.core.replay_input import (
    ReplayInputError, discover_replay_files, replay_input_id, replay_sections, select_replay,
)
from vg.core.replay_output import (
    ReportInputs, ReplayOutputError, publish_report_set, recover_report_set,
    validate_report_outputs, write_report_output,
)
from vg.core.truth_input import (
    TruthInputError, load_truth_matches, normalize_truth, resolve_truth_reference, select_truth_match,
)


def player_block() -> bytes:
    block = bytearray(0xE2)
    block[:3] = b'\xda\x03\xee'
    block[3:12] = b'PlayerOne'
    block[0xA5:0xA7] = (1).to_bytes(2, 'little')
    block[0xA9:0xAB] = (0xB801).to_bytes(2, 'little')
    block[0xD5] = 1
    return bytes(block)


class ProductIOContracts(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def family(self, parent: str = 'a') -> Path:
        folder = self.root / parent
        folder.mkdir(parents=True, exist_ok=True)
        frame0 = folder / 'match.0.vgr'
        frame0.write_bytes(player_block())
        for number in (1, 2, 10):
            (folder / f'match.{number}.vgr').write_bytes(b'opaque section')
        return frame0

    def assert_code(self, code: str, callable_, *args, **kwargs) -> None:
        with self.assertRaises((ReplayInputError, ReplayOutputError, TruthInputError)) as caught:
            callable_(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)

    def test_shared_contract_happy(self) -> None:
        first, second = self.family('a'), self.family('b')
        sources = [path for _, path in replay_sections(first)] + [path for _, path in replay_sections(second)]
        before = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
        discovered = discover_replay_files(self.root)
        self.assertEqual(discovered, (first, second))
        self.assertEqual([replay_input_id(path, self.root) for path in discovered], ['a/match.0.vgr', 'b/match.0.vgr'])
        self.assertEqual(select_replay(first), first)
        self.assertEqual(select_replay(first.parent), first)
        self.assertEqual([number for number, _ in replay_sections(first)], [0, 1, 2, 10])
        row = {'replay_name': 'match', 'players': {'PlayerOne': {'kills': 0, 'gold': None}}, 'extra': {'keep': True}}
        truth = self.root / 'truth.json'
        for envelope in (row, {'matches': {'match': row}}, {'matches': [row]}):
            truth.write_text(json.dumps(envelope), encoding='utf-8')
            self.assertEqual(select_truth_match(load_truth_matches(truth), truth, replay_name='match'), row)
        inputs = ReportInputs(files=(truth,), replays=discovered)
        left, right, receipt = [self.root / name for name in ('one.json', 'two.csv', 'receipt.json')]
        result = publish_report_set(inputs, {left: '{"ok":true}', right: b'col\nvalue\n'}, receipt)
        self.assertEqual(result['status'], 'complete')
        self.assertEqual(json.loads(receipt.read_text())['current_outputs'], [str(left), str(right)])
        self.assertEqual(left.read_bytes(), b'{"ok":true}')
        self.assertEqual(right.read_bytes(), b'col\nvalue\n')
        self.assertEqual(before, {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in sources})
        print(json.dumps({'scenario': 'T1-happy', 'source_hashes_before': {str(path): value for path, value in before.items()},
                          'source_hashes_after': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
                          'receipt': result}, sort_keys=True))
        self.assertEqual(recover_report_set(receipt)['status'], 'complete')
        next_result = publish_report_set(inputs, {left: 'next'}, receipt)
        self.assertEqual(next_result['stale_outputs'], [str(right)])
        self.assertEqual(right.read_bytes(), b'col\nvalue\n')
        self.assertIsNotNone(next_result['prior_receipt_identity'])

    def test_shared_contract_failure(self) -> None:
        frame0 = self.family()
        self.assert_code('input_missing', discover_replay_files, self.root / 'missing')
        self.assert_code('input_not_directory', discover_replay_files, frame0)
        self.assert_code('replay_gap', replay_sections, frame0, require_contiguous=True)
        self.assert_code('replay_malformed', select_replay, frame0.with_name('match.1.vgr'))
        self.family('b')
        self.assert_code('replay_ambiguous', select_replay, self.root)
        alias = frame0.with_name('match.01.vgr')
        alias.write_bytes(b'duplicate')
        self.assert_code('replay_ambiguous', replay_sections, frame0)
        alias.unlink()
        for data, code in ((b'', 'replay_empty'), (b'random bytes', 'replay_malformed')):
            frame0.write_bytes(data)
            self.assert_code(code, select_replay, frame0)
        frame0.write_bytes(player_block())
        truth = self.root / 'truth.json'
        for value in ([], 4, {'players': []}, {'players': {'x': 2}}, {'match_info': []},
                      {'players': {'x': {'gold': True}}}, {'duration_seconds': -1}, {'gold': float('inf')}):
            self.assert_code('truth_invalid', normalize_truth, value, truth)
        self.assert_code('truth_ambiguous', normalize_truth, {'matches': [
            {'replay_name': 'match', 'replay_file': 'a/match.0.vgr'},
            {'replay_name': 'match', 'replay_file': 'a/match.0.vgr'}]}, truth)
        inputs = ReportInputs(replays=(frame0,))
        hard, symbolic = self.root / 'hard.json', self.root / 'symbolic.json'
        os.link(frame0, hard)
        symbolic.symlink_to(frame0)
        for output in (frame0, hard, symbolic, frame0.with_name('match.99.vgr')):
            self.assert_code('output_alias', validate_report_outputs, inputs, (output,))
        distinct = self.root / 'out.json'
        self.assert_code('output_alias', validate_report_outputs, inputs, (distinct, distinct))
        self.assert_code('output_alias', publish_report_set, inputs, {distinct: 'new'}, distinct)
        prior = frame0.read_bytes()
        for point in ('stage', 'first', 'second', 'rollback'):
            with self.subTest(fault=point):
                self._publication_fault(inputs, point)
        self.assertEqual(frame0.read_bytes(), prior)

    def _publication_fault(self, inputs: ReportInputs, point: str) -> None:
        left, right, receipt = [self.root / name for name in ('one.json', 'two.json', 'receipt.json')]
        left.write_bytes(b'old one')
        right.write_bytes(b'old two')
        real_replace = os.replace
        calls = 0

        def replace(source, target) -> None:
            nonlocal calls
            if Path(target) in (left, right):
                calls += 1
                fail = calls == (1 if point == 'first' else 2)
                if fail or (point == 'rollback' and calls >= 3):
                    raise OSError('injected replace failure')
            real_replace(source, target)

        if point == 'stage':
            with patch('vg.core.report_transaction.stage_payload', side_effect=OSError('injected stage failure')):
                self.assert_code('publication_failed', publish_report_set, inputs, {left: 'new one', right: 'new two'}, receipt)
        else:
            with patch('os.replace', side_effect=replace):
                self.assert_code('recovery_required' if point == 'rollback' else 'publication_failed',
                                 publish_report_set, inputs, {left: 'new one', right: 'new two'}, receipt)
        if point == 'rollback':
            pending = json.loads(receipt.read_text())
            self.assertEqual(pending['status'], 'pending')
            self.assertTrue(all(Path(row['backup']).exists() for row in pending['entries']))
            self.assert_code('recovery_required', publish_report_set, inputs, {left: 'another'}, receipt)
            unowned = self.root / 'unowned.txt'
            unowned.write_bytes(b'keep')
            self.assertEqual(recover_report_set(receipt)['status'], 'rolled_back')
            self.assertEqual(unowned.read_bytes(), b'keep')
        self.assertEqual(left.read_bytes(), b'old one')
        self.assertEqual(right.read_bytes(), b'old two')
        self.assertFalse(receipt.exists())
        self.assertEqual(list(self.root.glob('.*.tmp')), [])
        self.assertEqual(list(self.root.glob('.*.backup')), [])
        print(json.dumps({'scenario': 'T1-failure', 'fault': point, 'receipt_exists': receipt.exists(),
                          'restored_hashes': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in (left, right)}}))

    def test_changed_source_and_late_alias_are_rejected(self) -> None:
        frame0 = self.family()
        output = self.root / 'report.json'
        output.write_bytes(b'old')
        inputs = ReportInputs(replays=(frame0,))
        frame0.write_bytes(player_block() + b'changed')
        self.assert_code('input_changed', write_report_output, inputs, output, 'new')
        self.assertEqual(output.read_bytes(), b'old')
        inputs = ReportInputs(replays=(frame0,))
        from vg.core.replay_output import stage_payload

        def stage(target, payload, encoding='utf-8'):
            temporary = stage_payload(target, payload, encoding)
            output.unlink()
            output.symlink_to(frame0)
            return temporary

        before = frame0.read_bytes()
        with patch('vg.core.replay_output.stage_payload', side_effect=stage):
            self.assert_code('output_alias', write_report_output, inputs, output, 'new')
        self.assertEqual(frame0.read_bytes(), before)
        self.assertEqual(list(self.root.glob('.*.tmp')), [])

    def test_truth_scoping_and_invalid_documents(self) -> None:
        truth = self.root / 'truth.json'
        rows = normalize_truth({'matches': [
            {'replay_name': 'same', 'replay_file': 'a/match.0.vgr'},
            {'replay_name': 'same', 'replay_file': 'b/match.0.vgr'}]}, truth)
        self.assertEqual(select_truth_match(rows, truth, replay_file='b/match.0.vgr'), rows[1])
        self.assert_code('truth_ambiguous', select_truth_match, rows, truth, replay_name='same')
        self.assert_code('truth_no_match', select_truth_match, rows, truth, replay_name='absent')
        self.assert_code('truth_unreadable', load_truth_matches, truth)
        for invalid in (b'\xff', b'{'):
            truth.write_bytes(invalid)
            self.assert_code('truth_invalid', load_truth_matches, truth)
        self.assertEqual(resolve_truth_reference('a/match.0.vgr', truth), self.root / 'a/match.0.vgr')
        if os.name != 'nt':
            self.assert_code('truth_unreadable', resolve_truth_reference, r'C:\\source\\match.0.vgr', truth)

    def test_empty_discovery_and_batch_accounting(self) -> None:
        self.assertEqual(discover_replay_files(self.root), ())
        self.assertEqual(batch_report([])['status'], 'empty')
        rows = [{'input_id': 'a/match.0.vgr', 'replay_file': 'a/match.0.vgr', 'status': 'complete', 'error_code': None, 'error': None},
                {'input_id': 'b/match.0.vgr', 'replay_file': 'b/match.0.vgr', 'status': 'failed', 'error_code': 'replay_empty', 'error': 'empty'}]
        result = batch_report(rows)
        self.assertEqual((result['status'], result['discovered'], result['succeeded'], result['failed']), ('partial', 2, 1, 1))
        self.assertIs(PartialBatchError(result).report, result)


if __name__ == '__main__':
    unittest.main()
