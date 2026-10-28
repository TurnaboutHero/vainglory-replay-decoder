# Android 15518(2015) 클라이언트 정적 분석 — 2026-10-28

macOS에서 공개 아카이브의 Android 클라이언트를 내려받아, 실행 없이 이름·문자열
수준의 정적 분석만 수행했다. 게임 실행, 서버 요청, 바이너리 수정은 하지 않았다.

## 대상 자료

| 항목 | 값 |
|---|---|
| 출처 | archive.org item `VaingloryV15518.DroidFive`, `Vainglory v15518.DroidFive.apk` |
| 내려받기 | <https://archive.org/download/VaingloryV15518.DroidFive/Vainglory%20v15518.DroidFive.apk> |
| APK SHA-256 | `5f5590632d2f8db3353725b683abbe0eb604781a9bb6f554fa5101fe21c90bb3` |
| APK 크기 | 10,890,611 bytes |
| 패키지 | `com.superevilmegacorp.game`, versionCode `15518`, 빌드 2015-03-11 |
| 분석 대상 | `lib/armeabi/libGame.so` (ELF 32-bit ARM, EABI5, stripped, 21,885,948 bytes) |
| `libGame.so` SHA-256 | `4aeb54599af10327fdc37b6df0e297dfbc32cebfadf9ceb46ac750d77fb2f159` |
| 보조 확인 | 같은 아카이브의 iOS 4.13.0 IPA `com.superevilmegacorp.kindred` |

원본 APK·ELF·IPA는 저장소에 넣지 않는다. 아래 결과는 `SYMBOLS.json`에 파생
메타데이터로만 남긴다.

## 방법

`nm -a`로는 정적 심볼이 0개지만 exported dynamic symbol table에는 약 4.7만
개가 남아 있어 `KindredReplay`/`openReplayFile` 주소로 Thumb 코드를
디스어셈블할 수 있었다. 같은 ELF의 출력 가능한 문자열에는 맹글링된 C++ 이름이
남아 있다. `vg.research.android_client_symbols`가 출력 가능한 실행을
영숫자·밑줄 단위로 나눈 뒤 각 조각이 `_Z...` 전체와 일치할 때만 후보로
삼고, macOS `c++filt`로 디맹글링해 리플레이 심볼과
`Nuo::Kindred::Action*` 클래스를 분류한다. 디맹글링되지 않은 이름 수와
경고는 결과 JSON의 `counts`/`warnings`에 남는다. 코드 실행·동적 계측·페이로드
해독은 하지 않는다.

교차 비교는 저장소의 2020 Windows 의미 카탈로그
`vg/docs/event_semantics_2026-10-04.json`(SHA-256
`9bec8765397e1db669522a9ec86cde52f0f6efd41b2e853dc886ae4045256674`,
`Action*` 이름 84개)을 기준으로 하며, 일치/불일치 목록은
`SYMBOLS.json`의 `cross_client`에 그대로 들어간다.

```sh
python -B -m vg.research.android_client_symbols <libGame.so> -o SYMBOLS.json
```

## 확인된 것

1. **리플레이 구현 위치(2015 빌드).** `Nuo::Kindred::KindredReplay`는
   `KindredConnectionType`을 갖는 연결 객체이며 `isLocalOnly()`가 있다.
   `init/uninit/connect/disconnect/service/pause/resume/rewind`,
   `write(void const*, unsigned int)`를 제공하고, 파일 쪽은
   `openReplayFile/closeReplayFile/flushReplayFile/openReplayFileForRead/
   closeReplayFileForRead/rewindReplayFileForRead`로 분리된다. 전역
   `_sReplayFile`과 파일명 리터럴 `VaingloryReplay.dat`도 확인된다.
   - 해석(추정): 리플레이는 로컬 전용 연결로 기록 바이트를 네트워크 수신
     경로에 재생하는 구조다. 이는 이후 Windows 4.x 기록이 `Action*` 메시지
     스트림으로 보이는 것과 일치한다.
2. **2015 빌드는 줄 단위 텍스트 `.dat`.** 2020 Windows 클라이언트의 번호
   매긴 `.vgr` 섹션 계열과 컨테이너·프레이밍이 다르다. 2015 빌드 문자열에는
   `.vgr`이 없고 `VaingloryReplay.dat`과 `%.5f:Pkt*:...` 라인 포맷만 있다.
   기록·재생 경로와 41개 라인 포맷은
   [REPLAY_FORMAT.md](REPLAY_FORMAT.md)에 정리했다.
3. **Action 분류 49개.** 2015 ELF에서 확인된 `Nuo::Kindred::Action*` 클래스
   49개 중 44개가 위 2020 카탈로그의 이름 84개와 일치한다. 2015에만 있는
   것은 `ActionActivateItem`, `ActionAssignMaster`, `ActionBuyAbility`,
   `ActionModifyEnergyCost`, `ActionPauseGame` 5개이고, 카탈로그에만 있는
   이름은 40개(예: `ActionStartMatch`, `ActionCreateZoneOfControl`,
   `ActionEquipTalent`)다. 전체 목록은 `SYMBOLS.json`의
   `cross_client.both/client_only/repo_only`에 있다.
   - 해석: 액션 이름공간은 여러 해에 걸쳐 안정적이지만, 동일 이름이 같은
     와이어 레이아웃을 뜻하지 않는다. 2015 문자열에 없다는 사실은 그 클래스가
     2015 빌드에 없다는 증거가 아니라, 스트립된 이름 테이블에 남지 않았다는
     범위의 관측이다.
4. **생성자 시그니처(필드 후보).** 디맹글링된 생성자 인자 목록이 남아 있다.
   - `ActionImpactHealth(unsigned int, float, CombatDamageParams::DamageType,
     CombatDamageParams::DamageSource, bool, unsigned int)`
   - `ActionApplyBuff(unsigned int, unsigned int, char const*, float,
     unsigned int, unsigned int, float)`
   - `ActionModifyCooldown(unsigned int, unsigned int, float, bool, bool)`
   - `ActionEndMatch(unsigned int, EndGameReason)`
   - `ActionTeamSurrenderStateChanged(unsigned int, TeamState,
     unsigned int const*, unsigned char const*, float const*, float)`
   - `ActionActorRespawn(unsigned int, Math::Vector3 const&)`
   전체 49개 목록은 [SYMBOLS.json](SYMBOLS.json)에 있다.

## iOS 4.13.0 보조 확인

같은 아카이브의 iOS 앱은 Mach-O fat(armv7/arm64)이고
`LC_ENCRYPTION_INFO(_64) cryptid=1`(FairPlay)이다. __TEXT 약 28 MB가
암호화되어 있어 macOS만으로는 코드·ObjC 이름·`__cstring`을 정적으로 읽을 수
없다. 암호화되지 않은 `Data/` 자원은 매직으로 구분된다: `RSC0`
(`0x52534330`), `CFF0`(`0x43464630`), 폰트(`GSUB`/`OS/2`/`FFTM`), Ogg/RIFF
오디오. iOS 쪽 액션 이름 증거는 이번 슬라이스에 포함하지 않는다.

## 확립되지 않은 것

- 액션 opcode 번호, 레코드 프레이밍, 필드 순서와 직렬화 규칙
- `KindredReplay::write`가 받는 바이트 스트림의 압축·암호화 여부
- 2015 `.dat`와 2020 `.vgr`의 실제 변환 관계
- 생성자 인자 순서를 와이어 순서로 승격할 수 없음(복사 생성자만 남은
  클래스도 있음)
- 실제 실행·서버 결과·리플레이 재생 검증은 수행하지 않았다
