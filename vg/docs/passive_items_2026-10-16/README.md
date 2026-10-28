# 장착 효과·버프·사용 아이템 후속 정적 연구

기준 커밋 `98629429c5dfea78e904fe4c9df9c3bf613aadff` 이후 연구다. 같은 `research/sequential-rea-20261016` worktree에서 수행했으며 production 기능은 수정하지 않았다. 원본 게임 EXE·리플레이·전체 localization·REA raw exports는 커밋하지 않는다. 잠긴 화면을 우회하거나 보안 설정을 바꾸지 않고 Windows의 기존 REA 6.4.0 + Ghidra 12.1.4 headless 한 세션을 직렬 사용했다.

## 1. 이름과 전체 후보 목록

[KOREAN_NAME_MAPPING.md](KOREAN_NAME_MAPPING.md), [NAMES_AND_DEFINITIONS.json](NAMES_AND_DEFINITIONS.json)은 실제 한국어/영어 localization key와 hash-pinned item definition을 연결한다. 생명의 샘504와 재생의 분수487은 별개다. 수호령531은 RooksDecree이며 ProtectorContract535는 수호자의 계약서다. 천상의 장막539은 SeraphicShell이다. 요청의 “척령장”은 exact match가 없고 로컬 “척력장”533/Pulseweave를 후보로 분리했다.

[ITEM_CATALOG.json](ITEM_CATALOG.json)은 설치 자료의 93 item 선언 후보 목록이다. 고정 장착 능력치, 조건부 proc, buff/stack, timer, duplicate, 판매 정리는 서로 다른 계층이다. 현재 utility는 active capability, passive cooldown key, buff declaration reference 및 property 선언만 추출하며 고정 stat 전체를 의미 해독하거나 실제 효과 목록을 완성한 것은 아니다. active item에도 Lifespring/Travel 같은 passive declaration이 있을 수 있다. quantity/unique 선언은 buff stack과 다르다.

## 2. 새로 좁힌 native 연결

1. [소유·스택](01_OWNERSHIP_AND_STACKS.md): definition+30 → item별 buff-ID ledger → 조건부 공유 보존/cancel/decrement. policy0와 cap1인 버프를 복사본마다 독립 상태로 가정할 수 없다. 큐 생성 순서 때문에 항상 같은 ledger ID라는 일반화도 하지 않는다. 기존 Bonesaw/Dragon’s Eye trigger·감쇠 연구를 재사용했고 사망 reset은 미확정이다.
2. [자기 회복·방어](02_REGEN_AND_DEFENSE.md): 생명의 샘은 strict 지연 및 최소량 조건 뒤 self resource0 ADD를 큐잉하며 실제 ADD에는 alive guard가 있다. Husk는 정확한 sliding window 대신 accumulator 감쇠 경로를 갖고 threshold 초과분의 damage 변경·fortified buff enqueue·cooldown 직접 적용이 구분된다. Shell은 BlockBuffs 및 cooldown/damage behavior graph까지 닫혔으나 mask/enum과 실제 modifier algebra는 열려 있다.
3. [조건부 패시브](03_CONDITIONAL_PASSIVES.md): 축전판·척력장 후보·수호령의 callback/child buff graph를 정리한다. 전체 효과의 실제 실행으로 승격하지 않는다.
4. [사용 아이템](04_ACTIVE_ITEMS.md): 분수·도가니·전쟁 걸음의 factory → selection → ApplyBuff producer를 나눴다. SelectInRadius의 후보 filter, mode gate, ApplyBuffToMyself의 빈 local dispatch가 새 경계다. 도가니가 구성하는 ReflexBlock/BlockDebuffs 포인터는 확인했지만 정화·면역을 이름만으로 확정하지 않는다.

## 3. 배제한 해석과 관측해야 할 정보

- 소유 수량 = 독립 proc/stack/timer 수, 판매 한 번 = 모든 공유 효과 삭제라는 해석을 배제했다.
- Husk accumulator = 정확한 1초 event window, trigger hit 전체가 항상 반감된다는 해석을 배제했다.
- 분수 radius selector = 모든 선택 actor의 실제 heal 수신이라는 결론은 근거 부족이다.
- Shell property1 = 자동 100% magic immunity, BlockDebuffs 이름 = 기존 debuff 정화라는 결론은 보류했다.
- cooldown 선언값 = accepted activation 시 실제 남은 시간, request target = 수혜자 집합이라는 해석을 배제했다.

구현 전 최소 관측은 actor generation, item instance/definition, buff instance/source/target/state/current/cap, accepted resource/cooldown event, 시간 원천이다. 서버 모드 producer와 클라이언트 receive/apply는 별도 연결로 보존한다. 후속 reducer 후보는 관측된 buff-ID 공유 ledger와 state2 unlink 같은 근거 기반 상태 추적이다. 현재 자료만으로 자동 proc 생성·정화·사망 reset·서버 지급 예측을 추가하지 않는다.

## 4. 검증과 재현

[VALIDATION.md](VALIDATION.md)에 명령·수·범위를 기록한다. [REA_RECEIPT.json](REA_RECEIPT.json)은 native export별 hash/evidence ID 및 실패 요청을 보존한다. [PE_CHECK.json](PE_CHECK.json)은 selected binary의 6개 dispatch edge와 빈 leaf, Shell property global을 독립 바이트 검사한다. 이전 Linux 1173 통과 receipt는 `326582d`에만 적용하며 이번 변경의 전체 검증 결과라고 부르지 않는다.

이번 replay 교차 대조·실제 화면 검증은 0건이다. H5810은 개발 표본이며 독립 holdout이 아니다. 원본 build와 설치 asset hash의 연결은 기록했지만 현재 실행/recording build 일치는 별도 검증해야 한다. 모든 수치·주소는 선택 build에 한정한다.
