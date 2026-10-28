# 검증 기록

기준7753523 이후 연구 전용 변경이다. 기존 worktree/브랜치와 다른 세션을 보존했다. 시작 시 working tree clean, Java 없음 확인. REA/Ghidra ephemeral import 하나를 직렬 사용하고 성공적으로 close했다. 새 설치·GUI 잠금 우회·보안 변경·게임 실행·라이브 요청·공개 전송은 없었다.

## 실행한 검사

- `python -m unittest tests.test_cooldown_item_declarations tests.test_research_cooldown_models tests.test_cooldown_event_timeline tests.test_stat_stacking_model tests.test_passive_item_catalog tests.test_sequential_pe`: **36 tests**,0 failures/errors/skips,0.298s.
- 새 cooldown 선언 extractor: 해시 검증93 resources,32 inline active rows; metadata/relocation 오염 거절 및 finite float32 예제. 관련 세 모듈25 tests pass.
- 새 stat 구성 witness:5 tests pass. generic getter를 대수적으로 재현하며 arbitrary clamp를 넣지 않는다. 서버 피해/HEAL simulator나 모든 입력에서 instruction-bit-exact하는 모델이 아니다.
- `stat_stacking_pe.verify(<selected EXE>)`:4 registry/name/factory 연결,35% 초기 store,하한0/.5 초기 자료 및3 folded stub 바이트 PASS. 초기 store는 runtime 불변 증명이 아니다.
- `capacitor_retired_evidence.py --binary <selected EXE> --data-root <installed Data>`: 기존 출력 byte-identical, 잘못된 executable hash 거절,36 native receipt 검증. 세부 CAPACITOR_NATIVE_RECEIPTS.json.
- names/item/buff selected metadata와 locale/resource SHA를 재검증했다. named marker8개 cap1/policy0는 metadata이며 실제 모든 lifecycle 적용과 다르다.
- 독립 review: named-prefix/모델 범위 및 A/B 증폭·source/target·selector 검토. phase/event selector는 low5 bits 조건으로 수정했다. 모델 precision 범위와 실제 client stub 경계를 보강했다.

Native REA112 envelopes 중110 success(open 포함),2 failed. 별도 close 성공. exact-entry 실패, containing-procedure 조회, bounded raw read를 별도로 보존한다. 원본 전체 export 대신 hash/evidence identifier만 커밋한다.

## 수행하지 않은 검증

전체 Windows suite는 이번 연구 변경 때문에 다시 실행하지 않았다. 기존 Windows symlink 권한 실패와 이전 Linux full-suite 통과를 이번 커밋의 결과로 재사용하지 않는다. 실제 게임 화면0, 실제 replay 교차대조0, independent holdout0. H5810은 개발에 사용한 표본이다. 외부 역사·커뮤니티 실험은 부모 작업의 별도 검토이며 현재 binary/asset 값이나 실제 accepted event의 대체 근거가 아니다.

Root 독립 재실행: capacitor/retired structured JSON 및93-item cooldown JSON 모두 저장 결과와 exact match(3.98s). UTF-8/JSON/상대 링크/원본 경로 검사와 staged whitespace 검사를 수행했다.
