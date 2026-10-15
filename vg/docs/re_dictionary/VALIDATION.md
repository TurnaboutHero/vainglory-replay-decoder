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

## Combined offline integration

The combined feature branch starts at `65bab83` and adds recording identity
diagnostics, bounded outgoing request parsing, the VGNL offline importer and
this dictionary. The identity module adds diagnostics to `native_roster.py`.
To keep historical dictionary evidence immutable, its original roster source
reference now resolves to `baseline/native_roster-65bab83.py.txt`, an exact
snapshot of `vg/core/native_roster.py` at `65bab83` with the original hash.
This does not upgrade historical roster claims or actor/skin split status.

All 97 catalog source hashes still verify against the original evidence roots.
The 54 external references still require explicitly provided roots.

## Independently reviewed research follow-up

The follow-up to combined baseline `709dd8bb` adds 20 bounded/unresolved entries,
bringing the catalog to 71 entries, 137 sources and the same 9 artifacts. All 51
original entries, 97 original source records and 9 artifact records are unchanged.
The adjacent `deepening/README.md` summarizes the three investigations;
`deepening/SOURCE_MANIFEST.json` lists the new source hashes and namespaces.

Default validation verifies 52 repository sources and reports 85 external
references as unresolved. With both original roots supplied, all 137 hashes
verify. The Draft 2020-12 schema and deterministic index checks pass.
The focused dictionary/model/guardrail run passes 55 tests: 30 existing dictionary
tests, 7 terminal models, 5 override models, 8 cooldown arithmetic models and
5 research-scope guardrails. Independent review separately reran all 25 new tests.

The producer review receipt is an external hash-pinned catalog source. Independent
integration review verified the 20 additions, unchanged original entries and no
production decoder diff. New raw native exports remain external; all-request
provenance and withheld winner remain unchanged. Synthetic models cover selected
normal-range control flow/arithmetic, not complete native execution, historical
application, general cast eligibility, exact final display or server validation.

Final combined offline regression suite: 1,065 tests passed in 108.778 seconds
using Python 3.12.14. The full command above includes all 25 new tests.

## Reviewed buff/status extension

The separate follow-up to `52f1786d` adds 29 bounded entries, bringing the catalog
to 100 entries, 161 source references and the same 9 artifact identities. All
71 previous entries, 137 source records and 9 artifact records are unchanged.
The schema adds only the `status_effect` category; no production decoder or
research CLI Python code changes. The generated index includes 타격 강화제 and
수정 강화제 while retaining canonical English identities in structured facts.

Default verification resolves 60 repository references and reports 101 external
sources unresolved. Supplying the original research/shared roots verifies all
161 source hashes. Draft 2020-12 and deterministic index checks pass. The portable
focused run passes 59 tests: 30 dictionary tests plus 7 lifecycle models,
5 jungle/infusion models, 11 status models and 6 catalog scope checks.

Producer reviews bind the frozen lifecycle, jungle/infusion and status packages.
The adjacent `buff_status/SOURCE_MANIFEST.json` exposes their source hashes and
external-reference status. New disassembly, executable/resource contents and raw
replay payloads are not imported. Build-bound checks remain external evidence;
portable models are not substitutes for native execution or runtime observations.

Important safeguards include predicate-false expiry for an already-expired timer,
explicit post-reactivation model scope, Lifetime stubs versus real infusion
script-list refresh, conditional acquisition/stat/heal behavior, mutable flag
contributors, action-specific readiness conditions, deferred slow cleanup and
metadata-filtered queued cleanse. Native `043e` payload16 versus historical22,
and unsupported historical `043f`38, remain blockers to production decoding.

Final full combined offline suite: 1,094 tests passed in 79.691 seconds.
Independent integration review reran all 29 new tests and verified every source
hash plus the schema, with no production/research Python delta.

## Reviewed progression/reward extension

The isolated follow-up to `20c76277` adds 20 bounded entries covering hero XP/level,
skill ranks, creature deaths/credit and shared-reward boundaries. The catalog now
contains 120 entries, 230 sources and the same 9 artifacts. All 100 previous
entries, 161 source records and 9 artifacts are unchanged; production and research
Python code and the schema are unchanged.

Default validation verifies 74 repository references and reports 156 external
sources unresolved. With both original roots supplied, all 230 hashes verify.
Draft 2020-12 and deterministic index checks pass. The focused run passes 67 tests:
30 dictionary tests plus 11 skill-rank, 12 XP/hero, 4 creature-parser, 4 finite
individual-resource and 6 catalog-scope tests.

The source manifest binds four independent producer reviews. Native/resource/
replay exports remain external. Skill tests use a small curated fixture of counts
and selected fields instead of original raw replay samples. Creature findings
retain `accepted_for_index:false`: research-catalog inclusion is not acceptance
for a gameplay index, reducer, last-hit or objective-award attribution.

The hero model preserves cap-12 exit, level-one progress reset, below-cap zero-delta
recalculation and subtraction of one old threshold rather than a per-level loop.
Learned-rank algebra excludes rank zero. Resource models illustrate finite small
integer ADD/SET distinctions only, not native floating point, full lifetime
sources or shared-reward eligibility. Historical producer build remains unmatched.

## Reviewed XP baseline and structure extension (2026-10-15)

The isolated extension from `2a9925d` adds 13 research entries, for 133 total, and 25 bounded model/catalog tests. All 120 prior entries and 230 prior source definitions remain unchanged. The 250 current source hashes verify with original external roots. The XP recurrence checker reproduces 5010 float32 comparisons using ten initial baselines from the same development-seen, unmatched recording; this is not independent gameplay proof. Structure findings retain unaccepted replay-index/production flags, with raw exports and assets external.

Independent producer receipts are referenced in the catalog. Integration receipt and final full-suite log are held externally to avoid self-referential hashes. Production/research Python and catalog schema are unchanged.
