# Resource controls for opcode041d

The original requirement is preserved verbatim:

> Capture14-byte record→12-byte native buffer plus resource ADD/SET before/after float32 bits, including6/7/11/14; establish CS visible label and lane-versus-jungle controls.

This package combines50 directly sampled receiver buffers,48 synthetic native resource transitions and two separately observed natural unit-kill controls. At native004d2d18, immediately after memmove and before endian conversion, the captured12-byte destination equals the first12 bytes of the14-byte record payload. The destination is EBP−0xe40 and the source is packet+2. Dispatch identity, thread, event order, constructor arguments and full unchanged reader dictionaries link each observation. Static receiver evidence is included in `receiver-041d.c.txt`.

| Scenario | Binary observable | Evidence |
| --- | --- | --- |
| Original C08 receiver buffer |50 exact dispatch→raw12→constructor chains; index2 ADD35 and index3 ADD15 |`controls.json` raw_receiver_buffer_controls |
| Resource6/7/11/14, ADD/SET, positive/zero/negative |48 matched source→constructor→queue→apply transitions, exact float32 bits |`controls.json` synthetic_controls |
| Clamping and positive balance credit |Negative result clamps to0; positive resource6 ADD also credits resource7 |Auditor recomputation from native before values |
| Natural lane unit |One red flag-bearing lane unit dies; visible icon0→1 and native resource14 0→1 |`lane-before.png`, `lane-after.png`, natural_controls lane |
| Natural jungle unit |First of two jungle creatures dies while the second remains alive; icon0→1 and native0→1 |`jungle-before.png`, `jungle-after.png`, natural_controls jungle |
| Broader sample trace |Lane10 and jungle3 separate+1 transitions each uniquely align with original resource14 ADD1 within sampled recording-clock intervals |13 source records with offsets, bits, file hashes and native line references |
| Tamper rejection |15 embedded-data mutations and5 additional external-provenance mutations rejected |`test_audit.py` |

The48 synthetic cases comprise24 seed SET10 operations and24 tested operations: four resource indices × ADD/SET × operand3/0/−20. Synthetic source metadata remains explicit; these are controlled reader inputs, not naturally emitted source events. Source subtraction reconstructs the original modified section hash in external-file mode.

The50 raw-buffer controls are original C08 inputs on indices2/3. Their identical section/time/content occurs at6–19 source offsets per record; every candidate is retained and external mode independently enumerates the complete matching offset set. No unique source offset is claimed. This ambiguity does not affect the observed dispatch-to-buffer identity. Arithmetic semantics for indices2/3 are not claimed. The48 controlled6/7/11/14 cases supply the separate ADD/SET arithmetic axis; their `native_prefix_hex` remains explicitly derived, rather than a sampled stack buffer. The frozen probe source hash is verified against the capture receipt.

The visual label is the actual minion-shaped icon and adjacent number. No literal “CS” text or tooltip was observed. The natural comparisons establish that both the observed lane and jungle kills increment this displayed counter. They do not establish a global victim taxonomy, exact victim actorIDs, or lane-only semantics. The existing [scoreboard evidence](../counter-ui.json) separately compares ten rendered K/D/A/icon rows against native samples.

All four PNGs are unmodified full3094×1870 captures. Image generation and thumbnail output are not used as proof. The natural records use `record_clock_unverified` intervals, with live samples explicitly reporting `not_replay` and non-atomic boundaries; no exact native dispatch association is claimed for natural kills. Gold/net-worth observations remain native values, not inferred kill-reward totals.

From this directory, run the standalone audit and negative checks:

```sh
python3 audit.py
python3 test_audit.py
```

To recheck hashed external captures, every selected1-based line, source offsets and all246 source section files, pass the outer workspace:

```sh
python3 audit.py --workspace /path/to/outer/vg
python3 test_audit.py --workspace /path/to/outer/vg
```

The auditor returns `ok:true` and `strict_requirement_complete:true` for the original requirement through these complementary controls. It returns `whole_event_semantics_verified:false`: other resources, flags, opaque suffix semantics and cross-build behavior remain outside this package. No atlas status is changed here.
