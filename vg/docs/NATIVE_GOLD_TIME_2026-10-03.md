# Windows gold dataflow and final clock boundary

Executable SHA256: `659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`. Addresses are preferred Windows VAs, not runtime addresses or Android offsets. This audit uses an existing Ghidra12.1.3 project read-only with no new analysis or client launch. Selected decompilation and constant bytes are retained in [native-paths.txt](evidence/2026-10-03-gold-time/native-paths.txt).

## Snapshot to resource storage

Dispatcher004cfec0 case03f3 copies746 payload bytes and endian-converts its fields. Handler004d5930 skips baseline decoding for nonzero payload+326. For zero, payload+286/+290 (hex11e/122) become local_78/local_74 within the temporary block at local_360: offsets2e8/2ec, or resource array2d0 + indices6/7.

Constructor0081ac20 receives that block and copies it through0081f5d0 into ActionHeroSpawn+40. The same copy routine preserves all16 resources during queue cloning0092e320. The ActionHeroSpawn vtable at0127c914 binds slot8 to apply0094e170 and slotc to queue cloning. Apply calls0095c940 when event+358 is zero. That routine assigns all16 resources from source+2d0 to actor component+2f0, so resource6 becomes component+308 and resource7 becomes+30c. This closes the Windows path independently of the earlier Android snapshot proof.

The supported746/750-byte payload variants share this prefix. No unrecognized layout is inferred from similar values.

## Resource arithmetic and scoreboard binding

Action041d apply0094f210 calls ADD0093ead0 for mode0, otherwise SET0095f160. ADD with resource6 and positive value increments component+30c before updating resource6. Constant01213f98 is float32 zero (`00000000`); there is no positive epsilon threshold. SET bypasses the resource7 increment. Store0095f270 clamps nonpositive values to0 and stores at component+2f0+4*index. Float32 storage is significant, so an unrounded double-precision sum is not the same state.

Export004c13b0 reads component+30c and passes it under literal `myNW`. Scoreboard row006f6fd0 reads the same field and only calls00740390 when `int(value * float32(0.01))` exceeds its cached integer at row+f4. Formatter00740390 uses `%.1fk` and multiplier float32(0.001). Constant bytes are `0ad7233c` at0121cce0 and `6f12833a` at0121cc60.

Final-screen function006f4fb0 enables final flags, shows the banner and refreshes16 player rows. It does not force the cached gold integer to reset. A displayed11.2k is therefore not an assertion that an EOF raw value rounds to11.2k; when and with which value the row last updated also matters. The new decoder exposes raw recorded state only.

## Duration findings and remaining boundary

03f1 apply0094d450 reaches00549620, which calls primary transition00549f60(2) and secondary transition0054a030(3). Constructor005483c0 registers005497a0 as primary state1 tick and no tick for state2. State1 entry is00548c60; its exit is005491a0. These callback registrations are not by themselves proof of the runtime callback order.

Scoreboard006f50e0 reads the game clock through00548880/00548870, compares integer seconds modulo60 to cache+1184, and passes the clock to0073a770, which formats minutes and seconds with `%d:%02d`. Importantly replay final entry00565f90 calls006f4f00(1,...) before006f4fb0.006f4f00 registers006f2d60 and immediately calls006f5050, which calls006f50e0. Thus final entry DOES refresh the time through its parent path. No final-flag guard was found in006f5050 or006f50e0.

The file's anchor-interpolated terminal-request time equals EOF in all3 checked recordings. The table preserves the captures available to this static audit; the later [runtime follow-up](RUNTIME_DISPLAY_2026-10-03.md) observed C16 at27:55 with its terminal clock within1.953125 milliseconds of file interpolation:

| Recording | EOF/request seconds | Previously captured display |
| --- | ---: | --- |
| normal17 |164.07888793945312|2:44|
| C34 |39.87332534790039|0:39|
| C16 |1675.6412353515625|27:53|

Choosing03f1 instead of EOF does not explain the earlier C16 capture. The later runtime measurement supplies the actual terminal/final clock and cached gold inputs for one successful path; the earlier27:53 cause remains unresolved. A scheduler/clock discrepancy is not proven by static code alone. No universal offset, final duration claim, or UI cache simulation is added.

## Export boundary

`read_native_gold` describes EOF state for a supported recording layout. It rejects unproved state and never manufactures a600 baseline. The result is additive in debug gold output; legacy partial estimates are retained for compatibility. Safe match/index fields remain withheld pending separate final validation. No new game run was required for this change.
