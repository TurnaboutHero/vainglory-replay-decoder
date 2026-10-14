# Reproduce selected static receipts

Input: Vainglory.exe, SHA256 d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc. Do not execute it.

Use Ghidra 12.1.3 with JDK 21. Import the PE in a fresh private project, x86 little-endian 32-bit Windows loader, and run without auto-analysis. The included CombatProbe.java disassembles each explicit function entry, decompiles it, and writes both C and instructions. Invoke analyzeHeadless with -import INPUT -noanalysis -scriptPath THIS_DIRECTORY -postScript CombatProbe.java OUTPUT followed by the function entries named in receipts. For vtable output pass v:01280658. After first import, use -process Vainglory.exe instead of -import. Use a private project; never run two writers against one Ghidra project.

For each objdump-START-END.txt receipt, run GNU objdump -d --start-address=0xSTART --stop-address=0x(END+1) INPUT. These are bounded instruction evidence, not guessed function boundaries.

The original research used a private copy of the earlier combat project. Previously defined callee names/types may change decompiled C formatting versus a fresh project. Compare input hash, address, instructions, branches and data flow, not only text hashes. receipt-hashes.json records the delivered artifacts' integrity, not a guarantee of cross-version decompiler text identity.
