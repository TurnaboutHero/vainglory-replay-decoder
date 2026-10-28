# 축전판 증폭의 값 경로와 실행 경계

## 조사 범위

이번 후속 조사에서는 두 가지를 더 닫았다. 축전판 factory가 호출하는 **설정 함수도 값을 저장하지 않으며**, 라임 passive의 별도 증가 경로는 피해 context에서 gain을 계산해 resource5에 직접 더한다. 그 경로에는 amp33..36 소비가 없다. 반면 실제 서버의 회복·보호막 배율은 이 client의 독립 consumer 후보를 대조해도 복구되지 않아 수치로 인증할 수 없다. constructor가 stat36 layer1을 1로 seed한다는 가정도 배제했다.

이 문서는 `010c67c` 이후 후속 조사다. 선택 Windows x86 EXE SHA-256은 `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`이며, 모든 주소는 preferred VA다. 목표는 [앞선 축전판 조사](../stat_stacking_2026-10-16/05_CAPACITOR_AND_RETIRED.md)의 factory/stub 관찰 이후 독립 consumer, attribute 초기값, 실제 amount producer와 적용 경계를 더 닫는 것이다. A는 회복·보호막 수치 증폭, B는 다른 수신자의 이동 속도 발동이다. 두 효과의 성공을 서로 대신하는 증거로 쓰지 않는다.

로컬 설치 원본 `659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`와 선택 LAA EXE는 길이 29,545,984 bytes가 같고, PE Characteristics의 LAA bit 한 곳만 다르다. 코드의 stub는 LAA 변경으로 생긴 것이 아니다. [PE_BOUNDARIES.json](PE_BOUNDARIES.json)은 원본/선택 파일 해시, 유일한 차이와 선택 code edge를 고정한다. 이 사실은 서버 코드의 존재·부재나 다른 플랫폼/버전의 동작을 증명하지 않는다.

새 [CAPACITOR_VALUE_PATHS.json](CAPACITOR_VALUE_PATHS.json)은 [capacitor_value_paths.py](../../research/capacitor_value_paths.py)로 재현한다. 여기서 executable-section E8·literal pointer 검색은 명령 경계가 보장되지 않은 후보 목록이다. REA 함수 경계·xref와 합쳐 해석하며, 후보 수만으로 모든 간접 호출을 배제하지 않는다. 이전 리소스·provider·registry 증거와 함께 읽는다.

## A: 15% 선언에서 실제 배율까지

`008ee2c0`의 축전판 Control은 property index0 `HEAL_AMP`를 `008676d0`으로 읽어 attribute36 (`0x24`, `OUTGOING_HEAL_AMP`) layer2에, index1 `BARRIER_AMP`를 `008676a0`으로 읽어 attribute34 (`0x22`, `OUTGOING_BARRIER_AMP`) layer0에 설정한다. 두 property의 float32 bits는 `3e19999a`(약 .15)다. incoming barrier/heal은 별도 ID33/35다. label switch `007d1410`과 thunk의 selector/index를 확인했지만, **동일한 .15 선언이 동일한 1.15 배율이라는 결론은 아직 아니다.**

`00937480`은 stat-array 기준으로 selector0/1/2/3에 각 layer를 돌려주고, selector−1은 다음 raw 값을 계산한다.

```text
E[i] = ((layer3[i] + 1) * layer1[i] + layer0[i]) * (layer2[i] + 1)
```

| ID | 역할 | actor의 stat component 기준 layer0 / 1 / 2 / 3 |
| --- | --- | --- |
| 33 | incoming barrier amp | +a4 / +158 / +20c / +2c0 |
| 34 | outgoing barrier amp | +a8 / +15c / +210 / +2c4 |
| 35 | incoming heal amp | +ac / +160 / +214 / +2c8 |
| 36 | outgoing heal amp | +b0 / +164 / +218 / +2cc |

이 getter 자체는 clamp도 amount 곱셈도 하지 않는다. 예를 들어 모든 다른 layer가 0이면 layer2에 .15를 넣어도 E36은 0이다. 반대로 layer1이 1이면 E36이 약 1.15가 된다. 따라서 초기 layer 값, 그 값을 읽는 consumer, consumer가 `E`, `1+E`, 혹은 다른 식을 쓰는지를 함께 확인해야 한다. 단순 tooltip 번역·synthetic 곱셈으로 이 간극을 채우지 않는다.

초기값도 확인 범위를 좁혔다. `CKinActorAttributes` wrapper `00957710..00957781`의 `0095776a` CALL은 ECX=object+20으로 `0081c640`을 호출한다. 그 111-byte body는 45회 loop로 layer0/1/2/3의 각 45개 float를 **모두 0**으로 만들고 dirty/resource 관련 영역도 지운다. 후속 session의 pseudo와 assembly도 같은 loop를 확인했다. 이 construction 시점에는 stat36 layer1을 1로 seed하지 않는다. 뒤의 `00944de0(1)`도 33..36 layer0을 0으로 둔다. 따라서 이 두 초기화만을 근거로 “기본 E36이 1이므로 .15 적용 후 1.15”라고 설명할 수 없다. 이후 replicated state·다른 grant·정의 초기화가 값을 바꾸는 가능성과 실제 heal consumer가 T36을 별도로 사용하는 가능성은 남아 있다.

네 ID의 bound는 file-backed 데이터에서 모두 0으로 보이지만 시작 코드는 다르다. `0044e000`이 `0186c0bc`의 `7f7fffff`(FLT_MAX)를 EAX로 읽고 `0044e0b6/bb/c0/c5`에서 upper globals `020e73cc/d0/d4/d8`에 저장한다. `0044e174`의 vector store는 `01212310`의 `[0,−1,−1,−1]`을 lower stat32..35에 쓰며, `0044e17b`는 lower36 `01a76128`에 `bf800000`(−1)을 쓴다. 그러므로 확인한 **시작 설정**은 ID33..36의 lower −1 / upper FLT_MAX다. 현재 실행 중의 값·불변 cap·모든 getter가 이 bound를 사용한다는 주장은 아니다.

## 동일 stub의 바깥 consumer를 찾은 범위

선택 코드의 E8 후보는 `004b7c00`에 대해 `00860d1c`, `00860d35` 두 곳이다. 둘 다 older `BuffBehavior_GrantTemporaryResource` apply `00860cb0` 안에 있다. resource4와 resource5 각각의 분기에서 source ID, bearer ID와 양을 넘긴다. 다른 stat/heal consumer가 있다는 가정을 이 두 호출에 덧붙이지 않는다.

literal pointer `00860cb0`은 `0127db78`(vtable `0127db6c`+0c)에만 있다. `004b7c00`을 담은 다른 literal pointer `0121e9bc`는 `CKinSetActorRepUniform` RTTI의 vtable `0121e9b0`+0c다. 이는 동일 코드가 접힌 다른 의미의 virtual method이므로, 공유 주소의 class 이름을 resource 증폭 함수의 원래 이름으로 사용하지 않는다. `004b7c00`의 확인된 bytes `d9 ee c3`는 x87 0을 돌려준다.

독립 inlined clamp consumer를 찾기 위한 ID33..36 upper/lower 주소 검색에서는 초기화 store 외 사용 후보를 찾지 못했다. 단, indexed getter는 global base+index로 읽을 수 있어 이 검색의 부정 결과만으로 없다고 할 수 없다. fresh REA incoming references는 `004b7c00`의 위 두 CALL과 접힌 virtual pointer, `00860cb0`의 위 vtable pointer를 교차 확인했다. generic `00937480`의 12개 CALL은 여섯 외부 함수로 모인다. 전체 body를 대조한 결과는 아래와 같다.

| 후보/호출자 | 본문에서 확인한 실제 대상 | 이 조사에서의 판정 |
| --- | --- | --- |
| `00824960` → getter `00824aeb` | stat5(수정력)과 대상 combat graph | amp33..36 consumer가 아님 |
| `00832f60` → getter 세 곳 | stat4(무기력), stat40(레벨) | variable처럼 보인 decompile 문맥도 실제 인자4/40; amp 아님 |
| `00847f10` → getter `0084819a` | stat0(max HP), Rona 관련 graph | amp 아님 |
| `008ecb90` → getter `008ece3b` | stat0(max HP) 관련 계산 | amp 아님 |
| `0093e940` → getter `0093ea97` | 임의 stat/layer 값을 읽어 변경하는 공통 setter | 33..36도 표현 가능하지만 heal/barrier amount consumer가 아님 |
| `00944de0` → getter 다섯 곳 | level 초기화/성장, stat0/2/39 | amp consumer가 아님; level1은 33..36 layer0을 각각 0으로 설정 |

별도 raw SSE displacement `+218` 후보도 body와 객체 identity를 대조했다. `00915a40`의 두 참조는 `*KindredSoundBalance*`/Skye sound timing, `005456d0`은 좌표/행렬 변환, `004cbc90`은 `03f3` snapshot 직렬화였다. 숫자 offset이 같다는 이유로 actor의 outgoing heal layer2로 식별하지 않았다. 이는 **발견 후보를 배제한 기록**이며 모든 indexed/script/간접 consumer가 없다는 증명은 아니다.

새 behavior를 경유하는 우회도 분리했다. `ModifyAttribute` vtable `0121b2e4`, `GrantTemporaryResourceNew` `0121b134`, `ApplyBuffToSelection` `0121b428`는 각각 lifecycle slots +4/+8/+0c/+10이 모두 `0045ecd0`(`ret 4`)이다. 단일 +4만 확인한 앞선 결론을 네 슬롯으로 확장했다. **configure-time 우회도 없다:** `00529040`(ModifyAttribute)은 `8b c1 c2 0c 00`, `00528fc0`(New temporary resource)은 `8b c1 c2 08 00`으로, 둘 다 `mov eax,ecx; ret N`이며 actor 값이나 provider 설정을 저장하지 않는다. 따라서 factory가 attribute/layer/provider 인자를 전달했다는 사실과 이 selected body가 실제로 그것을 저장·적용했다는 주장은 구분된다. 이 범위 밖의 script·wire apply·server path까지 동일하게 비활성이라고 결론내리지 않는다.

## Rook, 핀 W, 라임 W와 passive

Rook's Decree의 `008f13c0`은 New temporary resource behavior에 **resource4**, provider `008362c0`을 설정한다. provider의 operand buff+21c는 raw source ID이고, local properties는 `BONUS_HEALTH_RATIO`/`BARRIER_STRENGTH`라는 이름을 갖는다. raw ID를 bonus HP 값으로 고쳐 쓰는 것은 근거가 아니다. 해당 provider와 New behavior가 accepted resource4를 실제로 만들었다는 경계를 닫아야 한다.

핀 W `Ability__Phinn__B`는 actor resource `4AB809A4E9DFF0585281C1AB70EAF2BC`, SHA `4df3571ea1e7cbd33a95ec068ba82f99c496b9d11beeee3549e76b54a3f0f9cf`에서 root+64 ability-pointer array의 index1로 연결된다. 선택 선언에서 B property6 `Fortified Health Base`의 +04/+08/+0c raw floats는 `100/25/25`, property7 `MaxHealthScaling` +04는 .05, property8 `DefenseFinnStatScaling` +04는 .18이다. rank/overdrive 계산 getter를 확인하지 않고 이 세 raw field에 계산 규칙을 붙이지 않았다.

W factory `008b4620`은 self 및 radius selection과 `Buff_Phinn_PoliteCompany_FortifiedHealth` 적용 graph를 만든다. buff factory `00908330`은 source의 HP·방어 관련 필드, B properties6/7/8 및 `Phaster` talent 유무로 `local_c`를 계산하고 older resource behavior `00811df0`에 **resource5**와 `local_c`를 설정한다. 이 provider 안에서 attribute34/36을 읽는 직접 식은 확인되지 않았다. 증폭이 존재한다면 이후 amount consumer에서 적용되는지를 확인해야 한다.

fresh `008353f0`은 첫 operand `x`와 source의 perk property0 `k`로 `x/(1+k)-x`를 돌려준다. 이를 `00908330`에 대입하면 talent 조정 전 requested amount는 아래 field-level 식이다. `C`는 source actor의 stat component, `P6/P7/P8`은 native B getter 결과다. 이 식에서 raw field를 검증되지 않은 “유효 bonus HP/방어” 이름으로 바꾸지 않았다.

```text
adjust(x) = x/(1+k) - x
F = P6 + (C[+d4] - adjust(C[+20]))*P7
       + ((C[+f0] - adjust(C[+3c])) + (C[+f4] - adjust(C[+40])))*P8
```

`Phaster` 분기는 이 F에 talent property를 곱하고 별도 behavior를 추가한다. 이 pre-resource 식과 이후 resource4/5 공통 helper의 0 반환을 분리해야 한다. local property base100을 바로 실제 W 양이라고 보고하거나, 속성 label을 근거로 이 식에 1.15를 추가하지 않는다.

라임은 `Reim`이다. actor resource `E69FFAF512614E619DEA07FF9CCA56E8`, SHA `daf3c1e1c840ac17fe51a510597e8850d5dfbc92127c83dbc1bb41f84c2839fe`의 B index1은 `Ability__Reim__B`/`삭풍`으로 연결된다. `008b5630`은 Damage와 `Buff_Reim_Immobilize` graph를 구성한다. W의 직접 보호막으로 해석하지 않는다. 별도 passive `00909390`이 `lastGainedBarrier`/`currentMaxFortifiedHealth`를 만들고 post-attack callback `00847620`, interval `00841f00`을 등록한다. perk property8/9/10의 local +04 raw 값은 각각 `FROSTGUARD_MAX_HEALTH_PERCENT=.4`, `FROSTGUARD_HERO_FORT_HEALTH=.15`, `FROSTGUARD_NONHERO_FORT_HEALTH=.025`다.

여기서는 앞선 함수 경계 미복구를 실제로 좁혔다. `00847620`의 bytes `e9 0b a6 ff ff`는 **`00841c30`으로 JMP**한다. 그 body는 mode!=0, combat+c=Reim bearer ID, combat+14!=bearer ID를 요구하고 combat+4==3을 거절한다. **combat context+18이 가리키는 actor**의 +1e0 bit0에 따라 property9/10을 골라 `gain=max(1, combat[+44]*ratio)`를 만든다. 이 actor pointer의 역할을 별도 event-layout 근거 없이 피해 대상이라고 확정하지 않았다. 두 invulnerability 관련 검사 뒤, resource가 없으면 **self→self resource5**를 `00858000`으로 만들고, 있으면 `maxHP*property8`의 잔여량으로 gain을 제한한 뒤 **엄격히 양수일 때만** `00858230`으로 증가시킨다. 이미 cap 이상이면 이 branch는 음수 보정을 보내지 않고 증가를 생략한다. 첫 생성 branch에는 이 maxHP cap 계산이 보이지 않아 양쪽을 하나의 capped 식으로 합치지 않았다.

이 증가 body와 `00858230`은 outgoing/incoming amp33..36을 읽거나 곱하지 않는다. `00858230`은 `delta=max(-current, requestedDelta)`를 resource+20에 더하고 양의 delta일 때 phase6을 보낸다. 따라서 고정된 combat+44·property·maxHP·기존 resource 입력 아래 **이 명시적 branch의 requested gain에는 축전판 배율이 없다.** 최종 서버 수치와 다른 script 단계까지 없다는 의미는 아니다. Reim W가 해당 post-attack event와 허용 combat category로 들어오는지까지는 아직 미결이므로, “W를 쓰면 항상 passive가 증가한다”는 결론은 내리지 않는다.

`00858000`의 다른 direct callers `0083e320`, `0083e640`, `0083ebd0`도 확인했다. 모두 자기→자기 resource4 재생 경로이고, 위치/시간 조건과 1,500 또는 800의 cap을 사용한다. 이 본문들에서도 amp33..36 소비는 발견되지 않았다. 각자의 trigger/hero identity를 축전판으로 치환하지 않았다.

후속 incoming-reference 조회에서 `00858230`의 확인된 외부 직접 CALL은 **여섯 곳**이다: `0083e5fb`(`0083e320`), `0083e867`(`0083e640`), `0083ef02`(`0083ebd0`), `00841ebc`(`00841c30`), `008420d4`(`00841f00`), **`00860e79`(`00860cb0`)**. 마지막 old-resource caller도 목록에서 빠뜨리지 않았다. 이 경로에는 신규 stack delta의 공통 0 helper 외에 기존 resource handle·generation·cached configuration·현재 stack 수에 따른 분기가 있으므로 모든 재계산을 하나의 “항상 0” 동작으로 합치지 않는다. 이번 조사는 해당 body/직접 caller를 대조했으며 알려지지 않은 간접/script entry가 없다는 증명은 아니다.

## B: 수치 증폭과 다른 이동 속도 경로

앞선 exact factory→handler→predicate 검사는 유지한다. Control의 `BuffCallback_Heal` mask `0x48`은 phase3/6만 선택하고, source ID가 buff+21c와 일치해야 하며, **target이 축전판 bearer 자신이면 거절**한다. actor filter도 통과해야 한다. `0086f4f0`은 source/target ID·pointer 및 amount를 event에 담아 callback component에 보낸다.

older temporary resource producer `00858000`은 양이 양수일 때 phase6을 보낸다. `00860cb0`에서는 mode byte `0209e204!=0`과 양의 stack delta를 확인한 뒤 resource4/5 공통 계산 함수를 지나간다. 선택 body에서 그 함수가 0을 돌려주므로 이 경로의 새 양수 phase6은 성립하지 않는다. 다른 accepted resource 변화나 script가 event를 만들 수 있는지는 별도 문제다. phase6 자체가 있어도 SelectHealTarget 이후 Lockout 적용 lifecycle이 위 stub이면 해당 graph만으로 SpeedBoost 수락까지 이어지지 않는다.

따라서 B가 보였다는 관찰은 A의 15% 수치를 증명하지 않으며, A의 resource 증가만으로 B의 다른 수신자·lockout 조건을 증명하지 않는다. Lyra 자체 speed 등 별도 hero 효과도 대조군에서 분리해야 한다.

| 요청 사례 | 이번에 닫은 정적 값 경로 | 실제 효과 결론 / 남은 경계 |
| --- | --- | --- |
| 축전판 A 일반 회복 | outgoing36/layer2 인자, 0으로 시작하는 네 layer, 저장하지 않는 configure와 lifecycle | 실제 heal amount consumer가 미복구여서 1.15·중첩 식 인증 불가 |
| 축전판 A 일반 보호막 | outgoing34/layer0 인자와 같은 저장/적용 stub 경계 | 실제 incoming33/outgoing34 합성 순서·수치 인증 불가 |
| Rook's Decree | resource4/provider → New behavior, configure와 모든 확인 lifecycle이 stub | 이 selected graph에서 accepted amount 생성까지 이어지지 않음; live server 결과는 별도 |
| 핀 W | resource5 requested F와 talent 분기 → old apply의 resource4/5 공통 0 반환 | F의 15% 증가를 입증하지 못함; resource5라는 이유로 서버 증폭 미지원이라고도 할 수 없음 |
| 라임 passive 기존 resource | 고정 damage/property/HP/current 입력 → cap 잔여량 → 양의 delta 직접 더함 | 이 explicit delta에는 amp계수가 없음; 다른 단계·서버 결과와 W 진입 category는 별도 |
| 축전판 B 자기 수신 | predicate의 target=bearer 거절 | 이 callback에서 제외; 다른 hero/item 자체 speed의 부재는 주장하지 않음 |
| 축전판 B 다른 수신 | phase3/6·source·actor filter → target selection → Lockout/SpeedBoost graph | Lockout apply stub 및 현재 live 관측 부재로 accepted speed 미확인 |

## 최소 재현 사례와 관측 항목

다음은 실행 결과가 아니라, 이후 가능한 승인된 환경에서 판별력을 갖는 최소 사례다. [환경 조사](03_VALIDATION_ENVIRONMENT.md)의 현재 관측은 게임 process 부재와 잠긴 WTS session으로 native effect 관측이 막혀 있음을 확인했다. 실행·unlock·instrumentation을 수행하지 않았다.

| 사례 | 통제 입력 | A를 판별하는 관측 | B를 별도로 판별하는 관측 |
| --- | --- | --- | --- |
| P1 핀 W → 다른 영웅 | 같은 rank·HP·추가 HP·armor/shield·talent, Cap만 유무 변경 | source stat34/36 네 layer와 consumer 입력/출력, resource5 accepted amount·instance | positive phase6, source/target generation, Cap predicate, Lockout와 SpeedBoost 수락 |
| P2 핀 W → 자기 자신 | P1의 self recipient만 비교 | resource5 수치 증폭은 self에도 있는지 독립 측정 | 확인한 predicate의 self-target 거절과 일치하는지; Cap 외 speed와 분리 |
| R1 Rook → 다른 영웅 | 동일 추가 HP·발동 hit·대상, projectile 적중/불발 분리 | resource4 provider 실제 입력과 accepted amount, stat34 consumer | 동일 event와 lockout 조건; miss일 때 무조건 발동 가설 반증 |
| I1 incoming/outgoing 분리 | source만 Cap / target만 Cap / 둘 다 없음 | source34/36과 target33/35를 따로 관측; 합성·곱셈 순서 기록 | bearer·source·target 관계를 각각 확인 |
| M1 라임 W와 passive | 같은 target type·damage·기존 fortified 상태, W와 별도 attack 비교 | 직접 W graph와 passive 증가 callback을 구분; resource5 cap/증가/감소 시점 | self recipient는 Cap callback 거절 예상; 다른 source 효과 혼입 방지 |

값 비교는 전체 HP bar나 tooltip만으로 하지 않는다. resource ID4/5, source/target actor generation, buff instance, accepted action 전후 값 및 실제 amount를 같은 시각에 묶는다. zero/초과 회복, 기존 lockout, talent, 거절된 buff와 projectile 불발은 별도로 기록한다. synthetic model은 후보 식의 모순을 드러낼 수 있지만 실제 consumer를 고르거나 accepted effect를 생성한 증거가 아니다.

## 근거와 검증

원본 REA envelope의 SHA-256·evidence ID·subject hash는 [REA_RECEIPTS.json](REA_RECEIPTS.json)에 있다. 아래는 실제 확인한 첫 직렬 session `effect-closure`의 파일 번호이며 raw export 자체는 private에 보관한다.

| 닫은 범위 | REA 파일 번호 / 주소 |
| --- | --- |
| 공통 0 helper, old resource apply의 incoming edges | 004 `004b7c00`, 017 `00860cb0` |
| generic raw getter의 모든 확인된 incoming references와 실제 caller body | 008 `00937480`; 041 `00824960`, 042 `00832f60`, 043 `00847f10`; 이전 batch의 `008ecb90`, `0093e940`, `00944de0`도 대조 |
| outgoing/incoming clamp global references | 009..016, read-bytes031 `0044e000` |
| configure-time 무저장 | 023 `00528fc0`, 024 `00529040` 및 SHA-gated opcode 확인 |
| 같은 +218 offset의 다른 객체를 배제 | resolve036..039, pseudo040/044/045 |
| Phinn pre-resource 조정 helper | 046 `008353f0`, 이전 batch `00908330` |
| Reim post-attack JMP와 증가 body | resolve021, read022 `00847620`; pseudo047/assembly054 `00841c30` |
| 공통 temp-resource producer의 독립 caller와 increment body | incoming006/007; pseudo048..050, 051 `00858230` |
| actor의 생성/level 초기화 진입 | 035 `0093fba0`, 052 `00941b60`, 053 allocation-descriptor xrefs; 실제 zero loop는 새 PE 검사에서 고정 |

별도 단일 후속 session `effect-closure-followup`의 **004 pseudo / 007 assembly `0081c640`**은 zero loop를 확인했고, **005 resolve `00957760`**은 실제 wrapper entry `00957710`을 식별했다. **006 incoming `00858230`**은 위 여섯 외부 CALL을 확인했다. 두 Ghidra project를 동시에 실행하지 않았으며 후속 session은 완료 후 닫았다. 이 파일 번호도 같은 공개 receipt 목록에 session을 구분해 보존한다.

`00450910`의 거대한 incoming-reference 조회 005는 transport response budget을 초과해 이 문서의 consumer 부재 증거로 사용하지 않았다. 함수 경계가 없는 initializer와 Reim jump는 실패를 숨기지 않고 raw bytes·상대주소·확인된 도착 body로 보완했다. 이 표가 모든 server/script/간접 실행 경로의 완전한 inventory라는 주장은 아니다.

```powershell
python -m vg.research.capacitor_value_paths --binary <selected-Vainglory.exe> --data-root <installed-Data> --output <research-output.json>
```

재현기는 원본 게임 파일을 쓰지 않는다. executable/resource SHA, property symbol·pointer, clamp initializer, config stub, Reim jump, constructor zero loop 및 call 후보를 검사한다. UTF-8/LF output은 보존 JSON과 byte-identical하게 재현됐고 잘못된 EXE는 내용 해석 전에 거절했다. [전체 검증 기록](VALIDATION.md)은 독립 reviewer의 훼손 resource 거절·관련 46개 test와 native 환경 제한을 구분한다. 테스트 통과는 실제 heal/barrier/speed 효과 실행을 뜻하지 않는다.
