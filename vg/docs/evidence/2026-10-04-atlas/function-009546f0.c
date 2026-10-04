// 009546f0 FUN_009546f0

void __thiscall FUN_009546f0(int param_1,void *param_2,size_t param_3,uint param_4)

{
  size_t _Size;
  int iVar1;
  int iVar2;
  
  _Size = param_3;
  param_4 = (param_4 & 0xff0000 | param_4 >> 0x10) >> 8 | (param_4 & 0xff00 | param_4 << 0x10) << 8;
  param_3 = Ordinal_8(param_3);
  iVar1 = *(int *)(param_1 + 0x40008);
  if (0x1ffff < (int)(_Size + 8 + iVar1)) {
    FUN_0096bfa0(0);
    iVar1 = *(int *)(param_1 + 0x40008);
  }
  iVar2 = param_1 + 8 + *(int *)(param_1 + 0x4000c) * 0x20000;
  memmove((void *)(iVar1 + iVar2),&param_4,4);
  memmove((void *)(*(int *)(param_1 + 0x40008) + 4 + iVar2),&param_3,4);
  memmove((void *)(*(int *)(param_1 + 0x40008) + 8 + iVar2),param_2,_Size);
  *(int *)(param_1 + 0x40008) = *(int *)(param_1 + 0x40008) + _Size + 8;
  return;
}


