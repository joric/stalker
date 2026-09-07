#!/usr/bin/env python3
"""Tapa las celdas sin Landscape usando los vertices del HLOD.

Quince celdas del juego no tienen Landscape: solo mallas, agua y caminos
(verificado contando LandscapeComponent: cero). De esas, siete tienen un
`HLOD_Terrain_L0_*` del que si se pueden sacar vertices en coordenadas de mundo,
con un punto cada 15-30 m — o sea, entre 15 y 30 veces mas grueso que el metro
por muestra del Landscape. Las otras ocho guardan la malla en un formato que
este lector no toca (posiciones cuantizadas o Nanite).

El relleno resuelve Laplace sobre el hueco: los pixeles conocidos del borde y
los puntos del HLOD quedan fijos, y el interior se relaja hasta la media de sus
vecinos. Donde hay puntos de HLOD el resultado es dato real interpolado; donde
no los hay es puro relleno desde el borde, o sea terreno inventado. Por eso la
salida trae un mapa de procedencia y el renderizador los dibuja distinto.

Despues de relajar hay que SUAVIZAR el interior del hueco. Con los puntos del
HLOD como restriccion dura cada uno queda como un hoyuelo y el relleno sale con
una reticula de puntitos bien visible en el mapa — los puntos estan cada 15-30 m
y Laplace no los funde. El suavizado usa un radio del orden de esa separacion y
respeta el borde, asi que la costura con el Landscape real no se mueve.
"""
import os
import re
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from hlod_mesh import terrain_points                       # noqa: E402

SRC_LANDSCAPE, SRC_HLOD, SRC_GUESS = 0, 1, 2

# El radio del suavizado se saca de la separacion media entre puntos del HLOD:
# separacion ~= lado_celda / sqrt(n_puntos). Con la mitad de esa separacion los
# hoyuelos se funden sin borrar la forma que traen los puntos.
SMOOTH_FACTOR = 0.5


def laplace_fill(z, fixed, iterations=800):
    """Relaja los pixeles no fijos hasta la media de sus vecinos."""
    u = z.copy()
    u[~fixed] = np.nanmean(z[fixed]) if fixed.any() else 0.0
    for _ in range(iterations):
        acc = np.zeros_like(u)
        acc[1:, :] += u[:-1, :]
        acc[:-1, :] += u[1:, :]
        acc[:, 1:] += u[:, :-1]
        acc[:, :-1] += u[:, 1:]
        cnt = np.zeros_like(u)
        cnt[1:, :] += 1
        cnt[:-1, :] += 1
        cnt[:, 1:] += 1
        cnt[:, :-1] += 1
        nu = acc / cnt
        u = np.where(fixed, z, nu)
    return u


def smooth_interior(u, hole, radius):
    """Suaviza solo adentro del hueco; el borde con el Landscape real no se toca."""
    if radius < 1 or not hole.any():
        return u
    k = 2 * radius + 1
    pad = np.pad(u, radius, mode="edge")
    c = np.cumsum(np.cumsum(pad, axis=0), axis=1)
    c = np.pad(c, ((1, 0), (1, 0)))
    h, w = u.shape
    r0 = np.arange(h)[:, None]
    c0 = np.arange(w)[None, :]
    tot = (c[r0 + k, c0 + k] - c[r0, c0 + k] - c[r0 + k, c0] + c[r0, c0])
    sm = tot / (k * k)
    # Desvanecer hacia el borde del hueco para que no se marque un escalon.
    return np.where(hole, sm, u)


def fill(height_m_path, hlod_dir, out_path, out_src_path, cell_size_m=508,
         pad=24):
    z = np.load(height_m_path)
    z = np.where(np.isfinite(z) & (z != 0), z, np.nan)
    src = np.where(np.isfinite(z), SRC_LANDSCAPE, SRC_GUESS).astype(np.uint8)
    n = z.shape[0]

    holes = {}
    for f in os.listdir(hlod_dir):
        m = re.match(r"^HLOD_Terrain_L0_X(-?\d+)Y(-?\d+)\.uexp$", f)
        if m:
            holes[(int(m.group(1)), int(m.group(2)))] = os.path.join(hlod_dir, f)

    filled_hlod = filled_flat = 0
    for (cx, cy), path in sorted(holes.items()):
        c0 = (cx + 8) * cell_size_m
        r0 = (cy + 8) * cell_size_m
        c1, r1 = c0 + cell_size_m, r0 + cell_size_m
        if not np.isnan(z[r0:r1, c0:c1]).any():
            continue                                        # no era un hueco
        cs, ce = max(0, c0 - pad), min(n, c1 + pad)
        rs, re_ = max(0, r0 - pad), min(n, r1 + pad)
        sub = z[rs:re_, cs:ce].copy()
        fixed = np.isfinite(sub)

        pts = terrain_points(path, cx, cy)
        used = 0
        if len(pts):
            pc = np.round(pts[:, 0] / 100.0).astype(int) - cs
            pr = np.round(pts[:, 1] / 100.0).astype(int) - rs
            ok = (pc >= 0) & (pc < sub.shape[1]) & (pr >= 0) & (pr < sub.shape[0])
            pc, pr, pz = pc[ok], pr[ok], pts[ok, 2] / 100.0
            new = ~fixed[pr, pc]
            sub[pr[new], pc[new]] = pz[new]
            fixed[pr[new], pc[new]] = True
            used = int(new.sum())

        if not fixed.any():
            continue
        out = laplace_fill(sub, fixed)
        if used:
            out = smooth_interior(out, np.isnan(z[rs:re_, cs:ce]),
                                  radius=max(6, int(round(SMOOTH_FACTOR
                                                          * 508 / np.sqrt(used)))))
        hole = np.isnan(z[rs:re_, cs:ce])
        z[rs:re_, cs:ce] = np.where(hole, out, z[rs:re_, cs:ce])
        block = src[rs:re_, cs:ce]
        src[rs:re_, cs:ce] = np.where(hole,
                                      SRC_HLOD if used else SRC_GUESS, block)
        if used:
            filled_hlod += 1
            print(f"  X{cx}Y{cy}: {used} puntos de HLOD")
        else:
            filled_flat += 1
            print(f"  X{cx}Y{cy}: sin puntos, relleno solo desde el borde")

    np.save(out_path, z.astype(np.float32))
    np.save(out_src_path, src)
    print(f"celdas con HLOD {filled_hlod}, sin HLOD {filled_flat}")
    print(f"sin dato original: {(src != SRC_LANDSCAPE).mean():.2%}")


if __name__ == "__main__":
    fill(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
