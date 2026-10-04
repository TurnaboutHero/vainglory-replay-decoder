# Recorded player-state accuracy, 2026-10-04

The ordinary decoder now reconstructs player identity, hero, K/D/A, held items,
spendable gold, native net worth and displayed CS from framed native records.
Eight independently observed recordings, containing 37 players, matched every
required field through the default CLI, Python API and legacy CLI: **777/777
comparisons, zero mismatches or missing required fields**. These are 259 field
groups repeated through three public surfaces, not 777 independent observations.

This is evidence for the pinned client build and the observed record boundaries.
It does not establish universal replay compatibility or certify match-final
scores. The [machine-readable summary](evidence/2026-10-04-accuracy/summary.json)
records the comparison counts, source digests and private evidence hashes.

## Use the result

Run from the repository root with Python 3.10 or newer:

```sh
python3 -m vg.decoder_v2.decode_match /path/to/match.0.vgr
python3 -m vg.decoder_v2.decode_match /path/to/match.0.vgr --at-game-time 900
python3 -m vg.decoder_v2.decode_match /path/to/match.0.vgr --at-record-time 894.6184692382812
python3 -m vg.decoder_v2.decode_match /path/to/match.0.vgr --format safe-json
```

The default is `state-json`, schema `decoder_v2.player_state.v3`, at
`scope=recorded_end`. A supported time query applies a common ordered record
prefix to every field. Ambiguous paused, backward or otherwise incompatible time
selection is rejected; EOF applies the actual recording order. `--format
safe-json` preserves the previous v2 final/capture output. Python callers use
`vg.decoder_v2.decode_player_state`; the existing `decode_match` API retains its
older contract.

`--at-record-time` selects seconds in the recorded replay stream and requires
`state-json`. It is mutually exclusive with `--at-game-time`; Python callers use
`at_record_time`. GameTime is a projection from recorded clock anchors. A native
game clock between anchors can differ because the original client advances it
with runtime ticks. Exact native comparisons must therefore verify the selected
section and record offset independently, as described in the
[midpoint follow-up](PLAYER_STATE_MIDPOINT_2026-10-04.md).

Check `support_status`, per-field provenance, `replay_scope`, and the section and
record offset. Names are associated with recording-scoped 32-bit native actor
IDs. Distinct actors with the same name remain distinct. Unproved hero/team
associations remain unavailable. Known zero is numeric zero; an unobserved value
is null.

`items` preserves HUD-visible held instances and their quantities. `native_items`
also retains hidden system items. Native item 515 resolves to Level Juice through
the original definition asset. Physical collection order is not a claim about
rendered HUD slot order. JSON is the authoritative inventory projection; CSV
retains IDs, counts, names and gold but does not represent every stack quantity.

`gold_balance` is native resource 6; `net_worth` is resource 7. Both reproduce
float32 state, including ADD/SET behavior. They are not an inferred `gold_earned`
total. Cached, rounded scoreboard labels can lag the raw native value.
`minion_kills` is the client's displayed CS counter, resource 14; this does not
claim a lane-only count or separately classify jungle kills.

## Independent comparisons

| Recording | Role | Players | EOF section:offset | Matched groups per surface |
| --- | --- | ---: | --- | ---: |
| C16 | 5v5 development/control | 10 | 170:92098 | 70/70 |
| C48 | 3v3 holdout | 6 | 128:42500 | 42/42 |
| C50 | 3v3 holdout | 6 | 134:32569 | 42/42 |
| C51 | 3v3 replacement holdout | 6 | 138:62789 | 42/42 |
| C52 | 3v3 development regression | 6 | 116:55834 | 42/42 |
| C33 | Inventory control | 1 | 6:44185 | 7/7 |
| normal17 | Practice control | 1 | 16:58543 | 7/7 |
| C34 | Death control | 1 | 4:23281 | 7/7 |
| **Total** | **8 recordings** | **37** | | **259/259** |

Seven comparison groups cover six requested categories: name, hero, KDA, items,
gold balance, net worth and CS. KDA is one group; the two gold values are separate.
Every row passed the default CLI, direct `decode_player_state` API and the legacy
CLI's outer player fields. The final three holdouts contain 18 players and 126
groups per surface, or 378 comparisons across all surfaces.

References were acquired from the running original game, passive native state,
rendered screens and original hero/item definition assets. Source section hashes,
native replay-reader buffer positions and EOF boundaries were checked. Reference
manifests and their source hashes were frozen before each first comparison.
Expected values did not come from a decoder output. Float32 gold bits must match
exactly; rounded display text is supporting evidence only.

C48, C50 and C52 were initially reserved. C52 exposed a forward clock mapping
problem and was reclassified as development evidence after the fix. C51 was
selected as its replacement before capture and first comparison. Its first
legacy check exposed a comparator projection defect: it inspected the embedded
native result instead of the outer legacy fields. The comparator was corrected,
two regressions were added, and all three surfaces were compared again. No C51
numeric extraction rule was tuned. Earlier failed reports remain preserved.

Private full comparison reports are under
`.omo/evidence/accuracy-20261004/final-public-surfaces-v2/`. Each contains exact
expected/actual fields, recording identity, provenance and missing/mismatch
details. Raw recordings, client binaries, screenshots and large native traces
are retained outside version control. The committed compact summary is an index
of that evidence, not a substitute for the private inputs needed to reproduce it.

## Inventory and failure controls

The original C33 replay matched 18 observed inventory operations. A new recording
made with the actual client matched eight operations and all 16 before/after
states: duplicate Weapon Blades, selling one copy, buying a replacement,
upgrading that replacement while keeping the spare, and consuming an infusion.
An additional backward-seek trace matched 11 operations. These are inventory
component observations aligned by action and record, not full seven-group
snapshots at every intermediate action.

Removing one of the two independently observed Weapon Blades makes the item
comparison fail. Flipping one gold bit in C16 makes the full comparison exit 1
with 69/70 groups matched. These controls distinguish correct output from
plausible wrong output without changing production data or the frozen truth.

The implementation also fixes repeated spawn/snapshot handling. Native actor
creation can ignore a later spawn for an existing actor; the readers preserve
the first effective lifetime instead of resetting its values. A roster naming
a conflicting ignored hero is no longer certified as supported. Tests exercise
that disagreement, unknown baselines, duplicate names, unsupported variants,
nullable exports, unknown teams and ambiguous clock queries.

## Corpus and event coverage

The separate structural audit covers all 56 original recordings, 7,870 sections
and 30,729,156 framed records: 85 observed opcodes and 93 recorded length variants.
Public state coverage is complete for 55 recordings and 504 players. C41 is
explicitly rejected for backward mixed clock segments. **This 55/56 output
coverage is not independent accuracy certification.**

All 109 historical tournament player rows and 60 historical item-count rows are
inventoried without altering their values. They overlap the corpus and lack the
complete same-boundary labels needed here; they do not increase the eight-recording
accuracy denominator.

The [event atlas](EVENT_SEMANTICS_2026-10-04.md) covers all 161 fixed-build
candidates: 38 unknown, 12 layout-only, 97 class-linked and 14 with at least one
application claim. The last category does not mean every behavior or variant of
those events is understood. Required field prefixes and native application paths
are documented separately from opaque suffixes and remaining whole-event meaning.

The bounded atlas validation and full framing audit pass. The stricter
`--require-per-opcode-runtime-controls` research gate still fails nine checks;
its old `--require-player-state-semantics` spelling remains an exact alias. That
gate requires more controlled trigger/variant experiments than the independently
observed EOF comparisons establish. In particular, 0444 has no occurrences in
the 56-recording corpus. See the exact [acceptance scope](TASK8_ACCEPTANCE_SCOPE_2026-10-04.md).

## Validation and restoration

The initial EOF implementation passed **832 tests on macOS/Python 3.14.7** and **832
tests on Windows/Python 3.13.2**, with no errors, failures or skipped tests.
Both hosts used identical hashes for the 607 Python/core-definition source files.
The Windows bundle's 1,055 files also matched the exported snapshot and remained
unchanged during its run. All 605 Python files compiled successfully in memory.
LSP diagnostics were unavailable because the Python language server was not
installed; no LSP success is claimed.

Review findings about null inventory export, unknown-team win statistics,
nullable hero rendering, repeated native lifetimes and legacy comparison fields
were corrected and verified. The initial audit was performed by the root executor
when reviewer account limits prevented another independent pass. The subsequent
independent gate approved commit `d4faf76d267f3d5643f23b9afe5cc147f006116b` for
the documented EOF scope, independently rechecking 113 focused tests and 154/154
fresh comparison groups. Midpoint support and its additional verification are
reported separately in the linked follow-up. Nonblocking test-helper and
module-size maintenance observations remain outside this change.

All four owned runtime sessions ended. The final readback verified **274 original
temporary-slot files** across 12 trials, including byte hashes and timestamps.
Owned game/probe/worker processes and scheduled tasks are absent. An earlier
dual-probe attempt crashed after detach; that failed attempt is retained and later
captures used a single passive RPC probe. The original Windows checkout and
original recording/client sources were preserved. Temporary Java cache data was
moved to the macOS Trash after the read-only native analysis ended.

## Reproduce with the retained private evidence

Use a new output path; evidence tools reject unsafe overwrites. For example:

```sh
python3 -B -m vg.tools.player_state_accuracy compare \
  --manifest .omo/evidence/accuracy-20261004/reference-c16/manifest.json \
  --recording C16 --require-six-fields --surface default-cli \
  --output /tmp/c16-default-accuracy-new.json
python3 -B -m vg.tools.player_state_accuracy compare \
  --manifest .omo/evidence/accuracy-20261004/reference-c16/manifest.json \
  --recording C16 --require-six-fields --surface legacy-cli \
  --output /tmp/c16-legacy-accuracy-new.json
python3 -B -m vg.tools.event_semantics_atlas validate \
  --atlas vg/docs/event_semantics_2026-10-04.json --require-reviewed \
  --output /tmp/vg-event-atlas-new.json
python3 -X utf8 -B -m unittest discover -s tests -q
```

The native capture workflow, guards and reference import are documented in
[player-state capture](PLAYER_STATE_CAPTURE_2026-10-04.md). Private source paths
must be available for full accuracy replay. A clean checkout can run the unit
suite and inspect the committed native semantic proofs and minimal fixtures.
