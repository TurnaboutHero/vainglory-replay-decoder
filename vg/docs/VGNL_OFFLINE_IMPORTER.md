# Offline VGNL application-payload importer

`vg.core.vgnl_importer` imports locally supplied **complete binary WebSocket
application payloads**, one payload per input file. It does not parse raw TCP,
WebSocket wire framing, masking, fragmentation, packet captures, base64, or a
concatenated payload stream. Obtain correctly delimited, unmasked application
payloads through an independently authorized workflow before using it.

This is a standard-library-only, offline adapter for a statically observed
Android producer contract. It contains no network, account, authentication,
client/APK execution, installation or server-control implementation.

## CLI

Use Python 3.12+ from the repository root. Supply the raw replayId context
explicitly; the binary header does not contain that value. List payload files
in capture order. The output directory must be new, and its parent must exist.

```sh
python -B -m vg.core.vgnl_importer capture/000.bin capture/001.bin \
  --replay-id 'the-exact-raw-replayId' --output reports/import-01
```

Optional local JSON sidecars are read without contacting their purported source:

```sh
python -B -m vg.core.vgnl_importer capture/002.bin \
  --replay-id 'the-exact-raw-replayId' --resume capture/resume.json \
  --terminal-scoreboard capture/terminal.json --output reports/import-02
```

Exit codes:

- **0:** supplied observations validated under this adapter policy; warnings or
  withheld reconstruction can remain. This is not a complete-replay assertion
- **1:** bundle written with validation/continuity errors; no reconstructed VGR
- **2:** input/output/argument failure; existing inputs and output directories are
  never overwritten. An interrupted new output may remain without its manifest

## Python API

```python
from vg.core.vgnl_importer import SourceInput, decode_frame, import_payloads

inputs = [SourceInput.read("capture/000.bin"), SourceInput.read("capture/001.bin")]
frame = decode_frame(inputs[0].data)  # raises VGNLFormatError with code and offset
result = import_payloads(inputs, replay_id="the-exact-raw-replayId")
print(result.report["status"], result.report["issues"])
manifest_path = result.write("reports/import-01")
```

`SourceInput(data: bytes, locator: str)` also accepts in-memory bytes. The caller
owns the locator and replay-context assertions; neither is validated against a
server. `ImportResult.sections` maps section numbers to reconstructed bytes only
when the entire import passes the conservative reconstruction gate.

## Bundle and provenance

`manifest.json` has schema `vg.vgnl-import.v1` and includes:

- Every input's locator, ordinal, byte length, SHA-256 and retained `sources/NNNNNN.bin`
  file, including invalid payloads and exact JSON sidecar bytes
- Valid frame epoch, sequence, flags, section/offset, payload length/SHA-256/CRC32,
  record count, raw first/last timestamp hex and sampled game clock
- Every native record's input byte offset, source-section byte offset, raw timestamp,
  body length and full-record SHA-256. Native timestamp bytes remain opaque
- Explicit errors/warnings with source indices and missing-range/conflict details
- When safe, `replay/imported.N.vgr`, reconstructed byte length/SHA-256 and source
  indices. A fixed safe filename is used; the supplied replayId is never a path

The original bytes are authoritative evidence for reinspection. Source hashes
identify bytes; they do not establish who produced or authenticated them.
CRC32 checks **payload bytes only**, and does not authenticate the header or sender.

## Strict validation and reconstruction policy

The observed header is 68 bytes, big endian, with magic `VGNL`, version 1, data
kind 1 or end kind 2. The importer checks exact message length, payload CRC32,
nonnegative signed sequence/section/offset, 64-bit offset addition, finite sampled
clock, observed flag combinations and end-frame shape. Data payloads must contain
one or more complete native records with 4 opaque timestamp bytes, signed i32
body length in 0–2,097,152, and body bytes. Count and first/last timestamp bounds
must match. Zero-length bodies are allowed by the producer contract; acceptance
here does not guarantee the existing game-record decoder accepts their semantics.

One import accepts one explicit raw replay context and one transport epoch.
Different epochs are retained and reported as errors, never combined. Separate
archives must be imported separately. Frames do not carry a platform match ID,
so mistakenly labelled same-epoch data from different matches cannot be detected
from this header alone. The caller must supply correctly scoped inputs.

The original input order is retained. Out-of-order valid inputs get a warning;
continuity is checked in numeric sequence order. Expected sequence starts at 0,
or at an explicitly supplied resume claim. Missing sequences are interval reports,
not expanded lists. Byte-identical duplicate frames and exact duplicate source
ranges are explicit warnings and are reconstructed once. Different bytes for the
same sequence or source range are errors. Partial overlaps, source byte gaps,
missing section numbers, section-order regressions, frames after an end, and
inconsistent end timestamp bytes are errors.

**Any error withholds all reconstructed VGR files.** Input bytes, metadata and
issues are still exported. No zero filling, overlap merging, automatic epoch
joining, or accepting the first of conflicting copies occurs. If no errors,
missing prior history or bytes exist, contiguous observed sections can be exported
without a transport end; the missing end is explicitly reported. Neither that
prefix nor a transport end proves the source section is complete or gameplay ended.
A dropped tail cannot be inferred from an end frame because it carries no final
section size manifest.

Observed flags, finite-clock requirements, strict JSON typing, duplicate-key
rejection and conflict gating are **adapter acceptance choices**, not assertions
about all producer versions or server validation behavior.

## Resume sidecar: claims do not supply missing bytes

The adapter sidecar is an explicit projection, not an implementation of a server
response parser. Its exact keys are:

```json
{
  "epoch": "00000000-0000-4000-8000-000000000001",
  "latest_sequence": 4,
  "segments": [
    {"source_section": 0, "source_offset": 0, "length": 1000}
  ]
}
```

Types must be JSON integers, never booleans, strings or floats. Sequence is
-1 through 2^63-2; section is 0 through 2^31-1; offsets/lengths are 0 through
2^63-1 with checked addition. The expected next sequence is latest+1 and each
section cursor is the maximum claimed end, matching the observed consumer's
boundary calculation. The adapter additionally reports holes, overlapping claims,
duplicate segments, wrong epochs and replay frames conflicting with resume
sequence/offset boundaries.

An existing sequence history or any claimed prior byte range always withholds VGR
reconstruction. Resume metadata has no independently checked bytes or hashes, so
it is never used to fill, authenticate or deduplicate prior content. To reconstruct
from scratch, provide the actual complete payload sequence beginning at zero in a
separate import without a resume claim. This version does not append to or trust
previous import bundles.

## Identity and terminal-scoreboard boundaries

- `raw_replay_id` remains a caller-supplied label. The separately marked logical
  normalization uses Java UTF-16 code units: it strips 37 units only for a
  73-unit value with a hyphen at unit index 36. It is not UUID validation or a
  player/account identifier; the raw Unicode value remains unchanged
- Transport `epoch`, platform match/replay context, `player_uuid`, `install_id`
  and native `entity_id` remain distinct. No automatic cross-identity join exists
- Optional terminal JSON must contain exactly `type: terminal_scoreboard`, a
  matching `epoch`, `source: native_terminal_actor_model`, and `players`
- Each of 1–16 rows must contain only integer `entity_id` (1–4294967294) and
  `hero` (1–64 printable ASCII characters excluding quote/backslash). Additional
  account/K/D/A fields are rejected; duplicate entity IDs are rejected
- Every accepted snapshot is preserved separately. Entity→hero is corroboration
  only, without an automatic join. Hero text is not a verified canonical hero ID;
  a snapshot may be an older cached fuller snapshot

The manifest always leaves recording client, account identity, server
acceptance/authentication and replay completeness unverified; authoritative result
and definitive-analysis eligibility remain false. Terminal rows supply no K/D/A,
team, gold or damage. Existing decoder result/eligibility gates are unchanged.

## Evidence and verification (2026-10-15)

Contract reference: static public VGNA Android 1.11 APK SHA-256
`8394caa6f44b536924e8dd733870ee7642a04cc47abcb971ffcaadfe931a2543`.
The separately observed request-header build is 113. This is a reference contract,
not a proven recording-client build. The implementation was based on the existing
static-analysis deliverables, pinned here for reproducibility:

| Source artifact | SHA-256 |
| --- | --- |
| `offline_frame.py` | `fa673839fed9f52c8ede248de8834d8a633655fa04095c2340ef5510459bb57d` |
| `schema-manifest.json` | `700f461557c3077eb9ca508d7f15301361f94f363039234d7d28250768195a99` |
| `REPORT.md` | `c4c0ee3f478367fadb626ef261b50835123c3022f747b68195c6b71a3720869a` |

No APK, native code excerpts, credentials, private replay bytes or account data
are included in this change. No server requests or client execution were used.

Run portable coverage:

```sh
python -X utf8 -B -m unittest tests.test_vgnl_importer -v
python -X utf8 -B -m unittest discover -s tests -v
```

Verification passed on Python 3.12.14 and Node.js v24.19.0: **30 focused tests**
and **962 full regression tests**. Independent review also checked randomized
reconstruction/malformed input and existing-destination symlink refusal.

Focused tests cover the header, CRC, every truncation point, record bounds,
flags, signed limits/overflow, exact deduplication, conflicts, gaps, epoch separation,
resume claims, terminal restrictions, provenance, CLI outputs/no-overwrite and the
existing synthetic product fixture through the unchanged player-state decoder.

A separate local check wrapped **H5810 sections 0–2** in **62 synthetic envelopes**
and reconstructed all **254,191 bytes / 5,988 native records** exactly. Original,
reconstructed and re-read source hashes matched, as did the existing VGR parser's
record counts. The three section hashes were:

- 0: `36b5bda0c5277efdf71b92e6275209912efd07e7f0139e6b2a70c4c13d92a08b`
- 1: `9580ce82ffbdb9b79e21e53d0634ad8258a73753a70efce67dfe104cfaf5df6a`
- 2: `55242390ac790e809c606c449cf52144b06b69b209c82e36b41572a15eea50fd`

Those source VGR files are not committed or needed by the portable suite.
**There is no actual captured VGNL/server holdout in this validation.** Synthetic
transport wrapping of existing VGR bytes does not prove real upload, server
compatibility, sender identity, complete games or authoritative statistics.
