#!/usr/bin/env python3
"""Corta los tiles raster del relieve (hipsometria + sombreado) para el visor web.

Esquema: el mismo que usa el visor de joric, para que esto sea drop-in y un PR
a su repo sea copiar archivos.

  - proyeccion `identity` sobre unidades de mundo de Unreal, extent 0..812900
  - tiles de 512 px; el zoom z cubre el mundo con 2^z x 2^z tiles
  - o sea, el lado de la imagen a zoom z es 512 * 2^z px

**Hasta z4 y no mas.** z4 son 8192 px y el dato nativo son 8129 muestras de un
metro: generar z5 seria inventar pixeles. El visor estira los tiles de z4 con
`maxAvailableZoom: 4`, y las curvas —que van en vector aparte— siguen nitidas a
cualquier zoom. Son 341 tiles en total contra los 1365 que saldrian con z5.

El relieve NO lleva las curvas quemadas: son una capa aparte, para poder
combinarlas con cualquier base y con opacidad variable.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))
from render_topo import (GUESS_TINT, HLOD_TINT, box_blur,       # noqa: E402
                         hillshade, hypsometric)

TILE = 512
MAX_ZOOM = 4
WORLD_UU = 812900


def relief_rgb(height_m, source=None, blur=1, exag=6.0):
    z = np.load(height_m).astype(np.float32)
    zs = box_blur(z, blur)
    del z
    lo, hi = np.nanpercentile(zs, 1), np.nanpercentile(zs, 99)
    rgb = hypsometric(zs, lo, hi)
    sh = hillshade(zs, vert_exag=exag)[..., None]
    del zs
    rgb = np.clip(rgb * (0.80 + 0.28 * sh), 0, 255).astype(np.uint8)
    del sh
    if source and os.path.exists(source):
        src = np.load(source)
        for val, tint in ((1, HLOD_TINT), (2, GUESS_TINT)):
            m = src == val
            if not m.any():
                continue
            a = tint[3] / 255.0
            rgb[m] = (rgb[m] * (1 - a) + np.array(tint[:3]) * a).astype(np.uint8)
    return rgb


def write_level(img, zoom, out_dir, quality):
    side = TILE * (1 << zoom)
    im = img.resize((side, side), Image.LANCZOS) if img.size[0] != side else img
    n = 1 << zoom
    written = total = 0
    for x in range(n):
        for y in range(n):
            tile = im.crop((x * TILE, y * TILE, (x + 1) * TILE, (y + 1) * TILE))
            d = os.path.join(out_dir, str(zoom), str(x))
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, f"{y}.webp")
            tile.save(p, "WEBP", quality=quality, method=4)
            written += 1
            total += os.path.getsize(p)
    return written, total, im


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("height_m")
    ap.add_argument("out_dir")
    ap.add_argument("--source", default=None)
    ap.add_argument("--max-zoom", type=int, default=MAX_ZOOM)
    ap.add_argument("--quality", type=int, default=82)
    a = ap.parse_args()

    rgb = relief_rgb(a.height_m, a.source)
    print(f"relieve {rgb.shape[1]}x{rgb.shape[0]} px")
    base = Image.fromarray(rgb)
    del rgb

    # De arriba hacia abajo: cada nivel sale de reescalar el maximo, no de
    # reescalar el anterior, para que no se acumule el suavizado.
    top = base.resize((TILE * (1 << a.max_zoom),) * 2, Image.LANCZOS)
    del base
    grand = 0
    for zoom in range(a.max_zoom, -1, -1):
        side = TILE * (1 << zoom)
        im = top if zoom == a.max_zoom else top.resize((side, side), Image.LANCZOS)
        n, total, _ = write_level(im, zoom, a.out_dir, a.quality)
        grand += total
        print(f"  z{zoom}: {n:4d} tiles ({side}x{side} px)  {total/1e6:6.2f} MB")
    print(f"total {grand/1e6:.1f} MB en {a.out_dir}")


if __name__ == "__main__":
    main()
