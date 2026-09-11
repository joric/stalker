@echo off

for /f "usebackq delims=" %%a in (".env") do set %%a

rem set image=%EXPORT_DIR%\Stalker2\Content\LevelBitmaps\T_Regions_Map.png
set image=T_Regions_Map.png

python %MAPS_TOOLS%\regions.py "%image%" --skip-color "#0000ff" --dest-res 812900 --simplify 5%% -o regions.json
