# 효과 실행 경계 추가 분석 — 2026-10-16

기준 커밋 `010c67c02e5645a058282406a2aed3530cc842e2`에서 이어진 정적 연구다. 브랜치는 `research/sequential-rea-20261016`이며 production decoder는 변경하지 않는다. [이전 연구](../stat_stacking_2026-10-16/README.md)의 조건부 계산과 이번 accepted effect 증거를 혼동하지 않는다.

1. [Capacitor 값·발동 경로](01_CAPACITOR.md): outgoing barrier34/layer0와 heal36/layer2 선언을 실제 소비자와 분리했다. 단일 zero helper 외의 생성 경로, constructor와 getter 호출자를 역추적했다.
2. [방어·관통·감소 순서](02_DAMAGE_ORDER.md): 알려진 생산자와 로컬 실행 stub을 구분하고, 순서를 식별할 수 있는 관측값과 실험의 한계를 기록했다.
3. [실행 환경·증거 경계](03_VALIDATION_ENVIRONMENT.md): WTSActive와 unlocked는 별개다. native effect 검증은 수행하지 않았으며 실제 GUI/game 실행 결과를 주장하지 않는다.

## 이번에 좁힌 연결

- `00847620`은 미해결 함수가 아니라 `00841c30`으로 가는 JMP였다. Reim post-attack perk는 source/target/kind/mode 조건 아래 `max(1, combat[+44]*ratio)`를 계산한다. 새 resource5 생성은 `00858000`, 기존 인스턴스 증가는 `00858230`으로 간다. 기존 인스턴스에만 이 body의 maxHP cap이 적용된다. 이는 `004b7c00`의 0 반환을 우회하는 별도 경로다.
- `00858230`은 resource bookkeeping과 양수 phase6 알림을 갱신한다. 이것만으로 최종 actor HP/fortified health 반영이나 증폭 계산을 증명하지 않는다. Reim 경로는 self→self이므로 Capacitor speed callback의 self-target 제외 조건에서 탈락한다. W가 이 callback을 일으키는지는 별도 미확정이다.
- 임의의 `+218` SSE 접근 네 곳은 Sound/geometry/snapshot 객체였다. actor heal 증폭 소비자 후보에서 제외했다. generic getter의 확인된 direct callers에서도 AMP33..36 전용 소비자는 찾지 못했다. 이 범위 밖의 간접 호출·다른 코드 생성 형태까지 부재라고 말하지 않는다.
- 속성 wrapper `00957710`의 `0081c640` 초기화는 45개 슬롯의 네 층을 모두 0으로 만든다. 이후 level/buff 변경과 실제 소비자 적용은 별도 단계다. 초기 heal layer에 1이 숨겨져 있다는 가설은 배제했지만 이것을 영구 runtime 값으로 취급하지 않는다.
- 설치 원본과 분석용 LAA EXE는 29,545,984 bytes 중 PE characteristics 한 byte만 다르다. 게임 코드와 확인된 stub은 같다. 분석용 LAA 패치가 stub을 만들었다는 가설을 배제한다.

## 증거 재현

[PE_BOUNDARIES.json](PE_BOUNDARIES.json)은 두 EXE 전체 SHA와 LAA 차이, 세 stub·네 direct call·다섯 virtual edge의 검증 결과다. [CAPACITOR_VALUE_PATHS.json](CAPACITOR_VALUE_PATHS.json)은 hash-gated raw/asset 추출 결과이며 [REA_RECEIPTS.json](REA_RECEIPTS.json)은 새 REA envelope 해시·evidence ID 목록이다. 원본 EXE, asset, 리플레이와 전체 decompiler export는 커밋하지 않는다.

`vg.research.effect_boundary_probe`와 `vg.research.capacitor_value_paths`는 읽기 전용 검증 도구다. [검증 기록](VALIDATION.md)에 명령과 결과를 남긴다. 각 가설의 주소·입출력·호출자·반증 조건은 개별 보고서에 있다. 실제 화면 관측 0, 새 독립 리플레이 검증 0이다. H5810은 개발 표본이며 독립 검증으로 세지 않는다.

## 남은 실검증

Capacitor의 15% 선언을 실제 accepted amount로 바꾸는 소비자, Phinn/Rook의 최종 자원 반영, armor/shield/shred/pierce/Grumpjaw의 실제 비가환 실행 순서는 확인되지 않았다. 현재 설치물의 일부 실행 graph는 stub에 닿으며, 별도 서버 코드도 확보하지 않았다. 이는 서버 구현 전체의 부재나 라이브 효과 미지원의 증명이 아니다. 각 보고서의 최소 실험은 source/target generation, resource instance, accepted action 전후 amount와 중간 단계값을 필요로 한다. 최종 HP만으로 서로 교환 가능한 연산 순서는 식별되지 않는다.

## 후속: 생명의 샘의 HP 저장 경계

[회복 증폭 소비자 후속 조사](../amplification_consumers_2026-10-16/README.md)는 생명의 샘 producer에서 resource0 ADD와 maxHP clamp의 첫 실제 저장까지 연결한다. 이 명시적 경로에 amp33..36 계산은 없으며, 저장 뒤 generic callback에 전달되는 값은 accepted HP 차이가 아니라 원래 requested operand다. 실제 15% 소비자·후속 callback·서버 효과는 여전히 별도 미확정이다.
