import sqlite3
import sys
from enum import StrEnum
from pathlib import Path
from typing import assert_never

from vg.core.replay_input import discover_replay_files, select_replay
from vg.core.vgr_database import VGDatabase


class DatabaseCommand(StrEnum):
    INIT = 'init'
    HEROES = 'heroes'
    ITEMS = 'items'
    SEARCH = 'search'
    EXPORT = 'export'
    IMPORT = 'import'


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description='VGR Database Builder')
    parser.add_argument('command', choices=list(DatabaseCommand), type=DatabaseCommand,
                        help='Command to run')
    parser.add_argument('-q', '--query', help='Search query')
    parser.add_argument('-i', '--input', help='Input directory or file for import')
    parser.add_argument('-o', '--output', default='vg_data.json', help='Output file for export')
    parser.add_argument('--db', default='vainglory.db', help='Database file path')

    args = parser.parse_args(argv)
    if args.command == 'import' and not args.input:
        parser.error('import requires --input')
    if args.command == 'search' and not args.query:
        parser.error('search requires --query')

    db = VGDatabase(args.db)
    try:
        db.connect()
        if db.foreign_key_violations:
            print(f'foreign_key_violation: {db.db_path}: {len(db.foreign_key_violations)} existing violations; imports are blocked.', file=sys.stderr)
        command: DatabaseCommand = args.command
        match command:
            case DatabaseCommand.INIT:
                db.create_tables()
                hero_count = db.populate_heroes()
                item_count = db.populate_items()
                print(f'Database initialized. Heroes: {hero_count}; Items: {item_count}; Path: {db.db_path}')
            case DatabaseCommand.HEROES:
                for hero in db.get_heroes():
                    print(f"{hero['name']:15} ({hero['name_ko']}) - {hero['role']}")
            case DatabaseCommand.ITEMS:
                current_category = None
                for item in db.get_items():
                    if item['category'] != current_category:
                        current_category = item['category']
                        print(f"\n=== {current_category} ===")
                    print(f"  [{item['tier']}] {item['name']}")
            case DatabaseCommand.SEARCH:
                results = db.search_hero(args.query)
                if results:
                    for hero in results:
                        print(f"{hero['name']} ({hero['name_ko']}) - {hero['role']}, {hero['attack_type']}")
                else:
                    print('No results found.')
            case DatabaseCommand.EXPORT:
                print(f'Exported catalog JSON: {db.export_json(args.output)}')
            case DatabaseCommand.IMPORT:
                path = Path(args.input)
                files = discover_replay_files(path) if path.is_dir() else (select_replay(path),)
                imported = 0
                for source in files:
                    imported += db.import_replay(str(source))
                print(f'Import complete: {imported} imported, {len(files) - imported} already present, {len(files)} discovered.')
            case unreachable:
                assert_never(unreachable)
        return 0
    except (ValueError, OSError, sqlite3.Error) as error:
        print(f'database_error: {db.db_path}: {error}', file=sys.stderr)
        return 2
    finally:
        db.close()
