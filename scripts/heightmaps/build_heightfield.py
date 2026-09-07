#!/usr/bin/env python3
"""Pega los 241 cells del Landscape en un solo heightfield y lo guarda en .npy.

Ubicacion: sale del nombre de la celda, no de los datos. Verificado el
2026-09-05 por continuidad exacta de bordes (52 pares en 9 celdas, sin
excepciones): dentro de la celda los cuatro heightmaps van

    #0 #1
    #2 #3

X+1 va a la derecha, Y+1 va hacia abajo.

Cuidado con el conteo de muestras, que es donde estuvo el primer error. Cada
textura de 256x256 NO es una componente de 255 quads: son 2x2 SUBSECCIONES de
127 quads, y la fila y la columna del limite entre subsecciones estan
DUPLICADAS dentro de la textura (verificado: fila 127 == fila 128 exacta, con
126 != 127 y 128 != 129). Sacando esa duplicada, la componente son 254 quads.

Lo confirma el HLOD por otro lado: los vertices de `HLOD_Terrain_L0_X2Y2` estan
en coordenadas de mundo y van de 508.000 a 558.800, o sea celdas de 50.800 uu
= 2 componentes * 254 quads * 100 uu. Con 255 quads darian 51.000 y no cierra.

Pegar los 256x256 enteros estiraba el mapa un 0,4 % — hasta 32 m de error
acumulado en el borde — y por eso el ajuste libre de la escala daba 99,1
uu/muestra en vez de 100.

Entonces: cada tile aporta 254 muestras nuevas y la ultima se comparte con la
componente siguiente: 16 celdas * 2 tiles * 254 + 1 = 8129 de lado, y la
muestra mide 100 uu exactos.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from landscape import CELL_RE, heightmaps           # noqa: E402

TILE = 256
SUBSECTION = 128                                    # 2x2 subsecciones por textura
DUP_INDEX = SUBSECTION                              # la fila/col repetida
TILE_UNIQUE = TILE - 1                              # 255 muestras, 254 quads
STEP = TILE_UNIQUE - 1                              # 254: la ultima se comparte
CELLS = 16                                          # X,Y de -8 a 7
CELL_MIN = -8
SIDE = CELLS * 2 * STEP + 1                         # 8129

SUB_OFFSET = {0: (0, 0), 1: (1, 0), 2: (0, 1), 3: (1, 1)}   # (col, fila)

NO_DATA = 0                                         # 0 no aparece en heightmaps reales


def build(cells_dir):
    grid = np.zeros((SIDE, SIDE), dtype=np.uint16)
    names = sorted({f[:-6] for f in os.listdir(cells_dir)
                    if f.endswith(".ubulk") and CELL_RE.match(f[:-6])})
    placed = 0
    for name in names:
        cx, cy = (int(v) for v in CELL_RE.match(name).groups())
        tiles = heightmaps(os.path.join(cells_dir, name))
        if len(tiles) != 4:
            print(f"  aviso: {name} trajo {len(tiles)} heightmaps, esperaba 4")
        for sub, (_, h) in enumerate(tiles):
            h = np.delete(np.delete(h, DUP_INDEX, axis=0), DUP_INDEX, axis=1)
            ox, oy = SUB_OFFSET[sub]
            gx = ((cx - CELL_MIN) * 2 + ox) * STEP
            gy = ((cy - CELL_MIN) * 2 + oy) * STEP
            grid[gy:gy + TILE_UNIQUE, gx:gx + TILE_UNIQUE] = h
            placed += 1
    return grid, len(names), placed


if __name__ == "__main__":
    cells_dir, out = sys.argv[1], sys.argv[2]
    grid, ncells, ntiles = build(cells_dir)
    np.save(out, grid)
    cov = np.count_nonzero(grid) / grid.size
    print(f"celdas {ncells}  tiles {ntiles}  grilla {grid.shape}")
    print(f"cobertura {cov:.1%}  min {grid[grid > 0].min()}  max {grid.max()}")
    print(f"-> {out}")
