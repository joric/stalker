#!/usr/bin/env python3
"""Exporta el heightfield submuestreado, para leer la cota bajo el cursor en el visor.

Codificacion: **8 bits, WebP sin perdida, 2048 px**. Se llego ahi midiendo, no
por gusto:

  - 16 bits partidos en R y G (la convencion de Unreal) pesan 4,1 MB: el byte
    bajo es ruido de alta frecuencia y no comprime. Y daban 1,8 mm de precision,
    que para un cartel bajo el cursor es absurdo.
  - Con paso de medio metro el rango entero (121,7 m) entra en 8 bits, el PNG/WebP
    predice bien y baja a 0,64 MB — seis veces menos.

Quedan 4 m por pixel y 48 cm de paso. Sobra para un cartel, y para todo lo demas
esta el heightfield completo del lado del pipeline.
"""
import argparse
import json
import os

import numpy as np
from PIL import Image

SIDE = 2048
WORLD_UU = 812900


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("height_m")
    ap.add_argument("out_img")
    ap.add_argument("out_json")
    ap.add_argument("--side", type=int, default=SIDE)
    a = ap.parse_args()

    z = np.load(a.height_m).astype(np.float32)
    lo, hi = float(np.nanmin(z)), float(np.nanmax(z))
    s = np.asarray(Image.fromarray(z).resize((a.side, a.side), Image.BILINEAR),
                   dtype=np.float32)
    q = np.clip(np.round((s - lo) / (hi - lo) * 255), 0, 255).astype(np.uint8)
    Image.fromarray(q).save(a.out_img, "WEBP", lossless=True, method=6)

    json.dump({"side": a.side, "min_m": lo, "max_m": hi, "world_uu": WORLD_UU,
               "step_m": (hi - lo) / 255.0,
               "metres_per_pixel": WORLD_UU / 100.0 / a.side},
              open(a.out_json, "w"), indent=1)
    print(f"{a.side}x{a.side}  {lo:.1f}..{hi:.1f} m  paso {(hi-lo)/255*100:.0f} cm  "
          f"{os.path.getsize(a.out_img)/1e6:.2f} MB -> {a.out_img}")


if __name__ == "__main__":
    main()
