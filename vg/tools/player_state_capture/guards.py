from __future__ import annotations

import math
from pathlib import PureWindowsPath
import re

CLIENT_HASHES = frozenset({
    '659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642',
    'd6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc',
})


class CaptureError(ValueError):
    def __init__(self, code: str, message: str):
        self.code = code
        super().__init__(message)


def require(condition, code, message):
    if not condition:
        raise CaptureError(code, message)


def identifier(value):
    require(isinstance(value, str) and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', value),
            'invalid_identifier', 'Expected a bounded alphanumeric capture identifier')
    return value


def require_session(row):
    fields = ('level', 'session_id', 'session_state', 'session_flags', 'bytes', 'expected_bytes')
    require(isinstance(row, dict) and all(type(row.get(k)) is int for k in fields),
            'session_unavailable', 'Fresh WTS response is incomplete')
    version = row.get('os_version')
    require(isinstance(version, list) and len(version) == 3 and all(type(v) is int for v in version)
            and version[0] >= 10 and version[2] >= 10240,
            'session_unavailable', 'Modern Windows WTS session required')
    require(row['expected_bytes'] > 0 and row['bytes'] >= row['expected_bytes']
            and tuple(row[k] for k in fields[:4]) == (1, 1, 0, 1),
            'session_unavailable', 'Session 1 must be active and unlocked')


def require_process(expected, actual, live_game_pids):
    require(type(expected.get('pid')) is int and expected['pid'] > 0
            and set(live_game_pids) == {expected['pid']},
            'foreign_process', 'Exactly the owned game must be running')
    require(actual.get('pid') == expected['pid']
            and isinstance(expected.get('create_time'), (int, float))
            and not isinstance(expected['create_time'], bool)
            and math.isfinite(expected['create_time'])
            and actual.get('create_time') == expected['create_time'],
            'process_identity_mismatch', 'PID creation identity changed')
    require(isinstance(expected.get('exe'), str) and isinstance(actual.get('exe'), str)
            and PureWindowsPath(expected['exe']) == PureWindowsPath(actual['exe']),
            'executable_identity_mismatch', 'Executable path changed')
    require(expected.get('sha256') in CLIENT_HASHES and actual.get('sha256') == expected['sha256'],
            'executable_identity_mismatch', 'Executable hash changed')


def require_backup(metadata, actual_hashes, live_game_pids, archive_exists=False):
    require(not live_game_pids, 'game_still_running', 'Stop owned game before restoration')
    require(not archive_exists, 'backup_conflict', 'Substituted-slot archive already exists')
    slot = metadata.get('slot_name')
    require(isinstance(slot, str) and re.fullmatch(r'[A-Za-z0-9_-]+', slot),
            'invalid_slot', 'Backup slot name is not a single safe basename')
    rows = metadata.get('files', [])
    require(bool(rows) and len({r.get('name') for r in rows}) == len(rows),
            'backup_conflict', 'Backup must have unique original sections')
    for row in rows:
        name = row.get('name', '')
        require(re.fullmatch(re.escape(slot) + r'\.\d+\.vgr', name) is not None,
                'invalid_slot', 'Backup file is outside the owned numbered slot')
        require(actual_hashes.get(name) == row.get('sha256') and re.fullmatch(r'[0-9a-f]{64}', row.get('sha256', '')),
                'backup_hash_changed', 'Original backup bytes do not match their receipt')
    require(set(actual_hashes) == {row['name'] for row in rows},
            'backup_conflict', 'Unexpected backup entries')
