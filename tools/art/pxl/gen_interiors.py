#!/usr/bin/env python3
"""Genera los interiores de los 12 negocios x 5 niveles.

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

def puesto(t):
    if t <= 2:
        L = Layout("vereda", "vereda", outdoor=True)
        L.put("_umbrella", 150, 112)
        L.counter("_stall_table", 154, 1)
        L.put("_price_board", 120, 140)
        if t >= 1:
            L.put("_cooler", 246, 140)
            L.put("_crate", 280, 146)
            L.put("_crate", 96, 146)
        if t >= 2:
            L.wall_item("_string_lights", 100, 20)
            L.on_counter("_register", 0)
            L.station(110, 138, "stand")
        return L
    L = Layout("azulejo", "damero")
    L.put("_shelf_wood", 40, WALL)
    L.put("_fridge_drinks", 96, WALL)
    L.counter("_counter_wood", 150, 1)
    L.on_counter("_register", 0)
    L.on_counter("_mate_set", 1)
    L.wall_item("_fileteado_sign", 164, 14)
    L.wall_item("_pennant", 250, 10)
    if t == 4:
        L.put("_shelf_wood", 300, WALL)
        L.counter("_counter_glass", 236, 1)
        L.wall_item("_clock", 140, 40)
        L.put("_plant", 360, 140)
        L.fx_at("fx_neon", 258, 40)
    ceiling_lamps(L, 2 + t - 3)
    return L


def kiosco(t):
    L = Layout("azulejo", "damero")
    L.put("_shelf_wood", 30, WALL)
    L.counter("_counter_glass", 150, 1)
    L.on_counter("_register", 0)
    L.wall_item("_poster", 100, 24)
    if t >= 1:
        L.put("_fridge_drinks", 86, WALL)
        L.put("_shelf_metal", 230, WALL)
    if t >= 2:
        L.wall_item("_clock", 132, 30)
        L.put("_shelf_wood", 290, WALL)
        L.on_counter("_mate_set", 1)
    if t >= 3:
        L.put("_freezer", 330, 150)
        L.wall_item("_pennant", 160, 8)
        L.wall_item("_jersey", 200, 30)
        L.counter("_counter_glass", 230, 1)
    if t >= 4:
        L.fx_at("fx_neon", 40, 4)
        L.fx_at("fx_tv", 280, 4)
        L.put("_plant", 10, 150)
        L.put("_cart", 360, 150)
    ceiling_lamps(L, min(4, 1 + t))
    return L


def comida(t):
    if t <= 2:
        L = Layout("vereda", "vereda", outdoor=True)
        L.put("_prep_table", 60, 120)
        L.counter("_grill", 160, 1)
        L.fx_at("fx_smoke", 180, 64)
        if t >= 1:
            L.put("_umbrella", 140, 96)
            L.put("_cafe_table", 280, 150)
            L.put("_chalkboard", 110, 150)
        if t >= 2:
            L.wall_item("_string_lights", 60, 18)
            L.put("_cafe_table", 330, 156)
            L.station(90, 134, "stand")
        return L
    L = Layout("ladrillo", "madera")
    L.put("_grill", 30, WALL)
    L.fx_at("fx_smoke", 50, 22)
    L.station(64, 134, "stand")
    L.put("_wine_rack", 110, WALL)
    L.counter("_counter_wood", 150, 1)
    L.on_counter("_register", 0)
    L.put("_dining_table", 240, 152)
    L.put("_dining_table", 300, 158)
    L.wall_item("_fileteado_sign", 150, 12)
    if t >= 4:
        L.put("_dining_table", 350, 146)
        L.put("_stove", 250, WALL)
        L.fx_at("fx_smoke", 270, 30)
        L.station(282, 128, "stand")
        L.wall_item("_jersey", 200, 40)
    ceiling_lamps(L, 3 + (t - 3))
    return L


def lavadero(t):
    L = Layout("chapa", "cemento")
    L.put("_wash_bay", 40, 140)
    L.fx_at("fx_foam", 78, 92)
    L.station(30, 140, "stand")
    if t >= 1:
        L.put("_vacuum", 150, 140)
        L.put("_drums", 360, 140)
    if t >= 2:
        L.put("_wash_bay", 180, 140)
        L.fx_at("fx_foam", 218, 92)
        L.station(170, 140, "stand", True)
    if t >= 3:
        L.counter("_counter_metal", 300, 1)
        L.put("_desk_pc", 296, WALL)
        L.wall_item("_poster", 300, 20)
    if t >= 4:
        L.wall_item("_fileteado_sign", 150, 6)
        L.put("_plant", 376, 150)
        L.wall_item("_clock", 260, 10)
    return L


def almacen(t):
    L = Layout("azulejo", "madera")
    L.put("_shelf_almacen", 30, WALL)
    L.counter("_counter_wood", 140, 1)
    L.on_counter("_scale", 0)
    L.wall_item("_salames", 150, 30)
    if t >= 1:
        L.put("_shelf_almacen", 92, WALL)
        L.put("_crate", 240, 152)
        L.put("_crate", 262, 152)
    if t >= 2:
        L.on_counter("_slicer", 1)
        L.wall_item("_clock", 210, 18)
        L.put("_shelf_almacen", 290, WALL)
    if t >= 3:
        L.put("_fridge_drinks", 30, WALL)
        L.wall_item("_fileteado_sign", 150, 8)
        L.on_counter("_mate_set", 1)
        L.counter("_counter_glass", 220, 1)
    if t >= 4:
        L.wall_item("_pennant", 240, 6)
        L.put("_plant", 6, 150)
    ceiling_lamps(L, min(4, 2 + t // 2))
    return L


def cafeteria(t):
    L = Layout("madera_pared", "damero")
    L.put("_counter_wood", 40, WALL + 6)
    L.put("_coffee_machine", 54, WALL - 22)
    L.fx_at("fx_steam", 60, 50)
    L.station(76, 120, "stand")
    L.counter("_pastry_case", 140, 1)
    L.on_counter("_register", 0)
    L.wall_item("_chalkboard", 140, 20)
    L.put("_cafe_table", 240, 154)
    if t >= 1:
        L.put("_cafe_table", 300, 158)
    if t >= 2:
        L.put("_cafe_table", 350, 150)
        L.wall_item("_clock", 250, 20)
    if t >= 3:
        L.put("_shelf_wood", 330, WALL)
        L.wall_item("_poster", 290, 22)
        L.put("_plant", 214, 150)
    if t >= 4:
        L.fx_at("fx_neon", 230, 10)
        L.counter("_counter_glass", 16, 1, queue=False)
    ceiling_lamps(L, min(4, 2 + t))
    return L


def restaurante(t):
    L = Layout("ladrillo", "madera")
    L.put("_stove", 30, WALL)
    L.fx_at("fx_smoke", 46, 24)
    L.station(60, 128, "stand")
    L.put("_prep_table", 100, WALL + 8)
    L.counter("_counter_wood", 170, 1)
    L.put("_dining_table", 260, 152)
    L.wall_item("_fileteado_sign", 170, 10)
    if t >= 1:
        L.put("_dining_table", 320, 158)
        L.put("_wine_rack", 360, WALL)
    if t >= 2:
        L.station(126, 128, "stand")
        L.wall_item("_clock", 250, 20)
    if t >= 3:
        L.put("_dining_table", 300, 132)
        L.wall_item("_jersey", 300, 24)
    if t >= 4:
        L.put("_stove", 230, WALL)
        L.fx_at("fx_smoke", 246, 24)
        L.station(258, 128, "stand")
        L.put("_plant", 6, 150)
    ceiling_lamps(L, min(4, 2 + t))
    return L


def supermercado(t):
    L = Layout("pintura_super", "ceramica")
    L.put("_gondola", 20, WALL)
    L.counter("_checkout", 140, 1)
    L.put("_cart", 100, 156)
    if t >= 1:
        L.put("_gondola", 96, WALL)
        L.put("_fridge_drinks", 300, WALL)
    if t >= 2:
        L.put("_freezer", 330, 148)
        L.put("_gondola", 214, WALL)
    if t >= 3:
        L.counter("_checkout", 230, 1)
        L.wall_item("_poster", 180, 10)
    if t >= 4:
        L.put("_fridge_drinks", 40, WALL)
        L.put("_cart", 370, 160)
        L.fx_at("fx_tv", 160, 12)
    ceiling_lamps(L, min(4, 2 + t))
    return L


def gimnasio(t):
    L = Layout("pintura_gym", "goma")
    L.wall_item("_mirror", 30, 22)
    L.put("_treadmill", 30, 140)
    L.station(54, 132, "stand")
    L.counter("_counter_metal", 160, 1)
    if t >= 1:
        L.put("_weight_rack", 240, WALL + 2)
        L.put("_water_cooler", 120, WALL)
    if t >= 2:
        L.put("_bench_press", 250, 150)
        L.station(280, 136, "stand")
        L.put("_punching_bag", 350, 120, top=40)
    if t >= 3:
        L.put("_treadmill", 90, 148)
        L.wall_item("_mirror", 250, 20)
        L.wall_item("_poster", 140, 22)
    if t >= 4:
        L.fx_at("fx_tv", 190, 8)
        L.put("_plant", 376, 150)
    ceiling_lamps(L, min(4, 2 + t))
    return L


def taller(t):
    L = Layout("chapa", "cemento")
    L.put("_car_lift", 30, 140)
    L.station(130, 140, "stand", True)
    L.wall_item("_tool_wall", 140, 30)
    L.counter("_counter_metal", 290, 1)
    if t >= 1:
        L.put("_tires", 220, 140)
        L.put("_drums", 254, WALL + 30)
    if t >= 2:
        L.put("_workbench", 140, WALL + 6)
        L.station(170, 128, "stand")
    if t >= 3:
        L.put("_car", 200, 158)
        L.wall_item("_poster", 290, 20)
        L.wall_item("_clock", 340, 20)
    if t >= 4:
        L.fx_at("fx_tv", 360, 50)
        L.wall_item("_fileteado_sign", 20, 4)
    return L


def mensajeria(t):
    L = Layout("pintura_celeste", "ceramica")
    L.put("_parcel_shelf", 20, WALL)
    L.counter("_counter_wood", 150, 1)
    L.on_counter("_scale", 0)
    L.put("_scooter", 300, 150)
    if t >= 1:
        L.put("_desk_pc", 90, WALL + 4)
        L.station(110, 126, "stand")
    if t >= 2:
        L.put("_parcel_shelf", 240, WALL)
        L.put("_filing", 312, WALL)
    if t >= 3:
        L.put("_conveyor", 30, 156)
        L.fx_at("fx_conveyor", 31, 128)
        L.put("_scooter", 296, 156)
    if t >= 4:
        L.wall_item("_clock", 200, 16)
        L.put("_water_cooler", 360, WALL)
        L.fx_at("fx_tv", 200, 40)
    ceiling_lamps(L, min(4, 2 + t))
    return L


def distribuidora(t):
    L = Layout("chapa", "cemento")
    L.put("_pallet_rack", 20, WALL + 10)
    L.put("_pallet_boxes", 120, 150)
    L.counter("_counter_metal", 300, 1)
    if t >= 1:
        L.put("_forklift", 160, 146)
        L.station(186, 128, "stand")
    if t >= 2:
        L.put("_dock_door", 262, WALL - 4)
        L.put("_pallet_rack", 176, WALL + 10)
    if t >= 3:
        L.put("_conveyor", 110, 156)
        L.fx_at("fx_conveyor", 111, 128)
        L.station(140, 136, "stand")
    if t >= 4:
        L.put("_machine", 100, WALL + 10)
        L.station(160, 124, "stand")
        L.wall_item("_poster", 230, 6)
    ceiling_lamps(L, min(4, 2 + t))
    return L


# Rubros donde tiene sentido una repisa con mercadería en la pared.
RETAIL = {"puesto", "kiosco", "almacen", "cafeteria", "supermercado", "restaurante"}

BUSINESSES = {
    "puesto": puesto, "kiosco": kiosco, "comida": comida, "lavadero": lavadero, "almacen": almacen, "cafeteria": cafeteria,
    "restaurante": restaurante, "supermercado": supermercado, "gimnasio": gimnasio, "taller": taller,
    "mensajeria": mensajeria, "distribuidora": distribuidora,
}


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
NO_INTERIOR = {"puesto": 2, "comida": 2, "lavadero": 2}


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
    js = ['// GENERADO por gen_interiors.py — no editar a mano.', 'include("furniture.px.js")', 'include("rooms.px.js")', ""]
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
