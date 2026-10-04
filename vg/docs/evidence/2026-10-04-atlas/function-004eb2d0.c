// 004eb2d0 FUN_004eb2d0

undefined4 FUN_004eb2d0(int param_1)

{
  char cVar1;
  int *piVar2;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_011c7d1f;
  local_10 = ExceptionList;
  ExceptionList = &local_10;
  thunk_FUN_0096eff0(DAT_01e44f28 ^ (uint)&stack0xfffffffc);
  FUN_0096cb80();
  if (param_1 == 0) {
    piVar2 = (int *)FUN_011b8402(0x838);
    if (piVar2 == (int *)0x0) {
LAB_004eb3a2:
      piVar2 = (int *)0x0;
    }
    else {
      local_8._0_1_ = 1;
      local_8._1_3_ = 0;
      *piVar2 = (int)Nuo::Kindred::KindredNetworking::vftable;
      FUN_0097d270();
      local_8 = CONCAT31(local_8._1_3_,2);
      piVar2[0x20c] = 0;
      FUN_004cde60();
    }
  }
  else {
    if (param_1 != 1) goto LAB_004eb3b1;
    piVar2 = (int *)FUN_011b8402(0x81c);
    if (piVar2 == (int *)0x0) goto LAB_004eb3a2;
    local_8 = 4;
    *piVar2 = (int)Nuo::Kindred::KindredReplay::vftable;
    piVar2[1] = 0;
    piVar2[3] = 0;
    piVar2[4] = 0;
    *(undefined1 *)(piVar2 + 5) = 1;
    FUN_004cdbb0();
  }
  local_8 = 0xffffffff;
  DAT_01ef0e80 = piVar2;
LAB_004eb3b1:
  if ((DAT_01ef0e80 != (int *)0x0) && (cVar1 = (**(code **)(*DAT_01ef0e80 + 4))(), cVar1 != '\0')) {
    ExceptionList = local_10;
    return 1;
  }
  ExceptionList = local_10;
  return 0;
}


