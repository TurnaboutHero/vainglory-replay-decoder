// 00958330 FUN_00958330

undefined4 * FUN_00958330(undefined4 *param_1)

{
  uint uVar1;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  puStack_c = &LAB_011cd138;
  local_10 = ExceptionList;
  uVar1 = DAT_01e44f28 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  *param_1 = Nuo::Game::Component::vftable;
  local_8 = 0;
  FUN_01129bb0(uVar1);
  param_1[5] = Nuo::Game::Referenceable<Nuo::Kindred::CKinItemSet>::vftable;
  *(undefined2 *)(param_1 + 0x1c) = 0;
  *param_1 = Nuo::Kindred::CKinItemSet::vftable;
  param_1[5] = Nuo::Kindred::CKinItemSet::vftable;
  param_1[0x1b] = 2000;
  param_1[7] = 0;
  param_1[0x11] = 0;
  param_1[8] = 0;
  param_1[0x12] = 0;
  param_1[9] = 0;
  param_1[0x13] = 0;
  param_1[10] = 0;
  param_1[0x14] = 0;
  param_1[0xb] = 0;
  param_1[0x15] = 0;
  param_1[0xc] = 0;
  param_1[0x16] = 0;
  param_1[0xd] = 0;
  param_1[0x17] = 0;
  param_1[0xe] = 0;
  param_1[0x18] = 0;
  param_1[0xf] = 0;
  param_1[0x19] = 0;
  param_1[0x10] = 0;
  param_1[0x1a] = 0;
  *(byte *)((int)param_1 + 0x71) =
       *(byte *)((int)param_1 + 0x71) ^
       (*(byte *)(DAT_0209e208 + 0x18) ^ *(byte *)((int)param_1 + 0x71)) & 0x7f;
  ExceptionList = local_10;
  return param_1;
}


