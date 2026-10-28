#!/usr/bin/env python3
"""Genera los interiores de los 24 negocios provinciales (10.0) x 5 niveles.

Escribe:
  tools/art/pxl/interiors.px.js  -> escenas PXL (capas "back" y "front")
  data/interiors.json            -> puestos de trabajo, fila de clientes y animaciones

Lienzo 400x170 (1 m = 24 px). Pared 0..110, piso 110..170.
Los mostradores van en la capa "front" (tapan las piernas de quien atiende).
Empleados detrás del mostrador: pies en y=134. Clientes: pies en y~164.
"""
import json
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
    "_scale": (20, 16), "_slicer": (24, 18), "_mate_set": (18, 14), "_shelf_wood": (52, 72), "_shelf_metal": (52, 74),
    "_shelf_almacen": (58, 76), "_gondola": (72, 66), "_fridge_drinks": (34, 72), "_freezer": (48, 32), "_grill": (66, 42),
    "_stove": (62, 48), "_prep_table": (58, 38), "_coffee_machine": (42, 36), "_pastry_case": (62, 36), "_dining_table": (42, 32),
    "_cafe_table": (36, 30), "_chalkboard": (36, 28), "_wine_rack": (32, 58), "_car": (66, 32), "_car_lift": (86, 66),
    "_tool_wall": (62, 42), "_tires": (26, 38), "_drums": (34, 30), "_workbench": (62, 36), "_wash_bay": (98, 62),
    "_vacuum": (18, 36), "_treadmill": (52, 42), "_weight_rack": (48, 48), "_bench_press": (56, 36), "_punching_bag": (20, 52),
    "_mirror": (72, 48), "_desk_pc": (54, 40), "_filing": (24, 48), "_water_cooler": (18, 46), "_parcel_shelf": (62, 68),
    "_pallet_rack": (82, 82), "_forklift": (52, 44), "_dock_door": (72, 74), "_pallet_boxes": (36, 32), "_scooter": (42, 34),
    "_clock": (18, 18), "_pennant": (40, 14), "_jersey": (24, 24), "_fileteado_sign": (72, 20), "_plant": (20, 30),
    "_poster": (22, 28), "_lamp_hanging": (16, 18), "_crate": (22, 16), "_salames": (30, 22), "_checkout": (68, 44),
    "_cart": (30, 30), "_conveyor": (112, 38), "_machine": (52, 58), "_stall_table": (82, 36), "_umbrella": (90, 70),
    "_cooler": (32, 24), "_price_board": (20, 32), "_string_lights": (200, 16), "_wall_shelf": (70, 22),
    # 10.0 (furniture_v10.px.js)
    "_bales": (42, 28), "_sacks": (38, 28), "_barrels_wood": (46, 32), "_steel_tank": (30, 70), "_olive_press": (48, 50),
    "_citrus_crates": (42, 30), "_drying_rack": (62, 42), "_oven": (54, 58), "_meat_hooks": (44, 36), "_cheese_shelf": (46, 52),
    "_electronics_bench": (72, 42), "_potato_bins": (48, 28), "_banana_hooks": (42, 42), "_apple_bins": (48, 30),
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
        cx, cy, w = self.counters[idx]
        pw, ph = SZ[part]
        x = cx + w - pw - 4 - slot * 24
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
        (2, "_shelf_wood", 140, F), (2, "_pennant", 30, "wall:12"), (3, "_crate", 330, F), (3, "_crate", 352, F),
        (3, "_poster", 300, "wall:24"), (4, "_potato_bins", 320, N), (4, "_plant", 370, F)]),
    "almazara": ("cal", "ceramica", "_counter_glass", 270, "_register", [
        (0, "_olive_press", 30, M), (0, "_crate", 100, F), (1, "_steel_tank", 100, F), (1, "_shelf_wood", 140, F),
        ("station", 1, 70, 132), (2, "_steel_tank", 136, F), (3, "_machine", 180, M), ("station", 3, 210, 126),
        (3, "_clock", 300, "wall:18"), (4, "_steel_tank", 350, F), (4, "_plant", 20, F)]),
    "olivar": ("cal", "cemento", "_counter_wood", 260, "_scale", [
        (0, "_crate", 30, F), (0, "_crate", 54, F), (0, "_sacks", 90, F), (1, "_olive_press", 120, M),
        (2, "_shelf_wood", 30, F), (2, "_wine_rack", 190, F), (3, "_steel_tank", 340, F), (3, "_pennant", 140, "wall:12"),
        (4, "_conveyor", 30, N), ("fx", 4, "fx_conveyor", 31, 128)]),
    "bodega_torrontes": ("cal", "madera", "_counter_wood", 240, "_register", [
        (0, "_barrels_wood", 30, F), (0, "_wine_rack", 100, F), (1, "_barrels_wood", 140, M), (1, "_cafe_table", 330, N),
        (2, "_steel_tank", 180, F), (2, "_lamp_hanging", 300, "wall:4"), (3, "_wine_rack", 360, F), (3, "_barrels_wood", 30, N),
        (4, "_chalkboard", 290, "wall:30"), (4, "_cafe_table", 150, N)]),
    "citricola": ("cal", "cemento", "_counter_metal", 290, "_scale", [
        (0, "_citrus_crates", 30, F), (0, "_citrus_crates", 80, M), (1, "_citrus_crates", 130, F), (1, "_prep_table", 180, M),
        ("station", 1, 205, 130), (2, "_conveyor", 40, N), ("fx", 2, "fx_conveyor", 41, 128), (3, "_steel_tank", 220, F),
        (3, "_machine", 150, F), (4, "_forklift", 330, N), (4, "_citrus_crates", 250, N)]),
    "bananal": ("madera_rustica", "cemento", "_counter_wood", 250, "_scale", [
        (0, "_banana_hooks", 30, "wall:30"), (0, "_crate", 40, F), (1, "_banana_hooks", 90, "wall:30"), (1, "_prep_table", 120, M),
        ("station", 1, 146, 130), (2, "_citrus_crates", 30, N), (3, "_banana_hooks", 160, "wall:30"), (3, "_cooler", 330, F),
        (4, "_conveyor", 60, N), ("fx", 4, "fx_conveyor", 61, 128)]),
    "desmotadora": ("chapa", "cemento", "_counter_metal", 300, "_register", [
        (0, "_bales", 30, F), (0, "_machine", 90, F), ("station", 0, 120, 128), (1, "_bales", 150, M), (1, "_conveyor", 20, N),
        ("fx", 1, "fx_conveyor", 21, 128), (2, "_machine", 200, F), ("station", 2, 230, 128), (3, "_pallet_rack", 210, N),
        (4, "_forklift", 140, N), (4, "_clock", 300, "wall:18")]),
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
        (0, "_drying_rack", 30, F), (1, "_drying_rack", 100, F), (1, "_crate", 30, N), (2, "_wine_rack", 170, F),
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
        (0, "_bales", 30, F), (0, "_machine", 90, F), ("station", 0, 120, 128), (1, "_bales", 150, M), (2, "_conveyor", 20, N),
        ("fx", 2, "fx_conveyor", 21, 128), (2, "_machine", 200, F), ("station", 2, 230, 128), (3, "_pallet_rack", 200, N),
        (4, "_forklift", 130, N)]),
    "chacra_peras": ("madera_rustica", "cemento", "_counter_wood", 260, "_scale", [
        (0, "_apple_bins", 30, M), (0, "_crate", 100, F), (1, "_apple_bins", 90, F), (1, "_prep_table", 150, M),
        ("station", 1, 176, 130), (2, "_citrus_crates", 30, F), (3, "_cooler", 340, F), (3, "_pennant", 140, "wall:10"),
        (4, "_conveyor", 40, N), ("fx", 4, "fx_conveyor", 41, 128)]),
    "manzanas": ("chapa", "cemento", "_counter_metal", 300, "_scale", [
        (0, "_apple_bins", 30, F), (0, "_apple_bins", 90, M), (1, "_conveyor", 20, N), ("fx", 1, "fx_conveyor", 21, 128),
        (2, "_machine", 150, F), ("station", 2, 180, 128), (3, "_pallet_rack", 210, N), (4, "_forklift", 140, N),
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
        (4, "_machine", 210, F), (4, "_fileteado_sign", 30, "wall:6")]),
    "usina_lactea": ("azulejo", "ceramica", "_counter_glass", 270, "_register", [
        (0, "_cheese_shelf", 30, F), (0, "_freezer", 90, M), (1, "_steel_tank", 100, F), (1, "_steel_tank", 134, F),
        (2, "_machine", 170, F), ("station", 2, 200, 126), (3, "_conveyor", 20, N), ("fx", 3, "fx_conveyor", 21, 128),
        (4, "_steel_tank", 350, F), (4, "_clock", 220, "wall:18")]),
    "molino_harinero": ("cal", "cemento", "_counter_metal", 300, "_scale", [
        (0, "_sacks", 30, F), (0, "_sacks", 70, M), (1, "_machine", 110, F), ("station", 1, 140, 128), (2, "_sacks", 170, M),
        (2, "_conveyor", 20, N), ("fx", 2, "fx_conveyor", 21, 128), (3, "_pallet_rack", 200, N), (4, "_forklift", 300, N)]),
    "panaderia": ("madera_pared", "damero", "_counter_glass", 230, "_register", [
        (0, "_oven", 30, F), (0, "_pastry_case", 100, M), (1, "_coffee_machine", 236, "on1"), (1, "_cafe_table", 340, N),
        (2, "_shelf_wood", 150, F), (2, "_chalkboard", 290, "wall:30"), (3, "_cafe_table", 30, N), (3, "_fileteado_sign", 160, "wall:6"),
        (4, "_lamp_hanging", 300, "wall:4"), (4, "_plant", 370, F), ("fx", 4, "fx_steam", 60, 20)]),
}


def province_layout(bid, t):
    wall_kind, floor, counter, cx, on_top, items = PROVINCES[bid]
    L = Layout(wall_kind, floor)
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
        if base == "on":
            L.on_counter(part, 1)
        elif base == "on1":
            L.on_counter(part, 1)
        elif isinstance(base, str) and base.startswith("wall:"):
            L.wall_item(part, x, int(base[5:]))
        else:
            L.put(part, x, base)
    ceiling_lamps(L, min(4, 2 + t))
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


def js_items(items):
    return ", ".join(f'stamp("{p}", {x}, {y})' for p, x, y in items)


def main():
    js = ['// GENERADO por gen_interiors.py — no editar a mano.', 'include("furniture.px.js")', 'include("furniture_v10.px.js")', 'include("rooms.px.js")', ""]
    meta = {"_doc": "Generado por tools/art/pxl/gen_interiors.py. Coordenadas en píxeles del lienzo 400x170 de cada interior.",
            "size": [W, H], "behind_y": BEHIND, "queue_y": QUEUE_Y, "businesses": {}}
    errors = []
    for bid, fn in BUSINESSES.items():
        tiers = []
        for t in range(5):
            L = fn(t)
            if not L.outdoor and bid in RETAIL:
                add_wall_shelves(L, 1 if t < 2 else 2)
            name = f"int_{bid}_{t}"
            errors += check_text_items(name, L)
            js.append(f'scene("{name}", {{ w: {W}, h: {H}, bg: "u", layers: true }},')
            js.append(f'  layer("back", room("{L.wall}", "{L.floor}", {str(L.outdoor).lower()}, {t}), {js_items(L.back) or "px(0, 0, \".\")"}),')
            js.append(f'  layer("front", {js_items(L.front) or "px(0, 0, \".\")"}))')
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
    if errors:
        sys.exit("Carteles fuera de lugar:\n  " + "\n  ".join(errors))
    print("ok:", len(BUSINESSES) * 5, "interiores")


if __name__ == "__main__":
    main()
