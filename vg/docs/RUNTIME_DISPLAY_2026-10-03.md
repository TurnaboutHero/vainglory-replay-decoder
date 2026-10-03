# Observed replay clock and cached gold display

Two instrumented Windows replay runs reached their final screens and detached normally: normal17 at normal speed, and C16 after seeking near the end and continuing at normal speed. C16 displayed **27:55**; its terminal clock differed from file interpolation by **1.953125 milliseconds**. Ten C16 gold labels were explained by the last cached formatter inputs. This validates those playback paths, not a universal final-match algorithm.

The selected numeric evidence, event sequence numbers, float bits, replay scopes, artifact hashes and restoration receipts are in [runtime-display.json](evidence/2026-10-03-gold-time/runtime-display.json). Private full traces, screenshots, replay bytes and machine paths are excluded from this repository. Screenshot transcription was checked visually; hashes identify the private artifacts but do not independently authenticate that transcription.

## Runtime method

The original client SHA256 is `659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`. Runs used an owned copy with only the PE LargeAddressAware flag changed, SHA256 `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`. The original executable and source recordings retained their hashes.

The bounded Frida17.17.0 observer checked the executable identity and relocated instruction bytes before installing seven entry hooks. These covered the anchor, terminal, final entry, time formatter, gold row, gold formatter and gold text consumer. The actor resolver was checked without invoking it. There were no interior or return hooks, native gameplay calls, or writes to gameplay state. Hook installation still modifies executable instructions and can affect timing; successful completion does not prove zero observer effect.

The observer captured the actual floating-point argument at time formatter0073a770 and gold formatter00740390. Gold text was captured at007a84e0 only when its caller was007403cf, before the text consumer ran. Gold-row actor resolution required matching handle generations, the expected resolver vtable method00541fa0, and its exact instruction bytes. `actor_ref_178` remains a native reference label: its equality to known replay IDs and resource values is corroboration, not a new serialization-layout proof.

normal17 used all17 sections and ran at1x. C16 used all171 sections, sought through the replay UI at12:06:30UTC to approximately25:42, then continued at1x. Its scoreboard was opened at12:07:42UTC; terminal/final occurred at12:08:43.995UTC. Each observer was bounded to180 seconds and reported no error before detaching.

## Clock result

| Recording | File EOF seconds | Native terminal/final seconds | Runtime minus file | Final screen |
| --- | ---: | ---: | ---: | --- |
| normal17 |164.07888793945312|164.07742309570312|-0.00146484375|2:44|
| C16 |1675.6412353515625|1675.6392822265625|-0.001953125|27:55|

C16's last anchor supplied1671.967529296875 at sequence3039. The runtime advanced3.6717529296875 seconds before terminal sequence3124 and final sequence3125. File interpolation adds3.6737060546875 seconds after the same anchor. Both terminal and final captured multiplier1.

The last C16 time formatter call, sequence3107, received1675.0020751953125, approximately637 milliseconds before terminal. Truncation and `%d:%02d` produce27:55, matching the screenshot. Final refresh does not require another formatter call when the integer-second cache is unchanged. In normal17, the final formatter received164.07742309570312 and the screen showed2:44.

The earlier C16 capture showing27:53 remains a valid historical observation with an unresolved run-specific cause. The new run demonstrates that a fixed two-second subtraction is not warranted. It does not isolate the contribution of earlier playback speed, scheduling, UI timing or instrumentation. No such cause is asserted, and final duration remains withheld from safe/index output.

## Gold result

The latest pre-terminal samples equal the previously decoded EOF resource7 values for all11 observed actors across both runs. These samples were not atomic terminal snapshots: normal17's was103 milliseconds before terminal using target timestamps; C16's were594-595 milliseconds before terminal. Every retained display value equals its last observed gold formatter input, whose captured text matches the final screenshot.

The row updates only when `trunc(float32(resource7 * float32(0.01)))` exceeds its cached bucket. It passes the actual float at that update to the formatter; it does not pass `bucket * 100`. Formatter00740390 applies float32(0.001) and `%.1fk`.

| C16 actor_ref_178 | Latest resource7 | Bucket | Retained formatter input | Observed text |
| ---: | ---: | ---: | ---: | --- |
|1500|11195.3017578125|111|11177.3017578125|11.2k|
|1501|13540.34375|135|13501.34375|13.5k|
|1502|19710.677734375|197|19701.677734375|19.7k|
|1503|15820.3330078125|158|15802.3330078125|15.8k|
|1504|14220.46875|142|14202.46875|14.2k|
|1505|15881.759765625|158|15804.759765625|15.8k|
|1506|16532.23046875|165|16502.23046875|16.5k|
|1507|12175.7509765625|121|12109.7509765625|12.1k|
|1508|16467.78125|164|16401.78125|16.4k|
|1509|10691.978515625|106|10616.978515625|10.6k|

normal17's latest resource7 was30372 while its retained formatter input was30300, producing30.3k. Intermediate inputs30102 and30201 further show why a floor-to-100 simulation is wrong. C16 actor1500 has bucket111 but displays11.2k from input11177.3017578125. Actors1505,1507,1508 and1509 retain labels lower than directly rounding their latest resource7 would produce.

This explains the observed UI difference without changing the decoder's raw resource state. A general reconstruction of historical UI cache inputs would require validated update timing. Gold display remains observation-only and safe/index final gold remains withheld.

## Observer limits and failed attempt

The trace field `sample.time_labels` is not durable time-label evidence. It reads UI+13ba8, which is shared formatting scratch: time formatter0073a770 uses it, but team-gold formatters0073a9a0 and0073abd0 overwrite it. Thus late C16 samples contain74.5k. The time widget receives its text through UI+10dc; its persistent internal text layout was not established here. Clock claims above use formatter arguments and the rendered screenshot, not those scratch samples. `state.record_clock` also remained stale during playback and is excluded from clock claims.

An earlier broader normal17 observer included additional hooks and ended when the client exited during final processing. Its cause remains unproven. It is retained privately as a failed attempt, not successful acceptance or evidence for a playback-speed formula. Removing those hooks preceded the two successful runs but does not prove a particular hook caused the failure.

The owned game, observer, interactive worker and scheduled task were stopped. Both successful trials' slots were restored from hash-checked backups, as recorded in the receipt. The earlier failed trial had already been restored separately. Final environment verification found no game, owned observer/worker or task. No decoder implementation changed in this follow-up.
