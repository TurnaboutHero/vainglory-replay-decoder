// 0081b910 FUN_0081b910

undefined4 * __thiscall
FUN_0081b910(undefined4 *param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,
            undefined4 param_5,undefined1 param_6,undefined4 param_7)

{
  param_1[4] = param_2;
  param_1[5] = param_7;
  param_1[6] = param_3;
  param_1[7] = param_4;
  *(undefined1 *)(param_1 + 9) = param_6;
  param_1[1] = 0;
  param_1[2] = 0;
  *(undefined1 *)(param_1 + 3) = 0;
  *param_1 = Nuo::Kindred::ActionModifyActorAttribute::vftable;
  param_1[8] = param_5;
  return param_1;
}


