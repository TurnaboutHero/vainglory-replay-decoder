# Reproduction
Work outside the repository. Input exe must remain unchanged.

Environment: Ghidra 12.1.3, JDK 21, Linux. Native REA IPC is blocked; these receipts are standalone Ghidra receipts, not successful REA bridge calls.

The initial import is:
GHIDRA/support/analyzeHeadless PROJECT_DIR combat -import EXE -noanalysis -scriptPath SCRIPTS -postScript CombatProbe.java OUTPUT_DIR 0081bb60 0081b8d0 0052ad40 v:0127ca18 v:0121aaf4 0094ee90

Set JAVA_HOME to the provided JDK, JAVA_TOOL_OPTIONS=-Duser.home=WRITABLE_HOME, and XDG_CONFIG_HOME/XDG_CACHE_HOME to writable locations. Set GHIDRA_HOME and GHIDRA_PROJECT for the portable probe.sh wrapper; run it with bash.

Subsequent passes:
bash probe.sh pass2 0094f500 0094b6c0 0092eb60 0052aea0 0052ae00 v:0127c98c 00563a30 008708a0 00536dd0 00963200
bash probe.sh pass3 r:0094f500 00945cc0 0094f500 00945d70 0095cf10 0095cd10 0095dd50 0095dcf0 009401f0 008579e0 0094f170
bash probe.sh pass4 009613b0 00956380 0093d4a0 0052aea0 0094f170 00945d70
python raw_refs.py /path/to/Vainglory.exe
bash probe.sh pass5 00551b00 00598230 00598df0 009547d0

r: deletes a function definition in the analysis database only, to split a tail-call boundary. It does not modify input bytes.
v: prints 28 raw pointer words; only the identified slots are semantically claimed. Entries after a given vtable boundary may belong to adjacent tables.
The original analysis used no whole-program autoanalysis or runtime execution. These receipts are now archived alongside the bounded decoder patch.
Decompiler signatures are inferred and sometimes omit this/return values. Check INSTRUCTIONS in each receipt for register-based argument flow.
raw_refs.py uses byte-level matching, deliberately labels E8 results candidates, and does not assert every match is a decoded instruction.

## Clock/HUD follow-up passes
bash probe.sh pass6 0086bbf0 0054d550 0054d530 0054d510 0112aa20 0112a080
bash probe.sh pass7 005b9c30 005b9920 005b9930
bash probe.sh pass8 00947480 009476c0 00947820 009686d0 005a4070 005a48d0 005ad730
bash probe.sh pass9 0112a7a0 005a40e0 005a6b40 009383d0 00534230 00407760 0092ad50
bash probe.sh pass10 0112b970 00954e40 0093c860 v:0127cae0
bash probe.sh pass11 0112b9e0 004c6990 0094fc50
bash probe.sh pass12 0093ba70 0112a7d0 0112a6e0 0112b130 004ce050 004ca300
bash probe.sh pass13 0094fc60 00950710 0095f470
bash probe.sh pass14 v:0127cbcc 0081bde0 0081c350

Raw absolute-reference candidate scanning uses the same PE mapping and little-endian pointer search as raw_refs.py. CC-padding boundary guesses are candidate hints, not proven function starts. In particular the global writer at 0112ba10 belongs to 0112b9e0, not the initial guessed 0112b970. All final findings rely on disassembled Ghidra receipts.
