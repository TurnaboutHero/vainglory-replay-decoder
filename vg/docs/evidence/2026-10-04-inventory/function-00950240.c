// 00950240 FUN_00950240

void __fastcall FUN_00950240(int param_1)

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
  
  if (DAT_0209e204 != '\0') {
    iVar1 = FUN_00857970(*(undefined4 *)(param_1 + 0x18));
    if (iVar1 != 0) {
      uVar2 = 0;
      uVar9 = 1;
      uVar8 = 0;
      do {
        uVar3 = ((int)"reorderItem"[uVar8] + uVar9) % 0xfff1;
        uVar4 = ((int)"reorderItem"[uVar8 + 1] + uVar3) % 0xfff1;
        uVar5 = ((int)"reorderItem"[uVar8 + 2] + uVar4) % 0xfff1;
        uVar6 = ((int)"reorderItem"[uVar8 + 3] + uVar5) % 0xfff1;
        uVar7 = ((int)"reorderItem"[uVar8 + 4] + uVar6) % 0xfff1;
        iVar1 = uVar8 + 5;
        uVar8 = uVar8 + 6;
        uVar9 = ((int)"reorderItem"[iVar1] + uVar7) % 0xfff1;
        uVar2 = ((((((uVar2 + uVar3) % 0xfff1 + uVar4) % 0xfff1 + uVar5) % 0xfff1 + uVar6) % 0xfff1
                 + uVar7) % 0xfff1 + uVar9) % 0xfff1;
      } while (uVar8 < 0xc);
      FUN_00595490(0,0,uVar2 << 0x10 | uVar9,*(undefined4 *)(param_1 + 0x10),
                   *(undefined4 *)(param_1 + 0x14));
    }
  }
  return;
}


