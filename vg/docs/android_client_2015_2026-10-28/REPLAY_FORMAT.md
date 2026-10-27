# 2015 Android 리플레이 기록 형식 — 2026-10-28

Android 15518(2015) `libGame.so`의 exported dynamic symbol과 Thumb-2 코드를
정적으로 분석해, 당시 리플레이가 **줄 단위 텍스트 로그**임을 확인했다. 실행·
리플레이 재생·서버 요청은 하지 않았다.

## 방법

- 정적/로컬 심볼 이름은 제거됐지만 exported dynamic symbol과 코드 바이트는
  남아 있다. `llvm-nm -D --defined-only`로 `KindredReplay`/`openReplayFile`
  주소를 얻고, 그 주소의 코드를 디스어셈블했다.
- `llvm-objdump -d --triple=thumbv7a-none-eabi`를 사용했다. ARM 모드로 읽으면
  잘못 해석되므로 Thumb triple이 필요하다.
- PC-relative literal pool 값을 ELF32 program header로 VA→offset 변환해
  참조 문자열과 상수를 확인했다.
- 전체 포맷 문자열 목록과 경고는 `SYMBOLS.json.replay_line_formats` 및
  `SYMBOLS.json.warnings`에 있다.

## 확인된 구조

1. **기록 파일.** `openReplayFile` @`0x4bc51c`는 `getReplayDataFilename(true)`로
   기본 이름을 만들고, `strftime` 포맷 `_%Y-%m-%dT%H-%M-%S.dat`(문자열
   @`0xff73c4`)을 덧붙인 뒤 `fopen(path, "w")`(@`0xff73dc`)로 연다. FILE*는
   전역 `Nuo::Kindred::_sReplayFile`(@`0x014e15a8`)에 저장된다. 기본 이름
   리터럴 `VaingloryReplay.dat`(@`0xff73e0`)도 같은 문자열 군에 있다.
2. **재생 파일.** `openReplayFileForRead` @`0x4bc494`는 같은 이름 규칙으로
   `fopen(path, "r")`을 호출한다(@`0xff73c0`의 `r`). `KindredReplay::connect`
   @`0x4dc6f8`은 파일을 열고 상태를 0→2로 바꾼다.
3. **재생 루프.** `KindredReplay::service` @`0x4dc678`은 상태 3(일시정지)이면
   건너뛰고, `getDeltaTime()`을 누적해 다음 패킷 시각에 도달하면
   `processPacketFromStr` → `getNextPacket` → `stripTimeStamp` 순서로 진행한다.
   `pause` @`0x4dc4f4`는 상태를 3으로, `resume` @`0x4dc500`은 이전 상태로
   되돌린다. `write` @`0x4dc4f0`은 `return 1`만 하므로 재생 중 outbound
   write는 파일에 기록되지 않는다.
4. **레코드 단위.** `getNextPacket` @`0x4bac8c`은
   `fgets(buf, 0x800, _sReplayFile)`을 호출한다. 즉 한 줄이 한 패킷이고
   최대 2047바이트다. `stripTimeStamp` @`0x4bad1c`은
   `sscanf(line, "%f:%*s", &t)`(@`0xff70c0`)로 줄 앞의 float 시각만 읽는다.
5. **줄 포맷.** 기록 문자열은 `%.5f:<이름>:<콤마 구분 인자>` 형태이며,
   `Pkt*` 40개와 `LocalInput_MoveTo` 1개를 확인했다. 아래 표의 필드 수는
   **인식된 변환 지정자 수**(`field_count`)이고, 비어 있지 않은 콤마 토큰
   수는 `token_count`, 빈 토큰까지 포함한 값은 `total_token_count`다.
   미인식 토큰은 `fields`에 `unknown:<토큰>` 자리표시자로 남고, 하나 이상
   있을 때 `unknown_tokens`에도 기록된다. 같은 이름의 포맷이 여러 번
   나오면 최상위 `format`이 첫 변형이고 이후 변형은 `variants`에 들어가며,
   `variant_count`는 최상위를 포함한 총 개수다. 형식 문자열은 ELF에 그대로
   존재하는 값이다.
   `†`는 리터럴이 콤마로 끝나는 경우로, **해당 리터럴이 보여주는 개수일 뿐
   전체 런타임 필드 수의 하한**이다.

| 이름 | 필드 수 | 포맷 |
|---|---:|---|
| `LocalInput_MoveTo` | 3 | `%.5f:LocalInput_MoveTo:%.5f,%.5f,%.5f` |
| `PktActivateItem` | 3 | `%.5f:PktActivateItem:%d,%d,%d` |
| `PktActorDead` | 1 | `%.5f:PktActorDead:%d` |
| `PktActorDie` | 2 | `%.5f:PktActorDie:%d,%d` |
| `PktActorRespawn` | 4 | `%.5f:PktActorRespawn:%d,%.5f,%.5f,%.5f` |
| `PktApplyBuff` | 7 | `%.5f:PktApplyBuff:%d,%d,%d,%.5f,%d,%d,%.5f` |
| `PktCancelAbility` | 2 | `%.5f:PktCancelAbility:%d,%d` |
| `PktCancelBuff` | 2 | `%.5f:PktCancelBuff:%d,%d` |
| `PktConnected` | 4 | `%.5f:PktConnected:%d,%d,%d,%s` |
| `PktConsumeItem` | 2 | `%.5f:PktConsumeItem:%d,%d` |
| `PktDecrementBuff` | 3 | `%.5f:PktDecrementBuff:%d,%d,%d` |
| `PktDetonateProjectile` | 4 | `%.5f:PktDetonateProjectile:%d,%.5f,%.5f,%.5f` |
| `PktEndMatch` | 2 | `%.5f:PktEndMatch:%d,%d` |
| `PktEntityAutoActorBounce` | 3 | `%.5f:PktEntityAutoActorBounce:%d,%.5f,%.5f` |
| `PktEntityAutoMoveTo` | 5 | `%.5f:PktEntityAutoMoveTo:%d,%.5f,%.5f,%.5f,%.5f` |
| `PktEntityAutoOrbit` | 6 | `%.5f:PktEntityAutoOrbit:%d,%.5f,%.5f,%.5f,%.5f,%.5f` |
| `PktEntityCancelAutoOrbit` | 4 | `%.5f:PktEntityCancelAutoOrbit:%d,%.5f,%.5f,%.5f` |
| `PktEntityDestroy` | 1 | `%.5f:PktEntityDestroy:%d` |
| `PktEntityFaceDir` | 4 | `%.5f:PktEntityFaceDir:%d,%.5f,%.5f,%.5f` |
| `PktEntityMoveTo` | 4 | `%.5f:PktEntityMoveTo:%d,%.5f,%.5f,%.5f` |
| `PktEntityMoveToAndFace` | 5 | `%.5f:PktEntityMoveToAndFace:%d,%d,%.5f,%.5f,%.5f` |
| `PktEntitySpawn` | 29† | `%.5f:PktEntitySpawn:%d,%d,%d,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%d,%d,%d,%d,%d,%d,%d,%d,` |
| `PktEntityTeleportTo` | 4 | `%.5f:PktEntityTeleportTo:%d,%.5f,%.5f,%.5f` |
| `PktFireProjectile` | 12 | `%.5f:PktFireProjectile:%d,%d,%d,%d,%.5f,%.5f,%.5f,%d,%d,%d,%d,%d` |
| `PktGrantAbility` | 2 | `%.5f:PktGrantAbility:%d,%d` |
| `PktGrantItem` | 3 | `%.5f:PktGrantItem:%d,%d,%d` |
| `PktHeroSpawn` | 90† | `%.5f:PktHeroSpawn:%d,%d,%d,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%d,%d,%.5f,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%d,%.5f,%.5f,%.5f,%.5f,%.5f,%.5f,%d,%d,%d,%d,%d,%d,%.5f,%.5f,%.5f,%d,%d,%d,%d,%d,%d,%d,` |
| `PktImpactHealth` | 6 | `%.5f:PktImpactHealth:%d,%d,%.5f,%d,%d,%d` |
| `PktItemActivated` | 2 | `%.5f:PktItemActivated:%d,%d` |
| `PktJoinedMatch` | 3 | `%.5f:PktJoinedMatch:%d,%d,%d` |
| `PktLevelUp` | 2 | `%.5f:PktLevelUp:%d,%d` |
| `PktModifyActorAttribute` | 7 | `%.5f:PktModifyActorAttribute:%d,%d,%.5f,%d,%d,%d,%d` |
| `PktModifyBuffDuration` | 3 | `%.5f:PktModifyBuffDuration:%d,%d,%.5f` |
| `PktModifyBuffStack` | 3 | `%.5f:PktModifyBuffStack:%d,%d,%d` |
| `PktModifyCooldown` | 5 | `%.5f:PktModifyCooldown:%d,%d,%.5f,%d,%d` |
| `PktModifyVisibility` | 4 | `%.5f:PktModifyVisibility:%d,%d,%d,%d` |
| `PktPlayAbility` | 3 | `%.5f:PktPlayAbility:%d,%d,%d` |
| `PktPlayAbilityOnLoc` | 5 | `%.5f:PktPlayAbilityOnLoc:%d,%.5f,%.5f,%.5f,%d` |
| `PktPlayerConnected` | 3 | `%.5f:PktPlayerConnected:%d,%d,%s` |
| `PktPlayerInfo` | 3 | `%.5f:PktPlayerInfo:%d,%d,%s` |
| `PktSellItem` | 2 | `%.5f:PktSellItem:%d,%d` |

일부 예: `PktImpactHealth`는 `int32,int32,float,int32,int32,int32` 6개,
`PktActorDie`는 `int32,int32`, `PktHeroSpawn`은 리터럴 기준 90개다.
`%f:%[^:]:%s`(@`0xff73a8`)도 같은 문자열 군에 있어 3분절 파싱 경로가 별도로
존재한다.

## `†` 리터럴의 한계

`PktEntitySpawn`(29개)과 `PktHeroSpawn`(90개) 리터럴은 둘 다 `,\n`으로
끝난다. 즉 콤마 뒤에 개행이 있어 그 자체로 한 줄을 끝내지만, 바로 뒤 rodata에
`%u,%u,%u,%f,...` 형태의 별도 변환 리터럴이 존재한다. 이 리터럴이 같은 줄에
이어 붙는 접미사인지, 다른 레코드/파서용 조각인지는 이번 슬라이스에서
호출 지점까지 확정하지 못했다. 따라서 두 개수는 "이 리터럴에 적힌 변환 수"로만
읽어야 하며, 실제 전체 필드 수는 더 많을 수 있다. 나머지 39개는 콤마로
끝나지 않아 리터럴 자체가 필드 목록을 닫는다.

## 해석과 한계

- 2015 Android 기록은 **텍스트 라인 로그**다. 저장소가 다루는 2020 Windows
  `.vgr`의 번호 매긴 바이너리 섹션과는 컨테이너·프레이밍이 다르다. 2020
  클라이언트의 문자열 대조는
  [../windows_client_2020_2026-10-28/README.md](../windows_client_2020_2026-10-28/README.md)에
  있다.
- 필드 타입은 `%d`=int32, `%u`=uint32, `%f`/`%.5f`=float, `%s`=문자열이라는
  printf/scanf 관례로 표기했으며, 플랫폼 ABI 확인은 하지 않았다.
- 포맷 문자열은 writer와 reader가 공유하는 패턴이다. 어떤 위치가 entity ID,
  좌표, 쿨다운인지의 의미는 각 `Pkt*` 처리 함수 분석이 별도로 필요하다.
- 런타임 실행, 실제 `.dat` 생성·재생, 2020 `.vgr`와의 대응 관계는 확인하지
  않았다.
