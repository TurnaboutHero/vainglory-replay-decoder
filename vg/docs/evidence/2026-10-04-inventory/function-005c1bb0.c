// 005c1bb0 FUN_005c1bb0

void __fastcall FUN_005c1bb0(int *param_1)

{
  int *piVar1;
  int *piVar2;
  char cVar3;
  int iVar4;
  uint uVar5;
  undefined4 uVar6;
  uint uVar7;
  uint uVar8;
  int iVar9;
  undefined4 local_c;
  
  piVar1 = param_1 + 0x45;
  piVar2 = (int *)*piVar1;
  uVar8 = 0;
  if (piVar2 != (int *)0x0) {
    if (param_1[0x46] != piVar2[1]) {
      *piVar1 = 0;
      param_1[0x46] = DAT_020ec6fc;
      (**(code **)(*param_1 + 0x98))();
      return;
    }
    iVar4 = (**(code **)(*piVar2 + 8))();
    if (iVar4 != 0) {
      uVar7 = 0;
      while( true ) {
        piVar2 = (int *)*piVar1;
        if (piVar2 != (int *)0x0) {
          if (param_1[0x46] == piVar2[1]) {
            (**(code **)(*piVar2 + 8))();
          }
          else {
            *piVar1 = 0;
            param_1[0x46] = DAT_020ec6fc;
          }
        }
        uVar5 = FUN_0093a6f0();
        if (uVar5 <= uVar7) break;
        piVar2 = (int *)*piVar1;
        if (piVar2 != (int *)0x0) {
          if (param_1[0x46] == piVar2[1]) {
            (**(code **)(*piVar2 + 8))();
          }
          else {
            *piVar1 = 0;
            param_1[0x46] = DAT_020ec6fc;
          }
        }
        uVar5 = FUN_00939ef0();
        if (uVar5 <= uVar7) break;
        piVar2 = (int *)*piVar1;
        if (piVar2 != (int *)0x0) {
          if (param_1[0x46] == piVar2[1]) {
            (**(code **)(*piVar2 + 8))();
          }
          else {
            *piVar1 = 0;
            param_1[0x46] = DAT_020ec6fc;
          }
        }
        uVar5 = FUN_00939ef0();
        if ((uVar5 <= uVar8) || (5 < (int)uVar8)) break;
        piVar2 = (int *)*piVar1;
        if (piVar2 != (int *)0x0) {
          if (param_1[0x46] == piVar2[1]) {
            (**(code **)(*piVar2 + 8))();
          }
          else {
            *piVar1 = 0;
            param_1[0x46] = DAT_020ec6fc;
          }
        }
        iVar4 = FUN_009393c0(uVar7);
        if (iVar4 != DAT_01265f34) {
          piVar2 = (int *)*piVar1;
          if (piVar2 != (int *)0x0) {
            if (param_1[0x46] == piVar2[1]) {
              (**(code **)(*piVar2 + 8))();
            }
            else {
              *piVar1 = 0;
              param_1[0x46] = DAT_020ec6fc;
            }
          }
          uVar6 = FUN_009392b0(iVar4);
          cVar3 = FUN_005a0790(uVar6);
          if (cVar3 == '\0') {
            iVar9 = iVar4;
            FUN_004a8e30(iVar4);
            cVar3 = FUN_0093d3d0(iVar9);
            if (cVar3 != '\0') {
              local_c = 0;
              if (((char)param_1[0xb0f] != '\0') || (*(char *)((int)param_1 + 0x2c3d) != '\0')) {
                local_c = 1;
              }
              FUN_005c17a0(uVar8,iVar4,0,local_c);
              uVar8 = uVar8 + 1;
            }
          }
        }
        uVar7 = uVar7 + 1;
      }
      uVar7 = 0;
      while( true ) {
        piVar2 = (int *)*piVar1;
        if (piVar2 != (int *)0x0) {
          if (param_1[0x46] == piVar2[1]) {
            (**(code **)(*piVar2 + 8))();
          }
          else {
            *piVar1 = 0;
            param_1[0x46] = DAT_020ec6fc;
          }
        }
        uVar5 = FUN_0093a6f0();
        if (uVar5 <= uVar7) break;
        piVar2 = (int *)*piVar1;
        if (piVar2 != (int *)0x0) {
          if (param_1[0x46] == piVar2[1]) {
            (**(code **)(*piVar2 + 8))();
          }
          else {
            *piVar1 = 0;
            param_1[0x46] = DAT_020ec6fc;
          }
        }
        uVar5 = FUN_00939ef0();
        if (uVar5 <= uVar7) break;
        piVar2 = (int *)*piVar1;
        if (piVar2 != (int *)0x0) {
          if (param_1[0x46] == piVar2[1]) {
            (**(code **)(*piVar2 + 8))();
          }
          else {
            *piVar1 = 0;
            param_1[0x46] = DAT_020ec6fc;
          }
        }
        uVar5 = FUN_00939ef0();
        if ((uVar5 <= uVar8) || (5 < (int)uVar8)) break;
        piVar2 = (int *)*piVar1;
        if (piVar2 != (int *)0x0) {
          if (param_1[0x46] == piVar2[1]) {
            (**(code **)(*piVar2 + 8))();
          }
          else {
            *piVar1 = 0;
            param_1[0x46] = DAT_020ec6fc;
          }
        }
        iVar4 = FUN_009393c0(uVar7);
        if (iVar4 != DAT_01265f34) {
          piVar2 = (int *)*piVar1;
          if (piVar2 != (int *)0x0) {
            if (param_1[0x46] == piVar2[1]) {
              (**(code **)(*piVar2 + 8))();
            }
            else {
              *piVar1 = 0;
              param_1[0x46] = DAT_020ec6fc;
            }
          }
          cVar3 = FUN_0093d3d0(iVar4);
          if (cVar3 == '\0') {
            piVar2 = (int *)*piVar1;
            if (piVar2 != (int *)0x0) {
              if (param_1[0x46] == piVar2[1]) {
                (**(code **)(*piVar2 + 8))();
              }
              else {
                *piVar1 = 0;
                param_1[0x46] = DAT_020ec6fc;
              }
            }
            if ((char)param_1[0xb0f] != '\0') {
              FUN_005c17a0(uVar8,iVar4,0,1);
              uVar8 = uVar8 + 1;
            }
          }
        }
        uVar7 = uVar7 + 1;
      }
      uVar7 = 0;
      param_1[0xb0d] = uVar8;
      while( true ) {
        piVar2 = (int *)*piVar1;
        if (piVar2 != (int *)0x0) {
          if (param_1[0x46] == piVar2[1]) {
            (**(code **)(*piVar2 + 8))();
          }
          else {
            *piVar1 = 0;
            param_1[0x46] = DAT_020ec6fc;
          }
        }
        uVar5 = FUN_0093a6f0();
        if (uVar5 <= uVar7) break;
        piVar2 = (int *)*piVar1;
        if (piVar2 != (int *)0x0) {
          if (param_1[0x46] == piVar2[1]) {
            (**(code **)(*piVar2 + 8))();
          }
          else {
            *piVar1 = 0;
            param_1[0x46] = DAT_020ec6fc;
          }
        }
        uVar5 = FUN_00939ef0();
        if (uVar5 <= uVar7) break;
        piVar2 = (int *)*piVar1;
        if (piVar2 != (int *)0x0) {
          if (param_1[0x46] == piVar2[1]) {
            (**(code **)(*piVar2 + 8))();
          }
          else {
            *piVar1 = 0;
            param_1[0x46] = DAT_020ec6fc;
          }
        }
        uVar5 = FUN_00939ef0();
        if ((uVar5 <= uVar8) || (5 < (int)uVar8)) break;
        piVar2 = (int *)*piVar1;
        if (piVar2 != (int *)0x0) {
          if (param_1[0x46] == piVar2[1]) {
            (**(code **)(*piVar2 + 8))();
          }
          else {
            *piVar1 = 0;
            param_1[0x46] = DAT_020ec6fc;
          }
        }
        uVar6 = FUN_009393c0(uVar7);
        piVar2 = (int *)*piVar1;
        if (piVar2 != (int *)0x0) {
          if (param_1[0x46] == piVar2[1]) {
            (**(code **)(*piVar2 + 8))();
          }
          else {
            *piVar1 = 0;
            param_1[0x46] = DAT_020ec6fc;
          }
        }
        cVar3 = FUN_0093d3d0(uVar6);
        if (cVar3 == '\0') {
          piVar2 = (int *)*piVar1;
          if (piVar2 != (int *)0x0) {
            if (param_1[0x46] == piVar2[1]) {
              (**(code **)(*piVar2 + 8))();
            }
            else {
              *piVar1 = 0;
              param_1[0x46] = DAT_020ec6fc;
            }
          }
          if ((char)param_1[0xb0f] == '\0') {
            FUN_005c17a0(uVar8,uVar6,0,1);
            uVar8 = uVar8 + 1;
          }
        }
        uVar7 = uVar7 + 1;
      }
      if (uVar8 < 6) {
        iVar4 = 6 - uVar8;
        do {
          FUN_005c4d10();
          iVar4 = iVar4 + -1;
        } while (iVar4 != 0);
      }
    }
  }
  (**(code **)(*param_1 + 0x98))();
  return;
}


