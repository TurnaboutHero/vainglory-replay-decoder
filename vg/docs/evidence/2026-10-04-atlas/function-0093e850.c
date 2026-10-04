// 0093e850 FUN_0093e850

void __thiscall
FUN_0093e850(int param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,undefined4 param_5
            )

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uVar7;
  uint uVar8;
  
  FUN_0093e940(param_2,param_3,param_4,param_5,0);
  if (*(int *)(param_1 + 0x30) != 0) {
    FUN_0086f1e0(PTR_s_onActorAttributesChangedName_01a73048,param_2,param_3,&param_4);
  }
  uVar8 = 0;
  uVar2 = 1;
  uVar7 = 0;
  do {
    uVar3 = ((int)"onActorAttributesChanged"[uVar7] + uVar2) % 0xfff1;
    uVar4 = ((int)"onActorAttributesChanged"[uVar7 + 1] + uVar3) % 0xfff1;
    uVar5 = ((int)"onActorAttributesChanged"[uVar7 + 2] + uVar4) % 0xfff1;
    uVar6 = ((int)"onActorAttributesChanged"[uVar7 + 3] + uVar5) % 0xfff1;
    iVar1 = uVar7 + 4;
    uVar7 = uVar7 + 5;
    uVar2 = ((int)"onActorAttributesChanged"[iVar1] + uVar6) % 0xfff1;
    uVar8 = (((((uVar8 + uVar3) % 0xfff1 + uVar4) % 0xfff1 + uVar5) % 0xfff1 + uVar6) % 0xfff1 +
            uVar2) % 0xfff1;
  } while (uVar7 < 0x19);
  FUN_00539400(0,0,uVar8 << 0x10 | uVar2);
  return;
}


