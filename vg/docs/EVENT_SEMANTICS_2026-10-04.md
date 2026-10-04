# Fixed-build event semantics atlas

Finite framing follow-up inspected eight fresh native bodies on the pinned build.
Reader `004ca130` consumes timestamp4, BE32 packet length and the complete packet;
`004eb4a0` passes that buffer and length to `004cfec0`. For recorded `03ee:222`,
`03f2:126`, `041c:22`, and `041d:14`, the dispatcher advances past opcode2 and
copies respectively216/122/15/12 bytes without a branch length-equality test.
The remaining6/4/7/2 bytes do not change the direct action input or next record
cursor. Recorder `009546f0` copies the entire packet and advances by length+8.
`0095c590` also confirms attribute stores in four layers0/b4/168/21c plus index*4.

The subsequent indirect-target inspection closes the required-field suffix gap:
`004eb2d0(1)` constructs `KindredReplay` with vtable `012179b8`; slot+3c is
`004676f0`, whose complete body returns true without state access. Static global
xrefs identify only constructor assignment and cleanup zero writes to `01ef0e80`.
The networking vtable has a different target and remains excluded. The four
variants now carry `required_field_application` scoped to this build's replay
mode; their whole-event `application` remains unknown and opaque suffix meaning
is not invented. Nine per-opcode runtime-control checks remain pending. Each variant retains
its suffix-mutation falsification experiment. No holdout was used.

The C16 native reader EOF observation at section170 offset92098 now independently
matches all70 required player fields across10 players through the public CLI.
Raw sample631, source/trace/injection hashes, original hero assets and final
buffer bytes were rechecked. The compact proof is
[`c16-final-field-match.json`](evidence/2026-10-04-atlas/c16-final-field-match.json).
Nine primary rows link this final observation without promoting unisolated event
variants, guards, intermediate states, rendered slot order or lane-only CS meaning.

The [machine-readable atlas](event_semantics_2026-10-04.json) retains every
candidate from the [original catalog](vg-binary-event-candidates-2026-09-09.json),
bound to Windows client SHA256
`659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`.
It distinguishes names, payload layouts, native application paths, and matched
runtime evidence. **It does not claim that all 161 event meanings are decoded.**
Required player-state semantics still fail the strict acceptance gate until the
specific pending observations and variant mappings are supplied.

## Recomputed scope

| Dimension | Count | What it establishes |
| --- | ---: | --- |
| Candidate union | 161 | Receiver, emitter, or observed opcode is present |
| Receiver handled | 123 | This dispatcher has a non-default branch |
| Native emitter | 111 | Fixed header and known transport edge were found |
| Observed opcode | 85 | A strict record exists in the fixed corpus |
| Recorded payload variants | 93 | Exact observed opcode/length pairs |
| Serialized payload variants | 111 | Native emitter payload lengths, kept separate |
| Multiple recorded-length families | 8 | No prefix-based collapsing |
| Corpus recordings / sections | 56 / 7,870 | Original source set, individually hashed |
| Strict framed records | 30,729,156 | Fresh recount, identical to historical count |

The fresh audit reads every original section using `iter_records`. All section
hashes match both the frozen local manifest and the historical source-provenance
manifest. Per-recording, per-opcode and per-length counts match; there is no count
drift to explain. The extra `normal17` local control is explicitly listed outside
the fixed 56-recording census. Held-out recordings retain their partition; the
audit examines only framing, opcode, length and record-location metadata. It does
not decode held-out player names, counters, inventory or gold for tuning.

The eight variant families remain:

| Opcode | Recorded payload lengths |
| --- | --- |
| `03ee` | 216, 222 |
| `03f2` | 122, 126 |
| `03f3` | 746, 750 |
| `03f8` | 9, 14 |
| `0421` | 25, 30 |
| `0422` | 24, 30 |
| `043f` | 34, 38 |
| `0470` | 1, 6 |

Native packet lengths are a separate domain. For example, grant `043d` has a
12-byte native serialized body and a 14-byte recorded body. Consume `044b` has
10 versus 14 bytes; `0471` has 5 versus 6. A universal "six-byte trailer" rule is
contradicted by these different differences. No recorded variant inherits an
application claim solely because it resembles the shorter serialized prefix.
Research-only lengths mentioned in the inventory operation table but absent from
the fixed census remain named uncertainties, not fabricated observed variants.

## Proof boundaries

The initial atlas has 10 candidates with a traced static application for at
least one listed variant, 16 with partial layout evidence, 97 with class linkage
only, and 38 whose operation meaning remains unknown. These are candidate-level
counts; `applied_static` does not mean every variant of that candidate is proven.
Most traced inventory variants are native serialized bodies whose recorded
counterparts still need matched receiver/application evidence. No row currently
claims full independent six-field accuracy.

Native inventory effects are linked to the existing
[operation evidence](evidence/2026-10-04-inventory/operations.json), original
receiver branches and native apply exports. Resource arithmetic links to the
[Windows gold path](evidence/2026-10-03-gold-time/native-paths.txt). Roster offsets
link to the receiver and the [roster trace](NATIVE_ROSTER_2026-10-04.md).
The [Windows counter read paths](evidence/2026-10-04-counters/manifest.json)
independently bind computed attributes41/42 to `myKills`/`myDeaths` and resource11
to `myAssists`. Resource14 has a verified numeric scoreboard rendering path; its
visible label and lane/jungle counting definition still need controlled capture.
The inventory's practice grant observation corroborates distinct instance
allocation, but it is not silently promoted into proof of a recorded payload
variant or a complete replay baseline.

For secondary controls, direct inspection of the receiver and available leaf
exports establishes narrower structural facts:

| Opcode | Verified structure / consumer boundary | Still unknown |
| --- | --- | --- |
| `03ed` | Receiver copies 72 bytes, converts leading text through `0096d310`, endian-swaps fields at +64/+68, and uses +68 for entry lookup / `0095e8f0`. | Text's actual destination and gameplay purpose; not labeled player name. |
| `045c` | 16 six-byte entries: BE32 reference, gate byte, boolean byte. Gate != 0 calls `0095e850`; that leaf searches entry ID at +4 with stride `0xb8` and updates entry +`0xb4` bit 0. | Meaning of the bit and controlled UI/gameplay effect. |
| `0471` | BE32 reference + boolean; `0095e940` updates entry +`0xb4` bit 8 after the same lookup. | Meaning of that separate bit; no invented connection state. |
| `0470` | First byte normalizes to bool for `004bfdc0`; a separate call to `00548bf0` checks state/mode and then ORs object +`0x19d` with 4. | Gameplay label and dynamic ordering. The bit is not assigned from the incoming boolean. |
| `047c` | Same one-byte bool forwarding path, without the `00548bf0` call shown in `0470`. | Unobserved in this corpus; no pause label or runtime claim. |
| `03e8` | Native emitter `00814bc0` copies 64 bytes; recorded body is 70. | Field meanings and direction. |
| `0458` / `046d` / `046e` | Emitters `004ce5f0` / `004ce2f0` / `004ce1f0` copy one byte; recorded bodies are six bytes. | Action names, payload semantics, accepted/rejected outcomes. |

Those leaf exports were read and hashed into the private task-8 control review
receipt. The atlas's public assertions remain bounded to the linked portable
receiver/emitter evidence; no private raw binary or recording is published.

End-match/postgame classes and callbacks retain their narrower source meaning.
`03f1` is an action queue request with distinct reason handling; `048d` carries
accumulated analytics structures and is not a direct final K/D/A or final-duration
packet. `0452` callback presence does not prove all final-state updates have
finished. See the [native endgame paths](evidence/2026-09-08-endgame/native-static-analysis.md).

## Review ledger and remaining work

Every candidate has a review row with the actual inspected native path(s),
source hashes, native-copy lengths, unresolved statement, next inspection target,
and a falsifiable next observation. Candidates sharing native apply targets are
grouped by `implementation_group`. The 123 portable receiver snippets were read
and checked against their body hashes; fixed-header emitter and class-link
records were checked against the source catalog. This is a bounded static review,
not a claim that each class's full implementation was reverse engineered.

The ledger separately records unavailable matched passive observations and
unresolved controlled triggers. Absence of a corpus event does not prove it is
unused, reserved, or server-only. Class names do not determine payload fields,
network direction, or actual mutation. For a secondary unknown, the next native
consumer target and isolated before/after falsifier remain explicit. Required
field application claims need native proof plus independent matched observations;
the bounded review alone cannot replace them. C16 now supplies the scoped final
field observation, while per-opcode controlled coverage remains a separate ledger.

The native source files and field statuses change only with new evidence. To
incorporate a new observation, identify its opcode and exact domain/length, link
its hashed source, and update only the demonstrated claim. A runtime trace that
matches one variant does not authorize promotion of other lengths or other
recordings. Preserve uncertainty about trigger, direction, guard behavior,
slot order and seek semantics until independently addressed.

## Validator and audit commands

From the repository root using the configured Python 3.14:

```sh
python3.14 -B -m unittest tests.test_event_semantics_atlas -v
python3.14 -B -m vg.tools.event_semantics_atlas validate \
  --atlas vg/docs/event_semantics_2026-10-04.json \
  --source vg/docs/vg-binary-event-candidates-2026-09-09.json \
  --output /path/to/task-5-atlas.json
python3.14 -B -m vg.tools.event_semantics_atlas audit-corpus \
  --manifest /path/to/reference/manifest.json \
  --atlas vg/docs/event_semantics_2026-10-04.json \
  --output /path/to/task-8-atlas-corpus.json
python3.14 -B -m vg.tools.event_semantics_atlas validate \
  --atlas vg/docs/event_semantics_2026-10-04.json --require-reviewed \
  --require-per-opcode-runtime-controls --output /path/to/task-8-controls.json
```

Base validation and bounded-review validation pass. The last command currently
**exits 1** because nine per-opcode control checks remain pending. The legacy
`--require-player-state-semantics` alias preserves that exact strict behavior;
it is not the acceptance command for a scoped six-field snapshot. Neither flag
may be reported as a passing controlled-event audit. Unknown required-field
application still fails this audit, and field proof cannot promote whole-event
semantics. See [Task8 scope and acceptance](TASK8_ACCEPTANCE_SCOPE_2026-10-04.md)
for the independent exact-reference acceptance command.

The validator recomputes all summary counts and rejects candidate/variant loss,
source-hash drift, orphaned references, native-path/dimension drift, out-of-bounds
fields, class-only payload claims, receiver-only application claims, unsupported
runtime promotion, runtime evidence without the exact opcode/domain/length
association, and removal of a required player-state gate. Exit 0 means the
requested validation passed; 1 reports failed claims/corpus reconciliation; 2
reports input/schema/integrity/publication errors. Output uses the shared writer
and cannot overwrite consumed inputs. No LSP server was available or installed.

## Scoped C33 runtime observations

The C33 inventory trace has 18 independently rechecked record/native matches:
seven baseline observations (one 750-byte initial empty constructor and six
746-byte existing-actor calls), eight 14-byte grants and three 14-byte consumes.
Only these four recorded opcode/length variants carry `runtime_matched`.
Payload bytes, section offsets, source hashes, actor/component ownership and
before/after inventory arrays were compared directly with the raw native trace.
The match source is hashed in the atlas. This does not establish atomic six-field
clock alignment, existing-actor baseline reinitialization, seek behavior, or
all sale/upgrade cases. All nine primary reader gates remain pending; unused events retain separate unknowns.

## Remaining required gates after native follow-up

A fresh read-only Ghidra export of nine narrowly selected functions is preserved
with hashes in [the follow-up manifest](evidence/2026-10-04-atlas/manifest.json).
Existing roster exports and clock instructions were independently inspected and
linked. Exact receiver-size static application is now recorded for `03ee/216`,
`03f2/122`, and `046f/69`. This closes three static variant issues, while all
18 runtime items remained pending under the original broader event policy. The initial 32 issues classify as
two missing evidence links, twelve native variant/handoff questions, and eighteen
new matched-runtime requirements; the static-only pass left29 issues. The reader-scope audit below narrows the product acceptance gate without resolving optional event semantics.

| Remaining recorded variant | Native proof now linked | Missing evidence |
| --- | --- | --- |
| `03ee/222` | Copy216 → `004d52a0`, roster insertion/update | Exact222-byte record→receiver buffer association; name/hero/table snapshot at matched boundary |
| `03f2/126` | Copy122 → `0081a750` → `0094d480` | Exact126-byte handoff and absent/existing actor observation |
| `041c/22` | Copy15 → `0081b910` → `0094f1d0`; SET/ADD helper paths | Exact22-byte handoff; final `0095c590` layer store; K/D layer and rendered label alignment |
| `041d/14` | Copy12 → `0094f210`; resource ADD/SET | Exact14-byte handoff; float32 resources6/7/11/14 and CS label/control alignment |
| `0438/6` | Serializer `008180c0`; separately traced client reorder code | Actual recorded direction/consumer and slot transition; no receiver branch is established |
| `0448/6` | Serializer `00813dc0` / sender `0095bda0` | Mode3 activation direction/consumer and outcome |
| `0449/14` | Serializer `00813fc0` / sender `0095bea0` | Direction/consumer; request versus resulting consumption |
| `044a/22` | Serializer `00813ec0` / sender `0095bdd0` | Direction/consumer; request versus resulting consumption |
| `044c/22` | Copy21 → mode constructors → `0094ee90` | Exact22-byte handoff and downstream ability effects; direct apply contains no pointer/quantity store, which is not a transitive no-op proof |
| `044d/14` | Copy8 → `0081c200` → `009504f0` | Exact14-byte handoff; server-mode guard and separate consume/gold outcome |
| `048f/6` | Copy1 → `00529e00` callback notification | Exact6-byte handoff and registered `method_onRejectBuyItem` callback effects |

The seven receiver-prefix cases retain `application.status=unknown` on their
longer recorded variants. Their `native_prefix_application` records the exact
copy length, scoped native effect and opaque-tail status; it explicitly does
not certify the entire variant. The validator rejects altered copy lengths or
promotion of that prefix proof into a verified whole variant. Tail differences
are respectively6,4,7,2,1,6,5 bytes, with no universal trailer rule.

Every primary row's `player_state_gate.reason` names its concrete next
observation. Supported `0444` is quantity SET, not reorder; its low16-bit store
needs framed before/after observation. Native `0437` quick-buy and `0439` buy
paths require nonzero server mode and are secondary request research. The matched C33 grant,
consume and baseline observations still need broader guard/seek checks and an
independently aligned six-field snapshot. Static clock storage at manager+0x194
does not make the asynchronous record-clock diagnostic an atomic boundary.


## Primary six-field gate versus optional event research

The current production readers consume nine primary opcodes:
`03ee`, `03f2`, `03f3`, `041c`, `041d`, `043d`, `0444`, `044b`, and `046f`.
The atlas pins hashes of `native_roster.py`, `native_stats.py`, `native_gold.py`,
`native_inventory.py`, and `native_query.py`; validation rejects policy source
drift so future reader changes require this audit to be refreshed.

The strict per-opcode research audit currently has **nine pending control checks**.
These are not nine missing experiments for the scoped C16 recorded-EOF workflow:
native static application proof plus independently matched fields establish that
observed reconstruction, with C33 providing additional inventory transitions.
0444 is unobserved in the56-recording corpus and its live control is extension
coverage. The four
used recorded suffix gaps (`03ee/222`, `03f2/126`, `041c/22`, `041d/14`) have
required-field-only static proof from the replay constructor and indirect target.
The observed workflow uses an independently matched native record boundary and
all six requested field categories. It does not claim lane-only CS or rendered
item slot order. Counter, gold and inventory readers distinguish created actors from known
baselines, ignore repeated same-actor spawns, and withhold state after040b until
cleanup can be established. Ambiguous GameTime selection that would skip an
earlier record but include a later one fails closed; recorded-EOF and RecordTime
remain ordered traversals. Extending paused/seek time mapping requires an aligned
native snapshot, not another copy of every event hook.

Nine formerly required candidates are optional secondary research because the
current readers do not consume them: `0437`, `0438`, `0439`, `0448`, `0449`,
`044a`, `044c`, `044d`, `048f`. Their native layout/application unknowns remain
unchanged and visible. Static client-side exclusions are narrow: `0437`, `0439`
and `044d` require nonzero mode to execute their request callbacks. `0438` has a
separate client serialization path that reorders entries, so unused does not
mean no-op. `044c` and `048f` can dispatch further callbacks; their transitive
inventory effects remain unknown. Those open semantic questions do not require
the entire atlas to be decoded before assessing the supported six-field reader.
