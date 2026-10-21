"""Edificios de los negocios: 5 niveles visuales por negocio (tier 0..4).

Lienzo 200x150 por nivel, apoyado sobre la vereda (abajo). Se arman con
piezas modulares: fachadas porteñas, toldos rayados, carteles con
fileteado, vidrieras con contenido según el rubro, luces, balcones.
"""
import json
import os
from px import Canvas, RAMPS
from icons import ICONS

W, H = 200, 150
GROUND = H - 1   # última fila (apoyo)


def icon_rows(name):
    raw = ICONS.get(name, ICONS["estrella"]).strip("\n").split("\n")
    return [r.replace("о", "o")[:16].ljust(16, ".") for r in raw]


def ramp(name):
    return RAMPS.get(name, RAMPS["gris"])


# ------------------------------------------------------------------ piezas

def wall(cv, x, y, w, h, rname, texture="plaster"):
    light, base, dark = ramp(rname)
    cv.rect(x, y, w, h, base)
    if texture == "brick":
        for yy in range(y + 2, y + h, 4):
            cv.hline(x + 1, yy, w - 2, dark)
            off = 0 if ((yy - y) // 4) % 2 == 0 else 3
            for xx in range(x + off, x + w, 6):
                cv.vline(xx, yy + 1, 3, dark)
    elif texture == "plaster":
        for yy in range(y + 1, y + h, 3):
            for xx in range(x + ((yy * 7) % 5), x + w - 1, 9):
                cv.put(xx, yy, light)
    elif texture == "metal":
        for xx in range(x + 2, x + w - 1, 4):
            cv.vline(xx, y + 1, h - 2, dark)
            cv.vline(xx + 1, y + 1, h - 2, light)
    cv.vline(x + w - 2, y, h, dark)
    cv.frame(x, y, w, h, "o")


def cornice(cv, x, y, w, rname="crema"):
    light, base, dark = ramp(rname)
    cv.rect(x - 2, y, w + 4, 4, base)
    cv.hline(x - 2, y, w + 4, light)
    cv.hline(x - 2, y + 3, w + 4, dark)
    for xx in range(x, x + w, 6):
        cv.put(xx, y + 4, dark)
        cv.put(xx + 1, y + 4, dark)
    cv.frame(x - 2, y, w + 4, 4, "o")


def window(cv, x, y, w, h, content="none", frame_ramp="blanco", lit=False):
    light, base, dark = ramp(frame_ramp)
    cv.rect(x, y, w, h, base)
    cv.frame(x, y, w, h, "o")
    gx, gy, gw, gh = x + 2, y + 2, w - 4, h - 4
    cv.rect(gx, gy, gw, gh, "L" if lit else "b")
    cv.rect(gx, gy + gh // 2, gw, gh - gh // 2, "y" if lit else "c")
    # reflejo diagonal
    for i in range(min(gw, gh) // 2):
        cv.put(gx + 1 + i, gy + gh - 2 - i, "h" if not lit else "w")
    _window_content(cv, gx, gy, gw, gh, content)
    cv.frame(gx - 1, gy - 1, gw + 2, gh + 2, dark)
    cv.frame(x, y, w, h, "o")


def _window_content(cv, x, y, w, h, content):
    cols = ["r", "y", "n", "c", "q", "v", "p"]
    if content == "shelves":
        for row in range(2):
            yy = y + 2 + row * (h // 2)
            cv.hline(x, yy + 3, w, "m")
            for i, xx in enumerate(range(x + 1, x + w - 1, 3)):
                cv.rect(xx, yy, 2, 3, cols[(i + row) % len(cols)])
    elif content == "candy":
        for i, xx in enumerate(range(x + 1, x + w - 3, 5)):
            cv.rect(xx, y + h - 6, 4, 5, "l")
            cv.rect(xx + 1, y + h - 4, 2, 2, cols[i % len(cols)])
            cv.hline(xx, y + h - 7, 4, "r")
    elif content == "tables":
        for xx in range(x + 2, x + w - 6, 9):
            cv.hline(xx, y + h - 5, 6, "m")
            cv.vline(xx + 2, y + h - 4, 4, "k")
            cv.rect(xx + 1, y + h - 7, 2, 2, "w")
    elif content == "weights":
        for xx in range(x + 2, x + w - 8, 10):
            cv.hline(xx, y + h - 4, 8, "g")
            cv.rect(xx, y + h - 6, 2, 5, "o")
            cv.rect(xx + 6, y + h - 6, 2, 5, "o")
    elif content == "boxes":
        for xx in range(x + 1, x + w - 5, 6):
            cv.rect(xx, y + h - 6, 5, 5, "t")
            cv.frame(xx, y + h - 6, 5, 5, "m")
    elif content == "people":
        for i, xx in enumerate(range(x + 2, x + w - 4, 8)):
            cv.rect(xx, y + h - 8, 3, 3, "S")
            cv.rect(xx - 1, y + h - 5, 5, 5, cols[i % len(cols)])


def door(cv, x, y, w, h, rname="madera", glass=True):
    light, base, dark = ramp(rname)
    cv.rect(x, y, w, h, base)
    cv.vline(x + w // 2, y, h, dark)
    if glass and h > 12:
        cv.rect(x + 2, y + 3, w // 2 - 3, h // 2 - 2, "c")
        cv.rect(x + w // 2 + 2, y + 3, w - w // 2 - 4, h // 2 - 2, "c")
        cv.put(x + 3, y + 4, "b")
    cv.put(x + w // 2 - 2, y + h // 2 + 2, "y")
    cv.put(x + w // 2 + 2, y + h // 2 + 2, "y")
    cv.frame(x, y, w, h, "o")


def awning(cv, x, y, w, main, accent="blanco", depth=8, scallop=True):
    m = ramp(main)
    a = ramp(accent)
    for xx in range(x, x + w):
        stripe = ((xx - x) // 5) % 2 == 0
        col = m if stripe else a
        for yy in range(y, y + depth):
            shade = col[2] if yy == y + depth - 1 else (col[0] if yy == y else col[1])
            cv.put(xx, yy, shade)
    if scallop:
        for xx in range(x, x + w, 5):
            stripe = ((xx - x) // 5) % 2 == 0
            col = m if stripe else a
            cv.hline(xx + 1, y + depth, 3, col[2])
            cv.put(xx + 2, y + depth + 1, col[2])
    cv.hline(x - 1, y - 1, w + 2, "o")
    cv.vline(x - 1, y, depth, "o")
    cv.vline(x + w, y, depth, "o")
    for xx in range(x, x + w, 5):
        cv.put(xx, y + depth, "o")
        cv.put(xx + 4, y + depth, "o")
        cv.put(xx + 1, y + depth + 1, "o")
        cv.put(xx + 3, y + depth + 1, "o")
        cv.put(xx + 2, y + depth + 2, "o")


def sign(cv, cx, y, w, h, main, icon, ornate=False, lit=False):
    x = cx - w // 2
    light, base, dark = ramp(main)
    cv.rect(x, y, w, h, base)
    cv.hline(x + 1, y + 1, w - 2, light)
    cv.hline(x + 1, y + h - 2, w - 2, dark)
    cv.frame(x, y, w, h, "o")
    inner = "y" if lit else "e"
    cv.frame(x + 2, y + 2, w - 4, h - 4, inner)
    cv.stamp(icon_rows(icon), cx - 8, y + h // 2 - 8)
    if ornate:
        # fileteado: volutas en las esquinas
        for (sx, sy, fx) in ((x - 6, y + 1, False), (x + w, y + 1, True)):
            curl = ["..yy..", ".y..y.", "y..y.y", "y.yy.y", ".y...y", "..yyy."]
            cv.stamp([r.replace("y", "Y") for r in curl], sx, sy + h // 2 - 3, flip=fx)
            cv.stamp(["rr", "r."], sx + (4 if not fx else 0), sy, flip=fx)
    if lit:
        for xx in range(x + 2, x + w - 2, 4):
            cv.put(xx, y - 1, "L")


def string_lights(cv, x1, x2, y, sag=4):
    n = x2 - x1
    for i in range(n + 1):
        t = i / max(n, 1)
        yy = y + int(sag * 4 * t * (1 - t))
        cv.put(x1 + i, yy, "o")
        if i % 6 == 3:
            cv.put(x1 + i, yy + 1, "y" if (i // 6) % 2 == 0 else "q")
            cv.put(x1 + i, yy + 2, "L" if (i // 6) % 2 == 0 else "y")


def crate(cv, x, y, fill):
    cv.rect(x, y, 10, 7, "M")
    cv.hline(x, y + 3, 10, "m")
    cv.frame(x, y, 10, 7, "o")
    for i in range(3):
        cv.put(x + 2 + i * 3, y - 1, fill)
        cv.put(x + 3 + i * 3, y - 1, fill)


def plant(cv, x, y):
    cv.rect(x + 1, y + 6, 6, 5, "Q")
    cv.frame(x + 1, y + 6, 6, 5, "o")
    cv.ellipse(x + 4, y + 3, 3, 3, "n")
    cv.put(x + 3, y + 1, "N")
    cv.put(x + 5, y + 3, "G")


def table_umbrella(cv, cx, main):
    cv.rect(cx - 6, GROUND - 7, 12, 2, "M")
    cv.vline(cx - 5, GROUND - 5, 5, "k")
    cv.vline(cx + 4, GROUND - 5, 5, "k")
    cv.vline(cx, GROUND - 22, 15, "d")
    awning_dome(cv, cx, GROUND - 26, 10, main)


def awning_dome(cv, cx, y, r, main):
    """Sombrilla rayada vista de frente."""
    m = ramp(main)
    a = ramp("blanco")
    rows = r // 2 + 1
    tmp = Canvas(2 * r + 5, rows + 4)
    for yy in range(rows):
        half = max(1, int(r * ((yy + 1) / rows) ** 0.55))
        for xx in range(-half, half + 1):
            col = m if ((xx + 60) // 3) % 2 == 0 else a
            shade = col[0] if yy == 0 else (col[2] if yy == rows - 1 else col[1])
            tmp.put(r + 2 + xx, yy + 1, shade)
    tmp.outline_all("o")
    cv.blit(tmp, cx - r - 2, y - 1)


def car(cv, x, y, rname="rojo", wet=False):
    l, b, d = ramp(rname)
    cv.rect(x + 6, y, 18, 6, b)
    cv.rect(x + 8, y + 1, 6, 4, "b")
    cv.rect(x + 16, y + 1, 6, 4, "b")
    cv.rect(x, y + 6, 32, 7, b)
    cv.hline(x, y + 6, 32, l)
    cv.hline(x, y + 12, 32, d)
    cv.rect(x + 29, y + 8, 3, 2, "y")
    for wx in (x + 4, x + 22):
        cv.rect(wx, y + 11, 6, 5, "o")
        cv.rect(wx + 2, y + 12, 2, 3, "g")
    cv.frame(x, y + 6, 32, 7, "o")
    cv.frame(x + 6, y, 18, 7, "o")
    if wet:
        for i, (fx, fy) in enumerate(((x + 3, y + 3), (x + 12, y - 3), (x + 24, y + 2), (x + 30, y + 4))):
            cv.ellipse(fx, fy, 2, 2, "w")
            cv.put(fx - 1, fy - 1, "h")


def smoke(cv, x, y):
    for i, (dx, dy, r) in enumerate(((0, 0, 2), (2, -5, 3), (-1, -11, 3), (2, -17, 2))):
        cv.ellipse(x + dx, y + dy, r, r, "l" if i % 2 else "w")


def balcony(cv, x, y, w):
    cv.rect(x, y, w, 2, "g")
    cv.frame(x, y, w, 2, "o")
    cv.hline(x, y - 6, w, "o")
    for xx in range(x, x + w, 3):
        cv.vline(xx, y - 6, 6, "o")
    for xx in range(x + 1, x + w, 6):
        cv.put(xx, y - 4, "x")


def fridge(cv, x, y, rname="rojo"):
    l, b, d = ramp(rname)
    cv.rect(x, y, 12, 20, b)
    cv.rect(x + 2, y + 5, 8, 12, "b")
    for yy in range(y + 7, y + 17, 4):
        cv.hline(x + 2, yy, 8, "w")
        for xx in range(x + 3, x + 10, 2):
            cv.put(xx, yy - 1, "r" if xx % 4 else "n")
    cv.rect(x + 2, y + 1, 8, 3, "w")
    cv.frame(x, y, 12, 20, "o")


def neon(cv, x, y, text_cols):
    cv.rect(x, y, len(text_cols) * 4 + 2, 7, "u")
    cv.frame(x, y, len(text_cols) * 4 + 2, 7, "o")
    for i, c in enumerate(text_cols):
        cv.rect(x + 2 + i * 4, y + 2, 2, 3, c)


def roof_tiles(cv, x, y, w):
    cv.rect(x - 3, y, w + 6, 5, "R")
    for xx in range(x - 3, x + w + 3, 4):
        cv.vline(xx, y + 1, 4, "B")
    cv.hline(x - 3, y, w + 6, "r")
    cv.frame(x - 3, y, w + 6, 5, "o")


# --------------------------------------------------------- fachadas genéricas

def storefront(cv, cx, w, floors, wall_r, main, accent, icon, content, tier, texture="plaster",
               door_r="madera", awning_on=True, ornate=False, lit=False, wide_window=False):
    floor_h = 34
    h = 16 + floors * floor_h
    x = cx - w // 2
    y = GROUND - h + 1
    wall(cv, x, y, w, h, wall_r, texture)
    cornice(cv, x, y, w)
    # planta baja
    gy = GROUND - floor_h + 3
    dw = 14
    dx = x + w // 2 - dw // 2 if not wide_window else x + w - dw - 6
    door(cv, dx, gy + 6, dw, floor_h - 6, door_r)
    if wide_window:
        window(cv, x + 5, gy + 8, dx - x - 9, floor_h - 12, content, lit=lit)
    else:
        ww = (w - dw) // 2 - 9
        if ww >= 10:
            window(cv, x + 5, gy + 8, ww, floor_h - 12, content, lit=lit)
            window(cv, dx + dw + 4, gy + 8, ww, floor_h - 12, content, lit=lit)
    if awning_on:
        awning(cv, x + 3, gy - 2, w - 6, main, accent, depth=7)
    # pisos superiores
    for f in range(1, floors):
        fy = GROUND - floor_h * (f + 1) + 6
        n = max(1, (w - 10) // 22)
        span = (w - 10) // n
        for i in range(n):
            wx = x + 6 + i * span + (span - 12) // 2
            window(cv, wx, fy + 4, 12, 18, "none", lit=lit and (i + f) % 2 == 0)
        if f == 1 and tier >= 3:
            balcony(cv, x + 4, fy + 24, w - 8)
    # cartel
    sy = y + 6 if floors == 1 else y + 6
    sign(cv, cx, sy, min(w - 12, 46 + tier * 4), 22, main, icon, ornate, lit)
    return x, y, h


# -------------------------------------------------------------- arquetipos

def arch_stall(t, art):
    cv = Canvas(W, H)
    main, accent, icon = art["main"], art["accent"], art["sign"]
    cx = W // 2
    if t >= 3:
        if t == 3:
            storefront(cv, cx + 10, 70, 1, "crema", main, accent, icon, "candy", t, awning_on=True)
        else:
            storefront(cv, cx + 15, 120, 2, "celeste", main, accent, icon, "shelves", t, ornate=True, lit=True)
            string_lights(cv, cx - 45, cx + 75, GROUND - 76, 5)
    # mesa con mantel
    tw = [30, 40, 44, 36, 36][t]
    tx = cx - tw // 2 if t < 3 else (cx + 10 - 35 - tw - 8 if t == 3 else cx + 15 - 60 - tw - 6)
    ty = GROUND - 12
    l, b, d = ramp(main)
    cv.rect(tx, ty, tw, 4, b)
    cv.hline(tx, ty, tw, l)
    for xx in range(tx, tx + tw, 4):
        cv.rect(xx, ty + 4, 2, 3, b)
    cv.frame(tx, ty, tw, 4, "o")
    cv.vline(tx + 2, ty + 4, 8, "k")
    cv.vline(tx + tw - 3, ty + 4, 8, "k")
    # mercadería sobre la mesa
    goods = ["y", "r", "c", "q", "n", "p", "v"]
    for i, xx in enumerate(range(tx + 2, tx + tw - 3, 4)):
        hh = 3 + (i % 2)
        cv.rect(xx, ty - hh, 3, hh, goods[i % len(goods)])
        cv.frame(xx, ty - hh, 3, hh, "o")
    # sombrilla
    pole_x = tx + tw // 2
    cv.vline(pole_x, ty - 26, 26, "d")
    awning_dome(cv, pole_x, ty - 30, 14 + t * 2, main)
    if t >= 1:
        crate(cv, tx - 12, GROUND - 7, "y")
        if t < 3:
            crate(cv, tx + tw + 2, GROUND - 7, "r")
        fridge(cv, tx + tw + 14, GROUND - 19, "celeste") if t < 3 else None
    if t >= 2:
        # caja registradora
        cv.rect(tx + tw - 10, ty - 7, 8, 7, "g")
        cv.rect(tx + tw - 9, ty - 9, 6, 2, "b")
        cv.frame(tx + tw - 10, ty - 7, 8, 7, "o")
        cv.put(tx + tw - 8, ty - 5, "y")
        # cartelito en un palo
        if t == 2:
            cv.vline(tx - 8, GROUND - 40, 33, "k")
            sign(cv, tx - 8, GROUND - 58, 26, 22, accent if accent != "blanco" else "amarillo", icon, ornate=True)
            string_lights(cv, tx - 8, pole_x, ty - 28, 4)
    return cv


def arch_kiosk(t, art):
    cv = Canvas(W, H)
    main, accent, icon = art["main"], art["accent"], art["sign"]
    cx = W // 2
    if t <= 2:
        w = [56, 64, 70][t]
        x = cx - w // 2
        h = 74
        y = GROUND - h + 1
        wall(cv, x, y, w, h, "crema", "brick")
        cornice(cv, x, y, w)
        # ventanita con reja
        window(cv, x + 6, GROUND - 46, w - 12, 26, "candy")
        for xx in range(x + 9, x + w - 6, 4):
            cv.vline(xx, GROUND - 44, 22, "d")
        cv.rect(x + 3, GROUND - 20, w - 6, 3, "M")
        cv.frame(x + 3, GROUND - 20, w - 6, 3, "o")
        sign(cv, cx, y + 5, w - 8, 20, main, icon, ornate=t >= 2, lit=t >= 2)
        if t >= 1:
            awning(cv, x + 2, GROUND - 54, w - 4, main, accent, 6)
            fridge(cv, x + w + 3, GROUND - 19, "rojo")
        if t >= 2:
            string_lights(cv, x - 2, x + w + 14, GROUND - 58, 4)
            # revistero
            cv.rect(x - 14, GROUND - 16, 12, 16, "M")
            for i, c in enumerate(["r", "c", "y"]):
                cv.rect(x - 13, GROUND - 15 + i * 5, 10, 4, c)
            cv.frame(x - 14, GROUND - 16, 12, 16, "o")
    else:
        w = 100 if t == 3 else 150
        storefront(cv, cx, w, 2 if t == 3 else 3, "crema", main, accent, icon, "candy", t,
                   texture="brick", ornate=True, lit=True, wide_window=True)
        neon(cv, cx - w // 2 + 6, GROUND - 68, ["r", "y", "r", "c"])
        fridge(cv, cx + w // 2 + 3, GROUND - 19, "rojo")
        if t == 4:
            fridge(cv, cx + w // 2 + 17, GROUND - 19, "celeste")
            string_lights(cv, cx - w // 2, cx + w // 2, GROUND - 42, 4)
    return cv


def arch_food_cart(t, art):
    cv = Canvas(W, H)
    main, accent, icon = art["main"], art["accent"], art["sign"]
    cx = W // 2
    if t <= 2:
        w = [36, 50, 60][t]
        x = cx - w // 2
        # parrilla/carro
        cv.rect(x, GROUND - 22, w, 12, "d")
        cv.rect(x + 2, GROUND - 24, w - 4, 3, "o")
        for xx in range(x + 3, x + w - 3, 3):
            cv.put(xx, GROUND - 23, "g")
        for i, xx in enumerate(range(x + 4, x + w - 8, 9)):
            cv.rect(xx, GROUND - 27, 7, 3, "R" if i % 2 == 0 else "q")
            cv.frame(xx, GROUND - 27, 7, 3, "o")
        cv.frame(x, GROUND - 22, w, 12, "o")
        l, b, d = ramp(main)
        cv.rect(x, GROUND - 14, w, 4, b)
        cv.hline(x, GROUND - 14, w, l)
        if t == 0:
            cv.vline(x + 3, GROUND - 10, 10, "k")
            cv.vline(x + w - 4, GROUND - 10, 10, "k")
        else:
            for wx in (x + 4, x + w - 12):
                cv.ellipse(wx + 4, GROUND - 5, 4, 4, "o")
                cv.ellipse(wx + 4, GROUND - 5, 2, 2, "g")
        smoke(cv, x + w // 2, GROUND - 32)
        cv.vline(x - 2, GROUND - 48, 38, "d")
        awning_dome(cv, x - 2 + w // 2 + 1, GROUND - 52, 12 + t * 3, main)
        if t >= 1:
            sign(cv, x + w + 16, GROUND - 46, 26, 22, accent if accent != "blanco" else "amarillo", icon, ornate=t >= 2)
            cv.vline(x + w + 16, GROUND - 24, 24, "k")
        if t >= 2:
            for bx in (x - 30, x + w + 26):
                cv.rect(bx, GROUND - 8, 16, 3, "M")
                cv.frame(bx, GROUND - 8, 16, 3, "o")
                cv.vline(bx + 2, GROUND - 5, 5, "k")
                cv.vline(bx + 13, GROUND - 5, 5, "k")
            string_lights(cv, x - 30, x + w + 40, GROUND - 56, 5)
    elif t == 3:
        # food truck
        x = cx - 50
        l, b, d = ramp(main)
        cv.rect(x, GROUND - 50, 80, 40, b)
        cv.hline(x, GROUND - 50, 80, l)
        cv.rect(x + 80, GROUND - 38, 22, 28, b)
        cv.rect(x + 84, GROUND - 35, 14, 10, "b")
        cv.frame(x + 80, GROUND - 38, 22, 28, "o")
        cv.frame(x, GROUND - 50, 80, 40, "o")
        window(cv, x + 10, GROUND - 44, 50, 18, "people", lit=True)
        cv.rect(x + 8, GROUND - 26, 54, 3, "w")
        cv.frame(x + 8, GROUND - 26, 54, 3, "o")
        awning(cv, x + 8, GROUND - 52, 54, accent if accent != "blanco" else "amarillo", "blanco", 6)
        for wx in (x + 10, x + 76):
            cv.ellipse(wx + 6, GROUND - 6, 6, 6, "o")
            cv.ellipse(wx + 6, GROUND - 6, 3, 3, "g")
        sign(cv, x + 36, GROUND - 76, 40, 20, main, icon, ornate=True)
        smoke(cv, x + 6, GROUND - 58)
    else:
        storefront(cv, cx, 140, 2, "rojo", main, accent, icon, "tables", t, texture="brick", ornate=True, lit=True)
        smoke(cv, cx + 60, GROUND - 90)
        for bx in (cx - 92, cx + 76):
            cv.rect(bx, GROUND - 8, 16, 3, "M")
            cv.frame(bx, GROUND - 8, 16, 3, "o")
    return cv


def arch_carwash(t, art):
    cv = Canvas(W, H)
    main, accent, icon = art["main"], art["accent"], art["sign"]
    cx = W // 2
    if t == 0:
        car(cv, cx - 16, GROUND - 16, "rojo", wet=True)
        cv.rect(cx + 24, GROUND - 7, 7, 7, "C")
        cv.frame(cx + 24, GROUND - 7, 7, 7, "o")
        cv.hline(cx + 31, GROUND - 3, 16, "n")
        sign(cv, cx - 40, GROUND - 46, 28, 20, main, icon)
        cv.vline(cx - 40, GROUND - 26, 26, "k")
    elif t <= 2:
        w = 90 if t == 1 else 150
        x = cx - w // 2
        # techo sobre columnas
        cv.rect(x, GROUND - 58, w, 8, "g")
        cv.hline(x, GROUND - 58, w, "l")
        cv.frame(x, GROUND - 58, w, 8, "o")
        awning(cv, x + 2, GROUND - 50, w - 4, main, accent, 5, scallop=False)
        for xx in range(x + 2, x + w, 44):
            cv.rect(xx, GROUND - 44, 4, 44, "l")
            cv.frame(xx, GROUND - 44, 4, 44, "o")
        car(cv, x + 10, GROUND - 16, "verde", wet=True)
        if t == 2:
            car(cv, x + 60, GROUND - 16, "amarillo", wet=True)
            cv.rect(x + w - 14, GROUND - 24, 10, 24, "v")
            cv.frame(x + w - 14, GROUND - 24, 10, 24, "o")
        sign(cv, cx, GROUND - 84, 50, 22, main, icon, ornate=t == 2, lit=t == 2)
    else:
        w = 120 if t == 3 else 170
        x = cx - w // 2
        h = 70 if t == 3 else 86
        wall(cv, x, GROUND - h + 1, w, h, "blanco", "metal")
        cornice(cv, x, GROUND - h + 1, w, "gris")
        bays = 2 if t == 3 else 3
        bw = (w - 10) // bays
        for i in range(bays):
            bx = x + 5 + i * bw
            cv.rect(bx + 2, GROUND - 40, bw - 4, 40, "u")
            cv.frame(bx + 2, GROUND - 40, bw - 4, 40, "o")
            if t == 4:
                for k in range(4):
                    cv.rect(bx + 4 + k * 6, GROUND - 38, 3, 20, ["r", "c", "y", "n"][k])
            car(cv, bx + (bw - 32) // 2, GROUND - 16, ["rojo", "celeste", "amarillo"][i % 3], wet=True)
        sign(cv, cx, GROUND - h + 6, 60 + (t - 3) * 10, 22, main, icon, ornate=True, lit=True)
    return cv


def outdoor_table(cv, x, main):
    cv.rect(x, GROUND - 9, 12, 2, "w")
    cv.frame(x, GROUND - 9, 12, 2, "o")
    cv.vline(x + 5, GROUND - 7, 7, "o")
    cv.vline(x + 5, GROUND - 22, 13, "d")
    awning_dome(cv, x + 5, GROUND - 25, 9, main)
    for sx in (x - 4, x + 13):
        cv.rect(sx, GROUND - 6, 3, 6, "k")


def shopping_cart(cv, x):
    cv.rect(x, GROUND - 10, 11, 6, "l")
    for xx in range(x + 1, x + 11, 2):
        cv.vline(xx, GROUND - 10, 6, "g")
    cv.frame(x, GROUND - 10, 11, 6, "o")
    cv.vline(x + 11, GROUND - 13, 4, "o")
    cv.put(x + 2, GROUND - 2, "o")
    cv.put(x + 9, GROUND - 2, "o")
    cv.hline(x + 1, GROUND - 4, 10, "o")


def banner_flag(cv, x, main):
    l, b, d = ramp(main)
    cv.vline(x, GROUND - 40, 40, "d")
    cv.rect(x + 1, GROUND - 40, 9, 22, b)
    cv.vline(x + 9, GROUND - 40, 22, d)
    cv.frame(x + 1, GROUND - 40, 9, 22, "o")
    cv.rect(x + 3, GROUND - 34, 5, 2, "w")
    cv.rect(x + 3, GROUND - 30, 5, 2, "w")


def bike(cv, x):
    for wx in (x, x + 10):
        cv.ellipse(wx + 3, GROUND - 4, 3, 3, "o")
        cv.ellipse(wx + 3, GROUND - 4, 2, 2, (0, 0, 0, 0)) if False else None
        cv.put(wx + 3, GROUND - 4, "g")
    cv.hline(x + 3, GROUND - 7, 10, "r")
    cv.vline(x + 7, GROUND - 10, 4, "o")


def chalkboard(cv, x):
    cv.rect(x, GROUND - 16, 12, 12, "u")
    cv.frame(x, GROUND - 16, 12, 12, "m")
    for yy in (GROUND - 13, GROUND - 10, GROUND - 7):
        cv.hline(x + 2, yy, 7, "w")
    cv.vline(x + 2, GROUND - 4, 4, "m")
    cv.vline(x + 9, GROUND - 4, 4, "m")


def moto(cv, x, rname="amarillo"):
    l, b, d = ramp(rname)
    for wx in (x, x + 14):
        cv.ellipse(wx + 3, GROUND - 4, 3, 3, "o")
        cv.put(wx + 3, GROUND - 4, "g")
    cv.rect(x + 4, GROUND - 10, 12, 4, b)
    cv.frame(x + 4, GROUND - 10, 12, 4, "o")
    cv.rect(x + 3, GROUND - 18, 9, 8, "q")
    cv.frame(x + 3, GROUND - 18, 9, 8, "o")
    cv.vline(x + 17, GROUND - 14, 6, "o")


def truck(cv, x, rname="verde"):
    l, b, d = ramp(rname)
    cv.rect(x, GROUND - 30, 44, 22, "w")
    cv.hline(x, GROUND - 30, 44, "h")
    cv.rect(x + 4, GROUND - 24, 30, 9, b)
    cv.frame(x, GROUND - 30, 44, 22, "o")
    cv.rect(x + 44, GROUND - 22, 16, 14, b)
    cv.rect(x + 48, GROUND - 20, 9, 6, "b")
    cv.frame(x + 44, GROUND - 22, 16, 14, "o")
    for wx in (x + 6, x + 34, x + 50):
        cv.ellipse(wx + 3, GROUND - 5, 4, 4, "o")
        cv.ellipse(wx + 3, GROUND - 5, 1, 1, "g")


def arch_generic(content, wall_r, texture="plaster", door_r="madera", extra=None):
    def f(t, art):
        cv = Canvas(W, H)
        main, accent, icon = art["main"], art["accent"], art["sign"]
        cx = W // 2
        widths = [64, 80, 96, 120, 160]
        floors = [1, 1, 1, 2, 2][t]
        storefront(cv, cx, widths[t], floors, wall_r, main, accent, icon, content, t,
                   texture=texture, door_r=door_r, awning_on=t >= 1, ornate=t >= 2, lit=t >= 2,
                   wide_window=t in (2, 4))
        if t >= 2:
            plant(cv, cx - widths[t] // 2 - 10, GROUND - 10)
            plant(cv, cx + widths[t] // 2 + 2, GROUND - 10)
        if t >= 3:
            string_lights(cv, cx - widths[t] // 2, cx + widths[t] // 2, GROUND - 40 - 34 * (floors - 1) - 4, 4)
        if t == 4:
            roof_tiles(cv, cx - widths[t] // 2, GROUND - (16 + floors * 34) - 4, widths[t])
        left = cx - widths[t] // 2
        right = cx + widths[t] // 2
        if extra == "tables" and t >= 1:
            outdoor_table(cv, left - 22, main)
            if t >= 3:
                outdoor_table(cv, right + 8, main)
        elif extra == "chalk" and t >= 1:
            chalkboard(cv, left - 16)
            if t >= 3:
                outdoor_table(cv, right + 8, accent if accent != "crema" else "marron")
        elif extra == "carts" and t >= 1:
            for i in range(min(t, 3)):
                shopping_cart(cv, left - 16 - i * 5)
        elif extra == "gym" and t >= 1:
            banner_flag(cv, left - 14, main)
            if t >= 2:
                bike(cv, right + 6)
        return cv
    return f


def arch_garage(t, art):
    cv = Canvas(W, H)
    main, accent, icon = art["main"], art["accent"], art["sign"]
    cx = W // 2
    w = [70, 90, 110, 140, 170][t]
    x = cx - w // 2
    h = [56, 60, 66, 74, 84][t]
    wall(cv, x, GROUND - h + 1, w, h, "gris", "brick")
    cornice(cv, x, GROUND - h + 1, w, "gris")
    doors = 1 if t < 3 else 2
    dw = (w - 12) // doors
    for i in range(doors):
        dx = x + 6 + i * dw
        cv.rect(dx + 2, GROUND - 36, dw - 4, 36, "u")
        for yy in range(GROUND - 34, GROUND, 4):
            cv.hline(dx + 2, yy, dw - 4, "x")
        cv.rect(dx + 2, GROUND - 36, dw - 4, 10, "g")
        for yy in range(GROUND - 34, GROUND - 26, 3):
            cv.hline(dx + 2, yy, dw - 4, "d")
        cv.frame(dx + 2, GROUND - 36, dw - 4, 36, "o")
        car(cv, dx + (dw - 32) // 2, GROUND - 16 - (6 if t >= 2 and i == 0 else 0), ["azul", "rojo"][i % 2])
        if t >= 2 and i == 0:
            cv.rect(dx + (dw - 32) // 2 + 2, GROUND - 6, 28, 2, "y")
            cv.frame(dx + (dw - 32) // 2 + 2, GROUND - 6, 28, 2, "o")
    sign(cv, cx, GROUND - h + 5, min(w - 10, 50 + t * 6), 20, main, icon, ornate=t >= 2, lit=t >= 3)
    if t >= 1:
        for i in range(2 + t):
            cv.ellipse(x + w + 6, GROUND - 3 - i * 5, 3, 2, "o")
    return cv


def arch_warehouse(t, art):
    cv = Canvas(W, H)
    main, accent, icon = art["main"], art["accent"], art["sign"]
    cx = W // 2
    w = [80, 100, 120, 150, 180][t]
    x = cx - w // 2
    h = [50, 56, 64, 72, 82][t]
    y = GROUND - h + 1
    wall(cv, x, y + 10, w, h - 10, "celeste" if art["archetype"] == "depot" else "blanco", "metal")
    # techo a dos aguas
    roof = Canvas(w + 8, 16)
    for i in range(11):
        roof.hline(2 + i * 2, 12 - i, w + 4 - i * 4, "R" if i % 2 else "r")
    roof.outline_all("o")
    cv.blit(roof, x - 4, y - 2)
    gates = 1 + t // 2
    gw = (w - 10) // gates
    for i in range(gates):
        gx = x + 5 + i * gw
        cv.rect(gx + 3, GROUND - 32, gw - 6, 32, "Y")
        for yy in range(GROUND - 30, GROUND, 3):
            cv.hline(gx + 3, yy, gw - 6, "y")
        cv.frame(gx + 3, GROUND - 32, gw - 6, 32, "o")
    if art["archetype"] == "depot":
        for i in range(min(t + 1, 3)):
            moto(cv, x - 22 - i * 4 if i == 0 else x + w + 2 + (i - 1) * 20, ["amarillo", "rojo", "celeste"][i])
    else:
        for i in range(t + 1):
            crate(cv, x - 14 - (i % 2) * 11, GROUND - 7 - (i // 2) * 8, "y")
        if t >= 2:
            truck(cv, x + w - 64, art["main"])
    sign(cv, cx, y + 14, min(w - 16, 48 + t * 5), 20, main, icon, ornate=t >= 2, lit=t >= 3)
    return cv


ARCHETYPES = {
    "stall": arch_stall,
    "kiosk": arch_kiosk,
    "food_cart": arch_food_cart,
    "carwash": arch_carwash,
    "shop": arch_generic("shelves", "verde", "plaster"),
    "cafe": arch_generic("tables", "crema", "brick", extra="chalk"),
    "restaurant": arch_generic("people", "bordo", "brick", extra="tables"),
    "supermarket": arch_generic("shelves", "blanco", "plaster", "gris", extra="carts"),
    "gym": arch_generic("weights", "violeta", "plaster", "gris", extra="gym"),
    "garage": arch_garage,
    "depot": arch_warehouse,
    "warehouse": arch_warehouse,
}


def business_badge(art):
    """Ícono 24x24 del negocio para listas: casita con el color y su ícono."""
    cv = Canvas(24, 24)
    l, b, d = ramp(art["main"])
    cv.rect(1, 6, 22, 17, b)
    cv.hline(2, 7, 20, l)
    for i in range(6):
        cv.hline(11 - i * 2, i, 2 + i * 4, d if i % 2 else b)
    cv.stamp(icon_rows(art["sign"]), 4, 7)
    cv.outline_all("o")
    return cv


def generate(out, data_dir):
    d = os.path.join(out, "businesses")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(data_dir, "businesses.json"), encoding="utf-8") as f:
        data = json.load(f)
    for b in data["businesses"]:
        art = b["art"]
        fn = ARCHETYPES[art["archetype"]]
        for t in range(5):
            cv = fn(t, art)
            cv.save(f"{d}/{b['id']}_{t}.png")
        business_badge(art).save(f"{d}/{b['id']}_badge.png")
