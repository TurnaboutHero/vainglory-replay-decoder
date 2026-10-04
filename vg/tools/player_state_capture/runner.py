from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid

from .evidence import digest, import_capture, metadata, publish, read_json
from .guards import identifier, require, require_backup, require_process, require_session
from vg.core.replay_output import ReportInputs, validate_report_outputs

FROZEN_SCRIPTS = {
    'probe.py': '76df8cef512ddcfa9de2906ae3b704449bdf3430021550107c07004ae6411bf5',
    'control.py': '30d23f589e82fdb5b72304aefcf5fdd8fe8f9a26f1e0d423e30276b542c45989',
    'session_state.py': '477b8308af4a82bcbb92fee1677034fb4fc919dcad87c9166ee25bb953d8a2d0',
    'session_guard.py': '8acc483d0fdfe75174242b0b1dcc1814ef28ca76487fa84d6a83c8ef5d9ce050',
    'restore.ps1': 'e1d6203eb4051d951f589cc223c5ff3db7e98c784f1a34461a6b46f271512cff',
    'interactive.py': 'fe151c1b62810b7f47cd9407e9dce9f3e7bcb5e4a6075dc9aa3f9b705fefc5c4',
}
DEPENDENCIES = 'D:/Documents/GitHub/VG_REVERSE_ENGINEERING/work/windows-clock-runtime/deps'
EXECUTABLE = 'D:/Documents/GitHub/VG_REVERSE_ENGINEERING-offline-qa-20261003/replay-stability-20261003/client-laa/Vainglory.exe'


def load_profile(path):
    require(os.name == 'nt', 'unsupported_host', 'The frozen owned-client runner runs locally on Windows')
    profile = read_json(path)
    require(profile.get('profile') == 'winsrv-owned-20261004', 'unsupported_profile', 'Unknown frozen runner profile')
    root = Path(profile['remote_root']).resolve()
    require(root.is_absolute() and root.is_dir(), 'invalid_root', 'Exact existing owned runtime root required')
    for name, expected in FROZEN_SCRIPTS.items():
        require((root / name).is_file() and digest(root / name) == expected,
                'runner_identity_mismatch', f'Frozen runner script differs: {name}')
    require(Path(profile['process']['exe']).resolve() == Path(EXECUTABLE).resolve(),
            'executable_identity_mismatch', 'This frozen runner only supports its original LAA executable path')
    return profile, root


def command(args, root, timeout=15):
    result = subprocess.run(args, cwd=root, capture_output=True, text=True, timeout=timeout, check=False)
    require(result.returncode == 0, 'runner_failed', f'Fixed runner failed: {Path(args[1]).name}; {result.stderr[-300:]}')
    return json.loads(result.stdout)


def preflight(profile, root, require_game=True):
    require_session(command([sys.executable, str(root / 'session_state.py')], root, 5))
    sys.path.insert(0, DEPENDENCIES)
    import psutil
    games = [p.pid for p in psutil.process_iter(['name']) if (p.info['name'] or '').lower() == 'vainglory.exe']
    if not require_game:
        require(not games, 'game_still_running', 'All game processes must be stopped before restoring the slot')
        return games
    expected = profile['process']
    process = psutil.Process(expected['pid'])
    actual = {'pid': process.pid, 'create_time': process.create_time(), 'exe': process.exe(),
              'sha256': digest(process.exe())}
    require_process(expected, actual, games)
    ready = read_json(root / 'ready.json')
    worker = psutil.Process(ready['pid'])
    require(worker.pid == profile['worker']['pid'] and worker.create_time() == profile['worker']['create_time']
            and process.ppid() == worker.pid and str(root / 'interactive.py').lower() in ' '.join(worker.cmdline()).lower(),
            'foreign_process', 'Worker creation identity and game parent must prove ownership')
    status = command([sys.executable, str(root / 'control.py'), 'status'], root, 65)
    require(status['state']['owned_pid'] == process.pid and status['state']['owned_alive'] is True,
            'foreign_process', 'Worker does not own the expected game')
    return actual


def capture(profile_path, spec_path, output_dir, seconds=3):
    require(type(seconds) is int and 1 <= seconds <= 180, 'invalid_duration', 'Observation must be bounded to 1..180 seconds')
    profile, root = load_profile(profile_path)
    process = preflight(profile, root)
    spec_path = Path(spec_path).resolve()
    spec = read_json(spec_path)
    identifier(spec.get('capture_id'))
    require(spec.get('process') == process, 'process_identity_mismatch', 'Import specification must freeze this exact process')
    sources = []
    for ref in spec['source_files']:
        source = (spec_path.parent / ref['path']).resolve()
        require(digest(source) == ref['sha256'], 'source_hash_changed', 'Source changed before capture')
        sources.append((source, ref['sha256']))
        ref['path'] = str(source)
    for ref in spec.get('artifacts', []):
        ref['path'] = str((spec_path.parent / ref['path']).resolve())
    probe_name = 'player_state_probe.js'
    require(digest(root / probe_name) == digest(Path(__file__).with_name(probe_name)),
            'probe_identity_mismatch', 'Remote probe differs from this package')
    output = Path(output_dir).resolve()
    require(not output.exists(), 'output_exists', 'Capture output must be new')
    raw = output.with_name(output.name + '-raw-' + uuid.uuid4().hex)
    raw.mkdir(parents=True, exist_ok=False)
    invocation = [sys.executable, str(root / 'probe.py'), '--pid', str(process['pid']), '--seconds', str(seconds),
                  '--script', probe_name, '--output', str(raw / 'native.jsonl')]
    started = datetime.now(timezone.utc).isoformat()
    shot_name = spec['capture_id'] + '-' + uuid.uuid4().hex + '.png'
    command([sys.executable, str(root / 'control.py'), 'shot', '--name', shot_name], root, 65)
    result = subprocess.run(invocation, cwd=root, capture_output=True, text=True, timeout=seconds + 30, check=False)
    publish(raw / 'runner.json', {'invocation': invocation, 'begin_utc': started,
                                 'end_utc': datetime.now(timezone.utc).isoformat(), 'returncode': result.returncode,
                                 'stdout': result.stdout, 'stderr': result.stderr}, [profile_path, spec_path])
    with (raw / 'actions.jsonl').open('xb') as stream:
        stream.write((root / 'commands.jsonl').read_bytes())
    require(all(digest(path) == expected for path, expected in sources), 'source_hash_changed', 'Source changed during capture')
    spec.setdefault('artifacts', []).extend([
        metadata(raw / 'native.jsonl', artifact_id='native', role='native'),
        metadata(root / shot_name, artifact_id='screenshot', role='screenshot'),
        metadata(raw / 'actions.jsonl', artifact_id='actions', role='actions'),
        metadata(raw / 'runner.json', artifact_id='runner', role='runner'),
    ])
    spec.update(native_artifact_id='native', alignment={'kind': 'unverified'})
    publish(raw / 'import-spec.json', spec, [spec_path, profile_path, *(p for p, _ in sources)])
    verification = import_capture(raw / 'import-spec.json', output)
    require(result.returncode == 0, 'native_observer_failed', f'Native observer failed; evidence retained in {raw}')
    return verification


def restore(profile_path, trial, output):
    identifier(trial)
    profile, root = load_profile(profile_path)
    games = preflight(profile, root, require_game=False)
    stage = root / trial
    backup = read_json(stage / 'slot-backup.json')
    require(backup.get('owned_game_pid') == profile['process']['pid'], 'foreign_process', 'Backup belongs to a different game')
    actual = {p.name: digest(p) for p in (stage / 'slot-backup').iterdir() if p.is_file()}
    require_backup(backup, actual, games, (stage / 'substituted-slot').exists())
    require(not Path(output).exists() and not Path(output).is_symlink(),
            'output_exists', 'Restore report output must be new before any mutation')
    reserved = tuple(Path(backup['temp_dir']) / row['name'] for row in backup['files'])
    validate_report_outputs(ReportInputs(files=(Path(profile_path), stage / 'slot-backup.json'),
                                        reserved_replays=reserved), (Path(output),))
    result = command(['powershell.exe', '-NoProfile', '-File', str(root / 'restore.ps1'), '-Trial', trial], root, 60)
    rows = []
    for row in backup['files']:
        path = Path(backup['temp_dir']) / row['name']
        require(path.is_file() and digest(path) == row['sha256'], 'restore_mismatch', 'Restored slot hash mismatch')
        rows.append({'name': row['name'], 'sha256': digest(path)})
    report = {'ok': True, 'trial': trial, 'receipt': result, 'verified_files': rows,
              'source_backup': metadata(stage / 'slot-backup.json')}
    publish(output, report, [profile_path, stage / 'slot-backup.json', stage / 'slot-restored.json'])
    return report
