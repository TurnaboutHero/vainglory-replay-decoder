# 8. Reward snapshot serializer extension

## Starting basis

The individual-resource path in RESOURCE_RECEIVER_FOLLOWUP_2026-10-16.md and
02_REWARDS.md establishes one actor/resource/operand update for 041d, without a
verified award cause or recipient vector. This extension checks the separate
snapshot producer 004ca310 and full serializer 004cbc90. It does not infer a
shared award from equal values, retained attackers, or temporal coincidence.

Selected artifact: Windows x86 LAA executable SHA256
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.
Existing archived htons-references.json instead identifies executable
`659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`;
its first-90-instruction serializer excerpt was insufficient for a full-body
check and is not silently upgraded to the selected artifact.

## Next check performed

Read the existing full 004ca310 assembly and fresh full 004cbc90 pseudocode and
assembly. Follow the caller's one-actor inputs, serializer argument reads,
array loops, conditional component-field copy, and final opcode/payload copy.
No new Ghidra query, native execution, replay recount, or production code change
was performed by this reviewer. Unknown fields remain unnamed.

## Result

004ca310 receives one actor pointer in its stack argument, retains it in EBX,
and reads actor ID at EBX+178 into EDI at004ca5e1. Calls004ca3aa/3ba/3ca/3da/3ea
invoke00939330/00939470/00939520/00939240/009391e0 with the same actor and count10,
filling five caller arrays. Direct reads004ca374/004ca384 copy actor component
[EBX+20]+300/+304. Other same-actor getters assemble position/state and
component/inventory inputs. These roles do not by themselves label every array
or scalar. Call004ca6ec sends the assembled arguments to004cbc90. The alternate
branch004ca90d calls004cb6a0 and is outside this full-serializer extension.

The full004cbc90 body consumes caller scalars/pointers and byte-swaps selected
words and float bit patterns. When its byte argument at stack+30 is zero, it
copies a fixed selection of fields from the supplied component pointer; it does
not calculate a shared award. Assembly004cd164..004cd184 copies three supplied
eight-byte blocks.004cd1a0..004cd22c copies five parallel arrays using the
supplied count at stack+50;004cd251..004cd2c9 copies another caller-supplied
array group/count, and004cd2e0..004cd319 copies a third. These loops serialize
arrays inside one actor snapshot; no recipient-set semantics are established.
Array element meanings are not expanded here.

004cd31b selects opcode03f3;004cd344..004cd357 copies exactly0x2ea payload bytes;
004cd362..004cd368 submits opcode plus payload,0x2ec bytes, to004cb590. This
matches the selected746-byte snapshot payload shape. The reviewed serializer
contains conversion, copying and packaging rather than an explicit award
producer, cause selection, recipient eligibility loop or allocation formula.
No field in the reviewed caller/serializer slice is positively identified as
an award cause/group or recipient set. Opaque caller fields are not therefore
proven to be award metadata, and are not proven incapable of carrying additional
meaning elsewhere. No all-network absence claim follows.

## Closed reason and remaining falsification

Closed for this bounded static question: acquiring the complete selected-build
serializer removes the old truncated-body limitation, but does not expose a
verified reward-cause/group/recipient-set bridge. Per-target snapshot values
remain compatible with many different upstream award histories.041d and03f3
remain distinct input paths, neither newly promoted to authoritative payout
causation by this inspection.

A full semantic absence proof remains blocked by unnamed caller/component
fields, untraced getter implementations, other serializers/callers, and missing
authoritative reward production. No broad schema expansion is needed to retain
this boundary. If a concrete candidate field appears, next targeted bodies are
00939330,00939470,00939520,00939240 and009391e0 for the five arrays, followed only
by the implicated source field. A matched-build trace binding explicit award
cause/group and recipients through producer, enqueue, serializer and balances
would falsify the current unverified-causation conclusion. Historical source
build and server behavior remain separate questions.

## Acquisition anchors

Raw exports stay in private-evidence; these SHA256 values identify the exact
review inputs rather than copying raw decompiler output into the repository.

| Input | SHA256 | Evidence ID |
| --- | --- | --- |
|017-procedure_assembly-0x004ca310.json|93900bd2d9cd323408e077c89e4f306c86c473b74f710b8eba14cc2f0592bb91|See common prior acquisition receipt|
|031-procedure_pseudo_code-0x004cbc90.json|54d6f02d14cd0598c351af0bf1c3fa5d37500f5521dc593efc010c5eb0302496|ev_7b2b00cb656b895cc61b7eb6c4c718b9f5621a15967778b86ba34475640c27c0|
|042-procedure_assembly-0x004cbc90.json|64a0f3a5cd1bc6dba86b5279566656d6da6333d8991aff3ec6f1fbab9e6fcdda|ev_04e29fcbb97b68ae06a1a2c1bc021b833c37d972590410c161c7d1ddee146abd|
