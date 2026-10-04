// 009392b0 FUN_009392b0

void __thiscall FUN_009392b0(int param_1,int param_2)

{
  int iVar1;
  int *piVar2;
  uint uVar3;
  undefined4 uVar4;
  undefined4 uVar5;
  undefined4 uVar6;
  
  uVar3 = 0;
  if ((*(byte *)(param_1 + 0x71) & 0x7f) != 0) {
    piVar2 = (int *)(param_1 + 0x1c);
    do {
      iVar1 = *piVar2;
      if ((iVar1 != 0) && (*(int *)(iVar1 + 0x30) == param_2)) goto LAB_009392db;
      uVar3 = uVar3 + 1;
      piVar2 = piVar2 + 1;
    } while (uVar3 < (*(byte *)(param_1 + 0x71) & 0x7f));
  }
  iVar1 = 0;
LAB_009392db:
  uVar6 = 0;
  uVar5 = **(undefined4 **)(**(int **)(DAT_0209e200 + 0x20) + *(int *)(iVar1 + 0x2c) * 4);
  uVar4 = 0;
  FUN_0112a790(0,uVar5,0);
  FUN_0112ab50(uVar4,uVar5,uVar6);
  return;
}


