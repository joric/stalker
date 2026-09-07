#!/usr/bin/env bash
# Reconstruye todo, del juego instalado a los datos del visor web.
#
# Existe porque el DLC va a cambiar el Landscape y esto hay que poder rehacerlo
# de un comando, no encadenando seis pasos a mano.
#
#   ./tools/build_all.sh
#
# Entradas, todas configurables por variable de entorno (ver README):
#   STALKER2_DIR   el juego instalado
#   RETOC_BIN      el binario de retoc
#   TELEPORT_UTOC  el .utoc del mod Teleport, para las coordenadas de calibracion
#   MARKERS_DIR    data/ del repo joric/stalker, para los nombres del buscador
#   WORK_DIR       trabajo intermedio (~2 GB, regenerable)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
GAME="${STALKER2_DIR:-$HOME/.local/share/Steam/steamapps/common/S.T.A.L.K.E.R. 2 Heart of Chornobyl}"
RETOC="${RETOC_BIN:-$ROOT/refs/retoc/retoc}"
TELEPORT="${TELEPORT_UTOC:-$ROOT/refs/Teleport/TeleportStalker2-Windows.utoc}"
MARKERS="${MARKERS_DIR:-$ROOT/refs/stalker/data}"
WORK="${WORK_DIR:-$ROOT/tmp/build}"
OUT="$ROOT/data"
CELLS="$WORK/terr/Stalker2/Content/_Stalker_2/maps/_Stalker2_WorldMap/WorldMap_WP/_Generated_"
HLODS="$WORK/hlod/Stalker2/Content/_Stalker_2/maps/_Stalker2_WorldMap/WorldMap_WP/_Generated_"
T="$ROOT/tools"

# Las quince celdas sin Landscape. Si el DLC agrega terreno, esta lista cambia:
# la imprime build_heightfield.py como "aviso".
HOLES="X-5Y1 X-4Y1 X-3Y-6 X-3Y-3 X-2Y4 X-1Y-2 X-1Y0 X-1Y2 X0Y-3 X0Y-1 X0Y4 X1Y4 X2Y2 X5Y1 X6Y4"

for f in "$RETOC" "$TELEPORT" "$MARKERS/markers.json"; do
  [ -e "$f" ] || { echo "falta: $f — ver el README" >&2; exit 1; }
done
[ -d "$GAME/Stalker2/Content/Paks" ] || { echo "falta el juego en $GAME" >&2; exit 1; }

echo "==> trabajo en $WORK"
mkdir -p "$WORK" "$OUT"

echo "==> 1/6 extrayendo las celdas del Landscape"
"$RETOC" to-legacy --no-shaders -f "Terrain_L0_X" "$GAME/Stalker2/Content/Paks" "$WORK/terr" | tail -1

echo "==> 2/6 extrayendo los HLOD de las celdas sin Landscape"
for c in $HOLES; do
  "$RETOC" to-legacy --no-shaders -f "HLOD_Terrain_L0_$c" "$GAME/Stalker2/Content/Paks" "$WORK/hlod" >/dev/null 2>&1 || true
done

echo "==> 3/6 pegando el heightfield"
python3 "$T/build_heightfield.py" "$CELLS" "$WORK/height.npy"

echo "==> 4/6 calibrando contra las ubicaciones del mod Teleport"
"$RETOC" unpack "$TELEPORT" "$WORK/tp_raw" >/dev/null
python3 "$T/extract_pois.py" \
  "$WORK/tp_raw/Content/Mods/Teleport/data/DT_Locations.uasset" "$WORK/pois.json"
python3 "$T/calibrate.py" \
  "$WORK/height.npy" "$WORK/pois.json" "$WORK/height_m.npy" "$OUT/calibration.json"

echo "==> 5/6 rellenando los huecos con los HLOD"
python3 "$T/fill_holes.py" \
  "$WORK/height_m.npy" "$HLODS" "$WORK/height_filled.npy" "$WORK/source.npy"

echo "==> 6/6 exportando para el visor"
python3 "$T/export_contours.py" "$WORK/height_filled.npy" "$OUT"
python3 "$T/build_tiles.py" "$WORK/height_filled.npy" "$OUT/relief" --source "$WORK/source.npy"
python3 "$T/export_height_lookup.py" "$WORK/height_filled.npy" "$OUT/height.webp" "$OUT/height.json"
python3 "$T/build_places.py" "$MARKERS" "$WORK/pois.json" "$WORK/height_filled.npy" "$OUT/places.json"

echo "==> listo. $(du -sh "$OUT" | cut -f1) en $OUT"
echo "    el raster de 16 bits, aparte:"
echo "    python3 tools/export_heightmap.py $WORK/height_filled.npy heightmap.png --source $WORK/source.npy"
