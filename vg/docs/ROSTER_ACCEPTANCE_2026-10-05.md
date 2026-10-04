# Approved roster UI acceptance - 2026-10-05

The user confirmed that the original in-game scoreboard displays player nicknames and hero portraits without hero-name text. They explicitly approved replacing the literal rendered-name condition with a portrait plus independently matched actor ID, original hero definition and unique K/D/A comparison, and recognizing the roster verification as complete.

The original experiment remains recorded in the atlas as `original_required_experiment`. Its literal-text interpretation required visible Petal/Lance name text. That UI-text observation remains unproved. The approved criterion now accepts the actually rendered portraits, with manual interpretation disclosed and independent original-source/native/asset checks retained.

The immutable [identity index](evidence/2026-10-04-opcode-controls/roster-identity.json) and [original screenshot](evidence/2026-10-04-opcode-controls/roster-identity-board.png) provide the evidence:

| Nickname | Native actor ID | Original definition ID | Original asset hero | Rendered K/D/A |
|---|---|---|---|---|
| Guest |1501|246|Petal|8/0/9|
| Guest |1502|275|Lance|2/4/16|

All ten native K/D/A tuples are unique at this observed boundary; row order does not establish identity. Both Guest actors are compared in216-byte and222-byte roster payloads among50 exact original-frame/dispatch/native-consumer controls. The original paired definition manifest and hero resources independently resolve246/Petal and275/Lance. Raw skin values are compared without claiming skin-index/name resolution.

Native capture lines244 and248 bracket the original screenshot interval. Across342 raw samples, players, native roster and game-clock bits remain fixed at exhausted EOF; playback time continues advancing and changes during32 reads. The reader retains the exact last framed source record in section169, with section170 absent and the source file closed. Native reads are non-atomic; this is observed stability, not an atomic or paused-reader claim.

The [auditor](evidence/2026-10-04-opcode-controls/audit_roster_identity.py) recomputes the embedded comparisons. Its optional `--workspace` mode also checks the raw captures, all170 original sections, source uniqueness, full342-sample stability, capture receipt and paired original assets. The [tests](evidence/2026-10-04-opcode-controls/test_roster_identity.py) preserve row-order independence and reject11 identity/boundary mutations.

Only the03ee player-state runtime-control gate changes to verified. Both216/222 required-field proofs remain bounded to the pinned replay build; whole-event suffixes, networking behavior and other builds remain outside this acceptance. All nine primary runtime-control gates now have bounded evidence. This is separate from universal decoder accuracy, unknown event semantics, and final-game completeness.
