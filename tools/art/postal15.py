"""15.0: la postal de la pantalla de inicio. Noroeste argentino a la hora dorada:
Andes nevados, cerros de siete colores, viaducto del tren, pueblo de adobe, ruta.

Se pinta por capas con alfa (assets/escenarios/start/) para que start_postcard.gd
las mueva en parallax e intercale tren, vehículos y animales. Misma luz que toda
la 14: sol bajo a la izquierda, sombras violetas frías, pixel art en cúmulos limpios
(valores cuantizados; tramado sólo en el degradé del cielo).

  python tools/art/postal15.py          -> capas, sprites y data/postal.json
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "assets", "escenarios", "start")

W, H = 480, 900
YY, XX = np.mgrid[0:H, 0:W].astype(np.float64)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
BY = BAYER[YY.astype(int) % 4, XX.astype(int) % 4]

SUN = (118.0, 402.0)
ROAD_TOP, ROAD_BOT = 644, 678
LANE_FAR, LANE_NEAR = 660, 674


def hx(c):
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64)


def mix(a, b, t):
    t = np.asarray(t, dtype=np.float64)
    if t.ndim == 2:
        t = t[..., None]
    return a * (1 - t) + b * t


_T = {}


def vnoise(u, v, seed):
    if seed not in _T:
        _T[seed] = np.random.default_rng(seed).random((256, 256))
    t = _T[seed]
    iu, iv = np.floor(u).astype(int), np.floor(v).astype(int)
    fu, fv = u - iu, v - iv
    fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
    a = t[iv % 256, iu % 256] * (1 - fu) + t[iv % 256, (iu + 1) % 256] * fu
    b = t[(iv + 1) % 256, iu % 256] * (1 - fu) + t[(iv + 1) % 256, (iu + 1) % 256] * fu
    return a * (1 - fv) + b * fv


def fbm(u, v, seed, oct=4):
    r, a, tot = 0.0, 1.0, 0.0
    for o in range(oct):
        r = r + a * vnoise(u * 2 ** o, v * 2 ** o, seed + o * 13)
        tot += a
        a *= 0.5
    return r / tot


def ridged(u, v, seed, oct=3):
    return 1 - np.abs(2 * fbm(u, v, seed, oct) - 1)


def line1(x, seed, scale, oct=4):
    return fbm(x / scale, np.full_like(x, 0.5), seed, oct)


def blur1(a, n):
    k = np.ones(n) / n
    return np.convolve(np.pad(a, n, mode="edge"), k, mode="same")[n:-n]


def box(a, r):
    if r <= 0:
        return a
    p = np.pad(a, r, mode="edge")
    c = np.cumsum(np.cumsum(p, 0), 1)
    n = 2 * r
    s = c[n:, n:].copy()
    s[1:, :] -= c[:-n - 1, n:][:s.shape[0] - 1, :]
    s[:, 1:] -= c[n:, :-n - 1][:, :s.shape[1] - 1]
    s[1:, 1:] += c[:-n - 1, :-n - 1][:s.shape[0] - 1, :s.shape[1] - 1]
    return (s / (n + 1) ** 2)[:a.shape[0], :a.shape[1]]


def tones(val, n):
    v = box(np.clip(val, 0, 1), 1)
    return np.round(v * (n - 1)) / (n - 1)


class Layer:
    def __init__(self):
        self.rgb = np.zeros((H, W, 3))
        self.a = np.zeros((H, W), dtype=bool)

    def put(self, m, c):
        c = np.asarray(c, dtype=np.float64)
        if c.ndim == 1:
            self.rgb[m] = c
        else:
            self.rgb[m] = c[m]
        self.a |= m

    def px(self, x, y, c):
        if 0 <= x < W and 0 <= y < H:
            self.rgb[y, x] = c
            self.a[y, x] = True

    def rect(self, x0, y0, x1, y1, c):
        x0, x1 = max(0, int(x0)), min(W - 1, int(x1))
        y0, y1 = max(0, int(y0)), min(H - 1, int(y1))
        if x1 >= x0 and y1 >= y0:
            self.rgb[y0:y1 + 1, x0:x1 + 1] = c
            self.a[y0:y1 + 1, x0:x1 + 1] = True


def sun_grade(rgb, strength=1.0):
    """Luz de la hora dorada alrededor del sol: suma ámbar cerca y enfría lo lejano."""
    d = np.hypot((XX - SUN[0]) / 1.5, YY - SUN[1])
    g = np.clip(1 - d / 330, 0, 1) ** 2
    return mix(rgb, hx("#FFC070"), g * 0.42 * strength)


# ------------------------------------------------------------------ cielo

def sky():
    l = Layer()
    stops = [(0, "#232A63"), (130, "#3F3E8C"), (230, "#7A519E"), (300, "#C2607F"), (362, "#EE8A5C"), (420, "#FBBA62"), (480, "#FFE3A0"), (640, "#FFE3A0")]
    c = np.zeros((H, W, 3))
    ys = [s[0] for s in stops]
    for ch in range(3):
        c[..., ch] = np.interp(YY, ys, [hx(s[1])[ch] for s in stops])
    d = np.hypot((XX - SUN[0]) / 1.35, YY - SUN[1])
    c = mix(c, hx("#FFD98C"), np.clip(1 - d / 240, 0, 1) ** 2.2 * 0.75)
    # cirros encendidos: vetas largas teñidas de rosa y oro
    n = fbm(XX / 90 + YY / 40, YY / 11, 3, 4)
    n2 = fbm(XX / 40, YY / 7, 9, 3)
    cir = np.clip((n * 0.7 + n2 * 0.3 - 0.54) / 0.14, 0, 1) * np.clip((YY - 120) / 90, 0, 1) * np.clip((395 - YY) / 80, 0, 1)
    tint = mix(hx("#FFB98C"), hx("#FFE9BE"), np.clip((YY - 220) / 170, 0, 1))
    c = mix(c, tint, np.round(cir * 3) / 3 * 0.72)
    step = 7.0
    c = np.floor(c / step + BY[..., None] * 0.98) * step
    disc = d < 16
    c[d < 21] = hx("#FFEAB0")
    c[disc] = hx("#FFFBE2")
    l.put(YY < 760, c)
    rng = random.Random(4)
    for _ in range(70):                            # estrellas fijas, sólo en lo alto
        x, y = rng.randrange(W), rng.randrange(0, 190)
        k = rng.choice((0.3, 0.45, 0.7)) * (1 - y / 230)
        l.rgb[y, x] = mix(l.rgb[y, x], hx("#FFF6D8"), k)
    return l


# ------------------------------------------------------------------ cordillera

def andes():
    l = Layer()
    x = XX[0]
    top = 432 - 96 * line1(x, 21, 150, 3) ** 1.2 - 44 * np.abs(2 * line1(x + 40, 22, 62, 3) - 1) - 7 * line1(x, 23, 11, 2)
    top += np.clip(np.abs(x - SUN[0]) / 95 - 1.2, -1.2, 0) * -34       # abra por donde baja el sol
    m = (YY >= top[None, :]) & (YY < 560)
    dep = YY - top[None, :]
    u = XX + dep * 0.55
    v = dep
    g = ridged(u / 15, v / 30, 31, 4)
    dg = np.gradient(g, axis=1)
    face = blur1(np.gradient(top), 9)
    lit = 0.46 + np.clip(-face[None, :] * 1.7, -0.3, 0.34) + np.clip(dg * 8.5, -0.3, 0.34)
    val = tones(lit, 6)
    base = mix(hx("#4E4A92"), hx("#E08C86"), val)
    # nieve con alpenglow arriba de la línea
    line = 372 + 16 * fbm(XX / 38, YY / 38, 33, 3) + g * 15
    snow = YY < line
    snow_c = mix(hx("#8E7FC4"), hx("#FFE8D0"), np.round(np.clip(val * 1.25, 0, 1) * 3) / 3)
    base = np.where(snow[..., None], snow_c, base)
    base = mix(base, hx("#F7B37C"), np.clip((YY - 405) / 130, 0, 1) * 0.74)    # bruma del valle
    l.put(m, sun_grade(base, 0.9))
    rim = m & (dep < 1.2)
    l.rgb[rim] = mix(l.rgb[rim], hx("#FFF0C8"), 0.65)
    return l


# ------------------------------------------------------------------ cerros de colores

BANDS = ["#B4462F", "#D96A4A", "#EBAA4F", "#F2D7A2", "#92A873", "#8A5067", "#CC7140", "#C75C74", "#E4895A", "#A8483C"]
SERP = [(274, 566), (300, 552), (318, 546), (336, 541), (346, 536), (334, 529), (312, 524), (300, 519), (312, 513), (334, 509), (348, 505), (340, 499), (322, 495), (316, 490), (326, 485), (338, 481)]


def strata(top, seed, haze, ground=640, tilt=0.42, scale=1.0):
    dep = YY - top[None, :]
    u = XX + dep * (0.5 + 0.6 * vnoise(XX / 60, YY / 60, seed + 1))
    g = ridged(u / (9 * scale), dep / (40 * scale), seed, 4)
    g2 = fbm(XX / 30, YY / 30, seed + 2, 3)
    dg = np.gradient(g, axis=1)
    rng = random.Random(seed)
    # bandas de grosor variable, plegadas e inclinadas
    fold = 9 * np.sin(XX / 57 + seed) + 6 * np.sin(XX / 23 + seed * 2)
    s = (YY + XX * 0.10 * tilt * 2 - top[None, :] * tilt + fold + g * 6 * scale + g2 * 10) / scale
    thick, pos, seq = [], 0.0, []
    while pos < 900:
        t = rng.choice((5, 7, 9, 12, 16, 22))
        pos += t
        thick.append(pos)
        seq.append(rng.randrange(len(BANDS)))
    idx = np.searchsorted(np.array(thick), np.clip(s + 200, 0, 899))
    pal = np.stack([hx(c) for c in BANDS])
    col = pal[np.array(seq)[idx]]
    face = blur1(np.gradient(top), 25)
    lit = 0.5 + np.clip(-face[None, :] * 1.5, -0.27, 0.27) + np.clip(dg * 6.2, -0.3, 0.3)
    lit = lit - np.clip(dep / 300, 0, 0.2)
    val = tones(lit, 6)
    c = col * (0.46 + 0.86 * val[..., None])
    c = mix(c, hx("#4A3C78"), np.clip(0.62 - val, 0, 0.62) * 0.62)
    c = mix(c, hx("#FFD08A"), np.clip(val - 0.68, 0, 1) * 0.5)
    c = mix(c, hx("#F7B37C"), haze)
    return c, dep


def hills():
    l = Layer()
    x = XX[0]
    # cerro del fondo
    t1 = 486 - 52 * line1(x, 41, 130, 3) - 14 * line1(x, 42, 30, 3)
    c, dep = strata(t1, 51, 0.40, scale=0.75)
    m = (YY >= t1[None, :]) & (YY < 780)
    l.put(m, c)
    l.rgb[m & (dep < 1.2)] = hx("#FFD9A0")
    # el cerro grande, héroe de la postal: a la derecha del sol
    t2 = 592 - 148 * np.exp(-((x - 330) / 118) ** 2) - 54 * np.exp(-((x - 462) / 56) ** 2) - 20 * line1(x, 43, 42, 3) - 4 * line1(x, 44, 9, 2)
    c, dep = strata(t2, 57, 0.06)
    m = (YY >= t2[None, :]) & (YY < 780)
    l.put(m, sun_grade(c, 0.55))
    l.rgb[m & (dep < 1.3)] = mix(l.rgb[m & (dep < 1.3)], hx("#FFEBC0"), 0.75)
    # lomada izquierda
    t3 = 600 - 76 * np.exp(-((x - 24) / 96) ** 2) - 16 * line1(x, 45, 34, 3) - 3 * line1(x, 46, 8, 2)
    c, dep = strata(t3, 63, 0.02, scale=1.15)
    m = (YY >= t3[None, :]) & (YY < 780)
    l.put(m, sun_grade(c, 0.8))
    l.rgb[m & (dep < 1.3)] = mix(l.rgb[m & (dep < 1.3)], hx("#FFEBC0"), 0.7)
    # camino de cornisa en zigzag sobre el cerro grande (lo recorre un puntito con luces)
    img = Image.new("L", (W, H), 0)
    ImageDraw.Draw(img).line(SERP, fill=255, width=1)
    r = np.array(img) > 0
    l.rgb[r] = mix(l.rgb[r], hx("#F6DCAE"), 0.62)
    return l


# ------------------------------------------------------------------ viaducto

def deck(x):
    return 500.0 + ((x - 240.0) / 240.0) ** 2 * 22.0


def viaduct():
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dark = (52, 44, 82, 255)
    mid = (88, 72, 112, 255)
    lit = (246, 182, 104, 255)
    towers = [58, 132, 206, 280, 354, 428]
    for tx in towers:
        ty = deck(tx) + 11
        gy = 612 + 8 * math.sin(tx / 37)
        hh = gy - ty
        for k in range(0, 2):                      # dos pilas por caballete (profundidad)
            ox = k * 7
            col = mid if k == 0 else dark
            spread = hh * 0.13
            d.line([(tx - 2 + ox, ty), (tx - 2 + ox - spread, gy)], fill=lit if k == 0 else col)
            d.line([(tx + 3 + ox, ty), (tx + 3 + ox + spread, gy)], fill=col)
            d.line([(tx + 4 + ox, ty), (tx + 4 + ox + spread, gy)], fill=dark)
            n = 5
            for i in range(n):
                t0, t1 = i / n, (i + 1) / n
                y0, y1 = ty + hh * t0, ty + hh * t1
                x0l, x0r = tx - 2 + ox - spread * t0, tx + 3 + ox + spread * t0
                x1l, x1r = tx - 2 + ox - spread * t1, tx + 3 + ox + spread * t1
                d.line([(x0l, y0), (x1r, y1)], fill=col)
                d.line([(x0r, y0), (x1l, y1)], fill=dark)
                d.line([(x1l, y1), (x1r, y1)], fill=col)
    # viga reticulada del tablero
    for x in range(-4, W + 4):
        y = deck(x)
        for dy, c in ((0, lit), (1, mid), (10, dark), (11, dark)):
            if 0 <= x < W:
                d.point((x, y + dy), fill=c)
    for x in range(-8, W + 8, 12):
        d.line([(x, deck(x) + 1), (x + 6, deck(x + 6) + 10)], fill=mid)
        d.line([(x + 6, deck(x + 6) + 10), (x + 12, deck(x + 12) + 1)], fill=dark)
        d.line([(x, deck(x) + 2), (x, deck(x) + 10)], fill=dark)
    for x in range(0, W, 8):                       # baranda
        d.line([(x, deck(x) - 3), (x, deck(x))], fill=mid)
    for x in range(0, W):
        d.point((x, deck(x) - 3), fill=(120, 96, 128, 255))
    return im


# ------------------------------------------------------------------ valle y pueblo

def adobe_noise(seed):
    return fbm(XX / 2.3, YY / 2.3, seed, 2)


def house(l, x, base, w, h, seed, wall="#D99B62", roof="flat", win=True, windows=None):
    side = max(3, int(w * 0.22))
    wall_c = hx(wall)
    n = adobe_noise(seed)
    rng = random.Random(seed)
    x0, x1 = x, x + w
    ty = base - h
    m = (XX >= x0) & (XX <= x1) & (YY >= ty) & (YY <= base)
    c = wall_c * (0.98 + np.round((n - 0.5) * 8) / 8 * 0.20)[..., None]
    c = mix(c, hx("#FFD49A"), np.clip((x1 - XX) / w, 0, 1) * 0.28)
    l.put(m, c)
    sm = (XX > x1) & (XX <= x1 + side) & (YY >= ty + 2) & (YY <= base)
    sc = mix(wall_c, hx("#4A3C78"), 0.55)
    l.put(sm, sc * (0.96 + np.round((n - 0.5) * 6) / 6 * 0.14)[..., None])
    if roof == "flat":                             # techo de torta de barro, con caña y parapeto
        l.rect(x0 - 1, ty - 2, x1 + side, ty, mix(hx("#A87850"), hx("#FFE2B0"), 0.25))
        l.rect(x0 - 1, ty - 2, x1 + side, ty - 2, hx("#FFE6BC"))
        l.rect(x0 - 1, ty + 1, x1 + side, ty + 1, mix(wall_c, hx("#4A3C78"), 0.45))
        for vx in range(x0 + 2, x1, 4):            # vigas que asoman
            l.px(vx, ty + 2, hx("#5A3A34"))
    else:                                          # dos aguas con paja
        for i in range(0, h // 2 + 3):
            l.rect(x0 - 1 + i, ty - i, x1 + 1 - i, ty - i, mix(hx("#C89A5A"), hx("#FFE2A8"), 1 - i / (h / 2 + 3)))
    dx = x0 + rng.randint(3, max(3, w - 8))
    l.rect(dx, base - 8, dx + 4, base, hx("#5C3A30"))
    l.rect(dx, base - 8, dx + 1, base, hx("#7E5038"))
    if win:
        for wx in range(x0 + 3, x1 - 3, 9):
            if abs(wx - dx) > 6 and rng.random() < 0.8:
                l.rect(wx, ty + 5, wx + 3, ty + 8, hx("#3A3050"))
                l.px(wx, ty + 5, hx("#6C6490"))
                if windows is not None:
                    windows.append((wx, ty + 5, rng.randrange(3)))
    # sombra arrojada hacia atrás-derecha
    sh = (XX > x1 + side) & (XX < x1 + side + h * 0.55) & (YY > base - 1 - (x1 + side + h * 0.55 - XX) * 0.18) & (YY <= base + 1)
    return sh


def church(l, x, base, windows):
    white, sh = hx("#FBF0DA"), hx("#A48EB0")
    # nave
    l.rect(x + 12, base - 25, x + 52, base, white)
    l.rect(x + 53, base - 23, x + 62, base, sh)
    l.rect(x + 12, base - 25, x + 14, base, hx("#FFFDF0"))
    for i in range(0, 8):                          # techo a dos aguas de la nave
        l.rect(x + 11 + i, base - 26 - i, x + 53 - i, base - 26 - i, mix(hx("#C2703F"), hx("#FFC88A"), 1 - i / 8))
    l.rect(x + 22, base - 13, x + 42, base - 11, hx("#E8D6BE"))
    # portal y arco
    l.rect(x + 27, base - 12, x + 36, base, hx("#5C3A30"))
    l.rect(x + 28, base - 12, x + 29, base, hx("#8A5A3E"))
    # ventanas de la nave
    for wx in (x + 18, x + 43):
        l.rect(wx, base - 19, wx + 2, base - 15, hx("#3A3050"))
        windows.append((wx, base - 19, 1))
    # torre campanario
    tx = x
    l.rect(tx, base - 52, tx + 13, base, white)
    l.rect(tx + 14, base - 50, tx + 17, base, sh)
    l.rect(tx, base - 52, tx + 2, base, hx("#FFFDF0"))
    l.rect(tx - 1, base - 54, tx + 14, base - 53, hx("#E9D8C2"))
    l.rect(tx + 4, base - 47, tx + 9, base - 39, hx("#3A2E50"))      # ojo del campanario
    l.rect(tx + 5, base - 48, tx + 8, base - 48, hx("#3A2E50"))
    l.rect(tx + 6, base - 45, tx + 7, base - 42, hx("#D8A848"))      # campana
    for i in range(0, 8):                          # remate
        l.rect(tx + 1 + i // 2, base - 55 - i, tx + 12 - i // 2, base - 55 - i, mix(hx("#FBF0DA"), hx("#B8A0C0"), i / 16))
    l.rect(tx + 6, base - 68, tx + 7, base - 62, hx("#3A3050"))      # cruz
    l.rect(tx + 4, base - 66, tx + 9, base - 65, hx("#3A3050"))
    return tx + 6, base - 68


def poplar(l, x, base, h, seed):
    """Álamo dorado de otoño, en penacho, luz a la izquierda."""
    rng = random.Random(seed)
    r = h * 0.17
    u = (XX - x) / r
    t = np.clip((base - 3 - YY) / h, 0, 1)
    prof = np.sin(np.clip(t, 0, 1) * math.pi) ** 0.55 * (1 - t * 0.35)
    nz = fbm(XX / 3, YY / 4, seed, 3)
    m = (np.abs(u) < prof + (nz - 0.5) * 0.7) & (YY > base - 3 - h) & (YY < base - 3)
    lit = np.clip(0.6 - u * 0.55 + (nz - 0.5) * 1.1, 0, 1)
    val = np.round(lit * 4) / 4
    c = mix(mix(hx("#7A4E3C"), hx("#D8892E"), np.clip(val * 2, 0, 1)), hx("#FFE27A"), np.clip(val * 2 - 1, 0, 1))
    l.rect(x, base - 6, x + 1, base, hx("#4E3638"))
    l.put(m, c)


def cardon(l, x, base, h, r, seed):
    """Cardón a contraluz: costillas, brazos en codo y filo de sol a la izquierda."""
    lit, mid, dark, deep = hx("#F2D28E"), hx("#7C8C5A"), hx("#46604E"), hx("#2C3448")

    def shade_u(u, ribs):
        t = np.round(np.clip(0.56 - u * 0.66, 0, 1) * 6) / 6
        c = mix(deep, dark, np.clip(t * 2.5, 0, 1))
        c = np.where((t > 0.4)[..., None], mix(dark, mid, np.clip(t * 2.5 - 1, 0, 1)), c)
        c = np.where((t > 0.85)[..., None], lit, c)
        return np.where(ribs[..., None], c, mix(c, deep, 0.5))

    def column(cx, top, bot, rr):
        u = (XX - cx) / rr
        m = (np.abs(u) <= 1) & (YY >= top + rr * (1 - np.sqrt(np.clip(1 - u ** 2, 0, 1)))) & (YY <= bot)
        l.put(m, shade_u(u, np.cos(u * 11.0) > -0.35))

    def elbow(sd, jy, cx, rr):
        """Brazo: sale del tronco, dobla en cuarto de círculo y sube."""
        ex = x + sd * r * 0.7
        rad = abs(cx - ex)
        ccy = jy - rad
        d = np.hypot(XX - ex, YY - ccy) - rad                    # distancia al eje del codo
        m = ((XX - ex) * sd >= 0) & (YY >= ccy) & (np.abs(d) <= rr)
        u = (d / rr) * (1.0 if sd > 0 else -1.0)
        l.put(m, shade_u(u, np.cos(d / rr * 11.0) > -0.35))
        return ccy

    arms = ((-1, base - h * 0.34, x - r * 2.9, base - h * 0.80, r * 0.72),
            (1, base - h * 0.46, x + r * 2.7, base - h * 0.74, r * 0.66))
    for sd, jy, cx, ty, rr in arms:
        cy = elbow(sd, jy, cx, rr)
        column(cx, ty, cy + 1, rr)
    column(x, base - h, base, r)
    rng = random.Random(seed)
    for _ in range(int(h * 0.16)):                               # espinas sueltas sobre el filo
        l.px(int(x - r * rng.uniform(0.3, 0.95)), rng.randrange(int(base - h) + 4, int(base)), hx("#FFEFC0"))
    for fx, fy in ((x, base - h), (x + r * 2.7, base - h * 0.74)):    # flor del cardón
        for dx, dy in ((0, 0), (-1, 0), (1, 0), (0, -1)):
            l.px(int(fx + dx), int(fy + dy - 1), hx("#FFF3DC"))
        l.px(int(fx), int(fy - 1), hx("#F2B84B"))


def valley():
    """Fondo del valle: lecho seco, río, pueblo y álamos."""
    l = Layer()
    x = XX[0]
    top = 604 + 7 * np.sin(x / 44) - 12 * line1(x, 71, 60, 3) + 5 * ((x - 240) / 240) ** 2
    m = (YY >= top[None, :]) & (YY < 790)
    n = fbm(XX / 16, YY / 5, 72, 4)
    val = np.round(np.clip(0.52 + (n - 0.5) * 2.2 + (YY - 620) / 90, 0, 1) * 5) / 5
    c = mix(hx("#B4784E"), hx("#F4C684"), val)
    c = sun_grade(c, 1.0)
    l.put(m, c)
    l.rgb[m & (YY - top[None, :] < 1.2)] = hx("#FFE4AE")
    # lecho seco y río de deshielo que cruza bajo el viaducto
    cx = 158 + 72 * np.sin(YY / 31.0) + (YY - 610) * 1.1
    hw = 7 + (YY - 606) * 0.42
    bed = m & (np.abs(XX - cx) < hw + 6)
    l.put(bed, mix(hx("#E9D0A4"), hx("#FFEED0"), np.round(fbm(XX / 7, YY / 3, 74, 2) * 4) / 4))
    water = m & (np.abs(XX - cx) < hw * 0.55)
    wc = mix(hx("#6FA7C8"), hx("#FFD9A0"), np.round(fbm(XX / 9, YY / 2, 75, 2) * 3) / 3 * 0.8)
    l.put(water, wc)
    river_mask = water & (YY < ROAD_TOP - 1)
    river_rgb = l.rgb.copy()
    # matas de jarilla y piedras
    rng = random.Random(9)
    for _ in range(90):
        tx, ty = rng.randrange(W), rng.randrange(612, ROAD_TOP - 2)
        if not m[ty, tx] or bed[ty, tx]:
            continue
        r = rng.choice((2, 2, 3, 4))
        for dy in range(-r, 1):
            for dx in range(-r - 1, r + 2):
                if dx * dx / (r + 1) ** 2 + dy * dy / r ** 2 <= 1:
                    t = (dx + r) / (2 * r + 1) * 0.6 - dy / r * -0.3
                    l.px(tx + dx, ty + dy, mix(hx("#E5C46A"), hx("#5F6E4A"), min(1.0, t + 0.2)))
    windows = []
    # pueblo escalonado sobre la margen derecha
    shadow_all = np.zeros((H, W), dtype=bool)
    rows = [
        (620, [(252, 26, 15, "#C98A58"), (286, 22, 13, "#D99B62"), (372, 28, 16, "#CF9060"), (408, 24, 14, "#D99B62")]),
        (628, [(236, 22, 13, "#DCA46C"), (264, 30, 17, "#C78656"), (354, 22, 14, "#E0A872"), (384, 30, 16, "#D2935E"), (424, 26, 14, "#C98A58")]),
        (637, [(222, 28, 16, "#D99B62"), (256, 24, 13, "#E0A872"), (288, 20, 12, "#CF9060"), (368, 26, 15, "#D99B62"), (400, 22, 13, "#E0A872"), (432, 28, 15, "#CF9060")]),
    ]
    for tx, hh, seed in ((231, 52, 1), (244, 60, 2), (345, 56, 3), (446, 66, 4), (462, 58, 5), (216, 44, 6)):
        poplar(l, tx, 620, hh, seed + 80)
    for i, (base, houses) in enumerate(rows):
        if i == 1:
            church(l, 306, 626, windows)
        for j, (hxx, w, h, col) in enumerate(houses):
            sh = house(l, hxx, base, w, h, 100 + i * 10 + j, col, "flat" if (i + j) % 3 else "paja", True, windows)
            shadow_all |= sh
    sm = shadow_all & m & ~l.a
    d = shadow_all & m
    l.rgb[d] = mix(l.rgb[d], hx("#4A3C78"), 0.42)
    l.rect(298, 592, 298, 628, hx("#E8E2D8"))              # mástil de la plaza
    fl_pos = (299, 592)
    chimneys = [(278, 609), (396, 610), (446, 621)]
    for cxx, cyy in chimneys:
        l.rect(cxx, cyy, cxx + 2, cyy + 4, hx("#6E4A4A"))
    # álamos delante, junto a la ruta
    for tx, hh, seed in ((206, 70, 11), (194, 58, 12), (452, 74, 13), (218, 50, 14)):
        poplar(l, tx, 640, hh, seed + 90)
    river_mask &= np.all(l.rgb == river_rgb, axis=-1)     # sólo lo que no tapan árboles ni casas
    return l, river_mask, windows, chimneys, fl_pos


# ------------------------------------------------------------------ ruta y primer plano

def road():
    l = Layer()
    m = (YY >= ROAD_TOP - 3) & (YY < H)
    n = fbm(XX / 22, YY / 9, 91, 4)
    n2 = fbm(XX / 5, YY / 3, 92, 3)
    v = np.round(np.clip(0.5 + (n - 0.5) * 0.8 + (n2 - 0.5) * 0.7 - (YY - 690) / 260, 0, 1) * 6) / 6
    c = mix(hx("#7A4A44"), hx("#E8B070"), v)
    c = mix(c, hx("#2E2A50"), np.clip((YY - 720) / 190, 0, 0.72))
    l.put(m, sun_grade(c, 0.5))
    # banquina y borde de la ruta
    l.rect(0, ROAD_TOP - 3, W, ROAD_TOP - 1, hx("#F2CE94"))
    l.rect(0, ROAD_TOP - 3, W, ROAD_TOP - 3, hx("#FFEAC2"))
    # asfalto gastado
    a = (YY >= ROAD_TOP) & (YY <= ROAD_BOT)
    t = np.clip((YY - ROAD_TOP) / (ROAD_BOT - ROAD_TOP), 0, 1)
    ac = mix(hx("#7C6A84"), hx("#4A4464"), t)
    gl = np.clip(1 - np.hypot((XX - SUN[0]) / 170, (YY - ROAD_TOP) / 12), 0, 1)
    ac = mix(ac, hx("#FFC88A"), np.round(gl * 4) / 4 * 0.5)                  # brillo rasante del sol
    grain = np.round((fbm(XX / 3, YY / 1.5, 93, 2) - 0.5) * 6) / 6
    ac = ac * (1 + grain[..., None] * 0.16)
    l.put(a, ac)
    cracks = (ridged(XX / 30, YY / 8, 94, 3) > 0.965) & a
    l.rgb[cracks] = hx("#3A3454")
    # línea central discontinua y bordes
    my = (ROAD_TOP + ROAD_BOT) // 2 + 1
    for x in range(-6, W, 26):
        l.rect(x, my, x + 13, my + 1, hx("#F4E6C0"))
    l.rect(0, ROAD_TOP + 1, W, ROAD_TOP + 1, hx("#E9DDBE"))
    l.rect(0, ROAD_BOT - 1, W, ROAD_BOT - 1, hx("#D6C8AA"))
    l.rect(0, ROAD_BOT + 1, W, ROAD_BOT + 3, hx("#C89A66"))
    # piedras al borde
    rng = random.Random(5)
    for _ in range(46):
        x, y = rng.randrange(W), rng.randrange(ROAD_BOT + 6, 900)
        r = rng.choice((2, 3, 3, 5, 8))
        for dy in range(-r, 2):
            for dx in range(-r - 2, r + 3):
                if (dx / (r + 2)) ** 2 + (dy / r) ** 2 <= 1 and 0 <= y + dy < H and 0 <= x + dx < W:
                    t = 0.5 - dx / (r * 3) - dy / (r * 2.2) * -0.4
                    l.px(x + dx, y + dy, mix(hx("#4A3C60"), hx("#E8BE8C"), np.clip(t, 0, 1)))
    return l


def post(l):
    """Mojones y cartel de ruta nacional, parte del borde del camino."""
    for x in range(26, W, 92):
        l.rect(x, ROAD_TOP - 11, x + 2, ROAD_TOP - 2, hx("#F6EEDC"))
        l.rect(x + 3, ROAD_TOP - 10, x + 3, ROAD_TOP - 2, hx("#8A7A90"))
        l.rect(x, ROAD_TOP - 8, x + 2, ROAD_TOP - 7, hx("#D8402E"))
    sx = 138
    l.rect(sx + 8, ROAD_TOP - 34, sx + 9, ROAD_TOP - 2, hx("#6E6680"))
    l.rect(sx, ROAD_TOP - 50, sx + 18, ROAD_TOP - 33, hx("#F6F0E2"))
    l.rect(sx + 1, ROAD_TOP - 49, sx + 17, ROAD_TOP - 34, hx("#1E4E8C"))
    for i, row in enumerate(("111", "101", "111", "001", "111")):            # ruta 9
        for j, b in enumerate(row):
            if b == "1":
                l.rect(sx + 7 + j * 2, ROAD_TOP - 47 + i * 2, sx + 8 + j * 2, ROAD_TOP - 46 + i * 2, hx("#FFFFFF"))


def fore():
    l = Layer()
    cardon(l, 84, 706, 128, 11, 1)
    cardon(l, 424, 702, 96, 9, 2)
    return l


# ------------------------------------------------------------------ sprites

def save_rgba(a, name):
    Image.fromarray(a.astype(np.uint8), "RGBA").save(os.path.join(OUT, name))


def train():
    """Locomotora y coche, 2 cuadros (biela). Celeste y blanco con ventanas encendidas."""
    w, h = 42, 18
    a = np.zeros((h * 2, w * 2, 4), np.uint8)
    im = Image.fromarray(a, "RGBA")
    d = ImageDraw.Draw(im)

    def body(ox, oy, f, loco):
        navy, sky_c, cream = (34, 58, 112, 255), (70, 120, 184, 255), (246, 236, 214, 255)
        if loco:
            d.polygon([(ox + 2, oy + 4), (ox + 34, oy + 4), (ox + 38, oy + 8), (ox + 38, oy + 14), (ox + 2, oy + 14)], fill=sky_c)
            d.rectangle((ox + 24, oy + 3, ox + 33, oy + 9), fill=navy)
            d.rectangle((ox + 26, oy + 5, ox + 31, oy + 8), fill=(255, 226, 150, 255))
            d.rectangle((ox + 6, oy + 2, ox + 9, oy + 4), fill=(52, 44, 66, 255))
            d.line([(ox + 2, oy + 4), (ox + 34, oy + 4)], fill=(170, 206, 232, 255))
            d.rectangle((ox + 2, oy + 10, ox + 38, oy + 11), fill=cream)
            d.rectangle((ox + 37, oy + 12, ox + 38, oy + 13), fill=(255, 244, 200, 255))
        else:
            d.rectangle((ox + 1, oy + 3, ox + 39, oy + 14), fill=sky_c)
            d.line([(ox + 1, oy + 3), (ox + 39, oy + 3)], fill=(190, 220, 240, 255))
            d.rectangle((ox + 1, oy + 11, ox + 39, oy + 12), fill=cream)
            for wx in range(ox + 4, ox + 36, 7):
                d.rectangle((wx, oy + 5, wx + 4, oy + 8), fill=(255, 222, 140, 255))
                d.point((wx, oy + 5), fill=(255, 248, 214, 255))
        d.rectangle((ox + 2, oy + 14, ox + 38, oy + 14), fill=(30, 26, 40, 255))
        for wx in (ox + 7, ox + 12, ox + 28, ox + 33):
            d.rectangle((wx - 1, oy + 15, wx + 2, oy + 17), fill=(30, 26, 40, 255))
            d.point((wx + (f % 2), oy + 16), fill=(196, 202, 212, 255))

    for f in range(2):
        body(f * w, 0, f, True)
        body(f * w, h, f, False)
    im.save(os.path.join(OUT, "start_train.png"))


def condor():
    """Cóndor planeando: alas con dedos abiertos, collar blanco. 4 cuadros."""
    w, h = 44, 20
    im = Image.new("RGBA", (w * 4, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    dark, mid, white = (28, 24, 38, 255), (66, 58, 84, 255), (240, 234, 222, 255)
    for f, lift in enumerate((-3, -1, 2, -1)):
        ox = f * w
        cx, cy = ox + w // 2, 10
        for sd in (-1, 1):
            tipx, tipy = cx + sd * 20, cy + lift
            d.polygon([(cx, cy - 2), (cx + sd * 10, cy - 2 + lift // 2), (tipx, tipy), (cx + sd * 12, cy + 3), (cx, cy + 2)], fill=dark)
            d.line([(cx + sd * 2, cy - 1), (cx + sd * 12, cy + lift // 2)], fill=mid)
            d.line([(cx + sd * 4, cy + 1), (cx + sd * 12, cy + 2)], fill=white)
            for k in range(3):                     # plumas primarias abiertas
                d.line([(cx + sd * (15 + k * 2), cy + lift // 2 + 1), (tipx + sd * 1, tipy + 1 + k)], fill=dark)
        d.ellipse((cx - 3, cy - 3, cx + 3, cy + 3), fill=dark)
        d.line([(cx + 3, cy - 2), (cx + 5, cy - 2)], fill=white)
        d.point((cx + 6, cy - 2), fill=(214, 120, 96, 255))
        d.polygon([(cx - 3, cy + 1), (cx - 8, cy + 5), (cx - 2, cy + 3)], fill=dark)
    im.save(os.path.join(OUT, "start_condor.png"))


def llama():
    """Llama: parada, pastando (2), mirando; 6 cuadros de 26x30."""
    w, h = 26, 30
    im = Image.new("RGBA", (w * 4, h * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def one(ox, oy, wool, wool_d, graze, leg, tail):
        d.ellipse((ox + 5, oy + 13, ox + 19, oy + 22), fill=wool)
        d.arc((ox + 5, oy + 13, ox + 19, oy + 22), 90, 270, fill=(255, 240, 214, 255))
        d.pieslice((ox + 5, oy + 15, ox + 19, oy + 23), 20, 160, fill=wool_d)
        if graze:
            d.polygon([(ox + 16, oy + 15), (ox + 22, oy + 21), (ox + 21, oy + 25), (ox + 18, oy + 22), (ox + 15, oy + 19)], fill=wool)
            d.rectangle((ox + 20, oy + 24, ox + 24, oy + 27), fill=wool)
            d.point((ox + 24, oy + 27), fill=(60, 44, 44, 255))
        else:
            d.polygon([(ox + 16, oy + 16), (ox + 19, oy + 16), (ox + 21, oy + 5), (ox + 18, oy + 5)], fill=wool)
            d.line([(ox + 21, oy + 6), (ox + 21, oy + 15)], fill=wool_d)
            d.rectangle((ox + 18, oy + 3, ox + 24, oy + 7), fill=wool)
            d.rectangle((ox + 23, oy + 5, ox + 24, oy + 6), fill=(92, 62, 56, 255))
            d.point((ox + 21, oy + 4), fill=(40, 30, 36, 255))
            d.line([(ox + 19, oy + 1), (ox + 19, oy + 3)], fill=wool_d)
            d.line([(ox + 21, oy + 1), (ox + 21, oy + 3)], fill=wool_d)
        for lx in (7, 10, 15, 18):
            d.line([(ox + lx, oy + 22), (ox + lx + leg * ((lx % 2) * 2 - 1), oy + 28)], fill=wool_d if lx in (10, 18) else wool)
            d.point((ox + lx + leg * ((lx % 2) * 2 - 1), oy + 28), fill=(52, 40, 44, 255))
        d.line([(ox + 5, oy + 15), (ox + 3, oy + 13 + tail)], fill=wool_d)
        d.point((ox + 12, oy + 15), fill=(214, 72, 78, 255))           # borla de la señalada
        d.point((ox + 13, oy + 15), fill=(246, 190, 70, 255))

    wa, wb = (240, 222, 196, 255), (176, 140, 124, 255)
    wc, wd = (146, 100, 74, 255), (92, 62, 66, 255)
    for r, (a, b) in enumerate(((wa, wb), (wc, wd))):
        one(0, r * h, a, b, False, 0, 0)
        one(w, r * h, a, b, True, 0, 0)
        one(2 * w, r * h, a, b, True, 0, 2)
        one(3 * w, r * h, a, b, False, 1, 1)
    im.save(os.path.join(OUT, "start_llama.png"))


def flag():
    """Bandera argentina flameando, 4 cuadros de 16x10."""
    w, h = 16, 12
    a = np.zeros((h, w * 4, 4), np.uint8)
    cel, bl, sol = (116, 176, 226, 255), (248, 246, 238, 255), (242, 184, 72, 255)
    for f in range(4):
        for x in range(13):
            off = int(round(1.4 * math.sin(x * 0.75 - f * math.pi / 2) * (x / 12 + 0.2)))
            shade = 1.0 if (x + f) % 4 < 2 else 0.84
            for y in range(9):
                c = cel if (y < 3 or y >= 6) else bl
                if y == 4 and x == 6:
                    c = sol
                c = tuple(int(v * shade) for v in c[:3]) + (255,)
                yy = y + 1 + off
                if 0 <= yy < h:
                    a[yy, f * w + x] = c
    save_rgba(a, "start_flag.png")


def tuft():
    """Paja brava mecida por el viento, 3 cuadros de 18x16."""
    w, h = 18, 16
    im = Image.new("RGBA", (w * 3, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    rng = random.Random(3)
    blades = [(rng.randint(2, 15), rng.randint(7, 14), rng.choice([(236, 200, 110, 255), (204, 160, 80, 255), (160, 118, 66, 255), (252, 228, 150, 255)])) for _ in range(16)]
    for f, lean in enumerate((0, 2, 4)):
        for bx, bh, c in blades:
            d.line([(f * w + bx, h - 1), (f * w + bx + lean * bh // 12, h - 1 - bh)], fill=c)
    im.save(os.path.join(OUT, "start_tuft.png"))


def far_car():
    a = np.zeros((3, 4, 4), np.uint8)
    a[1, 0:3] = (60, 50, 70, 255)
    a[0, 1] = (220, 200, 180, 255)
    a[1, 3] = (255, 240, 170, 255)
    save_rgba(a, "start_far_car.png")


def twinkle():
    a = np.zeros((3, 9, 4), np.uint8)
    for f, s in enumerate(((1,), (1, 2), (1,))):
        a[1, f * 3 + 1] = (255, 248, 220, 255)
        if 2 in s:
            for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
                a[dy, f * 3 + dx] = (255, 240, 200, 150)
    save_rgba(a, "start_star.png")


def overlays(river, windows):
    # brillos del río: 4 cuadros que se alternan
    ys, xs = np.where(river)
    rng = np.random.default_rng(5)
    y0, y1 = ys.min(), ys.max()
    h = y1 - y0 + 1
    a = np.zeros((h, W * 4, 4), np.uint8)
    for f in range(4):
        pick = rng.random(len(xs)) < 0.22
        for x, y in zip(xs[pick], ys[pick]):
            a[y - y0, f * W + x] = (255, 244, 208, 235)
            if x + 1 < W:
                a[y - y0, f * W + x + 1] = (255, 226, 170, 190)
    save_rgba(a, "start_river.png")
    # ventanas que se encienden: 3 grupos
    ymin = min(w[1] for w in windows)
    ymax = max(w[1] for w in windows) + 5
    hh = ymax - ymin + 1
    b = np.zeros((hh, W * 3, 4), np.uint8)
    for wx, wy, g in windows:
        size = (2, 3)
        b[wy - ymin:wy - ymin + size[1] + 1, g * W + wx:g * W + wx + size[0] + 2] = (255, 214, 120, 255)
        b[wy - ymin, g * W + wx] = (255, 246, 200, 255)
    save_rgba(b, "start_windows.png")
    return int(y0), int(ymin)


def finish(layers):
    """Paleta común (como una tirada de postal): los cúmulos quedan limpios."""
    comp = np.zeros((H, W, 3))
    for lay in layers:
        comp[lay.a] = lay.rgb[lay.a]
    pal_img = Image.fromarray(np.clip(comp, 0, 255).astype(np.uint8), "RGB").quantize(colors=128, method=Image.MEDIANCUT, dither=Image.NONE)
    for lay in layers:
        im = Image.fromarray(np.clip(lay.rgb, 0, 255).astype(np.uint8), "RGB")
        q = im.quantize(palette=pal_img, dither=Image.NONE).convert("RGB")
        lay.rgb = np.array(q, dtype=np.float64)


def save_layer(l, name, keep=True):
    out = np.zeros((H, W, 4), np.uint8)
    out[..., :3] = np.clip(l.rgb, 0, 255)
    out[..., 3] = np.where(l.a, 255, 0)
    Image.fromarray(out, "RGBA").save(os.path.join(OUT, name))


def main():
    os.makedirs(OUT, exist_ok=True)
    s, a, h = sky(), andes(), hills()
    v, river, windows, chimneys, fl = valley()
    r = road()
    post(r)
    f = fore()
    layers = [s, a, h, v, r, f]
    finish(layers)
    for lay, name in zip(layers, ("start_sky.png", "start_andes.png", "start_hills.png", "start_valley.png", "start_road.png", "start_fore.png")):
        save_layer(lay, name)
    viaduct().save(os.path.join(OUT, "start_viaduct.png"))
    train(); condor(); llama(); flag(); tuft(); far_car(); twinkle()
    ry, wy = overlays(river, windows)
    info = {
        "w": W, "h": H, "road_top": ROAD_TOP, "road_bot": ROAD_BOT, "lane_far": LANE_FAR, "lane_near": LANE_NEAR,
        "river_y": ry, "windows_y": wy, "serp": [list(p) for p in SERP], "chimneys": chimneys, "flag": list(fl),
        "ground": "#%02x%02x%02x" % tuple(int(k) for k in r.rgb[H - 1, W // 2]),
        "deck_a": 500.0, "deck_b": 22.0, "sky_top": "#232A63",
        "llamas": [[132, 634, 0], [168, 640, 1], [150, 628, 0]],
        "tufts": [[112, 690], [300, 694], [176, 692], [350, 690]],
    }
    with open(os.path.join(ROOT, "data", "postal.json"), "w", encoding="utf-8", newline="") as fh:
        json.dump(info, fh, indent=1)
    print("postal lista")


if __name__ == "__main__":
    main()
