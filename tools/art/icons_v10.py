"""Íconos de producto de la 10.0 (16x16): uno por producto regional del Excel.

Formas simples con la paleta px2, luz arriba a la izquierda y contorno de
1 px. Se guardan en assets/pixel_art/icons/<nombre>.png y los productos de
data/businesses.json los referencian por nombre (ver tools/v10/build_data.py).
"""
import os
from px2 import Canvas


def _c():
    return Canvas(16, 16)


def fruit(main, shade, hi="W", leaf=True, rx=5, ry=5):
    cv = _c()
    cv.ellipse(8, 9, rx, ry, shade)
    cv.ellipse(7, 8, rx - 1, ry - 1, main)
    cv.put(5, 6, hi)
    if leaf:
        cv.vline(8, 2, 3, "M2")
        cv.rect(9, 2, 3, 2, "G2")
    return cv


def pear():
    cv = _c()
    cv.ellipse(8, 11, 5, 4, "G2")
    cv.ellipse(8, 6, 3, 3, "G2")
    cv.ellipse(7, 10, 4, 3, "G3")
    cv.vline(8, 1, 3, "M2")
    cv.put(6, 8, "W")
    return cv


def cluster(main, shade, n=6, small=False):
    cv = _c()
    pos = [(5, 5), (9, 5), (7, 8), (11, 8), (5, 9), (9, 11), (7, 13)][:n] if not small else [(5, 6), (9, 6), (7, 9), (11, 10), (5, 11), (9, 13)]
    for x, y in pos:
        cv.ellipse(x, y, 2, 2, shade)
        cv.put(x - 1, y - 1, main)
        cv.put(x, y - 1, main)
    if not small:
        cv.vline(7, 1, 3, "M2")
        cv.rect(8, 1, 3, 2, "G2")
    return cv


def cherries():
    cv = _c()
    for x in (5, 11):
        cv.ellipse(x, 11, 3, 3, "R1")
        cv.put(x - 1, 10, "R3")
    for k in range(6):
        cv.put(5 + k // 2, 7 - k, "G1")
        cv.put(11 - k // 2, 7 - k, "G1")
    cv.rect(7, 1, 3, 2, "G2")
    return cv


def banana():
    cv = _c()
    for k in range(10):
        y = 11 - abs(k - 5) // 2
        cv.rect(3 + k, y - 1, 1, 4, "Y3" if k < 8 else "Y2")
        cv.put(3 + k, y + 2, "Y1")
    cv.rect(2, 9, 2, 2, "M1")
    return cv


def bottle(body, label, cap="o"):
    cv = _c()
    cv.rect(6, 1, 4, 2, cap)
    cv.rect(6, 3, 4, 3, body)
    cv.rect(4, 6, 8, 9, body)
    cv.rect(5, 9, 6, 3, label)
    cv.vline(5, 6, 3, "W")
    return cv


def jar(fill, lid="M2"):
    cv = _c()
    cv.rect(4, 2, 8, 2, lid)
    cv.rect(3, 4, 10, 10, fill)
    cv.vline(4, 5, 7, "W")
    cv.rect(5, 8, 6, 3, "w")
    return cv


def sack(color, mark=None, mark2=None):
    cv = _c()
    cv.rect(4, 4, 8, 10, color)
    cv.rect(3, 6, 10, 8, color)
    cv.rect(5, 2, 6, 3, color)
    cv.hline(5, 4, 6, "M2")
    cv.vline(4, 6, 6, "W")
    if mark:
        cv.rect(6, 8, 4, 3, mark)
    if mark2:
        cv.put(7, 9, mark2)
    return cv


def bale(fill, puffs):
    cv = _c()
    cv.rect(2, 5, 12, 9, fill)
    for x in (5, 10):
        cv.vline(x, 5, 9, "M2")
    for x, y in ((4, 4), (8, 3), (12, 4), (6, 7), (11, 8)):
        cv.rect(x - 1, y, 3, 2, puffs)
    return cv


def meat(bone=True):
    cv = _c()
    cv.ellipse(7, 9, 5, 4, "R1")
    cv.ellipse(7, 8, 4, 3, "R2")
    cv.rect(5, 7, 4, 2, "R3")
    if bone:
        cv.rect(11, 3, 2, 6, "W")
        cv.rect(10, 2, 4, 2, "W")
    return cv


def salame():
    cv = _c()
    cv.rect(3, 6, 11, 6, "R1")
    cv.rect(3, 7, 11, 4, "R2")
    for x, y in ((5, 8), (8, 9), (11, 8), (7, 7)):
        cv.put(x, y, "W")
    cv.vline(14, 7, 3, "M3")
    cv.vline(2, 7, 3, "M3")
    return cv


def cheese():
    cv = _c()
    for k in range(8):
        cv.hline(2 + k // 2 * 0, 6 + k, 4 + k, "Y3")
    cv.rect(2, 6, 12, 8, "Y3")
    cv.hline(2, 6, 12, "Y4")
    cv.rect(2, 12, 12, 2, "Y2")
    for x, y in ((5, 9), (9, 8), (11, 11)):
        cv.rect(x, y, 2, 2, "Y1")
    return cv


def fish():
    cv = _c()
    cv.ellipse(7, 8, 5, 3, "C2")
    cv.ellipse(7, 7, 4, 2, "C3")
    for k in range(4):
        cv.vline(12 + k, 8 - k, k * 2 + 1, "C2")
    cv.put(4, 7, "o")
    return cv


def logs():
    cv = _c()
    for x, y in ((5, 6), (11, 6), (8, 11)):
        cv.ellipse(x, y, 3, 3, "M2")
        cv.ellipse(x, y, 2, 2, "M4")
        cv.put(x, y, "M3")
    return cv


def nugget():
    cv = _c()
    cv.ellipse(6, 9, 4, 3, "Y2")
    cv.put(4, 8, "Y4")
    cv.ellipse(11, 10, 3, 3, "l")
    cv.put(10, 9, "W")
    return cv


def barrel_oil():
    cv = _c()
    cv.rect(4, 3, 8, 11, "x")
    cv.hline(4, 6, 8, "d")
    cv.hline(4, 10, 8, "d")
    cv.vline(5, 3, 11, "g")
    cv.rect(7, 7, 2, 3, "o")
    cv.put(7, 6, "o")
    return cv


def ingot():
    cv = _c()
    cv.rect(3, 8, 10, 5, "d")
    cv.rect(4, 6, 8, 3, "l")
    cv.hline(4, 6, 8, "W")
    return cv


def tv():
    cv = _c()
    cv.rect(2, 3, 12, 9, "x")
    cv.rect(3, 4, 10, 7, "C2")
    cv.rect(4, 5, 4, 2, "C4")
    cv.rect(6, 12, 4, 2, "x")
    return cv


def gadget():
    cv = _c()
    cv.rect(2, 5, 12, 8, "d")
    cv.rect(3, 6, 6, 4, "C3")
    for k in range(3):
        cv.put(11, 6 + k * 2, ["G3", "Y3", "R3"][k])
    return cv


def tractor():
    cv = _c()
    cv.rect(3, 6, 8, 4, "R2")
    cv.rect(7, 3, 4, 4, "R2")
    cv.rect(8, 4, 2, 2, "C4")
    cv.ellipse(5, 12, 3, 3, "o")
    cv.ellipse(12, 13, 2, 2, "o")
    cv.put(5, 12, "g")
    return cv


def poncho():
    cv = _c()
    for k in range(7):
        cv.hline(8 - k - 1, 3 + k, (k + 1) * 2, "R2")
    cv.rect(1, 10, 14, 4, "R2")
    cv.hline(1, 12, 14, "Y2")
    cv.hline(2, 7, 12, "w")
    for x in range(2, 15, 3):
        cv.put(x, 14, "R1")
    return cv


def leaf(main="M3", vein="M2"):
    cv = _c()
    cv.ellipse(8, 8, 4, 6, main)
    cv.vline(8, 2, 12, vein)
    for k in range(3):
        cv.put(7 - k, 6 + k * 2, vein)
        cv.put(9 + k, 6 + k * 2, vein)
    return cv


def pepper():
    cv = _c()
    cv.ellipse(8, 9, 3, 5, "R2")
    cv.put(7, 6, "R3")
    cv.rect(7, 2, 2, 3, "G1")
    return cv


def root():
    cv = _c()
    for k in range(10):
        cv.rect(3 + k, 5 + k // 2, 3, 3, "M3")
    cv.rect(3, 5, 2, 2, "W")
    cv.rect(1, 2, 3, 3, "G2")
    return cv


def garlic():
    cv = _c()
    cv.ellipse(8, 10, 5, 4, "w")
    cv.vline(8, 7, 7, "l")
    cv.vline(5, 8, 5, "l")
    cv.rect(7, 2, 2, 5, "G3")
    return cv


def potatoes():
    cv = _c()
    for (x, y), c in zip(((5, 7), (10, 7), (8, 11)), ("M3", "R2", "u")):
        cv.ellipse(x, y, 3, 3, c)
        cv.put(x - 1, y - 1, "W")
    return cv


def nut():
    cv = _c()
    cv.ellipse(8, 8, 5, 5, "M3")
    cv.ellipse(7, 7, 3, 3, "M4")
    cv.vline(8, 3, 11, "M2")
    return cv


def peanut():
    cv = _c()
    cv.ellipse(6, 6, 3, 3, "M4")
    cv.ellipse(10, 10, 3, 3, "M4")
    cv.rect(7, 7, 3, 3, "M4")
    cv.put(5, 5, "W")
    return cv


def olives():
    cv = _c()
    for x, y in ((5, 8), (10, 6), (10, 11)):
        cv.ellipse(x, y, 2, 3, "G1")
        cv.put(x - 1, y - 1, "G3")
    cv.vline(7, 2, 4, "M1")
    return cv


def hop():
    cv = _c()
    for k in range(5):
        cv.hline(8 - k, 4 + k * 2, k * 2 + 1, "G3")
        cv.hline(8 - k, 5 + k * 2, k * 2 + 1, "G2")
    cv.rect(7, 1, 2, 3, "G1")
    return cv


def sunflower():
    cv = _c()
    cv.ellipse(8, 7, 5, 5, "Y2")
    cv.ellipse(8, 7, 2, 2, "M1")
    cv.vline(8, 12, 4, "G1")
    return cv


def wheat():
    cv = _c()
    cv.vline(8, 5, 10, "Y1")
    for k in range(4):
        cv.rect(5, 3 + k * 2, 2, 2, "Y2")
        cv.rect(10, 3 + k * 2, 2, 2, "Y2")
        cv.put(8, 2 + k * 2, "Y3")
    return cv


def empanada():
    cv = _c()
    cv.ellipse(8, 10, 6, 4, "E2")
    cv.rect(2, 10, 13, 4, "E2")
    for x in range(3, 14, 2):
        cv.put(x, 9 - abs(x - 8) // 3, "M3")
    cv.hline(2, 13, 13, "M3")
    return cv


def tea():
    cv = _c()
    cv.rect(3, 4, 10, 10, "G1")
    cv.rect(4, 5, 8, 4, "G3")
    cv.vline(4, 5, 8, "W")
    cv.rect(6, 10, 4, 2, "Y2")
    return cv


ICONS10 = {
    "limon": lambda: fruit("Y3", "Y2"), "naranja": lambda: fruit("Q", "Y1"), "mandarina": lambda: fruit("Q", "R2", rx=4, ry=4),
    "pomelo": lambda: fruit("R3", "Q"), "manzana": lambda: fruit("R2", "R1"), "pera": pear, "cereza": cherries,
    "arandano": lambda: cluster("C3", "u", small=True), "uva": lambda: cluster("d", "u"), "pasa": lambda: cluster("M3", "M1"),
    "banana": banana, "aceituna": olives, "nuez": nut, "mani": peanut, "ajo": garlic, "papa": potatoes,
    "pimiento": pepper, "mandioca": root, "lupulo": hop, "girasol": sunflower, "trigo": wheat,
    "vino": lambda: bottle("R1", "E1"), "vino_blanco": lambda: bottle("G1", "Y3"), "aceite_oliva": lambda: bottle("Y2", "G2", "G1"),
    "miel": lambda: jar("Y2"), "dulce": lambda: jar("M3"),
    "arroz": lambda: sack("W", "C3"), "azucar": lambda: sack("W", "R2"), "harina": lambda: sack("E1", "Y2", "Y1"),
    "sal": lambda: sack("w", "C2"), "quinoa": lambda: sack("E2", "Q", "R2"), "soja": lambda: sack("Y3", "G2"),
    "alfalfa": lambda: bale("G2", "G3"), "algodon": lambda: bale("E1", "W"), "lana": lambda: bale("E2", "w"),
    "carne": lambda: meat(False), "cordero": meat, "salame": salame, "queso": cheese, "pescado": fish,
    "madera": logs, "oro": nugget, "petroleo": barrel_oil, "aluminio": ingot, "televisor": tv,
    "equipo": gadget, "tractor": tractor, "poncho": poncho, "tabaco": lambda: leaf("M3", "M2"), "te": tea,
    "empanada": empanada,
}


def generate(out):
    d = os.path.join(out, "icons")
    os.makedirs(d, exist_ok=True)
    for name, fn in ICONS10.items():
        cv = fn()
        cv.outline()
        cv.save(os.path.join(d, "p_%s.png" % name))
