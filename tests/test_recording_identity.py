"""Synthetic protocol guards, not native-runtime or account validation."""

from dataclasses import asdict
import hashlib
import struct
import unittest

from tests.test_native_roster import anchor, packet, roster, spawn
from vg.core.native_query import GameTime, RecordTime
from vg.core.native_roster import NativeRosterResult, read_native_roster
from vg.core.recording_identity import read_recording_identity
from vg.core.stat_evidence import frame_scope


def identity(actor=1500, value=b'raw-external-id', *, length=222, team=1, time=0, name=b'A'):
    payload = bytearray(length)
    payload[:len(name)] = name
    payload[64:64 + min(len(value), 64)] = value[:64]
    if length >= 164:
        struct.pack_into('>I', payload, 160, actor)
    if length >= 172:
        struct.pack_into('>II', payload, 164, 243, 42)
    if length > 210:
        payload[210] = team
    return packet(0x03ee, payload, time)


def selection(actor=1500, team=1, *, length=101, time=0):
    payload = bytearray(length)
    if length >= 4:
        struct.pack_into('>I', payload, 0, actor)
    if length > 100:
        payload[100] = team
    return packet(0x03e9, payload, time)


class RecordingIdentityTests(unittest.TestCase):
    def read(self, data):
        return read_recording_identity([(0, anchor() + data)])

    def test_initial_candidate_survives_periodic_empty_snapshot(self):
        result = self.read(identity() + identity(value=b'', length=216))
        history, = result.external_id_histories
        self.assertEqual([row.payload_length for row in history.observations], [222, 216])
        self.assertEqual([row.status for row in history.observations], ['nonempty', 'empty'])
        self.assertEqual(history.status, 'observed_single_candidate')
        self.assertEqual(history.candidates[0].raw_value_hex, b'raw-external-id'.hex())
        self.assertEqual(history.candidates[0].source_records, ((0, len(anchor())),))
        self.assertIsNone(result.authenticated_account_id)
        self.assertIsNone(result.authenticated_uploader_identity)
        self.assertFalse(result.recording_client_verified)
        self.assertEqual(result.completeness_status, 'unknown')

    def test_identifier_is_not_restricted_to_uuid_ascii_or_initial_layout(self):
        for value in (b'not-a-uuid', b'\xff\xfe', '한글😀'.encode()):
            with self.subTest(value=value):
                history, = self.read(identity(value=value, length=216)).external_id_histories
                self.assertEqual(history.candidates[0].raw_value_hex, value.hex())
                self.assertEqual(history.status, 'observed_single_candidate')
                self.assertEqual(history.candidates[0].utf8_value,
                                 None if value == b'\xff\xfe' else value.decode())

    def test_bounded_field_stops_at_first_nul_and_retains_padding(self):
        row = self.read(identity(value=b'abc\0def')).external_id_histories[0].observations[0]
        self.assertEqual(row.raw_value_hex, b'abc'.hex())
        self.assertTrue(row.raw_field_hex.startswith(b'abc\0def'.hex()))
        self.assertEqual(len(row.raw_field_hex), 128)

    def test_unterminated_field_is_unknown_not_an_identifier(self):
        history, = self.read(identity(value=b'x' * 64)).external_id_histories
        self.assertEqual(history.status, 'incomplete')
        self.assertEqual(history.candidates, ())
        row, = history.observations
        self.assertEqual(row.status, 'unterminated_field')
        self.assertIsNone(row.raw_value_hex)
        self.assertEqual(row.raw_field_hex, (b'x' * 64).hex())

    def test_conflicting_history_never_picks_latest_nonempty(self):
        history, = self.read(identity(value=b'a') + identity(value=b'b') + identity(value=b'', length=216)
                             + identity(value=b'a')).external_id_histories
        self.assertEqual(history.status, 'conflicting_candidates')
        self.assertEqual([row.raw_value_hex for row in history.candidates], ['61', '62'])
        self.assertEqual(len(history.candidates[0].source_records), 2)
        self.assertIn('conflicting_nonempty_candidates', history.issues)

    def test_same_name_and_identifier_do_not_merge_actors(self):
        histories = self.read(identity(actor=1500) + identity(actor=1501)).external_id_histories
        self.assertEqual([row.native_actor_id for row in histories], [1500, 1501])
        self.assertEqual([row.status for row in histories], ['shared_candidate', 'shared_candidate'])
        self.assertEqual(histories[0].candidates[0].shared_with_actor_ids, (1501,))
        self.assertEqual(histories[1].candidates[0].shared_with_actor_ids, (1500,))

    def test_unsupported_roster_lengths_are_retained_without_parsing(self):
        for length in (0, 64, 128, 164, 215, 217, 221, 223):
            with self.subTest(length=length):
                data = packet(0x03ee, b'\xff' * length)
                result = self.read(data)
                self.assertEqual(result.external_id_histories, ())
                row, = result.unassigned_external_id_observations
                self.assertEqual(row.status, 'unsupported_layout')
                self.assertIsNone(row.native_actor_id)
                self.assertIsNone(row.raw_value_hex)
                self.assertEqual(row.raw_payload_hex, (b'\xff' * length).hex())
                self.assertEqual(result.external_id_evidence_status, 'incomplete')

    def test_reserved_roster_actor_does_not_create_identity(self):
        for actor in (0, 0xffffffff):
            result = self.read(identity(actor=actor))
            self.assertEqual(result.external_id_histories, ())
            row, = result.unassigned_external_id_observations
            self.assertEqual(row.status, 'reserved_actor')
            self.assertEqual(row.raw_actor_id, actor)
            self.assertEqual(row.raw_value_hex, b'raw-external-id'.hex())

    def test_complete_selection_and_roster_agree(self):
        result = self.read(identity(team=0xa1) + selection(team=0xb1) + selection())
        selected = result.selection
        self.assertEqual(selected.status, 'observed')
        self.assertEqual(selected.roster_consistency, 'consistent')
        self.assertEqual((selected.recording_selected_actor_id, selected.recording_selected_team_id), (1500, 1))
        self.assertEqual(selected.observations[0].raw_team_byte, 0xb1)
        self.assertEqual(selected.observations[0].team_id, 1)

    def test_sentinel_team_one_is_never_selection(self):
        for actor in (0, 0xffffffff):
            for prefix in (b'', selection()):
                result = self.read(identity() + prefix + selection(actor))
                self.assertEqual(result.selection.status, 'unresolved')
                self.assertIsNone(result.selection.recording_selected_actor_id)
                self.assertIsNone(result.selection.recording_selected_team_id)
                self.assertEqual(result.selection.observations[-1].raw_actor_id, actor)
                self.assertEqual(result.selection.observations[-1].raw_team_byte, 1)

    def test_supported_then_unsupported_selection_is_incomplete(self):
        for length in (0, 4, 100, 102, 107):
            with self.subTest(length=length):
                result = self.read(identity() + selection() + selection(length=length))
                self.assertEqual(result.selection.status, 'incomplete')
                self.assertIsNone(result.selection.recording_selected_actor_id)
                self.assertIsNone(result.selection.recording_selected_team_id)
                self.assertEqual(result.selection.observations[-1].payload_length, length)
                self.assertEqual(len(result.selection.observations[-1].raw_payload_hex), length * 2)

    def test_unsupported_team_is_visible_and_unresolved(self):
        result = self.read(identity() + selection(team=0xff))
        self.assertEqual(result.selection.status, 'unresolved')
        self.assertEqual(result.selection.observations[0].team_id, 15)
        self.assertIsNone(result.selection.recording_selected_team_id)

    def test_changing_actor_or_team_never_returns_scalar(self):
        for later in (selection(1501), selection(team=2)):
            result = self.read(identity() + identity(1501) + selection() + later)
            self.assertEqual(result.selection.status, 'changing_selection')
            self.assertIsNone(result.selection.recording_selected_actor_id)
            self.assertIsNone(result.selection.recording_selected_team_id)

    def test_roster_conflict_missing_or_unsupported_never_corroborates(self):
        for roster_data, status, consistency in (
            (b'', 'uncorroborated', 'missing_roster'),
            (identity(team=2), 'conflicting_roster', 'conflict'),
            (identity() + identity(team=2), 'conflicting_roster', 'conflict'),
            (identity() + packet(0x03ee, b'x'), 'incomplete', 'incomplete'),
        ):
            with self.subTest(status=status):
                result = self.read(roster_data + selection())
                self.assertEqual(result.selection.status, status)
                self.assertEqual(result.selection.roster_consistency, consistency)
                self.assertIsNone(result.selection.recording_selected_actor_id)

    def test_missing_selection_is_explicit(self):
        self.assertEqual(self.read(identity()).selection.status, 'missing')

    def test_cutoff_uses_same_boundary_and_full_source_hash(self):
        data = anchor() + identity() + selection() + identity(value=b'future', time=2) + selection(1501, time=2)
        frames = [(0, data)]
        for cutoff in (RecordTime(1), GameTime(101)):
            result = read_recording_identity(frames, cutoff)
            self.assertEqual(result.selection.status, 'observed')
            self.assertEqual(len(result.external_id_histories[0].observations), 1)
            self.assertEqual(result.record_boundary, (0, len(anchor() + identity())))
            self.assertEqual(result.replay_scope, frame_scope(frames))
            self.assertEqual(result.sources[0].sha256, hashlib.sha256(data).hexdigest())
            self.assertEqual(result.sources[0].size_bytes, len(data))
        self.assertEqual(read_recording_identity(frames).selection.status, 'changing_selection')

    def test_malformed_future_input_does_not_bypass_query_audit(self):
        result = read_recording_identity([(0, anchor() + identity() + selection() + b'bad')], RecordTime(0))
        self.assertEqual(result.query_status, 'malformed_records')
        self.assertEqual(result.external_id_histories, ())
        self.assertEqual(result.selection.status, 'unavailable')
        self.assertIsNone(result.record_boundary)

    def test_invalid_query_preserves_source_evidence_not_interpretation(self):
        data = anchor() + identity()
        for frames, cutoff in (([], None), ([(0, data)], GameTime(999)),
                               ([(0, data), (2, data)], None),
                               ([(0, data), (0, data)], None)):
            result = read_recording_identity(frames, cutoff)
            self.assertNotEqual(result.query_status, 'accepted')
            self.assertEqual(result.selection.status, 'unavailable')
            self.assertEqual(result.external_id_histories, ())
            self.assertEqual(len(result.sources), len(frames))

    def test_paused_clock_nonprefix_query_cannot_leak_later_evidence(self):
        frames = [(0, anchor(0, 0) + identity() + selection() + identity(value=b'later', time=9)),
                  (1, anchor(10, 0) + selection(1501, time=11))]
        result = read_recording_identity(frames, GameTime(1))
        self.assertEqual(result.query_status, 'ambiguous_game_time')
        self.assertIsNone(result.record_boundary)
        self.assertEqual(result.external_id_histories, ())
        self.assertEqual(result.selection.status, 'unavailable')
        recorded = read_recording_identity(frames, RecordTime(9))
        self.assertEqual(len(recorded.external_id_histories[0].observations), 2)
        self.assertEqual(recorded.selection.recording_selected_actor_id, 1500)

    def test_forward_clock_jump_keeps_record_query_but_rejects_game_query(self):
        frames = [(0, anchor(0, 0) + identity() + selection()),
                  (1, anchor(10, 21) + identity(value=b'later', time=11))]
        for cutoff in (None, RecordTime(11)):
            result = read_recording_identity(frames, cutoff)
            self.assertEqual(result.query_status, 'accepted')
            self.assertEqual(len(result.external_id_histories[0].observations), 2)
            self.assertEqual(result.selection.status, 'observed')
            self.assertEqual(result.record_boundary, (1, len(anchor(10, 21))))
        result = read_recording_identity(frames, GameTime(1))
        self.assertEqual(result.query_status, 'unsupported_clock')
        self.assertEqual(result.external_id_histories, ())
        self.assertEqual(result.selection.status, 'unavailable')

    def test_nonzero_start_is_partial_not_complete_selection(self):
        result = read_recording_identity([(1, anchor() + identity() + selection())])
        self.assertEqual(result.selection.status, 'incomplete')
        self.assertEqual(result.external_id_evidence_status, 'incomplete')
        self.assertEqual(result.completeness_status, 'unknown')

    def test_record_scope_changes_with_bytes_and_keeps_actor_local(self):
        first = self.read(identity(value=b'first'))
        second = self.read(identity(value=b'second'))
        self.assertNotEqual(first.replay_scope, second.replay_scope)
        self.assertEqual(first.external_id_histories[0].native_actor_id,
                         second.external_id_histories[0].native_actor_id)
        self.assertNotEqual(first.external_id_histories[0].candidates, second.external_id_histories[0].candidates)

    def test_lookalike_bytes_inside_other_opcode_are_not_observations(self):
        result = self.read(packet(0x7777, identity() + selection()))
        self.assertEqual(result.external_id_histories, ())
        self.assertEqual(result.selection.status, 'missing')

    def test_additive_roster_path_retains_original_raw_history(self):
        data = identity() + spawn() + identity(value=b'', length=216)
        result = read_native_roster([(0, anchor() + data)])
        self.assertTrue(result.valid)
        rows = result.players[0].observations
        self.assertEqual(len(rows), 2)
        self.assertEqual(bytes.fromhex(rows[0].raw_payload_hex)[64:80], b'raw-external-id\0')
        self.assertEqual(bytes.fromhex(rows[1].raw_payload_hex)[64:128], bytes(64))
        self.assertEqual(result.recording_identity.record_boundary, result.record_boundary)
        # Previously valid positional construction is still valid.
        self.assertIsNone(NativeRosterResult(True, 'accepted', 'test').recording_identity)
        base = asdict(read_native_roster([(0, anchor() + roster() + spawn())]))
        changed = asdict(read_native_roster([(0, anchor() + roster() + spawn() + selection(0xffffffff))]))
        for key in ('recording_identity', 'record_boundary'):
            base.pop(key)
            changed.pop(key)
        self.assertEqual(base, changed)


if __name__ == '__main__':
    unittest.main()
