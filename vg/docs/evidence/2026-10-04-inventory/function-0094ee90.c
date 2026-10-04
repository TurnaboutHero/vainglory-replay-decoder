// 0094ee90 FUN_0094ee90

void __fastcall FUN_0094ee90(int param_1)

{
  byte bVar1;
  int iVar2;
  int *piVar3;
  int iVar4;
  uint uVar5;
  uint uVar6;
  uint uVar7;
  int *piVar8;
  uint uVar9;
  int local_10;
  undefined4 local_c;
  int local_8;
  
  if (DAT_0209e204 != '\0') {
    return;
  }
  local_8 = param_1;
  iVar2 = FUN_00857970(*(undefined4 *)(param_1 + 0x10));
  iVar2 = *(int *)(iVar2 + 0xc);
  if (iVar2 == 0) {
    return;
  }
  while (*(int *)(*(int *)(iVar2 + 4) + 0x54) != DAT_02093f14) {
    iVar2 = *(int *)(iVar2 + 0x10);
    if (iVar2 == 0) {
      return;
    }
  }
  bVar1 = *(byte *)(iVar2 + 0x71);
  uVar7 = 0;
  uVar5 = bVar1 & 0x7f;
  if ((bVar1 & 0x7f) == 0) {
    return;
  }
  piVar8 = (int *)(iVar2 + 0x1c);
  do {
    if (*piVar8 != 0) {
      iVar4 = *(int *)(local_8 + 0x14);
      piVar3 = (int *)(iVar2 + 0x1c);
      if (*(int *)(*piVar8 + 0x30) == iVar4) {
        iVar2 = *(int *)(local_8 + 0x24);
        if (iVar2 == 0) {
          local_c = *(undefined4 *)(local_8 + 0x18);
          uVar7 = 0;
          if ((bVar1 & 0x7f) != 0) break;
          goto LAB_0094f003;
        }
        if (iVar2 == 1) {
          uVar7 = 0;
          if ((bVar1 & 0x7f) != 0) goto LAB_0094ef70;
          goto LAB_0094ef83;
        }
        if (iVar2 != 2) goto LAB_0094f0b5;
        uVar7 = 0;
        if ((bVar1 & 0x7f) != 0) goto LAB_0094ef37;
        goto LAB_0094ef4a;
      }
    }
    uVar7 = uVar7 + 1;
    piVar8 = piVar8 + 1;
    if (uVar5 <= uVar7) {
      return;
    }
  } while( true );
  while( true ) {
    uVar7 = uVar7 + 1;
    piVar3 = piVar3 + 1;
    if (uVar5 <= uVar7) break;
    iVar2 = *piVar3;
    if ((iVar2 != 0) && (*(int *)(iVar2 + 0x30) == iVar4)) goto LAB_0094f005;
  }
LAB_0094f003:
  iVar2 = 0;
LAB_0094f005:
  FUN_00963200(iVar4);
  iVar4 = *(int *)(*(int *)(*(int *)(iVar2 + 0x18) + 0x1c) + 0x60);
  if (((((iVar4 != 2) && (iVar4 != 1)) && (iVar4 != 0)) && (iVar4 != 4)) ||
     (iVar4 = FUN_00857970(local_c), iVar4 == 0)) goto LAB_0094f0b5;
  local_10 = iVar4 + 0x14;
  if (local_10 == 0) {
    local_10 = 0;
    local_c = DAT_020ec6fc;
  }
  else {
    local_c = *(undefined4 *)(iVar4 + 0x18);
  }
  FUN_0095f600(&local_10);
  goto LAB_0094f064;
  while( true ) {
    uVar7 = uVar7 + 1;
    piVar3 = piVar3 + 1;
    if (uVar5 <= uVar7) break;
LAB_0094ef37:
    iVar2 = *piVar3;
    if ((iVar2 != 0) && (*(int *)(iVar2 + 0x30) == iVar4)) goto LAB_0094ef4c;
  }
LAB_0094ef4a:
  iVar2 = 0;
LAB_0094ef4c:
  FUN_00963200(iVar4);
  iVar2 = *(int *)(iVar2 + 0x18);
  if (*(int *)(*(int *)(iVar2 + 0x1c) + 0x60) != 4) goto LAB_0094f0b5;
  goto LAB_0094f067;
  while( true ) {
    uVar7 = uVar7 + 1;
    piVar3 = piVar3 + 1;
    if (uVar5 <= uVar7) break;
LAB_0094ef70:
    iVar2 = *piVar3;
    if ((iVar2 != 0) && (*(int *)(iVar2 + 0x30) == iVar4)) goto LAB_0094ef85;
  }
LAB_0094ef83:
  iVar2 = 0;
LAB_0094ef85:
  FUN_00963200(iVar4);
  iVar4 = *(int *)(iVar2 + 0x18);
  if (*(int *)(*(int *)(iVar4 + 0x1c) + 0x60) != 3) goto LAB_0094f0b5;
  local_c = *(undefined4 *)(local_8 + 0x20);
  *(ulonglong *)(iVar4 + 0x110) = (ulonglong)*(uint *)(local_8 + 0x1c);
  *(undefined4 *)(iVar4 + 0x118) = local_c;
  *(uint *)(iVar4 + 0x154) = *(uint *)(iVar4 + 0x154) & 0xffffffd7 | 0x10;
LAB_0094f064:
  iVar2 = *(int *)(iVar2 + 0x18);
LAB_0094f067:
  uVar5 = *(uint *)(iVar2 + 0x38) & 0x1f;
  if (uVar5 == 0x1f) {
LAB_0094f097:
    FUN_00563a30(1,0,0);
  }
  else if (*(short *)(uVar5 * 0x20 + 8 + iVar2 + 0x38) != 1) {
    if ((uVar5 != 0x1f) && (*(short *)(uVar5 * 0x20 + 8 + iVar2 + 0x38) == 2)) {
      FUN_008708a0();
    }
    goto LAB_0094f097;
  }
  FUN_00563a30(2,0,0);
LAB_0094f0b5:
  uVar7 = 0;
  uVar5 = 1;
  uVar9 = 0;
  do {
    uVar6 = ((int)"onPlayAbility"[uVar9] + uVar5) % 0xfff1;
    iVar2 = uVar9 + 1;
    uVar9 = uVar9 + 2;
    uVar5 = ((int)"onPlayAbility"[iVar2] + uVar6) % 0xfff1;
    uVar7 = ((uVar7 + uVar6) % 0xfff1 + uVar5) % 0xfff1;
  } while (uVar9 < 0xe);
  FUN_00536dd0(0,0,uVar7 << 0x10 | uVar5,*(undefined4 *)(local_8 + 0x14));
  return;
}


