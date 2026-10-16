# 3. Final result, surrender and team/crystal identity

Starting evidence: dictionary result/deepening entries and
xp_structures/STRUCTURE_DESTRUCTION.md. Selected hash is in README.

## Fresh team and result links

0094d450 forwards action+10 low byte and+14 reason to004c0e10. The latter
has special dialog/return handling for reasons5/6/7 and no normal end path for8;
otherwise00549e30 gates controller handling.00549620 stores team+19c/reason+190
before guarded primary2 and secondary3 transitions. Existing deepening evidence
already proves repeated requests can overwrite these fields without a new result
callback. The fresh bodies corroborate, not supersede, that boundary.

0093c830 is exactly the actor+17c team-byte getter. Both creation apply paths
0094d480/0094e170 copy action-object+1d to actor+17c; these are not replay payload
offsets. Therefore player actors and crystal actors use the generic stored team
field; a crystal resource name alone is not its runtime team assignment.
Normal00548c90 compares controller requested team to selected actor's team for
00597c40 and analytics004c1370; alternate mode compares requested team to1.
The branch does not translate screen colors into team IDs.

Selected-actor helper00939790 is context dependent: ordinary path uses cached
roster entry or searches a valid ID with flag20 at entry+b4; replay-related path
has a different cached entry, low-nibble1 then2 fallback, and a further selection
predicate. Thus requested team relative to selected actor is not an authenticated
account's result or a universal blue/red map. Preserve roster low-nibble IDs and
unknown screen-side mapping. Home/Away crystal names, camera side and color are
not independently linked to raw team IDs by these paths. Broad color-string
search produced UI/buff/irrelevant terms and was not used as mapping evidence.

## Surrender is a separate state/notification path

Fresh005e3790 (both interior string-reference queries resolve to this one function)
consumes a surrender-state object: team byte+0, state+4, actor IDs+8, votes+48,
deadline+98 and required votes+9c. In normal mode it compares that team with the
selected actor team: state1 displays votes needed,2 passed,3 refused; opposite
team state2 displays enemy surrendered. Its alternate mode differs. Deadline
minus controller clock is floored for display. UI strings and displayed passed
are not a demonstrated authoritative terminal producer.

00951220 broadcasts onSurrenderState; its caller005496f0 selects normal actor
broadcast versus alternate UI component.004c0df0 gates that via00549e30 and is
called from00950da0. This creates a concrete state-action→notification→UI lead,
separate from0094d450→end-match. No inspected chain proves vote passed→winner.
005e3790 object layout is not promoted to a recorded message layout.

008c6e40's crystal death declaration still leads through effects/delay/MarkMyselfDead,
not a newly found end producer. Incoming references to004c0e10 find end action
0094d450 and fixed wrapper005b74c4. No new crystal-to-terminal causal edge.
This is bounded database evidence; missing server/indirect paths remain possible.

## Decoder, falsifiers and measurement

03f1 now also exposes native_requested_team_raw/id and native_result_scope=end_request;
legacy native_winning_team fields remain aliases for compatibility. Contradictory
repeated requests and upper-word bits are preserved. No winner/color resolver.
Tests reject invented accepted/completed/winner semantics. Exact recording build
match remains unproved.

Next trace must bind actor lifetime and roster raw team, crystal actor ID/definition/
team, selected actor/context, camera/color configuration, surrender state action,
end action, accepted primary transition, result callback and rendered banner.
Use same-match observations from both teams and spectator/replay viewpoints;
vary crystal destruction and surrender. Different requested teams with an ignored
transition refute last-request=display result; changing selected actor without
changing underlying teams refutes camera-side=team ID. A traced server terminal
producer would reopen the causal gap. No native/screen/server execution performed.
