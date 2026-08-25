@echo off
setlocal EnableDelayedExpansion

rem /Game/GameLite/FPS_Game/UIRemaster/UITextures/Inventory/Consumable/T_cns_water
rem /Game/_DLC1/UI/UITextures/Inventory/QuestItems/T_QuestItem_Nord_patch
rem /Game/_Stalker_2/items/device/SM_dev_binocular/SM_dev_Binocular_01/T_inv_binocular_01

set content=C:\Temp\Exports\Stalker2\Content

for %%B in (
  "GameLite\FPS_Game\UIRemaster\UITextures\Inventory"
  "_DLC1\UI\UITextures\Inventory"
) do (
  set base=%%~B
  for %%I in (Ammo Armor Artifacts Attach Consumable Detectors Grenades Quest QuestItems WeaponAndAttachments) do (
    set dest=..\Images\Game\!base!\%%I\
    mkdir !dest!
    for %%F in (%content%\!base!\%%I\*T_*.png) do (
      set filename=%%~nxF
      if not "!filename:upgrade.png=!"=="!filename!" (
        rem Skip files ending with upgrade.png
      ) else (
        copy "%%F" "!dest!"
      )
    )
  )
)
