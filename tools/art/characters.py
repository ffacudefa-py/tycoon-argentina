"""Personajes pixel art (16x24 por cuadro), animación por fotogramas.

Spritesheet por variante: 8 columnas x 1 fila, cuadros de 16x24:
  0-3 caminar (mirando a la derecha), 4-5 quieto (respira), 6-7 trabajar
  (brazos), y una segunda hoja "celebrate" con 2 cuadros (brazos arriba).
El juego voltea horizontalmente para caminar a la izquierda.
"""
import os
from px import Canvas

SKINS = [("s", "S"), ("z", "Z"), ("s", "S"), ("t", "M")]
HAIRS = ["k", "o", "m", "Y", "x", "M", "k", "B"]
SHIRTS = [("c", "C"), ("r", "R"), ("n", "G"), ("y", "Y"), ("v", "V"), ("q", "Q"), ("w", "l"), ("b", "c")]
PANTS = [("A", "u"), ("x", "o"), ("m", "k"), ("A", "u"), ("d", "x"), ("u", "o"), ("m", "k"), ("x", "o")]
STYLES = ["short", "long", "cap", "short", "bun", "bald", "cap", "long"]


def draw_person(cv, ox, oy, v, pose, frame, apron=None):
    skin, skin_d = SKINS[v % len(SKINS)]
    hair = HAIRS[v % len(HAIRS)]
    shirt, shirt_d = SHIRTS[v % len(SHIRTS)]
    pant, pant_d = PANTS[v % len(PANTS)]
    style = STYLES[v % len(STYLES)]
    bob = 1 if (pose == "idle" and frame == 1) or (pose == "walk" and frame in (1, 3)) else 0
    y0 = oy + 3 + bob
    # --- cabeza (6x6) ---
    hx = ox + 5
    cv.rect(hx, y0, 6, 6, skin)
    cv.vline(hx + 5, y0 + 1, 5, skin_d)
    # pelo
    if style == "bald":
        cv.hline(hx, y0, 6, skin)
        cv.put(hx + 1, y0, "h")
    else:
        cv.hline(hx, y0 - 1, 6, hair)
        cv.hline(hx, y0, 6, hair)
        cv.vline(hx, y0, 3, hair)
        if style == "long":
            cv.vline(hx, y0, 6, hair)
            cv.vline(hx - 1, y0 + 1, 6, hair)
        if style == "bun":
            cv.rect(hx - 1, y0 - 2, 3, 2, hair)
        if style == "cap":
            cv.hline(hx, y0 - 1, 6, "r")
            cv.hline(hx, y0, 6, "r")
            cv.hline(hx + 4, y0 + 1, 4, "R")
    # ojo y boca (mirando a la derecha)
    cv.put(hx + 4, y0 + 2, "o")
    cv.put(hx + 4, y0 + 4, skin_d)
    # --- torso ---
    ty = y0 + 6
    cv.rect(ox + 4, ty, 8, 7, shirt)
    cv.vline(ox + 11, ty, 7, shirt_d)
    cv.hline(ox + 4, ty + 6, 8, shirt_d)
    if apron:
        cv.rect(ox + 6, ty + 2, 5, 6, apron)
        cv.hline(ox + 6, ty + 1, 5, "w")
    # --- brazos ---
    def arm(ax, ay, dx_list):
        for i, dx in enumerate(dx_list):
            cv.put(ax + dx, ay + i, shirt if i < 3 else skin)
    if pose == "celebrate":
        up = 1 if frame == 0 else 0
        for i in range(5):
            cv.put(ox + 3, ty - 1 - i + up, shirt if i < 2 else skin)
            cv.put(ox + 12, ty - 1 - i + up, shirt if i < 2 else skin)
    elif pose == "work":
        # brazo adelante moviéndose (atiende / entrega)
        reach = 2 if frame == 0 else 1
        cv.hline(ox + 11, ty + 2, reach + 1, shirt)
        cv.put(ox + 12 + reach, ty + 2, skin)
        cv.put(ox + 12 + reach, ty + 3, skin)
        arm(ox + 4, ty + 1, [0, 0, 0, 0, 0])
    elif pose == "walk":
        swing = [1, 0, -1, 0][frame]
        arm(ox + 5 + swing, ty + 1, [0, 0, 0, 0, 0])
    else:
        arm(ox + 7, ty + 1, [0, 0, 0, 0, 0])
    # --- piernas ---
    ly = ty + 7
    if pose == "walk":
        offs = [(-1, 2), (0, 1), (2, -1), (1, 0)][frame]
        lf, lb = offs
        cv.rect(ox + 5 + lb, ly, 2, 4 - bob, pant)
        cv.rect(ox + 8 + lf, ly, 2, 4 - bob, pant_d)
        cv.rect(ox + 5 + lb, ly + 4 - bob, 3, 1, "o")
        cv.rect(ox + 8 + lf, ly + 4 - bob, 3, 1, "o")
    else:
        cv.rect(ox + 5, ly, 2, 4 - bob, pant)
        cv.rect(ox + 8, ly, 2, 4 - bob, pant_d)
        cv.rect(ox + 5, ly + 4 - bob, 3, 1, "o")
        cv.rect(ox + 8, ly + 4 - bob, 3, 1, "o")


def make_sheet(v, apron=None):
    sheet = Canvas(16 * 10, 24)
    poses = [("walk", 0), ("walk", 1), ("walk", 2), ("walk", 3), ("idle", 0), ("idle", 1),
             ("work", 0), ("work", 1), ("celebrate", 0), ("celebrate", 1)]
    for i, (pose, fr) in enumerate(poses):
        cell = Canvas(16, 24)
        draw_person(cell, 0, 0, v, pose, fr, apron)
        cell.outline_all("o")
        sheet.blit(cell, i * 16, 0)
    return sheet


def dog_sheet():
    """Perro callejero decorativo: 4 cuadros 16x12."""
    sheet = Canvas(64, 12)
    for f in range(4):
        c = Canvas(16, 12)
        leg = [0, 1, 0, -1][f]
        c.rect(3, 4, 9, 4, "M")
        c.hline(3, 7, 9, "m")
        c.rect(10, 1, 4, 4, "M")
        c.put(13, 2, "o")
        c.put(10, 0, "m")
        c.put(14, 3, "o")
        c.put(2, 3 + (f % 2), "M")
        c.rect(4 + leg, 8, 1, 3, "m")
        c.rect(10 - leg, 8, 1, 3, "m")
        c.rect(6 - leg, 8, 1, 3, "M")
        c.outline_all("o")
        sheet.blit(c, f * 16, 0)
    return sheet


def generate(out):
    d = os.path.join(out, "characters")
    os.makedirs(d, exist_ok=True)
    for v in range(8):
        make_sheet(v).save(f"{d}/customer_{v}.png")
    aprons = ["r", "c", "n", "Y", "v", "q", "B", "A"]
    for v in range(8):
        make_sheet(v, apron=aprons[v]).save(f"{d}/worker_{v}.png")
    dog_sheet().save(f"{d}/dog.png")
