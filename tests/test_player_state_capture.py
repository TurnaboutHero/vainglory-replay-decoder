from copy import deepcopy
import hashlib
import json
from pathlib import Path
import struct
import tempfile
import unittest

from vg.tools.player_state_capture.__main__ import challenge, main
from vg.tools.player_state_capture.evidence import (export_reference, import_capture, inspect_native,
    metadata, native_float, publish, read_json, verify_capture)
from vg.tools.player_state_capture.guards import (CaptureError, require_backup, require_process,
    require_session)
from vg.tools.player_state_capture.alignment import align_capture, reader_boundary

SHA = 'd6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc'
IDENTITY = {'pid': 100, 'create_time': 10.5, 'exe': 'D:/owned/Vainglory.exe', 'sha256': SHA}


def fixture(root):
    root = Path(root)
    def save(name, value, lines=False):
        path = root / name
        path.write_text('\n'.join(json.dumps(row) for row in value) if lines else json.dumps(value))
        return path
    source = root / 'source.0.vgr'
    source.write_bytes(b'original fixture bytes')
    (root / 'shot.png').write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00\x00\x00\rIHDR' + struct.pack('>II', 1, 1))
    raw = {'value': 0, 'bits': 0}
    player = {'native_actor_id': 1500, 'display_name': 'Player', 'definition_id': 256,
              'kills': raw, 'deaths': raw, 'assists': raw, 'resource14': raw,
              'gold_balance': {'value': 1, 'bits': 0x3f800000},
              'net_worth': {'value': 2, 'bits': 0x40000000},
              'inventory': {'capacity': 8, 'occupied': 2,
                            'items': [{'definition_id': 101, 'quantity': 1}, {'definition_id': 101, 'quantity': 1}] + [None]*6}}
    sample = {'tag': 'player_state_sample', 'sequence': 1, 'pid': 100,
              'game_clock': {'value': 10, 'bits': 0x41200000}, 'roster_count': 1,
              'atomic_record_boundary': False, 'players': [player]}
    rows = [dict(IDENTITY, tag='identity'), {'tag': 'rpc_ready', 'result': {'guards': 3, 'passive': True}},
            {'payload': sample}, {'tag': 'observation_end', 'failed': False}, {'tag': 'detached'}]
    native = save('native.jsonl', rows, lines=True)
    actions = save('actions.jsonl', [{'command': {'op': 'shot'}, 'result': {'state': {'owned_pid': 100},
                    'shot': {'pid': 100, 'path': 'D:/owned/shot.png'}}}], lines=True)
    spec = {'capture_id': 'fixture', 'recording_id': 'C33', 'partition': 'development', 'trial': 'fixture',
            'process': dict(IDENTITY), 'source_files': [metadata(source, section=0)],
            'native_artifact_id': 'native', 'sample_sequence': 1, 'alignment': {'kind': 'unverified'},
            'artifacts': [metadata(native, artifact_id='native', role='native'),
                          metadata(actions, artifact_id='actions', role='actions'),
                          metadata(root / 'shot.png', artifact_id='shot', role='screenshot')]}
    return save('spec.json', spec), spec, rows


class CaptureGuardTests(unittest.TestCase):
    def assert_code(self, code, call):
        with self.assertRaises(CaptureError) as caught:
            call()
        self.assertEqual(caught.exception.code, code)

    def test_locked_desktop(self):
        row = {'level': 1, 'session_id': 1, 'session_state': 0, 'session_flags': 0,
               'bytes': 100, 'expected_bytes': 100, 'os_version': [10, 0, 19045]}
        self.assert_code('session_unavailable', lambda: require_session(row))
        row['session_flags'] = 1
        require_session(row)

    def test_executable_hash_changed(self):
        self.assert_code('executable_identity_mismatch',
                         lambda: require_process(IDENTITY, dict(IDENTITY, sha256='0'*64), [100]))

    def test_foreign_pid_and_reused_pid(self):
        self.assert_code('foreign_process', lambda: require_process(IDENTITY, IDENTITY, [100, 101]))
        self.assert_code('process_identity_mismatch',
                         lambda: require_process(IDENTITY, dict(IDENTITY, create_time=11), [100]))

    def test_backup_conflict_and_modified_bytes(self):
        backup = {'slot_name': 'owned', 'files': [{'name': 'owned.0.vgr', 'sha256': 'a'*64}]}
        self.assert_code('backup_conflict', lambda: require_backup(backup, {'owned.0.vgr': 'a'*64}, [], True))
        self.assert_code('backup_hash_changed', lambda: require_backup(backup, {'owned.0.vgr': 'b'*64}, []))
        self.assert_code('game_still_running', lambda: require_backup(backup, {'owned.0.vgr': 'a'*64}, [100]))

    def test_backup_path_escape(self):
        backup = {'slot_name': 'owned', 'files': [{'name': '../foreign.0.vgr', 'sha256': 'a'*64}]}
        self.assert_code('invalid_slot', lambda: require_backup(backup, {'../foreign.0.vgr': 'a'*64}, []))

    def test_windows_path_case_is_not_process_conflict(self):
        require_process(IDENTITY, dict(IDENTITY, exe='d:\\OWNED\\Vainglory.exe'), [100])


class CaptureEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.spec_path, self.spec, self.rows = fixture(self.root)
        self.dest = self.root / 'capture'

    def save_spec(self):
        self.spec_path.write_text(json.dumps(self.spec))

    def test_unaligned_import_preserves_observation_only(self):
        result = import_capture(self.spec_path, self.dest)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['status'], 'observation_only')
        self.assertFalse(result['alignment_verified'])
        self.assertTrue((self.dest / 'freeze.json').is_file())

    def test_lobby_samples_are_not_truth(self):
        self.rows[2]['payload'].update(game_clock=None, roster_count=0, players=[])
        path = self.root / 'lobby.jsonl'
        path.write_text('\n'.join(json.dumps(r) for r in self.rows))
        with self.assertRaisesRegex(CaptureError, 'No sample') as caught:
            inspect_native(path)
        self.assertEqual(caught.exception.code, 'no_observation')

    def test_missing_detach_and_script_error_fail(self):
        for rows, expected in [(self.rows[:-1], 'native_detach_missing'),
                               (self.rows + [{'tag': 'script_error'}], 'native_observer_failed')]:
            with self.subTest(expected=expected):
                path = self.root / 'bad.jsonl'
                path.write_text('\n'.join(json.dumps(r) for r in rows))
                with self.assertRaises(CaptureError) as caught:
                    inspect_native(path)
                self.assertEqual(caught.exception.code, expected)

    def test_duplicate_and_foreign_actor_sample_fail(self):
        for patch, expected in [({'players': self.rows[2]['payload']['players'] * 2, 'roster_count': 2}, 'actor_identity_invalid'),
                                ({'pid': 200}, 'foreign_process')]:
            rows = deepcopy(self.rows)
            rows[2]['payload'].update(patch)
            path = self.root / 'bad.jsonl'
            path.write_text('\n'.join(json.dumps(r) for r in rows))
            with self.assertRaises(CaptureError) as caught:
                inspect_native(path)
            self.assertEqual(caught.exception.code, expected)

    def test_missing_cleanup_cannot_pass_restored_gate(self):
        import_capture(self.spec_path, self.dest)
        result = verify_capture(self.dest, require_restored=True)
        self.assertFalse(result['ok'])
        self.assertEqual(result['errors'][0]['code'], 'cleanup_missing')

    def test_changed_hash_refuses_import_without_writes(self):
        (self.root / 'source.0.vgr').write_bytes(b'changed')
        with self.assertRaises(CaptureError):
            import_capture(self.spec_path, self.dest)
        self.assertFalse(self.dest.exists())

    def test_capture_output_never_overwrites(self):
        import_capture(self.spec_path, self.dest)
        frozen = (self.dest / 'capture.json').read_bytes()
        with self.assertRaises(CaptureError):
            import_capture(self.spec_path, self.dest)
        self.assertEqual((self.dest / 'capture.json').read_bytes(), frozen)

    def test_mutations_reject_without_changing_originals(self):
        import_capture(self.spec_path, self.dest)
        original = (self.dest / 'capture.json').read_bytes()
        for mutation in ('native-hash', 'foreign-pid', 'missing-screenshot'):
            self.assertTrue(challenge(self.dest, mutation)['ok'])
        self.assertEqual((self.dest / 'capture.json').read_bytes(), original)

    def test_unsupported_boundary_assertion_fails(self):
        self.spec['alignment'] = {'kind': 'recorded_end_paused', 'artifact_id': 'invented'}
        self.save_spec()
        result = import_capture(self.spec_path, self.dest)
        self.assertFalse(result['ok'])
        self.assertEqual(result['errors'][0]['code'], 'boundary_unproved')

    def test_float_bits_are_exact_and_finite(self):
        self.assertEqual(native_float({'value': 1, 'bits': 0x3f800000})['float32_bits'], '3f800000')
        for raw in ({'value': 2, 'bits': 0x3f800000}, {'value': float('nan'), 'bits': 0x7fc00000}):
            with self.assertRaises(CaptureError):
                native_float(raw)

    def test_report_source_alias_is_rejected(self):
        with self.assertRaises(ValueError):
            publish(self.spec_path, {'replacement': True}, [self.spec_path])
        self.assertEqual(read_json(self.spec_path)['capture_id'], 'fixture')

    def test_export_unaligned_requires_actual_cleanup_first(self):
        import_capture(self.spec_path, self.dest)
        with self.assertRaises(CaptureError) as caught:
            export_reference(self.dest, self.root / 'registry.json', self.root / 'export')
        self.assertEqual(caught.exception.code, 'capture_invalid')
        self.assertFalse((self.root / 'export').exists())

    def test_cli_verify_writes_real_report(self):
        import_capture(self.spec_path, self.dest)
        output = self.root / 'report.json'
        self.assertEqual(main(['verify', '--capture-dir', str(self.dest), '--output', str(output)]), 0)
        self.assertEqual(read_json(output)['native']['sample_count'], 1)

    def add_cleanup(self):
        def add(name, role, value):
            path = self.root / (name + '.json')
            path.write_text(json.dumps(value))
            self.spec['artifacts'].append(metadata(path, artifact_id=name, role=role))
        original = self.root / 'owned.0.vgr'
        original.write_bytes(b'original slot')
        ref = metadata(original)
        file = {'name': original.name, 'sha256': ref['sha256'],
                'last_write_utc': '2026-10-04T00:00:00+00:00', 'creation_utc': '2026-10-04T00:00:00+00:00'}
        self.spec['artifacts'].append(dict(ref, artifact_id='original', role='original_backup'))
        add('backup', 'slot_backup', {'slot_name': 'owned', 'owned_game_pid': 100, 'files': [file]})
        add('restored', 'slot_restored', {'all_backup_hashes_match': True, 'other_groups_touched': False,
                                        'restored_frames': 1, 'trial': 'fixture'})
        add('worker-cleanup', 'worker_cleanup', {'worker_absent': True, 'task_absent': True})
        add('worker-exited', 'worker_exited', {'state': {'owned_pid': 100, 'owned_alive': False}})
        add('readback', 'restored_inventory', {'old_owned_game_pid': 100, 'old_owned_game_pid_absent': True,
            'old_worker_observer_processes': [], 'trials': [{'trial': 'fixture', 'files': [dict(file, exists=True)]}]})

    def add_boundary(self):
        proof = {'producer': 'client_native', 'pid': 100, 'create_time': 10.5, 'sample_sequence': 1,
                 'loaded_source_files': [{'section': 0, 'sha256': self.spec['source_files'][0]['sha256']}],
                 'record_boundary': {'section': 0, 'record_offset': 0}, 'phase': 'after_apply',
                 'native_paused': True, 'native_recorded_end': True, 'game_clock_bits': 0x41200000}
        self.rows.insert(-2, {'payload': dict(proof, tag='player_state_boundary')})
        native = self.root / 'native.jsonl'
        native.write_text('\n'.join(json.dumps(r) for r in self.rows))
        self.spec['artifacts'][0].update(metadata(native))
        proof['native_log_sha256'] = self.spec['artifacts'][0]['sha256']
        path = self.root / 'boundary.json'
        path.write_text(json.dumps(proof))
        self.spec['artifacts'].append(metadata(path, artifact_id='boundary', role='native_boundary'))
        self.spec['alignment'] = {'kind': 'recorded_end_paused', 'artifact_id': 'boundary'}

    def test_complete_cleanup_requires_exact_timestamp_readback(self):
        self.add_cleanup()
        self.save_spec()
        import_capture(self.spec_path, self.dest)
        self.assertTrue(verify_capture(self.dest, require_restored=True)['restoration_verified'])
        changed = read_json(self.dest / 'capture.json')
        ref = next(r for r in changed['artifacts'] if r['role'] == 'restored_inventory')
        path = Path(ref['path'])
        row = read_json(path)
        row['trials'][0]['files'][0]['creation_utc'] = 'different'
        path.write_text(json.dumps(row))
        ref.update(metadata(path))
        result = verify_capture(self.dest, require_restored=True, capture_override=changed)
        self.assertEqual(result['errors'][0]['code'], 'restore_mismatch')

    def test_native_eof_export_preserves_duplicates_and_missing_semantics(self):
        self.add_cleanup()
        self.add_boundary()
        self.save_spec()
        import_capture(self.spec_path, self.dest)
        self.assertEqual(verify_capture(self.dest, True)['status'], 'aligned')
        registry = self.root / 'registry.json'
        registry.write_text(json.dumps({'schema_version': 'player_state.reference.v1', 'reference_sources': [],
            'recordings': [{'recording_id': 'C33', 'partition': 'development', 'source_files': self.spec['source_files'],
                            'observations': []}]}))
        (self.root / 'freeze.json').write_text(json.dumps({'manifest': metadata(registry)}))
        result = export_reference(self.dest, registry, self.root / 'export')
        self.assertTrue(result['ok'])
        observation = read_json(self.root / 'export/manifest.json')['recordings'][0]['observations'][0]
        self.assertEqual(observation['clock_kind'], 'recorded_end')
        self.assertNotIn('game_time', observation)
        fields = observation['players'][0]['fields']
        self.assertEqual(len(fields['native_items']['value']), 2)
        self.assertEqual(fields['items']['status'], 'unobserved')
        self.assertEqual(fields['gold_balance']['value']['float32_bits'], '3f800000')
        self.assertEqual(fields['minion_kills']['value'], 0)
        self.assertEqual(fields['hero']['status'], 'unobserved')
        with self.assertRaises(CaptureError) as caught:
            export_reference(self.dest, registry, self.root / 'record-export', query_clock='record_time')
        self.assertEqual(caught.exception.code, 'boundary_unproved')
        self.assertFalse((self.root / 'record-export').exists())

    def export_inventory(self, items, occupied):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.spec_path, self.spec, self.rows = fixture(self.root)
        self.dest = self.root / 'capture'
        self.rows[2]['payload']['players'][0]['inventory'].update(
            occupied=occupied, items=items + [None] * (8 - len(items)))
        self.add_cleanup()
        self.add_boundary()
        self.save_spec()
        import_capture(self.spec_path, self.dest)
        registry = self.root / 'registry.json'
        registry.write_text(json.dumps({'schema_version': 'player_state.reference.v1', 'reference_sources': [],
            'recordings': [{'recording_id': 'C33', 'partition': 'development', 'source_files': self.spec['source_files'],
                            'observations': []}]}))
        (self.root / 'freeze.json').write_text(json.dumps({'manifest': metadata(registry)}))
        return export_reference(self.dest, registry, self.root / 'export')

    def test_zero_native_quantity_is_exported_and_still_occupies_a_pointer(self):
        items = [{'definition_id': 101, 'quantity': 0}, {'definition_id': 101, 'quantity': 1}]
        self.assertTrue(self.export_inventory(items, 2)['ok'])
        observation = read_json(self.root / 'export/manifest.json')['recordings'][0]['observations'][0]
        self.assertEqual(observation['players'][0]['fields']['native_items']['value'],
                         [{'native_item_id': 101, 'quantity': 0}, {'native_item_id': 101, 'quantity': 1}])
        with self.assertRaises(CaptureError) as caught:
            self.export_inventory(items, 1)
        self.assertEqual(caught.exception.code, 'inventory_incomplete')

    def test_invalid_native_item_identity_or_quantity_is_rejected(self):
        for item in ({'definition_id': 101, 'quantity': -1}, {'definition_id': 101, 'quantity': True},
                     {'definition_id': 101, 'quantity': 1.0}, {'definition_id': 101},
                     {'definition_id': 0, 'quantity': 1}, {'definition_id': True, 'quantity': 1}):
            with self.subTest(item=item), self.assertRaises(CaptureError) as caught:
                self.export_inventory([item], 1)
            self.assertEqual(caught.exception.code, 'native_value_invalid')
            self.assertFalse((self.root / 'export').exists())

    def test_restoration_timestamp_formats_preserve_exact_fraction(self):
        from vg.tools.player_state_capture.evidence import utc_timestamp
        self.assertEqual(utc_timestamp('2026-10-04T01:44:11.849008+00:00'),
                         utc_timestamp('2026-10-04T01:44:11.8490080Z'))
        self.assertNotEqual(utc_timestamp('2026-10-04T01:44:11.849008+00:00'),
                            utc_timestamp('2026-10-04T01:44:11.8490081Z'))

    def test_external_boundary_claim_without_native_event_rejected(self):
        self.add_boundary()
        self.rows = [r for r in self.rows if r.get('payload', {}).get('tag') != 'player_state_boundary']
        native = self.root / 'native.jsonl'
        native.write_text('\n'.join(json.dumps(r) for r in self.rows))
        self.spec['artifacts'][0].update(metadata(native))
        self.save_spec()
        result = import_capture(self.spec_path, self.dest)
        self.assertEqual(result['errors'][0]['code'], 'boundary_unproved')

    def prepare_reader(self):
        content = struct.pack('>H', 0x03f1) + b'\x01\x02\x03'
        source = self.root / 'source.0.vgr'
        source.write_bytes(struct.pack('>fI', 10, len(content)) + content)
        self.spec['source_files'][0].update(metadata(source))
        reader = {'kind': 'replay', 'object': '0x1000', 'mode': 2,
                  'playback_time': {'value': 10, 'bits': 0x41200000},
                  'buffered_record_time': {'value': 10, 'bits': 0x41200000},
                  'needs_record': 1, 'content_length': len(content), 'content_hex': content.hex(),
                  'section': 1, 'file_open': False, 'slot_name': 'owned-slot'}
        self.rows[2]['payload'].update(replay_reader_before=reader, replay_reader_after=deepcopy(reader),
                                       replay_reader_unchanged=True, game_clock_flags=1)
        native = self.root / 'native.jsonl'
        native.write_text('\n'.join(json.dumps(r) for r in self.rows))
        self.spec['artifacts'][0].update(metadata(native))
        injection = self.root / 'injection.json'
        injection.write_text(json.dumps({'verification': {'ok': True, 'verified_frame_count': 1},
                                         'live_replay': {'oname': 'owned-slot'}}))
        self.spec['artifacts'].append(metadata(injection, artifact_id='injection', role='injection'))
        self.save_spec()

    def test_reader_bytes_establish_native_eof_without_counter_decoder(self):
        self.prepare_reader()
        import_capture(self.spec_path, self.dest)
        aligned = self.root / 'aligned'
        result = align_capture(self.dest, aligned, 1)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['status'], 'aligned')
        self.assertEqual(result['record_boundary'], {'section': 0, 'record_offset': 0})
        self.assertEqual(read_json(self.dest / 'capture.json')['alignment']['kind'], 'unverified')

    def test_pending_or_changing_reader_cannot_be_aligned(self):
        self.prepare_reader()
        artifacts = {r['artifact_id']: r for r in self.spec['artifacts']}
        original = inspect_native(self.root / 'native.jsonl', 1)
        for patch in ({'needs_record': 0}, {'mode': 1, 'section': 0}, {'content_hex': '0000000000'}):
            native = deepcopy(original)
            native['sample']['replay_reader_before'].update(patch)
            native['sample']['replay_reader_after'].update(patch)
            if patch.get('mode') == 1:
                native['sample']['game_clock_flags'] = 0
            with self.assertRaises(CaptureError):
                reader_boundary(self.spec, native, artifacts, self.root)
        native = deepcopy(original)
        native['sample']['replay_reader_after']['section'] += 1
        with self.assertRaises(CaptureError):
            reader_boundary(self.spec, native, artifacts, self.root)

    def test_exhausted_applied_eof_does_not_require_pause(self):
        self.prepare_reader()
        artifacts = {r['artifact_id']: r for r in self.spec['artifacts']}
        native = inspect_native(self.root / 'native.jsonl', 1)
        native['sample']['game_clock_flags'] = 6
        for key in ('replay_reader_before', 'replay_reader_after'):
            native['sample'][key]['mode'] = 1
        proof = reader_boundary(self.spec, native, artifacts, self.root)
        self.assertFalse(proof['native_paused'])
        self.assertTrue(proof['native_reader_exhausted'])

    def prepare_timed_reader(self, cross_section=False, game_time=10):
        self.prepare_reader()
        def record(time, opcode, payload):
            return struct.pack('>fIH', time, len(payload) + 2, opcode) + payload
        anchor = record(0, 0x046f, bytes(64) + struct.pack('>f', 0) + b'\0')
        applied = record(10, 0x03f1, b'applied')
        pending = record(11, 0x03f1, b'pending')
        frames = [anchor + applied, pending] if cross_section else [anchor + applied + pending]
        self.spec['source_files'] = []
        scope = hashlib.sha256(b'vgr-numbered-series-v1\0')
        for number, data in enumerate(frames):
            path = self.root / f'source.{number}.vgr'
            path.write_bytes(data)
            self.spec['source_files'].append(metadata(path, section=number))
            scope.update(struct.pack('>QQ', number, len(data)))
            scope.update(data)
        reader = self.rows[2]['payload']['replay_reader_before']
        reader.update(needs_record=0, section=len(frames)-1, file_open=True,
                      buffered_record_time={'value': 11, 'bits': 0x41300000},
                      content_hex=pending[8:].hex(), content_length=len(pending)-8)
        sample = self.rows[2]['payload']
        sample.update(utc_ms=1000, replay_reader_after=deepcopy(reader),
                      game_clock={'value': game_time, 'bits': struct.unpack('>I', struct.pack('>f', game_time))[0]})
        self.rows[1]['result']['guards'] = 5
        self.rows.insert(3, {'payload': dict(deepcopy(sample), sequence=2, utc_ms=1100)})
        injection = self.root / 'injection.json'
        injection.write_text(json.dumps({'verification': {'ok': True, 'verified_frame_count': len(frames)},
                                         'source_scope': 'sha256:' + scope.hexdigest(),
                                         'live_replay': {'oname': 'owned-slot'}}))
        next(r for r in self.spec['artifacts'] if r['role'] == 'injection').update(metadata(injection))
        self.save_native()
        return {'section': 0, 'record_offset': len(anchor)}

    def save_native(self):
        path = self.root / 'native.jsonl'
        path.write_text('\n'.join(json.dumps(r) for r in self.rows))
        self.spec['artifacts'][0].update(metadata(path))
        self.save_spec()

    def timed_proof(self):
        return reader_boundary(self.spec, inspect_native(self.root / 'native.jsonl', 1),
                               {r['artifact_id']: r for r in self.spec['artifacts']}, self.root)

    def test_paused_pending_boundary_uses_applied_predecessor(self):
        expected = self.prepare_timed_reader()
        import_capture(self.spec_path, self.dest)
        result = align_capture(self.dest, self.root / 'aligned', 1)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['record_boundary'], expected)
        capture = read_json(self.root / 'aligned/capture.json')
        self.assertEqual(capture['alignment']['kind'], 'stable_future_pending_buffer')
        proof = read_json(self.root / 'aligned-alignment/boundary.json')
        self.assertFalse(proof['native_recorded_end'])
        self.assertEqual(proof['stable_sample_sequences'], [1, 2])

    def test_paused_predecessor_across_sections(self):
        expected = self.prepare_timed_reader(cross_section=True)
        self.assertEqual(self.timed_proof()['record_boundary'], expected)

    def test_mode_one_future_buffer_certifies_boundary_without_pause_claim(self):
        expected = self.prepare_timed_reader()
        for row in self.rows[2:4]:
            row['payload']['game_clock_flags'] = 6
            for key in ('replay_reader_before', 'replay_reader_after'):
                row['payload'][key]['mode'] = 1
        self.save_native()
        proof = self.timed_proof()
        self.assertEqual(proof['record_boundary'], expected)
        self.assertFalse(proof['native_paused'])
        self.assertFalse(proof['native_recorded_end'])
        self.assertEqual(proof['stable_sample_sequences'], [1, 2])

    def test_timed_reader_rejects_unsafe_states(self):
        self.prepare_timed_reader()
        original = deepcopy(self.rows)
        for patch in ({'mode': 0}, {'mode': 3}, {'needs_record': 2}, {'file_open': False}, {'section': 99},
                      {'kind': 'not_replay'}, {'playback_time': {'value': 11, 'bits': 0x41300000}},
                      {'playback_time': {'value': 12, 'bits': 0x41400000}},
                      {'content_hex': '0000', 'content_length': 2}):
            with self.subTest(patch=patch):
                self.rows = deepcopy(original)
                for row in self.rows[2:4]:
                    for key in ('replay_reader_before', 'replay_reader_after'):
                        row['payload'][key].update(patch)
                self.save_native()
                with self.assertRaises(CaptureError):
                    self.timed_proof()

    def test_timed_reader_requires_complete_stable_native_samples(self):
        self.prepare_timed_reader()
        original = deepcopy(self.rows)
        for mutation in ('players', 'clock', 'reader', 'single', 'duplicate-sequence', 'time', 'guards'):
            with self.subTest(mutation=mutation):
                self.rows = deepcopy(original)
                sample = self.rows[3]['payload']
                if mutation == 'players':
                    sample['players'][0]['gold_balance'] = {'value': 2, 'bits': 0x40000000}
                elif mutation == 'clock':
                    sample['game_clock'] = {'value': 11, 'bits': 0x41300000}
                elif mutation == 'reader':
                    sample['replay_reader_after']['section'] += 1
                elif mutation == 'single':
                    del self.rows[3]
                elif mutation == 'duplicate-sequence':
                    sample['sequence'] = 1
                elif mutation == 'time':
                    sample['utc_ms'] = 1000
                else:
                    self.rows[1]['result']['guards'] = 3
                self.save_native()
                with self.assertRaises(CaptureError):
                    self.timed_proof()

    def test_timed_reader_rejects_unbound_source_and_ambiguous_record(self):
        self.prepare_timed_reader()
        injection = self.root / 'injection.json'
        receipt = read_json(injection)
        receipt['source_scope'] = 'sha256:' + '0'*64
        injection.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(CaptureError, 'exact original source'):
            self.timed_proof()
        self.prepare_timed_reader_reset()
        source = self.root / 'source.0.vgr'
        raw = source.read_bytes()
        source.write_bytes(raw + raw[-17:])
        self.spec['source_files'][0].update(metadata(source))
        with self.assertRaisesRegex(CaptureError, 'identify one original record'):
            self.timed_proof()

    def prepare_timed_reader_reset(self):
        self.spec_path, self.spec, self.rows = fixture(self.root)
        return self.prepare_timed_reader()

    def test_pending_first_record_has_no_applied_boundary(self):
        self.prepare_timed_reader()
        source = self.root / 'source.0.vgr'
        raw = source.read_bytes()[-17:]
        source.write_bytes(raw)
        self.spec['source_files'][0].update(metadata(source))
        injection = self.root / 'injection.json'
        receipt = read_json(injection)
        receipt['source_scope'] = 'sha256:' + hashlib.sha256(b'vgr-numbered-series-v1\0' + struct.pack('>QQ', 0, len(raw)) + raw).hexdigest()
        injection.write_text(json.dumps(receipt))
        with self.assertRaisesRegex(CaptureError, 'no applied predecessor'):
            self.timed_proof()

    def test_timed_alignment_recomputes_boundary_and_rejects_eof_relabel(self):
        self.prepare_timed_reader()
        import_capture(self.spec_path, self.dest)
        aligned = self.root / 'aligned'
        align_capture(self.dest, aligned, 1)
        capture = read_json(aligned / 'capture.json')
        capture['alignment']['kind'] = 'recorded_end_native'
        self.assertFalse(verify_capture(aligned, capture_override=capture)['ok'])
        capture['alignment']['kind'] = 'stable_future_pending_buffer'
        ref = next(r for r in capture['artifacts'] if r['role'] == 'native_boundary')
        path = Path(ref['path'])
        proof = read_json(path)
        proof['record_boundary']['record_offset'] = 0
        path.write_text(json.dumps(proof))
        ref.update(metadata(path))
        self.assertFalse(verify_capture(aligned, capture_override=capture)['ok'])

    def export_timed_fixture(self, game_time, *, query_clock='game_time', playback_time=10,
                             applied_time=10, via_cli=False):
        expected = self.prepare_timed_reader(game_time=game_time)
        raw_time = {'value': playback_time, 'bits': struct.unpack('>I', struct.pack('>f', playback_time))[0]}
        for row in self.rows[2:4]:
            for key in ('replay_reader_before', 'replay_reader_after'):
                row['payload'][key]['playback_time'] = raw_time
        self.save_native()
        if applied_time != 10:
            source = self.root / 'source.0.vgr'
            raw = bytearray(source.read_bytes())
            struct.pack_into('>f', raw, expected['record_offset'], applied_time)
            source.write_bytes(raw)
            self.spec['source_files'][0].update(metadata(source))
            injection = self.root / 'injection.json'
            receipt = read_json(injection)
            receipt['source_scope'] = 'sha256:' + hashlib.sha256(
                b'vgr-numbered-series-v1\0' + struct.pack('>QQ', 0, len(raw)) + raw).hexdigest()
            injection.write_text(json.dumps(receipt))
            next(r for r in self.spec['artifacts'] if r['role'] == 'injection').update(metadata(injection))
        self.add_cleanup()
        self.save_spec()
        import_capture(self.spec_path, self.dest)
        aligned = self.root / 'aligned'
        align_capture(self.dest, aligned, 1)
        registry = self.root / 'registry.json'
        registry.write_text(json.dumps({'schema_version': 'player_state.reference.v1', 'reference_sources': [],
            'recordings': [{'recording_id': 'C33', 'partition': 'development', 'source_files': self.spec['source_files'],
                            'observations': []}]}))
        (self.root / 'freeze.json').write_text(json.dumps({'manifest': metadata(registry)}))
        if via_cli:
            self.assertEqual(main(['export-reference', '--capture-dir', str(aligned), '--manifest', str(registry),
                                   '--output-dir', str(self.root / 'export'), '--query-clock', query_clock]), 0)
        else:
            export_reference(aligned, registry, self.root / 'export', query_clock=query_clock)
        observation = read_json(self.root / 'export/manifest.json')['recordings'][0]['observations'][0]
        self.assertEqual(observation['record_boundary'], expected)
        return observation

    def test_timed_export_uses_native_clock_and_exact_query_boundary(self):
        observation = self.export_timed_fixture(10)
        self.assertEqual(observation['game_time'], 10)
        self.assertEqual(observation['clock_kind'], 'game_time')

    def test_timed_export_rejects_unselectable_native_prefix_without_writes(self):
        with self.assertRaises(CaptureError) as caught:
            self.export_timed_fixture(9)
        self.assertEqual(caught.exception.code, 'unsupported_game_time_boundary')
        self.assertFalse((self.root / 'export').exists())

    def test_explicit_record_time_export_uses_native_playback_and_preserves_game_clock(self):
        observation = self.export_timed_fixture(9, query_clock='record_time', via_cli=True)
        self.assertEqual(observation['clock_kind'], 'record_time')
        self.assertEqual(observation['record_time'], 10)
        self.assertEqual(observation['observed_game_time'], 9)
        self.assertEqual(observation['observed_game_time_bits'], '41100000')
        self.assertNotIn('game_time', observation)

    def test_record_time_export_rejects_nonmatching_native_playback_prefix(self):
        with self.assertRaises(CaptureError) as caught:
            self.export_timed_fixture(9, query_clock='record_time', playback_time=9)
        self.assertEqual(caught.exception.code, 'unsupported_record_time_boundary')
        self.assertFalse((self.root / 'export').exists())

    def test_record_time_export_rejects_partial_equal_timestamp_boundary(self):
        with self.assertRaises(CaptureError) as caught:
            self.export_timed_fixture(9, query_clock='record_time', applied_time=11)
        self.assertEqual(caught.exception.code, 'unsupported_record_time_boundary')
        self.assertFalse((self.root / 'export').exists())

    def prepare_injected_archive(self, suffix='complete'):
        expected = self.prepare_timed_reader_reset()
        archive = self.root / ('archive-' + suffix)
        archive.mkdir()
        path = archive / 'owned-slot.0.vgr'
        path.write_bytes((self.root / 'source.0.vgr').read_bytes())
        self.spec['artifacts'].append(metadata(path, artifact_id='injected-0', role='injected_section'))
        restored = self.root / 'restored.json'
        restored.write_text(json.dumps({'trial': 'fixture', 'archived_substitution_frames': 1}))
        self.spec['artifacts'].append(metadata(restored, artifact_id='restored', role='slot_restored'))
        injection = self.root / 'injection.json'
        receipt = read_json(injection)
        del receipt['source_scope']
        receipt['verification'].update(source_frame_count=1, target_frame_count=1, source_min_frame=0,
            target_min_frame=0, source_max_frame=0, target_max_frame=0, hash_mismatch_count=0,
            size_mismatch_count=0, missing_target_frames=[], extra_target_frames=[])
        injection.write_text(json.dumps(receipt))
        next(r for r in self.spec['artifacts'] if r['role'] == 'injection').update(metadata(injection))
        self.save_spec()
        return expected, path

    def test_complete_original_injected_archive_binds_legacy_receipt(self):
        expected, path = self.prepare_injected_archive()
        self.assertEqual(self.timed_proof()['record_boundary'], expected)
        import_capture(self.spec_path, self.dest)
        result = align_capture(self.dest, self.root / 'aligned', 1)
        self.assertTrue(result['ok'], result)
        self.assertEqual(result['record_boundary'], expected)

    def test_injected_archive_rejects_missing_extra_renamed_changed_and_bad_receipts(self):
        for mutation in ('missing', 'extra-file', 'duplicate', 'renamed', 'changed', 'restore-count', 'injection-count'):
            with self.subTest(mutation=mutation):
                _, path = self.prepare_injected_archive(mutation)
                ref = next(r for r in self.spec['artifacts'] if r['role'] == 'injected_section')
                if mutation == 'missing':
                    self.spec['artifacts'].remove(ref)
                elif mutation == 'extra-file':
                    (path.parent / 'foreign.0.vgr').write_bytes(path.read_bytes())
                elif mutation == 'duplicate':
                    self.spec['artifacts'].append(dict(ref, artifact_id='duplicate'))
                elif mutation == 'renamed':
                    renamed = path.with_name('foreign.0.vgr')
                    path.rename(renamed)
                    ref.update(metadata(renamed))
                elif mutation == 'changed':
                    path.write_bytes(b'changed injected bytes')
                    ref.update(metadata(path))
                elif mutation == 'restore-count':
                    restored = self.root / 'restored.json'
                    receipt = read_json(restored)
                    receipt['archived_substitution_frames'] = 2
                    restored.write_text(json.dumps(receipt))
                else:
                    injection = self.root / 'injection.json'
                    receipt = read_json(injection)
                    receipt['verification']['target_frame_count'] = 2
                    injection.write_text(json.dumps(receipt))
                with self.assertRaises(CaptureError) as caught:
                    self.timed_proof()
                self.assertEqual(caught.exception.code, 'boundary_source_mismatch')


if __name__ == '__main__':
    unittest.main()
