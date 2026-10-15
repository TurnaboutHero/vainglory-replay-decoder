# Reproduce the bounded static receipts

Use Ghidra 12.1.3 / JDK 21, the SHA256-pinned EXE in REPORT.ko.md, and CombatProbe.java. Do not execute the game. The probe changes only a Ghidra analysis database. No REA IPC bypass is used.

A clean import can use:

    analyzeHeadless PROJECT_DIR combat -import Vainglory.exe -noanalysis -scriptPath scripts -postScript CombatProbe.java OUTPUT_DIR 004ca130 004eb4a0

Then process that project with `-process Vainglory.exe -noanalysis`, running the following address sets in order. Set GHIDRA_HOME and GHIDRA_PROJECT, JAVA_HOME and writable Java configuration directories, then invoke the portable wrapper with bash probe.sh. The analysis database is excluded.

- pass1: 004ca130 004eb4a0 004cfec0 004c6990 004ce050 004ca300
- pass2: 0092c240 004cb590 0112b850 004eab50 004eb410 004eb420 004eaca0 004eb430
- pass3: 004c0380 0112a6c0 0092bfb0 005497a0
- pass4: 004eb210 004ead60 004ead00 0092f390 0092eb60 004eb2d0
- pass5: 0092f720 00966fd0 009670c0 00953440 00975780 004cd3a0 v:012179b8
- pass6: 0092f980 0092fad0 00931bd0 0093d180
- pass7: 004c6b90
- pass8: 004c6380
- pass9: 0112b150

`prior-clock/` contains selected earlier standalone receipts, explicitly reused rather than claimed as a new runtime run. Disassembly/decompilation can differ in inferred function boundaries on a pristine import. 0092bfb0 was a speculative start inside another function and is NOT evidence for any finding. 004cfec0 is only a partial dispatcher recovery, not a whole-dispatcher proof. 004ead60 is a tail thunk whose C output inlines another function; no clock claim depends on that body.

Exploratory raw byte-reference candidate scans are omitted. Only the included disassembled receipts support final conclusions.

Offline corpus check requires the repository module vg.core.vgr_records and the privately held original H5810 folder. The checked-in script documents expected layout. From the repository root, run `PYTHONPATH=. python /path/to/corpus_check.py /path/to/H5810`. Results are written beside the script; copy it to a scratch directory first to preserve this archived receipt. This envelope census does not need or create runtime observations. No executable or original replay payloads are included in the portable artifact.

`python partition_counterexample.py` is standalone and regenerates the two explicitly synthetic arithmetic witnesses. Python binary64 arithmetic is exact for these chosen binary32 operands before the explicit binary32 store.
