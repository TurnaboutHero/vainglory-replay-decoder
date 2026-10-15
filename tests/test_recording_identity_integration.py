"""Synthetic, file-boundary regressions for additive recording identity evidence."""

from dataclasses import asdict
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.test_native_inventory import anchor, packet
from tests.test_native_roster import roster
from tests.test_player_state_service import state_snapshot
from vg.core.native_query import GameTime, RecordTime
from vg.core.native_roster import read_native_roster
from vg.core.recording_identity import summarize_recording_identity
from vg.core.replay_input import ReplayInputError, replay_sections
from vg.core.stat_evidence import frame_scope
from vg.decoder_v2.decode_match import decode_match, decode_match_debug
from vg.decoder_v2.player_state import decode_player_state


def identity_roster(actor=7, external_id=b'opaque-player-id', *, time=0, team=1):
    record = bytearray(roster(actor, b'Same', time=time, team=team))
    record[74:138] = (external_id + b'\0').ljust(64, b'\0')
    return bytes(record)


def selection(actor=7, *, time=1, team=1):
    payload = bytearray(101)
    struct.pack_into('>I', payload, 0, actor)
    payload[100] = team
    return packet(time, 0x03e9, payload)


def identity_recording(actor=7, external_id=b'opaque-player-id'):
    return (anchor() + identity_roster(actor, external_id) + state_snapshot(actor=actor)
            + selection(actor) + packet(10, 0xffff))


def json_value(value):
    return json.loads(json.dumps(value))


class RecordingIdentityIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.replay = self.root / 'match.0.vgr'
        self.data = identity_recording()
        self.replay.write_bytes(self.data)

    def cli(self, *args, module='vg.decoder_v2.decode_match'):
        return subprocess.run(
            [sys.executable, '-B', '-m', module, *map(str, args)],
            capture_output=True, text=True,
            cwd=Path(__file__).resolve().parents[1], timeout=30,
        )

    def frames(self, replay=None):
        return [(number, path.read_bytes())
                for number, path in replay_sections(replay or self.replay)]

    def assert_unverified(self, diagnostic):
        self.assertEqual(diagnostic.completeness_status, 'unknown')
        self.assertIsNone(diagnostic.authenticated_account_id)
        self.assertIsNone(diagnostic.authenticated_uploader_identity)
        self.assertFalse(diagnostic.recording_client_verified)

    def test_roster_and_state_share_the_typed_diagnostic_and_common_boundary(self):
        native = read_native_roster(self.frames())
        state = decode_player_state(self.replay)
        diagnostic = state.recording_identity
        self.assertEqual(diagnostic, summarize_recording_identity(native.recording_identity))
        self.assertEqual(diagnostic.detail_level, 'summary')
        self.assertEqual(diagnostic.record_boundary, native.record_boundary)
        self.assertEqual(diagnostic.record_boundary,
                         (state.record_boundary.section, state.record_boundary.record_offset))
        self.assertEqual(diagnostic.replay_scope, state.replay_scope)
        self.assertEqual(diagnostic.replay_scope, frame_scope(self.frames()))
        self.assertEqual(diagnostic.query_status, 'accepted')
        self.assertEqual(diagnostic.selection.recording_selected_actor_id, 7)
        self.assertEqual(diagnostic.selection.recording_selected_team_id, 1)
        self.assertEqual(json_value(asdict(diagnostic)),
                         json_value(state.to_dict()['recording_identity']))
        self.assert_unverified(diagnostic)
        self.assertEqual(state.support_status, 'supported')
        self.assertFalse(state.definitive_analysis['eligible'])

    def test_sources_hash_exact_numbered_bytes_including_unselected_future_sections(self):
        second = anchor(11, 111) + identity_roster(time=12) + packet(15, 0xffff)
        self.replay.with_name('match.1.vgr').write_bytes(second)
        state = decode_player_state(self.replay, at_record_time=1)
        diagnostic = state.recording_identity
        full = read_native_roster(self.frames(), RecordTime(1)).recording_identity
        expected = [(number, len(data), hashlib.sha256(data).hexdigest())
                    for number, data in self.frames()]
        self.assertEqual([(source.section, source.size_bytes, source.sha256)
                          for source in full.sources], expected)
        self.assertEqual([(source.section, source.size_bytes, source.sha256)
                          for source in state.source_files], expected)
        self.assertEqual(diagnostic.source_count, len(expected))
        self.assertEqual(diagnostic.replay_scope, frame_scope(self.frames()))
        self.assertEqual(diagnostic.external_id_histories[0].observation_count, 1)
        self.assertEqual(diagnostic.record_boundary[0], 0)

    def test_source_identity_changes_when_only_opaque_external_id_bytes_change(self):
        before = decode_player_state(self.replay)
        self.replay.write_bytes(identity_recording(external_id=b'opaque-player-ix'))
        after = decode_player_state(self.replay)
        self.assertNotEqual(before.recording_identity.replay_scope,
                            after.recording_identity.replay_scope)
        self.assertNotEqual(before.source_files[0].sha256, after.source_files[0].sha256)
        self.assertEqual(before.source_files[0].size_bytes, after.source_files[0].size_bytes)
        # Gameplay values and the stable recording-scoped native actor remain unchanged.
        for key in ('native_actor_id', 'name', 'hero_name', 'team_id', 'kills',
                    'deaths', 'assists', 'minion_kills', 'gold_balance', 'net_worth',
                    'items', 'native_items', 'inventory_capacity'):
            self.assertEqual(getattr(before.players[0], key), getattr(after.players[0], key), key)

    def test_literal_families_do_not_join_equal_actor_ids_or_external_id_histories(self):
        literal = self.root / '[match].0.vgr'
        literal.write_bytes(identity_recording(70000, b'literal-family'))
        literal.with_name('[match].1.vgr').write_bytes(
            anchor(11, 111) + identity_roster(70000, b'literal-family', time=12)
            + selection(70000, time=13))
        # A glob interpretation of [match] would select this unrelated family.
        lookalike = self.root / 'm.0.vgr'
        lookalike.write_bytes(identity_recording(70000, b'unrelated-family'))
        first = decode_player_state(literal)
        other = decode_player_state(lookalike)
        self.assertEqual(first.support_status, 'supported', first.support_reason)
        self.assertEqual([p.native_actor_id for p in first.players], [70000])
        self.assertEqual([h.native_actor_id for h in first.recording_identity.external_id_histories], [70000])
        self.assertEqual(first.recording_identity.external_id_histories[0].observation_count, 2)
        self.assertEqual(other.recording_identity.external_id_histories[0].observation_count, 1)
        self.assertNotEqual(first.recording_identity.external_id_histories[0].candidates,
                            other.recording_identity.external_id_histories[0].candidates)
        self.assertEqual(first.recording_identity.replay_scope, frame_scope(self.frames(literal)))
        self.assertNotEqual(first.recording_identity.replay_scope, other.recording_identity.replay_scope)
        self.assertEqual(first.recording_identity.source_count, 2)
        self.assertEqual([s.section for s in first.source_files], [0, 1])

    def test_directory_selection_accepts_one_nested_family_and_rejects_two(self):
        nested = self.root / 'nested'
        nested.mkdir()
        moved = nested / self.replay.name
        self.replay.rename(moved)
        state = decode_player_state(self.root)
        self.assertEqual(state.replay_file, str(moved))
        self.assertEqual(state.recording_identity,
                         summarize_recording_identity(read_native_roster(self.frames(moved)).recording_identity))
        (self.root / 'other.0.vgr').write_bytes(identity_recording(70000, b'other'))
        with self.assertRaises(ReplayInputError) as caught:
            decode_player_state(self.root)
        self.assertEqual(caught.exception.code, 'replay_ambiguous')
        output = self.root / 'report.json'
        output.write_text('previous report', encoding='utf-8')
        result = self.cli(self.root, '-o', output)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('replay_ambiguous', result.stderr)
        self.assertEqual(output.read_text(encoding='utf-8'), 'previous report')

    def test_duplicate_numeric_aliases_are_rejected_before_identity_decoding(self):
        alias = self.replay.with_name('match.00.vgr')
        alias.write_bytes(self.data)
        with patch('vg.decoder_v2.player_state.read_native_roster') as read_roster:
            with self.assertRaises(ReplayInputError) as caught:
                decode_player_state(self.replay)
            read_roster.assert_not_called()
        self.assertEqual(caught.exception.code, 'replay_ambiguous')
        self.assertIn('Duplicate numeric section suffix', caught.exception.reason)
        result = self.cli(self.replay)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn('replay_ambiguous', result.stderr)
        self.assertEqual(result.stdout, '')
        self.assertEqual(self.replay.read_bytes(), self.data)
        self.assertEqual(alias.read_bytes(), self.data)

    def test_mixed_prefix_selection_and_roster_cannot_corroborate_each_other(self):
        recording_a = self.root / 'recording_A.0.vgr'
        self.replay.rename(recording_a)
        data_a = anchor() + selection() + packet(10, 0xffff)
        recording_a.write_bytes(data_a)
        recording_b = self.root / 'recording_B.1.vgr'
        data_b = (anchor(11, 111) + identity_roster(time=12)
                  + state_snapshot(time=12) + packet(13, 0xffff))
        recording_b.write_bytes(data_b)
        # The section numbers, clocks, actor and team align. Only their filename
        # families distinguish this former research-helper cross-recording trap.
        self.assertEqual(replay_sections(recording_a), ((0, recording_a),))
        explicit = decode_player_state(recording_a)
        discovered = decode_player_state(self.root)
        self.assertEqual(explicit, discovered)
        diagnostic = explicit.recording_identity
        self.assertEqual(diagnostic.query_status, 'accepted')
        self.assertEqual(diagnostic.external_id_histories, ())
        self.assertEqual(diagnostic.selection.status, 'uncorroborated')
        self.assertEqual(diagnostic.selection.roster_consistency, 'missing_roster')
        self.assertEqual(diagnostic.selection.observation_count, 1)
        self.assertIsNone(diagnostic.selection.recording_selected_actor_id)
        self.assertIsNone(diagnostic.selection.recording_selected_team_id)
        self.assertEqual(diagnostic.replay_scope, frame_scope([(0, data_a)]))
        self.assertEqual(diagnostic.source_count, 1)
        self.assertEqual([s.sha256 for s in explicit.source_files], [hashlib.sha256(data_a).hexdigest()])
        self.assertEqual([s.path for s in explicit.source_files], [str(recording_a)])
        result = self.cli(recording_a)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), json_value(explicit.to_dict()))
        self.assertEqual(recording_b.read_bytes(), data_b)

    def test_cutoffs_exclude_future_external_id_and_selection_evidence(self):
        initial = (anchor() + identity_roster() + state_snapshot(actor=7)
                   + identity_roster(70000, b'other-player') + state_snapshot(actor=70000)
                   + selection())
        self.replay.write_bytes(initial + identity_roster(external_id=b'changed-id', time=5)
                                + selection(70000, time=6) + packet(10, 0xffff))
        frames = self.frames()
        for api_cutoff, native_cutoff in (({'at_game_time': 104}, GameTime(104)),
                                          ({'at_record_time': 4}, RecordTime(4))):
            with self.subTest(cutoff=api_cutoff):
                state = decode_player_state(self.replay, **api_cutoff)
                diagnostic = state.recording_identity
                self.assertEqual(diagnostic,
                                 summarize_recording_identity(read_native_roster(frames, native_cutoff).recording_identity))
                self.assertEqual([h.observation_count for h in diagnostic.external_id_histories], [1, 1])
                self.assertEqual([c.raw_value_hex for c in diagnostic.external_id_histories[0].candidates],
                                 [b'opaque-player-id'.hex()])
                self.assertEqual(diagnostic.selection.observation_count, 1)
                self.assertEqual(diagnostic.selection.recording_selected_actor_id, 7)
                self.assertEqual(diagnostic.record_boundary, (0, len(initial) - len(selection())))
        recorded_end = decode_player_state(self.replay).recording_identity
        self.assertEqual(recorded_end,
                         summarize_recording_identity(read_native_roster(frames).recording_identity))
        self.assertEqual([h.observation_count for h in recorded_end.external_id_histories], [2, 1])
        self.assertEqual([c.raw_value_hex for c in recorded_end.external_id_histories[0].candidates],
                         [b'opaque-player-id'.hex(), b'changed-id'.hex()])
        self.assertEqual(recorded_end.external_id_histories[0].status, 'conflicting_candidates')
        self.assertEqual(recorded_end.selection.observation_count, 2)
        self.assertEqual(recorded_end.selection.status, 'changing_selection')
        self.assertIsNone(recorded_end.selection.recording_selected_actor_id)
        self.assertIsNone(recorded_end.selection.recording_selected_team_id)

    def test_player_filter_does_not_rewrite_recording_selection_or_hide_other_histories(self):
        self.replay.write_bytes(anchor() + identity_roster() + state_snapshot(actor=7)
                                + identity_roster(70000, b'other-player')
                                + state_snapshot(actor=70000) + selection() + packet(10, 0xffff))
        all_state = decode_player_state(self.replay)
        selected = decode_player_state(self.replay, player_ids=[70000])
        missing = decode_player_state(self.replay, player_ids=[999])
        self.assertEqual([p.native_actor_id for p in selected.players], [70000])
        self.assertEqual(selected.recording_identity, all_state.recording_identity)
        self.assertEqual(missing.recording_identity, all_state.recording_identity)
        self.assertEqual(selected.recording_identity.selection.recording_selected_actor_id, 7)
        self.assertEqual(len(selected.recording_identity.external_id_histories), 2)
        self.assertEqual(missing.support_status, 'player_not_found')

    def test_invalid_queries_keep_source_provenance_without_identity_claims(self):
        cases = ((self.data, {'at_game_time': 99}, 'out_of_coverage'),
                 (self.data + b'broken', {'at_record_time': 1}, 'malformed_records'))
        for data, kwargs, status in cases:
            with self.subTest(status=status):
                self.replay.write_bytes(data)
                state = decode_player_state(self.replay, **kwargs)
                diagnostic = state.recording_identity
                cutoff = (GameTime(kwargs['at_game_time']) if 'at_game_time' in kwargs
                          else RecordTime(kwargs['at_record_time']))
                self.assertEqual(diagnostic,
                                 summarize_recording_identity(read_native_roster(self.frames(), cutoff).recording_identity))
                self.assertEqual(state.support_status, status)
                self.assertEqual(diagnostic.query_status, status)
                self.assertIsNone(diagnostic.record_boundary)
                self.assertEqual(diagnostic.external_id_histories, ())
                self.assertEqual(diagnostic.selection.observation_count, 0)
                self.assertIsNone(diagnostic.selection.recording_selected_actor_id)
                self.assertIsNone(diagnostic.selection.recording_selected_team_id)
                self.assertEqual(diagnostic.source_count, 1)
                self.assertEqual(state.source_files[0].sha256, hashlib.sha256(data).hexdigest())
                self.assert_unverified(diagnostic)

    def test_nonconsecutive_sections_cannot_create_a_cross_segment_identity(self):
        self.replay.with_name('match.2.vgr').write_bytes(
            anchor(11, 111) + identity_roster(70000, b'other-segment', time=12)
            + selection(70000, time=13))
        state = decode_player_state(self.replay)
        diagnostic = state.recording_identity
        self.assertEqual(state.support_status, 'mixed_segments')
        self.assertEqual(diagnostic.query_status, 'mixed_segments')
        self.assertEqual(diagnostic.external_id_histories, ())
        self.assertIsNone(diagnostic.selection.recording_selected_actor_id)
        self.assertEqual(diagnostic.source_count, 2)
        self.assertEqual([s.section for s in state.source_files], [0, 2])
        self.assertEqual(diagnostic.replay_scope, frame_scope(self.frames()))

    def test_default_and_timed_cli_json_exactly_match_api_diagnostics(self):
        for args, kwargs in (((), {}), (('--at-game-time', '101'), {'at_game_time': 101}),
                             (('--at-record-time', '1'), {'at_record_time': 1}),
                             (('--player-id', '7'), {'player_ids': [7]})):
            with self.subTest(args=args):
                result = self.cli(self.replay, *args)
                self.assertEqual(result.returncode, 0, result.stderr)
                actual = json.loads(result.stdout)
                expected = json_value(decode_player_state(self.replay, **kwargs).to_dict())
                self.assertEqual(actual, expected)
                self.assertIn('recording_identity', actual)
        self.assertEqual(self.replay.read_bytes(), self.data)

    def test_roster_cli_reports_separate_families_using_the_same_diagnostic(self):
        other = self.root / 'other.0.vgr'
        other.write_bytes(identity_recording(70000, b'other-family'))
        output = self.root / 'rosters.json'
        result = self.cli('--replay-root', self.root, '--output', output,
                          module='vg.core.native_roster')
        self.assertEqual(result.returncode, 0, result.stderr)
        reports = json.loads(output.read_text(encoding='utf-8'))
        self.assertEqual([r['replay'] for r in reports], ['match.0.vgr', 'other.0.vgr'])
        for report, replay in zip(reports, (self.replay, other)):
            self.assertEqual(report['result']['recording_identity'],
                             json_value(asdict(read_native_roster(self.frames(replay)).recording_identity)))

    def test_compact_diagnostic_size_is_bounded_for_repeated_empty_snapshots(self):
        compact_sizes = []
        full_sizes = []
        for count in (1, 256):
            with self.subTest(observations=count):
                data = (anchor() + identity_roster(external_id=b'')
                        + state_snapshot(actor=7) + selection()
                        + identity_roster(external_id=b'', time=5) * (count - 1)
                        + packet(10, 0xffff))
                self.replay.write_bytes(data)
                full = read_native_roster(self.frames()).recording_identity
                state = decode_player_state(self.replay)
                compact = state.recording_identity
                self.assertEqual(compact, summarize_recording_identity(full))
                self.assertEqual(compact.external_id_histories[0].observation_count, count)
                self.assertEqual(compact.external_id_histories[0].empty_observation_count, count)
                self.assertEqual(compact.external_id_histories[0].candidates, ())
                self.assertEqual(compact.selection.observation_count, 1)
                self.assertEqual(len(full.external_id_histories[0].observations), count)
                compact_json = json.dumps(state.to_dict()['recording_identity'], sort_keys=True)
                full_json = json.dumps(asdict(full), sort_keys=True)
                # Raw evidence and per-observation locations remain available only
                # in the full diagnostic. Bounded first/last locations are permitted.
                for field in ('observations', 'raw_payload_hex', 'raw_field_hex', 'source_records'):
                    self.assertNotIn('"' + field + '":', compact_json)
                self.assertIn('"raw_payload_hex":', full_json)
                self.assertIn('"observations":', full_json)
                compact_sizes.append(len(compact_json.encode('utf-8')))
                full_sizes.append(len(full_json.encode('utf-8')))
        self.assertLess(compact_sizes[-1], 4096)
        self.assertLess(compact_sizes[-1] - compact_sizes[0], 128)
        self.assertGreater(full_sizes[-1], full_sizes[0] * 30)

    def test_identity_reports_cannot_overwrite_input_or_numeric_siblings_through_aliases(self):
        sibling = self.replay.with_name('match.1.vgr')
        sibling_data = anchor(11, 111) + packet(12, 0xffff)
        sibling.write_bytes(sibling_data)
        hard = self.root / 'hard.json'
        os.link(self.replay, hard)
        symbolic = self.root / 'symbolic.json'
        symbolic.symlink_to(sibling)
        future = self.root / 'match.2.vgr'
        for output in (self.replay, sibling, hard, symbolic, future):
            with self.subTest(output=output):
                result = self.cli(self.replay, '-o', output)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(self.replay.read_bytes(), self.data)
                self.assertEqual(sibling.read_bytes(), sibling_data)
                self.assertFalse(future.exists())

    def test_additive_state_and_legacy_json_remain_byte_equivalent_to_baseline(self):
        # Canonical snapshots captured from 65bab83 before identity diagnostics.
        # Normalize only the disposable input path; every preexisting field is checked.
        expected = {
            'state-json': 'fcbd296c5744400a6967a1331a692082a1e3fdb13a28d6f3075c6e0ab4f063fe',
            'safe-json': 'cccee51c9e67e30e9ca54447830d31c7fa32f21e1221c083e954da862c78ba15',
            'debug-json': '6f98c77fcff04b46cc068e3ca37c815d37cfa4f453e68b8e4012493bac39d201',
        }
        api_outputs = {
            'state-json': decode_player_state(self.replay).to_dict(),
            'safe-json': decode_match(str(self.replay)).to_dict(),
            'debug-json': decode_match_debug(str(self.replay)),
        }
        for format_name, value in api_outputs.items():
            with self.subTest(format=format_name):
                cli = self.cli(self.replay, '--format', format_name)
                self.assertEqual(cli.returncode, 0, cli.stderr)
                self.assertEqual(json.loads(cli.stdout), json_value(value))
                if format_name == 'state-json':
                    self.assertIn('recording_identity', value)
                    value.pop('recording_identity')
                else:
                    self.assertNotIn('recording_identity', value)
                canonical = json.dumps(value, sort_keys=True, separators=(',', ':'))
                canonical = canonical.replace(str(self.replay), '<REPLAY>')
                self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(), expected[format_name])


if __name__ == '__main__':
    unittest.main()
