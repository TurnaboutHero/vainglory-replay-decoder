# REA/Ghidra follow-up on reward, revival and ability state

Baseline: `9712ab6985357bd89cd3cfc062e2068e303d3100`.
Branch: `research/rea-boundaries-20261016`.

## Access and tools

File reads and PowerShell/Python commands succeeded on KHH-Inspiron despite
the reported locked desktop. No desktop unlock or GUI operation was needed.
The current execution account is the managed sandbox account. Process-name
inspection initially found no Java/Ghidra process; CIM command-line inspection
was denied, so it was not used to claim a complete process inventory.

The original repository checkout had unrelated modifications and did not have
the requested commit. It was left intact. The explicitly requested remote was
cloned to a separate bare repository, and a separate worktree was created at
the exact baseline. All analysis here runs on Windows, with no Mac intermediary.

Existing cached REA `6.4.0` was executed directly, using existing Ghidra
`12.1.4_PUBLIC` and JDK `21.0.12.1+1`. REA creates its own temporary Ghidra
project/config/cache beneath the task's private evidence directory; no shared
Ghidra project is opened for writing. Ghidra operations are serialized in one
REA MCP session. Parallel reviewers read committed material and archived exports.
No software installation, security-setting change, live game execution, game
server request, packet injection, binary modification, public push or merge
is part of this work.

## Findings and explicit limits

1. [Resource receiver](RESOURCE_RECEIVER_FOLLOWUP_2026-10-16.md): independently
   checked `041d` receiver table, constructor call and serializer/apply/forward
   vtable slots in the LAA image. Fresh constructor, presentation flag setters,
   serializer and clone/enqueue bodies close the individual update pipeline.
   One actor/resource update remains distinct from authoritative shared-recipient
   selection and award causation.
2. [Revival and recall](RESPAWN_CALLER_FOLLOWUP_2026-10-16.md): verified
   `0432/0433` table paths and `+c` forwarding targets. Identified the precise
   missing dispatcher instruction ranges in an existing export, then extracted
   clone/enqueue/consumer bodies. Recall's selected type-4/mode-3 ability path
   reaches the 0411 request formatter and transport facade, with replay's no-send
   return separate from server acceptance. A missing caller in a partial export
   cannot establish binary unreachability.
3. [Ability/HUD](ABILITY_HUD_FOLLOWUP_2026-10-16.md): a charge-gated zero sync
   operand does not identify hidden recharge-timer state; inventory numeric
   formatting remains separate from the unclosed hero ability numeric path.
   Fresh writer/apply assembly and selected helper bodies distinguish new-state
   configuration, existing timer updates and subsequent received charge writes.
   Ultimate identity is resource/selector specific, not universally slot 2.

The separate PE verifier and [its receipt](RESPAWN_CALLER_PE_VERIFICATION_2026-10-16.json)
publish decoded addresses and hashes without distributing raw executable bytes.
[The acquisition receipt](REA_FOLLOWUP_ACQUISITION_2026-10-16.json) binds fresh
REA results by tool parameters, build identity, JSON hashes and Evidence IDs.
These are bounded research additions, not independently approved dictionary
claims or production decoder support. Generated `INDEX.ko.md` and catalog are
unchanged. H5810 remains previously used development evidence; no fresh replay
holdout or actual screen validation was performed.

## Local verification

Run from repository root, using `-X utf8` on a Windows locale whose default is
CP949. Hash-bound repository sources must retain their Git blob bytes (LF);
automatic checkout CRLF conversion otherwise invalidates source receipts.

```
python -X utf8 -B -m unittest tests.test_research_reward_models tests.test_research_respawn_recall tests.test_research_cooldown_models -q
python -X utf8 -B -m vg.research.dictionary validate --check-index
python -X utf8 -B -m vg.research.verify_respawn_pe --binary PATH_TO_SELECTED_EXE
```

18 existing bounded model/catalog tests passed. Dictionary validation checked
141 entries and 90 repository source hashes, with zero source failures; 172
external source references remain unresolved in this environment. That is
local catalog integrity, not external-source revalidation. The three selected
PE chains reproduced the committed result JSON exactly. A wrong-hash two-byte
fixture was rejected before interpretation. These are static file checks and
synthetic models, not native client or server execution.

Initial local checks exposed missing pytest, CP949 text decoding and CRLF
checkout receipt mismatches. No dependency was installed or production code
changed: existing unittest, explicit UTF-8 and exact Git source bytes resolved
the checks. Raw REA exports, generated analysis projects, binaries and test
fixtures remain outside this worktree and outside the commit.
