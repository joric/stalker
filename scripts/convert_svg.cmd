@echo off

svg2geojson T_Regions_Map.svg -d && move T_Regions_Map.geojson ..\data\regions.json


