# Respawn/recall caller follow-up, 2026-10-16

## Result and scope

This read-only review closes a documentation gap between the known respawn constructor call sites and the existing receiver jump-table evidence. Fresh exact-build exports now close the selected respawn clone/enqueue path and identify concrete type-4 request constructors. They do not recover an authoritative respawn producer or accepted recall request. No Ghidra/REA process, live client, binary modification, project modification, external write, or commit was performed. Existing actor-reset and recall-stub findings are not new findings here.

Addresses are PE32 preferred VAs at base `00400000`. The historical dispatcher-coverage receipt identifies reference executable SHA-256 `659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`. The respawn report identifies LAA executable `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`. These identities must remain distinct; the repository provenance entry documents their relation. The follow-up below independently verified the LAA executable identity and selected mapped bytes.

## Exact table path, reconstructed from committed evidence

The committed assembly export shows `004d02a5` subtracting `03ea`, `004d02aa` comparing the result with `a6`, `004d02b5` loading one index byte from `004d51e4 + result`, and `004d02bc` jumping through `004d5000 + index*4`. The coverage JSON supplies these selected entries:

| Opcode | Input index | Index-byte VA | Byte value | Target-word VA | Receiver target | Constructor call site |
|---|---:|---|---:|---|---|---|
| `0432` | `48` hex | `004d522c` | `3b` hex / 59 | `004d50ec` | `004d252d` | `004d25d5` -> `00819f70` |
| `0433` | `49` hex | `004d522d` | `3c` hex / 60 | `004d50f0` | `004d25fc` | `004d2651` -> `0081c430` |

Index-byte and target-word VAs above were first derived from the exported table bases and recorded indexes, then directly verified against mapped original LAA PE bytes as described below. The existing receiver C shows input `param_1` already advanced past the two-byte opcode: `0432` copies 16 payload bytes and converts actor ID plus three float words; `0433` copies 8 and converts actor ID plus one float. The output is an action object forwarded through `0092c240`, not a demonstrated local timer-expiry producer. For `0433`, the branch reaches that forwarding path through shared label `004d030c`.

The separate `0092c240` assembly is exact about the next boundary: it invokes action vtable slot `+0c` with argument `020db890`. That is not itself the apply slot `+08`. The fresh follow-up below recovers the `+0c` clone/enqueue implementations; receive dispatch remains distinct from immediate application. This is consistent with the existing shared replay/receive queue research; it is not a newly established direction or runtime execution claim.

## Independent original-PE verification

`python -B -m vg.research.verify_respawn_pe <original-LAA-executable>` completed successfully. The standalone standard-library verifier rejects any SHA-256 except the selected `d6717c...` executable, checks x86 PE32 headers, maps preferred VAs through file-backed PE section data, and emits only identity, decoded addresses/indexes and bounded span hashes. It executes no native code and modifies no input. Structured output is [RESPAWN_CALLER_PE_VERIFICATION_2026-10-16.json](RESPAWN_CALLER_PE_VERIFICATION_2026-10-16.json).

Both selected index bytes, receiver target words, and direct relative constructor calls matched the earlier table reconstruction. Direct reads also establish the next virtual targets without claiming their bodies have been analyzed:

| Action | Vtable | Apply `+08` | Forwarding `+0c` | SHA-256 of first 16 vtable bytes |
|---|---|---|---|---|
| ActorRespawn | `0127c6d0` | `0094c950` | `0092d820` | `3f8b7ae0e11fdaf01ada26acd6a13f257a6839b70371368adb8560e09b38cf99` |
| StartRespawnTimer | `0127cc30` | `00950c80` | `0092f4c0` | `d64ef711bf0b8eab98bf911ae1c8d334f606c49cf2fc6c8aef938783427995c8` |

Thus `0092d820` and `0092f4c0` are concrete next extraction targets. The fresh exports below establish their clone/enqueue bodies; the file pointers alone did not prove those semantics or a runtime call. Reading the two selected relative-call instructions only validates their known sites; it is not an exhaustive caller scan.

## Export completeness is a concrete blocker

The newer committed `replay-clock/pass1/004cfec0.txt` declares body ranges `004cfec0..004d02c2` and `004d4fe3..004d4ffd`. Both selected receiver targets and constructor call sites fall outside those ranges. The export still contains decompiled switch material, but its instruction listing ends at the indirect jump and resumes at the epilogue. Therefore an assembly-only caller search over this exported body will omit the respawn branches. An apparent missing caller here is an export/function-boundary limitation, not evidence that a path is unreachable.

Read-only recursive text searches of existing JSON exports under the experiment/session directories in `D:\VG_EVAL\rea-tools` (excluding installed Ghidra/JDK trees and `decoder` repository copies) found no occurrences of `4cfec0`, `4b7db0`, `59bc50`, `92c240`, `4d51e4`, or `4d5000`. Repository copies under decoder contain the historical evidence, not independent new extraction. This bounded search does not establish absence from the binary or from all external research directories.

## Fresh exact-build closure: clone/enqueue and type-4 requests

The parent obtained fresh REA/Ghidra 12.1.4 exports in the isolated ephemeral analysis session; this reviewer read those exports without running another analysis process. Their structured subjects identify the same LAA SHA-256 above. The cloned object and queue operations are now concrete:

- `0092d820` allocates `0x20` bytes with alignment operand `4`, copies source header `+4/+8/+0c`, assigns ActorRespawn vtable `0127c6d0`, copies actor `+10` and position `+14..+1c`, then calls `0092f720` at `0092d86d`.
- `0092f4c0` allocates `0x18` bytes with alignment operand `4`, copies the same header, assigns StartRespawnTimer vtable `0127cc30`, copies actor `+10` and timer word `+14`, then calls `0092f720` at `0092f503`.
- Assembly confirms these calls restore ECX from the incoming queue argument (`0092d85f`, `0092f4d3`), while the clone is the pushed argument. Combined with the previously verified `0092c240` argument `020db890`, these are cloned actions inserted into that queue object. Existing committed `replay-clock/pass5/0092f720.txt` supplies the insertion body: rewrites links at clone `+4/+8`, updates queue endpoints/current insertion pointer `+18`, and increments queue `+0c`, under calls `00976cc0/00976cd0`. Fresh `038` corroborates the insertion instructions. Fresh `039` closes the consumer dispatch boundary: `00931bd0` starts at queue head `020db894`, sets the current insertion pointer `020db8a8`, and tests action byte `+0c` at `00931c28`. A nonzero byte calls vslot `+08` directly at `00931c40`. A zero byte calls vslot `+04` at `00931c30`, then calls `+08` only when global `0209e204` is nonzero. It walks links at `+4`, later calls destructor slot `0`, and clears queue links/count. Received respawn/timer branches set `+0c=1`; cloning preserves that flag, so their selected queue path reaches the known apply slot. Local request constructors initialize the flag to zero, so their selected path reaches serializer `+04` first. This establishes static possible dispatch, retaining each apply body's own preconditions; it does not prove runtime invocation or transport transmission.

For recall's runtime type `4`, fresh `0059bc50` pseudocode and assembly identify the selected constructors precisely. At `0059bdef` it obtains selector `004a8c20`; selector equal to `1` calls `00529e80` at `0059be06`, otherwise it calls `0081c140` at `0059be20`. Both paths obtain their constructor operand through `00450c00`, then call `0092c240` at `0059be30`. The decompiler labels `00450c00` as a gloox accessor; that imported/aliased symbol name is not evidence of its gameplay semantics. The selected runtime Withdraw ability follows the existing ability path; the item branch documents the shared handler and must not be relabeled recall.

Fresh constructors make the action classes and operand placement explicit. `0081c140` assigns ActionRequestActivateAbility, initializes `+10/+14` to `ffffffff`, zeros `+18/+1c/+20`, stores its one-byte input at `+24`, and writes `3` at `+28`. `00529e80` assigns ActionRequestActivateItem, sets `+10=ffffffff`, input at `+14`, default position words from `020ed134/020ed13c` at `+18..+20`, and `3` at `+24`. These are local construction-and-queue facts; serializer selection, sending facade gates, server acceptance, and successful channel start remain separate evidence. Existing ability/item request schema research may contextualize them but this follow-up does not assign an outgoing recall opcode solely from the class name.

Fresh selected request bodies narrow that boundary further. The decoded request vtables are ability `0127cb58`: serializer `0094c1a0`, apply `00950340`, forwarding `0092f170`; item `0121a9b4`: serializer `00529ff0`, apply `00450910`, forwarding `00529f80`. Ability serializer `0094c1a0` requires literal `0209e204==0` and resolution of the local actor obtained via `00939790/00857970`. For action mode `0` or `3` it invokes `0095c230(action+14, action byte+24)`; the type-4 ability constructor sets mode `3`. Its apply `00950340` instead requires `0209e204!=0` and a resolved action actor ID, then dispatches `onRequestActivateAbility` callbacks. The selected item serializer calls `0095bda0(action+14)` for mode `3`; item apply `00450910` is an empty return in this client. Thus the selected local recall request is concretely a queued ability-request action whose zero flag selects serializer behavior and mode `3` selects `0095c230`, rather than a completion action. These four bodies do not independently establish network delivery or server acceptance. The final selected helper/formatter slice below binds this route to the shared networking/replay facade.

The final selected slice establishes a bounded outgoing recall-request chain: `0095c230` writes `htonl(action+14)` and action byte `+24` into a five-byte payload, passing it with formatter flag zero to `008181c0`. That formatter sets opcode `0411`, content length `7` (opcode plus five payload bytes), and calls `004cfea0`. Its plain-frame branch is corroborated by `057` assembly: copy five bytes at `00818211`, then pass total frame length `9` at `008182a1` and call facade wrapper at `008182a4`. An optional transform object `020e7344` with flag zero selects a separate framing branch; the plain-frame size must not be generalized across that branch. `004cfea0` calls `004eb3f0`, which invokes selected transport global `01ef0e80` vslot `+30`.

Together with the already established RecallInputCommand -> runtime Withdraw slot lookup -> `heroAbilityRequested(slot,3,0)` path, type `4`, selector choosing the ability constructor, zero request flag, literal `0209e204==0`, and successful local actor resolution, this is a selected client-outgoing `0411` request path for recall. The five-byte payload is specifically the constructor's `action+14=ffffffff` sentinel (four network-order bytes) plus constructor input byte stored at `+24`. The slot comes from the runtime Withdraw pointer lookup, not an invariant slot number; the existing caller has no local guard against lookup result `ffffffff`, and constructor narrowing to one byte must remain explicit. The sentinel must not be relabeled as the issuing actor ID. This chain proves possible request generation and facade routing, not packet delivery, server acceptance, countdown start, or completed recall.

The shared-handler item counterpart calls `0095bda0`, then formatter `00813dc0`, selecting opcode `0448` with four payload bytes (content length `6`). It does not replace the selected ability recall path. Fresh selector `004eb2d0` installs KindredNetworking for argument `0`, KindredReplay for `1`, into `01ef0e80`. Fresh assembly `062` confirms networking vtable `01217974` and replay vtable `012179b8`; fresh four-byte read `063` at replay `012179b8+30=012179e8` decodes pointer `004eb5d0`. Existing catalog transport-slot evidence links networking vslot `+30` to `004eb580`; the replay vslot linkage is independently corroborated by the fresh read above; fresh bodies corroborate that `004eb580` gates `00984ba0` behind `009811f0` and returns failure on rejected work, while `004eb5d0` merely returns `1` without send work. A successful facade/replay return therefore cannot be treated as network transmission or recall acceptance.

Export limitations remain visible: `052/053` formatter pseudocode warns about stack tracking; `057` is the selected ability formatter assembly corroboration. `058` serializer assembly includes the guard and indirect jump but omits its switch-case instruction ranges; the mode-3 branch is supported by fresh pseudocode `045` and helper `050/059`, not falsely claimed as covered by that shortened instruction listing. No further extraction is required for this bounded conclusion.

The fresh incoming-reference query for `009572b0` returns 26 entries because it includes references into the full body; only one targets the entry: call `0094c964` in apply `0094c950`. The other listed entries are internal control-flow references. The incoming query for `0094c950` returns one DATA reference at `0127c6d8`, its vtable slot. These exact query results corroborate the known selected caller and vtable use. They do not certify all indirect callers, runtime reachability, or a server/local timer producer.

The bounded selected request/transport route is now closed. Accessor names, complete runtime queue order, authoritative server processing, and accepted recall lifecycle remain outside this result. The original extraction hypotheses below are retained as falsification criteria, with clone/enqueue, conditional consumer dispatch, constructor identity, and selected outgoing request/transport route now resolved. Fresh constructor assembly identifies ability vtable `0127cb58` and item vtable `0121a9b4`; the selected serializer bodies and transport route are covered above.

Fresh source receipts (paths relative to task root, retained outside repository; no raw exports copied here):

| Private export | SHA-256 | REA evidence ID |
|---|---|---|
| `private-evidence/005-procedure_references-0x009572b0.json` | `5db510b57a3f3c636882282ad9b4d66fe49c3d70b7a8765f53fdf6c674d15099` | `ev_b011e0a93c358896e114903e62baf0f296da7c24250fc1ade8c8dfb79479aa42` |
| `private-evidence/007-procedure_references-0x0094c950.json` | `65d900379e733e6c54a9641839775c545127001caeff55a09da5016a88c7efe0` | `ev_2275ba4f487fe2c7f1d8541c0f473d0dd52b906a37c15fee494f665bca62be03` |
| `private-evidence/013-procedure_pseudo_code-0x0092d820.json` | `53adb6d622a5158f3700975867517832d4b09b214029019d28f7fafd0deb9d1b` | `ev_db14c650c17965ef789a79cf0499fd519a733053c78bf7ed9bf26590bf1d680c` |
| `private-evidence/014-procedure_pseudo_code-0x0092f4c0.json` | `ec877d5d881e0f0bc665a06d8b572b3f165cc950dfbf8b22788566143b8291ac` | `ev_24f2c1b1161a387103fd348d1f50a308c339d5c8a3daa7283e51600e62136574` |
| `private-evidence/015-procedure_pseudo_code-0x0059bc50.json` | `eb93dd1e619a3cfba2cd3e4af3db8eb4ba03fc532e65e0261753a969cdd17b0b` | `ev_02b1b008dae69f93c579fdc3b37c6f7bfffc721d3d1bc57d6f5428de5f08b3da` |
| `private-evidence/021-procedure_pseudo_code-0x0081c140.json` | `524e5da5e6e7be1522a76d5e499f3961f16d17bf5037aad4a928a8cbb06b404b` | `ev_74d9383a33125f5392f23d360886d8a7c1b76c5c4aef3da48a4462840bb6a6b0` |
| `private-evidence/022-procedure_pseudo_code-0x00529e80.json` | `dd2d9d6ae062d52e3760207508e1c4673f503eb943f69eb892f579dd44ed9725` | `ev_1566f2602d3942e1f4c957fcffd531e1fce1586159bf928ec74d94ce6a46f330` |
| `private-evidence/023-procedure_assembly-0x0059bc50.json` | `cfce7a834bc1a21457b27e5a30bb0d751d2c23a7285ef71fd27d72d82c74a317` | `ev_c032653118695a342abda540b10c3e165b7abc9660dafe887086bbd764a58920` |
| `private-evidence/026-procedure_assembly-0x0092d820.json` | `9d62c4ad50db2d41798b912f1ae6983a591cb9de4cd6baad5bd01d1a4cb5a321` | `ev_3003ffd18d8d788455a0ccaf558845fd8aafc1aff94dbbb8b5652b5efd3df52f` |
| `private-evidence/027-procedure_assembly-0x0092f4c0.json` | `ed06a6ee177e644750d3b22a729416d125b3edaa817eb8e2b1290718a983e092` | `ev_ff9ae5e9e3a5dc7f6956738aa604f7f7e784bc7ba8bd2ca7e78309be74ab7a6f` |
| `private-evidence/035-procedure_assembly-0x0081c140.json` | `4ded0ef75407dede4a329c6916d577d288d32b2b4e249c057ab175e1633177c3` | `ev_92c979851173366f5b49e409a46dce4b25c553f85896026dabae0824d3f22f7c` |
| `private-evidence/036-procedure_assembly-0x00529e80.json` | `2404e02df56ba55a5da5ae2397060e3f01df0a6415a2074f7fccd2b428265d98` | `ev_8e461d235fe1308c50632be8957dd733e2baf38aa34ef9d7a78ee748fab7e3cd` |
| `private-evidence/038-procedure_assembly-0x0092f720.json` | `8714e8d9e31a4bd3e1596043c536ce16c69985a10dfb9c54c34401e4080bd943` | `ev_2912d628643cd0646767a60df013d9a090b6ba13fa46524c31508efe53f85362` |
| `private-evidence/039-procedure_assembly-0x00931bd0.json` | `cd1c6a65cc5cabae9cd974422354f81af70c05a3afc424da1492ca17680ef83a` | `ev_a54c2935df0202678b5ff0572faa2daad5eb3ffe267b24e92d59a3eba6625441` |
| `private-evidence/040-read_bytes-0x0127cb58.json` | `8194d56ee46172c15872350e99a8a210d7e864c1954c518cfaeebc6e1a0280b1` | `ev_f6e51853517b4be9e5f657ebfcc68168184b4f8d5d050dc3dc539988f6097135` |
| `private-evidence/041-read_bytes-0x0121a9b4.json` | `7b0d61a947e57a2f32b6cb1a813a3ff442ea27a9b6e76c616aa38ac6404f8430` | `ev_0af68243b79b665bcb80c94ec01fa759b85aee5525833a9ed332bc9c65dbee7a` |
| `private-evidence/045-procedure_pseudo_code-0x0094c1a0.json` | `4137edf69d924cae1fe19b7250c2032796f64d27aad60fca5a1a4c2b8ac55b80` | `ev_6d1515bf959e51494749dd5704793457dea6a36329843666c3279c190b2fa163` |
| `private-evidence/046-procedure_pseudo_code-0x00529ff0.json` | `01e88fedac4a88131e1364138389c5aa8a1fa92b8340644db40795dfdf8e8f5a` | `ev_3433155e94252d80804371d0de3e20e44f88dc23a9273b3478951bc882e09852` |
| `private-evidence/047-procedure_pseudo_code-0x00950340.json` | `d14d6dd05119cca45def15fde55e83fc7feae1d4024c52bd7b1dadffb597ea9c` | `ev_1cc39d91e873587cf9c2f2c67ad41198e89f524b9198db9bdf126f1cdd172011` |
| `private-evidence/048-procedure_pseudo_code-0x00450910.json` | `94930393dc3652edc2fa26b6bb9e0952a3158704cb5c1278b1d1a19351482ace` | `ev_aa25755c255ad1ad0ac366f322d495f2dff78726706ae535650708739a9d7a97` |
| `private-evidence/050-procedure_pseudo_code-0x0095c230.json` | `295d1f2f38536ac157936af7ea862f5b3d1838ce5d73931c27563bb89469a82a` | `ev_41e7816870f9a4fe97e172be41e4fcd9068f5270adf616e3e6645b5a31ac0356` |
| `private-evidence/051-procedure_pseudo_code-0x0095bda0.json` | `c3cad38327d9145d6e51e2bd6c03b388ece9202dab90c65745ca80b3a1ab0a2b` | `ev_c234f043611324299cbe3f740f107e623a0b104af2c85007ff7be0c698188436` |
| `private-evidence/052-procedure_pseudo_code-0x008181c0.json` | `e341b77bdc28c05da6d63062ab6ff6073d70a87367c6b530fbf29343d2a14364` | `ev_3e7f0e9f894d2f3a3f2934538accb78b498f99452d1bf988800d695abdda1906` |
| `private-evidence/053-procedure_pseudo_code-0x00813dc0.json` | `976644a8bbcb754d670ad35465c120900e15605d75aa8adaaaf50228496ea254` | `ev_d7549c62ffb67a85e5d60d3086faa76dd4f098437d5b16b802007d7448f9ae1e` |
| `private-evidence/054-procedure_pseudo_code-0x004cfea0.json` | `f639ae8df134886aff7510c53c2a3967fd807898b37445d4386185de0e879733` | `ev_d9fd562053642004e03d0ce6d85b1594f61f2a63da4dd0e9ca821c6f913b85bd` |
| `private-evidence/055-procedure_pseudo_code-0x004eb3f0.json` | `90485ce57ef68670c414f51baf879a19da02824672c49c83def173f69f338b7e` | `ev_f98f79864c9a86471abb80e2aebad4a8ff1e1bea84ee0bc676810b15b8e06fce` |
| `private-evidence/056-procedure_pseudo_code-0x004eb5d0.json` | `1f1d2c2d47ab9776b89c4914c35357cfdaae59eee1bf4812bcf1e1d131141a01` | `ev_573c60462b623b80b101ca3a8f41a9b3d82e3985221faf64dced261520a6f130` |
| `private-evidence/057-procedure_assembly-0x008181c0.json` | `ad7bbf1615600aefed1a48c7f55acfa76197b69079f4981b992ba8389f39c4ce` | `ev_c853252db6fae26b5fa66553eb6231bf5e9fb498358d2ff6801334d4f8022554` |
| `private-evidence/058-procedure_assembly-0x0094c1a0.json` | `66bf8fcab4375b0d2facb50c297b2465944d888a7ee5bf46d548d7c40c16406e` | `ev_8dbb4d9956135ea443a9b32cab3f0cab5a30ae2e26af5b07b69470497244f095` |
| `private-evidence/059-procedure_assembly-0x0095c230.json` | `e4aa55e54d87f6c6233a13d952783f91f36f6316cecbc6cb0379e045f42d99a2` | `ev_c25eaafd6f3814246f13b49ba8546b657ed994b173673bc824c9cead9fd5c6d0` |
| `private-evidence/060-procedure_pseudo_code-0x004eb2d0.json` | `30292e757e64529eed9853643cecb8881bda5bbccf7fbc1db5993d1590acef7d` | `ev_393ce092a2fe12876cdd1a5bdb8ca57839f6831e3a528f6208557636ec63faec` |
| `private-evidence/061-procedure_pseudo_code-0x004eb580.json` | `08b637f4ac475fadacec8fdd05ba1811ac5cbefc8cadfa2d8c2e3f13749c81ed` | `ev_6aaf2bafab63288d90bcd659f78a258417b6a7b335d011dc2540ed65946552de` |
| `private-evidence/062-procedure_assembly-0x004eb2d0.json` | `bfa22ce53544836fe85224fc2ee306441f07d31a41e99904ae3e81dd6e183102` | `ev_53874920a95f78d7f5f5313cd8691696d5b1d35bacd913b47646649d50d66b27` |
| `private-evidence/063-read_bytes-0x012179e8.json` | `e352c13f02e7f5b1eacb7589337a70f879a769f037ce70429dfc3e2b404006cd` | `ev_903b2e0fc24f54daa2e7e9bb33e51d8df41f32f8d42b43d4b1a2e022ed850cd6` |


Existing queue-body file SHA-256 (LF checkout): `238322f31b6377ab66525ac88fc40ca99a0cd9586df685071272ad7ceb01685f`.

## Original extraction hypotheses and their final status

1. **Receiver table interpretation (selected bytes verified):** the two opcode entries reach the recorded constructor sites. Falsify by exact-build bytes disagreeing at `004d522c..004d522d`, `004d50ec..004d50f3`, or by contiguous assembly `004d252d..004d2661` contradicting the branch/call mapping. Extract those bounded spans with executable hash and section mapping; avoid trusting a containing-procedure export that excludes them.
2. **Action forwarding (selected clone/enqueue/consumer gate resolved above):** `0092c240` forwards these action types through virtual `+0c`; exact clone/enqueue/apply ordering remains unverified in this follow-up. The vtable words are now verified as `0092d820` and `0092f4c0`; extract their complete target bodies, and references to queue object `020db890`; follow the queue consumer to virtual `+08`, retaining gates and ownership. An implementation applying synchronously would falsify a deferred-queue hypothesis.
3. **Network versus replay origin:** known shared dispatcher use cannot identify a server producer. Extract all code/data references to `004cfec0`, buffered-receive `004b7db0`, and replay caller `004eb4a0` with call-site assembly and argument provenance. Label transport entry and replay entry separately. A receive path calling only recorder or presentation code would require revising the presumed action path.
4. **Recall request direction (selected outgoing ability route resolved above):** `0059bc50` remains the useful unresolved branch target from the existing recall report. Extract its complete body and references, branch on runtime ability type `4`, and follow the actual action construction/serializer/transport call with input slot and targeting-mode provenance. The final `0411` linkage above is based on the selected serializer/helper/formatter chain, rather than name or proximity. A type-4 branch that only changes local selection would falsify a direct outgoing-request claim.

No new gameplay semantics, payload suffix rule, countdown formula, recall-success metric, or production decoder support follows from this review.

## Reproducible local evidence receipts

SHA-256 below hashes exact Git-index blob bytes (LF), obtained with `git show :<path>`. Working-tree line-ending conversion can produce different byte hashes; these are not replacements for external original-file receipts.

| File relative to repository root | SHA-256 |
|---|---|
| `vg/docs/re_dictionary/respawn_recall/REPORT.md` | `4acb1e753422737702a3aca6cb08b3d07001a8392807f64f74a8e87810872871` |
| `vg/docs/evidence/2026-09-09-binary-events/native/dispatcher-coverage.json` | `50167166992c266ec23b0b859551120a40a7bd858c8c9135aef451894e67955d` |
| `vg/docs/evidence/2026-10-04-atlas/function-004cfec0.c` | `871d3ffdfa7d64a2e7e21fc1f68e049bcb83f4f510bee825057da7796bc40867` |
| `vg/docs/evidence/2026-10-14-cooldown-followup/replay-clock/pass1/004cfec0.txt` | `baba37ceed08c000e1b1b17973bb6ade7ea29d276e7b607f522dcdb09a80e89e` |
| `vg/docs/evidence/2026-10-14-cooldown-followup/replay-clock/pass2/0092c240.txt` | `1d328dda2a6bc60b433fb88eacacf7656b0c85220627c073a635732e8a4899dd` |

Verifier SHA-256: `1078489747e8227a5992beb34de7dac9938f1f3d728aea79358b21f1d320801c`. Structured PE-result SHA-256: `d77861582804f94d330adccdc3dd144618263dfae443ee726707f2c6b4ee0ff7`.
