# 2020 Windows `.vgr` 기록·재생 경로 — 2026-10-28

Windows SSH로 가져온 설치 원본(PE32 i386, SHA-256
`659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`)을
대상으로, 문자열의 절대 VA 참조를 찾아 그 주변만 디스어셈블했다.

## 방법

- `vg.research.windows_client_xrefs`가 PE32 섹션을 파싱해 문자열 VA를 구하고,
  `.text`에서 그 VA를 little-endian dword로 참조하는 위치를 찾는다.
  결과는 [XREFS.json](XREFS.json).
- 각 xref 주변은 `llvm-objdump -d --triple=i386-pc-windows-msvc`로 읽었고,
  사용한 발췌를 [DISASM.txt](DISASM.txt)에 커밋했다(같은 SHA-256).
- 심볼이 없어 함수 이름은 붙이지 않고 주소로만 부른다. 실행·언패킹·복호화는
  하지 않았다.

## 확인된 경로

1. **경로 포맷 함수 @`0x4ca240`.** `...` 호출 뒤 `0x4ca29c`에서
   `"%s/%s.%d.vgr"`(VA `0x1215eec`)를 push하고(`xref @0x4ca29d`,
   call @0x4ca2a2`) `0x96c5e0`을 호출한다. 스택
   버퍼(`0x104` 바이트)에 `디렉터리/기본이름.번호.vgr`을 만든 뒤
   `std::string`으로 복사한다.
2. **재생(reader) @`0x4cb3e0`.** `0x4cb40d`에서 위 경로 함수를 호출하고,
   `0x4cb42c`에서 `"rb"`(VA `0x1215ee8`)를 push해 `0x96c240`으로 `fopen`한다.
   FILE*는 전역 `0x1eb09d8`에 저장된다(`0x4cb43e`).
3. **기록(writer) @`0x4cb4a0`.** `0x4cb4cc`에서 같은 경로 함수를 호출한다.
   이어 `time`/`localtime`/`strftime` 계열 호출(`0x4cb4dc`–`0x4cb4f8`)로
   64바이트 버퍼에 `"_%Y-%m-%dT%H-%M-%S.dat"`(VA `0x1215ecc`) 형식의
   타임스탬프를 만든다. 그 뒤 `0x4cb516`에서 `"wb"`(VA `0x1215ee4`)를 push해
   `fopen`하고, 경로 인자는 1의 `.vgr` 경로다.
   - 이 블록에서 타임스탬프 문자열은 `fopen` 인자로 쓰이지 않는다. 이후
     manifest/로그에 쓰이는지의 여부는 이 슬라이스에서 확정하지 않았다.
4. **manifest 작성 @`0x4cda00`.** `"replayManifest-"`(VA `0x1215eb4`)로
   `std::string`을 만들고, 중간 문자열을 append한 뒤 `".txt"`(VA `0x1215ec4`)를
   append한다(`0x4cda1c`–`0x4cda5f`). `"w"`(VA `0x1215ea8`, xref `0x4cdac2`)로
   `fopen`하고(`call @0x4cdac7`), 각 항목을 `"%s\n"`(VA `0x1215eac`,
   xref `0x4cdb36`)로 쓴다(`call @0x4cdb3b`).
   - 최종 이름은 `replayManifest-<중간 문자열>.txt` 형태다. 중간 문자열의
     출처(매치/세션 ID)는 별도 추적이 필요하다.
5. **전역 `replayManifest.txt` — 블록 @`0x403160`, xref @`0x403163`.** 정적 초기화 블록에서
   `"replayManifest.txt"`(VA `0x1215e90`) 길이 0x12로 `std::string`을
   구성하고 `0x11b86c7`을 호출한다.

## 해석

- 2020 클라이언트는 `%s/%s.%d.vgr` 경로로 **번호가 붙은 섹션 파일**을 열고,
  reader는 `"rb"`, writer는 `"wb"`로 연다. 즉 2015 Android의 줄 단위 텍스트
  `.dat`와 달리 **바이너리 섹션 컨테이너**다.
- 2015의 `_%Y-%m-%dT%H-%M-%S.dat` 타임스탬프 형식은 2020 writer 블록에도
  남아 있지만, 이 블록에서 `.vgr` 경로와 직접 결합되지는 않는다.
- manifest는 `replayManifest-<...>.txt`를 `"w"`로 열어 `"%s\n"` 항목을 쓰는
  텍스트 파일이며, 전역 `replayManifest.txt` 이름도 별도로 존재한다.
- `.vgr` 섹션의 내부 헤더/레코드 프레이밍은 이번 슬라이스에서 열지 않았다.

## 한계

- 심볼이 없어 함수 경계와 호출 대상은 주소·호출 패턴으로만 식별했다.
- `fopen` 래퍼 `0x96c240`, 포맷 래퍼 `0x96c5e0`, manifest 출력 래퍼
  `0x96c280`의 정확한 시그니처는 문자열·인자 배치로 추정했다.
- 런타임 실행, 실제 녹화·재생, 서버 요청은 하지 않았다.
