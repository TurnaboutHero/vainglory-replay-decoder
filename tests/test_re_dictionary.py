"""Portable catalog/CLI tests; no game binary, private replay, Git, or network."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from vg.research import dictionary as d


class DictionaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = d.load_json(d.CATALOG_PATH)

    def altered(self):
        return deepcopy(self.catalog)

    def cli(self, *args, cwd=None):
        return subprocess.run([sys.executable, '-B', str(Path(d.__file__).resolve()), *args],
                              cwd=cwd, capture_output=True, text=True, encoding='utf-8')

    def test_schema_and_cross_references(self):
        self.assertEqual([], d.validate_document(self.catalog))

    def test_generated_index_is_deterministic_and_current(self):
        expected = d.render_index(self.catalog)
        self.assertEqual(expected, d.render_index(self.catalog))
        self.assertEqual(d.INDEX_PATH.read_text(encoding='utf-8'), expected)

    def test_repo_sources_verify_without_external_inputs(self):
        results = d.verify_sources(self.catalog)
        self.assertTrue(any(r['status'] == 'verified' for r in results))
        self.assertTrue(any(r['status'] == 'unresolved_external' for r in results))
        self.assertTrue(all(r['status'] in ('verified','unresolved_external') for r in results))

    def test_duplicate_entry_id_rejected(self):
        c = self.altered(); c['entries'].append(deepcopy(c['entries'][0]))
        self.assertTrue(any('duplicate entries ID' in e for e in d.validate_document(c)))

    def test_duplicate_source_id_rejected(self):
        c = self.altered(); c['sources'].append(deepcopy(c['sources'][0]))
        self.assertTrue(any('duplicate sources ID' in e for e in d.validate_document(c)))

    def test_unknown_reference_rejected(self):
        c = self.altered(); c['entries'][0]['evidence'][0]['source_id'] = 'src-does-not-exist'
        self.assertTrue(any('unknown source' in e for e in d.validate_document(c)))

    def test_unknown_artifact_rejected(self):
        c = self.altered(); c['entries'][0]['scope']['artifact_refs'] = ['missing']
        self.assertTrue(any('unknown artifact' in e for e in d.validate_document(c)))

    def test_wrong_address_space_rejected(self):
        c = self.altered(); e = next(x for x in c['entries'] if x['functions'])
        e['functions'][0]['address_kind'] = 'dex_file_offset'
        # Ensure a genuine mismatch even if the selected entry happens to be DEX.
        if c['artifacts'][0]['address_kind'] == 'dex_file_offset':
            self.fail('fixture drift')
        self.assertTrue(any('address-kind mismatch' in err for err in d.validate_document(c)))

    def test_function_artifact_must_be_scoped(self):
        c=self.altered(); e=next(x for x in c['entries'] if x['functions'])
        e['functions'][0]['artifact_id']='not-scoped'
        self.assertTrue(any('outside entry scope' in err for err in d.validate_document(c)))

    def test_proof_status_and_validation_are_distinct(self):
        c=self.altered(); c['entries'][0]['proof']['semantic_confidence']='static_instructions'
        self.assertTrue(d.validate_document(c))
        c=self.altered(); c['entries'][0]['proof']['validation_kinds']=['high']
        self.assertTrue(d.validate_document(c))

    def test_corrected_entry_requires_correction(self):
        c=self.altered(); c['entries'][0]['proof']['status']='corrected'; c['entries'][0]['corrections_ko']=[]
        self.assertTrue(any('explicit correction' in e for e in d.validate_document(c)))

    def test_empty_limits_and_evidence_rejected(self):
        for key in ('evidence','limitations_ko'):
            with self.subTest(key=key):
                c=self.altered(); c['entries'][0][key]=[]
                self.assertTrue(d.validate_document(c))

    def test_malformed_shape_reports_errors_without_crashing(self):
        for value in (None, [], 0, {}, {'schema_version':1}, {'entries':'bad'}):
            with self.subTest(value=value):
                self.assertTrue(d.validate_document(value))

    def test_hash_format_and_boolean_integer_rejected(self):
        c=self.altered(); c['sources'][0]['sha256']='BAD'; self.assertTrue(d.validate_document(c))
        c=self.altered(); c['schema_version']=True; self.assertTrue(d.validate_document(c))

    def test_nested_shapes_rejected_before_cross_reference_indexing(self):
        mutations = (
            ('scope', None), ('proof', []), ('functions', ['0x1234']),
            ('fields', ['payload+0']), ('calls', [None]), ('evidence', [{}]),
            ('layout_notes', [None]), ('related_entry_ids', [123]),
        )
        for key, value in mutations:
            with self.subTest(key=key):
                c = self.altered()
                c['entries'][0][key] = value
                self.assertTrue(d.validate_document(c))

    def test_layout_notes_are_optional_but_typed(self):
        c = self.altered()
        c['entries'][0]['layout_notes'] = ['Historical layout retained as text']
        self.assertEqual([], d.validate_document(c))
        self.assertIn('Historical layout retained as text', d.render_index(c))

    def test_field_offsets_require_nonnegative_integers(self):
        for offset in (True, -1, '0x20', 1.5, None):
            with self.subTest(offset=offset):
                c = self.altered()
                e = next(e for e in c['entries'] if e['fields'])
                e['fields'][0]['offset'] = offset
                self.assertTrue(d.validate_document(c))

    def test_unknown_keys_rejected(self):
        c=self.altered(); c['entries'][0]['mystery']=1; self.assertTrue(d.validate_document(c))

    def test_literal_uuid_and_machine_path_rejected(self):
        for value in ('00000000-0000-0000-0000-000000000001', '/workspace/secret'):
            c=self.altered(); c['entries'][0]['claim_ko']=value
            self.assertTrue(d.validate_document(c))

    def test_nonportable_paths_rejected(self):
        for path in ('../a','/a','a/../b','a//b','a\\b','./a','a\n',
                     'C:/evidence.txt','C:evidence.txt','file:///evidence.txt'):
            with self.subTest(path=path):
                self.assertFalse(d.portable_path(path))
                c=self.altered(); c['sources'][0]['location']['path']=path
                self.assertTrue(d.validate_document(c))

    def fixture_catalog(self, root, content=b'synthetic evidence'):
        (root/'evidence.txt').write_bytes(content)
        return {'sources':[{'id':'s','location':{'namespace':'fixture','path':'evidence.txt'},'sha256':hashlib.sha256(content).hexdigest()}]}

    def test_external_hash_match_mismatch_missing_unresolved(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); c=self.fixture_catalog(root)
            self.assertEqual('unresolved_external',d.verify_sources(c)[0]['status'])
            self.assertEqual('verified',d.verify_sources(c,external_roots={'fixture':root})[0]['status'])
            (root/'evidence.txt').write_bytes(b'changed')
            self.assertEqual('hash_mismatch',d.verify_sources(c,external_roots={'fixture':root})[0]['status'])
            (root/'evidence.txt').unlink()
            self.assertEqual('missing_source',d.verify_sources(c,external_roots={'fixture':root})[0]['status'])

    def test_symlink_escape_is_not_hashed(self):
        with tempfile.TemporaryDirectory() as tmp:
            outer=Path(tmp); root=outer/'root'; root.mkdir(); c=self.fixture_catalog(root)
            outside=outer/'outside'; outside.write_text('outside')
            (root/'evidence.txt').unlink(); (root/'evidence.txt').symlink_to(outside)
            self.assertEqual('unsafe_path',d.verify_sources(c,external_roots={'fixture':root})[0]['status'])

    def test_source_publication_namespace_mismatch(self):
        c=self.altered(); c['sources'][0]['publication']='existing_repository'
        c['sources'][0]['location']['namespace']='research'
        self.assertTrue(any('publication/namespace' in e for e in d.validate_document(c)))

    def test_search_opcode_case_and_conjunctive_text(self):
        self.assertEqual(d.search(self.catalog,opcode='044a'),d.search(self.catalog,opcode='0x044A'))
        self.assertTrue(d.search(self.catalog,opcode='0449'))
        self.assertEqual([],d.search(self.catalog,'definitely-absent-word'))
        self.assertTrue(d.search(self.catalog,'terminal entity'))
        self.assertTrue(all(e['category']=='health' for e in d.search(self.catalog,category='health')))

    def test_cli_search_from_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=self.cli('search','--opcode','0449','--json',cwd=tmp)
        self.assertEqual(0,p.returncode,p.stderr)
        self.assertTrue(json.loads(p.stdout))

    def test_cli_show_and_missing_id(self):
        p=self.cli('show','VGRE-health-impact-prefix'); self.assertEqual(0,p.returncode,p.stderr)
        self.assertEqual('VGRE-health-impact-prefix',json.loads(p.stdout)['id'])
        self.assertEqual(1,self.cli('show','VGRE-missing').returncode)

    def test_cli_default_and_strict_external_modes(self):
        p=self.cli('validate','--json','--check-index'); self.assertEqual(0,p.returncode,p.stderr)
        report=json.loads(p.stdout)
        self.assertTrue(report['generated_index_matches'])
        self.assertGreater(report['unresolved_external_sources'],0)
        self.assertEqual(2,self.cli('validate','--require-external').returncode)

    def test_cli_invalid_root_and_malformed_json(self):
        self.assertEqual(2,self.cli('validate','--external-root','repo=/tmp').returncode)
        self.assertEqual(2,self.cli('validate','--external-root','research=').returncode)
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'bad.json'; path.write_text('{"x": 1, "x": 2}')
            p=self.cli('--catalog',str(path),'search')
            self.assertEqual(2,p.returncode); self.assertIn('duplicate JSON key',p.stderr)

    def test_cli_does_not_modify_sources_or_catalog(self):
        paths=[d.CATALOG_PATH,d.SCHEMA_PATH,d.INDEX_PATH]
        before={p:(p.read_bytes(),p.stat().st_mtime_ns) for p in paths}
        self.assertEqual(0,self.cli('validate').returncode)
        self.assertEqual(0,self.cli('search','--opcode','041e').returncode)
        self.assertEqual(before,{p:(p.read_bytes(),p.stat().st_mtime_ns) for p in paths})

    def test_major_corrections_remain_present(self):
        entries={e['id']:e for e in self.catalog['entries']}
        for key in ('VGRE-request-item-layouts','VGRE-upload-terminal-hero-only','VGRE-health-resource-set-add',
                    'VGRE-cooldown-timer-reference-hud','VGRE-cooldown-expiry-overshoot-stage4'):
            self.assertTrue(entries[key]['corrections_ko'])
        self.assertIn('65bab83',' '.join(entries['VGRE-identity-spawn-skin-observation']['limitations_ko']))


if __name__=='__main__':
    unittest.main()
