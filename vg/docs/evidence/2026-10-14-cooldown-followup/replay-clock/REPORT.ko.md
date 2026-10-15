# Replay record 시계와 cooldown tick: 유한 정적 검증

## 결론

record timestamp와 cooldown은 같은 simulation-scaled delta 계열을 사용한다. 그러나 **record 간 시간차를 cooldown에서 그대로 빼는 정확한 reducer는 성립하지 않는다.** main loop에서 replay dispatch는 이전에 게시된 delta를 읽고, timer tick은 그 뒤 새로 게시된 현재 delta를 읽는다. record에는 실제 playback frame별 delta, dispatch 묶음, queue drain 경계가 없다. 따라서 정확한 remaining seconds는 여전히 보류해야 한다.

이번 결과는 정적 분석과 H5810 원본의 오프라인 framing 검사다. 게임 실행이나 새 runtime 검증은 없었다. 저장소 코드를 수정하지 않았다.

## 입력 / 범위

- 분석 EXE SHA256: d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc
- 역사적 Windows runtime 문서의 EXE SHA256: 659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642
- 앞선 입력 검증 보고서는 두 이미지 차이를 PE LAA flag로 제한했다. 여기서는 그 기존 보고서를 인용하며, 역사적 runtime을 새 관측으로 승격하지 않는다
- Ghidra 12.1.3 + JDK 21 standalone. 기존 project의 별도 사본에서 유한 함수만 분석했다. REA IPC 제한 우회 없음
- 주소는 preferred-image VA. decompiler 타입/호출규약은 추정이므로 핵심 흐름은 같은 receipt의 INSTRUCTIONS로 대조한다
- pass1/004cfec0.txt는 dispatcher 전체 복구본이 아니다. 개별 opcode receiver 연결은 앞선 atlas/전투 보고서 범위로 유지한다

## 1. Record 시각의 작성과 소비

004c6990은 0093ba70으로 배율을 읽어 0112b130에 넣고, 0112b970으로 QPC 초 delta를 계산한다. scaled delta는 min(raw seconds, 2.0) * scale이며 update 전달 전 float32로 변환된다.

recording guard 004ca300이 참이면 004c69fd에서 004ce050(current scaled delta)을 호출한다. 이 함수는 recording 객체/started guard 아래에서 float 01ef0b30에 전달 delta를 더한다. 004cb590은 이 accumulator를 009546f0의 timestamp 인자로 준다. 0451은 writer의 제외 목록에 있다. 모든 원본 game-clock assignment가 파일에 남는다고 가정할 수 없다.

004ca130은 timestamp 4 bytes를 byte-swap하고, BE32 길이와 전체 packet을 읽는다. replay object의 +0x10은 다음 record timestamp, +0x0c는 playback scheduling cursor다.

004eb4a0:
- mode +4 == 2이면 곧바로 반환
- mode +4 == 1이면 cursor = float32(cursor + 0112a7a0())
- buffered record가 없으면 reader 호출
- cursor < next timestamp이면 dispatch 전에 반환
- 그 외 004cfec0으로 packet을 넘기고 다음 record를 반복하여 읽음

004eb410/004eb420은 mode를 2로 저장/복원한다. 004eb430은 004cd3a0 결과로 cursor를 직접 바꾼다. 004cd3a0은 저장된 후보 시각 중 요청값에 가장 가까운 후보를 골라 파일을 다시 연다. 이는 cursor를 연속 증가만 하는 시계로 취급해서도 안 된다는 정적 근거다. UI 버튼과의 연결은 이번 범위 밖이다.

근거: pass1/004ca130.txt, 004eb4a0.txt, 004c6990.txt, 004ce050.txt; pass2/004cb590.txt, 004eb410.txt, 004eb420.txt, 004eb430.txt; pass5/004cd3a0.txt.

## 2. 핵심: dispatch는 새 delta 게시보다 앞선다

일반 main-loop 경로의 실제 호출 순서:

1. 004c69c0: QPC에서 이번 raw/scaled delta 계산
2. 004c69fd: 조건부 recording accumulator 증가
3. 004c6ac1: 004c0380 호출
4. 004c03a3: 004eb210 호출
5. 004eb210: global 01ef0e80의 vtable +0x1c 호출
6. replay vtable 012179b8의 +0x1c = 004eb4a0 → 기존 020ec6d0을 getter 0112a7a0으로 읽음
7. 004c6aeb: 0112b9e0(raw_delta, scaled_delta) 호출
8. 0112b9e0: stage 2 실행 후 global guard 020ec6dc가 0일 때 **020ec6d0 = 이번 scaled_delta**, 020ec6d4 = 이번 raw_delta
9. stage 3, stage 4, stage 5 등 실행. cooldown 009686d0은 stage 4에서 새 020ec6d0을 읽음

따라서 이 경로의 pump는 `직전 게시값`을 사용한다. 첫 호출/guard/다른 호출 경로까지 무조건 `정확히 직전 프레임`이라고 단정하지 않는다. guard가 게시를 막으면 오래된 값이 남을 수 있다.

004eb2d0(mode=1)은 012179b8 replay vtable 객체를 만들고 global 01ef0e80에 저장한다. 이를 통해 indirect +0x1c 연결도 확인했다.

근거: pass1/004c6990.txt; pass3/004c0380.txt; pass4/004eb210.txt, 004eb2d0.txt; pass5/vtable_012179b8.txt; prior-clock/0112b9e0.txt, 009686d0.txt, 00954e40.txt.

## 3. Queue drain과 timer update 순서

0092c240은 action vtable +0xc에 global queue 020db890을 전달한다. 예시 0428의 0092eb60, 0476의 0092f390은 action을 복제해 0092f720으로 삽입한다. 0092f720은 현재 drain 위치 +0x18이 없으면 tail에 추가하고, 있으면 그 위치 뒤에 삽입한다.

00931bd0은 queue를 순서대로 순회한다. action+0xc byte가 0이면 virtual +4 호출 후 mode global 0209e204 조건에 따라 virtual +8도 호출한다. byte가 0이 아니면 +8로 간다. 그러므로 모든 entry를 무조건 +8로 적용한다고 단정하면 안 된다. 처리 후 action들을 정리한다.

004c6380은 thunk 004c6b90 → 00931bd0을 0112b150(0..4, thunk)로 등록한다. 0112b150은 020ec834 + index*4를 쓴다. 0112b9e0이 이 callback들을 다음 경계에서 실행한다:

- stage 2 → 새 delta 게시 → callback 0 / queue drain
- stage 3 → callback 1 / queue drain
- stage 4 → callback 2 / queue drain
- stage 5 → callback 3 / queue drain → callback 4 / queue drain

cooldown tick은 stage 4다. 정상 guard/apply 조건 아래 replay에서 앞서 enqueue된 timer 수정은 stage 4 전에 drain될 수 있고, timer tick이 만든 후속 action은 뒤의 drain에서 처리될 수 있다. Record order와 timer tick을 단순히 한 줄로 교차시키는 임의 reducer로 이 순서를 대신하면 안 된다.

근거: pass2/0092c240.txt, 0112b850.txt; pass4/0092eb60.txt, 0092f390.txt; pass5/0092f720.txt; pass6/00931bd0.txt; pass7/004c6b90.txt; pass8/004c6380.txt; pass9/0112b150.txt; prior-clock/0112b9e0.txt.

## 4. 손실된 frame partition의 최소 반례

partition-counterexample.json / .py는 합성 산술 증명이며 실제 client 관측이 아니다.

### 같은 record dispatch, 다른 당해 tick

cursor=0, 직전 게시 delta=0.25, 다음 record timestamp=0.125라면 두 실행 모두 cursor=0.25에서 같은 record를 받아들인다. 그 action이 기존 unpaused timer를 1.0으로 설정한다고 하자. 현재 delta가 A=0.125이면 stage 4 후 0.875, B=0.25이면 0.75다. 둘 모두 2초 clamp 아래 유효한 delta다. record timestamp/order만으로 A와 B를 선택할 수 없다.

### 같은 정확한 delta 총합도 float32 단계는 복원하지 못함

초기 remaining=1.0에 2^-25를 네 번 빼고 매번 float32 저장하면 1.0(bits 3f800000)이다. 같은 정확한 총합인 2^-23을 한 번 빼면 0.9999998807907104(bits 3f7ffffe)다. 이 작은 dyadic delta는 반올림만 분리하는 수학적 반례이며 일반적 실제 FPS라고 주장하지 않는다.

## 5. 새 H5810 오프라인 검사

corpus-check.json, corpus_check.py:
- 파일 168개, record 663,517개, 서로 다른 timestamp 38,399개
- 같은 timestamp의 최대 record 수 686개, timestamp 역행 0개
- 0428 1,859개, 0429 109개, 046f 168개
- 0427, 0476, 0451은 모두 0개
- 마지막 record 시각 1677.9219970703125
- 마지막 046f record 시각 1670.0003662109375, 그 game-clock anchor 1651.0875244140625
- 마지막 anchor 이후 record interval 7.921630859375

동일 timestamp 그룹이 playback tick 경계라는 증거는 없다. 이 검사에서 pause/speed opcode가 없다는 사실은 runtime pause/seek/배속이 없었다는 증거도 아니다. 046f game-clock anchor는 cooldown timer 잔여값 또는 playback frame partition을 제공하지 않는다.

## 6. 기존 33초 / 2초 / 5x 연구와의 대조

기존 TERMINAL_DISPLAY_CALLS_2026-10-11.md는 005497a0의 game clock이 `float32(old_clock + published_delta * simulation_scale)`로 갱신되는 역사적 runtime을 기술한다. delta 자체가 이미 scaled라는 사실과 모순되지 않는다. game-clock getter의 별도 배율 곱을 cooldown timer에 그대로 적용하면 안 된다. 009686d0은 published delta를 한 번 뺀다.

기존 H5543 / H5519의 33초 / 2초 차이는 마지막 anchor 뒤 실제 tick들과 5x 계수로 설명되었고, 단순 record interval*5 근사와 실제 값도 달랐다. 이번 main-loop 순서/float32 분석은 그 차이가 생길 수 있는 구조를 더 좁힌 것이며, 두 역사적 runtime trace를 새로 재실행하거나 검증한 것이 아니다. 상수 33초/2초 교정, cooldown에 5를 추가 곱하기, raw game clock 차를 cooldown delta로 간주하기 모두 정당화되지 않는다.

## 정확한 잔여초를 위해 여전히 필요한 증거

동일 빌드/파일의 한 playback에서 다음을 연결한 runtime receipt가 필요하다:
- 매 update 계산된 raw/scaled delta 및 실제 020ec6d0 게시 순서
- replay cursor 전후 값, mode/seek와 실제 dispatch된 record 범위
- action identity와 apply guard, queue drain 경계
- target timer identity/generation, +24 전후 bits, +28 pause, stage 4 tick와 expiration callback
- 충전 수/state lookup의 유효성 및 조회 시점

원본 기록 당시 정확한 상태까지 주장하려면 playback trace만으로는 부족하다. 원본 tick/누락된 server clock setter 등 원본 실행 증거도 별도로 필요할 수 있다.

## 안전한 다음 패치

정확한 cooldown remaining reducer의 신규 도입은 권장하지 않는다. 허용 가능한 작은 변경은 evidence-gated diagnostic에 `playback_frame_partition_missing` 또는 동등한 사유를 추가하고, raw 관측값/record timestamp/identity provenance를 유지하며 추정 잔여초를 null로 남기는 것이다. 이 사유는 기존 전체 clock-invalid 판정을 바꾸지 않는 field-specific 설명이어야 한다. 기존 소비자 계약에 자리가 없으면 이번에는 문서와 테스트용 산술 반례만 추가하는 편이 안전하다.

이 지점에서 bounded clock-mapping 질문은 해결되었다: 단위 관계와 update 순서는 정적으로 연결됐으며, 잔여초 완성의 정확한 미확인 입력은 runtime frame partition과 적용/tick receipt다. 전체 프로그램 추가 추적은 하지 않는다.
