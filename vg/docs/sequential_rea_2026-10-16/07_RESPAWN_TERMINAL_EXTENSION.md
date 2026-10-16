# 7. Respawn initialization and terminal extension

## Starting basis and selected next targets

This extends [revival/recall](04_REVIVAL_RECALL.md) and [results/teams](03_RESULT_TEAMS.md) for the Windows x86 LAA SHA-256 recorded in [README](README.md). The existing result is a conditional nonzero-mode timer-expiry -> queued ActorRespawn -> existing-actor reset path. It does not bind ordinary received0433 to automatic local revival. Terminal request fields, accepted controller transitions, and result presentation likewise remain separate.

The next bounded targets were the mode-global writer, previously unresolved timer-type references00402f25/004ca483, ActionEndMatch clone/vtable references, and state-transition/callback registration. This reviewer read the parent's fresh serialized REA exports; no additional REA session, native execution or code change was performed.

## Actual result: mode initialization and timer reference closure

Fresh014 identifies0095da70 as a byte setter:0209e204=its input. Reference query015 finds one entry-target call at004bffc1 within004bff80. Body035 and assembly063 agree:004bffbf pushes literal0,004bffc1 calls0095da70;004bffd4 then pushes0 and004bffd6 calls transport selector004eb2d0. Thus this supplied client initialization path explicitly selects mode0 and networking transport. This is a static call sequence, not proof it ran in a particular recording, that every global writer was found, or that nonzero mode can never execute. Wider/indirect writes and missing implementation remain outside this bounded query.

Raw read057 resolves00402f25: it is the absolute store instruction inside a short initializer that loads the current value at01e3f840 and stores it into01ef0b44, then returns. It initializes the component type identifier, not a CKinRespawnTimer instance or its+18 pointer. The interior-address pseudocode request018 failed and supplies no function-body evidence.

Interior query019 at004ca483 resolves the already known containing function004ca310. Its timer-type match walks the actor component list, calls remaining-value getter0093b850, and places the result in snapshot data under native-state/other predicates. This is a snapshot **read**, not a nonzero timer+18 write. Re-extracting the whole snapshot routine did not reveal the missing spawn-point initialization at this selected reference.

The reviewed instance writers remain: constructor009588e0 zeroes+14/+18; received apply00950c80 sets+14 and only for a newly created timer zeroes+18; HeroSpawn0094e170 can restore+14 and zero+18. The registered tick00953990 consumes+18 as a pointer to three position words. These selected paths establish no nonzero+18 initializer. That is a precise missing edge, not an all-writers-absence claim. In particular, mode0 initialization plus received timer+18=0 must not be combined with the mode-nonzero expiry branch to invent an ordinary-client end-to-end path.

## Actual result: terminal clone and accepted-state boundary

Fresh020 finds0092df00 referenced at0127c840, ActionEndMatch vtable0127c834+0c. Fresh055 confirms it allocates0x18 bytes, copies header, requested team byte+10 and reason+14, installs that action vtable and calls0092f720. It is a polymorphic clone/enqueue implementation, **not a newly recovered direct terminal producer**. Fresh021 reports vtable references only at constructor store0081a6a7 and clone store0092df32. Query041 resolves the selected constructor to0081a680 despite the requested interior address0081a6a0; its entry-target call is dispatcher004d1682. This bounded reference database result does not exclude inline, indirect, server-side or unrecognized producers.

The separate raw wrapper read058 corroborates literal arguments requested team1/reason0 to004c0e10 at005b74c4. The attempted pseudocode query022 at that call site failed; do not present it as an analyzed whole function or authoritative crystal/surrender producer. Reason0 still has no independently proved universal crystal meaning.

Fresh050 confirms CKinClientGameSession constructor005483c0 registers primary state2 entry00548c90, no state2 tick, and exit005491b0. Reference025 finds the callback's entry-target reference at0054856c, a DATA registration in that constructor. Entry-reference inventories023/024 identify seven primary-transition callers and six secondary-transition callers, respectively; they are not seven/six accepted terminal outcomes. The additional primary caller0054a210 is a selected-actor/presentation path with its own flag checks; its body051 does not establish a new authoritative end request.

The earlier00549620 finding remains intact: request team/reason fields are written before guarded primary2/secondary3 requests. A registered state2 callback establishes what an accepted entry can dispatch; it does not prove that any observed request passed guards, that a repeated request ran the callback again, or that the final rendered banner corresponds to the last overwritten fields. No new winner or accepted-gameplay reducer follows.

## Closure, falsifiers and next measurement

Closed: the concrete client startup caller supplies mode0; the two selected timer-type leads are type initialization and snapshot reading; ActionEndMatch+0c is cloning rather than a new producer; primary2 result entry registration is independently linked. Open: nonzero-mode initialization, valid timer+18 creation, authoritative terminal producer, and accepted transition-to-rendered-result observations.

Falsifiers include a verified nonzero write to0209e204 in a reachable path, a traced nonzero timer+18 assignment on the same component generation, or an independently recovered inline ActionEndMatch construction upstream of cloning. Such evidence would extend these limits rather than invalidate the already observed mode0 call or selected reads. Changed executable hashes, vtable stores or callback registration also require revalidation.

The next matched-build measurement should retain mode writes and their caller, timer owner/generation,+14,+18 validity and initialization, engine delta, queued action header/position and accepted reset/control transition. For a terminal outcome, retain the originating action/caller and raw team/reason, controller states before/after, guard decision, state2 callback invocation and banner inputs at that invocation. Repeated contradictory requests and already-state2 requests are required counterexamples to last-request=accepted-result assumptions. No timing-nearest heuristic, constructor-only absence argument or screen-color mapping substitutes for these edges.

## Fresh source receipts

Files below remain under task-private `private-evidence/extended-rea`; raw exports are not copied into this report. SHA-256 binds each complete JSON envelope, including its exact-build subject and REA evidence identifier. The parent's common acquisition receipt may index the same files.

| Export | SHA-256 |
|---|---|
| `014-procedure_pseudo_code-0x0095da70.json` | `0a00c10423e8d6a4e8ed796ed0069b54c3d9e84c9eed2ccb5fa0290abfd06e67` |
| `015-procedure_references-0x0095da70.json` | `dbbd21f6b334f8c2d33ebde9ea336b87baf6252d1f7ff7eebcd3c966db11eae1` |
| `019-procedure_pseudo_code-0x004ca483.json` | `4c474d100a5e768ce9eb74c342a2df2f908cec795e33e6163f91ac462921ab9e` |
| `020-procedure_references-0x0092df00.json` | `26721d3c08d2119861908365f2a6671ad7b9ef2515eb26979fd1da1a14bf8bb2` |
| `021-xrefs-0x0127c834.json` | `1adaf5be97cf31d760bc2d3a008ce17c8316d76140749ce3e3577348f29d2de1` |
| `023-procedure_references-0x00549f60.json` | `0969f34cb416a2cb728409f58ae512aad06b858f2fd088a10703ce520cf70f07` |
| `024-procedure_references-0x0054a030.json` | `fb23fe13bac3c660f8eac7463fd31fddf592be748963e989c0984d6b50a6187e` |
| `025-procedure_references-0x00548c90.json` | `76df36429bf2a0bd8af5b25458a8691f17eb9ac6389a492796caad7b0efe2875` |
| `035-procedure_pseudo_code-0x004bff80.json` | `884c5d34bb3b1144d16300b75a7e57fb7097884971cc61080476bea7919adc4d` |
| `041-procedure_references-0x0081a6a0.json` | `732929b26d8356d249f398de31d0d7e585b69a5ed317fc730c40fb3b1383d647` |
| `050-procedure_pseudo_code-0x005483c0.json` | `57e2d2437688911b29bf2caf1d40c2d71622a13cf3c55751daa27045866b8d4f` |
| `051-procedure_pseudo_code-0x0054a210.json` | `b8b6da4309ceb944aac0ea9d14382022d005202c50365663f053cc3cd4726b30` |
| `055-procedure_pseudo_code-0x0092df00.json` | `15b503c3b6d4bb1b4563f3e76e45f2cffb9d2b0164f7fdc335a3430feb02f5fb` |
| `057-read_bytes-0x00402f10.json` | `befbce36f4e8e1d7e24e72b92ea07c9985ac90e70c0e8076f48ef13e6be77edf` |
| `058-read_bytes-0x005b74b0.json` | `d36a6815936e0220012243b6ecec07e8ae7b7def54f490a2a49da799018566f9` |
| `063-procedure_assembly-0x004bff80.json` | `b0a4fe3ac816d1ca6586ff74978475ad2535d1a46507d7bea1be748fa8ad45ee` |
