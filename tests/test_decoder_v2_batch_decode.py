import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tests.test_native_stats import packet

from vg.decoder_v2.batch_decode import decode_replay_batch, find_replays


class TestDecoderV2BatchDecode(unittest.TestCase):
    def test_find_replays_skips_macosx_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            good = base / "a" / "sample.0.vgr"
            bad = base / "__MACOSX" / "bad.0.vgr"
            good.parent.mkdir(parents=True)
            bad.parent.mkdir(parents=True)
            good.touch()
            bad.touch()

            replays = find_replays(str(base))

        self.assertEqual(replays, [good])

    def test_decode_replay_batch_summarizes_acceptance(self) -> None:
        payload = {
            "completeness_status": "complete_confirmed",
            "accepted_fields": {"hero": {"accepted_for_index": True},
                                "winner": {"accepted_for_index": False, "value": "left"}},
            "withheld_fields": {"duration_seconds": {"accepted_for_index": False}},
        }

        with tempfile.TemporaryDirectory() as temp_dir, patch(
            "vg.decoder_v2.batch_decode.find_replays",
            return_value=[Path(temp_dir) / "one.0.vgr", Path(temp_dir) / "two.0.vgr"],
        ), patch(
            "vg.decoder_v2.batch_decode.decode_match"
        ) as decode_match_mock:
            for name in ('one', 'two'):
                (Path(temp_dir) / f'{name}.0.vgr').write_bytes(packet(0, 1))
            decode_match_mock.return_value.to_dict.return_value = payload
            report = decode_replay_batch(temp_dir)

        self.assertEqual(report["schema_version"], "decoder_v2.batch.v2")
        self.assertEqual(report["total_replays"], 2)
        self.assertNotIn("winner", report["accepted_field_summary"])
        self.assertEqual(report["withheld_field_summary"]["winner"], 2)
        self.assertEqual(report["completeness_summary"]["complete_confirmed"], 2)
        self.assertEqual(report["accepted_field_summary"]["hero"], 2)
        self.assertEqual(report["withheld_field_summary"]["duration_seconds"], 2)


class TestBatchActualAcceptance(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.replay = self.root / 'sample.0.vgr'
        self.replay.write_bytes(packet(0, 1))

    def test_capture_and_false_flags_do_not_count_as_index_acceptance(self) -> None:
        # Given: a capture field, including a legacy true index flag.
        for flag in (False, True):
            with self.subTest(flag=flag):
                payload = {'scope': 'capture', 'completeness_status': 'complete_confirmed',
                           'accepted_fields': {'kills': {'accepted_for_index': flag, 'scope': 'capture'}},
                           'withheld_fields': {}}
                with patch('vg.decoder_v2.batch_decode.find_replays', return_value=[self.replay]), patch(
                    'vg.decoder_v2.batch_decode.decode_match'
                ) as decoder:
                    decoder.return_value.to_dict.return_value = payload
                    # When: counting acceptance.
                    report = decode_replay_batch(str(self.root))
                # Then: capture observations cannot contribute accepted counts.
                self.assertEqual(report['accepted_field_summary'], {})
                self.assertEqual(report['withheld_field_summary'], {'kills': 1})

    def test_partial_fields_and_duplicate_withheld_entries_are_counted_once(self) -> None:
        # Given: a partial observation and a field listed in both diagnostic groups.
        payload = {'scope': 'final', 'completeness_status': 'complete_confirmed',
                   'accepted_fields': {'hero': {'accepted_for_index': True},
                                       'gold': {'accepted_for_index': False, 'claim_status': 'partial'}},
                   'withheld_fields': {'gold': {'accepted_for_index': False}}}
        with patch('vg.decoder_v2.batch_decode.find_replays', return_value=[self.replay]), patch(
            'vg.decoder_v2.batch_decode.decode_match'
        ) as decoder:
            decoder.return_value.to_dict.return_value = payload
            # When: aggregating real acceptance flags.
            report = decode_replay_batch(str(self.root))
        # Then: one accepted metadata field and one withheld partial field.
        self.assertEqual(report['accepted_field_summary'], {'hero': 1})
        self.assertEqual(report['withheld_field_summary'], {'gold': 1})


if __name__ == "__main__":
    unittest.main()
