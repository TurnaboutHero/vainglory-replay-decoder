# Recording-client provenance (2026-10-05)

## Question

`decode_player_state` reported `support_status=supported` with `supported_client_sha256` for recordings
written by clients other than the reference Windows build. Can a recording identify the client build that
wrote it, so that support could be gated on it?

## Corpora

| corpus | `.0.vgr` families | origin |
|---|---|---|
| dev | 56 | the development corpus (2021–2022 recordings) |
| steamtemp | 20 | Steam Windows client practice sessions, 2026-10-03/04 (one empty file excluded) |
| vgna | 8 | VGNA community client uploads, 2026-10-04/05, held out from development |

## Probes

Scripts: [evidence/2026-10-05-recording-client](evidence/2026-10-05-recording-client/) take the three corpus roots as
arguments and print counts and byte positions only. Free-text payload strings, including player names, are never kept;
only version/build-shaped tokens are counted.

1. `client_probe.py`: the opcode/length signature of the first records, a count of version/build-shaped tokens
   (dotted numbers, `build`, `version`, platform names) in printable strings in the first 200 records of
   section 0, and the opcode/length histogram across all sections.
2. `byte_marker_probe.py`: for the first fixed-length `03ee` (216-byte payload), `03e9` (101) and `046f` (69)
   record of every family, (a) byte positions that are constant within each corpus but differ between corpora,
   and (b) positions that are constant within one corpus with a value that never occurs at that position in
   any other corpus. (b) also catches a marker that varies inside a mixed-build corpus.

## Result

- Early-record layout: the same two 12-record opening sequences occur in dev and vgna; steamtemp uses
  another opening of the same opcodes. All three share the first-record shape `03ee`/218.
- Strings: zero version/build-shaped tokens in any corpus.
- Opcodes: none occurs only in vgna. Comparing the top 8 lengths per opcode, no length occurs only in vgna.
- Byte markers: no candidate position in any of the three record types under either rule (a) or (b). 179/216, 86/101 and 52/69 positions
  are constant across all corpora; every other position varies within a corpus.

No in-band client identifier was found, so client identity cannot gate support.

## What support means

The operative compatibility gate is record-layout conformance: native readers reject unexpected payload
lengths for every opcode they consume (`native_roster` 03ee/03f3, `native_inventory`, `native_stats` and
`native_gold` spawn/snapshot lengths). Catalog labels additionally require matching catalog provenance once #14 lands; until then a mismatched roster
catalog is not detected.
In the 2026-10-05 held-out evaluation, VGNA-client recordings passed these gates, and recorded-end values
agreed with an independent parser except for documented reference staleness and naming differences.

The output now says this explicitly:

- `recording_client = {status: "unverified", reason: ...}` on every `decoder_v2.player_state.v3` result.
  The field is additive, so there is no schema change.
- `supported_client_sha256` is unchanged. It names the reference build that the layouts and catalogs came from.
- `support_status` is not downgraded for an unverified client. Marking every recording `partial` because the
  client cannot be known would remove the distinction the layout gate does provide.

## Limits

The probes cover early records and opcode/length histograms, not every byte of every record. A client
whose layout matches but whose game data maps definitions differently would only be caught by the
catalog-provenance and roster corroboration checks.
