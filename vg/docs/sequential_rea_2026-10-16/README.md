# Sequential REA/Ghidra follow-up

Base: `832ed978922184e83b0b1397243836774d785977` (merged PR29).
Branch: `research/sequential-rea-20261016`.
Selected artifact: Windows x86 LAA client SHA256
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.

## Method and scope

Investigate in order: (1) cooldown/ultimate availability, (2) rewards and recipients,
(3) terminal results and team/crystal identity, (4) revival/recall, (5) named buff/item stacks.
A candidate closes with fresh evidence or an explicit missing implementation/runtime
boundary, not with a longer function list. No live native/game/server execution,
packet transmission, binary modification, access bypass or software installation.

File/command access works despite the reported locked desktop. No GUI unlock is used.
Existing worktrees are preserved. Process names were inspected (no Java initially);
CIM command-line inspection required a read-only escalation and then succeeded;
this is not a guarantee that every other analysis session is known.
One fresh REA MCP session uses installed REA 6.4.0, Ghidra 12.1.4 and JDK21.
Ghidra writes only a new ephemeral project, serialized by this session. Raw exports,
projects and original client remain outside the repository. Function addresses are
preferred-image VAs in the selected hash, not historical-replay build certification.

## Evidence levels

- Raw: recorded operands and original float bits.
- Static confirmed: exact-build branches, field roles and call ordering.
- Conditional model: explicitly bounded tests; not native execution.
- Unresolved: runtime success, historical layout/build match, authoritative server causation.

H5810 is previously used development evidence, never an independent holdout.
No public push, PR or merge is authorized for these new files.

## Results and review

1. [Cooldown](01_COOLDOWN.md): timer re-arm and callback-to-three-button notification
   are connected; raw048a input roles are added without a readiness reducer.
2. [Rewards](02_REWARDS.md): retained damage source, resource mutation and client
   stubs narrow the boundary; authoritative recipient selection remains unknown.
3. [Results/teams](03_RESULT_TEAMS.md): surrender state notification is separate
   from terminal requests;03f1 gains requested-team aliases, never a certified winner.
4. [Revival/recall](04_REVIVAL_RECALL.md): a newly found inline ActorRespawn producer
   closes a conditional nonzero-mode expiry path. Ordinary receive mode and
   spawn-point initialization remain separate; recall execution stays stubbed.
5. [Named stacks](05_NAMED_STACKS.md): Bonesaw/Dragon's Eye named behavior, queued
   stack application and attribute delta connect to separate buff-definition caps5/15.
   These are exact selected-build declarations and code paths, not observed state.

[REA_RECEIPT.json](REA_RECEIPT.json) records acquisition parameters, evidence IDs
and private-export hashes; errors/interior resolutions are not counted as new
functions. [PE_CHECK.json](PE_CHECK.json) and [ITEM_DECLARATIONS.json](ITEM_DECLARATIONS.json)
were independently reproduced with the two hash-gated utilities under vg/research.
They require the selected local artifacts, which are excluded from Git.
[VALIDATION.json](VALIDATION.json) records the exact test scope, blocked method IDs
and log hashes. Unfiltered:1173 tests,2 failures,59 errors,3 skips from Windows
symlink privilege/secondary effects. Explicitly scoped rerun:1146 passed,27 skips,
zero failures/errors. Final focused16 passed. This is not a full Windows pass.
Dictionary:90 local hashes verified,172 external unresolved,0 failures,index matches.
Independent static/code reviews found no blockers. A new Linux run is still needed.

Minimal decoder changes preserve compatibility and raw bits. No runtime state,
reward rule, winner, ultimate eligibility or historical buff layout is inferred.
No fresh replay/screen validation occurred; H5810 remains development evidence.
Raw REA/Ghidra exports, original resources, executable and test logs remain private.
The ephemeral Ghidra session was closed after extraction.

## Reproduction

Run from repository root (Python3.12+ and Node18+):

```sh
python -X utf8 -B -m unittest discover -s tests -q
python -X utf8 -B -m unittest tests.test_cooldown_event_timeline tests.test_end_match_timeline tests.test_sequential_pe -q
python -X utf8 -B -m vg.research.dictionary validate --check-index
python -X utf8 -B -m vg.research.verify_sequential_pe --binary <selected-local-executable>
python -X utf8 -B -m vg.research.inspect_stack_items --binary <selected-local-executable> --data-root <selected-local-Data>
```

Public deliverables are this directory, vg/research/verify_sequential_pe.py,
vg/research/inspect_stack_items.py, tests/test_sequential_pe.py, and the small
native_event_fields/cooldown/end-match test additions. No binaries or recordings.

## Extended follow-up after326582d

[Independent parent verification](INDEPENDENT_326582d.md) applies to326582d only.
The subsequent docs-only extension follows [candidate outcomes](EXTENDED_CANDIDATES.json):
[time/ultimate](06_TIME_ULTIMATE_EXTENSION.md),
[respawn/terminal](07_RESPAWN_TERMINAL_EXTENSION.md),
[reward snapshot](08_REWARD_SNAPSHOT_EXTENSION.md),and
[stack/combat](09_STACK_COMBAT_EXTENSION.md).
New exact-build evidence includes0470/047c-to-publication-control with veto,
deferred scheduler cleanup,mode0 startup,regular interval debt behavior,and
ImpactHealth serialization/preparation versus application ordering.
[Selected PE checks](EXTENDED_PE_CHECK.json),[hero resource checks](EXTENDED_HERO_GRAPH.json)
and [fresh REA receipt](EXTENDED_REA_RECEIPT.json) preserve bounded reproduction inputs.
No production code or tests change in this extension;no new decoder reducer or
historical build promotion. Loaded resource identity,spawnpoint initialization,
authoritative terminal/reward/precalculation and actualscreen behavior remain open.
