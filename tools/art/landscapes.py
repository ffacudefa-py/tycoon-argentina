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
    """Nube esponjosa: tres bollos blancos con panza celeste."""
    cv.ellipse(x, y + 1, int(16 * s), int(5 * s), "C4")
    for dx, dy, r in ((-8, 0, 7), (2, -4, 9), (12, -1, 7)):
        cv.ellipse(x + int(dx * s), y + int(dy * s), int(r * s), int(r * s * 0.8), "W")
    cv.hline(x - int(14 * s), y + int(5 * s), int(30 * s), "C4")


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


def ground(cv, c1, c2, specks=None, rnd=None, tiles=True):
    """Vereda en 3/4: lajas con junta y borde de luz, más sombra hacia el frente."""
    cv.rect(0, EDGE + 1, BW, CURB - EDGE - 1, c1)
    if tiles:
        rows = [EDGE + 1, EDGE + 8, EDGE + 16, EDGE + 25]
        for j, y0 in enumerate(rows):
            off = (j % 2) * 11
            for x in range(-off, BW, 22):
                cv.hline(x, y0, 21, c2)                # junta
                cv.vline(x + 21, y0, (rows[j + 1] if j + 1 < len(rows) else CURB) - y0, c2)
                cv.hline(x + 1, y0 + 1, 19, "w")      # borde de luz de cada laja

    cv.hline(0, EDGE, BW, "o")
    cv.hline(0, EDGE + 1, BW, "l")


def bunting(cv, x1, x2, y):
    import math as _m
    for x in range(x1, x2):
        yy = y + int(4 * _m.sin(_m.pi * (x - x1) / max(1, x2 - x1)))
        cv.put(x, yy, "x")
        if (x - x1) % 5 == 2:
            c = "C3" if ((x - x1) // 5) % 2 else "W"
            cv.put(x, yy + 1, c); cv.put(x - 1, yy + 1, c); cv.put(x + 1, yy + 1, c); cv.put(x, yy + 2, c)


def props(cv, rnd, kind):
    """Utilería de vereda fuera del lote del negocio (x 60-135 y 345-420)."""
    for zone in ((64, 132), (348, 416)):
        x = rnd.randint(zone[0], zone[0] + 8)
        regional = {"noa": ["vasija", "cardon"], "nea": ["bananas", "yerba"], "cuyo": ["barrica", "uvas"],
                    "patagonia": ["lana", "lena"], "pampeana": ["fardo", "tranquera"], "centro_sierras": ["canasto", "sifon"]}.get(kind, [])
        items = rnd.sample(regional, len(regional)) + rnd.sample(["maceta", "banco", "farol", "mata"], 2) if regional else rnd.sample(["maceta", "banco", "farol", "barril", "mata", "cartel"], 3)
        for it in items:
            if x > zone[1]:
                break
            y = CURB - 4
            shadow_w = 10
            if it == "vasija":                      # vasija de barro con guarda
                cv.ellipse(x + 5, y - 7, 5, 6, "S2"); cv.ellipse(x + 4, y - 8, 3, 4, "S1")
                cv.rect(x + 3, y - 15, 5, 3, "S2"); cv.hline(x, y - 7, 11, "R2"); cv.hline(x + 1, y - 5, 9, "o")
                w = 12
            elif it == "cardon":
                cv.rect(x + 3, y - 18, 4, 18, "G1"); cv.vline(x + 4, y - 18, 18, "G2")
                cv.rect(x, y - 12, 3, 2, "G1"); cv.rect(x, y - 16, 2, 4, "G1"); cv.put(x + 5, y - 19, "R3")
                w = 10
            elif it in ("bananas", "uvas", "canasto"):           # cajón de fruta / canasto
                cv.rect(x, y - 8, 14, 8, "M3"); cv.hline(x, y - 8, 14, "M4"); cv.hline(x, y - 4, 14, "M2"); cv.frame(x, y - 8, 14, 8, "o")
                col = {"bananas": ("Y3", "Y2"), "uvas": ("R1", "u"), "canasto": ("E1", "M4")}[it]
                for k in range(4):
                    cv.ellipse(x + 2 + k * 3, y - 9, 2, 2, col[k % 2])
                w = 16
            elif it == "yerba":
                cv.rect(x, y - 12, 9, 12, "G2"); cv.rect(x + 1, y - 14, 7, 2, "G2"); cv.rect(x + 2, y - 8, 5, 3, "Y2")
                cv.vline(x, y - 12, 12, "G3"); cv.frame(x, y - 12, 9, 12, "o")
                w = 11
            elif it == "barrica":                   # barrica sobre caballete
                cv.vline(x + 1, y - 3, 3, "M1"); cv.vline(x + 12, y - 3, 3, "M1"); cv.hline(x, y - 3, 14, "M1")
                cv.ellipse(x + 7, y - 9, 7, 6, "M2"); cv.ellipse(x + 6, y - 10, 5, 4, "M3")
                cv.vline(x + 3, y - 14, 10, "x"); cv.vline(x + 11, y - 14, 10, "x"); cv.put(x + 5, y - 12, "M4")
                w = 16
            elif it in ("lana", "fardo"):
                cv.rect(x, y - 10, 14, 10, "E1" if it == "lana" else "Y2"); cv.vline(x + 4, y - 10, 10, "E2" if it == "lana" else "Y1")
                cv.vline(x + 9, y - 10, 10, "E2" if it == "lana" else "Y1"); cv.hline(x, y - 10, 14, "W" if it == "lana" else "Y3"); cv.frame(x, y - 10, 14, 10, "o")
                w = 16
            elif it == "lena":
                for k in range(3):
                    cv.ellipse(x + 3 + k * 5, y - 3, 3, 3, "M2"); cv.put(x + 3 + k * 5, y - 3, "M4")
                cv.ellipse(x + 6, y - 8, 3, 3, "M2"); cv.ellipse(x + 11, y - 8, 3, 3, "M2")
                w = 16
            elif it == "tranquera":
                for yy in (y - 12, y - 8, y - 4):
                    cv.hline(x, yy, 18, "M3")
                cv.vline(x, y - 14, 14, "M1"); cv.vline(x + 17, y - 14, 14, "M1")
                for k in range(14):
                    cv.put(x + 2 + k, y - 4 - (k * 8) // 14, "M2")
                w = 20
            elif it == "sifon":
                cv.rect(x + 1, y - 13, 6, 13, "C3"); cv.vline(x + 2, y - 13, 13, "C4"); cv.rect(x, y - 16, 8, 3, "g")
                cv.rect(x + 7, y - 16, 3, 1, "g"); cv.frame(x + 1, y - 13, 6, 13, "o")
                w = 11
            elif it == "maceta":
                cv.rect(x, y - 8, 9, 8, "M2"); cv.hline(x, y - 8, 9, "M3"); cv.frame(x, y - 8, 9, 8, "o")
                cv.ellipse(x + 4, y - 12, 6, 5, "G2"); cv.put(x + 2, y - 15, "G3"); cv.put(x + 6, y - 14, "R3")
                w = 11
            elif it == "banco":
                cv.rect(x, y - 9, 20, 3, "M3"); cv.rect(x, y - 15, 20, 3, "M3"); cv.hline(x, y - 15, 20, "M4")
                cv.vline(x + 2, y - 6, 6, "o"); cv.vline(x + 17, y - 6, 6, "o"); cv.frame(x, y - 15, 20, 3, "o")
                w = 22; shadow_w = 22
            elif it == "farol":
                cv.vline(x + 3, y - 40, 40, "o"); cv.vline(x + 2, y - 40, 40, "x")
                cv.rect(x, y - 47, 7, 7, "Y3"); cv.frame(x, y - 47, 7, 7, "o"); cv.put(x + 2, y - 45, "W")
                w = 10; shadow_w = 6
            elif it == "barril":
                cv.ellipse(x + 5, y - 7, 5, 7, "M2"); cv.ellipse(x + 4, y - 8, 3, 5, "M3")
                cv.hline(x, y - 10, 11, "x"); cv.hline(x, y - 4, 11, "x")
                w = 13
            elif it == "mata":
                for k in range(3):
                    cv.ellipse(x + 3 + k * 4, y - 4 - (k % 2) * 2, 4, 4, "G2" if k % 2 else "G1")
                cv.put(x + 6, y - 9, "G3")
                w = 16
            else:
                cv.rect(x, y - 22, 14, 12, "M1"); cv.rect(x + 1, y - 21, 12, 10, "u")
                for yy in (y - 19, y - 16, y - 13):
                    cv.hline(x + 3, yy, 8, "w")
                cv.vline(x + 1, y - 10, 10, "M2"); cv.vline(x + 12, y - 10, 10, "M2")
                w = 16
            for sx in range(x, x + shadow_w):                    # sombra de apoyo
                p = cv.img.getpixel((sx, y)) if 0 <= sx < BW else None
                if p:
                    cv.img.putpixel((sx, y), tuple(int(c * 0.7) for c in p[:3]) + (255,))
            x += w + rnd.randint(4, 10)
        bunting(cv, zone[0], zone[1], EDGE - 34)


def road(cv, curb=("l", "g"), asphalt=("u", "x"), line="w"):
    """Calle cálida y más clara (que no compita con la escena)."""
    cv.rect(0, CURB, BW, ROAD - CURB, curb[0])
    cv.hline(0, ROAD - 1, BW, curb[1])
    cv.rect(0, ROAD, BW, BH - ROAD, "g")
    cv.hline(0, ROAD, BW, "x")
    for j, y in enumerate(range(ROAD + 1, BH, 4)):     # adoquines
        for x in range((j % 2) * 4, BW, 8):
            cv.rect(x, y, 7, 3, "l" if (x + y) % 3 else "g")
            cv.hline(x, y + 3, 8, "d")
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
    KIND = "noa"
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
    props(cv, rnd, KIND)
    road(cv, ("E1", "E2"), ("x", "u"), "Y2")
    return cv


def nea(rnd):
    KIND = "nea"
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
    props(cv, rnd, KIND)
    road(cv, ("R2", "R1"), ("x", "u"), "w")
    return cv


def andes(cv, base, amp, seed, far=False):
    """Cordillera con picos, nieve que baja por las laderas y rampa de 3 tonos."""
    import math as _m
    import random as _r
    rr = _r.Random(seed)
    peaks = [(x + rr.randint(-14, 14), amp * rr.uniform(0.55, 1.0)) for x in range(-40, BW + 80, 46)]
    def top_at(x):
        h = 0.0
        for px, ph in peaks:
            h = max(h, ph - abs(x - px) * (ph / 46.0))
        return int(base - h)
    for x in range(BW):
        t = top_at(x)
        left = top_at(x - 1) > t or (top_at(x + 1) <= t and False)
        for y in range(t, EDGE):
            depth = y - t
            snow = depth < 7 + ((x * 7 + seed * 13) % 9) - (3 if (x // 3) % 2 else 0)
            if snow:
                c = "W" if not far else "l"
            else:
                lit = top_at(x - 2) > top_at(x + 2)
                c = ("l" if lit else "g") if far else ("g" if lit else "d")
            cv.put(x, y, c)
        cv.put(x, t, "g" if far else "x")


def cuyo(rnd):
    KIND = "cuyo"
    cv = Canvas(BW, BH)
    sky(cv, 0, 100, ["C2", "C3", "C4"])
    cloud(cv, 410, 20, 0.9)
    andes(cv, 112, 70, 1, far=True)
    andes(cv, 122, 54, 4)
    ridge(cv, 136, 14, 140, 30, ("M3", "M2"), "M4", 5)
    vine_rows(cv, 0, LOT[0] - 8, 128, EDGE)
    vine_rows(cv, LOT[1] + 8, BW, 128, EDGE)
    for x in list(range(4, LOT[0] - 20, 18)) + list(range(LOT[1] + 12, BW - 6, 18)):
        poplar(cv, x, 40 + (x % 3) * 6)
    ground(cv, "S2", "M3", ("M2", "E2"), rnd)
    props(cv, rnd, KIND)
    road(cv)
    return cv


def patagonia(rnd):
    KIND = "patagonia"
    cv = Canvas(BW, BH)
    sky(cv, 0, 100, ["C2", "C3", "C4"])
    for x, y in ((90, 22), (260, 30), (420, 18)):
        cloud(cv, x, y, 1.1)
    # Meseta patagónica (mesas de techo plano) y el Fitz Roy a lo lejos.
    for x in range(BW):
        top = 98 - int(18 * math.exp(-((x - 300) / 22.0) ** 2)) - int(8 * math.exp(-((x - 270) / 9.0) ** 2))
        for y in range(top, 118):
            cv.put(x, y, "l" if y < top + 6 else "g")
        cv.put(x, top, "g")
    for mx0, mw, mh in ((-10, 150, 108), (150, 120, 112), (330, 170, 106)):
        for x in range(mx0, mx0 + mw):
            if 0 <= x < BW:
                edge = min(x - mx0, mx0 + mw - x)
                top = mh + max(0, 8 - edge // 2)
                for y in range(top, 128):
                    cv.put(x, y, "E2" if y < top + 3 else ("S2" if (x + y) % 9 else "M3"))
                cv.put(x, top, "M3")
    for lx, lw in ((20, 110), (340, 120)):    # lagos detrás de la estepa (no cruzan el lote)
        cv.ellipse(lx + lw // 2, 126, lw // 2, 5, "C2")
        cv.hline(lx + 10, 124, lw - 20, "C4")
    ridge(cv, 146, 10, 160, 40, ("E2", "Y1"), "E1", 7)
    for _ in range(40):
        x = rnd.randrange(BW)
        if not LOT[0] < x < LOT[1]:
            cv.ellipse(x, EDGE - 2, 3, 2, "Y1")
            cv.put(x - 1, EDGE - 4, "Y2")
    ground(cv, "E2", "Y1", ("M3", "E1"), rnd)
    props(cv, rnd, KIND)
    road(cv)
    return cv


def pampeana(rnd):
    KIND = "pampeana"
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
    for _ in range(70):
        mx = rnd.randrange(BW)
        my = rnd.randrange(128, EDGE - 2)
        cv.put(mx, my, "G1"); cv.put(mx + 1, my - 1, "G3")
    windmill(cv, 96, 92)
    fence_line(cv, 140)
    ground(cv, "G2", "G3", ("G1", "Y2"), rnd)
    props(cv, rnd, KIND)
    road(cv, ("E2", "M3"), ("x", "u"), "w")
    return cv


def centro(rnd):
    KIND = "centro_sierras"
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
    props(cv, rnd, KIND)
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
