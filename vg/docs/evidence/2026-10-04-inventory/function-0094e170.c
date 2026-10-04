// 0094e170 FUN_0094e170

void __fastcall FUN_0094e170(int param_1)

{
  char cVar1;
  int iVar2;
  int iVar3;
  int iVar4;
  int *piVar5;
  uint uVar6;
  undefined4 uVar7;
  undefined4 *puVar8;
  uint uVar9;
  uint uVar10;
  uint uVar11;
  uint uVar12;
  uint *puVar13;
  undefined1 *puVar14;
  uint uVar15;
  uint uVar16;
  undefined4 uVar17;
  undefined4 uVar18;
  undefined4 local_358;
  int local_354;
  int local_350;
  uint local_34c;
  uint local_348;
  uint local_344;
  int local_340 [128];
  int local_140 [70];
  int local_28 [9];
  
  local_28[8] = DAT_01e44f28 ^ (uint)&stack0xfffffffc;
  iVar2 = FUN_00857970(*(undefined4 *)(param_1 + 0x18));
  if (iVar2 != 0) goto LAB_0094e95d;
  local_350 = iVar2;
  FUN_01129ea0(**(undefined4 **)(**(int **)(DAT_0209e200 + 0x20) + *(int *)(param_1 + 0x10) * 4),
               &local_350,1,0);
  iVar2 = local_350;
  local_354 = local_350;
  *(undefined4 *)(local_350 + 0x178) = *(undefined4 *)(param_1 + 0x18);
  *(undefined1 *)(local_350 + 0x1f0) = *(undefined1 *)(param_1 + 0x1c);
  *(undefined1 *)(local_350 + 0x17c) = *(undefined1 *)(param_1 + 0x1d);
  FUN_0095d140(*(undefined4 *)(param_1 + 0x10));
  *(uint *)(iVar2 + 500) =
       *(uint *)(iVar2 + 500) ^ (*(uint *)(iVar2 + 500) ^ *(uint *)(param_1 + 0x460)) & 0x3ff;
  iVar3 = FUN_00857970(*(undefined4 *)(param_1 + 0x484));
  if (iVar3 == 0) {
    *(undefined4 *)(iVar2 + 0x1c8) = 0;
    uVar7 = DAT_020ec6fc;
  }
  else {
    *(int *)(iVar2 + 0x1c8) = iVar3 + 0x14;
    uVar7 = *(undefined4 *)(iVar3 + 0x18);
  }
  *(undefined4 *)(iVar2 + 0x1cc) = uVar7;
  local_344 = *(undefined4 *)(param_1 + 0x10);
  if ((*(int *)(param_1 + 0x18) != -1) && (uVar6 = 0, iVar3 = DAT_020e7404, DAT_020e7408 != 0)) {
    do {
      if (*(int *)(iVar3 + 4) == *(int *)(param_1 + 0x18)) {
        if (iVar3 != 0) {
          *(uint *)(iVar3 + 0x78) = local_344;
        }
        break;
      }
      uVar6 = uVar6 + 1;
      iVar3 = iVar3 + 0xb8;
    } while (uVar6 < DAT_020e7408);
  }
  if (*(int *)(param_1 + 0x498) != 0) {
    FUN_0112ab70(*(int *)(param_1 + 0x498));
    *(undefined4 *)(param_1 + 0x498) = 0;
  }
  local_358 = 0;
  FUN_0112ac50(&local_358,1,DAT_01ef3aec,0);
  if ((*(int *)(param_1 + 0x10) != 0xffff) &&
     (iVar3 = FUN_00856900(**(undefined4 **)
                             (**(int **)(DAT_0209e200 + 0x20) + *(int *)(param_1 + 0x10) * 4)),
     iVar3 != 0)) {
    iVar4 = *(int *)(iVar3 + 100);
    uVar7 = 5;
    if ((*(int *)(iVar3 + 0x60) < iVar4) && (*(int *)(iVar3 + 0x68) < iVar4)) {
      uVar7 = 1;
    }
    if ((*(int *)(iVar3 + 0x60) < *(int *)(iVar3 + 0x68)) && (iVar4 < *(int *)(iVar3 + 0x68))) {
      uVar7 = 0;
    }
    *(undefined4 *)(iVar2 + 0x18c) = uVar7;
  }
  local_344 = *(uint *)(param_1 + 0x20);
  if (local_344 != 0xff) {
    iVar3 = *(int *)(param_1 + 0x18);
    cVar1 = FUN_00944430(iVar3);
    uVar6 = DAT_020e7408;
    iVar4 = DAT_020e7404;
    if (cVar1 != '\0') {
      if ((iVar3 != -1) && (uVar9 = 0, iVar3 = DAT_020e7404, DAT_020e7408 != 0)) {
        do {
          iVar2 = local_354;
          if (*(int *)(iVar3 + 4) == *(int *)(param_1 + 0x18)) {
            if (iVar3 != 0) {
              *(uint *)(iVar3 + 0x80) = local_344;
            }
            break;
          }
          uVar9 = uVar9 + 1;
          iVar3 = iVar3 + 0xb8;
        } while (uVar9 < DAT_020e7408);
      }
      local_344 = *(uint *)(param_1 + 0x24);
      if ((*(int *)(param_1 + 0x18) != -1) && (uVar9 = 0, uVar6 != 0)) {
        do {
          if (*(int *)(iVar4 + 4) == *(int *)(param_1 + 0x18)) {
            if (iVar4 != 0) {
              *(uint *)(iVar4 + 0x84) = local_344;
            }
            break;
          }
          uVar9 = uVar9 + 1;
          iVar4 = iVar4 + 0xb8;
        } while (uVar9 < uVar6);
      }
    }
  }
  FUN_0093fba0(*(undefined4 *)(param_1 + 0x360),param_1 + 0x14,*(undefined4 *)(param_1 + 0x480),
               param_1 + 0x28,param_1 + 0x34);
  FUN_009419d0();
  if (*(int *)(param_1 + 0x360) == 0) {
    FUN_00941ac0();
  }
  if (*(char *)(param_1 + 0x358) == '\0') {
    FUN_0095c940(param_1 + 0x40);
  }
  if (*(int *)(param_1 + 0x498) == 0) {
    local_348 = *(uint *)(param_1 + 0x49c);
    for (iVar3 = *(int *)(iVar2 + 0xc); iVar3 != 0; iVar3 = *(int *)(iVar3 + 0x10)) {
      if (*(int *)(*(int *)(iVar3 + 4) + 0x54) == DAT_01ef0b48) {
        local_28[0] = 0;
        local_28[1] = 0;
        local_28[2] = 0;
        local_28[3] = 0;
        local_28[4] = 0;
        local_28[5] = 0;
        local_28[6] = 0;
        local_28[7] = 0;
        uVar6 = FUN_0112a700(local_340,8,DAT_020e9cc8);
        uVar9 = 0;
        if (uVar6 != 0) goto LAB_0094e472;
        goto LAB_0094e487;
      }
    }
    goto LAB_0094e4cd;
  }
  goto LAB_0094e4e9;
code_r0x0094e708:
  local_344 = *(int *)(local_344 + 0x10);
  if (local_344 == 0) goto LAB_0094e760;
  goto LAB_0094e700;
  while( true ) {
    local_28[uVar9] = local_340[uVar9];
    uVar9 = uVar9 + 1;
    if (uVar6 <= uVar9) break;
LAB_0094e472:
    if (7 < uVar9) break;
  }
LAB_0094e487:
  uVar6 = 0;
  if (local_348 != 0) {
    puVar8 = (undefined4 *)(param_1 + 0x4c0);
    do {
      iVar3 = local_28[uVar6];
      if ((iVar3 != 0) && (*(int *)(iVar3 + 0x20) == puVar8[-8])) {
        *(undefined4 *)(iVar3 + 0x28) = *puVar8;
        *(bool *)(iVar3 + 0x30) = puVar8[8] != 0;
      }
      uVar6 = uVar6 + 1;
      puVar8 = puVar8 + 1;
    } while (uVar6 < local_348);
  }
LAB_0094e4cd:
  if (*(int *)(param_1 + 0x500) != 0) {
    FUN_0092fc40(*(int *)(param_1 + 0x500),*(undefined4 *)(param_1 + 0x504));
  }
LAB_0094e4e9:
  if (1 < *(uint *)(param_1 + 0x464)) {
    uVar6 = 1;
    do {
      FUN_00944de0(1);
      uVar6 = uVar6 + 1;
    } while (uVar6 < *(uint *)(param_1 + 0x464));
  }
  FUN_0095eb50(param_1 + 0x28,param_1 + 0x34);
  if (*(int *)(param_1 + 0x458) != 0) {
    FUN_0095c380(param_1 + 0x43c,param_1 + 0x430,param_1 + 0x448,param_1 + 0x454,
                 *(int *)(param_1 + 0x458));
  }
  if (DAT_0209e204 == '\0') {
    FUN_004a8f80(iVar2,*(undefined1 *)(param_1 + 0x1c));
  }
  if (*(char *)(param_1 + 0x358) == '\0') {
    local_348 = 0;
    if (*(int *)(param_1 + 0x45c) != 0) {
      puVar8 = (undefined4 *)(param_1 + 0x408);
      do {
        FUN_0093d080(puVar8[-0x28],puVar8[-0x1e],0,puVar8[-0x14],*puVar8,puVar8[-10]);
        puVar8 = puVar8 + 1;
        local_348 = local_348 + 1;
      } while (local_348 < *(uint *)(param_1 + 0x45c));
    }
LAB_0094e68a:
    if (DAT_0209e204 != '\0') {
      if (*(char *)(param_1 + 0x359) != '\0') {
        guard_check_icall(iVar2,*(undefined4 *)(param_1 + 0x10),*(undefined4 *)(param_1 + 0x14));
      }
      iVar3 = *(int *)(param_1 + 0x35c);
      if (iVar3 == 0) {
        if (*(char *)(param_1 + 0x359) == '\0') {
          iVar3 = *(int *)(*(int *)(iVar2 + 0x1c) + 4);
        }
        else {
          iVar3 = FUN_00937950();
        }
      }
      guard_check_icall(iVar2,iVar3,*(undefined4 *)(param_1 + 0x460));
    }
  }
  else if (DAT_0209e204 != '\0') {
    if (*(int *)(param_1 + 0x45c) != 0) {
      local_344 = 0;
      puVar13 = (uint *)(param_1 + 0x368);
      do {
        local_348 = FUN_00590930();
        local_34c = *puVar13;
        uVar18 = 0;
        uVar7 = **(undefined4 **)(**(int **)(DAT_0209e200 + 0x20) + local_34c * 4);
        uVar17 = 0;
        FUN_0112a790(0,uVar7,0);
        iVar3 = FUN_0112ab50(uVar17,uVar7,uVar18);
        if (((((*(char *)(iVar3 + 0x1c) != '\0') && (*(char *)(iVar3 + 0x123) != '\0')) &&
             (*(int *)(local_348 + 8) != 0)) && (cVar1 = FUN_00558e40(), cVar1 != '\0')) ||
           (cVar1 = FUN_0086fed0(local_34c), cVar1 != '\0')) {
          FUN_008725f0(*puVar13);
        }
        puVar13 = puVar13 + 1;
        local_344 = local_344 + 1;
      } while (local_344 < *(uint *)(param_1 + 0x45c));
    }
    goto LAB_0094e68a;
  }
  guard_check_icall(iVar2);
  FUN_004a8db0(iVar2);
  local_344 = *(int *)(iVar2 + 0xc);
  if (local_344 != 0) {
LAB_0094e700:
    if (*(int *)(*(int *)(local_344 + 4) + 0x54) != DAT_02091598) goto code_r0x0094e708;
    puVar14 = (undefined1 *)(param_1 + 0x470);
    local_34c = -param_1 - 0x470;
    do {
      FUN_00945dd0((char)puVar14 + (char)local_34c,puVar14[-8],*puVar14,puVar14[8]);
      puVar14 = puVar14 + 1;
    } while (puVar14 + local_34c < &DAT_00000008);
  }
LAB_0094e760:
  FUN_01129d20(DAT_020e9c28);
  if (((*(byte *)(iVar2 + 0x1e0) & 1) != 0) &&
     ((*(int *)(param_1 + 0x360) == 2 || (*(int *)(param_1 + 0x360) == 1)))) {
    iVar3 = FUN_01129d20(DAT_01ef0b44);
    *(undefined4 *)(iVar3 + 0x14) = *(undefined4 *)(param_1 + 0x364);
    *(undefined4 *)(iVar3 + 0x18) = 0;
  }
  if (DAT_0209e204 != '\0') {
    (**(code **)(param_1 + 0x490))(iVar2,*(undefined1 *)(param_1 + 0x494));
  }
  if (*(code **)(param_1 + 0x488) != (code *)0x0) {
    (**(code **)(param_1 + 0x488))(iVar2,*(undefined4 *)(param_1 + 0x48c));
  }
  iVar3 = *(int *)(*(int *)(iVar2 + 0x1c) + 0x44);
  if ((iVar3 != 0) && (iVar3 = FUN_0096c7a0(iVar3), iVar3 != 0)) {
    iVar3 = *(int *)(*(int *)(iVar2 + 0x1c) + 0x44);
    if (iVar3 == 0) {
      uVar7 = 0;
    }
    else {
      uVar7 = FUN_0096c7a0(iVar3,0x12345678);
      uVar7 = FUN_004c4450(iVar3,uVar7);
    }
    iVar3 = FUN_00936bd0(uVar7);
    FUN_009432c0(*(undefined4 *)(*(int *)(iVar2 + 0x2c) + 0x28 + iVar3 * 4));
  }
  uVar6 = FUN_0112ac50(local_140,0x46,DAT_01ef3360,0);
  local_344 = 0;
  local_34c = uVar6;
  if (uVar6 != 0) {
    do {
      uVar9 = local_344;
      iVar3 = local_354;
      if (local_140[local_344] != 0) {
        uVar15 = 0;
        uVar6 = 1;
        uVar16 = 0;
        do {
          uVar10 = ((int)"onEntitySpawned"[uVar16] + uVar6) % 0xfff1;
          uVar11 = ((int)"onEntitySpawned"[uVar16 + 1] + uVar10) % 0xfff1;
          uVar12 = ((int)"onEntitySpawned"[uVar16 + 2] + uVar11) % 0xfff1;
          iVar2 = uVar16 + 3;
          uVar16 = uVar16 + 4;
          uVar6 = ((int)"onEntitySpawned"[iVar2] + uVar12) % 0xfff1;
          uVar15 = ((((uVar15 + uVar10) % 0xfff1 + uVar11) % 0xfff1 + uVar12) % 0xfff1 + uVar6) %
                   0xfff1;
        } while (uVar16 < 0x10);
        FUN_00536dd0(0,1,uVar15 << 0x10 | uVar6,local_354);
        uVar6 = local_34c;
        iVar2 = iVar3;
      }
      local_344 = uVar9 + 1;
    } while (local_344 < uVar6);
  }
  if (DAT_0209e204 != '\0') {
    piVar5 = (int *)FUN_01129d20(DAT_020e9c2c);
    (**(code **)(*piVar5 + 0xc))();
    if (DAT_0209e204 != '\0') goto LAB_0094e95d;
  }
  if (DAT_0209e205 == '\0') {
    FUN_0054ff00(*(undefined4 *)(iVar2 + 0x178));
  }
LAB_0094e95d:
  __security_check_cookie(local_28[8] ^ (uint)&stack0xfffffffc);
  return;
}


