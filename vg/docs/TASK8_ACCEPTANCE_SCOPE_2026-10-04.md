# Task8 scope and exact acceptance

The atlas covers all161 candidates in the original fixed-build catalog:123
receiver handlers,111 emitters and85 observed opcodes, with overlap. The original
56 recordings contain7,870 sections and30,729,156 framed records. Their93 recorded
length variants,111 serialized variants and eight families with multiple recorded
lengths are retained separately. The full framing audit passed on those original
sources; changing a static explanation does not constitute a new corpus audit.

The bounded candidate status is38 unknown,12 layout-only,97 class-linked and14
with at least one static or runtime application claim. This does not say all161
meanings are decoded. Every candidate retains inspected native paths, hashed
evidence, a remaining unknown and a falsifier. Names never establish mutation.

## Required fields and remaining unknowns

For the pinned Windows build, the six-field path has native byte-layout,
application and consumer evidence. The replay constructor/vtable proves that
extra bytes in03ee/222,03f2/126,041c/22 and041d/14 do not alter the required field
application. Their opaque whole-event meaning remains unknown. C33 adds exact
framed inventory transitions for03f3/746,03f3/750,043d/14 and044b/14; this is not
universal variant or guard coverage.

C16 provides an independent native EOF snapshot at section170 offset92098:
ten actors and70/70 exact required values. The seven comparator entries represent
six categories because gold balance and net worth are checked separately. The
raw native reader buffer, sample631, all171 original section hashes, injection
receipt, original hero assets and float32 gold bits were checked. The post-fix
public CLI comparison remained exact. See
[the compact C16 proof](evidence/2026-10-04-atlas/c16-final-field-match.json),
[C33 runtime matches](evidence/2026-10-04-inventory/c33-runtime-matches.json),
[fixed-build native source manifest](evidence/2026-10-04-atlas/manifest.json), and
[the full atlas](event_semantics_2026-10-04.json).

This proves the observed recorded-EOF field workflow. It does not prove arbitrary
versions, every opcode's controlled trigger, intermediate states, rendered item
slot order or lane-only CS. Counter, gold and inventory readers track actor
creation separately from known baseline state and preserve unknown lifetimes.
Ambiguous GameTime queries fail closed if selection would skip an earlier record
and include a later one. Supporting such a paused/seek query requires one aligned
native boundary observation, not another hook capture for every opcode.

## Acceptance commands

Run from the repository root, with a fresh output path and a frozen independent
reference manifest. The exact C16 example is:

```sh
python3.14 -B -m vg.tools.event_semantics_atlas validate \
  --atlas vg/docs/event_semantics_2026-10-04.json --require-reviewed \
  --output .omo/evidence/accuracy-20261004/task-8-final-bounded.json
python3.14 -B -m vg.tools.player_state_accuracy compare \
  --manifest .omo/evidence/accuracy-20261004/reference-c16/manifest.json \
  --recording C16 --require-six-fields \
  --output .omo/evidence/accuracy-20261004/task-8-final-c16-exact.json
```

Both must exit0. The comparator must report `accuracy_certified: true` and match
every required value for every actor in every selected independent observation.
Missing fields, identity disagreement, unsupported state, mismatched boundaries,
quantity differences or even one float32 gold bit difference fail. There is no
percentage threshold and no permission to substitute partial historical labels
for complete truth. Repeat the exact comparison for each separately frozen
accepted recording; C16 alone does not certify the other55. Holdout acceptance
belongs to its independently captured comparison, not this atlas report.

The original56 structural audit is a separate criterion:

```sh
python3.14 -B -m vg.tools.event_semantics_atlas audit-corpus \
  --manifest .omo/evidence/accuracy-20261004/reference/manifest.json \
  --atlas vg/docs/event_semantics_2026-10-04.json \
  --output .omo/evidence/accuracy-20261004/task-8-final-framing.json
```

Its previously captured passing artifact is
`.omo/evidence/accuracy-20261004/task-8-atlas-corpus.json`. It establishes framing,
source hashes and census agreement, not semantic accuracy of every event.

## Preserved strict research command

```sh
python3.14 -B -m vg.tools.event_semantics_atlas validate \
  --atlas vg/docs/event_semantics_2026-10-04.json --require-reviewed \
  --require-per-opcode-runtime-controls \
  --output .omo/evidence/accuracy-20261004/task-8-final-controls.json
```

This currently exits1 with one pending primary-opcode control check,03ee. Eight
gates have bounded fixed-build runtime controls; see
[the opcode control report](OPCODE_CONTROLS_2026-10-04.md). The remaining03ee
condition is literal rendered hero-name text at an independently matched native
boundary. Native216/222 identity and skin comparisons alone do not meet it. The old
`--require-player-state-semantics` spelling is an exact alias, covered by a CLI
regression test. Neither its implementation nor its required proof was weakened.
These checks describe more controlled per-opcode coverage than the observed
six-field EOF workflow requires. In particular0444 has zero observed records in
the56 corpus: the new synthetic modify-stack controls establish native consumer
behavior, while natural emission remains unproved. This adds extension coverage
and does not replace C16 evidence.

The justified Task8 refinement is to require all161 bounded reviews, all56 strict
framing results and exact independent six-field agreement for each accepted
recording, while retaining unresolved event challenges as explicit research
unknowns. Requiring every optional challenge before accepting an already matched
field workflow would expand the original accuracy claim. This document does not
edit the root plan or claim the strict research command passed.
