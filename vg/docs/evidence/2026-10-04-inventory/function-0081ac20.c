// 0081ac20 FUN_0081ac20

undefined4 * __thiscall
FUN_0081ac20(undefined4 *param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,
            undefined4 param_5,undefined1 param_6,undefined4 param_7,undefined4 param_8,
            undefined8 *param_9,undefined8 *param_10,undefined4 param_11,undefined1 param_12,
            undefined1 param_13,undefined4 param_14,undefined4 param_15,undefined4 *param_16,
            undefined4 *param_17,undefined4 *param_18,undefined4 *param_19,undefined4 *param_20,
            int param_21,undefined4 *param_22,undefined4 *param_23,undefined4 *param_24,
            undefined1 *param_25,undefined4 param_26,undefined4 param_27,undefined4 param_28,
            undefined4 param_29,undefined1 param_30,undefined4 param_31,undefined4 param_32,
            undefined4 *param_33,undefined4 *param_34,undefined4 *param_35,undefined4 param_36,
            undefined4 param_37,undefined1 *param_38,undefined1 *param_39,undefined1 *param_40,
            undefined4 param_41,undefined4 param_42,undefined4 param_43,undefined4 param_44)

{
  byte bVar1;
  char cVar2;
  uint uVar3;
  byte *pbVar4;
  uint uVar5;
  undefined4 local_20;
  undefined4 local_1c;
  undefined4 local_18;
  undefined4 *local_14;
  void *local_10;
  undefined1 *puStack_c;
  undefined4 local_8;
  
  puStack_c = &LAB_011f6aa8;
  local_10 = ExceptionList;
  uVar3 = DAT_01e44f28 ^ (uint)&stack0xfffffffc;
  ExceptionList = &local_10;
  param_1[1] = 0;
  param_1[2] = 0;
  *(undefined1 *)(param_1 + 3) = 0;
  param_1[4] = param_2;
  param_1[5] = param_3;
  param_1[6] = param_4;
  *(undefined1 *)(param_1 + 7) = (undefined1)param_5;
  *(undefined1 *)((int)param_1 + 0x1d) = param_6;
  param_1[8] = param_7;
  param_1[9] = param_8;
  *param_1 = Nuo::Kindred::ActionHeroSpawn::vftable;
  local_8 = 0;
  *(undefined8 *)(param_1 + 10) = *param_9;
  param_1[0xc] = *(undefined4 *)(param_9 + 1);
  *(undefined8 *)(param_1 + 0xd) = *param_10;
  param_1[0xf] = *(undefined4 *)(param_10 + 1);
  local_14 = param_1;
  FUN_0081f5d0(param_11);
  *(undefined1 *)(param_1 + 0xd6) = param_12;
  *(undefined1 *)((int)param_1 + 0x359) = param_13;
  param_1[0xd8] = param_14;
  param_1[0x116] = param_26;
  param_1[0x118] = param_27;
  param_1[0x119] = param_28;
  param_1[0x120] = param_42;
  param_1[0x121] = param_41;
  param_1[0x122] = param_43;
  param_1[0x123] = param_44;
  param_1[0x124] = param_29;
  *(undefined1 *)(param_1 + 0x125) = param_30;
  param_1[0x126] = param_31;
  param_1[0x127] = param_32;
  param_1[0x140] = param_36;
  param_1[0x117] = param_21;
  param_1[0xd7] = 0;
  param_1[0xd9] = param_15;
  param_1[0x141] = param_37;
  if (param_21 == 0) {
    param_1[0xda] = 0xffff;
    param_1[0xe4] = 0xffffffff;
    param_1[0xee] = 0;
    param_1[0x102] = 0;
    param_1[0xf8] = 0;
  }
  else {
    param_1[0xda] = *param_16;
    param_1[0xe4] = *param_17;
    param_1[0xee] = *param_18;
    param_1[0x102] = *param_19;
    param_1[0xf8] = *param_20;
  }
  if ((uint)param_1[0x117] < 2) {
    param_1[0xdb] = 0xffff;
    param_1[0xe5] = 0xffffffff;
    param_1[0xef] = 0;
    param_1[0x103] = 0;
    param_1[0xf9] = 0;
  }
  else {
    param_1[0xdb] = param_16[1];
    param_1[0xe5] = param_17[1];
    param_1[0xef] = param_18[1];
    param_1[0x103] = param_19[1];
    param_1[0xf9] = param_20[1];
  }
  if ((uint)param_1[0x117] < 3) {
    param_1[0xdc] = 0xffff;
    param_1[0xe6] = 0xffffffff;
    param_1[0xf0] = 0;
    param_1[0x104] = 0;
    param_1[0xfa] = 0;
  }
  else {
    param_1[0xdc] = param_16[2];
    param_1[0xe6] = param_17[2];
    param_1[0xf0] = param_18[2];
    param_1[0x104] = param_19[2];
    param_1[0xfa] = param_20[2];
  }
  if ((uint)param_1[0x117] < 4) {
    param_1[0xdd] = 0xffff;
    param_1[0xe7] = 0xffffffff;
    param_1[0xf1] = 0;
    param_1[0x105] = 0;
    param_1[0xfb] = 0;
  }
  else {
    param_1[0xdd] = param_16[3];
    param_1[0xe7] = param_17[3];
    param_1[0xf1] = param_18[3];
    param_1[0x105] = param_19[3];
    param_1[0xfb] = param_20[3];
  }
  if ((uint)param_1[0x117] < 5) {
    param_1[0xde] = 0xffff;
    param_1[0xe8] = 0xffffffff;
    param_1[0xf2] = 0;
    param_1[0x106] = 0;
    param_1[0xfc] = 0;
  }
  else {
    param_1[0xde] = param_16[4];
    param_1[0xe8] = param_17[4];
    param_1[0xf2] = param_18[4];
    param_1[0x106] = param_19[4];
    param_1[0xfc] = param_20[4];
  }
  if ((uint)param_1[0x117] < 6) {
    param_1[0xdf] = 0xffff;
    param_1[0xe9] = 0xffffffff;
    param_1[0xf3] = 0;
    param_1[0x107] = 0;
    param_1[0xfd] = 0;
  }
  else {
    param_1[0xdf] = param_16[5];
    param_1[0xe9] = param_17[5];
    param_1[0xf3] = param_18[5];
    param_1[0x107] = param_19[5];
    param_1[0xfd] = param_20[5];
  }
  if ((uint)param_1[0x117] < 7) {
    param_1[0xe0] = 0xffff;
    param_1[0xea] = 0xffffffff;
    param_1[0xf4] = 0;
    param_1[0x108] = 0;
    param_1[0xfe] = 0;
  }
  else {
    param_1[0xe0] = param_16[6];
    param_1[0xea] = param_17[6];
    param_1[0xf4] = param_18[6];
    param_1[0x108] = param_19[6];
    param_1[0xfe] = param_20[6];
  }
  if ((uint)param_1[0x117] < 8) {
    param_1[0xe1] = 0xffff;
    param_1[0xeb] = 0xffffffff;
    param_1[0xf5] = 0;
    param_1[0x109] = 0;
    param_1[0xff] = 0;
  }
  else {
    param_1[0xe1] = param_16[7];
    param_1[0xeb] = param_17[7];
    param_1[0xf5] = param_18[7];
    param_1[0x109] = param_19[7];
    param_1[0xff] = param_20[7];
  }
  if ((uint)param_1[0x117] < 9) {
    param_1[0xe2] = 0xffff;
    param_1[0xec] = 0xffffffff;
    param_1[0xf6] = 0;
    param_1[0x10a] = 0;
    param_1[0x100] = 0;
  }
  else {
    param_1[0xe2] = param_16[8];
    param_1[0xec] = param_17[8];
    param_1[0xf6] = param_18[8];
    param_1[0x10a] = param_19[8];
    param_1[0x100] = param_20[8];
  }
  if ((uint)param_1[0x117] < 10) {
    param_1[0xe3] = 0xffff;
    param_1[0xed] = 0xffffffff;
    param_1[0xf7] = 0;
    param_1[0x10b] = 0;
    param_1[0x101] = 0;
  }
  else {
    param_1[0xe3] = param_16[9];
    param_1[0xed] = param_17[9];
    param_1[0xf7] = param_18[9];
    param_1[0x10b] = param_19[9];
    param_1[0x101] = param_20[9];
  }
  if (param_1[0x116] == 0) {
    param_1[0x10c] = 0;
    param_1[0x10f] = 0xffffffff;
    param_1[0x112] = 0;
    *(undefined1 *)(param_1 + 0x115) = 0;
  }
  else {
    param_1[0x10c] = *param_23;
    param_1[0x10f] = *param_22;
    param_1[0x112] = *param_24;
    *(undefined1 *)(param_1 + 0x115) = *param_25;
  }
  if ((uint)param_1[0x116] < 2) {
    param_1[0x10d] = 0;
    param_1[0x110] = 0xffffffff;
    param_1[0x113] = 0;
    *(undefined1 *)((int)param_1 + 0x455) = 0;
  }
  else {
    param_1[0x10d] = param_23[1];
    param_1[0x110] = param_22[1];
    param_1[0x113] = param_24[1];
    *(undefined1 *)((int)param_1 + 0x455) = param_25[1];
  }
  if ((uint)param_1[0x116] < 3) {
    param_1[0x10e] = 0;
    param_1[0x111] = 0xffffffff;
    param_1[0x114] = 0;
    *(undefined1 *)((int)param_1 + 0x456) = 0;
  }
  else {
    param_1[0x10e] = param_23[2];
    param_1[0x111] = param_22[2];
    param_1[0x114] = param_24[2];
    *(undefined1 *)((int)param_1 + 0x456) = param_25[2];
  }
  if (param_1[0x127] == 0) {
    param_1[0x128] = 0;
    param_1[0x130] = 0;
    param_1[0x138] = 0;
  }
  else {
    param_1[0x128] = *param_33;
    param_1[0x130] = *param_34;
    param_1[0x138] = *param_35;
  }
  if ((uint)param_1[0x127] < 2) {
    param_1[0x129] = 0;
    param_1[0x131] = 0;
    param_1[0x139] = 0;
  }
  else {
    param_1[0x129] = param_33[1];
    param_1[0x131] = param_34[1];
    param_1[0x139] = param_35[1];
  }
  if ((uint)param_1[0x127] < 3) {
    param_1[0x12a] = 0;
    param_1[0x132] = 0;
    param_1[0x13a] = 0;
  }
  else {
    param_1[0x12a] = param_33[2];
    param_1[0x132] = param_34[2];
    param_1[0x13a] = param_35[2];
  }
  if ((uint)param_1[0x127] < 4) {
    param_1[299] = 0;
    param_1[0x133] = 0;
    param_1[0x13b] = 0;
  }
  else {
    param_1[299] = param_33[3];
    param_1[0x133] = param_34[3];
    param_1[0x13b] = param_35[3];
  }
  if ((uint)param_1[0x127] < 5) {
    param_1[300] = 0;
    param_1[0x134] = 0;
    param_1[0x13c] = 0;
  }
  else {
    param_1[300] = param_33[4];
    param_1[0x134] = param_34[4];
    param_1[0x13c] = param_35[4];
  }
  if ((uint)param_1[0x127] < 6) {
    param_1[0x12d] = 0;
    param_1[0x135] = 0;
    param_1[0x13d] = 0;
  }
  else {
    param_1[0x12d] = param_33[5];
    param_1[0x135] = param_34[5];
    param_1[0x13d] = param_35[5];
  }
  if ((uint)param_1[0x127] < 7) {
    param_1[0x12e] = 0;
    param_1[0x136] = 0;
    param_1[0x13e] = 0;
  }
  else {
    param_1[0x12e] = param_33[6];
    param_1[0x136] = param_34[6];
    param_1[0x13e] = param_35[6];
  }
  if ((uint)param_1[0x127] < 8) {
    param_1[0x12f] = 0;
    param_1[0x137] = 0;
    param_1[0x13f] = 0;
  }
  else {
    param_1[0x12f] = param_33[7];
    param_1[0x137] = param_34[7];
    param_1[0x13f] = param_35[7];
  }
  if (((param_38 == (undefined1 *)0x0) && (param_39 == (undefined1 *)0x0)) &&
     (param_40 == (undefined1 *)0x0)) {
    bVar1 = *(byte *)((int)param_1 + 0x1d);
    uVar5 = 0;
    pbVar4 = (byte *)(param_1 + 0x11a);
    do {
      *pbVar4 = *pbVar4 | 1;
      pbVar4[8] = 0;
      *(undefined1 *)((int)param_1 + uVar5 + 0x478) = 0;
      uVar5 = uVar5 + 1;
      pbVar4 = pbVar4 + 1;
    } while (uVar5 < 8);
    pbVar4 = (byte *)(bVar1 + 0x470 + (int)param_1);
    *pbVar4 = *pbVar4 | 1;
  }
  else {
    *(undefined1 *)(param_1 + 0x11a) = *param_38;
    *(undefined1 *)(param_1 + 0x11c) = *param_39;
    *(undefined1 *)(param_1 + 0x11e) = *param_40;
    *(undefined1 *)((int)param_1 + 0x469) = param_38[1];
    *(undefined1 *)((int)param_1 + 0x471) = param_39[1];
    *(undefined1 *)((int)param_1 + 0x479) = param_40[1];
    *(undefined1 *)((int)param_1 + 0x46a) = param_38[2];
    *(undefined1 *)((int)param_1 + 0x472) = param_39[2];
    *(undefined1 *)((int)param_1 + 0x47a) = param_40[2];
    *(undefined1 *)((int)param_1 + 0x46b) = param_38[3];
    *(undefined1 *)((int)param_1 + 0x473) = param_39[3];
    *(undefined1 *)((int)param_1 + 0x47b) = param_40[3];
    *(undefined1 *)(param_1 + 0x11b) = param_38[4];
    *(undefined1 *)(param_1 + 0x11d) = param_39[4];
    *(undefined1 *)(param_1 + 0x11f) = param_40[4];
    *(undefined1 *)((int)param_1 + 0x46d) = param_38[5];
    *(undefined1 *)((int)param_1 + 0x475) = param_39[5];
    *(undefined1 *)((int)param_1 + 0x47d) = param_40[5];
    *(undefined1 *)((int)param_1 + 0x46e) = param_38[6];
    *(undefined1 *)((int)param_1 + 0x476) = param_39[6];
    *(undefined1 *)((int)param_1 + 0x47e) = param_40[6];
    *(undefined1 *)((int)param_1 + 0x46f) = param_38[7];
    *(undefined1 *)((int)param_1 + 0x477) = param_39[7];
    *(undefined1 *)((int)param_1 + 0x47f) = param_40[7];
  }
  if (DAT_0209e204 != '\0') {
    param_5 = param_1[0xb];
    local_20 = 0;
    local_1c = 0x3e800000;
    local_18 = 0;
    cVar2 = FUN_009f5a00(param_1[0x120],param_1 + 10,&param_5,0,&local_20,uVar3);
    if (cVar2 != '\0') {
      param_1[0xb] = param_5;
      ExceptionList = local_10;
      return param_1;
    }
  }
  ExceptionList = local_10;
  return param_1;
}


