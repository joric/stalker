@echo off

set out=C:\Temp\Exports

rmdir /s /q "%out%\Stalker2"

del /q missing_*.txt

call export_assets.cmd

call convert_bin.cmd

del cache.json

python build_markers.py
python build_icons.py

call export_assets.cmd

python build_markers.py
python build_icons.py

python build_sprites.py

call copy_lang.cmd

git add ../images/icons
git add ../images/sprites

echo All OK
