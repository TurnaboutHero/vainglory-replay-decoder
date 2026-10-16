# 5. Named item buffs, stack state and duration

Starting point: dictionary buff-lifetime entries and buff_status/lifecycle-additions.json.
Reuse generic creation/reapply/removal evidence; selected native043e/043f lengths
still do not certify historical extended layouts. No new stack reducer is enabled.

## Names and registry, with independent bounded reproduction

Fresh REA string references identify name globals; exact A1-name-load/A3-entry-store
sequences in0044b569/0044b587/0044b6b3/0044b6db/0044b6e5 and immutable entry+4
words map Buff_Item_Bonesaw→008edc70, BonesawDebuff→008edcc0,
Bonesaw_Pen→008edd90, DragonsEye_Control→008eefb0 and
DragonsEye_CrystalBonus→008ef000. verify_sequential_pe checks these exact bounded
sequences and factory words. The registry/name initializers lack Ghidra function
bodies, so pseudocode queries there/data pointers failed; their bytes were read,
not silently treated as decompiled functions. Duplicate/interior queries are
not counted as new functions. Factory callback/constant bodies corroborate names.

## Bonesaw

008edc70 registers onAfterApplyDamage→0083aa30. The callback requires combat+0c
match the parent owner ID and combat+8 bit2. It selects Item_Bonesaw property2
(selector1) and queues0081a060 with owner,target,Buff_Item_BonesawDebuff,duration,
new instance and stack operand1. This is conditional queued application, not
successful damage/recipient certainty inferred merely from event naming.

008edcc0 registers onTimeout→00824ec0, includes RefreshDuration behavior00812b50,
and adds ModifyAttrPerStackDelta00812280 for attribute7/layer2 with negated
Item_Bonesaw property1. At timeout with stacks>1,00824ec0 clears flag10,
writes remaining/initial duration .5 and requests old-stacks-1 through0095f4d0.
The generic final removal/refresh rules still apply; it is not an unconditional
all-stacks reset or demonstrated live cadence. Bonesaw_Pen instead uses a
lifetime attribute9/layer1 provider00868f90 = Bonesaw property0 minus PiercingSpear
property0. This separate penetration declaration is not the debuff stack count.

## Dragon's Eye

008eefb0's lifetime list declares applying CrystalBonus.008ef000 writes interval
operand .2, invokes009604f0(stackRate1,decayTime=property1,stackOnDefend0,
decayAll0,falloff=trunc(property2)), and adds per-stack attribute5/layer1 using
property0.008ef000 assembly supplies the arguments omitted by decompilation.
009604f0 registers pre-damage0084b240 and interval0084b370, initializes last-damage
clock to current-.1 and last-stack clock to current, and stores those settings.

0084b240 excludes combat bit4, checks owner source versus eligible target and
optionally owner defender.00944110 permits direct hero flag1 or a recursively
linked, generation-valid actor unless exclusion bit19 is set. Qualifying
pre-calculation updates lastDamageExchange from00548880; it does not certify
successful applied damage, universal hostile-enemy credit or every summon.

Under0209e204!=0,0084b370 requires now>=lastStack+rate. If lastDamage>=lastStack
and current<cap it queues current+1; otherwise decay requires now>lastDamage+decay
and current>0, then chooses zero or max(current-falloff,0). It updates lastStack
after enqueue. Each selected call queues one adjustment, not catch-up loops
for every missed interval. Assembly recovers inline action vtable0127c9f0,
owner ID, buff instance+220, absolute count and mode byte1;0092ea80 forwards it.

Action apply0094f440 resolves owner, finds matching buff instance+220, rejects
nonzero+224, and calls0093be10 with action ECX and buff manager argument.
Mode byte+1c nonzero uses absolute action+18; zero adds existing low16 stacks
with a nonnegative bound. It then invokes0095f4d0 and selected remove-if-zero.
The setter bounds against high16 cap at+250, stores low16 current, and when
notify is set and count changes dispatches virtual+c delta hooks, script+4c and
onStacksChanged. ModifyAttrPerStackDelta's vtable+c=00861530 sign-extends the
27-bit delta atbuff+258, multiplies its coefficient, and (mode nonzero) queues
attribute action0127c9a0→0092e8e0. Its apply0094f1d0 separately resolves actor
and chooses SET/ADD helpers. Queueing is distinct from observed stat application.

## Separate buff-definition cap bridge

inspect_stack_items reproduces ITEM_DECLARATIONS.json from four hash-pinned local
CFF resources, checking executable/resource hashes, symbols and relocations.
00939570 confirms selector1 reads selected property+4. Item declarations:
Bonesaw ARMOR_PEN .2,SHRED .1,DURATION3,MAX5; PiercingSpear ARMOR_PEN .1;
Dragon BONUS_CRYSTAL10,AMP_DURATION5,FALLOFF_PER_SEC3,MAX_STACKS15.
Values retain exact binary32 bits. These are local declarations, not inventory
quantity or observed runtime values.

The independent *KindredBuffs* resource551BCB541D80053BACD0A897B7993A77,
SHA256 e1a2478259c48bf69dfab706cd364915614d0ce212a292f34487834c3156bd79,
has symbol type69bb0cf9 and 1381 definitions. The bounded relocated table gives
index265 BonesawDebuff cap5 and337 DragonsEye_CrystalBonus cap15 at definition+24;
264 Bonesaw,332 Bonesaw_Pen and336 DragonsEye_Control each declare cap1.
Thus matching item MAX numbers are corroboration, not the source of runtime cap.

0094c9a0 resolves the action definition index through KindredBuffs, then generic
apply008659c0/00863050 chooses reuse or creation. Fresh00863050 also exposes
reapplication: stage input is bounded by existing+252 into+254, callbacks run,
and current+staged goes through0095f4d0. Decompilation mis-recovers allocation
return variables in its creation branch; no NULL-object writes are inferred.
Fresh008cef70 assembly at008ceff9 reads definition+24, at008cefff writes buff+252,
and at008cf009 stores bounded initial input into+254 before factory setup.
Together these close the selected-build static definition-to-cap bridge5/15.
Actual loaded resource pairing, overrides, lifecycle and runtime state still
require a matched-build trace. The historical replay layout is not certified.

## Counterexamples and next measurement

Inventory max_stack1 can coexist with many buff stacks. A queued adjustment can
be dropped for a missing/ending instance. A pre-calculated exchange can qualify
without successful damage. A large clock gap does not imply multiple catch-up
stacks from one interval callback. Zero historicaltimer or matching buff name is
not validated state. No native/game/server execution or independent holdout.
Next matched-build trace must bind inventory instance→owner/ability→buff definition/
instance/generation, capacity source, current stacks, last damage/last stack clocks,
flags, queued absolute action and resulting attribute. Vary sustained qualifying
combat,pre-calculation without damage,withdrawal,death,item sale/rebuy and duplicate
items; reject lifecycle changes. Trace actual loaded definition+24 and cap+252 to falsify the static local-resource
pairing; interval scheduling and historical message build remain open.
