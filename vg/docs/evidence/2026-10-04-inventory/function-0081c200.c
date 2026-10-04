// 0081c200 FUN_0081c200

undefined4 * __thiscall FUN_0081c200(undefined4 *param_1,undefined4 param_2,undefined4 param_3)

{
  param_1[4] = param_3;
  param_1[5] = param_2;
  param_1[1] = 0;
  param_1[2] = 0;
  *(undefined1 *)(param_1 + 3) = 0;
  *param_1 = Nuo::Kindred::ActionSellItem::vftable;
  return param_1;
}


