from copy import deepcopy
import json
from pathlib import Path
import unittest

from audit import audit


class InventoryAuditTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads(Path(__file__).with_name('controls.json').read_text())

    def test_complete_package(self):
        self.assertEqual(audit(self.data)['controls'], 25)

    def test_resolution_from_another_control_rejected(self) -> None:
        frames = self.data['runs'][0]['frames']
        frames[0]['resolution'] = deepcopy(frames[1]['resolution'])
        with self.assertRaises(AssertionError):
            audit(self.data)

    def test_resolution_dispatch_mismatch_rejected(self) -> None:
        self.data['runs'][0]['frames'][0]['resolution']['dispatch_id'] += 1
        with self.assertRaises(AssertionError):
            audit(self.data)

    def test_resolution_action_pointer_mismatch_rejected(self) -> None:
        self.data['runs'][0]['frames'][0]['resolution']['active_hook']['object'] = '0x1'
        with self.assertRaises(AssertionError):
            audit(self.data)

    def test_resolution_handler_mismatch_rejected(self) -> None:
        self.data['runs'][0]['frames'][0]['resolution']['active_hook']['name'] = 'item_set_apply'
        with self.assertRaises(AssertionError):
            audit(self.data)

    def test_consistent_wrong_opcode_handler_rejected(self) -> None:
        frame = self.data['runs'][0]['frames'][0]
        frame['resolution']['active_hook']['name'] = 'item_set_apply'
        for observation in frame['observations'][8:10]:
            observation['payload']['hook'] = 'item_set_apply'
        with self.assertRaises(AssertionError):
            audit(self.data)

    def test_resolved_actor_pointer_mismatch_rejected(self) -> None:
        self.data['runs'][0]['frames'][0]['resolution']['actor'] = '0x1'
        with self.assertRaises(AssertionError):
            audit(self.data)

    def test_missing_actor_nonzero_pointer_rejected(self) -> None:
        frame = self.data['runs'][0]['frames'][-1]
        self.assertFalse(frame['resolution']['present'])
        frame['resolution']['actor'] = frame['snapshots'][0]['primary_fields']['actor']
        with self.assertRaises(AssertionError):
            audit(self.data)

    def test_quantity_corruption_rejected(self):
        self.data['runs'][1]['frames'][0]['actual_after']['live'][0]['item']['quantity'] = 3
        with self.assertRaises(AssertionError):
            audit(self.data)

    def test_queue_pointer_corruption_rejected(self):
        self.data['runs'][0]['frames'][0]['observations'][5]['payload']['heap_action'] = '0x1'
        with self.assertRaises(AssertionError):
            audit(self.data)

    def test_other_player_side_effect_rejected(self):
        self.data['runs'][0]['frames'][0]['snapshots'][1]['other_players_sha256'] = '0' * 64
        with self.assertRaises(AssertionError):
            audit(self.data)

    def test_zero_pointer_retention_corruption_rejected(self):
        frame = self.data['runs'][1]['frames'][1]
        frame['actual_after']['deferred'][0]['item'] = deepcopy(frame['actual_after']['live'][1]['item'])
        frame['actual_after']['live'][1]['item'] = None
        frame['actual_after']['occupied'] -= 1
        with self.assertRaises(AssertionError):
            audit(self.data)


if __name__ == '__main__':
    unittest.main()
