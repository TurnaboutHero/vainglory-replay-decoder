"""Load a saved replay into an explicitly selected, quiescent filesystem slot."""
import argparse
from datetime import datetime
from enum import StrEnum
import json
import os
from pathlib import Path
from typing import TypedDict, assert_never

from vg.core.replay_archive import inventory, recover, replacement, select_family, snapshot
from vg.core.replay_input import ReplayInputError, discover_replay_files


class LoadResult(TypedDict, total=False):
    success: bool
    source_replay: str
    source_dir: str
    source_frames: int
    target_replay: str
    target_dir: str
    frames_copied: int
    source_scope: str
    recovery: str
    message: str
    error_code: str
    error: str


class SavedReplay(TypedDict):
    name: str
    path: str
    frames: int
    size_mb: float
    modified: str


class Command(StrEnum):
    LOAD = 'load'
    LIST = 'list'
    RECOVER = 'recover'
    STATUS = 'status'


class VGRLoader:
    DEFAULT_TEMP_PATH = Path(os.environ.get('TEMP', os.environ.get('TMP', 'C:\\Temp')))

    def __init__(self, temp_path: str | None = None):
        self.temp_path = Path(temp_path) if temp_path else self.DEFAULT_TEMP_PATH

    def find_active_replay(self, target_name: str | None = None) -> tuple[str, Path] | None:
        try:
            path = select_family(self.temp_path, target_name, recursive=False)
        except ReplayInputError as error:
            if error.code == 'input_missing':
                return None
            raise
        return path.name[:-6], path

    def count_frames(self, directory: Path, replay_name: str) -> int:
        return len(inventory(directory / f'{replay_name}.0.vgr').entries)

    def backup_active_replay(self, backup_dir: str | None = None, target_name: str | None = None) -> Path | None:
        active = self.find_active_replay(target_name)
        if active is None:
            return None
        name, frame0 = active
        destination = Path(backup_dir) if backup_dir else self.temp_path / 'vgr_backups' / datetime.now().strftime('%Y%m%d_%H%M%S_%f') / name
        snapshot(frame0, destination)
        return destination

    def load_replay(self, source_dir: str, source_name: str | None = None, target_name: str | None = None) -> LoadResult:
        try:
            source = select_family(Path(source_dir), source_name)
            target = select_family(self.temp_path, target_name, recursive=False)
            with replacement(source, target) as transaction:
                transaction.promote()
                transaction.commit()
                return {'success': True, 'source_replay': source.name[:-6], 'source_dir': str(source.parent),
                        'source_frames': len(transaction.expected), 'target_replay': target.name[:-6],
                        'target_dir': str(target.parent), 'frames_copied': len(transaction.expected),
                        'source_scope': transaction.source.scope, 'recovery': str(transaction.operation),
                        'message': 'Filesystem replacement verified; playback is not verified.'}
        except (ReplayInputError, OSError, ValueError) as error:
            return {'success': False, 'error_code': getattr(error, 'code', 'archive_failed'),
                    'error': str(error), 'recovery': str(getattr(error, 'recovery', '') or '')}

    def list_saved_replays(self, search_dir: str) -> list[SavedReplay]:
        results: list[SavedReplay] = []
        for frame0 in discover_replay_files(Path(search_dir)):
            if any(part.startswith(('.snapshot-', '.vgr-recovery-')) for part in frame0.relative_to(search_dir).parts):
                continue
            details = inventory(frame0)
            results.append({'name': frame0.name[:-6], 'path': str(frame0.parent),
                            'frames': len(details.entries), 'size_mb': round(sum(e.size for e in details.entries) / 1024 / 1024, 2),
                            'modified': datetime.fromtimestamp(frame0.stat().st_mtime).isoformat()})
        return sorted(results, key=lambda row: row['modified'], reverse=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    listing = commands.add_parser('list')
    listing.add_argument('directory')
    loading = commands.add_parser('load')
    loading.add_argument('source')
    loading.add_argument('-n', '--name')
    loading.add_argument('-t', '--temp')
    loading.add_argument('--target-name')
    status = commands.add_parser('status')
    status.add_argument('-t', '--temp')
    status.add_argument('--target-name')
    recovery = commands.add_parser('recover')
    recovery.add_argument('operation')
    args = parser.parse_args()
    try:
        match Command(args.command):
            case Command.LOAD:
                result = VGRLoader(args.temp).load_replay(args.source, args.name, args.target_name)
                print(json.dumps(result, indent=2))
                return 0 if result['success'] else 2
            case Command.LIST:
                print(json.dumps(VGRLoader().list_saved_replays(args.directory), indent=2))
            case Command.RECOVER:
                print(json.dumps({'restored': str(recover(Path(args.operation)))}))
            case Command.STATUS:
                active = VGRLoader(args.temp).find_active_replay(args.target_name)
                print(json.dumps({'active_replay': active[0] if active else None}))
            case unreachable:
                assert_never(unreachable)
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({'success': False, 'error_code': getattr(error, 'code', 'archive_failed'), 'error': str(error)}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
