"""Publication guardrails; same-fixture agreement is not native execution."""
import hashlib
import json
from pathlib import Path
import unittest
from vg.research import dictionary as d


class XPStructureCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = d.load_json(d.CATALOG_PATH)
        cls.entries = [e for e in cls.catalog['entries'] if 'xp-structure-followup' in e['tags']]
        cls.root = Path(__file__).resolve().parents[1]

    def test_static_and_historical_scope_remains_bounded(self):
        self.assertTrue(self.entries)
        for entry in self.entries:
            self.assertIn(entry['proof']['status'], ('bounded', 'unresolved'))
            self.assertFalse(entry['proof']['native_or_server_execution_performed_for_this_catalog'])
            self.assertEqual(entry['scope']['recording_build_match'], 'unverified')
            self.assertIn('independent_review', entry['proof']['validation_kinds'])
            self.assertFalse({'controlled_runtime', 'runtime_observation'} & set(entry['proof']['validation_kinds']))

    def test_exact_native_and_recording_domains(self):
        for entry in self.entries:
            self.assertTrue(set(entry['scope']['artifact_refs']) <= {'win-x86-laa', 'h5810-development'})
            self.assertTrue(entry['scope']['artifact_refs'])
            for function in entry['functions']:
                self.assertEqual(function['artifact_id'], 'win-x86-laa')
                self.assertEqual(function['address_kind'], 'preferred_va')

    def test_manifest_matches_hashed_catalog_sources(self):
        manifest = json.loads((self.root / 'vg/docs/re_dictionary/xp_structures/SOURCE_MANIFEST.json').read_text())
        self.assertFalse(manifest['native_execution'])
        self.assertFalse(manifest['raw_exports_distributed'])
        selected = [s for s in self.catalog['sources'] if s['id'].startswith('src-xpstructure-') or s['id'] == 'src-xp-hero-baseline-delta']
        self.assertEqual(manifest['sources'], selected)
        for source in selected:
            if source['location']['namespace'] == 'repo':
                self.assertEqual(hashlib.sha256((self.root / source['location']['path']).read_bytes()).hexdigest(), source['sha256'])
            if '/receipts/' in source['location']['path'] or '/raw/' in source['location']['path']:
                self.assertEqual(source['publication'], 'external_reference_only')

    def test_recurrence_is_development_evidence(self):
        entry = next(e for e in self.entries if e['id'] == 'VGRE-xp-historical-forward-recurrence')
        self.assertEqual(entry['scope']['artifact_refs'], ['h5810-development'])
        self.assertEqual(entry['scope']['execution_context'], 'synthetic_and_development')
        self.assertIn('development_corpus', entry['proof']['validation_kinds'])
        self.assertEqual(entry['functions'], [])


if __name__ == '__main__':
    unittest.main()
