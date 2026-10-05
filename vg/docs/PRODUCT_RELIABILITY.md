# Offline replay workflows and reliability

This guide covers inspecting one recording, capturing a scoreboard moment, exporting datasets and spreadsheets, maintaining a catalog, archiving files and contributing research. All examples run from the repository root. Choose a Python interpreter meeting the runtime requirements below and use that same interpreter throughout.

The single-recording CLI now defaults to `state-json` (`decoder_v2.player_state.v3`) for native player state. The examples below explicitly select `safe-json` where they exercise the earlier conservative v2 contract. Python `decode_match(...)`, batch and index contracts retain their meanings; use `decode_player_state(...)` for the new API. See the [main usage guide](../../README.md#start-here) for field semantics and migration.

## Offline quickstart

The maintained smoke test creates its own synthetic replay and truth data, runs the examples and checks that source bytes remain unchanged:

```sh
python -X utf8 -B -m unittest discover -s tests -p "test_product_quickstart.py" -v
```

To inspect the generated artifacts yourself, create a **new or empty** disposable directory. The fixture generator refuses to overwrite a nonempty directory. The fixture is not a playable match or an independent validation dataset. Its screenshot/observation pair is synthetic and exercises the comparison contract only.

<!-- offline-commands:start -->
```sh
python -B -m tests.test_product_quickstart --make-fixture ".quickstart"
python -B -m vg.decoder_v2.decode_match ".quickstart/replays/demo.0.vgr" --format safe-json -o ".quickstart/reports/safe.json"
python -B -m vg.decoder_v2.decode_match ".quickstart/replays/demo.0.vgr" --format safe-json --at-game-time 105 -o ".quickstart/reports/capture.json"
python -B -m vg.decoder_v2.decode_match ".quickstart/replays/demo.0.vgr" --format debug-json -o ".quickstart/reports/debug.json"
python -B -m vg.decoder_v2.batch_decode ".quickstart/replays" -o ".quickstart/reports/batch.json"
python -B -m vg.decoder_v2.index_export ".quickstart/replays" -o ".quickstart/reports/index.json"
```
<!-- offline-commands:end -->

`safe.json` uses `decoder_v2.match.v2`. Its final K/D/A, minion kills, gold, winner and exact duration remain withheld. A numerical duration candidate may appear inside a withheld decision; check `accepted_for_index`, not just whether a number exists.

`capture.json` uses `decoder_v2.capture.v2` with `scope="capture"`, the requested `at_game_time`, observed `as_of_game_time`, content `replay_scope` and roster identities. The synthetic fixture has a supported capture at 105 seconds. Its captured K/D/A is observable, but those counters are not approved for the final-match index. Debug output retains research candidates and does not widen acceptance.

### Metadata, truth, spreadsheets and statistics

<!-- offline-commands:start -->
```sh
python -B -m vg.core.vgr_parser ".quickstart/replays/demo.0.vgr" --no-auto-truth -o ".quickstart/reports/metadata.json"
python -B -m vg.core.unified_decoder ".quickstart/replays/demo.0.vgr" --truth ".quickstart/truth.json" -o ".quickstart/reports/legacy.json"
python -B -m vg.core.export_matches ".quickstart/replays/demo.0.vgr" -o ".quickstart/reports/result.csv"
python -B -m vg.core.export_matches ".quickstart/replays" --batch --csv-only -o ".quickstart/reports/csv-batch"
python -B -m vg.analysis.batch_report ".quickstart/replays" --truth ".quickstart/truth.json" -o ".quickstart/reports/statistics.json"
python -B -m vg.tools.replay_batch_parser ".quickstart/replays" -o ".quickstart/reports/parsed-batch.json"
```
<!-- offline-commands:end -->

Explicit truth must be a supported JSON/Markdown document with a matching, unambiguous row. JSON supports a single match or list/keyed `matches`; player rows and `match_info` are mappings. Consumed numeric statistics must be finite, nonnegative numbers rather than booleans. Relative replay references resolve against the truth document. Foreign-OS path metadata stays lexical; a research command that actually decodes those files needs accessible local references.

The legacy parser can automatically look for local truth candidates. Use `--no-auto-truth` for binary-only metadata or `--truth` for an explicit document; retained truth provenance identifies the selected source. An explicit bad document does not silently fall back to binary-only results.

`-o result.csv` creates distinct `result.csv` and `result.json`; `-o result.json` creates the same pair. A suffixless filename also produces both suffixes. An existing directory retains the legacy replay-derived basename. `--csv-only` preserves an explicit CSV destination and writes a receipt without match JSON files. Other ambiguous suffixes are rejected.

CSV is UTF-8 with BOM. Text that could begin a spreadsheet formula receives an apostrophe only in CSV; JSON keeps the original text. Numeric negatives remain numbers. Null statistics become blank CSV cells, while known zero is `0`. `duration_status`, `duration_source`, native/final status fields and sample counts preserve evidence scope. Batch `match_idx` is the discovered ordinal and may have gaps after failures; `input_id` is the relative POSIX frame-zero path and is identical across player, summary and JSON artifacts.

Batch statistics report `roster_known_samples` / `roster_total_samples` and `observed_player_samples`. If any selected match has no roster, total players, total kills, the global kill/gold averages and hero pick rates remain null; the terminal displays N/A. Observed per-hero samples remain visible. An explicitly empty dataset has zero selected matches and players, while its averages remain unavailable. Known zero counters in available rosters remain zero.

### Catalog, snapshots and a disposable replay slot

<!-- offline-commands:start -->
```sh
python -B -m vg.core.vgr_database init --db ".quickstart/catalog.sqlite"
python -B -m vg.core.vgr_database import --db ".quickstart/catalog.sqlite" -i ".quickstart/replays/demo.0.vgr"
python -B -m vg.core.vgr_database export --db ".quickstart/catalog.sqlite" -o ".quickstart/reports/catalog.json"
python -B -m vg.core.vgr_watcher ".quickstart/backups" --temp ".quickstart/replays" --once
python -B -m vg.core.vgr_loader list ".quickstart/replays"
python -B -m vg.core.vgr_loader status --temp ".quickstart/slot" --target-name slot
python -B -m vg.core.vgr_loader load ".quickstart/replays" --name demo --temp ".quickstart/slot" --target-name slot
```
<!-- offline-commands:end -->

These commands use only the fixture's disposable `slot` directory. They do not start or connect to the game. Use explicit source and target names when a directory has several families. Analysis can retain missing-section gaps as evidence, but slot loading requires contiguous numbered sections, disjoint source/target families and verified staging. Success proves copied filesystem bytes, not playback.

Watcher snapshots cover whole section contents and the associated manifest. Changed or newly appended sections produce a new verified snapshot. `--once` reports each family as `success`, `unchanged`, `pending` or `error`; pending/error returns 1 and later scans retry. A stable snapshot does not imply that the recording or match has ended. Continuous watching uses the same scan behavior, with `--interval` in seconds.

If a loader operation reports `recovery_required`, retain its operation directory and original backups. After the owning process has stopped, pass the returned `recovery` path:

```sh
python -B -m vg.core.vgr_loader recover "PATH_FROM_RECOVERY_FIELD"
```

Recovery checks ownership and hashes before restoring the previous slot. It refuses unknown changed bytes, a live owner, or an untrusted journal. A failed operation rolls back only the report bytes it published itself. If the report was edited, created, deleted-and-relinked or aliased by another program meanwhile, those bytes are preserved and the operation ends in `recovery_required` with "Report changed outside transaction"; move the other file aside, then run recovery to restore the previous report. The quickstart failure scenario exercises this command on a generated interrupted operation. Do not remove a recovery lock or guess an operation path to bypass that check.

Catalog initialization inserts missing built-in entries while preserving existing IDs and custom metadata. Import uses content/section `replay_scope`: the same bytes at a new path are a duplicate, the same display name with different bytes is distinct, and a growing recording is a new snapshot. Legacy rows without a content scope are not silently rekeyed; a colliding name reports `legacy_identity_unknown`. Existing foreign-key violations are reported and block further imports without automatic repair. Unknown historical zeros are not reinterpreted.

`catalog.json` explicitly has `coverage="catalog_only"`: it includes `heroes` and `items`, and excludes `skins`, `matches` and `match_players`. It is not a full database backup. New unavailable match/player statistics are SQL NULL. Raw hero identifiers and namespaces are preserved separately from the resolved catalog foreign key. Export refuses to overwrite the database or its live sidecars.

### Research and a scoped screen comparison

<!-- offline-commands:start -->
```sh
python -B -m vg.decoder_v2.truth_inventory --base ".quickstart/replays" --truth ".quickstart/truth.json" -o ".quickstart/reports/inventory.json"
python -B -m vg.decoder_v2.validation --truth ".quickstart/truth.json" --base ".quickstart/replays" -o ".quickstart/reports/validation.json"
python -B -m vg.decoder_v2.completeness_audit --base ".quickstart/replays" -o ".quickstart/reports/completeness.json"
python -B -m vg.analysis.final_screen_comparison ".quickstart/replays/demo.0.vgr" --observation ".quickstart/observation.json" --screenshot ".quickstart/synthetic-screen.png" -o ".quickstart/reports/comparison.json"
```
<!-- offline-commands:end -->

The [v2 capability matrix](decoder_v2/README.md#command-capability-matrix) lists all 40 supported command modules and their actual input kinds. Supply your own root/truth paths instead of relying on historical machine-local defaults. Foundation validation's `--base` is optional and controls additional inventory only; its truth-linked replays are still required for decoding.

The synthetic comparison can match its four K/D/A/CS fields. `compared_field_names` and `observation_only_fields` define that result: gold, winner, duration and result text remain observations, and `accepted_for_index` remains false. The command hashes the screenshot file and uses caller-asserted transcription; it does not authenticate the image or perform OCR. Real validation needs independently observed, correctly transcribed evidence.

## Python APIs

The same APIs work with your own explicit frame-zero path. This executable example uses the generated fixture:

<!-- offline-api:start -->
```python
from pathlib import Path
from vg.decoder_v2.decode_match import decode_match
from vg.decoder_v2.batch_decode import decode_replay_batch
from vg.core.unified_decoder import UnifiedDecoder
from vg.analysis.batch_report import decode_all_report

base = Path(".quickstart")
replay = base / "replays" / "demo.0.vgr"
capture = decode_match(str(replay), at_game_time=105).to_dict()
assert capture["scope"] == "capture"
assert capture["accepted_fields"]["kills"]["accepted_for_index"] is False
batch = decode_replay_batch(str(base / "replays"))
assert batch["discovered"] == batch["succeeded"] + batch["failed"]
legacy = UnifiedDecoder(str(replay)).decode_with_truth(str(base / "truth.json"))
assert legacy.duration_provenance["status"] == "supplied_truth"
statistics = decode_all_report(str(base / "replays"))
assert statistics["status"] == "complete"
print(capture["schema_version"], batch["status"], legacy.duration_seconds)
```
<!-- offline-api:end -->

Legacy list APIs `decode_batch`, `decode_all` and `scan_replay_folders` return lists on complete/empty input. A per-input failure raises `PartialBatchError` carrying `.report`; use `decode_batch_report`, `decode_all_report` or `scan_replay_report` when partial results are expected. `decode_batch_report` publishes its export set before returning. Pure decode/report builders return data without writing files.

## Status, selection and publication

| Outcome | CLI exit | Observable result |
| --- | ---: | --- |
| Complete run or intentionally empty existing batch root | 0 | `complete` or `empty`; every discovered input accounted for |
| One or more per-input batch failures | 1 | `partial` or `failed`; ordered input results and counts are retained |
| Invalid configuration/root/input selection, output alias or publication failure | 2 | Actionable path/reason; no success report for the failed publication |
| Well-formed capture with unavailable native evidence | 0 | Null statistics plus the specific withholding reason; command success is not field acceptance |

The batch invariant is `discovered == succeeded + failed`. Missing roots are errors; existing empty roots are explicit empty datasets. Single-family commands reject multiple families, nonexistent paths and arbitrary files. Discovery excludes AppleDouble and `__MACOSX` metadata, preserves separate nested names and loads numeric sibling sections in numeric order. Replay content identity and relative path identity serve different purposes.

Final-screen comparison separately returns 0 for matched compared counters, 1 for mismatch/unavailable and 2 for invalid input/publication. Watcher `--once` uses its snapshot states described above. Database and loader commands return 2 for operation errors. SQLite directory import is sequential: an earlier successful import can remain committed if a later input fails.

All supported report commands protect their actually consumed replay, truth, OCR, manifest, correction, screenshot or database inputs. Direct, symbolic and hard-link aliases, output-output collisions and future replay sibling names are rejected. Inputs and destinations are rechecked before replacing reports. Single-file publication stages and flushes content before replacement, preserving the prior report on handled failures. Parent-directory permissions still need to permit writing.

Multi-file CSV/JSON export is **recoverable publication**, not one atomic transaction for arbitrary readers. Check `export_receipt.json` for a batch, or `<csv-filename>.receipt.json` for a single export. A transaction `status="complete"` means its `current_outputs` and hashes were published; `batch.status` separately records complete/partial/failed/empty decoding. Files in `stale_outputs` belong to older generations and remain on disk. Consumers must use the receipt's current list, not glob every `match_*.json`.

If a replace and its rollback both fail, the receipt stays pending and blocks a new generation. Preserve backups and use the explicit recovery API after resolving the reported filesystem problem:

```python
from pathlib import Path
from vg.core.replay_output import recover_report_set
recover_report_set(Path("PATH_TO_PENDING_RECEIPT"))
```

Recovery validates owned backups and restores the preceding generation. It does not delete unrelated output files. Collision checks defend against accidental aliases and handled IO failures; they are not an adversarial concurrent filesystem security boundary.

## Troubleshooting examples

The fixture also contains two valid families under `ambiguous`, one valid and one corrupt family under `mixed`, and an existing `empty` root. The following commands intentionally demonstrate the documented outcomes:

<!-- offline-errors:start -->
```sh
python -B -m vg.decoder_v2.decode_match ".quickstart/missing.0.vgr"
python -B -m vg.decoder_v2.decode_match ".quickstart/ambiguous"
python -B -m vg.decoder_v2.batch_decode ".quickstart/mixed" -o ".quickstart/reports/partial.json"
python -B -m vg.decoder_v2.batch_decode ".quickstart/empty" -o ".quickstart/reports/empty.json"
python -B -m vg.decoder_v2.decode_match ".quickstart/replays/demo.0.vgr" --at-game-time 10000 -o ".quickstart/reports/unavailable.json"
```
<!-- offline-errors:end -->

In order, expect exits **2, 2, 1, 0, 0**. The missing/ambiguous cases have an actionable error. The mixed batch has two results, one success and one failure. The empty root has zero discovered inputs. The out-of-coverage capture has null K/D/A and a specific reason, not zero counters. For clock/baseline/identity failures, preserve the reason and recording scope; do not infer a replacement zero or a final score.

## Runtime and verification

| Capability | Runtime/dependencies | Verification scope |
| --- | --- | --- |
| Offline core, 40 v2 command imports/help, JSON/CSV, SQLite, filesystem snapshots/load/recovery | Python >=3.12; standard library | Generated fixture tests and full suite; no live game required |
| Windows screenshot capture | Interactive Windows desktop and Pillow, imported only when capturing | Platform-specific; core imports/help do not require Pillow |
| Native clock/gold probes | Windows game process plus separately specified observer environment; clock probe pins Frida 17.17.0 | Bounded runtime observations; no general client compatibility promise |
| `vgrplay_inject` external injector | Explicit external `vgrplay` executable and suitable target slot | Filesystem verification is separate from actual game playback |

Python 3.12 is the syntax floor. The full suite was executed on **macOS 26.7 arm64 with Python 3.14.7** (`Clang 22.1.3`) and **native Windows 11, build 10.0.22631, with Python 3.13.2** (64-bit). Both runs tested commit `9c28d88fd549de8c52c537b6f940046b889bbc0e`; each passed all 625 tests with exit 0. This records those runtimes and that source revision, not unexecuted Python versions. Optional instrumentation packages are not prerequisites for offline smoke tests.

| Verification | Command/evidence | Current recorded scope |
| --- | --- | --- |
| Pre-change macOS baseline | `python -X utf8 -B -m unittest discover -s tests -q`; pre-change baseline recorded in the approved reliability work plan | Historical baseline: 499 tests, two path failures and two private-fixture/Pillow errors; exit 1 |
| Offline quickstart | `python -B -m unittest discover -s tests -p 'test_product_quickstart.py' -v` | macOS Python 3.14.7: six maintained tests passed; 40 module help/option checks, executable examples and two recovery paths. Evidence: `.omo/evidence/task-19-vg-product-journey-20261003-{happy,failure}.log` and `.omo/evidence/product-quickstart/` |
| Verified macOS suite | `python -X utf8 -B -m unittest discover -s tests -q`; `.omo/evidence/F3-attempt-2/F3-macos-suite.log` | Commit above: 625 tests passed in 12.158s; exit 0 |
| Verified isolated Windows suite | Same command and commit; `.omo/evidence/F3-attempt-2/F3-windows-suite.log`, `.omo/evidence/F3-attempt-2/F3-windows-receipt.json` | 625 tests passed in 61.130s; exit 0. Receipt confirms tested source and protected checkouts remained unchanged |
| Static type checking | basedpyright | Not installed in the implementation environment; no type-check PASS claimed and no installation performed |

Final acceptance must account for all original 499 tests plus maintained additions, with no silent removal of coverage. Local task evidence is retained under `.omo/evidence/`; ignored evidence is not distributed as a promise to new checkout users. The smoke command is the reproducible entry point. Actual game playback, private corpus observations and source-bound software regression tests remain separate evidence.
