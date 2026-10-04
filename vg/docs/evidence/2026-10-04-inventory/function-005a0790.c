// 005a0790 FUN_005a0790

undefined4 FUN_005a0790(undefined4 *param_1)

{
  int iVar1;
  
  iVar1 = _strcoll((char *)*param_1,PTR_s_Healing_Flask_01a40870);
  if (iVar1 != 0) {
    iVar1 = _strcoll((char *)*param_1,PTR_s_Vision_Totem_01a40874);
    if (iVar1 != 0) {
      return 0;
    }
  }
  return 1;
}


