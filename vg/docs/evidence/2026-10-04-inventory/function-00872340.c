// 00872340 FUN_00872340

void __thiscall FUN_00872340(int param_1,int param_2,char param_3)

{
  int *piVar1;
  char *pcVar2;
  int iVar3;
  int iVar4;
  undefined4 uVar5;
  uint uVar6;
  uint uVar7;
  byte bVar8;
  int *piVar9;
  uint uVar10;
  int *piVar11;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_10 = ExceptionList;
  local_8 = 0xffffffff;
  puStack_c = &LAB_011f9390;
  uVar6 = DAT_01e44f28 ^ (uint)&stack0xfffffffc;
  uVar7 = 0;
  if ((*(byte *)(param_1 + 0x71) & 0x7f) == 0) {
    return;
  }
  piVar11 = (int *)(param_1 + 0x1c);
  piVar9 = piVar11;
  while ((iVar3 = *piVar9, iVar3 == 0 || (*(int *)(iVar3 + 0x30) != param_2))) {
    uVar7 = uVar7 + 1;
    piVar9 = piVar9 + 1;
    if ((*(byte *)(param_1 + 0x71) & 0x7f) <= uVar7) {
      return;
    }
  }
  if (iVar3 == 0) {
    return;
  }
  ExceptionList = &local_10;
  if (*(char *)(*(int *)(iVar3 + 0x14) + 0x1c) != '\0') {
    uVar7 = *(uint *)(iVar3 + 0x34);
    if ((short)uVar7 != 0) {
      *(short *)(iVar3 + 0x34) = (short)uVar7 + -1;
      uVar7 = *(uint *)(iVar3 + 0x34);
    }
    if ((uVar7 & 0xffff) != 0) goto LAB_008723df;
  }
  *(byte *)(iVar3 + 0x38) = *(byte *)(iVar3 + 0x38) | 1;
LAB_008723df:
  if ((*(byte *)(iVar3 + 0x38) & 1) != 0) {
    if (DAT_0209e204 != '\0') {
      piVar9 = *(int **)(*(int *)(iVar3 + 0x14) + 0x2c);
      iVar4 = *piVar9;
      while (iVar4 != 0) {
        if (*(float *)(iVar4 + 4) <= 0.0) {
          if (0.0 < *(float *)(iVar4 + 8)) {
            local_8 = 1;
            FUN_0092e8e0(&DAT_020db890);
          }
        }
        else {
          local_8 = 0;
          FUN_0092e8e0(&DAT_020db890);
        }
        piVar1 = piVar9 + 1;
        piVar9 = piVar9 + 1;
        iVar4 = *piVar1;
      }
      local_8 = 0xffffffff;
      if (param_3 != '\0') {
        FUN_00870c30(uVar6);
      }
    }
    *(char *)(param_1 + 0x70) = *(char *)(param_1 + 0x70) + -1;
    uVar5 = *(undefined4 *)(iVar3 + 0x2c);
    bVar8 = *(byte *)(param_1 + 0x71);
    uVar6 = 0;
    if ((bVar8 & 0x7f) != 0) {
      do {
        if (*piVar11 == iVar3) {
          *piVar11 = 0;
        }
        bVar8 = *(byte *)(param_1 + 0x71);
        uVar6 = uVar6 + 1;
        piVar11 = piVar11 + 1;
      } while (uVar6 < (bVar8 & 0x7f));
    }
    uVar7 = (uint)bVar8;
    uVar6 = 0;
    if ((bVar8 & 0x7f) != 0) {
      piVar11 = (int *)(param_1 + 0x44);
      do {
        if (*piVar11 == 0) {
          *(int *)(param_1 + 0x44 + uVar6 * 4) = iVar3;
          bVar8 = *(byte *)(param_1 + 0x71);
          break;
        }
        bVar8 = *(byte *)(param_1 + 0x71);
        uVar6 = uVar6 + 1;
        piVar11 = piVar11 + 1;
      } while (uVar6 < (uVar7 & 0x7f));
    }
    *(byte *)(param_1 + 0x71) = bVar8 | 0x80;
    uVar7 = 1;
    uVar6 = 0;
    uVar10 = 0;
    do {
      pcVar2 = "onItemSetChanged" + uVar10;
      uVar10 = uVar10 + 1;
      uVar7 = ((int)*pcVar2 + uVar7) % 0xfff1;
      uVar6 = (uVar7 + uVar6) % 0xfff1;
    } while (uVar10 < 0x11);
    FUN_00595490(0,0,uVar6 << 0x10 | uVar7,uVar5,0xffffffff);
  }
  ExceptionList = local_10;
  return;
}


