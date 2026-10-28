# 검증 범위

기준: `98629429c5dfea78e904fe4c9df9c3bf613aadff` 이후 같은 연구 브랜치. Production 파일 변경 없음. REA 6.4.0/Ghidra 12.1.4/JDK21 기존 설치, ephemeral immutable import 1개를 직렬 사용. 파일/명령 접근은 가능했고 GUI 잠금 우회·새 설치·보안 변경은 하지 않았다.

## 실행한 검사

- `python -m unittest tests.test_passive_item_catalog tests.test_sequential_pe -v`: 6 tests, 0 failures/errors, 0 skips (0.023s). Catalog의 executable/metadata/resource hash gate, nonfinite property bit 보존과 기존 PE negative checks 포함. 최종 catalog 확장 후 결과는 아래 최종 검사에 기록한다.
- `python -m vg.research.verify_passive_pe --binary <selected-exe>`: PASS. 6 dispatch pointers, folded `ret 8`, Shell property global name; [PE_CHECK.json](PE_CHECK.json). 동작 전체 증명이나 화면 검증은 아니다. Defense 분석자가 별도로 실행해 동일 결과를 확인했다.
- Shell의 정확한 시작주소 함수가 정의되지 않은 3개 REA query는 실패로 유지한다. 070 read_bytes의 세 작은 thunk를 후속 바이트 검사했고, 임의 인접 함수의 결과를 해당 callback 결과로 대체하지 않았다.
- UTF-8 decode 및 public 자료의 replacement character/원본 로컬 경로 검사: 해당 없음. 원본 EXE, decoded CFF, 전체 localization, raw native exports는 연구 커밋 밖에 남긴다.

전체 Windows suite는 이번에 반복하지 않았다. 과거 전체 Windows1173 결과에는 symlink 권한 실패가 있었으며, Linux1173 통과 receipt는 이전326582d에 대한 것이다. 어느 것도 이번 커밋의 새 전체 통과 결과라고 부르지 않는다.

## 증거 등급

정적 선택 build/asset 검사와 synthetic decoder tests만 수행했다. 실제 replay cross-check 0, 실제 화면 검증0, live server 요청0. H5810은 개발 표본이며 독립 holdout0. item catalog는 소유/효과 state/reward/서버 수혜 집합을 재현하는 simulator가 아니다.

## 최종 검사

- Catalog 확장 후 같은 focused command: 6 tests PASS, failures/errors/skips0 (0.008s). root+30의 array→entry→name indirection도 기존 synthetic case에서 검증한다.
- 전체93개 resource scan PASS: active capability34, buff declaration 보유47, passive cooldown key11. 서로 중복 가능한 선언 분류다. Root의 독립 재실행도 저장 JSON과 structured exact match (1.85s).
- 선택12개의 별도 resource 분석과 catalog 필드를 교차 확인했다. 세부 결과는 names/definition 및 catalog 자료에 남긴다.
- REA receipt94개 envelope: open1 + successful analysis90 + exact-procedure failures3. 오류를 성공 근거로 세지 않는다.
- 독립 검토2명: ownership/active scope와 defense/PE byte edge. ReflexBlock factory의 early-return 예외를 추가했고 helper selector4/5를 실제 resource apply와 구별했다.
