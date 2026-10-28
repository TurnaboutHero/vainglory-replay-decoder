# 기존 replay의 resource4/5 wire 관측

기준 `cb89d4c` 이후 독립 읽기 전용 조사다. 먼저 [RESOURCE_RECEIVER](../RESOURCE_RECEIVER_FOLLOWUP_2026-10-16.md), [NATIVE_GOLD](../NATIVE_GOLD_TIME_2026-10-03.md), [EVENT_SEMANTICS](../EVENT_SEMANTICS_2026-10-04.md)를 읽었다. 아래는 기존 development/control recording 세 개의 **엄격한 record framing과 raw field 관측**이다. 새 recording, 게임·서버 실행, Ghidra, 다운로드 또는 production parser 변경은 없다. held-out corpus의 gameplay 내용을 새로 분석하지 않았다.

## 표본과 전체 framing

| 표본 | 공개 표본 식별자 | section 범위 | 완전 framed record 수 | framing 오류 |041d payload 길이|
|---|---|---|---:|---:|---|
|H5810|`H5810`|0..167 (168개)|663517|0|14만 관측|
|C16|`C16`|0..170 (171개)|720282|0|14만 관측|
|normal17|`normal17`|0..16 (17개)|29170|0|14만 관측|

합계356 section,1412969 records다. 각 표본의 filename prefix는 하나이며 section 번호가0부터 연속됨을 확인했다. `vg.core.vgr_records.iter_records`로 각 파일을 처음부터 끝까지 모두 읽은 뒤에만 집계했다. timestamp는 finite BE float32, length는 BE u32이며 opcode를 포함한다. record마다 `offset+8+content_length`로 다음 경계에 도달한다. byte signature 검색 또는 손상 뒤 재동기화로 찾은 레코드는 없다. 이 결과는 framing 성공이지 recording/build match, 원본성과 gameplay mutation의 검증이 아니다. 이름이 substituted-slot인 기존 복사본도 이번에는 해시로 고정해 읽었고, 복사본의 원본 chain 전체가 별도로 재검증됐다고 주장하지 않는다.

모든 section의 현재 SHA-256은 private inventory에 있다. 아래 digest는 각 표본의 숫자순 section 목록 `{section,bytes,sha256}`을 `json.dumps(entries,sort_keys=True,separators=(',',':')).encode('utf-8')`로 직렬화한 **manifest SHA-256**이다. 전체 replay 단일 파일 hash가 아니다.

| 표본 | ordered section manifest SHA-256 |
|---|---|
|H5810|`384cbd2ec3a140e6baf60f4d8a58f0dc26b2df4347f201b7cb2eac96295495b7`|
|C16|`4f12b968a2e496ad0488a22c70046d05f648df16e0c1b0d79f2bd98f47dd94a8`|
|normal17|`9b75526ce848eb3ef98fdca1d5c55d9add513d3274fa28d53fc8f20e2ae894b0`|

## raw resource index별 전체 관측

041d payload의 검증된 prefix는 actor BE u32 `+0`, operand BE float32 `+4`, resource byte `+8`, raw mode byte `+9`, flag bytes `+10/+11`이다. 모든 관측 payload14에는 선택 native copy12 뒤의2바이트가 남으며, 이를 opaque tail로 보존한다. native SET/ADD 분기는 mode0/비zero로 나뉘지만 여기서는 원본 mode byte를 그대로 보고한다.

| 표본 | index4 전체 | 양수 / 음수 /0| index5 전체 | 양수 / 음수 /0| mode bytes |
|---|---:|---|---:|---|---|
|H5810|1407|1189 /218 /0|4|3 /1 /0|둘 다 전부0|
|C16|1569|1322 /247 /0|522|319 /203 /0|둘 다 전부0|
|normal17|229|228 /1 /0|0|0 /0 /0|index4 전부0|

index5 actor IDs는 H5810에서1506(4건), C16에서1507(198건),1505(244건),1503(80건)이다. 이는 numeric actor 참조이며 이 조사에서 영웅 이름·buff instance·ability와 결합하지 않았다. index4는1500대 외에도2000대 등의 actor가 포함되므로 플레이어 전용 이벤트로 간주하지 않는다. normal17의 index5 미관측은 해당17개 section의 사실일 뿐 모든 모드나 해당 native 기능의 부재 증명이 아니다.

## 최소 byte witness

아래 시각은 **해당 record header의 timestamp**이며 GameTime·화면 시각으로 바꾸지 않았다. offset은 section 시작 기준 record header 위치다. payload 시작은 항상 `record_offset+10`; 모든 witness의 opcode041d, content length16, payload length14다. operand bits는 network-order float의 최소4바이트 표기이며 전체 payload dump는 싣지 않는다. raw mode0, flags `[1,0]`, tail `0000`은 이 여섯 witness의 실제 바이트다. flags/tail을 reset 또는 제거 원인으로 이름 붙이지 않는다.

| ID | 표본 | section / record offset | record timestamp | actor | index | operand / bits | mode /flags /tail |
|---|---|---|---:|---:|---:|---|---|
|W1|H5810|2 / 42277|22.492843627929688|2121|4|150.0 / `43160000`|0 / `[1, 0]` / `0000`|
|W2|H5810|117 / 106740|1176.803955078125|1506|5|268.8863525390625 / `43867174`|0 / `[1, 0]` / `0000`|
|W3|H5810|135 / 146738|1359.3311767578125|1506|5|-29.925268173217773 / `c1ef66f3`|0 / `[1, 0]` / `0000`|
|W4|C16|8 / 108228|88.35222625732422|1507|5|821.0 / `444d4000`|0 / `[1, 0]` / `0000`|
|W5|C16|9 / 43642|90.31916809082031|1507|5|-821.0 / `c44d4000`|0 / `[1, 0]` / `0000`|
|W6|normal17|0 / 19547|4.767024993896484|2121|4|150.0 / `43160000`|0 / `[1, 0]` / `0000`|

| ID | section SHA-256 | record SHA-256 | packet SHA-256 |
|---|---|---|---|
|W1|`55242390ac790e809c606c449cf52144b06b69b209c82e36b41572a15eea50fd`|`cf7dfd2749c9ab465fedd6b46b83c45afbf0aa896801fdbc4e7cb083cae31d91`|`813b8fc9433c5745c1c9d77b4d9f0a7787bbda7e89349a5b1bee24abcc49d415`|
|W2|`01bd37c550c03f2a5e7ee930976fd3515c89482b1ecc168f53fe63d31a9c377e`|`fe1e4af47ebf1f307a849db35c37e9d9aa81299ee2d14f0d50b145e594edd4d8`|`5e08d7602223cd9557c26b7f9d5c014acd4d962bda41885f65c23b9e9f458698`|
|W3|`1b089d95a92968c825beb8b1129b25d15ccb17dce0ce399245d5a31215bb04d4`|`8e598bd3756588ad59cb7c47921087412906b8efac0487defe6013e46baae07d`|`977f54378e9689c4ed05b7f5c8cf11eb794b16205872b8eec20623e89095f95b`|
|W4|`b910afd81e42bf9912155aa1d3a352968ca322fb28f6fb2aec651f0c4fdf35fa`|`179a4c192298c387d3224023b56d8b12f95c8a0741fe60c24663726f59e7c7e3`|`9daa136f4c01cded149720cafdfdde91429116868241115348a31dbd87ad69df`|
|W5|`5ad5017eef4e05027dcf96db9b969b2a462f58dacd7d217c091672aa970b4f78`|`eaf564205fe2c3812fe31a72521756fdec4731efc0fe0c6a813715bef991ebdb`|`c630dffab0bd0f84d865db2e83b6b80a400f2169f87f56c252dc7aeaba34dae6`|
|W6|`da6d8cf0c2f5f161d4d1733e67b82bf6a6d72fa085d2cad57dc97000b4fad2f6`|`4a73e592029b99bfb87f6963d71313fb2d3653d7e23eac15fc1d6ec93138cf05`|`813b8fc9433c5745c1c9d77b4d9f0a7787bbda7e89349a5b1bee24abcc49d415`|

record hash 범위는 timestamp/length header를 포함한 `[record_offset, record_offset+8+content_length)`다. packet hash 범위는 record header를 제외한 `[record_offset+8, record_offset+8+content_length)`이며 opcode2와 payload를 포함한다. 같은150 index4 packet이 다른 표본에서 같은 hash를 갖는 것은 독립 controlled validation 세 건이 아니다. W4/W5의 +821/−821도 actor와 index가 같고 operand가 반대라는 관측일 뿐, 같은 buff instance의 정확한 생성·삭제/reset 짝으로 증명되지 않았다. 중간 자원·피해·다른 producer·clamp·baseline을 아직 재구성하지 않았고 직접 관측 화면도 없다.

## 00858230과 연결할 때 남는 provenance

선택 LAA에서 `00858230`이 temporary-resource component의 selector/amount/instance와 action 생성에 연결된다는 native 사실은 별도 producer 연구다. 이 raw041d prefix가 제공하는 것은 actor/resource/operand/mode/flags이며 **buff instance ID, producer 주소, ability ID, callback ID, shared-allocation ID, reset reason**은 없다. 따라서 index4/5 관측을 곧바로 특정 Phinn/Reim/아이템의 부여·감소·종료로 귀속할 수 없다. 다른 message나 side channel에 provenance가 있을 가능성도 이 조사로 배제하지 않는다.

여기서 가능한 안전한 결과는 raw resource-index4/5 update의 탐지·위치·부호·mode 목록이다. barrier/fortified health의 최종 상태, instance별 delta/reset tracker, 능력별 집계, damage-order 역산은 추가하지 않는다. 필요 증거는 같은 build의 actor lifetime/baseline, action enqueue/accepted apply와 temp-resource component instance를 동시에 관측한 trace, 각 producer의 wire serializer 연결, 다른 update/health split과 삭제 경계다. record timestamp 근접이나 +x/−x만으로 그 결손을 채우지 않는다.

## 재현 입력과 검사 범위

private `resource-replay-inventory-agent.json`은 전체 section 경로/hash/크기, 전체041d resource-index counts와 제한된 witness 예시를 담는다. 예시는 index4/5별 최대250개, 그 외 index별12개이며 **집계는 전체 입력 기준**이다. private `resource-replay-resource45-agent.jsonl`은 이 세 표본의 index4/5 모든3731 occurrences를 담는다. public에는 위 최소 witness만 남긴다. 전체 JSONL과 replay 원본, whole payload는 커밋하지 않는다.

기존 framing 테스트 `tests/test_vgr_records.py`는 exact cursor/owning timestamp, partial header/body와 nonfinite timestamp 거절 등을 다룬다. 이 조사에서 새 테스트나 native/game 실행을 수행한 것은 아니다. 후속 research wrapper는 기존 field decoder와 원본 hash를 재사용하여 제한된 witness classes를 재검증할 수 있다. 이 문서 작성 과정에서 production parser를 변경하지 않았다.

| 읽은 구현/검사 source | 현재 SHA-256 |
|---|---|
|`vg/core/vgr_records.py`|`08200f1dd4165055fe15ea724780f74ed22074118e5183ae47006e6271e406a6`|
|`tests/test_vgr_records.py`|`0862d80ba45564dd91f2a9372ea2319e4aee83ab52e821cf5197a04e8e65eebc`|
