// 0086fed0 FUN_0086fed0

bool __thiscall FUN_0086fed0(int param_1,int param_2)

{
  byte bVar1;
  int iVar2;
  uint uVar3;
  int *piVar4;
  
  uVar3 = 0;
  bVar1 = *(byte *)(param_1 + 0x71);
  if ((bVar1 & 0x7f) != 0) {
    piVar4 = (int *)(param_1 + 0x1c);
    do {
      iVar2 = *piVar4;
      if ((iVar2 != 0) && (*(int *)(iVar2 + 0x2c) == param_2)) {
        if (*(char *)(*(int *)(iVar2 + 0x14) + 300) != '\0') {
          return false;
        }
        if ((uint)*(ushort *)(iVar2 + 0x34) < *(uint *)(*(int *)(iVar2 + 0x14) + 0x20)) {
          return true;
        }
      }
      uVar3 = uVar3 + 1;
      piVar4 = piVar4 + 1;
    } while (uVar3 < (bVar1 & 0x7f));
  }
  return *(byte *)(param_1 + 0x70) < (bVar1 & 0x7f);
}


