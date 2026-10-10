# Definitive analysis eligibility

Policy `vg.definitive-analysis.v1` is applied automatically by the default player-state API/CLI, safe JSON output, legacy match JSON/CSV exports, both v2 batch formats, index exports and the analytical batch report. Analysis completion and final-result admission are separate outcomes. An input can finish decoding with `status=complete`, preserve its observed player values and still be excluded from definitive analysis.

Each decoded output exposes `definitive_analysis` with `eligible`, `status`, `reason_codes`, `reason` and `policy_version`. CSV player and summary rows expose the corresponding `definitive_analysis_eligible`, `definitive_analysis_status`, `definitive_analysis_reason_codes` and `definitive_analysis_reason` columns. Excluded recordings do not participate in `definitive_analysis.matches` or `definitive_analysis.statistics`. Batch exclusions retain the recording path, available input ID and replay content scope so the decision can be audited. Failed decoding remains a separate batch input failure.

| Reason code | Meaning |
|---|---|
| `recording_source_unverified` | No authenticated provenance binds this recording to its producing client. |
| `recording_version_unverified` | The producing client build cannot be established. |
| `recording_version_mismatch` | Recording-client metadata identifies an incompatible/mismatched build; exclusion still applies. |
| `final_result_unverified` | No source-bound completed-result validator authorizes final match statistics. |

Current `.vgr` records contain no client build identifier. `supported_client_sha256` identifies the reference executable used to study layouts, not the executable that produced a particular recording. The current code also has no source-bound final-result admission validator. Consequently this version admits **zero recordings** to definitive analysis, including native-supported recordings whose observed values independently match the game. No new provenance input or manual override is introduced. A serialized `eligible=true`, declared `recording_client.status=verified`, legacy completeness flag, supplied truth, terminal request or successful playback cannot enable inclusion. Admission is recomputed by the shared policy when constructing a batch subset.

The existing top-level `matches`/`states`, player rows, known zero values, nullable unknown fields and observed statistics are preserved. Definitive statistics have their own denominator: if all recordings are excluded, `included_matches=0`, `matches=[]`, `statistics.match_stats.total_matches=0`, aggregate kills/duration are null and the hero table is empty. An empty admitted set does not imply every match had zero kills or zero duration.

The policy distinguishes declared mismatches from unknown builds; it does not invent an in-band version detector. A future authenticated provenance and final-result validator would require a separately reviewed admission implementation and positive acceptance tests before any recording can enter the definitive subset. Until then unknown values and exclusion reasons remain explicit.

Verification uses `tests/test_analysis_eligibility.py` and the existing full unittest suite. The new scenarios exercise unknown/missing metadata, mismatched builds, forged verified flags, supplied truth, captures, measured zero, unknown final fields, separate aggregation denominators, real subprocess JSON/CSV outputs and empty input sets. Actual H5543/H5525/H5519 recordings were also re-decoded locally: their pre-existing output fields remain identical to the frozen baseline while all three are automatically excluded from definitive analysis. This is a policy verification, not another native gameplay accuracy or version certification claim.
