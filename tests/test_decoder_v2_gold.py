import struct
import unittest
from unittest.mock import patch

from vg.decoder_v2.gold import decode_gold_from_replay
from vg.decoder_v2.models import CompletenessStatus

from tests.test_decoder_v2_decode_match import make_assessment
from tests.test_native_stats import anchor, packet, resource


def _credit(entity_id_be: int, value: float, action: int, sell_flag: int = 0) -> bytes:
    return struct.pack(">fIHIfBB4x", 0.0, 16, 0x041D, entity_id_be, value, action, sell_flag)


class TestDecoderV2Gold(unittest.TestCase):
    def test_native_observation_uses_practice_baseline_and_survives_json(self) -> None:
        import json
        payload = bytearray(746)
        struct.pack_into('>I', payload, 8, 0x1234)
        struct.pack_into('>ff', payload, 286, 30000.0, 30000.0)
        data = anchor(0, 0) + packet(0, 0x03f3, payload)
        data += resource(1, 3, index=6, entity=0x1234)
        data += resource(2, -1000, index=6, entity=0x1234)
        parsed = {'teams': {'left': [{'name': 'p', 'entity_id': 0x3412}], 'right': []}}
        with patch('vg.decoder_v2.gold.VGRParser') as parser, patch(
                'vg.decoder_v2.gold.load_frames', return_value=[(0, data)]):
            parser.return_value.parse.return_value = parsed
            result = decode_gold_from_replay('x.0.vgr', make_assessment(CompletenessStatus.COMPLETE_CONFIRMED))
        output = json.loads(json.dumps(result.to_dict()))
        self.assertTrue(output['native_observation']['valid'])
        self.assertEqual(output['native_observation']['players'], [
            {'entity_id': 0x1234, 'gold_balance': 29003.0, 'net_worth': 30003.0}])
        self.assertEqual(output['native_observation']['as_of_game_time'], 2.0)
        self.assertFalse(output['accepted'])
        self.assertEqual(output['final_validation_status'], 'unverified')

    def test_credit_records_without_native_baseline_withhold_observation(self) -> None:
        parsed = {'teams': {'left': [{'name': 'p', 'entity_id': 0x3412}], 'right': []}}
        data = anchor(0, 0) + resource(1, 100, index=6, entity=0x1234)
        with patch('vg.decoder_v2.gold.VGRParser') as parser, patch(
                'vg.decoder_v2.gold.load_frames', return_value=[(0, data)]):
            parser.return_value.parse.return_value = parsed
            result = decode_gold_from_replay('x.0.vgr', make_assessment(CompletenessStatus.COMPLETE_CONFIRMED))
        self.assertFalse(result.native_observation.valid)
        self.assertEqual(result.native_observation.players, ())
        self.assertFalse(result.accepted)

    def test_decode_gold_observes_income_without_adopting_final_gold(self) -> None:
        parsed = {
            "teams": {
                "left": [{"name": "p1", "team": "left", "entity_id": 0x3412, "hero_name": "Alpha"}],
                "right": [{"name": "p2", "team": "right", "entity_id": 0x7856, "hero_name": "Beta"}],
            },
        }
        data = b"".join(
            [
                _credit(0x1234, 5000.0, 0x06),
                _credit(0x1234, 1000.0, 0x06, sell_flag=0x01),
                _credit(0x1234, -300.0, 0x06),
                _credit(0x5678, 6100.0, 0x06),
                _credit(0x5678, 999.0, 0x0D),
            ]
        )

        with patch("vg.decoder_v2.gold.VGRParser") as parser_cls, patch(
            "vg.decoder_v2.gold.load_frames",
            return_value=[(0, data)],
        ):
            parser_cls.return_value.parse.return_value = parsed
            result = decode_gold_from_replay(
                "sample.0.vgr",
                assessment=make_assessment(CompletenessStatus.COMPLETE_CONFIRMED),
            )

        by_name = {player.player_name: player for player in result.players}
        self.assertFalse(result.accepted)
        self.assertEqual(by_name["p1"].gold, 5600)
        self.assertEqual(by_name["p1"].gold_status, "partial_final_validation_missing")
        self.assertIsNone(by_name["p1"].action_06_sellback_refund)
        self.assertEqual(by_name["p1"].action_06_last_set_value, 1000.0)
        self.assertEqual(by_name["p1"].action_06_set_count, 1)
        self.assertEqual(by_name["p1"].action_06_spent, 300.0)
        self.assertEqual(by_name["p2"].gold, 6700)

    def test_resource_set_is_never_a_refund_or_spending_delta(self) -> None:
        parsed = {"teams": {"left": [{"name": "p", "entity_id": 0x3412}], "right": []}}
        for final_set in (0.0, -30.0, 1100.0):
            data = b''.join([
                _credit(0x1234, 100.0, 6),
                _credit(0x1234, 1200.0, 6, sell_flag=1),
                _credit(0x1234, final_set, 6, sell_flag=1),
                _credit(0x1234, -20.0, 6),
            ])
            with self.subTest(final_set=final_set), patch('vg.decoder_v2.gold.VGRParser') as parser, patch(
                    'vg.decoder_v2.gold.load_frames', return_value=[(0, data)]):
                parser.return_value.parse.return_value = parsed
                result = decode_gold_from_replay('x.0.vgr', make_assessment(CompletenessStatus.COMPLETE_CONFIRMED))
            player = result.players[0]
            self.assertIsNone(player.action_06_sellback_refund)
            self.assertEqual(player.action_06_last_set_value, final_set)
            self.assertEqual(player.action_06_set_count, 2)
            self.assertEqual(player.action_06_income, 100.0)
            self.assertEqual(player.action_06_spent, 20.0)
            self.assertFalse(result.accepted)

    def test_no_set_record_is_not_a_zero_balance_observation(self) -> None:
        parsed = {"teams": {"left": [{"name": "p", "entity_id": 0x3412}], "right": []}}
        with patch('vg.decoder_v2.gold.VGRParser') as parser, patch(
                'vg.decoder_v2.gold.load_frames', return_value=[(0, _credit(0x1234, 100.0, 6))]):
            parser.return_value.parse.return_value = parsed
            result = decode_gold_from_replay('x.0.vgr', make_assessment(CompletenessStatus.COMPLETE_CONFIRMED))
        self.assertIsNone(result.players[0].action_06_last_set_value)
        self.assertEqual(result.players[0].action_06_set_count, 0)

    def test_unrelated_payload_cannot_inflate_credit_income(self) -> None:
        parsed = {"teams": {"left": [{"name": "p", "entity_id": 0x3412}], "right": []}}
        fake = bytes.fromhex("10041d00001234") + struct.pack(">f", 9000.0) + bytes([6, 0])
        data = _credit(0x1234, 100.0, 6) + struct.pack(">fIH", 0.0, len(fake) + 2, 0x9999) + fake
        with patch("vg.decoder_v2.gold.VGRParser") as parser, patch(
            "vg.decoder_v2.gold.load_frames", return_value=[(0, data)],
        ):
            parser.return_value.parse.return_value = parsed
            result = decode_gold_from_replay("sample.0.vgr", make_assessment(CompletenessStatus.COMPLETE_CONFIRMED))
        self.assertEqual(result.players[0].gold, 700)
        self.assertEqual(result.players[0].record_count, 1)

    def test_unsupported_credit_values_do_not_become_zero_estimates(self) -> None:
        parsed = {"teams": {"left": [{"name": "p", "entity_id": 0x3412}], "right": []}}
        valid = _credit(0x1234, 100.0, 6)
        bad_records = (
            _credit(0x1234, float("nan"), 6),
            _credit(0x1234, float("inf"), 6),
            _credit(0x1234, 100.0, 6, sell_flag=2),
            struct.pack(">fIH", 0.0, 15, 0x041D) + valid[10:23],
            struct.pack(">fIH", 0.0, 17, 0x041D) + valid[10:] + b"x",
        )
        for bad in bad_records:
            with self.subTest(payload=bad.hex()), patch("vg.decoder_v2.gold.VGRParser") as parser, patch(
                "vg.decoder_v2.gold.load_frames", return_value=[(0, valid + bad)],
            ):
                parser.return_value.parse.return_value = parsed
                result = decode_gold_from_replay("sample.0.vgr", make_assessment(CompletenessStatus.COMPLETE_CONFIRMED))
                self.assertIsNone(result.players[0].gold)
                self.assertTrue(result.record_issues)

    def test_missing_or_duplicate_ids_do_not_attach_credit_observations(self) -> None:
        for roster in ([{"name": "p"}], [{"name": "p", "entity_id": 0x3412}, {"name": "q", "entity_id": 0x3412}]):
            with self.subTest(roster=roster), patch("vg.decoder_v2.gold.VGRParser") as parser, patch(
                "vg.decoder_v2.gold.load_frames", return_value=[(0, _credit(0x1234, 100.0, 6))],
            ):
                parser.return_value.parse.return_value = {"teams": {"left": roster, "right": []}}
                result = decode_gold_from_replay("sample.0.vgr", make_assessment(CompletenessStatus.COMPLETE_CONFIRMED))
                self.assertFalse(result.accepted)
                self.assertFalse(result.players)
                self.assertTrue(result.record_issues)

    def test_decode_gold_marks_incomplete_as_partial(self) -> None:
        parsed = {
            "teams": {
                "left": [{"name": "p1", "team": "left", "entity_id": 0x3412, "hero_name": "Alpha"}],
                "right": [],
            },
        }
        with patch("vg.decoder_v2.gold.VGRParser") as parser_cls, patch(
            "vg.decoder_v2.gold.load_frames",
            return_value=[(0, _credit(0x1234, 5000.0, 0x06))],
        ):
            parser_cls.return_value.parse.return_value = parsed
            result = decode_gold_from_replay(
                "sample.0.vgr",
                assessment=make_assessment(CompletenessStatus.INCOMPLETE_CONFIRMED),
            )

        self.assertFalse(result.accepted)
        self.assertEqual(result.players[0].gold, 5600)
        self.assertEqual(result.players[0].gold_status, "partial_incomplete_replay")


if __name__ == "__main__":
    unittest.main()
