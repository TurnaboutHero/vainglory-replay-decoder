#!/bin/bash
set -eu
BASE="$(cd "$(dirname "$0")" && pwd)"
: "${GHIDRA_HOME:?Set GHIDRA_HOME to Ghidra 12.1.3}"
: "${GHIDRA_PROJECT:?Set GHIDRA_PROJECT to a writable project directory}"
PASS="$1"; shift
"$GHIDRA_HOME/support/analyzeHeadless" "$GHIDRA_PROJECT" combat -process Vainglory.exe -noanalysis -scriptPath "$BASE/scripts" -postScript CombatProbe.java "$BASE/$PASS" "$@"
