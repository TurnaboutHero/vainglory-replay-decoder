import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vg.decoder_v2.level_signal_probe import build_level_signal_batch, build_level_signal_probe


def _heartbeat(entity_id_be: int, byte15: int, timestamp: float) -> bytes:
    record = bytearray(32)
    record[0:3] = bytes.fromhex("18043e")
    record[5:7] = entity_id_be.to_bytes(2, "big")
    record[9:11] = entity_id_be.to_bytes(2, "big")
    record[15] = byte15
    struct.pack_into(">f", record, 25, timestamp)
    return bytes(record)


def _credit(entity_id_be: int, value: float, action: int) -> bytes:
    return struct.pack(">fIHIfBB4x", 0.,16,0x041D,entity_id_be,value,action,0)


class TestLevelSignalProbe(unittest.TestCase):
    def test_probe_rejects_byte15_level_plus_12_when_values_exceed_cap(self) -> None:
        parsed = {
            "replay_name": "sample",
            "teams": {
                "left": [{"name": "p1", "entity_id": 0x3412}],
                "right": [],
            },
        }
        frames = [
            (0, _heartbeat(0x1234, 13, 4.0)),
            (1, _heartbeat(0x1234, 14, 5.0)),
            (2, _heartbeat(0x1234, 25, 6.0)),
            (3, _credit(0x1234, 1.0, 0x03)),
        ]

        with patch("vg.decoder_v2.level_signal_probe.VGRParser") as parser_cls, patch(
            "vg.decoder_v2.level_signal_probe.load_frames",
            return_value=frames,
        ), patch(
            "vg.decoder_v2.credit_events.load_frames",
            return_value=[frames[3]],
        ):
            parser_cls.return_value.parse.return_value = parsed
            report = build_level_signal_probe("sample.0.vgr")

        self.assertEqual(report["summary"]["players_with_heartbeat"], 1)
        self.assertEqual(report["summary"]["byte15_level_plus_12_hypothesis"], "rejected")
        self.assertEqual(report["summary"]["credit_action_03_players_with_records"], 1)
        self.assertEqual(report["byte15_level_plus_12_audit"][0]["byte15_inferred_level_max"], 13.0)

    def test_batch_wraps_truth_replays(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            replay_path = Path(temp_dir) / "sample.0.vgr"
            replay_path.write_bytes(b"sample")
            truth_path = Path(temp_dir) / "truth.json"
            truth_path.write_text("{}", encoding="utf-8")
            match = {"replay_name": "sample", "replay_file": str(replay_path)}

            with patch(
                "vg.decoder_v2.level_signal_probe._load_truth_matches",
                return_value=[match],
            ), patch(
                "vg.decoder_v2.level_signal_probe.build_level_signal_probe",
                return_value={
                    "summary": {
                        "viable_level_candidates": 0,
                        "byte15_level_plus_12_hypothesis": "rejected",
                        "heartbeat_records": 3,
                    }
                },
            ):
                report = build_level_signal_batch(str(truth_path))

        self.assertEqual(report["schema_version"], "decoder_v2.level_signal_batch.v1")
        self.assertEqual(report["matches_processed"], 1)
        self.assertEqual(report["summary"]["byte15_rejected_matches"], 1)


if __name__ == "__main__":
    unittest.main()
