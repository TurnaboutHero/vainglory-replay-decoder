# Live boots cooldown verification

This follow-up supersedes the current-status portion of the historical
[r1 foreground refusal](COOLDOWN_RUNTIME_GUARD_2026-10-14.md). The user directly
resumed Windows verification. Code baseline is `489c721`; the separate cooldown
parser branch `311232a1` was not merged. This increment publishes bounded runtime
evidence and changes no decoder behavior.

The owned LAA process passed executable SHA-256 verification and all five stock
observer byte guards. Fresh checks found an unlocked Default desktop and no
existing game, QA worker, or scheduled task. Normal window activation initially
failed; a title-bar click was sent only after WindowFromPoint/root ownership and
HTCAPTION checks identified the owned game. The actual game screenshot then
passed the foreground guard. No unrelated process was terminated. A later
standard window restore exposed the whole HUD below the taskbar.

Two practice matches were operated through the normal UI. The first ended at
20:20 before the remaining trials; the second supplied the sale/rebuy and tier
comparison. Actor pointer equality across these matches does not prove actor
lifetime continuity. Comparisons below are within their respective match.

## Observed results

| Trial | Result | Native observation and separate screen evidence |
| --- | --- | --- |
| Same definition, distinct instances | SUPPORTED | Definition 477 instances 2003 and 2004, quantity 1 each, had different item/ability pointers but the same actor-owned primary state and key. Using one changed shared charges from 1 to 0 and both HUD buttons showed 150. |
| Sell all, then rebuy | SUPPORTED | Definition 477 instance 2003 was used and sold. A sample established no 477 item remained. New instance 2004 had a different ability pointer but the same primary state, timer pointer/generation and charges 0; its HUD showed 75. |
| Different tiers | SUPPORTED for 477 versus 478 | Travel Boots instance 2005 and Sprint Boots instance 2006 had distinct primary keys/states. Using Travel changed only its charges to 0 while Sprint remained 1. Sprint was then actually used; both were 0 with different timer pointers. HUD showed Travel 90 before the second use and Travel 85/Sprint 150 afterward. |

Observed primary keys were `0x8c2eef5b` for definition 477 and `0x592b3a5f` for
definition 478. These are observations for this fixed build and the exercised
definitions, not mappings inferred for all boots. Secondary state pointers were
null in the observed boots. Primary owners matched the selected actor, state
class was 17, and the state was present in the actor's child list.

The [bounded receipt](evidence/2026-10-14-cooldown-live/summary.json) includes
selected boots fields, source/screenshot hashes, all three dispositions and
cleanup counts. Private screenshots, raw discovery samples, generated replay
files, backups and binaries remain outside this repository.

## Limits

Eleven short passive observer sessions detached successfully. Each sample checked
actor identity, inventory and child membership before and after reading. This
does not make the sample atomic or establish the full native pool handle and
lifetime. Timer generation equality is a limited comparison, not full handle
validation.

The collector's 35 offline Node-VM/syntax checks passed again against byte-identical
stock probe source. Receipt export asserted distinct instances, shared states,
complete inventory absence before rebuy, tier-specific charge transitions and
cleanup invariants. The initial smoke invocation rejected its historical HEAD
pin; the runtime baseline pin was refreshed while retaining exact stock source
comparison to `3361131`. Product parser tests were not rerun for this docs-only
increment.

The prepared collector called the timer field at offset `0x24` remaining time,
but it read zero while the HUD displayed positive countdowns. That semantic
label is contradicted by this run. The public receipt retains the field only as
raw bits with unverified semantics. Pause byte 0 and matching generations do not
resolve that discrepancy. Exact remaining seconds and replay apply/queue/tick
alignment remain unverified; no event-time subtraction or reducer is promoted.

This validates three practice actions, not replay-frame synchronization or every
activation opcode/mode, boot tier, hero, game version or replay end-state field.
The earlier 56-recording offline extraction claim retains its own scope.

## Teardown

The original 661 files were backed up before launch with content hashes and exact
creation/write FILETIMEs. After stopping the owned game and worker, 470 modified
or missing originals were restored and all 661 names, contents and timestamps
matched. The 61 new session files were moved to a private archive. All four owned
scheduled tasks were removed after checking their exact actions. Final checks
found no game, QA worker or task, no pending command, and unchanged original/LAA
executable hashes. Cleanup finished at 14:56:59 UTC on October 14 (23:56:59 KST).

The old cleanup utility contains an `observer_started=false` placeholder; it
does not describe this run. Observer evidence is the eleven explicit detach
receipts and absence of any live observer worker, recorded separately.
