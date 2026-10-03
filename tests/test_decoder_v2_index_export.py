import tempfile
import unittest
import json
from pathlib import Path
from unittest.mock import patch

from vg.decoder_v2.index_export import build_index_ready_export


class _FakeDecision:
    def __init__(self, accepted: bool, baseline_0e: int):
        self.accepted = accepted
        self.baseline_0e = baseline_0e

    def to_dict(self):
        return {"accepted": self.accepted, "baseline_0e": self.baseline_0e}


class TestDecoderV2IndexExport(unittest.TestCase):
    def test_build_index_ready_export_withholds_unverified_legacy_final_fields(self) -> None:
        batch = {
            "total_replays": 1,
            "completeness_summary": {"complete_confirmed": 1},
            "matches": [
                {
                    "replay_name": "sample",
                    "replay_file": "sample.0.vgr",
                    "game_mode": "GameMode_HF_Ranked",
                    "map_name": "Halcyon Fold",
                    "team_size": 3,
                    "completeness_status": "complete_confirmed",
                    "accepted_fields": {
                        "winner": {"accepted_for_index": True, "value": "left"},
                        "kills": {"accepted_for_index": True},
                        "gold": {"accepted_for_index": True},
                    },
                    "players": [
                        {
                            "name": "player1",
                            "team": "left",
                            "entity_id": 1,
                            "hero_name": "Alpha",
                            "kills": 1,
                            "deaths": 2,
                            "assists": 3,
                            "gold": 5600,
                            "gold_status": "accepted",
                        }
                    ],
                }
            ],
        }

        with patch("vg.decoder_v2.index_export.decode_replay_batch", return_value=batch):
            export = build_index_ready_export(tempfile.gettempdir())

        match = export["matches"][0]
        player = match["players"][0]
        self.assertEqual(export["schema_version"], "decoder_v2.index_export.v3")
        self.assertEqual((player["name"], player["team"], player["entity_id"], player["hero_name"]),
                         ("player1", "left", 1, "Alpha"))
        self.assertNotIn("winner", match)
        self.assertFalse({"kills", "deaths", "assists", "gold"} & player.keys())
        for field in ("kills", "deaths", "assists", "gold", "winner", "minion_kills"):
            self.assertFalse(match["withheld_fields"][field]["accepted_for_index"])
            self.assertIsNone(match["withheld_fields"][field]["value"])
            self.assertEqual(match["withheld_fields"][field]["evidence_status"], "unverified")
        self.assertEqual(match["kda_source_summary"], {
            "parser_rows": 0, "result_screen_rows": 0, "unresolved_rows": 1,
        })

    def test_build_index_ready_export_reports_nonfinals_candidate_without_export(self) -> None:
        batch = {
            "total_replays": 1,
            "completeness_summary": {"complete_confirmed": 1},
            "matches": [
                {
                    "replay_name": "sample",
                    "replay_file": r"C:\replays\Semis\1\sample.0.vgr",
                    "game_mode": "GameMode_HF_Ranked",
                    "map_name": "Halcyon Fold",
                    "team_size": 3,
                    "completeness_status": "complete_confirmed",
                    "accepted_fields": {
                        "winner": {"accepted_for_index": True, "value": "left"},
                        "kills": {"accepted_for_index": True},
                    },
                    "players": [
                        {
                            "name": "player1",
                            "team": "left",
                            "entity_id": 1,
                            "hero_name": "Alpha",
                            "kills": 1,
                            "deaths": 2,
                            "assists": 3,
                        }
                    ],
                }
            ],
        }

        with patch("vg.decoder_v2.index_export.decode_replay_batch", return_value=batch), patch(
            "vg.decoder_v2.minion_policy.evaluate_player_minion_policy",
            return_value={"player1": _FakeDecision(True, 42)},
        ) as player_candidates:
            export = build_index_ready_export(tempfile.gettempdir(), minion_policy="nonfinals-baseline-0e")

        player_candidates.assert_not_called()
        self.assertEqual(export["minion_policy"], "nonfinals-baseline-0e")
        self.assertNotIn("minion_kills", export["matches"][0]["players"][0])
        self.assertFalse(export["matches"][0]["minion_policy"]["accepted_match"])
        self.assertTrue(export["matches"][0]["minion_policy"]["candidate_match_eligible"])
        self.assertEqual(export["minion_policy_summary"]["accepted_matches"], 0)

    def test_build_index_ready_export_keeps_finals_minion_withheld_under_policy(self) -> None:
        batch = {
            "total_replays": 1,
            "completeness_summary": {"complete_confirmed": 1},
            "matches": [
                {
                    "replay_name": "sample",
                    "replay_file": r"C:\replays\SFC vs Law Enforcers (Finals)\2\sample.0.vgr",
                    "game_mode": "GameMode_HF_Ranked",
                    "map_name": "Halcyon Fold",
                    "team_size": 3,
                    "completeness_status": "complete_confirmed",
                    "accepted_fields": {},
                    "players": [
                        {
                            "name": "player1",
                            "team": "left",
                            "entity_id": 1,
                            "hero_name": "Alpha",
                        }
                    ],
                }
            ],
        }

        with patch("vg.decoder_v2.index_export.decode_replay_batch", return_value=batch), patch(
            "vg.decoder_v2.minion_policy.evaluate_player_minion_policy",
            return_value={"player1": _FakeDecision(False, 42)},
        ) as player_candidates:
            export = build_index_ready_export(tempfile.gettempdir(), minion_policy="nonfinals-baseline-0e")

        player_candidates.assert_not_called()
        self.assertNotIn("minion_kills", export["matches"][0]["players"][0])
        self.assertFalse(export["matches"][0]["minion_policy"]["accepted_match"])

    def test_build_index_ready_export_withholds_experimental_player_candidates(self) -> None:
        batch = {
            "total_replays": 1,
            "completeness_summary": {"complete_confirmed": 1},
            "matches": [
                {
                    "replay_name": "sample",
                    "replay_file": r"C:\replays\SFC vs Law Enforcers (Finals)\2\sample.0.vgr",
                    "game_mode": "GameMode_HF_Ranked",
                    "map_name": "Halcyon Fold",
                    "team_size": 3,
                    "completeness_status": "complete_confirmed",
                    "accepted_fields": {},
                    "players": [
                        {
                            "name": "player1",
                            "team": "left",
                            "entity_id": 1,
                            "hero_name": "Alpha",
                        },
                        {
                            "name": "player2",
                            "team": "right",
                            "entity_id": 2,
                            "hero_name": "Beta",
                        },
                    ],
                }
            ],
        }

        with patch("vg.decoder_v2.index_export.decode_replay_batch", return_value=batch), patch(
            "vg.decoder_v2.minion_policy.evaluate_player_minion_policy",
            return_value={
                "player1": _FakeDecision(True, 42),
                "player2": _FakeDecision(False, 99),
            },
        ) as player_candidates:
            export = build_index_ready_export(
                tempfile.gettempdir(),
                minion_policy="nonfinals-or-low-mixed-ratio-experimental",
            )

        player_candidates.assert_not_called()
        self.assertFalse(export["matches"][0]["minion_policy"]["accepted_match"])
        self.assertEqual(export["matches"][0]["minion_policy"]["accepted_player_count"], 0)
        self.assertNotIn("minion_kills", export["matches"][0]["players"][0])
        self.assertNotIn("minion_kills", export["matches"][0]["players"][1])

    def test_build_index_ready_export_withholds_kda_correction_file(self) -> None:
        batch = {
            "total_replays": 1,
            "completeness_summary": {"complete_confirmed": 1},
            "matches": [
                {
                    "replay_name": "sample",
                    "replay_file": str(Path(tempfile.gettempdir()) / "sample.0.vgr"),
                    "game_mode": "GameMode_HF_Ranked",
                    "map_name": "Halcyon Fold",
                    "team_size": 3,
                    "completeness_status": "complete_confirmed",
                    "accepted_fields": {
                        "winner": {"accepted_for_index": True, "value": "left"},
                        "kills": {"accepted_for_index": True},
                    },
                    "players": [
                        {
                            "name": "player1",
                            "team": "left",
                            "entity_id": 1,
                            "hero_name": "Alpha",
                            "kills": 1,
                            "deaths": 2,
                            "assists": 3,
                        }
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            correction_path = Path(tmp) / "correction.json"
            correction_path.write_text(
                json.dumps(
                    {
                        "replay_name": "sample",
                        "replay_file": str(Path(tempfile.gettempdir()) / "sample.0.vgr"),
                        "players": [
                            {
                                "name": "player1",
                                "corrected_kda": "12/1/4",
                                "kda_correction_status": "name_bound_unique",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with patch("vg.decoder_v2.index_export.decode_replay_batch", return_value=batch):
                export = build_index_ready_export(
                    tempfile.gettempdir(),
                    kda_correction_path=str(correction_path),
                )

        self.assertEqual(export["kda_correction_summary"]["corrected_matches"], 0)
        self.assertEqual(export["kda_correction_summary"]["corrected_rows"], 0)
        self.assertEqual(export["kda_correction_summary"]["withheld_documents"], 1)
        self.assertEqual(export["kda_correction_summary"]["withheld_rows"], 1)
        self.assertFalse({"kills", "deaths", "assists", "kda_source"} & export["matches"][0]["players"][0].keys())
        self.assertEqual(export["matches"][0]["kda_source_summary"]["result_screen_rows"], 0)
        self.assertFalse(export["matches"][0]["kda_correction"]["applied"])
        self.assertEqual(export["matches"][0]["kda_correction"]["status"], "withheld")

    def test_build_index_ready_export_withholds_kda_correction_directory(self) -> None:
        batch = {
            "total_replays": 1,
            "completeness_summary": {"complete_confirmed": 1},
            "matches": [
                {
                    "replay_name": "sample",
                    "replay_file": str(Path(tempfile.gettempdir()) / "sample.0.vgr"),
                    "game_mode": "GameMode_HF_Ranked",
                    "map_name": "Halcyon Fold",
                    "team_size": 3,
                    "completeness_status": "complete_confirmed",
                    "accepted_fields": {
                        "winner": {"accepted_for_index": True, "value": "left"},
                        "kills": {"accepted_for_index": True},
                    },
                    "players": [
                        {
                            "name": "player1",
                            "team": "left",
                            "entity_id": 1,
                            "hero_name": "Alpha",
                            "kills": 1,
                            "deaths": 2,
                            "assists": 3,
                        }
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            bundle_dir = Path(tmp) / "bundle"
            bundle_dir.mkdir()
            (bundle_dir / "result_screen_kda_correction_report.json").write_text(
                json.dumps({"groups": []}),
                encoding="utf-8",
            )
            (bundle_dir / "result_screen_kda_correction_merge.json").write_text(
                json.dumps(
                    {
                        "replay_name": "sample",
                        "replay_file": str(Path(tempfile.gettempdir()) / "sample.0.vgr"),
                        "players": [
                            {
                                "name": "player1",
                                "kills": 9,
                                "deaths": 8,
                                "assists": 7,
                                "kda_correction_status": "name_bound_unique",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with patch("vg.decoder_v2.index_export.decode_replay_batch", return_value=batch):
                export = build_index_ready_export(
                    tempfile.gettempdir(),
                    kda_correction_path=str(bundle_dir),
                )

        self.assertEqual(export["kda_correction_summary"]["corrected_matches"], 0)
        self.assertEqual(export["kda_correction_summary"]["withheld_documents"], 1)
        self.assertEqual(export["kda_correction_summary"]["withheld_rows"], 1)
        self.assertFalse({"kills", "deaths", "assists"} & export["matches"][0]["players"][0].keys())
        self.assertEqual(export["kda_correction_summary"]["ignored_noncorrection_documents"], 1)

    def test_build_index_ready_export_withholds_kda_correction_recursive_directory(self) -> None:
        batch = {
            "total_replays": 1,
            "completeness_summary": {"complete_confirmed": 1},
            "matches": [
                {
                    "replay_name": "sample",
                    "replay_file": str(Path(tempfile.gettempdir()) / "sample.0.vgr"),
                    "game_mode": "GameMode_HF_Ranked",
                    "map_name": "Halcyon Fold",
                    "team_size": 3,
                    "completeness_status": "complete_confirmed",
                    "accepted_fields": {
                        "winner": {"accepted_for_index": True, "value": "left"},
                        "kills": {"accepted_for_index": True},
                    },
                    "players": [
                        {
                            "name": "player1",
                            "team": "left",
                            "entity_id": 1,
                            "hero_name": "Alpha",
                            "kills": 1,
                            "deaths": 2,
                            "assists": 3,
                        }
                    ],
                }
            ],
        }

        with tempfile.TemporaryDirectory() as tmp:
            nested = Path(tmp) / "memory_sessions" / "probe" / "bundle"
            nested.mkdir(parents=True)
            (nested / "result_screen_kda_correction_merge.json").write_text(
                json.dumps(
                    {
                        "replay_name": "sample",
                        "replay_file": str(Path(tempfile.gettempdir()) / "sample.0.vgr"),
                        "players": [
                            {
                                "name": "player1",
                                "kills": 4,
                                "deaths": 5,
                                "assists": 6,
                                "kda_correction_status": "name_bound_unique",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            with patch("vg.decoder_v2.index_export.decode_replay_batch", return_value=batch):
                export = build_index_ready_export(
                    tempfile.gettempdir(),
                    kda_correction_path=str(Path(tmp) / "memory_sessions"),
                )

        self.assertEqual(export["kda_correction_summary"]["corrected_matches"], 0)
        self.assertEqual(export["kda_correction_summary"]["withheld_documents"], 1)
        self.assertEqual(export["kda_correction_summary"]["withheld_rows"], 1)
        self.assertFalse({"kills", "deaths", "assists"} & export["matches"][0]["players"][0].keys())


class TestFinalIndexBoundary(unittest.TestCase):
    def test_legacy_kills_flag_cannot_export_any_final_stat(self) -> None:
        # Given: legacy accepted flags with no source-bound final validation.
        from vg.decoder_v2.models import AcceptedPlayerFields, DecoderV2MatchOutput, FieldDecision
        output = DecoderV2MatchOutput(
            'legacy', 'sample', 'sample.0.vgr', 'mode', 'map', 3,
            'complete_confirmed', 'legacy heuristic',
            {'kills': FieldDecision(None, 'strong', True, 'legacy'),
             'gold': FieldDecision(None, 'strong', True, 'legacy'),
             'winner': FieldDecision('left', 'strong', True, 'legacy')}, {},
            (AcceptedPlayerFields('same', 'left', 1, 'Alpha', 1, 2, 3, 4000),),
        )
        batch = {'total_replays': 1, 'completeness_summary': {}, 'matches': [output.to_dict()]}
        # When: exporting a legacy output at the index boundary.
        with patch('vg.decoder_v2.index_export.decode_replay_batch', return_value=batch):
            report = build_index_ready_export(tempfile.gettempdir())
        # Then: final stats cannot leak, but metadata is preserved.
        row = report['matches'][0]['players'][0]
        self.assertEqual((row['name'], row['entity_id'], row['hero_name']), ('same', 1, 'Alpha'))
        self.assertFalse({'kills', 'deaths', 'assists', 'gold', 'minion_kills'} & row.keys())
        self.assertNotIn('winner', report['matches'][0])

    def test_malformed_correction_json_is_not_silently_ignored(self) -> None:
        # Given: an explicitly supplied invalid correction file.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'correction.json'
            path.write_text('{broken', encoding='utf8')
            # When/Then: malformed JSON fails instead of returning an uncorrected success.
            with patch('vg.decoder_v2.index_export.decode_replay_batch', return_value={
                'total_replays': 0, 'completeness_summary': {}, 'matches': []
            }), self.assertRaises(json.JSONDecodeError):
                build_index_ready_export(tmp, kda_correction_path=str(path))

    def test_capture_never_exports_final_stats_and_preserves_scoped_duplicate_names(self) -> None:
        # Given: two distinct entities sharing a display name in a capture output.
        from vg.decoder_v2.models import AcceptedPlayerFields, DecoderV2MatchOutput, FieldDecision
        scope = 'sha256:' + 'a' * 64
        players = tuple(AcceptedPlayerFields(
            'same', team, raw_id, hero, 1, 2, 3, 4000,
            entity_id_be=native_id, replay_scope=scope, identity_status='resolved',
        ) for team, raw_id, native_id, hero in (
            ('left', 1, 256, 'Alpha'), ('right', 2, 512, 'Beta'),
        ))
        output = DecoderV2MatchOutput(
            'decoder_v2.capture.v2', 'sample', 'sample.0.vgr', 'mode', 'map', 3,
            'complete_confirmed', 'legacy heuristic',
            {field: FieldDecision(None, 'strong', True, 'legacy',
                                  evidence_status='native_capture_observed', scope='capture')
             for field in ('kills', 'deaths', 'assists', 'gold')}, {}, players,
            scope='capture', replay_scope=scope,
        )
        batch = {'total_replays': 1, 'completeness_summary': {}, 'matches': [output.to_dict()]}
        # When: the capture passes through the index boundary.
        with patch('vg.decoder_v2.index_export.decode_replay_batch', return_value=batch):
            report = build_index_ready_export(tempfile.gettempdir())
        # Then: identities remain separate and no statistics become final.
        match = report['matches'][0]
        self.assertEqual(match['source_scope'], 'capture')
        self.assertEqual(match['replay_scope'], scope)
        self.assertEqual([p['entity_id_be'] for p in match['players']], [256, 512])
        self.assertEqual([p['hero_name'] for p in match['players']], ['Alpha', 'Beta'])
        for player in match['players']:
            self.assertEqual(player['replay_scope'], scope)
            self.assertEqual(player['identity_status'], 'resolved')
            self.assertFalse({'kills', 'deaths', 'assists', 'gold'} & player.keys())

    def test_malformed_correction_shapes_raise_specific_input_error(self) -> None:
        from vg.decoder_v2.index_export import CorrectionInputError
        # Given: explicit documents whose shape cannot describe correction rows.
        for payload in ([], {'players': {}}, {'players': [7]}, {'wrong_key': []}):
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / 'correction.json'
                path.write_text(json.dumps(payload), encoding='utf8')
                # When/Then: reject them before decoding any replay.
                with self.assertRaises(CorrectionInputError):
                    build_index_ready_export(tmp, kda_correction_path=str(path))

    def test_malformed_nested_correction_is_not_hidden_by_directory_inventory(self) -> None:
        # Given: an invalid correction nested below a requested directory.
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bundle' / 'result_screen_kda_correction_merge.json'
            path.parent.mkdir()
            path.write_text('{broken', encoding='utf8')
            # When/Then: errors propagate instead of being skipped by inventory selection.
            with self.assertRaises(json.JSONDecodeError):
                build_index_ready_export(tmp, kda_correction_path=tmp)

    def test_cli_correction_failure_keeps_existing_output_and_returns_nonzero(self) -> None:
        from contextlib import redirect_stderr, redirect_stdout
        import io
        from vg.decoder_v2.index_export import main
        # Given: unreadable/invalid correction inputs and a pre-existing output.
        for data in (None, b'\xff', b'{broken', b'{"players": 7}'):
            with self.subTest(data=data), tempfile.TemporaryDirectory() as tmp:
                source = Path(tmp) / 'correction.json'
                output = Path(tmp) / 'output.json'
                output.write_text('keep', encoding='utf8')
                if data is not None:
                    source.write_bytes(data)
                stdout, stderr = io.StringIO(), io.StringIO()
                # When: the CLI receives the explicit correction path.
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    code = main([tmp, '--kda-correction-path', str(source), '-o', str(output)])
                # Then: it cannot claim success or replace the output.
                self.assertEqual(code, 2)
                self.assertEqual(stdout.getvalue(), '')
                self.assertTrue(stderr.getvalue())
                self.assertEqual(output.read_text(encoding='utf8'), 'keep')


if __name__ == "__main__":
    unittest.main()
