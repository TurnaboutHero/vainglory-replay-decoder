# 한국어 아이템 이름과 선택 resource 검증

설치된 원본 한국어·영어 localization의 동일 key를 선택 Item CFF의 `root+0x08` 포인터와 연결했다. 아래 이름 대응은 과거 가격·조합 추정이 아니라 현재 읽은 asset의 직접 근거다. 실제 실행 중인 client 또는 recording의 버전 일치는 검증하지 않았다.

| 한국어 원문 | 영어 원문 | definition index / symbol | 역할 구분 |
| --- | --- | --- | --- |
| 뼈톱 | Bonesaw | 482 / `*Item_Bonesaw*` | 지속 효과 경로 |
| 용의 눈 | Dragon's Eye | 523 / `*Item_DragonsEye*` | 지속 효과 경로 |
| 거대괴수 갑주 | Slumbering Husk | 525 / `*Item_SlumberingHusk*` | 지속 효과 경로 |
| 천상의 장막 | Celestial Shroud | 539 / `*Item_SeraphicShell*` | 지속 효과 경로 |
| 생명의 샘 | Lifespring | 504 / `*Item_Lifespring*` | 지속 효과 경로 |
| 수호령 | Rook's Decree | 531 / `*Item_RooksDecree*` | 지속 효과 경로 |
| 축전판 | Capacitor Plate | 534 / `*Item_CapacitorPlate*` | 지속 효과 경로 |
| 척력장 | Pulseweave | 533 / `*Item_Pulseweave*` | 지속 효과 경로 · 척령장의 미확정 후보 |
| 재생의 분수 | Fountain of Renewal | 487 / `*Item_FountainOfRenewal*` | 사용 능력 경로 |
| 도가니 | Crucible | 488 / `*Item_Crucible*` | 사용 능력 경로 |
| 전쟁 걸음 | War Treads | 497 / `*Item_WarTreads*` | 사용 능력 경로 |
| 수호자의 계약서 | Protector Contract | 535 / `*Item_ProtectorContract*` | 지속 효과 경로 · 비교용, 요청된 수호령과 다름 |

**척령장**은 원본 한국어 이름과 정확히 일치하지 않았다. `STORE_ITEM_PULSEWEAVE_NAME`은 **척력장**이다. 두 표기를 자동 치환하거나 동일 요청으로 확정하지 않았다. “용의눈”, “생명의샘” 같은 입력의 공백 없는 형태와 위 localization의 공백 포함 원문도 구분해서 표시했다.

**생명의 샘**은 `STORE_ITEM_LIFEWELL_NAME` / `Item_Lifespring`, **재생의 분수**는 `STORE_ITEM_FOUNTAIN_NAME` / `Item_FountainOfRenewal`이다. **수호령**은 `Item_RooksDecree`이며 `Item_ProtectorContract`의 원문은 **수호자의 계약서**다. **천상의 장막**은 내부 symbol이 `Item_SeraphicShell`이지만 영어 표시는 `Celestial Shroud`다. 영어 내부 symbol을 그대로 번역하지 않았다.

## 재현과 출처

실행 파일에서 확인한 `build://Localization/` 및 `english.strings`, `localization_ko.strings` 이름을 단서로 상대 resource 이름을 찾았다. `Localization/english.strings`와 `Localization/localization_ko.strings`의 ASCII MD5 대문자값이 실제 asset ID와 일치한다. 각 파일 전체 SHA-256을 검증한 뒤 strict base64 디코딩과 UTF-8 디코딩을 하고 따옴표 key/value 항목을 읽었다. 두 언어 모두 중복 key 없이 7,322개다. 요청 항목의 `_NAME` key만 공개 JSON에 포함하며 전체 번역 파일은 복사하지 않았다.

| 원본 | Resource ID | SHA-256 |
| --- | --- | --- |
| Localization/english.strings | `7ED4F1146624D2D991A07272993B26C4` | `209df4c745201dec58bd5ef2497f1835298b21cbc8f23bd1bb1669589462d8d4` |
| Localization/localization_ko.strings | `AE9CB5A29032FAFA098A4BBE22C79B84` | `610d2d6a3a543a11ffa555284ddcc3ce90af2aa1b7b54afb99a6dcf98b469a5e` |

선택 LAA 실행 파일 SHA-256은 `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`이다. Definition manifest `03A640B504C2B4D7C8CBF3A04E189223`의 SHA-256은 `7292b885378be83cb8596601bad7d0c7adfaab1e91e23f8ea65601f03136755c`이다. PE32 CFF profile은 key-table VA `01e3f978`, version 12, architecture 0이다. 기존 checked `cff_resource.load_cff`로 선택된 12개 item만 디코딩하고 symbol type `fc7583e1`, 원본 symbol, root, relocation, 각 item의 고정 SHA-256을 확인했다. Asset ID별 원본 SHA-256과 필요한 INST field offset은 [NAMES_AND_DEFINITIONS.json](NAMES_AND_DEFINITIONS.json)에 있다.

## 선언과 실제 효과의 경계

`00940230`의 기존 정적 export는 definition `+0x38==0`일 때 지속 효과 경로로 들어가고, 비어 있지 않은 `+0x11c`를 해시해 actor 소유 keyed state를 찾거나 생성함을 보여 준다. `+0x38!=0`이면 item 하위 ability를 생성하며, external reference `+0x3c`가 비어 있으면 inline definition `+0x40`을 사용한다. 따라서 단순히 byte 이름을 추정한 분류가 아니다. 이 native 근거는 기존 hash-bound export이고 이번 작업은 선택 asset field를 새로 대조한 것이다.

선택 item의 external reference는 모두 빈 문자열이다. 재생의 분수·도가니·전쟁 걸음은 `+0x38=1`이고 `+0x44`에 각각 embedded ability 이름이 있다. 나머지 9개는 `+0x38=0`이며, 그 중 `+0x11c`는 거대괴수 갑주 `SlumberingHusk`, 천상의 장막 `SeraphicShell`, 수호령 `RooksDecree`, 척력장 `Pulseweave`, 비교용 수호자의 계약서 `ProtectorContract`에서 비어 있지 않다. 빈 이름이 지속 효과 또는 timer 부재를 뜻하지 않는다.

선택 item의 property pointer list `+0x130`과 각 property `+4` float32를 label·값·bits·offset으로 보존했다. 사용 능력의 별도 property list는 inline ability `+0x8c`, 즉 item root `+0xcc`다. 예를 들어 생명의 샘은 `TIME_OUT_OF_COMBAT=5`, `PCT_MISSING_HEALTH_HEAL≈0.015`를 선언하며, 원본 설명도 적 영웅과 전투가 없는 시간 이후 잃은 체력 비율 회복을 기술한다. 이는 요청한 가설을 **asset 선언 수준**에서 뒷받침하지만 실제 tick 주기·전투 감지·회복 적용은 native 실행 증거가 필요하다.

뼈톱·용의 눈의 stack, 거대괴수 갑주의 threshold/window/lockout, 천상의 장막의 cooldown/block duration, 수호령의 ability→attack barrier, 축전판의 heal/barrier amplification 및 대상별 lockout을 조건부 선언으로 구분했다. 재생의 분수에는 생명의 샘 지속 효과 참조도 있어 사용 능력 분류가 모든 효과를 설명하지는 않는다. 고정 능력치 수치의 native attribute ID 해석은 이번 검증 범위 밖이며, 지속 효과 item이라고 고정 능력치가 없다고 주장하지 않는다.

## Buff cap과 재사용 정책

Pinned KindredBuffs resource `551BCB541D80053BACD0A897B7993A77`, SHA-256 `e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79`의 1,381개 definition 중 선택한 26개를 읽었다. Cap은 definition `+0x24` u16, 재사용 정책은 `+0x28` u32이다. BonesawDebuff index265의 cap은 5, DragonsEye_CrystalBonus index337의 cap은 15, 나머지 선택 24개는 1이다. **선택 26개 모두 재사용 정책 0**이다.

기존 `00863050`의 검토된 경로에서 policy2는 일반 재사용을 건너뛰고, policy1은 동일 bestower 조건을 추가하며, 그 외는 active buff의 definition hash를 기준으로 재사용한다. Item instance는 해당 predicate에 없다. 따라서 같은 item을 여러 개 소유했다고 각자 독립 stack을 만든다고 결론낼 수 없다. Cap·정책은 선언과 선택된 재사용 경로만 설명하며 실제 적용 여부·모든 source lifetime·최종 유효 능력치·서버 판정은 확정하지 않는다.

이 작업은 assets 읽기와 private evidence 및 위 두 문서 작성만 수행했다. 설치·게임 실행·Ghidra·네트워크·production 변경은 없다.
