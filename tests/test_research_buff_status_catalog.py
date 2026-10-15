"""Portable safety checks for static buff/status research publication."""
import hashlib
import json
from pathlib import Path
import unittest
from vg.research import dictionary as d


class BuffStatusCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = d.load_json(d.CATALOG_PATH)
        cls.entries = [e for e in cls.catalog['entries'] if 'buff-status-followup' in e['tags']]
        cls.root = Path(__file__).resolve().parents[1]

    def test_no_runtime_promotion(self):
        self.assertTrue(self.entries)
        for entry in self.entries:
            self.assertIn(entry['proof']['status'], ('bounded', 'unresolved'))
            self.assertFalse(entry['proof']['native_or_server_execution_performed_for_this_catalog'])
            self.assertEqual(entry['scope']['recording_build_match'], 'unverified')
            self.assertIn('independent_review', entry['proof']['validation_kinds'])
            self.assertFalse({'controlled_runtime', 'runtime_observation'} & set(entry['proof']['validation_kinds']))

    def test_status_category_is_searchable(self):
        entries = d.search(self.catalog, category='status_effect')
        self.assertEqual(len(entries), 7)
        self.assertTrue(all('buff-status-followup' in e['tags'] for e in entries))

    def test_original_native_address_space_retained(self):
        for entry in self.entries:
            self.assertEqual(entry['scope']['artifact_refs'], ['win-x86-laa'])
            for location in entry['functions']:
                self.assertEqual(location['address_kind'], 'preferred_va')
                self.assertEqual(location['artifact_id'], 'win-x86-laa')

    def test_native_receipts_are_external_references(self):
        for source in self.catalog['sources']:
            if source['id'].startswith('src-buffstatus-') and source['kind'] == 'native_receipt_reference':
                self.assertEqual(source['publication'], 'external_reference_only')
                self.assertEqual(source['location']['namespace'], 'research')

    def test_manifest_matches_catalog_source_records(self):
        manifest = json.loads((self.root / 'vg/docs/re_dictionary/buff_status/SOURCE_MANIFEST.json').read_text())
        self.assertFalse(manifest['native_execution'])
        self.assertFalse(manifest['raw_exports_distributed'])
        self.assertEqual(manifest['sources'], [s for s in self.catalog['sources'] if s['id'].startswith('src-buffstatus-')])
        for source in manifest['sources']:
            if source['location']['namespace'] == 'repo':
                self.assertEqual(hashlib.sha256((self.root / source['location']['path']).read_bytes()).hexdigest(), source['sha256'])

    def test_historical_layout_mismatch_retains_limit(self):
        for entry in self.entries:
            limit = ' '.join(entry['limitations_ko'])
            self.assertIn('043e', limit)
            self.assertIn('16 bytes', limit)
            self.assertIn('22', limit)
            self.assertIn('no unsupported production decode', limit)


if __name__ == '__main__':
    unittest.main()
