"""Utilería 12.1 de los interiores (los muebles y objetos que aparecen al subir
de nivel), en pixel art "símil 3D".

Proyección oblicua de gabinete, la misma para todas las piezas: se ve la cara de
frente, la tapa (arriba) y un costado a la derecha; luz arriba-izquierda. Cada
cara tiene su tono de la rampa del material, filos con brillo, oclusión en los
rincones y contorno marrón (#3D1B0B) más claro del lado de la luz.

Cada pieza mide EXACTAMENTE lo mismo que en gen_interiors.SZ (las posiciones de
los puestos, la fila y las animaciones no cambian). La sombra de contacto en el
piso la agrega compose_interiors.py.

Uso: python tools/art/props_art.py  -> tools/art/pxl/out/props/<pieza>.png
     (lo llama compose_interiors.py)
"""
import math
import os
import random
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from minigames_art2 import Cv, shade_poly  # noqa: E402
import hands_art as HA  # noqa: E402

OUT = os.path.join(HERE, "pxl", "out", "props")
OUTL = "#3D1B0B"
OUTL_L = "#8E461F"

# ------------------------------------------------------------- rampas (oscuro -> claro)
R = {
    "wood":   ["#3E2114", "#5A2F1B", "#7A4426", "#9A5A33", "#B87444", "#D4935E", "#EBB884"],
    "oak":    ["#4A2A16", "#6B3D20", "#8A532C", "#A96D3C", "#C68A50", "#DDA96E", "#F0CC96"],
    "steel":  ["#2E2B3E", "#47445C", "#65627E", "#8784A0", "#AAA8C0", "#CFCDE0", "#F2F1F8"],
    "white":  ["#8F8796", "#B3ACB6", "#CFC9D0", "#E3DEE2", "#F1EDEF", "#FBF9FA", "#FFFFFF"],
    "red":    ["#4A1418", "#701E24", "#962A2E", "#B83A3C", "#D5576E", "#EE8A8F", "#FFC4C4"],
    "green":  ["#163A26", "#1F5434", "#2E7D4F", "#3F9E5E", "#67D08E", "#9FE6B0", "#D2F7DA"],
    "blue":   ["#16284A", "#1F3F6E", "#2F5FA0", "#3E74B8", "#5A8FD0", "#8FC4FF", "#D0E8FF"],
    "yellow": ["#6E4208", "#9A6010", "#C07A12", "#F0A00E", "#F6C43A", "#FFE07A", "#FFF6C8"],
    "orange": ["#5E2A0E", "#8A3F14", "#B5541F", "#E07A2C", "#F59A45", "#FFC07A", "#FFE6C4"],
    "burlap": ["#4E3420", "#6E4C2E", "#8E6A40", "#AE8754", "#C9A46C", "#DEC18E", "#F0DDB4"],
    "card":   ["#5A3A1E", "#7C5230", "#9E6E40", "#BC8A52", "#D2A56A", "#E4C18C", "#F4DEB4"],
    "brick":  ["#4A1A14", "#6E2A1E", "#8E3A28", "#AA4A30", "#C46440", "#DA845C", "#EEAE88"],
    "dark":   ["#14111A", "#1E1A26", "#2A2534", "#383145", "#4A4259", "#615873", "#7D7493"],
    "brass":  ["#5A3608", "#7A4A12", "#B5700A", "#E8A82A", "#FFD86A", "#FFF0A8", "#FFFFFF"],
    "glass":  ["#2A4A6E", "#3E6A94", "#5A8EB8", "#7CB0D6", "#A6D0EC", "#CFE8F8", "#FFFFFF"],
    "stone":  ["#3E3A44", "#5A5560", "#77717E", "#958F9A", "#B2ADB6", "#CFCBD2", "#ECEAEE"],
}
GOODS = ["#D5576E", "#F6C43A", "#3F9E5E", "#4E8FD8", "#E07A2C", "#8A63C2", "#F2E6CE", "#B83A3C", "#67D08E"]
METAL_OUT = ("#2E2B3E", "#65627E")


def outline(cv, dark=OUTL, light=OUTL_L):
    cv.outline(dark, light)


# ------------------------------------------------------------- primitivas 3D
def box(cv, x, y, w, h, d, ramp, top_tone=5, front_tone=3, side_tone=1, grad=True, edge=True):
    """Caja en proyección oblicua. (x, y) = esquina sup.-izq. del total; w x h =
    tamaño total; d = profundidad visible (la tapa mide d de alto y el costado
    d//2 de ancho). Devuelve el rectángulo del frente (fx, fy, fw, fh)."""
    ds = max(1, d // 2) if d > 0 else 0
    fx, fy, fw, fh = x, y + d, w - ds, h - d
    if d > 0:                                                         # tapa
        cv.poly([(fx, fy), (fx + fw - 1, fy), (fx + fw - 1 + ds, y), (fx + ds, y)], ramp[top_tone])
        if edge:
            cv.line([(fx + ds, y), (fx + fw - 1 + ds, y)], ramp[min(6, top_tone + 1)])
    if ds > 0:                                                        # costado derecho
        cv.poly([(fx + fw, fy), (fx + fw - 1 + ds, y + 1), (fx + fw - 1 + ds, y + fh - 1), (fx + fw, fy + fh - 1)], ramp[side_tone])
    for j in range(fh):                                               # frente con oclusión abajo
        t = front_tone
        if grad and j >= fh - 2:
            t = front_tone - 1
        cv.rect(fx, fy + j, fw, 1, ramp[max(0, t)])
    if edge and d > 0:
        cv.line([(fx, fy), (fx + fw - 1, fy)], ramp[6])               # filo de luz
    return fx, fy, fw, fh


def cylinder_v(cv, cx, top, bottom, r, ramp, cap=True, ry=None):
    """Cilindro vertical (tanque, termo, maceta): sombreado por columna y tapa elíptica."""
    ry = ry or max(1.0, r / 3)
    for x in range(int(cx - r), int(cx + r) + 1):
        u = (x + 0.5 - cx) / r
        if abs(u) > 1:
            continue
        b = -u * 0.55 + math.sqrt(max(0.0, 1 - u * u)) * 0.6
        idx = int(round((b * 0.5 + 0.5) * 6))
        if -0.55 < u < -0.38:
            idx = 6                                                    # reflejo especular
        hh = math.sqrt(max(0.0, 1 - u * u)) * ry
        cv.rect(x, int(top), 1, int(bottom - top) + 1, ramp[max(0, min(6, idx))])
        cv.rect(x, int(bottom), 1, int(hh) + 1, ramp[max(0, min(6, idx - 1))])
    if cap:
        cv.ell(cx, top, r - 0.4, ry, ramp[5])
        cv.ell(cx - r * 0.2, top - ry * 0.2, r * 0.55, ry * 0.5, ramp[6])


def disk(cv, cx, cy, r, ramp):
    """Disco con volumen (tapa de barril, rueda, fruta)."""
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            dx, dy = (x + 0.5 - cx) / r, (y + 0.5 - cy) / r
            if dx * dx + dy * dy > 1:
                continue
            b = -(dx * 0.5 + dy * 0.7) * 0.8 + 0.2
            cv.put(x, y, ramp[max(0, min(len(ramp) - 1, int(round((b * 0.5 + 0.5) * (len(ramp) - 1)))))])


def goods_row(cv, x0, x1, base, seed, maxh=8):
    """Fila de mercadería con volumen: frascos, botellas, cajitas, latas."""
    rnd = random.Random(seed)
    x = x0
    while x < x1 - 2:
        kind = rnd.choice(["jar", "bottle", "box", "can"])
        col = rnd.choice(GOODS)
        if kind == "bottle":
            h = rnd.randint(maxh - 2, maxh)
            if x + 3 > x1:
                break
            cv.rect(x, base - h + 3, 3, h - 3, col)
            cv.rect(x + 1, base - h, 1, 3, col)
            cv.put(x, base - h + 3, "#FFFFFF")
            cv.rect(x, base - 3, 3, 1, "#F2E6CE")
            x += 4
        elif kind == "jar":
            h = rnd.randint(min(4, maxh), min(6, maxh))
            if x + 4 > x1:
                break
            cv.rect(x, base - h, 4, h, col)
            cv.rect(x, base - h - 1, 4, 1, "#B2ADB6")
            cv.put(x, base - h, "#FFFFFF")
            cv.rect(x + 1, base - h + 2, 2, 2, "#F2E6CE")
            x += 5
        elif kind == "can":
            if x + 3 > x1:
                break
            cv.rect(x, base - 4, 3, 4, col)
            cv.rect(x, base - 4, 3, 1, "#CFCBD2")
            cv.put(x, base - 3, "#FFFFFF")
            x += 4
        else:
            h = rnd.randint(min(4, maxh), maxh)
            w = rnd.randint(4, 6)
            if x + w > x1:
                break
            cv.rect(x, base - h, w, h, col)
            cv.rect(x, base - h, w, 1, "#FFFFFF")
            cv.rect(x + w - 1, base - h + 1, 1, h - 1, "#3D1B0B")
            x += w + 1


def fruit(cv, cx, cy, r, ramp):
    disk(cv, cx, cy, r, ramp)
    cv.put(int(cx - r * 0.4), int(cy - r * 0.4), ramp[-1])


# ================================================================== MOSTRADORES
def counter_wood(w=74, h=34):
    cv = Cv(w, h)
    W = R["oak"]
    fx, fy, fw, fh = box(cv, 0, 0, w, h, 6, W)
    cv.rect(fx, fy, fw, 2, W[4])                                     # canto de la mesada
    cv.line([(fx, fy), (fx + fw - 1, fy)], W[6])
    for xx in range(4, fw, 9):                                        # veta de la tapa
        cv.line([(xx, 2), (xx + 6, 2)], W[4])
    n = 4
    pw = (fw - 6) // n
    for i in range(n):                                                # paneles con bisel
        px, py, ph = fx + 3 + i * pw, fy + 5, fh - 10
        cv.rect(px + 1, py, pw - 3, ph, W[2])
        cv.rect(px + 2, py + 1, pw - 5, ph - 2, W[3])
        cv.line([(px + 1, py), (px + pw - 3, py)], W[1])
        cv.line([(px + 1, py), (px + 1, py + ph - 1)], W[1])
        cv.line([(px + 2, py + ph - 1), (px + pw - 3, py + ph - 1)], W[5])
        cv.line([(px + pw - 3, py + 1), (px + pw - 3, py + ph - 1)], W[5])
        cv.put(px + 3, py + 2, W[5])
    cv.rect(fx, fy + fh - 3, fw, 3, W[1])                              # zócalo
    cv.line([(fx, fy + fh - 3), (fx + fw - 1, fy + fh - 3)], W[2])
    outline(cv)
    return cv


def counter_glass(w=74, h=34):
    cv = Cv(w, h)
    S, G = R["steel"], R["glass"]
    box(cv, 0, 18, w, h - 18, 0, S, front_tone=3)                     # base metálica
    for xx in range(5, w - 8, 8):
        for yy in (23, 25, 27):
            cv.rect(xx, yy, 5, 1, S[1])
    cv.rect(0, 18, w, 1, S[5])
    cv.rect(0, h - 2, w, 2, S[1])
    ds = 3
    cv.poly([(0, 6), (w - ds - 1, 6), (w - 1, 3), (ds, 3)], G[5])     # vidrio en 3D
    cv.rect(0, 6, w - ds, 12, G[3])
    cv.poly([(w - ds, 6), (w - 1, 3), (w - 1, 17), (w - ds, 18)], G[2])
    goods_row(cv, 2, w - ds - 2, 12, 3, 5)
    cv.rect(1, 12, w - ds - 2, 1, G[5])
    goods_row(cv, 2, w - ds - 2, 17, 8, 4)
    for k in range(6):                                                # reflejos
        cv.put(6 + k, 16 - k * 2, (255, 255, 255, 170))
        cv.put(7 + k, 16 - k * 2, (255, 255, 255, 110))
    for k in range(4):
        cv.put(44 + k, 15 - k * 2, (255, 255, 255, 120))
    cv.rect(0, 6, w - ds, 1, S[6])                                    # marco de aluminio
    cv.rect(0, 17, w - ds, 1, S[4])
    cv.rect(0, 6, 1, 12, S[5])
    cv.rect(w - ds - 1, 6, 1, 12, S[3])
    outline(cv, *METAL_OUT)
    return cv


def counter_metal(w=66, h=32):
    cv = Cv(w, h)
    S = R["steel"]
    fx, fy, fw, fh = box(cv, 0, 0, w, h, 5, S, top_tone=5, front_tone=4, side_tone=2)
    for xx in range(fx + 2, fx + fw - 1, 3):                          # acero cepillado
        cv.line([(xx, fy + 3), (xx, fy + fh - 5)], S[3])
    cv.rect(fx + fw // 2, fy + 3, 1, fh - 7, S[1])                    # puertas
    for hx in (fx + fw // 2 - 8, fx + fw // 2 + 3):                   # manijas
        cv.rect(hx, fy + 6, 5, 2, S[2])
        cv.rect(hx, fy + 6, 5, 1, S[6])
    cv.rect(fx, fy + fh - 4, fw, 4, R["dark"][3])                     # zócalo de goma
    cv.rect(fx, fy + fh - 4, fw, 1, R["dark"][5])
    outline(cv, *METAL_OUT)
    return cv


def register(w=24, h=20):
    cv = Cv(w, h)
    D = R["dark"]
    box(cv, 0, 9, w, h - 9, 3, D, top_tone=5, front_tone=3, side_tone=1)
    for i in range(4):                                                # teclado
        for j in range(2):
            cv.rect(3 + i * 4, 13 + j * 2, 3, 1, "#CFCDE0" if (i + j) % 3 else "#F6C43A")
    cv.rect(2, h - 3, w - 5, 1, D[1])                                 # cajón
    cv.rect(9, h - 2, 4, 1, D[5])
    box(cv, 5, 0, 12, 10, 2, D, top_tone=5, front_tone=4, side_tone=2)   # visor
    cv.rect(6, 3, 9, 4, "#0E2A1A")
    for x in (7, 9, 10, 12, 13):
        cv.put(x, 4, "#67D08E")
    cv.put(8, 5, "#67D08E")
    cv.rect(18, 2, 4, 6, "#F2E6CE")                                    # rollo de papel
    cv.rect(18, 2, 4, 1, "#FFFFFF")
    outline(cv)
    return cv


def scale(w=20, h=16):
    cv = Cv(w, h)
    S = R["steel"]
    box(cv, 0, 7, w, h - 7, 3, R["white"], top_tone=5, front_tone=3, side_tone=1)
    cv.rect(3, 11, 9, 3, "#2A1A20")
    for x in (4, 6, 7, 9, 10):
        cv.put(x, 12, "#FF6A5A")
    cv.rect(8, 5, 3, 3, S[2])
    cv.ell(9, 4, 8, 2.5, S[4])                                        # plato
    cv.ell(8, 3.5, 5, 1.2, S[6])
    outline(cv, *METAL_OUT)
    return cv


def slicer(w=24, h=18):
    cv = Cv(w, h)
    box(cv, 0, 10, w, h - 10, 3, R["red"])
    disk(cv, 10, 8, 7, R["steel"])
    for a in range(0, 360, 30):
        ang = math.radians(a)
        cv.put(int(10 + math.cos(ang) * 6.5), int(8 + math.sin(ang) * 6.5), R["steel"][6])
    disk(cv, 10, 8, 2, R["steel"][:3])
    cv.rect(17, 3, 5, 8, R["red"][4])                                 # empujador
    cv.rect(17, 3, 5, 1, R["red"][6])
    outline(cv)
    return cv


def mate_set(w=22, h=18):
    """Termo y mate sobre una repisita de pared con ménsulas (12.2: antes flotaban)."""
    cv = Cv(w, h)
    W_ = R["oak"]
    py = h - 6                                                        # tabla de la repisa
    box(cv, 0, py, w, 3, 1, W_, top_tone=5, front_tone=3)
    for bx in (3, w - 5):                                             # ménsulas
        cv.poly([(bx, py + 3), (bx + 2, py + 3), (bx + 2, h - 1)], W_[2])
        cv.line([(bx, py + 3), (bx + 2, h - 1)], W_[4])
    cylinder_v(cv, 5, 1, py - 1, 2.8, R["steel"])                     # termo
    cv.rect(2, 0, 6, 2, R["dark"][3])
    cv.rect(2, 0, 6, 1, R["dark"][5])
    disk(cv, 14, py - 4, 4.4, R["oak"])                               # mate de calabaza
    cv.rect(11, py - 9, 7, 2, R["brass"][3])                          # virola
    cv.rect(11, py - 9, 7, 1, R["brass"][5])
    cv.ell(14, py - 9, 3, 1, "#3F9E5E")                               # yerba
    cv.line([(15, py - 9), (17, py - 15)], R["steel"][5])             # bombilla
    outline(cv)
    return cv


# ================================================================== MERCADERÍA A GRANEL
def bales(w=42, h=28):
    cv = Cv(w, h)
    Wt = R["white"]
    rnd = random.Random(4)
    for x, y, bw, bh in ((7, 0, 15, 12), (21, 0, 15, 12), (0, 10, 15, 18), (14, 10, 15, 18), (27, 10, 15, 18)):
        fx, fy, fw, fh = box(cv, x, y, bw, bh, 4, Wt, top_tone=6, front_tone=4, side_tone=2)
        for k in range(10):                                           # textura de algodón
            cv.put(fx + rnd.randint(1, fw - 2), fy + rnd.randint(1, fh - 2), Wt[rnd.choice([2, 3, 5])])
        for yy in (fy + fh // 3, fy + 2 * fh // 3):                   # zunchos
            cv.rect(fx, yy, fw, 1, R["burlap"][2])
    outline(cv)
    return cv


def sack(cv, x, y, w, h, col_label, ramp=None):
    B = ramp or R["burlap"]
    body = [(x + 1, y + 6), (x + w - 2, y + 6), (x + w - 1, y + h - 3), (x + w - 3, y + h - 1), (x + 2, y + h - 1), (x, y + h - 3)]
    shade_poly(cv, body, B, 3)
    cv.poly([(x + 3, y + 1), (x + w - 4, y + 1), (x + w - 2, y + 7), (x + 1, y + 7)], B[4])  # boca fruncida
    cv.line([(x + 3, y + 1), (x + w - 4, y + 1)], B[6])
    cv.rect(x + 2, y + 5, w - 4, 1, B[1])                                 # atadura
    for yy in range(y + 9, y + h - 2, 3):                                  # trama
        for xx in range(x + 2 + (yy % 2), x + w - 2, 3):
            cv.put(xx, yy, B[2])
    lx, ly = x + w // 2 - 3, y + h // 2
    cv.rect(lx, ly, 6, 5, "#E4D6BC")                                     # etiqueta sobria
    cv.rect(lx + 1, ly + 2, 4, 1, B[2])


def sacks(w=38, h=28):
    cv = Cv(w, h)
    sack(cv, 11, 0, 15, 22, "#3F9E5E")
    sack(cv, 0, 6, 14, 22, "#D5576E")
    sack(cv, 23, 6, 15, 22, "#4E8FD8")
    outline(cv)
    return cv


def barrel_end(cv, cx, cy, r):
    disk(cv, cx, cy, r, R["oak"])
    for k in range(-int(r) + 2, int(r) - 1, 2):                         # duelas
        for yy in range(int(cy - r) + 1, int(cy + r)):
            if k * k + (yy + 0.5 - cy) ** 2 < (r - 1) ** 2:
                cv.put(int(cx + k), yy, R["oak"][2])
    for rr, col in ((r - 0.5, R["steel"][1]), (r - 3, R["steel"][2])):  # aros
        for a in range(0, 360, 8):
            ang = math.radians(a)
            cv.put(int(round(cx + math.cos(ang) * rr)), int(round(cy + math.sin(ang) * rr)), col)
    cv.put(int(cx - r * 0.5), int(cy - r * 0.6), R["steel"][6])
    disk(cv, cx + 1, cy + 1, 1.2, R["dark"])                            # tapón


def barrels_wood(w=46, h=32):
    cv = Cv(w, h)
    for cx, cy in ((15, 8), (31, 8), (7.5, 23), (23, 23), (38.5, 23)):
        barrel_end(cv, cx, cy, 7.4)
    cv.rect(2, h - 2, w - 4, 2, R["wood"][2])                           # cuñas
    outline(cv)
    return cv


def steel_tank(w=30, h=70):
    cv = Cv(w, h)
    S = R["steel"]
    for lx in (4, 23):                                                  # patas
        cv.rect(lx, h - 8, 3, 8, S[2])
        cv.rect(lx, h - 8, 1, 8, S[4])
    cylinder_v(cv, 14.5, 10, h - 11, 13.5, S, cap=False)
    for x in range(1, 29):                                              # techo cónico
        u = (x + 0.5 - 14.5) / 13.5
        top = 10 - int((1 - abs(u)) * 7)
        tone = 6 if -0.6 < u < -0.3 else (5 if u < 0.2 else 3)
        cv.rect(x, top, 1, 10 - top + 1, S[tone])
    cv.rect(13, 1, 3, 3, S[3])
    cv.rect(13, 1, 3, 1, S[6])
    for yy in (24, 44):                                                 # soldaduras
        cv.rect(2, yy, 26, 1, S[2])
    cv.rect(11, 50, 8, 5, S[1])                                         # válvula
    cv.rect(18, 51, 5, 2, R["red"][3])
    disk(cv, 9, 32, 3, R["white"])                                      # manómetro
    cv.line([(9, 32), (10, 30)], R["red"][2])
    for yy in range(16, h - 12, 4):                                     # escalera
        cv.rect(23, yy, 4, 1, S[1])
    cv.rect(23, 14, 1, h - 26, S[2])
    cv.rect(26, 14, 1, h - 26, S[2])
    outline(cv, *METAL_OUT)
    return cv


def olive_press(w=48, h=50):
    cv = Cv(w, h)
    St = R["stone"]
    box(cv, 0, 30, w, 20, 6, St)                                        # pileta de piedra
    for xx in range(4, w - 4, 7):
        cv.rect(xx, 40, 1, 8, St[2])
    disk(cv, 22, 22, 15, St)                                            # muela
    for a in range(0, 360, 20):
        ang = math.radians(a)
        cv.put(int(22 + math.cos(ang) * 12), int(22 + math.sin(ang) * 12), St[2])
    disk(cv, 22, 22, 3, R["dark"])
    cv.rect(20, 0, 5, 12, R["wood"][3])                                 # eje
    cv.rect(20, 0, 1, 12, R["wood"][5])
    cv.rect(38, 34, 9, 8, R["yellow"][3])                               # balde de aceite
    cv.rect(38, 34, 9, 2, R["yellow"][5])
    cv.rect(39, 36, 7, 2, "#7A8A1E")
    for ox, oy in ((6, 36), (10, 37), (8, 39)):                         # aceitunas
        disk(cv, ox, oy, 1.6, R["green"])
    outline(cv)
    return cv


def crate_box(cv, x, y, w, h, fruit_ramp=None, d=4):
    W = R["wood"]
    fx, fy, fw, fh = box(cv, x, y, w, h, d, W, top_tone=4, front_tone=4, side_tone=2)
    for yy in range(fy + 2, fy + fh - 1, 4):                            # tablas
        cv.rect(fx, yy, fw, 1, W[2])
    cv.rect(fx, fy, 1, fh, W[5])
    if fruit_ramp:
        rnd = random.Random(x * 7 + y)
        for i in range(fw // 3 + 1):
            fruit(cv, fx + 2 + i * 3 + rnd.random(), fy - 1 + rnd.random(), 1.9, fruit_ramp)


def crate(w=22, h=16):
    cv = Cv(w, h)
    crate_box(cv, 0, 3, w, h - 3, R["red"])
    cv.rect(4, 10, 8, 3, "#F2E6CE")
    cv.rect(5, 11, 5, 1, "#3D1B0B")
    outline(cv)
    return cv


def citrus_crates(w=42, h=30):
    cv = Cv(w, h)
    crate_box(cv, 0, 13, 21, 17, R["yellow"])
    crate_box(cv, 21, 13, 21, 17, R["orange"])
    crate_box(cv, 9, 1, 21, 15, R["orange"])
    outline(cv)
    return cv


POTATO = ["#4A2A14", "#6B4022", "#8E5A32", "#B07A48", "#C99862", "#DDB27E", "#EED0A0"]
APPLE_G = ["#2A4A10", "#3E6A16", "#5A8E1E", "#7CB02A", "#9ECC3E", "#C6E46E", "#EAF7B0"]


def bins(w, h, fruit_ramps, seed):
    cv = Cv(w, h)
    W = R["wood"]
    bw = w // 2
    for i in range(2):
        rnd = random.Random(seed + i)
        x = i * bw
        fx, fy, fw, fh = box(cv, x, 4, bw, h - 4, 6, W, top_tone=2, front_tone=4, side_tone=2)
        for k in range(16):                                              # carga apilada
            fruit(cv, fx + 2 + rnd.random() * (fw - 3), 3 + rnd.random() * 5, 2.2, fruit_ramps[(i + k) % len(fruit_ramps)])
        for yy in (fy + 4, fy + 9, fy + 14):
            if yy < fy + fh - 1:
                cv.rect(fx, yy, fw, 1, W[2])
        cv.rect(fx + 3, fy + fh - 8, 9, 4, "#F2E6CE")
        cv.rect(fx + 4, fy + fh - 7, 6, 1, "#3D1B0B")
    outline(cv)
    return cv


def potato_bins(w=48, h=28):
    return bins(w, h, [POTATO], 2)


def apple_bins(w=48, h=30):
    return bins(w, h, [R["red"], APPLE_G], 7)


def drying_rack(w=62, h=42):
    cv = Cv(w, h)
    W = R["wood"]
    for lx in (1, w - 6):
        box(cv, lx, 0, 5, h, 2, W, top_tone=5, front_tone=4, side_tone=2)
    rnd = random.Random(3)
    for r in range(3):
        y = 6 + r * 12
        box(cv, 4, y, w - 8, 6, 3, W, top_tone=4, front_tone=3, side_tone=1)
        for xx in range(6, w - 8, 3):                                     # pasas / yerba
            col = ["#5E2A4E", "#7E3E66", "#4E7A2A", "#6E9A3A"][(r * 2 + (xx // 3) % 2) % 4]
            cv.rect(xx, y - 1, 2, 2, col)
            if rnd.random() < 0.4:
                cv.put(xx, y - 2, col)
    outline(cv)
    return cv


def oven(w=54, h=58):
    cv = Cv(w, h)
    B = R["brick"]
    fx, fy, fw, fh = box(cv, 0, 8, w, h - 8, 6, B)
    for yy in range(fy + 2, fy + fh, 5):                                  # ladrillos
        cv.rect(fx, yy, fw, 1, B[2])
        for xx in range(fx + (yy // 5 % 2) * 4, fx + fw, 8):
            cv.rect(xx, yy, 1, 5, B[2])
    for yy in range(22, 46):                                              # boca en arco
        for xx in range(10, 42):
            dx = (xx - 25.5) / 15.5
            if yy >= 30 - math.sqrt(max(0, 1 - dx * dx)) * 8:
                cv.put(xx, yy, "#1A0C0C")
    rnd = random.Random(5)
    for k in range(60):                                                   # brasas
        cv.put(rnd.randint(13, 39), rnd.randint(36, 44), ["#FFE07A", "#F59A45", "#E07A2C", "#FFF6C8"][k % 4])
    for k in range(14):
        cv.put(rnd.randint(14, 38), rnd.randint(30, 36), "#B5541F")
    for xx in range(9, 43):                                               # arco claro
        dx = (xx - 25.5) / 16.5
        cv.put(xx, int(30 - math.sqrt(max(0, 1 - dx * dx)) * 9), B[5])
    cv.rect(8, 46, 36, 3, R["steel"][2])                                  # repisa de hierro
    cv.rect(8, 46, 36, 1, R["steel"][5])
    box(cv, 20, 0, 13, 10, 3, B, top_tone=5, front_tone=3, side_tone=1)           # chimenea de ladrillo
    cv.rect(21, 4, 10, 1, B[2])
    cv.rect(20, 0, 14, 2, B[1])                                           # remate
    outline(cv)
    return cv


MEAT = ["#4A1418", "#6E1E24", "#962A2E", "#B83A3C", "#D5576E", "#EE8A8F", "#FFD8D8"]


def meat_hooks(w=44, h=36):
    cv = Cv(w, h)
    S = R["steel"]
    cv.rect(0, 1, w, 2, S[4])
    cv.rect(0, 1, w, 1, S[6])
    for i, x in enumerate(range(4, w - 6, 10)):
        cv.line([(x + 3, 3), (x + 3, 7)], S[3])
        L = 22 + (i % 2) * 6
        shade_poly(cv, [(x, 8), (x + 7, 8), (x + 8, 8 + L * 0.6), (x + 6, 8 + L), (x + 1, 8 + L), (x - 1, 8 + L * 0.6)], MEAT, 3)
        cv.rect(x + 1, 12, 5, 2, "#FFF0E0")                                # grasa
        cv.line([(x + 2, 16), (x + 5, 22)], "#FFF0E0")
    outline(cv)
    return cv


def cheese_shelf(w=46, h=52):
    cv = Cv(w, h)
    W = R["oak"]
    box(cv, 0, 0, w, h, 4, W, top_tone=5, front_tone=1, side_tone=0)
    CH = ["#7A5208", "#A8780E", "#D29E22", "#F0C040", "#F8D868", "#FCEBA0", "#FFF8D8"]
    for r in range(3):
        y = 6 + r * 15
        cv.rect(2, y + 11, w - 6, 3, W[4])
        cv.rect(2, y + 11, w - 6, 1, W[6])
        for i in range(3):
            cx = 9 + i * 13
            for yy in range(y + 4, y + 11):                               # horma
                for xx in range(cx - 6, cx + 6):
                    u = (xx + 0.5 - cx) / 6
                    cv.put(xx, yy, CH[max(0, min(6, int(round((-u * 0.5 + 0.6) * 5))))])
            cv.ell(cx - 0.5, y + 4, 5.6, 1.5, CH[5])
            if (r + i) % 3 == 1:                                          # cuña cortada
                cv.poly([(cx, y + 4), (cx + 6, y + 4), (cx + 6, y + 10)], CH[6])
    outline(cv)
    return cv


def banana_hooks(w=42, h=42):
    cv = Cv(w, h)
    S = R["steel"]
    cv.rect(0, 1, w, 2, S[4])
    cv.rect(0, 1, w, 1, S[6])
    BAN = ["#6E5A08", "#9A800E", "#C8A818", "#E8CC2A", "#F6E05A", "#FFF09A", "#FFFBD8"]
    for x0 in (3, 22):
        cv.line([(x0 + 8, 3), (x0 + 8, 7)], S[2])
        cv.rect(x0 + 7, 7, 3, 4, R["green"][2])                            # pinzote
        for row in range(4):
            for k in range(4):
                bx, by = x0 + 1 + k * 4, 11 + row * 7
                shade_poly(cv, [(bx, by), (bx + 3, by), (bx + 4, by + 6), (bx + 2, by + 8), (bx + 1, by + 6)], BAN, 3 if row < 3 else 4)
                cv.put(bx + 2, by + 8, "#3D2A10")
    outline(cv)
    return cv


# ================================================================== MUEBLES Y EQUIPOS
def cafe_table(w=36, h=30):
    cv = Cv(w, h)
    D = R["dark"]
    for sx in (1, 27):                                                     # sillas de bistró
        cv.rect(sx, 6, 8, 2, R["wood"][4])
        for yy in range(8, 16, 3):
            cv.rect(sx + 1, yy, 6, 1, R["wood"][3])
        cv.rect(sx, 6, 1, 23, D[3])
        cv.rect(sx + 7, 6, 1, 23, D[3])
        cv.rect(max(0, sx - 1), 17, 10 if sx > 1 else 9, 3, R["wood"][4])
        cv.rect(max(0, sx - 1), 17, 10 if sx > 1 else 9, 1, R["wood"][6])
    cv.rect(17, 14, 2, 13, D[3])                                            # pie de hierro
    cv.rect(17, 14, 1, 13, D[5])
    cv.ell(18, 28, 6, 1.2, D[2])
    cv.ell(18, 12, 12, 3.5, R["white"][2])                                  # tapa de mármol
    cv.ell(18, 11.5, 11.5, 3, R["white"][4])
    cv.ell(15, 10.5, 6, 1.5, R["white"][6])
    cv.rect(13, 7, 4, 3, "#FFFFFF")                                         # pocillo
    cv.rect(13, 7, 4, 1, "#6D3A20")
    cv.put(17, 8, "#FFFFFF")
    cv.poly([(20, 10), (22, 8), (25, 8), (27, 10)], R["yellow"][4])         # medialuna
    cv.line([(21, 9), (26, 9)], R["yellow"][2])
    outline(cv)
    return cv


def chalkboard(w=36, h=28):
    cv = Cv(w, h)
    W = R["oak"]
    box(cv, 0, 0, w, h - 3, 2, W)
    cv.rect(3, 4, w - 7, h - 11, "#1E3A2C")
    for k in range(30):
        cv.put(4 + (k * 7) % (w - 9), 5 + (k * 5) % (h - 13), "#2A4A3A")
    M = [(5, 6), (5, 7), (5, 8), (5, 9), (6, 7), (7, 8), (8, 7), (9, 6), (9, 7), (9, 8), (9, 9),
         (11, 6), (11, 7), (11, 8), (11, 9), (12, 6), (13, 6), (12, 8), (12, 9), (13, 9),
         (15, 6), (15, 7), (15, 8), (15, 9), (16, 7), (17, 8), (18, 6), (18, 7), (18, 8), (18, 9),
         (20, 6), (20, 7), (20, 8), (21, 9), (22, 9), (23, 6), (23, 7), (23, 8), (22, 4)]
    for x, y in M:                                                          # "MENÚ" con tiza
        cv.put(x, y, "#F2EEE6")
    for i, yy in enumerate((12, 15, 18)):
        cv.rect(5, yy, 14 - i * 2, 1, "#CFC9D0")
        cv.rect(24, yy, 5, 1, "#F6C43A")
    cv.rect(2, h - 4, w - 5, 2, W[4])                                       # bandeja de tizas
    cv.rect(6, h - 5, 4, 1, "#FFFFFF")
    cv.rect(12, h - 5, 3, 1, "#F6C43A")
    outline(cv)
    return cv


def clock(w=18, h=18):
    cv = Cv(w, h)
    disk(cv, 8.5, 8.5, 8.3, R["red"])
    disk(cv, 8, 8, 6.6, R["white"][2:])
    for a in range(0, 360, 30):
        ang = math.radians(a)
        cv.put(int(round(8 + math.cos(ang) * 5.5)), int(round(8 + math.sin(ang) * 5.5)), "#4A4259" if a % 90 else "#3D1B0B")
    cv.line([(8, 8), (8, 4)], "#3D1B0B")
    cv.line([(8, 8), (11, 9)], "#3D1B0B")
    cv.put(8, 8, "#D5576E")
    cv.put(5, 4, "#FFFFFF")
    outline(cv)
    return cv


def coffee_machine(w=42, h=36):
    cv = Cv(w, h)
    S = R["steel"]
    fx, fy, fw, fh = box(cv, 0, 6, w, h - 6, 4, S, top_tone=5, front_tone=4, side_tone=2)
    for i in range(3):                                                      # pocillos arriba
        cv.rect(4 + i * 7, 1, 5, 5, "#FFFFFF")
        cv.rect(4 + i * 7, 1, 5, 1, "#E3DEE2")
        cv.rect(4 + i * 7 + 4, 2, 1, 4, "#CFC9D0")
    cv.rect(3, 13, fw - 6, 4, R["red"][3])
    cv.rect(3, 13, fw - 6, 1, R["red"][5])
    for i in range(2):                                                      # grupos cromados
        gx = 10 + i * 15
        disk(cv, gx, 20, 3, S)
        cv.line([(gx + 1, 23), (gx + 5, 24)], R["wood"][3])                # mango de madera del portafiltro
        cv.line([(gx + 1, 22), (gx + 5, 23)], R["wood"][5])
        cv.rect(gx - 2, 27, 5, 4, "#FFFFFF")                               # pocillo debajo
        cv.rect(gx - 2, 27, 5, 1, "#6D3A20")
        cv.put(gx + 3, 28, "#FFFFFF")
    cv.line([(fx + fw - 4, 18), (fx + fw - 4, 26), (fx + fw - 6, 28)], S[6])   # lanza de vapor
    disk(cv, 33, 16, 2.5, R["white"])                                       # manómetro
    cv.rect(fx + 1, fy + fh - 3, fw - 2, 2, S[1])                           # bandeja
    for xx in range(fx + 2, fx + fw - 2, 2):
        cv.put(xx, fy + fh - 3, S[5])
    outline(cv, *METAL_OUT)
    return cv


def conveyor(w=112, h=38):
    """Cinta: la superficie va en las filas 9..16 (ahí corre la animación fx_conveyor)."""
    cv = Cv(w, h)
    S, D = R["steel"], R["dark"]
    for lx in (4, w // 2 - 2, w - 9):                                       # patas
        box(cv, lx, 16, 5, h - 16, 2, S, top_tone=4, front_tone=3, side_tone=1)
    cv.rect(6, h - 8, w - 12, 2, S[2])
    cv.rect(6, h - 8, w - 12, 1, S[4])
    box(cv, 0, 6, w, 14, 3, S, top_tone=5, front_tone=3, side_tone=1)       # bastidor
    cv.rect(1, 9, w - 4, 8, D[2])                                           # banda
    for xx in range(2, w - 4, 6):
        cv.rect(xx, 9, 1, 8, D[4])
    for xx in range(4, w - 4, 10):                                          # rodillos
        disk(cv, xx, 18, 1.6, S)
    cv.rect(0, 17, w - 2, 1, S[5])
    for bx in (12, 46, 80):                                                 # cajas
        box(cv, bx, 0, 14, 10, 3, R["card"])
        cv.rect(bx + 5, 3, 3, 7, R["card"][6])
    outline(cv, *METAL_OUT)
    return cv


def cooler(w=32, h=24):
    cv = Cv(w, h)
    fx, fy, fw, fh = box(cv, 0, 3, w, h - 3, 5, R["red"], top_tone=6, front_tone=3, side_tone=1)
    cv.rect(0, 3, w - 2, 5, R["white"][5])                                  # tapa
    cv.rect(0, 3, w - 2, 1, "#FFFFFF")
    cv.rect(8, 0, 12, 3, R["white"][3])                                     # manija
    cv.rect(8, 0, 12, 1, "#FFFFFF")
    cv.rect(fx + 3, fy + 6, 10, 4, R["white"][5])
    cv.rect(fx + 4, fy + 7, 8, 1, R["blue"][3])
    outline(cv)
    return cv


def desk_pc(w=54, h=40):
    cv = Cv(w, h)
    W = R["wood"]
    fx, fy, fw, fh = box(cv, 0, 18, w, 22, 5, W)
    cv.rect(fx + fw - 18, fy + 2, 15, fh - 4, W[2])                         # cajonera
    for yy in (fy + 5, fy + 10):
        cv.rect(fx + fw - 17, yy, 13, 1, W[1])
        cv.rect(fx + fw - 12, yy - 2, 3, 1, R["brass"][4])
    box(cv, 10, 0, 24, 17, 3, R["dark"], top_tone=4, front_tone=3, side_tone=1)   # monitor
    cv.rect(12, 5, 18, 10, "#1E4A6E")
    for yy in range(6, 14, 2):
        cv.rect(13, yy, 6 + (yy * 3) % 9, 1, "#67D08E" if yy % 4 else "#8FC4FF")
    cv.rect(19, 17, 4, 3, R["dark"][3])
    cv.rect(6, 21, 20, 2, R["white"][3])                                    # teclado
    for xx in range(7, 25, 2):
        cv.put(xx, 21, R["white"][1])
    cv.rect(30, 21, 4, 2, R["white"][4])                                    # mouse
    cv.rect(40, 14, 7, 7, "#FFFFFF")                                        # taza
    cv.rect(40, 14, 7, 1, "#6D3A20")
    outline(cv)
    return cv


def fileteado_sign(w=72, h=20):
    cv = Cv(w, h)
    box(cv, 0, 0, w, h, 2, R["dark"], top_tone=4, front_tone=1, side_tone=0)
    cv.rect(3, 4, w - 7, h - 7, "#1A1420")
    for x in range(3, w - 4):                                               # filetes dorados
        cv.put(x, 4, R["brass"][4])
        cv.put(x, h - 4, R["brass"][3])
    for cx in (12, w - 14):                                                 # volutas y flores
        for a in range(0, 300, 20):
            ang = math.radians(a)
            r = 2 + a / 120
            cv.put(int(cx + math.cos(ang) * r), int(10 + math.sin(ang) * r * 0.8), R["brass"][4])
        disk(cv, cx, 10, 2.2, R["red"])
        cv.put(cx - 4, 7, R["green"][4])
        cv.put(cx + 4, 13, R["green"][4])
    for i, x in enumerate(range(22, w - 22, 4)):                            # guarda celeste y blanca
        cv.rect(x, 9, 2, 3, ["#74ACDF", "#FFFFFF"][i % 2])
    outline(cv)
    return cv


def forklift(w=52, h=44):
    cv = Cv(w, h)
    Y, D = R["yellow"], R["dark"]
    cv.rect(6, 2, 3, 34, D[3])                                              # mástil
    cv.rect(10, 2, 3, 34, D[3])
    cv.rect(6, 2, 1, 34, D[5])
    for yy in range(4, 34, 6):
        cv.rect(6, yy, 7, 1, D[2])
    cv.rect(0, 33, 14, 3, R["steel"][3])                                    # horquillas
    cv.rect(0, 33, 14, 1, R["steel"][6])
    box(cv, 0, 22, 10, 11, 3, R["card"])                                    # caja levantada
    box(cv, 13, 22, 37, 16, 5, Y, top_tone=5, front_tone=4, side_tone=2)    # carrocería
    cv.rect(38, 24, 11, 10, D[2])                                           # contrapeso
    cv.rect(38, 24, 11, 1, D[4])
    for k in range(5):                                                      # advertencia
        cv.line([(15 + k * 4, 34), (18 + k * 4, 31)], D[2])
    cv.rect(16, 2, 2, 20, D[3])                                             # jaula
    cv.rect(36, 2, 2, 20, D[3])
    cv.rect(16, 2, 22, 2, D[3])
    cv.rect(16, 2, 22, 1, D[5])
    cv.rect(24, 14, 9, 8, D[4])                                             # asiento
    cv.rect(23, 9, 3, 6, D[4])
    cv.line([(19, 20), (21, 14)], D[1])                                     # volante
    disk(cv, 21, 14, 2, D)
    cv.rect(37, 0, 3, 3, "#F59A45")                                         # baliza
    for wx, r in ((20, 5.5), (43, 5)):                                      # ruedas
        disk(cv, wx, h - 6, r, D)
        disk(cv, wx, h - 6, r * 0.45, R["steel"])
    outline(cv)
    return cv


def freezer(w=48, h=32):
    """Freezer de pozo (con letras: HELADOS)."""
    cv = Cv(w, h)
    Wt = R["white"]
    fx, fy, fw, fh = box(cv, 0, 0, w, h, 8, Wt, top_tone=5, front_tone=4, side_tone=2)
    cv.poly([(2, 7), (fw - 3, 7), (fw + 2, 1), (5, 1)], R["glass"][3])      # tapa de vidrio
    for i, col in enumerate(("#F08C8F", "#FFE07A", "#8B5A3C", "#B6F0B0", "#FFFFFF", "#D0A0E0")):
        cv.rect(8 + i * 6, 3, 4, 3, col)
        cv.put(8 + i * 6, 3, "#FFFFFF")
    for k in range(5):
        cv.put(10 + k * 2, 6 - k, (255, 255, 255, 150))
    cv.rect(fx + 4, fy + 6, fw - 8, 9, R["blue"][3])                        # cartel
    cv.rect(fx + 4, fy + 6, fw - 8, 1, R["blue"][5])
    LET = {"H": ["101", "111", "101"], "E": ["111", "110", "111"], "L": ["100", "100", "111"],
           "A": ["010", "111", "101"], "D": ["110", "101", "110"], "O": ["111", "101", "111"], "S": ["011", "010", "110"]}
    x = fx + 9
    for ch in "HELADOS":
        for j, row in enumerate(LET[ch]):
            for i, b in enumerate(row):
                if b == "1":
                    cv.put(x + i, fy + 9 + j, "#FFFFFF")
        x += 4
    cv.rect(fx + 3, fy + fh - 5, fw - 6, 1, Wt[1])                          # rejilla
    cv.rect(fx + 3, fy + fh - 3, fw - 6, 1, Wt[1])
    outline(cv, *METAL_OUT)
    return cv


def lamp_hanging(w=16, h=18):
    cv = Cv(w, h)
    cv.rect(7, 0, 1, 6, R["dark"][2])
    shade_poly(cv, [(4, 6), (11, 6), (15, 13), (0, 13)], R["green"], 3)     # pantalla esmaltada
    cv.rect(1, 12, 14, 1, R["green"][5])
    cv.line([(5, 6), (10, 6)], R["green"][6])
    cv.ell(7.5, 14.5, 3.5, 2, "#FFF6C8")                                    # lamparita
    cv.ell(7, 14, 1.5, 1, "#FFFFFF")
    outline(cv)
    for x in range(2, 14):                                                  # resplandor
        if not cv.opaque(x, 17):
            cv.put(x, 17, (255, 240, 180, 60))
    return cv


def machine(w=52, h=58):
    cv = Cv(w, h)
    B, S = R["blue"], R["steel"]
    fx, fy, fw, fh = box(cv, 0, 10, w, h - 10, 6, B)
    cv.poly([(10, 0), (32, 0), (28, 10), (14, 10)], S[3])                   # tolva
    cv.line([(10, 0), (32, 0)], S[6])
    cv.rect(12, 1, 18, 2, R["burlap"][4])
    cv.rect(5, 20, 20, 13, R["dark"][2])                                    # pantalla
    cv.rect(6, 21, 18, 11, "#0E3A2A")
    for yy in range(23, 31, 2):
        cv.rect(8, yy, 4 + (yy * 5) % 11, 1, "#67D08E")
    for i, rp in enumerate(("green", "yellow", "red")):                     # botones
        disk(cv, 32 + i * 5, 24, 1.8, R[rp])
    disk(cv, 37, 34, 5, S)                                                  # perilla
    for a in range(0, 360, 45):
        ang = math.radians(a)
        cv.put(int(37 + math.cos(ang) * 5.5), int(34 + math.sin(ang) * 5.5), S[1])
    for xx in range(fx, fx + fw):                                           # franja de advertencia
        cv.rect(xx, fy + fh - 7, 1, 3, "#F6C43A" if (xx // 3) % 2 else "#2A2534")
    cv.rect(fx, fy + fh - 3, fw, 3, S[1])
    cv.rect(fw - 2, 40, 5, 4, S[3])                                         # caño de salida
    outline(cv)
    return cv


def pallet(cv, x, y, w):
    W = R["wood"]
    cv.rect(x, y, w, 2, W[4])
    cv.rect(x, y, w, 1, W[6])
    for bx in range(x, x + w - 2, max(1, (w - 3) // 2)):
        cv.rect(bx, y + 2, 3, 2, W[2])
    cv.rect(x, y + 4, w, 1, W[3])


def pallet_boxes(w=36, h=32):
    cv = Cv(w, h)
    pallet(cv, 0, h - 5, w - 2)
    for bx, by in ((0, 13), (16, 13), (6, 0)):
        box(cv, bx, by, 18, 15 if by else 14, 4, R["card"])
        cv.rect(bx + 7, by, 3, 4, R["card"][6])
        cv.rect(bx + 2, by + 8, 6, 3, "#FFFFFF")
        cv.rect(bx + 3, by + 9, 4, 1, "#3D1B0B")
    outline(cv)
    for xx in range(2, w - 4, 5):                                           # film (sólo sobre las cajas)
        y = 6 + xx % 7
        if cv.opaque(xx, y) and cv.get(xx, y)[:3] != (0x3D, 0x1B, 0x0B):
            r, g, bb, _ = cv.get(xx, y)
            cv.put(xx, y, (min(255, r + 50), min(255, g + 50), min(255, bb + 50), 255))
    return cv


def pallet_rack(w=82, h=82):
    cv = Cv(w, h)
    B, O = R["blue"], R["orange"]
    for ux in (0, w - 6):                                                   # parantes perforados
        box(cv, ux, 0, 6, h, 2, B)
        for yy in range(3, h - 2, 4):
            cv.put(ux + 2, yy, B[0])
    for lvl in range(3):
        by = 24 + lvl * 27
        cv.rect(5, by, w - 10, 3, O[3])                                     # largueros
        cv.rect(5, by, w - 10, 1, O[5])
        pallet(cv, 8, by - 5, w - 18)
        rnd = random.Random(lvl)
        xx = 9
        while xx < w - 26:
            bw, bh = rnd.randint(14, 20), rnd.randint(10, 16)
            box(cv, xx, by - 5 - bh, bw, bh, 3, R["card"] if rnd.random() < 0.7 else R["white"])
            cv.rect(xx + bw // 2 - 1, by - 5 - bh + 1, 2, bh - 1, R["card"][6])
            xx += bw + 1
    cv.rect(0, h - 2, w, 2, B[1])
    outline(cv)
    return cv


def pastry_case(w=62, h=36):
    cv = Cv(w, h)
    W, G = R["oak"], R["glass"]
    box(cv, 0, 18, w, h - 18, 0, W, front_tone=3)
    cv.rect(2, 22, w - 4, 8, W[2])
    cv.rect(3, 23, w - 6, 6, W[3])
    cv.poly([(0, 6), (w - 4, 6), (w - 1, 2), (3, 2)], G[5])
    cv.rect(0, 6, w - 3, 12, G[3])
    cv.poly([(w - 3, 6), (w - 1, 2), (w - 1, 17), (w - 3, 18)], G[2])
    for row, yy in enumerate((10, 15)):                                     # medialunas
        for i in range(7):
            cx = 5 + i * 8 + row * 3
            if cx > w - 9:
                continue
            cv.poly([(cx, yy + 2), (cx + 2, yy - 1), (cx + 5, yy - 1), (cx + 7, yy + 2)], R["yellow"][4] if (i + row) % 3 else R["orange"][4])
            cv.line([(cx + 1, yy + 1), (cx + 6, yy + 1)], R["yellow"][2])
            cv.put(cx + 3, yy - 1, R["yellow"][6])
    cv.rect(1, 12, w - 5, 1, G[5])
    for k in range(5):
        cv.put(8 + k, 16 - k * 2, (255, 255, 255, 160))
    outline(cv)
    return cv


def pennant(w=40, h=14):
    cv = Cv(w, h)
    pts = [(x, 2 + int(3 * math.sin(math.pi * x / (w - 1)))) for x in range(w)]
    for x, y in pts:
        cv.put(x, y, R["dark"][3])
    for i, x0 in enumerate(range(1, w - 6, 7)):                            # banderines
        y0 = pts[x0][1] + 1
        col = ["#74ACDF", "#FFFFFF", "#F6C43A"][i % 3]
        cv.poly([(x0, y0), (x0 + 6, y0), (x0 + 3, y0 + 8)], col)
        cv.line([(x0 + 4, y0 + 1), (x0 + 3, y0 + 7)], "#CFC9D0" if col == "#FFFFFF" else "#3E74B8" if col == "#74ACDF" else "#C07A12")
        cv.line([(x0, y0), (x0 + 6, y0)], "#FFFFFF" if col != "#FFFFFF" else "#E3DEE2")
    outline(cv)
    return cv


def plant(w=20, h=30):
    cv = Cv(w, h)
    rnd = random.Random(9)
    for k in range(9):                                                      # hojas con volumen
        ang = -math.pi / 2 + (k - 4) * 0.33
        L = 9 + rnd.randint(0, 4)
        HA.capsule(cv, (10, 16), (10 + math.cos(ang) * L, 16 + math.sin(ang) * L), 2.2, R["green"], bias=0.2)
    cylinder_v(cv, 10, 18, 27, 6.5, R["brick"], cap=False)                 # maceta de barro
    cv.rect(3, 16, 15, 3, R["brick"][4])
    cv.rect(3, 16, 15, 1, R["brick"][6])
    outline(cv)
    return cv


def poster(w=22, h=28):
    cv = Cv(w, h)
    box(cv, 0, 0, w, h, 2, R["oak"])
    cv.rect(2, 3, w - 5, h - 6, "#F2E6CE")
    cv.rect(3, 4, w - 7, 10, "#74ACDF")                                     # paisaje
    cv.rect(3, 11, w - 7, 3, "#3F9E5E")
    disk(cv, 13, 7, 2.5, R["yellow"])
    cv.rect(4, 16, 12, 2, "#D5576E")
    for yy in (19, 21):
        cv.rect(4, yy, 10 - (yy % 3), 1, "#8E8496")
    outline(cv)
    return cv


def prep_table(w=58, h=38):
    cv = Cv(w, h)
    S = R["steel"]
    box(cv, 0, 6, w, 6, 4, S, top_tone=5, front_tone=4, side_tone=2)        # mesada
    for lx in (2, w - 7):                                                   # patas
        cv.rect(lx, 12, 3, h - 12, S[3])
        cv.rect(lx, 12, 1, h - 12, S[5])
    cv.rect(3, h - 9, w - 8, 3, S[3])                                       # estante de abajo
    cv.rect(3, h - 9, w - 8, 1, S[5])
    box(cv, 8, h - 17, 14, 8, 2, R["card"])
    box(cv, 6, 1, 22, 7, 2, R["wood"], top_tone=5, front_tone=4, side_tone=2)   # tabla de picar
    cv.line([(30, 4), (38, 4)], S[6])                                       # cuchilla
    cv.rect(38, 3, 4, 2, R["dark"][3])
    fruit(cv, 46, 4, 2.5, R["red"])
    fruit(cv, 51, 5, 2.3, R["green"])
    outline(cv, *METAL_OUT)
    return cv


SAL = ["#3E1414", "#5A1E1E", "#7A2A26", "#963A30", "#B05040", "#C87060", "#E0A090"]


def salames(w=30, h=22):
    cv = Cv(w, h)
    cv.rect(0, 1, w, 2, R["wood"][3])
    cv.rect(0, 1, w, 1, R["wood"][5])
    for i, x in enumerate(range(2, w - 4, 6)):
        cv.line([(x + 2, 3), (x + 2, 5)], "#F2E6CE")
        L = 9 + (i % 2) * 4
        HA.capsule(cv, (x + 2, 8), (x + 2, 6 + L), 2.4, SAL, bias=0.1)
        for yy in range(9, 6 + L, 3):                                       # hilo
            cv.put(x + 1, yy, "#F2E6CE")
            cv.put(x + 3, yy + 1, "#F2E6CE")
    outline(cv)
    return cv


def shelf(w, h, ramp, metal=False, seed=1):
    cv = Cv(w, h)
    fx, fy, fw, fh = box(cv, 0, 0, w, h, 4, ramp, top_tone=5, front_tone=1, side_tone=0)
    cv.rect(fx + 2, fy, fw - 4, fh - 2, R["dark"][2] if metal else ramp[0])   # fondo
    for i in range(4):
        by = fy + 2 + (i + 1) * (fh - 4) // 4
        goods_row(cv, fx + 3, fx + fw - 3, by - 1, seed + i, 9)
        cv.rect(fx + 1, by - 1, fw - 2, 2, ramp[4])
        cv.rect(fx + 1, by - 1, fw - 2, 1, ramp[6])
    cv.rect(fx, fy, 2, fh, ramp[3])
    cv.rect(fx + fw - 2, fy, 2, fh, ramp[2])
    if metal:
        for yy in range(fy + 2, fy + fh, 4):
            cv.put(fx + 1, yy, ramp[1])
    outline(cv, *(METAL_OUT if metal else (OUTL, OUTL_L)))
    return cv


def wall_shelf(w=70, h=22):
    cv = Cv(w, h)
    goods_row(cv, 4, w - 6, 16, 11, 12)
    box(cv, 0, 15, w, 6, 3, R["oak"])
    for bx in (8, w - 14):                                                  # ménsulas
        cv.rect(bx, 21, 5, 1, R["dark"][3])
    outline(cv)
    return cv


def wine_rack(w=32, h=58):
    cv = Cv(w, h)
    W = R["wood"]
    fx, fy, fw, fh = box(cv, 0, 0, w, h, 4, W, top_tone=5, front_tone=1, side_tone=0)
    cv.rect(fx + 2, fy + 2, fw - 4, fh - 4, "#1E100C")
    cols = ["#5E1E2E", "#2E4A1E", "#7A2A3A", "#E8D8A0"]
    for r in range(6):
        for c in range(3):
            cx, cy = fx + 5 + c * 8, fy + 6 + r * 8
            disk(cv, cx, cy, 3.2, ["#140A0A", "#140A0A", cols[(r + c) % 4], cols[(r + c) % 4], cols[(r + c) % 4], "#B8A890", "#FFFFFF"])
            cv.put(cx - 1, cy - 1, "#F2E6CE")
    for r in range(7):                                                      # celdas
        cv.rect(fx + 2, fy + 2 + r * 8, fw - 4, 1, W[3])
    for c in range(4):
        cv.rect(fx + 1 + c * 8, fy + 2, 1, fh - 4, W[3])
    outline(cv)
    return cv


def electronics_bench(w=72, h=42):
    cv = Cv(w, h)
    fx, fy, fw, fh = box(cv, 0, 20, w, 22, 5, R["wood"])
    for i in range(3):                                                      # cajoncitos
        cv.rect(fx + 4 + i * 12, fy + 7, 10, 7, R["wood"][2])
        cv.rect(fx + 8 + i * 12, fy + 10, 3, 1, R["brass"][4])
    box(cv, 4, 6, 22, 15, 3, R["stone"])                                    # osciloscopio
    cv.rect(6, 11, 11, 8, "#0E2A1A")
    for x in range(6, 17):
        cv.put(x, 15 + int(2 * math.sin(x * 0.9)), "#67D08E")
    for i in range(2):
        disk(cv, 21, 12 + i * 4, 1.5, R["dark"])
    cv.rect(32, 17, 18, 5, R["green"][2])                                   # placa
    cv.rect(32, 17, 18, 1, R["green"][4])
    for x in (34, 39, 44):
        cv.rect(x, 18, 3, 2, R["dark"][2])
    cv.line([(54, 20), (62, 12)], R["dark"][4])                             # soldador
    cv.put(62, 12, R["orange"][4])
    disk(cv, 66, 8, 3, R["glass"])                                          # lupa
    cv.line([(66, 11), (66, 20)], R["steel"][3])
    outline(cv)
    return cv


# ================================================================== catálogo
PIECES = {
    "_counter_wood": counter_wood, "_counter_glass": counter_glass, "_counter_metal": counter_metal,
    "_register": register, "_scale": scale, "_slicer": slicer, "_mate_set": mate_set,
    "_bales": bales, "_sacks": sacks, "_barrels_wood": barrels_wood, "_steel_tank": steel_tank,
    "_olive_press": olive_press, "_citrus_crates": citrus_crates, "_crate": crate,
    "_potato_bins": potato_bins, "_apple_bins": apple_bins, "_drying_rack": drying_rack, "_oven": oven,
    "_meat_hooks": meat_hooks, "_cheese_shelf": cheese_shelf, "_banana_hooks": banana_hooks,
    "_cafe_table": cafe_table, "_chalkboard": chalkboard, "_clock": clock, "_coffee_machine": coffee_machine,
    "_conveyor": conveyor, "_cooler": cooler, "_desk_pc": desk_pc, "_fileteado_sign": fileteado_sign,
    "_forklift": forklift, "_freezer": freezer, "_lamp_hanging": lamp_hanging, "_machine": machine,
    "_pallet_boxes": pallet_boxes, "_pallet_rack": pallet_rack, "_pastry_case": pastry_case,
    "_pennant": pennant, "_plant": plant, "_poster": poster, "_prep_table": prep_table, "_salames": salames,
    "_shelf_wood": lambda w, h: shelf(w, h, R["oak"], seed=3),
    "_shelf_metal": lambda w, h: shelf(w, h, R["steel"], True, seed=8),
    "_wall_shelf": wall_shelf, "_wine_rack": wine_rack, "_electronics_bench": electronics_bench,
}


import props_art2  # noqa: E402  (12.2: piezas nuevas y redibujadas)
props_art2.register(PIECES)


def render(name, size):
    """Dibuja la pieza al tamaño exacto (w, h) de gen_interiors.SZ.

    12.2: se pinta 2 px más chica y se centra, así el contorno entra entero en
    los cuatro lados (antes las 46 piezas tocaban el borde del lienzo y se veían
    cortadas en seco). Después pasa por finish(): contorno selectivo y luz."""
    w, h = size
    cv = PIECES[name](w - 2, h - 2)
    if cv.img.size != (w - 2, h - 2):
        raise SystemExit(f"{name}: mide {cv.img.size}, se esperaba {(w - 2, h - 2)}")
    big = Cv(w, h)
    big.img.alpha_composite(cv.img, (1, 1))
    big.outline(OUTL, OUTL_L)
    return finish(big.img)


def finish(img):
    """Terminación profesional de cada pieza:
    - contorno selectivo ("selout"): el contorno toma el tono oscuro del color
      que rodea en vez de ser siempre marrón (menos "recortado"), salvo abajo,
      donde la pieza apoya y queda bien marcado;
    - luz de borde: la primera fila/columna de cada forma del lado de la luz
      (arriba-izquierda) sube un poco; la del lado contrario baja (volumen);
    - oclusión al pie: las 2 filas de abajo se oscurecen levemente."""
    import numpy as np
    a = np.array(img).astype(np.int32)
    al = a[:, :, 3] > 0
    rgb = a[:, :, :3]
    H, W = al.shape
    outl = np.zeros_like(al)
    o1 = np.array([0x3D, 0x1B, 0x0B])
    o2 = np.array([0x8E, 0x46, 0x1F])
    m1 = (rgb == o1).all(axis=2) & al
    m2 = (rgb == o2).all(axis=2) & al
    m3 = (rgb == np.array([0x2E, 0x2B, 0x3E])).all(axis=2) & al        # contorno metálico
    m4 = (rgb == np.array([0x65, 0x62, 0x7E])).all(axis=2) & al
    outl = m1 | m2 | m3 | m4
    pad = np.pad(al & ~outl, 1)
    inner_n = [pad[1:-1, 2:], pad[1:-1, :-2], pad[2:, 1:-1], pad[:-2, 1:-1]]
    shifts = [(0, -1), (0, 1), (-1, 0), (1, 0)]
    out = a.copy()
    # el color de adentro más cercano, oscurecido, para el contorno
    acc = np.zeros((H, W, 3))
    cnt = np.zeros((H, W))
    for (dy, dx), has in zip(shifts, inner_n):
        nb = np.roll(rgb, (dy, dx), axis=(0, 1))
        sel = outl & has
        acc[sel] += nb[sel]
        cnt[sel] += 1
    have = cnt > 0
    avg = acc[have] / cnt[have][:, None]
    lum = avg.mean(axis=1, keepdims=True)
    dark = np.clip(avg * 0.42 + np.array([0x3D, 0x1B, 0x0B]) * 0.35 - 6, 0, 255)
    sel_idx = np.argwhere(have)
    # abajo (apoyo) queda el contorno marrón fuerte
    bottom = np.zeros((H, W), dtype=bool)
    below = np.pad(al, 1)[2:, 1:-1]
    bottom = outl & ~below
    for (y, x), c in zip(sel_idx, dark):
        if not bottom[y, x]:
            out[y, x, :3] = c
    # luz de borde y sombra del lado opuesto, sólo en el interior de la forma
    body = al & ~outl
    lp = np.pad(body, 1)
    up_out = ~lp[:-2, 1:-1]
    left_out = ~lp[1:-1, :-2]
    down_out = ~lp[2:, 1:-1]
    right_out = ~lp[1:-1, 2:]
    lit = body & (up_out | left_out) & ~(down_out | right_out)
    shd = body & (down_out | right_out) & ~(up_out | left_out)
    out[lit, :3] = np.clip(out[lit, :3] * 1.1 + 10, 0, 255)
    out[shd, :3] = np.clip(out[shd, :3] * 0.86, 0, 255)
    # oclusión al pie (las 2 filas de abajo de cada columna con cuerpo)
    ys = np.arange(H)[:, None]
    last = np.where(body.any(axis=0), H - 1 - np.argmax(body[::-1, :], axis=0), -10)
    foot = body & (ys >= last[None, :] - 1)
    out[foot, :3] = np.clip(out[foot, :3] * 0.88, 0, 255)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


def main():
    sys.path.insert(0, os.path.join(HERE, "pxl"))
    import gen_interiors as g
    os.makedirs(OUT, exist_ok=True)
    for name in PIECES:
        render(name, g.SZ[name]).save(os.path.join(OUT, name + ".png"))
    print("utilería:", len(PIECES), "piezas en", OUT)


if __name__ == "__main__":
    main()
