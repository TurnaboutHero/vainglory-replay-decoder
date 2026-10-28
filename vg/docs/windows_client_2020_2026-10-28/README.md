# Windows 4.x 클라이언트 리플레이 문자열 대조 — 2026-10-28

Windows SSH(`winsrv`)로 설치된 클라이언트를 macOS로 복사해, 실행 없이 printable
문자열만 정적으로 비교했다. 2015 Android의 텍스트 리플레이와 2020 Windows의
`.vgr` 계열이 같은 시대의 이름 규칙을 얼마나 공유하는지 확인하는 슬라이스다.

## 대상

| 항목 | 값 |
|---|---|
| 원격 경로 | `D:\SteamLibrary\steamapps\common\Vainglory\Vainglory.exe` |
| 형식 | PE32 GUI, Intel 80386 |
| 크기 | 29,545,984 bytes |
| SHA-256 | `659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642` |
| 비교 대상 | 2015 Android `libGame.so` 연구([../android_client_2015_2026-10-28/REPLAY_FORMAT.md](../android_client_2015_2026-10-28/REPLAY_FORMAT.md)) |

기존 REA 연구가 사용한 분석용 LAA 사본은 SHA-256
`d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`이고,
설치 원본과 PE characteristics 한 바이트만 다르다고 기록되어 있다
([../../effect_closure_2026-10-16/VALIDATION.md](../../effect_closure_2026-10-16/VALIDATION.md)).
이번 슬라이스는 설치 원본(`659f9eed…`)을 사용했다.

## 방법

- `ssh winsrv`에서 `scp`로 원본을 macOS로 복사한 뒤 SHA-256을 확인했다.
- `vg.research.windows_client_strings`가 8-bit ASCII와 UTF-16LE printable
  실행을 모두 모아 리플레이 문자열, `.vgr`/manifest 문자열, `Pkt` 문자열,
  텍스트 포맷, MSVC RTTI 클래스 이름을 분류한다(오프셋 포함).
- 실행·언패킹·복호화·디스어셈블리는 하지 않았다. RTTI는 단순
  `.?AVClass@Scope@Nuo@@` 형식만 `Nuo::Scope::Class`로 디코딩하고,
  템플릿·함수 스코프 형식은 `decoded: null`로 둔다.

```sh
python -B -m vg.research.windows_client_strings <Vainglory.exe> -o STRINGS.json
```

결과 요약은 [STRINGS.json](STRINGS.json)에 있다(printable 139,869개,
리플레이 문자열 16개, `Pkt` 문자열 0개, 텍스트 포맷 14개, RTTI 2,667개 중
단순 형식 1,993개만 디코딩).

## 확인된 것

1. **이름 규칙은 이어지고 컨테이너는 바뀐다.** rodata
   `14,766,224`–`14,766,332` 구간에 다음 리터럴이 이 순서로 있다
   (오프셋은 `STRINGS.json.vgr_and_manifest_strings`). `%s/%s`는
   `21,349,840`에도 한 번 더 나온다.
   - `replayManifest.txt`
   - `replayManifest-`
   - `_%Y-%m-%dT%H-%M-%S.dat`
   - `%s/%s.%d.vgr`
   - `%s/%s`

   2015 Android의 기록 파일 접미사 `_%Y-%m-%dT%H-%M-%S.dat`가 2020 Windows에도
   남아 있다. 그러나 실제 섹션 경로는 `%s/%s.%d.vgr`로, `디렉터리/기본이름.번호.vgr`
   형태다. 여기에 `replayManifest.txt`/`replayManifest-` 접두사가 붙는다.
   - 해석: 세션 이름은 시간 기반으로 유지하되, 한 개의 `.dat` 대신 번호가 붙은
     여러 `.vgr` 섹션과 manifest로 기록하는 구조로 바뀌었다.
2. **리플레이 RTTI 클래스.** `Nuo::Kindred::KindredReplay`,
   `Nuo::Kindred::ReplayDelegate`,
   `Nuo::Kindred::KindredSpectatorHUDReplay`,
   `Nuo::Kindred::KindredSpectatorHUDReplay::ReplayAnnotationNode`,
   `Nuo::Services::VideoReplayDelegate`가 남아 있다. 2015의 `KindredReplay`
   이름이 2020에도 유지된다.
3. **텍스트 라인 포맷은 이 빌드에 없다.** 2015 Android의 `Pkt*` 이름과
   `%.5f:Pkt...` 포맷은 ASCII+UTF-16LE printable 문자열에서 0건이다
   (`counts.pkt_strings=0`). `%...:` 형태 문자열 14건도 Pkt/LocalInput을
   포함하지 않는다. 2020 기록은 텍스트 라인이 아니라 `.vgr` 번호 섹션이다.
   - 이는 printable 문자열 범위의 관측이다. 문자열이 압축·난독화됐거나 다른
     모듈에 있을 가능성까지 배제하지 않는다.
4. **코드 참조 위치.** `%s/%s.%d.vgr`는 `0x4ca29d`, `replayManifest.txt`는
   `0x403163`, `replayManifest-`는 `0x4cda1d`, `.txt`는 `0x4cda58`에서
   참조된다([XREFS.json](XREFS.json)). 이 참조를 따라간 `.vgr` writer/reader와
   manifest 작성 경로는 [VGR_WRITER.md](VGR_WRITER.md)에 정리했다.

## 2015 포맷 질문에 대한 영향

2015 Android의 `PktEntitySpawn`/`PktHeroSpawn` 리터럴 뒤에 붙는
`%u,%u,%u,%f,...` 조각이 같은 줄의 접미사인지는, 2020 Windows 빌드에 텍스트
라인 writer가 없어 이 슬라이스에서도 확정하지 못했다. 해당 두 개수는 계속
"리터럴 기준 하한"으로 유지한다.

## 한계

- 문자열 수준 비교만 했다. `%s/%s.%d.vgr`를 실제로 쓰는 함수, manifest 형식,
  섹션 헤더는 디스어셈블하지 않았다.
- 설치 원본과 LAA 사본의 차이는 기존 문서의 기록을 인용했으며 이번에 다시
  바이트 비교하지 않았다.
- 런타임 실행, 리플레이 생성·재생, 서버 요청은 하지 않았다.
