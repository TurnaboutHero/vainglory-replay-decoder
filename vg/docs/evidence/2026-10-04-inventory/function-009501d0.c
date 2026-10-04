// 009501d0 FUN_009501d0

void __fastcall FUN_009501d0(int param_1)

{
  char *pcVar1;
  int iVar2;
  uint uVar3;
  uint uVar4;
  uint uVar5;
  
  if ((DAT_0209e204 != '\0') && (iVar2 = FUN_00857970(*(undefined4 *)(param_1 + 0x10)), iVar2 != 0))
  {
    uVar3 = 0;
    uVar5 = 1;
    uVar4 = 0;
    do {
      pcVar1 = "quickBuyItem" + uVar4;
      uVar4 = uVar4 + 1;
      uVar5 = ((int)*pcVar1 + uVar5) % 0xfff1;
      uVar3 = (uVar3 + uVar5) % 0xfff1;
    } while (uVar4 < 0xd);
    FUN_00539400(0,0,uVar3 << 0x10 | uVar5);
  }
  return;
}


