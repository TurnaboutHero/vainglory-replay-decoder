# 사용 아이템: 요청·선택·적용 경계

선택 EXE SHA-256 `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`의 정적 분석이다. 로컬 asset 선언은 [NAMES_AND_DEFINITIONS.json](NAMES_AND_DEFINITIONS.json), 명령별 원본 export hash와 evidence ID는 [REA_RECEIPT.json](REA_RECEIPT.json)에 연결한다. 실제 화면·라이브 서버·독립 리플레이 검증은 하지 않았다.

## 1. 공통 흐름과 새로 닫힌 경계

기존 `0094ee90`은 요청 actor/item instance/ability를 찾는 활성화 입구다. 그 입력 target을 최종 수혜자 집합으로 부를 수 없다. 새 factory 등록은 Fountain `00899170`, Crucible `00898b70`, WarTreads `0089a480`으로 연결된다(031–033). 아래는 factory가 만드는 behavior graph이며 전체 서버 실행을 복원했다는 뜻은 아니다.

- `005256b0` → `AbilityBehavior_AddMyselfToSelection`; vtable `0121a668+18` → `0085a750`, actor를 selection에 추가한다.
- `00526030` → `ClearSelection`; `0121a640+18` → `0085b440`, selection 객체를 반환하고 ability+30을 0으로 만든다.
- `00527e00` → `00819ce0` → `SelectInRadius`; `0127d4e8+18` → `0085db70`. owner 위치를 중심으로 factory의 반경을 제곱하고 `00858bd0`의 최대 200개 후보 filter를 거쳐 generation을 포함한 selection에 `008595b0`로 넣는다.
- `00525860` → `00819420` → `ApplyBuff`; `0127d3a8+18` → `0085a890`. **mode `0209e204!=0`에서만** selection을 돌고 name/hash, source actor, 각 대상, duration/stack provider 등을 구성하여 `0092d8d0`에 ApplyBuff를 큐잉한다. 생성 요청은 기존 `0094c9a0` 수신·적용과 별개다.
- `00525990` → `ApplyBuffToMyself`는 이 EXE에서 `0121a2c8+18`이 `0045e8a0`의 `ret 8`로 연결된다. decompiler의 gloox 이름은 동일 코드 병합 결과이며 게임 의미의 함수명이 아니다. 로컬 dispatch로 이 behavior의 실제 버프 생성은 증명하지 못한다.

[PE_CHECK.json](PE_CHECK.json)은 위 6개 vtable edge와 `ret 8` 바이트를 SHA gate로 재확인한다. factory/constructor/dispatch 출처: 052–057, 061–069, 071–083.

`ActorFilterSelector`의 `0127d1a4+8` → `0092cbb0`은 owner/candidate team byte+17c, actor 종류, 제외 ID, 위치·반경 등을 검사한다. factory는 selector+48 mask를 `0x10`으로 구성하지만, 기본 생성자의 +50 flag와 전역 구성에서 파생되는 `0x100` 등의 분기가 팀 조건을 우회할 수 있다. 따라서 단일 mask나 아이템 설명만으로 “항상 모든 아군 영웅”이라는 수혜자 집합을 확정하지 않는다. 다음 실험은 실제 초기화된 selector 전체 필드와 후보별 accept/reject를 기록하는 것이다. selection의 최대 200 후보와 저장 단위 8개도 효과 stack cap이 아니다.

## 2. 재생의 분수 — 생명의 샘과 구별

리소스 487의 factory `00899170`은 `Buff_Item_FountainOfRenewal`을 **ApplyBuffToMyself** helper에 주고 duration provider `008678a0`를 구성한다. 이후 sound, radius selector(RANGE property2), presentation, SetHasFired를 잇는다. 이것만으로 radius selector의 모든 actor가 heal 수혜자라는 결론은 나오지 않는다. 자기 적용 helper의 local dispatch는 위 stub 경계다.

버프 factory `008efac0`는 onBuffInterval → `00838070`을 등록한다. callback은 mode!=0일 때 buff bearer의 current HP와 산출 maximum HP를 읽어 `property0 * (1-current/maxClamped) * 100`을 계산하고 buff source+21c, owner+178, buff instance+220이 포함된 combat/health 교환 구조를 후속 helper에 전달한다(058). 이것은 periodic buff bearer 계산이고, ability selection 전체를 heal하는 루프가 아니다. interval 수, 수신 ApplyBuff duration, health 최종 반영/회복 증폭까지 독립 확인이 필요하다.

로컬 선언: HEAL_PER_PCT_MISSING_HEALTH=2.5, HEAL_TIME=3, RANGE=12, ability Cooldown=75. 선언과 callback 식을 그대로 연결하며 2.5를 초당 2.5%로 재해석하지 않는다. 생명의 샘 504의 별도 callback/자원0 producer는 [02](02_REGEN_AND_DEFENSE.md) 참조.

반증 조건: 선택 build에서 위 vtable/registry/asset hash가 다르거나 실제 accepted ApplyBuff가 다른 대상·duration을 사용하면 graph 이상의 추정을 폐기한다. 독립 replay의 실제 수신 buff/health event와 활성화 시각·대상을 교차 대조해야 한다.

## 3. 도가니 — 선언된 두 버프와 미확정 정화

`00898b70`은 owner를 먼저 selection에 추가하고 `Buff_Item_ReflexBlock`과 `Buff_BlockDebuffs`를 각각 stack1로 구성한다. duration은 별도 `*Item_ReflexBlock*` property2를 읽는다. ClearSelection 후 Crucible RANGE property0를 쓰는 radius selector를 구성하고 같은 두 버프를 다시 연결한다. 따라서 두 버프를 구성한다는 근거는 이름 추측이 아닌 실제 factory 포인터다. ApplyBuff의 mode!=0 큐 경계를 넘은 실제 수신은 미확인이다.

`008f0f70`은 먼저 `0209e208!=null`, `*0209e208==0x1c`, bearer actor+188==hash(`DAT_0128a640`) 조건이 함께 맞으면 즉시 반환한다. 이 미해독 mode/actor 예외를 통과한 ReflexBlock buff는 buff+24c 비트를 바꾸고 selector4 behavior에 `0095a840`을 설정한다(022/059). 이 provider는 mode0에서 값0, 나머지 모드에서는 ReflexBlock property0/1과 actor attribute 계산값을 이용한 보간 후 0 아래를 clamp하고 출력 두 번째 값에 -1을 준다. 이는 selector4에 값을 구성하는 근거이며, Husk fortified helper의 selector5와 다르다. 기존 resource enum의 4/barrier·5/fortified health와 이 helper의 실제 apply/inverse 연결은 추가 확인이 필요하다. 정확한 level/attribute 의미와 apply/inverse 수명은 미확정이다. BlockDebuffs의 실제 기존 debuff 제거·신규 debuff 차단 동작은 이번 범위에서 닫히지 않았다. “정화+면역”을 완료 판정으로 쓰지 않는다.

로컬 Crucible RANGE=12, ability Cooldown=75. 지속 시간은 Crucible 속성에서 임의로 가져오지 않는다. 다음 실험: ReflexBlock 별도 정의와 accepted buff duration, resource4 before/after, 기존 debuff와 신규 debuff 수신을 각각 구분한다. effect loop/end graph는 화면 확인이 아니다.

## 4. 전쟁 걸음 — 팀 범위와 duration provider

`0089a480`은 owner selection → presentation → ClearSelection → RANGE property3의 radius selector → `Buff_Item_WarTreads_Speed` ApplyBuff(stack1, duration callback `0086cdd0`) → SetHasFired graph를 만든다. `0086cdd0`는 selection에서 actor+1e0 bit1을 가진 수를 세어, count>1이면 `BASE_DURATION + (count-1)*PER_ALLY_BONUS_DURATION`을 출력한다(060). field bit을 단순히 모든 아군 수와 동치로 보지 않는다.

로컬 선언은 RANGE12, BASE_DURATION3, PER_ALLY_BONUS_DURATION0이므로 이 asset에서는 수에 따른 가산항이 0이다. SPEED3, ability Cooldown60도 선언이다. buff factory `008f3a50`은 speed behavior/provider `00868020`과 별도 callbacks를 구성한다(024). 실제 이동 속도 합성, 종료 inverse, cooldown 시작/거절 시 소비는 아직 열려 있다.

## 5. 검증 수준과 다음 표본

정적: factory → 정확한 behavior class/dispatch/mode gate, selected asset property, native recipient enumeration 및 provider 식까지 확인했다. 합성: catalog decoder의 구조·오염 입력 검사는 별도 test다. replay 교차 대조와 실제 화면 검증: 0건. H5810은 개발 표본이며 독립 검증 표본으로 사용하지 않는다.

다음 최소 표본은 각 활성화에 대해 request, accepted action, actor generation, buff source/target/instance, duration, resource4/5/0, cooldown before/after를 동시 관찰해야 한다. 수신이 없으면 서버 전용 생성 경계로 남기고 이름/설명으로 보충하지 않는다. 이 보고서로 production 예측·자동 효과 적용 기능을 추가하지 않았다.
