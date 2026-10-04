// 0094cfb0 FUN_0094cfb0

void __fastcall FUN_0094cfb0(int param_1)

{
  int iVar1;
  
  iVar1 = FUN_00857970(*(undefined4 *)(param_1 + 0x10));
  if (((DAT_0209e204 == '\0') && (iVar1 != 0)) && (iVar1 = *(int *)(iVar1 + 0xc), iVar1 != 0)) {
    while (*(int *)(*(int *)(iVar1 + 4) + 0x54) != DAT_02093f14) {
      iVar1 = *(int *)(iVar1 + 0x10);
      if (iVar1 == 0) {
        return;
      }
    }
    FUN_00872340(*(undefined4 *)(param_1 + 0x14),*(undefined1 *)(param_1 + 0x18));
  }
  return;
}


