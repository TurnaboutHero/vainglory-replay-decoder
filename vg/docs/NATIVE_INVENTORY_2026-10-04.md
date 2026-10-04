# Native inventory state, fixed Windows build

This research traces the original client SHA256
`659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`.
The [operation table](evidence/2026-10-04-inventory/operations.json) separates static native layouts,
observed recording variants, and runtime approval. C33 now provides an exact native baseline,
grant and consume match. The internal `read_native_inventory` reader is implemented; public
adapters are unchanged. Required multi-player/control accuracy gates remain separate.

The read-only Ghidra passes used `-process Vainglory.exe -readOnly -noanalysis`.
[Evidence hashes](evidence/2026-10-04-inventory/evidence-index.json) cover the copied native
exports, receiver branches, original-definition extraction and relocation-aware instruction guards.
The full local invocation/log files remain in the current research evidence directory.

## Representation and actual updates

Actor `+0x34` points to its item-set component: the assembly in
[index-5](evidence/2026-10-04-inventory/index-5.txt) establishes the register argument that the
decompiler omitted in `0093d080`. The live pointer array begins at component `+0x1c`, deferred
removed pointers at `+0x44`; each array has ten allocated entries. Byte `+0x70` is occupied count,
and low seven bits of byte `+0x71` are capacity; its high bit is dirty. The constructor `00958330`
clears both arrays and takes capacity from the game's configuration, rather than assuming six.
The original59 GameMode resources supply capacity6 or8. The reader selects by the046f
game-mode name and rejects unknown/changing configurations; it never assumes six rendered
slots or a universal eight native entries. [All source hashes and capacities](evidence/2026-10-04-inventory/game-mode-capacity.json)
are retained. Ordinary HF/5v5 modes have8; selected tutorial/Horde/PVE/Aral-AllBots modes have6.

Each item has definition pointer `+0x14`, definition ID `+0x2c`, instance ID `+0x30`, uint16
quantity `+0x34` and flags at `+0x38`. Equal definition IDs may have distinct instance IDs and
must not collapse. Array position is observable; this alone does not establish displayed slot order.

| Operation | Native path and effect |
|---|---|
| Grant `043d` | Receiver `004cfec0` → constructor `0081abe0` → apply `0094e070` → actor wrapper `0093d080` → component `0093cdc0`. Actor must resolve and mode byte `0209e204` must be zero. Three BE32 fields are actor, definition, instance. |
| New instance | Reject definition byte `+0x125` or native capacity rule `0086fed0`; otherwise initialize `00940230`, set uint16 quantity, insert in first null slot, increment occupied and set dirty. Grant uses quantity one. Baseline supplies its quantity. |
| Grant instance `0xffffffff` | Increment first same-definition stack whose quantity is less than definition `+0x20`. Does not allocate a new item. A full/missing stack is a no-op. |
| Consume `044b` | Actor/component lookup → `00872340`. Lookup is by instance ID. If definition `+0x1c` is nonzero, decrement nonzero uint16 quantity and retain while nonzero. Otherwise mark removed, null matching live pointer(s), decrement occupied, queue deferred pointer and set dirty. |
| Stack `0444` | `0094f6f0` looks up instance ID and stores the low 16 bits of the BE32 quantity. A quantity of zero does not remove the pointer. The native path assumes component/instance exists; malformed references are not a supported no-op. |
| Reorder `0438` | Client **serialization** path `0094c0b0` swaps both live and deferred entries, marks dirty, then emits the request. Apply `00950240` only invokes a callback in nonzero mode. Multiset is unchanged; calling all request opcodes mutation-free would be incorrect. |
| Buy / quick buy / sell | `0439` / `0437` / `044d` apply paths require nonzero mode. They do not themselves mutate this client inventory. Grant/consume outcomes must be observed; price or recipe guesses are not substitutes. |
| Activation `044c` | `0094ee90` updates ability targeting/state and invokes `onPlayAbility`; no direct quantity/pointer removal. Requests `0448` / `0449` / `044a` serialize different mode layouts. Activation is not consumption evidence. |
| Rejected buy `048f` | Calls `method_onRejectBuyItem`; no direct inventory mutation in its apply. |

`0092f980` resource side effects and the consume resource side effects are behind nonzero-mode
checks. A client inventory update therefore does not justify an invented gold adjustment.
The consume serializer writes a BE16 boolean, while the inspected receiver does not endian-swap
those final bytes before its constructor keeps one byte; extended flags retain their raw bytes.

## Spawn and seek boundaries

The 746-byte `03f3` layout routes through `004d5930` and `0081ac20` to `0094e170`.
Its BE32 actor is at payload `+8`; inventory count is at `+0x15e`, followed by ten-entry arrays
at `+0x162` (definitions), `+0x18a` (instances), and `+0x1b2` (quantities).
Payload `+0x146` controls the spawn/baseline path. Quantity arguments are narrowed to uint16.
The constructor maps these to Action arrays `+0x368`, `+0x390`, `+0x3b8` and count `+0x45c`.

An already-resolved actor causes `0094e170` to exit before these grants. A newly created actor
starts with a fresh component; when the spawn flag is zero it applies the recorded grants in
array order. Consequently repeated spawn packets are **not unconditional snapshot replacements**.
The actual C33 backward seek from section5 to2 constructs a fresh empty component (native
sequence70), then grants the five recorded baseline items (sequence91). All11 subsequent
inventory operations match the reader started at section2, including every resulting state.
[Seek proof](evidence/2026-10-04-inventory/c33-seek-runtime-matches.json) retains exact boundaries.
A client nonzero spawn flag skips this explicit baseline grant loop; it cannot be treated as an
observed complete empty inventory without the corresponding native state.

## Definition 515

Fresh extraction from the original `definitions.resource` gives index515 the serialized name
`*Item_LevelCandy*`, normalized as `Item_LevelCandy`. The manifest hash is
`7292b885378be83cb8596601bad7d0c7adfaab1e91e23f8ea65601f03136755c`;
[the exact result](evidence/2026-10-04-inventory/definition-515.json) retains build/profile identity.
This resolves the definition rather than inventing `Unknown 515` or deleting it.

The original English localization has `STORE_ITEM_LEVEL_CANDY_NAME = Level Juice` and describes
a practice-only level-up item. The original Item_LevelCandy asset SHA256
`6808f3493b90c657fd29313bf75a25f603c66b7e4a281498360fb1e8d60b71af` resolves
its+8 name-key pointer to that exact localization key. All93 original item assets provide
stackability, max-stack, grant-skip, uniqueness and localized names in
`vg/core/native_inventory_definitions.json`.

In the independently observed practice state, 515 is a held native instance2002, quantity1,
nonstackable, maximum1, with definition byte `+0x125 == 0`. That byte is a grant-skip check,
**not an established UI-visibility flag**. The first observer revision named the captured field
`hidden_or_auto_flag`; the current probe corrects it to `grant_skip_flag`. Native inventory and
rendered shop/inventory presentation need distinct evidence.

The HUD refresh005c1bb0 calls005a0790, which compares the original definition-name string
at resource+0 against `Healing Flask` and `Vision Totem`. Those two names are omitted from
the general HUD inventory. The reader preserves all native `items` and exposes `visible_items`
using that exact predicate. Definition526 has native name `Vision Totem` but localized name
`Scout Cam`; the predicate must not use localized text. Definition515 remains visible.
The HUD also separates active/passive entries, so returned array order is not claimed as UI slot order.

## Actual observations and remaining gate

All seven original C33 sections were read through `iter_records` and SHA256-checked against the
parent's frozen copy manifest. There are 42 inventory-related records: six746-byte and one750-byte
spawn, eight14-byte grants, three14-byte consumes, twelve6-byte activation requests and twelve22-byte
activation outcomes. Native serializer lengths differ: grant12, consume10, request4, activation21.
[Minimal examples](evidence/2026-10-04-inventory/c33-minimal-records.json) preserve source hash,
section, record offset and complete payload. [The native replay alignment](evidence/2026-10-04-inventory/c33-runtime-matches.json)
proves all18 baseline/grant/consume operations in order, including 746/750-byte baselines and
14-byte grant/consume records. Other observed lengths remain distinct from the native serializer.
The six parsed746-byte baselines include native actor1500 and definition515. No unsupported length
inherits the shorter variant's semantic support.

The [practice grant excerpt](evidence/2026-10-04-inventory/practice-grants.json) was independently
checked against the parent's actual passive native trace. At native times157.80320739746094 and
160.22312927246094, actor1500 receives definition458 as distinct instances2003 and2004.
The native count changes3→4→5, first-null array indices3 and4 receive the respective instance,
and every other entry remains exactly unchanged. Seven original instruction guards passed on the
owned LAA executable. This verifies actual allocation/multiplicity, but the observer attached after
initial spawn and the practice trace does not identify a replay payload variant. It does not close
the matched replay-baseline requirement by itself. The separate complete C33 trace closes that
requirement; the challenge trace additionally matches8 operations/16 before-and-after states
for duplicate purchase, selling one duplicate, rebuy, upgrade preserving a spare, and consumable use.

The [passive observer](../tools/player_state_capture/inventory_probe.js) now includes eight guarded
hooks, including component construction. It makes no native function calls and never writes game
memory. It records bounded before/after snapshots, action actor IDs, native clock bits and record
index. The parent must run it only inside the owned, executable-hash-verified capture lifecycle;
record index alone is not an exact replay record boundary. Error/limit rows invalidate completeness.

## Reproducible verification

From the repository root, with the configured Python3.14:

```sh
PYTHONDONTWRITEBYTECODE=1 "$PY" -B -m unittest tests.test_inventory_semantic_manifest -v
PYTHONDONTWRITEBYTECODE=1 "$PY" -B -m unittest tests.test_inventory_semantic_manifest.InventoryManifestTests.test_unknown_variant_cannot_inherit_semantics -v
node --check vg/tools/player_state_capture/inventory_probe.js
```

The focused suite checks immutable state, duplicate instance identity, exact-instance removal,
stack narrowing, capacity/uniqueness, unsupported input, shared clock cutoffs and a portable
minimal C33 fixture compared against all18 original native callback states. These tests are
regression evidence, separate from actual capture accuracy. The actual C33 sequence, challenge
sale/upgrade/use and C33 seek comparisons pass. Required C16 and independent control/holdout
comparisons are still pending. No full-corpus accuracy or rendered slot-order claim is made.
LSP is unavailable; no server was installed.
