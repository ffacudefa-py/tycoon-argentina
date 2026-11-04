"""12.2: utilería nueva y redibujada de los interiores (se registra en props_art.PIECES).

Corrige lo que marcó la revisión de arte de 12.2:
  - una máquina propia por rubro (prensa hidráulica, molino, amasadora) en vez del
    mismo bloque azul en todos lados (_machine queda para empaque/frutas);
  - colgantes con ménsulas y ganchos en S (carne, bananas, salames);
  - carne en cuartos con hueso y grasa, de silueta variada;
  - barriles acostados de costado (duelas, dos zunchos, tapa) en vez de "monedas";
  - fardos de algodón abombados con flejes;
  - cartel fileteado con "BIENVENIDOS" legible;
  - mesa de bar a escala humana y una cafetera chica de mostrador;
  - detalles fijos de pared: tablero eléctrico con su caño, almanaque y enchufe;
  - estantería de pan para la panadería; el freezer dice FRIO (no "HELADOS").
Todas se pintan al tamaño que pide props_art.render (2 px menos que gen_interiors.SZ).
Lo llama props_art.py al final (register(PIECES)).
"""
import math
import random

import props_art as P
from props_art import R, box, cylinder_v, disk, outline, METAL_OUT
from minigames_art2 import Cv, shade_poly

LET = {
    "A": ["010", "101", "111", "101", "101"], "B": ["110", "101", "110", "101", "110"],
    "D": ["110", "101", "101", "101", "110"], "E": ["111", "100", "110", "100", "111"],
    "F": ["111", "100", "110", "100", "100"], "I": ["111", "010", "010", "010", "111"],
    "N": ["101", "111", "111", "111", "101"], "O": ["111", "101", "101", "101", "111"],
    "R": ["110", "101", "110", "101", "101"], "S": ["011", "100", "010", "001", "110"],
    "V": ["101", "101", "101", "101", "010"], "M": ["101", "111", "111", "101", "101"],
    "L": ["100", "100", "100", "100", "111"], "C": ["011", "100", "100", "100", "011"],
}


def text(cv, x, y, s, col, shadow=None):
    for ch in s:
        g = LET.get(ch)
        if g:
            for j, row in enumerate(g):
                for i, b in enumerate(row):
                    if b == "1":
                        if shadow:
                            cv.put(x + i + 1, y + j + 1, shadow)
                        cv.put(x + i, y + j, col)
        x += 4


def text_w(s):
    return len(s) * 4 - 1


def bracket(cv, x, y, w=4, h=5, ramp=None):
    """Ménsula de pared en escuadra (sostiene la barra de un colgante)."""
    S = ramp or R["steel"]
    cv.rect(x, y, 2, h, S[2])
    cv.put(x, y, S[5])
    cv.line([(x + 1, y + h - 1), (x + w, y)], S[3])
    cv.rect(x, y + h - 1, 2, 1, S[1])


def s_hook(cv, x, y, S):
    cv.put(x, y, S[5])
    cv.put(x + 1, y + 1, S[4])
    cv.put(x, y + 2, S[3])
    cv.put(x - 1, y + 3, S[3])
    cv.put(x, y + 4, S[4])


# ------------------------------------------------------------------ pared
def elec_panel(w=14, h=42):
    """Tablero eléctrico gris con caño que sube hasta el cielorraso y calco de peligro."""
    cv = Cv(w, h)
    S = R["steel"]
    cv.rect(5, 0, 3, h - 18, S[3])                                    # caño
    cv.rect(5, 0, 1, h - 18, S[5])
    cv.rect(7, 0, 1, h - 18, S[1])
    for yy in (6, 16):                                                # grampas
        cv.rect(4, yy, 5, 2, S[2])
        cv.put(4, yy, S[5])
    fx, fy, fw, fh = box(cv, 0, h - 20, w, 20, 2, S, top_tone=5, front_tone=3, side_tone=1)
    cv.rect(fx + 1, fy + 1, fw - 2, fh - 3, S[4])                     # puerta
    cv.line([(fx + 1, fy + 1), (fx + fw - 2, fy + 1)], S[6])
    cv.rect(fx + fw - 3, fy + 6, 1, 4, S[1])                          # manija
    cv.poly([(fx + 4, fy + 12), (fx + 6, fy + 8), (fx + 8, fy + 12)], "#F6C43A")   # calco de peligro
    cv.put(fx + 6, fy + 10, "#2A2534")
    outline(cv, *METAL_OUT)
    return cv


def calendar(w=14, h=18):
    """Almanaque de pared colgado de un clavo: encabezado, foto y grilla de días."""
    cv = Cv(w, h)
    Wt = R["white"]
    cv.put(w // 2, 0, R["dark"][2])                                   # clavo
    cv.line([(w // 2, 0), (2, 3)], R["dark"][4])
    cv.line([(w // 2, 0), (w - 3, 3)], R["dark"][4])
    cv.rect(1, 3, w - 2, h - 3, Wt[4])
    cv.rect(1, 3, w - 2, 1, Wt[6])
    cv.rect(2, 4, w - 4, 5, R["blue"][4])                             # foto: cielo y cerro
    cv.poly([(2, 9), (6, 5), (9, 7), (w - 3, 5), (w - 3, 9)], R["green"][3])
    cv.rect(2, 9, w - 4, 2, R["red"][3])                              # mes
    for r in range(3):
        for c in range(4):
            cv.put(3 + c * 2, 12 + r * 2, Wt[1] if (r * 4 + c) % 7 else R["red"][3])
    cv.rect(1, h - 1, w - 2, 1, Wt[2])
    outline(cv)
    return cv


def outlet(w=6, h=6):
    cv = Cv(w, h)
    Wt = R["white"]
    cv.rect(0, 0, w, h, Wt[4])
    cv.rect(0, 0, w, 1, Wt[6])
    cv.rect(0, h - 1, w, 1, Wt[2])
    cv.put(2, 2, R["dark"][2])
    cv.put(3, 2, R["dark"][2])
    cv.put(2, 4, R["dark"][3])
    outline(cv)
    return cv


# ------------------------------------------------------------------ máquinas por rubro
def _hazard(cv, x, y, w):
    for xx in range(x, x + w):
        cv.rect(xx, y, 1, 2, "#F6C43A" if (xx // 3) % 2 else "#2A2534")


def machine_press(w=50, h=56):
    """Prensa hidráulica de fardos (algodón, lana, aceitunas, uva): dos columnas,
    cilindro arriba, vástago cromado y la plancha apretando un fardo con flejes."""
    cv = Cv(w, h)
    O, S = R["orange"], R["steel"]
    box(cv, 0, h - 8, w, 8, 2, R["dark"], top_tone=5, front_tone=3)                  # base
    for cx in (4, w - 10):                                                           # columnas
        box(cv, cx, 6, 6, h - 14, 2, O, top_tone=5, front_tone=3, side_tone=1)
    box(cv, 0, 2, w, 9, 3, O, top_tone=5, front_tone=3, side_tone=1)                 # travesaño
    cylinder_v(cv, w // 2 - 1, 0, 9, 6, S)                                           # cilindro
    cv.rect(w // 2 - 2, 11, 3, 10, S[5])                                             # vástago
    cv.rect(w // 2 - 2, 11, 1, 10, S[6])
    box(cv, 9, 21, w - 20, 5, 2, S, top_tone=5, front_tone=3)                        # plancha
    Wt = R["white"]
    fx, fy, fw, fh = box(cv, 11, 26, w - 24, h - 34, 3, Wt, top_tone=6, front_tone=4, side_tone=2)   # fardo
    rnd = random.Random(3)
    for k in range(14):
        cv.put(fx + rnd.randint(1, fw - 2), fy + rnd.randint(1, fh - 2), Wt[rnd.choice([2, 3, 6])])
    for yy in (fy + 4, fy + fh - 5):
        cv.rect(fx, yy, fw, 1, S[2])
    _hazard(cv, 1, h - 6, w - 4)
    cv.rect(w - 9, 30, 6, 8, R["dark"][3])                                           # botonera
    disk(cv, w - 6, 33, 1.4, R["red"])
    disk(cv, w - 6, 36, 1.2, R["green"])
    outline(cv)
    return cv


def machine_mill(w=50, h=56):
    """Molino (arroz, harina, yerba, papas): tolva de madera, cuerpo de la muela,
    motor con correa y la boca que llena una bolsa."""
    cv = Cv(w, h)
    S, Wd = R["steel"], R["wood"]
    cv.poly([(6, 0), (34, 0), (27, 12), (13, 12)], Wd[4])                            # tolva
    cv.line([(6, 0), (34, 0)], Wd[6])
    cv.poly([(27, 12), (34, 0), (36, 1), (29, 13)], Wd[2])
    for k in range(8, 34, 5):
        cv.line([(k, 1), (k + (20 - k) * 0.35, 11)], Wd[3])
    cv.rect(10, 1, 20, 2, R["burlap"][5])                                            # grano
    fx, fy, fw, fh = box(cv, 4, 12, 34, 30, 4, R["green"], top_tone=5, front_tone=3, side_tone=1)
    disk(cv, fx + fw // 2, fy + 13, 8, S)                                            # tapa de la muela
    disk(cv, fx + fw // 2, fy + 13, 3, R["dark"])
    for a in range(0, 360, 30):
        ang = math.radians(a)
        cv.put(int(fx + fw // 2 + math.cos(ang) * 6), int(fy + 13 + math.sin(ang) * 6), S[2])
    box(cv, 38, 24, 11, 12, 2, R["dark"], top_tone=5, front_tone=3)                 # motor
    for yy in range(28, 35, 2):
        cv.rect(39, yy, 8, 1, R["dark"][1])
    cv.line([(38, 27), (fx + fw // 2 + 6, fy + 9)], R["dark"][1])                    # correa
    cv.line([(38, 34), (fx + fw // 2 + 6, fy + 17)], R["dark"][1])
    cv.poly([(fx + 6, fy + fh), (fx + 14, fy + fh), (fx + 12, fy + fh + 4), (fx + 8, fy + fh + 4)], S[3])   # boca
    P.sack(cv, fx + 2, fy + fh + 3, 16, h - (fy + fh + 3), "#D5576E")              # bolsa llenándose
    box(cv, 22, h - 6, 26, 6, 1, R["dark"], top_tone=4, front_tone=2)               # pie
    outline(cv)
    return cv


def machine_mixer(w=50, h=56):
    """Amasadora / batidora industrial (pan, chacinados, lácteos): pie y cabezal
    crema con brazo, bol de acero con la masa y perillas."""
    cv = Cv(w, h)
    S = R["steel"]
    CR = ["#6E5A44", "#8E765A", "#B09676", "#CDB592", "#E2CDAA", "#F0E0C2", "#FAF2E2"]
    box(cv, 2, h - 8, w - 4, 8, 2, R["dark"], top_tone=5, front_tone=3)             # base
    box(cv, w - 16, 6, 13, h - 14, 3, CR, top_tone=5, front_tone=3, side_tone=1)   # columna
    box(cv, 8, 2, w - 10, 12, 4, CR, top_tone=6, front_tone=4, side_tone=2)        # cabezal
    cv.rect(12, 8, 8, 2, R["red"][3])                                               # franja
    cv.rect(w // 2 - 6, 14, 2, 10, S[4])                                            # gancho amasador
    cv.line([(w // 2 - 5, 24), (w // 2 - 1, 28)], S[5])
    cxb = (w - 12) / 2
    rb = (w - 22) / 2
    for x in range(int(cxb - rb), int(cxb + rb) + 1):                               # bol de acero
        u = (x + 0.5 - cxb) / rb
        if abs(u) > 1:
            continue
        b = -u * 0.5 + math.sqrt(max(0.0, 1 - u * u)) * 0.6
        idx = max(0, min(6, int(round((b * 0.5 + 0.5) * 6))))
        top = 26 + int(abs(u) ** 2 * 2)
        cv.rect(x, top, 1, h - 8 - top, S[idx])
    cv.ell(cxb, 26, rb, 2.6, S[2])
    cv.ell(cxb, 26.5, rb - 2, 1.8, "#F0D8A8")                                        # masa
    cv.ell(cxb - 3, 26, 4, 1, "#FFF0D0")
    for i, rp in enumerate(("red", "green")):
        disk(cv, w - 10, 22 + i * 6, 1.6, R[rp])
    outline(cv)
    return cv


# ------------------------------------------------------------------ colgantes
MEAT = ["#4A1418", "#6E1E24", "#8E2A2E", "#AE3A3C", "#C9545E", "#E07A80", "#F4B0B0"]
FAT = ["#C8B49A", "#E6D6BE", "#FFF4E2"]


def meat_hooks(w=42, h=34):
    """Riel con ménsulas, ganchos en S y cortes de carne con hueso y grasa (siluetas distintas)."""
    cv = Cv(w, h)
    S = R["steel"]
    cv.rect(0, 1, w, 2, S[4])
    cv.rect(0, 1, w, 1, S[6])
    bracket(cv, 0, 0, 4, 6)
    bracket(cv, w - 2, 0, -3, 6)
    shapes = [(3, 22, 8, "cuarto"), (13, 18, 7, "costillar"), (22, 24, 8, "cuarto"), (32, 16, 7, "pierna")]
    for x, L, wd, kind in shapes:
        if x + wd > w - 1:
            continue
        s_hook(cv, x + wd // 2, 3, S)
        top = 8
        if kind == "costillar":
            shade_poly(cv, [(x, top), (x + wd, top), (x + wd, top + L), (x, top + L - 3)], MEAT, 3)
            for k in range(top + 2, top + L - 2, 3):                          # costillas
                cv.line([(x + 1, k), (x + wd - 1, k + 1)], FAT[1])
        elif kind == "pierna":
            shade_poly(cv, [(x + 1, top), (x + wd - 1, top), (x + wd, top + L * 0.6), (x + wd // 2 + 1, top + L),
                            (x, top + L * 0.6)], MEAT, 3)
            cv.rect(x + wd // 2 - 1, top - 1, 2, 3, FAT[2])                    # hueso
        else:
            shade_poly(cv, [(x, top), (x + wd, top), (x + wd + 1, top + L * 0.5), (x + wd - 1, top + L),
                            (x + 1, top + L), (x - 1, top + L * 0.5)], MEAT, 3)
            cv.rect(x + 1, top + 1, wd - 2, 3, FAT[1])                         # capa de grasa
            cv.rect(x + 1, top + 1, wd - 2, 1, FAT[2])
            cv.rect(x + wd // 2, top + L - 3, 2, 3, FAT[2])                    # hueso abajo
        cv.put(x + 2, top + 5, MEAT[6])
    outline(cv)
    return cv


def add_brackets(fn):
    """Envuelve un colgante viejo: le agrega ménsulas en las puntas de la barra."""
    def wrapped(w, h):
        cv = fn(w, h)
        bracket(cv, 0, 0, 4, 6)
        bracket(cv, w - 2, 0, -3, 6)
        return cv
    return wrapped


# ------------------------------------------------------------------ mercadería
def barrels_wood(w=44, h=30):
    """Barriles de roble acostados (dos abajo, uno arriba): duelas, dos zunchos y la tapa."""
    cv = Cv(w, h)
    O = R["oak"]
    S = R["steel"]

    def barrel(x, y, bw, bh):
        cy = y + bh / 2
        for yy in range(y, y + bh):
            v = (yy + 0.5 - cy) / (bh / 2)
            if abs(v) > 1:
                continue
            bulge = math.sqrt(max(0.0, 1 - v * v))
            for xx in range(x + 3, x + bw):
                if (xx - x) > bw - 1 - (1 - bulge) * 2:
                    continue
                t = 4 - int(abs(v + 0.35) * 3.2)
                if (yy - y) % 4 == 0:
                    t -= 1                                                # junta de duelas
                cv.put(xx, yy, O[max(0, min(6, t))])
        for hx in (x + 8, x + bw - 6):                                    # zunchos
            for yy in range(y + 1, y + bh - 1):
                cv.put(hx, yy, S[1])
                cv.put(hx + 1, yy, S[3])
        for yy in range(y, y + bh):                                       # tapa
            for xx in range(x, x + 7):
                d = ((xx + 0.5 - (x + 3.5)) / 3.4) ** 2 + ((yy + 0.5 - cy) / (bh / 2)) ** 2
                if d <= 1:
                    cv.put(xx, yy, O[2] if d > 0.55 else O[3])
        cv.put(x + 3, int(cy), R["dark"][2])
        cv.line([(x + 9, y + 2), (x + bw - 8, y + 2)], O[6])

    bh = (h - 2) // 2
    barrel(0, h - bh - 1, w // 2 + 1, bh)
    barrel(w // 2 - 1, h - bh - 1, w // 2 + 1, bh)
    barrel(w // 4, 0, w // 2 + 1, bh + 1)
    cv.rect(3, h - 2, w - 6, 2, R["wood"][2])                             # cuñas
    outline(cv)
    return cv


def bales(w=40, h=26):
    """Fardos de algodón abombados, con flejes de acero y motas."""
    cv = Cv(w, h)
    Wt = R["white"]
    S = R["steel"]
    rnd = random.Random(4)
    for x, y, bw, bh in ((7, 0, 14, 11), (20, 0, 14, 11), (0, 9, 14, 16), (13, 9, 14, 16), (26, 9, 14, 16)):
        for yy in range(y, min(h, y + bh)):
            for xx in range(x, min(w, x + bw)):
                u = (xx + 0.5 - (x + bw / 2)) / (bw / 2)
                v = (yy + 0.5 - (y + bh / 2)) / (bh / 2)
                if abs(u) > 0.9 and abs(v) > 0.8:
                    continue                                              # esquinas redondeadas
                b = 0.75 - u * 0.25 - v * 0.35 - (u * u + v * v) * 0.12
                cv.put(xx, yy, Wt[max(1, min(6, int(round(b * 6))))])
        for k in range(8):
            cv.put(x + rnd.randint(2, bw - 3), y + rnd.randint(2, bh - 3), Wt[rnd.choice([2, 3])])
        for yy in (y + bh // 3, y + 2 * bh // 3):                         # flejes
            cv.rect(x + 1, yy, bw - 2, 1, S[2])
            cv.put(x + 1, yy, S[5])
    outline(cv)
    return cv


def bread_rack(w=50, h=70):
    """Estantería de panadería: panes redondos, flautas y medialunas."""
    cv = Cv(w, h)
    W = R["oak"]
    box(cv, 0, 0, w, h, 4, W, top_tone=5, front_tone=1, side_tone=0)
    BR = ["#6A3410", "#8E4A18", "#B06424", "#CC8034", "#E2A04E", "#F0C27A", "#FAE2B0"]
    for r in range(4):
        y = 6 + r * 16
        cv.rect(2, y + 12, w - 6, 3, W[4])
        cv.rect(2, y + 12, w - 6, 1, W[6])
        kind = r % 3
        x = 4
        while x < w - 10:
            if kind == 0:                                                 # pan redondo
                disk(cv, x + 4, y + 8, 4, BR)
                cv.line([(x + 2, y + 7), (x + 6, y + 6)], BR[1])
                x += 9
            elif kind == 1:                                               # flautas
                cv.poly([(x, y + 11), (x + 3, y + 2), (x + 5, y + 2), (x + 2, y + 11)], BR[4])
                cv.line([(x + 3, y + 3), (x + 1, y + 10)], BR[6])
                x += 5
            else:                                                         # medialunas
                cv.poly([(x, y + 11), (x + 3, y + 6), (x + 7, y + 6), (x + 10, y + 11), (x + 5, y + 9)], BR[5])
                cv.line([(x + 2, y + 9), (x + 8, y + 9)], BR[3])
                x += 11
    outline(cv)
    return cv


def fileteado_sign(w=70, h=18):
    """Cartel fileteado porteño: fondo negro, filete dorado, volutas, flores y BIENVENIDOS."""
    cv = Cv(w, h)
    box(cv, 0, 0, w, h, 2, R["dark"], top_tone=4, front_tone=1, side_tone=0)
    cv.rect(2, 3, w - 5, h - 5, "#1A1420")
    for x in range(3, w - 4):
        cv.put(x, 3, R["brass"][4])
        cv.put(x, h - 3, R["brass"][3])
    for cx, sgn in ((7, 1), (w - 9, -1)):                                 # volutas en las puntas
        for a in range(0, 330, 15):
            ang = math.radians(a)
            r = 1.2 + a / 160
            cv.put(int(cx + sgn * math.cos(ang) * r), int(h / 2 + math.sin(ang) * r * 0.8), R["brass"][5])
        disk(cv, cx, h / 2, 1.3, R["red"])
        cv.put(cx + sgn * 3, int(h / 2) - 3, R["green"][4])
    word = "BIENVENIDOS"
    text(cv, (w - text_w(word)) // 2, (h - 5) // 2 + 1, word, R["brass"][5], shadow=R["red"][2])
    outline(cv)
    return cv


def freezer_frio(fn):
    """El freezer de pozo dice FRIO (sirve para carnes, lácteos y helados)."""
    def wrapped(w, h):
        cv = fn(w, h)
        fx, fy = 4, 14
        cv.rect(fx, fy, w - 14, 9, R["blue"][3])
        cv.rect(fx, fy, w - 14, 1, R["blue"][5])
        text(cv, fx + (w - 14 - text_w("FRIO")) // 2, fy + 2, "FRIO", "#FFFFFF")
        return cv
    return wrapped


# ------------------------------------------------------------------ muebles a escala
def cafe_table(w=42, h=36):
    """Mesa de bar con tapa de mármol y dos sillas de bistró a escala de una persona."""
    cv = Cv(w, h)
    D = R["dark"]
    Wd = R["wood"]
    for sx, flip in ((0, False), (w - 10, True)):
        cv.rect(sx + 1, 4, 8, 2, Wd[4])                                   # respaldo
        cv.rect(sx + 1, 4, 8, 1, Wd[6])
        for yy in range(7, 16, 3):
            cv.rect(sx + 2, yy, 6, 1, Wd[3])
        cv.rect(sx + (8 if flip else 1), 4, 1, h - 5, D[3])              # pata trasera
        cv.rect(sx + (1 if flip else 8), 18, 1, h - 19, D[3])            # pata delantera
        cv.rect(sx, 17, 10, 3, Wd[4])                                     # asiento
        cv.rect(sx, 17, 10, 1, Wd[6])
        cv.rect(sx, 19, 10, 1, Wd[2])
        cv.rect(sx + 1, h - 8, 8, 1, D[2])                                # travesaño
    cx = w // 2
    cv.rect(cx - 1, 12, 2, h - 14, D[3])                                  # pie de hierro
    cv.rect(cx - 1, 12, 1, h - 14, D[5])
    cv.ell(cx, h - 2, 7, 1.4, D[2])
    cv.ell(cx, 11, 13, 3.6, R["white"][2])                                 # mármol
    cv.ell(cx, 10.5, 12.5, 3.1, R["white"][4])
    cv.ell(cx - 3, 9.5, 6, 1.4, R["white"][6])
    cv.rect(cx - 6, 5, 4, 4, "#FFFFFF")                                   # pocillo
    cv.rect(cx - 6, 5, 4, 1, "#6D3A20")
    cv.put(cx - 2, 6, "#FFFFFF")
    cv.poly([(cx + 2, 9), (cx + 4, 6), (cx + 8, 6), (cx + 10, 9)], R["yellow"][4])   # medialuna
    cv.line([(cx + 3, 8), (cx + 9, 8)], R["yellow"][2])
    outline(cv)
    return cv


def coffee_machine(w=28, h=26):
    """Cafetera espresso chica de mostrador (un grupo, lanza de vapor y pocillo)."""
    cv = Cv(w, h)
    S = R["steel"]
    fx, fy, fw, fh = box(cv, 0, 4, w, h - 4, 3, S, top_tone=5, front_tone=4, side_tone=2)
    for i in range(2):                                                    # pocillos arriba
        cv.rect(3 + i * 6, 0, 4, 4, "#FFFFFF")
        cv.rect(3 + i * 6, 0, 4, 1, "#E3DEE2")
    cv.rect(2, 9, fw - 4, 3, R["red"][3])
    cv.rect(2, 9, fw - 4, 1, R["red"][5])
    gx = 9
    disk(cv, gx, 15, 2.5, S)
    cv.line([(gx + 1, 17), (gx + 5, 18)], R["wood"][3])
    cv.rect(gx - 2, 19, 4, 3, "#FFFFFF")
    cv.rect(gx - 2, 19, 4, 1, "#6D3A20")
    disk(cv, fw - 6, 14, 2, R["white"])                                   # manómetro
    cv.line([(fw - 3, 13), (fw - 3, 19), (fw - 5, 21)], S[6])
    cv.rect(fx + 1, fy + fh - 2, fw - 2, 1, S[1])
    outline(cv, *METAL_OUT)
    return cv


NEW = {
    "_elec_panel": elec_panel, "_calendar": calendar, "_outlet": outlet,
    "_machine_press": machine_press, "_machine_mill": machine_mill, "_machine_mixer": machine_mixer,
    "_meat_hooks": meat_hooks, "_barrels_wood": barrels_wood, "_bales": bales, "_bread_rack": bread_rack,
    "_fileteado_sign": fileteado_sign, "_cafe_table": cafe_table, "_coffee_machine": coffee_machine,
}


def register(pieces):
    pieces["_banana_hooks"] = add_brackets(pieces["_banana_hooks"])
    pieces["_salames"] = add_brackets(pieces["_salames"])
    pieces["_freezer"] = freezer_frio(pieces["_freezer"])
    pieces.update(NEW)
    register2(pieces)


# ------------------------------------------------------------------ 12.2 revisión 2
def _sc(k):
    return lambda v: int(round(v * k))


def forklift(w=66, h=56):
    """Autoelevador a escala de una persona (mástil, horquillas con caja, jaula,
    asiento, contrapeso y ruedas macizas)."""
    cv = Cv(w, h)
    S = _sc(w / 52.0)
    Y, D = R["yellow"], R["dark"]
    cv.rect(S(6), S(2), S(3), S(34), D[3])
    cv.rect(S(10), S(2), S(3), S(34), D[3])
    cv.rect(S(6), S(2), 1, S(34), D[5])
    for yy in range(S(4), S(34), S(6)):
        cv.rect(S(6), yy, S(7), 1, D[2])
    cv.rect(0, S(33), S(14), S(3), R["steel"][3])
    cv.rect(0, S(33), S(14), 1, R["steel"][6])
    box(cv, 0, S(21), S(11), S(12), 3, R["card"])
    box(cv, S(13), S(22), S(37), S(16), 5, Y, top_tone=5, front_tone=4, side_tone=2)
    cv.rect(S(38), S(24), S(11), S(10), D[2])
    cv.rect(S(38), S(24), S(11), 1, D[4])
    for k in range(5):
        cv.line([(S(15 + k * 4), S(34)), (S(18 + k * 4), S(31))], D[2])
    cv.rect(S(16), S(2), 2, S(20), D[3])
    cv.rect(S(36), S(2), 2, S(20), D[3])
    cv.rect(S(16), S(2), S(22), 2, D[3])
    cv.rect(S(16), S(2), S(22), 1, D[5])
    cv.rect(S(24), S(14), S(9), S(8), D[4])
    cv.rect(S(23), S(9), S(3), S(6), D[4])
    cv.line([(S(19), S(20)), (S(21), S(14))], D[1])
    disk(cv, S(21), S(14), 2.4, D)
    cv.rect(S(37), 0, 3, 3, "#F59A45")
    for wx, r in ((S(20), 5.5 * w / 52), (S(43), 5 * w / 52)):
        disk(cv, wx, h - 7, r, D)
        disk(cv, wx, h - 7, r * 0.45, R["steel"])
    outline(cv)
    return cv


def lamp_tube(w=30, h=10):
    """Tubo fluorescente con su chasis blanco colgado de dos cadenitas."""
    cv = Cv(w, h)
    S = R["steel"]
    for x in (5, w - 6):
        for y in range(0, 4):
            cv.put(x, y, S[4] if y % 2 else S[2])
    box(cv, 0, 4, w, 4, 1, R["white"], top_tone=5, front_tone=3)
    cv.rect(2, 8, w - 4, 2, "#FFFBE6")
    cv.rect(2, 9, w - 4, 1, "#FFE9A8")
    outline(cv)
    return cv


def lamp_bronze(w=16, h=20):
    """Colgante de bronce con tulipa de vidrio esmerilado (panadería, bodega, almacén)."""
    cv = Cv(w, h)
    B = R["brass"]
    cv.rect(w // 2, 0, 1, 7, R["dark"][3])
    cv.rect(w // 2 - 2, 6, 5, 2, B[2])
    cv.put(w // 2 - 2, 6, B[4])
    for y in range(8, 16):
        half = 2 + (y - 8) * 0.8
        for x in range(int(w / 2 - half), int(w / 2 + half) + 1):
            u = (x + 0.5 - w / 2) / max(1, half)
            cv.put(x, y, "#FFF2CE" if u < -0.3 else ("#F5DC9C" if u < 0.4 else "#D9B36E"))
    cv.rect(2, 15, w - 4, 1, B[3])
    cv.rect(4, 16, w - 8, 2, "#FFF6D8")
    outline(cv)
    return cv


def pennant(w=40, h=14):
    """Banderines: cuatro triángulos grandes de color plano en un cordel."""
    cv = Cv(w, h)
    cv.line([(0, 1), (w - 1, 1)], R["dark"][4])
    cols = [("#74ACDF", "#4E8FC9"), ("#FFFFFF", "#CFC9D0"), ("#F6C43A", "#C07A12"), ("#74ACDF", "#4E8FC9")]
    tw = (w - 2) // 4
    for i, (c, d) in enumerate(cols):
        x0 = 1 + i * tw
        cv.poly([(x0, 2), (x0 + tw - 2, 2), (x0 + (tw - 2) / 2, h - 1)], c)
        cv.line([(x0 + (tw - 2) / 2, h - 1), (x0 + tw - 2, 2)], d)
    outline(cv)
    return cv


def cold_door(w=44, h=72):
    """Puerta de cámara frigorífica: chapa con bisagras, manija y cortina de tiras."""
    cv = Cv(w, h)
    S = R["steel"]
    fx, fy, fw, fh = box(cv, 0, 0, w, h, 3, S, top_tone=5, front_tone=4, side_tone=2)
    cv.rect(fx + 3, fy + 3, fw - 6, fh - 6, S[3])
    for x in range(fx + 5, fx + fw - 5, 4):
        cv.rect(x, fy + 7, 3, fh - 14, "#C6E4F0")
        cv.rect(x, fy + 7, 1, fh - 14, "#EEF8FC")
        cv.rect(x + 2, fy + 7, 1, fh - 14, "#94BFD0")
    for y in (fy + 9, fy + fh - 15):
        cv.rect(fx, y, 3, 6, S[1])
        cv.put(fx + 1, y + 1, S[5])
    cv.rect(fx + fw - 6, fy + fh // 2 - 6, 3, 12, S[6])
    cv.rect(fx + fw - 5, fy + fh // 2 - 6, 1, 12, S[2])
    text(cv, fx + (fw - text_w("FRIO")) // 2, fy + 1, "FRIO", "#FFFFFF")
    outline(cv, *METAL_OUT)
    return cv


def counter_pastry(w=72, h=32):
    """Vitrina de panadería: vidrio con dos bandejas de facturas, medialunas y tortas."""
    cv = Cv(w, h)
    Wd = R["oak"]
    G = R["glass"]
    box(cv, 0, 14, w, h - 14, 3, Wd, top_tone=5, front_tone=3, side_tone=1)
    cv.rect(2, h - 6, w - 6, 2, Wd[1])
    for x in range(1, w - 3):
        cv.put(x, 2, G[5])
        for y in range(3, 15):
            cv.put(x, y, G[3] if (x + y) % 9 else G[4])
    BR = ["#8E4A18", "#B06424", "#CC8034", "#E2A04E", "#F0C27A", "#FAE2B0"]
    for row, yb in enumerate((8, 13)):
        cv.rect(3, yb + 1, w - 8, 1, R["white"][5])
        x = 4
        k = 0
        while x < w - 10:
            if (k + row) % 3 == 0:
                cv.poly([(x, yb), (x + 2, yb - 3), (x + 6, yb - 3), (x + 8, yb), (x + 4, yb - 1)], BR[4])
                cv.line([(x + 1, yb - 1), (x + 7, yb - 1)], BR[1])
                x += 10
            elif (k + row) % 3 == 1:
                cv.rect(x, yb - 3, 6, 3, BR[3])
                cv.rect(x, yb - 3, 6, 1, "#FFF0F0")
                cv.put(x + 2, yb - 4, "#D5576E")
                x += 8
            else:
                disk(cv, x + 3, yb - 2, 2.6, BR)
                x += 7
            k += 1
    for k in range(4):
        cv.put(6 + k, 12 - k * 2, "#FFFFFF")
    outline(cv)
    return cv


def bales_pressed(w=40, h=26):
    """Fardos prensados: bloques rectos con flejes oscuros y fibra irregular."""
    cv = Cv(w, h)
    Wt = R["white"]
    rnd = random.Random(14)
    for x, y, bw, bh in ((7, 0, 14, 11), (20, 0, 14, 11), (0, 10, 14, 16), (13, 10, 14, 16), (26, 10, 14, 16)):
        fx, fy, fw, fh = box(cv, x, y, bw, bh, 3, Wt, top_tone=6, front_tone=4, side_tone=2)
        for k in range(16):
            xx, yy = fx + rnd.randint(0, fw - 2), fy + rnd.randint(0, fh - 1)
            cv.put(xx, yy, Wt[rnd.choice([2, 3])])
            cv.put(xx + 1, yy, Wt[rnd.choice([5, 6])])
        for xx in (fx + fw // 3, fx + 2 * fw // 3):
            cv.rect(xx, y, 1, bh, R["dark"][3])
    outline(cv)
    return cv


def chairs_3q(fn):
    """Las sillas de la mesa de bar con el asiento en 3/4 (tapa visible), como la mesa."""
    def wrapped(w, h):
        cv = fn(w, h)
        Wd = R["wood"]
        for sx in (0, w - 10):
            cv.poly([(sx, 18), (sx + 10, 18), (sx + 9, 15), (sx + 1, 15)], Wd[5])
            cv.line([(sx + 1, 15), (sx + 9, 15)], Wd[6])
        return cv
    return wrapped


def tool_wall(w=60, h=40):
    """Tablero perforado con herramientas colgadas: llave, martillo, serrucho,
    pinza y destornilladores (cada una con su gancho y su sombra)."""
    cv = Cv(w, h)
    Wd = R["card"]
    box(cv, 0, 0, w, h, 2, Wd, top_tone=5, front_tone=3, side_tone=1)
    for y in range(5, h - 3, 4):                                             # perforaciones
        for x in range(4, w - 4, 4):
            cv.put(x, y, Wd[1])
    S, D, Rd = R["steel"], R["dark"], R["red"]
    # martillo
    cv.rect(6, 6, 2, 22, R["wood"][4]); cv.rect(6, 6, 1, 22, R["wood"][6])
    cv.rect(3, 5, 9, 4, S[3]); cv.rect(3, 5, 9, 1, S[6])
    # llave inglesa
    cv.rect(17, 8, 2, 20, S[4]); cv.rect(17, 8, 1, 20, S[6])
    cv.poly([(14, 5), (22, 5), (21, 10), (15, 10)], S[4]); cv.rect(17, 5, 2, 3, Wd[3])
    # serrucho
    cv.poly([(26, 8), (40, 6), (40, 26), (26, 16)], S[5]); cv.line([(26, 16), (40, 26)], S[2])
    for k in range(27, 40, 2):
        cv.put(k, 16 + int((k - 26) * 10 / 14) + 1, S[1])
    cv.rect(39, 5, 5, 8, R["wood"][3]); cv.rect(39, 5, 5, 1, R["wood"][5])
    # pinza
    cv.line([(47, 6), (49, 26)], Rd[3], 2); cv.line([(52, 6), (50, 26)], Rd[2], 2)
    cv.rect(47, 4, 6, 3, S[3])
    # destornilladores
    for i, col in enumerate(("#F6C43A", "#3E74B8")):
        x = 54 + i * 3
        if x < w - 3:
            cv.rect(x, 8, 2, 7, col); cv.rect(x, 15, 1, 10, S[5])
    for x in (6, 17, 33, 50):                                                # sombra de cada herramienta
        cv.put(x + 2, 29, Wd[1])
    outline(cv)
    return cv


NEW2 = {"_tool_wall": tool_wall, "_forklift": forklift, "_lamp_tube": lamp_tube, "_lamp_bronze": lamp_bronze, "_pennant": pennant,
        "_cold_door": cold_door, "_counter_pastry": counter_pastry, "_bales": bales_pressed}


def register2(pieces):
    pieces["_cafe_table"] = chairs_3q(pieces["_cafe_table"])
    pieces.update(NEW2)
    register3(pieces)



# ------------------------------------------------------------------ 12.2 revisión 3
GRAPE = ["#3A1A4A", "#5A2A6E", "#7A3A8E", "#9A5AAE", "#C08AD0", "#E0C0F0", "#FFFFFF"]


def poster_theme(kind):
    """Póster enmarcado con el tema del rubro (uva, vaca, oveja, trigo, mate, fruta)."""
    def fn(w=20, h=26):
        cv = Cv(w, h)
        box(cv, 0, 0, w, h, 2, R["oak"])
        cv.rect(2, 3, w - 5, h - 6, "#F2E6CE")
        sky = {"uva": "#C9A0D8", "vaca": "#9FD4F0", "oveja": "#B8DCEC", "trigo": "#F7D98A",
               "mate": "#BCE0B0", "fruta": "#F6C8A0"}[kind]
        cv.rect(3, 4, w - 7, 12, sky)
        cv.rect(3, 13, w - 7, 3, "#4FB070")
        cx = w // 2 - 1
        if kind == "uva":
            for dx, dy in ((0, 0), (-2, 0), (2, 0), (-1, 2), (1, 2), (0, 4)):
                disk(cv, cx + dx, 7 + dy, 1.4, GRAPE)
            cv.put(cx, 5, "#3F9E5E")
        elif kind == "vaca":
            cv.rect(cx - 4, 8, 8, 4, "#FFFFFF")
            cv.rect(cx - 2, 9, 3, 2, "#2A2534")
            cv.rect(cx + 4, 7, 2, 3, "#FFFFFF")
            for lx in (cx - 4, cx - 1, cx + 2):
                cv.rect(lx, 12, 1, 2, "#2A2534")
        elif kind == "oveja":
            disk(cv, cx, 9, 3.5, R["white"])
            cv.rect(cx + 3, 8, 2, 2, "#2A2534")
            cv.rect(cx - 2, 12, 1, 2, "#2A2534")
            cv.rect(cx + 1, 12, 1, 2, "#2A2534")
        elif kind == "trigo":
            for dx in (-3, 0, 3):
                cv.line([(cx + dx, 14), (cx + dx, 6)], "#C07A12")
                for k in range(6, 11, 2):
                    cv.put(cx + dx - 1, k, "#F6C43A")
                    cv.put(cx + dx + 1, k + 1, "#F6C43A")
        elif kind == "mate":
            disk(cv, cx, 10, 3.2, R["oak"])
            cv.rect(cx - 2, 6, 5, 1, R["brass"][3])
            cv.line([(cx + 1, 6), (cx + 3, 3)], R["steel"][5])
        else:
            disk(cv, cx - 2, 10, 2.4, R["red"])
            disk(cv, cx + 2, 10, 2.4, R["orange"])
            cv.put(cx - 2, 7, "#3F9E5E")
        cv.rect(4, 18, w - 9, 2, "#D5576E")
        cv.rect(4, 21, w - 11, 1, "#8E8496")
        outline(cv)
        return cv
    return fn


def bales_soft(w=40, h=26):
    """Fardos de algodón: volumen esponjoso de contorno irregular, flejes metálicos claros."""
    cv = Cv(w, h)
    Wt = R["white"]
    S = R["steel"]
    rnd = random.Random(21)
    for x, y, bw, bh in ((7, 0, 14, 11), (20, 0, 14, 11), (0, 10, 14, 16), (13, 10, 14, 16), (26, 10, 14, 16)):
        for yy in range(y, min(h, y + bh)):
            for xx in range(x, min(w, x + bw)):
                u = (xx + 0.5 - (x + bw / 2)) / (bw / 2)
                v = (yy + 0.5 - (y + bh / 2)) / (bh / 2)
                if max(abs(u), abs(v)) > 0.92 and rnd.random() < 0.5:
                    continue
                b = 0.8 - u * 0.22 - v * 0.32 - (u * u + v * v) * 0.1
                cv.put(xx, yy, Wt[max(2, min(6, int(round(b * 6))))])
        for k in range(10):
            cv.put(x + rnd.randint(2, bw - 3), y + rnd.randint(2, bh - 3), Wt[3])
        for xx in (x + bw // 3, x + 2 * bw // 3):
            for yy in range(y + 1, min(h, y + bh) - 1):
                cv.put(xx, yy, S[3])
            cv.put(xx, y + 1, S[6])
    outline(cv)
    return cv


def cafe_table_v3(w=42, h=36):
    """Mesa de bar en 3/4: tapa en elipse; una silla de perfil (izquierda) y otra de
    espaldas (derecha), las dos con el asiento visto desde arriba."""
    cv = Cv(w, h)
    D, Wd = R["dark"], R["wood"]
    cv.rect(1, 4, 2, h - 5, D[3])
    cv.rect(1, 4, 1, h - 5, D[5])
    cv.rect(8, 19, 1, h - 20, D[3])
    cv.poly([(0, 19), (10, 19), (11, 16), (2, 16)], Wd[5])
    cv.rect(0, 19, 10, 2, Wd[3])
    cv.line([(2, 16), (11, 16)], Wd[6])
    sx = w - 11
    cv.rect(sx, 5, 10, 2, Wd[4])
    cv.rect(sx, 5, 10, 1, Wd[6])
    for k in range(sx + 1, sx + 10, 3):
        cv.rect(k, 7, 1, 10, Wd[3])
    cv.rect(sx, 5, 1, h - 6, D[3])
    cv.rect(sx + 9, 5, 1, h - 6, D[3])
    cv.poly([(sx - 1, 19), (sx + 11, 19), (sx + 10, 17), (sx, 17)], Wd[5])
    cv.rect(sx - 1, 19, 12, 2, Wd[3])
    cx = w // 2
    cv.rect(cx - 1, 12, 2, h - 14, D[3])
    cv.rect(cx - 1, 12, 1, h - 14, D[5])
    cv.ell(cx, h - 2, 7, 1.4, D[2])
    cv.ell(cx, 11, 13, 3.6, R["white"][2])
    cv.ell(cx, 10.5, 12.5, 3.1, R["white"][4])
    cv.ell(cx - 3, 9.5, 6, 1.4, R["white"][6])
    cv.rect(cx - 6, 5, 4, 4, "#FFFFFF")
    cv.rect(cx - 6, 5, 4, 1, "#6D3A20")
    cv.put(cx - 2, 6, "#FFFFFF")
    cv.poly([(cx + 2, 9), (cx + 4, 6), (cx + 8, 6), (cx + 10, 9)], R["yellow"][4])
    cv.line([(cx + 3, 8), (cx + 9, 8)], R["yellow"][2])
    outline(cv)
    return cv


def register3(pieces):
    for k in ("uva", "vaca", "oveja", "trigo", "mate", "fruta"):
        pieces["_poster_" + k] = poster_theme(k)
    pieces["_bales"] = bales_soft
    pieces["_cafe_table"] = cafe_table_v3
    register4(pieces)



# ------------------------------------------------------------------ 12.2 revisión 4
def pennant_garland(w=70, h=16):
    """Guirnalda de banderines en catenaria entre dos clavos, con el cordón visible."""
    cv = Cv(w, h)
    D = R["dark"]
    sag = 5.0
    ys = [1 + sag * (1 - ((x - (w - 1) / 2) / ((w - 1) / 2)) ** 2) for x in range(w)]
    for x in range(w):
        cv.put(x, int(round(ys[x])), D[4])
    for x in (0, w - 1):                                                     # clavos
        cv.put(x, 0, D[2])
        cv.put(x, 1, D[5])
    cols = [("#74ACDF", "#4E8FC9"), ("#FFFFFF", "#CFC9D0"), ("#F6C43A", "#C07A12"),
            ("#74ACDF", "#4E8FC9"), ("#FFFFFF", "#CFC9D0"), ("#F6C43A", "#C07A12")]
    n = len(cols)
    tw = (w - 8) / n
    for i, (c, d) in enumerate(cols):
        x0 = int(4 + i * tw)
        x1 = int(4 + (i + 1) * tw) - 2
        y0 = int(round(ys[x0])) + 1
        y1 = int(round(ys[x1])) + 1
        cv.poly([(x0, y0), (x1, y1), ((x0 + x1) / 2, max(y0, y1) + 7)], c)
        cv.line([((x0 + x1) / 2, max(y0, y1) + 7), (x1, y1)], d)
    outline(cv)
    return cv


def freezer_snow(fn):
    """Freezer de pozo con un copo en el cartel (el FRIO queda sólo en la cámara)."""
    def wrapped(w, h):
        cv = fn(w, h)
        fx, fy = 4, 14
        cv.rect(fx, fy, w - 14, 9, R["blue"][3])
        cv.rect(fx, fy, w - 14, 1, R["blue"][5])
        cx, cy = fx + (w - 14) // 2, fy + 4
        for d in range(-3, 4):
            cv.put(cx + d, cy, "#FFFFFF")
            cv.put(cx, cy + max(-3, min(3, d)), "#FFFFFF")
        for d in (-2, 2):
            cv.put(cx + d, cy + d, "#FFFFFF")
            cv.put(cx + d, cy - d, "#FFFFFF")
        return cv
    return wrapped


def bales_block(w=40, h=26):
    """Fardos de algodón prensados: cara superior clara, frente medio, lateral oscuro,
    flejes horizontales marcados y motas en racimos."""
    cv = Cv(w, h)
    Wt = R["white"]
    S = R["steel"]
    rnd = random.Random(31)
    for x, y, bw, bh in ((7, 0, 15, 11), (21, 0, 15, 11), (0, 10, 14, 16), (13, 10, 14, 16), (26, 10, 14, 16)):
        fx, fy, fw, fh = box(cv, x, y, bw, bh, 4, Wt, top_tone=6, front_tone=4, side_tone=2)
        for k in range(3):                                                   # motas en racimo
            cx, cy = fx + rnd.randint(2, fw - 3), fy + rnd.randint(2, fh - 3)
            for dx, dy in ((0, 0), (1, 0), (0, 1), (-1, 1)):
                cv.put(cx + dx, cy + dy, Wt[2])
        for yy in (fy + fh // 3, fy + 2 * fh // 3):                          # flejes horizontales
            cv.rect(fx, yy, fw, 1, S[2])
            cv.put(fx, yy, S[5])
            cv.put(fx + fw, yy - 1, S[1])
    outline(cv)
    return cv


def register4(pieces):
    pieces["_pennant"] = pennant_garland
    pieces["_bales"] = bales_block
    pieces["_freezer"] = freezer_snow(pieces["_freezer"])
    register5(pieces)



# ------------------------------------------------------------------ 12.2 revisión 5
def espresso(w=32, h=30):
    """Espresso de bar: cuerpo cromado con franja roja, dos grupos con portafiltro
    de mango de madera, pocillos debajo, manómetro, lanza de vapor y bandeja."""
    cv = Cv(w, h)
    S = R["steel"]
    fx, fy, fw, fh = box(cv, 0, 4, w, h - 4, 3, S, top_tone=6, front_tone=4, side_tone=2)
    for i in range(3):
        cv.rect(4 + i * 6, 0, 4, 4, "#FFFFFF")
        cv.rect(4 + i * 6, 0, 4, 1, "#E3DEE2")
        cv.rect(7 + i * 6, 1, 1, 3, "#CFC9D0")
    cv.rect(2, 9, fw - 4, 3, R["red"][3])
    cv.rect(2, 9, fw - 4, 1, R["red"][5])
    for gx in (8, 19):
        cv.rect(gx - 3, 13, 7, 3, S[2])                                     # grupo
        cv.rect(gx - 3, 13, 7, 1, S[6])
        cv.rect(gx - 2, 16, 5, 2, S[3])                                     # portafiltro
        cv.line([(gx + 3, 17), (gx + 7, 18)], R["wood"][2], 2)              # mango
        cv.rect(gx - 2, 21, 5, 4, "#FFFFFF")                                # pocillo
        cv.rect(gx - 2, 21, 5, 1, "#6D3A20")
        cv.put(gx + 3, 22, "#FFFFFF")
    disk(cv, fw - 4, 14, 2.2, R["white"])                                   # manómetro
    cv.put(fw - 4, 13, R["red"][3])
    cv.line([(fw - 2, 16), (fw - 2, 23), (fw - 4, 25)], S[6])               # lanza de vapor
    cv.rect(fx + 1, fy + fh - 3, fw - 2, 2, S[1])                           # bandeja
    for xx in range(fx + 2, fx + fw - 2, 2):
        cv.put(xx, fy + fh - 3, S[5])
    outline(cv, *METAL_OUT)
    return cv


def register5(pieces):
    pieces["_coffee_machine"] = espresso
