// 0094e070 FUN_0094e070

void __fastcall FUN_0094e070(int param_1)

{
  undefined4 uVar1;
  undefined4 uVar2;
  undefined4 *puVar3;
  int iVar4;
  uint uVar5;
  undefined4 *puVar6;
  undefined4 *puVar7;
  undefined4 *puVar8;
  
  iVar4 = FUN_00857970(*(undefined4 *)(param_1 + 0x18));
  if (iVar4 == 0) {
    return;
  }
  if (DAT_0209e204 != '\0') {
    return;
  }
  FUN_0093d080(*(undefined4 *)(param_1 + 0x10),*(undefined4 *)(param_1 + 0x14),1,1,0,1);
  if (DAT_0209e205 == '\0') {
    FUN_0054f9e0(iVar4,*(undefined4 *)(param_1 + 0x10));
    return;
  }
  FUN_005663e0(iVar4,*(undefined4 *)(param_1 + 0x10));
  uVar1 = *(undefined4 *)(param_1 + 0x10);
  uVar2 = *(undefined4 *)(iVar4 + 0x178);
  uVar5 = FUN_004cfd30("method_onItemSetChanged");
  puVar3 = *(undefined4 **)(DAT_020e74a0 + 4);
  puVar6 = (undefined4 *)puVar3[1];
  puVar8 = puVar3;
  if (*(char *)((int)puVar6 + 0xd) == '\0') {
    do {
      if ((uint)puVar6[4] < uVar5) {
        puVar7 = (undefined4 *)puVar6[2];
      }
      else {
        puVar7 = (undefined4 *)*puVar6;
        puVar8 = puVar6;
      }
      puVar6 = puVar7;
    } while (*(char *)((int)puVar7 + 0xd) == '\0');
    if ((puVar8 != puVar3) && ((uint)puVar8[4] <= uVar5)) goto LAB_0094e11f;
  }
  puVar8 = puVar3;
LAB_0094e11f:
  if ((puVar8 != puVar3) && (uVar5 = 0, puVar8[5] != 0)) {
    do {
      (**(code **)(puVar8[7] + 4 + uVar5 * 8))(*(undefined4 *)(puVar8[7] + uVar5 * 8),uVar2,uVar1,1)
      ;
      uVar5 = uVar5 + 1;
    } while (uVar5 < (uint)puVar8[5]);
  }
  return;
}


