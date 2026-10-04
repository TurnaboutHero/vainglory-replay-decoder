// 0093e940 FUN_0093e940

void __thiscall
FUN_0093e940(int param_1,int param_2,int param_3,float param_4,undefined4 param_5,undefined4 param_6
            )

{
  float10 fVar1;
  float fVar2;
  float fVar3;
  float fVar4;
  
  if (((char)param_6 == '\0') && (0.0 < param_4)) {
    if (param_2 == 0) {
      fVar4 = *(float *)(param_1 + 0x188) + DAT_012142c4;
      fVar2 = ((*(float *)(param_1 + 0x23c) + DAT_012142c4) * *(float *)(param_1 + 0xd4) +
              *(float *)(param_1 + 0x20)) * fVar4;
      fVar3 = DAT_020e7348;
      if (fVar2 <= DAT_020e7348) {
        fVar3 = fVar2;
      }
      if (fVar3 <= DAT_01a76098) {
        fVar3 = DAT_01a76098;
      }
      if (param_3 == 2) {
        fVar4 = *(float *)(param_1 + 0xd4) + *(float *)(param_1 + 0x20);
      }
      fVar3 = (((fVar4 * param_4 + fVar3) - fVar3) * *(float *)(param_1 + 0x2f0)) / fVar3;
      if (0.0 < fVar3) {
        *(float *)(param_1 + 0x2f0) = fVar3 + *(float *)(param_1 + 0x2f0);
      }
    }
    else if (param_2 == 2) {
      fVar4 = *(float *)(param_1 + 400) + DAT_012142c4;
      fVar2 = ((*(float *)(param_1 + 0x244) + DAT_012142c4) * *(float *)(param_1 + 0xdc) +
              *(float *)(param_1 + 0x28)) * fVar4;
      fVar3 = DAT_020e7350;
      if (fVar2 <= DAT_020e7350) {
        fVar3 = fVar2;
      }
      if (fVar3 <= DAT_01a760a0) {
        fVar3 = DAT_01a760a0;
      }
      if (param_3 == 2) {
        fVar4 = *(float *)(param_1 + 0xdc) + *(float *)(param_1 + 0x28);
      }
      fVar3 = (((fVar4 * param_4 + fVar3) - fVar3) * *(float *)(param_1 + 0x2f8)) / fVar3;
      if (0.0 < fVar3) {
        *(float *)(param_1 + 0x2f8) = fVar3 + *(float *)(param_1 + 0x2f8);
      }
    }
  }
  fVar1 = (float10)FUN_00937480(param_2,param_3);
  FUN_0095c710(param_2,param_3,(float)(fVar1 + (float10)param_4),param_5,param_6);
  return;
}


