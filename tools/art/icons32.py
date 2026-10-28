"""Íconos 2.0 de 32x32 para la interfaz (navegación, fichas, botones).

Silueta fuerte en un color dominante, rampa de 3-4 tonos con luz arriba a la
izquierda y contorno exterior de 1 px. Se generan en assets/pixel_art/icons32/.
"""
import math
import os
from px2 import Canvas
import coin_art


def ic_moneda():
    return coin_art.icon32()


def ic_billete():
    cv = Canvas(32, 32)
    for k, (dx, dy) in enumerate(((4, 9), (2, 6))):
        cv.rect(dx, dy, 26, 16, "G1" if k == 0 else "G2")
        if k == 1:
            cv.rect(dx + 2, dy + 2, 22, 12, "G3")
            cv.rect(dx + 3, dy + 3, 20, 10, "G2")
            cv.ellipse(dx + 13, dy + 8, 4, 4, "G3")
            cv.ellipse(dx + 13, dy + 8, 2, 3, "G1")
            cv.rect(dx + 4, dy + 4, 3, 2, "G3")
            cv.rect(dx + 19, dy + 10, 3, 2, "G3")
    cv.outline()
    return cv


def ic_corona():
    cv = Canvas(32, 32)
    pts = [(4, 10), (10, 18), (16, 6), (22, 18), (28, 10)]
    for y in range(6, 26):
        for x in range(3, 30):
            top = 26
            for (ax, ay), (bx, by) in zip(pts, pts[1:]):
                if ax <= x <= bx:
                    top = round(ay + (by - ay) * (x - ax) / (bx - ax))
            if y >= top and y <= 24:
                cv.put(x, y, "Y2" if y > top + 1 else "Y3")
    cv.rect(4, 21, 25, 4, "Y1")
    cv.hline(4, 21, 25, "Y2")
    for x, c in ((9, "R2"), (16, "C2"), (23, "R2")):
        cv.rect(x - 1, 16, 3, 3, c)
        cv.put(x - 1, 16, "W")
    for x, y in pts:
        cv.ellipse(x, y - 2, 2, 2, "Y3")
        cv.put(x - 1, y - 3, "Y4")
    cv.outline()
    return cv


def ic_tienda():
    cv = Canvas(32, 32)
    cv.rect(5, 14, 22, 15, "E1")
    cv.vline(26, 14, 15, "E2")
    for x in range(3, 29):
        stripe = ((x - 3) // 4) % 2 == 0
        for y in range(7, 13):
            cv.put(x, y, ("C3" if y < 12 else "C2") if stripe else ("W" if y < 12 else "l"))
    for x in range(3, 29, 4):
        cv.rect(x + 1, 13, 2, 1, "C2" if ((x - 3) // 4) % 2 == 0 else "l")
    cv.rect(3, 4, 26, 3, "C1")
    cv.hline(3, 4, 26, "C2")
    cv.rect(7, 17, 9, 7, "C4")
    cv.hline(7, 17, 9, "W")
    cv.rect(8, 21, 2, 3, "R2")
    cv.rect(11, 20, 2, 4, "Y2")
    cv.rect(18, 17, 7, 12, "M2")
    cv.vline(18, 17, 12, "M3")
    cv.put(23, 23, "Y3")
    cv.outline()
    return cv


def ic_mapa():
    cv = Canvas(32, 32)
    panels = [(3, 7, "G3", "G2"), (12, 5, "E1", "E2"), (21, 7, "G3", "G2")]
    for x, y, a, b in panels:
        cv.rect(x, y, 9, 21, a)
        cv.vline(x + 8, y, 21, b)
    cv.rect(23, 9, 6, 4, "C3")                     # río
    cv.rect(24, 13, 4, 14, "C3")
    cv.vline(24, 13, 14, "C4")
    for i in range(6):
        cv.put(5 + i, 14 + (i % 2), "R2")          # camino punteado
        cv.put(13 + i * 1, 16 - (i % 2), "R2")
    cv.rect(15, 9, 4, 4, "R2")                    # marcador
    cv.rect(16, 13, 2, 3, "R2")
    cv.put(15, 9, "R3")
    cv.put(16, 10, "W")
    cv.outline()
    return cv


def ic_bandera():
    cv = Canvas(32, 32)
    cv.rect(5, 3, 3, 26, "M3")
    cv.vline(5, 3, 26, "M4")
    cv.vline(7, 3, 26, "M2")
    cv.rect(3, 27, 7, 3, "x")
    for x in range(8, 28):
        dy = round(2 * math.sin((x - 8) / 20 * math.pi * 1.4))
        for y in range(4, 18):
            band = (y - 4) // 5
            c = ["C3", "W", "C3"][min(band, 2)]
            if math.cos((x - 8) / 20 * math.pi * 1.4) < -0.3:
                c = {"C3": "C2", "W": "l"}[c]
            cv.put(x, y + dy, c)
    cv.ellipse(17, 11 + round(2 * math.sin(9 / 20 * math.pi * 1.4)), 2, 2, "Y2")
    cv.outline()
    return cv


def ic_persona():
    cv = Canvas(32, 32)
    cv.ellipse(16, 25, 11, 7, "C2")
    cv.ellipse(15, 24, 9, 5, "C3")
    cv.rect(5, 26, 23, 5, "C2")
    cv.rect(13, 16, 6, 4, "S2")
    cv.ellipse(16, 11, 7, 8, "S1")
    cv.vline(22, 7, 9, "S2")
    cv.rect(9, 3, 14, 5, "M1")
    cv.hline(10, 3, 11, "M2")
    cv.rect(9, 7, 3, 4, "M1")
    cv.rect(18, 10, 2, 3, "o")
    cv.rect(13, 10, 2, 3, "o")
    cv.hline(14, 15, 4, "R2")
    cv.outline()
    return cv


def ic_engranaje():
    cv = Canvas(32, 32)
    for k in range(8):
        a = k * math.pi / 4
        cx, cy = 16 + math.cos(a) * 11, 16 + math.sin(a) * 11
        cv.rect(round(cx) - 2, round(cy) - 2, 5, 5, "g")
    cv.ellipse(16, 16, 10, 10, "g")
    cv.ellipse(15, 15, 8, 8, "l")
    cv.ellipse(16, 16, 7, 7, "g")
    cv.ellipse(16, 16, 4, 4, "x")
    cv.ellipse(16, 16, 3, 3, "u")
    cv.outline()
    return cv


def ic_grafico():
    cv = Canvas(32, 32)
    cv.rect(3, 27, 26, 2, "x")
    cv.rect(3, 4, 2, 25, "x")
    for i, (h, c) in enumerate(((7, "G2"), (12, "G2"), (10, "G2"), (18, "G2"))):
        x = 7 + i * 6
        cv.rect(x, 27 - h, 5, h, c)
        cv.vline(x, 27 - h, h, "G3")
        cv.vline(x + 4, 27 - h, h, "G1")
    for i in range(18):
        x = 7 + i
        y = 18 - round(i * 0.7)
        cv.rect(x, y, 2, 2, "Y2")
    cv.rect(24, 3, 5, 5, "Y2")
    cv.put(24, 3, "Y4")
    cv.outline()
    return cv


def ic_candado():
    cv = Canvas(32, 32)
    for a in range(0, 181, 4):
        x = round(16 + math.cos(math.radians(180 + a)) * 7)
        y = round(13 + math.sin(math.radians(180 + a)) * 8)
        cv.rect(x - 1, y, 3, 2, "g")
    cv.rect(8, 13, 3, 3, "g")
    cv.rect(21, 13, 3, 3, "g")
    cv.rect(5, 15, 22, 14, "Y2")
    cv.hline(5, 15, 22, "Y3")
    cv.vline(5, 15, 14, "Y3")
    cv.hline(5, 28, 22, "Y1")
    cv.vline(26, 15, 14, "Y1")
    cv.rect(14, 19, 4, 4, "Y1")
    cv.rect(15, 22, 2, 4, "Y1")
    cv.outline()
    return cv


def ic_reloj():
    cv = Canvas(32, 32)
    cv.ellipse(16, 16, 13, 13, "C2")
    cv.ellipse(16, 16, 11, 11, "W")
    cv.ellipse(17, 17, 10, 10, "l")
    cv.ellipse(16, 16, 9, 9, "W")
    for k in range(12):
        a = k * math.pi / 6
        cv.put(round(16 + math.cos(a) * 9), round(16 + math.sin(a) * 9), "x")
    cv.rect(15, 8, 2, 9, "o")
    for i in range(6):
        cv.put(16 + i, 16 + i // 2, "R2")
    cv.rect(15, 15, 2, 2, "R1")
    cv.outline()
    return cv


def ic_caja():
    cv = Canvas(32, 32)
    cv.rect(4, 12, 24, 17, "M3")
    cv.vline(27, 12, 17, "M2")
    cv.hline(4, 28, 24, "M2")
    pts = [(4, 12), (10, 5), (28, 5), (28, 12)]
    for y in range(5, 12):
        x0 = 4 + round((12 - y) * 6 / 7)
        cv.hline(x0, y, 28 - x0 + (12 - y) // 3, "M4")
    cv.hline(4, 12, 24, "M2")
    cv.rect(14, 5, 5, 23, "E2")
    cv.vline(14, 5, 23, "E1")
    cv.rect(7, 18, 5, 4, "E1")
    cv.hline(7, 19, 5, "M2")
    cv.outline()
    return cv


def ic_camion():
    cv = Canvas(32, 32)
    cv.rect(2, 8, 18, 14, "W")
    cv.hline(2, 8, 18, "W")
    cv.hline(2, 21, 18, "l")
    cv.rect(4, 11, 14, 5, "C3")
    cv.hline(4, 11, 14, "C4")
    cv.rect(20, 12, 9, 10, "R2")
    cv.hline(20, 12, 9, "R3")
    cv.rect(22, 14, 5, 4, "C4")
    cv.hline(2, 22, 27, "x")
    for wx in (7, 23):
        cv.ellipse(wx, 25, 3, 3, "o")
        cv.ellipse(wx, 25, 1, 1, "g")
    cv.outline()
    return cv


def ic_rayo():
    cv = Canvas(32, 32)
    poly = [(19, 2), (7, 18), (15, 18), (11, 30), (25, 12), (17, 12), (21, 2)]
    for y in range(32):
        for x in range(32):
            inside = False
            j = len(poly) - 1
            for i in range(len(poly)):
                xi, yi = poly[i]
                xj, yj = poly[j]
                if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
                    inside = not inside
                j = i
            if inside:
                cv.put(x, y, "Y3" if x + y < 30 else "Y2")
    cv.outline()
    return cv


def ic_check():
    cv = Canvas(32, 32)
    for i in range(8):
        cv.rect(5 + i, 15 + i, 5, 5, "G2")
    for i in range(14):
        cv.rect(12 + i, 21 - i * 1.15 if False else 22 - round(i * 1.2), 5, 5, "G2")
    for i in range(8):
        cv.put(5 + i, 15 + i, "G3")
    for i in range(14):
        cv.put(12 + i, 22 - round(i * 1.2), "G3")
    cv.outline()
    return cv


def ic_regalo():
    cv = Canvas(32, 32)
    cv.rect(5, 15, 22, 14, "R2")
    cv.vline(5, 15, 14, "R3")
    cv.vline(26, 15, 14, "R1")
    cv.rect(3, 10, 26, 6, "R2")
    cv.hline(3, 10, 26, "R3")
    cv.rect(14, 10, 4, 19, "Y2")
    cv.vline(14, 10, 19, "Y3")
    for dx in (-1, 1):
        for i in range(6):
            cv.rect(16 + dx * (3 + i) - (1 if dx < 0 else 0), 5 + abs(i - 3) // 1, 2, 3, "Y2")
    cv.rect(14, 7, 4, 4, "Y1")
    cv.outline()
    return cv


def ic_estrella():
    cv = Canvas(32, 32)
    pts = []
    for k in range(10):
        r = 14 if k % 2 == 0 else 6
        a = -math.pi / 2 + k * math.pi / 5
        pts.append((16 + math.cos(a) * r, 17 + math.sin(a) * r))
    for y in range(32):
        for x in range(32):
            inside = False
            j = len(pts) - 1
            for i in range(len(pts)):
                xi, yi = pts[i]
                xj, yj = pts[j]
                if (yi > y + 0.5) != (yj > y + 0.5) and x + 0.5 < (xj - xi) * (y + 0.5 - yi) / (yj - yi) + xi:
                    inside = not inside
                j = i
            if inside:
                cv.put(x, y, "Y3" if x < 16 and y < 18 else "Y2")
    cv.put(13, 11, "Y4")
    cv.outline()
    return cv


def ic_flecha_arriba():
    cv = Canvas(32, 32)
    for i in range(12):
        cv.hline(16 - i, 4 + i, i * 2 + 1, "G2")
        cv.put(16 - i, 4 + i, "G3")
    cv.rect(11, 16, 11, 13, "G2")
    cv.vline(11, 16, 13, "G3")
    cv.vline(21, 16, 13, "G1")
    cv.outline()
    return cv


def arrow(left):
    cv = Canvas(32, 32)
    for i in range(10):
        cv.rect(8 + i, 6 + i, 4, 2, "Y2")
        cv.rect(8 + i, 25 - i, 4, 2, "Y2" if i < 9 else "Y1")
    cv.rect(17, 15, 5, 3, "Y2")
    cv.outline()
    return cv if not left else _flip(cv)


def _flip(cv):
    out = Canvas(32, 32)
    out.paste(cv, 0, 0, flip=True)
    return out


def ic_cerrar():
    cv = Canvas(32, 32)
    for i in range(18):
        cv.rect(6 + i, 6 + i, 4, 3, "R2")
        cv.rect(23 - i, 6 + i, 4, 3, "R2")
    cv.outline()
    return cv


def ic_alerta():
    cv = Canvas(32, 32)
    for y in range(4, 28):
        half = round((y - 4) * 0.55)
        cv.hline(16 - half, y, half * 2 + 1, "Y2")
        cv.put(16 - half, y, "Y3")
    cv.rect(15, 11, 3, 9, "o")
    cv.rect(15, 22, 3, 3, "o")
    cv.outline()
    return cv


def ic_calendario():
    cv = Canvas(32, 32)
    cv.rect(4, 7, 24, 21, "W")
    cv.vline(27, 7, 21, "l")
    cv.rect(4, 7, 24, 6, "R2")
    cv.hline(4, 7, 24, "R3")
    for x in (9, 22):
        cv.rect(x, 4, 2, 6, "x")
    for r in range(3):
        for c in range(4):
            cv.rect(7 + c * 5, 15 + r * 4, 3, 2, "g" if (r, c) != (1, 2) else "R2")
    cv.outline()
    return cv


def ic_mate():
    cv = Canvas(32, 32)
    cv.ellipse(15, 21, 9, 8, "M2")
    cv.ellipse(14, 20, 7, 6, "M3")
    cv.rect(7, 11, 16, 4, "Y2")
    cv.hline(7, 11, 16, "Y3")
    cv.rect(8, 9, 14, 3, "G2")
    cv.hline(8, 9, 14, "G3")
    cv.rect(18, 2, 2, 10, "l")
    cv.rect(20, 2, 3, 2, "l")
    cv.vline(18, 2, 10, "W")
    cv.outline()
    return cv


ICONS32 = {
    "moneda": ic_moneda, "billete": ic_billete, "corona": ic_corona, "tienda": ic_tienda,
    "mapa": ic_mapa, "bandera": ic_bandera, "persona": ic_persona, "engranaje": ic_engranaje,
    "grafico": ic_grafico, "candado": ic_candado, "reloj": ic_reloj, "caja": ic_caja,
    "camion": ic_camion, "rayo": ic_rayo, "check": ic_check, "regalo": ic_regalo,
    "estrella": ic_estrella, "flecha_arriba": ic_flecha_arriba, "izquierda": lambda: arrow(True),
    "derecha": lambda: arrow(False), "cerrar": ic_cerrar, "alerta": ic_alerta,
    "calendario": ic_calendario, "mate": ic_mate,
}


def generate(out):
    d = os.path.join(out, "icons32")
    os.makedirs(d, exist_ok=True)
    for name, fn in ICONS32.items():
        cv = fn()
        cv.clean_orphans()
        cv.save(f"{d}/{name}.png")
