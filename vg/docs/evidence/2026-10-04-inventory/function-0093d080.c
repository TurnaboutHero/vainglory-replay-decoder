// 0093d080 FUN_0093d080

void FUN_0093d080(undefined4 param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,
                 undefined4 param_5,undefined4 param_6)

{
  int iVar1;
  uint uVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  uint uVar6;
  uint uVar7;
  uint uVar8;
  uint uVar9;
  
  FUN_0093cdc0(param_1,param_2,param_3,param_4,param_5,param_6);
  uVar8 = 0;
  uVar2 = 1;
  uVar9 = 0;
  do {
    uVar3 = ((int)"onGrantItem"[uVar9] + uVar2) % 0xfff1;
    uVar4 = ((int)"onGrantItem"[uVar9 + 1] + uVar3) % 0xfff1;
    uVar5 = ((int)"onGrantItem"[uVar9 + 2] + uVar4) % 0xfff1;
    uVar6 = ((int)"onGrantItem"[uVar9 + 3] + uVar5) % 0xfff1;
    uVar7 = ((int)"onGrantItem"[uVar9 + 4] + uVar6) % 0xfff1;
    iVar1 = uVar9 + 5;
    uVar9 = uVar9 + 6;
    uVar2 = ((int)"onGrantItem"[iVar1] + uVar7) % 0xfff1;
    uVar8 = ((((((uVar8 + uVar3) % 0xfff1 + uVar4) % 0xfff1 + uVar5) % 0xfff1 + uVar6) % 0xfff1 +
             uVar7) % 0xfff1 + uVar2) % 0xfff1;
  } while (uVar9 < 0xc);
  FUN_00536dd0(0,0,uVar8 << 0x10 | uVar2,param_1);
  return;
}


