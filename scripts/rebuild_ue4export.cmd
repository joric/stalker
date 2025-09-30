@echo off

set repo=C:\Temp\github\Ue4Export
set dest=D:\Shared\Tools\Hacking\Games\UE\Ue4Export

cd /d %repo%

dotnet publish -p:DebugType=None -r win-x64 -c Release --self-contained false || exit

copy /Y %repo%\Ue4Export\bin\Release\net8.0\win-x64\publish\*.* %dest%
copy /Y %repo%\CUE4Parse\CUE4Parse-Conversion\Resources\*.dll %dest%

set exe=%dest%\Ue4Export.exe

cd /d %~dp0

echo [Texture] > test_assetlist.txt
echo Stalker2/Content/GameLite/FPS_Game/UI/UIIcons/Markers/itr7/NotActive/Shadow/Texture_Signal_NotActive_General_Shadow.uasset >> test_assetlist.txt

set gamePath=E:\Games\S.T.A.L.K.E.R. 2.Heart.of.Chornobyl.Ultimate.Editon-InsaneRamZes\
set mappings="%gamePath%\Stalker2.usmap"
set paks="%gamePath%\Stalker2\Content\Paks"
set key=0x33A604DF49A07FFD4A4C919962161F5C35A134D37EFA98DB37A34F6450D7D386
set options=--mix-output --key %key% --mappings %mappings% %paks% UE5_1

set out=C:\Temp\Exports

%exe% %options% %~dp0\test_assetlist.txt %out%


