# Decoder v2 capability guide

Use [the offline quickstart](../PRODUCT_RELIABILITY.md#offline-quickstart) to generate a disposable fixture and run safe JSON, capture, debug, batch/index, truth and research examples. Python 3.12 is the syntax minimum; the [runtime ledger](../PRODUCT_RELIABILITY.md#runtime-and-verification) separates actual tested versions from requirements.

## Current evidence contract

`decode_match` defaults to `safe-json`. Final output is `decoder_v2.match.v2`; game-time capture is `decoder_v2.capture.v2`; debug wrappers are `decoder_v2.debug_match.v2` and `decoder_v2.debug_capture.v2`.

Validated player-block identity can support hero, team grouping and entity ID decisions. Final K/D/A, minion kills, gold, winner and exact duration remain withheld. A duration candidate may still be carried as a non-indexable estimate. `claim_status` describes evidence; `accepted_for_index` is a separate decision. Neither a completeness label nor a promising research policy authorizes final acceptance.

At a supported game time, captured K/D/A is tied to content scope, requested/observed clock and roster identity. Captured counters retain `accepted_for_index=false`. Recording/clock/identity/baseline/coverage errors preserve their specific reason; unknown values are null. Debug capture omits whole-recording winner/gold/duration candidates. Successful decoding of unavailable statistics is not successful field validation.

Batch and index outputs retain ordered results with scoped path `input_id`, `status`, `discovered`, `succeeded` and `failed`. Empty existing roots are explicit, missing roots fail, and index keeps duration's withheld decision at match level. Correction inputs are protected and do not bypass final withholding.

## Command capability matrix

There are **40 documented v2 command modules**: the three decode/batch/index entry points and 37 research/report commands. Invoke a row with `python -B -m vg.decoder_v2.MODULE --help`. All accept `-o`/`--output`; omitting output prints a report without writing one. Paths below identify consumed inputs, not merely filenames mentioned by metadata.

- **R**: one selected numbered replay family, including its read sections.
- **T**: supplied truth JSON normalized and validated for the fields the command uses. Locally referenced replay paths resolve relative to that document. Legacy parser Markdown support is separate; these research truth commands use JSON.
- **O**: OCR-derived truth JSON, not an OCR engine or raw screenshot.
- **M**: exactly associated replay manifest actually parsed; inventory-only metadata rows do not claim content decoding.
- **C**: an explicit correction JSON file or a directory whose JSON files are inspected.

For T-based analytical rows, R includes selected truth matches and any comparison baselines actually decoded. Foreign path strings can remain metadata in inventory workflows; analytical decoding requires accessible local files. Always provide your paths where historical defaults refer to a private dataset.

| Module | Supported/consumed inputs | Selection options | Result scope |
| --- | --- | --- | --- |
| `vg.decoder_v2.decode_match` | R; positional replay | `--format` `--at-game-time` | Safe final or scoped capture; debug retains candidates. |
| `vg.decoder_v2.validation` | T plus decoded referenced R; optional root inventory | `--truth` `--base` | --base adds explicit inventory; omitted means no machine-specific inventory scan. |
| `vg.decoder_v2.kda_postgame_audit` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.residual_signal_research` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_window_research` | Explicit positional R; optional matching T | `--truth` | Does not decode unrelated truth references. |
| `vg.decoder_v2.minion_window_fixture_research` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.hackedglory_minion_validation` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_outlier_compare` | T + referenced R, including decoded comparison baselines | `--truth` `--replay-name` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_hero_compare` | T + referenced R, including decoded comparison baselines | `--truth` `--replay-name` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_hero_outlier_score` | T + referenced R, including decoded comparison baselines | `--truth` `--replay-name` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_pattern_family_compare` | T + referenced R, including decoded comparison baselines | `--truth` `--replay-name` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_action_value_compare` | T + referenced R, including decoded comparison baselines | `--truth` `--replay-name` `--action` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_action_cluster_compare` | T + referenced R, including decoded comparison baselines | `--truth` `--replay-name` `--action` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.action02_value_context_profile` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.action02_sharing_profile` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.action02_hero_affinity` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.action02_subfamily_summary` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.hackedglory_xp_level_validation` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_action_provenance` | T + referenced R, including decoded comparison baselines | `--truth` `--replay-name` `--action` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_outlier_risk_report` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_acceptance_gate_research` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_policy_candidates` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_policy_cross_validation` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_policy_stability_audit` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_policy_validation` | T + referenced R, including decoded comparison baselines | `--truth` `--policy` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_series_profile` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_series_peer_compare` | T + referenced R, including decoded comparison baselines | `--truth` `--replay-name` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_series_bucket_rule_research` | T + referenced R, including decoded comparison baselines | `--truth` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_action_self_vs_team` | T + referenced R, including decoded comparison baselines | `--truth` `--replay-name` `--action` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.minion_action_relation_compare` | T + referenced R, including decoded comparison baselines | `--truth` `--replay-name` `--action` | Research candidates/fixture comparisons; no final-index promotion. |
| `vg.decoder_v2.truth_inventory` | T + root family/image/manifest inventory metadata | `--truth` `--base` | No screenshot/image or manifest-content decoding; family schema v2. |
| `vg.decoder_v2.truth_source_priority` | T + root family/image/manifest inventory metadata | `--truth` `--base` | No screenshot/image or manifest-content decoding. |
| `vg.decoder_v2.truth_labeling_queue` | T + root-selected uncovered R + associated M | `--truth` `--base` | Uncovered families stay separately identified. |
| `vg.decoder_v2.truth_capture_pack` | T + root-selected uncovered R + associated M | `--truth` `--base` `--limit` | Capture requirements follow actual accepted/withheld decisions. |
| `vg.decoder_v2.batch_decode` | R; positional recursive root | — | Per-input statuses and safe match payloads. |
| `vg.decoder_v2.completeness_audit` | R from explicit root | `--base` | All discovered families, including comparison baselines. |
| `vg.decoder_v2.completeness_outlier_compare` | R from explicit root | `--base` `--replay-name` | Selected replay plus comparison baselines. |
| `vg.decoder_v2.truth_stubs` | T + root-selected uncovered R + associated M | `--truth` `--base` | Only exact family/identifier manifest association; ambiguity is reported. |
| `vg.decoder_v2.truth_audit` | T + O; R for their matched intersection | `--truth` `--ocr` | Unmatched metadata rows do not require replay bytes. |
| `vg.decoder_v2.index_export` | R; positional recursive root; optional C | `--kda-correction-path` `--minion-policy` | Final field decisions remain conservative; experimental policy is not proof. |

All rows protect their actual inputs and output aliases before report publication. Their output is staged and replaced after a final identity check; errors preserve the prior report. See [publication and exit semantics](../PRODUCT_RELIABILITY.md#status-selection-and-publication). Metadata-only inventory does not require every referenced replay to exist, while a command that decodes a selected reference reports unreadable/missing input precisely.

## Research documents

- [Architecture](architecture.md): layers and responsibilities.
- [Protocol registry](protocol-registry.md): offsets and event catalog.
- [Claim ledger](claim-ledger.md): semantic claims and their judgments.
- [Validation matrix](validation-matrix.md): dated fixture results.
- [Open questions](open-questions.md): unresolved evidence and experiments.
- [Native integration history](../NATIVE_STATS_INTEGRATION_2026-09-07.md) and [October runtime display evidence](../RUNTIME_DISPLAY_2026-10-03.md): scoped capture/clock/gold findings.

The earlier local inventory reported 56 replay directories, 11 truth-linked directories and 19.6% directory coverage. That was a historical private-corpus snapshot, not current global coverage. Current truth inventory uses `decoder_v2.truth_inventory.v2`, counts individual replay families and retains separate directory summaries; two families in one directory do not inherit each other's truth coverage.

Final gold display can depend on retained UI formatter inputs. General end-time semantics, replay-clock history and broad corpus compatibility remain unresolved. A narrow K/D/A/CS match is not a match for gold, winner or duration.
