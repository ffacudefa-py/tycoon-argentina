"""Edificios 10.2: diseños detallados por provincia (192x150, 2 cuadros por nivel).

Cada provincia tiene 5 construcciones DISTINTAS (no la misma con agregados):
  nivel 1   puestito o rancho hecho a mano
  nivel 10  casa / local propio
  nivel 25  taller o galpón con patio de trabajo
  nivel 50  complejo productivo (dos naves, maquinaria, vehículos)
  nivel 100 sede insignia con cartel luminoso, banderas y flota
Piezas con textura (adobe, ladrillo, piedra, madera, chapa, vidrio, colonial),
techos (teja, paja, chapa, dientes de sierra), ventanas con postigos, rejas,
arcos y vidrieras, y utilería propia de cada rubro. Luz arriba a la izquierda.
"""
import math
from px2 import Canvas, RAMP
from buildings2 import W, H, G, sign, smoke, text, text_width, awning, lamp
from buildings3 import tree, crop, vines, sheep, cow, llama, windmill, water, soil, fence

# ------------------------------------------------------------ texturas

WALLS = {
    #          base   sombra  luz    detalle
    "adobe": ("E2", "S2", "E1", "S3"),
    "ladrillo": ("R2", "R1", "R3", "R1"),
    "piedra": ("g", "d", "l", "x"),
    "madera": ("M3", "M2", "M4", "M1"),
    "cal": ("w", "l", "W", "g"),
    "chapa": ("d", "x", "g", "x"),
    "colonial": ("W", "l", "W", "E2"),
    "hormigon": ("l", "g", "w", "d"),
    "vidrio": ("C3", "C2", "C4", "C1"),
    "verde": ("G2", "G1", "G3", "G1"),
    "celeste": ("C3", "C2", "C4", "C1"),
    "amarillo": ("Y2", "Y1", "Y3", "Y1"),
    "rojo": ("R2", "R1", "R3", "R1"),
    "crema": ("E1", "E2", "w", "S2"),
    "bordo": ("R1", "o", "R2", "o"),
}


def wall(cv, x, y, w, h, kind):
    b, s, l, d = WALLS[kind]
    cv.rect(x, y, w, h, b)
    if kind == "ladrillo":
        for j, yy in enumerate(range(y + 2, y + h, 4)):
            cv.hline(x, yy, w, s)
            for xx in range(x + (j % 2) * 4, x + w, 8):
                cv.put(xx, yy + 1, s)
                cv.put(xx, yy + 2, s)
                cv.put(xx + 1, yy + 1, l)
    elif kind == "adobe":
        for j, yy in enumerate(range(y + 3, y + h, 6)):
            cv.hline(x, yy, w, s)
            for xx in range(x + (j % 2) * 5, x + w, 11):
                cv.vline(xx, yy + 1, 5, s)
        for xx in range(x + 3, x + w, 13):
            cv.put(xx, y + (xx * 7) % max(1, h - 2) + 1, d)
    elif kind == "piedra":
        for j, yy in enumerate(range(y + 1, y + h, 5)):
            off = (j * 5) % 9
            for xx in range(x + off, x + w, 9):
                cv.rect(xx, yy, 7, 3, l if (xx + yy) % 3 else b)
                cv.hline(xx, yy + 3, 8, s)
                cv.put(xx + 7, yy + 1, s)
    elif kind == "madera":
        for xx in range(x + 3, x + w, 5):
            cv.vline(xx, y, h, s)
            cv.put(xx - 2, y + (xx * 3) % max(1, h), d)
    elif kind == "chapa":
        for xx in range(x + 1, x + w, 3):
            cv.vline(xx, y, h, l if xx % 6 == 1 else s)
    elif kind == "vidrio":
        for xx in range(x, x + w, 12):
            cv.vline(xx, y, h, "x")
        for yy in range(y, y + h, 10):
            cv.hline(x, yy, w, "x")
        for xx in range(x + 2, x + w - 3, 12):
            for yy in range(y + 2, y + h - 3, 10):
                cv.put(xx, yy, "W")
                cv.put(xx + 1, yy + 1, "W")
    elif kind in ("cal", "colonial", "hormigon", "crema"):
        for xx in range(x + 4, x + w - 2, 17):
            for yy in range(y + 5, y + h - 2, 13):
                cv.hline(xx + (yy // 13) % 3, yy, 3, s)
        if kind == "colonial":
            cv.rect(x, y + h - 8, w, 8, "E2")
            cv.hline(x, y + h - 8, w, "E1")
        if kind == "hormigon":
            for xx in range(x, x + w, 24):
                cv.vline(xx, y, h, s)
    else:
        for yy in range(y + 3, y + h, 7):
            for xx in range(x + (yy // 7 % 2) * 4, x + w - 2, 10):
                cv.hline(xx, yy, 3, s)
    cv.vline(x, y, h, l)
    cv.rect(x + w - 2, y, 2, h, s if kind != "colonial" else "l")


def roof(cv, x, y, w, kind, depth=10):
    """Techo apoyado sobre la pared cuyo borde superior está en y. Devuelve el y más alto."""
    if kind == "teja":
        for k in range(depth):
            yy = y - depth + k
            ww = w + 8 - (depth - k) * 2 if k < depth else w + 8
            xx = x - 4 + (depth - k)
            cv.hline(xx, yy, ww, "R2" if k % 3 else "R1")
            if k % 3 == 1:
                for sx in range(xx + (k // 3) % 2 * 2, xx + ww, 4):
                    cv.put(sx, yy, "R3")
        cv.hline(x - 4, y - 1, w + 8, "R1")
        return y - depth
    if kind == "paja":
        for k in range(depth):
            yy = y - depth + k
            xx = x - 5 + (depth - k) * 1
            ww = w + 10 - (depth - k) * 2
            cv.hline(xx, yy, ww, "Y2" if k % 2 else "Y1")
            for sx in range(xx, xx + ww, 3):
                cv.put(sx, yy + 1, "Y3" if (sx + k) % 2 else "M3")
        return y - depth
    if kind == "dos_aguas":
        half = w // 2 + 4
        for k in range(half // 2 + 1):
            cv.hline(x + w // 2 - k * 2, y - half // 2 + k, k * 4, "R2" if k % 2 else "R1")
        for k in range(half // 2 + 1):
            cv.put(x + w // 2 - k * 2, y - half // 2 + k, "R3")
        return y - half // 2
    if kind == "chapa":
        for k in range(depth):
            cv.hline(x - 3, y - depth + k, w + 6, "g" if k % 2 else "l")
        for xx in range(x - 3, x + w + 3, 4):
            cv.vline(xx, y - depth, depth, "d")
        cv.hline(x - 3, y - 1, w + 6, "x")
        return y - depth
    if kind == "curvo":
        for xx in range(x - 2, x + w + 2):
            t = (xx - x) / max(1, w)
            hh = int(depth * math.sin(math.pi * min(1.0, max(0.0, t))))
            cv.vline(xx, y - hh, hh + 1, "g" if xx % 4 else "d")
            cv.put(xx, y - hh, "l")
        return y - depth
    if kind == "dientes":
        for xx in range(x, x + w, 18):
            for k in range(9):
                cv.hline(xx + k, y - 9 + k, 18 - k * 2 if 18 - k * 2 > 0 else 0, "d")
                cv.put(xx + k, y - 9 + k, "l")
            cv.vline(xx + 17, y - 9, 9, "C4")
            cv.vline(xx + 16, y - 9, 9, "C3")
        return y - 9
    # plano con parapeto
    cv.rect(x - 2, y - 4, w + 4, 4, "l")
    cv.hline(x - 2, y - 4, w + 4, "W")
    cv.hline(x - 2, y - 1, w + 4, "g")
    return y - 4


def window(cv, x, y, w, h, style="simple", lit=False, color="G2"):
    glass_a, glass_b = ("Y4", "Y3") if lit else ("C4", "C3")
    if style == "arco":
        cv.rect(x - 1, y + 2, w + 2, h - 1, "M2")
        cv.ellipse(x + w // 2, y + 3, w // 2 + 1, 4, "M2")
        cv.rect(x, y + 3, w, h - 3, glass_a)
        cv.ellipse(x + w // 2, y + 3, w // 2, 3, glass_a)
        cv.rect(x, y + h // 2 + 2, w, h - h // 2 - 3, glass_b)
        cv.vline(x + w // 2, y, h, "M2")
    elif style == "vitrina":
        cv.rect(x - 2, y - 2, w + 4, h + 4, "x")
        cv.rect(x, y, w, h, glass_a)
        cv.rect(x, y + h // 2, w, h - h // 2, glass_b)
        for i in range(0, min(w, h) - 2, 3):
            cv.put(x + 3 + i, y + h - 3 - i, "W")
        cv.hline(x - 2, y + h + 2, w + 4, "l")
        return
    elif style == "industrial":
        cv.rect(x - 1, y - 1, w + 2, h + 2, "x")
        cv.rect(x, y, w, h, glass_a)
        for xx in range(x + 3, x + w, 4):
            cv.vline(xx, y, h, "x")
        cv.hline(x, y + h // 2, w, "x")
        return
    else:
        cv.rect(x - 1, y - 1, w + 2, h + 2, "M2" if style != "reja" else "x")
        cv.rect(x, y, w, h, glass_a)
        cv.rect(x, y + h // 2, w, h - h // 2, glass_b)
        cv.put(x + 1, y + 1, "W")
        cv.vline(x + w // 2, y, h, "M2" if style != "reja" else "x")
        if style == "reja":
            for xx in range(x + 1, x + w, 3):
                cv.vline(xx, y, h, "o")
    if style == "postigos":
        s, m, l, _ = RAMP.get({"G2": "verde", "C2": "celeste", "R2": "rojo", "M3": "madera", "Y2": "amarillo"}.get(color, "verde"))
        for sx in (x - 5, x + w + 1):
            cv.rect(sx, y - 1, 4, h + 2, m)
            for yy in range(y, y + h, 3):
                cv.hline(sx, yy, 4, s)
            cv.vline(sx, y - 1, h + 2, l)
    cv.rect(x - 2, y + h + 1, w + 4, 2, "l")      # alféizar
    cv.hline(x - 2, y + h + 2, w + 4, "g")


def door(cv, x, w, h, style="madera"):
    y = G - h + 1
    if style == "porton":
        cv.rect(x, y, w, h, "M2")
        cv.frame(x, y, w, h, "M1")
        for k in range(min(w, h)):
            cv.put(x + k * w // max(1, h), y + k, "M1")
            cv.put(x + w - 1 - k * w // max(1, h), y + k, "M1")
        cv.vline(x + w // 2, y, h, "M1")
        return
    if style == "persiana":
        cv.rect(x, y, w, h, "g")
        for yy in range(y, y + h, 3):
            cv.hline(x, yy, w, "d")
        cv.frame(x - 1, y - 1, w + 2, h + 1, "x")
        return
    if style == "vidrio":
        cv.rect(x, y, w, h, "x")
        cv.rect(x + 2, y + 2, w - 4, h - 2, "C4")
        cv.rect(x + 2, y + h // 2, w - 4, h // 2 - 1, "C3")
        cv.vline(x + w // 2, y, h, "x")
        return
    if style == "arco":
        cv.rect(x, y + 4, w, h - 4, "M1")
        cv.ellipse(x + w // 2, y + 5, w // 2, 5, "M1")
        cv.rect(x + 2, y + 6, w - 4, h - 6, "M2")
        cv.vline(x + w // 2, y + 3, h - 3, "M1")
        cv.put(x + w // 2 - 3, y + h // 2 + 2, "Y2")
        return
    cv.rect(x, y, w, h, "M2")
    cv.frame(x, y, w, h, "M1")
    for yy in range(y + 4, y + h - 2, 6):
        cv.rect(x + 2, yy, w - 4, 4, "M3")
    cv.put(x + w - 4, y + h // 2, "Y2")


def post_sign(cv, x, label, bg="M3", fg="W", h=26):
    tw = text_width(label)
    cv.vline(x + 2, G - h, h, "M1")
    cv.vline(x + tw + 3, G - h, h, "M1")
    cv.rect(x, G - h - 9, tw + 6, 10, bg)
    cv.frame(x, G - h - 9, tw + 6, 10, "M1")
    text(cv, label, x + 3, G - h - 7, fg)


def neon_sign(cv, cx, y, label, f, colors=("R3", "Y3")):
    tw = text_width(label)
    cv.rect(cx - tw // 2 - 5, y - 3, tw + 10, 13, "o")
    cv.frame(cx - tw // 2 - 4, y - 2, tw + 8, 11, colors[f % 2])
    text(cv, label, cx - tw // 2, y, colors[(f + 1) % 2] if f else "W", "u")
    for k in range(3):
        cv.vline(cx - tw // 2 - 2 + k * (tw // 2 + 2), y + 10, 4, "x")


def chimney(cv, x, y, h, f, brick=True):
    cv.rect(x, y - h, 7, h, "R1" if brick else "d")
    for yy in range(y - h + 2, y, 4):
        cv.hline(x, yy, 7, "R2" if brick else "g")
    cv.rect(x - 1, y - h - 2, 9, 2, "x")
    smoke(cv, x + 2, y - h - 6, f)


def flag(cv, x, y, f, colors=("C3", "W", "C3")):
    cv.vline(x, y, 34, "l")
    cv.put(x, y - 1, "Y2")
    for j, c in enumerate(colors):
        for i in range(16):
            dy = 1 if ((i + f * 3) // 4) % 2 else 0
            cv.put(x + 1 + i, y + 1 + j * 3 + dy, c)
            cv.put(x + 1 + i, y + 2 + j * 3 + dy, c)
    if colors == ("C3", "W", "C3"):
        cv.put(x + 8, y + 5, "Y2")


def lights(cv, x1, x2, y, f, sag=5):
    for xx in range(x1, x2):
        t = (xx - x1) / max(1, x2 - x1)
        yy = y + int(sag * math.sin(math.pi * t))
        cv.put(xx, yy, "x")
        if (xx - x1) % 6 == 3:
            cv.put(xx, yy + 1, ("Y3", "R3", "C4", "G3")[((xx - x1) // 6 + f) % 4])


def planter(cv, x, w=10, flower="R3"):
    cv.rect(x, G - 5, w, 5, "M2")
    cv.hline(x, G - 5, w, "M3")
    for xx in range(x + 1, x + w - 1, 2):
        cv.put(xx, G - 6, "G2")
        cv.put(xx, G - 7, flower if xx % 4 == 1 else "G3")


def bench(cv, x):
    cv.rect(x, G - 7, 16, 2, "M3")
    cv.rect(x, G - 11, 16, 2, "M3")
    cv.vline(x + 2, G - 5, 5, "x")
    cv.vline(x + 13, G - 5, 5, "x")


def crates(cv, x, n, fill=("R2", "Y2", "G2"), stack=1):
    for s in range(stack):
        for i in range(max(1, n - s)):
            cx, cy = x + i * 13 + s * 6, G - 10 - s * 10
            cv.rect(cx, cy, 12, 10, "M3")
            cv.hline(cx, cy, 12, "M4")
            cv.hline(cx, cy + 5, 12, "M2")
            cv.frame(cx, cy, 12, 10, "M1")
            for k in range(3):
                cv.rect(cx + 1 + k * 4, cy - 2, 3, 2, fill[(k + i) % len(fill)])


def sacks(cv, x, n, color="E1", mark="R2", stack=1):
    for s in range(stack):
        for i in range(max(1, n - s)):
            sx, sy = x + i * 10 + s * 5, G - 12 - s * 10
            cv.rect(sx, sy + 2, 10, 10, color)
            cv.rect(sx + 2, sy, 6, 3, color)
            cv.hline(sx + 2, sy + 2, 6, "M2")
            cv.vline(sx, sy + 3, 8, "W")
            cv.rect(sx + 3, sy + 6, 4, 3, mark)


def bales(cv, x, n, color="W", band="g", stack=1):
    for s in range(stack):
        for i in range(max(1, n - s)):
            bx, by = x + i * 14 + s * 7, G - 11 - s * 11
            cv.rect(bx, by, 13, 11, color)
            cv.vline(bx, by, 11, "W")
            cv.vline(bx + 4, by, 11, band)
            cv.vline(bx + 9, by, 11, band)
            cv.put(bx + 2, by + 3, "l")
            cv.put(bx + 7, by + 7, "l")


def barrels(cv, x, n, stack=1, wood=True):
    for s in range(stack):
        for i in range(max(1, n - s)):
            bx, by = x + i * 12 + s * 6, G - 11 - s * 10
            body, hi = ("M2", "M3") if wood else ("C2", "C3")
            cv.ellipse(bx + 5, by + 5, 5, 5, body)
            cv.ellipse(bx + 4, by + 4, 3, 3, hi)
            cv.vline(bx + 2, by + 1, 9, "x")
            cv.vline(bx + 8, by + 1, 9, "x")
            cv.put(bx + 5, by + 5, "M1" if wood else "C1")


def bottles(cv, x, n, color="R1"):
    cv.rect(x - 2, G - 4, n * 5 + 3, 4, "M3")
    for i in range(n):
        bx = x + i * 5
        cv.rect(bx, G - 14, 3, 10, color)
        cv.rect(bx + 1, G - 17, 1, 3, color)
        cv.put(bx, G - 12, "W")
        cv.rect(bx, G - 10, 3, 2, "E1")


def fruit_pile(cv, x, w, color, shade):
    for row in range(3):
        for xx in range(x + row * 3, x + w - row * 3, 4):
            cv.ellipse(xx + 1, G - 3 - row * 3, 2, 2, shade)
            cv.put(xx, G - 4 - row * 3, color)


def stall(cv, x, w, roof_ramp, f, goods=None, label=None):
    """Puestito de feria: mesa, toldo a rayas y mercadería."""
    cv.rect(x, G - 16, w, 3, "M3")
    cv.hline(x, G - 16, w, "M4")
    cv.rect(x + 1, G - 13, w - 2, 13, "M2")
    for xx in range(x + 2, x + w - 2, 6):
        cv.vline(xx, G - 13, 13, "M1")
    cv.vline(x + 1, G - 44, 28, "x")
    cv.vline(x + w - 2, G - 44, 28, "x")
    awning(cv, x - 4, G - 48, w + 8, roof_ramp, f, 9)
    if goods:
        goods(cv, x + 3, G - 16)
    if label:
        tw = text_width(label)
        cv.rect(x + w // 2 - tw // 2 - 3, G - 60, tw + 6, 10, "E1")
        cv.frame(x + w // 2 - tw // 2 - 3, G - 60, tw + 6, 10, "M2")
        text(cv, label, x + w // 2 - tw // 2, G - 58, "R1", "E2")


def tractor(cv, x, color="R2", f=0):
    s, m, l, _ = RAMP.get({"R2": "rojo", "G2": "verde", "Y2": "amarillo", "C2": "celeste"}[color])
    cv.rect(x + 4, G - 20, 22, 9, m)
    cv.hline(x + 4, G - 20, 22, l)
    cv.rect(x + 16, G - 32, 12, 13, m)
    cv.rect(x + 18, G - 30, 8, 7, "C4")
    cv.rect(x + 15, G - 34, 14, 2, s)
    cv.rect(x + 6, G - 27, 3, 7, "x")
    if f:
        smoke(cv, x + 6, G - 31, f)
    cv.ellipse(x + 23, G - 8, 8, 8, "o")
    cv.ellipse(x + 23, G - 8, 4, 4, "Y2")
    cv.ellipse(x + 7, G - 5, 5, 5, "o")
    cv.ellipse(x + 7, G - 5, 2, 2, "Y2")


def pickup(cv, x, color="C2", f=0, cargo=None):
    ramp = {"C2": "celeste", "R2": "rojo", "G2": "verde", "Y2": "amarillo", "d": "gris", "W": "blanco"}[color]
    s, m, l, _ = RAMP[ramp]
    cv.rect(x, G - 16, 40, 9, m)
    cv.hline(x, G - 16, 40, l)
    cv.rect(x + 24, G - 25, 14, 10, m)
    cv.rect(x + 26, G - 23, 10, 6, "C4")
    cv.put(x + 27, G - 22, "W")
    cv.rect(x + 38, G - 13, 2, 3, "Y3")
    if cargo:
        cargo(cv, x + 2, G - 16)
    for wx in (x + 8, x + 31):
        cv.ellipse(wx, G - 5, 5, 5, "o")
        cv.ellipse(wx, G - 5, 2, 2, "g")


def truck(cv, x, color="R2", label=None, f=0, box="W"):
    ramp = {"C2": "celeste", "R2": "rojo", "G2": "verde", "Y2": "amarillo", "d": "gris", "R1": "bordo"}[color]
    s, m, l, _ = RAMP[ramp]
    cv.rect(x, G - 34, 50, 26, box)
    cv.frame(x, G - 34, 50, 26, "g")
    cv.hline(x, G - 34, 50, "W")
    if label:
        tw = text_width(label)
        text(cv, label[:9], x + max(2, 25 - tw // 2), G - 25, s, "l")
    cv.rect(x + 51, G - 26, 18, 18, m)
    cv.hline(x + 51, G - 26, 18, l)
    cv.rect(x + 58, G - 24, 9, 7, "C4")
    cv.put(x + 59, G - 23, "W")
    cv.rect(x + 67, G - 13, 2, 3, "Y3")
    cv.rect(x, G - 8, 69, 3, "x")
    for wx in (x + 10, x + 22, x + 58):
        cv.ellipse(wx, G - 4, 5, 5, "o")
        cv.ellipse(wx, G - 4, 2, 2, "g")


def silo(cv, x, h, w=16):
    cv.rect(x, G - h + 1, w, h, "l")
    cv.vline(x + 1, G - h + 1, h, "W")
    cv.rect(x + w - 3, G - h + 1, 3, h, "g")
    for yy in range(G - h + 4, G, 5):
        cv.hline(x, yy, w, "g")
    cv.ellipse(x + w // 2, G - h, w // 2, 5, "d")
    cv.ellipse(x + w // 2 - 1, G - h - 1, w // 2 - 2, 3, "l")
    cv.vline(x + w + 1, G - h, h, "x")
    for yy in range(G - h, G, 4):
        cv.hline(x + w, yy, 3, "x")


def tank(cv, x, h, w=20, band="C2"):
    cv.rect(x, G - h + 1, w, h - 4, "W")
    cv.vline(x + 1, G - h + 1, h - 4, "W")
    cv.rect(x + w - 3, G - h + 1, 3, h - 4, "l")
    cv.ellipse(x + w // 2, G - h + 1, w // 2, 3, "l")
    cv.rect(x, G - h + 10, w, 4, band)
    for lx in (x + 2, x + w - 4):
        cv.rect(lx, G - 4, 2, 5, "x")


def water_tower(cv, x, f=0):
    for k in range(30):
        cv.put(x + 2 + k // 10, G - k, "x")
        cv.put(x + 16 - k // 10, G - k, "x")
    cv.rect(x, G - 46, 18, 16, "C2")
    cv.hline(x, G - 46, 18, "C3")
    cv.rect(x - 1, G - 48, 20, 2, "C1")


def greenhouse(cv, x, w, h):
    for xx in range(x, x + w):
        t = (xx - x) / max(1, w - 1)
        hh = int(h * math.sin(math.pi * t) * 0.6 + h * 0.4)
        cv.vline(xx, G - hh, hh, "C4" if xx % 6 else "l")
        cv.put(xx, G - hh, "W")
    for xx in range(x + 4, x + w - 3, 8):
        cv.ellipse(xx, G - 6, 3, 4, "G2")


def cactus(cv, x, h=26):
    cv.rect(x, G - h, 5, h, "G1")
    cv.vline(x + 1, G - h, h, "G2")
    cv.rect(x - 5, G - h + 10, 5, 3, "G1")
    cv.rect(x - 5, G - h + 2, 3, 8, "G1")
    cv.rect(x + 5, G - h + 14, 5, 3, "G1")
    cv.rect(x + 7, G - h + 6, 3, 8, "G1")


def horse(cv, x, f=0, color="M2"):
    cv.rect(x, G - 16, 18, 8, color)
    cv.rect(x + 16, G - 24 + f % 2, 5, 10, color)
    cv.rect(x + 19, G - 25 + f % 2, 6, 4, color)
    cv.vline(x + 15, G - 24, 8, "o")
    cv.vline(x - 1, G - 15, 7, "o")
    for lx in (x + 2, x + 6, x + 12, x + 16):
        cv.vline(lx, G - 8, 9, "M1")


def antenna(cv, x, f=0):
    for k in range(48):
        cv.put(x - k // 12, G - k, "x")
        cv.put(x + k // 12, G - k, "x")
    for yy in range(G - 44, G, 8):
        cv.hline(x - (G - yy) // 12, yy, ((G - yy) // 12) * 2 + 1, "d")
    cv.put(x, G - 50, "R3" if f else "R1")
    cv.ellipse(x + 8, G - 34, 4, 4, "l")
    cv.put(x + 8, G - 34, "x")


def solar(cv, x, n=3):
    for i in range(n):
        px = x + i * 14
        cv.rect(px, G - 12, 12, 6, "C1")
        for xx in range(px + 3, px + 12, 3):
            cv.vline(xx, G - 12, 6, "C2")
        cv.hline(px, G - 12, 12, "C3")
        cv.vline(px + 6, G - 6, 6, "x")


def snow_roof(cv, x, y, w):
    cv.hline(x - 3, y - 1, w + 6, "W")
    for xx in range(x - 2, x + w + 2, 5):
        cv.put(xx, y, "W")
        cv.put(xx + 1, y + 1, "W")


def arches(cv, x, y, w, h, n):
    """Galería de arcos (colonial / estancia)."""
    aw = w // n
    for i in range(n):
        ax = x + i * aw + 2
        cv.rect(ax, y + 6, aw - 4, h - 6, "u")
        cv.ellipse(ax + (aw - 4) // 2, y + 6, (aw - 4) // 2, 5, "u")
        cv.rect(ax + 1, y + h - 4, aw - 6, 4, "x")
    for i in range(n + 1):
        cv.rect(x + i * aw - 1, y, 3, h, "W")


def fileteado(cv, x, y, w, label, f):
    """Cartel porteño con fileteado: fondo negro, borde dorado y volutas."""
    tw = text_width(label)
    cv.rect(x, y, w, 15, "o")
    cv.frame(x + 1, y + 1, w - 2, 13, "Y2")
    for k in range(4):
        cv.put(x + 4 + k, y + 11 - k, "R2")
        cv.put(x + w - 5 - k, y + 11 - k, "R2")
        cv.put(x + 4 + k, y + 3 + k, "G3")
        cv.put(x + w - 5 - k, y + 3 + k, "G3")
    text(cv, label, x + (w - tw) // 2, y + 4, "Y4" if f else "Y3", "R1")


def done(cv):
    cv.outline()
    return cv


def C():
    return Canvas(W, H)


# =================================================================== NOA

def algodonal(t, f):
    cv = C()
    soil(cv, 0, W, "M2", "M3", 6)
    if t == 0:
        crop(cv, 4, 90, "algodon", 2, f)
        stall(cv, 112, 46, "amarillo", f, lambda c, x, y: bales(c, x + 2, 2), "ALGODÓN")
    elif t == 1:
        crop(cv, 2, 70, "algodon", 3, f)
        wall(cv, 86, G - 38, 62, 39, "adobe")
        roof(cv, 86, G - 38, 62, "paja", 9)
        door(cv, 96, 14, 26)
        window(cv, 120, G - 30, 14, 12, "postigos", color="C2")
        post_sign(cv, 150, "ALGODÓN", "Y2", "M1")
        bales(cv, 150, 1)
    elif t == 2:
        crop(cv, 2, 56, "algodon", 3, f)
        wall(cv, 62, G - 48, 80, 49, "madera")
        roof(cv, 62, G - 48, 80, "curvo", 14)
        door(cv, 84, 34, 34, "porton")
        bales(cv, 146, 3, stack=2)
        tractor(cv, 4, "R2", f)
        sign(cv, 102, G - 76, "ALGODONERA", "madera")
    elif t == 3:
        wall(cv, 4, G - 56, 92, 57, "chapa")
        roof(cv, 4, G - 56, 92, "dientes")
        for xx in range(12, 86, 16):
            window(cv, xx, G - 46, 10, 10, "industrial")
        door(cv, 36, 28, 30, "persiana")
        chimney(cv, 80, G - 56, 18, f)
        sign(cv, 50, G - 84, "DESMOTADORA", "noche")
        bales(cv, 100, 4, stack=3)
        crop(cv, 158, 34, "algodon", 2, f)
    else:
        wall(cv, 18, G - 70, 120, 71, "hormigon")
        roof(cv, 18, G - 70, 120, "dientes")
        for xx in range(26, 130, 14):
            window(cv, xx, G - 60, 9, 12, "industrial", lit=(xx // 14 + f) % 2 == 0)
        door(cv, 64, 30, 34, "persiana")
        neon_sign(cv, 78, G - 92, "TEXTIL SANTIAGO", f)
        silo(cv, 142, 74)
        silo(cv, 160, 64)
        bales(cv, 2, 1, stack=1)
        flag(cv, 6, G - 60, f)
    return done(cv)


def papas_andinas(t, f):
    cv = C()
    soil(cv, 0, W, "M2", "M3", 6)
    if t == 0:
        crop(cv, 6, 80, "papa", 2, f)
        stall(cv, 104, 52, "rojo", f, lambda c, x, y: [c.ellipse(x + 4 + i * 7, y - 2, 3, 2, ["R2", "u", "M3", "Y2", "Q", "R1"][i]) for i in range(6)], "PAPAS")
        llama(cv, 168, f)
    elif t == 1:
        wall(cv, 70, G - 40, 66, 41, "adobe")
        roof(cv, 70, G - 40, 66, "plano")
        door(cv, 80, 16, 28, "madera")
        window(cv, 108, G - 32, 16, 12, "reja")
        crop(cv, 4, 60, "quinoa", 2, f)
        llama(cv, 146, f)
        llama(cv, 170, f + 1)
        post_sign(cv, 4, "PAPA ANDINA", "R2")
    elif t == 2:
        wall(cv, 40, G - 46, 96, 47, "piedra")
        roof(cv, 40, G - 46, 96, "paja", 12)
        door(cv, 56, 18, 30, "arco")
        window(cv, 88, G - 36, 14, 12, "postigos", color="R2")
        window(cv, 112, G - 36, 14, 12, "postigos", color="R2")
        sacks(cv, 140, 3, "E1", "u", 2)
        llama(cv, 6, f)
        crop(cv, 2, 34, "papa", 1, f)
        sign(cv, 88, G - 76, "PAPAS ANDINAS", "bordo")
    elif t == 3:
        wall(cv, 8, G - 50, 70, 51, "adobe")
        roof(cv, 8, G - 50, 70, "teja", 10)
        arches(cv, 12, G - 34, 62, 34, 3)
        wall(cv, 86, G - 56, 70, 57, "madera")
        roof(cv, 86, G - 56, 70, "curvo", 12)
        door(cv, 104, 30, 34, "porton")
        sacks(cv, 158, 3, "E1", "R2", 3)
        sign(cv, 120, G - 84, "COOPERATIVA", "bordo")
    else:
        wall(cv, 20, G - 62, 140, 63, "colonial")
        roof(cv, 20, G - 62, 140, "teja", 12)
        arches(cv, 26, G - 40, 128, 40, 6)
        for xx in (34, 66, 98, 130):
            window(cv, xx, G - 56, 12, 10, "postigos", lit=f == 0, color="C2")
        neon_sign(cv, 90, G - 90, "PAPAS DE LA QUEBRADA", f)
        flag(cv, 4, G - 64, f)
        flag(cv, 170, G - 64, f + 1, ("R2", "Y2", "G2"))
    return done(cv)


def almazara(t, f):
    cv = C()
    soil(cv, 0, W, "S2", "E2", 6)
    if t == 0:
        for i in range(4):
            tree(cv, 12 + i * 18, "olivo", f, 0.9)
        stall(cv, 112, 50, "verde", f, lambda c, x, y: bottles(c, x + 4, 6, "Y2"), "ACEITE")
    elif t == 1:
        for i in range(3):
            tree(cv, 10 + i * 18, "olivo", f, 1.0)
        wall(cv, 74, G - 42, 70, 43, "cal")
        roof(cv, 74, G - 42, 70, "teja", 10)
        door(cv, 84, 16, 28, "arco")
        window(cv, 110, G - 34, 16, 14, "reja")
        bottles(cv, 150, 6, "Y2")
        sign(cv, 109, G - 64, "ACEITE DE OLIVA", "verde")
    elif t == 2:
        for i in range(2):
            tree(cv, 10 + i * 18, "olivo", f, 1.1)
        wall(cv, 48, G - 52, 100, 53, "piedra")
        roof(cv, 48, G - 52, 100, "teja", 11)
        door(cv, 64, 26, 34, "porton")
        window(cv, 100, G - 42, 14, 12, "postigos", color="G2")
        window(cv, 124, G - 42, 14, 12, "postigos", color="G2")
        barrels(cv, 152, 3, 2)
        sign(cv, 98, G - 78, "ALMAZARA", "verde")
    elif t == 3:
        wall(cv, 6, G - 56, 96, 57, "cal")
        roof(cv, 6, G - 56, 96, "chapa", 8)
        for xx in range(14, 94, 16):
            window(cv, xx, G - 48, 10, 10, "industrial")
        door(cv, 40, 30, 32, "persiana")
        tank(cv, 108, 62)
        tank(cv, 130, 56, band="G2")
        tank(cv, 152, 50, band="Y2")
        sign(cv, 54, G - 80, "ACEITES DEL VALLE", "verde")
    else:
        wall(cv, 14, G - 66, 110, 67, "colonial")
        roof(cv, 14, G - 66, 110, "teja", 12)
        arches(cv, 20, G - 44, 98, 44, 4)
        neon_sign(cv, 70, G - 94, "OLIVA CATAMARCA", f, ("G3", "Y3"))
        tank(cv, 128, 74, 22, "G2")
        tank(cv, 152, 66, 22, "Y2")
        for i in range(2):
            tree(cv, 6 + i * 172, "olivo", f, 1.0)
    return done(cv)


def olivar(t, f):
    cv = C()
    soil(cv, 0, W, "E2", "S2", 6)
    if t == 0:
        for i in range(3):
            tree(cv, 14 + i * 22, "olivo", f, 0.8)
        stall(cv, 104, 56, "verde", f, lambda c, x, y: [c.rect(x + 2 + i * 9, y - 8, 7, 8, "C3") or c.rect(x + 3 + i * 9, y - 6, 5, 5, "G1") for i in range(5)], "ACEITUNAS")
    elif t == 1:
        for r in range(2):
            for i in range(4):
                tree(cv, 8 + i * 22 + r * 10, "olivo", f, 0.8 + r * 0.15)
        wall(cv, 110, G - 36, 60, 37, "cal")
        roof(cv, 110, G - 36, 60, "dos_aguas")
        door(cv, 132, 16, 26)
        post_sign(cv, 94, "OLIVAR", "G1")
    elif t == 2:
        vines(cv, 2, 70, 1, f)
        wall(cv, 80, G - 50, 90, 51, "adobe")
        roof(cv, 80, G - 50, 90, "teja", 10)
        door(cv, 92, 22, 32, "arco")
        window(cv, 124, G - 40, 12, 12, "postigos", color="G2")
        window(cv, 146, G - 40, 12, 12, "postigos", color="G2")
        sign(cv, 125, G - 74, "FINCA FAMATINA", "verde")
    elif t == 3:
        for i in range(3):
            tree(cv, 10 + i * 18, "olivo", f, 1.1)
        wall(cv, 64, G - 54, 110, 55, "madera")
        roof(cv, 64, G - 54, 110, "curvo", 14)
        door(cv, 96, 34, 34, "porton")
        for i in range(5):
            cv.rect(138 + i * 7, G - 14, 6, 14, "C3")
            cv.rect(138 + i * 7, G - 16, 6, 2, "G1")
            cv.put(139 + i * 7, G - 9, "G2")
        sign(cv, 118, G - 84, "ACEITUNERA", "verde")
    else:
        wall(cv, 30, G - 64, 130, 65, "crema")
        roof(cv, 30, G - 64, 130, "plano")
        wall(cv, 70, G - 84, 50, 21, "crema")
        roof(cv, 70, G - 84, 50, "teja", 8)
        for xx in range(40, 150, 20):
            window(cv, xx, G - 52, 12, 14, "arco", lit=(xx // 20 + f) % 2 == 0)
        door(cv, 86, 20, 30, "arco")
        neon_sign(cv, 95, G - 108, "RIOJA OLIVA", f, ("G3", "Y3"))
        flag(cv, 6, G - 66, f)
        tree(cv, 176, "olivo", f, 1.0)
    return done(cv)


def bodega_torrontes(t, f):
    cv = C()
    soil(cv, 0, W, "M3", "S2", 6)
    if t == 0:
        vines(cv, 4, 90, 1, f, grape="Y3")
        stall(cv, 112, 50, "bordo", f, lambda c, x, y: bottles(c, x + 4, 6, "G1"), "VINO")
    elif t == 1:
        vines(cv, 2, 76, 2, f, grape="Y3")
        wall(cv, 88, G - 42, 72, 43, "adobe")
        roof(cv, 88, G - 42, 72, "paja", 10)
        door(cv, 100, 16, 28, "arco")
        window(cv, 128, G - 32, 14, 12, "reja")
        barrels(cv, 162, 2)
    elif t == 2:
        vines(cv, 2, 60, 2, f, grape="Y3")
        wall(cv, 66, G - 52, 106, 53, "colonial")
        roof(cv, 66, G - 52, 106, "teja", 10)
        arches(cv, 72, G - 36, 94, 36, 4)
        sign(cv, 119, G - 76, "BODEGA DE ALTURA", "bordo")
    elif t == 3:
        vines(cv, 2, 50, 2, f, grape="Y3")
        wall(cv, 56, G - 60, 120, 61, "colonial")
        roof(cv, 56, G - 60, 120, "teja", 11)
        cv.rect(100, G - 82, 30, 22, "W")
        roof(cv, 100, G - 82, 30, "teja", 7)
        cv.ellipse(115, G - 72, 4, 4, "M2")
        arches(cv, 62, G - 38, 108, 38, 5)
        barrels(cv, 2, 3, 2)
        sign(cv, 115, G - 104, "TORRONTÉS", "bordo")
    else:
        wall(cv, 12, G - 66, 168, 67, "colonial")
        roof(cv, 12, G - 66, 168, "teja", 12)
        arches(cv, 18, G - 42, 156, 42, 7)
        for xx in range(24, 170, 24):
            window(cv, xx, G - 60, 10, 10, "postigos", lit=f == 0, color="R2")
        neon_sign(cv, 96, G - 94, "BODEGAS CAFAYATE", f, ("Y3", "R3"))
        flag(cv, 4, G - 68, f)
        flag(cv, 170, G - 68, f + 1, ("R1", "W", "R1"))
    return done(cv)


def citricola(t, f):
    cv = C()
    soil(cv, 0, W, "G1", "G2", 6)
    if t == 0:
        for i in range(4):
            tree(cv, 12 + i * 18, "limon", f, 0.9)
        stall(cv, 110, 54, "amarillo", f, lambda c, x, y: fruit_pile(c, x + 2, 46, "Y3", "Y2"), "LIMONES")
    elif t == 1:
        for i in range(3):
            tree(cv, 10 + i * 18, "limon", f, 1.0)
        wall(cv, 70, G - 40, 76, 41, "amarillo")
        roof(cv, 70, G - 40, 76, "teja", 9)
        window(cv, 80, G - 32, 30, 18, "vitrina")
        door(cv, 118, 16, 28, "vidrio")
        crates(cv, 150, 3, ("Y3", "Y2", "G3"), 2)
        sign(cv, 108, G - 62, "JUGOS", "verde")
    elif t == 2:
        for i in range(2):
            tree(cv, 8 + i * 18, "limon", f, 1.1)
        wall(cv, 46, G - 50, 100, 51, "verde")
        roof(cv, 46, G - 50, 100, "curvo", 13)
        door(cv, 70, 34, 32, "porton")
        crates(cv, 112, 3, ("Y3", "Y2", "G3"), 3)
        pickup(cv, 148, "Y2", f, lambda c, x, y: [c.rect(x + 2 + i * 6, y - 4, 5, 4, "Y3") for i in range(3)])
        sign(cv, 96, G - 80, "CITRUS TUCUMÁN", "verde")
    elif t == 3:
        wall(cv, 4, G - 58, 100, 59, "hormigon")
        roof(cv, 4, G - 58, 100, "dientes")
        for xx in range(12, 96, 14):
            window(cv, xx, G - 48, 9, 10, "industrial")
        door(cv, 38, 30, 32, "persiana")
        tank(cv, 108, 66, 22, "Y2")
        tank(cv, 132, 58, 22, "G2")
        chimney(cv, 158, G, 70, f)
        sign(cv, 54, G - 84, "JUGOS DEL NORTE", "amarillo")
    else:
        wall(cv, 10, G - 72, 130, 73, "vidrio")
        roof(cv, 10, G - 72, 130, "plano")
        cv.rect(10, G - 24, 130, 24, "Y2")
        cv.hline(10, G - 24, 130, "Y3")
        door(cv, 62, 26, 24, "vidrio")
        neon_sign(cv, 75, G - 94, "CITRÍCOLA ACONQUIJA", f, ("Y3", "G3"))
        tank(cv, 146, 80, 22, "Y2")
        tank(cv, 168, 70, 20, "G2")
    return done(cv)


# =================================================================== NEA

def bananal(t, f):
    cv = C()
    water(cv, 0, W, f)
    soil(cv, 0, 150, "G1", "G2", 5)
    if t == 0:
        for i in range(4):
            tree(cv, 12 + i * 16, "banana", f, 1.0)
        stall(cv, 104, 50, "amarillo", f, lambda c, x, y: [c.rect(x + 2 + i * 9, y - 6, 7, 6, "Y3") or c.put(x + 2 + i * 9, y - 6, "Y1") for i in range(5)], "BANANAS")
    elif t == 1:
        for i in range(4):
            tree(cv, 8 + i * 15, "banana", f, 1.1)
        wall(cv, 80, G - 36, 64, 37, "madera")
        roof(cv, 80, G - 36, 64, "paja", 12)
        cv.rect(78, G - 40, 4, 40, "M1")
        cv.rect(142, G - 40, 4, 40, "M1")
        door(cv, 100, 16, 26)
        crates(cv, 148, 2, ("Y3", "Y2"), 2)
    elif t == 2:
        for i in range(3):
            tree(cv, 8 + i * 15, "banana", f, 1.2)
        wall(cv, 58, G - 46, 92, 47, "madera")
        roof(cv, 58, G - 46, 92, "chapa", 9)
        door(cv, 76, 30, 30, "porton")
        for i in range(3):
            cv.vline(122 + i * 8, G - 40, 6, "M1")
            cv.rect(119 + i * 8, G - 34, 7, 12, "G2")
            cv.rect(120 + i * 8, G - 28, 5, 6, "Y3")
        pickup(cv, 150, "G2", f)
        sign(cv, 104, G - 72, "BANANAS FORMOSA", "verde")
    elif t == 3:
        for i in range(2):
            tree(cv, 8 + i * 15, "banana", f, 1.2)
        wall(cv, 44, G - 54, 104, 55, "celeste")
        roof(cv, 44, G - 54, 104, "curvo", 14)
        door(cv, 72, 40, 34, "persiana")
        crates(cv, 150, 3, ("Y3", "Y2", "G3"), 3)
        sign(cv, 96, G - 84, "EMPAQUE DEL RÍO", "celeste")
    else:
        wall(cv, 20, G - 66, 120, 67, "verde")
        roof(cv, 20, G - 66, 120, "dientes")
        for xx in range(30, 130, 14):
            window(cv, xx, G - 56, 9, 10, "industrial", lit=(xx // 14 + f) % 2 == 0)
        door(cv, 64, 30, 32, "persiana")
        neon_sign(cv, 80, G - 92, "BANANERA DEL NORTE", f, ("Y3", "G3"))
        water_tower(cv, 150, f)
        tree(cv, 6, "banana", f, 1.2)
        cv.rect(148, G - 7, 44, 5, "M3")
        cv.hline(148, G - 7, 44, "M4")
    return done(cv)


def desmotadora(t, f):
    cv = C()
    soil(cv, 0, W, "M2", "S3", 6)
    if t == 0:
        tree(cv, 14, "nogal", f, 1.3)
        cv.rect(70, G - 22, 50, 12, "M3")
        cv.frame(70, G - 22, 50, 12, "M1")
        bales(cv, 70 + 4, 3)
        for wx in (70 + 10, 70 + 40):
            cv.ellipse(wx, G - 6, 6, 6, "M1")
            cv.ellipse(wx, G - 6, 2, 2, "M3")
        post_sign(cv, 140, "ALGODÓN", "W", "M1")
    elif t == 1:
        wall(cv, 40, G - 44, 90, 45, "ladrillo")
        roof(cv, 40, G - 44, 90, "chapa", 8)
        door(cv, 56, 26, 30, "porton")
        window(cv, 96, G - 34, 20, 12, "reja")
        bales(cv, 134, 4, stack=2)
        sign(cv, 85, G - 66, "ALGODONERA", "noche")
    elif t == 2:
        wall(cv, 14, G - 54, 110, 55, "chapa")
        roof(cv, 14, G - 54, 110, "curvo", 14)
        door(cv, 50, 40, 36, "persiana")
        silo(cv, 132, 60)
        silo(cv, 152, 52)
        sign(cv, 69, G - 82, "DESMOTADORA", "noche")
    elif t == 3:
        wall(cv, 4, G - 60, 120, 61, "ladrillo")
        roof(cv, 4, G - 60, 120, "dientes")
        for xx in range(12, 116, 16):
            window(cv, xx, G - 50, 10, 12, "industrial")
        door(cv, 44, 30, 34, "persiana")
        chimney(cv, 104, G - 60, 24, f)
        silo(cv, 130, 70)
        silo(cv, 150, 64)
        silo(cv, 170, 58, 14)
        sign(cv, 60, G - 92, "HILADOS CHACO", "noche")
    else:
        wall(cv, 4, G - 74, 140, 75, "hormigon")
        roof(cv, 4, G - 74, 140, "dientes")
        for xx in range(12, 136, 14):
            window(cv, xx, G - 64, 9, 12, "industrial", lit=(xx // 14 + f) % 2 == 0)
        door(cv, 56, 34, 36, "persiana")
        neon_sign(cv, 74, G - 100, "TEXTIL IMPENETRABLE", f)
        silo(cv, 150, 84)
        silo(cv, 170, 76, 14)
    return done(cv)


def arrocera(t, f):
    cv = C()
    water(cv, 0, W, f)
    if t == 0:
        crop(cv, 4, 96, "arroz", 2, f)
        stall(cv, 112, 50, "celeste", f, lambda c, x, y: sacks(c, x + 2, 3, "W", "C3"), "ARROZ")
    elif t == 1:
        crop(cv, 2, 70, "arroz", 3, f)
        for k in range(4):
            cv.rect(88 + k * 22, G - 6, 3, 6, "M1")
        wall(cv, 86, G - 40, 70, 34, "madera")
        roof(cv, 86, G - 40, 70, "paja", 10)
        door(cv, 104, 14, 22)
        window(cv, 130, G - 32, 14, 10, "postigos", color="C2")
        tree(cv, 172, "naranja", f, 1.0)
    elif t == 2:
        crop(cv, 2, 52, "arroz", 3, f)
        wall(cv, 60, G - 50, 90, 51, "cal")
        roof(cv, 60, G - 50, 90, "teja", 10)
        door(cv, 74, 24, 32, "porton")
        window(cv, 110, G - 40, 14, 12, "postigos", color="C2")
        window(cv, 130, G - 40, 14, 12, "postigos", color="C2")
        silo(cv, 158, 58)
        sign(cv, 105, G - 74, "ARROZ IBERÁ", "celeste")
    elif t == 3:
        crop(cv, 2, 40, "arroz", 2, f)
        wall(cv, 44, G - 56, 96, 57, "chapa")
        roof(cv, 44, G - 56, 96, "curvo", 14)
        door(cv, 74, 34, 36, "persiana")
        for i in range(3):
            silo(cv, 142 + i * 16, 66 - i * 6, 14)
        sign(cv, 92, G - 84, "ARROCERA ESTEROS", "celeste")
    else:
        wall(cv, 14, G - 66, 110, 67, "celeste")
        roof(cv, 14, G - 66, 110, "plano")
        for xx in range(22, 116, 16):
            window(cv, xx, G - 56, 10, 12, "simple", lit=(xx // 16 + f) % 2 == 0)
        door(cv, 56, 26, 30, "vidrio")
        neon_sign(cv, 69, G - 88, "ARROZALES DEL IBERÁ", f, ("C4", "Y3"))
        for i in range(4):
            silo(cv, 128 + i * 15, 84 - i * 6, 13)
    return done(cv)


def molino_arrocero(t, f):
    cv = C()
    soil(cv, 0, W, "G1", "G2", 6)
    if t == 0:
        for i in range(3):
            tree(cv, 12 + i * 18, "naranja" if i % 2 else "limon", f, 0.9)
        stall(cv, 100, 60, "naranja", f, lambda c, x, y: fruit_pile(c, x + 2, 26, "Q", "Y1") or sacks(c, x + 32, 2, "W", "C3"), "MOLINO")
    elif t == 1:
        windmill(cv, 30, f)
        wall(cv, 70, G - 44, 70, 45, "piedra")
        roof(cv, 70, G - 44, 70, "dos_aguas")
        door(cv, 92, 22, 30, "porton")
        sacks(cv, 146, 3, "W", "C3", 2)
    elif t == 2:
        wall(cv, 30, G - 58, 80, 59, "ladrillo")
        roof(cv, 30, G - 58, 80, "dos_aguas")
        for xx in (42, 62, 82):
            window(cv, xx, G - 48, 10, 14, "arco")
        door(cv, 58, 24, 30, "porton")
        silo(cv, 120, 62)
        silo(cv, 140, 56)
        sign(cv, 70, G - 92, "MOLINO", "noche")
        tree(cv, 172, "naranja", f, 1.0)
    elif t == 3:
        wall(cv, 4, G - 64, 104, 65, "ladrillo")
        roof(cv, 4, G - 64, 104, "chapa", 8)
        for xx in range(12, 100, 16):
            window(cv, xx, G - 54, 10, 14, "arco")
        door(cv, 40, 30, 34, "porton")
        chimney(cv, 92, G - 64, 20, f)
        for i in range(3):
            silo(cv, 114 + i * 18, 76 - i * 6)
        sign(cv, 56, G - 94, "MOLINO ARROCERO", "noche")
    else:
        wall(cv, 4, G - 76, 116, 77, "ladrillo")
        roof(cv, 4, G - 76, 116, "teja", 12)
        cv.rect(46, G - 104, 32, 18, "R2")
        roof(cv, 46, G - 104, 32, "teja", 8)
        cv.ellipse(62, G - 96, 5, 5, "W")
        cv.vline(62, G - 99, 4, "o")
        cv.hline(62, G - 96, 3, "o")
        for xx in range(12, 112, 16):
            window(cv, xx, G - 66, 10, 14, "arco", lit=(xx // 16 + f) % 2 == 0)
        door(cv, 46, 32, 34, "arco")
        neon_sign(cv, 62, G - 126, "MOLINOS DEL LITORAL", f)
        for i in range(4):
            silo(cv, 124 + i * 16, 90 - i * 6, 14)
    return done(cv)


def yerbatal(t, f):
    cv = C()
    soil(cv, 0, W, "R1", "R2", 8)
    if t == 0:
        crop(cv, 2, 96, "yerba", 3, f)
        stall(cv, 108, 56, "verde", f, lambda c, x, y: sacks(c, x + 2, 4, "G2", "Y2"), "YERBA")
    elif t == 1:
        crop(cv, 2, 66, "yerba", 3, f)
        wall(cv, 78, G - 40, 72, 41, "madera")
        roof(cv, 78, G - 40, 72, "chapa", 8)
        door(cv, 92, 16, 28)
        window(cv, 120, G - 32, 16, 12, "postigos", color="G2")
        tree(cv, 166, "pino", f)
    elif t == 2:
        crop(cv, 2, 50, "yerba", 3, f)
        wall(cv, 58, G - 48, 100, 49, "ladrillo")
        roof(cv, 58, G - 48, 100, "curvo", 12)
        door(cv, 78, 28, 32, "porton")
        for yy in (G - 40, G - 30):
            cv.hline(120, yy, 34, "M3")
            for xx in range(121, 154, 3):
                cv.put(xx, yy - 1, "G2")
        chimney(cv, 146, G - 48, 16, f)
        sign(cv, 108, G - 76, "SECADERO", "verde")
    elif t == 3:
        crop(cv, 2, 36, "yerba", 2, f)
        wall(cv, 42, G - 58, 110, 59, "verde")
        roof(cv, 42, G - 58, 110, "dientes")
        for xx in range(50, 144, 14):
            window(cv, xx, G - 48, 9, 10, "industrial")
        door(cv, 80, 30, 32, "persiana")
        chimney(cv, 140, G - 58, 22, f)
        sacks(cv, 156, 3, "G2", "Y2", 3)
        sign(cv, 97, G - 86, "YERBATERA", "verde")
    else:
        wall(cv, 14, G - 70, 150, 71, "verde")
        roof(cv, 14, G - 70, 150, "teja", 12)
        cv.rect(14, G - 24, 150, 24, "R2")
        cv.hline(14, G - 24, 150, "R3")
        for xx in range(22, 160, 16):
            window(cv, xx, G - 62, 10, 12, "postigos", lit=(xx // 16 + f) % 2 == 0, color="Y2")
        door(cv, 76, 26, 24, "vidrio")
        neon_sign(cv, 89, G - 96, "YERBA TIERRA COLORADA", f, ("G3", "Y3"))
        tree(cv, 176, "pino", f)
        flag(cv, 2, G - 72, f)
    return done(cv)


# ================================================================== Cuyo

def frigorifico(t, f):
    cv = C()
    soil(cv, 0, W, "G2", "G3", 6)
    if t == 0:
        fence(cv, 2, 92)
        cow(cv, 10, f)
        cow(cv, 48, f + 1, "M2")
        stall(cv, 116, 50, "rojo", f, lambda c, x, y: [c.rect(x + 3 + i * 10, y - 10, 6, 10, "R2") or c.put(x + 5 + i * 10, y - 7, "W") for i in range(4)], "CARNES")
    elif t == 1:
        fence(cv, 2, 70)
        cow(cv, 12, f)
        wall(cv, 80, G - 42, 80, 43, "cal")
        roof(cv, 80, G - 42, 80, "teja", 9)
        window(cv, 90, G - 32, 30, 18, "vitrina")
        door(cv, 128, 16, 28, "vidrio")
        awning(cv, 86, G - 44, 34, "rojo", f, 7)
        sign(cv, 120, G - 64, "CARNICERÍA", "rojo")
    elif t == 2:
        fence(cv, 2, 50)
        cow(cv, 8, f, "M2")
        wall(cv, 60, G - 50, 110, 51, "cal")
        roof(cv, 60, G - 50, 110, "chapa", 8)
        door(cv, 78, 32, 34, "persiana")
        window(cv, 122, G - 40, 34, 14, "industrial")
        sign(cv, 115, G - 72, "FRIGORÍFICO", "rojo")
    elif t == 3:
        wall(cv, 4, G - 58, 120, 59, "hormigon")
        roof(cv, 4, G - 58, 120, "plano")
        cv.rect(4, G - 40, 120, 6, "R2")
        door(cv, 20, 30, 34, "persiana")
        door(cv, 66, 30, 34, "persiana")
        tank(cv, 130, 64, 22, "R2")
        sign(cv, 64, G - 82, "CARNES DEL MORRO", "rojo")
    else:
        wall(cv, 4, G - 72, 120, 73, "hormigon")
        roof(cv, 4, G - 72, 120, "plano")
        cv.rect(4, G - 50, 120, 8, "R2")
        for xx in range(12, 116, 16):
            window(cv, xx, G - 66, 10, 12, "industrial", lit=(xx // 16 + f) % 2 == 0)
        door(cv, 20, 30, 34, "persiana")
        door(cv, 70, 30, 34, "persiana")
        neon_sign(cv, 64, G - 94, "FRIGORÍFICO SAN LUIS", f)
        truck(cv, 122, "R2", "CARNES", f)
    return done(cv)


def pasas(t, f):
    cv = C()
    soil(cv, 0, W, "E2", "S2", 6)
    if t == 0:
        vines(cv, 4, 80, 1, f)
        for i in range(3):
            cv.rect(96 + i * 14, G - 6, 12, 4, "M3")
            for k in range(4):
                cv.put(97 + i * 14 + k * 3, G - 7, "u")
        post_sign(cv, 150, "PASAS", "u", "W")
    elif t == 1:
        vines(cv, 2, 70, 2, f)
        wall(cv, 86, G - 38, 70, 39, "adobe")
        roof(cv, 86, G - 38, 70, "plano")
        for yy in (G - 44, G - 50):
            cv.hline(84, yy, 74, "M3")
            for xx in range(85, 158, 3):
                cv.put(xx, yy - 1, "u" if xx % 2 else "M2")
        door(cv, 100, 16, 26)
        window(cv, 128, G - 30, 14, 12, "reja")
    elif t == 2:
        vines(cv, 2, 56, 2, f)
        wall(cv, 64, G - 48, 100, 49, "adobe")
        roof(cv, 64, G - 48, 100, "teja", 10)
        for xx in range(70, 160, 18):
            cv.rect(xx, G - 20, 14, 4, "M3")
            for k in range(4):
                cv.put(xx + 1 + k * 3, G - 21, "u")
        door(cv, 102, 22, 28, "arco")
        sign(cv, 114, G - 72, "SECADERO ZONDA", "bordo")
    elif t == 3:
        vines(cv, 2, 40, 2, f)
        wall(cv, 48, G - 56, 120, 57, "chapa")
        roof(cv, 48, G - 56, 120, "curvo", 14)
        door(cv, 86, 40, 34, "persiana")
        sign(cv, 108, G - 84, "PASAS DEL ZONDA", "bordo")
    else:
        wall(cv, 14, G - 68, 150, 69, "crema")
        roof(cv, 14, G - 68, 150, "teja", 12)
        arches(cv, 20, G - 40, 138, 40, 6)
        for xx in range(26, 160, 24):
            window(cv, xx, G - 62, 10, 12, "postigos", lit=f == 0, color="R2")
        neon_sign(cv, 89, G - 94, "PASAS SAN JUAN", f, ("R3", "Y3"))
        flag(cv, 2, G - 70, f)
    return done(cv)


def bodega_malbec(t, f):
    cv = C()
    soil(cv, 0, W, "M2", "M3", 6)
    if t == 0:
        vines(cv, 2, 100, 1, f)
        stall(cv, 118, 48, "bordo", f, lambda c, x, y: bottles(c, x + 4, 6, "R1"), "MALBEC")
    elif t == 1:
        vines(cv, 2, 76, 2, f)
        wall(cv, 88, G - 38, 70, 39, "adobe")
        roof(cv, 88, G - 38, 70, "teja", 8)
        door(cv, 100, 16, 26, "arco")
        window(cv, 128, G - 30, 14, 12, "postigos", color="R2")
        barrels(cv, 160, 2)
        sign(cv, 123, G - 58, "VINO CASERO", "bordo")
    elif t == 2:
        vines(cv, 2, 56, 2, f)
        wall(cv, 64, G - 52, 108, 53, "piedra")
        roof(cv, 64, G - 52, 108, "teja", 11)
        door(cv, 104, 28, 36, "arco")
        for xx in (74, 146):
            window(cv, xx, G - 44, 14, 14, "arco")
        sign(cv, 118, G - 78, "BODEGA MALBEC", "bordo")
    elif t == 3:
        vines(cv, 2, 40, 2, f)
        wall(cv, 46, G - 60, 130, 61, "ladrillo")
        roof(cv, 46, G - 60, 130, "teja", 12)
        cv.rect(96, G - 84, 30, 24, "R2")
        roof(cv, 96, G - 84, 30, "teja", 7)
        door(cv, 98, 26, 38, "arco")
        for xx in (58, 76, 136, 154):
            window(cv, xx, G - 50, 10, 14, "arco")
        sign(cv, 111, G - 108, "CORDÓN DEL PLATA", "bordo")
    else:
        wall(cv, 10, G - 70, 172, 71, "piedra")
        roof(cv, 10, G - 70, 172, "plano")
        wall(cv, 66, G - 96, 60, 27, "vidrio")
        roof(cv, 66, G - 96, 60, "plano")
        door(cv, 80, 32, 40, "arco")
        for xx in (22, 44, 130, 152):
            window(cv, xx, G - 58, 12, 18, "arco", lit=(xx + f) % 2 == 0)
        neon_sign(cv, 96, G - 118, "BODEGA MALBEC MENDOZA", f, ("R3", "Y3"))
        lamp(cv, 4, G - 54)
    return done(cv)


# ============================================================= Patagonia

def estancia_ovina(t, f):
    cv = C()
    soil(cv, 0, W, "E2", "Y1", 6)
    if t == 0:
        fence(cv, 0, 110)
        for i in range(4):
            sheep(cv, 6 + i * 24, f + i)
        stall(cv, 122, 50, "celeste", f, lambda c, x, y: bales(c, x + 2, 3, "E1", "l"), "LANA")
    elif t == 1:
        fence(cv, 0, 76)
        for i in range(3):
            sheep(cv, 6 + i * 22, f + i)
        wall(cv, 86, G - 40, 76, 41, "chapa")
        roof(cv, 86, G - 40, 76, "dos_aguas")
        door(cv, 112, 20, 30, "porton")
    elif t == 2:
        for i in range(2):
            sheep(cv, 4 + i * 20, f + i)
        wall(cv, 50, G - 48, 110, 49, "rojo")
        roof(cv, 50, G - 48, 110, "chapa", 9)
        for xx in (60, 136):
            window(cv, xx, G - 40, 14, 14, "postigos", color="C2")
        door(cv, 92, 26, 32, "porton")
        windmill(cv, 176, f)
        sign(cv, 105, G - 72, "ESTANCIA", "rojo")
    elif t == 3:
        for i in range(3):
            sheep(cv, 2 + i * 18, f + i)
        wall(cv, 60, G - 54, 120, 55, "cal")
        roof(cv, 60, G - 54, 120, "chapa", 10)
        cv.rect(60, G - 54, 120, 6, "R2")
        arches(cv, 66, G - 34, 108, 34, 5)
        chimney(cv, 160, G - 64, 12, f)
        sign(cv, 120, G - 86, "LA ESCONDIDA", "rojo")
    else:
        wall(cv, 18, G - 64, 150, 65, "piedra")
        roof(cv, 18, G - 64, 150, "chapa", 12)
        cv.rect(18, G - 64, 150, 5, "R2")
        for xx in range(28, 160, 20):
            window(cv, xx, G - 52, 12, 16, "postigos", lit=(xx // 20 + f) % 2 == 0, color="R2")
        door(cv, 84, 22, 34, "arco")
        chimney(cv, 150, G - 76, 14, f)
        neon_sign(cv, 93, G - 96, "CORDERO PATAGÓNICO", f)
        flag(cv, 2, G - 66, f)
    return done(cv)


def lanera(t, f):
    cv = C()
    soil(cv, 0, W, "E2", "S2", 6)
    if t == 0:
        for i in range(3):
            sheep(cv, 6 + i * 22, f + i)
        cv.rect(90, G - 30, 50, 4, "M3")
        for k in range(4):
            cv.vline(92 + k * 15, G - 26, 26, "M1")
        bales(cv, 96, 3, "E1", "l")
        post_sign(cv, 148, "LANA", "C2")
    elif t == 1:
        wall(cv, 40, G - 42, 90, 43, "madera")
        roof(cv, 40, G - 42, 90, "dos_aguas")
        door(cv, 70, 26, 30, "porton")
        bales(cv, 134, 4, "E1", "l", 2)
        sheep(cv, 6, f)
    elif t == 2:
        wall(cv, 20, G - 52, 116, 53, "celeste")
        roof(cv, 20, G - 52, 116, "curvo", 14)
        door(cv, 58, 36, 34, "persiana")
        bales(cv, 142, 3, "E1", "l", 3)
        sign(cv, 78, G - 80, "LAVADERO DE LANA", "celeste")
    elif t == 3:
        wall(cv, 4, G - 60, 124, 61, "chapa")
        roof(cv, 4, G - 60, 124, "dientes")
        for xx in range(12, 120, 14):
            window(cv, xx, G - 50, 9, 12, "industrial")
        door(cv, 46, 34, 34, "persiana")
        chimney(cv, 110, G - 60, 22, f)
        bales(cv, 134, 4, "W", "g", 3)
        sign(cv, 66, G - 86, "LANERAS DEL CHUBUT", "noche")
    else:
        wall(cv, 4, G - 74, 130, 75, "hormigon")
        roof(cv, 4, G - 74, 130, "dientes")
        for xx in range(12, 126, 14):
            window(cv, xx, G - 64, 9, 12, "industrial", lit=(xx // 14 + f) % 2 == 0)
        door(cv, 48, 36, 36, "persiana")
        neon_sign(cv, 69, G - 100, "LANERA DEL SUR", f, ("C4", "W"))
        truck(cv, 120, "C2", "LANA", f)
    return done(cv)


def chacra_peras(t, f):
    cv = C()
    soil(cv, 0, W, "G1", "G2", 6)
    for i in range(2):
        cv.rect(2 + i * 6, G - 76, 4, 76, "G1")
        cv.rect(3 + i * 6, G - 80, 2, 6, "G2")
    if t == 0:
        for i in range(4):
            tree(cv, 26 + i * 18, "pera", f, 0.9)
        stall(cv, 120, 52, "verde", f, lambda c, x, y: fruit_pile(c, x + 2, 44, "G3", "G2"), "PERAS")
    elif t == 1:
        for i in range(3):
            tree(cv, 26 + i * 18, "pera" if i % 2 else "cerezo", f, 1.0)
        wall(cv, 96, G - 40, 70, 41, "madera")
        roof(cv, 96, G - 40, 70, "teja", 9)
        door(cv, 110, 16, 28)
        window(cv, 138, G - 32, 14, 12, "postigos", color="R2")
        crates(cv, 168, 1, ("G3", "Y3"), 2)
    elif t == 2:
        for i in range(2):
            tree(cv, 26 + i * 18, "pera", f, 1.1)
        wall(cv, 70, G - 50, 104, 51, "madera")
        roof(cv, 70, G - 50, 104, "curvo", 13)
        door(cv, 100, 34, 34, "porton")
        crates(cv, 146, 2, ("G3", "Y3", "R2"), 3)
        sign(cv, 122, G - 80, "ALTO VALLE", "verde")
    elif t == 3:
        tree(cv, 26, "pera", f, 1.1)
        wall(cv, 46, G - 58, 120, 59, "cal")
        roof(cv, 46, G - 58, 120, "dientes")
        for xx in range(54, 158, 14):
            window(cv, xx, G - 48, 9, 10, "industrial")
        door(cv, 88, 36, 34, "persiana")
        sign(cv, 106, G - 84, "FRUTÍCOLA ALTO VALLE", "verde")
    else:
        wall(cv, 20, G - 70, 150, 71, "vidrio")
        roof(cv, 20, G - 70, 150, "plano")
        cv.rect(20, G - 26, 150, 26, "G2")
        cv.hline(20, G - 26, 150, "G3")
        door(cv, 82, 28, 26, "vidrio")
        neon_sign(cv, 95, G - 94, "PERAS DE RÍO NEGRO", f, ("G3", "Y3"))
        tree(cv, 180, "cerezo", f, 0.9)
    return done(cv)


def manzanas(t, f):
    cv = C()
    soil(cv, 0, W, "G1", "G2", 6)
    if t == 0:
        for i in range(4):
            tree(cv, 12 + i * 18, "manzana", f, 0.9)
        stall(cv, 110, 54, "rojo", f, lambda c, x, y: fruit_pile(c, x + 2, 46, "R2", "R1"), "MANZANAS")
    elif t == 1:
        for i in range(3):
            tree(cv, 10 + i * 18, "manzana", f, 1.0)
        wall(cv, 74, G - 42, 80, 43, "rojo")
        roof(cv, 74, G - 42, 80, "dos_aguas")
        door(cv, 102, 24, 30, "porton")
        crates(cv, 156, 2, ("R2", "R3"), 2)
    elif t == 2:
        for i in range(2):
            tree(cv, 8 + i * 18, "manzana", f, 1.1)
        wall(cv, 48, G - 52, 110, 53, "rojo")
        roof(cv, 48, G - 52, 110, "curvo", 14)
        door(cv, 80, 40, 36, "persiana")
        crates(cv, 160, 2, ("R2", "R3", "G3"), 3)
        sign(cv, 103, G - 80, "EMPAQUE", "rojo")
    elif t == 3:
        wall(cv, 4, G - 58, 120, 59, "rojo")
        roof(cv, 4, G - 58, 120, "dientes")
        for xx in range(12, 116, 14):
            window(cv, xx, G - 48, 9, 10, "industrial")
        door(cv, 44, 36, 34, "persiana")
        antenna(cv, 170, f)
        sign(cv, 64, G - 84, "MANZANARES", "rojo")
    else:
        wall(cv, 4, G - 72, 130, 73, "hormigon")
        roof(cv, 4, G - 72, 130, "dientes")
        cv.rect(4, G - 30, 130, 6, "R2")
        for xx in range(12, 126, 14):
            window(cv, xx, G - 62, 9, 12, "industrial", lit=(xx // 14 + f) % 2 == 0)
        door(cv, 50, 36, 30, "persiana")
        neon_sign(cv, 69, G - 98, "MANZANAS DEL LIMAY", f)
        antenna(cv, 174, f)
        tank(cv, 140, 54, 20, "R2")
    return done(cv)


def electronica(t, f):
    cv = C()
    cv.rect(0, G - 4, W, 5, "W")
    for xx in range(3 + f, W, 11):
        cv.put(xx, 14 + (xx * 7) % 60, "W")
    if t == 0:
        wall(cv, 60, G - 34, 70, 35, "madera")
        roof(cv, 60, G - 34, 70, "dos_aguas")
        door(cv, 74, 16, 26)
        window(cv, 100, G - 26, 18, 12, "simple", lit=True)
        post_sign(cv, 140, "SERVICE", "C2")
    elif t == 1:
        wall(cv, 40, G - 42, 100, 43, "chapa")
        roof(cv, 40, G - 42, 100, "chapa", 8)
        snow_roof(cv, 40, G - 50, 100)
        window(cv, 50, G - 32, 40, 18, "vitrina", lit=True)
        door(cv, 104, 18, 28, "vidrio")
        sign(cv, 90, G - 66, "ELECTRÓNICA", "celeste")
    elif t == 2:
        wall(cv, 20, G - 52, 130, 53, "celeste")
        roof(cv, 20, G - 52, 130, "plano")
        snow_roof(cv, 20, G - 56, 130)
        for xx in range(28, 140, 16):
            window(cv, xx, G - 44, 10, 10, "industrial", lit=True)
        door(cv, 70, 30, 28, "persiana")
        sign(cv, 85, G - 76, "ARMADORA FUEGUINA", "celeste")
    elif t == 3:
        wall(cv, 4, G - 60, 140, 61, "chapa")
        roof(cv, 4, G - 60, 140, "dientes")
        snow_roof(cv, 4, G - 70, 140)
        for xx in range(12, 136, 14):
            window(cv, xx, G - 50, 9, 10, "industrial", lit=True)
        door(cv, 54, 36, 34, "persiana")
        antenna(cv, 172, f)
        sign(cv, 74, G - 92, "PLANTA RÍO GRANDE", "celeste")
    else:
        wall(cv, 10, G - 80, 150, 81, "vidrio")
        roof(cv, 10, G - 80, 150, "plano")
        snow_roof(cv, 10, G - 84, 150)
        cv.rect(10, G - 26, 150, 26, "d")
        cv.hline(10, G - 26, 150, "g")
        door(cv, 70, 30, 26, "vidrio")
        neon_sign(cv, 85, G - 104, "TECNOFUEGO", f, ("C4", "W"))
        antenna(cv, 176, f)
    return done(cv)


# =============================================================== Pampeana

def estancia_ganadera(t, f):
    cv = C()
    soil(cv, 0, W, "G2", "G3", 6)
    if t == 0:
        fence(cv, 0, 110)
        cow(cv, 6, f)
        cow(cv, 44, f + 1, "M2")
        windmill(cv, 104, f)
        post_sign(cv, 130, "HACIENDA", "M3")
    elif t == 1:
        fence(cv, 0, 80)
        cow(cv, 8, f)
        horse(cv, 44, f)
        wall(cv, 90, G - 38, 70, 39, "cal")
        roof(cv, 90, G - 38, 70, "paja", 10)
        door(cv, 104, 16, 26)
        window(cv, 132, G - 30, 14, 12, "postigos", color="G2")
        windmill(cv, 176, f)
    elif t == 2:
        fence(cv, 0, 56)
        cow(cv, 4, f)
        cow(cv, 30, f + 1, "M2")
        wall(cv, 66, G - 46, 104, 47, "cal")
        roof(cv, 66, G - 46, 104, "teja", 10)
        arches(cv, 72, G - 30, 92, 30, 4)
        sign(cv, 118, G - 72, "ESTANCIA", "madera")
    elif t == 3:
        crop(cv, 2, 60, "girasol", 1, f)
        wall(cv, 70, G - 54, 76, 55, "rojo")
        roof(cv, 70, G - 54, 76, "dos_aguas")
        door(cv, 92, 30, 36, "porton")
        silo(cv, 152, 70)
        silo(cv, 170, 62, 14)
        sign(cv, 108, G - 90, "HACIENDA CALDENAL", "madera")
    else:
        crop(cv, 2, 40, "trigo", 1, f)
        wall(cv, 46, G - 64, 120, 65, "colonial")
        roof(cv, 46, G - 64, 120, "teja", 12)
        wall(cv, 86, G - 90, 40, 27, "colonial")
        roof(cv, 86, G - 90, 40, "teja", 8)
        arches(cv, 52, G - 40, 108, 40, 5)
        for xx in (60, 92, 124, 148):
            window(cv, xx, G - 58, 10, 12, "postigos", lit=f == 0, color="G2")
        neon_sign(cv, 106, G - 114, "LA PAMPA GANADERA", f)
        flag(cv, 176, G - 70, f)
    return done(cv)


# ================================================================ Centro

def salames(t, f):
    cv = C()
    soil(cv, 0, W, "G2", "G3", 6)

    def salami_rack(c, x, n):
        c.hline(x, G - 40, n * 6 + 4, "M2")
        for i in range(n):
            c.vline(x + 3 + i * 6, G - 40, 3, "x")
            c.rect(x + 2 + i * 6, G - 37, 3, 11 + (i % 2) * 3, "R1")
            c.put(x + 3 + i * 6, G - 33, "W")
    if t == 0:
        stall(cv, 70, 56, "bordo", f, lambda c, x, y: [c.rect(x + 2 + i * 8, y - 4, 7, 4, "R1") or c.put(x + 4 + i * 8, y - 3, "W") for i in range(6)], "SALAMES")
        salami_rack(cv, 140, 5)
    elif t == 1:
        wall(cv, 60, G - 42, 80, 43, "crema")
        roof(cv, 60, G - 42, 80, "teja", 9)
        window(cv, 70, G - 32, 30, 18, "vitrina")
        door(cv, 110, 16, 28)
        salami_rack(cv, 4, 6)
        sign(cv, 100, G - 64, "CHACINADOS", "bordo")
    elif t == 2:
        wall(cv, 40, G - 52, 110, 53, "piedra")
        roof(cv, 40, G - 52, 110, "teja", 11)
        door(cv, 60, 24, 32, "arco")
        for xx in (96, 120):
            window(cv, xx, G - 42, 14, 14, "postigos", color="G2")
        salami_rack(cv, 4, 5)
        sign(cv, 95, G - 78, "COLONIA CAROYA", "bordo")
    elif t == 3:
        wall(cv, 4, G - 58, 120, 59, "ladrillo")
        roof(cv, 4, G - 58, 120, "chapa", 9)
        for xx in range(12, 116, 16):
            window(cv, xx, G - 48, 10, 12, "industrial")
        door(cv, 46, 30, 32, "persiana")
        chimney(cv, 106, G - 58, 18, f)
        crates(cv, 132, 3, ("R1", "M3", "Y2"), 2)
        sign(cv, 64, G - 86, "FÁBRICA DE SALAMES", "bordo")
    else:
        wall(cv, 10, G - 72, 140, 73, "ladrillo")
        roof(cv, 10, G - 72, 140, "teja", 12)
        cv.rect(10, G - 30, 140, 8, "G1")
        for xx in range(18, 144, 16):
            window(cv, xx, G - 64, 10, 14, "arco", lit=(xx // 16 + f) % 2 == 0)
        door(cv, 64, 32, 28, "vidrio")
        neon_sign(cv, 80, G - 98, "SALAMES CAROYA", f)
        truck(cv, 120, "R1", "SALAMES", f)
        flag(cv, 2, G - 74, f, ("G2", "W", "R2"))
    return done(cv)


def usina_lactea(t, f):
    cv = C()
    soil(cv, 0, W, "G2", "G3", 6)
    if t == 0:
        fence(cv, 0, 90)
        cow(cv, 6, f)
        cow(cv, 44, f + 1)
        stall(cv, 116, 52, "celeste", f, lambda c, x, y: [c.rect(x + 3 + i * 9, y - 9, 6, 9, "W") or c.rect(x + 3 + i * 9, y - 9, 6, 2, "C2") for i in range(5)], "LECHE")
    elif t == 1:
        cow(cv, 4, f)
        wall(cv, 50, G - 42, 90, 43, "cal")
        roof(cv, 50, G - 42, 90, "dos_aguas")
        door(cv, 80, 26, 30, "porton")
        tank(cv, 148, 40, 20, "C2")
        sign(cv, 95, G - 76, "TAMBO", "celeste")
    elif t == 2:
        cow(cv, 2, f)
        wall(cv, 40, G - 50, 100, 51, "celeste")
        roof(cv, 40, G - 50, 100, "curvo", 12)
        door(cv, 70, 36, 32, "persiana")
        tank(cv, 146, 56, 20, "C2")
        tank(cv, 168, 48, 18, "C3")
        sign(cv, 90, G - 76, "LÁCTEOS", "celeste")
    elif t == 3:
        wall(cv, 4, G - 58, 110, 59, "cal")
        roof(cv, 4, G - 58, 110, "dientes")
        for xx in range(12, 106, 14):
            window(cv, xx, G - 48, 9, 10, "industrial")
        door(cv, 40, 34, 34, "persiana")
        for i in range(3):
            tank(cv, 118 + i * 24, 74 - i * 6, 20, "C2")
        sign(cv, 59, G - 84, "CUENCA SANTAFESINA", "celeste")
    else:
        wall(cv, 4, G - 74, 120, 75, "hormigon")
        roof(cv, 4, G - 74, 120, "plano")
        cv.rect(4, G - 32, 120, 8, "C2")
        for xx in range(12, 116, 16):
            window(cv, xx, G - 66, 10, 14, "industrial", lit=(xx // 16 + f) % 2 == 0)
        door(cv, 46, 32, 26, "vidrio")
        neon_sign(cv, 64, G - 98, "USINA LÁCTEA", f, ("C4", "W"))
        for i in range(2):
            tank(cv, 130 + i * 30, 86 - i * 8, 26, "C2")
    return done(cv)


def molino_harinero(t, f):
    cv = C()
    soil(cv, 0, W, "Y1", "Y2", 6)
    if t == 0:
        crop(cv, 2, 100, "trigo", 3, f)
        stall(cv, 118, 50, "amarillo", f, lambda c, x, y: sacks(c, x + 2, 4, "E1", "Y2"), "HARINA")
    elif t == 1:
        crop(cv, 2, 70, "trigo", 3, f)
        windmill(cv, 90, f)
        wall(cv, 110, G - 40, 64, 41, "piedra")
        roof(cv, 110, G - 40, 64, "dos_aguas")
        door(cv, 132, 20, 28, "porton")
    elif t == 2:
        crop(cv, 2, 46, "trigo", 3, f)
        wall(cv, 52, G - 62, 50, 63, "piedra")
        roof(cv, 52, G - 62, 50, "dos_aguas")
        door(cv, 66, 22, 30, "arco")
        window(cv, 72, G - 54, 10, 12, "arco")
        silo(cv, 112, 66)
        silo(cv, 132, 58)
        tractor(cv, 152, "R2", f)
        sign(cv, 77, G - 96, "MOLINO", "madera")
    elif t == 3:
        wall(cv, 4, G - 70, 90, 71, "crema")
        roof(cv, 4, G - 70, 90, "plano")
        for xx in range(12, 86, 16):
            window(cv, xx, G - 60, 10, 14, "simple")
        door(cv, 34, 30, 34, "persiana")
        for i in range(4):
            silo(cv, 98 + i * 22, 92 - i * 4, 20)
        sign(cv, 49, G - 92, "HARINERA", "madera")
    else:
        wall(cv, 4, G - 86, 96, 87, "hormigon")
        roof(cv, 4, G - 86, 96, "plano")
        for xx in range(12, 92, 14):
            window(cv, xx, G - 78, 9, 14, "industrial", lit=(xx // 14 + f) % 2 == 0)
        door(cv, 34, 34, 36, "persiana")
        for i in range(4):
            silo(cv, 104 + i * 22, 112 - i * 4, 20)
        neon_sign(cv, 96, G - 120, "MOLINOS PAMPA HÚMEDA", f, ("Y3", "W"))
    return done(cv)


def panaderia(t, f):
    cv = C()
    cx = W // 2
    if t == 0:
        cv.rect(cx - 28, G - 30, 56, 22, "W")
        cv.frame(cx - 28, G - 30, 56, 22, "M2")
        for i in range(5):
            cv.rect(cx - 22 + i * 10, G - 26, 7, 4, "Y2")
            cv.put(cx - 22 + i * 10, G - 27, "Y3")
        for wx in (cx - 18, cx + 16):
            cv.ellipse(wx, G - 4, 4, 4, "o")
            cv.ellipse(wx, G - 4, 1, 1, "g")
        awning(cv, cx - 32, G - 46, 64, "bordo", f, 8)
        fileteado(cv, cx - 40, G - 66, 80, "MEDIALUNAS", f)
        return done(cv)
    if t == 1:
        wall(cv, 46, G - 64, 100, 65, "crema")
        roof(cv, 46, G - 64, 100, "plano")
        window(cv, 56, G - 40, 46, 26, "vitrina")
        for i in range(5):
            cv.rect(60 + i * 8, G - 20, 6, 3, "Y2")
        door(cv, 112, 20, 34, "vidrio")
        awning(cv, 50, G - 48, 92, "bordo", f, 8)
        fileteado(cv, 54, G - 62, 84, "PANADERÍA", f)
        planter(cv, 30)
        return done(cv)
    if t == 2:
        wall(cv, 30, G - 84, 132, 85, "ladrillo")
        roof(cv, 30, G - 84, 132, "plano")
        for xx in (42, 74, 106, 138):
            window(cv, xx, G - 76, 14, 16, "postigos", color="G2")
        window(cv, 40, G - 42, 70, 28, "vitrina")
        door(cv, 122, 22, 34, "vidrio")
        awning(cv, 34, G - 50, 124, "bordo", f, 9)
        fileteado(cv, 56, G - 104, 80, "CONFITERÍA", f)
        bench(cv, 6)
        return done(cv)
    if t == 3:
        wall(cv, 18, G - 98, 156, 99, "colonial")
        roof(cv, 18, G - 98, 156, "plano")
        for xx in range(28, 166, 28):
            window(cv, xx, G - 90, 14, 18, "arco")
            cv.hline(xx - 4, G - 70, 22, "x")
            for bx in range(xx - 4, xx + 18, 3):
                cv.vline(bx, G - 74, 4, "x")
        window(cv, 26, G - 44, 96, 30, "vitrina")
        door(cv, 132, 26, 38, "vidrio")
        awning(cv, 22, G - 52, 148, "bordo", f, 10)
        fileteado(cv, 50, G - 118, 92, "LA PORTEÑA", f)
        for tx in (2, 176):
            cv.rect(tx, G - 14, 14, 3, "W")
            cv.rect(tx + 6, G - 11, 2, 12, "x")
        return done(cv)
    wall(cv, 6, G - 110, 180, 111, "colonial")
    roof(cv, 6, G - 110, 180, "plano")
    cv.rect(70, G - 132, 52, 22, "W")
    cv.ellipse(96, G - 132, 26, 10, "l")
    cv.ellipse(96, G - 132, 22, 8, "C3")
    for xx in range(16, 180, 24):
        window(cv, xx, G - 100, 12, 20, "arco", lit=(xx // 24 + f) % 2 == 0)
        cv.hline(xx - 3, G - 78, 18, "x")
        for bx in range(xx - 3, xx + 15, 3):
            cv.vline(bx, G - 82, 4, "x")
    window(cv, 14, G - 46, 66, 32, "vitrina", lit=True)
    window(cv, 112, G - 46, 66, 32, "vitrina", lit=True)
    door(cv, 84, 24, 40, "vidrio")
    awning(cv, 10, G - 54, 172, "bordo", f, 10)
    fileteado(cv, 30, G - 70, 132, "CONFITERÍA OBELISCO", f)
    lamp(cv, 2, G - 70)
    return done(cv)


ARCH4 = {
    "algodonal": algodonal, "papas_andinas": papas_andinas, "almazara": almazara, "olivar": olivar,
    "bodega_torrontes": bodega_torrontes, "citricola": citricola, "bananal": bananal, "desmotadora": desmotadora,
    "arrocera": arrocera, "molino_arrocero": molino_arrocero, "yerbatal": yerbatal, "frigorifico": frigorifico,
    "pasas": pasas, "bodega_malbec": bodega_malbec, "estancia_ovina": estancia_ovina, "lanera": lanera,
    "chacra_peras": chacra_peras, "manzanas": manzanas, "electronica": electronica, "estancia_ganadera": estancia_ganadera,
    "salames": salames, "usina_lactea": usina_lactea, "molino_harinero": molino_harinero, "panaderia": panaderia,
}
