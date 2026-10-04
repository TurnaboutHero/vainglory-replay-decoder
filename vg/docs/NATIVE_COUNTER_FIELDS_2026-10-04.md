# Native counters and gold query boundary

`native_stats` and `native_gold` now use `native_query.select_native_query`.
They validate the full recording before selecting records. `GameTime(t)` and
`RecordTime(t)` are inclusive, reject nonfinite/out-of-coverage inputs, and
preserve the existing per-section 046f game-clock mapping. EOF applies every
record, including records projected beyond an earlier paused section endpoint.
EOF and `GameTime(last_game_time)` therefore need not select the same state.
If a game-time cutoff would omit an earlier record but include a later record
after a paused clock anchor, it returns `ambiguous_game_time` with no state.
Every supported query selects a contiguous record prefix; EOF and explicit
RecordTime remain available when a GameTime mapping is ambiguous. Roster uses
the same query audit as counters, gold and inventory.

`record_boundary` identifies the actual last selected `(section, offset)`;
`applied_game_time` is its mapped game time. Legacy `as_of_game_time` keeps the
requested-time contract. This distinction is deliberate: callers requiring an
actual applied boundary must use `record_boundary`. A time cutoff ignores
semantic errors after the selection but never ignores corrupt future framing.
Gold retains float32 baseline, float32 ADD, and nonzero-mode SET semantics.
Unknown values are never replaced by rounded display text.

Forward game-clock jumps alone do not change native dispatch order. EOF and
RecordTime can therefore pass the complete structural/record-order audit while
the GameTime mapping is unavailable. In that case `ClockAudit` reports
`record_order_only`, `game_time_mapping_valid=false`, and no first, last,
requested, as-of or applied game time is fabricated. The public service retains
the exact record boundary and explains the missing mapping in `support_reason`.
Explicit GameTime queries remain unsupported; backward resets such as C41
still reject every query. These rules do not interpret a forward jump as proof
of dropped records.

Actor creation is separate from successful baseline reconstruction.
`0094e170` first calls `00857970` for the actor ID and immediately returns for
an existing actor; its baseline writes are bypassed. Consequently repeated
03f3 records cannot overwrite live counters/resources or repair an unknown
state. An earlier 03f2 or 03f3 without explicit baseline still establishes actor
existence. A 040b removal request does not prove the later pool cleanup and
identity reuse boundary, so requested actors remain unsupported afterward.
The exact guard is retained in
[function-0094e170.c](evidence/2026-10-04-inventory/function-0094e170.c).

## Independently traced Windows memory paths

The source executable SHA256 is
`659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`.
Fresh bounded Ghidra exports and their hashes are in
[evidence/2026-10-04-counters/manifest.json](evidence/2026-10-04-counters/manifest.json).
These are static provenance, not runtime agreement evidence.

| Field | Independent native read path |
| --- | --- |
| Kills | `004c13b0` emits `myKills` from actor+0x20 component attribute41. Four layers are at component+0xc4/+0x178/+0x22c/+0x2e0. `006f7a80` reads the same formula for scoreboard K. |
| Deaths | Same paths emit `myDeaths` from attribute42, offsets +0xc8/+0x17c/+0x230/+0x2e4. |
| Assists | `004c13b0` emits `myAssists` from component+0x31c, resource11. Scoreboard `006f7a80` reads the same field. |
| Scoreboard CS (`minion_kills`) | `006f6fd0` copies component+0x328 to row+0xe4; `006f7a80` converts this value and calls `00740890`, which stores it at widget+0x75b0 and invokes rendering `0073e2f0`. The integer formatting branch reads +0x75b0 and renders the creep-icon scoreboard value. The observed C33 board shows CS0 alongside KDA0/0/0 and gold30.0k. This field means displayed CS, not an independently established lane-minion-only count. Controlled lane/jungle contribution remains unproved. |
| Net worth | `004c13b0` reads component+0x30c, resource7, alongside the KDA report. Its float32 bits, and resource6 at component+0x308, are captured directly by the observer. Existing gold receiver/apply proof remains authoritative for balance/worth semantics. |

The native attribute formula is `((layer3 + 1) * layer1 + layer0) *
(layer2 + 1)`, clamped to native per-attribute bounds. The reader supports its
proven base-layer events and fails closed on unsupported layers; no arbitrary
layer is accepted merely because its index names kills/deaths.

The public `minion_kills` name is retained for compatibility and is explicitly
defined as the client's scoreboard CS. Native resource14 and its display path
can be supported without inventing a taxonomy of which creatures contribute.
Nonzero same-boundary native/display comparisons remain an independent accuracy
gate; the C33 zero observation alone does not establish those counts.

## Passive capture

`vg/tools/player_state_capture/player_state_probe.js` exports `start(options)`,
`sample()`, and `stop()`. The launcher must independently verify the executable
hash and pass it as `verified_executable_sha256`. The observer accepts the
original and documented LAA executable hashes and checks five native function
entries with relocation-aware byte guards. It performs no native function calls,
memory writes, or function interception.

Actor lookup `00857970` calls pool enumerator `0112ac50`. The observer reproduces
only its memory reads, including active-index bounds and exclusion bitset, then
joins actual actor+0x178 IDs to the native player table at `020e7404/020e7408`.
It emits original attribute layers, float32 resource bits, roster identity and
native inventory array entries. Display name is the row+8 UTF16 vector: setter
`0095e8f0` passes row+8 to `004b53d0`; instruction inspection establishes vector
length/capacity/data offsets +0/+4/+8.

Samples are asynchronous. `atomic_record_boundary` is explicitly false;
`record_clock_unverified` is diagnostic only because this global can be stale
during replay. A successful sample is not an independently matched recording
boundary. Version 2 also reads the actual native replay object before and after
the player reads: its buffered record bytes/time, applied flag, pause mode,
section, file-open state and slot name. Fresh native sources establish that
`004eb4a0` dispatches buffered content through `004cfec0`, then sets object+0x14
to 1; `004ca130` advances section only after the current file's timestamp read
reaches EOF. The exhausted reader or paused final buffered record can therefore be independently
matched to original framed bytes. Root-owned captures must establish that link
before the strict comparator can certify all six fields. Runtime receipts and
their exact source boundaries are maintained separately from this static proof.
