"""Paisajes regionales de la 10.0 (480x200), detrás del negocio de cada provincia.

Misma estructura que las calles de la 0.7 (para que personas y colectivo caigan
en su lugar): fondo 0-149, borde en 150, vereda/banquina 151-181, cordón
182-185 y ruta 186-199. El centro (LOT 142-338) queda más despejado porque ahí
va el edificio.

  noa        cerros de colores, cardones y cielo de altura
  nea        selva subtropical sobre tierra colorada
  cuyo       los Andes nevados y viñedos con álamos
  patagonia  estepa, un lago azul y la cordillera
  pampeana   llanura infinita, molino y alambrado
  centro     sierras verdes y un pueblo de techos rojos
(CABA usa la calle porteña de la 0.7: locations/street_centro.png.)
"""
import math
import os
import random
from px2 import Canvas

BW, BH = 480, 200
EDGE, CURB, ROAD = 150, 182, 186
LOT = (142, 338)


def sky(cv, top, bottom, bands):
    h = (bottom - top) // len(bands)
    for i, c in enumerate(bands):
        cv.rect(0, top + i * h, BW, h + 1, c)
        if i:
            for x in range(0, BW, 4):        # tramado suave entre bandas
                cv.put(x + (i % 2) * 2, top + i * h, bands[i - 1])


def cloud(cv, x, y, s=1.0):
    cv.ellipse(x, y, int(14 * s), int(5 * s), "W")
    cv.ellipse(x + int(10 * s), y - 3, int(9 * s), int(5 * s), "W")
    cv.hline(x - int(12 * s), y + int(4 * s), int(30 * s), "l")


def ridge(cv, base, amp, period, phase, colors, light=None, seed=0):
    """Línea de cerros: colores = (cuerpo, sombra); light = lado iluminado."""
    for x in range(BW):
        t = (x + phase) / period
        h = amp * (0.55 + 0.45 * math.sin(t * 2 * math.pi) + 0.15 * math.sin(t * 7.3 + seed))
        top = int(base - h)
        slope = math.cos(t * 2 * math.pi)
        for y in range(top, EDGE):
            c = colors[0]
            if light and slope > 0.2:
                c = light
            elif slope < -0.3:
                c = colors[1]
            cv.put(x, y, c)
        cv.put(x, top, "o")


def ground(cv, c1, c2, specks=None, rnd=None):
    cv.rect(0, EDGE + 1, BW, CURB - EDGE - 1, c1)
    for y in range(EDGE + 3, CURB, 5):
        for x in range((y // 5 % 2) * 6, BW, 13):
            cv.hline(x, y, 3, c2)
    if specks and rnd:
        for _ in range(60):
            cv.put(rnd.randrange(BW), rnd.randrange(EDGE + 2, CURB), rnd.choice(specks))
    cv.hline(0, EDGE, BW, "o")


def road(cv, curb=("l", "g"), asphalt=("u", "x"), line="w"):
    cv.rect(0, CURB, BW, ROAD - CURB, curb[0])
    cv.hline(0, ROAD - 1, BW, curb[1])
    cv.rect(0, ROAD, BW, BH - ROAD, asphalt[1])
    cv.hline(0, ROAD, BW, asphalt[0])
    for x in range(0, BW, 32):
        cv.rect(x + 6, 193, 16, 2, line)


def cardon(cv, x, h):
    cv.rect(x, EDGE - h, 5, h, "G1")
    cv.vline(x + 1, EDGE - h, h, "G2")
    for side, yy in ((-1, EDGE - h + 10), (1, EDGE - h + 16)):
        ax = x - 5 if side < 0 else x + 5
        cv.rect(ax, yy, 5, 3, "G1")
        cv.rect(ax + (0 if side < 0 else 2), yy - 10, 3, 10, "G1")
        cv.vline(ax + (1 if side < 0 else 3), yy - 10, 10, "G2")
    cv.put(x + 2, EDGE - h - 1, "o")


def poplar(cv, x, h=46):
    cv.rect(x + 2, EDGE - 8, 2, 8, "M2")
    cv.ellipse(x + 3, EDGE - h // 2 - 4, 4, h // 2, "G1")
    cv.ellipse(x + 2, EDGE - h // 2 - 6, 2, h // 2 - 4, "G2")


def jungle_tree(cv, x, rnd):
    h = rnd.randint(40, 70)
    cv.rect(x, EDGE - h, 4, h, "M2")
    for k in range(4):
        cv.ellipse(x + 2 + rnd.randint(-10, 10), EDGE - h + rnd.randint(-6, 10), rnd.randint(10, 16), rnd.randint(6, 9), rnd.choice(("G1", "G2", "G1")))
    cv.ellipse(x - 2, EDGE - h - 2, 6, 3, "G3")


def vine_rows(cv, x0, x1, y0, y1, grape="u"):
    for y in range(y0, y1, 6):
        cv.hline(x0, y, x1 - x0, "G1")
        cv.hline(x0, y - 1, x1 - x0, "G2")
        for x in range(x0 + (y // 6) % 3, x1, 7):
            cv.put(x, y + 1, grape)


def fence_line(cv, y):
    cv.hline(0, y, BW, "M3")
    cv.hline(0, y + 4, BW, "M3")
    for x in range(0, BW, 14):
        cv.vline(x, y - 2, 10, "M2")


def windmill(cv, x, y):
    for k in range(36):
        cv.put(x - k // 6, y + k, "d")
        cv.put(x + k // 6, y + k, "d")
    for bx, by in ((-7, -7), (7, -7), (7, 7), (-7, 7), (0, -9), (9, 0), (0, 9), (-9, 0)):
        for k in range(1, 8):
            cv.put(x + bx * k // 8, y + by * k // 8, "l")
    cv.rect(x - 1, y - 1, 3, 3, "R2")


def house(cv, x, w, h, roof="R2", wall_c="w"):
    cv.rect(x, EDGE - h, w, h, wall_c)
    for k in range(6):
        cv.hline(x - 2 + k, EDGE - h - 1 - k, w + 4 - k * 2, roof)
    cv.rect(x + w // 2 - 2, EDGE - 9, 4, 9, "M2")
    cv.rect(x + 2, EDGE - h + 4, 4, 4, "C3")


def noa(rnd):
    cv = Canvas(BW, BH)
    sky(cv, 0, 120, ["C2", "C3", "C3", "C4"])
    cloud(cv, 60, 22)
    cloud(cv, 400, 34, 0.8)
    # Cerros de siete colores (Quebrada de Humahuaca): bandas inclinadas que
    # siguen la ladera, con un tono más oscuro del lado en sombra.
    bands = (("R2", "R1"), ("Q", "Y1"), ("E2", "S2"), ("G3", "G2"), ("S2", "S3"), ("R3", "R2"))
    for x in range(BW):
        t = (x + 10) / 170
        h = 46 * (0.55 + 0.45 * math.sin(t * 2 * math.pi) + 0.15 * math.sin(t * 7.3 + 1))
        top = int(112 - h)
        shade = math.cos(t * 2 * math.pi) < -0.2
        for y in range(top, EDGE):
            k = int((y - top * 0.5 + 5 * math.sin(x / 19.0)) // 6) % len(bands)
            cv.put(x, y, bands[k][1 if shade else 0])
        cv.put(x, top, "o")
    ridge(cv, 138, 22, 120, 60, ("M3", "M2"), "M4", 3)
    for x in (24, 70, 104, 372, 420, 452):
        cardon(cv, x, rnd.randint(22, 34))
    ground(cv, "E2", "S2", ("M3", "S1"), rnd)
    road(cv, ("E1", "E2"), ("x", "u"), "Y2")
    return cv


def nea(rnd):
    cv = Canvas(BW, BH)
    sky(cv, 0, 110, ["C2", "C3", "C4"])
    cloud(cv, 120, 26, 1.2)
    cloud(cv, 330, 18)
    ridge(cv, 120, 18, 200, 0, ("G1", "G1"), "G2", 2)
    for x in list(range(0, LOT[0] - 10, 22)) + list(range(LOT[1] + 6, BW, 22)):
        jungle_tree(cv, x + rnd.randint(-4, 4), rnd)
    for x in range(LOT[0], LOT[1], 30):
        cv.ellipse(x, EDGE - 6, 16, 8, "G1")
    ground(cv, "R1", "R2", ("R3", "M2"), rnd)
    road(cv, ("R2", "R1"), ("x", "u"), "w")
    return cv


def cuyo(rnd):
    cv = Canvas(BW, BH)
    sky(cv, 0, 100, ["C2", "C3", "C4"])
    cloud(cv, 410, 20, 0.9)
    # cordillera nevada
    for x in range(BW):
        t = x / 95.0
        h = 62 + 22 * math.sin(t * 2.1) + 10 * math.sin(t * 5.7)
        top = int(118 - h)
        for y in range(top, EDGE):
            c = "W" if y < top + 10 else ("g" if math.cos(t * 2.1) > 0 else "d")
            cv.put(x, y, c)
        cv.put(x, top, "x")
    ridge(cv, 136, 14, 140, 30, ("M3", "M2"), "M4", 5)
    vine_rows(cv, 0, LOT[0] - 8, 128, EDGE)
    vine_rows(cv, LOT[1] + 8, BW, 128, EDGE)
    for x in list(range(4, LOT[0] - 20, 18)) + list(range(LOT[1] + 12, BW - 6, 18)):
        poplar(cv, x, 40 + (x % 3) * 6)
    ground(cv, "S2", "M3", ("M2", "E2"), rnd)
    road(cv)
    return cv


def patagonia(rnd):
    cv = Canvas(BW, BH)
    sky(cv, 0, 100, ["C1", "C2", "C3", "C4"])
    for x, y in ((90, 18), (260, 30), (420, 14)):
        cv.ellipse(x, y, 26, 4, "W")
        cv.hline(x - 20, y + 4, 40, "l")
    for x in range(BW):
        t = x / 70.0
        top = int(96 - 30 * abs(math.sin(t)) - 8 * math.sin(t * 3.1))
        for y in range(top, 128):
            cv.put(x, y, "W" if y < top + 8 else "d")
        cv.put(x, top, "x")
    cv.rect(0, 120, BW, 12, "C2")         # lago
    for x in range(0, BW, 9):
        cv.hline(x + (x // 9) % 4, 124, 4, "C4")
    ridge(cv, 146, 10, 160, 40, ("E2", "Y1"), "E1", 7)
    for _ in range(40):
        x = rnd.randrange(BW)
        if not LOT[0] < x < LOT[1]:
            cv.ellipse(x, EDGE - 2, 3, 2, "Y1")
            cv.put(x - 1, EDGE - 4, "Y2")
    ground(cv, "E2", "Y1", ("M3", "E1"), rnd)
    road(cv)
    return cv


def pampeana(rnd):
    cv = Canvas(BW, BH)
    sky(cv, 0, 126, ["C2", "C3", "C3", "C4"])
    cloud(cv, 70, 30, 1.3)
    cloud(cv, 300, 22, 1.1)
    cloud(cv, 450, 40, 0.8)
    cv.rect(0, 126, BW, EDGE - 126, "G2")
    for y in range(128, EDGE, 4):
        for x in range((y // 4 % 2) * 5, BW, 11):
            cv.hline(x, y, 4, "Y2" if y < 138 else "G3")
    cv.hline(0, 126, BW, "G1")
    for x in (40, 410):
        cv.ellipse(x, 120, 12, 8, "G1")
        cv.rect(x - 1, 124, 3, 6, "M2")
    windmill(cv, 96, 92)
    fence_line(cv, 140)
    ground(cv, "G2", "G3", ("G1", "Y2"), rnd)
    road(cv, ("E2", "M3"), ("x", "u"), "w")
    return cv


def centro(rnd):
    cv = Canvas(BW, BH)
    sky(cv, 0, 110, ["C2", "C3", "C4"])
    cloud(cv, 380, 28)
    ridge(cv, 116, 34, 150, 20, ("G1", "u"), "G2", 4)
    ridge(cv, 134, 16, 110, 70, ("G2", "G1"), "G3", 6)
    for x in list(range(6, LOT[0] - 16, 26)) + list(range(LOT[1] + 6, BW - 16, 26)):
        house(cv, x, 18, 14 + (x % 3) * 3, ("R2", "R1", "Q")[x % 3])
    cv.rect(46, EDGE - 40, 6, 40, "w")      # campanario
    for k in range(4):
        cv.hline(45 + k, EDGE - 41 - k, 8 - k * 2, "R2")
    ground(cv, "E1", "E2", ("l", "E2"), rnd)
    road(cv)
    return cv


LANDSCAPES = {"noa": noa, "nea": nea, "cuyo": cuyo, "patagonia": patagonia, "pampeana": pampeana, "centro_sierras": centro}


def generate(out):
    d = os.path.join(out, "locations")
    os.makedirs(d, exist_ok=True)
    for name, fn in LANDSCAPES.items():
        cv = fn(random.Random(name))
        cv.save(os.path.join(d, "street_%s.png" % name))


if __name__ == "__main__":
    generate(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "pixel_art"))
