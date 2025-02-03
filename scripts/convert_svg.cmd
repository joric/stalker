@echo off

svg2geojson T_Regions_Map.svg -d && copy T_Regions_Map.geojson ..\data\regions.json


