"""Receipt validation and conservative rollback for owned report generations."""

import json
import os
from pathlib import Path
import re
from typing import NotRequired, TypedDict

from vg.core.batch_result import BatchReport

from vg.core.replay_output import ReplayOutputError, file_identity, stage_payload, validate_output_sources


class ReportEntry(TypedDict):
    path: str
    parent: str
    staged: str
    backup: str | None
    old_hash: str | None
    new_hash: str


class ReportReceipt(TypedDict):
    batch: NotRequired[BatchReport]
    schema: str
    transaction_id: str
    status: str
    receipt: str
    current_outputs: list[str]
    stale_outputs: list[str]
    prior_receipt_identity: str | None
    entries: list[ReportEntry]
    receipt_backup: str | None
    protected_inputs: list[str]


def digest(path: Path) -> str | None:
    if path.is_symlink():
        raise ReplayOutputError(path, 'Recovery refuses symbolic links', 'recovery_required')
    return file_identity(path).digest if path.exists() else None


def load_receipt(path: Path) -> ReportReceipt:
    try:
        if path.is_symlink():
            raise ReplayOutputError(path, 'Receipt must not be a symbolic link', 'recovery_required')
        data: ReportReceipt = json.loads(path.read_text(encoding='utf-8'))
        if (not isinstance(data, dict) or data.get('schema') != 'replay.report-set.v1'
                or data.get('status') not in ('pending', 'complete')
                or data.get('receipt') != str(path.absolute())
                or not isinstance(data.get('transaction_id'), str)
                or re.fullmatch('[0-9a-f]{32}', data['transaction_id']) is None):
            raise ReplayOutputError(path, 'Invalid report receipt', 'recovery_required')
        for field in ('current_outputs', 'stale_outputs', 'protected_inputs'):
            if not isinstance(data.get(field), list) or any(not isinstance(p, str) for p in data[field]):
                raise ReplayOutputError(path, f'Invalid {field}', 'recovery_required')
        if not isinstance(data.get('entries'), list):
            raise ReplayOutputError(path, 'Invalid receipt entries', 'recovery_required')
        destinations = []
        for entry in data['entries']:
            if not isinstance(entry, dict) or not isinstance(entry.get('path'), str):
                raise ReplayOutputError(path, 'Invalid receipt entry', 'recovery_required')
            target = Path(entry['path'])
            stage_name = entry.get('staged')
            if (not isinstance(stage_name, str) or Path(stage_name).parent != target.parent
                    or not Path(stage_name).name.startswith(f'.{target.name}.')
                    or not Path(stage_name).name.endswith('.tmp')):
                raise ReplayOutputError(path, 'Invalid staged file ownership', 'recovery_required')
            if (not target.is_absolute() or entry.get('parent') != str(target.parent.resolve())
                    or entry.get('backup') not in (
                    None, str(target.with_name(f'.{target.name}.{data["transaction_id"]}.backup')))):
                raise ReplayOutputError(path, 'Invalid backup ownership', 'recovery_required')
            for field in ('new_hash', 'old_hash'):
                value = entry.get(field)
                if not (value is None and field == 'old_hash') and (
                        not isinstance(value, str) or re.fullmatch('[0-9a-f]{64}', value) is None):
                    raise ReplayOutputError(path, 'Invalid receipt digest', 'recovery_required')
            if (entry['backup'] is None) != (entry['old_hash'] is None):
                raise ReplayOutputError(path, 'Missing owned backup', 'recovery_required')
            destinations.append(target)
        if [str(target) for target in destinations] != data['current_outputs']:
            raise ReplayOutputError(path, 'Receipt output inventory mismatch', 'recovery_required')
        expected = str(path.with_name(f'.{path.name}.{data["transaction_id"]}.backup'))
        if data.get('receipt_backup') not in (None, expected):
            raise ReplayOutputError(path, 'Invalid prior receipt backup', 'recovery_required')
        old = data.get('prior_receipt_identity')
        if (old is None) != (data['receipt_backup'] is None) or (
                old is not None and (not isinstance(old, str) or re.fullmatch('[0-9a-f]{64}', old) is None)):
            raise ReplayOutputError(path, 'Invalid prior receipt identity', 'recovery_required')
        checked = [path]
        protected = tuple(Path(p) for p in data['protected_inputs'])
        for target in destinations:
            validate_output_sources(protected, target)
            validate_output_sources(checked, target)
            checked.append(target)
        for entry in data['entries']:
            for name in (entry['staged'], entry['backup']):
                if name is not None:
                    artifact = Path(name)
                    validate_output_sources((*protected, *checked), artifact)
                    checked.append(artifact)
        if data['receipt_backup'] is not None:
            validate_output_sources((*protected, *checked), Path(data['receipt_backup']))
        return data
    except (OSError, UnicodeError, json.JSONDecodeError, TypeError, KeyError) as error:
        raise ReplayOutputError(path, str(error), 'recovery_required') from error


def cleanup_backups(data: ReportReceipt) -> None:
    for entry in data['entries']:
        Path(entry['staged']).unlink(missing_ok=True)
        if entry['backup'] is not None:
            Path(entry['backup']).unlink(missing_ok=True)
    if data['receipt_backup'] is not None:
        Path(data['receipt_backup']).unlink(missing_ok=True)


def restore_receipt(data: ReportReceipt) -> None:
    """Validate every target first; preserve backups for retry if any restoration fails."""
    receipt = Path(data['receipt'])
    try:
        for entry in data['entries']:
            target = Path(entry['path'])
            if str(target.parent.resolve()) != entry['parent']:
                raise ReplayOutputError(target, 'Destination parent changed', 'recovery_required')
            current = digest(target)
            if current not in (entry['old_hash'], entry['new_hash']):
                raise ReplayOutputError(target, 'Current bytes are not owned by this transaction', 'recovery_required')
            if entry['backup'] is not None and digest(Path(entry['backup'])) != entry['old_hash']:
                raise ReplayOutputError(target, 'Backup is missing or changed', 'recovery_required')
            staged = Path(entry['staged'])
            if staged.exists() and digest(staged) != entry['new_hash']:
                raise ReplayOutputError(staged, 'Staged payload changed', 'recovery_required')
        if data['receipt_backup'] is not None and digest(Path(data['receipt_backup'])) != data['prior_receipt_identity']:
            raise ReplayOutputError(receipt, 'Prior receipt backup changed', 'recovery_required')
        for entry in reversed(data['entries']):
            target = Path(entry['path'])
            if digest(target) == entry['old_hash']:
                continue
            if entry['backup'] is None:
                target.unlink()
            else:
                temporary = stage_payload(target, Path(entry['backup']).read_bytes())
                try:
                    os.replace(temporary, target)
                finally:
                    temporary.unlink(missing_ok=True)
        if data['receipt_backup'] is None:
            receipt.unlink(missing_ok=True)
        else:
            temporary = stage_payload(receipt, Path(data['receipt_backup']).read_bytes())
            try:
                os.replace(temporary, receipt)
            finally:
                temporary.unlink(missing_ok=True)
    except OSError as error:
        raise ReplayOutputError(receipt, str(error), 'recovery_required') from error


def recover_report_set(receipt: Path) -> ReportReceipt:
    """Rollback pending receipts only; completed generations are left untouched."""
    receipt = receipt.absolute()
    data = load_receipt(receipt)
    if data['status'] == 'pending':
        restore_receipt(data)
        cleanup_backups(data)
        return {**data, 'status': 'rolled_back'}
    return data
