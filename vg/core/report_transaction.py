"""Stage report sets, retain rollback data and publish a final receipt last."""

from collections.abc import Mapping
import json
import os
from pathlib import Path
import uuid

from vg.core.replay_output import (
    ReportInputs, ReplayOutputError, stage_payload, validate_report_outputs,
)
from vg.core.report_recovery import (
    ReportEntry, ReportReceipt, cleanup_backups, digest, load_receipt,
    recover_report_set, restore_receipt,
)


def _backup(path: Path, transaction: str) -> str | None:
    if not path.exists():
        return None
    backup = path.with_name(f'.{path.name}.{transaction}.backup')
    created = False
    try:
        with backup.open('xb') as stream:
            created = True
            stream.write(path.read_bytes())
            stream.flush()
            os.fsync(stream.fileno())
    except OSError:
        if created:
            backup.unlink(missing_ok=True)
        raise
    return str(backup)


def _receipt_payload(data: ReportReceipt) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, indent=2) + '\n'


def publish_report_set(inputs: ReportInputs, outputs: Mapping[Path, str | bytes], receipt: Path) -> ReportReceipt:
    """Handled failures restore prior bytes or leave a pending, recoverable receipt."""
    receipt = receipt.absolute()
    validate_report_outputs(inputs, (*outputs, receipt))
    outputs = {Path(path).absolute(): payload for path, payload in outputs.items()}
    destinations = (*outputs, receipt)
    validate_report_outputs(inputs, destinations)
    prior = load_receipt(receipt) if receipt.exists() else None
    if prior is not None and prior['status'] == 'pending':
        raise ReplayOutputError(receipt, 'Recover the pending generation before publishing', 'recovery_required')
    transaction = uuid.uuid4().hex
    staged: dict[Path, Path] = {}
    entries: list[ReportEntry] = []
    data: ReportReceipt = {
        'schema': 'replay.report-set.v1', 'transaction_id': transaction, 'status': 'pending',
        'receipt': str(receipt), 'current_outputs': [str(path) for path in outputs],
        'stale_outputs': sorted(set(prior['current_outputs'] + prior['stale_outputs']) - set(map(str, outputs))) if prior else [],
        'prior_receipt_identity': digest(receipt), 'entries': entries,
        'receipt_backup': None, 'protected_inputs': [str(path.resolve()) for path in inputs.sources()],
    }
    pending = False
    try:
        for target, payload in outputs.items():
            staged[target] = stage_payload(target, payload)
        for target, temporary in staged.items():
            entries.append({'path': str(target), 'parent': str(target.parent.resolve()), 'staged': str(temporary), 'old_hash': digest(target),
                            'new_hash': digest(temporary), 'backup': _backup(target, transaction)})
        data['receipt_backup'] = _backup(receipt, transaction)
        staged[receipt] = stage_payload(receipt, _receipt_payload(data))
        validate_report_outputs(inputs, destinations)
        os.replace(staged[receipt], receipt)
        pending = True
        for target in outputs:
            validate_report_outputs(inputs, destinations)
            if digest(target) != next(entry['old_hash'] for entry in entries if entry['path'] == str(target)):
                raise ReplayOutputError(target, 'Destination changed during publication', 'publication_failed')
            os.replace(staged[target], target)
        complete: ReportReceipt = {**data, 'status': 'complete'}
        staged[receipt] = stage_payload(receipt, _receipt_payload(complete))
        validate_report_outputs(inputs, destinations)
        os.replace(staged[receipt], receipt)
    except (OSError, UnicodeError, ReplayOutputError) as error:
        if pending:
            restore_receipt(data)
        cleanup_backups(data)
        if isinstance(error, ReplayOutputError):
            raise
        raise ReplayOutputError(receipt, str(error), 'publication_failed') from error
    finally:
        for temporary in staged.values():
            temporary.unlink(missing_ok=True)
    cleanup_backups(data)
    return complete
