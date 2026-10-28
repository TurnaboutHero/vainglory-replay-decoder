# 1. Cooldown, ultimate availability and HUD

## Starting point and questions

Read dictionary entries VGRE-cooldown-timer-reference-hud,
VGRE-cooldown-replay-time-identifiability, VGRE-deepening-cooldown-two-state-blocker-selector,
VGRE-status-action-specific-gates and VGRE-ability-slot-ultimate-identity;
then ABILITY_HUD_FOLLOWUP_2026-10-16.md and COOLDOWN_TIMER_RESOLUTION_2026-10-15.md.

Already proven (not counted as fresh discoveries): state+20 stores timer body+14;
body+24 remaining differs from wrapper+24; charge-gated getter can return zero
while a hidden recharge timer runs; inventory formatting uses float32(remaining+.99)
then truncation, not exact ceil. Ability+11c/+120 selector is not universal cast
eligibility. Ultimate is definition/selector specific, not universal native slot2.
Replay header time alone does not identify game-clock progression under unknown pause.

## Supported decoder improvement

The stateless 048a parser now names byte16 as native_charge_setter_input and byte17
as native_base_charge_creation_input while retaining every raw byte and float bit.
Metadata records creation-only config and timer-input-before-charge-input dispatch.
These are roles of inputs in the selected native receiver, not observations that
it created a state or successfully applied a final charge count. There is no new
readiness/timer reducer or owner/key cache.

Bounded source: 0052aea0 resolves actor/key. Existing-state branch skips
009401f0/0095dd50/0095dcf0. Both branches dispatch 0095cf10, then0095cd10.
The hash-gated PE check reproduces those direct call sites and the linked
0095cf10→009613b0/00956380 edges. This check does not prove all branch conditions.

Independent review found no blockers. Current parser regression tests distinguish
byte16/17, repeated same-owner/key input with changing config, and absence of
state_created/resulting_charges/ready fields. Existing nonfinite/negative-zero
coverage remains active. Reproducible command: python -X utf8 -B -m unittest
 tests.test_cooldown_event_timeline tests.test_item_activation_timeline
 tests.test_research_cooldown_models tests.test_sequential_pe -q.

## Fresh extraction and closure

Fresh extraction closes the following bounded edges:

- 00958030 installs callback vtable01280678 at state+1c. Table+4 points to
  009519a0. Tick009686d0 reads engine delta through0112a7a0/global020ec6d0;
  if unpaused it subtracts delta from body+24 and invokes callback+4 at <=0.
- 009519a0 assembly adjusts ECX by -1c before0095cd10/00956380. Its callback+26
  is state+42; callback+28 is state+44. For selected mode0 and strict negative
  remaining it stores abs(overshoot) at state+3c, increments charges through
  the setter, then advances recharge lifecycle.
- 00956380 is not an unconditional stop: it marks a currently active timer
  through0112a080; if charge differs from unsigned base+40 plus signed modifier+41,
  it allocates/rebinds a timer and writes effective duration from0086bbf0 into
  initial+20/remaining+24 and callback pointer+1c. Full-cap returns without
  replacement. Invalid/null handles retain prior observer preconditions.
- Fresh0054d550→005b9930→005ad730→005a40e0 and
  0054d530→005b9920→005ad700→005a4070 connect modified/ended events to three
  buttons: base controller+340, stride16c8. The downstream005a6b40 selected-key
  guard and005a40e0 negative-delta filter prevent unconditional global-ready
  interpretation. Effects are not numeric text or authoritative activation.
-00936490 accumulates rank, charges/timer, action state, resource, child-provider,
  status and definition exceptions.008702c0 checks its complete zero result for
  an item-selected ability; neither a status subset nor a zero cooldown alone
  establishes ready.0093bce0 was an interior-address guess resolved to0093bc80;
  that unrelated curve output was excluded from conclusions.

Boundary: inventory countdown formatting and engine delta are identified, but
historical replay clock/pause partition, all hero numeric branches, per-hero
ultimate selector and native successful cast are not observed. No timer reducer
is justified. Next measurement: same-generation actor/ability/key, timer body,
charges, engine delta/pause, complete readiness reason mask, displayed selector,
HUD number, outgoing request and separately received apply action at bracketed
frames before/after expiry and under stun/silence. Repeat per hero/ultimate and
charge ability; reject identity changes and distinguish request from apply.
Falsifiers: callback table target or ECX correction differs on another build;
positive charges with hidden active timer refute zero-sync→no-timer; nonzero
readiness reason with zero timer refutes timer-only readiness.
