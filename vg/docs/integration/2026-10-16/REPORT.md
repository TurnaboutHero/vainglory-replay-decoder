# Consolidation audit: 2026-10-16

Frozen main `65bab83ae27e4c0f81338471a30a4aa1ee0944df`; research start `e95918c98962f334a68b703cc04e61edc9200be5`.
Integration content commit `303031aa08ad2f14d9acab637a72216d454ea1c4`. Main is an ancestor of the research start; no main change was dropped.
23 original remote tips were freshly fetched. Open PR count was zero; PR27 and PR28 were already merged.

## Preservation matrix

Feature files / missing counts use feature delta bases, including main merge-side bases for already merged branches. Different blobs are reviewed supersession/combined modules, not automatically missing content. The machine-readable [BRANCHES.json](BRANCHES.json) retains exact differing blob IDs, patch-equivalent commit IDs and cleanup reasons.

| Branch | Frozen tip | In main | In integration | Feature files / missing | Related PR | Unique-change / preservation reason |
| --- | --- | --- | --- | --- | --- | --- |
| `codex/cooldown-research-followup` | `311232a1deaa60835068a1939eaf1ec023e21ac0` | ancestor | ancestor | 203 / 0 | none | No unique commits vs research; 202 feature files identical, README expanded. Parent separately audits cooldown semantics. |
| `codex/pr27-integration-validation` | `b40a9de5420e7d7a1d95be7a507b57273fb6a1bc` | patch-equivalent | patch/content | 205 / 0 | none | Portable test patch equivalent exists; integration merge commit itself lacks patch-id by design. 204 blobs identical, README expanded. No missing file. |
| `codex/pr27-portable-tests` | `2c37d2ba46d6d17e52e279f6ca78405c9f1314cc` | patch-equivalent | patch/content | 3 / 0 | none | Patch-equivalent cf23a5d history already present; fixture and test blobs identical; README reference list expanded. |
| `codex/rea-item-activation` | `cf23a5daf3d1bf856e3a02e1252f340d12f12e1e` | ancestor | ancestor | 17 / 0 | #27 MERGED | Merged PR27. 14 identical feature blobs; native_event_fields adds cooldown cases without removing item cases; timeline difference is help-text expansion; README reference list expanded. |
| `codex/rea-item-events` | `df1da9a28282d0298b3eece999a2454ab9959ff3` | ancestor | ancestor | 7 / 0 | #26 MERGED | Merged PR26. Four identical feature blobs. Later item-activation/cooldown additions supersede shared timeline/native_event_fields; original sell/rejection cases retained. |
| `codex/verified-cooldown-events` | `ed828514bccd631f3d0dfeb5a19e3b832da83302` | ancestor | ancestor | 203 / 0 | #28 MERGED | Merged PR28; 202 identical feature blobs; README expansion only. Parent cooldown audit owns deeper confirmation. |
| `codex/verified-cooldown-events-local-20261015` | `a64db6ebf6b50c77b5a9d107620967617310c42c` | patch-equivalent | patch/content | 104 / 0 | none | Commit patch equivalent in target; 102 identical blobs; cooldown doc and README differing. Parent cooldown audit reviews exact superseding doc edits. |
| `feat/decoder-stat-accuracy-20261004` | `b7d5a3af675db6d6a96ae3c71823a3f6d13b5d24` | ancestor | ancestor | 192 / 0 | #13 MERGED | Merged PR13. 173 identical introduced blobs, zero absent. 19 shared-file blobs differ after eligibility, capture/display, provenance, and recording-identity work. Historical tip remains reachable through main; do not replace current shared files with older ones. |
| `feat/offline-combined-integration-20261015` | `61c6d4900742d69902ed2a7be4d6c55c47a16d92` | not yet included | ancestor | 29 / 0 | none | Exact ancestor. 24 feature blobs identical; README and generated dictionary/catalog/schema superseded by reviewed chain. All old entry/source IDs and objects retained. |
| `feat/offline-outgoing-requests` | `5688ce3b0c64ef2d3cefe1b668474ce0a3a4851a` | not yet included | patch/content | 4 / 0 | none | 5688ce3 patch-id matches 0be9ea1; implementation/test/doc blobs identical; README contains all old nonempty lines. |
| `feat/offline-vgnl-importer` | `9c241bca100a088af5f435f2f2e9098320aa87d6` | not yet included | patch/content | 4 / 0 | none | 9c241bc patch-id matches 19652d4; implementation/test/doc blobs identical; README contains all old nonempty lines. |
| `feat/recording-identity-diagnostics` | `f9a4436525428475ee073e8b38385771e05ed50b` | not yet included | ancestor | 15 / 0 | none | Exact ancestor f9a4436. All14 implementation/test/doc feature blobs identical; README contains all old nonempty lines. |
| `feat/reverse-engineering-dictionary` | `a2dc5ec64fb12e3d0c6d5dafb08c97748529116e` | not yet included | patch/content | 8 / 0 | none | a2dc5ec patch-id matches84d68a9. Parser/package/test blobs identical. All51 entries unchanged in current141; all97 sources retained, one intentionally repointed to frozen baseline file preserving original source SHA. Current schema adds status_effect; keep expanded catalog/index/validation/schema. |
| `feat/reviewed-buff-status-20261015` | `51f5db7d7ecfc3fba9ec9c9f82bd524ea0be3aff` | not yet included | ancestor | 49 / 0 | none | Exact ancestor.45 identical feature blobs; all entry/source objects retained unchanged; README/catalog/index/validation superseded by later reviewed additions. |
| `feat/reviewed-progression-rewards-20261015` | `471beb6d9c661db13fa93956e084071c62d6af37` | not yet included | ancestor | 64 / 0 | none | Exact ancestor.60 identical feature blobs; all entry/source objects retained unchanged; generated summary files expanded later. |
| `feat/reviewed-research-followup-20261015` | `b6e2fa2d6451d90b8d37a91e737db87a00085ee0` | not yet included | ancestor | 40 / 0 | none | Exact ancestor.35 identical feature blobs; all entry/source objects retained unchanged; generated docs/schema expanded later. |
| `feat/reviewed-respawn-recall-20261015` | `9712ab6985357bd89cd3cfc062e2068e303d3100` | not yet included | ancestor | 81 / 0 | none | Exact ancestor. All81 feature delta blobs identical; no missing or differing feature file. |
| `feat/reviewed-xp-structures-20261015` | `46e2a47cc6dd4908d5180f1e288e4d91bbb177f4` | not yet included | ancestor | 75 / 0 | none | Exact ancestor.71 identical feature blobs; all entry/source objects retained unchanged; generated docs expanded later. |
| `fix/definitive-analysis-eligibility-20261011` | `296b10174db299f896bb4bd5c41bc57187de497f` | ancestor | ancestor | 30 / 0 | #25 MERGED | Merged PR25.28 feature blobs identical. player_state differences only add recording_identity import/result/output and move roster acquisition before query-validity return; definitive eligibility handling retained. README reference list expanded. |
| `fix/h5672-spawn-skin-identity-20261014` | `76e1fbacb422a1fa7b3736451d76264bbd338953` | not yet included | ancestor | 14 / 0 | none | Only initially missing feature: merged all five original commits. Actor/skin split and all ten missing evidence/test files preserved alongside recording diagnostics. Combined module hashes and historical evidence references reconciled. |
| `main` | `65bab83ae27e4c0f81338471a30a4aa1ee0944df` | ancestor | ancestor | 203 / 0 | none | Baseline reference; protect/default main. Feature-content check of last merge delta202 identical blobs, README expanded in research. |
| `publish-cooldown-integration` | `81fd070f43677979e86772657d43799c53573adf` | patch-equivalent | patch/content | 203 / 0 | none | Integration merge connector differs in identity but202 feature blobs identical,README expanded. No unique content found; parent cooldown audit owns confirmation. |
| `research/rea-boundaries-20261016` | `e95918c98962f334a68b703cc04e61edc9200be5` | not yet included | ancestor | 89 / 0 | none | Research baseline itself; all89 last-feature-delta blobs identical. Preserve until integration branch is merged and verified; contains latest REA/verifier deliverables. |

## Integration and conflict decisions

The outgoing-request, offline VGNL importer and dictionary connector commits differ in SHA but match stable patch IDs and implementation/test blobs. Cooldown/PR27 branches contain no unique unpreserved evidence. Reviewed research entries and source identities remain retained.

The sole missing branch was `fix/h5672-spawn-skin-identity-20261014`: five commits and ten absent files. It was merged, preserving `recording_identity` imports/fields in the same modules. A skin mismatch remains separately visible; an actor-definition mismatch still blocks actor identity. It does not make recordings definitive or certify rendered skin.

The only textual merge conflict was the current `native_roster.py` SHA in `event_semantics_2026-10-04.json`; it was recomputed from the combined module. The skin branch extends the old roster report. Both dictionary and atlas now reference a byte-identical frozen main roster report, preserving the original SHA rather than changing historical proof. Generated dictionary index was rebuilt.

Canonical regression hashes were not refreshed: each intended skin addition/reason is explicitly asserted then projected out for the old main comparison. Safe/debug output remains identical; disposable Windows paths are normalized before JSON escaping, including tuple children. New symlink-only tests skip only actual EACCES/EPERM/WinError1314; other alias checks remain active.

## Scope and cleanup

Production additions: bounded offline request parsing, provenance-preserving VGNL import, recording-scoped identity diagnostics, actor/skin separation. Research dictionary, models and native receipts remain bounded evidence; they do not enable shared-reward, buff/status, timer, ultimate or recall-success reducers. H5810 remains a development sample, including older reports titled as independent state comparisons.

All 22 non-main frozen branches are conditional cleanup candidates only after this integration is merged and the latest tips/main are rechecked. Preserve main and the integration branch while its PR is open. Patch-equivalent old connector branches need content checks even if ancestry differs. There are no pre-existing open PRs to close. No main merge, PR closure or local/remote branch deletion was performed.

External research roots are not bundled. Dictionary integrity is distinct from renewed native/server execution; see validation results before merging.

## Validation and review

[Independent code review](REVIEW.md) found no production blocker in the offline parsers/importer, identity code and combined actor/skin path. Focused review scope:115 tests, OK with2 symlink capability skips. Atlas:30 tests, OK. The original three main canonical output hashes were retained and pass after explicit validation/projection of intentional additions.

The unfiltered full Windows suite attempted1,169 tests: **2 failures,60 errors,3 skips**. This is not a full pass.57 errors are direct WinError1314 symlink fixture failures; two secondary errors unlink missing fixtures; one is C:/D: relpath; two assertion failures arise from unavailable symlink callbacks. The two assertion failures and cross-volume error reproduce unchanged on frozen main. Existing account rights were used without security-setting changes.

A second capability-limited run kept the same1,169 method slots, explicitly excluding25 classified method IDs: **1,141 non-skipped methods passed,28 skips,zero failures/errors**. Whole-method exclusions also omit portable assertions within those methods. This supports available-scope validation only. [VALIDATION.json](VALIDATION.json) lists every exclusion and original log hashes; it does not relabel blocked tests as passed. Full symlink/cross-volume validation on a capable platform remains a merge gate.

Dictionary validation:141 entries,90 repository source hashes verified,zero source failures;172 external source references unresolved. Generated index matches. The hash-gated PE verifier reproduced all three selected opcode chains. No new replay holdout, screen/native/server execution or external-root revalidation was performed.

GitHub Actions workflow query returned zero workflows. A draft PR is appropriate while full capable-platform validation remains outstanding. CI/check state is read again after PR publication; absence of CI is not test success.
