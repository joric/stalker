#!/usr/bin/env python3
"""Exporta las curvas de nivel como GeoJSON en coordenadas de mundo de Unreal.

Por que vectores y no tiles raster, que es lo que uno esperaria de un mapa web:
medido sobre este terreno, las tres equidistancias juntas pesan 2,4 MB
comprimidos. En tiles harian falta miles de imagenes por equidistancia, se verian
pixeladas pasando el zoom nativo, y el color, el grosor y la equidistancia
quedarian horneados. En vector se eligen en el navegador.

Sistema de coordenadas: unidades de mundo de Unreal, que es el mismo que usa el
visor de joric (`projection: 'identity'`, extent 0..812900). La grilla mide
8129 muestras de 100 uu, o sea 812.900 uu exactos, asi que la conversion es
multiplicar por 100 y nada mas. La fila crece hacia abajo, igual que su `top=0`
/ `bottom=812900`.

Las cotas van en **metros de mundo**, no sobre el punto mas bajo: asi coinciden
con la Z de cualquier otro dato del juego (los marcadores, por ejemplo), y una
lectura de cota bajo el cursor no se contradice con nada.
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from render_topo import box_blur                            # noqa: E402

UU_PER_SAMPLE = 100
SIMPLIFY_M = 1.5      # tolerancia Douglas-Peucker, en metros: deja 4-5% de los
                      # vertices sin que se note a ninguna escala util


def simplify(pts, eps):
    """Douglas-Peucker iterativo (sin recursion: hay lineas de 100k puntos)."""
    if len(pts) < 3:
        return pts
    keep = np.zeros(len(pts), bool)
    keep[0] = keep[-1] = True
    stack = [(0, len(pts) - 1)]
    while stack:
        a, b = stack.pop()
        if b <= a + 1:
            continue
        seg = pts[a:b + 1]
        p0 = pts[a]
        d = pts[b] - p0
        length = float(np.hypot(d[0], d[1]))
        rel = seg - p0
        if length == 0:
            dist = np.hypot(rel[:, 0], rel[:, 1])
        else:
            dist = np.abs(d[0] * rel[:, 1] - d[1] * rel[:, 0]) / length
        i = int(dist.argmax())
        if dist[i] > eps:
            keep[a + i] = True
            stack.append((a, a + i))
            stack.append((a + i, b))
    return pts[keep]


def contours(z, interval, index_every, blur):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    zs = box_blur(z, blur)
    lo = np.ceil(np.nanmin(zs) / interval) * interval
    hi = np.nanmax(zs)
    levels = list(np.arange(lo, hi, interval))
    fig = plt.figure()
    cs = plt.contour(zs, levels=levels)
    feats = []
    for lev, allsegs in zip(cs.levels, cs.allsegs):
        major = abs((lev / interval) % index_every) < 1e-6
        for seg in allsegs:
            if len(seg) <= 2:
                continue
            s = simplify(np.asarray(seg, dtype=np.float64), SIMPLIFY_M)
            if len(s) <= 2:
                continue
            coords = [[int(round(p[0] * UU_PER_SAMPLE)),
                       int(round(p[1] * UU_PER_SAMPLE))] for p in s]
            feats.append({"type": "Feature",
                          "properties": {"e": round(float(lev), 1),
                                         "i": 1 if major else 0},
                          "geometry": {"type": "LineString",
                                       "coordinates": coords}})
    plt.close(fig)
    return feats, levels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("height_m")
    ap.add_argument("out_dir")
    ap.add_argument("--intervals", default="2,5,10")
    ap.add_argument("--index-every", type=int, default=5)
    ap.add_argument("--blur", type=int, default=3)
    a = ap.parse_args()

    z = np.load(a.height_m)
    os.makedirs(a.out_dir, exist_ok=True)
    for iv in [float(v) for v in a.intervals.split(",")]:
        feats, levels = contours(z, iv, a.index_every, a.blur)
        gj = {"type": "FeatureCollection",
              "properties": {"interval_m": iv, "index_every": a.index_every,
                             "crs": "unreal-world-uu", "extent": 812900},
              "features": feats}
        name = f"contours-{iv:g}m.geojson"
        path = os.path.join(a.out_dir, name)
        with open(path, "w") as f:
            json.dump(gj, f, separators=(",", ":"))
        nv = sum(len(x["geometry"]["coordinates"]) for x in feats)
        print(f"{iv:g} m: {len(feats)} lineas, {nv} vertices, "
              f"{len(levels)} niveles -> {name} "
              f"({os.path.getsize(path)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
