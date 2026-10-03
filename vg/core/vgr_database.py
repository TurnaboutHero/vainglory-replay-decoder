#!/usr/bin/env python3
"""
VGR Database Builder - Build hero/item database for Vainglory
"""

import sqlite3
import json
from pathlib import Path
from typing import List, Dict, Optional

from vg.core.vgr_mapping import normalize_hero_name
from vg.core.replay_input import replay_sections, select_replay
from vg.core.vgr_catalog import HEROES_DATA, ITEMS_DATA, KOREAN_NAMES, resolve_hero_to_catalog
from vg.core.replay_output import ReportInputs, validate_report_outputs, write_report_output
from vg.core.stat_evidence import frame_scope

try:
    from vgr_parser import VGRParser
except ImportError:
    from .vgr_parser import VGRParser



class VGDatabaseError(ValueError):
    def __init__(self, code: str, path: Path, reason: str):
        self.code = code
        self.path = path
        self.reason = reason
        super().__init__(f"{code}: {path}: {reason}")


class VGDatabase:
    """Vainglory SQLite database manager"""
    
    def __init__(self, db_path: str = "vainglory.db"):
        self.db_path = Path(db_path)
        self.conn: Optional[sqlite3.Connection] = None
        
    def connect(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys=ON")
        self.foreign_key_violations = [tuple(row) for row in self.conn.execute("PRAGMA foreign_key_check")]
        
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            
    def create_tables(self):
        """Create database tables"""
        cursor = self.conn.cursor()
        
        # Heroes table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS heroes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                name_ko TEXT,
                role TEXT,
                attack_type TEXT,
                image_path TEXT,
                wiki_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                category TEXT,
                tier_name TEXT,
                tier INTEGER,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Skins table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS skins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hero_id INTEGER,
                name TEXT NOT NULL,
                rarity TEXT,
                image_path TEXT,
                FOREIGN KEY (hero_id) REFERENCES heroes(id)
            )
        ''')
        
        # Matches table (for replay data)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                replay_name TEXT UNIQUE,
                game_mode TEXT,
                frame_count INTEGER,
                duration INTEGER, -- Match duration in seconds
                winning_team INTEGER, -- 1: Left (Blue), 2: Right (Red)
                match_date TIMESTAMP,
                file_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Match players table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS match_players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id INTEGER,
                player_name TEXT,
                player_uuid TEXT,
                team INTEGER,
                hero_id INTEGER,
                kills INTEGER DEFAULT 0,
                deaths INTEGER DEFAULT 0,
                assists INTEGER DEFAULT 0,
                minion_kills INTEGER DEFAULT 0,
                gold INTEGER DEFAULT 0,
                items TEXT, -- JSON array of item names
                FOREIGN KEY (match_id) REFERENCES matches(id),
                FOREIGN KEY (hero_id) REFERENCES heroes(id)
            )
        ''')
        
        additions = {
            'matches': {'source_replay_name': 'TEXT', 'replay_scope': 'TEXT', 'provenance_json': 'TEXT'},
            'match_players': {'source_hero_id': 'INTEGER', 'source_hero_namespace': 'TEXT'},
        }
        for table, columns in additions.items():
            existing = {row['name'] for row in cursor.execute(f'PRAGMA table_info({table})')}
            for name, declaration in columns.items():
                if name not in existing:
                    cursor.execute(f'ALTER TABLE {table} ADD COLUMN {name} {declaration}')
        cursor.execute('CREATE UNIQUE INDEX IF NOT EXISTS matches_replay_scope ON matches(replay_scope) WHERE replay_scope IS NOT NULL')
        self.conn.commit()
        
    def populate_heroes(self):
        """Insert hero data"""
        cursor = self.conn.cursor()
        
        for name, role, attack_type in HEROES_DATA:
            name_ko = KOREAN_NAMES.get(name, "")
            wiki_url = f"https://www.vaingloryfire.com/vainglory/wiki/heroes/{name.lower().replace(' ', '-')}"
            
            cursor.execute('''
                INSERT INTO heroes (name, name_ko, role, attack_type, wiki_url)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO NOTHING
            ''', (name, name_ko, role, attack_type, wiki_url))
        
        self.conn.commit()
        return len(HEROES_DATA)
        
    def populate_items(self):
        """Insert item data"""
        cursor = self.conn.cursor()
        
        for name, category, tier_name, tier in ITEMS_DATA:
            cursor.execute('''
                INSERT INTO items (name, category, tier_name, tier)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(name) DO NOTHING
            ''', (name, category, tier_name, tier))
        
        self.conn.commit()
        return len(ITEMS_DATA)
    
    def get_heroes(self) -> List[Dict]:
        """Get all heroes"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM heroes ORDER BY name')
        return [dict(row) for row in cursor.fetchall()]
    
    def get_items(self) -> List[Dict]:
        """Get all items"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM items ORDER BY category, tier, name')
        return [dict(row) for row in cursor.fetchall()]
    
    def search_hero(self, query: str) -> List[Dict]:
        """Search heroes by name"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM heroes 
            WHERE name LIKE ? OR name_ko LIKE ?
            ORDER BY name
        ''', (f'%{query}%', f'%{query}%'))
        return [dict(row) for row in cursor.fetchall()]
    
    def export_json(self, output_path: str):
        """Export hero and item catalogs with explicit coverage metadata."""
        output = Path(output_path)
        reserved = (self.db_path, *(Path(str(self.db_path) + suffix) for suffix in ('-wal', '-shm', '-journal')))
        inputs = ReportInputs(files=reserved)
        validate_report_outputs(inputs, (output,))
        data = {
            'schema_version': 'vg.catalog-export.v1',
            'coverage': 'catalog_only',
            'included_tables': ['heroes', 'items'],
            'excluded_tables': ['skins', 'matches', 'match_players'],
            'heroes': self.get_heroes(),
            'items': self.get_items(),
        }
        write_report_output(inputs, output, json.dumps(data, indent=2, ensure_ascii=False))
        return output_path

    def import_replay(self, file_path: str):
        """Parse and import a replay file into the database"""
        self.foreign_key_violations = [tuple(row) for row in self.conn.execute('PRAGMA foreign_key_check')]
        if self.foreign_key_violations:
            raise VGDatabaseError('foreign_key_violation', self.db_path,
                                  f'{len(self.foreign_key_violations)} existing foreign-key violations; no import was attempted.')
        first = select_replay(file_path)
        inputs = ReportInputs(replays=(first,))
        sections = replay_sections(first)
        scope = frame_scope([(number, path.read_bytes()) for number, path in sections])
        data = VGRParser(str(first)).parse()
        inputs.recheck()
        self.create_tables()
        existing = self.conn.execute('SELECT id FROM matches WHERE replay_scope=?', (scope,)).fetchone()
        if existing:
            return False

        name = data['replay_name']
        collision = self.conn.execute('SELECT replay_scope FROM matches WHERE replay_name=?', (name,)).fetchone()
        if collision and collision['replay_scope'] is None:
            raise VGDatabaseError('legacy_identity_unknown', self.db_path,
                                  f'Existing replay {name!r} has no content identity; use a separate database until explicitly migrated.')
        storage_name = f'{name}#{scope}' if collision else name
        info = data['match_info']
        truth_source = data.get('truth_source')
        provenance = {
            'accepted_for_index': False,
            'replay_scope': scope,
            'truth_source': truth_source,
            'duration': data.get('duration_provenance') or {
                'status': 'supplied_truth' if truth_source and info.get('duration_seconds') is not None else 'unknown',
                'source': truth_source,
                'reason': 'Legacy parser values have no independently accepted final-screen validation.',
                'accepted_for_index': False,
                'replay_scope': scope,
            },
            'players': [],
        }
        catalog = {normalize_hero_name(row['name']).casefold(): row['id'] for row in self.get_heroes()}
        players = []
        for player in data['teams']['left'] + data['teams']['right']:
            hero, source_id, namespace, reason = resolve_hero_to_catalog(player, catalog)
            team = player.get('team_id')
            if team is None:
                team = {'left': 1, 'right': 2}.get(player.get('team'))
            players.append((player, team, hero, source_id, namespace))
            provenance['players'].append({'player_name': player['name'], 'hero_resolution_reason': reason})
        inputs.recheck()
        try:
            with self.conn:
                cursor = self.conn.execute('''
                    INSERT INTO matches
                    (replay_name, game_mode, frame_count, duration, winning_team, match_date, file_path,
                     source_replay_name, replay_scope, provenance_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (storage_name, info['mode'], len(sections), info.get('duration_seconds'),
                      {'left': 1, 'right': 2}.get(info.get('winner')), data.get('parsed_at'), str(first),
                      name, scope, json.dumps(provenance, ensure_ascii=False)))
                for player, team, hero, source_id, namespace in players:
                    self.conn.execute('''
                        INSERT INTO match_players
                        (match_id,player_name,player_uuid,team,hero_id,kills,deaths,assists,minion_kills,gold,items,
                         source_hero_id,source_hero_namespace)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (cursor.lastrowid, player['name'], player.get('uuid'), team, hero,
                          player.get('kills'), player.get('deaths'), player.get('assists'),
                          player.get('minion_kills'), player.get('gold'), json.dumps(player.get('items', [])),
                          source_id, namespace))
                inputs.recheck()
            return True
        except sqlite3.Error as error:
            raise VGDatabaseError('import_failed', first, str(error)) from error


def main(argv=None) -> int:
    from vg.core.vgr_database_cli import main as database_main
    return database_main(argv)


if __name__ == '__main__':
    raise SystemExit(main())
