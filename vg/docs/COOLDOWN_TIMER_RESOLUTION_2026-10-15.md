# Timer reference resolution and bounded live follow-up

Baseline `5582c26`; LAA image SHA-256
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`.
This corrects the prepared collector's pointer interpretation. It does not add a
replay countdown reducer or claim a completed three-stage HUD comparison.

## Static cause established with REA

`009613b0` allocates a timer under the cooldown state and stores **body+0x14**
at state+0x20, plus its generation at state+0x24. The timer-specific constructor
`00958d70` identifies `Referenceable<CKinTimer>` and writes body vtable
`0127ba9c` and inner vtable `0127baac`. Inner virtual slot +8 selects `00541fa0`:
the actual instructions return zero for null, otherwise **ECX-0x14**.

The getter `0093c860` calls that resolver and reads returned-body+0x24. The old
collector skipped the resolver and read inner+0x24, which is **body+0x38**.
That location is outside the registered timer size 0x2c. Generation equality at
inner+4 never established that inner itself was the timer body. The correction
comes from the timer constructor/resolver, not an assumed actor handle layout.

The [REA static receipt](evidence/2026-10-15-cooldown-timer/native-static.json)
retains Evidence IDs, image identity, provider/profile and full selected
pseudocode/assembly. It is shipped-artifact evidence, not execution evidence.

## Actual HUD number and overlay path

New incoming references to `009383d0` locate inventory consumer `005c5290`.
Its cooldown branches reach `005c51b0`; item lookup `00938370` checks instance
and available charges before reaching `0093c860`. The formatter's instructions
are ADDSS at `005c51e5`, then CVTTSS2SI at `005c51f4`, followed by `0096db20`
with `%d` and the text widget's virtual +0x98 call.

The constant at `01227654` has bits **0x3f7d70a4**, float32
**0.9900000095367432**. The observed static rule is float32 addition followed by
truncating signed-int conversion. It is not exact ceil: sufficiently small
positive fractions can remain at the lower integer. The same function computes
`1 - remaining / initial` with DIVSS/SUBSS and stores the overlay value at +0x638.
This establishes the selected numeric/overlay path, not every HUD branch or
text refresh timing. Nonfinite/out-of-range conversion is not promoted.

## Corrected observer and checks

`cooldown_probe.js` is a passive extension concatenated after the unchanged
stock probe. It validates timer-specific inner/body vtables, resolver slot and
instruction bytes, state ownership, timer class/pool identity, child membership,
callback subobject address, generation and pending bits before reading body
+0x20/+0x24/+0x28. Optional old inner+0x24 bits remain separately labeled unknown.

Null, stale, pending, wrong-type and unreadable timers remain unavailable with
unknown availability. They are never converted into zero or a ready item.
Charge gating is reported separately. Raw unsigned/signed bits, negative zero
and nonfinite values are preserved. Stock byte guards are unchanged.

Samples remain non-atomic and do not establish full native handle validity or
an indefinitely stable actor lifetime. An actor-child change between snapshots
still rejects the sample; its stable diagnostic code is retained without leaking
stock/native exception text. The new tests reproduce inner-raw-zero/body-positive,
corrupt resolver/type/owner/generation/pending cases, callback address versus
vtable confusion, ASLR, float serialization and volatile actor-child rejection.

## What the live run actually established

The [runtime receipt](evidence/2026-10-15-cooldown-timer/runtime-summary.json)
contains bounded Travel Boots observations and private screenshot hashes.

- A validated body read decreased through 85.46994, 82.49044 and 49.235958 seconds;
  the legacy inner+0x24 read remained zero. Native initial value was 90.099998,
  not inferred from the tooltip's 90. Pause was zero in these observations.
- A later use episode supplied a native value 82.829498 and HUD 82, but the
  following sample failed `changed_actor_or_inventory`. This is partial temporal
  corroboration, not an exact same-instant or completed bracketing match.
- `short-middle` was captured after expiry: both native samples had charges 1,
  null timer and remaining null; HUD had no countdown. Its filename does not
  make it a successful positive middle-stage comparison. `short-expiry` also
  provides post-expiry evidence, not the exact expiration frame.
- A separate guarded function instrument recorded 22,160 selected calls to
  stage-4 callback `009686d0`; 800 retained unpaused, same-delta before/after pairs
  matched float32 subtraction exactly, with zero mismatches. Minimum retained
  remaining value was 25.450062. The retention cap omitted expiry rows.

The tick experiment used Frida function instrumentation without changing return
values. It can affect timing and validates this instrumented run only. It is
separate from the shipped passive collector and does not recover original
recording frame partitions. The initial tracing prototype had an export-name
error; the corrected instrument completed and detached. Both failed continuous
collector attempts detached and are preserved as failures.

The last automatic three-stage attempt captured **zero stages**: the owned GUI
worker's one-hour loop ended at **17:24:43 UTC** before its first click could be
processed. Windows remained unlocked. The scheduled-task limit had been extended,
but that did not extend the worker's own loop. This timing failure was not
handled in time. No further experiment was started after the operator requested
closure. **Positive middle HUD bracketing and exact expiry remain unverified.**

## Replay and scope boundaries

The existing SHA-pinned `311232a1` static receipts retain the distinct replay
pump `004eb4a0`, enqueue `0092c240`, drain/apply `00931bd0`, publication
`0112b9e0` and stage-4 tick `009686d0` paths. The pump uses already-published
delta; timer tick uses the newly published delta, with intervening queue drains.
Game clock, record timestamp and these application boundaries are not equivalent.
Those receipts were reused, not merged. This run was practice, not replay
playback; it establishes no replay remaining-time accuracy or frame alignment.
H5810 and the previous three boots identity cases were not rerun. Source/version,
server final values and definitive eligibility are not promoted.

## Teardown and original preservation

A fresh backup contained 661 originals with SHA-256 and exact creation/write
FILETIMEs, rechecked before launch. After the worker exited, the owned game was
stopped only after PID/create-time/path/hash checks. The unprocessed capture-stop
command was archived as evidence. The owned scheduled task was removed; all
original filenames, contents and timestamps matched. Thirteen originals needed
restoration; 133 new session files were privately archived. Original/LAA hashes
were unchanged. Fresh checks found no game, owned observer, worker or task.
The owned REA target/session was closed. Raw recordings, backups, dumps, private
screenshots and helper logs were not published.
