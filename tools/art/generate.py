#!/usr/bin/env python3
"""Genera TODO el arte pixel art del juego en assets/pixel_art/.

Uso:  python3 tools/art/generate.py
Además escribe una hoja de contacto (docs/art_preview.png) para revisar
el resultado de un vistazo.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "assets", "pixel_art")
DATA = os.path.join(ROOT, "data")

import backgrounds  # noqa: E402
import buildings2  # noqa: E402
import chars2  # noqa: E402
import coin_art  # noqa: E402
import icons32  # noqa: E402
import logo  # noqa: E402
import map_art  # noqa: E402
import fx_art  # noqa: E402
import map_avatars  # noqa: E402
import ui_art  # noqa: E402
from icons import ICONS  # noqa: E402
from px import Canvas, PAL  # noqa: E402


def gen_icons():
    d = os.path.join(OUT, "icons")
    os.makedirs(d, exist_ok=True)
    problems = []
    for name, art in ICONS.items():
        rows = art.strip("\n").split("\n")
        clean = []
        for r in rows:
            r = r.replace("о", "o").replace(" ", ".")
            if len(r) > 16:
                problems.append(f"{name}: fila de {len(r)} > 16")
            for ch in r:
                if ch != "." and ch not in PAL:
                    problems.append(f"{name}: color desconocido '{ch}'")
            clean.append(r[:16].ljust(16, "."))
        cv = Canvas(16, 16)
        top = (16 - len(clean)) // 2
        cv.stamp([r if all(c in PAL or c == "." for c in r) else "".join(c if (c in PAL or c == ".") else "." for c in r) for r in clean], 0, top)
        cv.save(os.path.join(d, f"{name}.png"))
    coin_art.icon16().save(os.path.join(d, "moneda.png"))  # moneda 2.1 (procedural)
    return problems


def contact_sheet():
    from PIL import Image
    biz = json.load(open(os.path.join(DATA, "businesses.json"), encoding="utf-8"))["businesses"]
    sheet = Image.new("RGBA", (5 * 200, len(biz) * 150 + 220), (43, 39, 70, 255))
    for j, b in enumerate(biz):
        for t in range(5):
            im = Image.open(os.path.join(OUT, "businesses", f"{b['id']}_{t}.png")).crop((0, 0, 192, 150))
            sheet.alpha_composite(im, (t * 200, j * 150))
    x = 0
    for name in sorted(ICONS):
        im = Image.open(os.path.join(OUT, "icons", f"{name}.png"))
        sheet.alpha_composite(im, (4 + (x % 50) * 20, len(biz) * 150 + 10 + (x // 50) * 20))
        x += 1
    for i in range(8):
        im = Image.open(os.path.join(OUT, "characters", f"customer_{i}.png"))
        sheet.alpha_composite(im.crop((0, 0, 160, 48)), (4 + (i % 4) * 170, len(biz) * 150 + 80 + (i // 4) * 50))
    for i, z in enumerate(["barrio", "centro", "costanera", "industrial"]):
        im = Image.open(os.path.join(OUT, "backgrounds", f"street_{z}.png")).crop((0, 0, 240, 200)).resize((120, 100))
        sheet.alpha_composite(im, (700 + (i % 2) * 150, len(biz) * 150 + 10 + (i // 2) * 105))
    sheet = sheet.resize((sheet.width, sheet.height), Image.NEAREST)
    os.makedirs(os.path.join(ROOT, "docs"), exist_ok=True)
    sheet.save(os.path.join(ROOT, "docs", "art_preview.png"))


def main():
    os.makedirs(OUT, exist_ok=True)
    problems = gen_icons()
    ui_art.generate(OUT)
    chars2.generate(OUT)          # personajes 2.0 (32x48)
    icons32.generate(OUT)         # íconos 2.0 (32x32)
    fx_art.generate(OUT)
    fixed = buildings2.generate(OUT, DATA)   # edificios 2.0 (192x150, 2 cuadros)
    print(f"Píxeles huérfanos corregidos en edificios: {fixed}")
    logo.main()
    world = json.load(open(os.path.join(DATA, "world.json"), encoding="utf-8"))
    # 10.0: fondos provisorios por región (las calles de la 0.7) hasta el arte de F3.
    backgrounds.generate(OUT, sorted({z.get("street", z["id"]) for z in world["zones"]}))
    map_avatars.generate(OUT, DATA)
    map_art.generate(OUT, DATA)     # mapas de la Argentina (10.0)
    contact_sheet()
    for p in problems:
        print("AVISO:", p)
    n = sum(len(f) for _, _, f in os.walk(OUT))
    print(f"Arte generado: {n} archivos en {OUT}")


if __name__ == "__main__":
    main()
