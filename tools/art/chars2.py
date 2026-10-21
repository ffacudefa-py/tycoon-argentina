"""Personajes 2.0: cuadros de 32x48, 10 por hoja (320x48).

Orden de cuadros: 0-3 caminar (mirando a la derecha), 4-5 quieto,
6-7 trabajar (atender), 8-9 festejar. Pies en la fila 46.
Escala: 1 m = 24 px (persona ~1,8 m = 44 px).
"""
import os
from px2 import Canvas, sheet

SKINS = [("S1", "S2", "S3"), ("S2", "S3", "M2"), ("M3", "M2", "M1"), ("S1", "S2", "S3")]
HAIRS = [("M1", "M2"), ("o", "u"), ("Y2", "Y3"), ("R1", "R2"), ("g", "l"), ("M2", "M3"), ("o", "x"), ("M1", "M2")]
STYLES = ["short", "long", "curly", "cap", "bald", "short", "bun", "cap"]
# camisa: (sombra, medio, luz, rayas o None)
SHIRTS = [("C2", "C3", "C4", "W"), ("R1", "R2", "R3", None), ("G1", "G2", "G3", None), ("Y1", "Y2", "Y3", None),
          ("R2", "W", "W", "R2"), ("u", "x", "d", None), ("l", "w", "W", None), ("C1", "C2", "C3", None)]
PANTS = [("o", "u", "x"), ("C1", "C2", "C3"), ("M1", "M2", "M3"), ("x", "d", "g"), ("o", "u", "x"), ("C1", "C2", "C3"), ("M1", "M2", "M3"), ("u", "x", "d")]
EXTRAS = ["", "", "", "", "mustache", "mate", "", ""]


def leg(cv, hip_x, foot_x, top, bottom, ramp, shoe):
    s, m, l = ramp
    n = bottom - top
    for i in range(n + 1):
        y = top + i
        x = round(hip_x + (foot_x - hip_x) * i / n)
        cv.rect(x, y, 4, 1, m)
        cv.put(x, y, l)
        cv.put(x + 3, y, s)
    cv.rect(foot_x - 1, bottom + 1, 6, 2, shoe)
    cv.hline(foot_x - 1, bottom + 1, 6, "x" if shoe == "o" else "d")


def arm(cv, sx, sy, angle_dx, angle_dy, sleeve, skin, length=11):
    for i in range(length):
        x = round(sx + angle_dx * i / length)
        y = round(sy + angle_dy * i / length)
        c = sleeve[1] if i < 5 else skin[0]
        cv.rect(x, y, 3, 1, c)
        cv.put(x + 2, y, sleeve[0] if i < 5 else skin[1])
    hx = round(sx + angle_dx)
    hy = round(sy + angle_dy)
    cv.rect(hx, hy, 3, 2, skin[0])
    cv.put(hx + 2, hy + 1, skin[1])


def person(v, pose, f, worker=False):
    cv = Canvas(32, 48)
    skin = SKINS[v % len(SKINS)]
    hair = HAIRS[v % len(HAIRS)]
    style = STYLES[v % len(STYLES)]
    shirt = SHIRTS[v % len(SHIRTS)]
    pants = PANTS[v % len(PANTS)]
    extra = EXTRAS[v % len(EXTRAS)] if not worker else ""
    bob = 1 if (pose == "walk" and f in (1, 3)) or (pose == "idle" and f == 1) else 0
    jump = -2 if pose == "celebrate" and f == 0 else 0
    oy = -bob + jump
    # --- piernas ---
    if pose == "walk":
        front, back = [(5, -3), (1, 1), (-3, 5), (1, 1)][f]
        leg(cv, 12, 12 + back, 32 + oy, 43, (pants[0], pants[0], pants[1]), "o")   # pierna de atrás, más oscura
        leg(cv, 15, 15 + front, 32 + oy, 43, pants, "o")
    else:
        leg(cv, 12, 12, 32 + oy, 43 + min(0, jump), (pants[0], pants[0], pants[1]), "o")
        leg(cv, 16, 16, 32 + oy, 43 + min(0, jump), pants, "o")
    # --- brazo de atrás ---
    sleeve = (shirt[0], shirt[0])
    if pose == "walk":
        swing = [-4, 0, 4, 0][f]
        arm(cv, 11, 20 + oy, swing, 10, sleeve, (skin[1], skin[2]))
    elif pose == "celebrate":
        arm(cv, 10, 20 + oy, -4, -10 if f == 0 else -8, sleeve, (skin[1], skin[2]))
    else:
        arm(cv, 11, 20 + oy, 0, 10, sleeve, (skin[1], skin[2]))
    # --- torso ---
    ty = 19 + oy
    s0, s1, s2, stripe = shirt
    cv.rect(11, ty, 11, 13, s1)
    cv.vline(11, ty, 13, s2)
    cv.vline(20, ty, 13, s0)
    cv.vline(21, ty, 13, s0)
    if stripe:
        for x in (13, 16, 19):
            cv.vline(x, ty + 1, 12, stripe if stripe != s1 else s2)
    cv.hline(13, ty, 6, s2)                      # cuello
    cv.put(16, ty + 1, s0)
    cv.hline(11, ty + 12, 11, pants[0])          # cinturón
    if worker:
        ap = ["Q", "G2", "R2", "C2", "Y2", "M3", "R1", "C1"][v % 8]
        cv.rect(13, ty + 3, 8, 12, ap)
        cv.vline(20, ty + 3, 12, "o")
        cv.hline(13, ty + 2, 8, "w")
        cv.rect(15, ty + 7, 4, 3, "w")           # bolsillo
    # --- cabeza ---
    hx, hy = 10, 6 + oy
    cv.rect(hx + 1, hy, 10, 12, skin[0])
    cv.rect(hx, hy + 2, 12, 9, skin[0])
    cv.vline(hx, hy + 2, 9, skin[1])
    cv.hline(hx + 2, hy + 11, 8, skin[1])
    cv.rect(13, 18 + oy, 4, 1, skin[2])          # cuello
    cv.put(hx + 12, hy + 6, skin[0])             # nariz
    cv.put(hx + 12, hy + 7, skin[1])
    cv.rect(hx + 3, hy + 5, 2, 3, skin[1])       # oreja
    cv.put(hx + 3, hy + 6, skin[2])
    cv.vline(hx + 9, hy + 4, 3, "o")             # ojo
    cv.put(hx + 9, hy + 4, "u")
    cv.hline(hx + 8, hy + 3, 3, hair[0])         # ceja
    smile = pose in ("celebrate", "work")
    cv.hline(hx + 8, hy + 9, 3, "R1" if smile else skin[2])
    if smile:
        cv.put(hx + 10, hy + 8, "R1")
    h0, h1 = hair
    if style in ("short", "cap", "bun"):
        cv.rect(hx, hy - 1, 12, 4, h0)
        cv.hline(hx + 1, hy - 1, 9, h1)
        cv.rect(hx, hy + 2, 3, 4, h0)
    if style == "long":
        cv.rect(hx, hy - 1, 12, 4, h0)
        cv.hline(hx + 1, hy - 1, 9, h1)
        cv.rect(hx - 1, hy + 2, 5, 12, h0)
        cv.vline(hx, hy + 3, 10, h1)
    if style == "curly":
        for dx, dy in ((0, 0), (3, -2), (6, -2), (9, -1), (-1, 3), (-1, 6), (1, 9)):
            cv.rect(hx + dx, hy + dy, 3, 3, h0)
            cv.put(hx + dx, hy + dy, h1)
    if style == "bun":
        cv.rect(hx - 2, hy - 2, 4, 4, h0)
        cv.put(hx - 1, hy - 2, h1)
    if style == "cap":
        cap = "R2" if not worker else ["Q", "G2", "R2", "C2", "Y2", "M3", "R1", "C1"][v % 8]
        cv.rect(hx, hy - 2, 12, 4, cap)
        cv.hline(hx + 1, hy - 2, 9, "W" if cap != "W" else "l")
        cv.rect(hx + 9, hy + 1, 6, 2, cap)        # visera
        cv.hline(hx + 9, hy + 2, 6, "o")
    if style == "bald":
        cv.hline(hx + 2, hy, 7, skin[0])
        cv.put(hx + 3, hy + 1, "W")
        cv.rect(hx, hy + 3, 3, 4, h0)
    if extra == "mustache":
        cv.hline(hx + 8, hy + 8, 4, h0 if style != "bald" else "g")
    # --- brazo de adelante ---
    fsleeve = (shirt[0], shirt[1])
    fskin = (skin[0], skin[1])
    if pose == "walk":
        swing = [4, 0, -4, 0][f]
        arm(cv, 17, 20 + oy, swing, 10, fsleeve, fskin)
    elif pose == "work":
        reach = 7 if f == 0 else 5
        arm(cv, 17, 20 + oy, reach, 5, fsleeve, fskin)
        cv.rect(17 + reach + 1, 24 + oy, 4, 4, "Y2" if f == 0 else "C3")   # entrega un producto
        cv.put(17 + reach + 1, 24 + oy, "Y4" if f == 0 else "C4")
    elif pose == "celebrate":
        arm(cv, 18, 20 + oy, 4, -10 if f == 0 else -8, fsleeve, fskin)
    else:
        arm(cv, 17, 20 + oy, 1, 10, fsleeve, fskin)
        if extra == "mate":
            cv.rect(19, 27 + oy, 4, 5, "M2")      # mate
            cv.hline(19, 27 + oy, 4, "G2")
            cv.put(19, 28 + oy, "M3")
            cv.vline(21, 23 + oy, 4, "l")         # bombilla
    cv.outline("o")
    return cv


def make_sheet(v, worker=False):
    poses = [("walk", 0), ("walk", 1), ("walk", 2), ("walk", 3), ("idle", 0), ("idle", 1),
             ("work", 0), ("work", 1), ("celebrate", 0), ("celebrate", 1)]
    return sheet([person(v, p, f, worker) for p, f in poses])


def generate(out):
    d = os.path.join(out, "characters")
    os.makedirs(d, exist_ok=True)
    for v in range(8):
        make_sheet(v).save(f"{d}/customer_{v}.png")
        make_sheet(v, True).save(f"{d}/worker_{v}.png")
