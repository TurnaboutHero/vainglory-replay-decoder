// 0095c590 FUN_0095c590

void __thiscall FUN_0095c590(int param_1,uint param_2,undefined4 param_3,undefined4 param_4)

{
  uint uVar1;
  uint uVar2;
  
  switch(param_3) {
  case 0:
    *(undefined4 *)(param_1 + param_2 * 4) = param_4;
    break;
  case 1:
    *(undefined4 *)(param_1 + 0xb4 + param_2 * 4) = param_4;
    break;
  case 2:
    *(undefined4 *)(param_1 + 0x168 + param_2 * 4) = param_4;
    break;
  case 3:
    *(undefined4 *)(param_1 + 0x21c + param_2 * 4) = param_4;
  }
  uVar1 = 1 << (param_2 & 0x1f);
  uVar2 = 0;
  if (0x1f < param_2) {
    uVar2 = uVar1;
  }
  uVar1 = uVar1 ^ uVar2;
  if (0x3f < param_2) {
    uVar2 = uVar1;
  }
  *(uint *)(param_1 + 0x310) = *(uint *)(param_1 + 0x310) | uVar1;
  *(uint *)(param_1 + 0x314) = *(uint *)(param_1 + 0x314) | uVar2;
  return;
}


