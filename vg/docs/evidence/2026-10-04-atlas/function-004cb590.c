// 004cb590 FUN_004cb590

void FUN_004cb590(void *param_1,undefined4 param_2)

{
  char cVar1;
  ushort uVar2;
  undefined4 local_8;
  
  cVar1 = FUN_00943900();
  if (cVar1 != '\0') {
    local_8 = 0;
    memmove(&local_8,param_1,2);
    uVar2 = Ordinal_15(local_8);
    if (uVar2 < 0x3ed) {
      if (0x3e9 < uVar2) {
        return;
      }
      if (uVar2 == 0) {
        return;
      }
    }
    else {
      switch(uVar2) {
      case 0x411:
      case 0x412:
      case 0x413:
      case 0x42e:
      case 0x433:
      case 0x435:
      case 0x436:
      case 0x437:
      case 0x439:
      case 0x44e:
      case 0x451:
      case 0x453:
      case 0x454:
      case 0x459:
      case 0x45a:
      case 0x45b:
      case 0x46c:
      case 0x473:
      case 0x475:
      case 0x479:
      case 0x47a:
      case 0x47c:
      case 0x47d:
        goto switchD_004cb5eb_caseD_411;
      case 0x46f:
        DAT_01ef0b2e = 1;
      }
    }
    FUN_009546f0(param_1,param_2,DAT_01ef0b30);
  }
switchD_004cb5eb_caseD_411:
  return;
}


