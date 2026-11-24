"""15.2: fondo de la página de pioneros (web/pioneros.html): las 6 regiones del juego
como pilares, cada una con su paisaje a la hora dorada, con la técnica de la postal del
NOA de la pantalla de inicio (tools/art/postal15.py): planos pintados con ruido, tonos
cuantizados, sol bajo a la IZQUIERDA (todo tiene filo cálido a la izquierda y sombra
violeta a la derecha, y las sombras se proyectan largas hacia la derecha) y bruma que
aclara lo lejano.

  NOA        la postal de inicio (capas reales) + cardones, pirca y piedras adelante
  NEA        Garganta del Diablo en herradura, bruma que sube, pasarela, río y selva
  Cuyo       Aconcagua, álamos dorados, bodega, camino y viñedo con parras adelante
  Patagonia  agujas de granito del Fitz Roy, campo de hielo y glaciar al lago, lengas
  Pampeana   cúmulos y estratos, estancia con eucaliptos, molino, ombú, vacas, trigal
  Centro     sierras con monte, dique, capilla jesuítica, cosechadora y algarrobo

  python tools/art/pilares_web.py [región]  -> web/img/pilares.png (1920x1080) + web/img/region_<id>.png
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import postal15 as P  # noqa: E402  (ruido, tonos y paleta de la postal)

ROOT = P.ROOT
OUT = os.path.join(ROOT, "web", "img")
START = os.path.join(ROOT, "assets", "escenarios", "start")
FONT = os.path.join(ROOT, "assets", "fonts", "VT323-Regular.ttf")

W, H = 300, 900
YY, XX = np.mgrid[0:H, 0:W].astype(np.float64)
BY = P.BAYER[YY.astype(int) % 4, XX.astype(int) % 4]
hx, mix, fbm, ridged, tones, blur1 = P.hx, P.mix, P.fbm, P.ridged, P.tones, P.blur1
HAZE = hx("#F7B37C")
OUTL = hx("#3D1B0B")
LIGHT = np.array([-0.86, -0.28, 0.43])                 # sol bajo a la izquierda
LIGHT = LIGHT / np.linalg.norm(LIGHT)
SHADOW = hx("#3A2E5A")
RIM = hx("#FFD08A")


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
        x, y = int(round(x)), int(round(y))
        if 0 <= x < W and 0 <= y < H:
            self.rgb[y, x] = c
            self.a[y, x] = True

    def rect(self, x0, y0, x1, y1, c):
        x0, x1 = max(0, int(x0)), min(W - 1, int(x1))
        y0, y1 = max(0, int(y0)), min(H - 1, int(y1))
        if x1 >= x0 and y1 >= y0:
            self.rgb[y0:y1 + 1, x0:x1 + 1] = c
            self.a[y0:y1 + 1, x0:x1 + 1] = True

    def local(self, x0, y0, x1, y1):
        x0, x1 = max(0, int(x0)), min(W, int(x1))
        y0, y1 = max(0, int(y0)), min(H, int(y1))
        if x1 <= x0 or y1 <= y0:
            return None
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float64)
        return (slice(y0, y1), slice(x0, x1)), yy, xx

    def put_local(self, sl, m, col):
        sub = self.rgb[sl]
        sub[m] = col[m] if col.ndim == 3 else col
        self.a[sl] |= m


def comp(layers):
    out = np.zeros((H, W, 3))
    for l in layers:
        if isinstance(l, np.ndarray):
            out = l.copy()
        else:
            out[l.a] = l.rgb[l.a]
    return out


def ell_mask(cx, cy, rx, ry):
    return ((XX - cx) / rx) ** 2 + ((YY - cy) / ry) ** 2 <= 1.0


def glow(sun, strength=1.0, reach=330):
    d = np.hypot((XX - sun[0]) / 1.5, YY - sun[1])
    return np.clip(1 - d / reach, 0, 1) ** 2 * strength


def ramp(stops, v):
    pal = np.stack([hx(c) for c in stops])
    i = np.clip(np.round(np.asarray(v) * (len(stops) - 1)), 0, len(stops) - 1).astype(int)
    return pal[i]


def hazed(col, k, haze=HAZE):
    return mix(col, haze, np.clip(k, 0, 1))


def edges(m):
    """Bordes de una máscara: (izquierda, derecha, arriba, abajo)."""
    l_ = np.zeros_like(m)
    l_[:, 1:] = m[:, :-1]
    r_ = np.zeros_like(m)
    r_[:, :-1] = m[:, 1:]
    u_ = np.zeros_like(m)
    u_[1:, :] = m[:-1, :]
    d_ = np.zeros_like(m)
    d_[:-1, :] = m[1:, :]
    return m & ~l_, m & ~r_, m & ~u_, m & ~d_


def rim_light(l, mask=None, k=0.55, dark=None):
    """Filo cálido a la izquierda y borde violeta a la derecha de lo que haya en la capa."""
    m = l.a if mask is None else mask
    le, ri, up, _ = edges(m)
    l.rgb[le | (up & le)] = mix(l.rgb[le | (up & le)], RIM, k)
    if dark is not None:
        l.rgb[ri] = mix(l.rgb[ri], dark, 0.5)


def shadow_on(img, cx, cy, rx, ry, k=0.42):
    m = ell_mask(cx, cy, rx, ry)
    img[m] = mix(img[m], SHADOW, k)


def long_shadow(img, x, base, h, w, k=0.4):
    """Sombra larga hacia la derecha de un objeto parado en (x, base)."""
    shadow_on(img, x + h * 0.55, base + 1, h * 0.62, max(2, w * 0.08), k)


# ------------------------------------------------------------------ cielo

SKY_STOPS = [(0, "#232A63"), (130, "#3F3E8C"), (230, "#7A519E"), (300, "#C2607F"), (362, "#EE8A5C"),
             (420, "#FBBA62"), (480, "#FFE3A0"), (900, "#FFE3A0")]


def sky(seed, sun, stops=None, clouds=0.72, horizon=640):
    l = Layer()
    stops = stops or SKY_STOPS
    c = np.zeros((H, W, 3))
    ys = [s[0] for s in stops]
    for ch in range(3):
        c[..., ch] = np.interp(YY, ys, [hx(s[1])[ch] for s in stops])
    d = np.hypot((XX - sun[0]) / 1.35, YY - sun[1])
    c = mix(c, hx("#FFD98C"), np.clip(1 - d / 260, 0, 1) ** 2.2 * 0.75)
    n = fbm(XX / 90 + YY / 40, YY / 11, seed, 4)
    n2 = fbm(XX / 40, YY / 7, seed + 6, 3)
    v = n * 0.7 + n2 * 0.3
    cir = np.clip((v - 0.54) / 0.14, 0, 1) * np.clip((YY - 120) / 90, 0, 1) * np.clip((395 - YY) / 80, 0, 1)
    tint = mix(hx("#FFB98C"), hx("#FFE9BE"), np.clip((YY - 220) / 170, 0, 1))
    c = mix(c, tint, np.round(cir * 3) / 3 * clouds)
    under = np.clip((v - 0.5) / 0.05, 0, 1) * (1 - np.clip((v - 0.56) / 0.05, 0, 1))
    c = mix(c, hx("#B05A86"), under * clouds * 0.35 * np.clip((YY - 140) / 120, 0, 1) * np.clip((395 - YY) / 80, 0, 1))
    c = np.floor(c / 7.0 + BY[..., None] * 0.98) * 7.0
    l.put(YY < horizon + 60, c)
    rng = random.Random(seed)
    for _ in range(54):
        x, y = rng.randrange(W), rng.randrange(0, 200)
        k = rng.choice((0.3, 0.45, 0.7)) * (1 - y / 240)
        l.rgb[y, x] = mix(l.rgb[y, x], hx("#FFF6D8"), k)
    return l


def cumulus(l, seed, cx, cy, rx, ry, n_base=9, n_top=3):
    """Cúmulo en coliflor: lóbulos arriba, base plana en sombra. La luz de los lóbulos se
    mezcla suave (sin costuras verticales) y se escalona en 5 valores."""
    rng = random.Random(seed)
    balls = []
    for k in range(n_base):
        t = k / (n_base - 1)
        r = ry * (0.26 + 0.34 * math.sin(math.pi * t)) * rng.uniform(0.8, 1.15)
        bx = cx + (t - 0.5) * rx * 1.55 + rng.uniform(-5, 5)
        by = cy + ry * 0.42 - r * 0.85
        balls.append((bx, by, r))
    for k in range(n_top):
        r = ry * rng.uniform(0.2, 0.32)
        balls.append((cx + rng.uniform(-0.4, 0.4) * rx, cy - ry * rng.uniform(0.15, 0.55), r))
    base_y = cy + ry * 0.42
    num = np.zeros((H, W))
    den = np.zeros((H, W))
    inside_any = np.zeros((H, W), dtype=bool)
    for bx, by, rr in balls:
        d2 = ((XX - bx) ** 2 + (YY - by) ** 2) / (rr * rr)
        inside = d2 <= 1.0
        nz = np.sqrt(np.clip(1 - d2, 0, 1))
        lam = np.clip((XX - bx) / rr * LIGHT[0] + (YY - by) / rr * LIGHT[1] + nz * LIGHT[2], 0, 1)
        wgt = np.where(inside, np.exp(nz * 3.0), 0.0)
        num += wgt * lam
        den += wgt
        inside_any |= inside
    cov = inside_any.any(axis=0)
    first = np.where(cov, np.argmax(inside_any, axis=0), H)
    body = cov[None, :] & (YY >= first[None, :]) & (YY <= base_y)
    xs = np.where(cov)[0]
    if len(xs):
        lo_, hi_ = xs.min(), xs.max()
        corner = np.minimum(XX - lo_, hi_ - XX)
        body &= (base_y - YY) >= np.clip(10 - corner, 0, 10) * 0.9
    m = (inside_any | body) & (YY <= base_y)
    lam = np.where(den > 0, num / np.maximum(den, 1e-6), 0.35)
    lam = P.box(lam, 2)
    under = np.clip((YY - (base_y - ry * 0.55)) / (ry * 0.55), 0, 1)
    val = np.clip(lam * 0.9 + 0.1 - under * 0.55, 0, 1)
    l.put(m, ramp(["#4E3E7A", "#6E4E8A", "#A05E8C", "#D8807E", "#FFB488", "#FFE2B0"], val))
    le, _, up, dn = edges(m)
    l.rgb[le | up] = mix(l.rgb[le | up], hx("#FFF0D0"), 0.55)
    l.rgb[dn] = hx("#5A3E78")


def stratus(l, seed, y, h, x0=-20, x1=W + 20):
    """Bancos de nubes bajas y largas cerca del horizonte, encendidos abajo."""
    n = fbm(XX / 40, YY / 4, seed, 3)
    hh = h * (0.55 + 0.9 * fbm(XX / 46, np.full_like(XX, 2.0), seed + 9, 2))
    band = np.clip(1 - np.abs(YY - y - (fbm(XX / 60, np.full_like(XX, 5.0), seed + 3, 2) - 0.5) * h) / hh, 0, 1)
    m = (n * 0.8 + band * 0.7 > 1.0) & (XX >= x0) & (XX <= x1)
    v = np.clip(0.4 + (YY - y) / h * 0.4 + (n - 0.5), 0, 1)
    l.put(m, ramp(["#A0688E", "#D88A88", "#F6B48A", "#FFDCA8"], np.round(v * 3) / 3))


# ------------------------------------------------------------------ montañas y suelos

def rock(top, seed, lo, hi, bottom, haze=0.0, snow=None, snow_lo="#8E7FC4", snow_hi="#FFE8D0", sun=(-60, 400), light=0.9, scale=15, gully=0.0):
    """Macizo con caras iluminadas desde la izquierda; la nieve baja en lenguas por las
    cárcavas (sin franja punteada)."""
    l = Layer()
    m = (YY >= top[None, :]) & (YY < bottom)
    dep = YY - top[None, :]
    g = ridged((XX + dep * 0.55) / scale, dep / (scale * 2), seed, 4)
    dg = np.gradient(g, axis=1)
    face = blur1(np.gradient(top), 9)
    lit = 0.46 + np.clip(-face[None, :] * 2.4, -0.36, 0.4) + np.clip(dg * 7.0, -0.26, 0.3)
    gl = ridged(XX / 7 + fbm(XX / 20, YY / 50, seed + 9, 2) * 3, YY / 80, seed + 7, 3)
    if gully:
        lit = lit - (gl > 0.82) * gully * np.clip(dep / 30, 0, 1)
    val = tones(lit, 6)
    base = mix(hx(lo), hx(hi), val)
    if snow is not None:
        x = XX[0]
        line = snow + 36 * (P.line1(x, seed + 2, 16, 3) - 0.5) * 2 + 34 * gl - 10
        sv = np.clip(val * 1.2 + 0.1, 0, 1)
        sc = ramp([snow_lo, P_mid(snow_lo, snow_hi), snow_hi], np.round(sv * 2) / 2)
        base = np.where((YY < line)[..., None], sc, base)
    base = mix(base, HAZE, np.clip(haze, 0, 1))
    base = mix(base, hx("#FFC070"), glow(sun, 0.42 * light))
    l.put(m, base)
    le, _, up, _ = edges(m)
    l.rgb[up | le] = mix(l.rgb[up | le], hx("#FFF0C8"), 0.6)
    return l


def P_mid(a, b):
    ca, cb = hx(a), hx(b)
    c = (ca + cb) / 2
    return "#%02X%02X%02X" % tuple(int(v) for v in c)


def ground(top, seed, stops, bottom=H, sun=(-60, 400), vx=150, rows=0.0, row_n=9, haze_k=0.5):
    """Suelo en perspectiva: grano fino, valor más claro y velado hacia el horizonte,
    surcos opcionales que convergen al punto de fuga (sin manchas de camuflaje)."""
    l = Layer()
    m = (YY >= top) & (YY < bottom)
    dep = np.clip(YY - top, 0.5, None)
    fine = fbm(XX / (1.6 + dep / 120), YY / (1.2 + dep / 160), seed, 2)
    v = 0.62 - dep / (H - top) * 0.45 + (fine - 0.5) * 0.35 + glow(sun, 0.25)
    if rows:
        u = np.mod((XX - vx) / dep * row_n, 1.0)
        far = np.clip((dep - 24) / 40, 0, 1)                # lejos: tono parejo, sin moiré
        v = v + ((u < 0.35) * -0.18 + (u > 0.8) * 0.08) * rows * far
    col = ramp(stops, np.clip(v, 0, 1))
    col = hazed(col, np.clip(1 - dep / 70, 0, 1) * haze_k)
    l.put(m, col)
    return l


# ------------------------------------------------------------------ vegetación

FOLIAGE = {   # de sombra (violeta/teal) a luz (ocre/dorado): hora dorada, no mediodía
    "verde": ["#1C2236", "#273A3E", "#3A5440", "#62723E", "#A0924A", "#E8C470"],
    "selva": ["#141C2C", "#1B3036", "#284838", "#456238", "#7E8440", "#CDB45E"],
    "ombu": ["#182032", "#24383A", "#34503C", "#566C3C", "#948C46", "#DEC068"],
    "eucalipto": ["#2A2E44", "#3A4A52", "#56685C", "#7E8A64", "#B4AA78", "#EAD49A"],
    "lenga": ["#2E1A2E", "#5A2434", "#923A30", "#C8602E", "#EE9A44", "#FFD27A"],
    "algarrobo": ["#1C2234", "#2A3A3C", "#405440", "#66723E", "#A29648", "#E2C46A"],
    "alamo": ["#3E2A2E", "#6E4A30", "#A8762E", "#D8A23A", "#F2CC5A", "#FFF0A0"],
    "parra": ["#1E2638", "#2C4038", "#42603A", "#6E823C", "#AEA048", "#EAD078"],
}
BARK = {
    "oscura": ["#221A24", "#3E2E34", "#664A44", "#A07A60"],
    "clara": ["#4A4A5A", "#7A7480", "#B4A8A0", "#E8DAC6"],
    "roja": ["#26161E", "#4E2A2E", "#84483C", "#C08666"],
    "palma": ["#2E242C", "#50424A", "#7E6A64", "#B89A80"],
}


def stroke(l, x0, y0, x1, y1, w0, w1, bark="oscura", seed=1, haze=0.0, wobble=0.0):
    """Tronco/rama cilíndrico con corteza, luz a la izquierda y borde violeta a la derecha."""
    pal = BARK[bark]
    n = max(2, int(math.hypot(x1 - x0, y1 - y0) * 1.6))
    rng = random.Random(seed)
    for i in range(n + 1):
        t = i / n
        cx = x0 + (x1 - x0) * t + wobble * math.sin(t * 7 + seed)
        cy = y0 + (y1 - y0) * t
        hw = max(0.6, (w0 + (w1 - w0) * t) / 2)
        for dx in range(int(-hw - 1), int(hw + 2)):
            u = dx / hw
            if abs(u) > 1.0:
                continue
            v = 0.66 - u * 0.62 + (rng.random() - 0.5) * 0.18
            if (int(cy) // 2 + dx * 5 + seed) % 9 == 0:
                v -= 0.3
            col = hx(pal[int(np.clip(round(v * 3), 0, 3))])
            if u < -0.78:
                col = mix(col, RIM, 0.45)
            if u > 0.8:
                col = mix(hx(pal[0]), SHADOW, 0.3)
            l.px(cx + dx, cy, hazed(col, haze))


def canopy(l, cx, cy, w, h, seed, pal="verde", clumps=14, leaf=1.0, haze=0.0, flat_bottom=0.75):
    """Copa con volumen: forma grande (60 % de la luz) + relieve de racimos, textura de
    hojas, huecos con cielo en el borde, panza en sombra, filo dorado a la izquierda."""
    rng = random.Random(seed)
    stops = FOLIAGE[pal]
    win = l.local(cx - w * 0.62, cy - h * 0.66, cx + w * 0.62, cy + h * 0.62)
    if win is None:
        return
    sl, yy, xx = win
    gx, gy = (xx - cx) / (w * 0.5), (yy - cy) / (h * 0.5)
    gy_f = np.where(gy > 0, gy / max(0.35, flat_bottom), gy)
    gd2 = gx ** 2 + gy_f ** 2
    leafn = fbm(xx / 1.8, yy / 1.8, seed, 2) - 0.5
    leafm = fbm(xx / 4.0, yy / 4.0, seed + 5, 2) - 0.5
    n = max(clumps * 2, 18)
    cl = []
    tries = 0
    while len(cl) < n and tries < n * 30:
        tries += 1
        ux, uy = rng.uniform(-1, 1), rng.uniform(-1, 0.85)
        if ux * ux + uy * uy > 0.92:
            continue
        cl.append((cx + ux * w * 0.42, cy + uy * h * 0.42, min(w, h) * rng.uniform(0.13, 0.2)))
    best_z = np.full(yy.shape, -1e9)
    loc = np.zeros(yy.shape)
    inside_c = np.zeros(yy.shape, dtype=bool)
    for px, py, r in cl:
        d2 = ((xx - px) ** 2 + (yy - py) ** 2) / (r * r)
        inside = d2 <= 1.0 + leafn * 0.9 * leaf
        nz = np.sqrt(np.clip(1 - d2, 0, 1))
        lam = np.clip(((xx - px) / r) * LIGHT[0] + ((yy - py) / r) * LIGHT[1] + nz * LIGHT[2], 0, 1)
        z = nz * r * 0.6 + (py - cy) * 0.25
        front = inside & (z > best_z)
        loc = np.where(front, lam, loc)
        best_z = np.where(front, z, best_z)
        inside_c |= inside
    body = gd2 <= 1.0 + leafn * 0.5 * leaf + leafm * 0.35
    inside = (inside_c & (gd2 <= 1.35 + leafn * 0.6)) | (body & (gd2 < 0.75))
    gnz = np.sqrt(np.clip(1 - np.clip(gd2, 0, 1), 0, 1))
    glam = np.clip(gx * LIGHT[0] + gy * LIGHT[1] + gnz * LIGHT[2], 0, 1)
    val = glam * 0.62 + loc * 0.42 - 0.08
    val = val - np.clip(gy, 0, 1) * 0.25
    val = val + leafn * 0.3 * leaf + leafm * 0.1
    sky_holes = (gd2 > 0.55) & (leafn > 0.28) & (leafm > 0.05)
    dark_holes = (gd2 <= 0.55) & (leafn > 0.36) & (glam < 0.6)
    inside = inside & ~sky_holes
    val = np.where(dark_holes, 0.02, val)
    col = ramp(stops, np.clip(val, 0, 1))
    if haze:
        col = hazed(col, haze)
    l.put_local(sl, inside, col)
    sub_ = l.rgb[sl]
    le, ri, up, dn = edges(inside)
    lit_edge = (le | up) & (gx < 0.35)
    sub_[lit_edge] = mix(sub_[lit_edge], hazed(RIM, haze), 0.6)
    sub_[(ri | dn) & (gx > -0.2)] = hazed(mix(hx(stops[0]), SHADOW, 0.3), haze)


def tree(l, x, base, h, w, kind="verde", seed=1, haze=0.0, lean=0.0, bark="oscura", clumps=10, trunk_w=None, tiers=3, flat=0.65, wobble=0.0, side=0.0):
    """Árbol con estructura: tronco con raíces, horqueta, ramas principales que salen
    hacia arriba y afuera, y una copa por rama más la de arriba (pisos), de atrás hacia
    adelante. Las ramas se ven en los huecos y debajo de cada piso."""
    rng = random.Random(seed)
    tw = trunk_w or max(3, w * 0.1)
    fork_y = base - h * 0.44
    fork_x = x + lean * h * 0.44
    stroke(l, x, base, fork_x, fork_y, tw, tw * 0.72, bark, seed, haze, wobble)
    for side in (-1, 1):                                 # raíces
        stroke(l, x + side * tw * 0.2, base - 3, x + side * tw * 1.1, base + 1, tw * 0.45, 1.5, bark, seed + 2 + side, haze)
    subs = []
    for k in range(tiers):
        f = (k / (tiers - 1) - 0.5) * 2 if tiers > 1 else 0.0
        ang = f * 0.95 * (1 - abs(side) * 0.4) + side * 0.55 + rng.uniform(-0.12, 0.12)
        L = h * rng.uniform(0.3, 0.42)
        ex = fork_x + math.sin(ang) * w * 0.4 + lean * L
        ey = fork_y - math.cos(ang) * L * 0.85
        mx_ = (fork_x + ex) / 2 + rng.uniform(-3, 3)
        my_ = (fork_y + ey) / 2 + rng.uniform(-2, 4)
        stroke(l, fork_x, fork_y, mx_, my_, tw * 0.62, tw * 0.45, bark, seed + 10 + k, haze)
        stroke(l, mx_, my_, ex, ey, tw * 0.45, tw * 0.25, bark, seed + 20 + k, haze)
        subs.append((ex, ey - h * 0.06, w * 0.56, h * 0.36))
    subs.append((fork_x + lean * h * 0.4, base - h * 0.8, w * 0.62, h * 0.4))
    for i, (sx, sy, sw, sh) in enumerate(sorted(subs, key=lambda p: p[1])):
        canopy(l, sx, sy, sw, sh, seed + 31 + i, kind, clumps, haze=haze, flat_bottom=flat)


def lenga_tree(l, x, base, h, w, seed=1):
    """Lenga patagónica barrida por el viento: tronco retorcido que se inclina a la
    derecha, ramas largas horizontales y follaje en pisos chatos con panza oscura."""
    rng = random.Random(seed)
    pts = [(x, base)]
    cx, cy = x, base
    for k in range(5):
        cx += rng.uniform(9, 15)
        cy -= h * 0.12
        pts.append((cx, cy))
    for k in range(len(pts) - 1):
        stroke(l, pts[k][0], pts[k][1], pts[k + 1][0], pts[k + 1][1], 13 - k * 2.2, 11 - k * 2.2, "roja", seed + k)
    tiers = []
    for k in range(1, len(pts)):
        px, py = pts[k]
        L = w * (0.55 - k * 0.05) * rng.uniform(0.8, 1.1)
        ex, ey = px + L, py - rng.uniform(2, 10)
        stroke(l, px, py, ex, ey, 6 - k * 0.8, 2, "roja", seed + 40 + k)
        if k % 2 == 0:
            stroke(l, px, py, px - L * 0.35, py - 6, 4, 1.5, "roja", seed + 60 + k)
            tiers.append((px - L * 0.3, py - 8, L * 0.55, 18))
        tiers.append((px + L * 0.55, ey - 6, L * 1.2, 30 - k * 2))
    for i, (tx, ty, tw_, th_) in enumerate(sorted(tiers, key=lambda t: t[1])):
        canopy(l, tx, ty, tw_, th_, seed + 80 + i, "lenga", 12, leaf=1.15, flat_bottom=0.6)


def ombu(l, x, base, h, w, seed=1):
    """Ombú: base con contrafuertes, tronco que se abre en cuatro ramas gruesas que
    entran en una copa ancha en pisos (las ramas se ven entre la copa y el tronco)."""
    pal = BARK["oscura"]
    hk = int(h * 0.3)
    for k in range(hk):
        yy = base - k
        t = k / hk
        half = w * 0.1 * (1.5 - t * 0.45) + 10 * math.exp(-k / 5.0)
        for dx in range(int(-half), int(half) + 1):
            u = dx / max(half, 1)
            rib = math.sin(dx * 0.8 + k * 0.04) * 0.16
            v = 0.62 - u * 0.62 + rib
            col = hx(pal[int(np.clip(round(v * 3), 0, 3))])
            if u < -0.8:
                col = mix(col, RIM, 0.45)
            if u > 0.85:
                col = mix(hx(pal[0]), SHADOW, 0.3)
            l.px(x + dx, yy, col)
    ty = base - hk
    limbs = ((-0.42, -0.42), (-0.16, -0.62), (0.14, -0.6), (0.42, -0.4))
    ends = []
    for k, (dx, dy) in enumerate(limbs):
        ex, ey = x + dx * w, base + dy * h
        mx_, my_ = x + dx * w * 0.45, ty - 6 + dy * 10
        stroke(l, x + dx * 12, ty + 4, mx_, my_, 11, 8, "oscura", seed + k)
        stroke(l, mx_, my_, ex, ey, 8, 4, "oscura", seed + 10 + k)
        ends.append((ex, ey))
    pieces = [(ends[0][0], ends[0][1] - 6, 0.62, 0.34), (ends[3][0], ends[3][1] - 6, 0.6, 0.33),
              (ends[1][0], ends[1][1] - 8, 0.64, 0.36), (ends[2][0], ends[2][1] - 8, 0.64, 0.36),
              (x, base - h * 0.82, 0.7, 0.34)]
    for i, (cx_, cy_, sw, sh) in enumerate(sorted(pieces, key=lambda p_: p_[1])):
        canopy(l, cx_, cy_, w * sw, h * sh, seed + 30 + i, "ombu", 12, flat_bottom=0.5)


def palm(l, x, base, h, seed=1, bend=0.12, haze=0.0, fronds=16, size=1.0):
    """Palmera pindó: tronco anillado curvo, corona llena de frondas arqueadas con
    folíolos colgantes y algunas hojas secas colgando."""
    rng = random.Random(seed)
    pal = BARK["palma"]
    tx, ty = x, base
    sgn = 1 if seed % 2 else -1
    for k in range(int(h)):
        t = k / h
        px = x + bend * h * t * t * sgn
        tx, ty = px, base - k
        hw = 2.6 * size * (1 - t * 0.25)
        for dx in range(int(-hw - 1), int(hw + 2)):
            u = dx / hw
            if abs(u) > 1:
                continue
            v = 0.66 - u * 0.62 - (0.3 if k % 5 == 0 else 0)
            col = hx(pal[int(np.clip(round(v * 3), 0, 3))])
            if u < -0.7:
                col = mix(col, RIM, 0.4)
            l.px(px + dx, base - k, hazed(col, haze))
    dead, dead2 = hazed(hx("#8A6A48"), haze), hazed(hx("#5A4234"), haze)
    for i in range(5):                                   # hojas secas colgando
        a = -math.pi / 2 + (i - 2) * 0.5
        for s in range(int(18 * size)):
            l.px(tx + math.cos(a) * s * 0.4 + (i - 2) * 2, ty + s, dead if s % 3 else dead2)
    cols = [hazed(hx(c), haze) for c in ("#18243A", "#2A4436", "#4E6A3A", "#9A9446", "#E6C470")]
    order = sorted(range(fronds), key=lambda i: math.sin(i / fronds * 2 * math.pi + seed))
    for i in order:
        a = i / fronds * 2 * math.pi + rng.uniform(-0.12, 0.12)
        back = math.sin(a + seed) < -0.2
        L = rng.uniform(30, 42) * size
        dirx = math.cos(a)
        lift = rng.uniform(0.45, 0.85)
        base_t = 0 if back else (3 if dirx < -0.3 else 2)
        for s in range(0, 46):
            t = s / 45
            fx = tx + dirx * L * t
            fy = ty - lift * L * t * 0.9 + (L * 0.9) * t * t
            l.px(fx, fy, cols[max(0, base_t - 1)])
            if s % 2 == 0 and 0.1 < t < 0.98:
                ll = int((1 - t * 0.7) * 11 * size + 2)
                for side in (-1, 1):
                    for q in range(ll):
                        qx = fx + side * q * 0.42 * (1 if abs(dirx) < 0.4 else 0.75)
                        qy = fy + q * 0.95
                        c = base_t
                        if side > 0 or back:
                            c = max(0, base_t - 1)
                        elif q < ll * 0.35:
                            c = min(4, base_t + 1)
                        l.px(qx, qy, cols[c])
    for k in range(4):
        l.px(tx + k - 1, ty + 3, hazed(hx("#C8742E"), haze))
        l.px(tx + k - 1, ty + 4, hazed(hx("#8A4A22"), haze))


def poplar(l, x, base, h, seed, haze=0.0, pal="alamo"):
    """Álamo en penacho (como la postal), luz a la izquierda."""
    stops = FOLIAGE[pal]
    win = l.local(x - h * 0.25, base - h - 2, x + h * 0.25, base + 2)
    if win is None:
        return
    sl, yy, xx = win
    r = h * 0.15
    u = (xx - x) / r
    t = np.clip((base - 3 - yy) / h, 0, 1)
    prof = np.sin(np.clip(t, 0, 1) * math.pi) ** 0.55 * (1 - t * 0.3)
    nz = fbm(xx / 2.5, yy / 3.5, seed, 3)
    m = (np.abs(u) < prof + (nz - 0.5) * 0.75) & (yy > base - 3 - h) & (yy < base - 3)
    lit = np.clip(0.62 - u * 0.55 + (nz - 0.5) * 1.0 - (1 - t) * 0.12, 0, 1)
    col = ramp(stops, np.round(lit * 5) / 5)
    if haze:
        col = hazed(col, haze)
    l.put_local(sl, m, col)
    l.rect(x, base - 5, x + 1, base, hazed(hx("#4E3638"), haze))


def boulder(l, cx, cy, rx, ry, seed, stops=("#2A2236", "#4A3E54", "#7A6672", "#B08C80", "#E8C29A")):
    win = l.local(cx - rx - 1, cy - ry - 1, cx + rx + 2, cy + ry + 2)
    if win is None:
        return
    sl, yy, xx = win
    nx, ny = (xx - cx) / rx, (yy - cy) / ry
    d2 = nx ** 2 + ny ** 2
    n = fbm(xx / 3, yy / 3, seed, 2) - 0.5
    m = (d2 <= 1 + n * 0.4) & (yy <= cy + ry * 0.55)
    nz = np.sqrt(np.clip(1 - d2, 0, 1))
    facet = np.round((nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2] + n * 0.3) * 3) / 3       # caras planas
    l.put_local(sl, m, ramp(list(stops), np.clip(facet, 0, 1)))


def grass_tufts(l, rng, n, y0, y1, x0=0, x1=W, cols=("#5E4A3E", "#A0804E", "#E2C27C", "#FFEAB0"), scale=1.0):
    for _ in range(n):
        cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
        k = (cy - y0) / max(1, (y1 - y0))
        hgt = int((3 + k * 9) * scale)
        for b in range(-3, 4):
            ang = b * 0.22 + rng.uniform(-0.1, 0.1)
            for j in range(hgt):
                t = j / max(1, hgt)
                px = cx + math.sin(ang) * j + ang * t * t * 4
                c = cols[3] if (b < 0 and t > 0.55) else (cols[2] if b <= 0 else (cols[1] if t > 0.3 else cols[0]))
                l.px(px, cy - j, hx(c))


def flowers(l, rng, n, y0, y1, cols, x0=0, x1=W):
    for _ in range(n):
        cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
        c = hx(rng.choice(cols))
        l.px(cx, cy, c)
        if (cy - y0) / max(1, y1 - y0) > 0.5:
            l.px(cx + 1, cy, c)
            l.px(cx, cy - 1, mix(c, hx("#FFFFFF"), 0.4))
            l.px(cx, cy + 1, hx("#2F4A34"))


def fern(l, x, y, size, seed, cols=("#1B3036", "#2C4C3A", "#4E6A3A", "#9A9446")):
    """Helecho: frondas en abanico, folíolos alternados."""
    rng = random.Random(seed)
    for a in range(-75, 76, 15):
        rad = math.radians(a - 90)
        L = size * rng.uniform(0.75, 1.0)
        for r in range(int(L)):
            t = r / L
            fx = x + math.cos(rad) * r
            fy = y + math.sin(rad) * r * 0.85 + t * t * L * 0.45
            l.px(fx, fy, hx(cols[1]))
            if r % 2 == 0 and t > 0.1:
                ll = int((1 - t) * 5 + 1)
                for q in range(ll):
                    l.px(fx - q * 0.7, fy + q * 0.6, hx(cols[3] if a < 0 and q < 2 else cols[2]))
                    l.px(fx + q * 0.7, fy + q * 0.6, hx(cols[0] if a > 0 else cols[1]))


def sprite(l, x, y, rows, pal, k=1):
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch in pal:
                l.rect(x + i * k, y + j * k, x + i * k + k - 1, y + j * k + k - 1, hx(pal[ch]))


def water(img, top, bottom, src_top, k=0.5, seed=1, tint="#7A6FB0", foam=0.0):
    """Agua: reflejo de lo de arriba en trazos horizontales largos (no punteado)."""
    m = (YY >= top) & (YY < bottom)
    ys = np.clip(2 * top - YY + (fbm(XX / 40, YY / 1.5, seed, 2) - 0.5) * 5, src_top, top - 1).astype(int)
    ref = img[ys, XX.astype(int)]
    col = mix(ref, hx(tint), k)
    col = mix(col, SHADOW, np.clip((YY - top) / (bottom - top), 0, 1) * 0.3)
    streak = fbm(XX / (8 + np.clip(YY - top, 0, 200) * 0.25), YY / (0.8 + np.clip(YY - top, 0, 200) * 0.02), seed + 1, 3)
    col = np.where((streak > 0.62)[..., None], mix(col, hx("#FFE6B8"), 0.45), col)
    col = np.where((streak < 0.3)[..., None], mix(col, SHADOW, 0.2), col)
    if foam:
        fm = (fbm(XX / 14, YY / 1.6, seed + 2, 3) > 0.66 - foam * 0.1)
        col = np.where(fm[..., None], hx("#FFF2E2"), col)
    return m, col


def jungle_hill(top, seed, haze, size, dens=1.0):
    """Loma cubierta de selva: base pareja y muchas copas chicas encima (más chicas y
    veladas cuanto más lejos)."""
    l = Layer()
    m = (YY >= top[None, :] + size * 0.4) & (YY < 760)
    l.put(m, hazed(ramp(["#16202E", "#1E3034", "#2C4638"], np.clip(fbm(XX / 6, YY / 6, seed, 2), 0, 1)), haze))
    rng = random.Random(seed)
    for _ in range(int(W / size * 3 * dens)):
        cx = rng.uniform(-size, W + size)
        cy = top[int(min(W - 1, max(0, cx)))] + rng.uniform(0, size * 1.6)
        canopy(l, cx, cy, size * rng.uniform(1.2, 1.8), size * rng.uniform(0.8, 1.1), int(cx * 13 + cy) + seed, "selva", 5, leaf=0.8, haze=haze)
    return l


def ruins(l, x, y, sun):
    """Ruinas jesuíticas de San Ignacio: fachada de piedra arenisca roja con portal en
    arco, pilastras, cornisa rota y pasto arriba. Luz a la izquierda."""
    w, h = 96, 46
    stone = fbm(XX / 2.5, YY / 2.5, 501, 2)
    block = (np.mod(YY - y, 5) == 0) | (np.mod(XX - x + np.floor((YY - y) / 5) * 4, 9) == 0)
    top = y - h + 6 * (fbm(XX / 7, np.full_like(XX, 1.0), 502, 2) - 0.5) * 2 - 8 * np.exp(-((XX - x - 30) / 10) ** 2)
    m = (XX >= x) & (XX <= x + w) & (YY >= top) & (YY <= y)
    v = 0.6 + (stone - 0.5) * 0.35 - block * 0.18 - (XX > x + w - 20) * 0.3 + glow(sun, 0.25)
    l.put(m, ramp(["#4A2228", "#7A3430", "#A84C38", "#CC6E48", "#E8966A"], np.clip(v, 0, 1)))
    for k, (ax, aw, ah) in enumerate(((x + 36, 24, 30), (x + 10, 12, 18), (x + 72, 12, 18))):
        arch = (((XX - ax - aw / 2) / (aw / 2)) ** 2 + ((YY - (y - ah + aw / 2)) / (aw / 2)) ** 2 <= 1) | ((XX >= ax) & (XX <= ax + aw) & (YY >= y - ah + aw / 2) & (YY <= y))
        l.put(arch & m, ramp(["#1E1420", "#3A2030"], (XX < ax + aw * 0.3).astype(float)))
        le, _, up, _ = edges(arch & m)
        l.rgb[le | up] = hx("#F0A878")
    for px in (x + 4, x + 30, x + 62, x + 88):          # pilastras
        l.rect(px, y - h + 10, px + 2, y, hx("#E8966A"))
        l.rect(px + 3, y - h + 10, px + 3, y, hx("#5A2A2E"))
    grass = m & (YY < top + 3)
    l.rgb[grass] = ramp(["#3A5A34", "#6E8A40"], (fbm(XX / 2, YY / 2, 503, 2) > 0.5).astype(float))[grass]
    le, _, up, _ = edges(m)
    l.rgb[le] = mix(l.rgb[le], RIM, 0.6)


def araucaria(l, x, base, h, seed, haze=0.0):
    """Pino Paraná: tronco recto alto y copa en candelabro (ramas que suben y terminan en
    penachos chatos)."""
    stroke(l, x, base, x, base - h * 0.82, max(3, h * 0.035), 2, "roja", seed, haze)
    rng = random.Random(seed)
    tops = []
    for k in range(7):
        a = -1.0 + k / 6 * 2.0
        L = h * rng.uniform(0.16, 0.24)
        ex, ey = x + math.sin(a) * L * 1.4, base - h * 0.78 - math.cos(a) * L * 0.6
        stroke(l, x, base - h * 0.7, ex, ey, 2.5, 1.5, "roja", seed + k, haze)
        tops.append((ex, ey))
    for k, (ex, ey) in enumerate(sorted(tops, key=lambda t: t[1])):
        canopy(l, ex, ey - 2, h * 0.16, h * 0.07, seed + 20 + k, "selva", 5, leaf=0.9, haze=haze, flat_bottom=0.4)


def sheep(l, x, y, k=2, seed=0):
    rows = [
        "..WWWWW..",
        ".WWWWWWWH",
        "LWWWWWWKK",
        ".WWWWWWW.",
        "..K.K.K..",
        "..K.K.K..",
    ]
    sprite(l, x, y, rows, {"W": "#F2E6D2", "L": "#FFF6E4", "H": "#2A2024", "K": "#3A2E30"}, k)
    l.rect(x + 1 * k, y + 1 * k, x + 2 * k, y + 3 * k, hx("#FFF8EC"))
    l.rect(x + 6 * k, y + 3 * k, x + 7 * k, y + 3 * k + k - 1, hx("#C8B49C"))


def silo(l, x, base, w, h):
    """Silo de chapa: cilindro con bandas, techo cónico, luz a la izquierda."""
    for dx in range(int(w)):
        u = (dx - w / 2) / (w / 2)
        v = 0.7 - u * 0.55
        col = ramp(["#5A5468", "#8A8696", "#BEB8C2", "#EAE2DE"], np.array(np.clip(v, 0, 1)))
        for yy in range(int(base - h), int(base)):
            c = col if (yy - base) % 7 else mix(col, hx("#4A4458"), 0.4)
            l.px(x + dx, yy, c)
        cone = h * 0.22 * (1 - abs(u))
        for yy in range(int(base - h - cone), int(base - h)):
            l.px(x + dx, yy, hx("#D8D0D4") if u < 0 else hx("#7A7488"))


# ------------------------------------------------------------------ NOA (la postal de inicio)

def noa():
    def ld(n):
        return Image.open(os.path.join(START, n)).convert("RGBA")
    base = ld("start_sky.png")
    for n in ("start_andes.png", "start_hills.png", "start_viaduct.png", "start_valley.png"):
        base.alpha_composite(ld(n))
    river = ld("start_river.png")
    base.alpha_composite(river.crop((0, 0, 480, river.height)), (0, 594 - river.height // 2))
    flag = ld("start_flag.png")
    fw = flag.width // 4
    base.alpha_composite(flag.crop((0, 0, fw, flag.height)), (299 - fw // 2, 592 - flag.height // 2))
    lla = ld("start_llama.png")
    lw, lh = lla.width // 4, lla.height // 2
    for x, y, f in ((132, 634, 0), (168, 640, 1), (150, 628, 0)):
        base.alpha_composite(lla.crop((0, f * lh, lw, (f + 1) * lh)), (x - lw // 2, y - lh // 2))
    base.alpha_composite(ld("start_road.png"))
    base.alpha_composite(ld("start_fore.png"))
    tuft = ld("start_tuft.png")
    tw = tuft.width // 3
    for x, y in ((112, 690), (300, 694), (176, 692), (350, 690)):
        base.alpha_composite(tuft.crop((0, 0, tw, tuft.height)), (x - tw // 2, y - tuft.height // 2))
    con = ld("start_condor.png")
    cw = con.width // 4
    base.alpha_composite(con.crop((0, 0, cw, con.height)), (250, 300))
    img = np.array(base.convert("RGB"), dtype=np.float64)
    out = img[:, 70:370].copy()
    # primer plano: pirca de piedras irregulares con luz arriba y sombra proyectada
    rng = random.Random(3)
    wall = Layer()
    top_w = 744 + 3 * np.sin(XX[0] / 23)
    wm = (YY >= top_w[None, :]) & (YY < 772) & (XX > 112)
    pts = [(rng.uniform(100, 310), rng.uniform(740, 776)) for _ in range(70)]
    best = np.full((H, W), 1e9)
    idx = np.zeros((H, W), dtype=int)
    second = np.full((H, W), 1e9)
    for i, (sx, sy) in enumerate(pts):
        d = np.hypot((XX - sx) * 0.8, (YY - sy) * 1.3)
        closer = d < best
        second = np.where(closer, best, np.minimum(second, d))
        idx = np.where(closer, i, idx)
        best = np.where(closer, d, best)
    mortar = (second - best) < 1.1
    stone_v = np.array([rng.random() for _ in pts])[idx]
    centers_y = np.array([p[1] for p in pts])[idx]
    lit = np.clip(0.4 + stone_v * 0.35 + (centers_y - YY) / 10, 0, 1)
    col = ramp(["#3A2A38", "#5E4652", "#8A6A68", "#B8907C", "#E2BC98"], lit)
    col = np.where(mortar[..., None], hx("#2A1E2A"), col)
    wall.put(wm, col)
    le, _, up, _ = edges(wm)
    wall.rgb[up] = hx("#F2CC9A")
    shadow_on(out, 240, 775, 140, 4, 0.5)
    fl = P.Layer()                                         # cardones grandes de primer plano
    P.cardon(fl, 98, 868, 150, 7.5, 3)
    P.cardon(fl, 330, 812, 96, 5.0, 4)
    cl = Layer()
    sub = fl.a[:, 70:370]
    cl.put(sub, fl.rgb[:, 70:370])
    ribs = cl.a & (np.mod(XX, 3) == 0)
    cl.rgb[ribs] = mix(cl.rgb[ribs], hx("#24303A"), 0.35)
    rim_light(cl, k=0.7, dark=SHADOW)
    for cx_, h_ in ((28, 150), (260, 96)):
        long_shadow(out, cx_, 868 if cx_ < 100 else 812, h_ * 0.6, 20, 0.35)
    l = Layer()
    pc = 176 - (YY - 684) * 0.62 - ((YY - 684) / 216) ** 2 * 30
    sand = (YY > 684) & (np.abs(XX - pc) < 1 + (YY - 684) * 0.12 + (fbm(XX / 3, YY / 3, 8, 2) - 0.5) * (2 + (YY - 684) * 0.05))
    l.put(sand, ramp(["#8A6A5A", "#B48A6E", "#D8AE86", "#F0CC9E"], np.clip(0.55 + (fbm(XX / 3, YY / 3, 7, 2) - 0.5) * 0.6, 0, 1)))
    for gx_, gy_ in ((150, 800), (190, 830), (250, 870), (30, 880), (120, 890), (280, 740)):
        grass_tufts(l, rng, 9, gy_ - 10, gy_ + 6, gx_ - 18, gx_ + 18, cols=("#5A4A3A", "#9A7A4E", "#D8B46E", "#F6DE9A"), scale=1.35)
    for bx_, by_, rx_ in ((210, 850, 16), (240, 868, 10), (40, 760, 8), (270, 796, 7)):
        shadow_on(out, bx_ + rx_ * 1.2, by_ + rx_ * 0.4, rx_ * 1.5, rx_ * 0.3, 0.4)
        boulder(l, bx_, by_, rx_, rx_ * 0.7, bx_)
    flowers(l, rng, 30, 730, 900, ["#F2D04A", "#E86A5C", "#F2F0E0"])
    warm = (YY > 820) & (fbm(XX / 30, YY / 10, 9, 3) > 0.6) & ~l.a
    out[warm] = mix(out[warm], hx("#D89A6E"), 0.35)
    for bx_, by_, rx_ in ((150, 884, 12), (276, 880, 9), (96, 846, 6)):
        shadow_on(out, bx_ + rx_ * 1.2, by_ + rx_ * 0.4, rx_ * 1.5, rx_ * 0.3, 0.4)
        boulder(l, bx_, by_, rx_, rx_ * 0.7, bx_ + 1)
    return comp([out, wall, l, cl])


# ------------------------------------------------------------------ NEA: Garganta del Diablo

def nea():
    """Misiones: lomas de selva, ruinas jesuíticas de San Ignacio, araucarias y un yerbal
    en hileras sobre tierra colorada, con el camino rojo que lleva a las ruinas."""
    sun = (-40, 410)
    s = sky(11, sun)
    x = XX[0]
    far = jungle_hill(520 - 30 * P.line1(x, 71, 70, 3), 71, 0.5, 6)
    mid = jungle_hill(566 - 36 * P.line1(x, 72, 60, 3) - 10 * np.exp(-((x - 60) / 40) ** 2), 72, 0.28, 9)
    near = jungle_hill(612 - 18 * P.line1(x, 73, 50, 3), 73, 0.1, 12, 0.8)
    rui = Layer()
    ruins(rui, 150, 650, sun)
    trees = Layer()
    araucaria(trees, 44, 648, 140, 81, 0.15)
    araucaria(trees, 112, 640, 96, 82, 0.3)
    araucaria(trees, 276, 652, 170, 83, 0.08)
    hor, vx = 652, 196
    dep = np.clip(YY - hor, 0.5, None)
    u = (XX - vx) / dep
    row = np.mod(u * 5.5, 1.0)
    leafp = fbm(XX / 2.2, YY / 2.2, 51, 2)
    bump = np.abs(np.sin(YY * (0.9 - dep * 0.0025) + np.floor(u * 5.5) * 1.3))       # matas redondas en hilera
    hedge = row < 0.5 * (0.6 + 0.4 * bump) + (leafp - 0.5) * 0.15
    n = fbm(XX / 3, YY / 2, 52, 2)
    earth = ramp(["#4A1E1E", "#7A2E24", "#A8442C", "#C8603A", "#E08A5A"], np.clip(0.55 + (n - 0.5) * 0.5 - dep / 800 + glow(sun, 0.3), 0, 1))
    side = np.clip(row / 0.5, 0, 1)
    gv = np.clip(0.8 - side * 0.65 + (leafp - 0.5) * 0.7 + glow(sun, 0.25), 0, 1)
    col = np.where(hedge[..., None], ramp(FOLIAGE["verde"], gv), earth)
    col = np.where(((~hedge) & (row < 0.66))[..., None], mix(col, SHADOW, 0.35), col)
    flat = mix(mix(hx("#4E6A3A"), hx("#A8442C"), 0.4), HAZE, 0.25)
    farz = np.clip((dep - 20) / 40, 0, 1)
    col = mix(flat * np.ones_like(col), col, farz)
    col = hazed(col, np.clip(1 - dep / 40, 0, 1) * 0.45)
    yerbal = Layer()
    yerbal.put(YY >= hor, col)
    road = Layer()
    rc = vx + (YY - hor) * -0.18 - ((YY - hor) / 250) ** 2 * 70
    rw = 1 + (YY - hor) * 0.1
    rm = (YY > hor + 2) & (np.abs(XX - rc) < rw)
    road.put(rm, ramp(["#7A2E24", "#A8442C", "#C8603A", "#E8925E"], np.clip(0.6 + (fbm(XX / 4, YY / 2, 54, 2) - 0.5) * 0.6 - (XX - rc) / np.maximum(rw, 1) * 0.3, 0, 1)))
    pre = comp([s, far, mid, near, trees, rui, yerbal, road])
    shadow_on(pre, 150 + 96 + 24, 652, 40, 3, 0.4)
    fg = Layer()                                         # matas de yerba de primer plano con hojas
    for cx_, cy_, w_ in ((20, 846, 120), (290, 870, 110), (60, 900, 90)):
        shadow_on(pre, cx_ + w_ * 0.5, cy_ + w_ * 0.22, w_ * 0.6, 6, 0.45)
        canopy(fg, cx_, cy_, w_, w_ * 0.55, int(cx_) + 91, "verde", 14, leaf=1.2, flat_bottom=0.6)
    return comp([pre, fg])


# ------------------------------------------------------------------ Cuyo: Aconcagua y viñedos

def cuyo():
    sun = (-50, 420)
    s = sky(21, sun)
    x = XX[0]
    t = 470 - 64 * P.line1(x, 31, 80, 3) - 28 * np.abs(2 * P.line1(x, 32, 34, 3) - 1)
    back = rock(t, 33, "#4E4A92", "#C98AA0", 640, haze=np.clip((YY - 420) / 160, 0, 1) * 0.6, snow=448, sun=sun, gully=0.2)
    # Aconcagua: macizo asimétrico, dos cumbres, ladera oeste (izquierda) larga y al sol
    peak = 600 - 236 * np.exp(-((x - 172) / np.where(x < 172, 118.0, 86.0)) ** 2) \
        - 86 * np.exp(-((x - 80) / 40) ** 2) - 18 * np.abs(2 * P.line1(x, 34, 18, 3) - 1) - 4 * P.line1(x, 35, 5, 2)
    summit = 356 + 0.0035 * (x - 174) ** 2 - 9 * np.exp(-((x - 150) / 12) ** 2) - 6 * np.exp(-((x - 204) / 12) ** 2)
    peak = np.maximum(peak, summit)
    acon = rock(peak, 36, "#3E3478", "#F09C86", 640, haze=np.clip((YY - 460) / 140, 0, 1) * 0.5, snow=420, sun=sun, scale=10, gully=0.45,
                snow_lo="#7E74C0", snow_hi="#FFF2DE")
    t2 = 586 - 24 * P.line1(x, 39, 70, 3) - 4 * P.line1(x, 40, 9, 2)
    foot = rock(t2, 41, "#4E3462", "#D08C5C", 690, haze=0.26, sun=sun, scale=8, gully=0.3)
    trees = Layer()                                      # cortina de álamos dorados
    for i, px0 in enumerate(range(2, W, 7)):
        if 150 < px0 < 242:
            continue
        poplar(trees, px0, 632 + (i % 3), 46 + (i * 13) % 20, 300 + i, haze=0.12)
    bod = Layer()                                        # bodega de adobe con galería
    bx, by, bw, bh = 152, 598, 88, 36
    adobe = tones(fbm(XX / 3, YY / 3, 41, 2), 3)
    mm = (XX >= bx) & (XX <= bx + bw) & (YY >= by) & (YY <= by + bh)
    bod.put(mm, mix(hx("#C27E4E"), hx("#F6D09A"), np.clip(adobe * 0.5 + glow(sun, 0.5) * 0.7, 0, 1)))
    bod.put(mm & (XX > bx + bw - 22), mix(hx("#7A4A4E"), hx("#A06A5A"), adobe))
    for k in range(-4, bw + 5):
        for j in range(9):
            c = "#C0563E" if (j % 3) else "#7A3030"
            if (k + j) % 4 == 0:
                c = "#E8865A"
            if k > bw - 22:
                c = "#8A3A34" if (j % 3) else "#5A2428"
            bod.px(bx + k, by - j, hx(c))
    bod.rect(bx - 5, by, bx + bw + 5, by + 1, hx("#4A2024"))
    for k in range(5):
        ax = bx + 8 + k * 16
        bod.put(((XX - ax - 5) ** 2 / 25 + (YY - by - 16) ** 2 / 64 < 1) | ((XX >= ax) & (XX <= ax + 10) & (YY >= by + 16) & (YY <= by + bh)), hx("#3A2230"))
        bod.rect(ax, by + 16, ax + 1, by + bh, hx("#6A4048"))
    bod.rect(bx + 38, by - 22, bx + 48, by - 9, hx("#F2D4A4"))
    bod.rect(bx + 46, by - 22, bx + 48, by - 9, hx("#B88A6A"))
    bod.rect(bx + 42, by - 18, bx + 44, by - 14, hx("#6A4A3A"))
    for bxx in (bx - 14, bx - 5, bx + bw + 4):
        bod.put(ell_mask(bxx + 4, by + bh - 3, 4.5, 3.8), hx("#8A5432"))
        bod.put(ell_mask(bxx + 3, by + bh - 4, 2.2, 1.8), hx("#C08A50"))
        bod.rect(bxx, by + bh - 5, bxx + 8, by + bh - 5, hx("#3D2A22"))
        bod.rect(bxx, by + bh - 1, bxx + 8, by + bh - 1, hx("#3D2A22"))
    vine = Layer()                                       # viñedo en perspectiva
    hor, vx = 640, 196
    dep = np.clip(YY - hor, 0.5, None)
    u = (XX - vx) / dep
    row = np.mod(u * 6.5, 1.0)
    leafp = fbm(XX / 2.2, YY / 2.2, 51, 2)
    hedge = row < 0.42 + (leafp - 0.5) * 0.25
    n = fbm(XX / 3, YY / 2, 52, 2)
    earth = ramp(["#4E3238", "#6E4440", "#9A6450", "#C48A5E", "#E8B07A"], np.clip(0.5 + (n - 0.5) * 0.5 - dep / 700 + glow(sun, 0.3), 0, 1))
    side = np.clip(row / 0.42, 0, 1)
    gv = np.clip(0.78 - side * 0.65 + (leafp - 0.5) * 0.8 + glow(sun, 0.3), 0, 1)
    green = ramp(FOLIAGE["parra"], gv)
    col = np.where(hedge[..., None], green, earth)
    col = np.where(((~hedge) & (row < 0.62))[..., None], mix(col, SHADOW, 0.35), col)
    grape = hedge & (fbm(XX / 1.2, YY / 1.2, 53, 1) > 0.8) & (dep > 60) & (side > 0.3)
    col[grape] = hx("#4A2458")
    flat = mix(mix(hx("#6E7A44"), hx("#B08A5E"), 0.45), HAZE, 0.25)            # lejos: tono parejo
    farz = np.clip((dep - 28) / 46, 0, 1)
    col = mix(flat * np.ones_like(col), col, farz)
    col = hazed(col, np.clip(1 - dep / 40, 0, 1) * 0.45)
    vine.put(YY >= hor, col)
    road = Layer()
    rc = 196 + (YY - hor) * -0.25 - ((YY - hor) / 260) ** 2 * 90
    rw = 1 + (YY - hor) * 0.09
    rm = (YY > hor + 2) & (np.abs(XX - rc) < rw)
    road.put(rm, ramp(["#A0704A", "#C8925E", "#E8B880", "#F6D4A0"], np.clip(0.6 + (fbm(XX / 4, YY / 2, 54, 2) - 0.5) * 0.6 - (XX - rc) / np.maximum(rw, 1) * 0.3, 0, 1)))
    for k in range(-12, 13):                             # postes de la espaldera
        for yy in range(hor + 40, H, 38):
            d = yy - hor
            px0 = int(vx + (k + 0.21) / 6.5 * d)
            hgt = int(d * 0.09) + 2
            vine.rect(px0, yy - hgt, px0, yy, hx("#4A3326"))
            vine.px(px0 - 1, yy - hgt, hx("#B08A6A"))
    pre = comp([s, back, acon, foot, trees, bod, vine, road])
    shadow_on(pre, bx + bw + 30, by + bh + 2, 40, 3, 0.4)
    fg = Layer()                                         # racimos colgando en las hileras cercanas
    rngv = random.Random(61)
    for _ in range(260):
        gx, gy = rngv.uniform(0, W), rngv.uniform(760, 900)
        d_ = gy - hor
        uu = (gx - vx) / d_ * 6.5
        if not (0.3 < (uu % 1.0) < 0.42):
            continue
        n_ = int(2 + d_ / 80)
        for rr in range(n_):
            for c_ in range(-(n_ - rr) // 2, (n_ - rr) // 2 + 1):
                fg.px(gx + c_, gy + rr, hx("#3A1A4E") if c_ >= 0 else hx("#7A4A92"))
    stroke(fg, 14, 905, 30, 830, 8, 6, "oscura", 81)             # poste cabecero inclinado, madera gastada
    for wy0 in (838, 856):                                # dos alambres que bajan hacia la hilera
        for xx_ in range(26, 150):
            fg.px(xx_, wy0 + (xx_ - 26) * 0.32 + math.sin((xx_ - 26) / 40 * math.pi) * 3, hx("#9A92A0"))
    for k in range(14):                                  # seto bajo y continuo sobre los alambres
        cx_ = 34 + k * 8
        cy_ = 840 + (cx_ - 26) * 0.32
        canopy(fg, cx_, cy_, 22 - k * 0.5, 12 - k * 0.2, 83 + k, "parra", 5, leaf=1.25, flat_bottom=0.6)
    for gx, gy in ((30, 848), (49, 851), (77, 865), (103, 872), (122, 880)):
        for rr in range(7):
            for c_ in range(-3 + rr // 2, 4 - rr // 2):
                fg.rect(gx + c_ * 2, gy + rr * 2, gx + c_ * 2 + 1, gy + rr * 2 + 1, hx("#3A1A4E") if c_ > 0 else hx("#6E3E86"))
            fg.px(gx - 2 + rr % 2, gy + rr * 2, hx("#C8A0DC"))
    return comp([pre, fg])


# ------------------------------------------------------------------ Patagonia: Fitz Roy, glaciar y estepa

def granite(towers, sun, base_y=600):
    """Agujas de granito: punta filosa, paredes casi verticales, caras planas inclinadas
    (izquierda al sol, derecha violeta), grietas en los cambios de cara, filo cálido."""
    l = Layer()
    x = XX[0]
    top = np.full(W, 1e9)
    owner = np.zeros(W, dtype=int)
    for i, (c, hw, t) in enumerate(towers):
        u = np.abs(x - c) / hw
        jag = 3 * np.abs(((x * 0.43 + i * 1.7) % 2) - 1)
        prof = np.where(u < 1.35, t + u ** 1.1 * hw * 2.4 + jag, 1e9)
        better = prof < top
        owner = np.where(better, i, owner)
        top = np.minimum(top, prof)
    top = np.minimum(top, base_y)
    m = (YY >= top[None, :]) & (YY < base_y)
    cs = np.array([t[0] for t in towers], dtype=float)[owner][None, :]
    hws = np.array([t[1] for t in towers], dtype=float)[owner][None, :]
    tops = np.array([t[2] for t in towers], dtype=float)[owner][None, :]
    xn = (XX - cs) / hws
    facet = np.floor(xn * 1.6 + (YY - tops) / hws * 0.28 + (fbm(XX / 9, YY / 30, 66, 2) - 0.5) * 0.8)
    v = 0.6 - np.clip(facet, -3, 3) * 0.12 - (YY - tops) / 1100
    seam = np.zeros_like(m)
    seam[:, 1:] = facet[:, 1:] != facet[:, :-1]
    v = np.where(seam, v - 0.2, v)
    col = ramp(["#1E1E46", "#2E3068", "#4E4482", "#8E5E86", "#D88C80", "#FFC696"], np.clip(v, 0, 1))
    col = hazed(col, np.clip((YY - 430) / 190, 0, 1) * 0.42)
    l.put(m, col)
    le, ri, up, _ = edges(m)
    l.rgb[le | up] = mix(l.rgb[le | up], hx("#FFE2B4"), 0.75)
    l.rgb[ri] = mix(l.rgb[ri], hx("#1A1840"), 0.4)
    return l


def patagonia():
    """Patagonia: agujas del Fitz Roy a lo lejos detrás del lago, estancia con galpón y
    cortina de álamos, estepa con majada de ovejas, la ruta 40 de ripio y el alambrado."""
    sun = (-60, 430)
    stops = [(0, "#1F2A63"), (140, "#3B4790"), (240, "#6E5AA6"), (310, "#B8668C"), (370, "#E8906A"), (430, "#F7C27A"), (490, "#FFE6B0"), (900, "#FFE6B0")]
    s = sky(31, sun, stops)
    x = XX[0]
    far = rock(560 - 50 * P.line1(x, 60, 50, 3), 61, "#4A4A8E", "#C890A8", 640, haze=0.5, snow=540, sun=sun, scale=9)
    towers = [(160, 22, 352), (124, 9, 410), (138, 7, 436), (198, 10, 418), (216, 8, 452), (96, 10, 470), (240, 12, 486)]
    fitz = granite(towers, sun, base_y=612)
    for k in range(3):
        fitz.rgb[fitz.a] = hazed(fitz.rgb[fitz.a], 0.06)
    hills = rock(610 - 16 * P.line1(x, 62, 60, 3), 63, "#3A3456", "#A07A78", 650, haze=0.3, snow=596, sun=sun, scale=10, snow_lo="#8E86C4", snow_hi="#F4ECE6", gully=0.3)
    pre = comp([s, far, fitz, hills])
    lake = Layer()
    m, col = water(pre, 630, 668, 420, 0.5, 71, "#2E8CA8")
    lake.put(m, col)
    pre = comp([pre, lake])
    steppe = ground(666, 72, ["#4E3E3E", "#7A5E48", "#B08A58", "#D8B070", "#F2D592"], sun=sun, haze_k=0.4)
    road = Layer()
    rc = 208 - (YY - 668) * 0.62 + ((YY - 668) / 230) ** 2 * 30
    rw = 1.5 + (YY - 668) * 0.12
    rm = (YY > 669) & (np.abs(XX - rc) < rw)
    road.put(rm, ramp(["#6A5A66", "#9A8A88", "#C8B4A4", "#EAD6C0"], np.clip(0.6 + (fbm(XX / 2, YY / 2, 82, 2) - 0.5) * 0.9 - (XX - rc) / np.maximum(rw, 1) * 0.3, 0, 1)))
    gnd = comp([pre, steppe, road])
    est = Layer()                                        # estancia: álamos, casa y galpón
    for i, px0 in enumerate(range(196, 300, 6)):
        poplar(est, px0, 662 + (i % 2), 40 + (i * 7) % 12, 600 + i, haze=0.1, pal="verde")
    hx0, hy0 = 206, 648
    est.rect(hx0, hy0, hx0 + 26, hy0 + 14, hx("#F4EADC"))
    est.rect(hx0 + 20, hy0, hx0 + 26, hy0 + 14, hx("#B8A8B8"))
    for k in range(-2, 29):
        for j in range(6):
            est.px(hx0 + k, hy0 - j, hx("#C0503C" if k < 20 else "#7A3030"))
    est.rect(hx0 + 5, hy0 + 5, hx0 + 8, hy0 + 9, hx("#3A3048"))
    est.rect(hx0 + 13, hy0 + 5, hx0 + 16, hy0 + 14, hx("#5A3A3A"))
    gx0 = 240
    est.rect(gx0, hy0 + 2, gx0 + 34, hy0 + 14, hx("#A8A4B0"))
    for k in range(0, 34, 3):
        est.rect(gx0 + k, hy0 + 2, gx0 + k, hy0 + 14, hx("#7A7688"))
    for k in range(-2, 37):
        for j in range(5):
            est.px(gx0 + k, hy0 + 2 - j + abs(k - 17) * 0.0, hx("#A8483C" if j % 2 else "#C05A44"))
    rim_light(est, k=0.4)
    shadow_on(gnd, 240, 664, 46, 3, 0.4)
    fence = Layer()
    for i in range(14):
        t = i / 13
        fx = 236 - t * 250 + 0
        fy = 670 + t * 230
        hh = 6 + t * 30
        fence.rect(fx, fy - hh, fx + max(1, t * 3), fy, hx("#4A3326"))
        fence.rect(fx, fy - hh, fx, fy, hx("#A07A5A"))
    for wk in (0.45, 0.75):
        for i in range(400):
            t = i / 399
            fence.px(236 - t * 250, 670 + t * 230 - (6 + t * 30) * wk, hx("#8A7A7A"))
    flock = Layer()
    rng = random.Random(41)
    pts = sorted([(rng.uniform(120, 290), rng.uniform(690, 780)) for _ in range(26)], key=lambda p_: p_[1])
    for fx, fy in pts:
        k = 1 if fy < 730 else 2
        shadow_on(gnd, fx + 8 * k, fy + 6 * k, 6 * k, 1.2 * k, 0.4)
        sheep(flock, fx, fy, k, int(fx))
    flora = Layer()
    grass_tufts(flora, rng, 110, 680, 900, scale=1.15)
    for _ in range(7):
        cx, cy = rng.uniform(0, 110), rng.uniform(760, 892)
        r = 5 + (cy - 740) / 24
        shadow_on(gnd, cx + r * 1.4, cy + r * 0.2, r * 1.6, r * 0.3, 0.4)
        canopy(flora, cx, cy - r * 0.5, r * 2.4, r * 1.5, int(cx * 3 + cy), "algarrobo", 6, leaf=1.3, flat_bottom=0.6)
    for bx_, by_, rx_ in ((40, 880, 14), (70, 896, 9)):
        shadow_on(gnd, bx_ + rx_ * 1.3, by_ + rx_ * 0.4, rx_ * 1.6, rx_ * 0.3, 0.45)
        boulder(flora, bx_, by_, rx_, rx_ * 0.72, bx_)
    return comp([gnd, est, fence, flock, flora])


# ------------------------------------------------------------------ Pampeana

def pampeana():
    """Pampa: horizonte bajo con montes de eucaliptos, silos y galpón; potrero con vacas,
    molino y bebedero; el ombú; trigal en surcos con la huella hacia los silos."""
    sun = (-40, 470)
    s = sky(41, sun, clouds=0.85, horizon=650)
    stratus(s, 44, 600, 10)
    band = (YY > 620) & (YY < 652)
    s.rgb[band] = mix(s.rgb[band], hx("#FFE6B0"), 0.35)
    far = Layer()
    x = XX[0]
    far.put((YY >= 646) & (YY < 662), hazed(hx("#6A5A8E"), 0.5))
    for i, (cx, hh) in enumerate(((10, 54), (24, 66), (38, 58), (52, 48), (250, 60), (266, 74), (282, 64), (296, 52))):
        tree(far, cx, 652, hh, 28, "eucalipto", 45 + i, haze=0.4, bark="clara", clumps=6, trunk_w=2, tiers=3, flat=0.9)
    sil = Layer()
    for k, (sx, sw, sh) in enumerate(((176, 14, 44), (192, 14, 50), (208, 14, 44), (226, 10, 32))):
        silo(sil, sx, 652, sw, sh)
    sil.rect(203, 590, 205, 652, hx("#6A6478"))           # elevador
    sil.rect(199, 586, 209, 592, hx("#8A8496"))
    for yy in range(592, 640, 6):
        sil.rect(205, yy, 206, yy + 2, hx("#4A4458"))
    sil.rect(130, 636, 162, 652, hx("#A8402E"))           # galpón rojo
    sil.rect(150, 636, 162, 652, hx("#7A2E26"))
    for k in range(-2, 35):
        sil.px(130 + k, 636 - abs(k - 16) * 0.35, hx("#E8D8CC"))
    sil.rect(140, 642, 148, 652, hx("#4A2028"))
    for k in sil.rgb[sil.a].shape[:1]:
        pass
    sil.rgb[sil.a] = hazed(sil.rgb[sil.a], 0.18)
    rim_light(sil, k=0.4)
    pasture = ground(656, 46, ["#2E4434", "#466238", "#6E843E", "#A8A852", "#D8C878"], sun=sun, haze_k=0.5, bottom=716)
    wheat = ground(714, 47, ["#6A3A30", "#9A5A38", "#C88446", "#EAAE58", "#F8D88E"], sun=sun, vx=200, rows=1.0, row_n=10)
    road = Layer()
    for off in (-1, 1):
        rc = 200 - (YY - 656) * 0.6 + off * (1.5 + (YY - 656) * 0.06)
        rm = (YY > 658) & (np.abs(XX - rc) < 1 + (YY - 656) * 0.025)
        road.put(rm, ramp(["#7A4A3A", "#A8704E", "#D49C70"], np.clip(fbm(XX / 3, YY / 3, 48, 2), 0, 1)))
    gnd = comp([s, far, sil, pasture, wheat, road])
    mol = Layer()                                        # molino
    mx, mb, mt = 134, 704, 590
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    d.line([(mx - 2, mt), (mx - 12, mb)], fill=255, width=1)
    d.line([(mx + 2, mt), (mx + 12, mb)], fill=150, width=1)
    for k in range(0, mb - mt, 12):
        y0, y1 = mt + k, min(mb, mt + k + 12)
        h0, h1 = 2 + (y0 - mt) / (mb - mt) * 10, 2 + (y1 - mt) / (mb - mt) * 10
        d.line([(mx - h0, y0), (mx + h1, y1)], fill=200)
        d.line([(mx - h0, y0), (mx + h0, y0)], fill=255)
    arr = np.array(img)
    mol.put(arr == 255, hx("#2E2840"))
    mol.put(arr == 200, hx("#E8A070"))
    mol.put(arr == 150, hx("#4E4660"))
    hub = (mx, mt - 4)
    for i in range(16):
        a = i / 16 * 2 * math.pi
        for r in range(3, 19):
            mol.px(hub[0] + math.cos(a) * r, hub[1] + math.sin(a) * r * 0.95, hx("#F6E2CC" if (i % 2 and math.cos(a) < 0.3) else ("#C8A8A0" if i % 2 else "#8A7A8A")))
    for r in (9, 18):
        for k in range(120):
            a = k / 120 * 2 * math.pi
            mol.px(hub[0] + math.cos(a) * r, hub[1] + math.sin(a) * r * 0.95, hx("#5A4A62"))
    mol.put(ell_mask(hub[0], hub[1], 3, 3), hx("#2E2840"))
    for k in range(14):
        mol.px(hub[0] + 3 + k, hub[1], hx("#2E2840"))
    mol.rect(hub[0] + 16, hub[1] - 5, hub[0] + 19, hub[1] + 3, hx("#E2C8B8"))
    mol.put(ell_mask(156, 706, 14, 3.5), hx("#4E5A80"))
    mol.put(ell_mask(156, 705, 12, 2), hx("#F6D4A0"))
    long_shadow(gnd, mx, mb, 90, 24, 0.3)
    cows = Layer()
    cow = [
        "..BB...........",
        ".WWB.BBBBBBBB..",
        "WWWBBLLBBBBBBB.",
        "WWWBBBWWBBBBBBT",
        ".BBBBWWWWBBBBD.",
        "..BBB.....BBD..",
        "..B.B.....B.D..",
        "..B.B.....B.D..",
    ]
    for cx, cy, k in ((176, 672, 1), (198, 678, 1), (240, 668, 1), (256, 676, 1), (214, 690, 2), (166, 694, 2)):
        long_shadow(gnd, cx + 4 * k, cy + 8 * k, 14 * k, 12, 0.4)
        sprite(cows, cx, cy, cow, {"B": "#7A3A26", "L": "#B8643E", "W": "#F2E6D8", "T": "#4A2418", "D": "#4A2418"}, k=k)
    fence = Layer()
    for px0 in range(-10, W + 20, 20):
        fence.rect(px0, 700, px0 + 1, 716, hx("#3E2A26"))
        fence.rect(px0, 700, px0, 716, hx("#A07A5A"))
    for wy in (704, 710):
        for xx in range(W):
            fence.px(xx, wy, hx("#8A7A7A"))
    long_shadow(gnd, 40, 716, 150, 120, 0.45)
    om = Layer()
    ombu(om, 40, 716, 150, 130, 49)
    fg = Layer()
    rng = random.Random(46)
    for _ in range(200):
        cx, cy = rng.uniform(-4, W + 4), rng.uniform(800, 905)
        hh = int(14 + (cy - 796) * 0.32)
        lean = rng.uniform(-0.25, 0.08)
        for j in range(hh):
            fg.px(cx + lean * j, cy - j, hx("#9A6A36") if j < hh * 0.5 else hx("#D8A250"))
        for j in range(5):
            ex, ey = cx + lean * (hh + j * 2), cy - hh - j * 2
            fg.px(ex - 1, ey, hx("#FFE2A0"))
            fg.px(ex + 1, ey, hx("#B07A3A"))
            fg.px(ex, ey - 1, hx("#F2C46A"))
    flowers(fg, rng, 40, 760, 900, ["#B86AC8", "#8A4EA8", "#F2F0E0"])
    return comp([gnd, mol, cows, fence, om, fg])


# ------------------------------------------------------------------ Centro

def combine(l, x, y, k=2):
    """Cosechadora vista de costado avanzando a la izquierda: cabezal ancho con molinete,
    cabina alta vidriada, tolva de grano, tubo de descarga plegado, escape, rueda grande
    adelante y chica atrás. Luz a la izquierda."""
    R, RL, RD = hx("#C8403A"), hx("#F07A5E"), hx("#7A2228")
    Y, YD = hx("#F2C23A"), hx("#A8781E")
    K, O, X = hx("#221C26"), hx("#6A6474"), hx("#D8D8E0")

    def box_(x0, y0, x1, y1, c):
        l.rect(x + x0 * k, y + y0 * k, x + x1 * k + k - 1, y + y1 * k + k - 1, c)

    def wheel(cx, cy, r):
        for yy in range(-r, r + 1):
            for xx in range(-r, r + 1):
                d = math.hypot(xx, yy)
                if d <= r + 0.3:
                    c = K if d > r * 0.55 else (X if d < r * 0.2 else O)
                    if d > r * 0.55 and xx < -r * 0.4 and yy < 0:
                        c = hx("#4A4250")
                    l.rect(x + (cx + xx) * k, y + (cy + yy) * k, x + (cx + xx) * k + k - 1, y + (cy + yy) * k + k - 1, c)

    box_(19, 6, 47, 16, RD)                              # lateral en sombra (vista de tres cuartos)
    box_(30, 1, 45, 6, RD)
    box_(3, 11, 18, 17, YD)
    box_(16, 9, 44, 19, R)                               # cuerpo
    box_(16, 9, 18, 19, RL)
    box_(42, 9, 44, 19, RD)
    box_(20, 13, 30, 14, RD)                             # rejilla
    box_(27, 1, 43, 9, K)                                # tolva con contorno
    box_(28, 3, 42, 9, R)
    box_(28, 3, 42, 3, RL)
    box_(41, 3, 42, 9, RD)
    box_(17, 0, 27, 9, K)                                # cabina
    box_(18, 1, 26, 8, hx("#9CC8E8"))
    box_(18, 1, 20, 8, hx("#D8F0FF"))
    box_(16, 0, 27, 0, hx("#F2E8E0"))
    box_(18, -2, 29, -1, hx("#D8CCC4"))                # techo de la cabina
    box_(30, 1, 44, 2, RL)
    box_(36, 0, 37, 3, O)                                # escape
    for i in range(16):                                  # tubo de descarga plegado sobre la tolva
        box_(28 + i * 0.9, 2 - (i > 12), 29 + i * 0.9, 2 - (i > 12), hx("#B8B0B8"))
    box_(0, 14, 15, 20, Y)                               # cabezal
    box_(0, 14, 15, 14, hx("#FFE08A"))
    box_(0, 20, 15, 20, YD)
    for i in range(0, 15, 3):                            # dientes
        box_(i, 21, i, 21, O)
    for i in range(5):                                   # molinete
        box_(1 + i * 3, 10, 1 + i * 3, 14, O)
    box_(0, 10, 15, 10, K)
    box_(0, 12, 15, 12, hx("#4A4250"))
    box_(15, 16, 17, 18, YD)                             # alimentador
    wheel(22, 20, 5)
    wheel(39, 21, 3)


def centro():
    sun = (-50, 420)
    layers = [sky(51, sun)]
    x = XX[0]
    specs = ((512, 62, "#4E4A92", "#C490A8", 0.55, 14), (552, 54, "#4A4E88", "#A8A0B0", 0.36, 12), (592, 44, "#344E5A", "#A0A66E", 0.16, 9))
    hill_tops = []
    for k, (base, amp, lo, hi, hz, sc) in enumerate(specs):
        t = base - amp * P.line1(x, 81 + k, 80 - k * 12, 3) - 14 * np.abs(2 * P.line1(x, 85 + k, 22, 3) - 1)
        layers.append(rock(t, 87 + k, lo, hi, 700, haze=hz * 0.8, sun=sun, scale=sc * 0.7, gully=0.4 + k * 0.1))
        hill_tops.append(t)
    shrubs = Layer()                                      # monte serrano: matas, no puntitos
    rng = random.Random(95)
    t3 = hill_tops[2]
    gul = ridged(XX / 7, YY / 26, 96, 3)
    placed = 0
    tries = 0
    while placed < 150 and tries < 6000:
        tries += 1
        sx = rng.uniform(0, W)
        sy = rng.uniform(t3[int(min(W - 1, max(0, sx)))] + 6, 640)
        if gul[int(sy), int(min(W - 1, sx))] < 0.72 and rng.random() > 0.12:
            continue
        placed += 1
        r = 1.5 + (sy - 590) / 40
        canopy(shrubs, sx, sy, r * 3, r * 2.2, int(sx * 13 + sy), "algarrobo", 3, leaf=0.6, haze=0.14 - (sy - 590) / 600)
    pre = comp(layers + [shrubs])
    lake = Layer()
    m, col = water(pre, 628, 672, 420, 0.42, 91, "#4E6AA8")
    lake.put(m, col)
    dam = Layer()
    dam.rect(0, 622, 70, 630, hx("#D8CCBE"))
    dam.rect(0, 630, 70, 636, hx("#8A7E80"))
    for k in range(0, 70, 7):
        dam.rect(k, 622, k, 636, hx("#6A5E62"))
    town = Layer()
    rng2 = random.Random(22)
    for i in range(9):
        hx0 = 92 + i * 13 + rng2.randrange(-3, 3)
        hy0 = 616 - (i % 3) * 3
        town.rect(hx0, hy0, hx0 + 9, hy0 + 7, hazed(hx("#F6EADA"), 0.18))
        town.rect(hx0 + 6, hy0, hx0 + 9, hy0 + 7, hazed(hx("#B8A8B8"), 0.18))
        town.rect(hx0 - 1, hy0 - 2, hx0 + 10, hy0, hazed(hx("#B0503C"), 0.18))
        town.px(hx0 + 3, hy0 + 3, hx("#4A3A5A"))
    cap = Layer()
    cx, cy = 224, 590
    cap.rect(cx, cy, cx + 34, cy + 26, hx("#F6EAD4"))
    cap.rect(cx + 24, cy, cx + 34, cy + 26, hx("#B8A4B0"))
    for k in range(-3, 38):
        for j in range(5):
            cap.px(cx + k, cy - j, hx(("#B0503C" if j % 2 else "#8A3A30") if k < 26 else ("#7A3030" if j % 2 else "#5A2428")))
    for k in range(16):
        cap.rect(cx + 4 + k // 3, cy - 5 - k, cx + 16 - k // 3, cy - 5 - k, hx("#F6EAD4"))
        cap.px(cx + 16 - k // 3, cy - 5 - k, hx("#B8A4B0"))
    cap.rect(cx + 9, cy - 16, cx + 11, cy - 12, hx("#7A5A3A"))
    cap.rect(cx + 10, cy - 25, cx + 10, cy - 20, hx("#5A3A2A"))
    cap.rect(cx + 8, cy - 23, cx + 12, cy - 23, hx("#5A3A2A"))
    cap.rect(cx + 11, cy + 13, cx + 17, cy + 26, hx("#4A3048"))
    cap.put(ell_mask(cx + 14, cy + 13, 3, 3), hx("#4A3048"))
    cap.rect(cx + 4, cy + 8, cx + 6, cy + 12, hx("#4A3048"))
    soy = ground(672, 92, ["#1C2C30", "#2A4434", "#466438", "#7A8C44", "#C0B862"], sun=sun, vx=40, rows=1.2, row_n=8)
    # rastrojo cosechado: franjas paralelas a los surcos, borde siguiendo la perspectiva
    dep = np.clip(YY - 672, 1, None)
    u = (XX - 40) / dep * 8
    stub = Layer()
    rag = (fbm(XX / 3, YY / 2, 97, 2) - 0.5) * 0.5            # borde a lo largo de los surcos
    sm = (YY > 688) & (YY < 770 + 36 * fbm(XX / 24, np.full_like(XX, 3.0), 98, 3)) & (u > 2.4 + rag) & (u < 7.2 + rag)
    stub.put(sm, ramp(["#8A6E44", "#B8985A", "#DCC07C", "#F2DCA0"], np.clip(0.55 + (np.mod(u, 1.0) < 0.3) * -0.25 + (fbm(XX / 2, YY / 1.5, 98, 2) - 0.5) * 0.4, 0, 1)))
    straw = (YY > 760) & (YY < 830) & (u > 2.6) & (u < 7) & (fbm(XX / 1.5, YY / 1.5, 99, 2) > 0.74)
    stub.put(straw, hx("#E8CC84"))
    gnd = comp([pre, lake, dam, town, cap, soy, stub])
    bales = Layer()
    for bx, by, r in ((206, 712, 6), (244, 728, 8), (282, 750, 10)):
        long_shadow(gnd, bx, by + r, r * 2.2, r * 2, 0.45)
        bales.put(ell_mask(bx, by, r, r), hx("#9A6A3A"))
        bales.put(ell_mask(bx - r * 0.2, by - r * 0.1, r * 0.78, r * 0.78), hx("#D0A058"))
        bales.put(ell_mask(bx - r * 0.35, by - r * 0.3, r * 0.38, r * 0.38), hx("#F6D088"))
        for kk in range(2, r, 3):
            ring = ell_mask(bx, by, kk, kk) & ~ell_mask(bx, by, kk - 1, kk - 1)
            bales.put(ring, hx("#A87A44"))
    mach = Layer()
    mx0, my0 = 18, 748
    shadow_on(gnd, mx0 + 80, my0 + 66, 82, 6, 0.5)
    shadow_on(gnd, mx0 + 66, my0 + 64, 64, 2.5, 0.7)
    combine(mach, mx0, my0, 3)
    dust = Layer()
    dn = fbm(XX / 6, YY / 4, 93, 3)
    plume = np.clip(1 - (XX - (mx0 + 140)) / 80, 0, 1)
    dm = (YY < my0 + 52) & (YY > my0 + 20 - (XX - mx0 - 140) * 0.15) & (XX > mx0 + 136) & (XX < mx0 + 220) & (dn + plume * 0.5 > 0.82)
    dm = dm & ((dn + plume * 0.5 - 0.82) * 3 > BY)
    dust.put(dm, ramp(["#E8C49A", "#F6DCB2", "#FFF0D8"], np.round(np.clip(dn * 2 - 0.6, 0, 1) * 2) / 2))
    road = Layer()
    rd = np.zeros((H, W), dtype=bool)
    road.put(rd, ramp(["#7A4A3A", "#A8704E", "#D49C70", "#ECC08E"], np.clip(0.55 + (fbm(XX / 3, YY / 2, 98, 2) - 0.5) * 0.7, 0, 1)))
    gnd2 = comp([gnd, bales, mach, dust, road])
    shadow_on(gnd2, 300, 902, 90, 10, 0.6)
    shadow_on(gnd2, 280, 898, 34, 3.5, 0.75)
    fg = Layer()
    tree(fg, 252, 904, 220, 140, "algarrobo", 99, bark="oscura", lean=-0.05, trunk_w=13, tiers=3, flat=0.6, wobble=3.0)
    flora = Layer()
    grass_tufts(flora, rng, 70, 794, 900, cols=("#24302E", "#4E6A3A", "#9A9A4E", "#E2CC7A"))
    flowers(flora, rng, 50, 774, 900, ["#F2D04A", "#FFFFFF", "#E86A9A"])
    return comp([gnd2, flora, fg])


# ------------------------------------------------------------------ marco: pilares con capitel y base

REGIONS = [("noa", "NOA", noa), ("nea", "NEA", nea), ("cuyo", "CUYO", cuyo), ("patagonia", "PATAGONIA", patagonia),
           ("pampeana", "PAMPEANA", pampeana), ("centro", "CENTRO", centro)]
CW, CH = 1920, 1080
GAP = 16
TOP = 104
GOLD = [hx(c) for c in ("8E5A10", "F6B40E", "F2D173", "F7EDA4")]


def backdrop():
    yy, xx = np.mgrid[0:CH, 0:CW].astype(np.float64)
    c = np.zeros((CH, CW, 3))
    for ch in range(3):
        c[..., ch] = np.interp(yy, [0, 500, 1080], [hx("#141226")[ch], hx("#221F3C")[ch], hx("#2B2746")[ch]])
    by = P.BAYER[yy.astype(int) % 4, xx.astype(int) % 4]
    c = np.floor(c / 6.0 + by[..., None] * 0.98) * 6.0
    rng = random.Random(5)
    for _ in range(420):
        x, y = rng.randrange(CW), rng.randrange(CH)
        c[y, x] = mix(c[y, x], hx("#FFF6D8"), rng.choice((0.25, 0.4, 0.7)))
    return c


def box(canvas, xa, ya, xb, yb, col):
    canvas[ya:yb, xa:xb] = col


def disc(canvas, cx, cy, r, col):
    for yy in range(cy - r, cy + r + 1):
        for xx in range(cx - r, cx + r + 1):
            if (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r:
                canvas[yy, xx] = col


def chevron_sign(canvas, cx, cy, name, font):
    """Cartel con el estilo de los rótulos de la página (.tag): cinta marrón oscura con
    doble filete dorado, rombos y chevrones dorados, texto crema con sombra."""
    m = font.getmask(name, mode="1")
    tw, th = m.size
    pw, ph = tw + 44, 32
    x0, y0 = cx - pw // 2, cy - ph // 2
    box(canvas, x0 - 2, y0 - 2, x0 + pw + 2, y0 + ph + 2, OUTL)
    box(canvas, x0, y0, x0 + pw, y0 + ph, hx("#2E1A10"))
    box(canvas, x0, y0 + 3, x0 + pw, y0 + 6, hx("#4A2A18"))
    box(canvas, x0, y0, x0 + pw, y0 + 3, GOLD[2])
    box(canvas, x0, y0 + 3, x0 + pw, y0 + 4, GOLD[0])
    box(canvas, x0, y0 + ph - 3, x0 + pw, y0 + ph, GOLD[1])
    box(canvas, x0, y0 + ph - 4, x0 + pw, y0 + ph - 3, hx("#5C3520"))
    for dx in (x0 + 9, x0 + pw - 10):                     # rombos
        for j in range(-3, 4):
            for i in range(-3 + abs(j), 4 - abs(j)):
                canvas[cy + j, dx + i] = GOLD[2] if j < 0 else GOLD[1]
    for side in (-1, 1):
        ex = x0 - 4 if side < 0 else x0 + pw + 3
        for j in range(ph + 6):
            dy = j - (ph + 6) / 2
            reach = int(13 - abs(dy) * 0.68)
            for k in range(max(0, reach - 5), reach + 1):
                canvas[y0 - 3 + j, ex + side * k] = OUTL if k == reach else (GOLD[3] if dy < 0 else GOLD[1])
    tx, ty = cx - tw // 2, y0 + (ph - th) // 2 - 1
    for j in range(th):
        for i in range(tw):
            if m.getpixel((i, j)):
                canvas[ty + j + 2, tx + i] = hx("#140A06")
    for j in range(th):
        for i in range(tw):
            if m.getpixel((i, j)):
                canvas[ty + j, tx + i] = hx("#FFF6E6")


def frame_pillar(canvas, x0, art, name, font):
    y0, y1 = TOP, TOP + H
    canvas[y0:y1, x0:x0 + W] = art
    box(canvas, x0 - 5, y0 - 5, x0 + W + 5, y0, OUTL)
    box(canvas, x0 - 5, y1, x0 + W + 5, y1 + 5, OUTL)
    box(canvas, x0 - 5, y0, x0, y1, OUTL)
    box(canvas, x0 + W, y0, x0 + W + 5, y1, OUTL)
    box(canvas, x0 - 3, y0 - 3, x0 + W + 3, y0 - 2, GOLD[2])
    box(canvas, x0 - 3, y0 - 3, x0 - 2, y1 + 3, GOLD[2])
    box(canvas, x0 + W + 2, y0 - 3, x0 + W + 3, y1 + 3, GOLD[0])
    box(canvas, x0 - 3, y1 + 2, x0 + W + 3, y1 + 3, GOLD[0])
    cap = [(-12, 34, 26, 1), (-8, 26, 16, 2), (-4, 16, 6, 1)]
    for inset, ya, yb, _ in cap:
        box(canvas, x0 + inset - 2, y0 - ya - 2, x0 + W - inset + 2, y0 - yb + 2, OUTL)
    for inset, ya, yb, tone in cap:
        xa, xb = x0 + inset, x0 + W - inset
        box(canvas, xa, y0 - ya, xb, y0 - yb, GOLD[tone])
        box(canvas, xa, y0 - ya, xb, y0 - ya + 1, GOLD[3])
        box(canvas, xa, y0 - yb - 1, xb, y0 - yb, GOLD[0])
    for cx in (x0 - 10, x0 + W + 10):
        for r, col in ((7, OUTL), (5, GOLD[2]), (3, GOLD[0]), (1, GOLD[3])):
            disc(canvas, cx, y0 - 22, r, col)
    by0 = y1 + 5
    for inset, ya, yb, tone in ((-6, 0, 10, 1), (-12, 10, 22, 2), (-16, 22, 66, 1)):
        xa, xb = x0 + inset, x0 + W - inset
        box(canvas, xa - 2, by0 + ya, xb + 2, by0 + yb + 2, OUTL)
        box(canvas, xa, by0 + ya, xb, by0 + yb, GOLD[tone])
        box(canvas, xa, by0 + ya, xb, by0 + ya + 1, GOLD[3])
    chevron_sign(canvas, x0 + W // 2, by0 + 44, name, font)


def main():
    os.makedirs(OUT, exist_ok=True)
    font = ImageFont.truetype(FONT, 28)
    canvas = backdrop()
    left = (CW - (6 * W + 5 * GAP)) // 2
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    for i, (rid, name, fn) in enumerate(REGIONS):
        if only and rid != only:
            continue
        art = np.clip(fn(), 0, 255)
        Image.fromarray(art.astype(np.uint8)).save(os.path.join(OUT, "region_%s.png" % rid))
        frame_pillar(canvas, left + i * (W + GAP), art, name, font)
        print("pilar", rid)
    if not only:
        Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8)).save(os.path.join(OUT, "pilares.png"), optimize=True)
        print("ok", os.path.join(OUT, "pilares.png"))


if __name__ == "__main__":
    main()
