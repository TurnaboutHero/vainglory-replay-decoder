# 클라이언트 공통 전투 상태: 첫 정적 연결 지도

후속 안내: 아래 최초 보고서의 timer 단위/pause/HUD 미확인 사항 중 일부는 CLOCK-HUD.ko.md에서 추가 검증했다. 두 문서를 함께 읽어야 한다.

## 결론

0428(쿨다운 변경), 048a(쿨다운 동기화), 0429(능력 충전 변경)는 별개 이벤트지만 실제 클라이언트에서 같은 쿨다운/충전 상태 변경 함수에 합류한다. 따라서 이벤트별로 독립 숫자 하나씩 갱신하는 구현은 충분하지 않다. 특히 쿨다운 변경 자체가 충전 수를 바꿀 수 있고, 048a는 타이머 변경 후 패킷의 충전 수를 다시 설정한다.

이 보고서는 원본 실행 파일을 실행하지 않은 정적 증거다. 게임 화면, 실시간 타이머, 서버 판정, 재생 배속은 검증하지 않았다. 저장소 코드는 변경하지 않았다.

## 입력과 방법

- main: 7d1e0e982d24bf48a11de6debbaeab7b7db090ba
- 기존 활성화 근거: origin/codex/rea-item-activation 33611314a29d2ad57a4c56a2f6da569b22ec9641
- 별도 actor/skin 분리 근거: origin/fix/h5672-spawn-skin-identity-20261014 45e42a41acf16974dd42588c3a70b09c4cf59dd6
- 분석 EXE SHA256: d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc
- 입력 담당자가 검증한 기준 빌드와의 차이: PE LAA 플래그만 다름. 실제 입력은 수정하지 않았다
- Ghidra 12.1.3, JDK 21, x86 LE 32 Windows loader, standalone analyzeHeadless
- REA IPC 접근 제한은 우회하지 않았다. 전체 자동분석 대신 알려진 시작점에서 유한한 함수 집합만 disassemble/decompile했다
- 모든 주소는 이 이미지의 정적 VA. decompiler 타입/호출규약 추정은 불완전하므로 핵심 필드와 호출은 같은 파일의 실제 명령어로 대조했다
- 특히 pass2/0094f500은 tail jump가 00945cc0까지 함수 몸체에 흡수된 초기 결과다. pass3에서 경계를 나눴으며 실제 0094f500 명령은 client/server guard 후 00945cc0 tail jump다. C 출력의 재인라인을 독립 실행 증거로 세지 않는다

## 확인된 정적 간선

### 0428: 쿨다운 변경

기존 dispatcher 004cfec0의 0428 분기 → 생성자 0081bb60 → vtable 0127ca18의 +8 슬롯 0094f500 → 00945cc0

- 생성자: action+10 owner, +14 lookup key, +18 float bits, +1c mode byte 저장
- 0094f500: DAT_0209e204가 0일 때만 00945cc0으로 분기
- 00945cc0: 00857970으로 owner 조회 후, owner의 특정 타입 객체들을 0112a700으로 열거한다. 객체+28과 action+14를 비교한다
- mode != 0: 0095cf10(state, float) 직접 호출
- mode == 0: 00945d70(state, float) 호출. 유효한 타이머가 있으면 현재 timer+24를 읽고 입력 float를 더해 0095cf10 호출; 없으면 0을 기준으로 더한다

따라서 이 모드의 차이는 정적 범위에서 '직접 값 적용 / 현재 값에 더하기'다. 수치 단위가 초인지, 전체 replay 시간과 어떻게 연동되는지는 아직 미확인이다.

근거: pass1/0081bb60.txt, pass1/vtable_0127ca18.txt, pass3/0094f500.txt, pass3/00945cc0.txt, pass3/00945d70.txt

### 048a: 동일 상태 검색 또는 생성 후 동기화

기존 dispatcher 048a 분기 → 생성자 0052ad40 → vtable 0121aaf4의 +8 슬롯 0052aea0

- action+10으로 owner 조회
- 008579e0(owner, &action+14): 동일 타입 객체들의 +28 키를 비교하는 검색
- 없으면 해당 타입 생성 01129d20 → 009401f0으로 state+28 키, state+44 하위 2비트, state+48 하위 3비트 초기화
- 신규 상태에만 0095dd50으로 state+2c를 action+1c에서 설정하고, 0095dcf0으로 state+40을 action+21에서 설정
- 기존/신규 모두 0095cf10(state, action+18), 이어서 0095cd10(state, action+20 byte) 호출

중요: 048a가 올 때마다 모든 설정 필드를 덮어쓰는 것이 아니다. 일부 필드는 새 객체일 때만 설정된다. 타이머 setter의 충전 변화 이후 명시적 충전 값이 적용되는 순서도 보존해야 한다.

근거: pass1/0052ad40.txt, pass1/vtable_0121aaf4.txt, pass4/0052aea0.txt의 0052aebf–0052af44, pass3/008579e0.txt, pass3/009401f0.txt, pass3/0095dd50.txt, pass3/0095dcf0.txt

### 0429: 충전 setter 공유, 그러나 식별 경로는 다름

생성자 0081b8d0 → vtable 0127c98c의 +8 슬롯 0094f170 → 0095cd10

- owner 조회 후 actor+2c → [component+28 + action+14*4] → ability+124로 상태 객체를 얻는다
- mode != 0은 action+18을 충전 setter에 직접 전달
- mode == 0은 기존 state+42 byte에 action+18을 더하고 하한 처리 후 전달

0428/048a의 key와 0429의 배열 인덱스는 구조적으로 다르다. 숫자가 같다는 이유로 같은 능력 ID로 합치면 안 된다. 배열 범위와 유효 owner에 대한 전제도 별도로 검증해야 한다.

근거: pass1/0081b8d0.txt, pass2/vtable_0127c98c.txt, pass4/0094f170.txt, 특히 0094f186–0094f193

### 공유 상태와 timer

0095cd10:
- state+42 현재 충전 byte 저장
- state+40 unsigned byte와 state+41 signed byte 합으로 상한 제한
- 0으로 가거나 0에서 벗어나는 전이에 이벤트 발행
- 문자열 원본은 onCooldownStarted, onCooldownEnded. 이 명칭이 충전/쿨다운 의미를 뒷받침한다

0095cf10:
- 0093d4a0으로 generation-checked timer handle 유효성을 검사
- 타이머가 없는 상태에서 양수 적용: 충전 1 감소(하한 0), 009613b0으로 타이머 시작
- 타이머가 있는 상태에서 0 이하 적용: 충전 1 증가 후 00956380 호출
- 유효 타이머에 양수 적용: timer+24 갱신, 필요하면 timer+20도 더 큰 값으로 갱신
- onCooldownModified 이벤트는 새 값과 이전 값의 차이를 함께 전달하는 경로가 있다

009613b0:
- state+20 pointer / state+24 generation handle로 타이머 객체 보관
- timer+20 및 timer+24를 같은 입력 값으로 초기화하고 timer+1c에 state+1c 연결
- state+2c 조건을 검사하며 모든 양수 입력이 무조건 타이머를 만든다고 일반화할 수 없다

00956380:
- 기존 타이머 정리 경로
- 충전이 최대치가 아니면 타이머를 다시 만들고 0086bbf0의 반환값으로 timer+20/+24 초기화
- 연속 충전 복구 모델의 유력 근거지만 0086bbf0 계산식, tick/clock은 이번에 추적하지 않았다

필드 이름은 구조와 이벤트명에 근거한 작업용 의미다. timer+24는 현재 잔여량으로 강하게 보이지만 tick 감소와 시간 단위까지 증명한 것은 아니다. timer+20은 초기/확장 길이 후보다.

근거: pass3/0095cd10.txt, pass3/0095cf10.txt, pass4/0093d4a0.txt, pass4/009613b0.txt, pass4/00956380.txt, raw-refs.json

## 활성화에서 상태까지: 확인과 빈칸

기존 044c apply 0094ee90를 새 입력에서 재확인했다. actor의 item component에서 item+30 instance를 찾고 item+18 ability로 이동한다. item instance와 actor/ability ID를 혼동하면 안 된다.

00963200은 item+18 ability의 +124 상태를 읽고 +38 또는 (+30 + +2c)*+34 계산을 검사한다. 같은 정의를 가진 다른 아이템들의 상태 전이를 건드리는 경로도 보인다. 이것은 item ability와 위 충전 상태를 잇는 구조적 증거다. 하지만 044c → 0095cf10 직접 호출을 확인한 것은 아니다.

0094ee90는 onPlayAbility 문자열을 해시해 00536dd0 이벤트 전달 함수를 호출한다. onPlayAbility, onCooldownModified, onCooldownEnded 문자열 참조가 00551b00 부근에 함께 있다. 이 등록부와 UI 후보는 추가 후보로 유지한다. 직접 timer/charge HUD 읽기, 숫자 반올림, overlay 비율, 숨겨진 아이템 규칙은 아직 검증하지 않았다.

근거: pass1/0094ee90.txt, pass2/00963200.txt, pass2/00536dd0.txt, raw-refs.json. raw byte 검색의 absolute/E8 후보는 자동으로 유효 xref/함수라고 확정하지 않는다.

## 넓은 지도에서 유지할 경계

- replay reader 004ca130 → 004eb4a0 → 004cfec0 및 공통 queue 0092c240: 기존 저장소 근거. 이번 전체 receiver 재분석은 하지 않았다
- actor/skin: 기존 분리 구현을 존중. actor identity 확인과 skin label 미확정은 별개
- 0411–0417 일반 능력 요청/실행, 041a/041b override, 043a/043b grant/downgrade, 043c cancel, 0489 behavior sync: 기존 atlas 후보 유지
- 043e–0447/048b buff 계열: 후보 유지. 이번 타이머 공유 증거를 보호막/무적/피해 흡수 증거로 확대하지 않는다
- 0444 item quantity, 044b consumption: 기존 inventory 근거 유지. 충전 byte +42와 item quantity +34는 별개
- 확인되지 않은 HUD와 clock을 추정 구현으로 메우지 않는다

## 다음 최소 검증

1. 공통 timer 객체의 tick 함수와 0086bbf0 계산을 추적해 시간 단위, pause, 배속 기준 확인
2. 00551b00 이벤트 등록부의 실제 callback을 읽어 HUD인지 스크립트 계층인지 분리
3. 0428/048a key ↔ ability+124 객체 ↔ 0429 slot의 생성/소유 관계를 교차 검증
4. 이후 실제 replay record와 state transitions를 검증하되, 요청/성공/취소 및 charge 0/최대치 경계를 분리

이 보고서로 확인한 첫 공통 경로에서 분석을 멈춘다. 기능 구현, 커밋, 병합, 게임 실행은 하지 않았다.

### 마지막 짧은 확인: 이벤트 등록부

pass5/00551b00.txt에서 세 문자열이 같은 타입 등록 함수에 연결됨을 추가 확인했다.

- onPlayAbility → callback 0054d510
- onCooldownModified → callback 0054d550
- onCooldownEnded → callback 0054d530

등록은 확인했지만 callback 내용은 이번 범위 밖이다. 따라서 이 타입이 HUD 자체인지, 중간 스크립트 계층인지 확정하지 않는다. pass5의 다른 세 함수는 인접 등록/전달 후보의 원문을 보존한 것이며 새로운 의미 판정에 사용하지 않았다.
