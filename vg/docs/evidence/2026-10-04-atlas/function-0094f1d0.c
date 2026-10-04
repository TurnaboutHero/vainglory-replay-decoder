// 0094f1d0 FUN_0094f1d0

void __fastcall FUN_0094f1d0(int param_1)

{
  int iVar1;
  
  iVar1 = FUN_00857970(*(undefined4 *)(param_1 + 0x10));
  if (iVar1 != 0) {
    if (*(char *)(param_1 + 0x24) != '\0') {
      FUN_0095c620(*(undefined4 *)(param_1 + 0x18),*(undefined4 *)(param_1 + 0x1c),
                   *(undefined4 *)(param_1 + 0x20),*(undefined4 *)(param_1 + 0x14));
      return;
    }
    FUN_0093e850(*(undefined4 *)(param_1 + 0x18),*(undefined4 *)(param_1 + 0x1c),
                 *(undefined4 *)(param_1 + 0x20),*(undefined4 *)(param_1 + 0x14));
  }
  return;
}


