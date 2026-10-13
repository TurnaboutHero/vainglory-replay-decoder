# REA item-event timeline decoding

Baseline: main `cd8390aeb2433eca6eedf2c62606503331f8f7ac`.
REA 6.4.0 with Ghidra 12.1.4 inspected the native x86 Windows executable:

```text
659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642
```

This change exposes recorded item requests and notifications in the existing
lossless timeline. The default selection now includes `044d` and `048f`.

```sh
python -B -m vg.analysis.event_timeline /path/to/match.0.vgr \
  --opcode 0x044d --opcode 0x048f -o /path/to/item-events.jsonl
```

## Decoded contract

| Opcode | Exact recorded payload / content length | Structured fields |
| --- | --- | --- |
| `044d` | 14 / 16 bytes | `native_type=item_sell_request`; BE32 actor in `ref0`; BE32 item instance in `native_item_instance_id`; `native_conditional=true`; final six bytes in `remaining_hex`. |
| `048f` | 6 / 8 bytes | `native_type=item_buy_reject_notification`; `native_callback=method_onRejectBuyItem`; first byte in `uninterpreted_bytes`; final five bytes in `remaining_hex`. |

Both rows carry `native_semantic_scope=receiver_prefix`, the reference build's
SHA-256, `native_evidence=rea-item-events.windows_2026_10_14.v1`, and the
original timestamp, section, record index/offset and complete `payload_hex`.
`decoded` describes bounded field extraction, not verification of every suffix
byte or successful application of the event. The recording's producer build is
not authenticated by the evidence hash.

The item instance is deliberately not `ref1`: entity filtering and identity
enrichment apply to actors, not held item instances. An actorless rejection is
not attributed to a nearby request and is excluded by an entity filter. Its
first byte has no established rejection-reason enumeration. The output does not
infer sale success, quantity, refund, or a rejected item ID.

Native serialized lengths `044d/8` and `048f/1` are not admitted as recorded
variants. Shorter and longer records retain their complete payload and report
`unexpected_content_length`. An inconsistent directly supplied `VGRRecord`
reports `unexpected_payload_length` before a field read. Broken record framing
retains the existing CLI error behavior.

## Native observations

REA reproduces the existing bounded receiver/application proof and adds a
trace of the registered rejection consumer:

- `004d3f89` copies eight bytes for `044d`. Constructor `0081c200` stores the
  actor at action+`14` and instance at action+`10`; apply `009504f0` checks
  nonzero `DAT_0209e204` and actor lookup before forwarding to the sell path.
- `004d4f99` copies one byte for `048f`, initializes the
  `ActionRejectBuyItem_Client` action, and queues it. Apply `00529e00` dispatches
  the registered `method_onRejectBuyItem` callbacks without passing an actor,
  item ID or reason argument.
- The callback string has observed references at `00529e02` and `005ce619`.
  The latter belongs to `005ce440`, the `KindredHUDQuickBuy` constructor, which
  registers `005ce000`. Its complete body clears owner+`20bd` bit `80` using
  `AND ... 7f`. This is one static UI consumer, not a transitive no-op proof for
  all callbacks and not an observed live UI execution.

[The bounded native receipt](evidence/2026-10-14-rea-items/native-receipt.json)
retains REA Evidence IDs, normalized-result hashes, selected machine bytes,
constructor/apply excerpts and the leaf callback assembly. The full private REA
snapshot is hashed in that receipt. Existing
[inventory paths](NATIVE_INVENTORY_2026-10-04.md) and
[event-variant atlas](EVENT_SEMANTICS_2026-10-04.md) remain authoritative for the
separate inventory reducer and unverified whole-event application gates.

## Actual replay verification

The development corpus was scanned afresh: 56 recordings, 7,870 sections and
30,729,156 strictly framed records, excluding AppleDouble metadata. The changed
timeline was then run on every recording and compared with independently read
original record locators, raw bytes and BE32 values:

| Event | Original records | Matching timeline rows | Recordings |
| --- | ---: | ---: | ---: |
| `044d/14` | 326 | 326 | 47 |
| `048f/6` | 11 | 11 | 9 |

All 7,870 source section hashes were checked before and after verification and
were unchanged. Real CLI invocations for one recording containing each event
also returned decoded JSONL with exit 0. The path-free
[verification receipt](evidence/2026-10-14-rea-items/corpus-verification.json)
contains source-hash multiset and decoded-module digests.

This verifies offline extraction and source provenance. It does not assert
runtime callback execution, all rejection causes, network direction, sale
outcomes, refund rules, other builds, or final-result correctness. No held-out
corpus was used for tuning, and no game or replay slot was modified.

Regression tests exercise exact lengths, unsigned IDs, raw byte retention,
actor-versus-item filtering, actual CLI success/truncation, and preservation of
inventory baselines/transitions until a separate `044b` consume record arrives:

```sh
python -X utf8 -B -m unittest tests.test_item_event_timeline \
  tests.test_event_timeline tests.test_native_inventory \
  tests.test_native_inventory_queries -q
```

The focused 62 tests passed on macOS Python 3.14.7 and Windows Python 3.13.
The full macOS suite passed all 911 tests with no skips. The event atlas's base
validator passed with zero issues; this does not promote its separately pending
per-opcode runtime controls.
