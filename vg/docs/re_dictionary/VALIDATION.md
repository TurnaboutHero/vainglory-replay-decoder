# Dictionary validation, 2026-10-15

The catalog curates 51 entries, 97 source references and 9 artifact identities
against decoder baseline `65bab83`. It is not an exhaustive inventory of all
archived research, and an artifact identity is not necessarily a verified release.

## Reproduce

From the repository root, using Python 3.12 or newer:

```sh
python -X utf8 -B -m unittest tests.test_re_dictionary -v
python -X utf8 -B -m unittest discover -s tests -v
python -B -m vg.research.dictionary validate --check-index
```

The full suite also requires Node.js 18 or newer. The dictionary itself has no
third-party dependencies, network requests or write operations.

Final local results on Python 3.12.14 and Node.js 24.19.0: all 30 focused
dictionary tests and all 962 offline regression tests passed. `git diff --check`
also passed.

Default validation verifies 43 repository references and reports 54 external
references as unresolved. To verify the latter, supply the existing research
and shared evidence directories explicitly:

```sh
python -B -m vg.research.dictionary validate --check-index \
  --external-root research=/path/to/research \
  --external-root shared=/path/to/shared --require-external
```

With those original evidence roots available, all 97 source hashes matched,
with zero unresolved or failed sources, and the generated Korean index matched
the committed catalog. External reports, raw binaries and replay recordings
are not bundled by this change. A fresh clone cannot independently resolve
the 54 external references without those inputs.

The schema and catalog also passed an independent Draft 2020-12 check using
`jsonschema` 4.26.0. This optional reviewer check is not a runtime dependency.
Focused tests cover nested malformed shapes, typed layout notes and offsets,
cross-references, duplicate IDs and JSON keys, unsafe paths, hash failures,
read-only CLI behavior and index determinism.

## Evidence limits

- Hash verification proves source-file identity, not the truth of every claim
- No native game execution, live network/server test or new runtime observation
  was performed for this catalog
- Static semantics, synthetic tests, historical corpus observations and runtime
  receipts remain distinct; uncertain claims retain their limitations
- Baseline `65bab83` does not include the separate actor/skin identity split;
  dictionary documentation is not an implementation or integration claim
