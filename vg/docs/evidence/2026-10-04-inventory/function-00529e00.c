// 00529e00 FUN_00529e00

void FUN_00529e00(void)

{
  undefined4 *puVar1;
  char cVar2;
  int iVar3;
  undefined4 *puVar4;
  undefined4 *puVar5;
  char *pcVar6;
  undefined4 *puVar7;
  uint uVar8;
  
  pcVar6 = "method_onRejectBuyItem";
  uVar8 = 0x811c9dc5;
  cVar2 = 'm';
  do {
    pcVar6 = pcVar6 + 1;
    uVar8 = ((int)cVar2 ^ uVar8) * 0x1000193;
    cVar2 = *pcVar6;
  } while (cVar2 != '\0');
  iVar3 = FUN_00966080();
  puVar1 = *(undefined4 **)(iVar3 + 4);
  puVar4 = (undefined4 *)puVar1[1];
  puVar7 = puVar1;
  if (*(char *)((int)puVar1[1] + 0xd) == '\0') {
    do {
      if ((uint)puVar4[4] < uVar8) {
        puVar5 = (undefined4 *)puVar4[2];
      }
      else {
        puVar5 = (undefined4 *)*puVar4;
        puVar7 = puVar4;
      }
      puVar4 = puVar5;
    } while (*(char *)((int)puVar5 + 0xd) == '\0');
    if ((puVar7 != puVar1) && ((uint)puVar7[4] <= uVar8)) goto LAB_00529e56;
  }
  puVar7 = puVar1;
LAB_00529e56:
  if ((puVar7 != puVar1) && (uVar8 = 0, puVar7[5] != 0)) {
    do {
      (**(code **)(puVar7[7] + 4 + uVar8 * 8))(*(undefined4 *)(puVar7[7] + uVar8 * 8));
      uVar8 = uVar8 + 1;
    } while (uVar8 < (uint)puVar7[5]);
  }
  return;
}


