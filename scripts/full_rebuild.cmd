@echo off
set out=C:\Temp\Exports

rmdir /s /q "%out%\Stalker2" 2>nul
del /q missing_*.txt 2>nul
del /q cache.json 2>nul

call export_assets.cmd || exit /b 1
call convert_bin.cmd || exit /b 1
python build_markers.py || exit /b 1
call export_assets.cmd || exit /b 1
python build_markers.py || exit /b 1
python build_icons.py || exit /b 1
call export_assets.cmd || exit /b 1
python build_icons.py || exit /b 1
python build_sprites.py || exit /b 1
call copy_lang.cmd || exit /b 1

git add ../images/icons
git add ../images/sprites

echo All OK
