# 피해 순서: 역호출자, 별도 자원 경로와 판별 가능한 실험

기준 `010c67c`, 선택 Windows x86 LAA SHA-256 `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`. 정적 분석이며 게임·서버 실행, 외부 웹, production 변경은 하지 않았다. 기존 [관통 경계](../stat_stacking_2026-10-16/06_PENETRATION.md), [사슬니](../stat_stacking_2026-10-16/04_HERO_DEFENSE.md), [Phinn/Reim 자원 구분](../stat_stacking_2026-10-16/05_CAPACITOR_AND_RETIRED.md)을 재사용한다. 아래 새 역호출자 결과는 기존 경계와 구분한다.

## 1. 현재 닫힌 입력·출력 경로

| 대상/시작점 | 확인된 producer와 입력 | 실제로 확인된 출력 | 여기서 입증하지 않는 것 |
|---|---|---|---|
| 사슬니 `008e5b60` factory | Combat callback, target-ID selector, event mask0x20; MultiplyDamage behavior에 `008423f0` provider 지정 | provider 자체는 buff u16count와 actor property2로 `1-p*n` 반환 | 이 함수가 호출되어 실제 damage context를 바꾼다는 전체 실행 경로 |
| Combat dispatch `00947cb0` | `0095fa10` predicate와 context | 통과하면 등록 behavior virtual+4 호출 | MultiplyDamage의 해당 slot은 `0045ecd0` 빈 함수라서 피해 곱셈 실행 근거가 아님 |
| Phinn W `008b4620` | self/radius selection, named `Buff_Phinn_PoliteCompany_FortifiedHealth` | buff factory `00908330`이 source HP/방어·ability property 및 별도 Phaster 분기를 읽어 resource5 amount를 구성 | 수혜자 전체의 실제 accepted fortified-health 값, server 증폭 순서 |
| temporary resource `00860cb0` | mode nonzero, resource selector4/5, stack delta/current count | `004b7c00`을 거친 amount로 `00858000` 또는 기존 resource adjust 경로 선택 | `004b7c00`은 선택 EXE에서0 반환. 반환0을 server의 기능 부재로 해석할 수 없음 |
| resource producer `00858000` | source, target, resource selector, amount, buff instance | component에 selector+1c/amount+20/instance+24를 넣고 `0092e950`으로 queue에 복제. amount>0이면 `0086f4f0(6,source,target,amount)` | 이 알림은 queued resource action의 최종 수락이나 damage mitigation 순서를 보증하지 않음 |
| Reim perk `00909390` | lastGainedBarrier/currentMaxFortifiedHealth 초기0, interval0.1 | `onPostCalculateAttack`에 `00847620`, `onBuffInterval`에 `00841f00` 등록 | 직접 W damage/root graph와 동일 실행이라고 주장하지 않음; fresh047/054는 아래 별도 resource5 producer를 닫음 |
| Reim interval `00841f00` | mode nonzero, instance-ID로 resource lookup, amount>0, 저장 clock | actor state4면 제거 경로; 일정 시간 경과면 property6/7·현재 최대값 기반으로 음의 resource adjust | 현재 공격 raw damage를 읽어 armor/pen을 합성하는 함수가 아님. attack→resource 생성은 아래847620 jump target841c30에서 별도로 확인됨 |
| health receive `0094e970`→`0086eb50` | 이미 계산된 음수 amount, actor/source IDs·flags | barrier4/fortified5/HP0 등에 분배 | armor와 penetration을 최종 합성하는 계산기라는 근거 없음 |

사슬니 vtable `0121b690`의 RTTI가 MultiplyDamage인 것과 실제 실행은 구분한다. typed accessor `00459660`은 this 반환, Combat virtual slot의 `004b7310`과 `004a8190`도 빈 본문이었다. 같은 class 이름의 server 구현이나 다른 독립 consumer는 이 선택 route의 stub만으로 배제되지 않는다.

## 2. 별도 consumer와 역호출자 조사 범위

기존 `008e1120`과 `008ecb90`은 owner generation을 검증해 연결 actor를 찾고, effective defense에서 base를 빼거나 property로 계산한 값을 attribute7/8 layer1에 복사하는 별도 consumer다. 첫 추출 요청의 내부 주소 `008e124c`/`008ecca6`를 함수 시작점으로 오인하지 않는다. 이들이 방어를 읽는다고 해서 damage mitigation 함수나 Phinn/Reim 구현으로 이름 붙이지 않는다. 해당 source/buff registry를 별도로 연결해야 한다.

기존 Adagio `008385e0`은 damage context에 shielding-pierce 계수를 포함하지만 최종 전달 call `0083886c→00450910`이 선택 클라이언트의 빈 leaf로 닫혔다. 이는 일반 공격 관통 순서를 증명하지 않는다. `00938a20`의 reciprocal 계산은 last-hit HUD 추정이며 공격자 penetration을 읽지 않는다. 이 두 예를 서버 피해식 대신 쓰지 않는다.

필요한 역방향 측정은 `008423f0`의 주소 사용처(직접 CALL뿐 아니라 factory 함수 포인터), Combat dispatch/필터의 caller에서 event index5/6의 실제 stage, `00847620`의 attack context 입력과 resource producer 출력이다. 범위가 제한된 xref가 한 factory만 반환해도 모든 간접 provider 호출이 없다는 증거로 쓰지 않는다. 부모의 단일 REA 세션에만 이 대상을 요청했다.

## 3. 최소 비교는 식의 적합보다 중간 상태를 먼저 기록한다

동일 build와 actor lifetime, target 레벨, raw physical damage, 공격자 weapon/ability scaling, crit/proc, 비용/slot 조건을 고정한다. 가능하면 직접 stat 입력을 조절하는 허가된 controlled fixture를 쓰고, 실제 아이템을 바꿨다면 raw damage와 추가 proc가 동일하다고 추정하지 말고 함께 기록한다. 여기서는 실험을 실행하지 않았다.

1. target armor가0인 baseline과 서로 다른 두 양수 armor 수준을 기록한다. 각 수준에서 공격자 accepted pierce0/양수 한 값만 바꾼다. 최종 HP와 함께 damage context의 mitigation 직전/직후 amount, 실제 effective armor와 pierce를 기록한다. armor0에서 pierce 변화가 영향을 주는지는 방어 감소/우회 등 가설을 분리하는 단서이나, baseline 결과만으로 특정 식을 확정하지 않는다.
2. 같은 두 양수 armor에서 공격 직전 이미 수락된 Bonesaw target stack0/5를 비교한다. 해당 공격이 만든 새 stack은 다음 입력과 분리한다. source/target generation, target attr7 네 layer와 accepted action 순번을 캡처한다. 첫 공격에 최대 stack을 주입한 모델을 실전 순서라고 부르지 않는다.
3. 위 조건 중 하나를 고정하고 사슬니 passive0/5만 바꿔 피해 context의 각 stage를 비교한다. 최종 damage 비율만 보고 armor 전/후를 결정하지 않는다. 사슬니 효과가 독립 상수 배율이고 나머지 stage도 순수 곱이면, 두 배율의 순서는 교환 가능하므로 최종 HP만으로는 원리상 구별할 수 없다.
4. armor shred와 pierce가 모두 armor에 적용되는 단순 비율이라고 가정한 두 가설도 서로 교환 가능할 수 있다. 그 경우 armor0/양수의 최종 damage만 늘려도 순서가 식별되지 않는다. 검증된 additive modifier, clamp/threshold, immunity 또는 관측 가능한 중간 amount가 있어야 순서를 판별할 수 있다. 그런 연산이 실제 존재함을 확인하기 전에 임의 flat penetration이나 음수 armor 규칙을 도입하지 않는다.
5. HP가 충분하고 barrier/fortified/회복이0인 상태로 damage-order 표본을 먼저 분리한다. Phinn/Reim 자원 경로는 이후 동일 amount의 별도 barrier4/fortified5 상태로 반복하여 health split 경계만 본다. 기존 자원의 감소를 armor mitigation 전 raw damage로 착각하지 않는다. Reim에서는 interval decay와 attack-generated gain을 timestamp/instance로 구분한다.

이 최소 단계들은 틀린 동일시를 배제하는 계획이며 실제 server 식의 예상 수치를 넣지 않는다. 두 가설이 관측 가능한 모든 출력에서 같으면 결과를 '미식별'로 남긴다. 임의 산술을 구현한 재현 test는 native 또는 server 재현 검증이 아니므로, 입증 전 damage-order model/test를 만들지 않았다.

## 4. 수락 기준과 반증

닫힘의 기준은 concrete raw-context producer→조건/provider 평가→actual field write→하류 serialization/accepted amount→resource split의 주소·필드·mode guard 연결이다. received health amount와 constructor의 raw input만 연결해서 중간 mitigation 순서를 채우지 않는다. 관측된 target layer나 actual loaded property가 선언과 다르면 그 run을 다른 build/state로 표시하고 표를 재사용하지 않는다. 누락된 callback, zero helper, stub 경로 또는 rejected action은 성공으로 세지 않는다.

현 단계의 정확한 미해결점은 실제 server/독립 consumer가 armor·target shred·attacker pierce·사슬니 factor를 어떤 입력과 순서로 사용하는지다. client의 구성 선언·provider 반환식·health split은 각각 확인되지만 그 사이를 가정으로 연결하지 않는다. H5810은 기존 unmatched 개발 표본이며 이 실험의 독립 검증이 아니다.

## 기존 입력 receipt

이 절의 기존 native 입력은 [stat_stacking REA_RECEIPT.json](../stat_stacking_2026-10-16/REA_RECEIPT.json)의 complete-envelope hash/evidence ID에 묶인다. 참조 export는034(00908330),037(00909390),050(00841f00),083(004b7c00),084(00858000),093/094(callback/MultiplyDamage constructor),101–104/106(combat dispatch·predicate·selected leaf),107/108(별도 defense consumer),109/112(Adagio context 및 실제 CALL)이다. 앞 단계에서 확인한 사실을 이번 단계의 새 발견으로 세지 않는다. 새 effect-closure 역호출자 export는 별도 receipt로 추가한다.

## 새 역호출자 결과와 Reim 등록점 보정

fresh017의 `00860cb0` incoming inventory에서 함수 밖의 확인된 참조는 vtable DATA `0127db78`이다. fresh018의 `00947cb0`은 vtable DATA `0127b9e8`; fresh019의 `0095fa10`은 caller `00947cb0`의 CALL site `00947cc7`이다. 내부 분기 참조는 외부 caller로 세지 않았다. fresh020의 `008423f0` xref는 factory 주소사용처 `008e5bd0`이다. 이것은 같은 실행 경로의 설정→vtable→predicate 연결을 보강하며, direct-call inventory에 provider가 없다는 이유로 모든 간접 실행이 없다고 증명하지 않는다.

fresh021은 `00847620`이 Ghidra function-manager의 어떤 procedure에도 포함되지 않는다고 보고했다. 그러나 fresh022가 반환한 정확한 시작점은 near jump이며, relative target을 stdlib signed rel32로 계산하면 **`00847620→00841c30`**이다. 따라서 `not_in_procedure`를 Reim 공격 후 callback의 부재나 빈 구현으로 승격할 수 없다. 등록점과 실제 body candidate를 분리했고, 부모의 단일 세션이 fresh047/054로 target `00841c30`의 본문/assembly를 제공했다(아래). 이 384-byte snapshot 전체를 하나의 함수라고 간주하거나 padding 뒤의 이웃 코드를 Reim callback에 합치지 않는다.

fresh032의 temp-resource type global `020e9cd4` xref inventory는 `0041c295`, `008577df`, `00858027`, `00932b86`, `00955ee5`이다. 원시 type-global 참조 목록이므로 이 다섯 주소를 모두 생성자 또는 실제 damage consumer라고 부르지 않는다. 기존 `00858027` producer와 `00932b70` lookup 경로 외의 owner/type 등록을 부모가 별도로 연결한다.

새 complete-envelope receipts:

| Export | SHA-256 | Evidence ID |
|---|---|---|
| `017-procedure_references-0x00860cb0.json` | `8c6659c6e1d5f69f71a9a020ddf78395e276525361f7e0830c48d382e947fa33` | `ev_c224d67afced73174f3bef4ce6dde3059b606bd8e413696aed58f983bebc2d61` |
| `018-procedure_references-0x00947cb0.json` | `4986f94501d3ce69b4dd5c39780309794852e08c3cf80f1510279be9b031bdf8` | `ev_90d0f1b5de8c0c59f29cdcf71f6700e1460d9551142d86517d15f3061a70d37b` |
| `019-procedure_references-0x0095fa10.json` | `774dbb682d7bbcb0576face0a47df92be1d8fe0c5d960ec5885d82072c3a76d2` | `ev_b5050b4b72a00421745187e132ea231485103c23a574ccd45bbf243ceaf38804` |
| `020-xrefs-0x008423f0.json` | `101be36826940f38ce6e9a7a0306cadbcbe758d2cf3a17059d9384aea02c27ed` | `ev_84dd2ad60b66b17ca21a77d14ac3d1de7c2392856237937b3d7505d959e64ff5` |
| `021-resolve_containing_procedure-0x00847620.json` | `a6fcda1ab885abedc341ad3ce79a5e5b02885fcbb2a7f6af0bcc4a57bc64deb2` | `ev_c3805fb6d07551b960a6c7a0a1a741ad14e0c8c1c9d324c4398e4b938152f1c6` |
| `022-read_bytes-0x00847620.json` | `f7e11cbfb0c27df7de290c6e16c35edd6838146e725a516a074bb65ba42d8ada` | `ev_0c4ee5efd7752a365e2508fd266cb6a42cd4bdb362c66f08b7cf60181b3432dc` |
| `032-xrefs-0x020e9cd4.json` | `c7789ab7647e3ec39d9f3f288a5bdd5757685189869e6382b99dc725847b4faa` | `ev_236fb7b79ebb489dc2a5e33a5feb4a2ffcbb1c0e1bca2153995ea8f546bd61b5` |

## Reim 공격 후 provider의 실제 resource5 producer

fresh047/054는 등록 thunk `00847620→00841c30` 뒤에 실제 구현이 있음을 확인했다. 이전의 function-manager `not_in_procedure`는 이 구현을 찾는 데 필요한 경계 보정이었고 부재 판정이 아니었다.

`00841c30`은 mode `0209e204==0`이면 반환한다. context의 `__PARENT__` buff에서 owner actor를 찾고 `__COMBAT_PARAMS__`의 source ID `+0c`가 owner ID와 같아야 하며, target ID `+14`가 owner ID면 제외하고 kind `+4==3`도 제외한다. 이 본문이 context+44를 읽는다는 것은 확인되지만 그 값을 raw damage 또는 최종 HP damage로 이름 붙이지 않는다.

유효한 정의·context와 보통의 유한값 조건에서 후보 amount는 `context.float[+44] * property[index9 또는10]`이며 최소1로 올린다. property9/10 선택은 **context+18이 가리키는 actor의+1e0 bit0**를 검사한다. 이 pointer를 target pointer라고 바꾸거나 '영웅 대상일 때'라고 추정하지 않는다. amount가 양수인 경로는 `lastGainedBarrier` clock을 기록한 뒤, 해당 actor의 buff manager에서 active hash `020db4b0` 또는 `Buff_Turret_Invulnerable`을 발견하면 반환한다. 따라서 뒤의 grant veto가 발생해도 clock 갱신이 없었다고 가정하면 틀린다.

이어 parent buff instance ID `+220`으로 `00932b70`을 호출한다. resource component가 없으면 **`00858000(owner,owner,5,amount,buffInstance)`**를 호출한다(`00841e0b`). 기존 component가 있으면 actor의 effective max-health를 소비자 bounds로 제한하고 property8을 곱한 cap을 구한다. `currentAmount + candidate >= cap`이면 증가량을 `cap-currentAmount`로 바꾸며, 양수일 때만 `00858230(owner,owner,component,increment)`를 호출한다(`00841ebc`). 새 component branch에 동일 cap 검사가 보인다고 일반화하지 않는다.

fresh051 `00858230`은 delta를 `max(requestedDelta,-currentAmount)`로 제한하고 action을 `0092e950`으로 queue에 복제한 뒤 component+20을 직접 증가시킨다. 양수 실제 delta만 `0086f4f0` event6 알림을 낸다. 반환 후 Reim callback은 component+20을 `currentMaxFortifiedHealth`에 기록한다. 새 component 생성, 기존 component 갱신, queued action의 하류 수락과 전체 health 자원의 최종 합산을 구분한다.

**이 Reim 경로는 `004b7c00`을 호출하지 않는다.** 따라서 Phinn/공통 temporary-resource route의 RET0만으로 모든 fortified-health producer가 막혔다고 주장할 수 없다. Reim에는 실제 mode-gated resource5 생성/갱신 경로가 있다. 동시에 context+44를 생성한 단계와 armor/penetration/Grumpjaw factor 순서는 이 callback에서 확인되지 않는다. Reim 자원 증가량을 final damage의 역산값으로 사용하면 최소1, definition cap, buff veto, clock side effect와 기존 component 상태 때문에 잘못된 결론이 날 수 있다.

추가 complete-envelope receipts:

| Export | SHA-256 | Evidence ID |
|---|---|---|
| `047-procedure_pseudo_code-0x00841c30.json` | `b1b7050a8599727cbc5bd0d5e8ab78c1c39ef87bd1007d00798f5833d751b5a3` | `ev_1ac1245f54952d0d52d27942762dfda4c27187b58b36d8fa7e86749560168096` |
| `051-procedure_pseudo_code-0x00858230.json` | `b1a0e1f977eba1549d19a592911dd059a027ca480b6d4ea87dc4ee8ac43b1613` | `ev_052109df1853670e333eb83fe29ca77ac7021bf7b41d952009bfe00f34f1d4c1` |
| `054-procedure_assembly-0x00841c30.json` | `4395ffcc1682d28d1f18f0bbca0175f5c45bc477de8ab10078f7ac4141e02679` | `ev_d0670df55b8c19a10d910a16b0cb6cae39fd8fe87ec9dc7931466045bb45949e` |
