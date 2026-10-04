// 00549470 FUN_00549470

void __thiscall FUN_00549470(int param_1,undefined4 param_2,undefined4 param_3,char param_4)

{
  char cVar1;
  uint uVar2;
  int iVar3;
  int *piVar4;
  undefined4 uVar5;
  uint uVar6;
  int local_44 [5];
  uint local_30;
  uint local_2c [4];
  undefined4 local_1c;
  uint local_18;
  uint local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  local_8 = 0xffffffff;
  puStack_c = &LAB_011cd550;
  local_10 = ExceptionList;
  uVar2 = DAT_01e44f28 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  local_14 = uVar2;
  FUN_0054a030(2);
  FUN_0095d910(param_2,uVar2);
  FUN_00940e40();
  FUN_004c0de0();
  FUN_004c0d60();
  FUN_004c1150();
  *(undefined4 *)(param_1 + 0x194) = param_3;
  FUN_00456f50(&DAT_01ab9c78);
  local_8 = 0;
  FUN_00456f50(&DAT_01ab9c78);
  local_8 = CONCAT31(local_8._1_3_,1);
  cVar1 = FUN_0099c230();
  if (cVar1 != '\0') {
    iVar3 = FUN_00999a00();
    piVar4 = (int *)(iVar3 + 0x94);
    if (local_44 != piVar4) {
      if (0xf < *(uint *)(iVar3 + 0xa8)) {
        piVar4 = (int *)*piVar4;
      }
      FUN_00457390(piVar4,*(undefined4 *)(iVar3 + 0xa4));
    }
    FUN_009988a0(local_2c);
  }
  uVar5 = FUN_00938fb0(local_44);
  FUN_004b3200(uVar5);
  uVar5 = FUN_00938fb0();
  if (param_4 == '\0') {
    FUN_004adf70();
  }
  else {
    FUN_004ade70(uVar5);
  }
  cVar1 = FUN_004eb1a0();
  if (cVar1 == '\0') {
    FUN_004cd980(local_2c,local_44);
  }
  if (0xf < local_18) {
    uVar6 = local_18 + 1;
    uVar2 = local_2c[0];
    if (0xfff < uVar6) {
      uVar2 = *(uint *)(local_2c[0] - 4);
      uVar6 = local_18 + 0x24;
      if (0x1f < (local_2c[0] - uVar2) - 4) {
                    /* WARNING: Subroutine does not return */
        _invalid_parameter_noinfo_noreturn();
      }
    }
    FUN_011b8432(uVar2,uVar6);
  }
  local_1c = 0;
  local_18 = 0xf;
  local_2c[0] = local_2c[0] & 0xffffff00;
  if (0xf < local_30) {
    uVar2 = local_30 + 1;
    iVar3 = local_44[0];
    if (0xfff < uVar2) {
      iVar3 = *(int *)(local_44[0] + -4);
      uVar2 = local_30 + 0x24;
      if (0x1f < (local_44[0] - iVar3) - 4U) {
                    /* WARNING: Subroutine does not return */
        _invalid_parameter_noinfo_noreturn();
      }
    }
    FUN_011b8432(iVar3,uVar2);
  }
  ExceptionList = local_10;
  __security_check_cookie(local_14 ^ (uint)&stack0xfffffffc);
  return;
}


