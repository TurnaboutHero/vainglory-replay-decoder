// 0094a400 FUN_0094a400

void __fastcall FUN_0094a400(int param_1)

{
  char cVar1;
  undefined4 uVar2;
  undefined4 local_10;
  undefined4 local_c;
  undefined2 local_8;
  
  if (DAT_0209e204 != '\0') {
    cVar1 = *(char *)(param_1 + 0x18);
    uVar2 = *(undefined4 *)(param_1 + 0x14);
    local_10 = Ordinal_8(*(undefined4 *)(param_1 + 0x10));
    local_c = Ordinal_8(uVar2);
    local_8 = Ordinal_9(cVar1 != '\0');
    FUN_00814cc0(&local_10,0);
  }
  return;
}


