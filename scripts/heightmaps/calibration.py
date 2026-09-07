"""Como se pasa del heightfield crudo a metros y a coordenadas del mundo.

Todo esto se midio el 2026-09-05 contra las 355 ubicaciones con coordenadas del
`DT_Locations` del mod Teleport (`extract_pois.py`), que es la unica fuente de
pares (lugar, coordenada) que no exige entrar al juego.

Horizontal
    1 muestra = 100 uu = 1 m, y el origen de la grilla cae en el (0,0) del mundo:
        world_x = col * 100      world_y = fila * 100
    El ajuste libre de la escala dio 99,1 uu/muestra, 7 cm mejor que 100 sobre un
    residuo de 87 cm — o sea, ruido. Se usa 100, que ademas cierra con la grilla
    de World Partition: 510 muestras por celda * 16 celdas = 8160 m.

Vertical
    La formula es la estandar de Landscape de Unreal,
        z_uu = (v - 32768) / 128 * Z_SCALE
    con Z_SCALE = 100, el valor por defecto del motor.

    Ojo con como se llego a ese 100, porque la via directa engania: regresar Z
    contra v da pendientes de 0,63-0,70 (ZScale 81-90), no 0,781. Son dos efectos
    sumados y los dos tiran para abajo:
      - La Zona es PLANA. La mitad de las ubicaciones esta entre 3 y 8 m, asi que
        la regresion casi no tiene palanca.
      - Dilucion por desalineacion: el error de muestreo esta en la variable
        independiente, y eso atenua la pendiente hacia cero.
    Corrigiendo con la media geometrica de la regresion directa y la inversa da
    94, y fijando ZScale y ajustando solo el offset el residuo tiene minimo claro
    en 100 (0,64 m contra 0,84 en 90 y 0,95 en 110).

Calidad
    Residuo mediano 0,64 m, p90 6,1 m sobre 288 ubicaciones. Los descartados se
    explican solos y confirman el ajuste en vez de romperlo: `School Rooftop`
    +129 m es una azotea, `Scanner 1` +96 m una antena, `Main Menu` -42 m ni
    siquiera es un lugar del mapa.
"""
UU_PER_SAMPLE = 100.0
UU_PER_METRE = 100.0
Z_SCALE = 100.0
HEIGHT_MIDPOINT = 32768


def raw_to_metres(v, z_offset_uu):
    """v (uint16 del heightmap) -> metros, con el offset del actor ya medido."""
    return ((v - HEIGHT_MIDPOINT) / 128.0 * Z_SCALE + z_offset_uu) / UU_PER_METRE


def sample_to_world(col, row):
    return col * UU_PER_SAMPLE, row * UU_PER_SAMPLE
