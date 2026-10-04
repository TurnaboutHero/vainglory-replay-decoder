// 0093d3d0 FUN_0093d3d0

undefined4 __thiscall FUN_0093d3d0(int param_1,int param_2)

{
  int iVar1;
  int *piVar2;
  uint uVar3;
  
  uVar3 = 0;
  if ((*(byte *)(param_1 + 0x71) & 0x7f) != 0) {
    piVar2 = (int *)(param_1 + 0x1c);
    do {
      iVar1 = *piVar2;
      if ((iVar1 != 0) && (*(int *)(iVar1 + 0x30) == param_2)) goto LAB_0093d3fb;
      uVar3 = uVar3 + 1;
      piVar2 = piVar2 + 1;
    } while (uVar3 < (*(byte *)(param_1 + 0x71) & 0x7f));
  }
  iVar1 = 0;
LAB_0093d3fb:
  return CONCAT31((int3)((uint)iVar1 >> 8),*(int *)(iVar1 + 0x18) != 0);
}


