// 0092f980 FUN_0092f980

void __fastcall FUN_0092f980(int param_1)

{
  int *piVar1;
  int iVar2;
  void **ppvVar3;
  uint uVar4;
  int *piVar5;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  puStack_c = &LAB_011f9bc0;
  local_10 = ExceptionList;
  uVar4 = DAT_01e44f28 ^ (uint)&stack0xfffffffc;
  if (DAT_0209e204 != '\0') {
    piVar5 = *(int **)(*(int *)(param_1 + 0x14) + 0x2c);
    iVar2 = *piVar5;
    ppvVar3 = &local_10;
    while (ExceptionList = ppvVar3, iVar2 != 0) {
      if (*(float *)(iVar2 + 4) <= 0.0) {
        if (0.0 < *(float *)(iVar2 + 8)) {
          local_8 = 1;
          FUN_0092e8e0(&DAT_020db890);
        }
      }
      else {
        local_8 = 0;
        FUN_0092e8e0(&DAT_020db890);
      }
      piVar1 = piVar5 + 1;
      piVar5 = piVar5 + 1;
      ppvVar3 = ExceptionList;
      iVar2 = *piVar1;
    }
    local_8 = 0xffffffff;
    FUN_00865e30(uVar4);
  }
  ExceptionList = local_10;
  return;
}


