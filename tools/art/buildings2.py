"""Edificios 2.0: 192x150 por cuadro, 2 cuadros de animación por nivel
(hoja de 384x150: toldo que flamea, luces que titilan, humo, neón).
La fila 149 es el piso. Escala 1 m = 24 px (puerta 50 px, persona 44 px).
"""
import json
import math
import os
from px2 import Canvas, RAMP, sheet

W, H = 192, 150
G = H - 1  # fila del piso

FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "B": ["11110", "10001", "10001", "11110", "10001", "10001", "11110"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "D": ["11110", "10001", "10001", "10001", "10001", "10001", "11110"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "F": ["11111", "10000", "10000", "11110", "10000", "10000", "10000"],
    "G": ["01111", "10000", "10000", "10011", "10001", "10001", "01111"],
    "H": ["10001", "10001", "10001", "11111", "10001", "10001", "10001"],
    "I": ["111", "010", "010", "010", "010", "010", "111"],
    "J": ["00111", "00010", "00010", "00010", "10010", "10010", "01100"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "P": ["11110", "10001", "10001", "11110", "10000", "10000", "10000"],
    "Q": ["01110", "10001", "10001", "10001", "10101", "10010", "01101"],
    "R": ["11110", "10001", "10001", "11110", "10100", "10010", "10001"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    "U": ["10001", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "Z": ["11111", "00001", "00010", "00100", "01000", "10000", "11111"],
    "X": ["10001", "10001", "01010", "00100", "01010", "10001", "10001"],
    "W": ["10001", "10001", "10001", "10101", "10101", "11011", "10001"],
    "Y": ["10001", "10001", "01010", "00100", "00100", "00100", "00100"],
    "Ñ": ["01101", "10010", "10001", "11001", "10101", "10011", "10001"],
    "2": ["01110", "10001", "00001", "00110", "01000", "10000", "11111"],
    "4": ["00010", "00110", "01010", "10010", "11111", "00010", "00010"],
    "$": ["00100", "01111", "10100", "01110", "00101", "11110", "00100"],
    "0": ["01110", "10001", "10011", "10101", "11001", "10001", "01110"],
    "1": ["010", "110", "010", "010", "010", "010", "111"],
    "3": ["11110", "00001", "00001", "01110", "00001", "00001", "11110"],
    "5": ["11111", "10000", "11110", "00001", "00001", "10001", "01110"],
    "6": ["01110", "10000", "10000", "11110", "10001", "10001", "01110"],
    "7": ["11111", "00001", "00010", "00100", "01000", "01000", "01000"],
    "8": ["01110", "10001", "10001", "01110", "10001", "10001", "01110"],
    "9": ["01110", "10001", "10001", "01111", "00001", "00001", "01110"],
    " ": ["000", "000", "000", "000", "000", "000", "000"],
}
ACCENTED = {"É": "E", "Á": "A", "Í": "I", "Ó": "O", "Ú": "U"}


def text_width(s):
    return sum(len(FONT[ACCENTED.get(c, c)][0]) + 1 for c in s) - 1


def text(cv, s, x, y, color, shadow="o"):
    for ch in s:
        base = ACCENTED.get(ch, ch)
        g = FONT[base]
        for j, row in enumerate(g):
            for i, b in enumerate(row):
                if b == "1":
                    cv.put(x + i + 1, y + j + 1, shadow)
                    cv.put(x + i, y + j, color)
        if ch in ACCENTED:
            cv.put(x + 3, y - 2, color)
            cv.put(x + 2, y - 1, color)
        x += len(g[0]) + 1


# ------------------------------------------------------------------ piezas

def wall(cv, x, y, w, h, mat):
    if mat == "ladrillo":
        cv.rect(x, y, w, h, "R2")
        for j, yy in enumerate(range(y + 3, y + h, 5)):
            cv.hline(x, yy, w, "R1")
            for xx in range(x + (j % 2) * 5, x + w, 10):
                cv.vline(xx, yy + 1, 4, "R1")
                cv.put(xx + 1, yy + 1, "R3")
        cv.vline(x, y, h, "R3")
    else:
        s, m, l, hi = {"crema": ("E2", "E1", "w", "W"), "celeste": ("C2", "C3", "C4", "W"), "verde": ("G1", "G2", "G3", "G3"),
                       "blanco": ("l", "w", "W", "W"), "gris": ("x", "d", "g", "l"), "amarillo": ("Y1", "Y2", "Y3", "Y4"),
                       "rojo": ("R1", "R2", "R3", "R3"), "violeta": ("u", "x", "d", "g"), "naranja": ("Y1", "Q", "Y3", "Y4")}[mat]
        cv.rect(x, y, w, h, m)
        for yy in range(y + 2, y + h, 6):             # revoque: textura sugerida
            for xx in range(x + (yy // 6 % 2) * 4, x + w - 2, 9):
                cv.hline(xx, yy, 2, s)
        cv.vline(x, y, h, l)
    cv.rect(x + w - 3, y, 3, h, "o" if mat == "violeta" else ("R1" if mat == "ladrillo" else "x"))
    cv.put(x + w - 3, y, "x")


def cornice(cv, x, y, w, ornate=False):
    cv.rect(x - 3, y, w + 6, 5, "w")
    cv.hline(x - 3, y, w + 6, "W")
    cv.hline(x - 3, y + 4, w + 6, "l")
    for xx in range(x - 2, x + w + 3, 4):
        cv.rect(xx, y + 5, 2, 2, "l")
    if ornate:
        for xx in range(x, x + w, 16):
            cv.rect(xx + 6, y - 3, 4, 3, "w")
            cv.put(xx + 7, y - 3, "W")


def window_frame(cv, x, y, w, h, frame="madera"):
    s, m, l, _ = RAMP[frame]
    cv.rect(x - 2, y - 2, w + 4, h + 4, m)
    cv.hline(x - 2, y - 2, w + 4, l)
    cv.hline(x - 2, y + h + 1, w + 4, s)


def glass(cv, x, y, w, h, lit=False):
    cv.rect(x, y, w, h, "Y4" if lit else "C4")
    cv.rect(x, y + h // 2, w, h - h // 2, "Y3" if lit else "C3")
    for i in range(min(w, h) // 2):
        if i % 3 != 2:
            cv.put(x + 2 + i, y + h - 3 - i, "W")


def goods_shelves(cv, x, y, w, h, palette=("R2", "Y2", "G2", "C2", "Q", "R3", "G3", "Y3")):
    rows = max(1, h // 11)
    for r in range(rows):
        yy = y + 2 + r * 11
        cv.hline(x, yy + 8, w, "M2")
        for i, xx in enumerate(range(x + 2, x + w - 4, 6)):
            c = palette[(i + r * 3) % len(palette)]
            cv.rect(xx, yy + 2, 4, 6, c)
            cv.put(xx, yy + 2, "W")
            cv.hline(xx, yy + 7, 4, "o")


def content(cv, x, y, w, h, kind):
    if kind == "goods":
        goods_shelves(cv, x, y, w, h)
    elif kind == "candy":
        for i, xx in enumerate(range(x + 2, x + w - 7, 9)):
            cv.rect(xx, y + h - 12, 7, 11, "l")
            cv.hline(xx, y + h - 13, 7, "R2")
            for k, c in enumerate(("R2", "Y2", "G2", "C2", "R3")):
                cv.put(xx + 1 + (k * 2) % 5, y + h - 10 + k, c)
        goods_shelves(cv, x, y, w, max(11, h - 16), ("Y2", "R2", "C2", "G2"))
    elif kind == "tables":
        for xx in range(x + 3, x + w - 12, 16):
            cv.rect(xx, y + h - 11, 12, 2, "M3")
            cv.vline(xx + 5, y + h - 9, 8, "M1")
            cv.rect(xx + 2, y + h - 14, 3, 3, "W")
            cv.rect(xx + 7, y + h - 15, 2, 4, "Y2")
        cv.rect(x + 2, y + 3, w - 4, 3, "Y3")
    elif kind == "people":
        for i, xx in enumerate(range(x + 4, x + w - 8, 12)):
            cv.rect(xx + 1, y + h - 22, 5, 5, ["S1", "S2", "M3"][i % 3])
            cv.rect(xx, y + h - 17, 7, 9, ["R2", "C2", "G2", "Y2"][i % 4])
            cv.rect(xx - 2, y + h - 9, 12, 2, "M3")
    elif kind == "weights":
        for xx in range(x + 4, x + w - 14, 16):
            cv.hline(xx, y + h - 8, 12, "g")
            cv.rect(xx, y + h - 12, 3, 9, "o")
            cv.rect(xx + 9, y + h - 12, 3, 9, "o")
        cv.rect(x + 3, y + 4, w - 6, 8, "x")
        cv.rect(x + 5, y + 6, (w - 10) // 2, 4, "R2")
    elif kind == "boxes":
        for i, xx in enumerate(range(x + 2, x + w - 9, 10)):
            for k in range(1 + i % 2):
                cv.rect(xx, y + h - 9 - k * 9, 9, 8, "M3")
                cv.hline(xx, y + h - 9 - k * 9, 9, "M4")
                cv.vline(xx + 4, y + h - 9 - k * 9, 8, "E2")
    elif kind == "cars":
        car(cv, x + w // 2 - 22, y + h - 18, "rojo")


def door(cv, x, y, w=26, h=50, shutter=0.0):
    cv.rect(x - 2, y - 2, w + 4, h + 2, "M2")
    cv.hline(x - 2, y - 2, w + 4, "M3")
    cv.rect(x, y, w, h, "M3")
    cv.vline(x + w // 2, y, h, "M1")
    cv.rect(x + 3, y + 4, w // 2 - 5, h // 2 - 4, "C4")
    cv.rect(x + w // 2 + 2, y + 4, w // 2 - 5, h // 2 - 4, "C4")
    cv.put(x + 4, y + 5, "W")
    cv.put(x + w // 2 + 3, y + 5, "W")
    cv.rect(x + w // 2 - 3, y + h // 2 + 3, 2, 3, "Y3")
    cv.rect(x + w // 2 + 2, y + h // 2 + 3, 2, 3, "Y3")
    if shutter > 0:
        sh = int(h * shutter)
        for yy in range(y, y + sh):
            cv.hline(x, yy, w, "g" if yy % 2 == 0 else "d")
        cv.hline(x, y + sh, w, "x")


def awning(cv, x, y, w, ramp_a, f, depth=11):
    a = RAMP[ramp_a]
    b = ("l", "w", "W", "W")
    for xx in range(x, x + w):
        stripe = ((xx - x) // 6) % 2 == 0
        r = a if stripe else b
        for yy in range(y, y + depth):
            c = r[3] if yy == y else (r[0] if yy == y + depth - 1 else r[2] if yy < y + 3 else r[1])
            cv.put(xx, yy, c)
    off = f  # flameo: el festón se corre 1 px
    for xx in range(x, x + w, 6):
        stripe = ((xx - x) // 6) % 2 == 0
        r = a if stripe else b
        cv.rect(xx + 1 + off, y + depth, 4, 2, r[1])
        cv.rect(xx + 2 + off, y + depth + 2, 2, 1, r[0])
    cv.hline(x - 1, y - 1, w + 2, "o")


def sign(cv, cx, y, label, ramp="noche", ornate=False, lit_frame=None):
    tw = text_width(label)
    w = tw + 14
    h = 15
    x = cx - w // 2
    s, m, l, hi = RAMP[ramp]
    cv.rect(x, y, w, h, m)
    cv.hline(x, y, w, l)
    cv.hline(x, y + h - 1, w, s)
    cv.frame(x + 2, y + 2, w - 4, h - 4, "Y2")
    text(cv, label, x + 7, y + 4, "Y3", "o")
    cv.frame(x - 1, y - 1, w + 2, h + 2, "o")
    if ornate:   # fileteado: volutas en los extremos
        for ex, d in ((x - 2, -1), (x + w + 1, 1)):
            curl = [(0, 3), (d, 4), (2 * d, 6), (2 * d, 8), (d, 10), (0, 11), (d, 12), (3 * d, 7)]
            for i, (dx, dy) in enumerate(curl):
                cv.put(ex + dx, y + dy, "Y2" if i % 2 else "R2")
                cv.put(ex + dx, y + dy + 1, "o")
    if lit_frame is not None:  # bombitas alrededor que titilan
        for i, xx in enumerate(range(x + 2, x + w - 1, 4)):
            on = (i + lit_frame) % 2 == 0
            cv.put(xx, y - 3, "Y4" if on else "Y1")
            cv.put(xx, y + h + 2, "Y4" if not on else "Y1")
    return x, w


def string_lights(cv, x1, x2, y, f, sag=5):
    n = x2 - x1
    for i in range(n + 1):
        t = i / max(1, n)
        yy = y + round(sag * 4 * t * (1 - t))
        cv.put(x1 + i, yy, "o")
        if i % 7 == 3:
            on = ((i // 7) + f) % 2 == 0
            cv.rect(x1 + i, yy + 1, 2, 2, ["Y3", "R3", "C4", "G3"][(i // 7) % 4] if on else "x")


def plant(cv, x, y):
    cv.rect(x, y + 7, 8, 7, "Q")
    cv.hline(x, y + 7, 8, "Y3")
    cv.vline(x + 7, y + 7, 7, "Y1")
    cv.ellipse(x + 4, y + 3, 5, 4, "G2")
    cv.ellipse(x + 3, y + 2, 2, 2, "G3")
    cv.put(x + 6, y + 5, "G1")
    cv.frame(x - 1, y + 6, 10, 9, "o")


def lamp(cv, x, y_top):
    cv.vline(x, y_top, G - y_top, "u")
    cv.vline(x + 1, y_top, G - y_top, "x")
    cv.rect(x - 3, y_top - 6, 8, 6, "u")
    cv.rect(x - 2, y_top - 5, 6, 4, "Y4")
    cv.rect(x - 2, G - 2, 6, 3, "u")


def crate(cv, x, y, fill):
    cv.rect(x, y, 14, 9, "M3")
    cv.hline(x, y, 14, "M4")
    cv.hline(x, y + 4, 14, "M2")
    cv.frame(x - 1, y - 1, 16, 11, "o")
    for i in range(4):
        cv.ellipse(x + 2 + i * 3, y - 2, 2, 2, fill[i % len(fill)])


def fridge(cv, x, y, ramp="rojo", label=True):
    s, m, l, hi = RAMP[ramp]
    cv.rect(x, y, 18, G - y + 1, m)
    cv.vline(x, y, G - y + 1, l)
    cv.vline(x + 17, y, G - y + 1, s)
    cv.rect(x + 3, y + 8, 12, G - y - 12, "C4")
    for yy in range(y + 11, G - 5, 6):
        cv.hline(x + 3, yy + 4, 12, "W")
        for xx in range(x + 4, x + 14, 3):
            cv.rect(xx, yy, 2, 4, ["R2", "G2", "Y2", "Q"][(xx + yy) % 4])
    if label:
        cv.rect(x + 2, y + 2, 14, 4, "W")
        cv.hline(x + 4, y + 3, 10, s)
    cv.frame(x - 1, y - 1, 20, G - y + 2, "o")


def smoke(cv, x, y, f):
    for i, (dx, dy, r) in enumerate(((0, 0, 3), (3 + f, -7, 4), (-1 + f, -15, 4), (2 - f, -22, 3))):
        cv.ellipse(x + dx, y + dy, r, r - 1, "l" if (i + f) % 2 else "w")


def car(cv, x, y, ramp="rojo", wet=False, f=0):
    s, m, l, hi = RAMP[ramp]
    cv.rect(x + 9, y, 26, 8, m)
    cv.rect(x + 11, y + 2, 10, 5, "C4")
    cv.rect(x + 23, y + 2, 10, 5, "C4")
    cv.rect(x, y + 8, 44, 9, m)
    cv.hline(x, y + 8, 44, l)
    cv.hline(x, y + 16, 44, s)
    cv.rect(x + 40, y + 10, 3, 2, "Y3")
    cv.rect(x + 1, y + 10, 2, 2, "R3")
    for wx in (x + 9, x + 34):
        cv.ellipse(wx, y + 17, 4, 4, "o")
        cv.ellipse(wx, y + 17, 2, 2, "g")
    cv.frame(x - 1, y + 7, 46, 11, "o")
    cv.frame(x + 8, y - 1, 28, 9, "o")
    if wet:
        for i, (fx, fy) in enumerate(((x + 4, y + 4), (x + 18, y - 4), (x + 36, y + 2), (x + 26, y + 9))):
            cv.ellipse(fx + (f if i % 2 else -f), fy, 3, 2, "W")
            cv.put(fx - 1, fy - 1, "C4")


def balcony(cv, x, y, w):
    cv.rect(x, y, w, 3, "x")
    cv.hline(x, y, w, "d")
    cv.hline(x, y - 10, w, "o")
    for xx in range(x, x + w, 4):
        cv.vline(xx, y - 10, 10, "o")
    for xx in range(x + 2, x + w - 2, 8):
        cv.put(xx, y - 5, "x")
        cv.put(xx + 1, y - 6, "x")


def upper_floor(cv, x, y, w, lit_f=None):
    n = max(1, (w - 12) // 30)
    span = (w - 12) // n
    for i in range(n):
        wx = x + 8 + i * span + (span - 18) // 2
        window_frame(cv, wx, y + 10, 18, 30, "blanco")
        glass(cv, wx, y + 10, 18, 30, lit=lit_f is not None and (i + lit_f) % 2 == 0)
        # persianas de madera entreabiertas
        for yy in range(y + 10, y + 18):
            cv.hline(wx, yy, 18, "G2" if yy % 2 == 0 else "G1")
        cv.rect(wx - 4, y + 42, 26, 3, "w")
        cv.ellipse(wx + 3, y + 40, 3, 2, "G2")
        cv.ellipse(wx + 14, y + 40, 3, 2, "R3")


# --------------------------------------------------------- fachada genérica

def storefront(cv, cx, w, floors, mat, sign_text, sign_ramp, aw_ramp, kind, t, f, shutter=0.0, neon=None):
    floor_h = 62
    h = 14 + floors * floor_h
    x = cx - w // 2
    y = G - h + 1
    wall(cv, x, y, w, h, mat)
    cornice(cv, x, y, w, ornate=t >= 3)
    gy = G - floor_h + 1               # arranque de la planta baja
    # vidrieras y puerta
    dw = 26
    dx = x + w - dw - 10 if w >= 120 else cx - dw // 2
    door(cv, dx, G - 49, dw, 50, shutter)
    if w >= 120:
        vw = dx - x - 18
        window_frame(cv, x + 8, gy + 18, vw, 34)
        glass(cv, x + 8, gy + 18, vw, 34, lit=t >= 3)
        content(cv, x + 8, gy + 18, vw, 34, kind)
    else:
        for vx in (x + 6, dx + dw + 6):
            vw = (w - dw) // 2 - 12
            if vw >= 12:
                window_frame(cv, vx, gy + 20, vw, 30)
                glass(cv, vx, gy + 20, vw, 30)
                content(cv, vx, gy + 20, vw, 30, kind)
    if t >= 1:
        awning(cv, x + 2, gy + 2, w - 4, aw_ramp, f)
    for fl in range(1, floors):
        fy = G - floor_h * (fl + 1) + 1
        upper_floor(cv, x, fy, w, f if t >= 4 else None)
        if fl == 1 and t >= 3:
            balcony(cv, x + 6, fy + 52, w - 12)
    sign(cv, cx, y + 5, sign_text, sign_ramp, ornate=t >= 2, lit_frame=f if t >= 3 else None)
    if neon:
        nx = x + 6
        ny = gy - 2 if floors == 1 else G - floor_h - 14
        on = f == 0
        tw = text_width(neon)
        cv.rect(nx, ny, tw + 6, 11, "u")
        cv.frame(nx - 1, ny - 1, tw + 8, 13, "o")
        text(cv, neon, nx + 3, ny + 2, "R3" if on else "R1", "u")
    return x, y, w, h


# ------------------------------------------------------------- negocios

def puesto(t, f):
    cv = Canvas(W, H)
    cx = W // 2
    if t >= 3:
        if t == 3:
            # casilla con persiana levantada y ventanita
            bx, bw = cx + 6, 64
            wall(cv, bx, G - 82, bw, 83, "celeste")
            cornice(cv, bx, G - 82, bw)
            window_frame(cv, bx + 8, G - 58, bw - 16, 26)
            glass(cv, bx + 8, G - 58, bw - 16, 26)
            content(cv, bx + 8, G - 58, bw - 16, 26, "candy")
            for yy in range(G - 62, G - 56):
                cv.hline(bx + 6, yy, bw - 12, "g" if yy % 2 else "d")
            cv.rect(bx + 4, G - 31, bw - 8, 4, "M3")
            cv.hline(bx + 4, G - 31, bw - 8, "M4")
            awning(cv, bx + 2, G - 70, bw - 4, "celeste", f, 9)
            sign(cv, bx + bw // 2, G - 80, "PUESTO", "noche", ornate=True)
            tx = cx - 74
        else:
            storefront(cv, cx + 22, 140, 2, "celeste", "EL PUESTITO", "noche", "amarillo", "goods", 4, f)
            tx = cx - 92
            string_lights(cv, tx, cx - 46, G - 66, f)
    else:
        tx = cx - [24, 30, 34][t]
    tw = [48, 60, 62, 46, 42][t]
    ty = G - 20
    # mesa con mantel a cuadros celeste y blanco
    for xx in range(tx, tx + tw):
        for yy in range(ty, ty + 9):
            check = ((xx - tx) // 3 + (yy - ty) // 3) % 2 == 0
            cv.put(xx, yy, ("C3" if yy < ty + 8 else "C2") if check else ("W" if yy < ty + 8 else "l"))
    cv.frame(tx - 1, ty - 1, tw + 2, 11, "o")
    cv.rect(tx + 3, ty + 10, 3, 10, "M2")
    cv.rect(tx + tw - 6, ty + 10, 3, 10, "M2")
    # mercadería: cajas de alfajores, botellas, bolsas de snacks, frasco de golosinas
    gx = tx + 3
    items = [("alf", 0), ("bot", 0), ("snk", 0), ("alf", 1), ("bot", 1), ("jar", 0), ("snk", 1), ("bot", 2)]
    for kind, v in items[: 3 + t if t < 3 else 5]:
        if gx > tx + tw - 7:
            break
        if kind == "alf":
            cv.rect(gx, ty - 5, 8, 5, ["M2", "C1"][v])
            cv.hline(gx, ty - 5, 8, ["M3", "C2"][v])
            cv.rect(gx + 2, ty - 4, 4, 2, "W")
            gx += 9
        elif kind == "bot":
            c = ["R2", "G2", "Y2"][v]
            cv.rect(gx + 1, ty - 12, 3, 12, c)
            cv.rect(gx + 2, ty - 15, 1, 3, c)
            cv.put(gx + 1, ty - 11, "W")
            cv.rect(gx + 1, ty - 8, 3, 3, "W")
            gx += 5
        elif kind == "snk":
            c = ["Y2", "R3"][v]
            cv.rect(gx, ty - 9, 6, 9, c)
            cv.hline(gx, ty - 9, 6, "W")
            cv.rect(gx + 1, ty - 6, 4, 3, "R2" if v == 0 else "Y3")
            gx += 7
        elif kind == "jar":
            cv.rect(gx, ty - 10, 8, 10, "l")
            cv.hline(gx, ty - 11, 8, "R2")
            for k, c in enumerate(("R2", "Y2", "G2", "C2", "R3", "Y3")):
                cv.put(gx + 1 + (k * 3) % 6, ty - 8 + k, c)
            gx += 9
    if t < 3:
        # sombrilla grande que flamea
        pole = tx + tw // 2
        cv.rect(pole, ty - 44, 2, 44, "x")
        r = 24 + t * 3
        for yy in range(10):
            half = round(r * ((yy + 1) / 10) ** 0.5)
            for xx in range(-half, half + 1):
                stripe = ((xx + 60) // 5) % 2 == 0
                rr = RAMP["celeste"] if stripe else ("l", "w", "W", "W")
                cv.put(pole + xx + (1 if f and yy > 6 else 0), ty - 54 + yy, rr[2] if yy < 3 else (rr[0] if yy == 9 else rr[1]))
        cv.rect(pole - 1, ty - 57, 4, 3, "Y2")
        # cartelito de pizarra con precio
        cv.rect(tx - 16, ty - 4, 13, 12, "u")
        cv.frame(tx - 17, ty - 5, 15, 14, "M2")
        text(cv, "$5", tx - 14, ty - 2, "W", "u")
        cv.vline(tx - 15, ty + 8, 12, "M2")
        cv.vline(tx - 6, ty + 8, 12, "M2")
    if t >= 1:
        # conservadora y cajones
        cv.rect(tx + tw + 4, G - 13, 18, 14, "C2")
        cv.hline(tx + tw + 4, G - 13, 18, "C4")
        cv.rect(tx + tw + 4, G - 16, 18, 4, "W")
        cv.frame(tx + tw + 3, G - 17, 20, 19, "o")
        if t < 3:
            crate(cv, tx - 34, G - 9, ("R2", "Y2", "G2"))
    if t >= 1 and t < 3:
        # ristra de snacks colgando de la sombrilla
        for i in range(4):
            cv.rect(tx + 6 + i * 6, ty - 30 + (i + f) % 2, 5, 7, ["Y2", "R3", "G3", "Y3"][i])
            cv.vline(tx + 8 + i * 6, ty - 33, 3, "x")
    if t == 2:
        # caja registradora y luces
        cv.rect(tx + tw - 16, ty - 11, 13, 11, "g")
        cv.rect(tx + tw - 14, ty - 15, 9, 4, "C4")
        cv.rect(tx + tw - 14, ty - 8, 9, 3, "x")
        cv.frame(tx + tw - 17, ty - 12, 15, 13, "o")
        string_lights(cv, tx - 20, tx + tw + 26, ty - 66, f, 6)
        sign(cv, tx + tw + 26, G - 64, "PUESTO", "noche", ornate=True)
        cv.rect(tx + tw + 25, G - 48, 2, 48, "M2")
    cv.outline()
    return cv


def kiosco(t, f):
    cv = Canvas(W, H)
    cx = W // 2
    if t <= 2:
        w = [70, 84, 92][t]
        x = cx - w // 2
        h = 104
        wall(cv, x, G - h + 1, w, h, "ladrillo")
        cornice(cv, x, G - h + 1, w)
        # ventanita con reja y mostrador
        window_frame(cv, x + 8, G - 70, w - 16, 36)
        glass(cv, x + 8, G - 70, w - 16, 36)
        content(cv, x + 8, G - 70, w - 16, 36, "candy")
        for xx in range(x + 11, x + w - 8, 5):
            cv.vline(xx, G - 70, 36, "d")
        cv.rect(x + 4, G - 32, w - 8, 5, "M3")
        cv.hline(x + 4, G - 32, w - 8, "M4")
        for yy in range(G - 26, G):
            cv.hline(x + 6, yy, w - 12, "g" if yy % 2 else "d")    # persiana baja del mostrador
        sign(cv, cx, G - h + 8, "KIOSCO", "rojo", ornate=t >= 2, lit_frame=f if t >= 2 else None)
        if t >= 1:
            awning(cv, x + 2, G - 82, w - 4, "rojo", f, 9)
            fridge(cv, x + w + 4, G - 42, "rojo")
        if t >= 2:
            # revistero con figuritas
            cv.rect(x - 24, G - 26, 18, 27, "M2")
            for i, c in enumerate(("R2", "C2", "Y2", "G2")):
                cv.rect(x - 22, G - 24 + i * 6, 14, 5, c)
                cv.hline(x - 22, G - 24 + i * 6, 14, "W")
            cv.frame(x - 25, G - 27, 20, 29, "o")
    else:
        w = 128 if t == 3 else 172
        storefront(cv, cx, w, 2, "ladrillo", "MAXIKIOSCO" if t == 4 else "KIOSCO", "rojo", "rojo", "candy", t, f, neon="24 HS")
        fridge(cv, cx + w // 2 + 4, G - 42, "rojo")
        if t == 4:
            fridge(cv, cx - w // 2 - 22, G - 42, "celeste")
    cv.outline()
    return cv


def comida(t, f):
    cv = Canvas(W, H)
    cx = W // 2
    if t <= 2:
        w = [52, 70, 78][t]
        x = cx - w // 2
        # parrilla con chorizos y humo
        cv.rect(x, G - 34, w, 16, "x")
        cv.hline(x, G - 34, w, "d")
        cv.rect(x + 2, G - 37, w - 4, 3, "o")
        for xx in range(x + 3, x + w - 3, 3):
            cv.put(xx, G - 36, "g")
        for i, xx in enumerate(range(x + 5, x + w - 12, 12)):
            cv.rect(xx, G - 41, 10, 4, "R1" if i % 2 else "Q")
            cv.hline(xx, G - 41, 10, "R3" if i % 2 else "Y3")
        cv.rect(x + 2, G - 30, w - 4, 4, "Y1")    # brasas
        cv.dither(x + 2, G - 30, w - 4, 4, "R3", "Y2") if f else None
        smoke(cv, x + w // 2, G - 48, f)
        smoke(cv, x + w // 2 + 14, G - 46, 1 - f)
        if t == 0:
            for lx in (x + 3, x + w - 6):
                cv.rect(lx, G - 18, 3, 19, "o")
        else:
            cv.rect(x, G - 18, w, 6, "Q")
            cv.hline(x, G - 18, w, "Y3")
            for wx in (x + 8, x + w - 10):
                cv.ellipse(wx, G - 6, 6, 6, "o")
                cv.ellipse(wx, G - 6, 3, 3, "g")
            awning(cv, x - 4, G - 74, w + 8, "naranja", f, 9)
            cv.rect(x, G - 64, 2, 30, "x")
            cv.rect(x + w - 2, G - 64, 2, 30, "x")
            sign(cv, cx, G - 92, "CHORIPÁN", "noche", ornate=t >= 2)
        if t >= 2:
            for bx in (x - 30, x + w + 12):
                cv.rect(bx, G - 12, 20, 4, "M3")
                cv.hline(bx, G - 12, 20, "M4")
                cv.rect(bx + 2, G - 8, 2, 9, "M1")
                cv.rect(bx + 16, G - 8, 2, 9, "M1")
                cv.frame(bx - 1, G - 13, 22, 6, "o")
            string_lights(cv, x - 30, x + w + 32, G - 100, f, 6)
    elif t == 3:
        # food truck
        x = cx - 72
        cv.rect(x, G - 74, 110, 56, "Q")
        cv.hline(x, G - 74, 110, "Y3")
        cv.hline(x, G - 19, 110, "Y1")
        cv.rect(x + 110, G - 52, 32, 34, "Q")
        cv.rect(x + 116, G - 48, 20, 14, "C4")
        cv.frame(x + 109, G - 53, 34, 36, "o")
        cv.frame(x - 1, G - 75, 112, 58, "o")
        window_frame(cv, x + 12, G - 64, 70, 24)
        glass(cv, x + 12, G - 64, 70, 24, lit=True)
        content(cv, x + 12, G - 64, 70, 24, "people")
        cv.rect(x + 10, G - 40, 74, 4, "W")
        awning(cv, x + 10, G - 76, 74, "amarillo", f, 8)
        for wx in (x + 20, x + 120):
            cv.ellipse(wx, G - 9, 9, 9, "o")
            cv.ellipse(wx, G - 9, 4, 4, "g")
        sign(cv, x + 50, G - 100, "CHORIPÁN", "noche", ornate=True, lit_frame=f)
        smoke(cv, x + 4, G - 84, f)
    else:
        storefront(cv, cx, 172, 2, "ladrillo", "PARRILLA", "noche", "naranja", "tables", 4, f)
        cv.rect(cx + 60, G - 150 + 2, 8, 16, "x")
        smoke(cv, cx + 64, G - 150 + 4, f)
    cv.outline()
    return cv


def lavadero(t, f):
    cv = Canvas(W, H)
    cx = W // 2
    if t == 0:
        car(cv, cx - 30, G - 22, "rojo", True, f)
        cv.rect(cx + 24, G - 10, 10, 11, "C2")
        cv.hline(cx + 24, G - 10, 10, "C4")
        cv.hline(cx + 34, G - 3, 30, "G2")
        sign(cv, cx - 66, G - 60, "LAVADO", "celeste")
        cv.rect(cx - 67, G - 44, 2, 44, "M2")
    elif t <= 2:
        w = 120 if t == 1 else 180
        x = cx - w // 2
        cv.rect(x, G - 86, w, 10, "g")
        cv.hline(x, G - 86, w, "l")
        cv.frame(x - 1, G - 87, w + 2, 12, "o")
        awning(cv, x + 2, G - 76, w - 4, "celeste", f, 7)
        for xx in range(x + 2, x + w, 58):
            cv.rect(xx, G - 66, 5, 67, "l")
            cv.vline(xx + 4, G - 66, 67, "g")
        car(cv, x + 12, G - 22, "verde", True, f)
        if t == 2:
            car(cv, x + 78, G - 22, "amarillo", True, 1 - f)
            cv.rect(x + w - 18, G - 34, 14, 35, "u")    # aspiradora
            cv.rect(x + w - 16, G - 30, 10, 6, "C3")
        sign(cv, cx, G - 110, "LAVADERO", "celeste", ornate=t == 2, lit_frame=f if t == 2 else None)
    else:
        w = 150 if t == 3 else 184
        x = cx - w // 2
        h = 104 if t == 3 else 120
        wall(cv, x, G - h + 1, w, h, "blanco")
        cornice(cv, x, G - h + 1, w, ornate=True)
        bays = 2 if t == 3 else 3
        bw = (w - 10) // bays
        for i in range(bays):
            bx = x + 5 + i * bw
            cv.rect(bx + 3, G - 58, bw - 6, 59, "u")
            cv.frame(bx + 2, G - 59, bw - 4, 61, "o")
            if t == 4:
                for k in range(5):
                    cv.rect(bx + 6 + k * 8, G - 56 + (f + k) % 2 * 2, 4, 26, ["R2", "C3", "Y2", "G2", "R3"][k])
            car(cv, bx + (bw - 44) // 2, G - 22, ["rojo", "celeste", "amarillo"][i % 3], True, f)
        sign(cv, cx, G - h + 8, "LAVADERO", "celeste", ornate=True, lit_frame=f)
    cv.outline()
    return cv


GENERIC = {
    # id: (material, texto, rampa cartel, rampa toldo, vidriera, extra, persiana)
    "almacen": ("verde", "ALMACÉN", "noche", "verde", "goods", "crates", 0.3),
    "cafeteria": ("crema", "CAFÉ", "madera", "madera", "tables", "chalk", 0.0),
    "restaurante": ("ladrillo", "RESTAURANTE", "bordo", "bordo", "people", "tables", 0.0),
    "supermercado": ("blanco", "SUPER", "rojo", "rojo", "goods", "carts", 0.0),
    "gimnasio": ("violeta", "GIMNASIO", "noche", "celeste", "weights", "flag", 0.0),
    "taller": ("gris", "TALLER", "naranja", "naranja", "cars", "tires", 0.5),
    "mensajeria": ("amarillo", "ENVÍOS", "celeste", "celeste", "boxes", "motos", 0.0),
    "distribuidora": ("verde", "DISTRIBUIDORA", "amarillo", "amarillo", "boxes", "truck", 0.6),
}


def generic(bid):
    mat, label, s_ramp, a_ramp, kind, extra, shutter = GENERIC[bid]

    def fn(t, f):
        cv = Canvas(W, H)
        cx = W // 2
        widths = [96, 112, 128, 144, 176]
        floors = [1, 1, 1, 2, 2][t]
        x, y, w, h = storefront(cv, cx, widths[t], floors, mat, label, s_ramp, a_ramp, kind, t, f, shutter if t < 4 else 0.0,
                                neon="ABIERTO" if t == 4 and bid in ("cafeteria", "restaurante", "almacen") else None)
        left, right = x, x + w
        if t >= 2:
            plant(cv, left - 12, G - 14)
            plant(cv, right + 3, G - 14)
        if t >= 3:
            lamp(cv, left - 16 if left > 18 else right + 14, G - 60)
        if extra == "crates" and t >= 1:
            crate(cv, left - 18 if t < 2 else left - 30, G - 9, ("G3", "R2", "Y2"))
        elif extra == "chalk" and t >= 1:
            cv.rect(left - 18, G - 22, 14, 18, "u")
            cv.frame(left - 19, G - 23, 16, 20, "M2")
            for yy in (G - 19, G - 15, G - 11):
                cv.hline(left - 16, yy, 9, "W")
        elif extra == "tables" and t >= 1:
            for tx in ((left - 26,) if t < 3 else (left - 26, right + 8)):
                cv.rect(tx, G - 14, 16, 3, "W")
                cv.rect(tx + 7, G - 11, 2, 12, "x")
                cv.rect(tx + 7, G - 36, 2, 22, "x")
                awning(cv, tx - 4, G - 40, 24, a_ramp, f, 5)
        elif extra == "carts" and t >= 1:
            for i in range(min(t, 3)):
                cx2 = left - 20 - i * 6
                cv.rect(cx2, G - 14, 14, 8, "l")
                for xx in range(cx2, cx2 + 14, 3):
                    cv.vline(xx, G - 14, 8, "g")
                cv.frame(cx2 - 1, G - 15, 16, 10, "o")
                cv.put(cx2 + 2, G - 2, "o")
                cv.put(cx2 + 11, G - 2, "o")
        elif extra == "flag" and t >= 1:
            cv.rect(left - 14, G - 58, 2, 58, "x")
            cv.rect(left - 12, G - 58 + f, 11, 28, "R2")
            text(cv, "GYM"[:1], left - 9, G - 50 + f, "W", "R1")
        elif extra == "tires" and t >= 1:
            for i in range(2 + t):
                cv.ellipse(right + 9, G - 4 - i * 6, 7, 3, "o")
                cv.ellipse(right + 9, G - 4 - i * 6, 4, 1, "x")
        elif extra == "motos" and t >= 1:
            for i in range(min(t, 3)):
                mx = left - 30 if i == 0 else right + 4 + (i - 1) * 26
                cv.ellipse(mx + 4, G - 5, 5, 5, "o")
                cv.ellipse(mx + 20, G - 5, 5, 5, "o")
                cv.rect(mx + 5, G - 14, 16, 6, ["Y2", "R2", "C2"][i])
                cv.rect(mx + 3, G - 26, 12, 12, "Q")
                cv.hline(mx + 3, G - 26, 12, "Y3")
        elif extra == "truck" and t >= 2:
            tx = right - 80 if t < 4 else left + 6
            cv.rect(tx, G - 40, 60, 30, "W")
            cv.rect(tx + 4, G - 34, 40, 12, "G2")
            text(cv, "D", tx + 20, G - 32, "W", "G1")
            cv.rect(tx + 60, G - 30, 22, 20, "G2")
            cv.rect(tx + 64, G - 27, 13, 8, "C4")
            for wx in (tx + 10, tx + 48, tx + 70):
                cv.ellipse(wx, G - 7, 5, 5, "o")
        cv.outline()
        return cv
    return fn


ARCH = {"puesto": puesto, "kiosco": kiosco, "comida": comida, "lavadero": lavadero}


def badge(bid, main):
    """Insignia 32x32 para listas: casita con el color del rubro."""
    cv = Canvas(32, 32)
    ramp = {"celeste": "celeste", "rojo": "rojo", "naranja": "naranja", "azul": "celeste", "verde": "verde",
            "marron": "madera", "bordo": "bordo", "violeta": "gris", "gris": "gris", "amarillo": "amarillo"}.get(main, "celeste")
    s, m, l, hi = RAMP[ramp]
    for y in range(4, 14):
        half = y + 1
        cv.hline(16 - half, y, half * 2, m if y > 5 else l)
    cv.rect(4, 13, 24, 16, "E1")
    cv.vline(27, 13, 16, "E2")
    awning(cv, 4, 13, 24, ramp, 0, 5)
    cv.rect(8, 21, 7, 8, "M3")
    cv.rect(18, 21, 7, 5, "C4")
    cv.outline()
    return cv


def generate(out, data_dir):
    d = os.path.join(out, "businesses")
    os.makedirs(d, exist_ok=True)
    data = json.load(open(os.path.join(data_dir, "businesses.json"), encoding="utf-8"))
    total_fixed = 0
    for b in data["businesses"]:
        fn = ARCH.get(b["id"]) or generic(b["id"])
        for t in range(5):
            frames = [fn(t, f) for f in (0, 1)]
            for fr in frames:
                total_fixed += fr.clean_orphans()
            sheet(frames).save(f"{d}/{b['id']}_{t}.png")
        badge(b["id"], b["art"]["main"]).save(f"{d}/{b['id']}_badge.png")
    return total_fixed
