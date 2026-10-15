# Vainglory RE 기능 사전

이 파일은 catalog.json에서 생성됩니다. 직접 수정하지 말고 원본 catalog를 갱신하세요.

기준 checkout: `65bab83` · 갱신: 2026-10-15 · 항목: 120

검토된 기능 묶음과 중요한 정정만 담았습니다. 기존 evidence 전체를 검증 완료로 승격한 목록이 아닙니다.
정적 명령 검증, synthetic test, 개발 corpus 관측, runtime 관측은 서로 다른 증거입니다. semantic confidence가 높아도 서버 권위나 live 실행은 증명되지 않습니다.
raw binary/replay, 실제 player UUID, 새 raw disassembly는 포함하지 않습니다. 외부 원문은 hash-bound reference로만 남습니다.

## 빠른 검색

```sh
python -B -m vg.research.dictionary search 쿨다운
python -B -m vg.research.dictionary search --opcode 0449
python -B -m vg.research.dictionary show VGRE-health-impact-prefix
python -B -m vg.research.dictionary validate --check-index
```

외부 근거의 미해결은 검증 성공과 구별됩니다. 실제 source를 가진 사람은 `--external-root research=/path/to/research --external-root shared=/path/to/shared --require-external`을 validate에 추가하세요.

## 기능별 목차

- 파일·빌드 출처: [Windows 파일 해시와 주소 기준](#vgre-provenance-pe-variants)
- 프레임·시간 소유권: [Native buff record prefix and historical mismatch](#vgre-buff-record-layout-boundary), [VGR 레코드 경계와 시각 소유권](#vgre-vgr-record-framing)
- actor·roster·계정 경계: [identity authenticated account from roster](#vgre-deepening-identity-authenticated-account-from-roster), [identity external string mastery cache](#vgre-deepening-identity-external-string-mastery-cache), [identity mastery response cache](#vgre-deepening-identity-mastery-response-cache), [identity mastery rpc method](#vgre-deepening-identity-mastery-rpc-method), [Actor 리소스 종류와 네이티브 분류](#vgre-entity-actor-resource-kind), [040b 삭제 액션과 지연 정리](#vgre-entity-destroy-lifecycle-observation), [03e9 기록 선택 actor와 팀](#vgre-identity-bootstrap-selection), [03ee 외부 문자열의 관측 이력](#vgre-identity-external-string-history), [한 기록 family와 unknown completeness](#vgre-identity-recording-family-validation), [03ee 명단의 네이티브 식별 계약](#vgre-identity-roster-native-contract), [생성 관찰·스킨 값·실제 수명 분리](#vgre-identity-spawn-skin-observation)
- 종료·승패·완전성: [terminal banner reason keys](#vgre-deepening-terminal-banner-reason-keys), [terminal clock lifecycle](#vgre-deepening-terminal-clock-lifecycle), [terminal gold final refresh cache](#vgre-deepening-terminal-gold-final-refresh-cache), [terminal last request is final result](#vgre-deepening-terminal-last-request-is-final-result), [terminal primary entry](#vgre-deepening-terminal-primary-entry), [terminal repeated field callback divergence](#vgre-deepening-terminal-repeated-field-callback-divergence), [03f1 요청 팀과 상대 승리 boolean](#vgre-result-request-relative-win)
- 아이템·설정·소유: [타격·수정 강화제 지속시간 갱신과 조건부 능력치 선언](#vgre-infusion-refresh-and-stat-declarations), [아이템 인스턴스·수량·인벤토리 갱신](#vgre-inventory-native-instance-state), [아이템 사용 요청과 모드별 메시지](#vgre-item-activation-envelope), [설정 mode와 선택 제스처 분리](#vgre-item-configuration-selection), [회복 아이템·정찰 카메라의 키와 생성 선언](#vgre-item-consumable-keys-spawn-declaration), [판매 요청과 구매 거절 알림의 한계](#vgre-item-sell-reject-prefix), [Buff_JungleMinion_5v5_CrystalOrb](#vgre-jungle-definition-1066), [Buff_JungleMinion_5v5_CrystalOrb_Lockout](#vgre-jungle-definition-1067), [Buff_JungleMinion_5v5_CrystalOrb_Effect](#vgre-jungle-definition-1068), [Buff_JungleMinion_5v5_WeaponOrb](#vgre-jungle-definition-1069), [Buff_JungleMinion_5v5_WeaponOrb_Effect](#vgre-jungle-definition-1070), [Buff_JungleMinion_TreeEnt_Restore](#vgre-jungle-definition-220), [Buff_JungleMinion_TreeEnt_Barrier](#vgre-jungle-definition-221), [Buff_JungleMinion_TreeEnt_Immobilize](#vgre-jungle-definition-222), [Buff_JungleMinion_TreeEnt_RootField](#vgre-jungle-definition-223), [Buff_JungleMinion_TreeEnt_CancelRootOnDeath](#vgre-jungle-definition-224), [Buff_JungleMinion_CrystalMiner_CrystalAmp](#vgre-jungle-definition-225), [Buff_JungleMinion_CrystalMiner_Defense](#vgre-jungle-definition-226), [Buff_JungleMinion_CrystalMiner_Empowerment](#vgre-jungle-definition-227), [타격 강화제 (Weapon Infusion)](#vgre-jungle-definition-283), [수정 강화제 (Crystal Infusion)](#vgre-jungle-definition-284), [Jungle visual identity](#vgre-jungle-visual-identity), [Orb acquisition stub boundary](#vgre-orb-acquisition-stub-boundary)
- 쿨다운·clock·timer: [능력 슬롯과 궁극기 표시 순서](#vgre-ability-slot-ultimate-identity), [buff lifetime create reapply stack dispatch](#vgre-buff-lifetime-create-reapply-stack-dispatch), [buff lifetime removal expiry dispatch](#vgre-buff-lifetime-removal-expiry-dispatch), [만료 초과량과 재생성 타이머의 다음 순회](#vgre-cooldown-expiry-overshoot-stage4), [소유자·키 기반 공유 쿨다운 상태](#vgre-cooldown-owner-key-identity), [기록 시각만으로 쿨다운을 복원할 수 없는 이유](#vgre-cooldown-replay-time-identifiability), [타이머 본체 역참조와 HUD 숫자 변환](#vgre-cooldown-timer-reference-hud), [쿨다운·충전 이벤트의 원시 필드](#vgre-cooldown-wire-fields), [combat packed override](#vgre-deepening-combat-packed-override), [cooldown buff capacity lifecycle](#vgre-deepening-cooldown-buff-capacity-lifecycle), [cooldown buff duration modifiers](#vgre-deepening-cooldown-buff-duration-modifiers), [cooldown effective stat flags](#vgre-deepening-cooldown-effective-stat-flags), [cooldown two state blocker selector](#vgre-deepening-cooldown-two-state-blocker-selector), [scout cam upgrade modifier declarations](#vgre-deepening-scout-cam-upgrade-modifier-declarations), [게임 시계 앵커·재생 누적·화면 시간](#vgre-replay-game-clock-anchor-display)
- 게임 요청과 전송: [combat 041a](#vgre-deepening-combat-041a), [combat 041b](#vgre-deepening-combat-041b), [combat 0425](#vgre-deepening-combat-0425), [0411/0412/0413 능력 요청](#vgre-request-ability-layouts), [0448/0449/044a 아이템 요청](#vgre-request-item-layouts), [이동 3종과 공격 대상 선택](#vgre-request-movement-attack), [게임 요청 compact frame](#vgre-request-plain-frame), [전송 facade와 replay no-send 분기](#vgre-request-send-replay-boundary)
- 플랫폼 JSON schema: [authenticate는 executeCommand 인수](#vgre-platform-authenticate-command), [첫 RPC parameter는 credential일 수 있음](#vgre-platform-credential-capable-identity), [플랫폼 JSON envelope](#vgre-platform-json-envelope), [lobby·party·pending의 서로 다른 schema](#vgre-platform-lobby-party-pending), [명명된 matchId와 품질 telemetry](#vgre-platform-match-state-quality), [startSessionForPlayer 11개 값](#vgre-platform-start-session)
- Android 패키지와 routing: [connect hook은 원래 목적지 관측](#vgre-android-match-socket-observation), [원본과 VGNA의 한정된 변경 범위](#vgre-android-matched-base-delta), [region bootstrap은 고정 routing](#vgre-android-region-routing)
- VGNA replay upload: [identity event의 출처와 응답](#vgre-upload-identity-events), [continuous upload policy 연결은 미확정](#vgre-upload-policy-bounded-gap), [terminal_scoreboard는 entity→hero만](#vgre-upload-terminal-hero-only), [VGNL 68-byte transport header](#vgre-upload-vgnl-frame)
- client 산술·HUD·stub: [critical 산술의 mode gate와 RET 경계](#vgre-combat-critical-stub), [4-array 유효 stat 계산](#vgre-combat-effective-stats), [방어 계산은 last-hit HUD 추정](#vgre-combat-hud-attack-estimate), [property scaling과 TooltipDamage](#vgre-combat-property-tooltip)
- 받은 HP와 표시: [041e 실제 resource 변경 operand](#vgre-health-impact-prefix), [받은 action은 apply로 직접 진입](#vgre-health-incoming-dispatch), [041d SET/ADD와 음수 SET 정정](#vgre-health-resource-set-add), [impact·HP·보호량·표시량 분리](#vgre-health-split-display), [Treant duration extension and gated heal](#vgre-treant-duration-extension-and-heal)
- action↔impact의 제한된 연관: [아이템 instance는 actor와 함께 묶기](#vgre-correlation-item-instance-scope), [시간·actor 근접성은 인과 키가 아님](#vgre-correlation-no-causal-key), [play actor/target/slot과 불투명 suffix](#vgre-correlation-play-fields), [creature classification native_kind_flags](#vgre-creature-classification-native-kind-flags), [creature credit generation_checked_link](#vgre-creature-credit-generation-checked-link), [creature credit retained_hero_reference](#vgre-creature-credit-retained-hero-reference), [creature cs coincidence_boundary](#vgre-creature-cs-coincidence-boundary), [creature death raw_source](#vgre-creature-death-raw-source), [creature objective distinct_definitions](#vgre-creature-objective-distinct-definitions), [combat target storage](#vgre-deepening-combat-target-storage), [ambient gold payout declaration](#vgre-reward-ambient-gold-payout-declaration), [bounty multiplier](#vgre-reward-bounty-multiplier), [goldshell distance provider](#vgre-reward-goldshell-distance-provider), [individual resource apply](#vgre-reward-individual-resource-apply)
- 구현 상태: [영웅 레벨 상한과 성장 효과](#vgre-hero-level-effects), [영웅 레벨 변화 액션](#vgre-level-action-delta), [Downgrade and conditional refund](#vgre-skill-downgrade-refund), [Gated skill investment and point spending](#vgre-skill-investment-apply), [Overdrive equality and property bonus differ](#vgre-skill-overdrive-condition), [Rank bits, base rank and prerequisites](#vgre-skill-rank-prerequisite), [Display slots and runtime identities](#vgre-skill-slot-selection), [Absolute skill ranks restored by HeroSpawn](#vgre-skill-snapshot-restore), [Skill upgrade request is separate from application](#vgre-skill-upgrade-request), [레벨 내 경험치와 표시 비율](#vgre-xp-progress-threshold-ui)
- status_effect: [Separate movement attack skill and item gates](#vgre-status-action-specific-gates), [Metadata and identity based blockers](#vgre-status-buff-blocker-matching), [Cleanse metadata filtered cancellation](#vgre-status-cleanse-filtered-queue), [Display records are separate from logical flags](#vgre-status-display-native-distinction), [Per-source gameplay flag lifecycle](#vgre-status-flag-contributor-lifecycle), [Selected named status masks](#vgre-status-named-factory-masks), [Movement modifier maximum per category](#vgre-status-slow-max-category)

## 파일·빌드 출처

### VGRE-provenance-pe-variants

**Windows 파일 해시와 주소 기준**

현재 LAA 이미지와 과거 기준 이미지는 구별한다. 현재 이미지의 PE LAA 비트를 메모리에서 해제하면 과거 해시가 재현되며, 변경 위치는 파일 오프셋 390 한 곳이다.

- 상태: supported · 의미 확신: high · 검증: file_hash, independent_review
- 경계: client_native / not_applicable / static_only
- 정확한 파일: `win-x86-laa`, `win-x86-reference`
- 한계: 이 관계는 H5810 기록기 빌드를 증명하지 않는다.
- 한계: 동일한 코드 구간 해시는 전체 변형 실행 파일의 동일성을 뜻하지 않는다.
- 근거: [src-pe_relation](#src-pe_relation) · entire JSON
- 근거: [src-network](#src-network) · Scope and provenance


## 프레임·시간 소유권

### VGRE-buff-record-layout-boundary

**Native buff record prefix and historical mismatch**

Native043e formatter emits16-byte payload;043f emits34. Common prefix carries raw target/source actor IDs, half-float duration, instance and buff-definition index.043f adds stack count and unnamed extra fields. Historical043e22 and043f38 variants remain unsupported; matching prefix indices are diagnostic only.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- Opcode: `043e`, `043f`
- 함수/위치: `0x008145c0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x008144c0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x004d34d8` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x004d357d` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00819fe0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 필드: target_actor_raw = payload_after_opcode+0 (be_u32); Exact native prefix only; no historical extended-layout promotion.
- 필드: source_actor_raw = payload_after_opcode+4 (be_u32); Exact native prefix only; no historical extended-layout promotion.
- 필드: duration_raw = payload_after_opcode+8 (be_f16); Exact native prefix only; no historical extended-layout promotion.
- 필드: instance_raw = payload_after_opcode+10 (be_u32); Exact native prefix only; no historical extended-layout promotion.
- 필드: buff_definition_index_raw = payload_after_opcode+14 (be_u16); Exact native prefix only; no historical extended-layout promotion.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Observed records include repeated section snapshots; counts do not mean unique acquisitions or lifetimes. Action eligibility/override can still reject or replace ordinary apply.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-vgr-record-framing

**VGR 레코드 경계와 시각 소유권**

각 레코드는 BE float32 timestamp, BE uint32 content_length, BE uint16 opcode, payload 순서다. content_length에는 opcode 2바이트가 포함되며 다음 레코드는 현재 시작+8+content_length다. timestamp는 해당 레코드의 헤더에 속한다.

- 상태: corrected · 의미 확신: high · 검증: corpus_audit, static_instructions, synthetic_tests
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-reference`
- 함수/위치: `0x004ca130` (win-x86-reference, preferred_va, selected source-documented function); `0x004eb4a0` (win-x86-reference, preferred_va, selected source-documented function); `0x004cfec0` (win-x86-reference, preferred_va, selected source-documented function); `0x009546f0` (win-x86-reference, preferred_va, selected source-documented function)
- 필드: timestamp = VGR_record+0 (be_f32)
- 필드: content_length = VGR_record+4 (be_u32)
- 필드: opcode = VGR_record+8 (be_u16)
- 필드: payload = VGR_record+10 (bytes)
- 원문 layout: record+0: BE float32 timestamp
- 원문 layout: record+4: BE u32 content_length
- 원문 layout: record+8: BE u16 opcode
- 원문 layout: record+10: payload
- 정정: 옛 08 04 31 패턴의 08은 content length의 하위 바이트이며 0431이 opcode다. 다음 float을 시간으로 읽으면 다음 레코드의 timestamp를 잘못 사용할 수 있다
- 정정: 임의의 고정 6바이트 trailer 규칙은 opcode별 serialized/recorded 길이 차이와 모순된다
- 한계: finite timestamp만 허용하며 임의의 1,800초 상한을 두지 않는다
- 한계: 불완전 헤더, length<2, body overrun, nonfinite timestamp에서 그 자리 오류; 재동기화 검색을 하지 않는다
- 한계: 배포된 모든 증거 파일 검증을 뜻하지 않는다
- 한계: opcode의 게임 의미나 성공 적용
- 한계: 기존 검증 범위: 기존 독립 순차 검사: 실제 7,870개 파일, 1,044,589,605바이트, 30,729,156개 레코드 완전 소비; AppleDouble 5개 제외
- 근거: [src-legacy-3a2fe01804f4](#src-legacy-3a2fe01804f4) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-816f50695af4](#src-legacy-816f50695af4) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-7361b4612daa](#src-legacy-7361b4612daa) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.


## actor·roster·계정 경계

### VGRE-deepening-identity-authenticated-account-from-roster

**identity authenticated account from roster**

Client mastery cache use does not prove authentication, service account namespace, uploader ownership, or modern VGNA compatibility.

- 상태: unresolved · 의미 확신: unassigned · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0093b270` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0056f050` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00997dc0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: No certified/displayed winner, exact final gold/time, authenticated account or uploader inference. Callback order excludes reentrancy and nested UI guard reconstruction.
- 근거: [src-deepening-09908834d9ba](#src-deepening-09908834d9ba) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f8c7558a816d](#src-deepening-f8c7558a816d) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f1eed04cad1f](#src-deepening-f1eed04cad1f) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-09908834d9ba](#src-deepening-09908834d9ba) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-6c2e708b509a](#src-deepening-6c2e708b509a) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-identity-external-string-mastery-cache

**identity external string mastery cache**

Roster entry+44 string getter0093b270 feeds scoreboard lookup0056f050 outer key; nested hero value passes through KindredHeroMasteryManifest thresholds and result is stored UI+75a4.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0093b270` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x006f5d07` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x006f5d32` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x006f5d3a` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0056f050` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x007e50c0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x01264028` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: No certified/displayed winner, exact final gold/time, authenticated account or uploader inference. Callback order excludes reentrancy and nested UI guard reconstruction.
- 근거: [src-deepening-09908834d9ba](#src-deepening-09908834d9ba) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f8c7558a816d](#src-deepening-f8c7558a816d) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f1eed04cad1f](#src-deepening-f1eed04cad1f) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f804572b3e72](#src-deepening-f804572b3e72) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-3bbf4528ff44](#src-deepening-3bbf4528ff44) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-1de244922c2b](#src-deepening-1de244922c2b) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-e358da15fc1e](#src-deepening-e358da15fc1e) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-ddcafec18612](#src-deepening-ddcafec18612) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-6c2e708b509a](#src-deepening-6c2e708b509a) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-identity-mastery-response-cache

**identity mastery response cache**

Handler0056f190 traverses response vector rows stride24, outer string+c, nested string/integer rows stride1c; stores same cache. This proves client dataflow, not source authenticity.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0056f190` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0056f217` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0056f22b` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0121fc78` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: No certified/displayed winner, exact final gold/time, authenticated account or uploader inference. Callback order excludes reentrancy and nested UI guard reconstruction.
- 근거: [src-deepening-09908834d9ba](#src-deepening-09908834d9ba) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f8c7558a816d](#src-deepening-f8c7558a816d) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f1eed04cad1f](#src-deepening-f1eed04cad1f) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-7f0bce357f27](#src-deepening-7f0bce357f27) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f7ad612fc5c4](#src-deepening-f7ad612fc5c4) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-6c2e708b509a](#src-deepening-6c2e708b509a) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-identity-mastery-rpc-method

**identity mastery rpc method**

Platform table01293fb8 slot4c resolves00997de0 using literal getHeroMastery; builder0098d780 serializes context string and vector. No network request occurred; response dispatch and authentication remain unverified.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x01293fb8` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00997de0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x01295260` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0098d780` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: No certified/displayed winner, exact final gold/time, authenticated account or uploader inference. Callback order excludes reentrancy and nested UI guard reconstruction.
- 근거: [src-deepening-09908834d9ba](#src-deepening-09908834d9ba) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f8c7558a816d](#src-deepening-f8c7558a816d) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f1eed04cad1f](#src-deepening-f1eed04cad1f) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-a684ae59db6d](#src-deepening-a684ae59db6d) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-2d186061c682](#src-deepening-2d186061c682) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-0be03adf5873](#src-deepening-0be03adf5873) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-8df4eb06449a](#src-deepening-8df4eb06449a) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-6c2e708b509a](#src-deepening-6c2e708b509a) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-entity-actor-resource-kind

**Actor 리소스 종류와 네이티브 분류**

Actor SYMB type key 0x2419fb6c와 일치하는 resource root의 첫 scalar uint32가 네이티브 kind다. 선택된 빌드에서 0은 hero, 2/3은 structure로 묶을 근거가 있으며 그 외는 raw kind를 보존하고 unknown이다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, resource_decode, synthetic_tests
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-reference`
- 함수/위치: `0x004222f0` (win-x86-reference, preferred_va, selected source-documented function); `0x0112bec0` (win-x86-reference, preferred_va, selected source-documented function); `0x004c4450` (win-x86-reference, preferred_va, selected source-documented function); `0x0112c820` (win-x86-reference, preferred_va, selected source-documented function); `0x00954e40` (win-x86-reference, preferred_va, selected source-documented function); `0x00942d90` (win-x86-reference, preferred_va, selected source-documented function); `0x00942480` (win-x86-reference, preferred_va, selected source-documented function)
- 원문 layout: SYMB: root_offset u32, type_key u32, NUL name
- 원문 layout: Actor serialized size: 0x208
- 원문 layout: Actor root+0: native kind
- 원문 layout: actor+0x1c: definition root pointer
- 원문 layout: actor+0x1e0: derived flags
- 원문 layout: key-table VA: 01e3f978
- 정정: bit31은 FortressMinion에도 있으므로 hero 판정에 쓰지 않는다
- 정정: 이름 부분 문자열이나 파일명으로 종류를 추측하지 않는다
- 한계: manifest 첫 relocation 포인터를 kind enum으로 읽지 않는다
- 한계: 정확한 serialized_name, type key, root 범위, hash/profile pairing 필요
- 한계: single SYMB, 최대1024 ASCII와 zero padding은 현재 reader 제한이지 native loader 규칙이 아니다
- 한계: kind4 전체 분류, minion 하위 분류, 화면/생존/owner/kill credit
- 한계: 기존 검증 범위: paired 자산 9개: hero 3, kind2 1, kind3 3, kind4 2; 모든 kind를 검증한 census가 아님
- 근거: [src-legacy-491ccfd0d6da](#src-legacy-491ccfd0d6da) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-52e5ac43e76b](#src-legacy-52e5ac43e76b) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-608dc233d1c3](#src-legacy-608dc233d1c3) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.

### VGRE-entity-destroy-lifecycle-observation

**040b 삭제 액션과 지연 정리**

040b ActionEntityDestroy는 첫 BE32 entity ID를 대상으로 삭제 경로를 요청한다. 0112a1f0은 pool 정리 비트를 설정하며 즉시 메모리 해제를 하지 않는다. 기록된 삭제 후에도 역사적 spawn identity와 후속 참조를 유지해야 한다.

- 상태: bounded · 의미 확신: high · 검증: static_instructions, corpus_audit, synthetic_tests
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-reference`
- Opcode: `040b`
- 함수/위치: `0x004cfec0` (win-x86-reference, preferred_va, selected source-documented function); `0x004d2427` (win-x86-reference, preferred_va, selected source-documented function); `0x0081a6c0` (win-x86-reference, preferred_va, selected source-documented function); `0x0094d470` (win-x86-reference, preferred_va, selected source-documented function); `0x0092b630` (win-x86-reference, preferred_va, selected source-documented function); `0x0112a1f0` (win-x86-reference, preferred_va, selected source-documented function); `0x00857970` (win-x86-reference, preferred_va, selected source-documented function)
- 원문 layout: payload+0: entity BE32
- 원문 layout: payload+4..5: opaque
- 원문 layout: action+0x10: entity ID
- 원문 layout: DAT_0209e204: mode branch selector
- 한계: 마지막 payload2바이트는 opaque
- 한계: 0430 사망이나 0431 전환을 entity lifetime 종료로 사용하지 않는다
- 한계: 이 코퍼스에는 duplicate destroy 또는 destroy 뒤 same-ID spawn의 실제 양성 사례가 없어 해당 경계는 synthetic tests
- 한계: record timestamp의 실제 삭제 완료, respawn, ID 재사용
- 한계: 기존 검증 범위: 121개 section/300,667 records에서 1,242개 040b는 모두 payload6; 삭제 뒤 다른 opcode 참조가 남은 ID 3개
- 근거: [src-legacy-50ed693565fd](#src-legacy-50ed693565fd) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-d5a2c970ee47](#src-legacy-d5a2c970ee47) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.

### VGRE-identity-bootstrap-selection

**03e9 기록 선택 actor와 팀**

03e9의 첫 BE32는 기록에 선택된 actor이고 +100은 해당 roster team 하위 nibble에서 온다. 선택 getter에는 모드·이름·팀에 따른 대체 경로가 있다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, development_corpus, independent_review
- 경계: client_native / not_applicable / static_only
- 정확한 파일: `win-x86-laa`, `h5810-development`
- Opcode: `03e9`
- 함수/위치: `0x004cb030` (win-x86-laa, preferred_va, bootstrap writer); `0x00939790` (win-x86-laa, preferred_va, selected actor getter); `0x0093b1d0` (win-x86-laa, preferred_va, roster team getter); `0x004d00b2` (win-x86-laa, preferred_va, bootstrap receiver)
- 필드: recording_selected_actor_id = payload_after_opcode+0 (be_u32)
- 필드: recording_selected_team_id = payload_after_opcode+100 (u8)
- 정정: selected actor를 uploader/account owner 또는 무조건 my_team으로 부르지 않는다.
- 정정: actor sentinel -1에 대한 team getter 결과는 1이므로 team=1만으로 유효 참가자를 확정할 수 없다.
- 한계: 101-byte compact payload와 H5810 사례에 대한 제한된 증거이다.
- 한계: 선택 모드 자체는 03e9에서 식별되지 않는다.
- 근거: [src-identity](#src-identity) · Native chain: 03e9 bootstrap
- 근거: [src-identity_review](#src-identity_review) · REPORT
- 근거: [src-artifact-ff1ad1b8c623](#src-artifact-ff1ad1b8c623) · whole artifact; content remains external
- 근거: [src-artifact-a4848e801e05](#src-artifact-a4848e801e05) · whole artifact; content remains external
- 근거: [src-artifact-0a8763f8d6b4](#src-artifact-0a8763f8d6b4) · whole artifact; content remains external

### VGRE-identity-external-string-history

**03ee 외부 문자열의 관측 이력**

03ee +64는 actor와 별개인 NUL 종료 문자열이며 roster +0x44에 저장된다. H5810 최초 10개 관측은 비어 있지 않고 주기 snapshot 1,680개는 빈 값이므로 이후 빈 값으로 이력을 덮어쓰면 안 된다.

- 상태: supported · 의미 확신: high · 검증: static_instructions, development_corpus
- 경계: client_native / not_applicable / static_only
- 정확한 파일: `win-x86-laa`, `h5810-development`
- Opcode: `03ee`
- 함수/위치: `0x004d52a0` (win-x86-laa, preferred_va, roster string receiver); `0x0095ea90` (win-x86-laa, preferred_va, external string setter)
- 필드: external_identifier_candidate = payload_after_opcode+64 (bounded_nul_string[64])
- 필드: actor_id = payload_after_opcode+160 (be_u32)
- 한계: 실제 식별자 문자열은 이 사전에 포함하지 않는다.
- 한계: 계정 인증, 장기 안정성, filename UUID와 matchId의 동등성은 미확정이다.
- 근거: [src-identity](#src-identity) · Player/account identity limits
- 근거: [src-protocol](#src-protocol) · Raw roster identity history

### VGRE-identity-recording-family-validation

**한 기록 family와 unknown completeness**

독립검증에서 서로 다른 파일 prefix를 이어 붙이는 오류가 발견되어 단일 prefix·중복 없는 숫자 section·0 시작·연속성·비어 있지 않은 입력을 decode 전에 검사하도록 연구 collector를 수정했다.

- 상태: corrected · 의미 확신: high · 검증: synthetic_tests, development_corpus, independent_review
- 경계: offline_analysis / not_applicable / synthetic_and_development
- 정확한 파일: `h5810-development`
- 정정: 서로 다른 filename prefix를 이어 붙여 동일 recording으로 처리하던 collector 동작을 거부하도록 수정했다.
- 한계: 주어진 파일의 연속성은 원래 모든 section 존재나 실제 경기 종료를 증명하지 않는다.
- 한계: source-manifest hash와 recording content-scope hash는 별개 namespace다.
- 근거: [src-identity](#src-identity) · Independent-review correction: input family and artifact scope
- 근거: [src-identity_review](#src-identity_review) · REPORT

### VGRE-identity-roster-native-contract

**03ee 명단의 네이티브 식별 계약**

03ee의 검증된 prefix는 NUL 종료 이름, unsigned BE32 actor/definition/skin과 team 하위 nibble이다. 동일 이름의 두 플레이어는 actor ID로 구별하고 spawn만으로 player membership을 만들지 않는다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, controlled_runtime
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-reference`, `win-x86-laa`
- Opcode: `03ee`
- 함수/위치: `0x004d274e` (win-x86-reference, preferred_va, selected source-documented function); `0x004d274e` (win-x86-laa, preferred_va, selected source-documented function); `0x004cfec0` (win-x86-reference, preferred_va, selected source-documented function); `0x004cfec0` (win-x86-laa, preferred_va, selected source-documented function); `0x004d52a0` (win-x86-reference, preferred_va, selected source-documented function); `0x004d52a0` (win-x86-laa, preferred_va, selected source-documented function); `0x0096d310` (win-x86-reference, preferred_va, selected source-documented function); `0x0096d310` (win-x86-laa, preferred_va, selected source-documented function); `0x0095e5e0` (win-x86-reference, preferred_va, selected source-documented function); `0x0095e5e0` (win-x86-laa, preferred_va, selected source-documented function); `0x0095e9f0` (win-x86-reference, preferred_va, selected source-documented function); `0x0095e9f0` (win-x86-laa, preferred_va, selected source-documented function); `0x0081e800` (win-x86-reference, preferred_va, selected source-documented function); `0x0081e800` (win-x86-laa, preferred_va, selected source-documented function)
- 필드: name = payload_after_opcode+0 (bounded_nul_string[64])
- 필드: external_string = payload_after_opcode+64 (bounded_nul_string[64])
- 필드: actor_id = payload_after_opcode+160 (be_u32)
- 필드: definition_id = payload_after_opcode+164 (be_u32)
- 필드: skin_hash = payload_after_opcode+168 (be_u32)
- 필드: team_raw_low_nibble = payload_after_opcode+210 (u8 & 0x0f)
- 원문 layout: payload+0..63: name
- 원문 layout: payload+64: separate account-string region; not account authentication
- 원문 layout: payload+0xa0: actor BE32
- 원문 layout: payload+0xa4: definition BE32
- 원문 layout: payload+0xa8: skin hash BE32
- 원문 layout: payload+210: raw team byte & 0x0f
- 원문 layout: player-entry+0x78: definition
- 원문 layout: player-entry+0xb0: team nibble
- 정정: 기존 NATIVE_ROSTER 문서의 hero-name 화면 조건은 2026-10-05 승인된 portrait+독립 identity 조건으로 대체됐다; literal text 관찰을 새로 주장하지 않는다
- 정정: 오래된 atlas의 9개 runtime gate pending 문구보다 OPCODE_CONTROLS/ROSTER_ACCEPTANCE의 bounded 완료 상태가 최신이다
- 한계: 03ee payload 216/222만 지원; 수신기는 216바이트를 복사하며 추가 6바이트는 opaque
- 한계: 이름은 strict UTF-8 BMP, 최대 63 encoded bytes; non-BMP/invalid UTF-8는 unsupported로 남긴다
- 한계: team 숫자를 left/right 화면 팀으로 바꾸지 않는다
- 한계: 원자적 스냅샷이 아닌 안정된 구간의 관찰이며 모든 빌드/전송 모드를 인증하지 않는다
- 한계: literal hero-name text, skin 이름/인덱스, 전체 suffix
- 한계: 기존 검증 범위: 50개 원본 source/dispatch/consumer 비교(216바이트 40개, 222바이트 10개); 같은 이름 두 행은 별도 actor/원본 hero asset/유일 KDA로 연결; 화면 판독은 수동
- 근거: [src-legacy-8a02e2be2ba4](#src-legacy-8a02e2be2ba4) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-c97bae0f3414](#src-legacy-c97bae0f3414) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-5cc7fe753b75](#src-legacy-5cc7fe753b75) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-23b5c8c50a77](#src-legacy-23b5c8c50a77) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-fd9ff98c63f2](#src-legacy-fd9ff98c63f2) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-fbc9cad2c455](#src-legacy-fbc9cad2c455) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.

### VGRE-identity-spawn-skin-observation

**생성 관찰·스킨 값·실제 수명 분리**

03f2/03f3의 prefix는 definition/skin/actor 순 unsigned BE32다. 이 정보는 이전 spawn 관찰에 따른 identity이며 repeated spawn이 새 생명주기나 무조건 state replacement를 증명하지 않는다. skin raw hash 일치는 skin 인덱스나 자산 이름 해석과 별개다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, controlled_runtime, synthetic_tests
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-reference`, `win-x86-laa`
- Opcode: `03f2`, `03f3`
- 함수/위치: `0x0094d480` (win-x86-reference, preferred_va, selected source-documented function); `0x0094d480` (win-x86-laa, preferred_va, selected source-documented function); `0x0094e170` (win-x86-reference, preferred_va, selected source-documented function); `0x0094e170` (win-x86-laa, preferred_va, selected source-documented function); `0x004d5930` (win-x86-reference, preferred_va, selected source-documented function); `0x004d5930` (win-x86-laa, preferred_va, selected source-documented function); `0x0081ac20` (win-x86-reference, preferred_va, selected source-documented function); `0x0081ac20` (win-x86-laa, preferred_va, selected source-documented function)
- 필드: definition_id = payload_after_opcode+0 (be_u32)
- 필드: skin_hash = payload_after_opcode+4 (be_u32)
- 필드: actor_id = payload_after_opcode+8 (be_u32)
- 원문 layout: spawn payload+0: definition BE32
- 원문 layout: spawn payload+4: skin BE32
- 원문 layout: spawn payload+8: actor BE32
- 원문 layout: 03f3 payload+0x146: baseline branch flag
- 정정: H5672 원래 독립 검증은 64 supported groups 일치/0 mismatch/6 unknown이며 actor/skin split 후 결과가 아니다
- 정정: 기존 actor가 이미 resolve되면 0094e170은 baseline grant 전 반환하므로 반복 snapshot으로 무조건 덮어쓰지 않는다
- 한계: 03f2 payload 122/126, 03f3 746/750만 검증된 recorded variants
- 한계: entity sentinel 0xffffffff는 resolve하지 않는다
- 한계: 원래 baseline 65bab83의 roster는 first effective spawn과 skin까지 비교하며 H5672 최초 skin 충돌을 유지한다
- 한계: 별도 actor/skin split 브랜치 설명을 이 main에 이미 적용된 기능으로 표시하지 않는다
- 한계: 모든 length/presence 조합, 일반 respawn/ID 재사용, skin label
- 한계: 기존 검증 범위: 03f2 linked apply 60건은 122/existing 14와 126/absent 46; 03f3는 fresh 750-byte 10개와 existing 746-byte 50개
- 한계: 기준 main 65bab83에는 actor/skin split 구현이 없다. 보관 FLOW-MAP의 다른 branch 구현 설명을 main 상태로 읽지 않는다.
- 근거: [src-legacy-d5a2c970ee47](#src-legacy-d5a2c970ee47) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-8a02e2be2ba4](#src-legacy-8a02e2be2ba4) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-5cc7fe753b75](#src-legacy-5cc7fe753b75) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-fce4914d0b4f](#src-legacy-fce4914d0b4f) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-2096f6d0e790](#src-legacy-2096f6d0e790) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-d5c9da98be4d](#src-legacy-d5c9da98be4d) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.


## 종료·승패·완전성

### VGRE-deepening-terminal-banner-reason-keys

**terminal banner reason keys**

0073af90 selects VICTORY/DEFEAT by boolean for reason0 and SURRENDER for reason2; other reasons skip text-key assignment in this function.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0073af90` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0124fc04` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0124fc24` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0124fc40` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: No certified/displayed winner, exact final gold/time, authenticated account or uploader inference. Callback order excludes reentrancy and nested UI guard reconstruction.
- 근거: [src-deepening-09908834d9ba](#src-deepening-09908834d9ba) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f8c7558a816d](#src-deepening-f8c7558a816d) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f1eed04cad1f](#src-deepening-f1eed04cad1f) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-592d9786b4a9](#src-deepening-592d9786b4a9) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-b0dd017522f4](#src-deepening-b0dd017522f4) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-6c2e708b509a](#src-deepening-6c2e708b509a) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-terminal-clock-lifecycle

**terminal clock lifecycle**

Accepted primary2 commits before result callback and has no primary tick. Final refresh still reads controller clock, not terminal packet timestamp; UI formatter is modulo60-cache gated.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00549ffa` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0054a019` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x005497a0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00548870` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x006f557d` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: No certified/displayed winner, exact final gold/time, authenticated account or uploader inference. Callback order excludes reentrancy and nested UI guard reconstruction.
- 근거: [src-deepening-09908834d9ba](#src-deepening-09908834d9ba) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f8c7558a816d](#src-deepening-f8c7558a816d) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f1eed04cad1f](#src-deepening-f1eed04cad1f) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-3f546d5d0d00](#src-deepening-3f546d5d0d00) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-6dda242b856c](#src-deepening-6dda242b856c) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-6ab9f1b58c3c](#src-deepening-6ab9f1b58c3c) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-d32981953aa3](#src-deepening-d32981953aa3) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-6c2e708b509a](#src-deepening-6c2e708b509a) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-terminal-gold-final-refresh-cache

**terminal gold final refresh cache**

Final refresh visits16 rows without reset of each row gold cache; formatter runs only when truncated resource7*float32(.01) exceeds prior cached integer.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x006f5020` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x006f502b` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x006f7104` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x006f710a` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x006f711b` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: No certified/displayed winner, exact final gold/time, authenticated account or uploader inference. Callback order excludes reentrancy and nested UI guard reconstruction.
- 근거: [src-deepening-09908834d9ba](#src-deepening-09908834d9ba) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f8c7558a816d](#src-deepening-f8c7558a816d) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f1eed04cad1f](#src-deepening-f1eed04cad1f) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-65f790466d1d](#src-deepening-65f790466d1d) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-58bc1f4ae6c5](#src-deepening-58bc1f4ae6c5) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-6c2e708b509a](#src-deepening-6c2e708b509a) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-terminal-last-request-is-final-result

**terminal last request is final result**

Neither last request nor first recorded request universally proves accepted callback/display result; initial state, guards, perspective, and nested UI transitions matter.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00549fa0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00549fb7` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00564e90` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: No certified/displayed winner, exact final gold/time, authenticated account or uploader inference. Callback order excludes reentrancy and nested UI guard reconstruction.
- 근거: [src-deepening-09908834d9ba](#src-deepening-09908834d9ba) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f8c7558a816d](#src-deepening-f8c7558a816d) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f1eed04cad1f](#src-deepening-f1eed04cad1f) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-6dda242b856c](#src-deepening-6dda242b856c) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-2626275848a3](#src-deepening-2626275848a3) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-ce219ed8f1ee](#src-deepening-ce219ed8f1ee) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-6c2e708b509a](#src-deepening-6c2e708b509a) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-terminal-primary-entry

**terminal primary entry**

00549620 writes team/reason, then synchronously requests primary2 before secondary3. Primary2 entry00548c90 executes only if the primary transition accepts.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0054962d` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00549633` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00549699` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x005496a6` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00549fa0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00549fec` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00549ffa` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0054a019` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: No certified/displayed winner, exact final gold/time, authenticated account or uploader inference. Callback order excludes reentrancy and nested UI guard reconstruction.
- 근거: [src-deepening-09908834d9ba](#src-deepening-09908834d9ba) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f8c7558a816d](#src-deepening-f8c7558a816d) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f1eed04cad1f](#src-deepening-f1eed04cad1f) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-afbcd8686e13](#src-deepening-afbcd8686e13) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-6dda242b856c](#src-deepening-6dda242b856c) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-3f546d5d0d00](#src-deepening-3f546d5d0d00) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-6c2e708b509a](#src-deepening-6c2e708b509a) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-terminal-repeated-field-callback-divergence

**terminal repeated field callback divergence**

A repeat while primary2 overwrites controller fields but same-state primary guard prevents a fresh result callback. Counterexample is synthetic, not an observed replay.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0054962d` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00549633` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00549fa0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00549fa2` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: No certified/displayed winner, exact final gold/time, authenticated account or uploader inference. Callback order excludes reentrancy and nested UI guard reconstruction.
- 근거: [src-deepening-09908834d9ba](#src-deepening-09908834d9ba) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f8c7558a816d](#src-deepening-f8c7558a816d) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-f1eed04cad1f](#src-deepening-f1eed04cad1f) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-afbcd8686e13](#src-deepening-afbcd8686e13) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-6dda242b856c](#src-deepening-6dda242b856c) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-0792a03dcffe](#src-deepening-0792a03dcffe) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-ce219ed8f1ee](#src-deepening-ce219ed8f1ee) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-6c2e708b509a](#src-deepening-6c2e708b509a) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-result-request-relative-win

**03f1 요청 팀과 상대 승리 boolean**

03f1 첫 BE32의 low byte는 종료 요청의 team 값이다. 일반 모드 결과 경로는 이 값을 선택 actor의 팀과 비교해 상대 win boolean을 만든다. 대체 모드는 팀 대신 1과 비교한다.

- 상태: bounded · 의미 확신: high · 검증: static_instructions
- 경계: client_native / not_applicable / static_only
- 정확한 파일: `win-x86-laa`, `h5810-development`
- Opcode: `03f1`
- 함수/위치: `0x0094d450` (win-x86-laa, preferred_va, ActionEndMatch apply); `0x004c0e10` (win-x86-laa, preferred_va, end handler); `0x00549620` (win-x86-laa, preferred_va, controller end state); `0x00548c90` (win-x86-laa, preferred_va, relative result processing); `0x004c1370` (win-x86-laa, preferred_va, analytics win boolean setter)
- 필드: end_request_team_word = payload_after_opcode+0 (be_u32; consumer uses low byte)
- 필드: end_reason = payload_after_opcode+4 (u8)
- 정정: in-band selected-team 증거가 전혀 없다는 과거 주장은 너무 넓다.
- 한계: 요청 관측, 실제 최종 화면, 성공한 apply, 서버 확정, 랭크 반영은 서로 다르다.
- 한계: reason 0을 crystal destruction으로 좁히지 않는다.
- 한계: reason 5/6/7은 validation dialog, 8은 no-op 경로가 있다.
- 근거: [src-identity](#src-identity) · End result: team-valued request vs relative boolean


## 아이템·설정·소유

### VGRE-infusion-refresh-and-stat-declarations

**타격·수정 강화제 지속시간 갱신과 조건부 능력치 선언**

Infusion reapply script-list handler copies original duration+0x230 into remaining+0x22c and adjusts flag bit4. It coexists with Lifetime reapply stubs. Declared item duration is150, distinct from TIME2.5. Stat builders use intercept/delta declarations; execution queues mode-gated commands rather than directly rewriting local stats.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00861ff0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00931b70` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00861250` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00861530` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 한계: Conditional interpolation endpoints at stack1/12 are algebraic models, not observed server totals. Dynamic stack/level ordering, final aggregation and full IEEE-754 effects remain unverified.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-inventory-native-instance-state

**아이템 인스턴스·수량·인벤토리 갱신**

inventory의 기본 식별은 definition 단독이 아니라 owner 아래의 item instance다. 043d grant, 044b consume, 0444 low16 quantity SET의 네이티브 경로를 구별한다. activation과 sell request만으로 inventory 감소나 gold 변화를 만들지 않는다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, synthetic_tests, controlled_runtime
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-reference`, `win-x86-laa`
- Opcode: `03f3`, `043d`, `044b`, `0444`, `0438`
- 함수/위치: `0x00958330` (win-x86-reference, preferred_va, selected source-documented function); `0x00958330` (win-x86-laa, preferred_va, selected source-documented function); `0x0093cdc0` (win-x86-reference, preferred_va, selected source-documented function); `0x0093cdc0` (win-x86-laa, preferred_va, selected source-documented function); `0x00940230` (win-x86-reference, preferred_va, selected source-documented function); `0x00940230` (win-x86-laa, preferred_va, selected source-documented function); `0x00872340` (win-x86-reference, preferred_va, selected source-documented function); `0x00872340` (win-x86-laa, preferred_va, selected source-documented function); `0x0094f6f0` (win-x86-reference, preferred_va, selected source-documented function); `0x0094f6f0` (win-x86-laa, preferred_va, selected source-documented function); `0x0094c0b0` (win-x86-reference, preferred_va, selected source-documented function); `0x0094c0b0` (win-x86-laa, preferred_va, selected source-documented function); `0x00950240` (win-x86-reference, preferred_va, selected source-documented function); `0x00950240` (win-x86-laa, preferred_va, selected source-documented function); `0x005c1bb0` (win-x86-reference, preferred_va, selected source-documented function); `0x005c1bb0` (win-x86-laa, preferred_va, selected source-documented function); `0x005a0790` (win-x86-reference, preferred_va, selected source-documented function); `0x005a0790` (win-x86-laa, preferred_va, selected source-documented function)
- 원문 layout: actor+0x34: item-set component
- 원문 layout: component+0x1c: live pointer array
- 원문 layout: component+0x44: deferred pointer array
- 원문 layout: component+0x70: occupied byte
- 원문 layout: component+0x71: low7 capacity/high1 dirty
- 원문 layout: item+0x14: definition pointer
- 원문 layout: item+0x18: ability pointer
- 원문 layout: item+0x2c: definition ID
- 원문 layout: item+0x30: instance ID
- 원문 layout: item+0x34: u16 quantity
- 원문 layout: item+0x38: flags
- 원문 layout: 03f3 payload+0x15e: count
- 원문 layout: 03f3 payload+0x162/+0x18a/+0x1b2: definitions/instances/quantities
- 정정: definition+0x125는 grant-skip 검사이며 UI hidden flag가 아니다
- 정정: 0438 serialization 경로는 live/deferred 배열 swap을 하므로 모든 request가 mutation-free라는 일반화는 틀리다
- 정정: native name Vision Totem은 localized Scout Cam과 다르며 일반 HUD 제외 predicate에는 native name을 쓴다
- 한계: capacity는 game-mode 자산에 따라6/8이며 고정6도 universal8도 아니다
- 한계: component arrays는10 allocated entries, occupied와 capacity는 별도
- 한계: zero quantity SET은 pointer 제거가 아니다; zero quantity consume은 검증된 경로에서 제거한다
- 한계: visible_items predicate는 native definition-name이며 localized label이 아니다
- 한계: 모든 코퍼스 정확도, 자연 발생 0444, 화면 slot order
- 한계: 기존 검증 범위: C33 baseline/grant/consume 18개 정렬, 별도 challenge 8 operations/16 states, backward seek11 operations; 이후 25 synthetic inventory controls
- 근거: [src-legacy-6ef08bd0ceaa](#src-legacy-6ef08bd0ceaa) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-7d0c0deb8b57](#src-legacy-7d0c0deb8b57) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-7cb34430c060](#src-legacy-7cb34430c060) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-7e39f84748f4](#src-legacy-7e39f84748f4) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-1c1d37dc9cae](#src-legacy-1c1d37dc9cae) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.

### VGRE-item-activation-envelope

**아이템 사용 요청과 모드별 메시지**

0448/0449/044a는 서로 다른 request prefix이며 044c는 actor, item instance, raw target/coordinate bits, mode가 있는 conditional activation message다. mode0만 target ref를, mode1만 active position을, mode2는 둘 다 없는 경로를 노출한다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, corpus_audit, synthetic_tests
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-reference`
- Opcode: `0448`, `0449`, `044a`, `044c`
- 함수/위치: `0x004d3e39` (win-x86-reference, preferred_va, selected source-documented function); `0x0081b7f0` (win-x86-reference, preferred_va, selected source-documented function); `0x0081b790` (win-x86-reference, preferred_va, selected source-documented function); `0x0081b740` (win-x86-reference, preferred_va, selected source-documented function); `0x0094ee90` (win-x86-reference, preferred_va, selected source-documented function); `0x00529ff0` (win-x86-reference, preferred_va, selected source-documented function); `0x0095bda0` (win-x86-reference, preferred_va, selected source-documented function); `0x0095bea0` (win-x86-reference, preferred_va, selected source-documented function); `0x0095bdd0` (win-x86-reference, preferred_va, selected source-documented function); `0x00813dc0` (win-x86-reference, preferred_va, selected source-documented function); `0x00813fc0` (win-x86-reference, preferred_va, selected source-documented function); `0x00813ec0` (win-x86-reference, preferred_va, selected source-documented function)
- 필드: 044c.actor = payload_after_opcode+0 (be_u32)
- 필드: 044c.item_instance = payload_after_opcode+4 (be_u32)
- 필드: 044c.target_if_mode_0 = payload_after_opcode+8 (be_u32)
- 필드: 044c.coordinates_if_mode_1 = payload_after_opcode+12 (2 x be_f32_bits)
- 필드: 044c.mode = payload_after_opcode+20 (u8)
- 필드: 044c.opaque_suffix = payload_after_opcode+21 (1 opaque byte)
- 원문 layout: 0448+0: instance BE32; +4..5 opaque
- 원문 layout: 0449+0/+4: unsigned anonymous BE32; +8..13 opaque
- 원문 layout: 044a+0/+4/+8: vector bits; +12: raw argument; +16..21 opaque
- 원문 layout: 044c+0 actor,+4 item instance,+8 target,+12/+16 coordinate bits,+20 mode,+21 opaque
- 정정: 클래스명이나 serializer 존재는 네트워크 방향과 recorder build를 인증하지 않는다
- 정정: mode별 비활성 target/coordinate 값은 의미있는 필드로 승격하지 않는다
- 한계: payload/content lengths:0448 6/8,0449 14/16,044a22/24,044c22/24; native serialized4/8/16과 혼동하지 않는다
- 한계: item instance와 anonymous arguments를 entity ref로 취급하지 않는다
- 한계: unsupported mode와 nonfinite coordinates는 raw bits를 유지하고 제한된 상태로 노출한다
- 한계: 35,264 일치는 shared parser를 통한 field extraction이지 독립 framing 재검증이나 모든 opcode runtime proof가 아니다
- 한계: 새 runtime execution, 성공 item use, 소비/cooldown 완료, request/outcome pairing
- 한계: 기존 검증 범위: 56 recordings에서 35,264 original rows와 timeline rows 일치: 0448 11,711;0449 31;044a 6,084;044c17,438
- 한계: 새 Windows outgoing producer 의미는 VGRE-request-item-layouts에 있다. 여기의 익명 historical field를 same-build outbound capture로 승격하지 않는다.
- 근거: [src-legacy-6450cba1b6f5](#src-legacy-6450cba1b6f5) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-b0fc6282fd01](#src-legacy-b0fc6282fd01) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-540e0f15860d](#src-legacy-540e0f15860d) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.

### VGRE-item-configuration-selection

**설정 mode와 선택 제스처 분리**

93개 기존 inventory catalog 항목 중 active-flag 34개의 실제 embedded/external ability 설정 +0x60은 mode4=25, mode3=7, mode2=2, mode0/1=0이다. Reflex Block/Aegis는 external definition을 따라야 한다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, resource_decode, independent_review, development_corpus
- 경계: client_native / not_applicable / static_only
- 정확한 파일: `win-x86-laa`, `h5810-development`
- 함수/위치: `0x0059bc50` (win-x86-laa, preferred_va, shared dispatcher); `0x00937040` (win-x86-laa, preferred_va, resolved item ability configuration getter); `0x00940230` (win-x86-laa, preferred_va, item ability binding); `0x0093f270` (win-x86-laa, preferred_va, runtime ability definition store); `0x00590ef0` (win-x86-laa, preferred_va, generic stored/fallback selector); `0x00592990` (win-x86-laa, preferred_va, item-selection callback)
- 필드: activation_configuration = AbilityDef+96 (u32)
- 필드: external_ability_reference = ItemDefinition+60 (reference)
- 필드: embedded_ability_definition = ItemDefinition+64 (structure)
- 정정: AbilityDef+0x60 configuration, +0x6a byte, request mode+0x24를 구별한다.
- 정정: 기존 target 재사용과 자동 fallback 경로가 있으므로 actor-bearing 필드에서 manual selection을 추론하지 않는다.
- 한계: 전체 932-entry manifest의 모든 Item을 독립 열거한 결과가 아니다.
- 한계: bundled 존재는 현재 shop 사용 가능성·live 경로·특정 UI gesture를 증명하지 않는다.
- 한계: H5810의 0449=0은 dead code 증거가 아니다.
- 근거: [src-item_target](#src-item_target) · Concrete producers and target origins; Supplied resource coverage
- 근거: [src-item_resource](#src-item_resource) · Native binding; External abilities
- 근거: [src-combat_review](#src-combat_review) · Item target semantics

### VGRE-item-consumable-keys-spawn-declaration

**회복 아이템·정찰 카메라의 키와 생성 선언**

선택된 자산에서 Healing Flask457은 key0x1b184adf/Cooldown120, Scout Cam526은 key0x6b3ebf4f/Charges2/Cooldown150이다. Cam의 native factory는 SpawnEntity와 actor392 VisionTotem을 선언하지만 선택 client setter/callback이 stub여서 실제 authoritative spawning은 이 경로만으로 증명되지 않는다.

- 상태: corrected · 의미 확신: high · 검증: resource_decode, static_instructions, corpus_audit, synthetic_tests
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-laa`
- Opcode: `044c`, `048a`, `03f2`, `03f3`
- 함수/위치: `0x00940230` (win-x86-laa, preferred_va, selected source-documented function); `0x0093f270` (win-x86-laa, preferred_va, selected source-documented function); `0x0089a3e0` (win-x86-laa, preferred_va, selected source-documented function); `0x00528270` (win-x86-laa, preferred_va, selected source-documented function); `0x005290e0` (win-x86-laa, preferred_va, selected source-documented function); `0x0045cd00` (win-x86-laa, preferred_va, selected source-documented function); `0x0089a410` (win-x86-laa, preferred_va, selected source-documented function)
- 원문 layout: itemDefinition+0x38 active; +0x3c external reference; inline+0x40 ability
- 원문 layout: embedded ability+0x18 empty group,+0x6a mode0
- 원문 layout: factory table01a766c0 name/01a766c4 factory
- 원문 layout: SpawnEntity vtable0121a590; target setter virtual+0x24
- 원문 layout: target string pointer01a74138→0125cb00
- 원문 layout: Actor392 symbol type0x2419fb6c
- 정정: 115/115 adjacency는 declared intent corroboration이며실제 native spawn call로 부르면 안 된다
- 정정: selected target setter005290e0과callback setter0045cd00은인자를보존하지않는stub임이 확인되어 authoritative 생성주장을 차단한다
- 한계: inventory max_stack1과 cooldown Charges2는 다른 수량이다
- 한계: Cam charge input3/config2 실제 사례가 있으므로 raw input을2로 clamp하지 않는다
- 한계: Cam numeric property/config150과 localized prose180은 충돌하며 prose로 numeric source를 덮어쓰지 않는다
- 한계: Scout Trap495/actor388은 Cam526/actor392와 별개
- 한계: ten activation rows의 instance identity는 unresolved이므로 proximity로 보충하지 않는다
- 한계: actual cooldown elapsed, server spawning 성공,owner lifetime/좌표 전파,한국어회복연고의 authoritative alias
- 한계: 기존 검증 범위: Flask/Cam 각각1,660 sync;조건부 활성화74/115;Cam115/115 뒤 동일 timestamp의새definition392 spawn 관찰, requested/spawn coordinate pairs는74/115만 일치
- 근거: [src-legacy-66473bba26c0](#src-legacy-66473bba26c0) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-115c58d88724](#src-legacy-115c58d88724) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-101d4f1bb6f5](#src-legacy-101d4f1bb6f5) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-58c0de22dc18](#src-legacy-58c0de22dc18) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-39db69cadeb8](#src-legacy-39db69cadeb8) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-a2358f682cf7](#src-legacy-a2358f682cf7) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.

### VGRE-item-sell-reject-prefix

**판매 요청과 구매 거절 알림의 한계**

044d payload14의 처음 두 BE32는 actor와 item instance이고 판매 요청 경로다. 048f payload6은 actor/item 없는 구매 거절 callback 알림이며 첫 바이트의 reason enum은 확정되지 않았다.

- 상태: bounded · 의미 확신: high · 검증: static_instructions, corpus_audit, synthetic_tests
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-reference`
- Opcode: `044d`, `048f`
- 함수/위치: `0x004d3f89` (win-x86-reference, preferred_va, selected source-documented function); `0x0081c200` (win-x86-reference, preferred_va, selected source-documented function); `0x009504f0` (win-x86-reference, preferred_va, selected source-documented function); `0x004d4f99` (win-x86-reference, preferred_va, selected source-documented function); `0x00529e00` (win-x86-reference, preferred_va, selected source-documented function); `0x005ce440` (win-x86-reference, preferred_va, selected source-documented function); `0x005ce000` (win-x86-reference, preferred_va, selected source-documented function)
- 원문 layout: 044d+0: actor BE32
- 원문 layout: 044d+4: instance BE32
- 원문 layout: 044d+8..13: opaque
- 원문 layout: 048f+0: uninterpreted byte
- 원문 layout: 048f+1..5: opaque
- 원문 layout: selected UI consumer: owner+0x20bd bit0x80 clear
- 한계: 044d 마지막6바이트와048f 마지막5바이트는 opaque
- 한계: 048f는 근처 요청이나 actor에 자동 귀속하지 않는다
- 한계: selected leaf callback만 보았으므로 모든 등록 callback의 전이적 no-op 증명이 아니다
- 한계: 판매 성공/환불, 모든 거절 사유, live callback 실행
- 한계: 기존 검증 범위: 56 recordings strict scan에서 044d326/326,048f11/11 rows 일치; 048f 정적 UI consumer 하나를 추가 추적
- 근거: [src-legacy-b07d3cee91f6](#src-legacy-b07d3cee91f6) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-026d9ced892c](#src-legacy-026d9ced892c) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-6e281d7ff695](#src-legacy-6e281d7ff695) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.

### VGRE-jungle-definition-1066

**Buff_JungleMinion_5v5_CrystalOrb**

Exact-build buff definition 1066 names Buff_JungleMinion_5v5_CrystalOrb, declares stack capacity 1 and policy 0; icon is icon_buff_orb_guardian_cp. Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x8f47b0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x21d24.
- 원문 layout: lookup2 seed12345678 name hash 0xf0f1a8a1; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-definition-1067

**Buff_JungleMinion_5v5_CrystalOrb_Lockout**

Exact-build buff definition 1067 names Buff_JungleMinion_5v5_CrystalOrb_Lockout, declares stack capacity 1 and policy 0; icon is icon_buff_orb_guardian_cp. Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x450910` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x21dbc.
- 원문 layout: lookup2 seed12345678 name hash 0x115dc56b; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-definition-1068

**Buff_JungleMinion_5v5_CrystalOrb_Effect**

Exact-build buff definition 1068 names Buff_JungleMinion_5v5_CrystalOrb_Effect, declares stack capacity 1 and policy 0; icon is (empty). Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x8f4a40` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x21e5c.
- 원문 layout: lookup2 seed12345678 name hash 0x321f3bd3; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-definition-1069

**Buff_JungleMinion_5v5_WeaponOrb**

Exact-build buff definition 1069 names Buff_JungleMinion_5v5_WeaponOrb, declares stack capacity 1 and policy 0; icon is icon_buff_orb_guardian_wp. Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x8f4ae0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x21ee4.
- 원문 layout: lookup2 seed12345678 name hash 0x69992acf; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-definition-1070

**Buff_JungleMinion_5v5_WeaponOrb_Effect**

Exact-build buff definition 1070 names Buff_JungleMinion_5v5_WeaponOrb_Effect, declares stack capacity 1 and policy 0; icon is (empty). Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x8f4dd0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x21f7c.
- 원문 layout: lookup2 seed12345678 name hash 0x8d311616; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-definition-220

**Buff_JungleMinion_TreeEnt_Restore**

Exact-build buff definition 220 names Buff_JungleMinion_TreeEnt_Restore, declares stack capacity 1 and policy 0; icon is icon_buff_treanthealing. Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x8f5740` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x7e6c.
- 원문 layout: lookup2 seed12345678 name hash 0xf7b2d182; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-definition-221

**Buff_JungleMinion_TreeEnt_Barrier**

Exact-build buff definition 221 names Buff_JungleMinion_TreeEnt_Barrier, declares stack capacity 1 and policy 0; icon is (empty). Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x8f5610` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x7f04.
- 원문 layout: lookup2 seed12345678 name hash 0x2e7f1ac6; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-definition-222

**Buff_JungleMinion_TreeEnt_Immobilize**

Exact-build buff definition 222 names Buff_JungleMinion_TreeEnt_Immobilize, declares stack capacity 1 and policy 0; icon is (empty). Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x8f56d0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x7f84.
- 원문 layout: lookup2 seed12345678 name hash 0x94d1f29f; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-definition-223

**Buff_JungleMinion_TreeEnt_RootField**

Exact-build buff definition 223 names Buff_JungleMinion_TreeEnt_RootField, declares stack capacity 1 and policy 0; icon is (empty). Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x8f5820` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x8008.
- 원문 layout: lookup2 seed12345678 name hash 0x9d5e13c; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-definition-224

**Buff_JungleMinion_TreeEnt_CancelRootOnDeath**

Exact-build buff definition 224 names Buff_JungleMinion_TreeEnt_CancelRootOnDeath, declares stack capacity 1 and policy 0; icon is (empty). Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x8f5670` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x808c.
- 원문 layout: lookup2 seed12345678 name hash 0xad257ec4; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-definition-225

**Buff_JungleMinion_CrystalMiner_CrystalAmp**

Exact-build buff definition 225 names Buff_JungleMinion_CrystalMiner_CrystalAmp, declares stack capacity 4 and policy 0; icon is icon_buff_crystal_miner. Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x8f4e70` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x8118.
- 원문 layout: lookup2 seed12345678 name hash 0x1cf09e09; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-definition-226

**Buff_JungleMinion_CrystalMiner_Defense**

Exact-build buff definition 226 names Buff_JungleMinion_CrystalMiner_Defense, declares stack capacity 1 and policy 0; icon is (empty). Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x8f50c0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x81b8.
- 원문 layout: lookup2 seed12345678 name hash 0x349ea62; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-definition-227

**Buff_JungleMinion_CrystalMiner_Empowerment**

Exact-build buff definition 227 names Buff_JungleMinion_CrystalMiner_Empowerment, declares stack capacity 1 and policy 0; icon is icon_buff_crystal_sentry. Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x8f5120` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x823c.
- 원문 layout: lookup2 seed12345678 name hash 0x3e3f6d73; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-definition-283

**타격 강화제 (Weapon Infusion)**

Exact-build buff definition 283 names Buff_Item_WeaponInfusion, declares stack capacity 12 and policy 0; icon is icon_item_weapon_infusion. Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x8f3b10` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x9e14.
- 원문 layout: lookup2 seed12345678 name hash 0x2b85b8d0; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-definition-284

**수정 강화제 (Crystal Infusion)**

Exact-build buff definition 284 names Buff_Item_CrystalInfusion, declares stack capacity 12 and policy 0; icon is icon_item_crystal_infusion. Factory registration is statically linked. production_ready remains false.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions, resource_decode
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x8ee7c0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 원문 layout: Resource 551BCB541D80053BACD0A897B7993A77 SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79, decoded definition offset 0x9ea4.
- 원문 layout: lookup2 seed12345678 name hash 0xfe03cbe2; not the ability/cooldown FNV1a key.
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-jungle-visual-identity

**Jungle visual identity**

CrystalOrb and WeaponOrb factories bind Effect_Blue_Buff and Effect_Red_Buff respectively through a client visual behavior. Resource actor localization GREEN/ORANGE is preserved separately. TreeEnt healing and older CrystalMiner families remain distinct.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x008f47b0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x008f4ae0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x005f8e20` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.

### VGRE-orb-acquisition-stub-boundary

**Orb acquisition stub boundary**

Selected orb death factories declare a90-second operand and buff name, but ApplyBuffToSelection helper setters do not store the arguments and execute is a stub in this client. No working kill-acquisition or automatic transfer follows from these declarations.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00883d40` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x008cd240` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00525a30` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0045cd00` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0045e8a0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 한계: Target-provider handle writer is not established as killer. Runtime duration and minimum/transfer behavior remain unverified.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.


## 쿨다운·clock·timer

### VGRE-ability-slot-ultimate-identity

**능력 슬롯과 궁극기 표시 순서**

초기 native ability slot은 definition list 순서이며 UI 세 번째 능력/궁극기와 universal slot2 관계가 아니다. Ringo C는 실제 resource와 localization으로 Hellfire Brew 궁극기에 연결되고 initial slot2/key0xcad52059가 도출된다.

- 상태: corrected · 의미 확신: high · 검증: resource_decode, static_instructions, corpus_audit
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0093fba0` (win-x86-laa, preferred_va, selected source-documented function); `0x0093f7d0` (win-x86-laa, preferred_va, selected source-documented function); `0x0093f270` (win-x86-laa, preferred_va, selected source-documented function); `0x0093cbf0` (win-x86-laa, preferred_va, selected source-documented function); `0x00858d10` (win-x86-laa, preferred_va, selected source-documented function)
- 원문 layout: Actor definition+0x4c: inline component definition, not pointer stored there
- 원문 layout: component definition+0x18 ability list; +0x24/+0x28/+0x2c UI selectors
- 원문 layout: component+0x28+4*slot native array; +0x78 display list; +0x164 count
- 원문 layout: ability+0x154 bits10..12 rank
- 원문 layout: property+4 base,+8 increment,+0xc rank5 extra
- 원문 layout: Ringo embedded ability INST+0xa5c; cooldown property0xcd0
- 정정: runtime add path는00858d10이며00958d10 오기가 아니다
- 정정: Krul first sync config0 vs definition base80은 base==모든048a config라는 가설을 반박한다
- 정정: Ringo C 의미를 C suffix만 보고 추정한 것이 아니라 original localization의 explicit ultimate reference로 보강했다
- 한계: Catherine initial list A_DefaultAttack,A,B,C 등에서 native slot2는B이며 third UI selector는3
- 한계: Ozo/Varya third UI는 native slot8
- 한계: Ringo key matching sync는 H5810에 없고 Krul C key0xee35beb6 sync168개만 관찰
- 한계: nominal Ringo90/80/70,Krul80/70/60은 learned rank1..3 property 연산이며 modifiers/timer start가 아니다
- 한계: runtime override 후 slot, Ringo actual cooldown, generic ultimate resolver
- 한계: 기존 검증 범위: 57 hero resources/255 embedded abilities;18 hero selectors가0/1/2와 다름;Ringo/ Krul 구체 key branch;7 source-invariant tests
- 근거: [src-legacy-66473bba26c0](#src-legacy-66473bba26c0) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-dd8d0c7f3e7d](#src-legacy-dd8d0c7f3e7d) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-5af109d2e37d](#src-legacy-5af109d2e37d) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-9eb65b2b4773](#src-legacy-9eb65b2b4773) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-398995e110f9](#src-legacy-398995e110f9) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.

### VGRE-buff-lifetime-create-reapply-stack-dispatch

**buff lifetime create reapply stack dispatch**

New factory-created buff dispatches Lifetime apply behavior; generic reapply and stack notification slots are stubs for Lifetime. Existing scripted handlers remain possible.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0094c9a0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x008659c0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00863050` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x008cef70` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00945bb0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x009477c0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0095f4d0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Action eligibility and factory success required
- 한계: No observed item buff execution
- 한계: Dynamic behavior update timing unresolved
- 한계: Only generic apply/inverse outer dispatch is closed. Prior unresolved exact active Scout modifiers and dynamic behavior-update timing remain unresolved.
- 근거: [src-buffstatus-4fdd371a12f4](#src-buffstatus-4fdd371a12f4) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-31336b548579](#src-buffstatus-31336b548579) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-f9777f46fbc2](#src-buffstatus-f9777f46fbc2) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-62c5d0f62db4](#src-buffstatus-62c5d0f62db4) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-365f1595b3c7](#src-buffstatus-365f1595b3c7) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-e77b0c4a391a](#src-buffstatus-e77b0c4a391a) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-fc6e1b76657f](#src-buffstatus-fc6e1b76657f) · Reviewed claim and its explicit conditional/static limits.

### VGRE-buff-lifetime-removal-expiry-dispatch

**buff lifetime removal expiry dispatch**

Removal0092d6a0 zeroes stacks, dispatches Lifetime inverse behavior, then marks state2. Timer expiry is flag/mode gated and can queue or skip direct removal.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0092d6a0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00948320` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00966410` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00967a20` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00954aa0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Timer<=0 alone does not imply removal
- 한계: Global0209e204 mode not independently named
- 한계: No replay runtime observation
- 한계: Only generic apply/inverse outer dispatch is closed. Prior unresolved exact active Scout modifiers and dynamic behavior-update timing remain unresolved.
- 근거: [src-buffstatus-4fdd371a12f4](#src-buffstatus-4fdd371a12f4) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-31336b548579](#src-buffstatus-31336b548579) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-f9777f46fbc2](#src-buffstatus-f9777f46fbc2) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-62c5d0f62db4](#src-buffstatus-62c5d0f62db4) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-365f1595b3c7](#src-buffstatus-365f1595b3c7) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-e77b0c4a391a](#src-buffstatus-e77b0c4a391a) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-fc6e1b76657f](#src-buffstatus-fc6e1b76657f) · Reviewed claim and its explicit conditional/static limits.

### VGRE-cooldown-expiry-overshoot-stage4

**만료 초과량과 재생성 타이머의 다음 순회**

선택된 stage4 tick은 subtraction 결과를 먼저 저장하고 finite <=0에서 callback을 호출한다. mode low2=0이며 strictly negative일 때 callback은 absolute overshoot를 state+0x3c에 보존한다. 선택 start path는 이를 한번 빼고 지우며, 정상 pool 순회 중 만들어진 replacement timer는 같은 순회에서 다시 tick되지 않는다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, synthetic_tests
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x009686d0` (win-x86-laa, preferred_va, selected source-documented function); `0x009519a0` (win-x86-laa, preferred_va, selected source-documented function); `0x00956380` (win-x86-laa, preferred_va, selected source-documented function); `0x009333b0` (win-x86-laa, preferred_va, selected source-documented function); `0x0095cd10` (win-x86-laa, preferred_va, selected source-documented function); `0x009613b0` (win-x86-laa, preferred_va, selected source-documented function); `0x0112b850` (win-x86-laa, preferred_va, selected source-documented function); `0x01129dd0` (win-x86-laa, preferred_va, selected source-documented function); `0x0112a080` (win-x86-laa, preferred_va, selected source-documented function); `0x0112a3c0` (win-x86-laa, preferred_va, selected source-documented function); `0x0112ade0` (win-x86-laa, preferred_va, selected source-documented function); `0x0112af70` (win-x86-laa, preferred_va, selected source-documented function); `0x0112afb0` (win-x86-laa, preferred_va, selected source-documented function)
- 원문 layout: state+0x1c callback subobject/vtable01280678
- 원문 layout: state+0x3c deferred overshoot
- 원문 layout: state+0x42 charge byte
- 원문 layout: state+0x44 low2 mode
- 원문 layout: constant0121cf5c float32 0.10000000149
- 원문 layout: pool+0x170 capacity/end low16,active high15
- 원문 layout: stage4 bulk slot entry+0x38 initialized null
- 정정: earlier untraced overshoot consumer와unknown ordinary same-stage retick 상태는 이 유한 확장으로 superseded
- 정정: scalar iterator만으로 optional bulk callback 부재를 단정했던 gap은 timer stage4 bulk slot zero initialization+registration trace로 제한적으로 닫혔다
- 정정: overshoot 완전 폐기와 즉시 무제한 catch-up 둘 다 근거 없음
- 한계: exact zero는 이전state+0x3c를 갱신하지 않는다; nonzero mode는 overshoot 저장 분기를 건너뛴다
- 한계: 009333b0는 ability+0x11c/+0x120 두 pointer만 순회하므로 primary+0x124에 일반화하지 않는다
- 한계: pending deletion은 sweep전 즉시 free slot을 만들지 않아 allocation failure 가능
- 한계: no-revisit는 normal initialized table/non-reentrant traversal/successful allocation 조건부
- 한계: 실제 expiry/recharge 영상, 모든 state+3c alias consumer, reentrant scheduler 또는 later callback-table mutation
- 한계: 기존 검증 범위: 추가7 model tests+bulk callback closure2, 전체 clock suite37; callback과 소비자 및 scalar/bulk 등록 연결이 닫힘
- 근거: [src-legacy-04a0c6efcf63](#src-legacy-04a0c6efcf63) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-8fe3c4ff7f7b](#src-legacy-8fe3c4ff7f7b) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-80ca2197b4ab](#src-legacy-80ca2197b4ab) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-a7d52092e883](#src-legacy-a7d52092e883) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.

### VGRE-cooldown-owner-key-identity

**소유자·키 기반 공유 쿨다운 상태**

쿨다운 state는 actor의 자식 목록에서 state+0x28 key로 조회된다. ability의 primary state+0x124, native slot, item instance는 별도 identity다. 같은 actor 아래 동일한 derived key를 쓰는 여러 item ability는 같은 state를 재사용할 수 있다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, resource_decode, controlled_runtime
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-laa`
- Opcode: `0428`, `0429`, `048a`, `044c`
- 함수/위치: `0x01129d20` (win-x86-laa, preferred_va, selected source-documented function); `0x01129dd0` (win-x86-laa, preferred_va, selected source-documented function); `0x0112a700` (win-x86-laa, preferred_va, selected source-documented function); `0x0093f270` (win-x86-laa, preferred_va, selected source-documented function); `0x0093f7d0` (win-x86-laa, preferred_va, selected source-documented function); `0x00940230` (win-x86-laa, preferred_va, selected source-documented function); `0x0093cdc0` (win-x86-laa, preferred_va, selected source-documented function); `0x008725f0` (win-x86-laa, preferred_va, selected source-documented function); `0x01129c00` (win-x86-laa, preferred_va, selected source-documented function); `0x00820f10` (win-x86-laa, preferred_va, selected source-documented function)
- 원문 layout: object+8 owner,+0xc child head,+0x10 sibling
- 원문 layout: state+0x28 key
- 원문 layout: ability+0x11c selected state alias; +0x124 primary; +0x120 secondary
- 원문 layout: component+0x28+4*slot ability array; +0x164 count
- 원문 layout: item+0x18 ability
- 원문 layout: abilityDefinition+0x18 primary group,+0x1c secondary group,+4 name,+0x6a mode
- 원문 layout: ability+0x128 override name
- 정정: 앞선 definition values unavailable은 Fountain과 후속 구체 사례에 한해 폐기됐지만 generic resolver는 여전히 미검증
- 정정: live r1 foreground refusal의 세 NOT_RUN은 후속 r2에서 세 bounded 사례 수행으로 대체됐다; 구 timer raw field의 잘못된 remaining 해석은 별도 다음 entry에서 정정
- 한계: primary+0x124와 secondary+0x120을 합치지 않는다
- 한계: FNV-1a는 signed-byte 연산 및 native fallback 분기를 따라야 하며 instance 번호를 hash하지 않는다
- 한계: state는 actor 소유라 item subtree 삭제만으로 자동 삭제되지 않지만 다른 explicit cleanup 부재는 증명하지 않았다
- 한계: 주소는 pool reuse 때문에 영구 lifetime identity가 아니다
- 한계: H5810에는 duplicate boots나 boots sale-all/rebuy 증거가 없어 별도 live 결과를 이 replay의 검증으로 재표시하면 안 된다
- 한계: 모든 ability/item key 조인, 임의 owner 수명, replay 시간정렬
- 한계: 기존 검증 범위: 같은 definition477 두 instance 공유, 판매 전체 뒤 rebuy 유지,477/478 별도 state의 세 practice 시나리오; Fountain487 key0x6f056481는 실제 resource와 native fallback으로 독립 도출 후206 sync로 corroborate
- 근거: [src-legacy-398995e110f9](#src-legacy-398995e110f9) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-1f058c438bde](#src-legacy-1f058c438bde) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-7632d10bac89](#src-legacy-7632d10bac89) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-ac1d27d0c366](#src-legacy-ac1d27d0c366) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-39db69cadeb8](#src-legacy-39db69cadeb8) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.

### VGRE-cooldown-replay-time-identifiability

**기록 시각만으로 쿨다운을 복원할 수 없는 이유**

일반 main-loop의 replay pump는 이전에 게시된 delta를 사용하고 stage4 timer는 새로 게시된 delta를 사용한다. record timestamp/order에는 playback frame partition과 queue/apply/tick 경계가 없으므로 정확한 remaining countdown은 유일하게 복원되지 않는다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, synthetic_tests
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x004c6990` (win-x86-laa, preferred_va, selected source-documented function); `0x004eb4a0` (win-x86-laa, preferred_va, selected source-documented function); `0x0112a7a0` (win-x86-laa, preferred_va, selected source-documented function); `0x0112b9e0` (win-x86-laa, preferred_va, selected source-documented function); `0x009686d0` (win-x86-laa, preferred_va, selected source-documented function); `0x0092c240` (win-x86-laa, preferred_va, selected source-documented function); `0x00931bd0` (win-x86-laa, preferred_va, selected source-documented function); `0x004c6380` (win-x86-laa, preferred_va, selected source-documented function); `0x0112b150` (win-x86-laa, preferred_va, selected source-documented function)
- 원문 layout: replay+0x0c scheduling cursor,+0x10 next record time,+4 pump mode
- 원문 layout: 020ec6d0 published scaled delta
- 원문 layout: 020ec6dc publication/stage guard
- 원문 layout: 020ec834 callback registration base
- 원문 layout: timer+0x28 pause
- 정정: 0112b9f7에서 guard!=0이면 publication만 생략하는 것이 아니라 stages3/4/5와 drains도 생략한다; stale delta로 stage4 tick한다는 설명은 틀리다
- 정정: 60×float32(1/60)와30×float32(1/30)은 테스트상 같은 정확 총합에도 repeated float32 subtraction 결과가 다르다
- 정정: H5810에서0427/0476/0451 부재는 playback pause/speed/seek 부재 증거가 아니다
- 한계: same timestamp group은 한 playback tick과 같지 않다
- 한계: pause byte, pump mode2, scale0, publication guard는 서로 다른 메커니즘
- 한계: raw delta cap2는 scale 적용 전이므로 scaled delta의 무조건2초 상한이 아니다
- 한계: normal finite float model 외 NaN, MXCSR/FTZ/DAZ, allocation failure를 일반화하지 않는다
- 한계: 새 native execution, 프레임 delta 실측, numerical replay confidence interval
- 한계: 기존 검증 범위: 기존 pinned clock receipts69개와 H5810입력168개 hash 검증; 후속 총37 standalone synthetic tests는 산술/순서 모델 검증
- 근거: [src-legacy-e5dd40aac2d1](#src-legacy-e5dd40aac2d1) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-5fb87d432e50](#src-legacy-5fb87d432e50) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-04a0c6efcf63](#src-legacy-04a0c6efcf63) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-8c544e50d99d](#src-legacy-8c544e50d99d) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-80ca2197b4ab](#src-legacy-80ca2197b4ab) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.

### VGRE-cooldown-timer-reference-hud

**타이머 본체 역참조와 HUD 숫자 변환**

state+0x20에는 timer body가 아니라 body+0x14 inner reference가 저장된다. timer-specific resolver로 body를 복구한 뒤 body+0x24가 remaining이다. 선택된 HUD formatter는 binary32(remaining+0.9900000095367432)를 truncating int로 변환하며 exact ceil과 다르다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, controlled_runtime, synthetic_tests
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x009613b0` (win-x86-laa, preferred_va, selected source-documented function); `0x00958d70` (win-x86-laa, preferred_va, selected source-documented function); `0x00541fa0` (win-x86-laa, preferred_va, selected source-documented function); `0x0093c860` (win-x86-laa, preferred_va, selected source-documented function); `0x009383d0` (win-x86-laa, preferred_va, selected source-documented function); `0x005c5290` (win-x86-laa, preferred_va, selected source-documented function); `0x005c51b0` (win-x86-laa, preferred_va, selected source-documented function); `0x009686d0` (win-x86-laa, preferred_va, selected source-documented function)
- 필드: inner_timer_reference = cooldown_state+32 (pointer to body+0x14)
- 필드: initial = timer_body+32 (float32)
- 필드: remaining = timer_body+36 (float32)
- 필드: pause = timer_body+40 (flag)
- 원문 layout: state+0x20 inner pointer = body+0x14
- 원문 layout: state+0x24 generation
- 원문 layout: body+0x20 initial,+0x24 remaining,+0x28 pause
- 원문 layout: timer body size0x2c; vtables0127ba9c/0127baac
- 원문 layout: inner virtual+8 resolver returns inner-0x14
- 원문 layout: 005c51e5 ADDSS;005c51f4 CVTTSS2SI
- 원문 layout: constant01227654 bits0x3f7d70a4
- 원문 layout: HUD overlay+0x638:1-remaining/initial
- 정정: 구 collector inner+0x24는 body+0x38로 timer size밖이었다; zero read는 실제 ready 증거가 아니다
- 정정: native82.829498은 선택 formatter에서83을 예측하므로 HUD82와 same-instant match라고 부르면 안 된다; 다음 bracket sample은 identity change로 무효
- 정정: short-middle과short-expiry는 post-expiry 관찰이며 양수 middle/정확 만료 frame이 아니다
- 정정: retention cap으로 expiry pairs가 없고 마지막 자동 three-stage 시도는0 stages였다
- 한계: generation equality만으로 inner pointer가 body이거나 full handle validity가 성립하지 않는다
- 한계: null/stale/pending/wrong-type/unreadable은 unavailable/unknown이지 ready zero가 아니다
- 한계: charge-gated getter는 charge!=0이면 running timer가 있어도0을 반환할 수 있다
- 한계: 샘플은 non-atomic이고 instrumented run timing만 검증한다
- 한계: formatter의 nonfinite/out-of-range conversion 및 모든 HUD branch는 미확정
- 한계: 정확한 expiry, 완성된 positive-middle HUD bracket, replay countdown accuracy
- 한계: 기존 검증 범위: corrected body의 양수 decreasing samples; 별도 stage4 호출22,160 중 retained unpaused800쌍은 float32 subtraction0 mismatch, 최소remaining25.450062
- 근거: [src-legacy-cb14c1897f23](#src-legacy-cb14c1897f23) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-30a1c379d62a](#src-legacy-30a1c379d62a) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-e171e36111f7](#src-legacy-e171e36111f7) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-04a0c6efcf63](#src-legacy-04a0c6efcf63) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.

### VGRE-cooldown-wire-fields

**쿨다운·충전 이벤트의 원시 필드**

0428/0429/048a는 owner와 서로 다른 lookup-key/ability-slot namespace 및 raw timer/config/charge 입력을 노출한다. wire 필드 추출은 resulting countdown·charges·실행 성공을 재구성하지 않는다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, corpus_audit, synthetic_tests
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-reference`, `win-x86-laa`
- Opcode: `0428`, `0429`, `048a`
- 함수/위치: `0x0081bb60` (win-x86-reference, preferred_va, selected source-documented function); `0x0081bb60` (win-x86-laa, preferred_va, selected source-documented function); `0x00945cc0` (win-x86-reference, preferred_va, selected source-documented function); `0x00945cc0` (win-x86-laa, preferred_va, selected source-documented function); `0x00945d70` (win-x86-reference, preferred_va, selected source-documented function); `0x00945d70` (win-x86-laa, preferred_va, selected source-documented function); `0x0081b8d0` (win-x86-reference, preferred_va, selected source-documented function); `0x0081b8d0` (win-x86-laa, preferred_va, selected source-documented function); `0x0094f170` (win-x86-reference, preferred_va, selected source-documented function); `0x0094f170` (win-x86-laa, preferred_va, selected source-documented function); `0x0052ad40` (win-x86-reference, preferred_va, selected source-documented function); `0x0052ad40` (win-x86-laa, preferred_va, selected source-documented function); `0x0052aea0` (win-x86-reference, preferred_va, selected source-documented function); `0x0052aea0` (win-x86-laa, preferred_va, selected source-documented function); `0x009401f0` (win-x86-reference, preferred_va, selected source-documented function); `0x009401f0` (win-x86-laa, preferred_va, selected source-documented function)
- 필드: 0428.owner = payload_after_opcode+0 (be_u32)
- 필드: 0428.lookup_key = payload_after_opcode+4 (be_u32)
- 필드: 0428.timer_operand = payload_after_opcode+8 (be_f32_bits)
- 필드: 0428.mode = payload_after_opcode+12 (u8)
- 필드: 0429.owner = payload_after_opcode+0 (be_u32)
- 필드: 0429.slot = payload_after_opcode+4 (be_u32)
- 필드: 0429.operand = payload_after_opcode+8 (be_u32)
- 필드: 0429.mode = payload_after_opcode+12 (u8)
- 필드: 048a.owner = payload_after_opcode+0 (be_u32)
- 필드: 048a.lookup_key = payload_after_opcode+4 (be_u32)
- 필드: 048a.timer_input = payload_after_opcode+8 (be_f32_bits)
- 필드: 048a.creation_config = payload_after_opcode+12 (be_f32_bits)
- 원문 layout: 0428+0 owner,+4 lookup key,+8 float bits,+12 mode,+13 opaque
- 원문 layout: 0429+0 owner,+4 ability slot,+8 operand u32,+12 mode,+13 opaque
- 원문 layout: 048a+0 owner,+4 key,+8 timer input bits,+12 creation config bits,+16 charge input,+17 config input,+18 masked flags,+19..21 exact-one inputs
- 정정: 0428/0429 mode0은 relative, 모든 nonzero는 direct static branch다; successful apply 주장 아님
- 정정: timeline decoded는 seconds/current charges/ownership 확인이 아니다
- 정정: 유일 H5810 코퍼스를 ZIP 이름이나 재검사 횟수로 새 independent observation 수에 더하지 않는다
- 한계: 0428/0429 payload14/content16,048a22/24만 관찰된 gate
- 한계: 0429 operand는 unsigned raw bits로 보존하며 signed arithmetic을 확정하지 않는다
- 한계: 048a timer input 다음 charge input 적용; configuration 일부는 새 object 생성시에만 적용
- 한계: 048a bytes19..21은 ==1 검사이며 generic nonzero truth가 아니다; byte18은 low2 mask와 raw를 모두 보존한다
- 한계: 독립 holdout, 상대0429/음수 산술 real 사례, countdown state
- 한계: 기존 검증 범위: H5810 development baseline168 sections/663,517 records;0428 1,859(상대645/직접1,214),0429 109,048a21,001;31/148 owner-key pairs의 config tuples 변화
- 근거: [src-legacy-ea2758c4086d](#src-legacy-ea2758c4086d) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-2a3ea8c63ec5](#src-legacy-2a3ea8c63ec5) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-baffd845ca14](#src-legacy-baffd845ca14) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-742c9eb3fd3c](#src-legacy-742c9eb3fd3c) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-b6cb4e0f9589](#src-legacy-b6cb4e0f9589) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-39db69cadeb8](#src-legacy-39db69cadeb8) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-06d5353318de](#src-legacy-06d5353318de) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.

### VGRE-deepening-combat-packed-override

**combat packed override**

Twenty packed entries at component+0x84 use first-inactive insertion, first-match single-level lookup and clear-all-matches. Slots store 15 bits; lookup/clear compare the unmasked operand. Full table insertion is a no-op; duplicate sources are possible.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00951d50` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00957260` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00871d70` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 원문 layout: Insertion truncates source but lookup/clear do not mask input; noncanonical source>32767 does not round-trip
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: Override apply requires resolved actor and global 0x0209e204 != 0; incoming play uses the opposite gate. Setup 0x004bff80 calls setter 0x0095da70 with zero; literal/direct-call scans cannot exclude alias or indirect writes.
- 한계: Historical payload suffixes remain opaque; no acknowledgement, hit success, causal transaction key or unique request/impact pairing. Numeric state transition requests may be rejected; dynamic behavior callbacks remain unresolved.
- 근거: [src-deepening-34c9e68da6ff](#src-deepening-34c9e68da6ff) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-8911ccbae0f8](#src-deepening-8911ccbae0f8) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-9d37dc38eb98](#src-deepening-9d37dc38eb98) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-2f20bcbf5127](#src-deepening-2f20bcbf5127) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-cooldown-buff-capacity-lifecycle

**cooldown buff capacity lifecycle**

Named ModifyMaxCharges methods change signed state+41 and current state+42 independently of base+40. Positive deltas grant current charges; negative deltas clamp only above the resulting cap. Lifetime wrappers dispatch addition/inverse methods.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0081d5c0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x009617e0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x009629b0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x009541b0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0093f1b0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0086ecb0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00810930` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x009477c0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00948320` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: Outer exact buff activation/removal/refresh timing remains unresolved; method labels describe arithmetic.
- 한계: Byte wrapping and signed/unsigned comparisons prevent unrestricted integer extrapolation.
- 한계: Not proof every replay charge input successfully applies.
- 근거: [src-deepening-763146dae926](#src-deepening-763146dae926) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-d4f1a88174ec](#src-deepening-d4f1a88174ec) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-37d63228f200](#src-deepening-37d63228f200) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-882cd47fa830](#src-deepening-882cd47fa830) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-b5a020905ffa](#src-deepening-b5a020905ffa) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-cooldown-buff-duration-modifiers

**cooldown buff duration modifiers**

Named ModifyMaxCooldown methods alter state+30/+34/+38 through add/multiply/override, inverse and new-minus-old/new-over-old update operations. Selected methods do not rewrite running timer state.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0081d600` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x009618c0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00962a90` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x009542d0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0093f210` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x005f9280` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0086bbf0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: Mode2 removal resets override -1, not saved prior override.
- 한계: Mode1 inverse/update has no local zero-divisor guard.
- 한계: No authoritative server stacking/uniqueness or full duration timing asserted.
- 근거: [src-deepening-763146dae926](#src-deepening-763146dae926) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-d4f1a88174ec](#src-deepening-d4f1a88174ec) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-37d63228f200](#src-deepening-37d63228f200) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-882cd47fa830](#src-deepening-882cd47fa830) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-b5a020905ffa](#src-deepening-b5a020905ffa) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-cooldown-effective-stat-flags

**cooldown effective stat flags**

0086bbf0 conditionally applies stat25 fractional reduction then divides by at least1 of stat15. Initial definition flags map to state+48; Flask/Cam flags0 bypass both, RingoC/KrulC lowbits3 enable stat25.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0086bbf0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0093f270` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0044e081` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: Initial creation only; existing shared state reuse does not reinitialize flags.
- 한계: Startup stat25 upper approx0.35 and lower -FLT_MAX do not prove immutable runtime caps.
- 한계: Nominal duration and start/remaining timer are distinct.
- 근거: [src-deepening-763146dae926](#src-deepening-763146dae926) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-d4f1a88174ec](#src-deepening-d4f1a88174ec) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-37d63228f200](#src-deepening-37d63228f200) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-882cd47fa830](#src-deepening-882cd47fa830) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-b5a020905ffa](#src-deepening-b5a020905ffa) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-cooldown-two-state-blocker-selector

**cooldown two state blocker selector**

00939d30 selects greatest charge-gated remaining among ability+11c/+120; a state with positive charge contributes zero. It does not directly examine+124.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00939d30` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0093c860` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: Not a universal cast eligibility/readiness predicate.
- 한계: Timer validity and object-lifetime preconditions retain prior collector corrections.
- 한계: No live HUD or authoritative successful cast evidence.
- 근거: [src-deepening-763146dae926](#src-deepening-763146dae926) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-d4f1a88174ec](#src-deepening-d4f1a88174ec) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-37d63228f200](#src-deepening-37d63228f200) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-882cd47fa830](#src-deepening-882cd47fa830) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-b5a020905ffa](#src-deepening-b5a020905ffa) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-scout-cam-upgrade-modifier-declarations

**scout cam upgrade modifier declarations**

Cam-targeted factories configure ScoutPak +1/-30; SuperScout extra +2/-30 by item property differences; Standard3v3 -1/-10. Resource527 declares both SuperScout and ScoutPak controls; conditional raw3 witness inventory includes527.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x008e25b0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x008f1410` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x008f2a00` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00867c60` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00867ca0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00867e10` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00867e70` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00939570` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0093f1b0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0093f210` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: Declaration and real native methods do not prove active buff lifetime or exact recorded capacity.
- 한계: Conditional totals3/120,5/90,1/140 assume unmodified base2/150 and named controls applied once.
- 한계: H5810 executable build remains unknown; inventory association is conditional.
- 근거: [src-deepening-763146dae926](#src-deepening-763146dae926) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-d4f1a88174ec](#src-deepening-d4f1a88174ec) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-37d63228f200](#src-deepening-37d63228f200) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-882cd47fa830](#src-deepening-882cd47fa830) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-b5a020905ffa](#src-deepening-b5a020905ffa) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-replay-game-clock-anchor-display

**게임 시계 앵커·재생 누적·화면 시간**

046f payload+64는 native game-clock anchor이며 바깥 record timestamp와 다르다. 선택된 Windows 경로에서 anchor 사이의 game clock은 published delta와 simulation scale을 곱해 누적·float32 저장하고 final formatter는 이 누적된 값을 받는다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, controlled_runtime
- 경계: reviewed_legacy_family / not_applicable / historical_mixed_evidence
- 정확한 파일: `win-x86-reference`, `win-x86-laa`
- Opcode: `046f`, `0451`, `03f1`
- 함수/위치: `0x00549470` (win-x86-reference, preferred_va, selected source-documented function); `0x00549470` (win-x86-laa, preferred_va, selected source-documented function); `0x005497a0` (win-x86-reference, preferred_va, selected source-documented function); `0x005497a0` (win-x86-laa, preferred_va, selected source-documented function); `0x0073a770` (win-x86-reference, preferred_va, selected source-documented function); `0x0073a770` (win-x86-laa, preferred_va, selected source-documented function); `0x004cb590` (win-x86-reference, preferred_va, selected source-documented function); `0x004cb590` (win-x86-laa, preferred_va, selected source-documented function); `0x009546f0` (win-x86-reference, preferred_va, selected source-documented function); `0x009546f0` (win-x86-laa, preferred_va, selected source-documented function)
- 원문 layout: 046f payload+64: game-clock float
- 원문 layout: controller+0x194: game clock
- 원문 layout: controller+0x19d bit0: clock gate
- 원문 layout: 020ec6d0 published delta
- 원문 layout: 01a761b0 simulation scale double
- 정정: 역사적33초/2초 화면 차이는 해당 run의 last-anchor 이후 speed/tick 누적으로 설명되며 고정 교정값이 아니다
- 정정: H5672의 화면10:00/clock600.34130859375와 query600의 exact record boundary를 같다고 하지 않는다
- 한계: record time, anchor-projected time, observed game clock, integer UI label은 별개
- 한계: 5x는 game-clock 경로에 근거가 있을 때만 적용하며 cooldown timer에 추가5배를 전이하지 않는다
- 한계: 마지막 record interval×5는 실제 tick sequence가 아니다
- 한계: writer가0451 resync를 제외하므로 파일의 부재가 live setter 부재를 뜻하지 않는다
- 한계: 원본 recorder simulation history, server-final duration, universal display correction
- 한계: 기존 검증 범위: 046f13 original-record controls; 후속 두 full replay의35,360/32,606 consecutive tick transitions bit-exact,153/152 anchors와 final formatter 연계
- 근거: [src-legacy-5cc7fe753b75](#src-legacy-5cc7fe753b75) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-5468275020d0](#src-legacy-5468275020d0) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-21fa1d248d2a](#src-legacy-21fa1d248d2a) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-767b08816437](#src-legacy-767b08816437) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.
- 근거: [src-legacy-e5dd40aac2d1](#src-legacy-e5dd40aac2d1) · Selected claim and limitations in this source; historical status may be superseded by the listed corrections.


## 게임 요청과 전송

### VGRE-deepening-combat-041a

**combat 041a**

Opcode 041a consumes a 13-byte native prefix. Guarded override insertion/clear helper semantics are established; historical application is unverified.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- Opcode: `041a`
- 함수/위치: `0x004d1520` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0081bda0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0094fc20` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00951d50` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x008177c0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 필드: actor_raw = payload_after_opcode+0 (be_u32); Native consumed prefix only; opaque suffix not assigned semantics.
- 필드: original_slot_raw = payload_after_opcode+4 (be_u32); Native consumed prefix only; opaque suffix not assigned semantics.
- 필드: replacement_slot_raw = payload_after_opcode+8 (be_u32); Native consumed prefix only; opaque suffix not assigned semantics.
- 필드: control_raw_nonzero_normalized = payload_after_opcode+12 (u8); Native consumed prefix only; opaque suffix not assigned semantics.
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: Override apply requires resolved actor and global 0x0209e204 != 0; incoming play uses the opposite gate. Setup 0x004bff80 calls setter 0x0095da70 with zero; literal/direct-call scans cannot exclude alias or indirect writes.
- 한계: Historical payload suffixes remain opaque; no acknowledgement, hit success, causal transaction key or unique request/impact pairing. Numeric state transition requests may be rejected; dynamic behavior callbacks remain unresolved.
- 근거: [src-deepening-34c9e68da6ff](#src-deepening-34c9e68da6ff) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-8911ccbae0f8](#src-deepening-8911ccbae0f8) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-9d37dc38eb98](#src-deepening-9d37dc38eb98) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-2f20bcbf5127](#src-deepening-2f20bcbf5127) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-combat-041b

**combat 041b**

Opcode 041b consumes a 8-byte native prefix. Guarded override insertion/clear helper semantics are established; historical application is unverified.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- Opcode: `041b`
- 함수/위치: `0x004d1590` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0081a370` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0094cf80` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00871d70` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00814ac0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 필드: actor_raw = payload_after_opcode+0 (be_u32); Native consumed prefix only; opaque suffix not assigned semantics.
- 필드: original_slot_raw = payload_after_opcode+4 (be_u32); Native consumed prefix only; opaque suffix not assigned semantics.
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: Override apply requires resolved actor and global 0x0209e204 != 0; incoming play uses the opposite gate. Setup 0x004bff80 calls setter 0x0095da70 with zero; literal/direct-call scans cannot exclude alias or indirect writes.
- 한계: Historical payload suffixes remain opaque; no acknowledgement, hit success, causal transaction key or unique request/impact pairing. Numeric state transition requests may be rejected; dynamic behavior callbacks remain unresolved.
- 근거: [src-deepening-34c9e68da6ff](#src-deepening-34c9e68da6ff) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-8911ccbae0f8](#src-deepening-8911ccbae0f8) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-9d37dc38eb98](#src-deepening-9d37dc38eb98) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-2f20bcbf5127](#src-deepening-2f20bcbf5127) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-deepening-combat-0425

**combat 0425**

Opcode 0425 consumes a 4-byte native prefix. When selected actor and required child component resolve, updates/clears the selected player actor target handle; unresolved target then clears selection. No caster, request sequence or success byte is consumed.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- Opcode: `0425`
- 함수/위치: `0x004d3ac2` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x005296f0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x005297a0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00597190` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 필드: target_actor_raw = payload_after_opcode+0 (be_u32); Native consumed prefix only; opaque suffix not assigned semantics.
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: Override apply requires resolved actor and global 0x0209e204 != 0; incoming play uses the opposite gate. Setup 0x004bff80 calls setter 0x0095da70 with zero; literal/direct-call scans cannot exclude alias or indirect writes.
- 한계: Historical payload suffixes remain opaque; no acknowledgement, hit success, causal transaction key or unique request/impact pairing. Numeric state transition requests may be rejected; dynamic behavior callbacks remain unresolved.
- 근거: [src-deepening-34c9e68da6ff](#src-deepening-34c9e68da6ff) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-8911ccbae0f8](#src-deepening-8911ccbae0f8) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-9d37dc38eb98](#src-deepening-9d37dc38eb98) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-2f20bcbf5127](#src-deepening-2f20bcbf5127) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-request-ability-layouts

**0411/0412/0413 능력 요청**

0411은 target-or-sentinel + ability-array index, 0412는 3D vector + index, 0413은 target word + vector + index다. index는 component+0x28+4*index를 선택하며 definition ID나 보편 A/B/C 이름이 아니다.

- 상태: supported · 의미 확신: high · 검증: static_instructions
- 경계: client_native / client_outgoing_request / static_only
- 정확한 파일: `win-x86-laa`
- Opcode: `0411`, `0412`, `0413`
- 함수/위치: `0x0094c1a0` (win-x86-laa, preferred_va, ability outgoing method); `0x00937010` (win-x86-laa, preferred_va, ability-array accessor); `0x00965fb0` (win-x86-laa, preferred_va, ability pointer to array index); `0x008181c0` (win-x86-laa, preferred_va, 0411 formatter); `0x008182c0` (win-x86-laa, preferred_va, 0412 formatter); `0x008183c0` (win-x86-laa, preferred_va, 0413 formatter)
- 필드: 0411.target = payload_after_opcode+0 (be_u32)
- 필드: 0411.index = payload_after_opcode+4 (u8)
- 필드: 0412.vector = payload_after_opcode+0 (3 x be_f32_bits)
- 필드: 0412.index = payload_after_opcode+12 (u8)
- 필드: 0413.target = payload_after_opcode+0 (be_u32)
- 필드: 0413.vector = payload_after_opcode+4 (3 x be_f32_bits)
- 필드: 0413.index = payload_after_opcode+16 (u8)
- 한계: 0413 concrete mode-2 UI producer는 이 조사에서 확립하지 않았다.
- 한계: mode는 opcode로 선택되고 별도 payload mode byte가 아니다.
- 한계: H5810에는 0411/12/13 관측이 없으며 요청/결과 transaction key도 미확정이다.
- 근거: [src-requests](#src-requests) · Hero ability: 0411 / 0412 / 0413

### VGRE-request-item-layouts

**0448/0449/044a 아이템 요청**

0448은 item-instance BE32, 0449는 target actor BE32 + item-instance BE32, 044a는 vector 3개 + item-instance BE32다. 활성 actor나 결과 성공 여부는 이 compact payload에 없다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions
- 경계: client_native / client_outgoing_request / static_only
- 정확한 파일: `win-x86-laa`
- Opcode: `0448`, `0449`, `044a`
- 함수/위치: `0x00529ff0` (win-x86-laa, preferred_va, item outgoing method); `0x00813dc0` (win-x86-laa, preferred_va, 0448 formatter); `0x00813fc0` (win-x86-laa, preferred_va, 0449 formatter); `0x00813ec0` (win-x86-laa, preferred_va, 044a formatter)
- 필드: 0448.item_instance = payload_after_opcode+0 (be_u32)
- 필드: 0449.target_actor = payload_after_opcode+0 (be_u32)
- 필드: 0449.item_instance = payload_after_opcode+4 (be_u32)
- 필드: 044a.vector = payload_after_opcode+0 (3 x be_f32_bits)
- 필드: 044a.item_instance = payload_after_opcode+12 (be_u32)
- 정정: 0449는 actor-bearing request다. 플레이어가 UI에서 직접 target을 골랐다는 증거가 아니다.
- 한계: instance ID는 definition ID·inventory index·UI slot과 다르다.
- 한계: 044c를 모든 요청의 성공 ack로 취급하지 않는다.
- 근거: [src-requests](#src-requests) · Item activation request layouts: 0448 / 0449 / 044a
- 근거: [src-item_target](#src-item_target) · Corrected conclusion
- 근거: [src-artifact-da8bbbcf712e](#src-artifact-da8bbbcf712e) · whole artifact; content remains external
- 근거: [src-artifact-70309fe0bcf8](#src-artifact-70309fe0bcf8) · whole artifact; content remains external

### VGRE-request-movement-attack

**이동 3종과 공격 대상 선택**

03f4/03f5/03f6은 vector 성분 0과 2만 보내는 8-byte payload다. 0424는 target actor BE32와 의미 미지정 flag 1 byte다.

- 상태: supported · 의미 확신: high · 검증: static_instructions
- 경계: client_native / client_outgoing_request / static_only
- 정확한 파일: `win-x86-laa`
- Opcode: `03f4`, `03f5`, `03f6`, `0424`
- 함수/위치: `0x00597040` (win-x86-laa, preferred_va, movement producer); `0x0052a420` (win-x86-laa, preferred_va, movement request); `0x00599a50` (win-x86-laa, preferred_va, attack target producer); `0x0052a320` (win-x86-laa, preferred_va, attack target request)
- 필드: movement_component_0 = payload_after_opcode+0 (be_f32_bits)
- 필드: movement_component_2 = payload_after_opcode+4 (be_f32_bits)
- 필드: attack_target_actor = payload_after_opcode+0 (be_u32)
- 필드: attack_raw_flag = payload_after_opcode+4 (u8)
- 한계: movement에는 explicit actor ID가 없다.
- 한계: 좌표 단위·축 이름·control flag 의미·공격 hit 성공은 미확정이다.
- 근거: [src-requests](#src-requests) · Movement: 03f4 / 03f5 / 03f6; Basic-attack target selection: 0424

### VGRE-request-plain-frame

**게임 요청 compact frame**

변환 전 frame은 BE16(content length=payload+2), BE16 opcode, payload다. 요청 packer는 조건부 transform을 허용하며 CipherDelegateBlowfish가 있으면 content를 8-byte 단위 zero-pad 후 변환한다.

- 상태: supported · 의미 확신: high · 검증: static_instructions
- 경계: client_native / client_outgoing_request / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0097f760` (win-x86-laa, preferred_va, rounded content size); `0x0097f6d0` (win-x86-laa, preferred_va, conditional transform)
- 필드: content_length = plain_network_frame+0 (be_u16)
- 필드: opcode = plain_network_frame+2 (be_u16)
- 필드: payload = plain_network_frame+4 (bytes)
- 한계: 키·session 값·handshake는 범위 밖이며 사전에 포함하지 않는다.
- 한계: VGR timestamp/BE32 length와 별개다. Plain schema는 live plaintext 주장도 아니다.
- 근거: [src-requests](#src-requests) · 2. Shared frame and conditional transform

### VGRE-request-send-replay-boundary

**전송 facade와 replay no-send 분기**

004eb2d0가 선택한 KindredNetworking은 조건부 버퍼·socket send로 가지만 KindredReplay의 같은 +0x30 slot은 전송 없이 1을 반환한다. 생성된 요청·참을 반환한 facade·기록 속 opcode는 실제 전송/성공과 같지 않다.

- 상태: supported · 의미 확신: high · 검증: static_instructions
- 경계: client_native / client_outgoing_request / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x004eb2d0` (win-x86-laa, preferred_va, transport selection); `0x004eb3f0` (win-x86-laa, preferred_va, send facade); `0x004eb580` (win-x86-laa, preferred_va, network send); `0x004eb5d0` (win-x86-laa, preferred_va, replay no-send); `0x00984ba0` (win-x86-laa, preferred_va, send buffer); `0x0096f030` (win-x86-laa, preferred_va, WS2_32 send wrapper); `0x00931bd0` (win-x86-laa, preferred_va, queue drain)
- 한계: 서버 수락·handshake·목적지·현재 가용성은 검증하지 않았다.
- 한계: incoming byte+0x0c=1은 apply +8, outgoing 0은 request +4로 간다.
- 근거: [src-requests](#src-requests) · 1. Direction and transport boundary; 4. Queue and response limits


## 플랫폼 JSON schema

### VGRE-platform-authenticate-command

**authenticate는 executeCommand 인수**

확인된 인증 경로의 URL/envelope method는 executeCommand이고 params는 provider, literal authenticate, 인증 object를 문자열화한 값이다. 내부 credentials는 JSON으로 parse/re-emit된다.

- 상태: supported · 의미 확신: high · 검증: static_instructions
- 경계: platform_json_rpc / client_request_response / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x004f15e0` (win-x86-laa, preferred_va, concrete caller); `0x009b4820` (win-x86-laa, preferred_va, authentication object builder); `0x0098b3b0` (win-x86-laa, preferred_va, three-string serializer)
- 한계: credential subtype/키·실제 값·암호학적 의미·현재 서버 동작은 미확정이다.
- 한계: 이 사전에는 credential 값이나 세션 상태가 없다.
- 근거: [src-platform](#src-platform) · 6. executeCommand / authenticate

### VGRE-platform-credential-capable-identity

**첫 RPC parameter는 credential일 수 있음**

공유 reader는 playerUUID와 뒤의 sessionToken을 같은 platform+0x2570에 기록한다. 일반 요청은 flag에 따라 +0x2570 또는 +0x25d4를 선택한다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions
- 경계: platform_json_rpc / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0099ed10` (win-x86-laa, preferred_va, bootstrap response consumer)
- 필드: request_identity_or_session = PlatformInterface+9584 (string)
- 필드: alternate_identity = PlatformInterface+9684 (string)
- 정정: params[0]을 stable public player ID로 export/log하지 않는다.
- 한계: alternate string 전체 provenance는 미확정이며 실제 값은 읽거나 싣지 않는다.
- 근거: [src-platform](#src-platform) · Identity source
- 근거: [src-network](#src-network) · Account/session and dynamic metadata

### VGRE-platform-json-envelope

**플랫폼 JSON envelope**

00995390은 method/params envelope와 /JSONRpc/method URL을 구성한다. JSON value tree가 직렬화되며 callback type 5/10/11/13은 로컬 query discriminator다.

- 상태: supported · 의미 확신: high · 검증: static_instructions
- 경계: platform_json_rpc / client_request_response / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00995390` (win-x86-laa, preferred_va, request builder); `0x00991920` (win-x86-laa, preferred_va, 24-byte JSON value append); `0x00999ba0` (win-x86-laa, preferred_va, JSON serializer); `0x0099d720` (win-x86-laa, preferred_va, callback dispatcher)
- 한계: jsonrpc/id member가 확인되지 않아 JSON-RPC 2.0이라고 단정하지 않는다.
- 한계: callback type을 gameplay opcode나 HTTP parameter로 해석하지 않는다.
- 한계: 비동기 enqueue 성공은 server success가 아니다.
- 근거: [src-platform](#src-platform) · 1. Shared framing, identity and callback dispatch
- 근거: [src-network](#src-network) · Request framing and response dispatch

### VGRE-platform-lobby-party-pending

**lobby·party·pending의 서로 다른 schema**

joinLobby는 identity + 문자열화 options JSON + version string이다. queryPendingMatch와 queryPartyInfo는 각각 identity string 하나만 보낸다. pending은 명명된 matchId/playerUUID를, party는 partyUUID/member uuid를 읽는다.

- 상태: supported · 의미 확신: high · 검증: static_instructions
- 경계: platform_json_rpc / client_request_response / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0099cd60` (win-x86-laa, preferred_va, joinLobby); `0x00998350` (win-x86-laa, preferred_va, inner lobby object); `0x009b7cc0` (win-x86-laa, preferred_va, queryPendingMatch); `0x009aa050` (win-x86-laa, preferred_va, pending reader); `0x009b79a0` (win-x86-laa, preferred_va, queryPartyInfo); `0x009a96e0` (win-x86-laa, preferred_va, party reader)
- 한계: lobby response reader는 matchId/host/roster를 읽지 않는다.
- 한계: party roster는 최종 match roster가 아니며 uuid/playerUUID/replay actor 동등성은 미확정이다.
- 한계: sites latency survey는 임의 combat server override 계약이 아니다.
- 근거: [src-platform](#src-platform) · 3. joinLobby; 4. queryPendingMatch; 5. queryPartyInfo

### VGRE-platform-match-state-quality

**명명된 matchId와 품질 telemetry**

shared state의 matchId는 embedded-state+0x9c와 exposed-state+0x94의 같은 위치다. 구체 match-end caller가 이 값과 maxPing/numPingSpikes 등을 recordMatchExperienceMetrics에 전달한다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions
- 경계: platform_json_rpc / client_request_response / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0099f8d0` (win-x86-laa, preferred_va, state reader); `0x00548c90` (win-x86-laa, preferred_va, match-end caller); `0x009b8c20` (win-x86-laa, preferred_va, recordMatchExperienceMetrics); `0x0098c3c0` (win-x86-laa, preferred_va, quality serializer)
- 정정: 품질 telemetry는 authoritative win/loss/ranking upload가 아니다.
- 한계: notifyGameResults/updateMatchInfo는 이 trace에서 concrete gameplay producer를 확립하지 못했다.
- 한계: 명명된 matchId와 replay filename UUID의 동등성은 검증되지 않았다.
- 근거: [src-network](#src-network) · Match state is the most useful non-secret boundary; What the match-end report actually proves
- 근거: [src-platform](#src-platform) · 7. Match identity, state and remaining unknowns

### VGRE-platform-start-session

**startSessionForPlayer 11개 값**

구체 caller의 배열은 identity/session, decimal version string, device integer, 의미 미지정 system string, production, language, OS, marketplace, hardwareIdName, hardwareName, hardwareIDFA의 11개 위치다.

- 상태: supported · 의미 확신: high · 검증: static_instructions
- 경계: platform_json_rpc / client_request_response / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x004f0920` (win-x86-laa, preferred_va, concrete caller); `0x009bb5c0` (win-x86-laa, preferred_va, method); `0x0098ab80` (win-x86-laa, preferred_va, positional serializer); `0x009b10b0` (win-x86-laa, preferred_va, type-5 response reader)
- 한계: index 3은 deviceId/UUID/token으로 명명하지 않는다.
- 한계: generic serializer의 null C-string 생략은 server optional parameter 규칙을 뜻하지 않는다.
- 한계: client response reader 타입은 server-side 필수성/유효범위 증거가 아니다.
- 근거: [src-platform](#src-platform) · 2. startSessionForPlayer
- 근거: [src-artifact-93f6a2f696d5](#src-artifact-93f6a2f696d5) · whole artifact; content remains external
- 근거: [src-artifact-8fb88e8a572e](#src-artifact-8fb88e8a572e) · whole artifact; content remains external


## Android 패키지와 routing

### VGRE-android-match-socket-observation

**connect hook은 원래 목적지 관측**

wrapper connect는 원래 sockaddr/길이로 원본 connect를 먼저 호출한다. 이후 AF_INET/AF_INET6, port7000..7999와 return/errno를 검사해 관측 callback을 보낸다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions
- 경계: android_native / socket_observation / static_only
- 정확한 파일: `android-vgna-1-11`, `android-vgna-wrapper`, `android-vgna-unlock`
- 함수/위치: `0x4bc8` (android-vgna-wrapper, elf_va, connect wrapper); `0xe644` (android-vgna-unlock, elf_va, match socket observer)
- 정정: VGNA integration/replay backend 존재를 authoritative combat server 교체와 같게 취급하지 않는다.
- 한계: EINPROGRESS도 보고하므로 handshake 성공이나 authoritative combat 연결 증거가 아니다.
- 한계: event label tcp만으로 실제 socket type을 증명하지 않는다.
- 한계: 이 hook에는 목적지 rewrite가 없지만 모든 engine 경로 부재 증명은 아니다.
- 근거: [src-routing](#src-routing) · 3. Match-socket hooks are observational

### VGRE-android-matched-base-delta

**원본과 VGNA의 한정된 변경 범위**

VGNA 1.11은 비교한 원본 4.13.4(147219) 기반을 유지한다. stock 코드 method 2개 변경, 새 VGNA DEX 339 classes, ARM64 wrapper/helper 추가, retained engine 두 site의 14 bytes 변경이 확인됐다.

- 상태: supported · 의미 확신: high · 검증: file_hash, static_instructions, package_comparison
- 경계: android_package / not_applicable / static_only
- 정확한 파일: `android-vgna-1-11`, `android-original-147219`, `android-vgna-classes2`, `android-vgna-unlock`, `android-vgna-wrapper`, `android-vgna-real-engine`
- 한계: ARM32 game library와 FMOD 동일성은 추가 ARM64/Java layer 영향 부재를 뜻하지 않는다.
- 한계: 패키지 크기 증가 대부분은 압축 변화다.
- 한계: release-evidence의 과거 1.09 scan은 이 1.11 파일을 커버하지 않는다.
- 한계: 공식 배포 여부·서명 검증과 malware 판정/설치 정책 인증은 다르다.
- 근거: [src-android](#src-android) · Acquisition and matched base; Executable and asset delta

### VGRE-android-region-routing

**region bootstrap은 고정 routing**

ARM64 helper는 region enum 0..4와 네 account/session operation을 고정 host URL로 바꾼다. 임의 combat host/port 입력은 이 경로에서 확인되지 않았다.

- 상태: supported · 의미 확신: high · 검증: static_instructions
- 경계: android_native / client_request_response / static_only
- 정확한 파일: `android-vgna-1-11`, `android-vgna-unlock`, `android-vgna-real-engine`
- 함수/위치: `0x1a0bc` (android-vgna-unlock, elf_va, HTTP option hook); `0x1a720` (android-vgna-unlock, elf_va, region selection)
- 한계: actual response·redirect·성공·stock match assignment→combat socket 전체 경로는 미확정이다.
- 한계: 원래 response callback을 새 parser로 대체하는 경로는 관측되지 않았다.
- 근거: [src-routing](#src-routing) · 1. Region-bootstrap inputs; 2. What the HTTP hook changes
- 근거: [src-artifact-ff19690bf970](#src-artifact-ff19690bf970) · whole artifact; content remains external


## VGNA replay upload

### VGRE-upload-identity-events

**identity event의 출처와 응답**

event JSON은 event sequence/time, 선택 mode와 optional player/match 문맥을 갖는다. runtime_phase/queue_active를 덮어쓰지만 payload는 open-ended다. 응답 소비는 2xx JSON과 directives이며 필수 event ack 필드는 없다.

- 상태: supported · 의미 확신: high · 검증: static_instructions
- 경계: identity_telemetry / client_request_response / static_only
- 정확한 파일: `android-vgna-1-11`, `android-vgna-classes2`
- 함수/위치: `0x19a2c` (android-vgna-classes2, dex_file_offset, VGNAIdentity worker); `0x1d188` (android-vgna-classes2, dex_file_offset, postJson)
- 한계: install_id/player_uuid/platform_match_uuid/replayId/epoch/entity_id는 별개 namespace다.
- 한계: client 필드 생성은 서버 검증·계정 소유·현재 서비스 응답 증거가 아니다.
- 한계: event sequence로 replay byte 순서를 만들지 않는다.
- 근거: [src-upload](#src-upload) · 1. Identity events; Identity scope and adapter boundary

### VGRE-upload-policy-bounded-gap

**continuous upload policy 연결은 미확정**

traced Java startup/tick/tail/connect와 native recorder publisher/getter에서 upload-mode 검사가 확인되지 않았다. 유일한 native policy-file consumer는 retired numbered path에서 파일 내용을 읽고 사용하지 않는다.

- 상태: bounded · 의미 확신: medium · 검증: static_instructions
- 경계: upload_policy / not_applicable / static_only
- 정확한 파일: `android-vgna-1-11`, `android-vgna-classes2`, `android-vgna-unlock`
- 함수/위치: `0x12bf8` (android-vgna-unlock, elf_va, retired policy-file consumer); `0x1218c` (android-vgna-unlock, elf_va, recorder JNI getter); `0x213f4` (android-vgna-unlock, elf_va, recorder cache publisher); `0x26f98` (android-vgna-unlock, elf_va, lifecycle wrapper)
- 한계: 특정 traced path의 missing link이며 실제 upload·전체 privacy bug·모든 server/runtime gate 부재 증거가 아니다.
- 한계: completed-only service 경로에는 별도 mode 검사가 있다.
- 한계: dedicated policy GET의 legacy fallback과 event directive의 invalid-mode 무시는 서로 다르다.
- 근거: [src-upload](#src-upload) · Upload preference: bounded conclusion
- 근거: [src-upload_native](#src-upload_native) · Native upload-policy file: actual consumer; Continuous recorder state exposure and gates

### VGRE-upload-terminal-hero-only

**terminal_scoreboard는 entity→hero만**

native terminal array의 각 행은 entity_id와 hero만 포함한다. Java가 terminal_scoreboard envelope를 만든다. native cache는 작은 후속 snapshot보다 이전의 더 큰 snapshot을 유지할 수 있다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions
- 경계: terminal_metadata / client_upload / static_only
- 정확한 파일: `android-vgna-1-11`, `android-vgna-classes2`, `android-vgna-unlock`, `android-vgna-real-engine`
- 함수/위치: `0x12398` (android-vgna-unlock, elf_va, nativeNearLiveTerminalScoreboard); `0x25cd4` (android-vgna-unlock, elf_va, terminal capture); `0x236d0` (android-vgna-classes2, dex_file_offset, Java finishLocked terminal builder)
- 정정: K/D/A·account ID·team·gold·damage·winner를 이 schema에서 얻을 수 없다.
- 한계: 0..16행, entity 1..4294967294, hero 1..64 printable ASCII이며 quote/backslash 제외다.
- 한계: hero string은 canonical server hero ID로 증명되지 않았다.
- 한계: invalid row는 제외되고 0 rows는 []다. JNI allocation 실패 null과 구별한다.
- 근거: [src-upload](#src-upload) · terminal_scoreboard
- 근거: [src-upload_native](#src-upload_native) · Exact terminal JSON schema; Row provenance, validation, and snapshot retention
- 근거: [src-artifact-bed88cb623ea](#src-artifact-bed88cb623ea) · whole artifact; content remains external
- 근거: [src-artifact-c013d8dd6732](#src-artifact-c013d8dd6732) · whole artifact; content remains external

### VGRE-upload-vgnl-frame

**VGNL 68-byte transport header**

VGNL v1 application frame은 68-byte big-endian header 뒤 complete native records를 싣는다. epoch/sequence는 transport namespace이고 CRC32는 payload 전체에만 적용된다.

- 상태: supported · 의미 확신: high · 검증: static_instructions, synthetic_tests
- 경계: replay_transport / client_upload / static_only
- 정확한 파일: `android-vgna-1-11`, `android-vgna-classes2`
- 함수/위치: `0x22bec` (android-vgna-classes2, dex_file_offset, VGNALiveReplayProducer.frame); `0x241dc` (android-vgna-classes2, dex_file_offset, tail complete records)
- 필드: magic = VGNL_application_frame+0 (ASCII VGNL)
- 필드: version = VGNL_application_frame+4 (u8)
- 필드: kind = VGNL_application_frame+5 (u8)
- 필드: flags = VGNL_application_frame+6 (be_u16)
- 필드: epoch = VGNL_application_frame+8 (16 raw UUID bytes)
- 필드: sequence = VGNL_application_frame+24 (be_i64)
- 필드: first_timestamp = VGNL_application_frame+32 (4 raw bytes)
- 필드: last_timestamp = VGNL_application_frame+36 (4 raw bytes)
- 필드: section_index = VGNL_application_frame+40 (be_i32)
- 필드: section_offset = VGNL_application_frame+44 (be_i64)
- 필드: game_clock = VGNL_application_frame+52 (be_f32)
- 필드: record_count = VGNL_application_frame+56 (be_i32)
- 필드: payload_length = VGNL_application_frame+60 (be_i32)
- 필드: payload_crc32 = VGNL_application_frame+64 (be_u32)
- 필드: payload = VGNL_application_frame+68 (complete native records)
- 한계: WebSocket application payload이며 TCP 자체 framing이 아니다.
- 한계: native timestamp raw4 bytes와 sampled game clock을 같게 취급하지 않는다.
- 한계: transport end frame은 경기 종료/서버 결과 확정이 아니다.
- 한계: offline adapter의 stricter validation은 APK/server acceptance 규칙과 구별한다.
- 근거: [src-upload](#src-upload) · 2. Continuous replay transport
- 근거: [src-artifact-73ec01e818c9](#src-artifact-73ec01e818c9) · whole artifact; content remains external


## client 산술·HUD·stub

### VGRE-combat-critical-stub

**critical 산술의 mode gate와 RET 경계**

등록된 DamageSelection callback은 E30>0 및 float32 random product<=E30일 때 amount를 1+E31로 곱한다. mode flag gate 뒤 exchange 구조를 만들지만 확인한 최종 consumer 00450910은 RET stub이다.

- 상태: bounded · 의미 확신: high · 검증: static_instructions, synthetic_math, independent_review
- 경계: client_native / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0088da90` (win-x86-laa, preferred_va, callback registration caller); `0x0088d1e0` (win-x86-laa, preferred_va, callback builder); `0x0086a310` (win-x86-laa, preferred_va, critical callback); `0x0085b670` (win-x86-laa, preferred_va, mode-gated behavior); `0x0081e5d0` (win-x86-laa, preferred_va, exchange structure constructor); `0x00450910` (win-x86-laa, preferred_va, one-instruction RET boundary)
- 한계: flag의 실제 runtime 의미를 server mode라고 명명하지 않는다.
- 한계: 1.5x는 E31=0.5일 때만 나오며 default로 단정하지 않는다.
- 한계: 이 selected chain의 stub은 모든 damage path가 stub임을 뜻하지 않는다.
- 한계: RNG seed/distribution·실행 hit·서버 damage 적용은 미확정이다.
- 근거: [src-damage](#src-damage) · Chain 3: registered critical-selection arithmetic → gated structure construction → stub
- 근거: [src-combat_review](#src-combat_review) · Formula and remaining chain review

### VGRE-combat-effective-stats

**4-array 유효 stat 계산**

stat ordinal을 공유하는 setter/getter는 B/A/T/M 배열을 사용하며 검사된 경로는 (B+(1+M)*A)*(1+T)에 caller별 clamp를 적용한다. label switch로 armor/shield/critical/pierce ordinal을 대조했다.

- 상태: supported · 의미 확신: high · 검증: static_instructions, synthetic_math, independent_review
- 경계: client_native / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x007d1410` (win-x86-laa, preferred_va, stat label switch); `0x0095c710` (win-x86-laa, preferred_va, stat setter wrapper); `0x0095c590` (win-x86-laa, preferred_va, array setter); `0x00937480` (win-x86-laa, preferred_va, stat getter)
- 필드: B = actor_attribute_component+32 (float32[45])
- 필드: A = actor_attribute_component+212 (float32[45])
- 필드: T = actor_attribute_component+392 (float32[45])
- 필드: M = actor_attribute_component+572 (float32[45])
- 한계: 전체 buff stacking·item uniqueness·live server modifier 규칙은 복원하지 않았다.
- 한계: pierce label 존재만으로 penetration 순서·중첩·caps가 증명되지 않는다.
- 근거: [src-damage](#src-damage) · Shared stat layout and defensible names
- 근거: [src-combat_review](#src-combat_review) · Formula and remaining chain review

### VGRE-combat-hud-attack-estimate

**방어 계산은 last-hit HUD 추정**

00938a20의 추정은 D0/(1+k*E7)+D1/(1+k*E8)+D2이며 k float32는 약 0.01이다. 확인된 소비자는 KindredHUDHealthBar의 estimate > current HP 조건에 따른 asset 선택이다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, synthetic_math, independent_review
- 경계: client_native / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x005c0af0` (win-x86-laa, preferred_va, HUD update); `0x005c0b90` (win-x86-laa, preferred_va, HUD estimator caller); `0x00938a20` (win-x86-laa, preferred_va, default attack estimate); `0x00856bc0` (win-x86-laa, preferred_va, damage descriptor evaluator)
- 정정: 관측된 reciprocal 식을 authoritative damage calculator나 third-party penetration 구현 검증으로 승격하지 않는다.
- 한계: 이 경로는 HP를 빼지 않고 attacker pierce/crit/damage amp를 읽지 않는다.
- 한계: defense 초기 lower clamp는 0이 아니라 -FLT_MAX다.
- 한계: -100 부근 extrapolation이나 universal negative-defense 규칙을 주장하지 않는다.
- 근거: [src-damage](#src-damage) · Chain 1: default-attack estimate → last-hit health-bar asset
- 근거: [src-combat_review](#src-combat_review) · UI classification
- 근거: [src-artifact-78bc97a84b82](#src-artifact-78bc97a84b82) · whole artifact; content remains external
- 근거: [src-artifact-3c0be6e88602](#src-artifact-3c0be6e88602) · whole artifact; content remains external

### VGRE-combat-property-tooltip

**property scaling과 TooltipDamage**

009433d0는 flag별 rank/level/weapon/crystal/mastery 항을 더하고 clamp를 순서대로 적용한다. flag04는 raw additive weapon array이며 descriptor의 E4-B4와 다르다. 구체 소비자는 TooltipDamage presentation이다.

- 상태: supported · 의미 확신: high · 검증: static_instructions, synthetic_math, independent_review
- 경계: client_native / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x009433d0` (win-x86-laa, preferred_va, property evaluator)
- 한계: 모든 ability가 이 evaluator를 쓴다고 단정하지 않는다.
- 한계: damage descriptor offsets와 property offsets를 섞지 않는다.
- 한계: rank/level 단순화는 ordinary nonnegative/positive 입력 범위다.
- 근거: [src-damage](#src-damage) · Chain 2: property evaluator
- 근거: [src-combat_review](#src-combat_review) · Formula and remaining chain review


## 받은 HP와 표시

### VGRE-health-impact-prefix

**041e 실제 resource 변경 operand**

041e compact prefix16은 target/source BE32, signed float32 operand, presentation word/kind/flag다. incoming apply는 target·health guard 뒤 split과 clamped resource writes를 수행한다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, development_corpus, synthetic_math, independent_review
- 경계: client_native / incoming_application / static_only
- 정확한 파일: `win-x86-laa`, `h5810-development`
- Opcode: `041e`
- 함수/위치: `0x004d2db0` (win-x86-laa, preferred_va, 041e dispatch); `0x0081b6b0` (win-x86-laa, preferred_va, impact constructor); `0x0094e970` (win-x86-laa, preferred_va, impact apply)
- 필드: target_actor = payload_after_opcode+0 (be_u32)
- 필드: source_actor = payload_after_opcode+4 (be_u32)
- 필드: signed_operand = payload_after_opcode+8 (be_f32_bits)
- 필드: presentation_word = payload_after_opcode+12 (be_u16)
- 필드: presentation_kind = payload_after_opcode+14 (u8; zero-extended dword in action)
- 필드: presentation_flag = payload_after_opcode+15 (u8; normalized !=0)
- 필드: H5810_opaque_suffix = payload_after_opcode+16 (6 opaque bytes)
- 정정: floating-text-only 경로가 아니라 실제 local resource field 쓰기를 한다.
- 한계: H5810 22-byte layout과 native compact16을 혼동하지 않는다.
- 한계: negative operand는 실제 HP loss나 credited damage 총계와 같지 않다.
- 한계: raw kind를 weapon/crystal/true damage enum으로 이름 붙이지 않는다.
- 근거: [src-health](#src-health) · Path 1: 041e -> ActionImpactHealth -> actual resource changes
- 근거: [src-combat_review](#src-combat_review) · Incoming health/damage path
- 근거: [src-artifact-37791b9a5ba1](#src-artifact-37791b9a5ba1) · whole artifact; content remains external
- 근거: [src-artifact-13b37af12c02](#src-artifact-13b37af12c02) · whole artifact; content remains external

### VGRE-health-incoming-dispatch

**받은 action은 apply로 직접 진입**

replay playback과 socket receive는 같은 dispatcher를 호출한다. 041d/041e는 action+0x0c=1을 설정해 queue apply slot+8로 간다. 별도 prepare slot+4의 동작을 received route에 합치면 안 된다.

- 상태: supported · 의미 확신: high · 검증: static_instructions
- 경계: client_native / incoming_application / static_only
- 정확한 파일: `win-x86-laa`
- Opcode: `041d`, `041e`
- 함수/위치: `0x004eb4a0` (win-x86-laa, preferred_va, replay playback); `0x004b7db0` (win-x86-laa, preferred_va, buffered receive); `0x004cfec0` (win-x86-laa, preferred_va, shared dispatcher); `0x0092c240` (win-x86-laa, preferred_va, enqueue); `0x00931bd0` (win-x86-laa, preferred_va, queue processor)
- 한계: conditional receive transform의 키/handshake는 조사 범위 밖이다.
- 한계: socket/replay 공유 소비자는 기록 producer build의 일치 증거가 아니다.
- 근거: [src-health](#src-health) · Shared incoming boundary

### VGRE-health-resource-set-add

**041d SET/ADD와 음수 SET 정정**

041d prefix12는 affected actor, float operand, resource index와 SET/ADD 및 raw flags다. ordinary HP는 resource0이고 SET/ADD 모두 clamped setter로 간다. H5810의 resource0 SET584개는 모두 -10000이며 finite negative SET는 0으로 clamp된다.

- 상태: corrected · 의미 확신: high · 검증: static_instructions, development_corpus, independent_review
- 경계: client_native / incoming_application / static_only
- 정확한 파일: `win-x86-laa`, `h5810-development`
- Opcode: `041d`
- 함수/위치: `0x004d2cf4` (win-x86-laa, preferred_va, 041d dispatch); `0x0094f210` (win-x86-laa, preferred_va, resource operation apply); `0x0095f160` (win-x86-laa, preferred_va, resource SET); `0x0095f270` (win-x86-laa, preferred_va, nonnegative clamp)
- 필드: target_actor = payload_after_opcode+0 (be_u32)
- 필드: operand = payload_after_opcode+4 (be_f32_bits)
- 필드: resource_index = payload_after_opcode+8 (u8)
- 필드: set_nonzero_add_zero = payload_after_opcode+9 (u8)
- 필드: raw_presentation_flag_1 = payload_after_opcode+10 (u8)
- 필드: raw_presentation_flag_2 = payload_after_opcode+11 (u8)
- 필드: H5810_opaque_suffix = payload_after_opcode+12 (2 opaque bytes)
- 정정: SET -10000을 10000 damage로 누적하지 않는다.
- 정정: resource6의 특수 presentation callback은 resource6=HP 증거가 아니다.
- 한계: source/cause가 없고 negative ADD도 자동 combat damage가 아니다.
- 한계: 같은 timestamp/payload라도 source 위치가 다르면 별도 관측을 보존한다.
- 근거: [src-health](#src-health) · Path 2: 041d -> ActionModifyActorResource -> SET or ADD
- 근거: [src-correlation](#src-correlation) · G. Repeated negative HP SET is not damage
- 근거: [src-correlation_native](#src-correlation_native) · SET

### VGRE-health-split-display

**impact·HP·보호량·표시량 분리**

negative operand는 resource4 흡수, resource5 half-absorption, ordinary resource0/alternate1 순으로 나뉜다. 표시 입력은 deltas0+1+4여서 delta5를 제외한다.

- 상태: supported · 의미 확신: high · 검증: static_instructions, synthetic_math, independent_review
- 경계: client_native / incoming_application / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0086eb50` (win-x86-laa, preferred_va, resource split); `0x0093ead0` (win-x86-laa, preferred_va, resource ADD); `0x0095f270` (win-x86-laa, preferred_va, clamped setter); `0x0053b700` (win-x86-laa, preferred_va, damage representation); `0x00535890` (win-x86-laa, preferred_va, damage formatting)
- 한계: finite-input illustration: -100, HP200, resource4=30, resource5=20이면 HPdelta=-50, display input=-80이다. 실제 runtime test가 아니다.
- 한계: state guard/max/현재값 clamp/alternate pool 때문에 operand와 HP loss가 다르다.
- 한계: source callbacks는 resource 쓰기 전에 원 operand를 받으며 killer credit이 아니다.
- 근거: [src-health](#src-health) · The local split is real arithmetic; Path 3
- 근거: [src-combat_review](#src-combat_review) · Incoming health/damage path

### VGRE-treant-duration-extension-and-heal

**Treant duration extension and gated heal**

TreeEnt Restore reapply expands remaining only when incoming duration is strictly greater; original duration only increases if exceeded too. Heal/recharge behavior is mode-gated, with unnamed conditional provider branches. Icon and coefficient do not prove healing delivered.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00860be0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00860ee0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00861f30` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Build-specific declaration only; index, name hash, item ID, buff stack capacity and cooldown charges are distinct domains. No observed buff acquisition or active lifetime is established.
- 한계: Blue/red refers to exact visual linkage, not a universal color-to-stat rule. Stat/heal command bodies retain literal mode-byte gates; selected orb acquisition helpers are stubs.
- 한계: Tick/list scheduling, exact heal dispatch target and runtime cadence remain unresolved.
- 근거: [src-buffstatus-2d9b8c138369](#src-buffstatus-2d9b8c138369) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-249a38261108](#src-buffstatus-249a38261108) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-25a78502e711](#src-buffstatus-25a78502e711) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-eae3928dda28](#src-buffstatus-eae3928dda28) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-0a1dff2b1a88](#src-buffstatus-0a1dff2b1a88) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6c40c4224ec5](#src-buffstatus-6c40c4224ec5) · Reviewed claim and its explicit conditional/static limits.


## action↔impact의 제한된 연관

### VGRE-correlation-item-instance-scope

**아이템 instance는 actor와 함께 묶기**

H5810 044c의 25개 서로 다른 instance 정수 중 18개가 여러 actor 아래 나타난다. actor 없는 request-shaped 0448/044a를 이 정수만으로 소유자에 연결할 수 없다.

- 상태: corrected · 의미 확신: high · 검증: development_corpus, static_instructions
- 경계: offline_analysis / mixed_requires_separation / static_only
- 정확한 파일: `win-x86-laa`, `h5810-development`
- Opcode: `0448`, `0449`, `044a`, `044c`
- 정정: item-instance ID는 global per-use/transaction ID가 아니다.
- 한계: 044c mode0만 target actor가 활성이고 mode1은 coordinates, mode2는 untargeted다.
- 한계: Windows receive dispatcher는 0411..14/0448..4a를 default exit로 보내며 historical request-shaped record의 원 outbound 보존을 증명하지 않는다.
- 근거: [src-correlation](#src-correlation) · 2. Actual corpus coverage and request boundary

### VGRE-correlation-no-causal-key

**시간·actor 근접성은 인과 키가 아님**

H5810 negative impact35192개에 대해 raw timestamp1.0 window에서 same-source 후보는 0개12156, 1개17584, 복수5452다. explicit target까지 맞춰도 복수2563이며 단일 후보도 인과를 확정하지 않는다.

- 상태: bounded · 의미 확신: high · 검증: development_corpus, synthetic_tests, independent_review
- 경계: offline_analysis / not_applicable / synthetic_and_development
- 정확한 파일: `win-x86-laa`, `h5810-development`
- 한계: 041e 소비 prefix에 cast/ability/item/transaction key가 복원되지 않았다. opaque suffix에 무엇도 없다는 증명은 아니다.
- 한계: serialized order와 known destroy segment를 보존하며 nearest tie-break·dedup·success 분류를 하지 않는다.
- 한계: raw outer time window는 simulation latency/서버 tick 단위로 복원된 값이 아니다.
- 한계: 041e와 041d를 한 damage total로 더하거나 per-cast damage를 만들지 않는다.
- 근거: [src-correlation](#src-correlation) · 3. Correlation method and quantified ambiguity
- 근거: [src-correlation_review](#src-correlation_review) · REPORT
- 근거: [src-correlation_native](#src-correlation_native) · Result

### VGRE-correlation-play-fields

**play actor/target/slot과 불투명 suffix**

0415/16/17은 ActionPlayAbility이며 byte+0x24는 actor ability-array index다. 0415는 actor/target/index, 0416은 actor/vector/index, 0417은 actor/target/vector/index다.

- 상태: supported · 의미 확신: high · 검증: static_instructions, development_corpus
- 경계: client_native / incoming_observation / static_only
- 정확한 파일: `win-x86-laa`, `h5810-development`
- Opcode: `0415`, `0416`, `0417`
- 함수/위치: `0x0094ff00` (win-x86-laa, preferred_va, ActionPlayAbility apply); `0x00952920` (win-x86-laa, preferred_va, targeted play helper)
- 필드: 0415.actor = payload_after_opcode+0 (be_u32)
- 필드: 0415.target = payload_after_opcode+4 (be_u32)
- 필드: 0415.index = payload_after_opcode+8 (u8)
- 필드: 0416.actor = payload_after_opcode+0 (be_u32)
- 필드: 0416.vector = payload_after_opcode+4 (3 x be_f32_bits)
- 필드: 0416.index = payload_after_opcode+16 (u8)
- 필드: 0417.actor = payload_after_opcode+0 (be_u32)
- 필드: 0417.target = payload_after_opcode+4 (be_u32)
- 필드: 0417.vector = payload_after_opcode+8 (3 x be_f32_bits)
- 필드: 0417.index = payload_after_opcode+20 (u8)
- 한계: H5810 0415=14, 0416=22 bytes, suffix는 opaque다. 0417 관측이 없어 accepted historical layout은 없다.
- 한계: onPlayAbility는 hit success가 아니며 slot0..13을 A/B/C로 명명하지 않는다.
- 한계: hero slot과 item instance는 같은 callback 이름이어도 별개 namespace다.
- 근거: [src-correlation](#src-correlation) · 1. Strongest native correlation fields
- 근거: [src-correlation_native](#src-correlation_native) · Exact native prefixes
- 근거: [src-artifact-07c468b8ae82](#src-artifact-07c468b8ae82) · whole artifact; content remains external

### VGRE-creature-classification-native-kind-flags

**creature classification native_kind_flags**

Actor resource kind1 sets0x10,kind5 sets0x100,kind4 sets4; minion icon uses0x110; selected named definitions independently decoded

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_progression_rewards / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00942480` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00942d90` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x005b19e0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Exact-build static client scope only; no native/server execution or independent recording holdout. Historical producer build remains unmatched; no production progression/reward reducer or authoritative award inference.
- 한계: No universal CS or objective-award taxonomy
- 한계: Producer accepted_for_index:false is preserved: bounded research-catalog inclusion is not acceptance for a replay index, state reducer or reward assignment.
- 한계: Raw death source, retained hero display reference, owner-like links and authoritative awarded killer remain distinct.
- 근거: [src-progression-57a34aa9c432](#src-progression-57a34aa9c432) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-950f804660d2](#src-progression-950f804660d2) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-1b60abe8fbc4](#src-progression-1b60abe8fbc4) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-c4c358323260](#src-progression-c4c358323260) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-336482845157](#src-progression-336482845157) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-caba033b27b0](#src-progression-caba033b27b0) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-d8461fd9775d](#src-progression-d8461fd9775d) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-95fa1f21d0c2](#src-progression-95fa1f21d0c2) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-44728f7a19e6](#src-progression-44728f7a19e6) · Reviewed static claim and its explicit conditional limits.

### VGRE-creature-credit-generation-checked-link

**creature credit generation_checked_link**

actor+1c8/+1cc is generation-checked, initialized from creation action+37c or alternate+484, and can supply hero display attribution

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_progression_rewards / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00939e40` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0094d480` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0094e170` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Exact-build static client scope only; no native/server execution or independent recording holdout. Historical producer build remains unmatched; no production progression/reward reducer or authoritative award inference.
- 한계: Action-object offsets are not replay payload offsets; owner/summoner semantics not universal
- 한계: Producer accepted_for_index:false is preserved: bounded research-catalog inclusion is not acceptance for a replay index, state reducer or reward assignment.
- 한계: Raw death source, retained hero display reference, owner-like links and authoritative awarded killer remain distinct.
- 근거: [src-progression-57a34aa9c432](#src-progression-57a34aa9c432) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-950f804660d2](#src-progression-950f804660d2) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-1b60abe8fbc4](#src-progression-1b60abe8fbc4) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-c4c358323260](#src-progression-c4c358323260) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-336482845157](#src-progression-336482845157) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-caba033b27b0](#src-progression-caba033b27b0) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-d8461fd9775d](#src-progression-d8461fd9775d) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-95fa1f21d0c2](#src-progression-95fa1f21d0c2) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-44728f7a19e6](#src-progression-44728f7a19e6) · Reviewed static claim and its explicit conditional limits.

### VGRE-creature-credit-retained-hero-reference

**creature credit retained_hero_reference**

Negative incoming health-change action can record direct or linked hero into victim+1c0 before damage apply; ineligible later sources leave it retained; hero-death battle log may prefer it

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_progression_rewards / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0094e970` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0094eaa0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x009396f0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x005b19e0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Exact-build static client scope only; no native/server execution or independent recording holdout. Historical producer build remains unmatched; no production progression/reward reducer or authoritative award inference.
- 한계: Not universal latest hitter, successful damage or awarded killer
- 한계: Producer accepted_for_index:false is preserved: bounded research-catalog inclusion is not acceptance for a replay index, state reducer or reward assignment.
- 한계: Raw death source, retained hero display reference, owner-like links and authoritative awarded killer remain distinct.
- 근거: [src-progression-57a34aa9c432](#src-progression-57a34aa9c432) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-950f804660d2](#src-progression-950f804660d2) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-1b60abe8fbc4](#src-progression-1b60abe8fbc4) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-c4c358323260](#src-progression-c4c358323260) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-336482845157](#src-progression-336482845157) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-caba033b27b0](#src-progression-caba033b27b0) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-d8461fd9775d](#src-progression-d8461fd9775d) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-95fa1f21d0c2](#src-progression-95fa1f21d0c2) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-44728f7a19e6](#src-progression-44728f7a19e6) · Reviewed static claim and its explicit conditional limits.

### VGRE-creature-cs-coincidence-boundary

**creature cs coincidence_boundary**

H5810 diagnostic2422 death actions,994 resource14 ADD1;990 updates have raw-source/same-time matches,81 ambiguous,4 unmatched

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, development_corpus
- 경계: independently_reviewed_progression_rewards / not_applicable / synthetic_and_development
- 정확한 파일: `h5810-development`
- 한계: Exact-build static client scope only; no native/server execution or independent recording holdout. Historical producer build remains unmatched; no production progression/reward reducer or authoritative award inference.
- 한계: Development-seen unmatched-build sample;1147 candidate pairs are not kills; no per-category counters
- 한계: Producer accepted_for_index:false is preserved: bounded research-catalog inclusion is not acceptance for a replay index, state reducer or reward assignment.
- 한계: Raw death source, retained hero display reference, owner-like links and authoritative awarded killer remain distinct.
- 한계: The pooled exact-time/raw-source join has no section, order or lifetime constraint; candidate pairs do not establish causal kill credit.
- 근거: [src-progression-57a34aa9c432](#src-progression-57a34aa9c432) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-950f804660d2](#src-progression-950f804660d2) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-1b60abe8fbc4](#src-progression-1b60abe8fbc4) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-c4c358323260](#src-progression-c4c358323260) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-336482845157](#src-progression-336482845157) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-caba033b27b0](#src-progression-caba033b27b0) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-d8461fd9775d](#src-progression-d8461fd9775d) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-95fa1f21d0c2](#src-progression-95fa1f21d0c2) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-44728f7a19e6](#src-progression-44728f7a19e6) · Reviewed static claim and its explicit conditional limits.

### VGRE-creature-death-raw-source

**creature death raw_source**

ActorDie stores victim and raw source; presentation path is gated; existing decoder preserves unsigned IDs and opaque suffix

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_progression_rewards / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00819f30` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0094c8f0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0092d7d0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Exact-build static client scope only; no native/server execution or independent recording holdout. Historical producer build remains unmatched; no production progression/reward reducer or authoritative award inference.
- 한계: Raw source is not an awarded killer
- 한계: Producer accepted_for_index:false is preserved: bounded research-catalog inclusion is not acceptance for a replay index, state reducer or reward assignment.
- 한계: Raw death source, retained hero display reference, owner-like links and authoritative awarded killer remain distinct.
- 근거: [src-progression-57a34aa9c432](#src-progression-57a34aa9c432) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-950f804660d2](#src-progression-950f804660d2) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-1b60abe8fbc4](#src-progression-1b60abe8fbc4) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-c4c358323260](#src-progression-c4c358323260) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-336482845157](#src-progression-336482845157) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-caba033b27b0](#src-progression-caba033b27b0) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-d8461fd9775d](#src-progression-d8461fd9775d) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-95fa1f21d0c2](#src-progression-95fa1f21d0c2) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-44728f7a19e6](#src-progression-44728f7a19e6) · Reviewed static claim and its explicit conditional limits.

### VGRE-creature-objective-distinct-definitions

**creature objective distinct_definitions**

Ghostwing331,Blackclaw uncaptured332,captured333,Kraken jungle320,captured321 independently identified at kind4

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_progression_rewards / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00942480` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x005b19e0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Exact-build static client scope only; no native/server execution or independent recording holdout. Historical producer build remains unmatched; no production progression/reward reducer or authoritative award inference.
- 한계: Captured creature death is not automatically objective capture or team credit
- 한계: Producer accepted_for_index:false is preserved: bounded research-catalog inclusion is not acceptance for a replay index, state reducer or reward assignment.
- 한계: Raw death source, retained hero display reference, owner-like links and authoritative awarded killer remain distinct.
- 근거: [src-progression-57a34aa9c432](#src-progression-57a34aa9c432) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-950f804660d2](#src-progression-950f804660d2) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-1b60abe8fbc4](#src-progression-1b60abe8fbc4) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-c4c358323260](#src-progression-c4c358323260) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-336482845157](#src-progression-336482845157) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-caba033b27b0](#src-progression-caba033b27b0) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-d8461fd9775d](#src-progression-d8461fd9775d) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-95fa1f21d0c2](#src-progression-95fa1f21d0c2) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-44728f7a19e6](#src-progression-44728f7a19e6) · Reviewed static claim and its explicit conditional limits.

### VGRE-deepening-combat-target-storage

**combat target storage**

Incoming play resolves the runtime override before target/vector writes, while state transition and onPlayAbility use the original slot. Target generation is an object-lifetime guard, not a cast transaction key. Target+vector writes replace coordinate/mode flags but retain handle storage.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_native_deepening / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0094ff00` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00952920` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00957260` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x0095f600` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x009432c0` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source)); `0x00946710` (win-x86-laa, preferred_va, Reviewed function, instruction, or data address (see cited source))
- 한계: Static client build only; no native/server execution or fresh independent recording holdout. Historical producer build and applied runtime state remain unverified.
- 한계: Override apply requires resolved actor and global 0x0209e204 != 0; incoming play uses the opposite gate. Setup 0x004bff80 calls setter 0x0095da70 with zero; literal/direct-call scans cannot exclude alias or indirect writes.
- 한계: Historical payload suffixes remain opaque; no acknowledgement, hit success, causal transaction key or unique request/impact pairing. Numeric state transition requests may be rejected; dynamic behavior callbacks remain unresolved.
- 한계: Copied destination handle is not immediately cleared when input validation fails. Nonzero handle storage alone does not prove active target mode.
- 한계: Behavior context has definition/actor/target/vector pointers; dynamic implementations and applied authoritative effects remain unresolved.
- 근거: [src-deepening-34c9e68da6ff](#src-deepening-34c9e68da6ff) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-8911ccbae0f8](#src-deepening-8911ccbae0f8) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-9d37dc38eb98](#src-deepening-9d37dc38eb98) · Reviewed claim and its explicit limits; consult source for exact instruction locations.
- 근거: [src-deepening-014b40b70e6f](#src-deepening-014b40b70e6f) · Frozen independent producer review, including exact approved source hashes and remaining limits.
- 근거: [src-deepening-2f20bcbf5127](#src-deepening-2f20bcbf5127) · Bounded synthetic test model only; does not prove native execution or runtime application.

### VGRE-reward-ambient-gold-payout-declaration

**ambient gold payout declaration**

AmbientGold declares resource6/provider context, but selected helper configuration and lifecycle execution are stubs in this client. Capacity9999 is neither gold amount nor recipient count. No split formula or recipient selection is established.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_progression_rewards / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x008d2eb0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00528fc0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0045ecd0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x008268c0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Exact-build static client scope only; no native/server execution or independent recording holdout. Historical producer build remains unmatched; no production progression/reward reducer or authoritative award inference.
- 한계: No shared-gold/XP recipient eligibility, participation window, last-hit priority, split denominator or authoritative amount established.
- 한계: 041d prefix carries individual target/operand/resource/mode/presentation fields, not kill source or recipient array. Historical suffixes remain opaque.
- 한계: Reporting ratios are not payout coefficients. Finite resource illustrations do not emulate native float32, complete lifetime sources or server causation.
- 근거: [src-progression-820a55e55144](#src-progression-820a55e55144) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-5a0e398204b3](#src-progression-5a0e398204b3) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-c44f49eb6438](#src-progression-c44f49eb6438) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-159ec2054d94](#src-progression-159ec2054d94) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-e47d6b3ef6fd](#src-progression-e47d6b3ef6fd) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-eee9a8e311d3](#src-progression-eee9a8e311d3) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-9a182b69a8af](#src-progression-9a182b69a8af) · Reviewed static claim and its explicit conditional limits.

### VGRE-reward-bounty-multiplier

**bounty multiplier**

Selected ARAM bounty factory declares attribute21/layer2/constant1, but its helper setter and lifecycle execution are stubs. It does not establish an applied bounty multiplier.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_progression_rewards / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x008cf910` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00529040` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Exact-build static client scope only; no native/server execution or independent recording holdout. Historical producer build remains unmatched; no production progression/reward reducer or authoritative award inference.
- 한계: No shared-gold/XP recipient eligibility, participation window, last-hit priority, split denominator or authoritative amount established.
- 한계: 041d prefix carries individual target/operand/resource/mode/presentation fields, not kill source or recipient array. Historical suffixes remain opaque.
- 한계: Reporting ratios are not payout coefficients. Finite resource illustrations do not emulate native float32, complete lifetime sources or server causation.
- 근거: [src-progression-820a55e55144](#src-progression-820a55e55144) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-5a0e398204b3](#src-progression-5a0e398204b3) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-c44f49eb6438](#src-progression-c44f49eb6438) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-159ec2054d94](#src-progression-159ec2054d94) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-e47d6b3ef6fd](#src-progression-e47d6b3ef6fd) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-eee9a8e311d3](#src-progression-eee9a8e311d3) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-9a182b69a8af](#src-progression-9a182b69a8af) · Reviewed static claim and its explicit conditional limits.

### VGRE-reward-goldshell-distance-provider

**goldshell distance provider**

Goldshell operand0x2e selects a projectile, not a gold amount. Its mode-gated provider resolves actor+0x1bc and returns one handle only within strict squared distance810000. This is not a general shared-XP recipient radius or proof of awarded killer.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_progression_rewards / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0088b530` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0086d160` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Exact-build static client scope only; no native/server execution or independent recording holdout. Historical producer build remains unmatched; no production progression/reward reducer or authoritative award inference.
- 한계: No shared-gold/XP recipient eligibility, participation window, last-hit priority, split denominator or authoritative amount established.
- 한계: 041d prefix carries individual target/operand/resource/mode/presentation fields, not kill source or recipient array. Historical suffixes remain opaque.
- 한계: Reporting ratios are not payout coefficients. Finite resource illustrations do not emulate native float32, complete lifetime sources or server causation.
- 근거: [src-progression-820a55e55144](#src-progression-820a55e55144) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-5a0e398204b3](#src-progression-5a0e398204b3) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-c44f49eb6438](#src-progression-c44f49eb6438) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-159ec2054d94](#src-progression-159ec2054d94) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-e47d6b3ef6fd](#src-progression-e47d6b3ef6fd) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-eee9a8e311d3](#src-progression-eee9a8e311d3) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-9a182b69a8af](#src-progression-9a182b69a8af) · Reviewed static claim and its explicit conditional limits.

### VGRE-reward-individual-resource-apply

**individual resource apply**

Individual resource6 ADD mutates the resolved target balance and positive operands also increment resource7 income total. SET/debit do not perform that positive-income increment. Same-team filtering belongs to presentation; all branches still require second target resolution before mutation.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_progression_rewards / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0094f210` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0093ead0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0095f160` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0095f270` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Exact-build static client scope only; no native/server execution or independent recording holdout. Historical producer build remains unmatched; no production progression/reward reducer or authoritative award inference.
- 한계: No shared-gold/XP recipient eligibility, participation window, last-hit priority, split denominator or authoritative amount established.
- 한계: 041d prefix carries individual target/operand/resource/mode/presentation fields, not kill source or recipient array. Historical suffixes remain opaque.
- 한계: Reporting ratios are not payout coefficients. Finite resource illustrations do not emulate native float32, complete lifetime sources or server causation.
- 근거: [src-progression-820a55e55144](#src-progression-820a55e55144) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-5a0e398204b3](#src-progression-5a0e398204b3) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-c44f49eb6438](#src-progression-c44f49eb6438) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-159ec2054d94](#src-progression-159ec2054d94) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-e47d6b3ef6fd](#src-progression-e47d6b3ef6fd) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-eee9a8e311d3](#src-progression-eee9a8e311d3) · Reviewed static claim and its explicit conditional limits.
- 근거: [src-progression-9a182b69a8af](#src-progression-9a182b69a8af) · Reviewed static claim and its explicit conditional limits.


## 구현 상태

### VGRE-hero-level-effects

**영웅 레벨 상한과 성장 효과**

유효 LEVEL 속성40은 base와 modifier 계층을 합성한다. 12 미만에서 증가량을 남은 상한으로 제한하고 성장 능력치와 능력 포인트를 처리한다. 증가량0도 재계산 경로를 실행할 수 있다.

- 상태: bounded · 의미 확신: high · 검증: static_instructions, synthetic_tests, corpus_audit, independent_review, file_hash
- 경계: native_gameplay / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00944de0` (win-x86-laa, preferred_va, level mutation); `0x0093fba0` (win-x86-laa, preferred_va, initialization)
- 한계: base+c0 단독 값은 유효 레벨이 아니다
- 한계: 시작 레벨과 전체 snapshot/수명 처리를 아직 닫지 않았다
- 한계: 유한 정상 값 모델 테스트는 native 실행 검증이 아니다
- 근거: [src-progression-xp-hero-report](#src-progression-xp-hero-report) · 2. Hero-level mutation, initialization and effects
- 근거: [src-progression-22c90cdc19a6](#src-progression-22c90cdc19a6) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-e47899d9a88c](#src-progression-e47899d9a88c) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-edc6e409f284](#src-progression-edc6e409f284) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-51a57ad65eff](#src-progression-51a57ad65eff) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-ea12af3d45eb](#src-progression-ea12af3d45eb) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-57a3320adc8b](#src-progression-57a3320adc8b) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-1f6c2d820b1c](#src-progression-1f6c2d820b1c) · Frozen review, input provenance or bounded test-only model.

### VGRE-level-action-delta

**영웅 레벨 변화 액션**

0434는 actor u32와 요청 레벨 증가량 u32를 전달한다. 수신기는 actor를 찾은 뒤 증가량을 적용한다. 기록만으로 실제 적용이나 절대 레벨을 단정하지 않는다.

- 상태: bounded · 의미 확신: high · 검증: static_instructions, synthetic_tests, corpus_audit, independent_review, file_hash
- 경계: native_gameplay / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- Opcode: `0434`
- 함수/위치: `0x004d31ec` (win-x86-laa, preferred_va, 0434 reader); `0x0081b840` (win-x86-laa, preferred_va, constructor); `0x0094b150` (win-x86-laa, preferred_va, serializer); `0x0094f120` (win-x86-laa, preferred_va, apply)
- 한계: H5810은 기존 자료이며 바이너리 일치가 확인되지 않았다
- 한계: 역사적 payload14의 끝6바이트는 의미 미확정으로 보존한다
- 근거: [src-progression-xp-hero-report](#src-progression-xp-hero-report) · 1. Applied level action and raw wire fields
- 근거: [src-progression-22c90cdc19a6](#src-progression-22c90cdc19a6) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-e47899d9a88c](#src-progression-e47899d9a88c) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-edc6e409f284](#src-progression-edc6e409f284) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-51a57ad65eff](#src-progression-51a57ad65eff) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-ea12af3d45eb](#src-progression-ea12af3d45eb) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-57a3320adc8b](#src-progression-57a3320adc8b) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-1f6c2d820b1c](#src-progression-1f6c2d820b1c) · Frozen review, input provenance or bounded test-only model.

### VGRE-skill-downgrade-refund

**Downgrade and conditional refund**

043b applies rank/history decrement only for nonzero rank; refund emission depends on global0209e204, not unconditional.

- 상태: bounded · 의미 확신: high · 검증: static_instructions, synthetic_tests, resource_decode, independent_review, file_hash
- 경계: native_static / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- Opcode: `043b`
- 함수/위치: `0x0094d360` (win-x86-laa, preferred_va, bounded static progression path); `0x0092d300` (win-x86-laa, preferred_va, bounded static progression path)
- 한계: Exact supplied build only; no live/server execution or current-version claim.
- 한계: H5810 recording build unmatched; request/action observation does not guarantee acceptance.
- 한계: Preserve mode, lifetime, slot overrides and ordering; no match-duration cap imposed.
- 근거: [src-skill-4ec21246b4db](#src-skill-4ec21246b4db) · Anchors and limitations; selected raw receipts are separately hashed.
- 근거: [src-progression-12bb9e88c8de](#src-progression-12bb9e88c8de) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-4ec21246b4db](#src-progression-4ec21246b4db) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-eae07b21a838](#src-progression-eae07b21a838) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-faa9c64596d7](#src-progression-faa9c64596d7) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-4966dd4e9b25](#src-progression-4966dd4e9b25) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-209bf9691ed0](#src-progression-209bf9691ed0) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-7257824606df](#src-progression-7257824606df) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-81a39cb66859](#src-progression-81a39cb66859) · Frozen review or bounded portable model/curated facts; no runtime inference.

### VGRE-skill-investment-apply

**Gated skill investment and point spending**

043a apply checks effective unspent stat1d and hero-level prerequisite; accepted local branch increments rank/history and spends one point.

- 상태: bounded · 의미 확신: high · 검증: static_instructions, synthetic_tests, resource_decode, independent_review, file_hash
- 경계: native_static / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- Opcode: `043a`
- 함수/위치: `0x0094df40` (win-x86-laa, preferred_va, bounded static progression path); `0x0096b400` (win-x86-laa, preferred_va, bounded static progression path); `0x0096b2c0` (win-x86-laa, preferred_va, bounded static progression path); `0x0093e850` (win-x86-laa, preferred_va, bounded static progression path)
- 한계: Exact supplied build only; no live/server execution or current-version claim.
- 한계: H5810 recording build unmatched; request/action observation does not guarantee acceptance.
- 한계: Preserve mode, lifetime, slot overrides and ordering; no match-duration cap imposed.
- 근거: [src-skill-4ec21246b4db](#src-skill-4ec21246b4db) · Anchors and limitations; selected raw receipts are separately hashed.
- 근거: [src-progression-12bb9e88c8de](#src-progression-12bb9e88c8de) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-4ec21246b4db](#src-progression-4ec21246b4db) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-eae07b21a838](#src-progression-eae07b21a838) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-faa9c64596d7](#src-progression-faa9c64596d7) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-4966dd4e9b25](#src-progression-4966dd4e9b25) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-209bf9691ed0](#src-progression-209bf9691ed0) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-7257824606df](#src-progression-7257824606df) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-81a39cb66859](#src-progression-81a39cb66859) · Frozen review or bounded portable model/curated facts; no runtime inference.

### VGRE-skill-overdrive-condition

**Overdrive equality and property bonus differ**

Resolved named condition is rank==base+(alternate?3:5); raw property bonus applies at rank5 only. Empty resolved slot implementation edge can return true.

- 상태: bounded · 의미 확신: high · 검증: static_instructions, synthetic_tests, resource_decode, independent_review, file_hash
- 경계: native_static / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0092ff60` (win-x86-laa, preferred_va, bounded static progression path); `0x0093cbf0` (win-x86-laa, preferred_va, bounded static progression path)
- 한계: Exact supplied build only; no live/server execution or current-version claim.
- 한계: H5810 recording build unmatched; request/action observation does not guarantee acceptance.
- 한계: Preserve mode, lifetime, slot overrides and ordering; no match-duration cap imposed.
- 근거: [src-skill-4ec21246b4db](#src-skill-4ec21246b4db) · Anchors and limitations; selected raw receipts are separately hashed.
- 근거: [src-progression-12bb9e88c8de](#src-progression-12bb9e88c8de) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-4ec21246b4db](#src-progression-4ec21246b4db) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-eae07b21a838](#src-progression-eae07b21a838) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-faa9c64596d7](#src-progression-faa9c64596d7) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-4966dd4e9b25](#src-progression-4966dd4e9b25) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-209bf9691ed0](#src-progression-209bf9691ed0) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-7257824606df](#src-progression-7257824606df) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-81a39cb66859](#src-progression-81a39cb66859) · Frozen review or bounded portable model/curated facts; no runtime inference.

### VGRE-skill-rank-prerequisite

**Rank bits, base rank and prerequisites**

Rank mask1c00 at ability+154; definition+58 base rank; normal requirements1(or2),2,4,6,8, alternate6,9,12; raw setter masks rather than saturates.

- 상태: bounded · 의미 확신: high · 검증: static_instructions, synthetic_tests, resource_decode, independent_review, file_hash
- 경계: native_static / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0095daa0` (win-x86-laa, preferred_va, bounded static progression path); `0x00937080` (win-x86-laa, preferred_va, bounded static progression path); `0x0093f270` (win-x86-laa, preferred_va, bounded static progression path)
- 한계: Exact supplied build only; no live/server execution or current-version claim.
- 한계: H5810 recording build unmatched; request/action observation does not guarantee acceptance.
- 한계: Preserve mode, lifetime, slot overrides and ordering; no match-duration cap imposed.
- 근거: [src-skill-4ec21246b4db](#src-skill-4ec21246b4db) · Anchors and limitations; selected raw receipts are separately hashed.
- 근거: [src-progression-12bb9e88c8de](#src-progression-12bb9e88c8de) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-4ec21246b4db](#src-progression-4ec21246b4db) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-eae07b21a838](#src-progression-eae07b21a838) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-faa9c64596d7](#src-progression-faa9c64596d7) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-4966dd4e9b25](#src-progression-4966dd4e9b25) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-209bf9691ed0](#src-progression-209bf9691ed0) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-7257824606df](#src-progression-7257824606df) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-81a39cb66859](#src-progression-81a39cb66859) · Frozen review or bounded portable model/curated facts; no runtime inference.

### VGRE-skill-slot-selection

**Display slots and runtime identities**

Initial display selectors vary by hero; Catherine1/2/3 and Ozo0/3/8 refute universal native slot2=ultimate. Runtime override/name mapping must be preserved.

- 상태: bounded · 의미 확신: high · 검증: static_instructions, synthetic_tests, resource_decode, independent_review, file_hash
- 경계: native_static / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x005acbf0` (win-x86-laa, preferred_va, bounded static progression path); `0x00936bd0` (win-x86-laa, preferred_va, bounded static progression path)
- 한계: Exact supplied build only; no live/server execution or current-version claim.
- 한계: H5810 recording build unmatched; request/action observation does not guarantee acceptance.
- 한계: Preserve mode, lifetime, slot overrides and ordering; no match-duration cap imposed.
- 근거: [src-skill-4ec21246b4db](#src-skill-4ec21246b4db) · Anchors and limitations; selected raw receipts are separately hashed.
- 근거: [src-progression-12bb9e88c8de](#src-progression-12bb9e88c8de) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-4ec21246b4db](#src-progression-4ec21246b4db) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-eae07b21a838](#src-progression-eae07b21a838) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-faa9c64596d7](#src-progression-faa9c64596d7) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-4966dd4e9b25](#src-progression-4966dd4e9b25) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-209bf9691ed0](#src-progression-209bf9691ed0) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-7257824606df](#src-progression-7257824606df) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-81a39cb66859](#src-progression-81a39cb66859) · Frozen review or bounded portable model/curated facts; no runtime inference.

### VGRE-skill-snapshot-restore

**Absolute skill ranks restored by HeroSpawn**

HeroSpawn action arrays feed absolute-rank setter and linked-slot synchronization independently of point investment; action offsets are not wire offsets.

- 상태: bounded · 의미 확신: high · 검증: static_instructions, synthetic_tests, resource_decode, independent_review, file_hash
- 경계: native_static / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- Opcode: `03f3`
- 함수/위치: `0x0094e170` (win-x86-laa, preferred_va, bounded static progression path); `0x0095c380` (win-x86-laa, preferred_va, bounded static progression path)
- 한계: Exact supplied build only; no live/server execution or current-version claim.
- 한계: H5810 recording build unmatched; request/action observation does not guarantee acceptance.
- 한계: Preserve mode, lifetime, slot overrides and ordering; no match-duration cap imposed.
- 근거: [src-skill-4ec21246b4db](#src-skill-4ec21246b4db) · Anchors and limitations; selected raw receipts are separately hashed.
- 근거: [src-progression-12bb9e88c8de](#src-progression-12bb9e88c8de) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-4ec21246b4db](#src-progression-4ec21246b4db) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-eae07b21a838](#src-progression-eae07b21a838) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-faa9c64596d7](#src-progression-faa9c64596d7) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-4966dd4e9b25](#src-progression-4966dd4e9b25) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-209bf9691ed0](#src-progression-209bf9691ed0) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-7257824606df](#src-progression-7257824606df) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-81a39cb66859](#src-progression-81a39cb66859) · Frozen review or bounded portable model/curated facts; no runtime inference.

### VGRE-skill-upgrade-request

**Skill upgrade request is separate from application**

0436 selected formatter serializes one native-slot byte; requesting is not a successful applied upgrade.

- 상태: bounded · 의미 확신: high · 검증: static_instructions, synthetic_tests, resource_decode, independent_review, file_hash
- 경계: native_static / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- Opcode: `0436`
- 함수/위치: `0x0052a5f0` (win-x86-laa, preferred_va, bounded static progression path); `0x004d6600` (win-x86-laa, preferred_va, bounded static progression path); `0x004cfbf0` (win-x86-laa, preferred_va, bounded static progression path)
- 한계: Exact supplied build only; no live/server execution or current-version claim.
- 한계: H5810 recording build unmatched; request/action observation does not guarantee acceptance.
- 한계: Preserve mode, lifetime, slot overrides and ordering; no match-duration cap imposed.
- 근거: [src-skill-4ec21246b4db](#src-skill-4ec21246b4db) · Anchors and limitations; selected raw receipts are separately hashed.
- 근거: [src-progression-12bb9e88c8de](#src-progression-12bb9e88c8de) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-4ec21246b4db](#src-progression-4ec21246b4db) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-eae07b21a838](#src-progression-eae07b21a838) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-faa9c64596d7](#src-progression-faa9c64596d7) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-4966dd4e9b25](#src-progression-4966dd4e9b25) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-209bf9691ed0](#src-progression-209bf9691ed0) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-7257824606df](#src-progression-7257824606df) · Frozen review or bounded portable model/curated facts; no runtime inference.
- 근거: [src-progression-81a39cb66859](#src-progression-81a39cb66859) · Frozen review or bounded portable model/curated facts; no runtime inference.

### VGRE-xp-progress-threshold-ui

**레벨 내 경험치와 표시 비율**

resource8은 레벨 내 경험치 진행량이다. HUD는 XP_REQUIRED 속성39로 나누어 목표 비율을 제한한 뒤 캐시를 애니메이션한다. 이미 상한인 경우는 종료하고 레벨1 초기화는0으로 설정한다. 그 외 상한 미만 재계산 경로는 기존 임계값을 호출당 한 번 차감한다.

- 상태: bounded · 의미 확신: high · 검증: static_instructions, synthetic_tests, corpus_audit, independent_review, file_hash
- 경계: native_gameplay / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x005ad770` (win-x86-laa, preferred_va, HUD ratio and cache); `0x00944de0` (win-x86-laa, preferred_va, threshold subtraction); `0x007d1410` (win-x86-laa, preferred_va, named attribute labels); `0x0095f270` (win-x86-laa, preferred_va, resource store)
- 한계: 누적 총 경험치 필드는 확정되지 않았다
- 한계: resource7은 LifetimeGold이며 경험치가 아니다
- 한계: H5810 임계값84부터244까지의 관측은 보편 곡선 증명이 아니다
- 한계: HUD와 helper의 clamp globals가 다르며 동일하다고 가정하지 않는다
- 한계: raw 비율은 애니메이션된 실제 표시값이 아니다
- 근거: [src-progression-xp-hero-report](#src-progression-xp-hero-report) · 3. XP current progress, threshold, and UI
- 근거: [src-progression-22c90cdc19a6](#src-progression-22c90cdc19a6) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-e47899d9a88c](#src-progression-e47899d9a88c) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-edc6e409f284](#src-progression-edc6e409f284) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-51a57ad65eff](#src-progression-51a57ad65eff) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-ea12af3d45eb](#src-progression-ea12af3d45eb) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-57a3320adc8b](#src-progression-57a3320adc8b) · Frozen review, input provenance or bounded test-only model.
- 근거: [src-progression-1f6c2d820b1c](#src-progression-1f6c2d820b1c) · Frozen review, input provenance or bounded test-only model.


## status_effect

### VGRE-status-action-specific-gates

**Separate movement attack skill and item gates**

00936490 accumulates readiness reasons with per-definition status exceptions and a distinct definition+6c branch testing flag10. Selection helpers use+6a/+6b and separate bypasses. Movement outer gate checks flag2/state5 with explicit override; inner mover still tests81.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00936490` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0096b5b0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00931340` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0086f730` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0086fb80` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0095dd70` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0095ded0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Status subset zero is not readiness
- 한계: Raw ReflexBlock/Aegis embedded defaults do not resolve inherited effective definitions
- 한계: No universal silence-blocks-all-items assertion
- 한계: Before-add callbacks may mutate flags. A zero modeled status-reason subset is not overall readiness; queued cancellation and pending-child removal do not prove synchronous state/UI cleanup.
- 근거: [src-buffstatus-a4cd780e2f2f](#src-buffstatus-a4cd780e2f2f) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-e5f7e2594dc9](#src-buffstatus-e5f7e2594dc9) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6732d26c2783](#src-buffstatus-6732d26c2783) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-f347f66b6b45](#src-buffstatus-f347f66b6b45) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-594c10a894d6](#src-buffstatus-594c10a894d6) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-00eb1bde27b4](#src-buffstatus-00eb1bde27b4) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-8b5ed6b76129](#src-buffstatus-8b5ed6b76129) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6952e73678c5](#src-buffstatus-6952e73678c5) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-7d8f7d69c15e](#src-buffstatus-7d8f7d69c15e) · Reviewed claim and its explicit conditional/static limits.

### VGRE-status-buff-blocker-matching

**Metadata and identity based blockers**

BlockBuffs creates typed blockers; matcher tests name hash, definition bytes/category bits, and a special identity list. Mode-gated ActionApplyBuff preparation retains first match; execution diverts to blocker callback or returns instead of normal apply.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x008da3c0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0052f0e0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0081d3c0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x009615e0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00962710` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x009378a0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00868a20` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00949b60` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0094c9a0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Mode0209e204 is unnamed
- 한계: At most32 collected blockers
- 한계: BlockDebuffs is not unconditional all-status immunity
- 한계: Before-add callbacks may mutate flags. A zero modeled status-reason subset is not overall readiness; queued cancellation and pending-child removal do not prove synchronous state/UI cleanup.
- 근거: [src-buffstatus-a4cd780e2f2f](#src-buffstatus-a4cd780e2f2f) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-e5f7e2594dc9](#src-buffstatus-e5f7e2594dc9) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6732d26c2783](#src-buffstatus-6732d26c2783) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-f347f66b6b45](#src-buffstatus-f347f66b6b45) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-594c10a894d6](#src-buffstatus-594c10a894d6) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-00eb1bde27b4](#src-buffstatus-00eb1bde27b4) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-8b5ed6b76129](#src-buffstatus-8b5ed6b76129) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6952e73678c5](#src-buffstatus-6952e73678c5) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-7d8f7d69c15e](#src-buffstatus-7d8f7d69c15e) · Reviewed claim and its explicit conditional/static limits.

### VGRE-status-cleanse-filtered-queue

**Cleanse metadata filtered cancellation**

Buff_Cleanse builds self-selection and CancelBuff mode2. In nonzero0209e204 mode only buffs whose definition+16 is nonzero are queued for ActionCancelBuff.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x008dda40` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00811820` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00811a20` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00811ad0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00860450` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x008709b0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0092dc00` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Queued cancellation is not synchronous erase-all
- 한계: No claim every debuff has the cancellation flag
- 한계: Network and UI timing unproven
- 한계: Before-add callbacks may mutate flags. A zero modeled status-reason subset is not overall readiness; queued cancellation and pending-child removal do not prove synchronous state/UI cleanup.
- 근거: [src-buffstatus-a4cd780e2f2f](#src-buffstatus-a4cd780e2f2f) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-e5f7e2594dc9](#src-buffstatus-e5f7e2594dc9) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6732d26c2783](#src-buffstatus-6732d26c2783) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-f347f66b6b45](#src-buffstatus-f347f66b6b45) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-594c10a894d6](#src-buffstatus-594c10a894d6) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-00eb1bde27b4](#src-buffstatus-00eb1bde27b4) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-8b5ed6b76129](#src-buffstatus-8b5ed6b76129) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6952e73678c5](#src-buffstatus-6952e73678c5) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-7d8f7d69c15e](#src-buffstatus-7d8f7d69c15e) · Reviewed claim and its explicit conditional/static limits.

### VGRE-status-display-native-distinction

**Display records are separate from logical flags**

DisplayStatusOnPlaque_Client stores localized status enum/string and buff+220 identifier, with an independent generation-checked display handle. The identifier is not a remaining-time float.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x0052f870` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x005335f0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x005336d0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x005336e0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0054aaa0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00938ff0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x005338d0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: End-to-end countdown rendering unresolved
- 한계: Status labels and particles do not prove native flag application
- 한계: Before-add callbacks may mutate flags. A zero modeled status-reason subset is not overall readiness; queued cancellation and pending-child removal do not prove synchronous state/UI cleanup.
- 근거: [src-buffstatus-a4cd780e2f2f](#src-buffstatus-a4cd780e2f2f) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-e5f7e2594dc9](#src-buffstatus-e5f7e2594dc9) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6732d26c2783](#src-buffstatus-6732d26c2783) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-f347f66b6b45](#src-buffstatus-f347f66b6b45) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-594c10a894d6](#src-buffstatus-594c10a894d6) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-00eb1bde27b4](#src-buffstatus-00eb1bde27b4) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-8b5ed6b76129](#src-buffstatus-8b5ed6b76129) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6952e73678c5](#src-buffstatus-6952e73678c5) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-7d8f7d69c15e](#src-buffstatus-7d8f7d69c15e) · Reviewed claim and its explicit conditional/static limits.

### VGRE-status-flag-contributor-lifecycle

**Per-source gameplay flag lifecycle**

ApplyGameplayFlags stores generation-checked per-source masks. Before-add callbacks can mutate expanded masks. The actor aggregate ORs up to128 collected children; removal destroys its own child, recomputes and emits the changed callback.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x008e29b0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0052ee10` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0081d390` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00961580` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00858e50` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00869720` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x009625e0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0112a680` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0112a0d0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Native event names are not replay opcodes
- 한계: Lifecycle expiry and mode gates remain material
- 한계: No arbitrary-count aggregation claim
- 한계: Before-add callbacks may mutate flags. A zero modeled status-reason subset is not overall readiness; queued cancellation and pending-child removal do not prove synchronous state/UI cleanup.
- 근거: [src-buffstatus-a4cd780e2f2f](#src-buffstatus-a4cd780e2f2f) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-e5f7e2594dc9](#src-buffstatus-e5f7e2594dc9) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6732d26c2783](#src-buffstatus-6732d26c2783) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-f347f66b6b45](#src-buffstatus-f347f66b6b45) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-594c10a894d6](#src-buffstatus-594c10a894d6) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-00eb1bde27b4](#src-buffstatus-00eb1bde27b4) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-8b5ed6b76129](#src-buffstatus-8b5ed6b76129) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6952e73678c5](#src-buffstatus-6952e73678c5) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-7d8f7d69c15e](#src-buffstatus-7d8f7d69c15e) · Reviewed claim and its explicit conditional/static limits.

### VGRE-status-named-factory-masks

**Selected named status masks**

Stunned factory supplies001f; Silence0018; ItemSilence0010; Tutorial_Rooted0001; Petal and Leo roots0023. Pre-add expansion and callback mutation follow.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x009166a0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00910af0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x008ed680` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0091a610` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00907d40` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x008fda60` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x008e29b0` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Factory configuration is conditional on successful application
- 한계: Named roots have different flags; do not generalize all roots
- 한계: Before-add callbacks may mutate flags. A zero modeled status-reason subset is not overall readiness; queued cancellation and pending-child removal do not prove synchronous state/UI cleanup.
- 근거: [src-buffstatus-a4cd780e2f2f](#src-buffstatus-a4cd780e2f2f) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-e5f7e2594dc9](#src-buffstatus-e5f7e2594dc9) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6732d26c2783](#src-buffstatus-6732d26c2783) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-f347f66b6b45](#src-buffstatus-f347f66b6b45) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-594c10a894d6](#src-buffstatus-594c10a894d6) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-00eb1bde27b4](#src-buffstatus-00eb1bde27b4) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-8b5ed6b76129](#src-buffstatus-8b5ed6b76129) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6952e73678c5](#src-buffstatus-6952e73678c5) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-7d8f7d69c15e](#src-buffstatus-7d8f7d69c15e) · Reviewed claim and its explicit conditional/static limits.

### VGRE-status-slow-max-category

**Movement modifier maximum per category**

Buff_Slow configures immediate0.5 category2 ModifyMoveSpeedNew. Collector00939f40 selects maximum applicable contribution per category and caps category2 with a stat quantity. Removal marks pending child rather than proving instant cleanup.

- 상태: bounded · 의미 확신: high · 검증: file_hash, independent_review, static_instructions
- 경계: independently_reviewed_buff_status_followup / not_applicable / static_only
- 정확한 파일: `win-x86-laa`
- 함수/위치: `0x00915c00` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x008e2b90` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00530800` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0081d640` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x009619d0` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00962b60` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x00939f40` (win-x86-laa, preferred_va, Reviewed native function or instruction address); `0x0112a080` (win-x86-laa, preferred_va, Reviewed native function or instruction address)
- 한계: Static possible client paths only; no native/server execution or fresh holdout. Historical producer build is unmatched. Native 043e consumes 16 bytes while the observed H5810 payload is 22; no unsupported production decode or runtime buff reconstruction is introduced.
- 한계: Finite collection limit800
- 한계: Directional predicates and cap apply
- 한계: No universal observed50-percent slow or additive stacking
- 한계: Before-add callbacks may mutate flags. A zero modeled status-reason subset is not overall readiness; queued cancellation and pending-child removal do not prove synchronous state/UI cleanup.
- 근거: [src-buffstatus-a4cd780e2f2f](#src-buffstatus-a4cd780e2f2f) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-e5f7e2594dc9](#src-buffstatus-e5f7e2594dc9) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6732d26c2783](#src-buffstatus-6732d26c2783) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-f347f66b6b45](#src-buffstatus-f347f66b6b45) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-594c10a894d6](#src-buffstatus-594c10a894d6) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-00eb1bde27b4](#src-buffstatus-00eb1bde27b4) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-8b5ed6b76129](#src-buffstatus-8b5ed6b76129) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-6952e73678c5](#src-buffstatus-6952e73678c5) · Reviewed claim and its explicit conditional/static limits.
- 근거: [src-buffstatus-7d8f7d69c15e](#src-buffstatus-7d8f7d69c15e) · Reviewed claim and its explicit conditional/static limits.

## 정확한 입력 파일과 주소 공간

### win-x86-laa

- 파일: Vainglory.exe
- SHA-256 (file_sha256): `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`
- 플랫폼/ABI: Windows / x86
- 빌드: PE timestamp 2020-03-09T21:30:28Z (release 식별 검증: False)
- 주소: preferred_va · image base: 0x00400000
- 주의: Header timestamp is build evidence, not a verified release version.

### win-x86-reference

- 파일: Vainglory.exe (older pinned reference)
- SHA-256 (file_sha256): `659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`
- 플랫폼/ABI: Windows / x86
- 빌드: older pinned reference (release 식별 검증: False)
- 주소: preferred_va · image base: 0x00400000
- 주의: In-memory clearing of LAA in the available image reproduces this hash; one-byte header difference does not identify a replay recorder.

### h5810-development

- 파일: H5810 numeric-section concatenation
- SHA-256 (numeric_section_concatenation_sha256): `ae8e37a0eb42f8d323311b20ceee2a1314fe97ae330be24cf30e3ffeca4870f0`
- 플랫폼/ABI: unknown / unknown
- 빌드: unknown recorder build (release 식별 검증: False)
- 주소: section_file_offset · image base: 해당 없음
- 주의: Previously development-seen recording; not a holdout and not proven same-build as the Windows image.

### android-vgna-1-11

- 파일: vgna-current.apk
- SHA-256 (file_sha256): `8394caa6f44b536924e8dd733870ee7642a04cc47abcb971ffcaadfe931a2543`
- 플랫폼/ABI: Android / arm64-v8a + armeabi-v7a
- 빌드: versionName 1.11; versionCode 147231; request header build 113 (release 식별 검증: True)
- 주소: zip_entry_offset · image base: 해당 없음
- 주의: Exact public APK scope only; not a backend/private server build.

### android-original-147219

- 파일: original.apk
- SHA-256 (file_sha256): `e82a6beed517db32536cd0f85a703d84dda84e1d184c990728dfb7c87d561d2d`
- 플랫폼/ABI: Android / arm64-v8a + armeabi-v7a
- 빌드: 4.13.4 (147219); versionCode 147219 (release 식별 검증: True)
- 주소: zip_entry_offset · image base: 해당 없음
- 주의: Third-party mirror acquisition; exact hash/signer cross-check, not an official-origin download.

### android-vgna-classes2

- 파일: classes2.dex
- SHA-256 (file_sha256): `997b1ccf62303da4b5ba78001ce4d141c457cc45a6a4d7e32430c8dda3cee88b`
- 플랫폼/ABI: Android / Dalvik/ART
- 빌드: member of exact VGNA 1.11 APK (release 식별 검증: True)
- 주소: dex_file_offset · image base: 해당 없음
- 주의: .text helper/wrapper file offset = VA - 0x1000; inspected engine .text file offset = VA. DEX offsets use uncompressed member bytes.

### android-vgna-unlock

- 파일: lib/arm64-v8a/libvg_unlock.so
- SHA-256 (file_sha256): `252b5c2ca758b817f30ac37076489d3dbd8fa20ea1d75f7fac7b3bc25f87920c`
- 플랫폼/ABI: Android / AArch64
- 빌드: member of exact VGNA 1.11 APK (release 식별 검증: True)
- 주소: elf_va · image base: 해당 없음
- 주의: .text helper/wrapper file offset = VA - 0x1000; inspected engine .text file offset = VA. DEX offsets use uncompressed member bytes.

### android-vgna-wrapper

- 파일: lib/arm64-v8a/libGameKindred.so
- SHA-256 (file_sha256): `15dae89c54912964f19434a47c449f28520539472f482a47d236a4d2fcf8ef17`
- 플랫폼/ABI: Android / AArch64
- 빌드: member of exact VGNA 1.11 APK (release 식별 검증: True)
- 주소: elf_va · image base: 해당 없음
- 주의: .text helper/wrapper file offset = VA - 0x1000; inspected engine .text file offset = VA. DEX offsets use uncompressed member bytes.

### android-vgna-real-engine

- 파일: lib/arm64-v8a/libGameKindred_real.so
- SHA-256 (file_sha256): `27e8f6586c172679c217df889abe3ce99b09299710e250d507685f6391c2525a`
- 플랫폼/ABI: Android / AArch64
- 빌드: member of exact VGNA 1.11 APK (release 식별 검증: True)
- 주소: elf_va · image base: 해당 없음
- 주의: .text helper/wrapper file offset = VA - 0x1000; inspected engine .text file offset = VA. DEX offsets use uncompressed member bytes.

## 근거 manifest

repo 경로는 현재 checkout에서 hash를 확인합니다. 외부 namespace 경로는 원문 위치를 이식 가능하게 표현하며, 링크가 열리거나 파일이 배포되었다는 의미가 아닙니다.

### src-android

- `research:rea-cloud/android-comparison/REPORT.md`
- SHA-256: `df7bc1f735d79723a8072bcde2f8b8d5ff054559336a00bbc10325efe9f468df`
- 종류: analysis_report · 보관: external_reference_only

### src-artifact-07c468b8ae82

- `research:action-damage-correlation/native/verification.json`
- SHA-256: `ae2adfc8190dbe73153ae673f86c50f4471dcd1f543091475d22611977bfe8e1`
- 종류: evidence_manifest · 보관: external_reference_only

### src-artifact-0a8763f8d6b4

- `research:match-result-analysis/native-evidence/roster-team-getter.txt`
- SHA-256: `c1631d1c0be48a4d648aa9facceb9e429aaa2e7ed84c133dc94703a427c4d257`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-artifact-13b37af12c02

- `research:incoming-health-damage/results/native-checks.json`
- SHA-256: `7601c3b5a2db4cb92236cf7d8c63d25f47dc8e1afb5cccc69cb9e8461c45e818`
- 종류: evidence_manifest · 보관: external_reference_only

### src-artifact-37791b9a5ba1

- `research:incoming-health-damage/curated-receipts.json`
- SHA-256: `d11098538cee53427f61803bd9325f4cb637c86003a3706e6a111624a119a871`
- 종류: evidence_manifest · 보관: external_reference_only

### src-artifact-3c0be6e88602

- `research:independent-combat-review/client-math-native-checks.json`
- SHA-256: `c5647f3f2521e121199d75c600243dcaa8cea6a662c76abfc74191bfff3508c4`
- 종류: evidence_manifest · 보관: external_reference_only

### src-artifact-70309fe0bcf8

- `research:server-gameplay-parameters/verification.json`
- SHA-256: `960b6c3217597e29d22fd0ba46949e4546f909e0710e7a513cce866be0ebcd48`
- 종류: evidence_manifest · 보관: external_reference_only

### src-artifact-73ec01e818c9

- `research:vgna-upload-schema/schema-manifest.json`
- SHA-256: `700f461557c3077eb9ca508d7f15301361f94f363039234d7d28250768195a99`
- 종류: evidence_manifest · 보관: external_reference_only

### src-artifact-78bc97a84b82

- `research:client-damage-math/portable/evidence.json`
- SHA-256: `2dbf032bcc5507a2b88ce95b20abc086b84241d5b8849f493a314a5a60f051be`
- 종류: evidence_manifest · 보관: external_reference_only

### src-artifact-8fb88e8a572e

- `research:platform-schema-trace/receipt-manifest.json`
- SHA-256: `d35423e1d1c6401fbf6c9b6130ef2c154371193be59c93598e6ee765e2ed27ee`
- 종류: evidence_manifest · 보관: external_reference_only

### src-artifact-93f6a2f696d5

- `research:platform-schema-trace/schema-summary.json`
- SHA-256: `9aab9cabd8c6b22fb133f600c4fbc74d5f99728de37df0f6944c624d9bc1e5d2`
- 종류: evidence_manifest · 보관: external_reference_only

### src-artifact-a4848e801e05

- `research:match-result-analysis/native-evidence/selected-actor-getter.txt`
- SHA-256: `dde0905376a832a2fd559d504370611eba819fbc1da31192b42004dee6f87562`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-artifact-bed88cb623ea

- `research:vgna-upload-schema/native/terminal-array.schema.json`
- SHA-256: `e06af7690ec912e506a30acff1956b04b05187b645449a3a5a94b5140b2bb8a7`
- 종류: evidence_manifest · 보관: external_reference_only

### src-artifact-c013d8dd6732

- `research:vgna-upload-schema/native/provenance.json`
- SHA-256: `41497694d8a64977daedc5282f1743186f8592d7bc3e85cca22a58556c61310e`
- 종류: evidence_manifest · 보관: external_reference_only

### src-artifact-da8bbbcf712e

- `research:server-gameplay-parameters/schemas.json`
- SHA-256: `32f2526f401ec8e89cca5b1983271f1080266a2500715518222a9c955a77176c`
- 종류: evidence_manifest · 보관: external_reference_only

### src-artifact-ff19690bf970

- `research:rea-cloud/android-comparison/artifacts/native-routing/findings.json`
- SHA-256: `d1d3a713538195e0de2af7f19f24469b5c308376dbdf8c0cf5b91c597d731baf`
- 종류: evidence_manifest · 보관: external_reference_only

### src-artifact-ff1ad1b8c623

- `research:match-result-analysis/native-evidence/bootstrap-writer.txt`
- SHA-256: `184f3ab2adae90e826dab614d7ab7a46d6fa327cfcb78671dd9e23f9f1b565a8`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-combat_review

- `research:independent-combat-review/REPORT.md`
- SHA-256: `df071eae08e5010110a20ebc5892c94bc3ea2cbdd4b59085a8ea9c377cd5a7ed`
- 종류: independent_review · 보관: external_reference_only

### src-correlation

- `research:action-damage-correlation/REPORT.md`
- SHA-256: `d36010e0a366844b2bacc64a701d0f06a5d95b917191b5a972fe6dcd0cbd0788`
- 종류: analysis_report · 보관: external_reference_only

### src-correlation_native

- `research:action-damage-correlation/native/REPORT.md`
- SHA-256: `562da8ac235c9af0a3a60d9f4065a941f441c6e27abb61b806ef5b2d9bec07ea`
- 종류: analysis_report · 보관: external_reference_only

### src-correlation_review

- `research:action-damage-correlation/REVIEW.md`
- SHA-256: `4e3cada8f92c0f39ff99507a784f5d0346d67f1eee5d655dae677b170e1ce9e9`
- 종류: independent_review · 보관: external_reference_only

### src-damage

- `research:client-damage-math/portable/REPORT.md`
- SHA-256: `d90a7c4f04f0c1b5d1a3ea744ebc6f0f1fe5b8c803e2415a5e4a984caeaa4a7e`
- 종류: analysis_report · 보관: external_reference_only

### src-deepening-014b40b70e6f

- `research:independent-deepening-review/review.json`
- SHA-256: `e6c834c265e2af39ea31279bf584e2aba5dde59f0529938bb24ea294a9720b08`
- 종류: independent_review · 보관: external_reference_only

### src-deepening-06095db2b8c7

- [repo:tests/research_models/override_fields.py](../../../tests/research_models/override_fields.py)
- SHA-256: `e2ec34bbe4c8f26ef492f28467fed4f348514f3e123a50c45ac34d598535ccc3`
- 종류: source_code · 보관: existing_repository

### src-deepening-0792a03dcffe

- `research:match-result-deepening/synthetic-terminal-counterexample.json`
- SHA-256: `4a168b367c0f899bf713b99e99b9b9ca909dab8635a76a05bacd83e45b04da38`
- 종류: evidence_manifest · 보관: external_reference_only

### src-deepening-09908834d9ba

- `research:match-result-deepening/REPORT.md`
- SHA-256: `00ac40a5f389815be047fefd89150a582cbfcd1b19f680c5ae418f521ec600a8`
- 종류: analysis_report · 보관: external_reference_only

### src-deepening-0be03adf5873

- `research:match-result-deepening/native/mastery-rpc-key.txt`
- SHA-256: `37f4ce6a3482093c607af730ca9d4268327d924326a73e720c4eb47d2e4f1c9e`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-1de244922c2b

- `research:match-result-deepening/native/mastery-lookup.txt`
- SHA-256: `97977795d02810d0556680456903e7937bc97a1aa530bc87fe9080c7c7a5e772`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-232fc680c622

- [repo:vg/docs/re_dictionary/deepening/README.md](../../../vg/docs/re_dictionary/deepening/README.md)
- SHA-256: `f0f8d654db11998281646fd19477b0ad0a369f48c001ad934dae0dd42a200ef9`
- 종류: analysis_report · 보관: existing_repository

### src-deepening-2626275848a3

- `research:match-result-deepening/terminal2/00564e50.txt`
- SHA-256: `9413f4c0c1f793afa319a4cdf216d89f81a5cbb60ad331a856f69d425bc2b481`
- 종류: evidence_manifest · 보관: external_reference_only

### src-deepening-2d186061c682

- `research:match-result-deepening/native/platform-getHeroMastery.txt`
- SHA-256: `98dd513240e0d596f343438d12c08db23346672e558060606574502ae4985c97`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-2f20bcbf5127

- [repo:tests/test_research_override_fields.py](../../../tests/test_research_override_fields.py)
- SHA-256: `536ed4f84cc7a5298e485444503c5740e4cd60128b0e179044b950683d1a3928`
- 종류: source_code · 보관: existing_repository

### src-deepening-34c9e68da6ff

- `research:combat-network-deepening/ARTIFACTS.sha256.json`
- SHA-256: `99b9f8c46bbad2483cdbc7706000316416a74a9a8bf3308e7572f5c4ac205694`
- 종류: evidence_manifest · 보관: external_reference_only

### src-deepening-37d63228f200

- `research:cooldown-deepening/portable/evidence-checks.json`
- SHA-256: `67f5d05e007839127020154e2a89afcd5f2fc03823d00f3de76c568afcfc748e`
- 종류: evidence_manifest · 보관: external_reference_only

### src-deepening-3bbf4528ff44

- `research:match-result-deepening/native/row-identity-reader.txt`
- SHA-256: `8f192fb682a451852f521acb18e7bdce47ddc8c3e296319ba81b73e1a556feba`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-3f546d5d0d00

- `research:match-result-deepening/native/primary-constructor.txt`
- SHA-256: `a75f0a27483606c6770ae34ae4e2d3368a93d6f12bc60916e88c22cd8ba45bfa`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-58bc1f4ae6c5

- `research:match-result-deepening/native/gold-ui-gate.txt`
- SHA-256: `b9d4ca1fc3da9bde6443d937a637b73b907113e143cffe210e342376bf66bb46`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-592d9786b4a9

- `research:match-result-deepening/native/banner-consumer.txt`
- SHA-256: `aafdb115e82b3406942668a63552847f36f356fc660203319b4f59069b0e7313`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-65f790466d1d

- `research:match-result-deepening/native/final-row-refresh.txt`
- SHA-256: `ae2187928c24a5c6a2de9cc522f8f8a669520293b740ad4846c28a64c77fe19c`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-6ab9f1b58c3c

- `research:match-result-deepening/native/clock-tick.txt`
- SHA-256: `bbc5d4a3e89eee7dec1d6aec9c3bb3b3a2afe412a03e0f3bb8ddc07cf9c0398a`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-6c2e708b509a

- [repo:tests/test_research_terminal_model.py](../../../tests/test_research_terminal_model.py)
- SHA-256: `865cedffcc00e27925191d37ae39a4ebae02f817814070ea8d725def0d3899fe`
- 종류: source_code · 보관: existing_repository

### src-deepening-6dda242b856c

- `research:match-result-deepening/native/primary-transition.txt`
- SHA-256: `2ca1a69d1076caaff9b117461e768e517855de5bdc14192d707cbb252ba0e3b0`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-763146dae926

- `research:cooldown-deepening/portable/REPORT.md`
- SHA-256: `fd9bfdd07422d854fbcdbabee127471d788e3f3924547580bdc52da26e37d28f`
- 종류: analysis_report · 보관: external_reference_only

### src-deepening-7f0bce357f27

- `research:match-result-deepening/native/mastery-response.txt`
- SHA-256: `f6e5402111d16adc27e09c356b51aefb00d9b54702304694f096925fc41196e1`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-882cd47fa830

- [repo:vg/docs/re_dictionary/deepening/cooldown-additions.json](../../../vg/docs/re_dictionary/deepening/cooldown-additions.json)
- SHA-256: `21948d47581c419572ae71271d866710791958852c6227d3c2002d247b572b82`
- 종류: analysis_report · 보관: existing_repository

### src-deepening-8911ccbae0f8

- `research:combat-network-deepening/REPORT.md`
- SHA-256: `10584f746f7c0a4a0f65ac9a0be5b8be4c76bec0c1fb1919f67624e8d45b8eab`
- 종류: analysis_report · 보관: external_reference_only

### src-deepening-8df4eb06449a

- `research:match-result-deepening/native/mastery-request-builder.txt`
- SHA-256: `c1b274d19b24bd6efdd1c0a72d9f393aedd0bb622c66f725f10c23368fe96f87`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-9676a04fd41e

- [repo:tests/test_research_followup_catalog.py](../../../tests/test_research_followup_catalog.py)
- SHA-256: `da713cf8c01a9faa8a2c1fe6d4031da3ace6fbb01edec2ab96756c668635042c`
- 종류: source_code · 보관: existing_repository

### src-deepening-9d37dc38eb98

- [repo:vg/docs/re_dictionary/deepening/combat-network-additions.json](../../../vg/docs/re_dictionary/deepening/combat-network-additions.json)
- SHA-256: `7ae2a5624b23ab5f7b6183f82eba583c165345b0522f09cd28306ffec3516523`
- 종류: analysis_report · 보관: existing_repository

### src-deepening-a684ae59db6d

- `research:match-result-deepening/native/platform-interface-slot.txt`
- SHA-256: `c36a999877933303a96b697d9f686e2c6c5780f55ba6b541194a383fa46c713a`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-afbcd8686e13

- `research:match-result-deepening/native/terminal-setter.txt`
- SHA-256: `eeef0fba32ea8704af439ee78ab111016ee12bb059cab70724c5e7accc020b59`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-b0dd017522f4

- `research:match-result-deepening/native/banner-keys.txt`
- SHA-256: `72df35939225703c84063b38630f977f00aaffb4c36e3e18ad6e71c914a258d6`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-b5a020905ffa

- [repo:tests/test_research_cooldown_models.py](../../../tests/test_research_cooldown_models.py)
- SHA-256: `a99ed095453bf3c191516d3dd021ba5118232921d23bf112ce5b6bf97abf8c1e`
- 종류: source_code · 보관: existing_repository

### src-deepening-ce219ed8f1ee

- `research:match-result-deepening/test_terminal_model.py`
- SHA-256: `86cf827e689433128ad7389a319e7455d28992152152062aa6b507d087ad43ae`
- 종류: source_code · 보관: external_reference_only

### src-deepening-d32981953aa3

- `research:match-result-deepening/native/clock-ui-gate.txt`
- SHA-256: `f2b2a1cc48f2b8e6096a84b80897fe3ac1b50e100f0b87c8ba7982018600815a`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-d4f1a88174ec

- `research:cooldown-deepening/portable/receipt-hashes.json`
- SHA-256: `e0dc2ebe834b878e274cf0d76da00cd686af213517e563f117363d4a3d24c2a6`
- 종류: evidence_manifest · 보관: external_reference_only

### src-deepening-ddcafec18612

- `research:match-result-deepening/native/mastery-manifest-keys.txt`
- SHA-256: `f5a4fb230e64cde35ffce3674cf942802b39100ac1a5859fa3e21e14bb6c5745`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-e358da15fc1e

- `research:match-result-deepening/native/mastery-tier.txt`
- SHA-256: `71ac81632ab6bed40284094d30407252f4d4529208beacdb520b9022706e27c1`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-f1eed04cad1f

- [repo:vg/docs/re_dictionary/deepening/match-result-additions.json](../../../vg/docs/re_dictionary/deepening/match-result-additions.json)
- SHA-256: `fbfbbe5d61ea51336ed851cff1b70e93eb53517a5903abf94507d2a47af51c6b`
- 종류: analysis_report · 보관: existing_repository

### src-deepening-f7ad612fc5c4

- `research:match-result-deepening/terminal7/0056f500.txt`
- SHA-256: `5839a0a565c1a47820b9036fa8222121d0422ecdbcdfc7deddf4f72a6b832485`
- 종류: evidence_manifest · 보관: external_reference_only

### src-deepening-f804572b3e72

- `research:match-result-deepening/native/roster-string-getter.txt`
- SHA-256: `57444aff329506bc2b083c455d6c0935f71eaf4929326bd131e3474b7335a5db`
- 종류: native_receipt_reference · 보관: external_reference_only

### src-deepening-f8c7558a816d

- `research:match-result-deepening/manifest.json`
- SHA-256: `98b0ecc30c753bf509921b3eb6f444458f3b3fc3274ffe87767293bd84b9c8ee`
- 종류: evidence_manifest · 보관: external_reference_only

### src-health

- `research:incoming-health-damage/REPORT.md`
- SHA-256: `79ffbc4d4dcdf125e1491c8afe39496f77445012543f71b7306a3c6ccbaa7a01`
- 종류: analysis_report · 보관: external_reference_only

### src-identity

- `research:match-result-analysis/REPORT.md`
- SHA-256: `8867e617248dddd9451fc8d670e30e20b26039767be838e4a393b50bc1b987d0`
- 종류: analysis_report · 보관: external_reference_only

### src-identity_review

- `research:identity-independent-review/REPORT.md`
- SHA-256: `2054055f25616cd77afdb08f6a46696291e3f364d46100cc8bc4741ebefab928`
- 종류: independent_review · 보관: external_reference_only

### src-item_resource

- `research:server-gameplay-parameters/item-semantics-resource/REPORT.md`
- SHA-256: `2742baa71b57e313765fca2fe79702e577177a44c7dd56cdc3138901a89fe2cd`
- 종류: analysis_report · 보관: external_reference_only

### src-item_target

- `research:server-gameplay-parameters/ITEM_TARGET_SEMANTICS.md`
- SHA-256: `af8b87435d54867279992970a3b71b023e60e0209bb08dbfc65a2937bc8ea360`
- 종류: analysis_report · 보관: external_reference_only

### src-legacy-026d9ced892c

- [repo:vg/docs/evidence/2026-10-14-rea-items/native-receipt.json](../../../vg/docs/evidence/2026-10-14-rea-items/native-receipt.json)
- SHA-256: `30c59d81b208e363a1a3d973f5e8e8b146221c61d3f71909023472298554f036`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-04a0c6efcf63

- `shared:cooldown-clock-hypotheses/REPORT.md`
- SHA-256: `ce35d475ab273ce80ffce8ecb1e9ad3db2352a026f7fa059282c0e8753225508`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-06d5353318de

- `research:cooldown-corpus-audit/audit-results-summary.txt`
- SHA-256: `d155a6655af28a9568367912ffbc0f38f04b96c423104fefef09e7c4d9b0e6e6`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-101d4f1bb6f5

- `research:ultimate-cloud-analysis/cam-link.json`
- SHA-256: `71dea57a56e03dcaa0bce2c378e397c3af82aca3afea03c0d353fb0fee31ee4d`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-115c58d88724

- `research:ultimate-cloud-analysis/items.json`
- SHA-256: `af3c4cce09ba057451cab8465993d16e866b1fa5f4ef0b1852ce2ad5190ab00e`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-1c1d37dc9cae

- [repo:vg/docs/evidence/2026-10-04-inventory/c33-runtime-matches.json](../../../vg/docs/evidence/2026-10-04-inventory/c33-runtime-matches.json)
- SHA-256: `27bfc5f7eec40d6d89d5bb7e96acb62e5c15ae1b50cc09501ef4fe3eb1df9a4a`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-1f058c438bde

- [repo:vg/docs/evidence/2026-10-14-fountain-definition/README.md](../../../vg/docs/evidence/2026-10-14-fountain-definition/README.md)
- SHA-256: `3e1f588e0992de5a395819cc4038d43682a9e2bb1d73ca7ca8c8e19a31250a4d`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-2096f6d0e790

- [repo:vg/docs/evidence/2026-10-14-cooldown-events/FLOW-MAP.md](../../../vg/docs/evidence/2026-10-14-cooldown-events/FLOW-MAP.md)
- SHA-256: `25657b5d9c5d8412f0fe8503cf3067509edcbfa7a1b4daf5cacf2034202c9580`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-21fa1d248d2a

- [repo:vg/docs/evidence/2026-10-11-terminal-display/summary.json](../../../vg/docs/evidence/2026-10-11-terminal-display/summary.json)
- SHA-256: `592656902f0fdcbc83222036828684d1e764053f7e6bf08ef0f36c9bf6b2b87f`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-23b5c8c50a77

- [repo:vg/docs/evidence/2026-10-04-roster/manifest.json](../../../vg/docs/evidence/2026-10-04-roster/manifest.json)
- SHA-256: `697631b57f7e13c79841141788e7727d65b35c6092ad54c19e1ac0bcd3283d77`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-2a3ea8c63ec5

- [repo:vg/docs/evidence/2026-10-14-cooldown-events/native-receipt.json](../../../vg/docs/evidence/2026-10-14-cooldown-events/native-receipt.json)
- SHA-256: `6e42ffcaa06894f0cd9748ca875770fb26e0f178f9c3b437976378f2b52a46fa`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-30a1c379d62a

- [repo:vg/docs/evidence/2026-10-15-cooldown-timer/native-static.json](../../../vg/docs/evidence/2026-10-15-cooldown-timer/native-static.json)
- SHA-256: `6d2a2fc5ceaf35aaf42c67e0cf8e85bc226e3f6de6c7689c46cd2c751981fca1`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-398995e110f9

- [repo:vg/docs/evidence/2026-10-14-cooldown-followup/ability-identity/IDENTITY-LIFECYCLE.md](../../../vg/docs/evidence/2026-10-14-cooldown-followup/ability-identity/IDENTITY-LIFECYCLE.md)
- SHA-256: `6b2810903b8b66d567cda921fe8d60a3ef07f98308a477388c3f9c59ebb79bd2`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-39db69cadeb8

- `research:cooldown-corpus-audit/REPORT.md`
- SHA-256: `8cc67f6b6ac5362789f7f9a8eb9b06328e8b1872e509d19cfa96cabb57d91abe`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-3a2fe01804f4

- [repo:vg/docs/RECORD_FRAMING_2026-09-06.md](../../../vg/docs/RECORD_FRAMING_2026-09-06.md)
- SHA-256: `346dfd0078c9619294cc3c64a2085639c463bb4202c6916fb31efcea25cbec46`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-491ccfd0d6da

- [repo:vg/docs/ENTITY_KIND_NATIVE_2026-09-09.md](../../../vg/docs/ENTITY_KIND_NATIVE_2026-09-09.md)
- SHA-256: `b4bfe7f50947ced189f97642ee6822265c1c0ba4decfbb6305aa6611de9eda9e`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-50ed693565fd

- [repo:vg/docs/ENTITY_LIFECYCLE_2026-09-09.md](../../../vg/docs/ENTITY_LIFECYCLE_2026-09-09.md)
- SHA-256: `e225326d7a507a3429f17f86b7b28b65404f00f1637ce34869108cc9565628e0`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-52e5ac43e76b

- [repo:vg/docs/ENTITY_RESOURCE_KIND_2026-09-09.md](../../../vg/docs/ENTITY_RESOURCE_KIND_2026-09-09.md)
- SHA-256: `68cb13c53bd6c9f347da34e97748161b3a7ffc86128c7f71a9b80bbf179d4739`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-540e0f15860d

- [repo:vg/docs/evidence/2026-10-14-rea-activation/corpus-verification.json](../../../vg/docs/evidence/2026-10-14-rea-activation/corpus-verification.json)
- SHA-256: `ab8e18a419ae743363bf6087dd291e4bb2801d5c099e4ae3f8ae42161bbf86d9`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-5468275020d0

- [repo:vg/docs/TERMINAL_DISPLAY_CALLS_2026-10-11.md](../../../vg/docs/TERMINAL_DISPLAY_CALLS_2026-10-11.md)
- SHA-256: `0e8b0f9ebfd548c97d321f5d804e82f4db0e3d405f321f49679c13a6d95418d0`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-58c0de22dc18

- `research:ultimate-cloud-analysis/cam_link.py`
- SHA-256: `0129a7797096679440a10310baf7d9fa33deb30162639e544ddf206a7bdd01b7`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-5af109d2e37d

- `research:ultimate-cloud-analysis/test_evidence.py`
- SHA-256: `694ead3fb25f85f143e9059b3c904061fbc2361f0532134c102b6df4945c54de`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-5cc7fe753b75

- [repo:vg/docs/OPCODE_CONTROLS_2026-10-04.md](../../../vg/docs/OPCODE_CONTROLS_2026-10-04.md)
- SHA-256: `ac39be107d2e2ddb9e6272ecfc39f090d7d66ec492aae2460b2d075a16762483`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-5fb87d432e50

- [repo:vg/docs/evidence/2026-10-14-cooldown-followup/replay-clock/partition_counterexample.py](../../../vg/docs/evidence/2026-10-14-cooldown-followup/replay-clock/partition_counterexample.py)
- SHA-256: `4a2fc6de0ed091cc4abd1c96583fc70d2e0f549f0958dbd154ac9752fd1fa485`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-608dc233d1c3

- [repo:vg/docs/evidence/2026-09-09-entity-kind.json](../../../vg/docs/evidence/2026-09-09-entity-kind.json)
- SHA-256: `dcfe7a644cfcd89107504fc32d3b882a2e676f6cc40505d897241c4408fadd46`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-6450cba1b6f5

- [repo:vg/docs/REA_ITEM_ACTIVATION_2026-10-14.md](../../../vg/docs/REA_ITEM_ACTIVATION_2026-10-14.md)
- SHA-256: `c3ed4336ab9e24b02ecb6a98f3b780d0e9b30d3e40bc661bdead14ea643f4cc0`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-6608fdb04825

- `research:identity-independent-review/pe-provenance-reconciliation.json`
- SHA-256: `997a5c3c41295a89c50e2775d37f97fd44941ea1b4e32e0b8692c4e822e4bee0`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-66473bba26c0

- `research:ultimate-cloud-analysis/REPORT.md`
- SHA-256: `42efa492cbd244a0f842089a7eddbfc1f686b2746ebedfcd2ded0522ebeeb0c0`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-6e281d7ff695

- [repo:vg/docs/evidence/2026-10-14-rea-items/corpus-verification.json](../../../vg/docs/evidence/2026-10-14-rea-items/corpus-verification.json)
- SHA-256: `e603a32d161dc12a5aec877f1fbea4599bfb115940cce0dc480f50f29ae8d83b`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-6ef08bd0ceaa

- [repo:vg/docs/NATIVE_INVENTORY_2026-10-04.md](../../../vg/docs/NATIVE_INVENTORY_2026-10-04.md)
- SHA-256: `5be72020b4f770e903c9ad432612e5800eed219774da5c5d5a31a0f65600dfdc`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-7361b4612daa

- [repo:vg/core/vgr_records.py](../../../vg/core/vgr_records.py)
- SHA-256: `08200f1dd4165055fe15ea724780f74ed22074118e5183ae47006e6271e406a6`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-742c9eb3fd3c

- `shared:cooldown-event-verification/h5810.json`
- SHA-256: `3aaaa5dc022ab2f398c958b9b6b6fc734da4f2272b2f5ee5cbecfa6ad585a403`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-7632d10bac89

- [repo:vg/docs/COOLDOWN_LIVE_2026-10-14.md](../../../vg/docs/COOLDOWN_LIVE_2026-10-14.md)
- SHA-256: `1e08767a49a48249d5ab1ba047de81b1bde3017f56f8d06b91146df5b30349e7`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-767b08816437

- [repo:vg/docs/evidence/2026-09-08-windows-clock/native-evidence.txt](../../../vg/docs/evidence/2026-09-08-windows-clock/native-evidence.txt)
- SHA-256: `f7890791dba9788c44333a8eebea4d87896eef819d40126c61f31ac6ecb29f76`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-7cb34430c060

- [repo:vg/docs/evidence/2026-10-04-inventory/operations.json](../../../vg/docs/evidence/2026-10-04-inventory/operations.json)
- SHA-256: `9a2d87f69052e58b8559b45031a27acffb3a5708559d63e7e6ca5a881ceefae6`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-7d0c0deb8b57

- [repo:vg/docs/INVENTORY_CONTROLS_2026-10-04.md](../../../vg/docs/INVENTORY_CONTROLS_2026-10-04.md)
- SHA-256: `b3442740e67766d07ee8b699a64f3da85136c6e79b6ea1b6273fb793faaa2806`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-7e39f84748f4

- [repo:vg/docs/evidence/2026-10-04-inventory/game-mode-capacity.json](../../../vg/docs/evidence/2026-10-04-inventory/game-mode-capacity.json)
- SHA-256: `7a2597ff33eaa064fdf2bce1c303c54d1ae834ef845f385e2075a1047467779b`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-80ca2197b4ab

- `shared:cooldown-clock-hypotheses/test_hypotheses.py`
- SHA-256: `64720956c1f8df673382b9758fe17679c4922df1bc481dfdc7dfb365494d3c8f`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-816f50695af4

- [repo:vg/docs/EVENT_SEMANTICS_2026-10-04.md](../../../vg/docs/EVENT_SEMANTICS_2026-10-04.md)
- SHA-256: `b8f68084ffb268bac6ab44832bd41a51457c5d0449654b6210cac85879574387`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-8546d549171b

- `research:identity-independent-review/REPORT.md`
- SHA-256: `2054055f25616cd77afdb08f6a46696291e3f364d46100cc8bc4741ebefab928`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-8a02e2be2ba4

- [repo:vg/docs/NATIVE_ROSTER_2026-10-04.md](../../../vg/docs/NATIVE_ROSTER_2026-10-04.md)
- SHA-256: `51a334c0d4a38469df07f1b18a01e17701fbdeb1064a461ddba9c2a7a5e0b1d1`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-8c544e50d99d

- `shared:cooldown-clock-hypotheses/input-verification.json`
- SHA-256: `6a7c287067eeac2b4f3c4075dad1426fdb558c56449defd86d829ff3fcc3ed0f`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-8fe3c4ff7f7b

- `shared:cooldown-clock-hypotheses/extended/EXTENSION.md`
- SHA-256: `39e2dc43f8e4a9cbcf00a1e06b0477ca0549622db626f7640a57b3bd5b96f46a`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-9eb65b2b4773

- `research:ultimate-cloud-analysis/artifact-hashes.json`
- SHA-256: `3b7a0067f5a1cb4caf90a0440e48b367ae7b400701be40e61bceecf6a05ab23e`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-a2358f682cf7

- `research:cooldown-corpus-audit/expansion-summary.txt`
- SHA-256: `4c9ded0eb2761f191f5981d09eebe67b27259d22a9e0ab0446a5fafaec1da528`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-a7d52092e883

- `shared:cooldown-clock-hypotheses/extended/registration-call-chain.txt`
- SHA-256: `6f60749428b946c0cb6c67e29c823ff64e53455678524673e274dffaf4a173c1`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-ac1d27d0c366

- [repo:vg/docs/evidence/2026-10-14-cooldown-live/summary.json](../../../vg/docs/evidence/2026-10-14-cooldown-live/summary.json)
- SHA-256: `b57c6e307766897ab62c52c7205e94ad72be1b39c8558ce69d38f8ae43c7ed53`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-b07d3cee91f6

- [repo:vg/docs/REA_ITEM_EVENTS_2026-10-14.md](../../../vg/docs/REA_ITEM_EVENTS_2026-10-14.md)
- SHA-256: `43d7f15838dc9d17000df4b8e34c7af84bc78612f91c51c59540f806de26a0be`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-b0fc6282fd01

- [repo:vg/docs/evidence/2026-10-14-rea-activation/native-receipt.json](../../../vg/docs/evidence/2026-10-14-rea-activation/native-receipt.json)
- SHA-256: `54a8aa48579ab004700fff786551a210d639ae17267cabf5cd1afb748f559c0b`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-b6cb4e0f9589

- `shared:cooldown-event-verification/unittest-926.log`
- SHA-256: `fd45e16f52a9d24532d431af08185bd253c2cc80c3f46ed53b4aebb6ccdd8a60`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-baffd845ca14

- [repo:vg/docs/evidence/2026-10-14-cooldown-events/h5810.json](../../../vg/docs/evidence/2026-10-14-cooldown-events/h5810.json)
- SHA-256: `b2a7bf0ac647a38b8636c211357268cd90e6537a1dabf84b1d5ee47caf2d90d7`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-c97bae0f3414

- [repo:vg/docs/ROSTER_ACCEPTANCE_2026-10-05.md](../../../vg/docs/ROSTER_ACCEPTANCE_2026-10-05.md)
- SHA-256: `8fca0ef8541212598c05d0981c60a88fdc3ac30bc84e48faabf7535de11ce2ea`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-cb14c1897f23

- [repo:vg/docs/COOLDOWN_TIMER_RESOLUTION_2026-10-15.md](../../../vg/docs/COOLDOWN_TIMER_RESOLUTION_2026-10-15.md)
- SHA-256: `ab60793a612d5f1257d4ca44767fac06dd4dd5106c9d4238bd8975470969a9d1`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-d5a2c970ee47

- [repo:vg/docs/TIMELINE_ENTITY_IDENTITY_2026-09-09.md](../../../vg/docs/TIMELINE_ENTITY_IDENTITY_2026-09-09.md)
- SHA-256: `2e4cccaf8b043bffb2a3af95b5109c2f734ba00cd20e7f8808b4e7aa6503b77d`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-d5c9da98be4d

- [repo:vg/docs/re_dictionary/baseline/native_roster-65bab83.py.txt](../../../vg/docs/re_dictionary/baseline/native_roster-65bab83.py.txt)
- SHA-256: `b3ced4d30bdb45459b3c315ac528efb59ae083c8263af85299e31dc8420452c7`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-dd8d0c7f3e7d

- `research:ultimate-cloud-analysis/heroes.json`
- SHA-256: `55fa66252da12b2c4cfd825e4c1bfc3138d747cd9230ca105f6dd02641fb81b2`
- 종류: existing_report_or_receipt · 보관: external_reference_only

### src-legacy-e171e36111f7

- [repo:vg/docs/evidence/2026-10-15-cooldown-timer/runtime-summary.json](../../../vg/docs/evidence/2026-10-15-cooldown-timer/runtime-summary.json)
- SHA-256: `35455377c93013c1e36fa7114e546b48d89742b3e0edd8dbfe7b9b15afb784ea`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-e5dd40aac2d1

- [repo:vg/docs/evidence/2026-10-14-cooldown-followup/replay-clock/REPORT.ko.md](../../../vg/docs/evidence/2026-10-14-cooldown-followup/replay-clock/REPORT.ko.md)
- SHA-256: `becd364dac3fd86b95d9ecc64b26db0f51de316ee5337a0992487dc6fd4c3c78`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-ea2758c4086d

- [repo:vg/docs/COOLDOWN_EVENT_FIELDS_2026-10-14.md](../../../vg/docs/COOLDOWN_EVENT_FIELDS_2026-10-14.md)
- SHA-256: `f8bda3ffbd016dbe4d2a173b193598734df3f34683e3f703ddfd69b4e8d50ad2`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-fbc9cad2c455

- [repo:vg/docs/evidence/2026-10-04-opcode-controls/roster-identity.json](../../../vg/docs/evidence/2026-10-04-opcode-controls/roster-identity.json)
- SHA-256: `743491516bdc0e424b1c019ead3066dca7c75477d6b4ce68f753fd7b641a33f5`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-fce4914d0b4f

- [repo:vg/docs/PLAYER_STATE_H5672_10MIN_2026-10-12.md](../../../vg/docs/PLAYER_STATE_H5672_10MIN_2026-10-12.md)
- SHA-256: `e9f4bcbfbe6c147fc9ce957aad32b57dcfbbbce1915c88c8d80f8b4fc272046d`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-legacy-fd9ff98c63f2

- [repo:vg/docs/evidence/2026-10-04-opcode-controls/roster-native.json](../../../vg/docs/evidence/2026-10-04-opcode-controls/roster-native.json)
- SHA-256: `474f31100cf46c7b2cb84c53ac9f1e68cdf7fa5d551b83d28eb6d97209e2f2ee`
- 종류: existing_report_or_receipt · 보관: existing_repository

### src-network

- `research:client-network-trace/REPORT.md`
- SHA-256: `9f22de9ddb5508cc6a6830e1df413ca761287da99ce4c16755347d946f3447c6`
- 종류: analysis_report · 보관: external_reference_only

### src-pe_relation

- `research:identity-independent-review/pe-provenance-reconciliation.json`
- SHA-256: `997a5c3c41295a89c50e2775d37f97fd44941ea1b4e32e0b8692c4e822e4bee0`
- 종류: provenance · 보관: external_reference_only

### src-platform

- `research:platform-schema-trace/REPORT.md`
- SHA-256: `81f303ec0d239c565c009fab9c9cbd33bc254e7f400676cf092ba828a285f3c4`
- 종류: analysis_report · 보관: external_reference_only

### src-protocol

- `research:replay-protocol-audit/REPORT.md`
- SHA-256: `7112dfa71971effa4ad4ec7f8bd437e24a134f065d68bf568a364f11e6c00ecb`
- 종류: analysis_report · 보관: external_reference_only

### src-requests

- `research:server-gameplay-parameters/REPORT.md`
- SHA-256: `bc736c7f91efa747c6dc69c0795a9eb315a0e4b5297ad582264ad9f93614099a`
- 종류: analysis_report · 보관: external_reference_only

### src-routing

- `research:rea-cloud/android-comparison/artifacts/native-routing/REPORT.md`
- SHA-256: `7ca6ff59db06982c61da7d21bc47b736682ae9ccf8292237c93c899d5e1d37c4`
- 종류: analysis_report · 보관: external_reference_only

### src-upload

- `research:vgna-upload-schema/REPORT.md`
- SHA-256: `c4c0ee3f478367fadb626ef261b50835123c3022f747b68195c6b71a3720869a`
- 종류: analysis_report · 보관: external_reference_only

### src-upload_native

- `research:vgna-upload-schema/native/REPORT.md`
- SHA-256: `273e5302ef843fa0dbefd44b56fcaced4a9762a1ad33b2d506a85d8249a3a3be`
- 종류: analysis_report · 보관: external_reference_only

### src-buffstatus-4fdd371a12f4

- `research:cooldown-deepening/lifecycle-delta/REPORT.md`
- SHA-256: `8c438f4ade9183c4fd116d5f90b3e9d28730ae2958c4ac7f9440a0c098632c24`
- 종류: analysis_report · 보관: external_reference_only

### src-buffstatus-31336b548579

- `research:cooldown-deepening/lifecycle-delta/receipt-hashes.json`
- SHA-256: `401cbcda16ac5222407ebce9ad32f735c7cd30c98c990a7e77557d3a6f18fe39`
- 종류: evidence_manifest · 보관: external_reference_only

### src-buffstatus-f9777f46fbc2

- `research:cooldown-deepening/lifecycle-delta/test-results.json`
- SHA-256: `8e78d3d5670e3a4961beb95c4127d0fbb9e8449e58039d21a780df14eba75adf`
- 종류: evidence_manifest · 보관: external_reference_only

### src-buffstatus-62c5d0f62db4

- `research:cooldown-deepening/lifecycle-delta/test_dispatch.py`
- SHA-256: `2151cbb8938862f553274091eb7d1a1eb8e6da5a87030245574087f0a17353a7`
- 종류: source_code · 보관: external_reference_only

### src-buffstatus-365f1595b3c7

- `research:independent-deepening-review/lifecycle-delta-review.json`
- SHA-256: `1c0fe2f4b13031580e754b5f8d472699ca99b62a9783d2eb2142cd742116462a`
- 종류: independent_review · 보관: external_reference_only

### src-buffstatus-e77b0c4a391a

- [repo:vg/docs/re_dictionary/buff_status/lifecycle-additions.json](../../../vg/docs/re_dictionary/buff_status/lifecycle-additions.json)
- SHA-256: `4d664423d0cdeca28d7adec84fbc668580efbadff1301f13baf6709f9d8e3b60`
- 종류: analysis_report · 보관: existing_repository

### src-buffstatus-fc6e1b76657f

- [repo:tests/test_research_buff_lifecycle.py](../../../tests/test_research_buff_lifecycle.py)
- SHA-256: `1bde24f8fb4d68bde4023233598d90a59a37db35fb6f460bdd79f5cfb6edae11`
- 종류: source_code · 보관: existing_repository

### src-buffstatus-2d9b8c138369

- `research:jungle-infusion-buffs/portable/REPORT.md`
- SHA-256: `eeaf30f3f397a0d3d71777e5e55c377403706225cb712ddd909da607f5bc255f`
- 종류: analysis_report · 보관: external_reference_only

### src-buffstatus-249a38261108

- `research:jungle-infusion-buffs/portable/receipt-hashes.json`
- SHA-256: `cdcb9d0a9fd0526415a9e3567862d595ad309454f060f454d486a24a1e02d911`
- 종류: evidence_manifest · 보관: external_reference_only

### src-buffstatus-25a78502e711

- `research:jungle-infusion-buffs/portable/native-anchors.json`
- SHA-256: `8e318be768beaa7907375e095f2bac357983ec86e010f6a68592b649166da709`
- 종류: evidence_manifest · 보관: external_reference_only

### src-buffstatus-eae3928dda28

- `research:independent-deepening-review/jungle-infusion-review.json`
- SHA-256: `d97cf6c6a56d9e50eb0ce2cded653396eb27055a21fae8f7d76bbea130595585`
- 종류: independent_review · 보관: external_reference_only

### src-buffstatus-0a1dff2b1a88

- [repo:vg/docs/re_dictionary/buff_status/jungle-candidates.json](../../../vg/docs/re_dictionary/buff_status/jungle-candidates.json)
- SHA-256: `cefe2615f21245bd178d298a4cb166d6ebc7e499dc4fc8f4f87828e75544c439`
- 종류: analysis_report · 보관: existing_repository

### src-buffstatus-6c40c4224ec5

- [repo:tests/test_research_jungle_infusion.py](../../../tests/test_research_jungle_infusion.py)
- SHA-256: `001cb01dac2d172bc1695f2b66b97e13901ccdcbd73c3c1b294d20f34812bb82`
- 종류: source_code · 보관: existing_repository

### src-buffstatus-a4cd780e2f2f

- `research:status-effect-gates/portable/REPORT.md`
- SHA-256: `29f3a4e44e78a868b946ddf9720981940e6975badfe069639d3bac025404cef4`
- 종류: analysis_report · 보관: external_reference_only

### src-buffstatus-e5f7e2594dc9

- `research:status-effect-gates/portable/PACKAGE.sha256.json`
- SHA-256: `7e49d00b74a3218ef001e34f77f347d1943508c2e0131bb5c16339bdedf3cd93`
- 종류: evidence_manifest · 보관: external_reference_only

### src-buffstatus-6732d26c2783

- `research:status-effect-gates/portable/receipt-hashes.json`
- SHA-256: `2c0f6e4e16aba0ee28822ecbfdd5bcfded91f79fcf9768fa25081bafd059e184`
- 종류: evidence_manifest · 보관: external_reference_only

### src-buffstatus-f347f66b6b45

- `research:status-effect-gates/portable/evidence-checks.json`
- SHA-256: `9dc4bb4cabf2449751e228e6cd7465241e074c07dd8e137f24686ccaaea47b53`
- 종류: evidence_manifest · 보관: external_reference_only

### src-buffstatus-594c10a894d6

- `research:status-effect-gates/portable/factory-identities.json`
- SHA-256: `588fffca43a9cddefb50758af168385bc9cb4de6f3c11ffd0e0d799a9d828b0c`
- 종류: evidence_manifest · 보관: external_reference_only

### src-buffstatus-00eb1bde27b4

- `research:status-effect-gates/portable/resource-flags.json`
- SHA-256: `83ba99848bd9a33ba1e813fd9f1c32e7af0f1ac929353bf0c4ea0d1eceb56f67`
- 종류: evidence_manifest · 보관: external_reference_only

### src-buffstatus-8b5ed6b76129

- `research:independent-deepening-review/status-effect-review.json`
- SHA-256: `14ee8ac73a0b15d9ce064a5f981e65c82445c1005876731b742bb13c83175397`
- 종류: independent_review · 보관: external_reference_only

### src-buffstatus-6952e73678c5

- [repo:vg/docs/re_dictionary/buff_status/status-additions.json](../../../vg/docs/re_dictionary/buff_status/status-additions.json)
- SHA-256: `e6c076c2e2951c76493dc348a3b273bc5834ab72aee5fb0e82b6b51d51ff4134`
- 종류: analysis_report · 보관: existing_repository

### src-buffstatus-7d8f7d69c15e

- [repo:tests/test_research_status_models.py](../../../tests/test_research_status_models.py)
- SHA-256: `cc4fea44392a22f2f0ea92e669e5366b68332a62c15b3a15e5b2d272d4b0a44a`
- 종류: source_code · 보관: existing_repository

### src-buffstatus-ad352c83dd55

- [repo:tests/test_research_buff_status_catalog.py](../../../tests/test_research_buff_status_catalog.py)
- SHA-256: `43e8b81c3adecd460de3dc598a42f70eb0521bc7951f977c7714dcad4001981e`
- 종류: source_code · 보관: existing_repository

### src-buffstatus-617028591c63

- [repo:vg/docs/re_dictionary/buff_status/README.md](../../../vg/docs/re_dictionary/buff_status/README.md)
- SHA-256: `0c9a56e37ad3614a703b12806ee2dbd1e2c0469753b4cca0dca7679a56ee9800`
- 종류: analysis_report · 보관: existing_repository

### src-skill-e32c9441a903

- `research:skill-rank-progression/receipts/core/0052a5f0.txt`
- SHA-256: `b41b4537c5ddf989a3f52e9941bbe12efffe4f5240392944efa119679762e262`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-6be779bd2f8f

- `research:skill-rank-progression/receipts/core/0052a5a0.txt`
- SHA-256: `2d9ef8536af0eacaed44e53aee11c1d1304e515e7ee2b9f255d2c5e1e704ac73`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-588ae13b408a

- `research:skill-rank-progression/receipts/core/005977c0.txt`
- SHA-256: `5da75a3ff64b0fc3af45dff12c9bffd00a0b371433f0ecf06d951dbd41180025`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-035459f7b571

- `research:skill-rank-progression/receipts/core/005acbf0.txt`
- SHA-256: `f3c66f83f9286811b5b8dfda732f6ef9ffd08cf061512ab13a48f90dc6474082`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-fd34f8f15834

- `research:skill-rank-progression/receipts/core/0092ff60.txt`
- SHA-256: `4d6f6da356129a64bc57b59307b1efe6074e8e9f10d177b9d98068fca8cb079d`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-e00cffe95d0f

- `research:skill-rank-progression/receipts/core/009467e0.txt`
- SHA-256: `a44928aa87fa04583d4cb6a913680cb42896ddb8bf7176c1d723350cbce54bc6`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-c26a2d66cac0

- `research:skill-rank-progression/receipts/rank/004d6600.txt`
- SHA-256: `23578fbeb812409e5f554d9fbbaf794aaca1fd5adfb4e00fe6c9ac675a498b67`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-6f46062d4046

- `research:skill-rank-progression/receipts/rank/0052a570.txt`
- SHA-256: `b0eb40dfa1553941734479316f215235b11a116e486b16c74011f13cc24dd845`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-86e397140a56

- `research:skill-rank-progression/receipts/rank/00937080.txt`
- SHA-256: `a8617aeac99979e12cc8f73bd5859b8561a695a2371db9da0fcdd86d688c619d`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-54757ca6fb08

- `research:skill-rank-progression/receipts/rank/00936bd0.txt`
- SHA-256: `fb964ebd9df188a366a2b9f34c469afaf87d4ccc0f7b3d68243c9b42a508c01e`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-bf11ff57e4f1

- `research:skill-rank-progression/receipts/rank/0093cbf0.txt`
- SHA-256: `01bdb24357f2d5665abd9a0af38d42bd61db5ee01b2cec718199cff18be86a25`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-ba63796095c9

- `research:skill-rank-progression/receipts/rank/00944ae0.txt`
- SHA-256: `4273e3f961a2d4a4420d803087dace18dea76d637f1968f9975405fd98ae41a3`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-6467259189d3

- `research:skill-rank-progression/receipts/apply/004cfbf0.txt`
- SHA-256: `663cb5fde116f8acaa4551222f3308b94b2d10d36ab0fdc97266a4b00d2e7d12`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-771ad24e44d7

- `research:skill-rank-progression/receipts/apply/0095daa0.txt`
- SHA-256: `4a4e70a76172599b773bd00a2a42ba56f9795b5d576c78e9f98e1b13f0a02649`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-4fb5788fafa6

- `research:skill-rank-progression/receipts/mutate/0096b2c0.txt`
- SHA-256: `15866307eaf1a3cadb9922fd5d2fdbba1b4a35813007784675810aa17f2d40a2`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-6a31e8004173

- `research:skill-rank-progression/receipts/mutate/0096b400.txt`
- SHA-256: `20e527a4624a0efa88923c77196fb3363b140ec5d2fe18662f6c6114a6b40d07`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-deb494a5d2aa

- `research:skill-rank-progression/receipts/mutate/0092d300.txt`
- SHA-256: `ba63b8ea6a7e838d4d6c6540845be551321e37a7860f19ec07cf14483127968d`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-8cf00fdcb0f6

- `research:skill-rank-progression/receipts/network/0094df40.txt`
- SHA-256: `b4ede0cd7b36cd11628da85cb1e87ec8b62210ed6007bb94c447ea8903c20a2f`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-1430dd047ace

- `research:skill-rank-progression/receipts/network/0094d360.txt`
- SHA-256: `d45dc42f75db7b5182e2ad363cad04c10cc5233c7791fdf0706c4c14411a7238`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-58d6e8a36a6b

- `research:skill-rank-progression/receipts/network/0095c380.txt`
- SHA-256: `71d1a4bff7775a0c28dc894b98a1003d71b6e0aea96f8c8652cdaac2a987a117`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-ea658ba3290e

- `research:skill-rank-progression/receipts/network/0081aba0.txt`
- SHA-256: `f0e39d96786be733a62cb637a08a64bfe934df291303b5f1dbe76f3fcb2d5bd4`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-cebac3b4c0f8

- `research:skill-rank-progression/receipts/network/008164c0.txt`
- SHA-256: `73caf64732d1ec33209d92affaa0a46587245f5ebd3c3ec50b72392bbacb3594`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-d6ff852dcb8f

- `research:skill-rank-progression/receipts/snapshot/0093e850.txt`
- SHA-256: `b9cdb1393bf6faa06f9ca87ff9d6fb8860950b344ac2f62c13bdea03e7050ac3`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-2af2a78412d7

- `research:skill-rank-progression/receipts/spawn/0094e170.txt`
- SHA-256: `941278ec8ce637f56e394427b5cd02d2de9580d0743acf94c2eb3f6a7c14b84d`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-6205c75fac79

- `research:skill-rank-progression/receipts/spawn/0094ada0.txt`
- SHA-256: `c5d1f745d51d56c5659750a03c535e83fd066cba59955449aa57d52308b651d8`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-2560ca2a43f2

- `research:skill-rank-progression/receipts/spawn/0093f270.txt`
- SHA-256: `bb6dc7f7f46bea72066e27b327409834adc61cf612d93b202427c4a44ce0877c`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-420cafc71469

- `research:skill-rank-progression/receipts/spawn/vtable_0127c914.txt`
- SHA-256: `af1df45ba4e4bee4393d982bbeaa184eb6fd9d8e4432fb48c46cc93f0e9daaa9`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-4ec21246b4db

- `research:skill-rank-progression/REPORT.md`
- SHA-256: `0b4d634ef4bc3ea0a0a0ea66158dec3a026c03b8858964a6d5f2f823c7a699bd`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-eae07b21a838

- `research:skill-rank-progression/resource-rank-fields.json`
- SHA-256: `6b3a49b8b51e9d99c6acd86120fab6e47e08343ef6b3ceeb66843849ad20ec18`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-faa9c64596d7

- `research:skill-rank-progression/corpus-observations.json`
- SHA-256: `c1e72ccd4b070a55953113e15e83ae28d7b8cf370235b5df33368b5b64efc190`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-9681fe0d93d3

- `research:skill-rank-progression/resources.py`
- SHA-256: `19bb9ccaad3e5f6d80138dbb45ed2606257e1eecedd0dede18236ae98bfcc03c`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-ee977b70e91c

- `research:skill-rank-progression/corpus.py`
- SHA-256: `a9bb842c3684faea986830a5eef9f408c965b10263b23b47b9ba0951d04d7335`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-1ca01c636d19

- `research:skill-rank-progression/models.py`
- SHA-256: `793ff36a1e6c39c53e00632ecf3ff2c2afb5296fa4295c30c5491f4c1981b30c`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-0359206016d9

- `research:skill-rank-progression/test_models.py`
- SHA-256: `9e79ccc63ae120a87931c74d9d1bc234a91c5fdb577e4e3091d76d85ac97112f`
- 종류: analysis_report · 보관: external_reference_only

### src-skill-61d6df10e04b

- `research:skill-rank-progression/tests.log`
- SHA-256: `4c3b3b2f85f7f81206f2731efca1a5c61f58b2f6c54d820b4003b988757b84ec`
- 종류: analysis_report · 보관: external_reference_only

### src-progression-12bb9e88c8de

- `research:independent-deepening-review/skill-rank-review.json`
- SHA-256: `32d42ccca13f6ac260f2c92e64ac0cc093ba222bc2f0ab73707930f6c90b7aff`
- 종류: independent_review · 보관: external_reference_only

### src-progression-4ec21246b4db

- `research:skill-rank-progression/REPORT.md`
- SHA-256: `0b4d634ef4bc3ea0a0a0ea66158dec3a026c03b8858964a6d5f2f823c7a699bd`
- 종류: analysis_report · 보관: external_reference_only

### src-progression-eae07b21a838

- `research:skill-rank-progression/resource-rank-fields.json`
- SHA-256: `6b3a49b8b51e9d99c6acd86120fab6e47e08343ef6b3ceeb66843849ad20ec18`
- 종류: evidence_manifest · 보관: external_reference_only

### src-progression-faa9c64596d7

- `research:skill-rank-progression/corpus-observations.json`
- SHA-256: `c1e72ccd4b070a55953113e15e83ae28d7b8cf370235b5df33368b5b64efc190`
- 종류: evidence_manifest · 보관: external_reference_only

### src-progression-4966dd4e9b25

- [repo:vg/docs/re_dictionary/progression_rewards/skill-additions.json](../../../vg/docs/re_dictionary/progression_rewards/skill-additions.json)
- SHA-256: `79453d6626204bfab6e811c508795a44d6bad5e6e6147a787b1b7a79f9518575`
- 종류: analysis_report · 보관: existing_repository

### src-progression-209bf9691ed0

- [repo:vg/docs/re_dictionary/progression_rewards/skill-fixtures.json](../../../vg/docs/re_dictionary/progression_rewards/skill-fixtures.json)
- SHA-256: `5c1f96ec2b4e6b0fbf13a8029c787f4f7e5ee55a0d9a3e6117fd54563db39753`
- 종류: evidence_manifest · 보관: existing_repository

### src-progression-7257824606df

- [repo:tests/research_models/skill_ranks.py](../../../tests/research_models/skill_ranks.py)
- SHA-256: `793ff36a1e6c39c53e00632ecf3ff2c2afb5296fa4295c30c5491f4c1981b30c`
- 종류: source_code · 보관: existing_repository

### src-progression-81a39cb66859

- [repo:tests/test_research_skill_ranks.py](../../../tests/test_research_skill_ranks.py)
- SHA-256: `a94bfd79c2830902d8ed96c1d5d037c6e5625a4a33f873183dc921d34d1be711`
- 종류: source_code · 보관: existing_repository

### src-progression-xp-hero-report

- [repo:vg/docs/re_dictionary/progression_rewards/XP_HERO_LEVELS.md](../../../vg/docs/re_dictionary/progression_rewards/XP_HERO_LEVELS.md)
- SHA-256: `8d444a55c67a5e0beb377a26b3af644ffd0beeb4a0f4d2ab2f5efb5aa256df4e`
- 종류: analysis_report · 보관: existing_repository

### src-progression-22c90cdc19a6

- `research:independent-deepening-review/experience-hero-level-review.json`
- SHA-256: `df881f44c915ed3fae0fa3612e83dab5c96a5daccb5dda5faf4fe9320e554c00`
- 종류: independent_review · 보관: external_reference_only

### src-progression-e47899d9a88c

- `research:experience-hero-levels/frozen-manifest.json`
- SHA-256: `174709bc6b3a9cfb67f7c7ee49cce04b816b1a6f7e36e4f09f3b100942f2d102`
- 종류: evidence_manifest · 보관: external_reference_only

### src-progression-edc6e409f284

- `research:experience-hero-levels/native-anchors.json`
- SHA-256: `aeb4f9f0d48e3bf13951db0f43082af072b38ce8cb30abe2c6b9a1798db195b2`
- 종류: evidence_manifest · 보관: external_reference_only

### src-progression-51a57ad65eff

- `research:experience-hero-levels/replay-evidence.json`
- SHA-256: `8f54e472ed781295f4b173fc0fbdb5305c5c11a741adb691c6a8a72e654f02c6`
- 종류: evidence_manifest · 보관: external_reference_only

### src-progression-ea12af3d45eb

- [repo:vg/docs/re_dictionary/progression_rewards/xp-additions.json](../../../vg/docs/re_dictionary/progression_rewards/xp-additions.json)
- SHA-256: `f2b43dfc21624e4ce3c9a9f191a1e57e3dad465c9444b8bbb3cf36d4bf56f3bf`
- 종류: analysis_report · 보관: existing_repository

### src-progression-57a3320adc8b

- [repo:tests/research_models/hero_xp.py](../../../tests/research_models/hero_xp.py)
- SHA-256: `a028a6c643d5d24e6f64744e527b1cbeacf17c34bcb442a40ef03872bfb30657`
- 종류: source_code · 보관: existing_repository

### src-progression-1f6c2d820b1c

- [repo:tests/test_research_hero_xp.py](../../../tests/test_research_hero_xp.py)
- SHA-256: `badd2f6a84ace2f8183efcc4a41e872d276ce0c13460529802170c0df0b9082e`
- 종류: source_code · 보관: existing_repository

### src-progression-820a55e55144

- `research:shared-reward-distribution/portable/REPORT.md`
- SHA-256: `8ff2c1d0047b0625cad1fe081f3c51318743bb3b6c12c19c10ba00d650b8019a`
- 종류: analysis_report · 보관: external_reference_only

### src-progression-5a0e398204b3

- `research:shared-reward-distribution/portable/ARTIFACTS.sha256.json`
- SHA-256: `8034ed272fb52aeb672560762bbd52303e6a760ef4ebd0599d08fef08af96e03`
- 종류: evidence_manifest · 보관: external_reference_only

### src-progression-c44f49eb6438

- `research:shared-reward-distribution/portable/native-spans.json`
- SHA-256: `347e547539d8bdcb7adefa34ebbd17e640faa3db2753f036c61c093e8a84010b`
- 종류: evidence_manifest · 보관: external_reference_only

### src-progression-159ec2054d94

- `research:shared-reward-distribution/portable/verification.json`
- SHA-256: `8b14fb15e286304faf8f209a1321960003cc95057fa43634c57ea58e2b461ede`
- 종류: evidence_manifest · 보관: external_reference_only

### src-progression-e47d6b3ef6fd

- `research:independent-deepening-review/shared-reward-review.json`
- SHA-256: `e255ef505308d555c0d0f6a23a70d605d61873a6d76f3d78c87479daa6cc7c54`
- 종류: independent_review · 보관: external_reference_only

### src-progression-eee9a8e311d3

- [repo:vg/docs/re_dictionary/progression_rewards/shared-reward-findings.json](../../../vg/docs/re_dictionary/progression_rewards/shared-reward-findings.json)
- SHA-256: `00dedfa24a822e30d2d63f2ea4dedac02f28ee4ee9bc439012180933eebc8afb`
- 종류: analysis_report · 보관: existing_repository

### src-progression-9a182b69a8af

- [repo:tests/test_research_reward_models.py](../../../tests/test_research_reward_models.py)
- SHA-256: `fc1223875e33de0b47f0442facfd85336f6e23bffee2a88917825245da355f8e`
- 종류: source_code · 보관: existing_repository

### src-progression-57a34aa9c432

- `research:creature-kill-credit/portable/REPORT.md`
- SHA-256: `c8fb3cef9533b7414cf13481a94bb8d4e317f0cdaebfdaf779b0fe7007164bf0`
- 종류: analysis_report · 보관: external_reference_only

### src-progression-950f804660d2

- `research:creature-kill-credit/portable/PACKAGE.sha256.json`
- SHA-256: `05673abfc994e0defe95fd2d33641214bfa92c5e45cf69a4f952060fad7b8a4e`
- 종류: evidence_manifest · 보관: external_reference_only

### src-progression-1b60abe8fbc4

- `research:creature-kill-credit/portable/EXTERNAL_RECEIPTS.json`
- SHA-256: `a67bb782f1f816a38a2348a9489726c9395e29082270abc597890244f48e30d9`
- 종류: evidence_manifest · 보관: external_reference_only

### src-progression-c4c358323260

- `research:creature-kill-credit/portable/actor-definitions.json`
- SHA-256: `9e54949a3e6202121d2d92719a5b564abfa9b13bcd084ccd5f5647e5fc612bda`
- 종류: evidence_manifest · 보관: external_reference_only

### src-progression-336482845157

- `research:creature-kill-credit/portable/correlation-summary.json`
- SHA-256: `832b51db477f328172667fa67fd1cf418e0a4a1666dffc10e1ab09d0faed85e2`
- 종류: evidence_manifest · 보관: external_reference_only

### src-progression-caba033b27b0

- `research:creature-kill-credit/portable/corpus-summary.json`
- SHA-256: `180003a07fc3f251a2c22632b78a7e2c90fa605de18f85278b8b6ef85b2e31cd`
- 종류: evidence_manifest · 보관: external_reference_only

### src-progression-d8461fd9775d

- `research:independent-deepening-review/creature-credit-review.json`
- SHA-256: `4caa6a2167efcd23ce173e6acc04ff5672ad1cab3f06653935460900ee56e17e`
- 종류: independent_review · 보관: external_reference_only

### src-progression-95fa1f21d0c2

- [repo:vg/docs/re_dictionary/progression_rewards/creature-findings.json](../../../vg/docs/re_dictionary/progression_rewards/creature-findings.json)
- SHA-256: `c2f2f02fcfb4f20585fcd19ca93bef32c4191da4f44b7193c09d4fc2ac4f0285`
- 종류: analysis_report · 보관: existing_repository

### src-progression-44728f7a19e6

- [repo:tests/test_research_creature_credit.py](../../../tests/test_research_creature_credit.py)
- SHA-256: `64cdff613da7027a9185ea45845d7a25d640913eba78c5b005a54418dea3a671`
- 종류: source_code · 보관: existing_repository

### src-progression-9b8ea21b85d8

- [repo:vg/docs/re_dictionary/progression_rewards/README.md](../../../vg/docs/re_dictionary/progression_rewards/README.md)
- SHA-256: `9c2cf4e6f597b5afdc9420faa43b4a16007aebc0dc403076d524f79b49627710`
- 종류: analysis_report · 보관: existing_repository

### src-progression-588c2b9bf0e1

- [repo:tests/test_research_progression_catalog.py](../../../tests/test_research_progression_catalog.py)
- SHA-256: `59a426f0340c3d3fb4ad5a929d6f0232b6cb15b52f7430aff6b0548968c8f486`
- 종류: source_code · 보관: existing_repository
