# Concrete item definition → cooldown key: Fountain of Renewal

## Result and correction

The locally available matched Data resources are sufficient for one concrete mapping. The earlier identity report's statement that definition values were unavailable must be narrowed: no generic all-ability/lifecycle mapping has been validated, but the Fountain of Renewal example below is now independently decoded and corroborated in H5810. This is an additive follow-up; the prior bundle remains unchanged.

Definition 487, `*Item_FountainOfRenewal*`, selects embedded ability `Ability__Item__FountainOfRenewal`. Its primary cooldown key is **0x6f056481 (1862624385)**. H5810 contains 133 `048a` observations for owner 1500 and 73 for owner 1501 with that key. This selected key has no `0428` observation in this corpus. No `0429` slot mapping or runtime successful application is established.

## Definition proof, not a numeric or temporal guess

1. The actual executable SHA256 is d6717c157f1608c896255a4bc9290a819d428f1f6d9fb1605c65ebb8e6f620cc. This is the analyzed LAA-flag variant. The already-established PE32 resource profile is used explicitly: key table VA 01e3f978, version 12, architecture 0. No product supported-build allowlist is changed.
2. The complete definition manifest `03A640B504C2B4D7C8CBF3A04E189223`, SHA256 7292b885378be83cb8596601bad7d0c7adfaab1e91e23f8ea65601f03136755c, decodes under the repository's checked CFF loader. Index 487 resolves to `*Item_FountainOfRenewal*` among the profile's 932 entries.
3. Item resource `3A4A448F2A4B2A65D84997E8DBC3784A`, SHA256 4f367432f83f947b6446c2f083d0d1de81d0c6ab678bfe3202140088cdb32c37, has matching symbol name, item type 0xfc7583e1 and root 0. Its active byte +38 is 1, external-ability reference +3c points to an empty string. The independently inspected 0096c770 is a NULL-or-empty predicate. Thus 00940230 takes its embedded definition at itemDefinition+40 and invokes 0093f270 with overrideName=0.
4. Embedded ability+4 resolves to `Ability__Item__FountainOfRenewal`; +18 cooldown group resolves to an empty string; +6a is zero. Empty group hashes to 0x811c9dc5, which equals the image-backed global 01ab9cb8. Therefore 0093f378–3bd selects the definition+4 name fallback. No unknown runtime value of global 020ea218 is needed for this branch.
5. The primary-state existence gate is also satisfied. Ability+8c is a property-pointer array with the property named `Cooldown`, whose +4 float is 75.0. 00933350 finds the named property and 0093cbc0 returns its entry. 0093f2f5–335 checks this property's +4/+8/+1c/+c floats, and the positive +4 routes to state lookup/creation. The image literal at 01227384 is `Cooldown`. This confirms a path to +124 assignment rather than merely hashing a dormant name.
6. Signed-byte FNV-1a over the ASCII ability name gives 0x6f056481. The same initializer searches the actor-owned cooldown list by that key and stores the selected pointer at ability+124. Those structural receipts accompany this report.

## Independent raw-record corroboration

H5810 section 34, offset 109574, record timestamp 346.0756530761719: `043d`, content length 16, payload `000005dc000001e7000007d70000` → owner 1500, item definition 487, instance 2007.

Section 35, offset 3206, timestamp 350.00958251953125: `048a`, content length 24, payload `000005dc6f0564810000000042960000010102000000` → owner 1500, derived key 0x6f056481, configuration float bits 0x42960000 (75.0).

The second independently addressed owner has `043d` in section 94, offset 54898, owner 1501, definition 487, instance 2015; its first matching `048a` is section 95, offset 4474, again key 0x6f056481 and configuration 75.0. Full locators, payloads and all 168 source section hashes are in example.json. Record timestamps are reported as encoded; they are not promoted to validated displayed game time.

The key derives from actual decoded resource fields and native branches. The subsequent record agreement corroborates it; temporal proximity alone does not establish the join. The grant instance is retained separately from the cooldown key. These observations do not prove permanent lifetime, uniqueness among all possible definitions, absence of overrides elsewhere, or successful action execution.

## Reproduction

From the workspace, run:

    python -B reproduce_example.py --repo /path/to/vainglory-replay-decoder --app /path/to/app --replay-dir /path/to/H5810 > /path/to/reproduced-example.json

The script verifies exact executable/manifest/item hashes, checks CFF envelopes and relocations using existing repository code, asserts the observed fields and property gate, derives the key, and scans framed raw records. It additionally asserts exact recorded payload/content lengths, expected owner/key counts, grant/sync locators, configuration bits and all 168 source hashes against the bundled historical example.json. It only reads input files. Do not redirect output over that bundled baseline. Raw executable/resource data and decryption key bytes are not bundled.

The required repository modules are vg/core/cff_resource.py, definition_catalog.py, entity_definition.py and vgr_records.py. Their source hashes are recorded in source-code-hashes.json. Ghidra receipts were produced with Ghidra 12.1.3 and JDK 21; calling conventions in C output are imperfect, so validate the included instructions. The 0096c770 receipt is GNU objdump output.

## Safe next boundary

A build-profile-specific definition-to-key evidence entry for this example is supportable. A generic resolver should first validate further embedded and external definitions, group fallback modes, custom overrides, ordered actor ability slots and lifecycle/cleanup. This evidence does not remove the separate timer/frame-boundary blocker, and it does not justify enabling a cooldown state reducer. No product code, repository changes, remote updates or client execution occurred in this follow-up.

## Publication validation

The hardened checker reproduced example.json exactly. An independent bounded item-catalog review decoded 93 item resources: 32 active embedded definitions, 59 inactive items and two external-reference items. Within those 32 embedded names/group strings only Fountain matched this key. External targets, non-item abilities and runtime overrides were not covered; this is not a global uniqueness claim. That separate collision census is contextual review, not a result regenerated by reproduce_example.py.
