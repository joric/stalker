@echo off

set repo=C:\Temp\github\Ue4Export
set dest=D:\Shared\Tools\Hacking\Games\UE\Ue4Export

cd /d %repo%

dotnet publish -p:DebugType=None -r win-x64 -c Release --self-contained false || exit

copy /Y %repo%\Ue4Export\bin\Release\net8.0\win-x64\publish\*.* %dest%
