// 004eb4a0 FUN_004eb4a0

void __fastcall FUN_004eb4a0(int param_1)

{
  char cVar1;
  float10 fVar2;
  undefined4 local_c;
  float local_8;
  
  if (*(int *)(param_1 + 4) != 2) {
    if (*(int *)(param_1 + 4) == 1) {
      fVar2 = (float10)FUN_0112a7a0();
      local_8 = (float)fVar2;
      *(float *)(param_1 + 0xc) = *(float *)(param_1 + 0xc) + local_8;
    }
    cVar1 = *(char *)(param_1 + 0x14);
    do {
      if (cVar1 != '\0') {
        cVar1 = FUN_004ca130(param_1 + 0x15,(undefined4 *)(param_1 + 0x818),&local_c,1);
        if (cVar1 == '\0') {
          return;
        }
        *(undefined4 *)(param_1 + 0x10) = local_c;
        *(undefined1 *)(param_1 + 0x14) = 0;
      }
      if (*(float *)(param_1 + 0xc) < *(float *)(param_1 + 0x10)) {
        return;
      }
      FUN_004cfec0(param_1 + 0x15,*(undefined4 *)(param_1 + 0x818));
      *(undefined1 *)(param_1 + 0x14) = 1;
      cVar1 = '\x01';
    } while (*(int *)(param_1 + 4) != 2);
  }
  return;
}


