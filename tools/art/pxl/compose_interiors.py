#!/usr/bin/env python3
"""12.1: arma los interiores finales estampando la utilería "símil 3D".

PXL pinta sólo la habitación de cada nivel (out/scenes/int_<negocio>_<n>/back.png);
gen_interiors.py deja en out/layout.json qué piezas van y dónde (ya ordenadas por
profundidad). Acá se dibuja cada pieza de tools/art/props_art.py con su sombra de
contacto en el piso (tramada, corrida a la derecha porque la luz viene de arriba a
la izquierda) y se escriben:
  assets/pixel_art/interiors/<negocio>_<n>_back.png   (habitación + utilería)
  assets/pixel_art/interiors/<negocio>_<n>_front.png  (mostradores y lo de arriba)
  assets/escenarios/interiors/...  lo mismo con la habitación re-estilizada a la paleta 11
                                   (restyle11 + calm_walls); es lo que carga el juego.

Uso: python tools/art/pxl/compose_interiors.py  (lo llama build.py)
"""
import json
import os
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.dirname(HERE))
import props_art  # noqa: E402
import restyle11  # noqa: E402

OUT_DIR = os.path.join(ROOT, "assets", "pixel_art", "interiors")
OUT11 = os.path.join(ROOT, "assets", "escenarios", "interiors")
SHADOW = (40, 18, 10)
BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5]


def contact_shadow(img, x, base, w, strength=0.42):
    """Elipse aplanada bajo la pieza, con borde tramado (look pixel, sin degradé)."""
    px = img.load()
    W, H = img.size
    cx = x + w / 2 + 2
    rx = w / 2 + 1
    ry = 3.2
    for yy in range(int(base - ry), int(base + ry) + 1):
        for xx in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if not (0 <= xx < W and 0 <= yy < H):
                continue
            d = ((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - base) / ry) ** 2
            if d > 1:
                continue
            k = strength * (1.0 - d * 0.55)
            if d > 0.6 and (BAYER[(yy % 4) * 4 + xx % 4] + 0.5) / 16 > (1 - d) * 2.5:
                continue
            r, g, b, a = px[xx, yy]
            if a == 0:
                continue
            px[xx, yy] = (int(r + (SHADOW[0] - r) * k), int(g + (SHADOW[1] - g) * k), int(b + (SHADOW[2] - b) * k), a)


def main():
    lay = json.load(open(os.path.join(HERE, "out", "layout.json"), encoding="utf-8"))
    size = lay["size"]
    wall = lay["wall"]
    cache = {}

    def piece(name):
        if name not in cache:
            cache[name] = props_art.render(name, size[name])
        return cache[name]

    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(OUT11, exist_ok=True)
    n = 0
    for scene, items in lay["scenes"].items():
        room = Image.open(os.path.join(HERE, "out", "scenes", scene, "back.png")).convert("RGBA")
        for warm in (False, True):
            if warm:
                room = restyle11.calm_walls(restyle11.restyle(room, selective=False)).convert("RGBA")
            _compose(scene, items, room.copy(), size, wall, piece, OUT11 if warm else OUT_DIR)
        n += 1
    print("interiores compuestos:", n)


def _compose(scene, items, back, size, wall, piece, out_dir):
    """Estampa sombras y utilería sobre la habitación y guarda las dos capas."""
    front = Image.new("RGBA", back.size, (0, 0, 0, 0))
    # sombras primero (todas en el piso), después las piezas de atrás hacia adelante
    for name, x, y in items["back"]:
        w, h = size[name]
        if y + h >= wall:
            contact_shadow(back, x, y + h - 1, w)
    for name, x, y in items["front"]:
        w, h = size[name]
        if y + h >= wall + 20:                     # mostradores (no lo que va arriba)
            contact_shadow(back, x, y + h - 1, w, 0.5)
    for name, x, y in items["back"]:
        back.alpha_composite(piece(name), (int(x), int(y)))
    for name, x, y in items["front"]:
        front.alpha_composite(piece(name), (int(x), int(y)))
    base = scene[4:]
    back.save(os.path.join(out_dir, base + "_back.png"))
    front.save(os.path.join(out_dir, base + "_front.png"))


if __name__ == "__main__":
    main()
