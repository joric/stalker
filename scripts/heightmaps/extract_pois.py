#!/usr/bin/env python3
"""Saca las ubicaciones con coordenadas de mundo del DT_Locations del mod Teleport.

Es la unica fuente conocida de pares (lugar, coordenada de mundo) que no exige
entrar al juego. Se usa para calibrar el heightfield: el juego no tiene ningun
comando de consola que imprima la posicion del jugador — `XShowPlayerCoordinates`,
`XToggleShowPlayerLocation` y `XShowCurrentLocation` existen pero estan vacios en
el build de release (verificado en juego el 2026-09-05).

El DataTable esta cocinado, asi que no se parsea la estructura: se barre el
archivo buscando filas de S_Location, que quedan serializadas como **el nombre
primero y las tres doubles inmediatamente despues**:

    ... 0b 10 | 0a 00 00 00 | "Slag Heap\\0" | x y z (3 doubles) | flags | ...

Ojo con el orden, que es la trampa de este archivo `[2026-09-05]`: leerlo al
reves —una terna de doubles y despues el primer FString que aparezca— tambien
"anda", porque entre el fin de una fila y el nombre de la siguiente hay pocos
bytes. Pero corre las etiquetas un renglon: Slag Heap terminaba a 1,4 km de su
lugar, con el nombre de la fila anterior. Las coordenadas nunca estuvieron mal
—la calibracion solo usa la terna, que es internamente consistente en los dos
casos—, se equivocaban los carteles. Se comprobo el orden correcto contra los
markers de joric: 225 nombres en comun caen a 37 m de mediana, contra 42 km con
el orden invertido.
"""
import json
import struct
import sys

# Rangos de cordura para una coordenada del mundo de S2, en unidades de Unreal.
XY_MIN, XY_MAX = 1e3, 2e6
Z_MAX = 2e4


def _read_fstring(d, i):
    """Devuelve (texto, bytes_consumidos) si en `i` arranca un FString ASCII."""
    if i + 4 > len(d):
        return None
    n = struct.unpack_from("<i", d, i)[0]
    if not (2 < n < 80) or i + 4 + n > len(d):
        return None
    s = d[i + 4:i + 4 + n]
    if s[-1:] != b"\x00" or not all(32 <= c < 127 for c in s[:-1]):
        return None
    return s[:-1].decode(), 4 + n


def extract(path):
    d = open(path, "rb").read()
    out, seen, i = [], set(), 0
    while i < len(d) - 28:
        row = _read_fstring(d, i)
        if row:
            name, used = row
            x, y, z = struct.unpack_from("<ddd", d, i + used)
            if (XY_MIN < abs(x) < XY_MAX and XY_MIN < abs(y) < XY_MAX
                    and abs(z) < Z_MAX):
                if name not in seen:
                    seen.add(name)
                    out.append({"name": name, "x": x, "y": y, "z": z})
                i += used + 24
                continue
        i += 1
    return out


if __name__ == "__main__":
    pois = extract(sys.argv[1])
    json.dump(pois, open(sys.argv[2], "w"), indent=1)
    print(f"{len(pois)} ubicaciones -> {sys.argv[2]}")
