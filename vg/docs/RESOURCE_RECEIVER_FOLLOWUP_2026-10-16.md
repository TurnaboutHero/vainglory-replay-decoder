# Individual resource receiver and provenance boundary, 2026-10-16

Baseline `9712ab6985357bd89cd3cfc062e2068e303d3100`; research branch `research/rea-boundaries-20261016`.
Preferred PE32 VAs, image base `00400000`; selected executable SHA-256
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.
This report concerns static input representation and action dispatch, not server award selection.

## Receiver table independently checked on the LAA file

The opcode subtraction index for `041d` is `041d-03ea=33` hex. The byte at
`004d51e4+33=004d5217` is `2a` hex (42 decimal), selecting the word at
`004d5000+4*2a=004d50a8`, whose value is `004d2cf4`. Do not confuse the opcode
subtraction index with the byte-selected jump index. The direct relative call
at `004d2d6d` resolves to constructor `0081b960`.

The 16-byte vtable span at `0127c9b4` independently resolves serializer `+4`
to `0094b380`, apply `+8` to `0094f210`, and forwarding `+c` to `0092e950`.
Span SHA-256: `5434c74695cc563a2be612b6c29022b203cc0c68cceb56b0c2342159c3464558`.
Reproduce with `python -X utf8 -B -m vg.research.verify_respawn_pe --binary PATH`;
the verifier refuses every other executable hash. The structured result is
[the PE verification receipt](RESPAWN_CALLER_PE_VERIFICATION_2026-10-16.json).

## What the receiver currently establishes

The committed `041d.c.txt` receiver branch copies 12 bytes, converts one actor
ID and one float operand, and constructs `0081b960(actor, resource_byte,
operand, boolean)`. Two remaining flag bytes select helper calls
`0092d2f0` and `0095ff00`; it then forwards the action through `0092c240`.
Those flags must remain distinct from an unproved award cause, source actor,
recipient vector, or shared allocation identifier. The branch neither
iterates recipients nor reads such a collection in this selected prefix.
This is a bounded branch observation, not proof that no other message or
server-side state can carry provenance.

Known apply `0094f210` resolves the one actor ID before the resource-6
presentation filter, then resolves it again before ADD/SET mutation. The
same-team condition belongs to that presentation branch. Resources 6/7/8
remain gold balance, LifetimeGold/positive-income accounting, and within-level
XP respectively. No new payout eligibility or arithmetic rule is introduced.

| Hypothesis | Selected input/output and boundary | Falsification / next evidence |
| --- | --- | --- |
| `041d` supplies one selected actor update | Receiver `004d2cf4`, ctor `0081b960`, vtable `0127c9b4`, apply `0094f210`; input actor/resource/operand/flags, output one action | Full constructor/serializer or another receiver suffix consuming a source/recipient vector would require extending this claim. Preserve exact-build prefix limits. |
| `+c` is a separate forwarding step | `0092c240` calls virtual `+c` with `020db890`; table selects `0092e950`, not apply directly | Extract complete `0092e950`, its helper and queue consumer; synchronous apply in this body would refute a deferred-only description. |
| Same-team decides only presentation in selected apply | Output of visual callback is independent of second actor lookup and ADD/SET branch | A caller selecting a recipient set upstream could establish additional rules, but cannot retroactively turn this apply's visual gate into award eligibility. |
| Resource events identify shared payout cause | Unsupported: selected receiver has no verified causal/group key | Requires authoritative producer or matched-build labelled events with explicit causal fields; proximity to a death or equal amounts is insufficient. |

## Fresh REA/Ghidra extraction

Fresh REA 6.4.0 / Ghidra 12.1.4 bodies are bound to the LAA hash above.
Constructor `0081b960` installs `0127c9b4`, writes actor/resource/operand at
`+10/+14/+18`, SET at `+1c`, and defaults presentation bytes `+1d=1,+1e=0`.
Receiver helpers `0092d2f0` and `0095ff00` respectively clear `+1d` and set
`+1e`. These are the known presentation flags, not new causation fields.

Forwarder `0092e950` allocates 0x20 bytes, copies the action header, three
words and three flag bytes, then calls `0092f720`. Assembly `0092e98d`
restores the queue argument into ECX before call `0092e9ae`. This is a
concrete clone/enqueue step, without synchronous apply in that body.
The received header byte `+c=1` is copied; queue consumer `00931bd0` tests
it at `00931c28` and calls virtual apply `+8` at `00931c40`. A zero header
instead calls serializer `+4` and applies only under `0209e204!=0`.

Serializer `0094b380` has a separate mode guard at `0209e204` and actor lookup.
For SET it compares against the selected current resource; for ADD against
zero. In the ordinary finite branch it suppresses emission when the absolute
float32 difference is below the value at `0186c080`, freshly read as `2^-23`.
No claim about NaN/infinity is made. It builds 12 payload bytes: BE actor,
byte-swapped operand bits, resource byte, SET boolean and two presentation
booleans, then calls `00816ec0`. No recipient vector, source actor or reason
is added here. This local emission guard is not a server award rule.

Fresh constructor references expose dispatcher call `004d2d6d`; cross-procedure
apply references expose vtable data slot `0127c9bc`. These are observations of
the analysed database, not exhaustive indirect-call or inlining exclusions.
The independent raw E8 scan agrees on the selected direct-call candidates,
but has a weaker instruction-boundary limitation. Raw exports stay private;
the common acquisition receipt lists their digests and Evidence IDs.

## Evidence levels and remaining experiment

New evidence is read-only PE verification and selected fresh REA extraction.
Historical receiver semantics above also use committed static exports; the
existing reference executable hash `659f9e...` remains distinct from the LAA
identity. The newly checked table/targets agree, without upgrading every
historical instruction or replay producer to a matched build.

No new replay sample, live screen validation, native game execution, packet
injection, server request, binary patch, or production reducer is involved.
H5810 remains a development sample. The decisive missing experiment is a
matched-build, labelled trace of a reward producer and its explicit recipient
and cause fields, followed through action application and observed balances.
Until then, the safe result is individual received updates and withheld
shared-award semantics.
