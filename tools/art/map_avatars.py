"""Ícono de la app (y el mapa y los avatares de la versión 0.5, ya reemplazados por PXL)."""
import json
import os
import random
from px import Canvas, RAMPS
from icons import ICONS

MW, MH = 360, 540


def mini_house(cv, x, y, w, h, wall, roof):
    cv.rect(x, y, w, h, wall)
    cv.hline(x, y, w, roof)
    cv.hline(x, y + 1, w, roof)
    cv.frame(x - 1, y - 1, w + 2, h + 2, "o")
    if w >= 5 and h >= 4:
        cv.put(x + 1, y + 3, "c")
        cv.put(x + w - 2, y + 3, "c")


def zone_fill(cv, z, rnd):
    m = z["map"]
    x, y, w, h = m["x"], m["y"], m["w"], m["h"]
    zid = z["id"]
    ground = {"barrio": ("N", "n"), "centro": ("l", "g"), "universidad": ("N", "n"), "costanera": ("e", "t"),
              "industrial": ("t", "M"), "puerto": ("g", "d"), "financiero": ("l", "w")}[zid]
    cv.dither(x, y, w, h, ground[0], ground[1], 0)
    cv.rect(x + 2, y + 2, w - 4, h - 4, ground[0])
    if zid == "barrio":
        for yy in range(y + 8, y + h - 8, 12):
            for xx in range(x + 6, x + w - 10, 11):
                mini_house(cv, xx + rnd.randint(0, 2), yy, 7, 6, "e", "r")
    elif zid == "centro":
        for yy in range(y + 8, y + h - 14, 22):
            for xx in range(x + 6, x + w - 12, 14):
                hh = rnd.randint(10, 18)
                mini_house(cv, xx, yy + 18 - hh, 9, hh, rnd.choice(["c", "l", "b", "e"]), "C")
    elif zid == "universidad":
        mini_house(cv, x + 14, y + 16, 40, 18, "r", "R")
        mini_house(cv, x + 70, y + 20, 40, 14, "e", "R")
        cv.rect(x + 30, y + 6, 6, 10, "r")
        cv.frame(x + 29, y + 5, 8, 12, "o")
        for xx in range(x + 10, x + w - 10, 16):
            cv.ellipse(xx, y + h - 22, 5, 4, "G")
        cv.rect(x + 10, y + h - 14, w - 20, 6, "y")
    elif zid == "costanera":
        for yy in range(y + 10, y + h - 10, 18):
            cv.ellipse(x + 20, yy, 4, 3, "n")
            mini_house(cv, x + 34, yy - 3, 12, 7, "w", "c")
            cv.ellipse(x + 62, yy + 6, 4, 3, "n")
    elif zid == "industrial":
        for xx in range(x + 8, x + w - 30, 34):
            mini_house(cv, xx, y + 14, 26, 14, "l", "d")
            cv.rect(xx + 20, y + 4, 3, 10, "M")
            cv.ellipse(xx + 24, y + 2, 3, 2, "w")
            mini_house(cv, xx + 4, y + 48, 22, 12, "g", "Q")
    elif zid == "puerto":
        cols = ["r", "y", "c", "n", "q"]
        for yy in range(y + 10, y + h - 20, 9):
            for xx in range(x + 8, x + w - 40, 12):
                cv.rect(xx, yy, 10, 6, cols[(xx + yy) % 5])
                cv.frame(xx - 1, yy - 1, 12, 8, "o")
        for cx in (x + w - 30, x + w - 14):
            cv.vline(cx, y + 6, 40, "o")
            cv.hline(cx - 10, y + 6, 16, "o")
    elif zid == "financiero":
        for xx in range(x + 8, x + w - 12, 16):
            hh = rnd.randint(40, 80)
            cv.rect(xx, y + h - 10 - hh, 11, hh, "b")
            for wy in range(y + h - 8 - hh, y + h - 12, 4):
                cv.hline(xx + 1, wy, 9, "c")
            cv.frame(xx - 1, y + h - 11 - hh, 13, hh + 2, "o")


def make_map(zones):
    rnd = random.Random(7)
    cv = Canvas(MW, MH)
    cv.dither(0, 0, MW, MH, "n", "N", 0)
    # río al este y bahía del puerto
    for y in range(MH):
        left = 334 + int(4 * ((y // 20) % 2)) - (0 if y < 380 else min(14, (y - 380) // 6))
        cv.rect(left, y, MW - left, 1, "C")
        cv.put(left, y, "b")
    for y in range(0, MH, 9):
        cv.hline(345 + (y * 7) % 10, y, 4, "b")
    # avenidas
    for x in (20, 166, 196, 248):
        cv.rect(x, 0, 4 if x in (20,) else 5, MH, "d")
    for y in (150, 268, 380, 424):
        cv.rect(0, y, 334, 5, "d")
    for y in (150, 268, 380, 424):
        for x in range(0, 334, 8):
            cv.put(x, y + 2, "y")
    # plaza central
    cv.ellipse(182, 400, 10, 8, "G")
    cv.put(182, 400, "w")
    for z in zones:
        zone_fill(cv, z, rnd)
    return cv


# ------------------------------------------------------------------ avatares

def face(cv, skin=("s", "S"), hair="k", style="short", mustache=False):
    s, sd = skin
    cv.ellipse(12, 13, 6, 7, s)
    cv.vline(17, 9, 9, sd)
    cv.put(9, 12, "o")
    cv.put(14, 12, "o")
    cv.hline(10, 16, 4, sd)
    if style == "short":
        cv.ellipse(12, 7, 7, 3, hair)
        cv.vline(5, 7, 4, hair)
    elif style == "curly":
        for dx, dy in ((-6, -3), (-3, -6), (1, -7), (5, -5), (7, -1), (-7, 1)):
            cv.ellipse(12 + dx, 10 + dy, 3, 3, hair)
    if mustache:
        cv.hline(9, 15, 6, "k")


def avatar(aid):
    bg = {"emprendedor": "c", "vecina": "p", "perro": "N", "gorra": "y", "mate": "n", "gato": "v",
          "alfajor": "t", "kiosquero": "q", "galera": "l", "corona": "y"}[aid]
    cv = Canvas(24, 24)
    cv.ellipse(11, 11, 11, 11, bg)
    if aid == "emprendedor":
        cv.rect(5, 19, 14, 5, "C")
        face(cv)
    elif aid == "vecina":
        cv.rect(5, 19, 14, 5, "r")
        face(cv, ("s", "S"), "M", "curly")
        cv.put(6, 15, "y")
        cv.put(18, 15, "y")
    elif aid == "perro":
        cv.ellipse(12, 13, 7, 6, "M")
        cv.ellipse(5, 9, 3, 5, "m")
        cv.ellipse(19, 9, 3, 5, "m")
        cv.put(9, 12, "o")
        cv.put(15, 12, "o")
        cv.rect(11, 15, 3, 2, "o")
        cv.put(12, 18, "r")
    elif aid == "gorra":
        cv.rect(5, 19, 14, 5, "n")
        face(cv, ("z", "Z"), "k", "short")
        cv.ellipse(12, 6, 7, 3, "r")
        cv.hline(12, 8, 9, "R")
    elif aid == "mate":
        cv.ellipse(11, 15, 6, 6, "m")
        cv.rect(6, 9, 11, 3, "y")
        cv.hline(6, 9, 11, "Y")
        cv.ellipse(10, 15, 2, 3, "M")
        cv.vline(14, 2, 9, "l")
        cv.vline(15, 2, 2, "l")
        cv.hline(7, 10, 9, "G")
    elif aid == "gato":
        cv.ellipse(12, 14, 7, 6, "d")
        for sx in (6, 16):
            cv.rect(sx, 6, 3, 4, "d")
            cv.put(sx + 1, 5, "d")
        cv.put(9, 13, "y")
        cv.put(15, 13, "y")
        cv.put(12, 16, "p")
        cv.hline(4, 16, 4, "l")
        cv.hline(17, 16, 4, "l")
    elif aid == "alfajor":
        rows = ICONS["alfajor"].strip("\n").split("\n")
        cv.stamp([r[:16] for r in rows], 4, 4)
    elif aid == "kiosquero":
        cv.rect(5, 19, 14, 5, "w")
        cv.rect(9, 19, 6, 5, "q")
        face(cv, ("s", "S"), "x", "short", mustache=True)
    elif aid == "galera":
        cv.rect(5, 19, 14, 5, "o")
        cv.put(12, 20, "w")
        face(cv, ("s", "S"), "x", "none", mustache=True)
        cv.rect(7, 0, 10, 6, "o")
        cv.hline(7, 4, 10, "R")
        cv.hline(4, 6, 16, "o")
    elif aid == "corona":
        cv.rect(5, 19, 14, 5, "V")
        face(cv, ("s", "S"), "k", "short")
        cv.rect(6, 3, 12, 4, "y")
        for px in (6, 11, 17):
            cv.put(px, 2, "y")
        cv.put(12, 4, "r")
    cv.outline_all("o")
    return cv


def app_icon():
    """Ícono 48x48 (se escala x4 a 192): puesto con sombrilla y moneda."""
    cv = Canvas(48, 48)
    for y in range(48):
        cv.hline(0, y, 48, "c" if y < 30 else ("E" if y < 38 else "x"))
    cv.dither(0, 28, 48, 3, "c", "b")
    # sombrilla
    for yy in range(7):
        half = int(16 * ((yy + 1) / 7) ** 0.55)
        for xx in range(-half, half + 1):
            col = RAMPS["celeste"] if ((xx + 60) // 4) % 2 == 0 else RAMPS["blanco"]
            cv.put(20 + xx, 8 + yy, col[1] if yy < 6 else col[2])
    cv.vline(20, 15, 16, "d")
    # mesa
    cv.rect(8, 30, 24, 4, "c")
    cv.hline(8, 30, 24, "b")
    cv.vline(10, 34, 6, "k")
    cv.vline(29, 34, 6, "k")
    for i, x in enumerate(range(10, 30, 4)):
        cv.rect(x, 26, 3, 4, ["y", "r", "n", "q", "v"][i % 5])
    # moneda grande
    cv.ellipse(37, 33, 8, 8, "y")
    cv.ellipse(37, 33, 6, 6, "Y")
    cv.ellipse(37, 33, 5, 5, "y")
    cv.vline(37, 28, 11, "o")
    cv.hline(35, 30, 4, "o")
    cv.hline(35, 33, 4, "o")
    cv.hline(35, 36, 4, "o")
    tmp = Canvas(48, 48)
    tmp.blit(cv, 0, 0)
    return cv


def generate(out, data_dir):
    # Desde la 0.6 el mapa y los avatares se dibujan con PXL
    # (tools/art/pxl/map.px.js y avatars.px.js); make_map() y avatar() quedan
    # sólo como referencia de la versión anterior.
    d = os.path.join(out, "icons")
    os.makedirs(d, exist_ok=True)
    ic = app_icon()
    ic.save(f"{d}/app_icon.png", scale=4)
    # Íconos adaptativos de Android (432x432): fondo liso y frente con margen.
    from PIL import Image
    bg = Image.new("RGBA", (432, 432), (117, 196, 242, 255))
    bg.save(f"{d}/app_icon_bg.png")
    fg = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    big = ic.img.resize((48 * 6, 48 * 6), Image.NEAREST)
    fg.paste(big, ((432 - 288) // 2, (432 - 288) // 2))
    fg.save(f"{d}/app_icon_fg.png")
