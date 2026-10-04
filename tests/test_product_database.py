import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from tests.test_native_stats import packet
from tests.test_product_duration_provenance import replay_bytes
from tests.test_vgr_database import make_parsed_replay
from vg.core.vgr_database import VGDatabase, VGDatabaseError
from vg.core.vgr_parser import VGRParser


class TestProductDatabase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / 'catalog.db'
        self.db = VGDatabase(str(self.path))
        self.db.connect()
        self.addCleanup(self.db.close)
        self.db.create_tables()
        self.db.populate_heroes()
        self.db.populate_items()

    def source(self, folder: str, name: str = 'sample', suffix: bytes = b'') -> Path:
        directory = self.root / folder
        directory.mkdir(exist_ok=True)
        path = directory / f'{name}.0.vgr'
        path.write_bytes(replay_bytes() + suffix)
        return path

    def test_database_happy_catalog_identity(self) -> None:
        db = self.db.conn
        hero = db.execute("SELECT id FROM heroes WHERE name='Alpha'").fetchone()[0]
        item = db.execute("SELECT id FROM items WHERE name='Weapon Blade'").fetchone()[0]
        db.execute("UPDATE heroes SET image_path='custom.png',role='custom',wiki_url='custom-url',created_at='2000-01-01' WHERE id=?", (hero,))
        db.execute("UPDATE items SET image_path='item.png' WHERE id=?", (item,))
        db.execute("INSERT INTO skins(hero_id,name) VALUES(?, 'owned skin')", (hero,))
        db.execute("INSERT INTO matches(replay_name) VALUES('legacy')")
        match = db.execute("SELECT id FROM matches WHERE replay_name='legacy'").fetchone()[0]
        db.execute("INSERT INTO match_players(match_id,hero_id,player_name) VALUES(?, ?, 'legacy player')", (match, hero))
        db.commit()
        self.db.create_tables()
        self.db.populate_heroes()
        self.db.populate_items()
        self.assertEqual(tuple(db.execute("SELECT id,image_path,role,wiki_url,created_at FROM heroes WHERE name='Alpha'").fetchone()), (hero, 'custom.png', 'custom', 'custom-url', '2000-01-01'))
        self.assertEqual(tuple(db.execute("SELECT id,image_path FROM items WHERE name='Weapon Blade'").fetchone()), (item, 'item.png'))
        self.assertEqual(db.execute('PRAGMA foreign_keys').fetchone()[0], 1)
        self.assertEqual(db.execute('PRAGMA foreign_key_check').fetchall(), [])
        self.assertEqual(db.execute('SELECT hero_id FROM skins').fetchone()[0], hero)
        self.assertEqual(db.execute('SELECT kills FROM match_players').fetchone()[0], 0)
        self.assertIsNone(db.execute('SELECT provenance_json FROM matches').fetchone()[0])

    def test_database_happy_scoped_import_and_nulls(self) -> None:
        first = self.source('first')
        duplicate = self.source('duplicate')
        before = hashlib.sha256(first.read_bytes()).hexdigest()
        self.assertTrue(self.db.import_replay(str(first)))
        self.assertFalse(self.db.import_replay(str(duplicate)))
        duplicate.write_bytes(duplicate.read_bytes() + packet(20, 1))
        self.assertTrue(self.db.import_replay(str(duplicate)))
        rows = self.db.conn.execute('SELECT * FROM matches ORDER BY id').fetchall()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['replay_name'], 'sample')
        self.assertEqual(rows[1]['replay_name'], 'sample#' + rows[1]['replay_scope'])
        self.assertNotEqual(rows[0]['replay_scope'], rows[1]['replay_scope'])
        for row in rows:
            self.assertEqual(row['source_replay_name'], 'sample')
            self.assertIsNone(row['duration'])
            self.assertIsNone(row['winning_team'])
            provenance = json.loads(row['provenance_json'])
            self.assertEqual(provenance['duration']['status'], 'unknown')
            self.assertFalse(provenance['accepted_for_index'])
        hero = self.db.conn.execute("SELECT id FROM heroes WHERE name='Ringo'").fetchone()[0]
        players = self.db.conn.execute('SELECT * FROM match_players').fetchall()
        for player in players:
            self.assertEqual(player['hero_id'], hero)
            self.assertEqual(player['source_hero_id'], 0xF300)
            self.assertEqual(player['source_hero_namespace'], 'binary')
            for stat in ('kills', 'deaths', 'assists', 'minion_kills', 'gold'):
                self.assertIsNone(player[stat])
        self.assertEqual(self.db.conn.execute('PRAGMA foreign_key_check').fetchall(), [])
        self.assertEqual(hashlib.sha256(first.read_bytes()).hexdigest(), before)

    def test_database_happy_measured_zero_and_catalog_coverage(self) -> None:
        source = self.source('zero', 'zero')
        parsed = make_parsed_replay('zero')
        parsed['match_info'].update(duration_seconds=0, winner=None)
        parsed['teams']['left'][0].update(kills=0, deaths=None, assists=0, minion_kills=0, gold=0)
        with patch('vg.core.vgr_database.VGRParser') as parser:
            parser.return_value.parse.return_value = parsed
            self.assertTrue(self.db.import_replay(str(source)))
        row = self.db.conn.execute('SELECT duration,winning_team FROM matches').fetchone()
        self.assertEqual(tuple(row), (0, None))
        player = self.db.conn.execute("SELECT kills,deaths,assists,minion_kills,gold FROM match_players WHERE player_name='left_player'").fetchone()
        self.assertEqual(tuple(player), (0, None, 0, 0, 0))
        output = self.root / 'catalog.json'
        self.db.export_json(str(output))
        data = json.loads(output.read_text())
        self.assertEqual(data['coverage'], 'catalog_only')
        self.assertEqual(data['included_tables'], ['heroes', 'items'])
        self.assertEqual(data['excluded_tables'], ['skins', 'matches', 'match_players'])
        self.assertTrue(data['schema_version'])
        self.assertEqual(len(data['heroes']), len(self.db.get_heroes()))

    def test_database_happy_supplied_truth_preserves_zero_and_source(self) -> None:
        source = self.source('truth', 'truth-sample')
        truth = self.root / 'supplied.json'
        truth.write_text(json.dumps({'matches': [{
            'replay_name': 'truth-sample', 'replay_file': str(source),
            'match_info': {'duration_seconds': 0, 'winner': 'left'},
            'players': {'PlayerOne': {'hero_name': 'Inara', 'kills': 0, 'deaths': 2, 'assists': 0, 'minion_kills': 0, 'gold': 0}},
        }]}))
        before = (source.read_bytes(), truth.read_bytes())
        with patch('vg.core.vgr_database.VGRParser', side_effect=lambda path: VGRParser(path, truth_path=str(truth), auto_truth=False)):
            self.assertTrue(self.db.import_replay(str(source)))
        match = self.db.conn.execute('SELECT * FROM matches').fetchone()
        provenance = json.loads(match['provenance_json'])
        self.assertEqual((match['duration'], match['winning_team']), (0, 1))
        self.assertEqual(provenance['duration']['status'], 'supplied_truth')
        self.assertEqual(provenance['duration']['source'], str(truth))
        self.assertFalse(provenance['duration']['accepted_for_index'])
        player = self.db.conn.execute('SELECT * FROM match_players').fetchone()
        self.assertEqual((player['kills'], player['deaths'], player['assists'], player['minion_kills'], player['gold']), (0, 2, 0, 0, 0))
        self.assertEqual(player['source_hero_namespace'], 'legacy_mapping')
        self.assertEqual((source.read_bytes(), truth.read_bytes()), before)

    def test_database_failure_existing_orphans_and_legacy_identity(self) -> None:
        source = self.source('legacy', 'legacy')
        db = self.db.conn
        db.execute("INSERT INTO matches(replay_name) VALUES('legacy')")
        db.commit()
        before = db.execute('SELECT * FROM matches').fetchall()
        with self.assertRaisesRegex(VGDatabaseError, 'legacy_identity_unknown'):
            self.db.import_replay(str(source))
        self.assertEqual(db.execute('SELECT * FROM matches').fetchall(), before)
        db.execute('PRAGMA foreign_keys=OFF')
        db.execute("INSERT INTO skins(hero_id,name) VALUES(999999, 'orphan')")
        db.commit()
        db.execute('PRAGMA foreign_keys=ON')
        with self.assertRaisesRegex(VGDatabaseError, 'foreign_key_violation'):
            self.db.import_replay(str(self.source('new', 'new')))
        self.assertEqual(len(db.execute('PRAGMA foreign_key_check').fetchall()), 1)
        self.assertEqual(db.execute('SELECT * FROM matches').fetchall(), before)

    def test_database_failure_rollback_and_unknown_hero(self) -> None:
        source = self.source('rollback', 'rollback')
        parsed = make_parsed_replay('rollback')
        parsed['teams']['left'][0].update(hero_id=2, hero_name='Uncatalogued')
        self.db.conn.execute("CREATE TRIGGER reject_second BEFORE INSERT ON match_players WHEN NEW.player_name='right_player' BEGIN SELECT RAISE(ABORT, 'injected second player failure'); END")
        self.db.conn.commit()
        with patch('vg.core.vgr_database.VGRParser') as parser:
            parser.return_value.parse.return_value = parsed
            with self.assertRaisesRegex(VGDatabaseError, 'import_failed'):
                self.db.import_replay(str(source))
            self.assertEqual(self.db.conn.execute('SELECT COUNT(*) FROM matches').fetchone()[0], 0)
            self.assertEqual(self.db.conn.execute('SELECT COUNT(*) FROM match_players').fetchone()[0], 0)
            self.db.conn.execute('DROP TRIGGER reject_second')
            self.db.conn.commit()
            self.assertTrue(self.db.import_replay(str(source)))
        row = self.db.conn.execute("SELECT hero_id,source_hero_id FROM match_players WHERE player_name='left_player'").fetchone()
        self.assertEqual(tuple(row), (None, 2))
        provenance = json.loads(self.db.conn.execute('SELECT provenance_json FROM matches').fetchone()[0])
        self.assertTrue(provenance['players'][0]['hero_resolution_reason'])

    def test_database_failure_export_aliases_and_cli(self) -> None:
        original = self.path.read_bytes()
        alias = self.root / 'alias.json'
        os.link(self.path, alias)
        for output in (self.path, alias, *(Path(str(self.path) + suffix) for suffix in ('-wal', '-shm', '-journal'))):
            with self.subTest(output=output):
                with self.assertRaises(ValueError):
                    self.db.export_json(str(output))
                self.assertEqual(self.path.read_bytes(), original)
        result = subprocess.run([sys.executable, '-B', '-m', 'vg.core.vgr_database', 'import', '--db', str(self.path), '--input', str(self.root / 'missing')], cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_database_failure_publication_and_conflicting_hero(self) -> None:
        output = self.root / 'old-report.json'
        output.write_bytes(b'old report')
        original = self.path.read_bytes()
        with patch('vg.core.replay_output.os.replace', side_effect=OSError('injected report failure')):
            with self.assertRaisesRegex(ValueError, 'injected report failure'):
                self.db.export_json(str(output))
        self.assertEqual(output.read_bytes(), b'old report')
        self.assertEqual(self.path.read_bytes(), original)
        self.assertEqual(list(self.root.glob('.*.tmp')), [])
        source = self.source('conflict', 'conflict')
        parsed = make_parsed_replay('conflict')
        parsed['teams']['left'][0].update(hero_id=0xB801, hero_name='Alpha')
        with patch('vg.core.vgr_database.VGRParser') as parser:
            parser.return_value.parse.return_value = parsed
            self.assertTrue(self.db.import_replay(str(source)))
        player = self.db.conn.execute("SELECT hero_id,source_hero_id,source_hero_namespace FROM match_players WHERE player_name='left_player'").fetchone()
        self.assertEqual(tuple(player), (None, 0xB801, 'binary'))


if __name__ == '__main__':
    unittest.main()
