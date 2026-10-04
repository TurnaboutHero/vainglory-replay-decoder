// 0094f6f0 FUN_0094f6f0

void __fastcall FUN_0094f6f0(int param_1)

{
  int iVar1;
  int iVar2;
  int *piVar3;
  uint uVar4;
  
  iVar1 = FUN_00857970(*(undefined4 *)(param_1 + 0x10));
  if (iVar1 != 0) {
    for (iVar1 = *(int *)(iVar1 + 0xc); iVar1 != 0; iVar1 = *(int *)(iVar1 + 0x10)) {
      if (*(int *)(*(int *)(iVar1 + 4) + 0x54) == DAT_02093f14) goto LAB_0094f721;
    }
    iVar1 = 0;
LAB_0094f721:
    uVar4 = 0;
    if ((*(byte *)(iVar1 + 0x71) & 0x7f) != 0) {
      piVar3 = (int *)(iVar1 + 0x1c);
      do {
        iVar2 = *piVar3;
        if ((iVar2 != 0) && (*(int *)(iVar2 + 0x30) == *(int *)(param_1 + 0x14))) goto LAB_0094f74c;
        uVar4 = uVar4 + 1;
        piVar3 = piVar3 + 1;
      } while (uVar4 < (*(byte *)(iVar1 + 0x71) & 0x7f));
    }
    iVar2 = 0;
LAB_0094f74c:
    *(short *)(iVar2 + 0x34) = (short)*(undefined4 *)(param_1 + 0x18);
  }
  return;
}


