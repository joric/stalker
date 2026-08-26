@echo off
set out=C:\Temp\Exports

:: Delete directory (ignore if doesn't exist)
if exist "%out%\Stalker2" (
    rmdir /s /q "%out%\Stalker2"
) else (
    echo Directory not found, skipping...
)

:: Delete missing files (ignore if none exist)
del /q missing_*.txt 2>nul

:: Run commands with proper error checking
call export_assets.cmd
if errorlevel 1 exit /b 1

call convert_bin.cmd
if errorlevel 1 exit /b 1

:: Delete cache.json if it exists
if exist cache.json (
    del /q cache.json
) else (
    echo cache.json not found, skipping...
)

python build_markers.py
if errorlevel 1 exit /b 1

call export_assets.cmd
if errorlevel 1 exit /b 1

python build_markers.py
if errorlevel 1 exit /b 1

python build_icons.py
if errorlevel 1 exit /b 1

call export_assets.cmd
if errorlevel 1 exit /b 1

python build_icons.py
if errorlevel 1 exit /b 1

python build_sprites.py
if errorlevel 1 exit /b 1

call copy_lang.cmd
if errorlevel 1 exit /b 1

git add ../images/icons
if errorlevel 1 exit /b 1

git add ../images/sprites
if errorlevel 1 exit /b 1

echo All OK
