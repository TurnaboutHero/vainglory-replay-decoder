import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from vg.decoder_v2.validation import build_foundation_report, validate_player_block_claims


class TestDecoderV2Validation(unittest.TestCase):
    @staticmethod
    def _write_truth_fixture(temp_dir: str) -> Path:
        replay_path = Path(temp_dir) / "sample.0.vgr"
        block = bytearray(0xE2)
        block[0:3] = b"\xDA\x03\xEE"
        block[3:3 + len("PlayerOne")] = b"PlayerOne"
        block[0xA5:0xA7] = (57093).to_bytes(2, "little")
        block[0xA9:0xAB] = (0xB801).to_bytes(2, "little")
        block[0xAB:0xAF] = bytes.fromhex("11223344")
        block[0xD5] = 1
        replay_path.write_bytes(bytes(block))

        truth_path = Path(temp_dir) / "truth.json"
        truth_path.write_text(
            json.dumps({"matches": [{
                "replay_name": "sample",
                "replay_file": str(replay_path),
                "match_info": {"duration_seconds": None, "winner": None},
                "players": {"PlayerOne": {"hero_name": "Inara"}},
            }]}), encoding="utf-8",
        )
        return truth_path

    def test_validate_player_block_claims_on_synthetic_truth(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            truth_path = self._write_truth_fixture(temp_dir)
            summary = validate_player_block_claims(str(truth_path))

        self.assertEqual(summary.matches_total, 1)
        self.assertEqual(summary.records_total, 1)
        self.assertEqual(summary.hero_matches, 1)
        self.assertEqual(summary.hero_total, 1)

    def test_build_foundation_report_embeds_decoder_validation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            truth_path = self._write_truth_fixture(temp_dir)
            with patch("vg.decoder_v2.validation.run_validation", return_value={"winner": {"correct": 1, "total": 1}}) as decoder_validation:
                report = build_foundation_report(str(truth_path))
            decoder_validation.assert_called_once_with(str(truth_path), verbose=False)

        self.assertIn("offset_claims", report)
        self.assertIn("event_header_claims", report)
        self.assertIn("current_decoder_validation", report)
        self.assertEqual(report["current_decoder_validation"]["winner"]["correct"], 1)
        self.assertEqual(report["player_block_validation"]["hero_matches"], 1)
        self.assertEqual(report["player_block_validation"]["hero_total"], 1)
        self.assertEqual(report["player_block_validation"]["records_total"], 1)
        self.assertEqual(report["completeness_validation"][0]["replay_name"], "sample")


if __name__ == "__main__":
    unittest.main()
