# Ability/HUD follow-up boundary : 2026-10-16

Baseline: `9712ab6`, branch `research/rea-boundaries-20261016`. Read-only review of existing repository material, archived REA JSON, and fresh parent-acquired REA outputs. This reviewer launched no REA/Ghidra or native execution and made no recording recount, binary/project mutation, or network operation. Static VAs below refer to LAA EXE SHA-256 `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`. This is a follow-up extraction plan and bounded source synthesis, not a new ultimate resolver or replay timer implementation.

## Useful distinction in the archived outputs

`004ca310`'s selected 048a-writing branch enumerates cooldown type `01ef0b3c`, reads state key +28, base +2c, bytes +40/+42 and flags, and calls `009383d0` for the float serialized before the configuration float. The existing charge-gated getter returns zero when state+42 is nonzero; otherwise it reaches the resolved timer-body +24 via `0093c860`. Thus a zero sync operand and positive available charges do not establish a stopped or absent recharge timer. This is a source-level implication, not a newly validated wire-to-state reconstruction. The old decompilation has missing ECX arguments and incorrect float/bit-swap casts. Fresh writer assembly now substantiates the selected serialization path below; it does not supply runtime execution evidence.

`005c5290` likewise has multiple presentation branches. One hashes a definition string at +11c and looks up actor state; another reaches instance lookup `00938370`. Stun/silence flags can select a badge and return before the countdown formatter. `005c51b0` is an inventory formatter, so its `trunc(float32(remaining + 0.99f))` and overlay `1 - remaining/initial` rule cannot yet be promoted to all hero ability buttons. The older named-effect path establishes identity guards and effects, not this numeric formatter for hero abilities.

## Evidence-to-extraction matrix

| Existing VA / path | Input -> output and known caller | Unresolved extraction target | Falsification / acceptance check |
| --- | --- | --- | --- |
| `0093fba0 -> 0093f7d0 -> 0093f270` | Inline actor definition+4c, ordered definition list+18 -> component+28+4*slot, ability+124 primary state | UI selectors at component definition+24/+28/+2c -> component+78 display list -> actual button consumer+16b0; extract relevant callers and instruction spans | Catherine A_DefaultAttack,A,B,C already refutes universal native slot2=third UI/ultimate. Verify selector traversal against all extracted ordered lists, including Ozo/Varya native8. |
| `0093cbf0`; ability+154 bits10..12 | Catalog reports rank bits and property base/increment/rank5-extra | Exact rank reader/writer callers, rank0 handling, learned-rank vs zero-based property operand; bind to chosen UI ability | Compare ranks 0,1,3,5 with independent resource values; do not infer timer start from nominal rank property. Selected rank instructions were not in this raw HUD export set. |
| `005a6b40 -> 00936950`; `005a4070/005a40e0` | Incoming state+28 compared to consumer-selected ability key -> Ready/CDReduce effect gates | Hero ability numeric text/overlay update callers; trace selected state pointer, primary vs secondary +120 state, and button count | A matching key proves the selected guard only. Reject a path that merely shares an effect name or consumes an alternate state. |
| `005c5290 -> 005c51b0` | Inventory identity/instance and status flags -> countdown text/overlay | Instruction spans and callers for branch predicates `0093d3d0`, `009367a0`, `00938300`, `009392b0`; compare hero formatter separately | Stunned/silenced branch bypasses formatter; text is not a universal availability predicate. Zero/negative initial and refresh cadence are unverified. |
| `00938370 -> 00939d30 -> 0093c860` | Inventory instance +30 -> item ability +18 -> charge-gated timer read | Recover explicit ECX/register arguments and missing-instance branch from assembly; extract `00939d30` | Decompiled null-item dereference is not a safe API contract. Preserve absent/stale state as unknown in an observer. |
| `004ca310 -> 009383d0 -> 0093c860` | Actor/key state -> charge-gated outgoing 048a float | Writer assembly now acquired; complete 048a apply `0052aea0` assembly, helper side effects, and caller/apply-stage receipts remain needed | Two states with same visible zero and different hidden recharge timers are compatible with this getter; raw sync zero cannot identify hidden timer. |
| `00940230`, `0093cdc0`, `008725f0`, `0093f270` | Item instance owns ability; ability selects actor-owned key state -> conditional sharing | Explicit gameplay cleanup on sell/replace/remove, runtime override/add/remove slot paths, actor generation boundaries | Deleting item children does not automatically delete actor-owned state sibling. Sharing requires same derived key and same actor lifetime; different actors or overrides refute unconditional sharing. |

## Fresh writer assembly and apply branch boundary

The parent supplied complete `004ca310` assembly and `0052aea0` pseudocode from the same SHA-bound LAA image. These are fresh static exports, distinct from the archived input table below.

At `004ca730`, ECX loads the enumerated cooldown pointer. Reads at `004ca737..004ca751` select state+48 flags, +2c float, +40 base-charge byte, +42 current-charge byte, +28 key and +44 low two bits. ECX is still that state at call `004ca76e -> 009383d0`; `004ca77a` stores the x87 result as float32. `004ca79b..004ca7e1` byte-swaps that float's raw bits into stack payload+8; `004ca7e4..004ca81b` similarly serializes saved state+2c into payload+12. This is bit serialization, not a float-to-integer numeric conversion. The +42 and +40 bytes reach payload+16/+17 at `004ca7d0`/`004ca7de`; low configuration bits and individually masked flags reach +18..+21. `004ca830..004ca86e` builds opcode 048a plus 22 payload bytes and submits 24 total bytes to `004cb590`. This establishes the selected writer fields and explicitly supplies the missing state ECX argument from the old pseudocode.

The resulting information-loss conclusion remains an inference combining this writer with the independently documented charge gate: when charges are nonzero, the outgoing float can be zero regardless of a positive recharge timer. It does not prove every live charged state has such a timer or reconstruct its hidden value.

Fresh `0052aea0` pseudocode resolves action+10 actor, then actor/key via `008579e0(action+14)`. Only the absent-state branch allocates type `01ef0b3c`, invokes `009401f0` with key/config low bits/three separate flags, then calls `0095dd50(action+1c)` and `0095dcf0(action+21)`. Both old-state and new-state branches then call `0095cf10(action+18)` followed by `0095cd10(action+20)`. Thus the selected control flow separates creation-only configuration from always-dispatched timer/charge inputs; it does not overwrite all configuration on every 048a. Fresh apply assembly and setter outputs now close the selected input-to-state dispatch boundary below; the full gameplay lifecycle remains outside this review.

`0052aea0` assembly explicitly preserves the selected state in EDI and moves EDI to ECX before `009401f0` (`0052aefa`), `0095dd50` (`0052af13`), `0095dcf0` (`0052af23`), `0095cf10` (`0052af31`), and `0095cd10` (`0052af41`). The existing-state branch at `0052aecb` jumps to `0052af2b`, bypassing all three creation helpers. Therefore +1c/+21 action fields do not overwrite existing state configuration through this selected apply path.

The new helper pseudocode establishes these bounded effects:

- `009401f0` writes state+28 key, low two state+44 bits, and three separate state+48 bits. `0095dd50` writes state+2c directly. `0095dcf0` writes state+40 base-charge byte; an increase or an over-cap current charge reaches `0095cd10`. Its omitted call arguments are not filled in from inference.
- `0095cf10` branches on `0093d4a0`'s low-byte predicate. In the inactive branch, nonpositive input returns; positive input requests `max(current_charge-1,0)` through `0095cd10`, then calls timer-start helper `009613b0`. In the active branch, nonpositive input requests current-charge+1 and calls `00956380`; positive input resolves the timer wrapper, replaces remaining +24, raises initial +20 when the new value exceeds it, and dispatches `onCooldownModified` with new-minus-old remaining. Fresh `0093d4a0` output now identifies the active predicate below; stop-helper internals remain outside the selected receiver slice.
- The positive active path compares state+24 generation with wrapper+4 before invoking wrapper virtual +8. A mismatch clears state+20 and resets its generation sentinel. The resolved timer body, rather than the wrapper itself, owns +20/+24. The decompiler's resulting null-body dereferences do not establish safe behavior for invalid handles; observer validation must still reject them.
- `0095cd10` writes state+42 after a capacity comparison involving unsigned base+40 and signed modifier+41. It dispatches `onCooldownStarted` when the old charge byte was nonzero and the new byte is zero, and `onCooldownEnded` on zero-to-nonzero. Same zero/nonzero class produces neither selected transition callback. Assembly now confirms `MOVZX` base+40, `MOVSX` modifier+41, their integer sum, two integer-to-double conversions with sign-indexed correction constants, float32 conversion, `MINSS`, `CVTTSS2SI`, then storage of AL (`0095cd1c..0095cd64`). The received charge input is explicitly zero-extended (`0052af3d`), so it is bounded to 0..255; the base/modifier sum ranges -128..382. This is a finite byte/capacity path, not an unrestricted signed `clamp(0,cap)` formula. In particular no independent lower-bound clamp is present in this setter. Negative-capacity interpretation and the correction-table constants are not extrapolated here.

These calls occur in order: timer input can first change charges and emit callbacks; the apply then explicitly calls `0095cd10(action+20)` with the received charge byte, with its own cap and transition logic. The final write is therefore not proof that intermediate callbacks were absent. A simplified overwrite-all or timer-only reducer would erase this distinction. No exact client frame ordering or successful gameplay activation follows from these static calls.

Fresh `0093d4a0` pseudocode returns true only after a non-null state+20 wrapper, matching state+24 generation, a non-null resolved body, and `0112aa20` returning zero. Generation mismatch clears the wrapper and resets the generation sentinel. This bounds “active” here to the selected valid-resolved, not-marked predicate rather than mere non-null storage; the `0112aa20` call's missing explicit argument remains a decompiler convention artifact, not an independently verified universal pending-object API contract.

`0095cf10` instructions confirm finite-positive paths use `COMISS`/`JBE`, the inactive decrement uses `MOVZX`/`DEC` then `MAXSS` against zero, and active nonpositive increments use `MOVZX`/`INC`/`MAXSS`; the timer update uses `MOVSS` to remaining +24 and only raises +20 after the comparison. `SUBSS` computes the modified delta before conversion to double for callback dispatch (`0095d01e..0095d038`). These are float32 operations. NaN/unordered and nonfinite inputs are not promoted into the prose “positive/nonpositive” model. Combined with the explicit later byte assignment, this closes the selected 048a receiver slice while retaining runtime ordering, arbitrary malformed input, and full gameplay lifecycle as unverified.

No additional broad extraction is needed for this bounded result. `00956380` and `009613b0` remain linked timer lifecycle helpers, not evidence of successful gameplay activation or exact replay frame progression.

Fresh raw JSON `016-procedure_pseudo_code-0x0052aea0.json`: SHA-256 `5d56d32cedc009a2c4e5bf049949054a426bd4cc2308a880f9e223b176da0e62`, Evidence ID `ev_0fa12df05da6a40cdb36cff99e9f5721df7ae5f510cb2b95fbf24747eb95b8b7`. Included by reference in the parent common fresh receipt manifest; raw native output is not copied into this repository.

Fresh raw JSON `017-procedure_assembly-0x004ca310.json`: SHA-256 `93900bd2d9cd323408e077c89e4f306c86c473b74f710b8eba14cc2f0592bb91`, Evidence ID `ev_4a0332ab6bdfc34300128db08e22a9b778436d6f2713333ca74f8af62430dd40`. Included by reference in the parent common fresh receipt manifest; raw native output is not copied into this repository.

## Ultimate identity and rank limits

The dictionary entry `VGRE-ability-slot-ultimate-identity` already records 57 hero resources / 255 embedded abilities and 18 heroes whose selectors differ from 0/1/2. Ringo C's Hellfire Brew ultimate identification has resource/localization evidence and initial slot2/key `0xcad52059`; Krul C key is `0xee35beb6`. These are build-specific examples. A C suffix, slot2, nominal rank cooldown, or temporal proximity alone is insufficient for generic ultimate identification. Ringo 90/80/70 and Krul 80/70/60 are learned rank1..3 property values, not validated running timer starts. Krul first sync config0 versus nominal base80 already refutes base==every-sync-config.

The external `ultimate-cloud-analysis` artifacts named in the catalog were not available in the supplied raw HUD directory and were not revalidated here. Catalog claims remain catalog-attributed rather than fresh binary findings. H5810 was previously inspected context, not an independent holdout; its lone slot0/operand4 0429 pattern supplies no general rank/slot diversity.

## Archived input hashes

Directory (read only): `D:\VG_EVAL\rea-tools\cooldown-hud-20261015-tty`. Hashes bind raw JSON files; quoted conclusions are summarized rather than reproducing full disassembly.

| Raw input | SHA-256 | Evidence ID |
| --- | --- | --- |
| `08-procedure_references.json` | `3f5154517b0bc2040b52dfbaa95305e02c406216de3af20837a08e76649037a6` | `ev_a177ddff1b041c11c4461699547342113849227e9bb9e8df72a2cf86bcc2371c` |
| `09-procedure_pseudo_code.json` | `0bc9cf7de907a5229efcf51f7c001281713bbfce5f773c009af39e35f31d6564` | `ev_0f42d9bf6a503b93fb96f29dc31ca7c32c11a20c0405364ba22035b5600428c7` |
| `11-procedure_pseudo_code.json` | `dd7d8aea6c6f50989d122dc9c58f163ed756cbf63b213ba3204027ef0ba2cfb6` | `ev_5111795e74917374fa7d6de597cd94cedc76db0d9983a118729f3c2316322db3` |
| `12-procedure_pseudo_code.json` | `61322e959f1ece5307267727017cc6f9c12a17708c17b5ffcc7289608c204305` | `ev_ecdb4327abda7d1550ecbf90e8d7e1aa29a45b34b447d44c31ed80e57ebeccc0` |
| `13-procedure_assembly.json` | `152c1e6ea3bd9e90cad37c051fef8f6605df2ea728677fa892ed2f0f68348ad3` | `ev_f73bd2b0a5818659e51c8a41c5a3553807c168f833e6b2722d6d74ce4bc8ec19` |
| `14-procedure_pseudo_code.json` | `3f20ead7470c311cbce88dd987a2009b5a913d313ea07f03093259fba1572790` | `ev_5d4a29a50d8d3e29b6c2e4d57c7985409a7ac4ea63a57422324ef8e937f7a672` |

Repository basis: [timer correction](COOLDOWN_TIMER_RESOLUTION_2026-10-15.md), [event boundary](COOLDOWN_EVENT_FIELDS_2026-10-14.md), [identity/lifetime](evidence/2026-10-14-cooldown-followup/ability-identity/IDENTITY-LIFECYCLE.md), [clock/HUD effects](evidence/2026-10-14-cooldown-events/CLOCK-HUD.ko.md), and [dictionary index](re_dictionary/INDEX.ko.md). No countdown reducer, identity enrichment, source/version promotion, or server-final-value claim is justified by this review.

Fresh closure input `028-procedure_assembly-0x0052aea0.json`: SHA-256 `fb49dd697aa76a4e67b38111f45c7424e676868bd4c827ca5abe8f04dd5e0c38`, Evidence ID `ev_b238bbac21d29c0e6251dca0aa589afcc56b390ec4a7a88dca35cb94c26cfe14` (parent common fresh manifest).

Fresh closure input `029-procedure_pseudo_code-0x0095dd50.json`: SHA-256 `1514c4d1b8f80b6644774bb984e51de993c8988dc5cff67928114542d23d051f`, Evidence ID `ev_c1fb3f0709dbb2c12f3e999ead9537fd160a017f91747149dbfdde2331f0fddc` (parent common fresh manifest).

Fresh closure input `030-procedure_pseudo_code-0x0095dcf0.json`: SHA-256 `93451c3140e62325810396a26767de167662ba9f5012d6b7d4bc1d98ab4b2533`, Evidence ID `ev_2e94f72e26993f691f4ab432e95f629b2090db390d7ce506faf0e6311c49d678` (parent common fresh manifest).

Fresh closure input `031-procedure_pseudo_code-0x0095cf10.json`: SHA-256 `ac1c4a2a7457857da1bc6907c4adf4e1198a203a78d7ed366fece2860a836fc3`, Evidence ID `ev_e9cc2e095812ade9b1ea8a54445450569ac5df2d98a37b8c13061e4ad5cdd819` (parent common fresh manifest).

Fresh closure input `032-procedure_pseudo_code-0x0095cd10.json`: SHA-256 `3c2b9c4eafd9411f38253153d1ece0e3fba35d44c50c123d463011b23df4c1f9`, Evidence ID `ev_e8634b3aa686ec1001cd2fb0a1665530d839686b2049de123c5d4e980b4b0fbc` (parent common fresh manifest).

Fresh closure input `033-procedure_pseudo_code-0x009401f0.json`: SHA-256 `f8e98861a7a435775dce3cb4cdaab168f89df42fc2c97c5972100bb5cdbb7950`, Evidence ID `ev_ecf41fef30e39579535609934446bf45da050ecf5ee8f7d102341ea63827425c` (parent common fresh manifest).

Fresh instruction/predicate input `043-procedure_assembly-0x0095cf10.json`: SHA-256 `5390511cb88e628f1a8bb8ef92e0f9831e4c6ae705f5c4dfb450d90d37a4899b`, Evidence ID `ev_684757fc0aa5eeddf0df100ff3f6ac53c269328a72a349372177c4d0764e258d` (parent common fresh manifest).

Fresh instruction/predicate input `044-procedure_assembly-0x0095cd10.json`: SHA-256 `4ef7f34dbba3e38eb4b0fdcfd8f9eec5a2c547dd967bccc8ec2f48c51d964fde`, Evidence ID `ev_cc99a485ced2a47962db17316d03c413aacc4f21d8066fae1a6e38996ae2ce93` (parent common fresh manifest).

Fresh instruction/predicate input `049-procedure_pseudo_code-0x0093d4a0.json`: SHA-256 `210104d66412318ef931030062a7880cf84ceb3630f054fea89375a578ddc792`, Evidence ID `ev_fde21a3400bf8176c36d6793544c4e9152e8e50e6dc5b3c7cedb6098b0065a26` (parent common fresh manifest).
