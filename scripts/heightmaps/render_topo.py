#!/usr/bin/env python3
"""Dibuja el mapa topografico: hipsometria + sombreado + curvas de nivel.

Decisiones y por que:

- **Datum**: el cero del mundo de S2 no es el nivel del mar, es un punto
  arbitrario (el terreno cae entre -316 y -195 en coordenadas de mundo). Las
  cotas se dan sobre el punto mas bajo del mapa, que no inventa nada. Si algun
  dia se quiere referir al nivel del agua o a la altura real de Chornobyl,
  alcanza con correr DATUM.
- **Suavizado antes de contornear**: el heightfield trae zanjas, terraplenes de
  camino y plateas de edificio de un metro de ancho. Sin suavizar, las curvas se
  llenan de dientes que no dicen nada del relieve. Es un box blur separable hecho
  con sumas acumuladas — no hay scipy en esta maquina.
- **Las curvas se rasterizan a mano** con PIL en vez de dejarselas a matplotlib:
  a 8161x8161 una figura de matplotlib se come varios GB, y aca /tmp es RAM.
  matplotlib se usa solo para SACAR los caminos, que es barato.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.dirname(__file__))

# Carta sobria: el color casi no dice altura, la dicen las curvas. La rampa va
# de un crema de bajio a un ocre palido de alto, con muy poco recorrido — si el
# color grita, las curvas dejan de leerse, que es lo que pasaba con la paleta
# saturada del primer intento.
RAMP = [
    (0.00, (233, 235, 228)),
    (0.25, (243, 240, 228)),
    (0.55, (246, 238, 219)),
    (0.80, (243, 230, 206)),
    (1.00, (236, 219, 194)),
]
PAPER = (250, 248, 243)
MINOR_RGBA = (150, 106, 66, 165)
MAJOR_RGBA = (104, 64, 34, 240)
HLOD_TINT = (120, 120, 128, 26)      # celdas reconstruidas del HLOD
GUESS_TINT = (120, 120, 128, 54)     # celdas interpoladas desde el borde


def box_blur(a, radius):
    """Media movil 2D con sumas acumuladas. Trata los NaN como huecos."""
    if radius <= 0:
        return a
    m = np.isfinite(a)
    v = np.where(m, a, 0.0).astype(np.float64)
    w = m.astype(np.float64)

    def run(x):
        c = np.cumsum(x, axis=0)
        c = np.vstack([np.zeros((1, x.shape[1])), c])
        lo = np.clip(np.arange(x.shape[0]) - radius, 0, x.shape[0])
        hi = np.clip(np.arange(x.shape[0]) + radius + 1, 0, x.shape[0])
        y = c[hi] - c[lo]
        c = np.cumsum(y, axis=1)
        c = np.hstack([np.zeros((y.shape[0], 1)), c])
        lo = np.clip(np.arange(y.shape[1]) - radius, 0, y.shape[1])
        hi = np.clip(np.arange(y.shape[1]) + radius + 1, 0, y.shape[1])
        return c[:, hi] - c[:, lo]

    s, n = run(v), run(w)
    out = np.where(n > 0, s / np.maximum(n, 1e-9), np.nan)
    return out.astype(np.float32)


def hillshade(z, azimuth=315.0, altitude=45.0, vert_exag=6.0):
    """Sombreado clasico. La exageracion vertical es alta a proposito: la Zona
    es muy plana y sin exagerar el relieve no se ve."""
    dy, dx = np.gradient(z * vert_exag)
    slope = np.pi / 2.0 - np.arctan(np.hypot(dx, dy))
    aspect = np.arctan2(-dx, dy)
    az = np.radians(360.0 - azimuth + 90.0)
    alt = np.radians(altitude)
    sh = (np.sin(alt) * np.sin(slope)
          + np.cos(alt) * np.cos(slope) * np.cos(az - aspect))
    return np.clip(sh, 0, 1)


def hypsometric(z, lo, hi):
    t = np.clip((z - lo) / max(hi - lo, 1e-6), 0, 1)
    stops = np.array([s[0] for s in RAMP])
    cols = np.array([s[1] for s in RAMP], dtype=np.float32)
    idx = np.clip(np.searchsorted(stops, t) - 1, 0, len(stops) - 2)
    t0, t1 = stops[idx], stops[idx + 1]
    f = ((t - t0) / (t1 - t0))[..., None]
    return cols[idx] * (1 - f) + cols[idx + 1] * f


def contour_paths(z, levels, scale):
    """Caminos de las curvas, en pixeles de la imagen final."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig = plt.figure()
    cs = plt.contour(z, levels=levels)
    out = {}
    for lev, allsegs in zip(cs.levels, cs.allsegs):
        out[float(lev)] = [seg * scale for seg in allsegs if len(seg) > 2]
    plt.close(fig)
    return out


def render(height_m, out_path, px_per_sample=0.25, interval=5.0, index_every=5,
           blur=3, exag=6.0, source=None):
    z = np.load(height_m)
    z = np.where(z == 0, np.nan, z)
    nodata = ~np.isfinite(z)
    datum = np.nanmin(z)
    z = z - datum                                   # cotas sobre el punto mas bajo

    zs = box_blur(z, blur)
    n = z.shape[0]
    w = int(round(n * px_per_sample))

    filled = np.where(np.isfinite(zs), zs, np.nanmedian(zs))
    lo, hi = np.nanpercentile(zs, 1), np.nanpercentile(zs, 99)
    rgb = hypsometric(filled, lo, hi)
    # Sombreado suave: solo lo justo para que se lea la forma del terreno sin
    # taparle el contraste a las curvas.
    sh = hillshade(filled, vert_exag=exag)[..., None]
    rgb = np.clip(rgb * (0.80 + 0.28 * sh), 0, 255)

    img = Image.fromarray(rgb.astype(np.uint8)).resize((w, w), Image.LANCZOS)

    if source is not None:
        src = np.load(source)
        ov = Image.new("RGBA", (w, w), (0, 0, 0, 0))
        od = ImageDraw.Draw(ov)
        sm = Image.fromarray(src).resize((w, w), Image.NEAREST)
        sa = np.array(sm)
        for val, tint in ((1, HLOD_TINT), (2, GUESS_TINT)):
            mask = Image.fromarray((sa == val).astype(np.uint8) * 255)
            od.bitmap((0, 0), mask, fill=tint)
        img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")

    top = float(np.nanmax(zs))
    levels = list(np.arange(interval, top, interval))
    paths = contour_paths(zs, levels, px_per_sample)
    draw = ImageDraw.Draw(img, "RGBA")
    for lev, segs in paths.items():
        major = abs((lev / interval) % index_every) < 1e-6
        col = MAJOR_RGBA if major else MINOR_RGBA
        wd = 2 if major else 1
        for seg in segs:
            draw.line([tuple(p) for p in seg], fill=col, width=wd)

    img.save(out_path)
    return dict(shape=z.shape, out=w, datum=float(datum), top=top,
                levels=len(levels), interval=interval,
                nodata=float(nodata.mean()))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("height_m")
    ap.add_argument("out")
    ap.add_argument("--px-per-sample", type=float, default=0.25)
    ap.add_argument("--interval", type=float, default=5.0)
    ap.add_argument("--index-every", type=int, default=5)
    ap.add_argument("--blur", type=int, default=3)
    ap.add_argument("--exag", type=float, default=6.0)
    ap.add_argument("--source", default=None)
    a = ap.parse_args()
    info = render(a.height_m, a.out, a.px_per_sample, a.interval,
                  a.index_every, a.blur, a.exag, a.source)
    print(f"grilla {info['shape']} -> {info['out']}x{info['out']} px")
    print(f"cotas 0..{info['top']:.1f} m sobre el punto mas bajo")
    print(f"{info['levels']} curvas cada {info['interval']:g} m")
    print(f"sin datos: {info['nodata']:.1%}")
    print(f"-> {info['out'] and a.out}")
