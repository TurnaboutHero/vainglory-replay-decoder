from copy import deepcopy
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


if __name__ == '__main__':
    unittest.main()
