# 능력치 중복·상한·삭제 아이템 후속 연구

기준 커밋 `7753523b93584b3a4fc64eb92e0c10c984800f39`, 브랜치 `research/sequential-rea-20261016`. 로컬 Windows에서 기존 REA6.4.0/Ghidra12.1.4 headless 한 세션으로 직렬 분석했다. 원본 EXE·리플레이·전체 localization과 raw exports는 연구 커밋에 넣지 않았다. 게임 실행·서버 요청·바이너리 수정·설치·잠금 우회·공개 push/merge는 하지 않았다.

## 1. 방어·저항 관통과 중복

[06_PENETRATION.md](06_PENETRATION.md): 이름/속성ID, ordinary 장착 stat ADD, named 관통의 단계 차액을 구분했다. shared cap-one marker가 각 이름당 하나씩 적용되는 조건에서 Bonesaw≈.2, Tension≈.3, 둘을 함께 써도≈.3이며 BrokenMyth1~6의 관통 구성은≈.45로 유지된다. ordinary 수정력 선언은50~300으로 늘어난다. 이것은 **구성 산술**이며 실제 HP 피해 검증이 아니다. target Bonesaw attr7/layer2 파쇄와 attacker attr9/11을 분리했다.

현재 native에서 고정 관통 단위, 관통이 방어를 줄이는지 피해 일부를 우회하는지, 최종 합성 순서·음수 방어·실제 상한을 닫지 못했다. 기존 HUD reciprocal 추정을 피해 계산기로 사용하지 않았다. 따라서 검증되지 않은 피해 효율/승률 곡선은 만들지 않았다.

## 2. 바다뱀의 가면·맹독 단검

[01_NAMES_AND_ITEMS.json](01_NAMES_AND_ITEMS.json), [02_LIFESTEAL.md](02_LIFESTEAL.md): 정확한 현지화와 리소스를 먼저 연결했다. 공통 콜백은 active High→Mid→Low 표식을 순서대로 골라 한 값(.15/.10/.05)을 combat+28에 더한다. raw 수치의 일반 MAX 알고리즘이나 모든 복사본의 합산이 아니다. 가면의 별도 충전 효과는 combat+4c 및 stack 조정 큐로 이어지며, cap1200/선언400~800/초기800을 혼동하지 않는다. 최종 accumulator→실제 heal 경로는 미확정이고 Book의 별도 heal context 전달은 client RET stub으로 닫혔다.

## 3. 쿨다운 감소·속도·직접 시간 변경

[03_COOLDOWN.md](03_COOLDOWN.md): ordinary item 값은 layer1 ADD로 nominal duration의 stat25 입력까지 연결된다. 감소율에 `(1-r)`을 곱하는 경로와 별도 stat15 속도 나눗셈 경로를 구분했다. stat15 라벨은 attack speed이며 임의의 동일한 haste 단위로 합치지 않는다. 초기화 instruction0044e081은 감소율 상한 변수에 float32 약.35를 저장하고 하한은0이다. writable 변수이므로 불변 cap으로 부르지 않는다. 초기 상태 flags가 적용을 결정하며 일반 사용 아이템은 own CDR을 대체로 사용하지 않는다. 궁극기는 slot2라는 이유만으로 공통 적용을 확정하지 않았다. 동일/상이 장비 조합과 float32 반올림 예제를 보고서에 남겼다.

## 4. 사슬니

[04_HERO_DEFENSE.md](04_HERO_DEFENSE.md): 정확히 Grumpjaw로 매칭했다. armor base/growth30/5, shielding20/3.637을 native level 식에 연결했고 레벨1/6/12 및 조건부 Bonesaw0/5 표를 제공한다. passive 선언은 incoming reduction7%, cap5이며 provider `1−.07*n`을 별도 구성한다. 방어 stat 증가가 아니다. 그러나 selected MultiplyDamage dispatch는 stub이므로 이 provider를 실제35% HP 피해 감소로 승격하지 않았다. 과거 tooltip/패치 값으로 현재 구현을 보충하지 않는다.

## 5. 충격파 주먹·메아리와 축전판

[05_CAPACITOR_AND_RETIRED.md](05_CAPACITOR_AND_RETIRED.md): 충격파 주먹은 Nullwave Gauntlet로 이름→리소스→등록 잔재가 확인되지만 실제 차단 소비자·구매/사용 가능성은 미확정이다. 메아리는 현재 manifest/localization/특정 EXE token의 연결을 찾지 못했으며 다른 Echo 이름을 대입하지 않았다.

축전판 A증폭은 outgoing barrier34/heal36 설정, B이속 발동은 Heal callback/선택/Lockout/SpeedBoost graph로 분리했다. B의 predicate는 source 소유 관계를 확인하고 자기 target을 제외한다. Phinn W resource5와 Rook selector4, Reim W 직접 damage/root 및 별도 perk를 구분한 지원/제외/미확정 표가 있다. resource4/5 공통 helper는 이 EXE에서0을 반환하므로 실서버 증폭 지원/비지원으로 단정할 수 없다.

## 검증·재현·다음 관측

[VALIDATION.md](VALIDATION.md), [REA_RECEIPT.json](REA_RECEIPT.json), [PE_CHECK.json](PE_CHECK.json)을 참조한다. 연구 코드/테스트/문서만 추가했다. 관련36 tests PASS, selected PE instruction/registry/stub 검사 PASS. native envelope112개 중 성공110(open1포함), 실패2, 세션 close 성공이다. 실패 함수 요청을 코드 부재로 해석하지 않았고 Nullwave의 containing-procedure 미해결과 code bytes 존재를 구분했다.

실제 replay 교차 대조0, 실제 화면 검증0, 독립 holdout0이다. H5810은 개발 표본이다. 다음 검증은 동일 build의 source/target/generation·item/buff instance·stack·각 stat layer·accepted damage/heal/resource/cooldown event를 동시 관찰해야 한다. 장비 슬롯·지출·raw damage와 추가 proc를 분리하고, 한 변수씩 바꿔야 한다. 원본 자료가 없거나 서버 stub이면 공식·생존율·캐릭터 전체 power curve를 추정으로 채우지 않는다.
