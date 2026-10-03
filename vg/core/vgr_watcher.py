"""Back up stable replay families; snapshot stability does not prove match completion."""
import argparse
from dataclasses import asdict
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import time
from typing import Literal, TypedDict

from vg.core.replay_archive import ArchiveError, Inventory, exclusive_lock, inventory, snapshot
from vg.core.replay_input import ReplayInputError, discover_replay_files
from vg.core.replay_output import ReplayOutputError, ReportInputs, write_report_output


class ScanResult(TypedDict):
    replay: str
    status: Literal['success', 'unchanged', 'pending', 'error']
    path: str
    error_code: str
    error: str


def _fingerprint(details: Inventory) -> str:
    payload = {'source': str(details.frame0.resolve()), 'sections': [asdict(e) for e in details.entries]}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


class VGRWatcher:
    def __init__(self, backup_dir: str, temp_path: str | None = None):
        self.temp_path = Path(temp_path) if temp_path else Path(os.environ.get('TEMP', os.environ.get('TMP', 'C:\\Temp')))
        self.backup_dir = Path(backup_dir).absolute()
        self.last_scan_report: list[ScanResult] = []
        self.known_replays: set[str] = set()
        self.last_backup_hash: str | None = None

    def _paths(self, frame0: Path) -> tuple[Path, Path]:
        identity = hashlib.sha256(str(frame0.resolve()).encode()).hexdigest()
        receipts = self.backup_dir / '.watcher'
        return receipts / f'{identity}.json', receipts / f'{identity}.lock'

    def _existing(self, receipt: Path, fingerprint: str, details: Inventory) -> Path | None:
        if not receipt.exists():
            return None
        data = json.loads(receipt.read_text(encoding='utf-8'))
        if data['fingerprint'] != fingerprint:
            return None
        destination = Path(data['snapshot'])
        if not destination.resolve().is_relative_to(self.backup_dir.resolve()) or destination.is_symlink():
            raise ArchiveError('recovery_required', receipt, 'Snapshot receipt leaves backup directory')
        recorded = json.loads((destination / 'snapshot.json').read_text(encoding='utf-8'))
        entries = [asdict(e) for e in details.entries]
        if recorded['sections'] != entries or inventory(destination / details.frame0.name, manifest=True).entries != details.entries:
            raise ArchiveError('recovery_required', destination, 'Acknowledged snapshot no longer verifies')
        if {p.name for p in destination.iterdir()} != {e.name for e in details.entries} | {'snapshot.json'}:
            raise ArchiveError('recovery_required', destination, 'Acknowledged snapshot has unexpected files')
        return destination

    def _backup(self, frame0: Path) -> ScanResult:
        receipt, lock = self._paths(frame0)
        receipt.parent.mkdir(parents=True, exist_ok=True)
        with exclusive_lock(lock, receipt.parent / (receipt.stem + '.operation'), recover_dead=True):
            for attempt in range(2):
                try:
                    details = inventory(frame0, manifest=True)
                    fingerprint = _fingerprint(details)
                    existing = self._existing(receipt, fingerprint, details)
                    if existing is not None:
                        return {'replay': str(frame0), 'status': 'unchanged', 'path': str(existing), 'error_code': '', 'error': ''}
                    destination = self.backup_dir / datetime.now().strftime('%y.%m.%d') / 'cache' / frame0.name[:-6] / fingerprint
                    source_inputs = ReportInputs(files=tuple(frame0.parent / e.name for e in details.entries), replays=(frame0,))
                    result = snapshot(frame0, destination, expected=details)
                    source_inputs.recheck()
                    write_report_output(source_inputs, receipt, json.dumps({'fingerprint': fingerprint, 'snapshot': result['path']}, indent=2))
                    self.known_replays.add(str(frame0.resolve()))
                    self.last_backup_hash = fingerprint
                    return {'replay': str(frame0), 'status': 'success', 'path': result['path'], 'error_code': '', 'error': ''}
                except (ArchiveError, ReplayOutputError) as error:
                    if error.code not in ('source_changed', 'input_changed') or attempt == 1:
                        raise
        raise ArchiveError('source_changed', frame0, 'No stable source after two attempts')

    def backup_replay(self, replay_name: str) -> Path | None:
        result = self._backup((self.temp_path / f'{replay_name}.0.vgr').absolute())
        return Path(result['path'])

    def scan_once(self) -> bool:
        self.last_scan_report = []
        try:
            families = tuple(p for p in discover_replay_files(self.temp_path) if p.parent == self.temp_path)
        except ReplayInputError as error:
            self.last_scan_report.append({'replay': str(self.temp_path), 'status': 'error', 'path': '',
                                          'error_code': error.code, 'error': str(error)})
            return False
        for frame0 in families:
            try:
                result = self._backup(frame0.absolute())
            except (OSError, ValueError, KeyError, TypeError) as error:
                code = getattr(error, 'code', 'snapshot_failed')
                result: ScanResult = {'replay': str(frame0), 'status': 'pending' if code in ('source_changed', 'input_changed', 'slot_busy') else 'error',
                                      'path': '', 'error_code': code, 'error': str(error)}
            self.last_scan_report.append(result)
        return any(row['status'] == 'success' for row in self.last_scan_report)

    def watch(self, interval: int = 5) -> None:
        try:
            while True:
                self.scan_once()
                print(json.dumps(self.last_scan_report, ensure_ascii=False), flush=True)
                time.sleep(interval)
        except KeyboardInterrupt:
            return


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backup_dir', nargs='?', default='./vgr_backups')
    parser.add_argument('-t', '--temp')
    parser.add_argument('-i', '--interval', type=int, default=5)
    parser.add_argument('--once', action='store_true')
    args = parser.parse_args()
    watcher = VGRWatcher(args.backup_dir, args.temp)
    if args.once:
        watcher.scan_once()
        print(json.dumps(watcher.last_scan_report, indent=2, ensure_ascii=False))
        return 1 if any(row['status'] in ('pending', 'error') for row in watcher.last_scan_report) else 0
    watcher.watch(args.interval)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
