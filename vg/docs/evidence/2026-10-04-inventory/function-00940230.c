// 00940230 FUN_00940230

void __thiscall FUN_00940230(int param_1,int param_2,undefined4 param_3,undefined4 param_4)

{
  char cVar1;
  undefined4 uVar2;
  int iVar3;
  undefined4 uVar4;
  undefined4 uVar5;
  
  iVar3 = param_2;
  *(undefined2 *)(param_1 + 0x34) = 1;
  *(undefined4 *)(param_1 + 0x2c) = param_4;
  *(int *)(param_1 + 0x14) = param_2;
  *(undefined4 *)(param_1 + 0x30) = param_3;
  if (*(char *)(param_2 + 0x38) == '\0') {
    cVar1 = FUN_0096c770(*(undefined4 *)(param_2 + 0x11c));
    if (cVar1 == '\0') {
      FUN_005f5050(*(undefined4 *)(*(int *)(param_1 + 0x14) + 0x11c));
      iVar3 = FUN_008579e0(*(undefined4 *)(*(int *)(param_1 + 8) + 8),&param_2);
      if (iVar3 == 0) {
        iVar3 = FUN_01129d20(DAT_01ef0b3c);
        *(byte *)(iVar3 + 0x48) = *(byte *)(iVar3 + 0x48) & 0xf8;
        *(int *)(iVar3 + 0x28) = param_2;
        *(uint *)(iVar3 + 0x44) = *(uint *)(iVar3 + 0x44) & 0xfffffffe | 2;
        FUN_0095dcf0(1);
      }
    }
    return;
  }
  uVar2 = FUN_01129d20(DAT_020e9d20);
  *(undefined4 *)(param_1 + 0x18) = uVar2;
  if (*(char *)(iVar3 + 0x38) == '\0') {
    FUN_0093f270(0,0,0);
    return;
  }
  cVar1 = FUN_0096c770(*(undefined4 *)(iVar3 + 0x3c));
  if (cVar1 != '\0') {
    FUN_0093f270(iVar3 + 0x40,0,0);
    return;
  }
  uVar5 = 0;
  uVar2 = *(undefined4 *)(iVar3 + 0x3c);
  uVar4 = 0;
  FUN_0112a790(0,uVar2,0);
  uVar2 = FUN_0112ab50(uVar4,uVar2,uVar5);
  FUN_0093f270(uVar2,0,0);
  return;
}


