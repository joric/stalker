@echo off

rem download Ue4Export here: https://github.com/CrystalFerrai/Ue4Export
rem assetlist.txt must have [Text] as a first line (ini header) to export files as json

set exe=D:\Shared\Tools\Hacking\Games\UE\Ue4Export\Ue4Export.exe
rem set exe=C:\Temp\github\Ue4Export\Ue4Export\bin\Release\net8.0\win-x64\publish\Ue4Export.exe

set gamePath=E:\Games\S.T.A.L.K.E.R. 2.Heart.of.Chornobyl.Ultimate.Editon-InsaneRamZes\
set mappings="%gamePath%\Stalker2.usmap"
set paks="%gamePath%\Stalker2\Content\Paks"
set key=0x33A604DF49A07FFD4A4C919962161F5C35A134D37EFA98DB37A34F6450D7D386
set options=--mix-output --key %key% --mappings %mappings% %paks% UE5_1

set out=C:\Temp\Exports

%exe% %options% %~dp0\assetlist.txt %out%

if exist %~dp0\missing_files.txt (
	%exe% %options% %~dp0\missing_files.txt %out%
)
