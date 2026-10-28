# 피해 순서 추가 조사: 사슬니 provider 전달 자체가 stub에서 소실됨

기준 commit `1e8099c463359a322b704c92388a9ee81ddb64ab`; 격리 worktree에서 원본 Windows x86 LAA EXE를 읽기 전용 분석했다. SHA-256 `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`. 게임 실행, 서버 관측 및 네트워크 송신은 없었다.

## 새 결론과 기존 설명의 정정

기존 보고서는 factory가 사슬니 damage provider `008423f0`를 "지정/설정"한다고 표현하고 나중 Combat 실행 slot의 stub에서 멈췄다. **설정하려는 값이 인자로 전달되는 것은 맞지만, 선택 클라이언트에서는 그 전달 메서드 자체가 값을 저장하지 않는다.** 그러므로 이 객체에 provider가 실제 등록되어 있다고 읽히는 표현은 정정한다.

1. `008e5bd0`은 stack local `[EBP-8]`에 provider 주소 `008423f0`, `[EBP-4]`에 tag4를 쓴다
2. `008e5bef`가 `00530ad0`으로 MultiplyDamage 객체를 받는다. constructor `00530b25–00530b32`는 객체+4를0, 객체+0을 vtable `0121b690`으로 만든다
3. factory는 객체+4를 callback behavior-list link로 사용한다. 이는 provider 저장 필드가 아니다
4. `008e5c12–008e5c1d`는 위 stack local 주소를 PUSH하고 ECX에 객체를 넣어 virtual `+14`를 호출한다
5. `0121b6a4`의 target은 `0045cd00`. 그 전체 본문은 `8b c1 c2 04 00`, 즉 `MOV EAX,ECX; RET 4`다. 인자를 읽거나 보관하거나 provider를 호출하지 않는다
6. 이후 Combat의 virtual+4가 `0045ecd0: RET 4`인 기존 경계도 그대로 남는다

따라서 **이 전달 route에는 서로 다른 두 stub 경계가 있다: provider 설정과 피해 실행.** provider `008423f0`의 독립 본문 `1-property2*count`가 존재하는 것과 그 함수를 이 객체가 실제 호출하는 것은 다르다. 서버판 구현, 다른 build, 직접 호출, 별도 interpreter와 모든 독립 consumer의 부재까지 증명하지 않는다.

## 전체 vtable과 경계

RTTI `0121b68c`는 `BuffBehavior_MultiplyDamage`; 바로 다음 `0121b6b4`는 별도 `BehaviorHelper_Heal<BuffBehaviorContext>`의 locator다. 따라서 조사한 table의9개 slot을 이웃 클래스의 함수까지 무한히 확장하지 않는다.

| slot | target | 실제 본문/역할 |
|---|---|---|
| +00 | 00532fd0 | destructor: base vtable 복구, flag에 따른 해제 |
| +04,+08,+0c,+10 | 0045ecd0 | RET4; 인자 무시 |
| +14,+18,+1c | 0045cd00 | this 반환, RET4; 인자 무시 |
| +20 | 00459660 | this 반환, RET |

이 객체의 보이는 virtual method 중 provider를 읽어 산술하는 함수는 없다. Destructor에는 외부 해제 helper 호출이 있으나 이를 damage 경로라고 해석하지 않는다. Ghidra가 `0045cd00`을 무관한 gloox export명으로 표시하는 것은 folded code의 이름 문제이며 실제 명령 바이트를 기준으로 판정했다.

## 관통 소비자 탐색: DB xref와 파일 전체 literal scan을 구분

복사한 Ghidra DB는 일부 함수만 disassemble되어 있으므로 처음 조회에서는 shielding-pierce 소비자조차 누락됐다. 원본 PE 파일 전체의 little-endian32 literal occurrences를 별도로 조사해 보완했다. 결과는 NATIVE_CHECK.json에 file offset과 mapped VA로 모두 남겼다.

- upper armor-pierce/bonus-armor-pierce/bonus-shield-pierce: 각각 초기화 immediate만 발견
- upper shielding-pierce `020e7374`: 초기화와 기존 Adagio instruction operand `00838809`
- lower shielding-pierce `01a760c4`: 초기화와 같은 Adagio의 operand `00838811`
- provider `008423f0`: factory stack-store의 operand `008e5bd3` 한 건

이 VA는 **명령 시작점이 아닌 operand 위치**다. 파일 전체 literal scan도 indexed addressing, 계산된 주소, relative call, 동적 생성 및 서버 구현을 모두 찾는 것은 아니다. 부재를 일반 관통 계산기 부재로 승격하지 않는다. 새 일반 armor/shield 관통 소비자는 발견하지 못했다.

## 최소 판별 실험: 뒤에 붙는 clamp만으로는 부족하다

아래는 실행 결과가 아니라 향후 허가된 fixture/관측을 위한 가설 판별 계획이다. 테스트 파일의 Fraction 산술은 정수/유리수 가설 검증이며 native x87/SSE 반올림 모델도 아니다.

### A. 관통 모델부터 분리

동일 build/source/target lifetime과 raw damage100, crit/proc0, 방어막/회복0을 고정하고 accepted pierce p=.3을 확인한다. item 교체로 raw damage가 바뀌면 비교를 폐기한다.

- 가설 R: defense를 (1-p)배 후 reciprocal mitigation
- 가설 B: damage p 비율은 우회, 나머지만 reciprocal mitigation
- defense0에서는 둘 다100이므로 이 한 점은 판별 실험이 아니다
- defense100에서는 R=1000/17≈58.8235, B=65로 갈린다

이는 두 **예시 가설**의 구별이지 해당 수치가 실제 server 정답이라는 주장이 아니다. 양수 defense에서 p0 baseline 및 p.3을 비교하고 실제 raw/context/accepted output을 기록한다. 추가 positive defense level로 단일점 우연 일치를 검사한다. 다른 계산이나 rounding이 발견되면 후보식부터 수정한다.

### B. 사슬니와 방어의 순서는 HP만으로 해결되지 않을 수 있음

고정 raw100, mitigation factor .5, passive factor .65의 정확한 산술에서 두 순서 모두32.5다. **그 뒤** barrier absorption, nonlethal cap, rounding 또는 임의 동일 함수 F를 붙여도 F(32.5)=F(32.5)다. 기존에 확인한 health split/nonlethal 준비가 downstream에 있다는 사실만으로 upstream 곱셈 순서가 식별되지는 않는다.

판별하려면 두 연산 사이의 값을 관측한다(이 예에서는50 대65). 또는 두 연산 **사이에** 실제 비선형 연산이 있음과 그 위치를 먼저 입증해야 한다. 예를 들어 가상의 cap60이 사이에 있으면32.5 대30이지만, 실제 code에서 그런 cap을 발견한 것은 아니다. 임의 cap을 게임 공식에 추가해서는 안 된다. 반올림도 두 곱 사이에 있다는 증거와 그 정밀도가 필요하다.

### 실행/중단 조건

필요한 기록은 matched build hash, raw input, actor ID+generation, target defense 각 layer, attacker pierce9–12, passive instance+count, mitigation/passive 직전·직후 amount, rounding/clamp 위치, 최종 accepted health action이다. 현재 제공된 클라이언트는 provider handoff부터 stub이며 서버/관측 fixture가 없으므로 이 중간값을 얻을 수 없다. 이것이 본 조사에서 피해 순서를 확정하지 못하는 구체적 blocker다. HP 표본을 더 모으는 것만으로 동일 출력 가설을 확정하지 않는다.

## 재현과 검증

원본 EXE를 소유한 환경에서:

    python -m vg.research.damage_order_native --binary /path/to/Vainglory.exe
    python -m unittest discover -s tests -p test_damage_order_native.py -v

선택 EXE에 대해 SHA 및9개 byte anchor, 양쪽 RTTI 경계를 확인했다. 8개 unittest 통과(각9개 anchor corruption subtest 포함). 테스트는 static-byte regression과 실험 식별성 검사이며 native 실행/server 통합 테스트가 아니다. 새로운 decoder/gameplay 동작은 활성화하지 않았다. receipts는 복사 DB의 fresh Ghidra12.1.3 decompilation/instructions이며 원본 게임 바이너리는 포함하지 않았다.
