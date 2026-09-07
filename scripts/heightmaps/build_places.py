#!/usr/bin/env python3
"""Arma el indice del buscador del visor.

Dos fuentes, en este orden de preferencia:

1. **Los markers de joric** (el clon de `joric/stalker`, en `refs/stalker/data/`).
   Trae las ubicaciones, los hubs y las regiones con el **nombre oficial
   localizado** del juego, sacado del `Localization_EN.json`. Es la fuente
   buena: "Zalissya" y no "Zalyssya".
2. **El `DT_Locations` del mod Teleport**, que ya se extrae para calibrar. Aporta
   ~130 lugares que no son ubicaciones del juego —campos de anomalias, puntos
   sueltos— con el nombre que le puso el autor del mod, y el sufijo de tipo de
   anomalia entre parentesis. Se agrega sólo lo que joric no cubre.

La cota **no** sale de la fuente: se lee del heightfield calibrado. Asi el numero
que muestra el buscador es el mismo terreno que dibujan las curvas, y las
regiones —que en los markers vienen con `z = -3` de relleno— quedan bien.

    build_places.py <markers_dir> <pois.json> <height_filled.npy> <places.json>
"""
import json
import sys

import numpy as np

UU_PER_SAMPLE = 100.0
# Dos entradas con el mismo nombre a menos de esto son el mismo lugar (el juego
# repite "Gas Station" y "Dam" en regiones distintas, y esos si son dos).
SAME_PLACE_UU = 200_000
SKIP = {"Main Menu", "TestArea interactibles"}   # no son lugares del mapa


def _norm(s):
    """Nombre comparable: sin el sufijo entre parentesis del mod Teleport."""
    return "".join(c for c in s.split("(")[0].lower() if c.isalnum())


def from_joric(d):
    loc = json.load(open(f"{d}/Localization/Localization_EN.json",
                         encoding="utf-8-sig"))["ST_S2BaseGameLocalization"]
    feats = json.load(open(f"{d}/markers.json"))["features"]
    out = []
    for f in feats:
        p = f["properties"]
        kind = (p.get("name"), p.get("type"))
        if kind[0] not in ("EMarkerType::Location", "EMarkerType::RegionMarker") \
                and kind[1] != "ESpawnType::Hub":
            continue
        name = loc.get(p.get("title"))
        if not name:
            continue
        x, y = f["geometry"]["coordinates"][:2]
        out.append({"n": name, "x": x, "y": y})
    return out


def merge(base, extra):
    """Agrega `extra` salteando lo que ya esta en `base` cerca y con el mismo nombre."""
    index = {}
    for e in base:
        index.setdefault(_norm(e["n"]), []).append(e)
    kept = list(base)
    for e in extra:
        k = _norm(e["n"])
        if any((e["x"] - o["x"]) ** 2 + (e["y"] - o["y"]) ** 2 < SAME_PLACE_UU ** 2
               for o in index.get(k, ())):
            continue
        index.setdefault(k, []).append(e)
        kept.append(e)
    return kept


def main(markers_dir, pois_json, height_npy, out_json):
    joric = from_joric(markers_dir)
    tp = [{"n": p["name"], "x": p["x"], "y": p["y"]}
          for p in json.load(open(pois_json)) if p["name"] not in SKIP]
    places = merge(merge([], joric), tp)
    n_joric = len(merge([], joric))

    g = np.load(height_npy)
    n = g.shape[0]
    col = np.clip(np.round([p["x"] / UU_PER_SAMPLE for p in places]), 0, n - 1).astype(int)
    row = np.clip(np.round([p["y"] / UU_PER_SAMPLE for p in places]), 0, n - 1).astype(int)
    z = g[row, col]          # el heightfield calibrado ya esta en metros

    out = sorted(({"n": p["n"], "x": round(p["x"]), "y": round(p["y"]),
                   "z": round(float(zi), 1)} for p, zi in zip(places, z)),
                 key=lambda d: d["n"])
    json.dump(out, open(out_json, "w"), separators=(",", ":"))
    print(f"{n_joric} de joric + {len(out) - n_joric} del Teleport "
          f"= {len(out)} lugares -> {out_json}")


if __name__ == "__main__":
    main(*sys.argv[1:5])
