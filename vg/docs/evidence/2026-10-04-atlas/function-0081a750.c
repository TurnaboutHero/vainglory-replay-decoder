// 0081a750 FUN_0081a750

undefined4 * __thiscall
FUN_0081a750(undefined4 *param_1,undefined4 param_2,undefined4 param_3,undefined4 param_4,
            undefined1 param_5,undefined1 param_6,undefined8 *param_7,undefined8 *param_8,
            undefined4 param_9,undefined1 param_10,undefined4 param_11,undefined4 param_12,
            undefined4 param_13,undefined4 param_14,undefined1 param_15,undefined1 param_16,
            undefined1 *param_17,undefined1 *param_18,undefined1 *param_19,undefined4 param_20,
            undefined4 param_21,undefined4 param_22,undefined4 param_23)

{
  param_1[4] = param_2;
  param_1[5] = param_3;
  param_1[6] = param_4;
  *(undefined1 *)(param_1 + 7) = param_5;
  *(undefined1 *)((int)param_1 + 0x1d) = param_6;
  param_1[1] = 0;
  param_1[2] = 0;
  *(undefined1 *)(param_1 + 3) = 0;
  *param_1 = Nuo::Kindred::ActionEntitySpawn::vftable;
  *(undefined8 *)(param_1 + 8) = *param_7;
  param_1[10] = *(undefined4 *)(param_7 + 1);
  *(undefined8 *)(param_1 + 0xb) = *param_8;
  param_1[0xd] = *(undefined4 *)(param_8 + 1);
  FUN_0081f5d0(param_9);
  param_1[0xd4] = param_23;
  *(undefined1 *)(param_1 + 0xd5) = param_10;
  param_1[0xd6] = param_11;
  param_1[0xd7] = param_12;
  param_1[0xd8] = param_13;
  param_1[0xdf] = param_20;
  param_1[0xe0] = param_21;
  param_1[0xe1] = param_22;
  param_1[0xe2] = param_14;
  *(undefined1 *)(param_1 + 0xe3) = param_15;
  *(undefined1 *)((int)param_1 + 0x38d) = param_16;
  if (((param_17 == (undefined1 *)0x0) && (param_18 == (undefined1 *)0x0)) &&
     (param_19 == (undefined1 *)0x0)) {
    FUN_00871f30(*(undefined1 *)((int)param_1 + 0x1d),param_1 + 0xd9,param_1 + 0xdb,param_1 + 0xdd);
    return param_1;
  }
  *(undefined1 *)(param_1 + 0xd9) = *param_17;
  *(undefined1 *)(param_1 + 0xdb) = *param_18;
  *(undefined1 *)(param_1 + 0xdd) = *param_19;
  *(undefined1 *)((int)param_1 + 0x365) = param_17[1];
  *(undefined1 *)((int)param_1 + 0x36d) = param_18[1];
  *(undefined1 *)((int)param_1 + 0x375) = param_19[1];
  *(undefined1 *)((int)param_1 + 0x366) = param_17[2];
  *(undefined1 *)((int)param_1 + 0x36e) = param_18[2];
  *(undefined1 *)((int)param_1 + 0x376) = param_19[2];
  *(undefined1 *)((int)param_1 + 0x367) = param_17[3];
  *(undefined1 *)((int)param_1 + 0x36f) = param_18[3];
  *(undefined1 *)((int)param_1 + 0x377) = param_19[3];
  *(undefined1 *)(param_1 + 0xda) = param_17[4];
  *(undefined1 *)(param_1 + 0xdc) = param_18[4];
  *(undefined1 *)(param_1 + 0xde) = param_19[4];
  *(undefined1 *)((int)param_1 + 0x369) = param_17[5];
  *(undefined1 *)((int)param_1 + 0x371) = param_18[5];
  *(undefined1 *)((int)param_1 + 0x379) = param_19[5];
  *(undefined1 *)((int)param_1 + 0x36a) = param_17[6];
  *(undefined1 *)((int)param_1 + 0x372) = param_18[6];
  *(undefined1 *)((int)param_1 + 0x37a) = param_19[6];
  *(undefined1 *)((int)param_1 + 0x36b) = param_17[7];
  *(undefined1 *)((int)param_1 + 0x373) = param_18[7];
  *(undefined1 *)((int)param_1 + 0x37b) = param_19[7];
  return param_1;
}


