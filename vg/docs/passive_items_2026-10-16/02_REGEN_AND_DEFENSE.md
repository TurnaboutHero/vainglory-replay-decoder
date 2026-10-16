# 생명의 샘·거대괴수 갑주·천상의 장막: 선택 native 경로

선택 LAA EXE SHA-256 `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`, x86 preferred VA 기준이다. 한국어 이름·resource hash·property offset은 [이름/정의 검증](KOREAN_NAME_MAPPING.md)과 [구조화 결과](NAMES_AND_DEFINITIONS.json)에 있다. 이 문서는 새 정적 export와 선택 assembly를 분석했다. 실제 게임 실행, recording build 일치, callback 호출 횟수, 최종 HP·피해 결과를 관측하지 않았다. 아래의 “수행한다”는 선택 코드 경로의 조건부 동작이다.

## 생명의 샘: 지연·최소량 조건이 있는 자기 resource ADD 경로

`Item_Lifespring` definition504의 선언은 `PCT_MISSING_HEALTH_HEAL≈0.015`, `TIME_OUT_OF_COMBAT=5`다. 재생의 분수487과 다른 item이다. `008f0100`은 buff+23c에 float32 0.5를 설정하고 `timeOfLastDamageExchange=0`을 초기화한다. interval callback은 `0083c4d0`, `onPreCalculateDamageExchange` callback은 `0083c6b0`으로 등록한다. 등록 자체에 mode gate는 없지만 interval callback 몸체는 global byte `0209e204!=0`일 때만 아래 producer 경로에 들어간다. 이 mode를 서버·practice·replay 전체와 임의로 동일시하지 않는다.

`0083c6b0`의 입력은 callback context의 parent와 combat parameters다. combat+0c가 bearer actor ID와 같고 combat+18 객체의 +1e0 bit0가 설정됐거나, combat+14가 bearer ID와 같고 combat+1c 객체의 같은 bit가 설정되면 `00548880()` 값을 `timeOfLastDamageExchange`에 저장한다. 이는 송신/수신 양쪽의 선택된 damage-exchange 조건이다. 이 bit의 전체 actor 분류나 실제 양수 피해·적대 관계까지 이 몸체만으로 일반화하지 않는다.

`0083c4d0`의 pseudocode에는 action 생성 인자가 생략됐으므로 assembly `0083c4f8..0083c68e`를 우선했다.

1. mode gate 통과 후 `now=00548880()`을 읽는다. `now > float(last + property(index1, selector1))`인 경우만 계속한다. 같은 시각의 경계는 `COMISS/JBE`로 제외된다. 원본 recording timestamp를 이 clock으로 대체하지 않는다.
2. actor stat component에서 `H=((+23c+1)*+d4 + +20)*(+188+1)`을 계산하고 globals `020e7348`/`01a76098`로 MINSS/MAXSS 제한한다. `current=component+2f0`을 읽어 `(H-current)*property(index0, selector1)*buff+23c`를 계산한다. stat 이름 해석은 기존 HP/resource 경로와 결합한 것이며 global 한계값의 모든 runtime 쓰기를 조사한 것은 아니다.
3. 계산된 float가 **1.0보다 클 때만** inline action을 만든다. vtable `0127c9b4`, action+10=bearer actor ID, +14 resource u32=0, +18=계산값, +1c mode byte=0, +1d flag=1, +1e flag=0을 설정한다 (`0083c647..0083c67b`). `0092e950`에 queue `020db890`을 전달한다. +1d flag를 SET mode나 resource ID로 읽으면 잘못이다.
4. 기존 exact-build apply `0094f210`의 mode0 경로는 `0093ead0` ADD이며 resource0일 때 현재 component+2f0가 양수여야 도달한다. 이 연결은 **살아 있는 대상에 대한 조건부 자기 HP ADD producer**를 뒷받침한다. 큐 처리·actor lookup 성공·그 이후 clamp·다른 callback을 건너뛴 최종 회복량은 확정하지 않는다.

따라서 “전투에서 벗어난 뒤 자동 재생”이라는 설명은 선언과 native producer의 두 수준에서 연결됐다. 매 0.5 벽시계 초마다 항상 회복하거나, 작은 회복량을 누적하거나, 사망자를 되살린다는 주장은 성립하지 않는다. 설정 interval과 실제 scheduler 호출 receipt는 별개다. 반증/확장 대상은 마지막 교환시각의 실제 갱신 조건, clock source, mode writer, queue apply와 observed HP다.

## 거대괴수 갑주: 누적값의 감소와 피해 callback의 threshold

`Item_SlumberingHusk` definition525는 threshold0.25, window1, fortified duration3, lockout30을 선언한다. `008f1fe0`은 buff+23c=0.2f를 설정한다. **mode `0209e204!=0`에서만** damage accumulator=0 및 fortified marker=0을 초기화하고 interval `00850f30`, before-damage `0095ae50`, before-receive-buff `00850e50`을 등록한다. 그 밖의 ready effect와 `SlumberingHusk` cooldown-name 조건 구성은 이 mode block 밖이다.

`00850f30`은 bearer의 위 `H` 조합과 threshold/index0, window/index1, buff interval을 읽는다. accumulator가 양수이면 `max(accumulator - H*threshold*interval/window,0)` 형태로 감소시킨다. 이는 정확한 최근 1초 피해의 event ring buffer가 아니라 선택된 누적값의 주기적 감쇠 경로다. 분모가 0이거나 비유한 입력일 때의 의미는 이 정상 선언으로 일반화하지 않는다.

`0095ae50`의 assembly는 다음 입력·출력을 연결한다.

- combat+14가 bearer ID와 같아야 한다. actor의 cooldown child 중 `SlumberingHusk` key를 찾는다. state가 없거나 charge+42가 비0이면 계속하고, charge0이면 resolved timer remaining이 양수일 때 반환한다 (`0095af45..0095af7b`). 선택된 remaining 비교·현재 charge가 trigger gate에 함께 쓰인다.
- fortified marker가 이미 비0이면 combat+44를 0.5배 한다. marker가 0이면 combat+44를 accumulator에 더한다. accumulator가 `H*threshold` 미만이면 반환한다.
- threshold에 도달하면 현재 combat+44에서 **threshold 초과 누적분의 절반**을 뺀다. 단순히 trigger hit 전체를 언제나 절반으로 만드는 식과 다르다 (`0095b089..0095b0b4`). marker를1로 설정하고 self/self `Buff_Item_SlumberingHuskFortifiedHealth` action을 duration index2로 구성해 virtual+0c에 queue를 전달한다.
- 이어 `SlumberingHusk` key의 cooldown-change action(vtable `0127ca18`, mode1, value property index3)을 구성한다. `0094b6c0`을 호출하고 **mode!=0에서만** 해당 action virtual+8을 직접 호출한다 (`0095b195..0095b215`). 앞의 buff enqueue와 이 direct apply를 같은 호출 방식으로 합치면 안 된다. 마지막에 accumulator를0으로 지운다.

`008f21d0`은 fortified buff에 behavior를 추가하고, 별도 helper 반환 object+8에5, +c에 bearer stat+2f0를 넣는다. 이 숫자5를 041d resource enum으로 동일시하거나 최종 fortified-health 산술로 확정하지 않는다. `00850e50`은 받은 buff-data name hash가 global `020e9c48`과 같을 때 fortified marker를0으로 만든다. 그 global은 `020a124c`에서 지연 초기화되므로 이 receipt만으로 특정 buff name이라고 명명하지 않았다.

반증 조건: damage accumulator가 정확한 sliding-window라는 주장, duplicate item별 독립 accumulator라는 주장, cooldown과 무관한 무조건 trigger는 위 조건과 맞지 않는다. 최종 피해·fortified 수치와 marker reset의 특정 buff identity에는 추가 helper/실행 근거가 필요하다.

## 천상의 장막: keyed cooldown과 조건부 damage behavior 구성

`Item_SeraphicShell` definition539의 원문 이름은 천상의 장막 / Celestial Shroud다. 선언은 `MAGIC_DAMAGE_REDUCTION=1`, `COOLDOWN=35`, `BLOCK_DURATION=0.5`이다. passive cooldown-name+11c는 `SeraphicShell`이다.

Factory `008f1630`은 다음 graph를 구성한다. 이는 callback 구성의 정적 근거이며 전투 event가 실제 발생했다는 뜻은 아니다.

| 구성 | 입력/설정 | 확인한 출력과 한계 |
| --- | --- | --- |
| `008103f0` | hash(`SeraphicShell`), byte+19=1 | constructor vtable 이름 `BuffCallback_CooldownOngoing`; ready/barrier effect와 추가 behavior를 연결. polarity의 전체 실행 구현은 이 constructor 이름만으로 확정하지 않음 |
| `0052f0e0` | 반환 behavior+18 byte=0x11 | `0081d3c0` constructor의 class는 `BuffBehavior_BlockBuffs`로 확인. 0x11의 세부 mask 의미와 실제 차단 결과는 확정하지 않음 |
| 첫 `008102e0` | mask+28 bit3, +2c=1, selector+3c=10, flags+40의 선택 low bits, predicate+18=`0084cde0` | constructor는 `BuffCallback_Combat`임을 확인. filter10을 보편적 ability-damage enum으로 단정하지 않음 |
| `0052f560` / `00813320` | `SeraphicShell` key condition | 각각 `BuffBehavior_ConditionalNew` / `BehaviorCondition_ActorHasCooldown` class 구성 |
| `005305c0` | 같은 key, callback pointer `00867d20` | `BuffBehavior_ModifyCurrentCooldown` 구성. 실행시 어떤 mode로 변경되는지는 class 이름만으로 대체하지 않음 |
| `0052ec60` | `Buff_Item_SeraphicShell_IsActive`, callback pointer `00867cf0` | named buff를 선택한 behavior 구성. 해당 helper의 전체 side effect는 미검증 |
| 두 번째 `008102e0`와 `00530ad0` | selector26, key condition, callback `00867d50` | `BuffBehavior_MultiplyDamage` class 구성. property1.0을 즉시 “100% 피해 무효”의 algebra로 바꾸지 않음 |

`0084cde0`의 low return bit는 context+18이 가리키는 object의 ushort+1e4 bit9가 clear일 때1이다. 이 field의 전체 상태 의미·source/target 역할은 따로 검증해야 한다.

`008f1910`은 IsActive factory로 finishing effect, 같은 byte0x11 behavior, combat selector26와 `MultiplyDamage` callback `00867d50`을 구성한다. 선언상 immunity·짧은 유지·35 cooldown과 양립하는 graph이지만, 이들 behavior의 실행 순서·filter enum·damage 산술·실제 차단은 별도 증거다.

REA queries `00867cf0`, `00867d20`, `00867d50`는 **No procedure exists**로 실패했다. 이는 코드 부재가 아니다. 후속 read-bytes receipt는 해당 주소들에 각각 완전한 작은 호출 sequence와 RET가 있음을 보여 준다. 세 sequence는 global `01a73e48` lookup -> `0112a790` -> `0112ab50` -> `00939570`이며 selector1과 property index2/1/0을 각각 전달한다. SHA-gated `verify_passive_pe`의 file-backed pointer 검사로 global `01a73e48` -> `0126cfa4` -> 정확한 `*Item_SeraphicShell*`도 확인했다. 144-byte receipt의 고정 opcode pattern과 세 direct relative-call target을 별도로 검산했다. 따라서 `00867cf0`은 Shell property index2 `BLOCK_DURATION`(선언0.5), `00867d20`은 index1 `COOLDOWN`(35), `00867d50`은 index0 `MAGIC_DAMAGE_REDUCTION`(1)을 selector1로 공급한다. 이것은 property getter와 behavior graph의 연결을 닫지만, 해당 값을 소비하는 behavior의 algebra나 runtime 성공을 대신 증명하지 않는다. full procedure 경계 복원이나 Ghidra annotation 변경은 하지 않았다.

## 재사용·실행 경계와 검증 가능한 반증

선택 buff300 Lifespring,314/315 Husk,341/342 Shell은 asset cap1·reuse policy0이다. 앞선 item-instance가 독립 buff state의 key라는 근거는 없으며, 같은 정의의 여러 복사본을 곧바로 독립 timer/stack으로 모델링하지 않는다. Queue 제출·callback 등록·로컬 mode 분기·서버 실행은 서로 다른 증거 수준이다.

| 주장/가설 | 현재 범위 | 확정에 필요한 반증 가능 관측 |
| --- | --- | --- |
| Lifespring이 5초 이후 자기 회복을 낸다 | 선택 mode에서 strict clock gate, 최소량>1, resource0 ADD producer | 실제 clock/bearer identity·queue apply와 전후 HP; 경계5초/작은결손/사망 상태 비교 |
| Husk가 짧은 burst를 제한한다 | accumulator 감쇠와 threshold hit의 combat+44 변경·buff enqueue | 동일 combat object의 전후 bits, marker reset name, lockout state, final damage/resource 적용 |
| Shell이 ability/debuff를 막는다 | localization 선언+조건부 behavior graph | combat selector10/26 enum과 dispatch, modifier operation, status0x11 의미, cooldown/IsActive 전이와 실제 피해·buff 수신 |

원본 native output은 저장소에 복사하지 않았다. Lifespring action의 기존 apply body `0094f210`은 이전 receiver 정적 receipt를 재사용했다. 아래 해시는 선택 raw JSON 전체를 묶고 Evidence ID는 exact-build REA receipt를 가리킨다. Failed no-procedure queries040..042는 성공 receipt로 계산하지 않는다.

## 선택 정적 receipt

| Raw JSON 이름 | SHA-256 | Evidence ID |
| --- | --- | --- |
| `009-procedure_pseudo_code-0x008f1fe0.json` | `78633b0d5b5b846e3446eaa264804e6647b56af87d186140b7fab500975f68ea` | `ev_236e4c280bf1812d9af6149e585bed63537c4e58afab213e971b405abaf3a387` |
| `010-procedure_pseudo_code-0x008f21d0.json` | `acf4c221484a89e0e2f98c0152303041b347bbfe83ae25cfe43e207495052358` | `ev_2043fd8b3fca3d4a22b6fa4615a8936aa58893890f2ad4e5d45734667a14fc8b` |
| `011-procedure_pseudo_code-0x008f0100.json` | `21060b0d54ce256a4c030e525936559363f98d52efa731c34c2f10d1e1f35d85` | `ev_b57026e3b7395291362d288de834a8a1c102b4152025c176675cc4d38b4776b1` |
| `026-procedure_pseudo_code-0x008f1630.json` | `f902346d7c81516703607c4fbd54726e51289a047eb95324e0cd9dca72da089d` | `ev_634c004d614f80753aad4880f8107141a6b35f0c71e68f5125474b9fc9f9b301` |
| `027-procedure_pseudo_code-0x008f1910.json` | `7a0c40abb69cbbd4e5c7c45ba80cd998a7aa8a84231248bf1f3e136608cc8a97` | `ev_68d7091140756372779f0316f8f606f6fdb7f6a1d2d769c6a02f501fb83fc13d` |
| `034-procedure_pseudo_code-0x00850f30.json` | `03ec37c86f28cf908e5f78028293ceb2ca327afb86272ba6964f2fe312f29630` | `ev_f2c6ff3bab4159c46686ef25296d646341ad13312e6caa8c8123f2dd4ea0db33` |
| `035-procedure_pseudo_code-0x0095ae50.json` | `1ef2451a2b3ca855369b40b748ea3f1ed66ccd57a7335fedf687ff4c3a97175a` | `ev_8c6a393ffe9559786e1d12f7dbe203deb6e578a717cff2ea85d1e262b6409d5f` |
| `036-procedure_pseudo_code-0x00850e50.json` | `bfa2d09c9a1dc3e95e7e5615752bc2353a2b4cfc8630aa1289251541ec2a520c` | `ev_763768b9e3822b3e4cf35641cb9d629f218f2890167ccbebb31ab25b0e74e322` |
| `037-procedure_pseudo_code-0x0083c4d0.json` | `0c68a8a541d0a3e0a36ac0f7d955bf248923bdb6432679cab62827fee338b752` | `ev_37c20ba34f7f4eb5fe3e556e38ea503b87e5cf1fda0996013e022d3c72c49d80` |
| `038-procedure_pseudo_code-0x0083c6b0.json` | `01207c60547bbe75761a5fb0c3624255990cb35182c63449b1c8691684752901` | `ev_20e6f9639d06c43e7650e17b7f2adc22a3cf70f34bbf099e8f60ffa5ec72d031` |
| `039-procedure_pseudo_code-0x0084cde0.json` | `5f78777c67839f9c3d17f18ef69c456626599d7709f49662f6df5bf029794537` | `ev_4b799c2a687efa6b8b7c05f8e315f6861dadf581b84ab2a4d9af6b09cdcf3e39` |
| `043-procedure_pseudo_code-0x008102e0.json` | `c7553dc4bc889fc90df86955e3bfba6e3f15e8c3a7e6c940dba7aa561a089333` | `ev_f60d0761ebaaed1f99b2c057c9b514587bfa1993d8f1a77510475f22b607328f` |
| `044-procedure_pseudo_code-0x008103f0.json` | `6caaae84823fd3ac583b068c8eaee2e1f9b1267ef08724f2634cf6ebcfa71f87` | `ev_afcf7e140a47fac45bdadf8b49d50a517ebb09ab7509a455136daaf929179c05` |
| `045-procedure_pseudo_code-0x00813320.json` | `132ea6bf30cbf61c09740850f39d621560cb29c2218a55a40be8173282eb0ff7` | `ev_e015ce7f9a786309de51b88e8850f5d604d89c6d4368893ed7836b8fbf34f958` |
| `046-procedure_pseudo_code-0x0052f560.json` | `5e89468e9d480e7bd0793ce870f68eb0e0ae3039750a4f01d980a51520ccbe1e` | `ev_ae42f2009458fab9251ffbba9550ba649ca3cd5c96dea3f3e3a82d4b07af9d9a` |
| `047-procedure_pseudo_code-0x0052f0e0.json` | `8b7b98293ef5b8e80d9d99486d4a300b218f755f52651d6e8da0ce5cfa856780` | `ev_72fb6a379d7936e0c9dc6e25b2a1179a0428f37a7d653c2e6ef09363998bf640` |
| `048-procedure_pseudo_code-0x005305c0.json` | `3ad9d4b759df4bc654c4d748cef6acd5fef0de3355ca381e3cd3ef6305eea545` | `ev_7006b05dc909baed91881ddd29c45c592e74f16aff7d84fde1ca750e4cd54943` |
| `049-procedure_pseudo_code-0x00530ad0.json` | `050d05aea280d4267b7a7bb130ac975908038202732329bf45e632d661b2d69b` | `ev_bb475a8478175bc28edd8713cdd061178529736c22522929918fd922b24d43c3` |
| `063-procedure_assembly-0x0083c4d0.json` | `ebd70da5351501c593460299665909d1b36d6922f76a38eef36e202df45597a7` | `ev_dda22e08e248bab2e3646da9bb37ed98fb571695d75b3c2f1e32bc12bca09527` |
| `064-procedure_assembly-0x0095ae50.json` | `7e76bbba5e69768fd25e24ffff78c2f6b50efeb078146337b69779056745324d` | `ev_5f7af24d7c8e418a0f937b21ffc464c2dbca6c4811f69190654c0614b93bd14f` |
| `070-read_bytes-0x00867cf0.json` | `63f55f462b0b8cee350f7f63fcb42d241db74345b9bb2e62a73e349f315f3115` | `ev_87c4d4d08c46d0ab3aec21d3b767dab14b5d25f870959ca8ebc24d797183ffd6` |
| `084-procedure_pseudo_code-0x0081d3c0.json` | `fb152b6e2c39bd1876fd1811da97ba0de59de154dc811261db9b0e45bbf2f525` | `ev_f9381a6275e1b43496a95d7d9146ff08446b00dbfeb1cf226949da6c55038c3a` |
| `prior-receiver/009-procedure_pseudo_code-0x0094f210.json` | `9962c213cb14cbe851670497b71acbbea8d78df923fd64deb6cd26c140c8141f` | `ev_b186fdf9c12df1dbb82ef048bc64106f9525d135ac2377aa662b1db2c9499dac` |

별도 재현 검산: `vg/research/verify_passive_pe.py`의 선택 EXE 검증 및 070 receipt의 세 고정 call sequence 검산 JSON SHA-256 `419e386b4681fcfff65ba858a008f9cdddb181e7ed78c945b566e0ebb0cf5a3b`. 이 검산은 REA evidence가 아닌 local static byte check이며, 원본 raw bytes·절대 경로는 공개 문서에 포함하지 않았다.
