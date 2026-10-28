# 임시 자원 경로와 리플레이 검출 — 2026-10-16

기준 `cb89d4cb7931b3f4520417adcf7e75143693518d`, 브랜치 `research/sequential-rea-20261016`에서 이어진 연구다. [이전 효과 경계](../effect_closure_2026-10-16/README.md)의 bookkeeping·callback·accepted effect 구분을 유지한다.

## 결과와 구현 범위

기존 `vg.analysis.native_event_fields.decode_fields`와 `vg.analysis.event_timeline`이 이미 정확한 `041d` layout에서 actor, 원시 resource index, float32 operand와 bits, ADD/SET, flag bytes, opaque tail, section/offset/record timestamp를 노출한다. 따라서 중복 parser나 보호막 상태 reducer를 추가하지 않았다. resource4/5는 기존 확정 골드·scoreboard reader의 대상도 아니다.

새 `vg.research.resource_wire_evidence`는 이 decoder를 재사용하여 **출처 감사**만 추가한다. 모든 record를 strict framing으로 읽고 section SHA·선택 record SHA·raw field witness를 남긴다. index4/5와 mode/sign별 count 및 첫 witness를 출력하며, actor lifetime·buff instance·source/cause·실제 적용량·누적 보호막 총량을 만들지 않는다. 값에 barrier/fortified health라는 확정 이름도 붙이지 않는다.

- [native 연결과 미확정 경계](01_NATIVE_BRIDGE.md): producer→action→queue→serializer/receiver→generic scalar resource mutation, callback과 wire의 차이.
- [기존 표본 검출](02_REPLAY_DETECTION.md): H5810/C16/normal17의 356 section, 1,412,969 framed records에서 index4/5 3,731건. H5810은 개발 표본이다.
- [RAW_OBSERVATIONS.json](RAW_OBSERVATIONS.json): 새 감사 도구의 전체 section hash 목록과 제한된 첫 witness. 원본 recording의 build는 in-band로 인증되지 않는다.
- [REA_RECEIPTS.json](REA_RECEIPTS.json): 재사용 native envelope 19개와 새 open·assembly 3개·close의 해시/evidence ID. 전체 export는 로컬에 보존한다.
- [검증 기록](VALIDATION.md): 테스트·재현·환경·증거 수준.

## 재현

기존 timeline에서 전체 raw resource rows를 출력한다. 두 명령 모두 이미 보유한 로컬 표본만 읽으며 다운로드·서버·게임 실행을 하지 않는다.

```text
python -m vg.analysis.event_timeline "<existing replay.0.vgr>" --opcode 0x041d --output "<timeline.jsonl>"
python -m vg.research.resource_wire_evidence "<existing replay.0.vgr>" --output "<resource-audit.json>"
python -m unittest tests.test_resource_wire_evidence tests.test_resource_wire_observations tests.test_native_gold tests.test_native_stats
```

`timestamp`/`record_time`은 outer replay header의 시각이다. 이를 실제 화면 game clock으로 바꾸지 않는다. 감사 출력의 `counts`는 record 수이며 operand 합계가 아니다. `operation_byte_raw=0`은 ADD, nonzero는 SET 입력이다. SET이나 음수 ADD만으로 특정 instance reset·소멸·피해 소비를 판별할 수 없다. native serializer의 payload12와 관측 VGR의 payload14도 동일 layout 전체로 취급하지 않는다.

## 다음에 필요한 가장 작은 실험

실행 가능한 기존 승인 환경에서 temporary resource instance의 ID·kind·current amount·원인 branch를 enqueue 직전 관측하고, 동일 action의 actor/index/operand/mode와 serializer/record 경계를 함께 기록해야 한다. 새 생성, 기존 증가, cached 감소, 해제/만료, actor destruction/reuse를 따로 구분한다. native accepted store 전후 aggregate와 instance 전후 값을 함께 비교하되 callback amount를 합산하지 않는다.

`0094e970`의 기존 damage apply도 resource4/5를 직접 바꾼다. 그러므로 `041d`만 모두 모아도 전체 aggregate 상태나 실제 보호량이 복원된다는 보장은 없다. 다른 mutation·spawn baseline·해제·수명 경계가 별도로 필요하다.

`041d`에 없는 instance·source·cause는 같은 actor·값·시간만으로 복원하지 않는다. 다른 source가 같은 scalar resource를 바꿀 수 있다. 현재 Windows 화면 실행을 가정하지 않았고 새 실제 화면 관측은 없다. 원본 게임 바이너리·리플레이·전체 native export는 제출하지 않는다.

## Lifecycle follow-up

[Expiry, removal and reset boundaries](03_LIFECYCLE.md) closes the negative remaining-instance cleanup and ordinary timeout-to-zero-stack hook. This is static lifecycle evidence, not reliable current resource reconstruction or a universal death/respawn reset. The hash-gated PE check and focused tests are reproducible without native execution.
