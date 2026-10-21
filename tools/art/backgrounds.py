"""Fondos de calle por zona (480x200) para la vista del negocio.

Capas: cielo con bandas tramadas, nubes, horizonte lejano propio de cada
zona, fila de edificios del medio, vereda de baldosas, cordón y calle.
Medidas que usa el juego (scripts/ui/components/business_scene.gd):
  SIDEWALK_Y = 150 (comienza la vereda), BUILDING_BASE_Y = 163,
  WALK_Y = 172 (pies de los peatones), STREET_Y = 178.
"""
import os
import random
from px import Canvas, RAMPS

BW, BH = 480, 200
SIDEWALK_Y, CURB_Y, STREET_Y = 150, 175, 178

SKIES = {
    "barrio": ["b", "b", "c", "c"],
    "centro": ["b", "c", "c", "C"],
    "universidad": ["b", "b", "c", "c"],
    "costanera": ["h", "b", "b", "c"],
    "industrial": ["L", "e", "t", "q"],
    "puerto": ["b", "c", "C", "A"],
    "financiero": ["L", "y", "q", "p"],
}


def sky(cv, zone):
    bands = SKIES[zone]
    band_h = SIDEWALK_Y // len(bands)
    for i, c in enumerate(bands):
        y0 = i * band_h
        cv.rect(0, y0, BW, band_h + 2, c)
        if i + 1 < len(bands):
            cv.dither(0, y0 + band_h - 2, BW, 3, c, bands[i + 1], i)


def cloud(cv, x, y, s):
    for dx, dy, r in ((0, 0, 4 + s), (6 + s, -3, 6 + s), (14 + 2 * s, 0, 5 + s), (8 + s, 2, 5 + s)):
        cv.ellipse(x + dx, y + dy, r + 2, r // 2 + 2, "w")
    cv.hline(x - 4, y + s // 2 + 3, 24 + 3 * s, "l")


def far_skyline(cv, zone, rnd):
    base = 120
    col = {"barrio": "l", "centro": "l", "universidad": "l", "costanera": "b", "industrial": "E", "puerto": "l", "financiero": "p"}[zone]
    if zone == "costanera" or zone == "puerto":
        cv.rect(0, base - 6, BW, SIDEWALK_Y - base + 6, "C")
        for x in range(0, BW, 7):
            cv.hline(x + rnd.randint(0, 3), base - 2 + rnd.randint(0, 20), 3, "b")
        if zone == "puerto":
            for cx in (60, 200, 380):
                cv.vline(cx, base - 70, 70, "d")
                cv.hline(cx - 30, base - 70, 50, "d")
                cv.vline(cx - 26, base - 70, 20, "g")
                cv.rect(cx - 30, base - 52, 6, 4, "y")
        else:
            for sx in (90, 300):
                cv.rect(sx, base - 12, 26, 6, "w")
                cv.vline(sx + 12, base - 30, 18, "d")
                for i in range(12):
                    cv.hline(sx + 13, base - 29 + i, 12 - i, "h")
        return
    x = 0
    while x < BW:
        w = rnd.randint(14, 34)
        h = {"centro": rnd.randint(40, 90), "financiero": rnd.randint(50, 100), "industrial": rnd.randint(18, 40)}.get(zone, rnd.randint(16, 40))
        cv.rect(x, base - h, w, h + 30, col)
        if zone in ("centro", "financiero"):
            for wy in range(base - h + 4, base, 6):
                for wx in range(x + 3, x + w - 2, 5):
                    cv.put(wx, wy, "g" if zone == "centro" else "q")
        if zone == "industrial" and rnd.random() < 0.4:
            cv.rect(x + w // 2, base - h - 26, 5, 26, "M")
            cv.ellipse(x + w // 2 + 4, base - h - 32, 5, 3, "l")
            cv.ellipse(x + w // 2 + 10, base - h - 38, 6, 4, "w")
        if zone == "universidad" and rnd.random() < 0.15:
            cv.rect(x + w // 2 - 3, base - h - 18, 7, 18, col)
            cv.ellipse(x + w // 2, base - h - 12, 2, 2, "w")
        x += w + rnd.randint(-4, 3)


def mid_row(cv, zone, rnd):
    """Fila de edificios del medio (frentes porteños de colores)."""
    palette = {
        "barrio": ["crema", "celeste", "amarillo", "verde", "rojo"],
        "centro": ["gris", "crema", "blanco", "celeste"],
        "universidad": ["rojo", "crema", "marron"],
        "costanera": ["blanco", "celeste", "amarillo"],
        "industrial": ["gris", "marron", "naranja"],
        "puerto": ["rojo", "azul", "amarillo", "verde"],
        "financiero": ["celeste", "azul", "gris"],
    }[zone]
    x = -5
    while x < BW:
        w = rnd.randint(30, 52)
        h = rnd.randint(36, 60) if zone not in ("centro", "financiero") else rnd.randint(54, 90)
        rname = palette[rnd.randrange(len(palette))]
        l, b, d = RAMPS[rname]
        top = SIDEWALK_Y - h
        if zone == "puerto":
            # contenedores apilados
            for row in range(3):
                for k in range(2):
                    cl = RAMPS[palette[(row + k + x) % len(palette)]]
                    cv.rect(x + k * (w // 2), SIDEWALK_Y - 14 * (row + 1), w // 2 - 1, 13, cl[1])
                    for vx in range(x + k * (w // 2) + 2, x + (k + 1) * (w // 2) - 2, 3):
                        cv.vline(vx, SIDEWALK_Y - 14 * (row + 1) + 2, 9, cl[2])
                    cv.frame(x + k * (w // 2), SIDEWALK_Y - 14 * (row + 1), w // 2 - 1, 13, "o")
            x += w + 6
            continue
        cv.rect(x, top, w, h, b)
        cv.hline(x, top, w, l)
        cv.vline(x + w - 1, top, h, d)
        cv.frame(x, top, w, h, "o")
        cv.rect(x - 1, top - 3, w + 2, 3, l)
        cv.frame(x - 1, top - 3, w + 2, 3, "o")
        for wy in range(top + 6, SIDEWALK_Y - 14, 16):
            for wx in range(x + 5, x + w - 10, 13):
                cv.rect(wx, wy, 8, 11, "c" if zone != "financiero" else "b")
                cv.hline(wx, wy, 8, "b")
                cv.frame(wx, wy, 8, 11, "o")
                if zone in ("barrio", "universidad") and rnd.random() < 0.5:
                    cv.hline(wx - 1, wy + 11, 10, "o")
                    for k in range(wx - 1, wx + 9, 2):
                        cv.put(k, wy + 10, "o")
        if zone == "barrio" and rnd.random() < 0.5:
            # techo de tejas
            for i in range(5):
                cv.hline(x + i * 2, top - 3 - i, w - i * 4, "R" if i % 2 else "r")
        x += w + rnd.randint(0, 4)


def trees(cv, zone, rnd):
    if zone in ("industrial", "puerto", "financiero"):
        return
    for x in range(20, BW, rnd.randint(90, 130)):
        x += rnd.randint(-10, 10)
        cv.rect(x, SIDEWALK_Y - 24, 4, 34, "m")
        cv.vline(x + 3, SIDEWALK_Y - 24, 34, "k")
        if zone == "costanera":
            for dx in (-12, -6, 0, 6, 12):
                cv.hline(x + dx - 2, SIDEWALK_Y - 28 + abs(dx) // 3, 8, "n")
            cv.ellipse(x + 2, SIDEWALK_Y - 28, 3, 2, "G")
        else:
            cv.ellipse(x + 2, SIDEWALK_Y - 34, 16, 12, "n")
            cv.ellipse(x - 4, SIDEWALK_Y - 38, 7, 5, "N")
            cv.ellipse(x + 8, SIDEWALK_Y - 28, 8, 5, "G")
            cv.outline_color_region(x - 16, SIDEWALK_Y - 48, 38, 30, (76, 175, 92), "o")


def sidewalk(cv, zone):
    tile = {"barrio": ("E", "e"), "centro": ("l", "g"), "universidad": ("t", "M"), "costanera": ("e", "E"),
            "industrial": ("g", "d"), "puerto": ("g", "d"), "financiero": ("w", "l")}[zone]
    cv.rect(0, SIDEWALK_Y, BW, CURB_Y - SIDEWALK_Y, tile[0])
    for y in range(SIDEWALK_Y, CURB_Y, 6):
        cv.hline(0, y, BW, tile[1])
        for x in range((y // 6) % 2 * 6, BW, 12):
            cv.vline(x, y, 6, tile[1])
            # baldosa vainilla porteña: puntitos
            cv.put(x + 3, y + 2, tile[1])
            cv.put(x + 8, y + 4, tile[1])
    cv.hline(0, SIDEWALK_Y, BW, "o")
    cv.rect(0, CURB_Y, BW, 3, "l")
    cv.hline(0, CURB_Y + 2, BW, "g")
    cv.hline(0, CURB_Y, BW, "w")
    cv.rect(0, STREET_Y, BW, BH - STREET_Y, "x")
    cv.dither(0, STREET_Y, BW, 2, "x", "d")
    for x in range(10, BW, 40):
        cv.rect(x, STREET_Y + 12, 18, 2, "y" if zone != "barrio" else "w")


def lamp(cv, x):
    cv.vline(x, SIDEWALK_Y - 46, 52, "u")
    cv.hline(x, SIDEWALK_Y - 46, 7, "u")
    cv.rect(x + 5, SIDEWALK_Y - 45, 4, 3, "L")
    cv.frame(x + 4, SIDEWALK_Y - 46, 6, 4, "o")
    cv.rect(x - 1, SIDEWALK_Y + 4, 3, 2, "u")


def make(zone):
    rnd = random.Random(zone)
    cv = Canvas(BW, BH)
    sky(cv, zone)
    for i in range(4):
        cloud(cv, rnd.randint(0, BW - 40), rnd.randint(10, 60), rnd.randint(0, 3))
    far_skyline(cv, zone, rnd)
    mid_row(cv, zone, rnd)
    trees(cv, zone, rnd)
    sidewalk(cv, zone)
    for x in (70, 410):
        lamp(cv, x)
    return cv


def generate(out, zones):
    d = os.path.join(out, "backgrounds")
    os.makedirs(d, exist_ok=True)
    for z in zones:
        make(z).save(f"{d}/street_{z}.png")
