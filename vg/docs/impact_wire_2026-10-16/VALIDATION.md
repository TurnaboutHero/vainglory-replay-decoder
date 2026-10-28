# 검증 기록

## 정확한 테스트 범위

```text
python -m unittest tests.test_impact_event_timeline tests.test_native_gold tests.test_native_stats tests.test_resource_wire_evidence tests.test_resource_wire_observations
Ran 73 tests — OK
```

새 impact 테스트5개와 이전 resource/gold/stats 검사68개다. exact length, raw source 역할·sentinel/high ID, NaN/Inf bits, opaque suffix6, nested marker 배제, numeric section/offset/record 시각, 기존 확정 통계와의 분리를 검사한다. 합성 검사이며 실제 accepted resource 감소나 UI 효과 검증이 아니다.

기존 Windows symlink privilege 제한은 별도다. 해당 검사를 통과한 것으로 보고하거나 보안 설정을 바꾸지 않는다. 이전 전체 Linux suite 결과도 이번 변경의 검증으로 사용하지 않는다.

## Native와 원본 표본

설치된 REA6.4.0/Ghidra12.1.4/JDK21의 한 headless immutable 프로젝트에서 순차로 조회했다. selected SHA는 `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`다. 이전 Windows 원본 SHA `659f9eed...`와 코드가 같고 LAA characteristic 한 byte만 다르다는 이전 전체 비교를 재사용한다.

원본 envelope와 replay가 있는 이 Windows 호스트에서 hash와 bytes를 재확인한다. 원본이 없는 외부 리뷰 환경에서 같은 검사를 독립 수행했다고 주장하지 않는다. H5810은 개발 표본이며 C16/normal17도 기존 대조 표본이다. 새로운 holdout·실제 화면 관측은 없다.

정적 메시지 입력과 실제 자원 감소를 구분한다. 사전 자원 상태와 guard가 없으면 같은 serialized impact operand가 서로 다른4/5 delta로 분할된다. snapshot의 비선형 wire mapping과 기존 actor no-op guard도 별도 경계다. reset/expiry/death는 주소 연결 없이 추정하지 않는다.

추가 공유 decoder 회귀 검사: `tests.test_impact_event_timeline tests.test_cooldown_event_timeline tests.test_actor_die_timeline tests.test_item_event_timeline tests.test_item_activation_timeline tests.test_event_semantics_atlas tests.test_event_timeline`에서75개 발견,74개 실행 PASS(실패/오류/skip0). 기존 `tests.test_event_timeline.EventTimelineTests.test_cli_rejects_discoverable_outputs_through_symlink_paths` 한 개만 Windows symlink 권한 제한으로 명시적으로 제외했다. 이 검사의 통과를 주장하지 않는다. 앞의73개와 impact5개가 겹치므로 결과를 합산하지 않는다.

기존 표본의 전체 strict scan:356 section,1,412,969 records.041e는 H5810 43,896 /C16 47,921 /normal17 2,285개로 총94,102개이며 모두payload22였다. 별도 stdlib field cursor와 새 `decode_fields` 결과를94,102개 전부 비교했고 불일치0이었다. section hash/bytes/record수 및 최소 witness를 `OBSERVATIONS.json`에 보존한다. 실제 적용량·buff 원인·공격력의 검증이 아니라 serialized raw field 일치다.

## 새 native 조회 완료

새 세션13 envelopes(open1+조회11+close1), 재사용14 envelopes 및 기존 committed source2개의 해시를 `REA_RECEIPTS.json`에 기록했다. 새 constructor/clone pseudo·assembly로041e prefix→action fields→queue→apply를 교차 확인했고,004d5930 pseudo/assembly와0095c940으로338/346→resource struct→component300/304 mapping을 재확인했다. 모든 조회와close가 성공했으며 Java 잔존 없음도 확인했다.

008577c0은 mode 조건 아래 최대64개의 같은 kind component를 순서대로 소비해 remaining+20을 줄이거나0으로 만든다. 확인한 body에는 별도041d·858230·callback·delete·expiry/death reset 호출이 없다. 이는 해당 body의 경계이며 다른 생산자나 간접 경로 전체의 부재를 뜻하지 않는다.

OBSERVATIONS SHA-256: `43c2724d5d1d755c7d5a80961956d71068e38fc7f989da985fac5c8b78be352d`. 원본 snapshot의338/346 바이트에 실제 양수가 있고, 기존 actor guard가 별도로 존재한다. 단순 선형 wire 역산278/282로 자원 값을 정하는 가설은 폐기했다.

최종 byte 교차 검사에서는 source356개의 해시·크기·record 수, impact94,102건의 layout/sign/raw fields, snapshot3,407건의338/346 값과selector, 공개 witness class17개를 원본의 독립 stdlib cursor로 다시 확인했다. 불일치0이며 source 원본이 있는 이 호스트의 검사다.

최종 로컬 독립 검토에서27 native envelope와 committed source2개의 byte 수·SHA·evidence ID를 원본으로 재검증했고 불일치가 없었다. native/decoder/snapshot 경계와 문서 링크·JSON·UTF-8·Python compilation·staged whitespace 검사도 통과했다.
