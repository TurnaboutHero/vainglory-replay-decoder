// 0093cdc0 FUN_0093cdc0

/* WARNING: Function: __alloca_probe replaced with injection: alloca_probe */

void __thiscall
FUN_0093cdc0(int param_1,int param_2,int param_3,char param_4,undefined2 param_5,undefined4 param_6,
            byte param_7)

{
  char *pcVar1;
  char cVar2;
  int iVar3;
  int iVar4;
  uint uVar5;
  int iVar6;
  uint uVar7;
  int *piVar8;
  uint uVar9;
  float fVar10;
  undefined4 uVar11;
  undefined4 uVar12;
  undefined4 uVar13;
  int local_12c8 [1200];
  uint local_8;
  
  local_8 = DAT_01e44f28 ^ (uint)&stack0xfffffffc;
  if (param_3 == -1) {
    uVar7 = 0;
    if ((*(byte *)(param_1 + 0x71) & 0x7f) == 0) goto LAB_0093d06b;
    piVar8 = (int *)(param_1 + 0x1c);
    while (((iVar3 = *piVar8, iVar3 == 0 || (*(int *)(iVar3 + 0x2c) != param_2)) ||
           (*(uint *)(*(int *)(iVar3 + 0x14) + 0x20) <= (*(uint *)(iVar3 + 0x34) & 0xffff)))) {
      uVar7 = uVar7 + 1;
      piVar8 = piVar8 + 1;
      if ((*(byte *)(param_1 + 0x71) & 0x7f) <= uVar7) {
        __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
        return;
      }
    }
    uVar5 = 0;
    *(short *)(iVar3 + 0x34) = (short)*(uint *)(iVar3 + 0x34) + 1;
    uVar9 = 0;
    uVar7 = 1;
    do {
      pcVar1 = "onItemSetChanged" + uVar9;
      uVar9 = uVar9 + 1;
      uVar7 = ((int)*pcVar1 + uVar7) % 0xfff1;
      uVar5 = (uVar5 + uVar7) % 0xfff1;
    } while (uVar9 < 0x11);
    uVar7 = uVar5 << 0x10 | uVar7;
  }
  else {
    uVar13 = 0;
    uVar12 = **(undefined4 **)(**(int **)(DAT_0209e200 + 0x20) + param_2 * 4);
    uVar11 = 0;
    FUN_0112a790(0,uVar12,0);
    iVar3 = FUN_0112ab50(uVar11,uVar12,uVar13);
    if ((*(char *)(iVar3 + 0x125) != '\0') || (cVar2 = FUN_0086fed0(param_2), cVar2 == '\0'))
    goto LAB_0093d06b;
    iVar4 = FUN_01129d20(DAT_020e9cc0);
    FUN_00940230(iVar3,param_3,param_2);
    FUN_0092f980();
    *(undefined2 *)(iVar4 + 0x34) = param_5;
    if ((param_4 == '\0') && (iVar3 = *(int *)(iVar4 + 0x18), iVar3 != 0)) {
      piVar8 = &DAT_01a79370;
      if (*(int *)(iVar3 + 0x124) != 0) {
        piVar8 = (int *)(*(int *)(iVar3 + 0x124) + 0x28);
      }
      iVar3 = *(int *)(iVar3 + 8);
      while ((iVar3 != 0 && (*(int *)(*(int *)(iVar3 + 4) + 0x54) != DAT_01e6ee20))) {
        iVar3 = *(int *)(iVar3 + 8);
      }
      uVar7 = FUN_0112a700(local_12c8,0x4b0,DAT_01ef0b3c);
      uVar5 = 0;
      if (uVar7 != 0) {
        do {
          iVar3 = local_12c8[uVar5];
          if (*(int *)(iVar3 + 0x28) == *piVar8) {
            iVar6 = (int)*(char *)(iVar3 + 0x41) + (uint)*(byte *)(iVar3 + 0x40);
            fVar10 = (float)((double)iVar6 + (double)(&DAT_012122c0)[-(iVar6 >> 0x1f)]);
            if ((float)param_7 <= fVar10) {
              fVar10 = (float)param_7;
            }
            *(char *)(iVar3 + 0x42) = (char)(int)fVar10;
            FUN_009613b0(param_6);
            break;
          }
          uVar5 = uVar5 + 1;
        } while (uVar5 < uVar7);
      }
    }
    uVar7 = 0;
    if ((*(byte *)(param_1 + 0x71) & 0x7f) != 0) {
      piVar8 = (int *)(param_1 + 0x1c);
      do {
        if (*piVar8 == 0) {
          *(int *)(param_1 + 0x1c + uVar7 * 4) = iVar4;
          break;
        }
        uVar7 = uVar7 + 1;
        piVar8 = piVar8 + 1;
      } while (uVar7 < (*(byte *)(param_1 + 0x71) & 0x7f));
    }
    uVar5 = 0;
    *(char *)(param_1 + 0x70) = *(char *)(param_1 + 0x70) + '\x01';
    *(byte *)(param_1 + 0x71) = *(byte *)(param_1 + 0x71) | 0x80;
    uVar7 = 1;
    param_2 = *(int *)(iVar4 + 0x2c);
    uVar9 = 0;
    do {
      pcVar1 = "onItemSetChanged" + uVar9;
      uVar9 = uVar9 + 1;
      uVar7 = ((int)*pcVar1 + uVar7) % 0xfff1;
      uVar5 = (uVar5 + uVar7) % 0xfff1;
    } while (uVar9 < 0x11);
    uVar7 = uVar5 << 0x10 | uVar7;
  }
  FUN_00595490(0,0,uVar7,param_2,1);
LAB_0093d06b:
  __security_check_cookie(local_8 ^ (uint)&stack0xfffffffc);
  return;
}


