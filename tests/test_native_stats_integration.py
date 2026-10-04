import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from vg.decoder_v2.completeness import assess_completeness
from vg.decoder_v2.models import ReplaySignalSummary
from vg.decoder_v2.kda import decode_kda_from_replay


class NativeStatsIntegrationTests(unittest.TestCase):
    def test_mixed_clock_overrides_terminal_candidate(self):
        signals = ReplaySignalSummary('x', 'x.0.vgr', 100, 99, 1000., 999., 1000., 1000., 1000.,
                                      native_clock_valid=False, native_clock_status='mixed_segments',
                                      native_clock_reason='Game clock moved backwards')
        result = assess_completeness(signals)
        self.assertEqual(result.status.value, 'completeness_unknown')
        self.assertIn('backwards', result.reason)

    def test_capture_query_is_supported(self):
        signals = ReplaySignalSummary('x', 'x.0.vgr', 1, 0, None, None, None, None, None)
        with patch('vg.decoder_v2.kda.extract_replay_signals', return_value=signals):
            result = decode_kda_from_replay('x.0.vgr', at_game_time=-1)
        self.assertFalse(result.accepted)
        self.assertEqual(result.scope, 'capture')

from vg.core.unified_decoder import UnifiedDecoder
from vg.decoder_v2.decode_match import decode_match, decode_match_debug, main
from vg.decoder_v2.models import KDAExtractionResult, KDAPlayerSummary, DurationEstimate
from tests.test_native_stats import anchor, snapshot, attribute, resource, packet, frame
from tests.test_native_inventory import anchor as state_anchor
from tests.test_native_roster import roster
from tests.test_player_state_service import state_snapshot
from vg.decoder_v2.player_state import decode_player_state

PARSED = {'replay_name':'x', 'replay_file':'x.0.vgr',
          'match_info':{'mode':'5v5','map_name':'map','team_size':1},
          'teams':{'left':[{'name':'p','team':'left','entity_id':1792,'hero_name':'Alpha'}], 'right':[]}}


class NativeCallerBoundaryTests(unittest.TestCase):
    def test_direct_capture_rejects_series_missing_section_zero(self):
        frames = [(1, anchor(0,100) + snapshot(0) + packet(10,1))]
        with patch('vg.decoder_v2.kda.extract_replay_signals', return_value=self.signals()), \
             patch('vg.decoder_v2.kda.VGRParser') as parser, \
             patch('vg.decoder_v2.kda.load_frames',return_value=frames):
            parser.return_value.parse.return_value=PARSED
            result=decode_kda_from_replay('x.0.vgr',at_game_time=105)
        self.assertFalse(result.accepted)
        self.assertEqual(result.players,())
        self.assertIn('section zero',result.reason)

    def signals(self, complete=False):
        return ReplaySignalSummary('x','x.0.vgr',100 if complete else 1,99 if complete else 0,
                                   5. if complete else None,None,5. if complete else None,None,None)

    def test_seeded_baseline_and_clock_offset_are_applied_in_caller(self):
        data=anchor(0,100)+snapshot(0)+attribute(2)+attribute(8)+packet(10,1)
        with patch('vg.decoder_v2.kda.extract_replay_signals',return_value=self.signals(True)), \
             patch('vg.decoder_v2.kda.VGRParser') as parser, \
             patch('vg.decoder_v2.kda.load_frames',return_value=[(0,data)]):
            parser.return_value.parse.return_value=PARSED
            final=decode_kda_from_replay('x.0.vgr')
            capture=decode_kda_from_replay('x.0.vgr',at_game_time=109)
        self.assertFalse(final.accepted)
        self.assertEqual(final.players,())
        self.assertEqual(capture.players[0].kills,8)
        self.assertEqual(capture.as_of_game_time,109)

    def test_missing_baseline_withholds_instead_of_zero(self):
        with patch('vg.decoder_v2.kda.extract_replay_signals',return_value=self.signals(True)), \
             patch('vg.decoder_v2.kda.VGRParser') as parser, \
             patch('vg.decoder_v2.kda.load_frames',return_value=[(0,anchor(0,100)+attribute(2)+packet(10,1))]):
            parser.return_value.parse.return_value=PARSED
            result=decode_kda_from_replay('x.0.vgr',at_game_time=109)
        self.assertFalse(result.accepted)
        self.assertEqual(result.players,())
        self.assertIn('missing_baseline',result.reason)

    def test_default_incomplete_still_stops_before_native_read(self):
        with patch('vg.decoder_v2.kda.extract_replay_signals',return_value=self.signals()), \
             patch('vg.decoder_v2.kda.read_native_stats') as reader:
            result=decode_kda_from_replay('x.0.vgr')
        self.assertFalse(result.accepted)
        reader.assert_not_called()

    def test_capture_never_runs_final_decoders_or_exports_final_claims(self):
        from vg.core.stat_evidence import frame_scope
        frames = [(0, anchor(0,100) + snapshot(0) + packet(10,1))]
        scope = frame_scope(frames)
        assessment=assess_completeness(self.signals())
        result=KDAExtractionResult(True,'capture',assessment,DurationEstimate(None,'unknown',assessment),
                                  (KDAPlayerSummary('p','left','Alpha',6,2,3,100,7,scope),),'capture',105,105,scope)
        with tempfile.TemporaryDirectory() as temporary, \
             patch('vg.decoder_v2.decode_match.VGRParser') as parser, \
             patch('vg.decoder_v2.decode_match.load_frames', return_value=frames), \
             patch('vg.decoder_v2.decode_match.decode_kda_from_replay',return_value=result), \
             patch('vg.decoder_v2.decode_match.decode_winner_from_replay') as winner, \
             patch('vg.decoder_v2.decode_match.decode_gold_from_replay') as gold, \
             patch('vg.decoder_v2.decode_match.collect_minion_candidates') as minions:
            parser.return_value.parse.return_value=PARSED
            replay = Path(temporary) / 'x.0.vgr'
            replay.write_bytes(frames[0][1])
            safe=decode_match(str(replay),at_game_time=105)
            debug=decode_match_debug(str(replay),at_game_time=105)
        winner.assert_not_called(); gold.assert_not_called(); minions.assert_not_called()
        self.assertEqual(safe.schema_version,'decoder_v2.capture.v2')
        self.assertEqual(safe.scope,'capture')
        self.assertEqual(safe.players[0].kills,6)
        self.assertIsNone(safe.players[0].gold)
        for key in ('kills','deaths','assists'):
            self.assertFalse(safe.accepted_fields[key].accepted_for_index)
        for key in ('winner','gold','duration_seconds'):
            self.assertIsNone(safe.withheld_fields[key].value)
        self.assertIsNone(debug['duration']); self.assertIsNone(debug['winner_debug'])

    def test_unified_observes_eof_as_recorded_state_without_final_validation(self):
        data = state_anchor(0, 500) + roster(7, b'p')
        data += state_snapshot(counters=(6, 2, 3, 100))
        data += attribute(2) + attribute(3, 2, index=42)
        data += resource(4, 4) + resource(5, 5, index=14)
        data += attribute(9.5, 100) + packet(10, 1)
        with tempfile.TemporaryDirectory() as temporary, \
             patch.object(UnifiedDecoder, '_detect_crystal_death', return_value=(9., 2000)):
            replay = Path(temporary) / 'x.0.vgr'
            replay.write_bytes(data)
            result = UnifiedDecoder(str(replay)).decode()
            state = decode_player_state(replay)
        self.assertEqual(result.player_state, state.to_dict())
        self.assertEqual(len(result.all_players), 1)
        player = result.all_players[0]
        self.assertEqual(player.entity_id, 1792)
        self.assertEqual(player.native_actor_id, 7)
        self.assertEqual((player.kills, player.deaths, player.assists, player.minion_kills),
                         (107, 4, 7, 105))
        self.assertEqual((player.gold_balance, player.net_worth, player.items), (25.5, 100.5, []))
        self.assertEqual(player.state_scope, 'recorded_end')
        self.assertEqual(player.record_boundary, result.player_state['record_boundary'])
        for field in ('kda', 'minion_kills', 'items', 'gold_balance', 'net_worth'):
            self.assertEqual(player.field_status[field]['provenance']['record_boundary'], player.record_boundary)
        self.assertTrue(result.kda_detection_used)
        self.assertEqual(result.native_stats_status, 'supported')
        self.assertEqual(result.final_validation_status, 'unverified')
        self.assertIsNone(result.winner)
        self.assertEqual(result.duration_seconds, 9)
        self.assertEqual(result.as_of_game_time, 510)

    def test_unified_real_mixed_frames_override_terminal_and_withhold_stats(self):
        with tempfile.TemporaryDirectory() as temporary, \
             patch.object(UnifiedDecoder,'_detect_crystal_death',return_value=(20.,2000)):
            replay = Path(temporary) / 'x.0.vgr'
            replay.write_bytes(state_anchor() + roster(7, b'p') + state_snapshot() + packet(10, 1))
            replay.with_name('x.1.vgr').write_bytes(state_anchor(11, 1) + packet(21, 1))
            result = UnifiedDecoder(str(replay)).decode()
            state = decode_player_state(replay)
        self.assertEqual(result.player_state, state.to_dict())
        self.assertEqual(result.duration_seconds, 20)
        self.assertIsNone(result.data_complete)
        self.assertEqual(result.native_stats_status,'mixed_segments')
        self.assertIsNone(result.winner)
        self.assertEqual(result.all_players, [])
        self.assertEqual(result.player_state['players'], ())
        self.assertEqual(result.player_state['support_status'], 'mixed_segments')
        for field in ('kda', 'minion_kills', 'items', 'gold_balance', 'net_worth'):
            self.assertEqual(result.player_state['field_status'][field]['status'], 'mixed_segments')

    def test_winner_rejects_accepted_capture_even_with_complete_assessment(self):
        from vg.decoder_v2.winner import decode_winner_from_replay
        assessment=assess_completeness(self.signals(True))
        result=KDAExtractionResult(True,'Capture only',assessment,DurationEstimate(5,'crystal',assessment),
                                  (KDAPlayerSummary('p','left','Alpha',6,2,3,100),),'capture',105,105)
        with patch('vg.decoder_v2.winner.decode_kda_from_replay',return_value=result):
            winner=decode_winner_from_replay('x.0.vgr')
        self.assertFalse(winner.accepted)
        self.assertIsNone(winner.winner)
        self.assertIn('Capture only',winner.reason)

    def test_cli_rejects_nonfinite_and_negative_capture(self):
        for value in ('nan','inf','-1'):
            with self.subTest(value=value), self.assertRaises(SystemExit) as caught:
                main(['x.0.vgr','--at-game-time',value])
            self.assertEqual(caught.exception.code,2)


if __name__ == '__main__':
    unittest.main()
