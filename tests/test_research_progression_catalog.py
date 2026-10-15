"""Guardrails for reviewed progression/reward findings, not game execution."""
import hashlib
import json
from pathlib import Path
import unittest
from vg.research import dictionary as d


class ProgressionCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = d.load_json(d.CATALOG_PATH)
        cls.entries = [e for e in cls.catalog['entries'] if 'progression-rewards-followup' in e['tags']]
        cls.root = Path(__file__).resolve().parents[1]

    def test_no_runtime_or_production_promotion(self):
        self.assertTrue(self.entries)
        for entry in self.entries:
            self.assertIn(entry['proof']['status'], ('bounded', 'unresolved'))
            self.assertFalse(entry['proof']['native_or_server_execution_performed_for_this_catalog'])
            self.assertEqual(entry['scope']['recording_build_match'], 'unverified')
            self.assertIn('independent_review', entry['proof']['validation_kinds'])
            self.assertFalse({'controlled_runtime', 'runtime_observation'} & set(entry['proof']['validation_kinds']))

    def test_exact_address_domain(self):
        for entry in self.entries:
            self.assertTrue(set(entry['scope']['artifact_refs']) <= {'win-x86-laa', 'h5810-development'})
            self.assertTrue(entry['scope']['artifact_refs'])
            for function in entry['functions']:
                self.assertEqual(function['artifact_id'], 'win-x86-laa')
                self.assertEqual(function['address_kind'], 'preferred_va')

    def test_manifest_and_repository_sources(self):
        manifest = json.loads((self.root / 'vg/docs/re_dictionary/progression_rewards/SOURCE_MANIFEST.json').read_text())
        self.assertFalse(manifest['native_execution'])
        self.assertFalse(manifest['raw_exports_distributed'])
        selected = [s for s in self.catalog['sources'] if s['id'].startswith(('src-progression-', 'src-skill-'))]
        self.assertEqual(manifest['sources'], selected)
        for source in selected:
            if source['location']['namespace'] == 'repo':
                self.assertEqual(hashlib.sha256((self.root / source['location']['path']).read_bytes()).hexdigest(), source['sha256'])
            if '/receipts/' in source['location']['path'] or '/raw/' in source['location']['path']:
                self.assertEqual(source['publication'], 'external_reference_only')

    def test_skill_corpus_fixture_omits_raw_payloads(self):
        fixture = json.loads((self.root / 'vg/docs/re_dictionary/progression_rewards/skill-fixtures.json').read_text())
        self.assertFalse(fixture['corpus']['build_match'])
        for record in fixture['corpus']['counts']:
            self.assertEqual(set(record), {'opcode', 'payload_length', 'count'})

    def test_creature_candidates_remain_unaccepted_for_replay_index(self):
        findings = json.loads((self.root / 'vg/docs/re_dictionary/progression_rewards/creature-findings.json').read_text())
        self.assertFalse(findings['production_ready'])
        self.assertFalse(findings['accepted_for_index'])
        for entry in findings['entries']:
            self.assertFalse(entry['production_ready'])
            self.assertFalse(entry['accepted_for_index'])

    def test_request_and_applied_skill_entries_stay_distinct(self):
        entries = {e['id']: e for e in self.entries}
        self.assertEqual(entries['VGRE-skill-upgrade-request']['opcodes'], ['0436'])
        self.assertEqual(entries['VGRE-skill-investment-apply']['opcodes'], ['043a'])


if __name__ == '__main__':
    unittest.main()
