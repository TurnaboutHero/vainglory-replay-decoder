import copy
import json
from pathlib import Path
import unittest

from audit_roster_identity import audit


class RosterIdentityAuditTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(Path(__file__).with_name('roster-identity.json').read_text())

    def reject(self, data):
        with self.assertRaises(ValueError):
            audit(data)

    def test_original_evidence(self):
        self.assertTrue(audit(self.data)['ok'])

    def test_player_array_order_is_not_identity(self):
        for bracket in self.data['brackets']:
            bracket['state']['players'].reverse()
            bracket['state']['native_roster'].reverse()
        self.assertEqual([r['actor_id'] for r in audit(self.data)['same_nickname_rows']], [1501, 1502])

    def test_wrong_portrait_is_rejected(self):
        self.data['manual_rows'][0]['portrait_hero'] = 'Lance'
        self.reject(self.data)

    def test_wrong_native_actor_is_rejected(self):
        self.data['controls'][2]['native_roster_row']['native_actor_id'] = 1502
        self.reject(self.data)

    def test_wrong_skin_bits_are_rejected(self):
        self.data['controls'][2]['wrapper']['returned_value'] ^= 1
        self.reject(self.data)

    def test_missing_222_coverage_is_rejected(self):
        self.data['controls'] = [r for r in self.data['controls'] if r['source']['content_length'] == 218]
        self.reject(self.data)

    def test_kda_collision_is_rejected(self):
        for bracket in self.data['brackets']:
            players = bracket['state']['players']
            for key in ('kills', 'deaths', 'assists'):
                players[0][key] = copy.deepcopy(players[1][key])
        self.reject(self.data)

    def test_eof_not_at_end_is_rejected(self):
        self.data['eof_frame']['offset'] -= 1
        self.reject(self.data)

    def test_future_section_is_rejected(self):
        for bracket in self.data['brackets']:
            for key in ('replay_reader_before', 'replay_reader_after'):
                bracket['state'][key]['section'] -= 1
        self.reject(self.data)

    def test_screenshot_outside_bracket_is_rejected(self):
        self.data['brackets'][0]['state']['utc_ms'] = self.data['brackets'][1]['state']['utc_ms']
        self.reject(self.data)

    def test_wrong_screenshot_hash_is_rejected(self):
        self.data['screenshot']['sha256'] = '0' * 64
        self.reject(self.data)

    def test_wrong_dispatch_order_is_rejected(self):
        self.data['controls'][0]['wrapper_line'] = self.data['controls'][0]['consumer_after_line'] + 1
        self.reject(self.data)

    def test_wrong_record_time_bits_are_rejected(self):
        self.data['controls'][0]['source']['time_bits'] ^= 1
        self.reject(self.data)


if __name__ == '__main__':
    unittest.main()
