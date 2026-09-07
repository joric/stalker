#!/usr/bin/env python3
"""Ajusta el offset vertical del Landscape contra las ubicaciones del Teleport.

Cuidado con el offset, que es donde se metio un bug que sobrevivio varias
vueltas: el ajuste se hace sobre el valor CRUDO del heightmap,

    Z_uu = (Z_SCALE/128) * v + b

y ese `b` ya lleva adentro el -32768*(Z_SCALE/128) = -25600 del punto medio. El
offset del actor es `b + 32768*Z_SCALE/128`, no `b`. Restando el punto medio dos
veces el terreno queda 256 m por debajo de donde va. En un mapa de curvas eso no
se nota —es un corrimiento constante— pero rompe cualquier cosa que mezcle el
heightfield con datos en Z de mundo, y por eso lo destapo el relleno del HLOD.
"""
import json
import sys

import numpy as np

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from calibration import HEIGHT_MIDPOINT, UU_PER_SAMPLE, Z_SCALE, raw_to_metres

OUTLIER_UU = 2000.0     # 20 m: azoteas, antenas y la camara del menu principal
WINDOW = 2              # mediana 5x5: baja la dilucion por desalineacion


def calibrate(height_npy, pois_json):
    g = np.load(height_npy).astype(np.float32)
    g = np.where(g == 0, np.nan, g)
    n = g.shape[0]
    pois = json.load(open(pois_json))
    x = np.array([p["x"] for p in pois])
    y = np.array([p["y"] for p in pois])
    z = np.array([p["z"] for p in pois])

    col = np.round(x / UU_PER_SAMPLE).astype(int)
    row = np.round(y / UU_PER_SAMPLE).astype(int)
    ok = (col >= 0) & (col < n) & (row >= 0) & (row < n)
    v = np.full(len(pois), np.nan)
    for i in np.where(ok)[0]:
        w = g[max(0, row[i] - WINDOW):row[i] + WINDOW + 1,
              max(0, col[i] - WINDOW):col[i] + WINDOW + 1]
        w = w[~np.isnan(w)]
        if w.size:
            v[i] = np.median(w)

    slope = Z_SCALE / 128.0
    m = ~np.isnan(v)
    b = np.median(z[m] - slope * v[m])
    good = m & (np.abs(z - (slope * v + b)) < OUTLIER_UU)
    b = float(np.median(z[good] - slope * v[good]))
    res = z[good] - (slope * v[good] + b)

    actor_z_uu = b + HEIGHT_MIDPOINT * slope
    return {
        "z_scale": Z_SCALE,
        "uu_per_sample": UU_PER_SAMPLE,
        "actor_z_offset_uu": actor_z_uu,
        "side": int(n),
        "n_points": int(good.sum()),
        "residual_median_m": float(np.median(np.abs(res)) / 100.0),
        "residual_p90_m": float(np.percentile(np.abs(res), 90) / 100.0),
        "corr": float(np.corrcoef(v[good], z[good])[0, 1]),
    }, raw_to_metres(g, actor_z_uu)


if __name__ == "__main__":
    info, h = calibrate(sys.argv[1], sys.argv[2])
    np.save(sys.argv[3], h.astype(np.float32))
    json.dump(info, open(sys.argv[4], "w"), indent=1)
    hv = h[np.isfinite(h)]
    print(f"offset del actor = {info['actor_z_offset_uu']:.1f} uu "
          f"= {info['actor_z_offset_uu']/100:.2f} m")
    print(f"n={info['n_points']}  residuo mediana {info['residual_median_m']:.3f} m "
          f"| p90 {info['residual_p90_m']:.2f} m | corr {info['corr']:+.4f}")
    print(f"terreno: {hv.min():.1f} a {hv.max():.1f} m  (relieve {hv.max()-hv.min():.1f} m)")
