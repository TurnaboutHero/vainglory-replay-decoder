# 검증 기록

기준 `010c67c02e5645a058282406a2aed3530cc842e2`, 기존 격리 worktree와 연구 브랜치를 유지했다. 원본·선택 EXE는 읽기만 했다. GUI 잠금 우회, 보안 설정 변경, 설치, 게임 실행·수정, 라이브 요청, 공개 push/merge는 하지 않았다.

## 자동·정적 검사

```text
python -m unittest tests.test_cooldown_item_declarations tests.test_research_cooldown_models tests.test_cooldown_event_timeline tests.test_stat_stacking_model tests.test_passive_item_catalog tests.test_sequential_pe tests.test_research_validation_environment tests.test_research_buff_lifecycle
Ran 46 tests — OK
```

독립 검토자가 위 distinct 46개를 실행했다. 기존 36개에 새 환경/증거 경계 3개와 기존 lifecycle 7개를 더한 수이며, 이전 subset 결과를 중복 합산하지 않았다. 새 3개는 WTSActive≠unlocked, unlocked≠owned process, hash-valid synthetic capture≠exportable reference를 검사한다. 실제 engine 효과 검사나 전체 suite 결과가 아니다.

- `python -m vg.research.effect_boundary_probe --selected <selected EXE> --original <installed original EXE>`: 전체 SHA, 한 바이트 LAA 차이, 세 stub·네 call·다섯 vtable edge PASS. 결과가 `PE_BOUNDARIES.json`과 정확히 일치했다.
- `python -m vg.research.capacitor_value_paths --binary <selected EXE> --data-root <installed Data>`: init/config/JMP bytes·호출 후보·두 hero asset 추출 PASS. 결과가 `CAPACITOR_VALUE_PATHS.json`과 정확히 일치했다.
- 두 도구의 잘못된 executable hash 거부 PASS. 첫 도구의 잘못된 original hash 거부 PASS. 훼손한 Phinn resource는 CFF 해석 전 resource SHA mismatch로 거부됐다. 원본 파일은 바꾸지 않고 임시 fixture만 사용했다.
- 독립 정적 검토에서 Reim context+18 pointer를 target으로 단정하던 표현을 수정하고, existing resource branch의 strictly-positive guard를 명시했다. cap 초과 시 음수 보정을 수행한다는 주장을 하지 않는다.

## REA 실행과 자료 한계

REA 6.4.0 / Ghidra 12.1.4 / JDK21의 immutable ephemeral 프로젝트를 순차로 사용했다. 첫 세션의 54번 export까지 보존한 뒤 로컬 queue 필드 이름 오류로 wrapper가 끝났다. 별도 이름으로 후속 분석 세션을 열었다. 두 프로젝트의 동시 쓰기는 없었다. 실패한 `00450910` incoming-reference 조회는 전체 결과가 MCP response budget을 초과했다. 이를 caller 부재 근거로 사용하지 않았다. 함수 exact-entry 실패도 raw JMP·containing-procedure로 재확인했다.

REA envelope 전체 대신 SHA·evidence ID·subject hash를 `REA_RECEIPTS.json`에 남긴다. raw bytes 후보 탐색은 특정 opcode/변위 형태에 한정되므로 완전한 instruction-boundary 검사나 모든 AMP 소비자 부재를 증명하지 않는다. 전체 원본·게임 asset·리플레이·전체 decompilation은 제출물에 넣지 않는다.

## 실행 검증 미실시

native effect 실행 검증은 수행하지 않았으며 실제 GUI/game 실행 결과를 주장하지 않는다. 기존 native runner의 세션·소유 프로세스 검증 조건과 합성 증거의 한계는 `03_VALIDATION_ENVIRONMENT.md`에 있다. 호스트별 실행 정보는 공개 문서에서 제외했다.

새 실제 화면 관측 0, 새 독립 replay 교차 검증 0, independent holdout 0이다. H5810은 개발 표본이다. 이전 Linux 전체 suite 결과를 이번 변경의 검증으로 재사용하지 않는다. production decoder 수정은 없다. 실제 AMP accepted amount·armor order는 보고서에 적은 관측값과 실행 가능한 환경이 확보돼야 닫힌다.

후속 REA에서 constructor `0081c640` pseudo/assembly, wrapper `00957710` 소속, `00858230`의 알려진 외부 direct callers 6개를 교차 확인했다. 후속 분석 세션은 `close_binary` 성공으로 정상 종료했다. 총 58 envelope 중 57 success, response-budget 실패 1개이며 두 open과 후속 close를 포함한다. 원본 envelope hash는 로컬 재생성해 catalog와 맞췄다.
