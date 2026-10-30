"""Íconos de negocio 11: el producto estrella de cada negocio en 32x32 con
volumen (luz desde arriba a la izquierda, 4 tonos por color) y contorno
marrón cálido. Reemplazan a los edificios chiquitos en businesses/<id>_badge.png,
que usan la pestaña Negocios y los pines del mapa.

Uso: python3 tools/art/product_badges.py
(escribe pixel_art/businesses/ y la versión 11 re-estilada en escenarios/).
generate.py lo llama después de buildings2 para que no se pisen.
"""
import math
import os
from PIL import Image, ImageDraw

S = 32
OUTLINE = (58, 30, 14)
LIGHT = (-0.5, -0.62, 0.6)

# Rampas: (sombra, medio, luz, brillo)
WHITE = ((150, 140, 128), (214, 206, 192), (244, 238, 226), (255, 255, 255))
CREAM = ((176, 146, 100), (226, 200, 150), (246, 228, 188), (255, 248, 226))
YELLOW = ((190, 128, 20), (240, 188, 40), (255, 224, 92), (255, 250, 190))
RED = ((118, 20, 26), (188, 40, 40), (230, 82, 70), (255, 172, 150))
GREEN = ((30, 80, 30), (60, 140, 50), (110, 190, 70), (190, 235, 140))
OLIVE = ((38, 58, 20), (78, 108, 30), (128, 158, 50), (200, 220, 120))
PURPLE = ((58, 20, 58), (108, 40, 98), (158, 80, 148), (220, 160, 210))
BROWN = ((70, 40, 20), (120, 70, 35), (170, 110, 60), (220, 170, 110))
TAN = ((138, 98, 58), (188, 148, 94), (220, 190, 134), (245, 225, 180))
POTATO = ((150, 108, 40), (200, 158, 70), (230, 198, 110), (250, 230, 170))
BLUE = ((20, 40, 90), (40, 90, 170), (90, 150, 220), (190, 225, 255))
GRAY = ((50, 50, 60), (90, 90, 105), (140, 140, 155), (205, 205, 218))
WINE = ((58, 10, 24), (108, 20, 40), (160, 40, 60), (220, 110, 120))
BOTTLE = ((18, 38, 24), (36, 66, 40), (66, 106, 58), (150, 190, 140))
PALEGLASS = ((120, 140, 80), (170, 190, 110), (210, 225, 150), (245, 250, 210))
PINK = ((170, 80, 80), (220, 130, 120), (245, 175, 160), (255, 222, 210))
CRUST = ((148, 68, 20), (204, 118, 40), (240, 168, 70), (255, 214, 140))
OIL = ((140, 110, 10), (196, 160, 30), (232, 204, 70), (255, 240, 160))
ORANGE = ((170, 80, 10), (230, 130, 30), (255, 180, 70), (255, 225, 160))


class Icon:
    def __init__(self):
        self.im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        self.p = self.im.load()

    def put(self, x, y, c):
        if 0 <= x < S and 0 <= y < S:
            self.p[x, y] = tuple(c) + (255,)

    @staticmethod
    def tone(d):
        return 3 if d > 0.88 else 2 if d > 0.55 else 1 if d > 0.12 else 0

    def sphere(self, cx, cy, rx, ry, ramp, hi=True):
        """Elipse con volumen de esfera."""
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                nx, ny = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
                q = nx * nx + ny * ny
                if q > 1.0:
                    continue
                nz = math.sqrt(1.0 - q)
                d = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]
                t = self.tone(d)
                self.put(x, y, ramp[t if hi or t < 3 else 2])

    def cyl(self, x0, y0, x1, y1, ramp):
        """Rectángulo con volumen de cilindro vertical (botellas, bolsas)."""
        cx, r = (x0 + x1 + 1) / 2.0, (x1 - x0 + 1) / 2.0
        for x in range(x0, x1 + 1):
            nx = (x + 0.5 - cx) / r
            nz = math.sqrt(max(0.0, 1.0 - nx * nx))
            t = self.tone(nx * LIGHT[0] + nz * (LIGHT[2] + 0.35))
            for y in range(y0, y1 + 1):
                self.put(x, y, ramp[t])

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.put(x, y, c)

    def poly(self, pts, c):
        layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(layer).polygon(pts, fill=tuple(c) + (255,))
        self.im.alpha_composite(layer)

    def line(self, pts, c, w=1):
        layer = Image.new("RGBA", (S, S), (0, 0, 0, 0))
        ImageDraw.Draw(layer).line(pts, fill=tuple(c) + (255,), width=w)
        self.im.alpha_composite(layer)

    def tube(self, pts, radius, ramp):
        """Trazo grueso con volumen: esferas a lo largo de una curva."""
        for i, (x, y) in enumerate(pts):
            r = radius(i / max(1, len(pts) - 1)) if callable(radius) else radius
            self.sphere(x, y, r, r, ramp)

    def leaf(self, x, y, ang, length, ramp):
        dx, dy = math.cos(ang), math.sin(ang)
        tip = (x + dx * length, y + dy * length)
        mid = (x + dx * length * 0.5, y + dy * length * 0.5)
        w = length * 0.32
        side = (-dy * w, dx * w)
        self.poly([(x, y), (mid[0] + side[0], mid[1] + side[1]), tip, (mid[0] - side[0], mid[1] - side[1])], ramp[1])
        self.poly([(x, y), (mid[0] + side[0], mid[1] + side[1]), tip], ramp[2])
        self.line([(x, y), tip], ramp[0])

    def finish(self):
        """Contorno de 1 px alrededor de la silueta."""
        src = self.im.copy()
        sp = src.load()
        for y in range(S):
            for x in range(S):
                if sp[x, y][3]:
                    continue
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if 0 <= nx < S and 0 <= ny < S and sp[nx, ny][3]:
                        self.p[x, y] = OUTLINE + (255,)
                        break
        return self.im


def arc(cx, cy, r, a0, a1, n):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / (n - 1)), cy + r * math.sin(a0 + (a1 - a0) * i / (n - 1))) for i in range(n)]


# ------------------------------------------------------------------ íconos

def algodonal(c):          # capullo de algodón abierto
    for a in range(5):
        ang = -math.pi / 2 + a * 2 * math.pi / 5 + 0.3
        c.poly([(16, 20), (16 + 13 * math.cos(ang - 0.25), 20 + 11 * math.sin(ang - 0.25)), (16 + 13 * math.cos(ang + 0.25), 20 + 11 * math.sin(ang + 0.25))], BROWN[1])
    c.line([(16, 24), (16, 30)], GREEN[0], 2)
    for x, y, r in [(10, 14, 6), (22, 14, 6), (16, 10, 6.5), (11, 20, 5.5), (21, 20, 5.5), (16, 17, 6)]:
        c.sphere(x, y, r, r * 0.95, WHITE)


def papas_andinas(c):      # papas andinas de colores
    for x, y, rx, ry, ramp in [(11, 13, 7, 5.5, PURPLE), (21, 15, 7.5, 6, POTATO), (15, 22, 8, 6, RED)]:
        c.sphere(x, y, rx, ry, ramp)
        for ex, ey in [(-2, -1), (2, 1), (0, 2)]:
            c.put(int(x + ex), int(y + ey), ramp[0])


def bottle(c, glass, cap, label, x0=9, x1=18):
    c.cyl(x0, 13, x1, 29, glass)
    c.poly([(x0, 13), (x0 + 3, 8), (x1 - 3, 8), (x1, 13)], glass[1])
    c.cyl(x0 + 3, 3, x1 - 3, 8, glass)
    c.cyl(x0 + 3, 1, x1 - 3, 3, cap)
    if label:
        c.cyl(x0, 17, x1, 24, label)


def almazara(c):           # botella de aceite de oliva y aceituna
    bottle(c, OIL, BROWN, CREAM)
    c.sphere(13.5, 20.5, 2.2, 2.2, OLIVE)
    c.sphere(24, 25, 5, 4, OLIVE)
    c.leaf(24, 21, -1.2, 8, GREEN)


def olivar(c):             # rama de olivo con aceitunas
    c.line([(3, 27), (28, 6)], BROWN[1], 2)
    for t, side in [(0.15, 1), (0.3, -1), (0.48, 1), (0.62, -1), (0.8, 1)]:
        x, y = 3 + 25 * t, 27 - 21 * t
        c.leaf(x, y, -0.68 + side * 0.9, 9, OLIVE)
    for x, y in [(12, 22), (17, 22), (21, 13)]:
        c.sphere(x, y, 3.2, 3.8, PURPLE)


def wine_glass(c, x, wine):
    c.poly([(x - 6, 12), (x + 6, 12), (x + 4, 21), (x - 4, 21)], (230, 236, 240))
    c.sphere(x, 18, 5, 4, wine)
    c.rect(x - 4, 12, x + 4, 15, (236, 242, 246))
    c.line([(x, 22), (x, 28)], (220, 226, 232), 2)
    c.rect(x - 4, 29, x + 4, 30, (210, 216, 222))
    c.put(x - 4, 13, (255, 255, 255)); c.put(x - 4, 14, (255, 255, 255))


def bodega_torrontes(c):   # vino blanco de altura
    bottle(c, PALEGLASS, YELLOW, CREAM, 4, 13)
    wine_glass(c, 23, YELLOW)


def bodega_malbec(c):      # Malbec
    bottle(c, BOTTLE, WINE, CREAM, 4, 13)
    c.rect(6, 19, 11, 21, WINE[1])
    wine_glass(c, 23, WINE)


def citricola(c):          # limón con hoja y gajo
    c.sphere(14, 18, 11, 8.5, YELLOW)
    c.poly([(3, 18), (6, 16), (6, 20)], YELLOW[1])
    c.poly([(25, 18), (22, 15), (22, 21)], YELLOW[0])
    for x, y in [(9, 15), (13, 21), (18, 16), (17, 23)]:
        c.put(x, y, YELLOW[3] if y < 18 else YELLOW[1])
    c.leaf(18, 10, -0.5, 11, GREEN)
    c.line([(16, 11), (18, 9)], BROWN[0], 1)


def bananal(c):            # racimo de bananas
    def bez(p0, p1, p2, n=16):
        return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                 (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / (n - 1) for i in range(n))]
    for tip, ctrl in [((28, 9), (14, 20)), ((26, 20), (10, 24)), ((18, 28), (6, 26))]:
        pts = bez((8, 6), ctrl, tip)
        c.tube(pts, lambda t: 1.4 + 2.6 * math.sin(min(1.0, t * 1.15) * math.pi * 0.9), YELLOW)
        x, y = pts[-1]
        c.rect(int(x) - 1, int(y) - 1, int(x), int(y), BROWN[0])
    c.rect(5, 2, 10, 7, GREEN[1])
    c.rect(5, 2, 10, 3, GREEN[2])


def desmotadora(c):        # fardo de algodón atado
    c.cyl(4, 12, 27, 29, CREAM)
    c.rect(4, 12, 27, 13, WHITE[3])
    for x in (9, 16, 22):
        c.rect(x, 12, x + 1, 29, BROWN[1])
    for x, y, r in [(10, 9, 4.5), (17, 7, 5), (23, 9, 4)]:
        c.sphere(x, y, r, r * 0.9, WHITE)


def arrocera(c):           # espigas de arroz
    for k, x0 in enumerate([8, 15, 22]):
        c.line([(x0, 30), (x0 + 2, 10)], GREEN[1], 1)
        c.leaf(x0 + 1, 24, -2.2 + k * 0.6, 9, GREEN)
        for j in range(6):
            gx, gy = x0 + 3 + j * 1.2, 7 + j * 2.8
            c.sphere(gx, gy, 1.6, 2.2, YELLOW, hi=False)


def molino_arrocero(c):    # bolsa de arroz con granos
    c.cyl(6, 9, 25, 30, TAN)
    c.poly([(6, 9), (9, 5), (22, 5), (25, 9)], TAN[2])
    c.rect(8, 16, 23, 24, CREAM[2])
    c.rect(8, 16, 23, 16, CREAM[0])
    for x, y in [(11, 19), (14, 21), (17, 19), (20, 21), (13, 23), (18, 23)]:
        c.rect(x, y, x + 1, y, WHITE[1])
    for x, y in [(12, 6), (15, 4), (18, 6), (16, 7), (20, 5)]:
        c.sphere(x, y, 1.5, 1.1, WHITE, hi=False)


def yerbatal(c):           # mate con bombilla
    c.sphere(15, 20, 10, 10, BROWN)
    c.rect(6, 9, 24, 11, GRAY[2])
    c.rect(6, 9, 24, 9, GRAY[3])
    c.sphere(15, 10, 8, 2, OLIVE, hi=False)
    c.line([(18, 10), (26, 1)], GRAY[3], 2)
    c.line([(19, 11), (27, 2)], GRAY[1], 1)
    c.rect(25, 0, 28, 1, GRAY[2])
    c.rect(9, 27, 21, 29, GRAY[1])


def frigorifico(c):        # bife de chorizo
    c.sphere(16, 17, 13, 10, CREAM)
    c.sphere(16, 17, 11, 8.5, RED)
    for x, y in [(11, 14), (18, 13), (14, 20), (21, 19)]:
        c.rect(x, y, x + 2, y, PINK[3])
    c.sphere(23, 20, 3, 3, WHITE)


def pasas(c):              # racimo de pasas
    c.line([(16, 3), (16, 9)], BROWN[1], 2)
    c.leaf(17, 5, -0.4, 9, OLIVE)
    for x, y in [(11, 11), (16, 11), (21, 11), (9, 16), (14, 16), (19, 16), (24, 16), (12, 21), (17, 21), (22, 21), (14, 26), (19, 26)]:
        c.sphere(x, y, 3.4, 3, ((40, 14, 20), (78, 30, 36), (116, 56, 52), (170, 110, 90)))
        c.put(x - 1, y + 1, (40, 14, 20))


def estancia_ovina(c):     # oveja
    for x, y, r in [(9, 16, 5), (14, 13, 5.5), (20, 13, 5.5), (25, 16, 5), (12, 20, 5), (18, 20, 5.5), (23, 20, 4.5)]:
        c.sphere(x, y, r, r * 0.9, WHITE)
    for x in (10, 14, 20, 24):
        c.rect(x, 24, x + 1, 29, GRAY[0])
    c.sphere(6, 13, 3.6, 4.4, GRAY)
    c.rect(3, 10, 5, 11, GRAY[0])
    c.put(5, 13, (255, 255, 255))


def lanera(c):             # ovillo de lana con agujas
    c.line([(4, 4), (27, 27)], BROWN[2], 2)
    c.line([(27, 4), (4, 27)], BROWN[2], 2)
    c.sphere(16, 17, 11, 11, CREAM)
    for k in range(4):
        pts = arc(10 + k * 4, 30, 18, -math.pi * 0.75, -math.pi * 0.42, 12)
        c.line(pts, CREAM[0], 1)
    c.line(arc(16, 17, 8, 3.6, 5.6, 10), CREAM[3], 1)
    c.rect(3, 3, 4, 4, RED[1]); c.rect(27, 3, 28, 4, RED[1])


def chacra_peras(c):       # pera
    c.sphere(16, 21, 10, 9, ((120, 130, 30), (180, 190, 50), (220, 220, 90), (250, 250, 180)))
    c.sphere(16, 11, 5.5, 6, ((120, 130, 30), (180, 190, 50), (220, 220, 90), (250, 250, 180)))
    c.line([(16, 6), (17, 1)], BROWN[0], 2)
    c.leaf(18, 4, -0.3, 8, GREEN)
    c.put(20, 24, (230, 140, 60)); c.put(21, 23, (230, 140, 60))


def manzanas(c):           # manzana roja
    c.sphere(11, 18, 9, 10, RED)
    c.sphere(21, 18, 9, 10, RED)
    c.rect(15, 8, 17, 9, RED[0])
    c.line([(16, 9), (17, 2)], BROWN[0], 2)
    c.leaf(18, 5, -0.3, 9, GREEN)
    c.sphere(10, 13, 2, 3, ((255, 200, 190),) * 4)


def electronica(c):        # televisor y celular
    c.rect(2, 6, 25, 22, GRAY[0])
    c.rect(3, 7, 24, 21, GRAY[1])
    for y in range(8, 21):
        c.rect(4, y, 23, y, BLUE[1] if y > 14 else BLUE[2])
    c.line([(6, 18), (12, 10)], BLUE[3], 1)
    c.line([(9, 19), (14, 12)], BLUE[3], 1)
    c.rect(11, 23, 16, 25, GRAY[1])
    c.rect(7, 26, 20, 27, GRAY[2])
    c.rect(21, 13, 29, 29, GRAY[0])
    c.rect(22, 14, 28, 27, BLUE[1])
    c.rect(22, 14, 28, 18, BLUE[2])
    c.rect(24, 28, 26, 28, GRAY[3])


def estancia_ganadera(c):  # cabeza de vaca Hereford
    c.poly([(3, 6), (8, 9), (6, 11)], CREAM[2])
    c.poly([(29, 6), (24, 9), (26, 11)], CREAM[2])
    c.sphere(5, 13, 3.5, 2.4, BROWN)
    c.sphere(27, 13, 3.5, 2.4, BROWN)
    c.sphere(16, 15, 9, 10, BROWN)
    c.poly([(13, 6), (19, 6), (21, 24), (11, 24)], WHITE[2])
    c.sphere(16, 24, 7, 5, PINK)
    c.rect(13, 24, 14, 25, PINK[0]); c.rect(18, 24, 19, 25, PINK[0])
    c.rect(10, 13, 11, 14, (20, 14, 10)); c.rect(21, 13, 22, 14, (20, 14, 10))


def salames(c):            # salame con rodaja
    pts = [(5 + i * 1.3, 25 - i * 1.15) for i in range(16)]
    c.tube(pts, 4.6, ((90, 30, 30), (140, 50, 45), (180, 80, 70), (220, 140, 120)))
    for x, y in [(9, 19), (13, 17), (17, 13), (20, 11), (12, 22)]:
        c.put(x, y, CREAM[3])
    for x, y in [(8, 25), (22, 9)]:
        c.line([(x - 3, y - 2), (x + 3, y + 3)], CREAM[1], 1)
    c.sphere(24, 24, 6, 6, ((150, 50, 50), (200, 80, 80), (220, 110, 100), (240, 160, 150)), hi=False)
    for x, y in [(22, 22), (25, 23), (23, 26), (26, 26), (24, 20)]:
        c.put(x, y, WHITE[3])


def usina_lactea(c):       # botella de leche y queso
    c.cyl(4, 11, 15, 29, WHITE)
    c.poly([(4, 11), (7, 6), (12, 6), (15, 11)], WHITE[2])
    c.cyl(7, 2, 12, 6, BLUE)
    c.cyl(4, 18, 15, 22, BLUE)
    c.poly([(14, 29), (30, 29), (30, 20), (14, 25)], YELLOW[1])
    c.poly([(14, 25), (30, 20), (26, 16)], YELLOW[2])
    for x, y in [(19, 26), (25, 24), (22, 27)]:
        c.sphere(x, y, 1.5, 1.2, YELLOW, hi=False)
        c.put(x, y, YELLOW[0])


def molino_harinero(c):    # bolsa de harina y espiga de trigo
    c.cyl(4, 11, 21, 30, CREAM)
    c.poly([(4, 11), (7, 7), (18, 7), (21, 11)], WHITE[2])
    c.sphere(12.5, 8, 6, 2.2, WHITE, hi=False)
    c.rect(6, 18, 19, 23, TAN[1])
    c.rect(6, 18, 19, 18, TAN[3])
    c.line([(26, 30), (23, 6)], YELLOW[0], 1)
    for j in range(7):
        y = 5 + j * 2.6
        c.sphere(22 + 0.15 * j - 1.4, y, 1.4, 2, YELLOW, hi=False)
        c.sphere(22 + 0.15 * j + 1.6, y + 1, 1.4, 2, YELLOW, hi=False)


def panaderia(c):          # medialuna
    pts = arc(16, 30, 15, math.pi * 1.08, math.pi * 1.92, 24)
    c.tube(pts, lambda t: 2.4 + 4.2 * math.sin(t * math.pi), CRUST)
    for t in (0.3, 0.42, 0.58, 0.7):
        x, y = pts[int(t * 23)]
        c.line([(x - 1, y - 4), (x + 1, y + 4)], CRUST[0], 1)
    c.put(14, 17, CRUST[3]); c.put(18, 17, CRUST[3])


ICONS = {
    "algodonal": algodonal, "papas_andinas": papas_andinas, "almazara": almazara, "olivar": olivar,
    "bodega_torrontes": bodega_torrontes, "citricola": citricola, "bananal": bananal,
    "desmotadora": desmotadora, "arrocera": arrocera, "molino_arrocero": molino_arrocero,
    "yerbatal": yerbatal, "frigorifico": frigorifico, "pasas": pasas, "bodega_malbec": bodega_malbec,
    "estancia_ovina": estancia_ovina, "lanera": lanera, "chacra_peras": chacra_peras,
    "manzanas": manzanas, "electronica": electronica, "estancia_ganadera": estancia_ganadera,
    "salames": salames, "usina_lactea": usina_lactea, "molino_harinero": molino_harinero,
    "panaderia": panaderia,
}


def generate(out_dir):
    """Escribe <out_dir>/businesses/<id>_badge.png para cada negocio."""
    d = os.path.join(out_dir, "businesses")
    os.makedirs(d, exist_ok=True)
    for bid, fn in ICONS.items():
        c = Icon()
        fn(c)
        c.finish().save(os.path.join(d, f"{bid}_badge.png"))


if __name__ == "__main__":
    import restyle11
    generate(restyle11.SRC)
    dst = os.path.join(restyle11.ROOT, "assets", "escenarios", "businesses")
    for bid in ICONS:
        im = Image.open(os.path.join(restyle11.SRC, "businesses", f"{bid}_badge.png"))
        restyle11.restyle(im, selective=True).save(os.path.join(dst, f"{bid}_badge.png"))
    print(len(ICONS), "íconos de negocio")
