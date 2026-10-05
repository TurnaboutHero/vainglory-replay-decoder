import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from vg.core import native_inventory
from vg.core.native_inventory import DEFINITIONS_PATH, read_native_inventory


def packet(time, opcode, payload=b''):
    return struct.pack('>fIH', time, len(payload) + 2, opcode) + payload


def anchor(time=0, game_time=100, mode=b'*GameMode_5v5_Practice*'):
    payload = bytearray(69)
    payload[:len(mode)] = mode
    struct.pack_into('>f', payload, 64, game_time)
    return packet(time, 0x046f, payload)


def snapshot(time=0, items=(), actor=7, length=746, flag=0):
    payload = bytearray(length)
    struct.pack_into('>I', payload, 8, actor)
    struct.pack_into('>I', payload, 326, flag)
    struct.pack_into('>I', payload, 350, len(items))
    for i, (definition, instance, quantity) in enumerate(items):
        struct.pack_into('>I', payload, 354 + i * 4, definition)
        struct.pack_into('>I', payload, 394 + i * 4, instance)
        struct.pack_into('>I', payload, 434 + i * 4, quantity)
    return packet(time, 0x03f3, payload)


def grant(time=1, definition=458, instance=2000, actor=7, length=14):
    return packet(time, 0x043d, struct.pack('>III', actor, definition, instance) + bytes(length - 12))


def spawn_without_baseline(time=0, actor=7, length=122):
    payload = bytearray(length)
    struct.pack_into('>I', payload, 8, actor)
    return packet(time, 0x03f2, payload)


def consume(time=2, instance=2000, actor=7, length=14):
    return packet(time, 0x044b, struct.pack('>IIH', actor, instance, 1) + bytes(length - 10))


def stack(time=2, instance=2000, quantity=3, actor=7):
    return packet(time, 0x0444, struct.pack('>III', actor, instance, quantity))


def values(result, actor=7):
    player = next(p for p in result.players if p.entity_id == actor)
    return None if player.items is None else [(i.definition_id, i.instance_id, i.quantity) for i in player.items]


def mismatched_catalog(test, **changes):
    """Patch in a copy of the bundled item catalog with altered/removed provenance keys."""
    catalog = json.loads(DEFINITIONS_PATH.read_text(encoding='utf-8'))
    for key, value in changes.items():
        if value is None:
            catalog.pop(key)
        else:
            catalog[key] = value
    temp = tempfile.TemporaryDirectory()
    test.addCleanup(temp.cleanup)
    path = Path(temp.name) / 'native_inventory_definitions.json'
    path.write_text(json.dumps(catalog), encoding='utf-8')
    return patch.object(native_inventory, 'DEFINITIONS_PATH', path)


class NativeInventoryTests(unittest.TestCase):
    def read(self, *records, ids=(7,), **kwargs):
        return read_native_inventory([(0, anchor() + b''.join(records))], ids, **kwargs)

    def test_empty_inventory_differs_from_missing_baseline(self):
        result = self.read(snapshot())
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(values(result), [])
        missing = self.read(grant())
        self.assertEqual(missing.status, 'missing_baseline')
        self.assertIsNone(values(missing))

    def test_actor_creation_does_not_establish_empty_inventory(self):
        for length in (122, 126):
            with self.subTest(length=length):
                result = self.read(spawn_without_baseline(length=length), grant(),
                                   snapshot(2, items=((458, 2000, 1),)))
                self.assertFalse(result.valid)
                self.assertEqual(result.status, 'missing_baseline')
                self.assertIsNone(values(result))

    def test_existing_actor_spawn_preserves_observed_inventory(self):
        result = self.read(snapshot(items=((458, 2000, 1),)), spawn_without_baseline(1),
                           snapshot(2, items=((515, 2001, 1),)))
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(values(result), [(458, 2000, 1)])

    def test_other_actor_creation_does_not_hide_player_baseline(self):
        result = self.read(spawn_without_baseline(actor=8), snapshot(1))
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(values(result), [])

    def test_nonbaseline_actor_cannot_gain_ignored_inventory_snapshot(self):
        result = self.read(snapshot(flag=1), snapshot(1, items=((458, 2000, 1),)))
        self.assertFalse(result.valid)
        self.assertIsNone(values(result))

    def test_native_hud_hidden_names_preserve_possession_and_level_juice(self):
        result = self.read(snapshot(items=((457, 2000, 1), (526, 2001, 1), (515, 2002, 1))))
        player = result.players[0]
        self.assertEqual([item.definition_id for item in player.items], [457, 526, 515])
        self.assertEqual([item.definition_id for item in player.visible_items], [515])
        self.assertEqual(player.visible_items[0].name, 'Level Juice')
        metadata = json.loads(DEFINITIONS_PATH.read_text())['definitions']
        self.assertEqual(metadata['526']['native_name'], 'Vision Totem')
        self.assertEqual(metadata['526']['name'], 'Scout Cam')
        self.assertEqual(self.read(snapshot()).players[0].visible_items, ())
        self.assertIsNone(self.read(grant()).players[0].visible_items)

    def test_duplicate_definitions_preserve_instances(self):
        result = self.read(snapshot(), grant(instance=2000), grant(2, instance=2001))
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(values(result), [(458, 2000, 1), (458, 2001, 1)])

    def test_sale_request_waits_for_exact_consume(self):
        before = [snapshot(items=((458, 2000, 1), (458, 2001, 1))),
                  packet(1, 0x044d, struct.pack('>II', 7, 2000) + bytes(6))]
        self.assertEqual(len(values(self.read(*before))), 2)
        result = self.read(*before, consume(instance=2000))
        self.assertEqual(values(result), [(458, 2001, 1)])

    def test_upgrade_preserves_spare_component(self):
        result = self.read(snapshot(items=((458, 2000, 1), (458, 2001, 1))),
                           consume(instance=2000), grant(3, 505, 2002))
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(values(result), [(505, 2002, 1), (458, 2001, 1)])
        self.assertEqual([i.array_index for i in result.players[0].items], [0, 1])

    def test_consumable_decrements_then_removes(self):
        before = snapshot(items=((481, 2000, 2),))
        self.assertEqual(values(self.read(before, consume())), [(481, 2000, 1)])
        self.assertEqual(values(self.read(before, consume(), consume(3))), [])

    def test_nonstackable_removal_is_not_quantity_subtraction(self):
        self.assertEqual(values(self.read(snapshot(items=((458, 2000, 3),)), consume())), [])

    def test_grant_sentinel_increments_first_nonfull_stack(self):
        result = self.read(snapshot(items=((481, 2000, 5), (481, 2001, 3))),
                           grant(1, 481, 0xffffffff))
        self.assertEqual(values(result), [(481, 2000, 5), (481, 2001, 4)])

    def test_grant_sentinel_without_stack_is_native_noop(self):
        self.assertEqual(values(self.read(snapshot(), grant(1, 481, 0xffffffff))), [])
        full = self.read(snapshot(items=((481, 2000, 5),)), grant(1, 481, 0xffffffff))
        self.assertEqual(values(full), [(481, 2000, 5)])

    def test_stack_replace_narrows_u16_without_removing_zero(self):
        result = self.read(snapshot(items=((481, 2000, 5),)), stack(quantity=65537))
        self.assertEqual(values(result), [(481, 2000, 1)])
        zero = self.read(snapshot(items=((481, 2000, 5),)), stack(quantity=0))
        self.assertEqual(values(zero), [(481, 2000, 0)])
        self.assertEqual(values(self.read(snapshot(items=((481, 2000, 0),)), consume())), [])

    def test_native_unique_definition_rejects_second_instance(self):
        result = self.read(snapshot(items=((457, 2000, 1),)), grant(1, 457, 2001))
        self.assertEqual(values(result), [(457, 2000, 1)])

    def test_original_game_mode_capacity_is_not_assumed_eight(self):
        data = anchor(mode=b'*GameMode_Horde_Casual*') + snapshot(
            items=tuple((458, 2000+i, 1) for i in range(7)))
        result = read_native_inventory([(0, data)], [7])
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(result.players[0].capacity, 6)
        self.assertEqual(len(result.players[0].items), 6)
        unknown = read_native_inventory([(0, anchor(mode=b'*UnobservedMode*') + snapshot())], [7])
        self.assertFalse(unknown.valid)
        self.assertEqual(unknown.status, 'unsupported_configuration')

    def test_capacity_rejects_ninth_instance_without_six_item_capping(self):
        result = self.read(snapshot(items=tuple((458, 2000+i, 1) for i in range(8))),
                           grant(1, 458, 2008))
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(len(values(result)), 8)
        self.assertEqual(result.players[0].capacity, 8)

    def test_baseline_preserves_original_quantity(self):
        result = self.read(snapshot(items=((481, 2000, 4),)))
        self.assertEqual(values(result), [(481, 2000, 4)])

    def test_repeated_baseline_is_existing_actor_noop(self):
        result = self.read(snapshot(items=((458, 2000, 1),)), grant(1, 458, 2001),
                           snapshot(2, items=()), include_transitions=True)
        self.assertEqual(values(result), [(458, 2000, 1), (458, 2001, 1)])
        self.assertFalse(result.transitions[-1].changed)

    def test_seek_from_independent_section_starts_from_its_native_baseline(self):
        result = read_native_inventory([(12, anchor() + snapshot(items=((505, 2005, 1),)))], [7])
        self.assertEqual(values(result), [(505, 2005, 1)])

    def test_definition515_resolves_and_is_not_discarded(self):
        result = self.read(snapshot(items=((515, 2002, 1),)))
        item = result.players[0].items[0]
        self.assertEqual((item.name, item.definition_name), ('Level Juice', 'Item_LevelCandy'))

    def test_activation_and_request_do_not_invent_consumption(self):
        result = self.read(snapshot(items=((515, 2000, 1),)),
                           packet(1, 0x0448, struct.pack('>I', 2000) + bytes(2)),
                           packet(2, 0x044c, struct.pack('>IIIffB', 7, 2000, 0xffffffff, 0, 0, 2) + b'\0'))
        self.assertEqual(values(result), [(515, 2000, 1)])

    def test_embedded_grant_signature(self):
        result = self.read(snapshot(), packet(1, 0xffff, grant(1)))
        self.assertTrue(result.valid, result.reason)
        self.assertEqual(values(result), [])

    def test_unknown_removal_target(self):
        result = self.read(snapshot(items=((458, 2000, 1),)), consume(instance=9999))
        self.assertFalse(result.valid)
        self.assertEqual(result.status, 'unsupported_state')
        self.assertIsNone(values(result))
        self.assertIn('9999', result.reason)

    def test_unknown_definition_is_unavailable_not_dropped(self):
        result = self.read(snapshot(), grant(definition=900000))
        self.assertEqual(result.status, 'unsupported_state')
        self.assertIsNone(values(result))
        self.assertIn('900000', result.reason)

    def test_unrecognized_length_does_not_borrow_known_prefix(self):
        for record in (grant(length=13), consume(length=12), snapshot(length=748)):
            with self.subTest(record=record[:10]):
                result = self.read(snapshot(items=((458, 2000, 1),)), record)
                self.assertEqual(result.status, 'unsupported_state')
                self.assertIsNone(values(result))

    def test_native_and_recorded_lengths_are_explicitly_supported(self):
        for baseline_length in (746, 750):
            for grant_length in (12, 14):
                for consume_length in (10, 14):
                    result = self.read(snapshot(length=baseline_length), grant(length=grant_length), consume(length=consume_length))
                    self.assertTrue(result.valid, result.reason)
                    self.assertEqual(values(result), [])

    def test_high_32bit_actor_is_not_truncated(self):
        actor = 0x12340007
        result = self.read(snapshot(actor=actor), grant(actor=actor), ids=(actor,))
        self.assertEqual(values(result, actor), [(458, 2000, 1)])
        self.assertEqual(result.players[0].entity_id, actor)

    def test_invalid_actor_ids_are_rejected(self):
        for ids in ((True,), (0,), (-1,), (0xffffffff,), (0x100000000,), (7, 7)):
            self.assertEqual(self.read(snapshot(), ids=ids).status, 'invalid_query')

    def test_one_actor_failure_does_not_hide_other_actor_evidence(self):
        result = self.read(snapshot(actor=7), snapshot(actor=8), grant(actor=8, definition=900000), ids=(7, 8))
        self.assertFalse(result.valid)
        self.assertEqual(values(result, 7), [])
        self.assertIsNone(values(result, 8))

    def test_destroy_request_does_not_invent_cleanup(self):
        result = self.read(snapshot(items=((458, 2000, 1),)), packet(1, 0x040b, struct.pack('>I', 7)), snapshot(2))
        self.assertEqual(result.status, 'unsupported_state')
        self.assertIn('cleanup boundary unobserved', result.reason)

    def test_nonzero_spawn_flag_cannot_invent_empty_inventory(self):
        result = self.read(snapshot(flag=1))
        self.assertEqual(result.status, 'unsupported_state')
        self.assertIsNone(values(result))

    def test_mismatched_catalog_withholds_inventory_without_raising(self):
        for changes in ({'build_sha256': '0' * 64}, {'manifest_sha256': '0' * 64},
                        {'schema_version': 'other'}, {'manifest_sha256': None}):
            with self.subTest(changes=changes), mismatched_catalog(self, **changes):
                result = self.read(snapshot(items=((515, 2002, 1),)))
                self.assertFalse(result.valid)
                self.assertEqual(result.status, 'unsupported_catalog')
                self.assertIn('catalog provenance', result.reason)
                self.assertEqual(result.players, ())
        self.assertTrue(self.read(snapshot(items=((515, 2002, 1),))).valid)

    def test_native_metadata_contains_original_asset_provenance(self):
        metadata = json.loads(DEFINITIONS_PATH.read_text())
        self.assertEqual(len(metadata['definitions']), 93)
        for row in metadata['definitions'].values():
            self.assertEqual(len(row['resource_sha256']), 64)
            self.assertTrue(row['name_key'])
            self.assertTrue(row['name'])


if __name__ == '__main__':
    unittest.main()
