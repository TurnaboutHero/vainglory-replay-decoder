# 축전판과 삭제 아이템 후보: 이름, 증폭, 발동의 경계

## 조사 기준

선택 EXE는 Windows x86 LAA `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`이다. 주소는 preferred VA의 16진수다. 로컬 설치 Data를 읽었다. 과거 원본 EXE에서 만든 inventory metadata의 build hash `659f9e…92642`와 선택 LAA hash는 구분하며, 리소스와 manifest는 각 SHA-256을 다시 검사했다. 정적 코드·리소스 증거이며 게임 실행·현재 상점·서버 동작·과거 recording과의 버전 일치를 인증하지 않는다.

재현 결과는 [CAPACITOR_AND_RETIRED.json](CAPACITOR_AND_RETIRED.json), 재현기는 [capacitor_retired_evidence.py](../../research/capacitor_retired_evidence.py), 원본 REA export의 해시·evidence ID·실패 경계는 [CAPACITOR_NATIVE_RECEIPTS.json](CAPACITOR_NATIVE_RECEIPTS.json)에 있다. 원본 export와 전체 현지화·게임 바이너리는 공개하지 않는다. 기존 [조건부 아이템 조사](../passive_items_2026-10-16/03_CONDITIONAL_PASSIVES.md)의 factory 선언을 아래의 실제 dispatch 검사로 좁혔다.

## 충격파 주먹: 아이템 침묵 선언과 남은 코드

현지화 `STORE_ITEM_NULLWAVE_GAUNTLET_NAME`은 한국어 **충격파 주먹**, 영어 **Nullwave Gauntlet**이다. 한국어 설명은 적 영웅에게 발사 후 폭발하여 **아이템 침묵**을 거는 것으로 구분하고, 영어 tip도 active items를 상대하는 용도다. 일반 능력 침묵·이동 불가·공격 불가로 번역하지 않는다. 이 설명의 단일 적 영웅 표적은 선언상 근거이며 실제 폭발의 모든 수신자가 한 명이라는 native 증거는 아직 없다.

| 단계 | 확인된 연결 | 해석 한계 |
| --- | --- | --- |
| 현지화 | KO `AE9CB5A29032FAFA098A4BBE22C79B84`, SHA `610d2d6a3a543a11ffa555284ddcc3ce90af2aa1b7b54afb99a6dcf98b469a5e`; EN `7ED4F1146624D2D991A07272993B26C4`, SHA `209df4c745201dec58bd5ef2497f1835298b21cbc8f23bd1bb1669589462d8d4` | 각 strict base64→UTF-8 7,322개 고유 key 검사 |
| 아이템 | manifest definition 521 `*Item_NullwaveGauntlet*`; resource `8208DDB97AFC248D2FB0DDE2E1C1687B`, SHA `7d6674ff6cad4beea788a6c5d5015df909dc409bf8fa6954c5c3ec7b605800a7`; root+08의 위 현지화 key | active byte=1, presentation-hidden=false는 구매·사용 가능 증거가 아님 |
| 선언 값 | inline `Ability__Item__NullwaveGauntlet`, Cooldown=35, Range=11; item EMP_Duration=4, EMP_Countdown=1 | 실제 남은 시간·거리·피해 확정값으로 사용하지 않음 |
| native 등록 후보 | active name-global `01a74ad4`→copy `00449294`→entry `01a766b8`+4=`00899670`; countdown `008ef0c0`; item-silence `008ef1f0` | SHA-gated 이름 포인터와 A1/A3 복사·file-backed factory 포인터를 검사 |
| countdown factory | `008ef0c0`은 충전 presentation, `Buff_Item_EMP_ItemSilence` 적용 graph, `BaseDamage`와 `PctHealthDamage` 조회 graph를 구성 | expiry callback·수신자·실제 피해/침묵 적용은 별도 |
| item-silence factory | `008ef1f0`은 `Effect_ItemSilence`/`Effect_Item_EMP_Hit` 및 list 초기화를 구성 | 이 body만으로 아이템 활성화 차단 getter나 능력 침묵 mask를 확정할 수 없음 |

`00899670` pseudo query는 “No procedure exists”였다. 후속 256-byte read는 해당 주소의 code bytes와 return을 확인했다. 함수 경계 미복구를 코드 부재로 해석하지 않았다. 현재 확보한 factory/리소스 잔재는 **상점 구매 가능**, **사용 요청 수락**, **적중 후 아이템 활성화 차단**, **일반 능력 침묵**을 각각 증명하지 않는다. 삭제 시점·당시 패치 동작은 별도의 역사 자료 영역이다.

## 메아리: 현재 빌드에서는 연결 고리가 미복구

현재 hash-pinned manifest는 932개 definition, 그중 `Item_*` 93개다. item definition 이름의 `Echo` 검색 결과는 0개다. 한·영 7,322개 key 각각에서 `STORE_ITEM_*` 중 `ECHO` key와 exact value `메아리`/`Echo`도 0개다. 선택 EXE의 exact ASCII 토큰 `Item_Echo`, `Ability__Item__Echo`, `Buff_Item_Echo`도 없다. `Vox_EchoChamber` 같은 다른 이름을 아이템으로 연결하지 않았다.

따라서 **메아리→현지화 key→리소스→registry→쿨다운 초기화 구현** 연결은 이 빌드에서 미복구다. 이름 변경·인라인 코드·manifest 밖 미참조 리소스·이전 버전까지 없다는 의미는 아니다. 일반적인 cooldown 변경 helper나 `ModifyCurrentCooldown`이라는 이름만으로 메아리 잔재라고 식별하지 않는다. 메아리의 초기화 대상, 궁극기·아이템·charge·공유 key·대기 중 능력에 관한 예외는 현재 native 근거로 확정할 수 없다.

## 축전판 A: 회복·보호막 증폭

축전판은 definition 534 `*Item_CapacitorPlate*`, resource `BC0C89FE5C550B32C501FACA5E276BEA`, SHA `826ad9643e0412a9f8c8f1e94accb2fa156d5321a355eb507e715066c9e00468`이다. `Buff_Item_CapacitorPlate_Control` factory `008ee2c0`의 Lifetime graph가 아래 속성을 구성한다. property thunks는 기존 240-byte receipt와 새 SHA-gated PE 검사에서 lookup→definition resolve→`00939570` 세 direct call 및 selector/index를 확인했다.

| provider | item property / 선언 float32 | ModifyAttribute 설정 |
| --- | --- | --- |
| `008676d0` | index0 `HEAL_AMP`, bits `3e19999a` ≈0.15 | attribute `0x24`(36) `OUTGOING_HEAL_AMP`, layer2 |
| `008676a0` | index1 `BARRIER_AMP`, bits `3e19999a` ≈0.15 | attribute `0x22`(34) `OUTGOING_BARRIER_AMP`, layer0 |

상수 ID의 이름은 native label switch `007d1410`의 `STORE_ITEM_ATTR_OUTGOING_*` key로 교차 확인했다. incoming barrier/heal은 각각 별도 ID `0x21`/`0x23`이다. 따라서 현재 설정은 시전자가 내보내는 증폭 채널이며, 수신자가 소유한 모든 회복·보호막을 키운다고 바꾸어 쓰지 않는다. label 연결은 실제 증폭 getter의 계산·소비까지 증명하지 않는다.

이것은 두 증폭 채널의 **설정** 근거다. `005301d0`가 구성한 `BuffBehavior_ModifyAttribute` vtable `0121b2e4`의 +4 dispatch는 `0045ecd0`(`c2 04 00`, `ret 4`)이다. 해당 dispatch를 통해서는 속성이 변경되지 않는다. +14 설정 함수와 consumer가 별도로 존재하므로 이 한 edge로 모든 서버·다른 build의 증폭 부재를 결론내리지 않는다. 선택 EXE에서 증폭 getter가 실제로 얼마를 반환하는지는 이 factory만으로 인증하지 않는다.

Rook's Decree 보호막 factory `008f13c0`은 `BuffBehavior_GrantTemporaryResourceNew`(`0052fb10`)에 resource **4**와 provider `008362c0`을 설정한다. 해당 New behavior vtable `0121b134`의 +4 역시 같은 `ret 4`다. provider의 raw buff+21c 정수와 property 연산을 bonus HP 공식으로 고쳐 쓰지 않는다. 이 graph가 양의 보호막을 실제로 적용하고 축전판의 `0x22` getter를 소비했다는 증거는 없다.

핀 W `뜻밖의 동행`/`Ability__Phinn__B`는 별도 경로다. `008b4620`은 self 추가와 radius selection을 구성한 뒤 `Buff_Phinn_PoliteCompany_FortifiedHealth`를 적용하도록 설정한다. 그 buff factory `00908330`은 source actor의 HP·방어 관련 필드와 ability property를 계산하고, `BuffBehavior_GrantTemporaryResource`(`00811df0`)에 resource **5**와 산출량을 넣는다. talent `Phaster` 분기도 있으므로 일반 W와 talent를 섞지 않는다.

이 older resource behavior의 apply `00860cb0`은 mode byte `0209e204!=0`에서만 진행한다. 양의 stack delta에 대해 **resource4와 resource5 모두** source/bearer ID 및 양을 `004b7c00`에 넘긴다. 그러나 선택 EXE의 해당 함수는 **`d9 ee c3` = `fldz; ret`**, 즉 0 반환 stub다. 그러므로 “resource5이므로 증폭 대상 아님”도, “공통 호출이므로 15% 증폭됨”도 입증되지 않는다. 이 빌드의 stub를 실제 서버 증폭 getter라고 해석하지 않는다.

## 축전판 B: 이동 속도 발동

증폭 설정과 별개로 Control은 `BuffCallback_Heal`을 만든다. assembly `008ee2c0`에서 vtable `0127ba2c`, phase mask+28=`0x48`, relation low bits+2c=1, byte+30 bit1=1, actor filter+1c=1을 확인했다. +20 handler `00949520`은 predicate `0095fc90`이 true일 때만 behavior list의 virtual+4를 실행한다.

현재 해석 가능한 조건은 다음과 같다.

1. phase 인자를 `&31` 한 bit가 `0x48`에 있어야 하므로 정확히 `(phase & 31) ∈ {3, 6}`이다. 원시 phase 값 자체를3/6으로 제한하지 않는다. 이를 모든 “회복 수신” 이벤트로 확대하지 않는다.
2. event[0]은 buff+21c와 같아야 한다. event[1]이 buff bearer actor+178과 같으면 제외한다. 따라서 **자기 자신이 수신자인 경우 이 callback은 거절**한다.
3. actor filter는 `00945c80`을 통과해야 한다. 여기서는 actor+1e0의 bit0이 필요하다. 그 bit를 별도 enum 근거 없이 “모든 아군 영웅”으로 확정하지 않는다.
4. `SelectHealTarget` dispatch `008627f0`은 event+0x0c의 actor 포인터를 selection에 넣는다. 이후 `ApplyBuffToSelection`으로 Lockout을 선언한다. 이 behavior vtable `0121b428`의 +4는 위 `ret 4`여서 이 dispatch 자체는 Lockout을 적용하지 않는다.
5. Lockout factory `008ee500`은 SpeedBoost 적용 graph를 구성한다. providers `00867700`/`00867730`/`00867760`은 각각 index4 `LOCKOUT_DURATION=15`, index3 `MSPD_DURATION=3`, index2 `MSPD_STRENGTH=1.5`를 읽는다. 이 값은 실제 lockout 시작·수신자별 timer·최종 이동 속도 측정이 아니다.

`00858000`은 temporary resource 양이 **양수일 때만** `0086f4f0(6, source, target, amount, …)`를 호출한다. `0086f4f0`은 event+00에 source actor ID, +04에 target actor ID, +08/+0c에 각각 resolve된 actor pointer, +10에 amount를 넣어 source와 target의 callback component에 전달한다. 같은 actor면 target 쪽 중복 dispatch는 생략한다. 이로써 resource 경로의 phase6·source/target layout과 위 callback mask 사이의 정적 연결은 있다. 하지만 `00860cb0`의 현재 0 반환 stub를 거친 amount는 이 양수 분기를 만족하지 못한다. 직접 HP 회복의 phase3 producer, 수신 actor generation, ally filter, downstream Lockout/SpeedBoost 수락까지 확인해야 실제 발동이 닫힌다.

## 요청 사례별 판정

여기서 **지원**은 적힌 부분의 정적 근거가 있다는 뜻이며 실제 게임 효과 성공을 뜻하지 않는다. **설정**은 factory에 구성되었으나 실행·수락이 닫히지 않은 상태다. **해당 경로 제외**는 확인한 predicate/dispatch 범위의 부정이며 모든 구현의 부정을 뜻하지 않는다. **미확정**은 예/아니오로 보완하지 않았다.

| 사례 | HP / barrier / fortified health | A 증폭 판정 | B 이동 속도 발동 판정 |
| --- | --- | --- | --- |
| Rook's Decree 수신자 | resource4 설정 지원 | 미확정: New behavior apply stub, 실제 `0x22` getter 소비 미복구 | 미확정: 양의 phase6·Lockout 수락 미확인 |
| 핀 W의 다른 수신자 | resource5 fortified 경로 지원 | 미확정: 4/5 공통 함수는 있으나 현재 0 반환 stub | phase6 후보 연결 지원; 실제 발동은 미확정 |
| 핀 W의 자기 수신 | resource5 경로·self selection 지원 | 미확정 | **해당 Cap callback에서 제외**: event target=Cap bearer 조건 |
| 라임 W `삭풍` / Reim B | `008b5630`의 직접 graph는 Damage + `Buff_Reim_Immobilize` | 직접 회복/보호막 producer 근거 없음; indirect perk까지의 전체 판정은 미확정 | W만으로 heal phase를 발생시킨다는 근거 없음 |
| 라임 perk의 fortified health | `00909390`의 `currentMaxFortifiedHealth`/`lastGainedBarrier`, interval `00841f00`의 감소 경로 지원 | 증가 callback `00847620` 함수 경계 미복구로 미확정 | 자기 수신이라면 위 source/target 조건으로 제외; 다른 route는 미확정 |
| 라이라 A `기디안 표식` / Lyra A | 로컬 현지화는 HP heal과 별도 speed를 선언 | native heal consumer/getter 미추적으로 미확정 | Lyra 자체 speed와 Cap speed를 분리; Cap accepted heal phase/Lockout은 미확정 |

**라임은 라이라가 아니다.** `CHAR_INFO_REIM_NAME=라임`, `HERO_ABILITY_REIM_B_NAME=삭풍`; `CHAR_INFO_LYRA_NAME=라이라`, `HERO_ABILITY_LYRA_A_NAME=기디안 표식`을 같은 hash-pinned 현지화에서 대조했다. 라임 W의 피해가 perk의 여분 체력 증가를 간접 유발하는지는 별도 combat callback·증가 producer를 닫아야 한다.

## 반증 조건과 검증 범위

다른 EXE/resource SHA, vtable·thunk opcode 불일치는 이 주소 결론을 무효화한다. 같은 build의 runtime trace가 필요하다면 item grant→Control buff와 source/bearer generation→phase3/6 context→predicate accept/reject→Lockout/SpeedBoost 수락→실제 resource/이속 변화를 각각 기록해야 한다. A는 같은 HP·추가 HP·방어·talent·rank에서 Capacitor 유무만 바꾸고 resource4와5를 따로 비교한다. B는 자기 수신/다른 수신, 양수/0/초과 회복, 기존 Lockout, Rook projectile 불발을 분리한다. 양의 accepted resource가 없거나 callback이 거절되면 무조건 발동 가설은 반증된다.

재현기는 실제 입력에서 11개 registry 후보, 5개 property thunk, 6개 vtable edge와 두 stub의 bytes를 검사했다. CLI의 UTF-8 output은 보존 JSON과 byte-identical(SHA `2e7ac195cb3778c2e908c303d06f3b64f8e45e9027e5cdb1938c45ce0b8e5285`)이며, EXE hash 불일치 입력 거절도 확인했다. 한글 이름과 JSON UTF-8 round trip도 검증했다.

```powershell
python -m vg.research.capacitor_retired_evidence --binary <selected-Vainglory.exe> --data-root <Data> --output <research-output.json>
```

연구용 파일 외 production 코드·게임 리소스·바이너리·서버는 변경하지 않았다. 게임 client 실행·구매·능력 발동 실험은 하지 않았다. 승인된 범위가 Windows 정적 분석이고, 필요한 live 효과 계산이 선택 client의 stub에 남아 있어 client 실행만으로 그 의미를 보완할 수 있다고 가정하지 않았다. 현재 핵심 경계는 **실제 증폭 getter 및 accepted speed 효과를 이 정적 build만으로 재현할 수 없다는 점**이다.
