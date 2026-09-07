#!/usr/bin/env python3
"""Exporta el heightfield como un raster de 16 bits, para quien lo quiera crudo.

Es la resolucion nativa del Landscape y no hay mas: 8129 x 8129 muestras de
1 m. El mundo mide 812.900 uu de lado y el Landscape guarda una muestra cada
100 uu, asi que un raster de 32k seria inventar tres de cada cuatro muestras.
La textura del mapa del PDA si es de 32k, pero es arte, no altura.

Sale un PNG gris de 16 bits (0 = min_m, 65535 = max_m, lineal) y un JSON al
lado con la georreferencia y la vuelta a metros. Opcionalmente una mascara PNG
con la procedencia de cada pixel, que importa: hay 15 celdas sin Landscape y
siete de ellas son terreno interpolado, o sea inventado.

    export_heightmap.py height_filled.npy heightmap.png [--source source.npy]
"""
import argparse
import json
import os

import numpy as np
from PIL import Image

UU_PER_SAMPLE = 100.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("height_npy")
    ap.add_argument("out_png")
    ap.add_argument("--source", help="source.npy: 0 Landscape, 1 HLOD, 2 interpolado")
    args = ap.parse_args()

    h = np.load(args.height_npy)
    lo, hi = float(h.min()), float(h.max())
    q = np.round((h - lo) / (hi - lo) * 65535.0).astype(np.uint16)
    Image.fromarray(q).save(args.out_png, optimize=True)

    side = int(h.shape[0])
    meta = {
        "width": side, "height": side,
        "bit_depth": 16,
        "min_m": lo, "max_m": hi,
        "to_metres": "m = min_m + value / 65535 * (max_m - min_m)",
        "metres_per_pixel": 1.0,
        "uu_per_pixel": UU_PER_SAMPLE,
        # El pixel (0,0) ES la muestra del mundo (0,0); +x a la derecha, +y abajo.
        # Ojo con los dos numeros: las muestras van de 0 a 812.800 (8128 pasos de
        # 100 uu), pero tratando cada pixel como una celda de 100 uu el raster
        # cubre 0..812.900, que es el extent del tileset de joric. La diferencia
        # es medio pixel, 50 uu = 0,5 m.
        "world_origin_uu": [0, 0],
        "sample_span_uu": (side - 1) * UU_PER_SAMPLE,
        "raster_extent_uu": side * UU_PER_SAMPLE,
        "axes": "col = x_uu / 100, row = y_uu / 100",
    }
    if args.source:
        src = np.load(args.source)
        mask_png = os.path.splitext(args.out_png)[0] + "_source.png"
        Image.fromarray((src.astype(np.uint8) * 127), mode="L").save(mask_png)
        meta["source_mask"] = os.path.basename(mask_png)
        meta["source_values"] = {"0": "Landscape", "127": "HLOD", "254": "interpolado"}
        meta["source_counts"] = {str(int(v) * 127): int(c)
                                 for v, c in zip(*np.unique(src, return_counts=True))}

    json.dump(meta, open(os.path.splitext(args.out_png)[0] + ".json", "w"), indent=1)
    print(f"{side} x {side} 16-bit, {lo:.1f} a {hi:.1f} m -> {args.out_png} "
          f"({os.path.getsize(args.out_png) / 1e6:.0f} MB)")


if __name__ == "__main__":
    main()
