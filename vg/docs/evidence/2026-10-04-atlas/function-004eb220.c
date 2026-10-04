// 004eb220 FUN_004eb220

/* WARNING: Globals starting with '_' overlap smaller symbols at the same address */

void FUN_004eb220(void)

{
  FUN_004ec6e0();
  (**(code **)(*DAT_01ef0e80 + 8))();
  _DAT_018ffffc = 0;
  _DAT_01900004 = 0;
  DAT_01900008 = 0;
  DAT_0190000c = 0;
  DAT_01900010 = 0;
  DAT_01900014 = 0;
  DAT_01900020 = 0;
  _DAT_01900024 = 0;
  DAT_01900028 = 0;
  DAT_0190002c = 0;
  DAT_01900030 = 0;
  _DAT_01900034 = 0;
  if (DAT_01ef0e80 != (int *)0x0) {
    (**(code **)*DAT_01ef0e80)(1);
  }
  DAT_01ef0e80 = (int *)0x0;
  thunk_FUN_0096efe0();
  return;
}


