# 사슬니의 기본 방어와 패시브: 선택 빌드의 증거 경계

## 식별과 입력

선택 실행 파일은 Windows x86 LAA SHA-256 `d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc`이다. 현재 설치 Data의 actor 리소스 `1DB03E986921288B174C67FEA457D5DC` SHA-256은 `046b55a3f561974874a0a39fccd1040a3664d70f393c1c5ed0347bdd7c6af7d4`이다. 기존 `native_roster_definitions.json`의 Grumpjaw 행과 같은 리소스이며, 기존 catalog의 실행 파일 hash는 별도 원본 빌드 `659f9eed557a426db57554d2a768efe34ba9fe02ba1085d77db64390b0d92642`이므로 catalog provenance와 이번 LAA 실행 파일을 혼동하지 않는다.

리소스 내부 actor 이름 `Grumpjaw`는 decoded INST `+228`, localization key `CHAR_INFO_GRUMPJAW_NAME`은 `+231`에 있다. 이름 담당자의 현재 설치 한국어 locale 검증은 resource `AE9CB5A29032FAFA098A4BBE22C79B84` SHA-256 `610d2d6a3a543a11ffa555284ddcc3ce90af2aa1b7b54afb99a6dcf98b469a5e`의 base64를 strict UTF-8로 해독하여 이 key의 값이 정확히 **사슬니**임을 확인했다. 영어 이름의 인상으로 한국어 영웅을 추정하지 않는다.

## 로컬 패시브 선언

기존 `vg.core.cff_resource.load_cff`를 사용해 위 리소스를 읽기 전용으로 해독했다. CFF version12, LAA key table VA `01e3f978`, symbol type `2419fb6c`, symbol `*Grumpjaw*`, INST 길이32360이다. root는0이며 root `+1a8` relocation은 property pointer table `7d7c`를 가리킨다. 다음 값은 각 property entry의 `+4` float32 선언이다. 실제 로드된 런타임 값이나 callback 실행 관찰은 아니다.

| index | 선언명 | entry INST offset | float32 값 |
|---:|---|---|---:|
|0|MAX_STACKS|7d90|5|
|1|ARMOR_CHARGE_TIME|7dbc|3|
|2|INCOMING_DAMAGE_REDUCTION|7df0|0.07000000029802322|
|3|ARMOR_REMOVE_COOLDOWN|7e2c|1|

`ARMOR`라는 두 property 이름만으로 armor/shield attribute 증가를 주장하지 않는다. 특히 index2는 incoming damage reduction이라는 별도 선언이다. 과거 패치 설명의 숫자를 현재 리소스의0.07 대신 넣지 않는다. 아래 fresh provider가 `1-0.07*n`을 지지하지만, 적용 피해 종류와 stack 변화 조건·시점은 별도 callback 실행 근거가 필요하다.

## 기본 방어와 레벨 증가

fresh024 `00944de0`은 actor ECX의 정의 `actor+1c`를 읽고 `new_level-1`을 사용한다. `0095c710(7,0, definition[+b0]*(L-1)+definition[+ac], actorID,1)`와 `0095c710(8,0, definition[+b8]*(L-1)+definition[+b4], actorID,1)`가 명시되어 있다. fresh070 `007d1410`은 attribute7을 `STORE_ITEM_ATTR_ARMOR`,8을 `STORE_ITEM_ATTR_SHIELDING`으로 연결한다. 따라서 이번 로컬 정의의 armor base30/growth5 및 shielding base20/growth float32 `3.63700008392334`를 필드와 연결할 수 있다.

| 레벨 L | armor base-layer 계산 | shielding base-layer 계산(소수 셋째 자리) |
|---:|---:|---:|
|1|30|20.000|
|6|55|38.185|
|12|85|60.007|

이는 위 정의를 로드하고 해당 레벨 재계산이 실행된 뒤의 **base layer** 조건부 표다. shielding은 보호막 resource4가 아니라 마법 방어 attribute8이다. 실제 effective defense는 다른 세 layer와 modifier, callback 및 snapshot/상태의 영향을 받으므로 표를 그대로 최종 방어라고 부르지 않는다. 일반 합성형 `((layer3+1)*layer1+base)*(layer2+1)`과 consumer별 bounds를 적용해야 하며, 방어 아이템·target shred는 해당 layer에서 별도로 반영한다. 표는 소수 표시용 반올림이며 모든 native 중간 연산의 bitwise 재현을 주장하지 않는다.

기존 [XP_HERO_LEVELS.md](../re_dictionary/progression_rewards/XP_HERO_LEVELS.md) 제2절과 fresh024가 함께 LEVEL attribute40의 네 layer 합성, 상한12, 상한 미만 delta0 재계산 가능성을 확인한다. 여기의1/6/12는 비교 입력이지 모든 recording의 시작 레벨을 선언한 것이 아니다.

## 패시브 provider와 선택 클라이언트의 stub 경계

추가 검증: [provider 전달 단계 정정](../damage_order_2026-10-16/REPORT.md). 아래 "지정"은 인자로 전달하려는 구성 의도를 뜻한다. 실제 `virtual+14`는 인자를 무시하는 stub이므로 이 선택 객체에 provider가 저장되었다는 뜻이 아니다.

fresh023 `008e5b60`은 등록된 `Buff_Grumpjaw_Perk_Armor` factory이다. buff+248에 `0095a340`,+244에 `00868d70`을 설정하고, `008102e0`으로 만든 callback들에 조건 비트와 behavior 목록을 붙인다. `00530ad0`이 만드는 behavior에는 provider `008423f0`를 지정한다. 이 factory가 여기서 armor/shield attribute7/8의 증가를 직접 setter에 쓰는 본문은 아니다.

fresh063 `008423f0`은 context가 가리키는 buff의 unsigned16 count `+250`과 owner actor 정의 `+1a8`의 property index2를 읽어 **`1 - property2 * count`**를 반환한다. 이 property가 위의 로컬0.07이면 다음 provider 값이 나온다. 이는 누적 곱 `(1-.07)^n`이 아니다.

| passive count n | provider 반환값(표시용) |
|---:|---:|
|0|1.00|
|1|0.93|
|2|0.86|
|3|0.79|
|4|0.72|
|5|0.65|

독립 stdlib PE mapping 읽기는 위 EXE hash를 먼저 확인한 뒤 constructor vtable immediate와 RTTI를 연결했다. `008102e0`의 vtable `0127b9cc` RTTI는 `BuffCallback_Combat`; 선택 nonstub slot은 `+1c→00947cb0`, `+20→004a8190`, `+34→004b7310`이다. `00530ad0`의 vtable `0121b690` RTTI는 `BuffBehavior_MultiplyDamage`; `+20→00459660`이다. 이 이름 연결은 원본 PE의 file-backed section VA mapping과 complete-object locator/type descriptor에서 읽었으며 실행 관측은 아니다. fresh103은 `00459660`이 this를 반환하는 accessor일 뿐 damage를 쓰지 않음을 확인한다. fresh104의 `004b7310`도 빈 본문이다. RTTI의 class 이름만으로 피해 변경 실행을 주장할 수 없다.

provider 자체에는 local mode guard나0..1 clamp가 보이지 않는다. 따라서 이 표는 유효한 property pointer와 관측 count0..5의 provider 반환값이다. fresh102 `00947cb0`은 filter `0095fa10`이 통과하면 context를 만들고 behavior 목록의 virtual `+4`를 호출하지만, 위 MultiplyDamage vtable의 `+4`는 빈 공통 함수 `0045ecd0`다. fresh101은 이 함수가 빈 본문임을 확인한다. 현재 선택 클라이언트의 이 dispatch에서 provider를 호출해 damage field에 곱하는 동작은 닫히지 않으며, 해당 branch는 stub로 연결된다. 모든 피해에 항상35% 감소나 실제 서버 피해를 수치로 확정하지 않는다.

fresh064 `008423d0`은 `max(u16count-1,0)`을 반환한다. fresh065 `00866ef0`은 actor definition property index3를 반환하므로 위 리소스에서는1이며, fresh066 `0086b540`은 mode `0209e204!=0`일 때 property index1을 output에 쓰므로 위 리소스에서는3이다. mode0에서는 그 output을 이 본문이 갱신하지 않는다. fresh061 `0095a340`과 assembly075는 property index0 entry의 `+4` float를 XMM0으로 `011b8a40`에 전달하고 반환값과 현재 u16count를 unsigned 비교함을 연결한다. 따라서 유효한 로컬 MAX_STACKS5의 변환 결과를 전제로 current count가5 미만인지 검사하는 eligibility 경로다. 누락된 property pointer에 대한 안전 동작이나 다른 비정상 float 변환까지 일반화하지 않는다. fresh062 `00868d70`은 buff+24c bit4가 켜졌으면1, 아니면 `1 - buff[+22c]/buff[+230]`을 반환한다. UI/기간 provider의 가능성은 있어도 이 반환식을 피해 multiplier와 동일시하지 않는다.

factory는 Armor와 CooldownCheck 이름을 쓰는 stack-change/apply graph도 구성한다. provider 계산, callback 조건 통과, queued action 생성, accepted stack mutation은 별개의 단계다. 충전3초/제거 cooldown1이라는 선언이 있다는 것과 모든3초/매피격마다 실제 stack이 바뀐다는 것은 같지 않다. 정확한 trigger·guard와 action body를 확인해야 한다.


`0095fa10`(fresh106)은 callback+28 event bitmask, +40 source/target ID selector, +38 damage-kind bitmask, required/excluded flag masks 및 선택 조건 provider를 검사한다. 첫 factory callback은 +28에0x20,+40에2를 넣으므로 대응 event index5와 context target ID 대조가 요구된다. 숫자5의 외부 event 의미는 별도 caller에서 연결해야 한다. 다른 두 callback은0x40 event bit를 쓴다. 이 필터 본문에는 최종 HP write가 없다. callback이 통과했다는 사실도 이 MultiplyDamage behavior의 stub를 실제 피해 연산으로 바꾸지 않는다.

반증·다음 측정은 구체적이다. 동일 hash의 실제 dispatch가 다른 virtual slot 또는 독립 damage-field consumer로 provider를 평가한다는 경로, 또는 서버 구현/빌드 일치 관측에서 해당 factor가 실제 damage operand에 반영된다는 증거가 필요하다. 클라이언트 stub만으로 서버에도 패시브가 없다고 결론 내리지 않는다. 반대로 asset 설명과 class 이름만으로 서버의 정확한 계산 순서를 채우지 않는다.

## Bonesaw0/최대 stack과 대상 방어의 조건부 비교

기존 [05_NAMED_STACKS.md](../sequential_rea_2026-10-16/05_NAMED_STACKS.md)의 Bonesaw target debuff factory는 `008edcc0`과 `00812280`을 통해 attribute7/layer2의 stack delta를 음의 SHRED property에 연결한다. 현재 로컬 Bonesaw는 SHRED float32 약0.1, target debuff cap5다. 따라서 **다른 세 layer가 기본값이고, 해당 debuff가 수락되어 layer2에 stack당 약−0.1만 들어간 경우** target의 armor는0stack 대비5stack에서 약절반이 된다. 이는 공격자의 armor penetration과 별개다. 수치는 표시용 십진 반올림이며 delta마다 float32로 누적되는 마지막 bit를 보증하지 않는다.

| 사슬니 레벨 | Bonesaw target stack0: armor | target stack5: armor(근사) | 사슬니 passive stack0 provider | passive stack5 provider |
|---:|---:|---:|---:|---:|
|1|30|15|1.00|0.65|
|6|55|27.5|1.00|0.65|
|12|85|42.5|1.00|0.65|

이 표의 passive provider 열은 armor에 더하지 않는다. passive count가 방어력 base/growth를 바꾼다고 전제하지 않았으며, 선택 local dispatch의 stub 경계가 있으므로 위 provider를 최종 HP damage에 바로 곱하지 않는다. 일반 공격에 Bonesaw qualifying callback이 발생하는 것과 그 공격의 피해 계산 전에 새 shred가 적용되는 것은 다르다. 공격 직전 이미 수락된0/5stack을 입력으로 삼아 비교해야 하며, 첫 공격부터 최대 shred라고 가정하지 않는다. shielding은 armor shred 표의 대상이 아니다.

## 비교 실험의 고정 조건

기본 성장식과 provider 반환식은 확인했지만 실제 mitigation/서버 실행 연결을 대신하는 효과 수치 비교 utility는 추가하지 않는다. 후속 비교는 같은 raw physical damage와 공격자 stats, 같은 대상 레벨/기본 armor/방어 아이템을 고정하고 사슬니 passive stack0..5와 Bonesaw target debuff stack0..5를 별도 축으로 둔다. Bonesaw가 대상에 쓰는 shred와 공격자가 가진 penetration을 합쳐 한 armor 수치 변화로 부르지 않는다. 공격자 아이템을 바꾸는 비교는 공격력/raw damage, 비용과 사용 slot을 함께 맞추거나 그 차이를 명시해야 한다. 동일 raw damage 비교는 전투 빌드 전체 DPS 우열을 뜻하지 않는다.

관측해야 할 값은 공격 전 target armor/shield의 effective 값과 각 modifier layer, passive instance/count, Bonesaw target debuff instance/count, 공격자 penetration, damage type/flags, passive callback 전후 damage, mitigation 후 resource write이다. target debuff 적용과 passive stack 소모의 선후관계도 필요하다. local queue 생성, callback 조건 통과, accepted mutation, 실제 HP 감소를 구분한다. 독립 replay 또는 서버 실행 관측은 아직 없으며 이 문서는 production reducer를 변경하지 않는다.

## Fresh native receipts

부모의 단일 직렬 REA 세션이 얻은 complete JSON envelope의 hash/evidence ID다. raw decompiler 출력은 task-private에 남긴다.

| Export | SHA-256 | Evidence ID |
|---|---|---|
| `023-procedure_pseudo_code-0x008e5b60.json` | `c02d031baa544ed7e2a9e033a022845c9e27c577b6cf91376f18b55f1f4c19ce` | `ev_7ff1af22a25f17b3719853ca949a4426f1ff041e32d73d6a38f2c08b35afcef8` |
| `024-procedure_pseudo_code-0x00944de0.json` | `2d837fee69fd5fc25450e58e79e5dd7a8c7e0d7e5c654a416ea100018af831d6` | `ev_c9cb43b5e81f834390631003315fb86efa843c69269b265570bf63b196f06109` |
| `061-procedure_pseudo_code-0x0095a340.json` | `9aab252b4d20af3153ab08b5fd380ebcb0eb7d83841e1774a80d7400632689d0` | `ev_71217afd34f7d662cbb409a2fc40cb119c11c07362927e3712b9baddffa2393e` |
| `062-procedure_pseudo_code-0x00868d70.json` | `1e96e60ff5c16892e3e512ff19f72bad7282fca83c043bb3ea5bbd7bd17be882` | `ev_bf4a884a0eb9e279a166540ab299b07ca7484ad4b89c999c6d98f6b32fab172f` |
| `063-procedure_pseudo_code-0x008423f0.json` | `7f360e6b7dcbb4899d9c851aa4198144da9277140153b76601b8d58eb4517732` | `ev_9d6b47ab586b81563f7b22ba47a600a936ed36e8c2f0932cac964d2edc07d741` |
| `064-procedure_pseudo_code-0x008423d0.json` | `ee8ba5f51e581569237ad0e797db9096b9bc96d906abab255a7ef5f76ec03ccb` | `ev_5e91916f74cc4598e5ff87c6699e62735404ab825e97441264ee2ddcdbfba219` |
| `065-procedure_pseudo_code-0x00866ef0.json` | `e9375437111e745868c662e13ecb785c839275c388c6c9e8b4c09dceb7d37c61` | `ev_3c3d9b3e13a65d32635d49fb8de632e007bcfb9185c8e791510c22a62169a7a9` |
| `066-procedure_pseudo_code-0x0086b540.json` | `0927c28fa82d054592f26e102e212204c6230dcdad1f0e4ef0f9ceef056921e9` | `ev_5b6d6aeb2fec5d05300004a843229f4781390668cb1e2ee5639dc1c96ed660d9` |
| `070-procedure_pseudo_code-0x007d1410.json` | `2cd94d540e4e7778a4837e0d6c3157d628bb6e1ba0e3a8705b614e8f896aa7fd` | `ev_a696135185576615d71b9dd276e277a52ddeb2d31866aa70351aaa4b55ee7b7c` |
| `075-procedure_assembly-0x0095a340.json` | `76137c370e2f17268c0d61ef11f2bcd8d608697e8621b42d3802b72dc0569ea4` | `ev_3e5362d28d79bda141851abf8cea52f37b574220311a90c87b252e986ff4d59b` |
| `093-procedure_assembly-0x008102e0.json` | `48fc6130939aa8bf3647deed9828fc37996c2e272041b2a80343a92ae24873e1` | `ev_2e9205b0dbacaa47e5dbb26b566ad4da3ffe7ea03997751c24e44bd2b0eb8a7d` |
| `094-procedure_assembly-0x00530ad0.json` | `65f54f18826407698b224e16b361d8f2eb894c243ebe89e95cd7c91805f83208` | `ev_a9b041d98a8106169c8108873ba205201d98dc43157ff240bb99c7efce6e166a` |
| `100-procedure_pseudo_code-0x4a8190.json` | `44a5ff17fb9446ea591cb3a03b1695a2ba270671fc4c424745829d43303695d3` | `ev_311213a5fcdd193bce340f04a7784514dac2057c863ee224488104c4f95fcc58` |
| `101-procedure_pseudo_code-0x45ecd0.json` | `d953e32658f7c4b09957550bf495447930086a67d6ba435d8aec3ca621969c05` | `ev_c987e1f6d155199803b8c1d0b8f334af330b386065280380f6b0d966cc30a035` |
| `102-procedure_pseudo_code-0x00947cb0.json` | `7638a2bf18184ca2e2a12392bd86761df07b9b2ea8182f0487a93aede18c55f4` | `ev_f6d3dba89517e18d6da5854153ca8a0d23e8722d2257ce307cff0d25ce09ec21` |
| `103-procedure_pseudo_code-0x00459660.json` | `0860fba9ecd50709a3946695e3def37c4da14f4769d49e7aa1f1967eff2c427b` | `ev_23bbbbf2e49403c54e312d0188b2433269ff241efa99a1dfffdfc7411f447fd0` |
| `104-procedure_pseudo_code-0x004b7310.json` | `ac2f1fc433a66ed5fb447ac8367ebf1c80a1927d3bf2f345c7a3b9d909b1d5c8` | `ev_bde934a5902ffcb5fcaf06c3e5ff0aa380d0a6b237088b8067848115ee48c712` |
| `106-procedure_pseudo_code-0x0095fa10.json` | `617e28ea2f15d0ac49f52061b9b7ed78028fb0e800bfc747793fe2f3f84f38bd` | `ev_cb43851babbf37a84896de55706327d5324168e2b236c0e8842fa5334b36096f` |
