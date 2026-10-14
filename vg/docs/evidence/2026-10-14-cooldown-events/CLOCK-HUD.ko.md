# 후속 정적 검증: 타이머의 단위, pause, HUD 효과

## 이번에 확정한 것

쿨다운 타이머의 +24는 실제로 매 update에서 감소하는 잔여 시간이다. 단위는 벽시계 초에 simulation 배율을 곱한 시간이다. 다만 replay record timestamp와 이 update 시계의 대응, replay UI 배속 제어까지는 확인하지 않았다. 따라서 기록 간 경과 시간을 단순히 빼는 replay reducer는 아직 승인할 수 없다.

### 1. 타이머 tick과 pause

00954e40의 등록부는 타입 전역 0209133c에 크기 0x2c 객체를 등록하고, update slot 4에 009686d0을 연결한다.

009686d0:
- timer+28이 0일 때만 갱신
- timer+24 -= 0112a7a0()
- 결과가 0 이하일 때 timer+1c의 virtual callback +4 호출
- 0112a7a0은 전역 float 020ec6d0을 반환

0427 생성자 0081bde0, vtable 0127cae0의 +8 → 0094fc50 → 00952610:
- owner를 찾고 state+28 key로 공통 상태 객체 검색
- 유효 타이머가 있는 경로에서 timer+28 = action+18 byte
- 즉 0427의 per-cooldown pause 상태와 tick 억제 byte가 직접 연결된다
- 타이머가 없을 때 pause를 저장해 나중에 적용한다는 증거는 없다

근거: pass8/009686d0.txt, pass10/00954e40.txt, pass9/0112a7a0.txt, pass10/vtable_0127cae0.txt, pass11/0094fc50.txt, pass14/0081bde0.txt.
0094fc50 출력은 tail jump 대상이 합쳐진 결과다. C에 나타나는 null RAM 표현은 불완전한 decompilation이며 정상 동작 의미로 채택하지 않는다. 실제 유효 timer 경로의 명령어 쓰기를 근거로 한다.

### 2. 초 단위와 simulation 배율

004c6990은 동일 clock 객체(this+20)에 다음 작업을 순서대로 한다.

1. 0093ba70: 전역 double 01a761b0 읽기
2. 0112b130: 해당 값을 0 이상으로 제한해 clock+20 배율 저장
3. 0112b970: QueryPerformanceCounter, QueryPerformanceFrequency를 사용해 초 단위 시각 및 delta 계산
4. raw delta를 clock+18에 저장
5. min(raw_delta_seconds, 2.0) * scale을 clock+10에 저장
6. 0112a7d0으로 scaled delta, 0112a6e0으로 raw delta를 각각 읽기
7. 0112b9e0(raw_delta, scaled_delta) 호출

0112b9e0은 global guard 020ec6dc가 0일 때:
- 020ec6d0 = scaled_delta
- 020ec6d4 = raw_delta
- update 단계 2/3/4/5 등을 순서대로 수행

따라서 타이머는 QPC 초 단위 delta의 상한 2초 및 simulation 배율 적용 결과를 뺀다. clock+10은 double이지만 update에 넘길 때 float로 변환된다.

주의: 0093ba70 C 출력은 float로 잘못 추정될 수 있다. 실제 명령어는 FLD double ptr [01a761b0]이다. 동일하게 0112b970의 정수→double helper 반환형 추정은 불완전하며 DIVSD / SUBSD / MINSD / MULSD 명령을 근거로 한다.

00950710 및 0095f470은 01a761b0에 0 이상으로 제한한 값을 저장한다. 0094fc60도 guard 아래에서 0 또는 상수를 저장한다. 이는 simulation pause/scale 경로다. replay UI가 어느 setter를 언제 호출하는지, 서버/리플레이 동기화 이벤트와 업데이트의 정확한 순서는 아직 미확인이다.

근거: pass11/004c6990.txt, pass10/0112b970.txt, pass11/0112b9e0.txt, pass12/0112a7d0.txt, pass12/0112a6e0.txt, pass12/0112b130.txt, pass12/0093ba70.txt, pass13/*.txt, clock-constants.json.

### 3. 0086bbf0은 시계가 아니라 길이 계산

- state+38 override가 0 이상이면 사용
- 아니면 (state+30 + state+2c) * state+34
- state+48 bit 1이 설정되면 actor attribute를 조합·제한한 값의 (1 - value)를 곱함
- bit 2가 설정되면 별도 actor attribute 조합값을 최소 1 이상으로 제한하고 그 값으로 나눔

원래 attribute의 이름, 모든 상한과 구성 의미는 이번 범위에서 확정하지 않는다. 이 함수를 timestamp 또는 clock source로 사용하는 것은 틀리다.
근거: pass6/0086bbf0.txt.

### 4. HUD 효과까지 연결

등록부 00551b00에서 확인한 callback의 후속 연결:

- onPlayAbility → 0054d510 → 005b9c30 → 005ada00 → 세 소비자에 005a48d0 호출
  - consumer+16b0과 전달 identity가 같으면 Effect_HUD_AbilityButton_Activated 사용
- onCooldownEnded → 0054d530 → 005b9920 → 005ad700 → 세 소비자에 005a4070 호출
  - 005a6b40의 identity/type guard 통과 후 009383d0에서 잔여값 읽음
  - Effect_HUD_AbilityButton_Ready 및 조건부 Effect_HUD_AbilityButton_CDReduce 사용
- onCooldownModified → 0054d550 → double delta를 float로 변환 → 005b9930 → 005ad730 → 세 소비자에 005a40e0 호출
  - delta < 0, identity/type guard 통과, consumer flag 조건 통과 시 Effect_HUD_AbilityButton_CDReduce 사용

005a6b40은 전달 state+28 key와 00936950(consumer+16b0)의 반환 key를 비교한다. 따라서 이벤트명만 같은 것이 아니라 선택된 능력과 state key를 맞추는 guard가 있다.

009383d0은 state+42(충전)가 0일 때만 0093c860의 timer+24 잔여값을 반환하며, 충전이 있으면 0을 반환한다. 이는 타이머가 존재해도 '사용 가능' 표시가 달라질 수 있음을 보여 준다.

근거: pass6/0054d5*.txt, pass7/*.txt, pass8/005a4070.txt, pass8/005a48d0.txt, pass8/005ad730.txt, pass9/005a40e0.txt, pass9/005a6b40.txt, pass9/009383d0.txt, pass10/0093c860.txt, clock-raw-refs.json의 원본 문자열.

확정 범위는 능력 버튼의 named effect 경로다. 숫자 텍스트 반올림, 원형 overlay 비율, 실제 픽셀, 세 소비자가 정확히 어떤 슬롯인지까지는 미확인이다. 이 결과를 'HUD 전체 완성'이라고 부르면 안 된다.

## 구현에 주는 경계

- 타이머 상태 값의 단위는 simulation-scaled seconds로 기술할 수 있음
- raw replay timestamp를 동일 clock으로 자동 간주하지 말 것
- pause 이벤트와 충전 수를 무시한 cooldown remaining 계산 금지
- 충전이 양수일 때 타이머가 계속 돌아도 HUD 가용성 getter는 0을 반환할 수 있음
- 기록 기반 동기화값의 정확한 시간/순서와 UI 배속 경로를 검증하기 전에는 이벤트 관측값과 출처를 보존하고 추정 잔여 초를 확정값으로 노출하지 말 것

게임 실행 없이 위 최소 연결을 확인한 시점에 중단했다. 저장소 코드는 변경하지 않았다.

추가 확인: 기존 atlas의 0476 ActionSetSimulationSpeed 생성자 0081c350은 vtable 0127cbcc를 저장하고, 그 +8 슬롯이 00950710이다. 따라서 0476이 위 simulation 배율 전역을 쓰는 직접 경로도 확인했다. 근거 pass14/0081c350.txt, pass14/vtable_0127cbcc.txt 및 pass13/00950710.txt. 이것만으로 replay UI 재생속도 조절과 동일 의미라고 단정하지 않는다.
