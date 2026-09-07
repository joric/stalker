"""Saca las posiciones de vertice de los HLOD de terreno de S.T.A.L.K.E.R. 2.

Sirve para tapar las 15 celdas donde el juego NO tiene Landscape (solo mallas,
agua y caminos). Ahi el `Terrain_L0_*` no trae ninguna LandscapeComponent, pero
el `HLOD_Terrain_L0_*` si trae mallas `StaticMesh_WM_Merged_Terrain_*`.

Los vertices vienen en **coordenadas de mundo**, no locales — es lo que permitio
medir que la celda de World Partition mide 50.800 uu y corregir el pegado del
heightfield.

No se parsea `FStaticMeshRenderData` entero: se busca el patron de un
`TArray<FVector3f>` cocinado. Ojo con la cabecera, que es donde se cayo la
primera version: el buffer de posiciones escribe `(Stride, NumVertices)` y
DESPUES `(ElementSize, ArrayNum)`, o sea `(12, n, 12, n)` — 16 bytes, no 8.
Arrancando a leer 8 bytes antes las columnas salen rotadas y los puntos parecen
caer fuera de la celda. Se detectan las dos formas y se valida que las
coordenadas caigan dentro de la celda que dice el nombre del paquete.
"""
import struct

import numpy as np

CELL_SIZE_UU = 50800.0        # verificado contra los vertices del HLOD
CELL_MIN = -8


def cell_bounds(cx, cy):
    x0 = (cx - CELL_MIN) * CELL_SIZE_UU
    y0 = (cy - CELL_MIN) * CELL_SIZE_UU
    return x0, y0, x0 + CELL_SIZE_UU, y0 + CELL_SIZE_UU


def vertex_arrays(path, min_count=100, max_count=500000, limit=1e7):
    """Todo TArray<FVector3f> plausible del archivo."""
    d = open(path, "rb").read()
    out = []
    i = 0
    while i < len(d) - 8:
        es, n = struct.unpack_from("<ii", d, i)
        if es == 12 and min_count < n < max_count:
            head = 8
            if i + 16 <= len(d) and struct.unpack_from("<ii", d, i + 8) == (12, n):
                head = 16
            if i + head + n * 12 > len(d):
                i += 4
                continue
            f = np.frombuffer(d, dtype="<f4", count=n * 3, offset=i + head)
            f = f.reshape(n, 3)
            if np.all(np.isfinite(f)) and np.abs(f).max() < limit:
                out.append((i, f))
                i += head + n * 12
                continue
        i += 4
    return out


def terrain_points(path, cx, cy, margin=2000.0):
    """Puntos (x, y, z) del HLOD que caen dentro de la celda, en unidades de mundo."""
    x0, y0, x1, y1 = cell_bounds(cx, cy)
    pts = []
    for _, f in vertex_arrays(path):
        m = ((f[:, 0] >= x0 - margin) & (f[:, 0] <= x1 + margin)
             & (f[:, 1] >= y0 - margin) & (f[:, 1] <= y1 + margin))
        if m.sum() > 50:
            pts.append(f[m])
    if not pts:
        return np.zeros((0, 3), dtype=np.float32)
    return np.unique(np.vstack(pts), axis=0)
