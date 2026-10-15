"""Guardrails for reviewed research; does not execute a native game or server."""
import unittest
from vg.research import dictionary as d


class ResearchFollowupCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = d.load_json(d.CATALOG_PATH)
        cls.entries = [e for e in cls.catalog['entries'] if 'deepening' in e['tags']]

    def test_new_claims_are_bounded_or_unresolved(self):
        self.assertTrue(self.entries)
        for entry in self.entries:
            self.assertIn(entry['proof']['status'], ('bounded', 'unresolved'))
            self.assertFalse(entry['proof']['native_or_server_execution_performed_for_this_catalog'])
            self.assertIn('independent_review', entry['proof']['validation_kinds'])
            self.assertNotIn('runtime_observation', entry['proof']['validation_kinds'])
            self.assertNotIn('controlled_runtime', entry['proof']['validation_kinds'])

    def test_build_identity_and_unverified_producer_preserved(self):
        for entry in self.entries:
            self.assertEqual(entry['scope']['artifact_refs'], ['win-x86-laa'])
            self.assertEqual(entry['scope']['recording_build_match'], 'unverified')
            self.assertTrue(entry['limitations_ko'])
            for function in entry['functions']:
                self.assertEqual(function['address_kind'], 'preferred_va')

    def test_raw_native_sources_remain_external(self):
        for source in self.catalog['sources']:
            if source['id'].startswith('src-deepening-') and source['kind'] == 'native_receipt_reference':
                self.assertEqual(source['publication'], 'external_reference_only')
                self.assertNotEqual(source['location']['namespace'], 'repo')

    def test_override_and_play_mode_gate_limits_remain_explicit(self):
        entries = {e['id']: e for e in self.entries}
        for opcode in ('041a', '041b'):
            entry = entries['VGRE-deepening-combat-' + opcode]
            limits = ' '.join(entry['limitations_ko'])
            self.assertIn('0x0209e204 != 0', limits)
            self.assertIn('opposite gate', limits)
            self.assertIn('opaque', limits)

    def test_account_and_result_promotions_are_withheld(self):
        entries = {e['id']: e for e in self.entries}
        self.assertEqual(entries['VGRE-deepening-identity-authenticated-account-from-roster']['proof']['status'], 'unresolved')
        result = entries['VGRE-deepening-terminal-last-request-is-final-result']
        self.assertIn('Neither last request nor first recorded request', result['claim_ko'])


if __name__ == '__main__':
    unittest.main()
