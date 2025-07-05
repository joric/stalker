@echo off

set path=D:\Shared\Tools\Hacking\Games\UE\S2HOCMM;%path%

set gamePath="E:\Games\S.T.A.L.K.E.R. 2.Heart.of.Chornobyl.Ultimate.Editon-InsaneRamZes"
set mergeLocalizationFrom=".\JSONs"
set saveModTo=".\ModOutput\Pak\localization_P.utoc"
set localizationDBFolder=".\LocalizationDB"
set mergeOutputFolder=".\Merged"
set buildFolder=".\ModOutput\Source"
set unrealReZenPath=".\UnrealReZen.exe"
set outputFormat=Localization_{0}.json
set aeskey=0x33A604DF49A07FFD4A4C919962161F5C35A134D37EFA98DB37A34F6450D7D386

mkdir %mergeLocalizationFrom%

S2HOCMM.exe -Extract --game %gamePath% --aes %aeskey% --output %localizationDBFolder% || goto :error

S2HOCMM.exe -Merge --input %mergeLocalizationFrom% --localizationdb %localizationDBFolder% --output %mergeOutputFolder% --format %outputFormat% || goto :error

copy %mergeOutputFolder%\*_UA.json ..\data\Localization\
copy %mergeOutputFolder%\*_EN.json ..\data\Localization\
copy %mergeOutputFolder%\*_FR.json ..\data\Localization\
copy %mergeOutputFolder%\*_RU.json ..\data\Localization\

exit 0

:error
echo Error occured, stopping
pause
exit 1
