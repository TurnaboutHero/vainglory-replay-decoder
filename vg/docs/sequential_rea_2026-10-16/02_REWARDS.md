# 2. Kill credit, reward recipients and resource application

Starting evidence: RESOURCE_RECEIVER_FOLLOWUP_2026-10-16.md,
progression_rewards/shared-reward-findings.json and creature-findings.json.
All selected VAs use the README artifact SHA. Prior conclusions are reused:
resource6 balance,7 LifetimeGold/positive income,8 within-level XP; same-team
condition in0094f210 is presentation only.041d names a single target, operand,
resource and mode/presentation flags; it does not establish a recipient vector.

## Fresh narrowing

Incoming REA references to0094f210 find the0127c9bc apply vtable slot;
0081b960's selected direct constructor call is004d2d6d in the receiver.
Incoming references to0093ead0 find exactly four calls from0094e970 (resources
4,5,0,1 for selected damage outputs) and0094f210. This is the analysed database's
reference inventory, not exclusion of unknown indirect, inlined or server calls.
No newly identified direct caller constructs a shared reward set.

0094e970 retains victim+1bc raw source and, for an eligible hero or generation-
checked linked hero, victim+1c0 before damage output application.009396f0 simply
returns+1c0. The interior0094eaa0 query resolves back to0094e970 and is not a
second function. This order refutes successful-damage/last-hit certainty from
the retained hero alone.0094c8f0's mode/target/00558e40-gated ActorDie path calls
00540c30 and one of00566400/0054fa00 for presentation; it does not grant gold/XP.

0093ead0 credits positive resource6 operand to component+30c, then calls store
0095f270 with existing selected resource plus operand and dispatches resource-
changed callbacks. SET0095f160 calls the store but has no positive-income increment.
0095f270 first floors finite nonpositive values to0; selected health/resource
max branches are not a shared-payout formula. No nonfinite behavior is modeled.

Fresh0045ecd0 assembly is RET4 and00528fc0 pseudocode returns immediately.
The Ambient Gold declaration's008268c0 reads __VAR1_FLOAT__ from a keyed provider;
a declaration/variable reader plus no-op execution cannot establish recipients,
range, split denominator or authoritative amount. Folded exported names at a
shared RET address do not identify gameplay behavior by name.

## Closed boundary and counterexamples

No client recipient-selection loop or death→gold/XP award producer is established.
Equal amounts/timestamps or same-team presentation can coexist with different
server recipient sets; retained eligible hero can survive later ineligible damage.
Those are counterexamples to the proposed shortcuts. No reward reducer change.

Next required experiment: on a matched build, collect separate authoritative
reward cause/group, explicit recipient IDs and amounts before enqueue, then
per-target041d apply and balances/XP. Vary killer, nearby ally, far ally, dead ally,
summoned source, objective and participation timing independently. An observed
award-group/source field or non-stub producer would reopen this boundary. A
labelled local trace without server producer still cannot certify the server rule.
No server request, fresh replay holdout or native execution was performed.
