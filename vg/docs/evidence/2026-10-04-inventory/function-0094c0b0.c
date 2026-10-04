// 0094c0b0 FUN_0094c0b0

void __fastcall FUN_0094c0b0(int param_1)

{
  char *pcVar1;
  undefined1 uVar2;
  undefined1 uVar3;
  int iVar4;
  int iVar5;
  undefined4 uVar6;
  int iVar7;
  uint uVar8;
  uint uVar9;
  uint uVar10;
  undefined4 local_10;
  undefined1 local_c;
  undefined1 local_b;
  int local_8;
  
  if (DAT_0209e204 == '\0') {
    local_8 = param_1;
    iVar7 = FUN_00857970(*(undefined4 *)(param_1 + 0x18));
    for (iVar7 = *(int *)(iVar7 + 0xc); iVar7 != 0; iVar7 = *(int *)(iVar7 + 0x10)) {
      if (*(int *)(*(int *)(iVar7 + 4) + 0x54) == DAT_02093f14) goto LAB_0094c0f2;
    }
    iVar7 = 0;
LAB_0094c0f2:
    iVar4 = *(int *)(param_1 + 0x14);
    iVar5 = *(int *)(param_1 + 0x10);
    uVar6 = *(undefined4 *)(iVar7 + 0x1c + iVar5 * 4);
    *(undefined4 *)(iVar7 + 0x1c + iVar5 * 4) = *(undefined4 *)(iVar7 + 0x1c + iVar4 * 4);
    *(undefined4 *)(iVar7 + 0x1c + iVar4 * 4) = uVar6;
    uVar6 = *(undefined4 *)(iVar7 + 0x44 + iVar5 * 4);
    *(undefined4 *)(iVar7 + 0x44 + iVar5 * 4) = *(undefined4 *)(iVar7 + 0x44 + iVar4 * 4);
    uVar10 = 1;
    *(undefined4 *)(iVar7 + 0x44 + iVar4 * 4) = uVar6;
    uVar9 = 0;
    *(byte *)(iVar7 + 0x71) = *(byte *)(iVar7 + 0x71) | 0x80;
    uVar8 = 0;
    local_10 = *(undefined4 *)(iVar7 + 8);
    do {
      pcVar1 = "onItemSetChanged" + uVar8;
      uVar8 = uVar8 + 1;
      uVar10 = ((int)*pcVar1 + uVar10) % 0xfff1;
      uVar9 = (uVar9 + uVar10) % 0xfff1;
    } while (uVar8 < 0x11);
    FUN_00595490(0,0,uVar9 << 0x10 | uVar10,0xffff,0);
    uVar2 = *(undefined1 *)(local_8 + 0x14);
    uVar3 = *(undefined1 *)(local_8 + 0x10);
    local_10 = Ordinal_8(*(undefined4 *)(local_8 + 0x18));
    local_c = uVar3;
    local_b = uVar2;
    FUN_008180c0(&local_10,0);
  }
  return;
}


