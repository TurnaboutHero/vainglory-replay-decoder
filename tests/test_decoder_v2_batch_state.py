import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.test_native_inventory import anchor
from tests.test_player_state_service import recording
from vg.core.replay_input import ReplayInputError
from vg.decoder_v2 import batch_decode, player_state


class BatchPlayerStateTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'replays'
        for name, data in (('a', recording(counters=(5, 2, 3, 4))), ('b', recording(actor=9, counters=(1, 0, 7, 2))),
                           ('c', anchor())):
            (self.root / name).mkdir(parents=True)
            (self.root / name / 'match.0.vgr').write_bytes(data)

    def test_state_batch_uses_player_state_for_every_input(self):
        report = batch_decode.decode_state_batch(str(self.root))
        self.assertEqual(report['schema_version'], 'decoder_v2.batch_state.v1')
        self.assertEqual((report['discovered'], report['succeeded'], report['failed']), (3, 3, 0))
        states = {state['input_id']: state for state in report['states']}
        self.assertEqual(set(states), {'a/match.0.vgr', 'b/match.0.vgr', 'c/match.0.vgr'})
        self.assertTrue(all(s['schema_version'] == 'decoder_v2.player_state.v3' for s in states.values()))
        single = player_state.decode_player_state(self.root / 'a' / 'match.0.vgr').to_dict()
        self.assertEqual({k: v for k, v in states['a/match.0.vgr'].items() if k != 'input_id'}, single)
        self.assertEqual([p['kills'] for p in states['b/match.0.vgr']['players']], [1])
        self.assertEqual(report['support_summary'], {'supported': 2, states['c/match.0.vgr']['support_status']: 1})
        self.assertEqual(report['player_field_summary']['kills'], {'supported': 2})
        self.assertEqual(report['scope'], 'recorded_end')

    def test_state_batch_queries_every_input_at_the_same_game_time(self):
        report = batch_decode.decode_state_batch(str(self.root), at_game_time=0)
        self.assertEqual(report['scope'], 'capture')
        self.assertEqual(report['requested_game_time'], 0)
        self.assertTrue(all(s['requested_game_time'] == 0 for s in report['states']))

    def test_state_batch_keeps_other_inputs_when_one_fails(self):
        real = player_state.decode_player_state
        def flaky(path, **kwargs):
            if Path(path).parent.name == 'b':
                raise ReplayInputError('replay_unreadable', Path(path), 'boom')
            return real(path, **kwargs)
        with patch.object(batch_decode, 'decode_player_state', side_effect=flaky):
            report = batch_decode.decode_state_batch(str(self.root))
        self.assertEqual((report['succeeded'], report['failed']), (2, 1))
        failed = [r for r in report['results'] if r['status'] == 'failed']
        self.assertEqual([(r['input_id'], r['error_code']) for r in failed], [('b/match.0.vgr', 'replay_unreadable')])
        self.assertEqual({s['input_id'] for s in report['states']}, {'a/match.0.vgr', 'c/match.0.vgr'})

    def test_cli_state_json_and_default_format_is_unchanged(self):
        out = Path(self.temp.name) / 'state.json'
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(batch_decode.main([str(self.root), '--format', 'state-json', '-o', str(out)]), 0)
        self.assertEqual(json.loads(out.read_text())['schema_version'], 'decoder_v2.batch_state.v1')
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            batch_decode.main([str(self.root)])
        self.assertEqual(json.loads(stdout.getvalue())['schema_version'], 'decoder_v2.batch.v2')
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            batch_decode.main([str(self.root), '--at-game-time', '0'])


if __name__ == '__main__':
    unittest.main()
