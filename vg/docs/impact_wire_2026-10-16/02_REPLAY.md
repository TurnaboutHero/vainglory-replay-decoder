# 기존 replay의041e와03f3 원시 관측

기준 `ecfe6df` 이후의 읽기 전용 조사다. 기존 [resource4/5 wire 관측](../resource_wire_2026-10-16/02_REPLAY_DETECTION.md)과 같은 H5810/C16 development 표본 및 normal17 local control만 사용했다. 같은356개 section의 SHA-256을 전부 다시 확인하고, BE float timestamp / BE u32 length를 읽는 독립 stdlib cursor로 파일 끝까지 순회했다. byte signature scan, 재동기화, 새 다운로드, 게임·서버·Ghidra 실행은 없다. 이 문서는 raw 관측이며 recording-build match 또는 accepted gameplay 결과를 주장하지 않는다.

## 전체 집계와 입력 hash

| 표본 | section 수 | strict records |041e payload22|03f3 payload750|03f3 payload746|
|---|---:|---:|---:|---:|---:|
|H5810|168|663517|43896|10|1670|
|C16|171|720282|47921|10|1700|
|normal17|17|29170|2285|1|16|

전체1412969 records에서041e 94102건,03f3 3407건이다. 해당 두 opcode에 위 표 외의 길이는 관측하지 않았다. source 파일과 ordered-section manifest SHA-256은 앞 단계02_REPLAY_DETECTION의 동일 입력이다. 이번에도 그 전체 section hash가 일치했고 framing 오류는0이다. 이 개수는 전체56-recording corpus의 새 census가 아니다.

| 표본 | 숫자순 section manifest SHA-256 |
|---|---|
|H5810|`384cbd2ec3a140e6baf60f4d8a58f0dc26b2df4347f201b7cb2eac96295495b7`|
|C16|`4f12b968a2e496ad0488a22c70046d05f648df16e0c1b0d79f2bd98f47dd94a8`|
|normal17|`9b75526ce848eb3ef98fdca1d5c55d9add513d3274fa28d53fc8f20e2ae894b0`|

manifest hash의 canonical 직렬화는 앞 단계 문서에 정의되어 있다. 단일 replay file hash 또는 실행 파일 hash와 혼동하지 않는다.

## 최초041e framing witness

아래 timestamp는 그 record의 outer header 값이다. game-time projection은 하지 않았다. payload 시작은 `record_offset+10`; content length24는 opcode2+payload22다. record SHA-256 범위는 header8을 포함한 `[offset,offset+8+content_length)`다. native `0094af20` serializer/041e receiver prefix에 따라 target BE u32+0, source raw BE u32+4, impact float32+8, BE u16+12, raw byte14와 bool input byte15를 별도 추출한다. native prefix16 뒤의6바이트는 opaque tail이다. impact operand는 raw 공격력 또는 최종 HP delta라고 이름 붙이지 않는다.

| 표본 | section / record offset | record timestamp | section SHA-256 | record SHA-256 |
|---|---|---:|---|---|
|H5810|5 / 44942|56.22051239013672|`67f298b52f9ff563ca4fdce2db351e3ba17e57e488f944738bcc69253d66e2c0`|`0eaf9a635d97bf18405e70ea25a09428af6b1610ca9fb10eb9efecfa9e32b5b2`|
|C16|6 / 43813|63.514076232910156|`403399e07f57e5fa839a6456f931e931edc3340b74586e81dcc771ee6315d5db`|`a68575a912e34e34f4229f632f1fa7a5945332c831bffc0d4447c0af9945130a`|
|normal17|4 / 24189|43.20309829711914|`9b204ae45cca774fd08a1ea2223f66b290af689e8774d63984d9e47f0a89aeb6`|`fdaed848705ca19345335f696ec990b592d97cc6ac2fe786f0da94ef90964f6a`|

## Snapshot offset 보정과 원시 관측

초기 조사에서 resource6 wire offset286을 기준으로 contiguous wire offset278/282를 추정한 것은 잘못이었다. native 배열의 연속성이 wire 필드의 연속성을 보장하지 않는다. 이 두 위치가0이었다는 이전 probe는 **resource4/5 관측으로 철회**하며 private v1에만 잘못된 가정의 기록으로 남긴다. 전체3407 snapshots를 실제 receiver assignment의 **resource4 payload+338(hex152), resource5 payload+346(hex15a)**로 다시 읽었다.

committed `native-paths.txt`의 `004d5930`은 resource array0인 local90에서 index4인 local80에 input+152, index5인 local7c에 input+15a를 쓴다. resource6 local78은 input+11e이므로 wire 배열이 연속이라는 추론의 반례다. 아래는 이 필드 연결을 적용한 현재 source bytes이며 runtime state observation은 아니다.

| 표본 | 지원03f3 수 | index4@338 positive /zero /negative | index5@346 positive /zero /negative |
|---|---:|---|---|
|H5810|1680|151 /1529 /0|0 /1680 /0|
|C16|1710|193 /1517 /0|49 /1661 /0|
|normal17|17|0 /17 /0|0 /17 /0|

모든3407개에서 gate+326 u32는0이다. 아래 비zero witness는 payload746이며 actor는 payload+8의 numeric reference다.

| ID | 표본 | section / offset | record timestamp | actor | index / wire offset | float / bits |
|---|---|---|---:|---:|---|---|
|S1|H5810|11 / 2450|110.01534271240234|1500|4 / 338|107.02127838134766 / `42d60ae5`|
|S2|C16|12 / 9046|120.01251220703125|1506|4 / 338|4.499786376953125 / `408ffe40`|
|S3|C16|9 / 10090|90.01441955566406|1507|5 / 346|821.0 / `444d4000`|

| ID | section SHA-256 | record SHA-256 |
|---|---|---|
|S1|`b36b313be9c75bdd56a5fb4910f805998ac27a70119c5ea1a0a255c96e289d4c`|`38cf1c2ca8341fb7856f3903ac0bcfbb687fa3d7f5b97694802489e77b87c7a3`|
|S2|`a2041c7933345223b0dab72c3f52e9600b277a424c64f9f5586f0883bf92ebd4`|`09d2166aa1758a77cc4d858c4c930b75cbfb2df40379367809456cd51203f19f`|
|S3|`5ad5017eef4e05027dcf96db9b969b2a462f58dacd7d217c091672aa970b4f78`|`8ce057c62f999284ce52cf3879e385b5ccb432d94484ff3955157ab929f28766`|

특히 기존 `0094e170`은 이미 존재하는 actor면 snapshot baseline 복사를 건너뛴다. payload gate0은 actor-existence guard를 제거하지 않는다. 비zero를 포함한 snapshot 필드는 baseline 후보/관측 입력이지 매번 적용되는 state SET이 아니다. 첫 actor 생성, 반복 snapshot, actor 재사용/파괴와 실제 reset을 분리한다.

## 041e raw prefix 부호와 witness

| 표본 | impact operand negative |positive |zero |
|---|---:|---:|---:|
|H5810|35192|8704|0|
|C16|36574|11347|0|
|normal17|2285|0|0|

각 표본 최초041e의 prefix는 다음과 같다. ID/operand/flags는 raw 입력이며 source reference `ffffffff`도 다른 관측에서는 실제 나타난다. 여기의 field 이름이 source actor의 존재/lookup 성공을 보증하지 않는다.

| 표본 | target raw |source raw|impact operand / bits|u16+12 /byte14 /byte15|opaque tail6|
|---|---:|---:|---|---|---|
|H5810|6903|1509|-1.0 / `bf800000`|5 /2 /0|`000000000000`|
|C16|7598|1500|-1.0 / `bf800000`|5 /2 /0|`000000000000`|
|normal17|2691|2694|-19.44444465637207 / `c19b8e39`|5 /4 /0|`000000000000`|

## 인접성 비교의 범위

041d4/5와041e가 같은 record timestamp 또는 가까운 파일 위치에 있더라도 대응하는 native producer/serializer와 actor/source/instance key가 연결되기 전에는 같은 impact의 구성원으로 묶지 않는다. 041d는 buff-instance key를 제공하지 않고, snapshot은 반복 적용 guard가 있으므로 시간 근접만으로 누락된 instance provenance를 채울 수 없다. fresh041e field proof 이후에는 동일 raw actor 참조·정확한 record order·시각차를 보고할 수 있지만, 그런 후보가 accepted resource split 또는 reset의 확정 match는 아니다.

private `impact-replay-inventory-agent.json`은 전체041e/03f3의 위치·시각·길이·section/record hash와 snapshot raw 후보를 담는다. 원본 또는 whole payload dump는 public에 싣지 않는다. 확인된041e prefix는 기존 `vg.analysis.native_event_fields.decode_fields`의 raw field case와 교차 검증했다. 누적 자원 상태, 피해 공식 또는 instance tracker를 추가하지 않았다.

## 구체적인 인접성의 반례와 한계

C16 actor1507의 index5 snapshot S3는 section9 offset10090, record time90.01441955566406에821을 담는다. 같은 actor/index의041d operand−821은 section9 offset43642,90.31916809082031이다. 그러나 그041d에 대해 record order상 가장 가까운 동일 target041e의 직전은 section8 offset117340,89.6285171508789의 **+5**(source ffffffff), 직후는 section9 offset76066,95.17888641357422의 **−68.46154022216797**(source1504)이다. 이를 −821 damage/split의 exact match로 주장할 수 없다. snapshot+821/041d−821 또한 instance key와 실제 apply 관측이 없어 reset 짝으로 확정하지 않는다.

H5810 actor1506의041d index5 +268.8863525390625(section117 offset106740)는 같은 timestamp1176.803955078125의 동일 target041e 두 개 사이에 있다: offset106644의−65.65045928955078(source1503), offset106764의−153.20584106445312(source1503). 순서와 timestamp가 같아도 어떤 callback의 결과인지, 어떤 resource split인지 정하지 않는다. 인접 두 impact 중 임의로 하나를 골라 coefficient를 맞추지 않는다.

private 비교는 모든3731개041d index4/5마다 동일 raw target actor를 가진041e의 record-order 직전/직후를 찾았다. H5810의 같은 timestamp 직전/직후 후보는29/132건, C16은92/234건, normal17은0/0건이다. 두 집합은 겹칠 수 있으며 causal pair 수나 matching accuracy가 아니다. 이 비교는 시간 창을 사후 조정한 match가 아니라 고정된 predecessor/successor 목록이다.

native `0094e970`은 serialized impact operand와 로컬 prestate를 이용해 resource4/5 split을 다시 계산한다. 따라서 별도041d가 없다는 이유로 split이 없었다고 단정하지 않는다. 반대로 인접041d를 그 impact의 split이라고 확정하지 않는다. 실제 수락된 감소량·instance 종료는 wire prefix 외의 provenance가 필요하다.

전체 snapshot/impact prefix와 neighbor 목록은 private v2 `impact-prefix-snapshot-agent.json`에 보존한다. v1 `impact-replay-inventory-agent.json`의278/282 probe는 resource 해석용으로 사용하지 않는다. source receiver assignment를 검증하지 않은 선형 offset 추정은 재사용하지 않는다.

## 전체041e field decoder 교차 검증

[OBSERVATIONS.json](OBSERVATIONS.json)은 전체356개 source section의 현재 SHA-256/크기/record 수, opcode layout/sign/raw code·byte counts, corrected snapshot338/346 counts 및 제한된 witness classes만 담는다. 전체 record 또는 payload는 담지 않는다. 독립 stdlib cursor에서 직접 구한 target/source/float bits/u16/raw byte14·15/opaque tail을 기존 `decode_fields(VGRRecord(...))`의 출력과 매041e마다 비교했다. H5810의43896건, C16의47921건, normal17의2285건, 합계94102건 모두 일치했다. source 자체를 바꾸거나 잘못된 payload를 보정한 뒤 비교하지 않았다.

추가 witness class는 최초 operand 부호, source raw ffffffff, byte15 nonzero이며 한 record가 여러 class를 대표할 수 있다. H5810의 raw byte15는0이43063건,1이833건이고 다른 두 표본은 전부0이다. 이 raw byte가 실제 최종 split을 어떻게 바꾸는지는 native consumer와 실제 apply 검증의 범위다. decoder 일치는 raw 필드 해독의 재현 증거이지 accepted split/HP/state 또는 instance reset의 검증이 아니다. 구현 source SHA-256은 JSON의 `sources_code`에 보존한다.

## Fresh native 연결 재확인

이번 단일 REA 세션의 fresh012/014 `004d5930`은 input+146(hex, decimal326)이0일 때 resource4에 대응하는 local80을 input+152(decimal338), resource5 local7c를 input+15a(decimal346)에서 읽는 것을 다시 확인했다. assembly의 정확한 read site는 `004d5d28`/`004d5d43`, selector 검사 site는 `004d5971`이다. fresh013 `0095c940`은 source resource block+2d0의16개 값을 actor stats component+2f0의16개 resource로 복사한다. 따라서 corrected snapshot offsets는 기존 요약의 추정이 아니라 같은 selected-LAA 본문으로 재확인됐다. 실제 호출 여부와 known-actor snapshot guard는 별개다.

fresh004/008 `0081b6b0`은 `ActionImpactHealth` constructor의 scalar/reference/flag 입력을 각각 보존하는 연결을 확인한다. 이 constructor와 앞서 확인한041e receiver/serializer의 native16 prefix는 observed payload22의 마지막6바이트를 임의 resource delta로 바꾸지 않는다. constructor 또는 raw decoder 연결만으로 최종 split·받은 피해·서버 실행을 검증했다고 주장하지 않는다. 이 작업에는 native game/server 실행이 없었다.

| Fresh envelope | SHA-256 | Evidence ID |
|---|---|---|
|`004-procedure_pseudo_code-0x0081b6b0.json`|`933b47a6b6e4e5ac9ac7495f638d44bede5a62c9538c8f11af376c2023e81327`|`ev_c92b743a75347fba2cd9e03f854068b3094b6b38f01dc7e73fe9b30b23f9cbdd`|
|`008-procedure_assembly-0x0081b6b0.json`|`a19330f19a43da858f335de7f7e05bf7ec6cf6a5a1061524cb4add1c467aefd3`|`ev_a56a9cfb3385eae4103d0dde35d5c947b3a048d2a0fe62c9b7faadf9210ef1e4`|
|`012-procedure_pseudo_code-0x004d5930.json`|`a78d3767b6578c26e335aea518940160e9a22ee0c5e49f2407e5f5bedd0520c9`|`ev_8815a601ff6aac4d78573f56414fb56f4228e07dfc0a85ad38131de3b5e83eb2`|
|`013-procedure_pseudo_code-0x0095c940.json`|`4ece78f6039693d3e58e770159f91078de7f53974ad14402782ca98eed6d6f1d`|`ev_da766c0263011db341a94981fe66517596826e30331087c3d0389c2cefad6d22`|
|`014-procedure_assembly-0x004d5930.json`|`b540ec47244009e5ecb0c9bf1ab6d142a6e8c5b3f0cee9a8727fc8510d065cf3`|`ev_1d4e0d9f60b1c01f7077070acec15dcd16770a2cbcd802d0cf80ec766966c9a4`|
