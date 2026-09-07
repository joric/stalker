"""Extrae el heightfield del Landscape de S.T.A.L.K.E.R. 2 desde los paquetes
`Terrain_L0_X*Y*` que escribe `retoc to-legacy`.

Lo verificado en juego/datos el 2026-09-05, que es de donde sale cada decision:

- El mundo es un Landscape de UE5 normal, partido en celdas de World Partition
  `Terrain_L0_X{-8..7}Y{-8..7}`. Las componentes NO se pueden ubicar leyendo
  SectionBaseX/Y: GSC serializa `LandscapeComponent` con un blob propio
  (`GSCPackedComponent`) en vez de propiedades etiquetadas.
- No hace falta. La ubicacion sale del nombre de la celda mas el orden de los
  cuatro `Texture2D_*`, que forman siempre un 2x2:
        #0 #1
        #2 #3
  Comprobado por continuidad exacta de bordes en 9 celdas: 52 pares, cero
  excepciones. X+1 va a la derecha, Y+1 va hacia abajo.
- Las alturas son B8G8R8A8 con el entero de 16 bits partido en R (alto) y G
  (bajo), que es la convencion de Landscape de Unreal.
- El `.ubulk` lleva, POR TEXTURA y en el orden de la tabla de exports, mip0 y
  mip1 pegados. Los mips 2 en adelante van inline en el `.uexp`.
- Las componentes vecinas DUPLICAN la fila/columna del borde compartido. Al
  pegar hay que descartar una de las dos o el mapa queda estirado.
"""
import os
import re
import struct

import numpy as np

from uasset import Package

CELL_RE = re.compile(r"^Terrain_L0_X(-?\d+)Y(-?\d+)$")

# Los cuatro heightmaps son los primeros Texture2D del paquete; los que siguen
# son Weightmap_*. Se valida igual por estadistica, no se confia en el orden.
HEIGHTMAPS_PER_CELL = 4


def _texture_dims(blob):
    """(SizeX, SizeY, formato, [(w,h) por mip en bulk]) de un export Texture2D.

    El formato va como FString justo despues de SizeX/SizeY/NumSlices, asi que
    se ancla en el 'PF_' y se leen los enteros hacia atras.
    """
    i = blob.find(b"PF_")
    if i < 0:
        return None
    size_x = struct.unpack_from("<i", blob, i - 16)[0]
    size_y = struct.unpack_from("<i", blob, i - 12)[0]
    end = blob.find(b"\x00", i)
    fmt = blob[i:end].decode()
    p = end + 1
    struct.unpack_from("<i", blob, p)[0]          # FirstMipToSerialize
    num_mips = struct.unpack_from("<i", blob, p + 4)[0]
    p += 8
    # Cada mip en bulk es [indice global, W, H, Slices]. Los inline cortan la
    # secuencia, asi que se para cuando las dimensiones dejan de tener sentido.
    mips = []
    w, h = size_x, size_y
    for _ in range(num_mips):
        if p + 16 > len(blob):
            break
        mw = struct.unpack_from("<i", blob, p + 4)[0]
        mh = struct.unpack_from("<i", blob, p + 8)[0]
        if mw != w or mh != h:
            break
        mips.append((w, h))
        p += 16
        w, h = max(w // 2, 1), max(h // 2, 1)
    return size_x, size_y, fmt, mips


def cell_textures(base_path):
    """Lista de (nombre, SizeX, SizeY, formato, offset_en_ubulk) de un cell."""
    pkg = Package(base_path)
    pkg.load_tables()
    uexp = open(base_path + ".uexp", "rb").read()
    out = []
    offset = 0
    for e in pkg.exports:
        if pkg.class_of(e) != "Texture2D":
            continue
        o = e.serial_offset - pkg.total_header_size
        info = _texture_dims(uexp[o:o + e.serial_size])
        if info is None:
            continue
        sx, sy, fmt, mips = info
        out.append((e.full_name, sx, sy, fmt, offset))
        offset += sum(w * h * 4 for w, h in mips)
    return out, offset


def heightmaps(base_path):
    """Los cuatro tiles de altura de una celda, en orden #0 #1 / #2 #3.

    Devuelve arrays uint16 crudos (el entero del heightmap, 32768 = altura 0).
    """
    texs, total = cell_textures(base_path)
    ubulk_path = base_path + ".ubulk"
    if not os.path.exists(ubulk_path):
        return []
    raw = np.fromfile(ubulk_path, dtype=np.uint8)
    if raw.size != total:
        raise ValueError(f"{os.path.basename(base_path)}: ubulk {raw.size} "
                         f"!= suma de mips {total}")
    # Los heightmaps son los exports llamados `Texture2D_0..3`; los `Weightmap_*`
    # son pesos de capa. Seleccionar por estadistica no alcanza: en
    # Terrain_L0_X-4Y-1 un weightmap pasa el filtro de suavidad.
    #
    # Esa misma celda es la unica de las 241 con un `Texture2D_4`: una textura
    # huerfana, sin componente. Se comprobo por bordes que no encaja en ningun
    # lado y que los cuatro primeros van en orden, asi que alcanza con cortar en
    # HEIGHTMAPS_PER_CELL respetando el orden de la tabla de exports.
    tiles = []
    for name, sx, sy, fmt, off in texs:
        if fmt != "PF_B8G8R8A8" or not name.startswith("Texture2D"):
            continue
        if len(tiles) == HEIGHTMAPS_PER_CELL:
            break
        a = raw[off:off + sx * sy * 4].reshape(sy, sx, 4)
        h = (a[:, :, 2].astype(np.uint16) << 8) | a[:, :, 1]
        # Control, no seleccion: un heightmap vive pegado a 32768 y es suave.
        if not (20000 < h.min() and h.max() < 50000):
            raise ValueError(f"{name}: rango {h.min()}..{h.max()} no es de altura")
        tiles.append((name, h))
    return tiles
