# Local validation environment and proof boundaries

## Starting basis and fresh receipt

Audit basis: commit `010c67c`, 2026-10-16. Native effect validation was not performed; no live-client or GUI execution result is claimed. Host-specific execution metadata is omitted from this public report.

The native WTSINFOEX layout has the level at byte 0 and aligned level-1 prefix at byte 8; session state and flags are at bytes 12 and 16. On supported modern Windows versions, flag 0 reports locked; flag 1 reports unlocked. Connection state `WTSActive` alone does not establish an unlocked desktop. Read-object access from `OpenInputDesktop` is also not proof that a desktop is unlocked.

## Existing harnesses and their scope

| Existing path | Available offline check | Requirement or limitation |
| --- | --- | --- |
| `vg/tools/player_state_capture/evidence.py`, CLI `verify`, `import`, `challenge`, `align`, `export-reference` | Validate existing receipt hashes, process identity recorded in artifacts, screenshot/action references, cleanup and supported boundary proofs; negative challenges modify a copied in-memory manifest | Artifact consistency is not independent proof that arbitrary synthetic input came from a client. Unaligned samples remain observation-only. Reference export additionally requires restoration and alignment evidence. |
| `vg/tools/player_state_capture/runner.py`, `guards.py` | Pure guard tests and inspection of frozen script identities | Native capture requires a fresh active/unlocked session, exact owned live PID/create time/path/hash, frozen worker ownership, scripts and dependencies. It cannot run against an absent client. No capture/restore commands were run. |
| `vg/tools/clock_probe/windows_read_clocks.py`, `WINDOWS_README.md` | Inspect the observer and historical clock receipts | ReadProcessMemory observer requires an existing process, exact original executable SHA `659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`, loaded-module identity and entry guards. It is not automatically compatible with the selected LAA executable `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`. It samples clocks, not new defense effects. |
| `vg/docs/WINDOWS_CLOCK_RUNTIME_2026-09-08.md` | Review historical clock/practice replay observations and failed scene attempts | Historical success does not establish a current process, current scene, UI pause behavior, or the new effect edges. |
| `vg/tools/clock_probe/clock_probe.py` and its Android documentation | Inspect older ARM64 hook design | Different platform/build; launching an owned process and instrumentation are outside this audit. No attempt was made. |
| `vg/research/stat_stacking_model.py`, `cooldown_item_declarations.py`, `passive_item_catalog.py`, `verify_sequential_pe.py` | Bounded algebraic witnesses, hash-pinned declarations and PE assertions against existing files | These check declared inputs/static instruction assertions, not authoritative accepted combat or live duration. The stat model is not bit-exact engine emulation. |
| `tests/test_research_buff_lifecycle.py` | Synthetic dispatch/countdown/expiry decisions under explicit preconditions | Caller eligibility, resource factory dispatch, script results, time units and native object lifetimes are external preconditions. |

The frozen runner expects six script hashes, including `session_state.py` SHA `477b8308af4a82bcbb92fee1677034fb4fc919dcad87c9166ee25bb953d8a2d0`. Dependency availability was not established by this audit.

## Next check and result

The smallest offline checks exercise truth boundaries rather than manufacture new combat observations. New `tests/test_research_validation_environment.py` checks that an active-but-locked WTS response fails the existing gate, an unlocked synthetic session cannot substitute for an absent owned process, and a hash-valid synthetic capture remains observation-only and cannot export reference truth without cleanup evidence. The last fixture has no alignment proof either; the observed export rejection is specifically `capture_invalid` / `cleanup_missing`, before the later alignment gate. No manifest or reference output is published by that rejection.

Executed with `PYTHONUTF8=1`:

```text
python -m unittest tests.test_research_validation_environment tests.test_research_buff_lifecycle tests.test_stat_stacking_model tests.test_cooldown_item_declarations
Ran 24 tests — OK
```

Three tests are new environment/evidence boundary cases; the other 21 exercise existing synthetic lifecycle, stat and cooldown models. These passing checks are neither a live-client result nor a full-suite result.

An offline replay may validate parser behavior and recorded accepted fields when those fields have established semantics and source/boundary provenance. It cannot independently identify an unrecorded activation/rejection, infer an unknown consumer from HP alone, or turn a constructed event sequence into engine evidence. In-memory witnesses can expose inconsistent proposed formulas or orderings; they cannot select among observationally equivalent armor/shred/pierce orders or prove a defense callback actually executed.

## Closed reason and remaining blocker

Environment feasibility is established for read-only local assets, receipt verification and bounded synthetic checks. Native effect observation was not performed. No present GUI/game execution result is claimed. Existing capture probes also need an explicit reviewed observation plan for the new cap/defense fields and their accepted-action boundaries; merely making the game available would not close those semantic edges.

For a later authorized capable session, the independent review should check executable and loaded-module identities, ownership, mode/target/source-instance guards, loaded properties, accepted-action timestamps and before/after resource fields against the actual effect graph. Keep native observations, replay boundary proofs and synthetic predictions separately identified. Until that evidence exists, the new defense/cap conclusions remain bounded by the static exports and the missing actual consumer/runtime observations. No production decoder change follows from this audit.
