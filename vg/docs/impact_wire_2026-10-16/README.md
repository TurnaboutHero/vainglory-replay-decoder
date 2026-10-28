# 직접 자원 감소와 041e / snapshot 경계

기준 `ecfe6df08e2153bc9a0c3d16fb9324791f30dd97`, 브랜치 `research/sequential-rea-20261016`에서 이어진 연구다. [이전 raw resource 연구](../resource_wire_2026-10-16/README.md)의 `041d`만으로 전체 resource4/5 상태를 복원할 수 없다는 경계를 좁혔다.

## 확인한 연결

`041e` 수신 action의 apply는 `0094e970`이다. 이 함수는 하나의 impact operand를 `0086eb50`에서 당시 actor 상태에 따라 나누고 resource4/5를 직접 변경한다. 별도의 resource별 감소량을 `041d`로 다시 보내는 구조로 보지 않는다. [Native 보고서](01_NATIVE.md)에 constructor·vtable·serializer·queue·setter와 입력/출력, 반증 조건을 기록했다.

동일한 wire operand라도 사전 resource 잔액에 따라 resource4/5 감소량이 달라진다. serializer도 음수 operand를 처리하며 값을 수정할 수 있다. 따라서 `041e` 값은 원래 공격력, 최종 HP 피해 또는 resource4/5 각각의 delta가 아니다. source actor reference도 credited source를 의미하지 않는다.

## 최소 디코더 개선

기존 `decode_fields`와 `iter_timeline`의 framing을 재사용했다. 관측된 content24/payload22의 `041e`만 처리하며 다음 원시 입력을 노출한다.

- actor references `ref0/ref1`, float32 operand `value/value_bits`.
- BE u16 `native_code_raw`, `native_byte14_raw`, `native_byte15_raw`.
- native receiver가 복사하는16 bytes 뒤의6 bytes는 `remaining_hex`로 보존.
- `native_semantic_scope=raw_impact_operand`; accepted damage·보호막 감소·buff instance·현재 자원 총량은 추가하지 않음.

짧은 native payload16을 관측 VGR payload22와 동일한 전체 layout으로 취급하지 않는다. 다른 길이는 거부하고 NaN/Inf는 JSON null 및 원래 bits로 보존한다. `041e`는 기존 default timeline opcode에도 포함된다. atlas의 whole-event application/runtime confidence를 승격한 것은 아니다. 기존 골드·scoreboard reader는 변경하지 않았다.

```text
python -m vg.analysis.event_timeline "<existing replay.0.vgr>" --opcode 0x041e --output "<impact.jsonl>"
python -m unittest tests.test_impact_event_timeline tests.test_native_gold tests.test_native_stats tests.test_resource_wire_evidence tests.test_resource_wire_observations
```

## Snapshot과 남은 경계

[표본 보고서](02_REPLAY.md)와 [OBSERVATIONS.json](OBSERVATIONS.json)에 원본 section/record hash·offset·outer record 시각·raw operand를 남긴다. wire는 native 메모리 배열 순서와 다르다. resource4는 payload `+0x152`(338), resource5는 `+0x15a`(346)에서 resource struct의 index4/5로 이동한다. resource6/7의 wire 위치에서 선형 역산한278/282는 이 자원들의 위치가 아니다.

Snapshot은 해당 값을 전달할 수 있지만 이미 존재하는 actor에 대한 spawn/apply guard를 무시하고 매번 상태를 덮어쓰면 안 된다. 인접한 snapshot과 impact record만으로 모든 intervening writer·수명·인스턴스 원인을 배제할 수 없다. 이번에는 전체 resource 상태 reducer 또는 snapshot의 일반16개 자원 API를 추가하지 않았다.

reset/expiry/death는 직접 연결이 확인된 범위만 다룬다. 피해 소비 helper가 인스턴스 bookkeeping을 바꾼다는 사실을 buff expiry나 actor death의 자원 초기화로 확장하지 않는다. 화면 대조는 잠금 때문에 수행하지 못했다. 새 서버 접근·표본 다운로드·binary 수정·공개 push/merge는 없다. H5810은 개발 표본이다.

[검증 기록](VALIDATION.md)과 [REA receipt catalog](REA_RECEIPTS.json)는 local native 검증, 합성 회귀 검사, 개발 표본의 byte 교차 검사와 미실시 runtime 검증을 구분한다. 원본 binary/replay와 전체 native export는 커밋하지 않는다.
