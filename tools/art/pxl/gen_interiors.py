#!/usr/bin/env python3
"""Genera los interiores de los 24 negocios provinciales (10.0) x 5 niveles.

Escribe:
  tools/art/pxl/interiors.px.js  -> escenas PXL: sólo la habitación (pared, piso, ventana)
  tools/art/pxl/out/layout.json  -> la utilería de cada nivel (la estampa compose_interiors.py,
                                    12.1: piezas "símil 3D" de tools/art/props_art.py)
  data/interiors.json            -> puestos de trabajo, fila de clientes y animaciones

12.1, reglas de profundidad (los personajes no se paran "encima" de los muebles):
  - la utilería del piso se ordena por la fila donde apoya (lo de adelante tapa);
  - un empleado nunca queda detrás de un mueble que está más adelante que él
    (se dibuja encima de la capa "back"): si pasa, el puesto se corre al hueco libre
    más cercano; si no hay, falla la generación;
  - los muebles del piso no se encastran entre sí (misma fila y superpuestos = error);
  - los clientes caminan con los pies en y >= 162: siempre delante de todo; donde
    se paran a hacer fila no puede haber ningún mueble del piso detrás de su cuerpo
    (no parecen subidos a una cinta o a un cajón).

Lienzo 400x170 (1 m = 24 px). Pared 0..110, piso 110..170.
Los mostradores van en la capa "front" (tapan las piernas de quien atiende).
Empleados detrás del mostrador: pies en y=134. Clientes: pies en y~164.
"""
import json
import zlib
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
W, H = 400, 170
WALL = 110
FRONT_BASE = 148
BEHIND = 134
QUEUE_Y = 164

# Tamaño final de cada pieza (con el contorno de 1 px ya sumado).
SZ = {
    "_counter_wood": (74, 34), "_counter_glass": (74, 34), "_counter_metal": (66, 32), "_register": (24, 20),
    "_scale": (20, 16), "_slicer": (24, 18), "_mate_set": (24, 20), "_shelf_wood": (52, 72), "_shelf_metal": (52, 74),
    "_shelf_almacen": (58, 76), "_gondola": (72, 66), "_fridge_drinks": (34, 72), "_freezer": (48, 32), "_grill": (66, 42),
    "_stove": (62, 48), "_prep_table": (58, 38), "_coffee_machine": (34, 32), "_pastry_case": (62, 36), "_dining_table": (42, 32),
    "_cafe_table": (44, 38), "_chalkboard": (36, 28), "_wine_rack": (32, 58), "_car": (66, 32), "_car_lift": (86, 66),
    "_tool_wall": (62, 42), "_tires": (26, 38), "_drums": (34, 30), "_workbench": (62, 36), "_wash_bay": (98, 62),
    "_vacuum": (18, 36), "_treadmill": (52, 42), "_weight_rack": (48, 48), "_bench_press": (56, 36), "_punching_bag": (20, 52),
    "_mirror": (72, 48), "_desk_pc": (54, 40), "_filing": (24, 48), "_water_cooler": (18, 46), "_parcel_shelf": (62, 68),
    "_pallet_rack": (82, 82), "_forklift": (68, 58), "_dock_door": (72, 74), "_pallet_boxes": (36, 32), "_scooter": (42, 34),
    "_clock": (18, 18), "_pennant": (72, 18), "_jersey": (24, 24), "_fileteado_sign": (72, 20), "_plant": (20, 30),
    "_poster": (22, 28), "_lamp_hanging": (16, 18), "_crate": (28, 20), "_salames": (30, 22), "_checkout": (68, 44),
    "_cart": (30, 30), "_conveyor": (112, 38), "_machine": (52, 58), "_stall_table": (82, 36), "_umbrella": (90, 70),
    "_cooler": (32, 24), "_price_board": (20, 32), "_string_lights": (200, 16), "_wall_shelf": (70, 22),
    # 10.0 (furniture_v10.px.js)
    "_bales": (42, 28), "_sacks": (42, 32), "_barrels_wood": (56, 38), "_steel_tank": (30, 70), "_olive_press": (48, 50),
    "_citrus_crates": (42, 30), "_drying_rack": (62, 42), "_oven": (54, 58), "_meat_hooks": (44, 36), "_cheese_shelf": (46, 52),
    "_electronics_bench": (72, 42),
    # 12.2: detalles fijos de pared (que el nivel 0 no quede pelado) y piezas por rubro
    "_lamp_tube": (32, 12), "_lamp_bronze": (18, 22), "_cold_door": (46, 74), "_counter_pastry": (74, 34),
    "_poster_uva": (22, 28), "_poster_vaca": (22, 28), "_poster_oveja": (22, 28), "_poster_trigo": (22, 28),
    "_poster_mate": (22, 28), "_poster_fruta": (22, 28),
    "_elec_panel": (16, 44), "_calendar": (16, 20), "_outlet": (8, 8),
    "_machine_press": (52, 58), "_machine_mill": (52, 58), "_machine_mixer": (52, 58), "_bread_rack": (52, 72), "_potato_bins": (48, 28), "_banana_hooks": (42, 42), "_apple_bins": (48, 30),
}
FX = {"fx_smoke": (24, 34), "fx_steam": (12, 18), "fx_neon": (48, 16), "fx_tv": (36, 24), "fx_foam": (30, 16), "fx_conveyor": (110, 10)}


class Layout:
    def __init__(self, wall, floor, outdoor=False):
        self.wall, self.floor, self.outdoor = wall, floor, outdoor
        self.back, self.front, self.stations, self.queue, self.fx = [], [], [], [], []
        self.counters = []

    def put(self, part, x, base, front=False, top=None):
        """base = fila donde apoya (abajo). top = posición y superior explícita (cosas colgadas)."""
        w, h = SZ[part]
        y = top if top is not None else base - h
        (self.front if front else self.back).append((part, x, y))
        return x, y, w, h

    def wall_item(self, part, x, y):
        return self.put(part, x, 0, top=y)

    def counter(self, part, x, workers=1, queue=True):
        cx, cy, w, h = self.put(part, x, FRONT_BASE, front=True)
        self.counters.append((x, cy, w))
        # Quien atiende va en el tercio izquierdo; los objetos, a la derecha.
        for i in range(workers):
            self.station(x + 18 + i * 30, BEHIND, "counter")
        if queue:
            self.queue.append([x + w // 2, QUEUE_Y])
        return cx, cy, w, h

    def on_counter(self, part, slot=0, idx=-1):
        """12.2: lo de arriba del mostrador se acomoda de derecha a izquierda
        sin pisarse (antes iba a 24 px fijos por lugar y una cafetera de 42 px
        tapaba la caja registradora)."""
        cx, cy, w = self.counters[idx]
        pw, ph = SZ[part]
        used = getattr(self, "_on_used", {}).get(idx if idx >= 0 else len(self.counters) + idx, 0)
        x = cx + w - pw - 4 - used
        self._on_used = getattr(self, "_on_used", {})
        self._on_used[idx if idx >= 0 else len(self.counters) + idx] = used + pw + 6
        (self.front).append((part, x, cy - ph + 3))

    def station(self, x, y, kind="stand", flip=False):
        self.stations.append({"x": int(x), "y": int(y), "kind": kind, "flip": flip})

    def fx_at(self, name, x, y):
        self.fx.append({"anim": name, "x": int(x), "y": int(y)})


def ceiling_lamps(L, n):
    for i in range(n):
        L.wall_item("_lamp_hanging", 40 + i * (320 // max(1, n - 1 if n > 1 else 1)), 4)


# ---------------------------------------------------------------- negocios
# 10.0: cada provincia es una lista a mano de (nivel mínimo, pieza, x, apoyo).
# apoyo: número = fila donde apoya; "wall:y" = colgado en la pared a esa altura;
# ("station", x, y) = puesto de trabajo extra; ("fx", nombre, x, y) = animación.
# El mostrador (counter) siempre está, con su caja/balanza arriba.

F = WALL          # apoyado contra la pared
M = 150           # en el medio del piso
N = 158           # adelante

PROVINCES = {
    "algodonal": ("cal", "cemento", "_counter_wood", 250, "_scale", [
        (0, "_bales", 30, F), (0, "_crate", 90, F), (1, "_bales", 80, M), (1, "_mate_set", 296, "wall:70"),
        (2, "_sacks", 140, F), (2, "_pennant", 40, "wall:12"), (3, "_conveyor", 20, N), ("fx", 3, "fx_conveyor", 21, 128),
        (3, "_machine", 150, M), ("station", 3, 180, 128), (4, "_bales", 330, F), (4, "_clock", 200, "wall:18")]),
    "papas_andinas": ("adobe", "cemento", "_counter_wood", 220, "_scale", [
        (0, "_potato_bins", 30, M), (0, "_sacks", 90, F), (1, "_potato_bins", 100, N), (1, "_mate_set", 280, "wall:70"),
        (2, "_shelf_wood", 140, F), (2, "_pennant", 30, "wall:12"), (3, "_crate", 318, F), (3, "_crate", 340, F),
        (3, "_poster", 300, "wall:24"), (4, "_potato_bins", 320, N), (4, "_plant", 370, F)]),
    "almazara": ("cal", "ceramica", "_counter_glass", 270, "_register", [
        (0, "_olive_press", 30, M), (0, "_crate", 60, F), (1, "_steel_tank", 100, F), (1, "_shelf_wood", 172, F),
        ("station", 1, 70, 132), (2, "_steel_tank", 136, F), (3, "_machine", 180, M), ("station", 3, 210, 126),
        (3, "_clock", 300, "wall:18"), (4, "_steel_tank", 350, F), (4, "_plant", 20, F)]),
    "olivar": ("cal", "cemento", "_counter_wood", 260, "_scale", [
        (0, "_crate", 30, F), (0, "_crate", 54, F), (0, "_sacks", 90, F), (1, "_olive_press", 120, M),
        (2, "_shelf_wood", 136, F), (2, "_wine_rack", 190, F), (3, "_steel_tank", 340, F), (3, "_pennant", 140, "wall:12"),
        (4, "_conveyor", 30, N), ("fx", 4, "fx_conveyor", 31, 128)]),
    "bodega_torrontes": ("cal", "madera", "_counter_wood", 240, "_register", [
        (0, "_barrels_wood", 30, F), (0, "_wine_rack", 100, F), (1, "_barrels_wood", 140, M), (1, "_cafe_table", 330, N),
        (2, "_steel_tank", 180, F), (2, "_lamp_hanging", 300, "wall:4"), (3, "_wine_rack", 360, F), (3, "_barrels_wood", 30, N),
        (4, "_chalkboard", 290, "wall:30"), (4, "_cafe_table", 150, N)]),
    "citricola": ("cal", "cemento", "_counter_metal", 290, "_scale", [
        (0, "_citrus_crates", 30, F), (0, "_citrus_crates", 80, M), (1, "_citrus_crates", 76, F), (1, "_prep_table", 180, M),
        ("station", 1, 205, 130), (2, "_conveyor", 40, N), ("fx", 2, "fx_conveyor", 41, 128), (3, "_steel_tank", 220, F),
        (3, "_machine", 150, F), (4, "_forklift", 196, N), (4, "_citrus_crates", 250, N)]),
    "bananal": ("madera_rustica", "cemento", "_counter_wood", 250, "_scale", [
        (0, "_banana_hooks", 30, "wall:30"), (0, "_crate", 40, F), (1, "_banana_hooks", 90, "wall:30"), (1, "_prep_table", 120, M),
        ("station", 1, 146, 130), (2, "_citrus_crates", 200, F), (3, "_banana_hooks", 160, "wall:30"), (3, "_cooler", 330, F),
        (4, "_conveyor", 60, N), ("fx", 4, "fx_conveyor", 61, 128)]),
    "desmotadora": ("chapa", "cemento", "_counter_metal", 300, "_register", [
        (0, "_bales", 30, F), (0, "_machine", 90, F), ("station", 0, 142, 128), (1, "_bales", 156, M), (1, "_conveyor", 20, N),
        ("fx", 1, "fx_conveyor", 21, 128), (2, "_machine", 200, F), ("station", 2, 230, 128), (3, "_pallet_rack", 210, N),
        (4, "_pallet_boxes", 260, F), (4, "_clock", 300, "wall:18")]),
    "arrocera": ("madera_rustica", "cemento", "_counter_wood", 260, "_scale", [
        (0, "_sacks", 30, F), (0, "_sacks", 70, F), (1, "_sacks", 120, M), (1, "_mate_set", 300, "wall:70"), (2, "_machine", 150, F),
        ("station", 2, 180, 128), (3, "_pallet_boxes", 30, N), (3, "_pennant", 40, "wall:12"), (4, "_forklift", 200, N)]),
    "molino_arrocero": ("ladrillo", "cemento", "_counter_metal", 300, "_register", [
        (0, "_sacks", 30, F), (0, "_machine", 80, F), ("station", 0, 110, 128), (1, "_conveyor", 20, N), ("fx", 1, "fx_conveyor", 21, 128),
        (2, "_sacks", 150, M), (2, "_machine", 200, F), (3, "_pallet_rack", 220, N), (4, "_forklift", 130, N), (4, "_clock", 310, "wall:18")]),
    "yerbatal": ("madera_rustica", "madera", "_counter_wood", 260, "_scale", [
        (0, "_drying_rack", 30, F), (0, "_mate_set", 300, "wall:70"), (1, "_sacks", 110, M), (1, "_drying_rack", 150, F),
        ("fx", 2, "fx_smoke", 70, 40), (2, "_machine", 210, F), ("station", 2, 240, 128), (3, "_conveyor", 20, N),
        ("fx", 3, "fx_conveyor", 21, 128), (4, "_sacks", 340, F), (4, "_pennant", 140, "wall:10")]),
    "frigorifico": ("azulejo", "ceramica", "_counter_glass", 260, "_scale", [
        (0, "_meat_hooks", 30, "wall:24"), (0, "_freezer", 40, M), (1, "_meat_hooks", 90, "wall:24"), (1, "_slicer", 260, "on"),
        (2, "_cheese_shelf", 150, F), (2, "_prep_table", 100, N), ("station", 2, 124, 140), (3, "_freezer", 200, M),
        (4, "_steel_tank", 330, F), (4, "_clock", 210, "wall:4")]),
    "pasas": ("adobe", "cemento", "_counter_wood", 260, "_scale", [
        (0, "_drying_rack", 30, F), (1, "_drying_rack", 100, F), (1, "_crate", 30, M), (2, "_wine_rack", 170, F),
        (2, "_sacks", 200, M), (3, "_barrels_wood", 330, F), (3, "_pennant", 30, "wall:10"), (4, "_conveyor", 40, N),
        ("fx", 4, "fx_conveyor", 41, 128)]),
    "bodega_malbec": ("ladrillo", "madera", "_counter_wood", 250, "_register", [
        (0, "_barrels_wood", 30, F), (0, "_wine_rack", 90, F), (1, "_wine_rack", 124, F), (1, "_barrels_wood", 30, N),
        (2, "_steel_tank", 170, F), (2, "_steel_tank", 204, F), (2, "_lamp_hanging", 300, "wall:4"), (3, "_cafe_table", 330, N),
        (3, "_chalkboard", 290, "wall:30"), (4, "_barrels_wood", 140, N), (4, "_fileteado_sign", 140, "wall:6")]),
    "estancia_ovina": ("madera_rustica", "madera", "_counter_wood", 260, "_scale", [
        (0, "_bales", 30, F), (0, "_meat_hooks", 100, "wall:24"), (1, "_bales", 80, M), (1, "_mate_set", 300, "wall:70"),
        (2, "_freezer", 150, F), (2, "_pennant", 30, "wall:10"), (3, "_bales", 340, F), (3, "_poster", 200, "wall:24"),
        (4, "_cafe_table", 150, N)]),
    "lanera": ("chapa", "cemento", "_counter_metal", 300, "_register", [
        (0, "_bales", 30, F), (0, "_machine", 90, F), ("station", 0, 142, 128), (1, "_bales", 156, M), (2, "_conveyor", 20, N),
        ("fx", 2, "fx_conveyor", 21, 128), (2, "_machine", 200, F), ("station", 2, 230, 128), (3, "_pallet_rack", 200, N),
        (4, "_forklift", 130, N)]),
    "chacra_peras": ("madera_rustica", "cemento", "_counter_wood", 260, "_scale", [
        (0, "_apple_bins", 30, M), (0, "_crate", 140, F), (1, "_apple_bins", 90, F), (1, "_prep_table", 150, M),
        ("station", 1, 176, 130), (2, "_citrus_crates", 30, F), (3, "_cooler", 340, F), (3, "_pennant", 140, "wall:10"),
        (4, "_conveyor", 40, N), ("fx", 4, "fx_conveyor", 41, 128)]),
    "manzanas": ("chapa", "cemento", "_counter_metal", 300, "_scale", [
        (0, "_apple_bins", 30, F), (0, "_apple_bins", 90, M), (1, "_conveyor", 20, N), ("fx", 1, "fx_conveyor", 21, 128),
        (2, "_machine", 150, F), ("station", 2, 180, 128), (3, "_pallet_rack", 210, N), (4, "_pallet_boxes", 252, F),
        (4, "_clock", 300, "wall:18")]),
    "electronica": ("pintura_celeste", "goma", "_counter_metal", 300, "_register", [
        (0, "_electronics_bench", 30, M), ("station", 0, 60, 132), (1, "_electronics_bench", 120, M), ("station", 1, 150, 132),
        (2, "_shelf_metal", 220, F), (2, "_desk_pc", 30, F), (3, "_conveyor", 20, N), ("fx", 3, "fx_conveyor", 21, 128),
        (3, "_clock", 140, "wall:14"), (4, "_machine", 160, F), ("fx", 4, "fx_tv", 280, 20)]),
    "estancia_ganadera": ("madera_rustica", "madera", "_counter_wood", 260, "_scale", [
        (0, "_meat_hooks", 30, "wall:24"), (0, "_sacks", 40, M), (1, "_mate_set", 300, "wall:70"), (1, "_freezer", 100, F),
        (2, "_meat_hooks", 140, "wall:24"), (2, "_sacks", 160, M), (3, "_poster", 220, "wall:24"), (3, "_cafe_table", 340, N),
        (4, "_pennant", 30, "wall:10"), (4, "_freezer", 200, F)]),
    "salames": ("ladrillo", "ceramica", "_counter_glass", 260, "_slicer", [
        (0, "_salames", 40, "wall:30"), (0, "_crate", 40, M), (1, "_salames", 90, "wall:30"), (1, "_prep_table", 100, M),
        ("station", 1, 124, 130), (2, "_cheese_shelf", 170, F), (3, "_salames", 330, "wall:30"), (3, "_freezer", 330, M),
        (4, "_machine", 230, F), (4, "_fileteado_sign", 30, "wall:6")]),
    "usina_lactea": ("azulejo", "ceramica", "_counter_glass", 270, "_register", [
        (0, "_cheese_shelf", 30, F), (0, "_freezer", 90, M), (1, "_steel_tank", 100, F), (1, "_steel_tank", 134, F),
        (2, "_machine", 170, F), ("station", 2, 200, 126), (3, "_conveyor", 20, N), ("fx", 3, "fx_conveyor", 21, 128),
        (4, "_steel_tank", 350, F), (4, "_clock", 220, "wall:18")]),
    "molino_harinero": ("cal", "cemento", "_counter_metal", 300, "_scale", [
        (0, "_sacks", 30, F), (0, "_sacks", 70, M), (1, "_machine", 110, F), ("station", 1, 140, 128), (2, "_sacks", 170, M),
        (2, "_conveyor", 20, N), ("fx", 2, "fx_conveyor", 21, 128), (3, "_pallet_rack", 200, N), (4, "_forklift", 140, N)]),
    "panaderia": ("madera_pared", "damero", "_counter_glass", 230, "_register", [
        (0, "_oven", 30, F), (0, "_pastry_case", 100, M), (1, "_coffee_machine", 236, "on1"), (1, "_cafe_table", 340, N),
        (2, "_shelf_wood", 150, F), (2, "_chalkboard", 290, "wall:30"), (3, "_cafe_table", 30, N), (3, "_fileteado_sign", 160, "wall:6"),
        (4, "_lamp_hanging", 300, "wall:4"), (4, "_plant", 370, F), ("fx", 4, "fx_steam", 60, 20)]),
}


# 12.2: una máquina propia por rubro (antes el mismo bloque azul en todos lados).
MACHINE = {"algodonal": "_machine_press", "desmotadora": "_machine_press", "lanera": "_machine_press",
           "estancia_ovina": "_machine_press", "almazara": "_machine_press", "olivar": "_machine_press",
           "pasas": "_machine_press", "molino_arrocero": "_machine_mill", "molino_harinero": "_machine_mill",
           "arrocera": "_machine_mill", "yerbatal": "_machine_mill", "papas_andinas": "_machine_mill",
           "panaderia": "_machine_mixer", "salames": "_machine_mixer", "usina_lactea": "_machine_mixer",
           "frigorifico": "_machine_mixer"}
# y piezas propias del rubro en lugar de las genéricas
SWAP = {("panaderia", "_shelf_wood"): "_bread_rack", ("frigorifico", "_cheese_shelf"): "_cold_door"}
COUNTER_SWAP = {"panaderia": "_counter_pastry"}
# Lámpara del techo según el rubro: tubo fluorescente en lo industrial y lo frío,
# colgante de bronce en lo tradicional, la verde de galpón en el resto.
TUBE = {"frigorifico", "usina_lactea", "electronica", "desmotadora", "lanera", "molino_arrocero", "molino_harinero",
        "citricola", "manzanas", "chacra_peras", "arrocera"}
BRONZE = {"panaderia", "bodega_malbec", "bodega_torrontes", "salames", "almazara", "olivar", "pasas",
          "estancia_ovina", "estancia_ganadera", "papas_andinas"}
LAMP_PARTS = {"_lamp_hanging", "_lamp_tube", "_lamp_bronze"}
POSTER = {"bodega_malbec": "_poster_uva", "bodega_torrontes": "_poster_uva", "pasas": "_poster_uva",
          "estancia_ganadera": "_poster_vaca", "frigorifico": "_poster_vaca", "salames": "_poster_vaca",
          "usina_lactea": "_poster_vaca", "estancia_ovina": "_poster_oveja", "lanera": "_poster_oveja",
          "molino_harinero": "_poster_trigo", "arrocera": "_poster_trigo", "molino_arrocero": "_poster_trigo",
          "panaderia": "_poster_trigo", "yerbatal": "_poster_mate", "citricola": "_poster_fruta",
          "manzanas": "_poster_fruta", "chacra_peras": "_poster_fruta", "bananal": "_poster_fruta",
          "olivar": "_poster_fruta", "almazara": "_poster_fruta"}
INDUSTRIAL = {"desmotadora", "lanera", "molino_arrocero", "molino_harinero", "arrocera", "electronica",
              "usina_lactea", "frigorifico", "citricola", "manzanas"}
# Detalles de pared propios del rubro desde el nivel 0 (que el local no quede pelado).
RUBRO_WALL = {
    "algodonal": [("_tool_wall", 150, 30)], "desmotadora": [("_tool_wall", 120, 30)], "lanera": [("_tool_wall", 120, 30)],
    "molino_arrocero": [("_tool_wall", 160, 30)], "molino_harinero": [("_tool_wall", 160, 30)],
    "arrocera": [("_poster", 200, 30)], "yerbatal": [("_poster", 200, 30), ("_wall_shelf", 120, 44)],
    "papas_andinas": [("_wall_shelf", 200, 44)], "almazara": [("_wall_shelf", 230, 44)], "olivar": [("_poster", 60, 30)],
    "bodega_torrontes": [("_fileteado_sign", 120, 18)], "bodega_malbec": [("_poster", 60, 30)],
    "citricola": [("_poster", 90, 30)], "bananal": [("_poster", 230, 30)], "pasas": [("_wall_shelf", 150, 44)],
    "frigorifico": [("_poster", 220, 30)], "estancia_ovina": [("_poster", 180, 30)],
    "estancia_ganadera": [("_poster", 250, 30)], "chacra_peras": [("_poster", 230, 30)],
    "manzanas": [("_tool_wall", 120, 30)], "electronica": [("_poster", 240, 30), ("_wall_shelf", 120, 44)],
    "salames": [("_poster", 120, 30)], "usina_lactea": [("_poster", 120, 30)],
    "panaderia": [("_wall_shelf", 120, 44)],
}


def province_layout(bid, t):
    wall_kind, floor, counter, cx, on_top, items = PROVINCES[bid]
    L = Layout(wall_kind, floor)
    counter = COUNTER_SWAP.get(bid, counter)
    L.counter(counter, cx, 1 + (t >= 3))
    L.on_counter(on_top, 0)
    for it in items:
        if it[0] == "station":
            _, tmin, x, y = it
            if t >= tmin:
                L.station(x, y, "stand")
            continue
        if it[0] == "fx":
            _, tmin, name, x, y = it
            if t >= tmin:
                L.fx_at(name, x, y)
            continue
        tmin, part, x, base = it
        if t < tmin:
            continue
        if part == "_machine":
            part = MACHINE.get(bid, part)
        part = SWAP.get((bid, part), part)
        if base == "on":
            L.on_counter(part, 1)
        elif base == "on1":
            L.on_counter(part, 1)
        elif isinstance(base, str) and base.startswith("wall:"):
            L.wall_item(part, x, int(base[5:]))
        else:
            L.put(part, x, base)
    # 12.2: detalles de pared del rubro desde el nivel 0, el tablero eléctrico sólo
    # en lo industrial, el almanaque en la mitad de los locales y un enchufe; el
    # validador los corre a un hueco libre o los saca.
    h0 = zlib.crc32(bid.encode())
    for part, x, y in RUBRO_WALL.get(bid, []):
        L.wall_item(part, x, y)
    if bid in INDUSTRIAL:
        L.wall_item("_elec_panel", 30 + h0 % 200, 6)
    if h0 % 2:
        L.wall_item("_calendar", 150 + (h0 // 7) % 160, 40)
    if (h0 // 3) % 2:
        L.wall_item("_outlet", 60 + (h0 // 13) % 260, 92)
    # un solo póster por local, con el tema del rubro
    seen = False
    keep = []
    for it in L.back:
        if it[0] == "_poster":
            if seen:
                continue
            seen = True
            it = (POSTER.get(bid, "_poster"), it[1], it[2])
        keep.append(it)
    L.back = keep
    L.lamp_part = "_lamp_tube" if bid in TUBE else ("_lamp_bronze" if bid in BRONZE else "_lamp_hanging")
    ceiling_lamps(L, min(3, 2 + t // 2))
    return L


# Rubros donde tiene sentido una repisa con mercadería en la pared.
RETAIL = {"panaderia", "papas_andinas", "salames"}

BUSINESSES = {bid: (lambda t, b=bid: province_layout(b, t)) for bid in PROVINCES}


def add_wall_shelves(L, n):
    """Repisas de pared en los huecos libres (que ningún local quede pelado)."""
    busy = []
    for p, x, y in L.back:
        w, h = SZ[p]
        if y < 70:
            busy.append((x - 4, x + w + 4))
    for f in L.fx:
        busy.append((f["x"] - 4, f["x"] + 52))
    placed = 0
    for x in range(24, 330, 6):
        if placed >= n:
            break
        if all(x + 70 < a or x > b for a, b in busy):
            L.back.append(("_wall_shelf", x, 40))
            busy.append((x - 10, x + 80))
            placed += 1


## Niveles sin local cerrado (mesita, carrito, lavadero a cielo abierto): el
## juego muestra sólo la vista de calle y oculta el botón FACHADA/ADENTRO.
NO_INTERIOR = {}


## Objetos con letras: no pueden quedar cortados por el borde de la pantalla
## (en 360 px de ancho se ven x=20..380 del lienzo) ni debajo de los botones
## FACHADA/BONOS (íconos) de arriba a la derecha (x=338..380, y<80).
TEXT_PARTS = {"_chalkboard", "_dock_door", "_freezer", "_fridge_drinks", "_gondola", "_jersey", "_neon_open",
              "_poster", "_price_board", "_scooter", "_vacuum", "fx_neon"}
VISIBLE_X = (20, 380)
BUTTONS = (338, 0, 380, 80)


def check_text_items(name, L):
    errs = []
    items = [(p, x, y, *SZ[p]) for p, x, y in L.back + L.front if p in TEXT_PARTS]
    items += [(e["anim"], e["x"], e["y"], *FX[e["anim"]]) for e in L.fx if e["anim"] in TEXT_PARTS]
    for p, x, y, w, h in items:
        if x < VISIBLE_X[0] or x + w > VISIBLE_X[1]:
            errs.append(f"{name}: {p} en x={x} queda cortado por el borde")
        bx0, by0, bx1, by1 = BUTTONS
        if x < bx1 and x + w > bx0 and y < by1 and y + h > by0:
            errs.append(f"{name}: {p} en ({x},{y}) queda debajo de los botones")
    return errs


# ---------------------------------------------------------------- 12.1 profundidad
CUSTOMER_LANE = 160          # ningún mueble del fondo apoya más abajo que esto
QUEUE_REACH = 21             # el cliente frena a ±10 px del lugar y mide ±11 px
BODY = (11, 44)              # medio ancho y alto del cuerpo de un personaje (sin el aire del sprite)


def _floor_items(L):
    """Utilería apoyada en el piso de la capa back: (pieza, x, y, w, h, base)."""
    out = []
    for p, x, y in L.back:
        w, h = SZ[p]
        base = y + h
        if base >= WALL:                     # lo colgado en la pared termina más arriba
            out.append((p, x, y, w, h, base))
    return out


def _hits(sx, sy, x, y, w, h, pad=2):
    bx0, by0, bx1, by1 = sx - BODY[0], sy - BODY[1], sx + BODY[0], sy
    return bx0 < x + w - pad and bx1 > x + pad and by0 < y + h - pad and by1 > y + pad


def fix_depth(name, L):
    """Corrige puestos tapados mal y valida la utilería. Devuelve errores."""
    errs = []
    items = _floor_items(L)
    for st in L.stations:
        bad = [it for it in items if it[5] > st["y"] + 1 and _hits(st["x"], st["y"], *it[1:5])]
        if not bad:
            continue
        if st["kind"] == "counter":
            errs.append(f"{name}: el que atiende en x={st['x']} queda detrás de {bad[0][0]}")
            continue
        x0 = st["x"]
        moved = False
        for d in range(4, 160, 4):
            for nx in (x0 - d, x0 + d):
                if not 24 <= nx <= W - 24:
                    continue
                if any(it[5] > st["y"] + 1 and _hits(nx, st["y"], *it[1:5]) for it in items):
                    continue
                if any(o is not st and abs(o["x"] - nx) < 22 and abs(o["y"] - st["y"]) < 10 for o in L.stations):
                    continue
                st["x"] = nx
                moved = True
                break
            if moved:
                break
        if not moved:
            errs.append(f"{name}: no hay lugar libre para el puesto de x={x0}")
    for i, a in enumerate(items):
        if a[5] > CUSTOMER_LANE:
            errs.append(f"{name}: {a[0]} en x={a[1]} invade el pasillo de los clientes (apoya en {a[5]})")
        for b in items[i + 1:]:
            ox = min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1])
            oy = min(a[2] + a[4], b[2] + b[4]) - max(a[2], b[2])
            if ox > 3 and oy > 3 and abs(a[5] - b[5]) < 6:
                errs.append(f"{name}: {a[0]} (x={a[1]}) y {b[0]} (x={b[1]}) se encastran")
    for q in L.queue:
        for it in items:
            if it[1] < q[0] + QUEUE_REACH and it[1] + it[3] > q[0] - QUEUE_REACH and it[5] > QUEUE_Y - BODY[1]:
                errs.append(f"{name}: la fila en x={q[0]} queda delante de {it[0]} (x={it[1]})")
    return errs


# ---------------------------------------------------------------- 12.2 pared sin choques
# Nada se superpone con el fondo ni entre sí: la ventana, lo colgado en la pared y
# las lámparas del techo se ubican en huecos libres (lo más cerca posible de donde
# estaban), sin tocar los muebles del piso, los mostradores, lo que va arriba del
# mostrador ni las animaciones. Un adorno que no entra se saca (y se avisa); una
# pieza del rubro que no entra es un error.
sys.path.insert(0, os.path.dirname(HERE))
import rooms_art  # noqa: E402

DECOR = {"_poster_uva", "_poster_vaca", "_poster_oveja", "_poster_trigo", "_poster_mate", "_poster_fruta",
         "_tool_wall", "_pennant", "_clock", "_poster", "_mate_set", "_lamp_hanging", "_wall_shelf", "_chalkboard",
         "_fileteado_sign", "_plant", "_jersey", "_elec_panel", "_calendar", "_outlet"}
WALL_PAD = 14                # aire entre cosas de la pared (y con la ventana)
WINDOW_PAD = 12              # nada alto pegado al marco de la ventana

# Vista de la ventana según el rubro (campo, viñedo, huerto o ciudad).
VIEW = {"bodega_malbec": "vinedo", "bodega_torrontes": "vinedo", "pasas": "vinedo", "olivar": "huerto",
        "almazara": "huerto", "manzanas": "huerto", "chacra_peras": "huerto", "citricola": "huerto",
        "bananal": "huerto", "yerbatal": "huerto", "estancia_ovina": "campo", "estancia_ganadera": "campo",
        "lanera": "campo", "algodonal": "campo", "desmotadora": "campo", "arrocera": "campo",
        "papas_andinas": "cerros", "molino_arrocero": "campo"}
PAD = 6
WALL_X = (28, 372)          # se ve x = 20..380 del lienzo (8 px de margen)


def _overlap(a, b, pad=PAD):
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw + pad and bx < ax + aw + pad and ay < by + bh + pad and by < ay + ah + pad


FLOOR_PAD = 6


def place_floor(name, L, notes):
    """12.2: los muebles del piso no se tapan entre sí (ni a los mostradores ni a
    lo de arriba del mostrador ni a la fila de clientes). Cada pieza, en el orden
    en que aparece al subir de nivel, se queda en su fila y busca el hueco libre
    más cercano; si no hay, prueba las otras filas; si tampoco, se omite (y se
    avisa). Su puesto de trabajo y su animación se mueven con ella."""
    obst = [(x, y, *SZ[p]) for p, x, y in L.front]
    for q in L.queue:
        obst.append((q[0] - QUEUE_REACH, QUEUE_Y - BODY[1] + 4, 2 * QUEUE_REACH, BODY[1]))
    placed = []
    keep = []
    floor = []
    for it in L.back:
        p, x, y = it
        w, h = SZ[p]
        (floor if y + h >= WALL else keep).append(it)
    BULKY = {"_forklift", "_pallet_rack", "_conveyor", "_machine", "_machine_press", "_machine_mill", "_machine_mixer",
             "_steel_tank", "_olive_press", "_shelf_metal", "_parcel_shelf"}
    counters = [(x, y, *SZ[p]) for p, x, y in L.front if p.startswith("_counter")]
    for p, x, y in floor:
        w, h = SZ[p]
        base = y + h
        extra = [(cx - 6, WALL - 90, cw + 12, 90 + ch) for cx, cy, cw, ch in counters] if p in BULKY else []
        tied_st = [st for st in L.stations if st["kind"] != "counter" and x - 8 <= st["x"] <= x + w + 8
                   and not any(st is t2 for t2 in getattr(L, "_tied", []))]
        tied_fx = [f for f in L.fx if x - 2 <= f["x"] <= x + w and base - h - 40 <= f["y"] <= base]
        lo, hi = (28, W - 28)            # 12.2: margen de seguridad dentro de lo visible
        best = None
        for b in [base] + [bb for bb in (WALL, 150, 158) if bb != base]:
            ny = b - h
            for d in range(0, 400, 2):
                for nx in ((x - d, x + d) if d else (x,)):
                    if nx < lo or nx + w > hi:
                        continue
                    r = (nx, ny, w, h)
                    if any(_overlap(r, o, FLOOR_PAD) for o in obst + placed + extra):
                        continue
                    best = (nx, ny)
                    break
                if best:
                    break
            if best:
                break
        if not best:
            notes.append(f"{name}: {p} no entra en el piso sin tapar a otro (se omite)")
            for st in tied_st:
                L.stations.remove(st)
            for f in tied_fx:
                L.fx.remove(f)
            continue
        nx, ny = best
        dx, dy = nx - x, ny - y
        if dx or dy:
            notes.append(f"{name}: {p} ({x},{y}) -> ({nx},{ny})")
        for st in tied_st:
            st["x"] += dx
            st["y"] += dy
        for f in tied_fx:
            f["x"] += dx
            f["y"] += dy
        L._tied = getattr(L, "_tied", []) + tied_st
        placed.append((nx, ny, w, h))
        keep.append((p, nx, ny))
    L.back = keep
    return []


def resolve_wall(name, L, t, notes):
    errs = []
    fixed = []
    movable = []
    lamps = []
    for p, x, y in L.back:
        w, h = SZ[p]
        if p in LAMP_PARTS:
            lamps.append(x)
        elif y + h < WALL:                       # colgado en la pared
            movable.append((p, x, y))
        else:
            fixed.append((x, y, w, h))
    fixed += [(x, y, *SZ[p]) for p, x, y in L.front]
    fixed += [(f["x"], f["y"], *FX[f["anim"]]) for f in L.fx]
    placed = list(fixed)
    out_back = [it for it in L.back if it[0] not in LAMP_PARTS and SZ[it[0]][1] + it[2] >= WALL]

    walls = []                          # lo ya ubicado en la pared (ventana incluida)

    def find(x0, y, w, h, pad_floor=PAD, pad_wall=WALL_PAD, lo=WALL_X[0], hi=WALL_X[1], text=False):
        bx0, by0, bx1, by1 = BUTTONS
        for d in range(0, 400, 2):
            for nx in ((x0 - d, x0 + d) if d else (x0,)):
                if nx < lo or nx + w > hi:
                    continue
                r = (nx, y, w, h)
                if text and _overlap(r, (bx0, by0, bx1 - bx0, by1 - by0), 0):
                    continue
                if any(_overlap(r, o, pad_floor) for o in placed):
                    continue
                if any(_overlap(r, o, pad_wall) for o in walls):
                    continue
                return nx
        return None

    window_x = None
    if L.wall != "chapa":                 # 12.2: ventana desde el nivel 0 (el local no queda ciego)
        bx, by, bw, bh = rooms_art.window_box(0)
        pref = [330, 60, 196][zlib.crc32(name[4:-2].encode()) % 3]
        nx = find(pref + bx, by, bw, bh, pad_floor=WINDOW_PAD)
        if nx is None:
            notes.append(f"{name}: sin lugar para la ventana (se omite)")
        else:
            window_x = nx - bx
            walls.append((nx, by, bw, bh))
    for p, x, y in movable:
        w, h = SZ[p]
        nx = find(x, y, w, h, pad_floor=WALL_PAD, text=p in TEXT_PARTS)
        if nx is None:
            nx = find(x, y, w, h, text=p in TEXT_PARTS)
        if nx is None and p not in DECOR:
            for ny in (y - 6, y + 6, y - 12, y + 12):          # el rubro se prueba un poco más arriba/abajo
                if ny >= 8 and ny + h < WALL:
                    nx = find(x, ny, w, h, text=p in TEXT_PARTS)
                    if nx is not None:
                        y = ny
                        break
        if nx is None:
            if p in DECOR:
                notes.append(f"{name}: {p} no entra en la pared (se omite)")
            else:
                errs.append(f"{name}: {p} no entra en la pared sin superponerse")
            continue
        if nx != x:
            notes.append(f"{name}: {p} x {x} -> {nx}")
        walls.append((nx, y, w, h))
        out_back.append((p, nx, y))
    lpart = getattr(L, "lamp_part", "_lamp_hanging")
    lw, lh = SZ[lpart]
    lamp_cx = []
    # Lámparas repartidas parejo en el espacio libre del techo (no amontonadas
    # al lado de la ventana o del cartel): se elige la posición libre más cercana
    # a cada cuantil del espacio libre.
    n = len(lamps)
    for i in range(n):
        free = [x for x in range(WALL_X[0], WALL_X[1] - lw, 2)
                if not any(_overlap((x, 4, lw, lh), o, WALL_PAD) for o in placed)
                and not any(_overlap((x, 4, lw, lh), o, WALL_PAD) for o in walls)
                and all(abs(x + lw / 2 - c) >= 64 for c in lamp_cx)]
        if not free:
            notes.append(f"{name}: no entran más lámparas ({len(lamp_cx)} de {n})")
            break
        want = WALL_X[0] + 20 + (WALL_X[1] - WALL_X[0] - 40 - lw) * (i + 0.5) / n
        # lejos de las otras lámparas: el hueco libre más cercano al lugar parejo
        nx = min(free, key=lambda x: abs(x - want))
        walls.append((nx, 4, lw, lh))
        out_back.append((lpart, nx, 4))
        lamp_cx.append(nx + lw // 2)
    L.back = out_back
    L.window_x = window_x
    L.lamp_cx = lamp_cx
    return errs


def check_no_overlap(name, L):
    """Verificación final independiente: nada de la pared toca a nadie."""
    errs = []
    rects = []
    for p, x, y in L.back:
        w, h = SZ[p]
        rects.append((p, (x, y, w, h), "w" if (y + h < WALL or p in LAMP_PARTS) else False))
    for p, x, y in L.front:
        w, h = SZ[p]
        rects.append((p, (x, y, w, h), "c" if y + h < FRONT_BASE - 20 else False))   # arriba del mostrador: no se pisa
    for f in L.fx:
        rects.append((f["anim"], (f["x"], f["y"], *FX[f["anim"]]), False))
    if L.window_x is not None:
        rects.append(("ventana", rooms_art.window_box(L.window_x), "w"))
    for i, (pa, ra, wa) in enumerate(rects):
        for pb, rb, wb in rects[i + 1:]:
            # lo de arriba del mostrador apoya 3 px sobre la mesada (a propósito)
            if pa.startswith("_counter") or pb.startswith("_counter"):
                continue
            if wa == "w" and wb == "w" and _overlap(ra, rb, WALL_PAD - 1):
                errs.append(f"{name}: {pa} y {pb} sin aire en la pared")
            elif (wa or wb) and _overlap(ra, rb, 0):
                errs.append(f"{name}: {pa} se superpone con {pb}")
    return errs


def depth_sorted(L):
    """Lo de la pared primero; lo del piso de atrás hacia adelante."""
    def key(it):
        p, x, y = it
        w, h = SZ[p]
        return (0 if y + h < WALL else 1, y + h, x)
    return sorted(L.back, key=key)


def js_items(items):
    return ", ".join(f'stamp("{p}", {x}, {y})' for p, x, y in items)


def main():
    js = ['// GENERADO por gen_interiors.py — no editar a mano.', 'include("furniture.px.js")', 'include("furniture_v10.px.js")', 'include("rooms.px.js")', ""]
    meta = {"_doc": "Generado por tools/art/pxl/gen_interiors.py. Coordenadas en píxeles del lienzo 400x170 de cada interior.",
            "size": [W, H], "behind_y": BEHIND, "queue_y": QUEUE_Y, "businesses": {}}
    errors = []
    notes = []
    layout = {}
    for bid, fn in BUSINESSES.items():
        tiers = []
        for t in range(5):
            L = fn(t)
            if not L.outdoor and bid in RETAIL:
                add_wall_shelves(L, 1 if t < 2 else 2)
            name = f"int_{bid}_{t}"
            errors += place_floor(name, L, notes)
            errors += fix_depth(name, L)
            errors += resolve_wall(name, L, t, notes)
            errors += check_text_items(name, L)
            errors += check_no_overlap(name, L)
            # 12.1: PXL pinta sólo la habitación; la utilería la estampa compose_interiors.py.
            js.append(f'scene("{name}", {{ w: {W}, h: {H}, bg: "u", layers: true }},')
            js.append(f'  layer("back", room("{L.wall}", "{L.floor}", {str(L.outdoor).lower()}, {t})),')
            js.append('  layer("front", px(0, 0, ".")))')
            layout[name] = {"back": [list(i) for i in depth_sorted(L)], "front": [list(i) for i in L.front],
                            "room": {"wall": L.wall, "floor": L.floor, "tier": t, "lamps": L.lamp_cx,
                                     "window_x": L.window_x, "view": VIEW.get(bid, "ciudad"), "seed": zlib.crc32(bid.encode()) % 997 + t}}
            if not L.queue:
                L.queue.append([W // 2, QUEUE_Y])
            if not L.stations:
                L.station(W // 2, BEHIND, "counter")
            tiers.append({"stations": L.stations, "queue": L.queue, "fx": L.fx, "outdoor": L.outdoor,
                          "has_interior": t > NO_INTERIOR.get(bid, -1)})
        meta["businesses"][bid] = tiers
    open(os.path.join(HERE, "interiors.px.js"), "w", encoding="utf-8", newline="\n").write("\n".join(js) + "\n")
    with open(os.path.join(ROOT, "data", "interiors.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
    with open(os.path.join(HERE, "out", "layout.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump({"size": SZ, "wall": WALL, "scenes": layout}, f)
    if notes:
        print("Ajustes de la pared:\n  " + "\n  ".join(notes))
    if errors:
        sys.exit("Interiores con problemas:\n  " + "\n  ".join(errors))
    print("ok:", len(BUSINESSES) * 5, "interiores")


if __name__ == "__main__":
    main()
