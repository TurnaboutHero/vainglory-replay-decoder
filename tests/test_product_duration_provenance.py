import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from tests.test_native_stats import anchor, packet, snapshot
from vg.core.stat_evidence import frame_scope
from vg.core.unified_decoder import DecodedMatch, UnifiedDecoder


def replay_bytes(crystal=None, death=None, roster=True):
    data = anchor(0, 100)
    if roster:
        block = bytearray(0xE2)
        block[:3] = b'\xda\x03\xee'
        block[3:12] = b'PlayerOne'
        block[0xA5:0xA7] = (1792).to_bytes(2, 'little')
        block[0xA9:0xAB] = (0xB801).to_bytes(2, 'little')
        block[0xD5] = 1
        data += packet(0, 1, block) + snapshot(0)
    events = []
    if crystal is not None:
        events.append((crystal, 2000))
    if death is not None:
        events.append((death, 7))
    for timestamp, entity in sorted(events):
        data += packet(timestamp, 0x0431, struct.pack('>IH', entity, 0))
        data += packet(timestamp, 1)
    return data + packet(max(crystal or 0, death or 0, 10), 1)


class ProductDurationProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.replay = self.root / 'sample.0.vgr'

    def test_duration_provenance_happy_binary_selection_and_serialization(self):
        # Given each existing duration-selection branch in real framed bytes.
        cases = ((120, 110, 120, 'crystal_death_candidate'),
                 (100, 150, 150, 'last_player_death'),
                 (120, None, 120, 'crystal_death_candidate'),
                 (None, 120, 120, 'last_player_death'))
        for crystal, death, expected, source in cases:
            with self.subTest(crystal=crystal, death=death):
                data = replay_bytes(crystal, death)
                self.replay.write_bytes(data)
                before = hashlib.sha256(data).hexdigest()
                # When the public decoder reads the actual generated file.
                result = UnifiedDecoder(str(self.replay)).decode()
                # Then JSON carries the estimate and source-bound limitations.
                self.assertEqual(result.duration_seconds, expected)
                for payload in (result.to_dict(), json.loads(result.to_json())):
                    provenance = payload['duration_provenance']
                    self.assertEqual(provenance['status'], 'estimated')
                    self.assertEqual(provenance['source'], source)
                    self.assertTrue(provenance['reason'])
                    self.assertEqual(provenance['replay_scope'], frame_scope([(0, data)]))
                    self.assertFalse(provenance['accepted_for_index'])
                self.assertEqual(result.native_stats_status, 'accepted')
                self.assertIsNone(result.winner)
                self.assertIsNone(result.left_team[0].gold_earned)
                self.assertIsNone(result.left_team[0].kills)
                self.assertEqual(hashlib.sha256(self.replay.read_bytes()).hexdigest(), before)

    def test_duration_provenance_happy_truth_override_including_zero(self):
        # Given a valid replay and an explicitly supplied matching truth row.
        data = replay_bytes(crystal=120)
        self.replay.write_bytes(data)
        truth_path = self.root / 'truth.json'
        for duration in (42, 0):
            with self.subTest(duration=duration):
                identity = {'replay_name': 'sample', 'replay_file': str(self.replay)}
                truth_path.write_text(json.dumps({'matches': [dict(identity,
                    match_info={'duration_seconds': duration}, players={})]}))
                before = (self.replay.read_bytes(), truth_path.read_bytes())
                # When truth is applied through the public API.
                result = UnifiedDecoder(str(self.replay)).decode_with_truth(str(truth_path))
                # Then the supplied value has provenance but no final acceptance.
                self.assertEqual(result.duration_seconds, duration)
                for payload in (result.to_dict(), json.loads(result.to_json())):
                    provenance = payload['duration_provenance']
                    self.assertEqual(provenance['status'], 'supplied_truth')
                    self.assertEqual(provenance['source'], str(truth_path))
                    self.assertEqual(provenance['selected_match'], identity)
                    self.assertEqual(provenance['replay_scope'], frame_scope([(0, data)]))
                    self.assertFalse(provenance['accepted_for_index'])
                self.assertIsNone(result.winner)
                self.assertIsNone(result.left_team[0].gold_earned)
                self.assertEqual((self.replay.read_bytes(), truth_path.read_bytes()), before)

    def test_duration_provenance_happy_legacy_positional_constructor(self):
        # Given all 29 legacy positional arguments, including the final evidence.
        evidence = {'replay_scope': 'legacy-scope'}
        values = ('sample', 'sample.0.vgr', '5v5', 'Rise', 5, 12, None,
                  [], [], 1, 12., 2000, [], [], [], 10, 1.2, None, 'unknown',
                  'unavailable', 'no baseline', None, False, False, False,
                  False, 'unverified', 'no final validation', evidence)
        # When a preexisting caller constructs the model positionally.
        result = DecodedMatch(*values)
        # Then legacy positions retain meaning and duration is unverified.
        self.assertEqual(result.duration_seconds, 12)
        self.assertIs(result.recording_evidence, evidence)
        self.assertEqual(result.final_stats_reason, 'no final validation')
        self.assertEqual(result.duration_provenance['status'], 'unknown')
        self.assertFalse(result.duration_provenance['accepted_for_index'])

    def test_duration_provenance_failure_unknown_duration_and_empty_roster(self):
        # Given recordings without a duration candidate, with and without a roster.
        for roster in (True, False):
            with self.subTest(roster=roster):
                data = replay_bytes(roster=roster)
                self.replay.write_bytes(data)
                # When decoding a real recording without a timing candidate.
                result = UnifiedDecoder(str(self.replay)).decode()
                # Then unavailable duration stays null and unaccepted.
                self.assertIsNone(result.duration_seconds)
                self.assertEqual(result.duration_provenance['status'], 'unknown')
                self.assertIsNone(result.duration_provenance['source'])
                self.assertFalse(result.duration_provenance['accepted_for_index'])
                self.assertIsNone(result.winner)
                for player in result.all_players:
                    self.assertIsNone(player.gold_earned)
                    self.assertIsNone(player.kills)
                if not roster:
                    self.assertEqual(result.all_players, [])

    def test_duration_provenance_failure_manual_defaults_are_independent(self):
        # Given callers that supply numbers without duration evidence.
        unknown = DecodedMatch('one', 'one.0.vgr', '5v5', 'Rise', 5)
        numeric = DecodedMatch('two', 'two.0.vgr', '5v5', 'Rise', 5, 120)
        # When serializing these legacy instances.
        payloads = [json.loads(value.to_json()) for value in (unknown, numeric)]
        # Then neither a number nor a missing number implies verified duration.
        self.assertIsNone(payloads[0]['duration_seconds'])
        self.assertEqual(payloads[1]['duration_seconds'], 120)
        for payload in payloads:
            self.assertEqual(payload['duration_provenance']['status'], 'unknown')
            self.assertFalse(payload['duration_provenance']['accepted_for_index'])
        self.assertIsNot(unknown.duration_provenance, numeric.duration_provenance)

    def test_duration_provenance_failure_mixed_clock_never_promotes_estimate(self):
        # Given a binary estimate with a backwards game-time anchor.
        self.replay.write_bytes(replay_bytes(crystal=120))
        (self.root / 'sample.1.vgr').write_bytes(anchor(121, 1) + packet(131, 1))
        # When the public decoder observes conflicting native clock segments.
        result = UnifiedDecoder(str(self.replay)).decode()
        # Then approximate duration does not override native or final withholding.
        self.assertEqual(result.duration_seconds, 120)
        self.assertEqual(result.duration_provenance['status'], 'estimated')
        self.assertFalse(result.duration_provenance['accepted_for_index'])
        self.assertEqual(result.native_stats_status, 'mixed_segments')
        self.assertIsNone(result.data_complete)
        self.assertIsNone(result.winner)
        self.assertIsNone(result.left_team[0].gold_earned)
        self.assertIsNone(result.left_team[0].kills)


if __name__ == '__main__':
    unittest.main()
