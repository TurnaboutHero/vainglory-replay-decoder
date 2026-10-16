# 검증 기록

## 코드와 회귀 검사

```text
python -m unittest tests.test_resource_wire_evidence tests.test_resource_wire_observations tests.test_native_gold tests.test_native_stats
Ran 68 tests — OK
```

새 테스트 6개와 기존 native gold/stats 검사다. raw4/5 ADD/SET·고위 actor ID·flags/tail·NaN/Inf bits 보존, 확정 gold/stats와의 분리, nested fake marker 배제, 후속 section framing 오류의 부분 성공 방지, 입력 및 미래 sibling output alias 거부를 검사했다. 합성 테스트이며 native effect 검증이 아니다.

검토자의 별도 넓은 실행은 `tests.test_resource_wire_observations tests.test_native_gold tests.test_native_stats tests.test_event_timeline` 77개 중 76 pass, 기존 symlink privilege 오류 1개였다. 실패는 `EventTimelineTests.test_cli_rejects_discoverable_outputs_through_symlink_paths`의 `WinError1314`다. 이를 통과나 skip으로 바꾸지 않았다. 위 68개 결과와 겹치므로 합산하지 않는다. 이전 Linux 전체 suite 결과를 이번 변경의 검증으로 사용하지 않는다.

새 research wrapper는 기존 `decode_fields`를 재사용하며 production parser/reducer는 변경하지 않는다. 독립 검토에서 hash preflight·재확인·전체 framing·unknown length·nonfinite·출력 alias·raw scope 경계에 중대한 문제가 없음을 확인했다.

## 로컬 표본과 원시 증거

`RAW_OBSERVATIONS.json`은 기존 개발/대조 표본 세 개에 새 도구를 실행한 결과다. 356 section, 1,412,969 records, resource4/5 3,731건이며 전체 framing 오류가 없었다. source bytes를 읽기 전후 hash/section set으로 재확인했다. 표본 build 인증, instance 원인, accepted effect 또는 독립 gameplay holdout 검증은 아니다. H5810은 개발 표본이다.

보고서의 source/record hash는 이 Windows 호스트가 원본 로컬 파일에서 계산했다. 외부 리뷰 환경이 원본 receipt envelope·replay 파일 없이 모든 hash를 독립 재계산했다고 주장하지 않는다. 이전 58 REA envelope hash 검증도 원본이 있는 이 호스트의 검증이다. 독립 검토의 코드·문서 재검토와 이 로컬 hash 검증은 다른 증거 수준이다.

## 환경과 미실시 항목

현재 작업은 로컬 파일·명령·headless 정적 분석에 한정했다. 잠긴 Windows에서 화면 검증 가능성을 가정하지 않았으며 게임 launch, 잠금 우회, 보안 설정 변경, 설치, 서버 요청·새 표본 다운로드·패킷 주입·바이너리 수정은 하지 않았다. 별도 Ghidra project 쓰기는 순차로만 수행한다. 새 실제 화면 관측 0, 새 독립 replay 표본 0이다.

실제 aggregate resource 반영·instance mapping·callback causality·서버의 최종 의미는 static operand/wire 연결만으로 확정하지 않는다. 필요한 최소 관측은 README와 native/replay 보고서에 명시했다.

같은 Windows 호스트의 독립 검토자가 `iter_records`/`decode_fields`/새 wrapper를 사용하지 않은 stdlib cursor로 원본을 다시 읽었다. 356 source hash·크기·section별 record 수, 1,412,969 records, private raw4/5 3,731건, 공개 witness 10개 및 sign/mode/layout count가 모두 일치했다(0 mismatch). 이는 원본이 있는 호스트의 독립 방법 교차 검사이며, 원본이 없는 외부 리뷰의 재계산을 뜻하지 않는다. RAW_OBSERVATIONS SHA-256: `1b1f05d4df0746f34b84973f694aea715a49821c4186c42ae759b1ff491bb178`. 관측한4/5 mode는 모두0이며 SET/reset 실제 관측을 주장하지 않는다.

## Native 교차 확인

REA 6.4.0 / Ghidra 12.1.4의 단일 headless immutable 프로젝트에서 `00858230`, `00858000`, `00816ec0` assembly를 새로 추출했다. producer의 local action vtable `0127c9b4`, actor/index/delta 및 ADD flags와 formatter opcode041d를 확인했다. `close_binary` 성공과 Java 잔존 없음을 확인했다. 새 envelope5개(open+assembly3+close), 재사용19개를 catalogued했다. 각 envelope hash는 원본이 있는 이 호스트에서 재계산한다.

기존 `verify_respawn_pe.verify(<selected EXE>)`도 새로 실행했으며 기존 `RESPAWN_CALLER_PE_VERIFICATION_2026-10-16.json`과 정확히 일치했다. 041d table→receiver `004d2cf4`→constructor `0081b960` 및 vtable serializer/apply/forward가 각각 `0094b380`/`0094f210`/`0092e950`임을 SHA-gated PE byte로 재확인했다. 이는 특정 replay record의 producer·instance·실제 효과를 인증하지 않는다.

최종 로컬 독립 검토자는 접근 가능한 원본 envelope로 새 catalog 24개의 byte 수·SHA·evidence ID를 다시 확인했고 불일치가 없었다. native/wire 경계와 새 wrapper/test 검토에서도 중대한 문제가 없었다. 이 재계산은 원본이 있는 Windows 호스트에서 수행했으며 외부 리뷰의 원본 접근 범위와 구별한다. JSON/UTF-8/상대 링크/Python compilation 검사도 통과했다.
