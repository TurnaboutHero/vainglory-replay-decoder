# 관통·파쇄·동일 아이템: 구성 산술과 실제 피해 경계

선택 x86 LAA EXE SHA-256 `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`. 기준7753523 이후의 새 REA/Ghidra 근거다. [01_NAMES_AND_ITEMS.json](01_NAMES_AND_ITEMS.json), 이전93개 [선언 목록](../passive_items_2026-10-16/ITEM_CATALOG.json), [PE_CHECK.json](PE_CHECK.json), [REA_RECEIPT.json](REA_RECEIPT.json)을 함께 읽는다. 아래 계수는 server damage 공식의 검증 결과가 아니다.

## 1. 공통 능력치 경로와 단위

`007d1410`(070)은 stat7 ARMOR,8 SHIELDING,9 ARMOR_PIERCE,10 BONUS_ARMOR_PIERCE,11 SHIELDING_PIERCE,12 BONUS_SHIELDING_PIERCE를 localization label로 연결한다. **BONUS라는 이름만으로10/12를 고정 수치 관통이라고 단정하지 않는다.** 8은 barrier resource4가 아니다.9/11의 item property는.1/.2/.3/.45 같은 coefficient지만, 방어 수치를 줄이는지 피해 일부를 우회하는지는 최종 소비자에서 별도 증명해야 한다.

`0092f980`(020 assembly)의 item definition+2c 목록은 entry+4 양수를 ActionModifyActorAttribute의 **layer1**과 ADD mode로 구성한다. entry+8 양수는 layer2를 구성한다. 원본 entry+c=2를 action layer2로 그대로 해석하면 틀린다. `0094f1d0`(069)→`0093e850`(087)→`0093e940`(027/111)→`00937480`(026)→`0095c710`(028)→`0095c590`(025)가 현재값+operand를 해당 layer에 저장한다. 부여 producer는 mode0209e204!=0 경계다. ordinary stat은 item instance별 부여와 passive shared buff를 구별한다.

유효 getter layer-1(전체)은 `E=(B+(1+M)*A)*(1+T)`다. 배열 payload에 B/A/T/M을 둔다. `0093e850`은 actor+20 component를 불러오고 `0093e940`은 component+20 payload를 getter에 준다. getter 자체는 상한/하한을 적용하지 않는다.9/11에2 또는 음수를 넣는 합성 입력도 그 값으로 계산된다. 이는 실제 아이템으로 그 상태를 만들 수 있다는 증거가 아니다. per-caller clamp와 서버 게임 규칙의 상한을 혼동하지 않는다.

## 2. Named 관통은 단계 차액을 구성한다

| Buff factory | 설정 | provider 식(selector1 item property0) |
| --- | --- | --- |
| `008f04a0`(043) | attr9/layer1 | PiercingSpear=.1 thunk00867a50 |
| `008edd90`(039) | attr9/layer1 | `00868f90`(052): Bonesaw(.2)−Spear(.1) |
| `008f3190`(044) | attr9/layer1 | `00869280`(054): TensionBow(.3)−Bonesaw(.2) |
| `008f0440`(041) | attr11/layer1 | PiercingShard=.1 thunk00867a20 |
| `008ee190`(042) | attr11/layer1 | `00868ff0`(053): BrokenMyth(.45)−Shard(.1) |

로컬 TensionBow480은 SpearPen/TensionPen/BonesawPen을 모두 선언하고 Bonesaw482는 SpearPen/BonesawPen을 선언한다. BrokenMyth496은 ShardPen/BrokenMythPen을 선언한다. 따라서 하위 marker를 한 번씩 적용하는 조건이면 단계 차액 합이 최고 단계 값으로 망원 합산된다. 임의 모든 passive에 적용되는 generic numeric MAX 구현을 발견한 것은 아니다.

각 selected marker cap1/reuse policy0, 동일 active definition hash 재사용 및 item ledger 정리는 이전 연구와 새01자료에서 확인했다. **현재 active marker 집합이 각 이름당 하나이고 lifetime effect가 실제 적용되는 조건**에서 다음 구성 산술이 나온다. 생성 큐의 중간 상태·실패·재사용 ID 수렴을 이 표가 재현하지 않는다.

| 장착 구성 | 조건부 attr9 계수 | 조건부 attr11 계수 | ordinary 장착 선언 |
| --- | --- | --- | --- |
| Bonesaw1 /2 /6 | 약.20 / .20 / .20 | 0 | WP30 /60 /180 |
| TensionBow1 /2 | 약.30 / .30 | 0 | WP40 /80 |
| TensionBow1+Bonesaw1 | 약.30 | 0 | WP70 |
| BrokenMyth1 | 0 | 약.45 | CP50,1slot |
| BrokenMyth2 | 0 | 약.45 | CP100,2slots |
| BrokenMyth3 | 0 | 약.45 | CP150,3slots |
| BrokenMyth4 | 0 | 약.45 | CP200,4slots |
| BrokenMyth5 | 0 | 약.45 | CP250,5slots |
| BrokenMyth6 | 0 | 약.45 | CP300,6slots |

이는 구성 산술이며 실제 HP 피해 예측이 아니다. 원시 property float32는.45=3ee66666 등이며 표시는 반올림했다. 신화6개를 관통270%로 더하는 모델은 이 named 구성과 맞지 않는다. CP에 의한 ability scaling은 이 연구의 고정 raw damage 비교에서 제외한다. 슬롯과 지출이 달라지는 구성들을 승률·골드 효율이나 추천 빌드로 비교하지 않는다. 가격을 새로 해독하지 않아 금액도 임의로 채우지 않았다. 과거6신화 빌드의 다른 버전 효과는 이 표의 해석 범위 밖이다.

## 3. 대상 뼈톱 파쇄는 공격자 관통과 별개

이전 exact-build `008edcc0` 구성은 target attr7/layer2에 −SHRED를 준다. local SHRED=.1, definition cap5다. 기존 after-damage0083aa30 trigger와 timeout00824ec0, generic stack delta00861530→041c action 경로를 재사용한다. 이미 수신·적용된 n stacks가 layer2에 선형 합산되고 다른 layer가0인 조건이면 target armor=`baseArmor*(1−.1*n)`이다. n=0..5이므로 조건부 남은 armor는100/90/80/70/60/50%다. 한 attack에서 새 stack 적용 전/후 어느 값을 쓰는지는 after-damage trigger 이름만으로 메우지 않는다.

[04_HERO_DEFENSE.md](04_HERO_DEFENSE.md)는 사슬니의 armor30+5*(level−1), shielding20+3.637*(level−1) 및 레벨별0/5파쇄 표를 제공한다. 사슬니 passive provider는 별도 `1−.07*n`을 구성한다. armor에 passive35%를 더하거나, 뼈톱이 그 배율까지 파쇄한다고 계산하지 않는다.

## 4. 실제 피해 계산의 닫히지 않은 경계

이 selected EXE의 `BuffBehavior_ModifyAttribute` 및 `BuffBehavior_MultiplyDamage` 구성과 local dispatch에는 folded client stub이 있다. Combat callback`00947cb0`(102)은 predicate`0095fa10`(106) 통과 시 behavior virtual+4를 호출한다. MultiplyDamage vtable0121b690의 그 slot은0045ecd0 `ret4`다. typed accessor00459660은 this를 반환할 뿐이다. 이 route는 provider를 이용해 실제 피해량을 변경하는 구현이 아니다. 그렇다고 독립 서버 구현이나 모든 native route가 없다는 결론도 아니다.

실제 health apply `0094e970`(010)은 이미 계산된 음수 amount를 `0086eb50`(009)로 나누어 barrier4/fortified5/HP0 등의 자원에 반영한다. 그 split은 armor/penetration 계산기가 아니다. 기존 `00938a20`의 reciprocal 식은 last-hit HUD 추정이며 attacker penetration을 읽지 않는다. 이를 현재 서버 피해식으로 대체하지 않았다.

관통 상한 변수020e736c의 bounded xref(079)는 초기화 store만 잡혔다. shield-pierce 변수020e7374는 별도 Adagio callback008385e0(109)에서 damage context에 더해지는 것을 확인했지만 최종 전달은 후속 `procedure_assembly(008385e0)`의 `0083886c CALL00450910`으로 닫혔다. 이 context도 empty client leaf에 전달되므로 실제 관통 피해 적용은 증명하지 않는다. 어느 경우도 전체 계산 순서·음수 방어·고정/비율 관통 합성이나 실제상한을 닫지 않는다. 부재 xref는 indexed getter의 부재 증명이 아니다.

따라서 현재 근거로는 **최종 HP damage에서 관통→파쇄→사슬니 배율의 연산 순서, 관통의 방어감소/피해우회 모델, 음수 방어 처리, 최종 피해 상·하한**을 확정할 수 없다. 미확정 식을 넣은 레벨별 피해 효율 곡선은 생성하지 않았다. 제공한 것은 유효 stat·구성 계수·base-defense 조건부 표다.

## 5. 재현·반증과 다음 실측

`vg/research/stat_stacking_model.py`는 getter와 위 **조건부 marker 집합** 산술만 담는다.이는 float32 입력/최종 저장을 사용하는 대수적 witness로, 모든 입력에서 x87/SSE 명령별 반올림과 bit-exact하다는 주장은 아니다.5개 합성 검사는 중복1..6의 고정 stat/marker 분리, 다른 아이템 coefficient 단순 합산 반례, target T와 attacker A 분리, 임의 clamp 삽입 방지 및 오염 입력 거절을 검사한다. 서버·리플레이 재현 검사가 아니다.

동일 build, 동일 actor level·기본 stats, raw damage100, crit/추가proc/방어막/회복0을 고정한 독립 표본이 필요하다. accepted attr9/10/11/12 및 target7/8, buff instance/source/stack, 사슬니 provider state를 동시에 관찰하고 normal hit와 named proc를 분리한다. target armor0/양수/가능하면음수, Bone stack0..5, itemduplicates1..6을 한 변수씩 바꾼다. 실제 수신 attr·HP delta가 구성 표와 다르면 marker 적용/실제 실행 가정을 폐기한다. 서버 관측을 새 임의 공식으로 적합하지 않는다. H5810은 개발 표본이며 이 실측을 수행한 독립 표본이 아니다.
