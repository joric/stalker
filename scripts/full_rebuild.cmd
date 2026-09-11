@echo off
set out=C:\Temp\Exports

if not exist "%out%\Stalker2" goto :skip_backup
set "postfix_count=1"

:backup_loop
if exist "%out%\Stalker2_%postfix_count%" (
    set /a postfix_count+=1
    goto :backup_loop
)

move "%out%\Stalker2" "%out%\Stalker2_%postfix_count%"

:skip_backup

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
