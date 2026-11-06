"""15.0: vehículos con el estándar de la 14 (reemplaza amb_car_* y colectivo_anim).

Cada vehículo se pinta por materiales (chapa, vidrio, cromo, goma) con la misma luz
de fachadas y paisajes: sol arriba a la izquierda, reflejo de cielo arriba de la
línea de horizonte de la chapa y de piso abajo, sombras hacia el violeta frío.

Sale una hoja por vehículo con 4 columnas y 3 filas, para animar por capas:
  fila 0: carrocería nivelada, trompa abajo (frena), trompa arriba (acelera), libre
  fila 1: ruedas, 4 cuadros de giro (la carrocería rebota aparte, sobre la suspensión)
  fila 2: sombra, luz trasera, luz de freno, puertas abiertas (colectivo)
Además data/vehicles.json con las medidas que usa street_vehicle.gd y las hojas
veh_puff.png (humo), veh_dust.png (tierra) y veh_beam.png (haz de faro).

  python tools/art/vehicles15.py
"""
import json
import math
import os

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "assets", "escenarios", "effects")

COOL = np.array([62, 56, 112], float)
WARM = np.array([255, 226, 176], float)
INK = (34, 28, 44)
SKYGLASS = (150, 196, 224)
GLASS_D = (34, 46, 78)
GLASS_M = (58, 86, 130)
CHROME = ((70, 72, 92), (132, 138, 156), (196, 202, 212), (252, 250, 240))
RUBBER = ((22, 20, 28), (40, 37, 48), (62, 58, 72), (94, 90, 106))
BAY = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]


def ramp(hexc):
    """5 tonos: las sombras tiran al violeta frío y las luces al ámbar."""
    b = np.array([int(hexc[i:i + 2], 16) for i in (1, 3, 5)], float)
    out = []
    for k, t in zip((0.42, 0.66, 0.86, 1.0, 1.0), (0.42, 0.24, 0.10, 0.0, 0.0)):
        out.append(b * k * (1 - t) + COOL * t)
    out[3] = b + (WARM - b) * 0.20
    out[4] = b + (WARM - b) * 0.58
    return [tuple(int(v) for v in np.clip(c, 0, 255)) for c in out]


class V:
    """Lienzo por materiales: cada píxel guarda qué es, y al final se sombrea."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.m = Image.new("L", (w, h), 0)
        self.d = ImageDraw.Draw(self.m)
        self.over = []                 # píxeles sueltos (x, y, color) encima de todo

    def poly(self, mat, pts):
        self.d.polygon(pts, fill=mat, outline=mat)

    def rect(self, mat, x0, y0, x1, y1):
        self.d.rectangle((x0, y0, x1, y1), fill=mat)

    def px(self, x, y, c):
        self.over.append((x, y, tuple(c)))

    def hline(self, x0, x1, y, c):
        for x in range(x0, x1 + 1):
            self.px(x, y, c)

    def vline(self, x, y0, y1, c):
        for y in range(y0, y1 + 1):
            self.px(x, y, c)


M_BODY, M_LOW, M_GLASS, M_CHROME, M_RUB, M_WELL, M_ROOF = 1, 2, 3, 4, 5, 6, 7


def shade(v, pal, low, belt, sill, roof_pal=None, reflect=0.46):
    """Sombrea por material. belt: fila de cintura; sill: fila del zócalo."""
    m = np.array(v.m)
    h, w = m.shape
    out = np.zeros((h, w, 4), np.uint8)
    any_mat = m > 0
    for x in range(w):
        col = np.where(any_mat[:, x])[0]
        if not len(col):
            continue
        top = col[0]
        for y in col:
            k = m[y, x]
            if k in (M_BODY, M_LOW, M_ROOF):
                p = pal if k == M_BODY else (low if k == M_LOW else roof_pal)
                if y < belt:                               # techo, parantes y tapas
                    t = 4 if y == top else (3 if y <= top + 2 else 2)
                else:
                    u = (y - belt) / max(1, sill - belt)
                    wob = 0.03 * math.sin(x * 0.19)
                    if u < 0.10:
                        t = 4
                    elif u < reflect + wob - 0.09:
                        t = 3
                    elif u < reflect + wob:
                        t = 1                              # horizonte reflejado en la chapa
                    elif u < 0.80:
                        t = 2
                    else:
                        t = 1
                out[y, x] = p[t] + (255,)
            elif k == M_GLASS:
                gt = np.where(m[:, x] == M_GLASS)[0]
                u = (y - gt[0]) / max(1, gt[-1] - gt[0])
                diag = ((x + y * 0.9) % 17) < 3.4
                c = SKYGLASS if (diag and u < 0.72) else (GLASS_M if u < 0.5 else GLASS_D)
                out[y, x] = c + (255,)
            elif k == M_CHROME:
                out[y, x] = CHROME[2 if y % 2 else 3] + (255,)
            elif k == M_RUB:
                out[y, x] = RUBBER[1 if y == top else 0] + (255,)
            elif k == M_WELL:
                out[y, x] = RUBBER[0] + (255,)
    for x, y, c in v.over:
        if 0 <= x < w and 0 <= y < h:
            out[y, x] = (c if len(c) == 4 else c + (255,))
    return out


def outline(a, color=INK):
    """Contorno de 1 px por fuera de la silueta."""
    al = a[..., 3] > 0
    h, w = al.shape
    o = a.copy()
    for y in range(h):
        for x in range(w):
            if al[y, x]:
                continue
            if any(0 <= nx < w and 0 <= ny < h and al[ny, nx] for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))):
                o[y, x] = color + (255,)
    return o


def shear(a, s, cx):
    """Cabeceo: corre las columnas hasta s px (la trompa baja si s > 0)."""
    h, w = a.shape[:2]
    o = np.zeros_like(a)
    for x in range(w):
        dy = int(round(s * (x - cx) / (w / 2)))
        if dy == 0:
            o[:, x] = a[:, x]
        elif dy > 0:
            o[dy:, x] = a[:-dy, x]
        else:
            o[:dy, x] = a[-dy:, x]
    return o


def wheel(a, cx, cy, r, angle, tyre=RUBBER, rim=CHROME, spokes=5):
    h, w = a.shape[:2]
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            if not (0 <= x < w and 0 <= y < h):
                continue
            dx, dy = x - cx, y - cy
            d = math.hypot(dx, dy)
            if d > r + 0.15:
                continue
            rr = r * 0.62
            if d > rr:
                c = tyre[1] if (dy < 0 and dx < 0 and d > r - 1) else tyre[0]
                if d > r - 0.9 and dy < -r * 0.3:
                    c = tyre[2]
            else:
                th = math.atan2(dy, dx) - angle
                sp = (th % (2 * math.pi / spokes)) / (2 * math.pi / spokes)
                c = rim[2] if (sp < 0.42) else rim[0]
                if d < rr * 0.42:
                    c = rim[3] if (dx + dy) < 0 else rim[1]
                elif d > rr - 0.8:
                    c = rim[3] if (dx + dy) < 0 else rim[1]
            a[y, x] = tuple(c) + (255,)


def wheels(fw, fh, axes, r, gy):
    fr = []
    for f in range(4):
        a = np.zeros((fh, fw, 4), np.uint8)
        for ax in axes:
            wheel(a, ax, gy - r, r, f * (2 * math.pi / 5) / 4)
        fr.append(a)
    return fr


def shadow(fw, fh, x0, x1, gy, drop=3):
    """Sombra sobre el asfalto, corrida hacia atrás-derecha como en toda la 14."""
    a = np.zeros((fh, fw, 4), np.uint8)
    for y in range(gy - 1, min(fh, gy + drop)):
        ins = y - (gy - 1)
        for x in range(x0 + 2 + ins, min(fw, x1 + 3 + ins)):
            a[y, x] = (40, 34, 72, 120 if ins < 2 else 70)
    return a


def glow(fw, fh, pts, color, r=2, strength=255):
    a = np.zeros((fh, fw, 4), np.uint8)
    for px, py in pts:
        for y in range(py - r - 1, py + r + 2):
            for x in range(px - r - 1, px + r + 2):
                if not (0 <= x < fw and 0 <= y < fh):
                    continue
                d = math.hypot(x - px, y - py)
                al = int(strength * max(0.0, 1 - d / (r + 1)) ** 1.3)
                if al > a[y, x, 3]:
                    a[y, x] = tuple(color) + (al,)
    return a


def assemble(body, fw, fh, axes, r, gy, sx0, sx1, tail, door=None, pitch=1):
    bd = outline(body)
    cx = fw / 2
    rows = [
        [bd, shear(bd, pitch, cx), shear(bd, -pitch, cx), np.zeros_like(bd)],
        wheels(fw, fh, axes, r, gy),
        [shadow(fw, fh, sx0, sx1, gy),
         glow(fw, fh, tail, (200, 30, 30), 1, 200),
         glow(fw, fh, tail, (255, 60, 40), 3, 255),
         door if door is not None else np.zeros_like(bd)],
    ]
    sh = np.zeros((fh * 3, fw * 4, 4), np.uint8)
    for j, row in enumerate(rows):
        for i, fr in enumerate(row):
            sh[j * fh:(j + 1) * fh, i * fw:(i + 1) * fw] = fr
    return Image.fromarray(sh, "RGBA")


def wells(v, axes, cy, r):
    for ax in axes:
        v.d.ellipse((ax - r, cy - r, ax + r, cy + r), fill=M_WELL)


def driver(v, x, y, skin=(214, 158, 118), shirt=(70, 62, 96)):
    """Silueta del conductor detrás del vidrio."""
    hair = (60, 44, 44)
    v.px(x, y, skin); v.px(x + 1, y, skin); v.px(x, y - 1, hair); v.px(x + 1, y - 1, hair); v.px(x - 1, y - 1, hair)
    for dy in (1, 2, 3):
        for dx in (-1, 0, 1):
            v.px(x + dx, y + dy, shirt)


def bumper(v, x0, x1, y):
    v.rect(M_CHROME, x0, y, x1, y + 1)


def sedan(body, taxi=False, low=None):
    fw, fh, gy = 64, 30, 28
    v = V(fw, fh)
    v.poly(M_BODY, [(3, 15), (5, 13), (15, 13), (20, 6), (37, 6), (45, 13), (56, 14), (60, 16), (60, 23), (3, 23)])
    pal = ramp(body)
    lowp = ramp(low) if low else pal
    if low:                                       # taxi porteño: techo de otro color
        v.poly(M_ROOF, [(15, 13), (20, 6), (37, 6), (45, 13)])
    v.poly(M_GLASS, [(17, 13), (21, 8), (28, 8), (28, 13)])
    v.poly(M_GLASS, [(30, 13), (30, 8), (36, 8), (42, 13)])
    wells(v, (15, 48), 23, 6)
    bumper(v, 57, 62, 21)
    bumper(v, 2, 6, 21)
    v.hline(16, 44, 14, CHROME[3])                 # moldura de cintura
    v.vline(29, 15, 22, pal[0])                    # puertas
    v.vline(44, 15, 21, pal[0])
    v.vline(16, 15, 21, pal[0])
    v.hline(24, 26, 16, CHROME[2])                 # manijas
    v.hline(37, 39, 16, CHROME[2])
    for y in (17, 18):                             # faro y luz de giro
        v.px(60, y, (255, 244, 200)); v.px(59, y, (255, 244, 200))
    v.px(60, 19, (255, 170, 60))
    for y in (16, 17, 18):
        v.px(3, y, (214, 44, 44)); v.px(4, y, (168, 28, 36))
    driver(v, 33, 10)
    for x in range(20, 30):                        # brillo del sol en el hombro
        if x % 7 < 4:
            v.px(x, 15, (255, 252, 236))
    if taxi:
        v.rect(M_ROOF, 25, 3, 32, 5)
        v.hline(25, 32, 3, (255, 244, 200))
        v.hline(27, 30, 4, (40, 34, 40))
    return shade(v, pal, lowp, 14, 23, roof_pal=lowp), dict(
        fw=fw, fh=fh, gy=gy, axes=(15, 48), r=5, sx0=4, sx1=60, tail=[(3, 17)], head=(61, 18), exhaust=(1, 24), len=58)


def rural(body):
    fw, fh, gy = 64, 30, 28
    v = V(fw, fh)
    v.poly(M_BODY, [(3, 12), (5, 6), (38, 6), (46, 13), (56, 14), (60, 16), (60, 23), (3, 23)])
    pal = ramp(body)
    v.poly(M_GLASS, [(6, 13), (8, 8), (17, 8), (17, 13)])
    v.poly(M_GLASS, [(19, 13), (19, 8), (29, 8), (29, 13)])
    v.poly(M_GLASS, [(31, 13), (31, 8), (37, 8), (43, 13)])
    wells(v, (15, 48), 23, 6)
    bumper(v, 57, 62, 21)
    bumper(v, 2, 6, 21)
    v.hline(5, 45, 14, CHROME[3])
    v.vline(30, 15, 22, pal[0])
    v.vline(45, 15, 21, pal[0])
    v.hline(25, 27, 16, CHROME[2])
    v.hline(38, 40, 16, CHROME[2])
    v.hline(9, 34, 5, CHROME[1])                   # barras de techo
    for x in (11, 32):
        v.px(x, 5, RUBBER[1])
    for y in (17, 18):
        v.px(60, y, (255, 244, 200)); v.px(59, y, (255, 244, 200))
    for y in (15, 16, 17):
        v.px(3, y, (214, 44, 44))
    driver(v, 34, 10)
    return shade(v, pal, pal, 14, 23), dict(
        fw=fw, fh=fh, gy=gy, axes=(15, 48), r=5, sx0=4, sx1=60, tail=[(3, 16)], head=(61, 18), exhaust=(1, 24), len=58)


def chata(body, load):
    fw, fh, gy = 68, 32, 30
    v = V(fw, fh)
    v.poly(M_BODY, [(2, 15), (32, 15), (34, 6), (46, 6), (51, 15), (61, 16), (64, 18), (64, 25), (2, 25)])
    pal = ramp(body)
    v.poly(M_GLASS, [(36, 15), (37, 8), (45, 8), (49, 15)])
    wells(v, (15, 51), 25, 6)
    bumper(v, 61, 66, 23)
    bumper(v, 1, 5, 23)
    v.hline(3, 31, 16, pal[4])
    v.vline(32, 16, 24, pal[0])
    v.vline(49, 16, 23, pal[0])
    v.hline(42, 44, 18, CHROME[2])
    for y in (19, 20):
        v.px(64, y, (255, 244, 200)); v.px(63, y, (255, 244, 200))
    for y in (18, 19, 20):
        v.px(2, y, (214, 44, 44))
    driver(v, 42, 10)
    a = shade(v, pal, pal, 16, 25)
    if load == "fardos":                          # carga arriba de la caja
        for (x0, y0, x1, y1) in ((5, 9, 16, 15), (17, 9, 29, 15), (9, 3, 22, 9)):
            for y in range(y0, y1):
                for x in range(x0, x1):
                    c = (236, 198, 110) if y == y0 else ((205, 160, 76) if (x + y * 3) % 5 else (150, 104, 52))
                    a[y, x] = c + (255,)
            for x in (x0 + 3, x1 - 4):
                a[y0:y1, x] = (120, 72, 44, 255)
    else:                                          # cajones de fruta
        for (x0, y0, x1, y1, f) in ((4, 8, 15, 15, (226, 92, 62)), (16, 8, 30, 15, (244, 168, 56))):
            for y in range(y0, y1):
                for x in range(x0, x1):
                    c = (176, 122, 72) if (y - y0) % 3 else (118, 76, 52)
                    if y == y0:
                        c = f if (x % 2) else tuple(int(k * 0.8) for k in f)
                    a[y, x] = c + (255,)
    return a, dict(fw=fw, fh=fh, gy=gy, axes=(15, 51), r=5, sx0=3, sx1=64, tail=[(2, 19)], head=(65, 20), exhaust=(0, 26), len=62)


def furgon(body):
    fw, fh, gy = 68, 36, 34
    v = V(fw, fh)
    v.poly(M_BODY, [(3, 5), (46, 5), (56, 15), (62, 18), (64, 21), (64, 29), (3, 29)])
    pal = ramp(body)
    v.poly(M_GLASS, [(44, 16), (44, 8), (47, 8), (54, 16)])
    v.poly(M_GLASS, [(30, 16), (30, 8), (41, 8), (41, 16)])
    wells(v, (15, 52), 29, 6)
    bumper(v, 61, 66, 27)
    bumper(v, 1, 5, 27)
    v.vline(43, 17, 28, pal[0])
    v.vline(28, 6, 28, pal[0])
    v.hline(36, 38, 19, CHROME[2])
    v.hline(4, 62, 22, ramp("#C8402E")[3])
    v.hline(4, 62, 23, ramp("#C8402E")[2])
    for y in (21, 22):
        v.px(64, y, (255, 244, 200)); v.px(63, y, (255, 244, 200))
    for y in (17, 18, 19, 20):
        v.px(3, y, (214, 44, 44))
    driver(v, 49, 11)
    return shade(v, pal, pal, 8, 29, reflect=0.55), dict(
        fw=fw, fh=fh, gy=gy, axes=(15, 52), r=5, sx0=4, sx1=64, tail=[(3, 18)], head=(65, 22), exhaust=(1, 30), len=62)


def camion(cab, carga):
    fw, fh, gy = 112, 48, 46
    v = V(fw, fh)
    pal, cpal = ramp(cab), ramp(carga)
    v.poly(M_LOW, [(3, 6), (72, 6), (74, 8), (74, 36), (3, 36)])     # caja con lona
    v.poly(M_BODY, [(76, 12), (92, 12), (96, 22), (107, 25), (109, 28), (109, 40), (76, 40)])
    v.poly(M_GLASS, [(84, 23), (84, 15), (91, 15), (95, 23)])
    v.rect(M_RUB, 3, 37, 104, 39)
    wells(v, (22, 36, 92), 40, 7)
    bumper(v, 104, 110, 38)
    v.vline(82, 13, 39, pal[0])
    v.hline(77, 80, 27, CHROME[2])
    for x in (108, 109):
        for y in (31, 32):
            v.px(x, y, (255, 244, 200))
    v.px(109, 33, (255, 170, 60))
    for y in (30, 31, 32, 33):
        v.px(3, y, (214, 44, 44))
    v.vline(78, 6, 12, CHROME[1])                  # caño de escape vertical
    v.vline(79, 6, 12, CHROME[3])
    driver(v, 88, 18)
    a = shade(v, pal, cpal, 22, 40, reflect=0.5)
    for x in range(9, 72, 9):                      # sogas de la lona
        a[7:36, x] = cpal[0] + (255,)
    a[35, 3:75] = cpal[0] + (255,)
    a[6, 3:73] = cpal[4] + (255,)
    return a, dict(fw=fw, fh=fh, gy=gy, axes=(22, 36, 92), r=6, sx0=4, sx1=110, tail=[(3, 32)], head=(110, 32), exhaust=(78, 5), len=107)


def moto(body):
    fw, fh, gy = 48, 34, 32
    im = Image.new("RGBA", (fw, fh), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    pal = ramp(body)
    d.polygon([(14, 24), (20, 19), (31, 19), (33, 23), (28, 27), (18, 27)], fill=pal[2] + (255,))   # cuadro y tanque
    d.line([(16, 20), (30, 20)], fill=pal[4] + (255,))
    d.line([(29, 19), (35, 27)], fill=CHROME[1] + (255,))            # horquilla
    d.line([(30, 17), (33, 13)], fill=CHROME[2] + (255,))
    d.rectangle((33, 12, 35, 13), fill=RUBBER[1] + (255,))
    d.rectangle((35, 18, 36, 19), fill=(255, 244, 200, 255))         # faro
    d.line([(10, 28), (24, 28)], fill=CHROME[2] + (255,))            # escape
    d.rectangle((18, 10, 24, 19), fill=(68, 92, 148, 255))           # conductor
    d.line([(18, 10), (18, 19)], fill=(110, 138, 192, 255))
    d.line([(23, 13), (33, 13)], fill=(58, 80, 134, 255))
    d.line([(21, 19), (26, 23)], fill=(52, 46, 74, 255))
    d.line([(26, 23), (25, 27)], fill=(52, 46, 74, 255))
    d.rectangle((19, 4, 24, 9), fill=(236, 74, 62, 255))             # casco
    d.line([(19, 4), (23, 4)], fill=(255, 150, 120, 255))
    d.rectangle((23, 6, 24, 7), fill=SKYGLASS + (255,))
    d.rectangle((6, 12, 16, 22), fill=(246, 178, 54, 255))           # caja de reparto
    d.line([(6, 12), (16, 12)], fill=(255, 226, 150, 255))
    d.line([(6, 22), (16, 22)], fill=(170, 100, 40, 255))
    d.line([(6, 12), (6, 22)], fill=(255, 216, 130, 255))
    return np.array(im), dict(fw=fw, fh=fh, gy=gy, axes=(11, 34), r=5, sx0=5, sx1=40, tail=[(13, 23)], head=(37, 18), exhaust=(6, 28), len=36)


# ---------------------------------------------------------------------- colectivos

LINES = [
    dict(id="bus60", top="#C8302E", low="#F2BE34", band="#C8302E", deco="curva", num="60"),
    dict(id="bus160", top="#C8302E", low="#D13A36", band="#F4EEE2", deco="rayas", num="160"),
    dict(id="bus103", top="#22508C", low="#D2402E", band="#F3DDA8", deco=None, num="103"),
    dict(id="bus59", top="#C8302E", low="#3F8E3A", band="#F2BE34", deco="filete", num="59"),
]
DIGITS = {
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
    "3": ["111", "001", "011", "001", "111"], "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"], "9": ["111", "101", "111", "001", "111"],
}
PASSENGERS = [(214, 158, 118), (150, 104, 80), (232, 186, 150), (120, 84, 70)]


def bus(line):
    fw, fh, gy = 136, 54, 52
    x0, x1 = 3, 131
    roof_y, belt, sill = 6, 30, 45
    v = V(fw, fh)
    pal, low = ramp(line["low"]), ramp(line["top"])
    white = ramp("#F4F0E6")
    v.poly(M_LOW, [(x0 + 2, roof_y), (x1 - 8, roof_y), (x1 - 2, roof_y + 3), (x1, roof_y + 14), (x1 + 1, belt), (x0, belt), (x0, roof_y + 3)])
    v.poly(M_BODY, [(x0, belt), (x1 + 1, belt), (x1 + 1, sill), (x0, sill)])
    v.poly(M_ROOF, [(x0 + 2, roof_y), (x1 - 8, roof_y), (x1 - 4, roof_y + 2), (x1 - 3, roof_y + 3), (x0, roof_y + 3)])
    v.rect(M_ROOF, 12, 2, 50, 5)                    # equipo de aire
    v.rect(M_ROOF, 68, 3, 88, 5)
    for gx0, gx1 in ((6, 52), (66, 100)):           # vidrios
        v.rect(M_RUB, gx0 - 1, 11, gx1 + 1, 28)
        v.rect(M_GLASS, gx0, 12, gx1, 27)
    doors = (53, 102)
    for d0 in doors:
        v.rect(M_RUB, d0, 11, d0 + 12, 44)
        v.rect(M_GLASS, d0 + 1, 12, d0 + 5, 43)
        v.rect(M_GLASS, d0 + 7, 12, d0 + 11, 43)
    v.poly(M_RUB, [(116, 10), (x1 - 3, 10), (x1, 16), (x1, 33), (116, 33)])          # parabrisas
    v.poly(M_GLASS, [(117, 11), (x1 - 4, 11), (x1 - 1, 16), (x1 - 1, 32), (117, 32)])
    wells(v, (29, 94), 45, 8)
    v.rect(M_RUB, x0, 45, x1 + 1, 46)
    v.rect(M_CHROME, x1 - 8, 43, x1 + 3, 45)
    v.rect(M_CHROME, x0 - 1, 43, x0 + 4, 45)
    bc = ramp(line["band"])                         # franja
    for x in range(x0, x1 + 1):
        if doors[0] <= x <= doors[0] + 12 or doors[1] <= x <= doors[1] + 12:
            continue
        for y in range(33, 37):
            v.px(x, y, bc[4] if y == 33 else (bc[3] if y < 36 else bc[2]))
    rng = np.random.default_rng(int(line["num"]))   # pasajeros
    for gx0, gx1 in ((6, 52), (66, 100)):
        for x in range(gx0 + 4, gx1 - 3, 9):
            if rng.random() < 0.72:
                c = PASSENGERS[int(rng.integers(0, 4))]
                top = 19 + int(rng.integers(0, 2))
                for dy in range(0, 4):
                    v.px(x, top + dy, c); v.px(x + 1, top + dy, c); v.px(x + 2, top + dy, c)
                for dx in (0, 1, 2):
                    v.px(x + dx, top - 1, (52, 42, 44))
                sh = tuple(int(k) for k in rng.integers(50, 130, 3))
                for dy in range(4, 8):
                    for dx in range(-1, 4):
                        v.px(x + dx, top + dy, sh)
    for gx0, gx1 in ((6, 52), (66, 100)):           # parantes
        for x in range(gx0 + 11, gx1, 12):
            v.vline(x, 12, 27, RUBBER[1])
            v.vline(x + 1, 12, 27, RUBBER[0])
        v.hline(gx0, gx1, 17, RUBBER[1])
    if line["deco"] == "curva":
        for i in range(36):
            x, y = 14 + i, 44 - int(9 * (i / 36) ** 1.6)
            for dy in (0, 1, 2):
                v.px(x, y - dy, low[3])
    elif line["deco"] == "rayas":
        w = ramp("#F4EEE2")
        for x in range(6, 124, 8):
            if not (doors[0] - 6 < x < doors[0] + 13 or doors[1] - 6 < x < doors[1] + 13 or abs(x - 29) < 14 or abs(x - 94) < 14):
                for k in range(6):
                    v.px(x + k, 44 - k, w[3])
    elif line["deco"] == "filete":                  # fileteado: voluta con hojas
        y_c = ramp("#F2BE34")
        for sx in (68, ):
            for i in range(22):
                a = i / 22 * math.pi * 2.2
                x, y = sx + i, 41 + int(2.6 * math.sin(a))
                v.px(x, y, y_c[4] if i % 3 else y_c[2])
                if i % 7 == 3:
                    v.px(x, y - 2, (244, 240, 230)); v.px(x + 1, y - 1, (244, 240, 230)); v.px(x - 1, y + 1, (244, 240, 230))
    for x in range(68, 99):                         # cartel LED
        for y in range(12, 17):
            v.px(x, y, (20, 16, 22))
    for dy in range(1, 4):
        for dx in range(0, 3):
            v.px(70 + dx, 12 + dy, (52, 110, 224))
    cx = 76
    for ch in line["num"]:
        for dy, row in enumerate(DIGITS[ch]):
            for dx, on in enumerate(row):
                if on == "1":
                    v.px(cx + dx, 12 + dy, (255, 176, 48))
        cx += 4
    for k in range(cx + 1, 97, 2):
        v.px(k, 13, (200, 120, 30)); v.px(k, 15, (200, 120, 30))
    for y in range(11, 19):                         # espejo, luces, chofer
        v.px(x1 + 3, y, RUBBER[1])
    v.hline(x1 - 1, x1 + 3, 10, RUBBER[1])
    for x in range(x1 - 3, x1 + 2):
        for y in range(38, 41):
            v.px(x, y, (255, 244, 200))
    v.hline(x1 - 2, x1 + 1, 41, (255, 170, 60))
    for y in range(30, 37):
        v.px(x0, y, (224, 48, 44)); v.px(x0 + 1, y, (176, 30, 36))
    driver(v, 124, 22, shirt=(92, 120, 170))
    a = shade(v, pal, low, belt, sill, roof_pal=white, reflect=0.62)
    a[6, 6:124] = (255, 252, 244, 255)              # techo blanco: reflejo limpio
    a[8, 3:128] = white[1] + (255,)
    door = np.zeros((fh, fw, 4), np.uint8)          # puertas abiertas: hueco y escalón con luz
    for d0 in doors:
        door[11:45, d0:d0 + 13] = (28, 24, 34, 255)
        door[12:44, d0 + 1:d0 + 2] = (150, 196, 224, 255)
        door[12:44, d0 + 11:d0 + 12] = (150, 196, 224, 255)
        door[16:30, d0 + 4:d0 + 9] = (64, 54, 56, 255)
        door[40:42, d0 + 2:d0 + 11] = (255, 214, 130, 255)
        door[43:45, d0 + 2:d0 + 11] = (120, 104, 96, 255)
    return a, dict(fw=fw, fh=fh, gy=gy, axes=(29, 94), r=7, sx0=4, sx1=131, tail=[(3, 33)], head=(133, 39), exhaust=(1, 46), len=129, door=door, bus=True)


# ---------------------------------------------------------------------- humo y tierra

def puff_sheet(col_l, col_d, name, n=6):
    fw = 12
    a = np.zeros((fw, fw * n, 4), np.uint8)
    rng = np.random.default_rng(7)
    for f in range(n):
        r = 1.2 + f * 0.85
        al = 225 * (1 - f / n) ** 0.8
        blobs = [(6 + rng.uniform(-1, 1), 6 + rng.uniform(-1, 1), r * rng.uniform(.7, 1)) for _ in range(3)]
        for y in range(fw):
            for x in range(fw):
                v = max(1 - math.hypot(x - bx, y - by) / br for bx, by, br in blobs)
                if v <= 0 or v * 1.5 * (1 - f / (n + 1)) + 0.15 < BAY[y % 4][x % 4] / 16:
                    continue
                c = col_l if (x - 6) + (y - 6) < 0 else col_d
                a[y, x + f * fw] = tuple(c) + (int(al),)
    Image.fromarray(a, "RGBA").save(os.path.join(OUT, name))


def beam():
    w, h = 38, 15
    a = np.zeros((h, w, 4), np.uint8)
    for x in range(w):
        half = 1 + x * 0.17
        al = 150 * (1 - x / w) ** 1.5
        for y in range(h):
            d = abs(y - 7) / half
            if d <= 1 and (1 - d) * 1.6 + 0.2 > BAY[y % 4][x % 4] / 16:
                a[y, x] = (255, 236, 176, int(al))
    Image.fromarray(a, "RGBA").save(os.path.join(OUT, "veh_beam.png"))


# ----------------------------------------------------------------------

def main():
    os.makedirs(OUT, exist_ok=True)
    table = {}

    def emit(name, res):
        body, meta = res
        door = meta.pop("door", None)
        im = assemble(body, meta["fw"], meta["fh"], meta["axes"], meta["r"], meta["gy"], meta["sx0"], meta["sx1"], meta["tail"], door)
        im.save(os.path.join(OUT, "veh_%s.png" % name))
        table[name] = {k: (list(x) if isinstance(x, tuple) else x) for k, x in meta.items()}

    emit("sedan_rojo", sedan("#C53A3A"))
    emit("sedan_celeste", sedan("#5EA6D8"))
    emit("sedan_crema", sedan("#E4CF9E"))
    emit("taxi", sedan("#2C2A34", taxi=True, low="#F2BE34"))
    emit("rural_verde", rural("#4C8F68"))
    emit("rural_gris", rural("#9AA2B0"))
    emit("chata_azul", chata("#2F68A8", "fardos"))
    emit("chata_roja", chata("#B5453A", "cajones"))
    emit("furgon", furgon("#E8E2D2"))
    emit("camion", camion("#D8652E", "#3E7A5A"))
    emit("moto", moto("#C8302E"))
    for line in LINES:
        emit(line["id"], bus(line))
    puff_sheet((226, 220, 226), (150, 142, 162), "veh_puff.png")
    puff_sheet((226, 186, 134), (170, 124, 88), "veh_dust.png")
    beam()
    with open(os.path.join(ROOT, "data", "vehicles.json"), "w", encoding="utf-8", newline="") as f:
        json.dump(table, f, indent=1)
    print("vehículos:", len(table))


if __name__ == "__main__":
    main()
