"""14.0: paisajes regionales pintados con luz (reemplaza el fondo de landscapes.py).

El paisaje (cielo, montañas, campo, vegetación, agua) se pinta en color continuo
con la misma luz de toda la 14: sol bajo arriba a la izquierda, sombras frías,
perspectiva atmosférica (lo lejano se aclara y se azula hacia el horizonte),
nubes con volumen (tapa cálida, panza lavanda). Después se cuantiza a una
paleta propia de cada escena con tramado Bayer sólo en franjas angostas, así
sigue siendo pixel art limpio.

La vereda, el cordón, la calle y la utilería salen de landscapes.py tal cual
(personas y colectivo caen en el mismo lugar) y reciben luz: degradé de sol,
sombra de cada objeto hacia atrás-derecha y oclusión contra la línea de fondo.

  python tools/art/landscapes14.py   -> assets/escenarios/locations/street_<region>.png
Lo corre restyle11.py al final (después del re-estilo, que pisaría estos).
"""
import math
import os
import random
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import landscapes as L  # noqa: E402
import restyle11 as R  # noqa: E402

W, H = 480, 200
EDGE = 150
LOT = (142, 338)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float64)
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
BY = BAYER[YY.astype(int) % 4, XX.astype(int) % 4]
SUN_X, SUN_Y = 70.0, -30.0


def hx(c):
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64)


def mix(a, b, t):
    t = np.asarray(t, dtype=np.float64)
    if t.ndim == 2:
        t = t[..., None]
    return a * (1 - t) + b * t


# ------------------------------------------------------------------ ruido

VAR = 0      # variante por provincia (cambia formas y ruido manteniendo la composición)


def noise1(x, seed, scale):
    rng = np.random.default_rng(abs(int(seed)) + VAR * 7919)
    g = rng.random(int(W / scale) + 4)
    u = x / scale
    i = np.floor(u).astype(int)
    f = u - i
    f = f * f * (3 - 2 * f)
    return g[i + 1] * (1 - f) + g[i + 2] * f


def fbm1(x, seed, scale, oct=4):
    v, a, tot = 0.0, 1.0, 0.0
    for o in range(oct):
        v = v + a * noise1(x, seed + o * 31, scale / (2 ** o))
        tot += a
        a *= 0.5
    return v / tot


def noise2(scale, seed, sx=1.0, sy=1.0):
    rng = np.random.default_rng(abs(int(seed)) + VAR * 7919)
    gh, gw = int(H / scale * sy) + 3, int(W / scale * sx) + 3
    g = rng.random((gh, gw))
    yy, xx = YY / scale * sy, XX / scale * sx
    y0, x0 = yy.astype(int), xx.astype(int)
    fy, fx = yy - y0, xx - x0
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx
    b = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def fbm2(scale, seed, oct=3, sx=1.0, sy=1.0):
    v, a, tot = 0.0, 1.0, 0.0
    for o in range(oct):
        v = v + a * noise2(scale / (2 ** o), seed + o * 17, sx, sy)
        tot += a
        a *= 0.5
    return v / tot


# ------------------------------------------------------------------ escena

class Scene:
    def __init__(self, zenith, horizon, haze, sun="#FFE9C2"):
        self.rgb = np.zeros((H, W, 3))
        self.zen, self.hor, self.haze, self.sun = hx(zenith), hx(horizon), hx(haze), hx(sun)
        self.depth = np.full((H, W), 1.0)      # 1 = cielo/infinito, 0 = vereda
        self.near = np.zeros((H, W), dtype=bool)
        self.cloudm = np.zeros((H, W), dtype=bool)

    def sky(self, horizon_y=130):
        t = np.clip(YY / horizon_y, 0, 1) ** 1.25
        c = mix(self.zen, self.hor, t)
        d = np.hypot((XX - SUN_X) / 1.3, YY - SUN_Y)
        glow = np.clip(1 - d / 300, 0, 1) ** 2.6
        c = mix(c, self.sun, glow * 0.42)
        self.rgb[:] = c

    def put(self, mask, color, depth):
        """Pinta color (H,W,3) donde mask, con perspectiva atmosférica según depth (0..1)."""
        haze = np.clip(depth, 0, 1) ** 1.5 * 0.58
        hz = mix(mix(self.haze, self.hor, 0.4), hx("#C9D2E6") if depth > 0.45 else hx("#F0DCC4"), 0.3)
        col = mix(color, hz[None, None, :] if np.ndim(color) == 3 else hz, haze)
        self.rgb[mask] = col[mask] if np.ndim(col) == 3 else col
        self.depth[mask] = depth

    def cloud(self, cx, cy, sx, sy, seed, puffs=6):
        # la escena muestra desde la fila 30: las nubes van enteras dentro de lo visible
        if cy < 80:
            cy = max(cy + 26, 34 + sy * 1.1)
        if VAR:
            vr = random.Random(VAR * 31 + seed)
            cx = (cx + vr.randint(-120, 120)) % W
            sx *= vr.uniform(0.8, 1.15)
        cx = min(max(cx, 40 + sx * 1.3 + 10), W - 40 - sx * 1.3 - 10)   # entera dentro del cuadro visible
        rng = random.Random(seed + VAR * 13)
        f = np.zeros((H, W))
        for _ in range(puffs):
            px = cx + rng.uniform(-0.9, 0.9) * sx
            py = cy + rng.uniform(-0.6, 0.1) * sy
            r = rng.uniform(0.35, 0.6) * sx
            f += np.exp(-(((XX - px) / r) ** 2 + ((YY - py) / (r * sy / sx * 1.4)) ** 2))
        f += 0.6 * np.exp(-(((XX - cx) / (sx * 1.3)) ** 2 + ((YY - cy - sy * 0.25) / (sy * 0.35)) ** 2))
        f *= 0.85 + 0.3 * fbm2(6, seed)
        m = f > 0.55
        if not m.any():
            return
        # luz en 3 tonos: tapa cálida arriba-izquierda, cuerpo, panza lavanda
        import facade_light as FL
        mf = m.astype(np.float64)
        s1 = FL.box_blur(mf, 2)
        up = np.roll(np.roll(s1, 3, axis=0), 2, axis=1)       # cuánto hay de nube arriba-izquierda
        rimlit = np.clip(1.2 - up * 1.0, 0, 1)
        ys = YY[m]
        bottom = np.clip((YY - ys.min()) / max(1, ys.max() - ys.min()), 0, 1)
        lit = np.clip(0.95 - bottom ** 1.6 * 0.9 + rimlit * 0.25, 0, 1)
        lob = FL.box_blur((fbm2(2.5, seed + 9, 2) > 0.55).astype(np.float64), 1)
        lit = np.clip(lit + (lob - 0.5) * 0.25 * (1 - bottom), 0, 1)
        top_c, mid_c, bel_c = hx("#FFF9EC"), hx("#EFE3DA"), hx("#B9B3CF")
        tone = np.where(lit > 0.62, 2, np.where(lit > 0.3, 1, 0))
        c = np.stack([bel_c, mid_c, top_c])[tone]
        rimc = m & ~np.roll(np.roll(m, 1, axis=0), 1, axis=1)
        c = np.where(rimc[..., None], hx("#FFFDF6"), c)
        skyt = self.rgb
        c = np.where((tone == 0)[..., None], mix(c, skyt, 0.32), c)
        far = np.clip((cy - 40) / 80, 0, 1)            # más lavadas hacia el horizonte
        c = mix(c, skyt, 0.22 * far)
        self.rgb[m] = c[m]
        self.cloudm |= m

    def quantize(self, n=40, rows=None):
        """Cuantiza el paisaje a n colores con tramado ordenado (bandas angostas)."""
        y1 = rows if rows else H
        reg = self.rgb[:y1]
        img = Image.fromarray(np.clip(reg, 0, 255).astype(np.uint8), "RGB")
        pal_img = img.quantize(colors=n, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
        pal = np.array(pal_img.getpalette()[:n * 3], dtype=np.float64).reshape(-1, 3)
        d = ((reg[:, :, None, :] - pal[None, None]) ** 2).sum(-1)
        order = np.argsort(d, axis=-1)
        i1, i2 = order[..., 0], order[..., 1]
        c1, c2 = pal[i1], pal[i2]
        seg = c2 - c1
        t = ((reg - c1) * seg).sum(-1) / np.maximum((seg * seg).sum(-1), 1)
        # tramado sólo cerca del punto medio entre dos tonos (franja angosta)
        sky = (self.depth[:y1] >= 1.0) & ~self.cloudm[:y1]
        use2 = sky & (t > 0.36) & (BY[:y1] < (t - 0.36) / 0.28)   # tramado sólo en el degradé del cielo
        use2 |= ~sky & (t > 0.5)
        idx = np.where(use2, i2, i1)
        self.rgb[:y1] = pal[idx]


# ------------------------------------------------------------------ piezas

def slope_light(top):
    """Luz de ladera: sube a la derecha (mira al sol) = luz; baja = sombra."""
    s = np.gradient(top.astype(np.float64))
    s = np.convolve(s, np.ones(5) / 5, mode="same")
    return np.clip(0.5 - s * 0.55, 0, 1)


def facet_light(top, seed):
    """Caras de cada cumbre: una arista baja desde la cima (con quiebres) y separa
    la cara al sol (izquierda) de la cara en sombra (derecha). Entre dos cumbres,
    el valle. Devuelve la luz 0..1 por píxel."""
    t = np.convolve(np.pad(top, 2, mode="edge"), np.ones(5) / 5, mode="valid")
    peaks = [x for x in range(1, W - 1) if t[x] <= t[x - 1] and t[x] < t[x + 1]]
    valleys = [x for x in range(1, W - 1) if t[x] >= t[x - 1] and t[x] > t[x + 1]]
    # cumbres con prominencia: descarta las ondulaciones chicas
    pk = []
    for p in peaks:
        lv = max([v for v in valleys if v < p], default=0)
        rv = min([v for v in valleys if v > p], default=W - 1)
        if min(t[lv], t[rv]) - t[p] > 3 or not pk:
            pk.append(p)
    if top[0] < top[1] and 0 not in pk:
        pk.insert(0, 0)
    pk = sorted(set(pk))
    lt = np.zeros((H, W))
    jit = fbm2(3, seed + 11, 2, sx=0.6, sy=1.4)
    cut = [0] + [int(t[a:b + 1].argmax()) + a for a, b in zip(pk[:-1], pk[1:])] + [W]
    for i, p in enumerate(pk):
        a, b = cut[i], cut[i + 1]
        dy = np.clip(YY - top[p], 0, None)
        ridge = p + dy * 0.28 + (jit - 0.5) * (4 + dy * 0.35)
        face = np.clip((ridge - XX) / 2.5 + 0.5, 0, 1)     # 1 = cara al sol
        dyv = np.clip(YY - np.minimum(top[min(a, W - 1)], top[min(b, W - 1)]), 0, None)
        wob = (jit - 0.5) * 10 + dyv * 0.12
        sl = (XX >= a + (wob if i else -99)) & (XX < b + (wob if i + 1 < len(pk) else 99))
        lt = np.where(sl, 0.22 + 0.62 * face, lt)
    return lt


def tones(val, n):
    """Valor 0..1 -> n tonos limpios (pixel art de cúmulos, sin moteado): el valor se
    suaviza antes, y sólo el borde entre dos tonos lleva 1 px de tramado."""
    import facade_light as FL
    v = FL.box_blur(np.clip(val, 0, 1), 1)
    q = v * (n - 1)
    base = np.floor(q)
    fr = q - base
    idx = np.round(q)
    return np.clip(idx, 0, n - 1) / (n - 1)


def mountains(sc, top, depth, lit_c, shade_c, deep_c, snow=None, seed=0, stria=0.0, base=EDGE):
    """Cordón montañoso: luz por ladera, quebradas, nieve y degradé hacia la base."""
    top = top.astype(np.float64)
    m = (YY >= top[None, :]) & (YY < base)
    if not m.any():
        return m
    lt = facet_light(top, seed)
    below = np.clip((YY - top[None, :]) / 60.0, 0, 1)
    gul = fbm2(6, seed, 2, sx=1.1, sy=0.8)          # planos de roca grandes (no moteado)
    lt = np.clip(lt + (gul - 0.5) * 0.25, 0, 1)
    val = tones(lt * (1 - 0.4 * below) + 0.1 * (1 - below), 5)
    cool = mix(shade_c, hx("#4E5A8C"), 0.25)
    c = np.where((val < 0.3)[..., None], mix(mix(deep_c, cool, 0.5) * 0.92, cool, val / 0.3), mix(cool, lit_c, (val - 0.3) / 0.7))
    if stria:
        st = (np.sin((YY - top[None, :] * 0.6) * 0.55 + gul * 6) > 0.6)
        c = np.where(st[..., None], c * (1 - stria), c)
    if snow is not None:
        line, depth_s = snow
        above = np.clip((line - top[None, :]) / 22.0, 0, 1)
        sd = depth_s * above * (0.6 + 0.6 * fbm2(9, seed + 5, 2))
        sn = m & (YY - top[None, :] < sd) & ((lt > 0.5) | (YY - top[None, :] < sd * 0.4))
        sc_l, sc_s = hx("#FFFDF6"), hx("#A9B6D8")
        snc = np.where((lt > 0.5)[..., None], sc_l, sc_s)      # nieve: dos tonos limpios
        c = np.where(sn[..., None], snc, c)
    rim = m & (YY - top[None, :] < 1.2) & (lt > 0.5)              # filo de luz de la cresta
    c = np.where(rim[..., None], mix(c, sc.sun, 0.45), c)
    sc.put(m, c, depth)
    return m


def hills(sc, top, depth, light_c, shade_c, seed, texture=0.12, base=EDGE):
    top = top.astype(np.float64)
    m = (YY >= top[None, :]) & (YY < base)
    lt = facet_light(top, seed) * 0.55 + 0.45 * np.clip(1 - (YY - top[None, :]) / 25, 0, 1)
    n = fbm2(6, seed, 2)
    lt = tones(np.clip(lt + (n - 0.5) * texture * 1.2, 0, 1), 4)
    c = mix(shade_c, light_c, lt)
    rim = m & (YY - top[None, :] < 1.2)
    c = np.where(rim[..., None], mix(c, sc.sun, 0.3), c)
    sc.put(m, c, depth)
    return m


def blob_shade(sc, mask, cx, cy, rx, ry, lit_c, mid_c, dark_c, depth, leaf=True, seed=0):
    nx = (XX - cx) / max(rx, 1)
    ny = (YY - cy) / max(ry, 1)
    lt = np.clip(0.62 - nx * 0.55 - ny * 0.6, 0, 1)
    if leaf:
        lt = np.clip(lt + (fbm2(3.5, seed, 2) - 0.5) * 0.6, 0, 1)
    lt = tones(lt, 4)
    c = np.where((lt > 0.5)[..., None], mix(mid_c, lit_c, (lt - 0.5) * 2), mix(dark_c, mid_c, lt * 2))
    sc.put(mask, c, depth)
    sc.near |= mask & (depth < 0.2)


def tree_round(sc, x, base, h, r, seed, depth, pal):
    lit, mid, dark, trunk = pal
    rng = random.Random(seed)
    tm = (abs(XX - x) <= max(1, r // 6)) & (YY >= base - h + r * 1.4) & (YY < base)
    sc.put(tm, mix(hx(trunk), hx("#2A1A14"), np.clip((XX - x + 1) / 3, 0, 1)[..., None] * 0.6 * np.ones((1, 1, 3))), depth)
    f = np.zeros((H, W))
    cy = base - h + r
    for k in range(7):
        px = x + rng.uniform(-0.8, 0.8) * r
        py = cy + rng.uniform(-0.6, 0.4) * r
        rr = rng.uniform(0.45, 0.75) * r
        f = np.maximum(f, 1 - np.hypot((XX - px) / rr, (YY - py) / (rr * 0.85)))
    edge_n = fbm2(1.6, seed, 2)
    m = f > (0.05 + edge_n * 0.22)
    blob_shade(sc, m, x, cy, r * 1.1, r, hx(lit), hx(mid), hx(dark), depth, seed=seed)


def poplar(sc, x, base, h, seed, depth, pal):
    lit, mid, dark, trunk = pal
    cy = base - h * 0.55
    rx, ry = max(3.0, h * 0.11), h * 0.5
    sh = 1 - np.hypot((XX - x) / rx, (YY - cy) / ry)
    n = fbm2(1.7, seed, 2)
    m = (sh > n * 0.35) & (YY < base - 3)
    tm = (abs(XX - x) < 1) & (YY >= base - 6) & (YY < base)
    sc.put(tm, hx(trunk), depth)
    blob_shade(sc, m, x, cy, rx, ry, hx(lit), hx(mid), hx(dark), depth, seed=seed)


def cardon(sc, x, base, h, seed, depth):
    rng = random.Random(seed)
    lit, mid, dark = hx("#8FC47A"), hx("#4E8F55"), hx("#24513A")
    parts = [(x, base - h, 3.2, h)]
    for side in (-1, 1):
        if rng.random() < 0.85:
            ay = base - h * rng.uniform(0.35, 0.6)
            ax = x + side * rng.uniform(6, 8)
            ah = h * rng.uniform(0.35, 0.5)
            parts.append((ax, ay - ah, 2.4, ah))
            arm = (abs(YY - ay) < 2.2) & ((XX - x) * side > 0) & ((XX - x) * side < abs(ax - x) + 1)
            sc.put(arm, mix(dark, mid, 0.6), depth)
    for px, py, r, hh in parts:
        u = (XX - px) / r
        m = (np.abs(u) <= 1) & (YY >= py + np.where(np.abs(u) > 0.6, 1, 0)) & (YY < py + hh)
        cap = (np.hypot(XX - px, (YY - py - r) * 1.1) <= r)
        m = m | (cap & (YY < py + r))
        lt = np.clip(0.75 - u * 0.65, 0, 1)
        rib = (np.round(XX - px) % 2 == 0)
        c = mix(dark, lit, lt)
        c = np.where(rib[..., None], c * 0.86, c)
        sc.put(m, c, depth)
        sc.near |= m
    fl = (np.hypot(XX - x, YY - (base - h - 1)) < 1.5)
    sc.put(fl, hx("#F27A8A"), depth)


def lake(sc, y0, y1, x0, x1, depth):
    t = np.clip((YY - y0) / max(1, y1 - y0), 0, 1)
    ex = ((XX - (x0 + x1) / 2) / ((x1 - x0) / 2)) ** 2 + ((YY - (y0 + y1) / 2) / ((y1 - y0) / 2 + 0.5)) ** 2
    m = ex <= 1
    c = mix(hx("#7FD3E0"), hx("#1F6E95"), t ** 0.8)
    c = mix(c, hx("#CFEFF5"), np.clip(1 - np.abs(YY - (y0 + 1.5)) / 1.5, 0, 1) * 0.6)   # orilla lejana clara
    rip = (np.abs(((XX * 0.13 + np.floor(YY) * 1.7) % 9) - 1) < 0.9) & ((YY.astype(int) - int(y0)) % 3 == 1)
    rip &= fbm2(5, 77, 2) > 0.55
    c = np.where(rip[..., None], mix(c, hx("#F2FDFF"), 0.55), c)
    sc.put(m, c, depth)
    return m


def field_rows(sc, y0, y1, x0, x1, c_a, c_b, line_c, seed, depth, every=(3, 7)):
    """Surcos/hileras con perspectiva (más juntas lejos, más separadas cerca)."""
    m = (YY >= y0) & (YY < y1) & (XX >= x0) & (XX < x1)
    t = np.clip((YY - y0) / max(1, y1 - y0), 0, 1)
    per = every[0] + (every[1] - every[0]) * t
    ph = (YY - y0) / per
    rowpos = ph - np.floor(ph)
    base = mix(hx(c_a), hx(c_b), (fbm2(4, seed, 2) > 0.5) * 0.35 + t * 0.3)
    c = np.where((rowpos < 0.38)[..., None], hx(line_c) * (0.8 + 0.4 * t[..., None]) / 1.0, base)
    lt = np.clip(0.5 + (fbm2(2, seed + 3, 2) - 0.5), 0, 1)
    c = c * (0.9 + 0.2 * lt[..., None])
    sc.put(m, c, depth)
    return m


# ------------------------------------------------------------------ regiones

def P(*c):
    return [hx(x) for x in c]


def RR(seed):
    return random.Random(seed + VAR * 101)


def noa():
    sc = Scene("#2F7FD0", "#BFE0EE", "#E9D7C8", "#FFE6BC")
    sc.sky(118)
    sc.cloud(80, 30, 28, 16, 3, 9)
    sc.cloud(390, 40, 22, 12, 4, 7)
    x = XX[0]
    far = 92 - 26 * fbm1(x, 11, 90) - 10 * fbm1(x, 12, 24)
    mountains(sc, far, 0.75, hx("#E8C2B8"), hx("#9C7FA0"), hx("#B49BB0"), seed=1)
    # Cerros de siete colores: bandas inclinadas que siguen la ladera
    top = 112 - 40 * (0.55 + 0.45 * np.sin((x + 10) / 170 * 2 * np.pi)) - 8 * fbm1(x, 3, 30)
    m = (YY >= top[None, :]) & (YY < EDGE)
    bands = P("#C9573F", "#E58A3C", "#E7C489", "#8DB876", "#C98C66", "#E27E7A", "#B5483A")
    k = ((YY - top[None, :] * 0.55 + 5 * np.sin(XX / 19.0)) // 6).astype(int) % len(bands)
    col = np.stack([b for b in bands])[k]
    lt = facet_light(top, 9)
    gul = fbm2(4, 9, 3, sx=1.1, sy=0.8)
    lt = np.clip(lt + (gul - 0.5) * 0.4, 0, 1)
    col = col * (0.62 + 0.5 * lt[..., None])
    col = mix(col, hx("#6E4A6E"), np.clip((1 - lt) * 0.35, 0, 0.35))
    sc.put(m, col, 0.35)
    near = 140 - 16 * fbm1(x, 5, 60) - 4 * fbm1(x, 6, 12)
    hills(sc, near, 0.12, hx("#E3B27E"), hx("#9E6A48"), 7, 0.15)
    rng = RR(4)
    for cx in (18, 70, 96, 131, 352, 405, 448):
        cardon(sc, cx + rng.randint(-6, 6), EDGE - 1 - rng.randint(0, 7), rng.randint(20, 40), cx, 0.06)
    for cx in range(4, W, 9):                      # matas de paja brava
        if not LOT[0] - 4 < cx < LOT[1] + 4:
            bx = cx + rng.randint(-2, 2)
            tuft = (np.abs(XX - bx) < 3 - (EDGE - 1 - YY) * 0.5) & (YY > EDGE - 5) & (YY < EDGE)
            sc.put(tuft, hx("#D8B45E") * (0.8 + 0.3 * (XX < bx)[..., None]), 0.05)
    return sc


def nea():
    sc = Scene("#3484C6", "#CFE7E2", "#CFE2D6", "#FFF0CC")
    sc.sky(112)
    sc.cloud(130, 36, 36, 20, 11, 10)
    sc.cloud(340, 26, 28, 15, 12, 8)
    sc.cloud(450, 70, 22, 10, 13, 6)
    x = XX[0]
    far = 102 - 14 * fbm1(x, 21, 80)
    hills(sc, far, 0.7, hx("#86B79A"), hx("#5D8C7C"), 21, 0.08)
    mid = 118 - 16 * fbm1(x, 22, 50)
    hills(sc, mid, 0.42, hx("#4F9A5A"), hx("#2F6447"), 22, 0.2)
    rng = RR(7)
    pal_far = ("#7DBE6A", "#3E8A4C", "#1E4E36", "#5A3A26")
    pal = ("#9BD46E", "#4C9A4F", "#1F5536", "#5A3622")
    for cx in range(-6, W + 10, 13):                 # dosel lejano continuo
        r_ = rng.randint(12, 15)
        tree_round(sc, cx + rng.randint(-4, 4), EDGE - 10, int(r_ * 2.6) + rng.randint(0, 8), r_, cx * 3 + 1000, 0.24, pal_far)
    for cx in list(range(0, LOT[0] - 4, 15)) + list(range(LOT[1] + 6, W + 10, 15)):
        r_ = rng.randint(13, 17)
        tree_round(sc, cx + rng.randint(-4, 4), EDGE - 1, int(r_ * 3.0) + rng.randint(0, 10), r_, cx * 7 + 2000, 0.07, pal)
    # palmera pindó
    for px in (118, 362):
        trunk = (np.abs(XX - px - (EDGE - YY) * 0.06) < 1.3) & (YY > EDGE - 62) & (YY < EDGE)
        sc.put(trunk, mix(hx("#7A5A42"), hx("#3E2A1E"), np.clip((XX - px) / 2, 0, 1)[..., None] * np.ones((1, 1, 3))), 0.05)
        for ang in np.linspace(-2.6, -0.5, 6).tolist() + [0.2, 0.6]:
            for t in np.linspace(0, 1, 26):
                fx = px + 3.7 + math.cos(ang) * 20 * t
                fy = EDGE - 62 + math.sin(ang) * 10 * t + 9 * t * t
                leaf = np.hypot(XX - fx, YY - fy) < 1.3 - t * 0.6
                sc.put(leaf, mix(hx("#A6DB7C"), hx("#2F7046"), t * 0.8 + (ang > -1.5) * 0.2), 0.05)
    for cx in range(-4, W + 8, 9):                   # sotobosque
        tree_round(sc, cx + rng.randint(-3, 3), EDGE - 1, rng.randint(12, 18), rng.randint(6, 9), cx * 11 + 3000, 0.05, ("#8CCB64", "#3E8A44", "#1A4A30", "#3A2618"))
    # tierra colorada en el pie de la selva
    red = (YY >= EDGE - 4) & (YY < EDGE) & ((XX < LOT[0]) | (XX > LOT[1]))
    sc.put(red, mix(hx("#C2543A"), hx("#8A3424"), (YY - EDGE + 4)[..., None] / 4 * np.ones((1, 1, 3))), 0.04)
    return sc


def cuyo():
    sc = Scene("#2A78C8", "#C9E4EF", "#DCE3EA", "#FFE8C0")
    sc.sky(110)
    sc.cloud(410, 26, 24, 13, 21, 8)
    sc.cloud(150, 18, 16, 8, 22, 6)
    x = XX[0]
    rr = RR(31)
    pk = np.zeros(W)
    px = -30
    while px < W + 40:
        px += rr.randint(26, 52)
        ph = rr.uniform(30, 70) * (1.25 if 250 < px < 330 else 1.0)     # el Aconcagua, al fondo del lote
        pk = np.maximum(pk, ph - np.abs(x - px - rr.randint(-10, 10)) * ph / rr.uniform(34, 46))
    peaks = 108 - pk - 6 * fbm1(x, 32, 10) - 3 * fbm1(x, 33, 4)
    mountains(sc, peaks, 0.42, hx("#F0D2BC"), hx("#6E6890"), hx("#8E86A2"), snow=(78, 26), seed=31)
    pre = 124 - 28 * np.clip(fbm1(x, 33, 50, 5) * 1.4 - 0.3, 0, 1)
    mountains(sc, pre, 0.36, hx("#D7A47E"), hx("#7C5A64"), hx("#8F6A5E"), snow=(90, 8), seed=33, stria=0.08)
    foot = 136 - 9 * fbm1(x, 34, 40)
    hills(sc, foot, 0.2, hx("#D9A86C"), hx("#9A6B48"), 34, 0.12)
    for (a, b) in ((0, LOT[0] - 6), (LOT[1] + 6, W)):
        field_rows(sc, 128, EDGE, a, b, "#5D9B4A", "#7BB25A", "#2C5A33", 35, 0.12, (3, 6))
    pal = ("#8FD07A", "#3F8C4E", "#1D4F35", "#5A3622")
    rng = RR(9)
    for cx in list(range(4, LOT[0] - 16, 15)) + list(range(LOT[1] + 18, W - 4, 13)):
        poplar(sc, cx + rng.randint(-3, 3), EDGE - 1, 38 + rng.randint(0, 18), cx, 0.07, pal)
    return sc


def patagonia():
    sc = Scene("#2C6FBE", "#CDE3EF", "#DDE6EE", "#FFEBCB")
    sc.sky(108)
    for cx, cy, s in ((90, 22, 1.2), (270, 30, 1.0), (420, 16, 1.1)):     # nubes lenticulares
        sc.cloud(cx, cy, 34 * s, 7 * s, int(cx), 7)
    x = XX[0]
    rr = RR(40)
    rng_ = np.zeros(W)
    px = -20
    while px < W + 30:
        px += rr.randint(16, 40)
        ph = rr.uniform(5, 18)
        rng_ = np.maximum(rng_, ph - np.abs(x - px) * ph / 24)
    fitz = 104 - rng_ - 46 * np.exp(-((x - 300) / 16.0) ** 2) - 26 * np.exp(-((x - 276) / 9.0) ** 2) \
        - 22 * np.exp(-((x - 326) / 8.0) ** 2) - 10 * fbm1(x, 41, 30) - 6 * fbm1(x, 42, 6)
    mountains(sc, fitz, 0.42, hx("#EED6C6"), hx("#5E6A94"), hx("#7E88A8"), snow=(90, 22), seed=41)
    mesa = 112 - 6 * fbm1(x, 43, 50) - 2 * fbm1(x, 44, 6)
    mm = mountains(sc, np.maximum(mesa, 104), 0.38, hx("#D9B98E"), hx("#8F6E5E"), hx("#9A7B62"), seed=43, stria=0.1, base=128)
    for lx0, lx1 in ((10, 140), (330, 476)):
        lake(sc, 123, 132, lx0, lx1, 0.3)
    steppe = 132 - 3 * fbm1(x, 45, 30)
    hills(sc, steppe, 0.14, hx("#E6CC8A"), hx("#A98B57"), 45, 0.2)
    rng = RR(5)
    for _ in range(70):                            # coirones
        bx = rng.randrange(W)
        if LOT[0] - 4 < bx < LOT[1] + 4:
            continue
        by = rng.randint(136, EDGE - 1)
        s = 1 + (by - 136) / 8
        tuft = (np.abs(XX - bx) < (s * 2.2) - (by - YY) * 0.6) & (YY > by - s * 2.5) & (YY <= by)
        sc.put(tuft, mix(hx("#F0D98E"), hx("#9C7B3E"), np.clip((XX - bx) / (s * 2) + 0.5, 0, 1)[..., None] * np.ones((1, 1, 3))), 0.08)
    return sc


def pampeana():
    sc = Scene("#2E7FCB", "#D4EAEF", "#E2E8DE", "#FFEBC6")
    sc.sky(126)
    sc.cloud(80, 34, 28, 15, 51, 10)
    sc.cloud(310, 26, 24, 13, 52, 9)
    sc.cloud(440, 46, 16, 9, 53, 7)
    rq = RR(8)
    cx = rq.randint(0, 30)
    while cx < W:                                  # banco de nubes bajas en el horizonte
        sc.cloud(cx, 108 + rq.randint(-4, 6), rq.randint(12, 26), rq.randint(4, 7), 200 + cx, 5)
        cx += rq.randint(45, 90)
    x = XX[0]
    hz = 124 + 1.5 * fbm1(x, 54, 60)
    hills(sc, hz, 0.6, hx("#9CC27E"), hx("#7AA068"), 54, 0.05)
    bands = [(126, 131, "#D9B85A", "#C59E44", "#A88332"), (131, 137, "#79B05A", "#5E9748", "#3F7535"),
             (137, 144, "#E3C564", "#CFA94A", "#AA8436"), (144, 150, "#6FAA55", "#52903F", "#356B2E")]
    for i, (a, b, c1, c2, c3) in enumerate(bands):
        field_rows(sc, a, b, 0, W, c1, c2, c3, 55 + i, 0.4 - i * 0.09, (2, 3 + i))
    pal = ("#8ECB72", "#3E8A4C", "#1D4E35", "#4A2E20")
    tree_round(sc, 40, 128, 18, 9, 61, 0.35, pal)       # monte lejano
    tree_round(sc, 58, 128, 14, 7, 62, 0.35, pal)
    tree_round(sc, 420, 129, 20, 10, 63, 0.33, pal)
    tree_round(sc, 446, 140, 42, 19, 64, 0.12, pal)     # ombú cercano
    # molino: torre de reticulado con luz y rueda
    mx, my = 96, 92
    for k in range(40):                            # silueta oscura detrás (lectura contra el cielo)
        for s_ in (-1, 1):
            p = (np.abs(XX - (mx + s_ * k / 6)) < 1.9) & (np.abs(YY - (my + k)) < 1.0)
            sc.put(p, hx("#2E2A3A"), 0.12)
    for a_ in range(16):
        ang = a_ / 16 * 2 * math.pi
        for t in np.linspace(2, 10, 9):
            p = (np.abs(XX - (mx + math.cos(ang) * t)) < 1.5) & (np.abs(YY - (my + math.sin(ang) * t)) < 1.5)
            sc.put(p, hx("#363244"), 0.12)
    for k in range(40):
        for s in (-1, 1):
            p = (np.abs(XX - (mx + s * k / 6)) < 0.8) & (np.abs(YY - (my + k)) < 0.8)
            sc.put(p, hx("#8E8C9E") if s < 0 else hx("#5A5868"), 0.2)
        if k % 8 == 4:
            p = (np.abs(YY - (my + k)) < 0.6) & (np.abs(XX - mx) < k / 6)
            sc.put(p, hx("#6E6C80"), 0.2)
    for a in range(16):
        ang = a / 16 * 2 * math.pi
        for t in np.linspace(2, 10, 9):
            p = (np.abs(XX - (mx + math.cos(ang) * t)) < 0.7) & (np.abs(YY - (my + math.sin(ang) * t)) < 0.7)
            sc.put(p, hx("#E6E2EE") if math.cos(ang) < 0.3 else hx("#9E9AB0"), 0.2)
    hub = np.hypot(XX - mx, YY - my) < 1.6
    sc.put(hub, hx("#C74A3E"), 0.2)
    # alambrado
    for yy in (141, 145):
        sc.put((np.abs(YY - yy) < 0.5) & ((XX < LOT[0]) | (XX > LOT[1])), hx("#8F7A68"), 0.1)
    for px in range(0, W, 14):
        if not LOT[0] < px < LOT[1]:
            post = (np.abs(XX - px) < 1) & (YY >= 138) & (YY < 149)
            sc.put(post, mix(hx("#9A6A44"), hx("#4E3222"), (XX > px)[..., None] * np.ones((1, 1, 3))), 0.1)
    return sc


def centro_sierras():
    sc = Scene("#2F7ECB", "#CFE6EE", "#DCE6E2", "#FFEBC8")
    sc.sky(112)
    sc.cloud(380, 32, 28, 16, 71, 9)
    sc.cloud(120, 22, 18, 10, 72, 6)
    x = XX[0]
    far = 96 - 44 * fbm1(x, 73, 120, 5) - 6 * fbm1(x, 76, 14)
    mountains(sc, far, 0.6, hx("#B8CFA6"), hx("#5E7C86"), hx("#7C988E"), seed=73)
    mid = 118 - 34 * fbm1(x, 74, 70, 5) - 4 * fbm1(x, 77, 10)
    mountains(sc, mid, 0.32, hx("#8CBB60"), hx("#2F5A44"), hx("#40684A"), seed=74, stria=0.05)
    near = 134 - 12 * fbm1(x, 75, 60)
    hills(sc, near, 0.22, hx("#8DBE62"), hx("#4E8446"), 75, 0.18)
    rng = RR(3)
    # pueblo serrano: casas con techo de teja, luz a la izquierda
    for hx0 in [8, 31, 52, 76, 101] + [LOT[1] + 14, LOT[1] + 40, LOT[1] + 61, LOT[1] + 92, LOT[1] + 118]:
        w_ = rng.randint(14, 18)
        h_ = rng.randint(10, 15)
        by = EDGE - 1 - rng.randint(0, 5)
        wall = (XX >= hx0) & (XX < hx0 + w_) & (YY >= by - h_) & (YY < by)
        u = (XX - hx0) / w_
        wc = mix(hx("#FFF3E0"), hx("#C9B49E"), np.clip(u * 1.2 - 0.1, 0, 1)[..., None] * np.ones((1, 1, 3)))
        sc.put(wall, wc, 0.1)
        side = (XX >= hx0 + w_) & (XX < hx0 + w_ + 4) & (YY >= by - h_ + (XX - hx0 - w_) * 0.5) & (YY < by)
        sc.put(side, hx("#9E8672"), 0.1)
        rc = rng.choice(["#C4553E", "#B4472F", "#D06A3E"])
        for k in range(6):
            roof = (np.abs(YY - (by - h_ - 1 - k)) < 0.5) & (XX >= hx0 - 2 + k) & (XX < hx0 + w_ + 2 - k + 4)
            sc.put(roof, hx(rc) * (1.15 - k * 0.05) * (1 - 0.25 * ((XX - hx0) / (w_ + 4))[..., None]), 0.1)
        win = (XX >= hx0 + 3) & (XX < hx0 + 6) & (YY >= by - h_ + 4) & (YY < by - h_ + 7)
        sc.put(win, hx("#3E6A8A"), 0.1)
        door = (XX >= hx0 + w_ - 6) & (XX < hx0 + w_ - 3) & (YY >= by - 7) & (YY < by)
        sc.put(door, hx("#6A3E26"), 0.1)
    # capilla con campanario
    cx = 46
    tower = (XX >= cx) & (XX < cx + 7) & (YY >= EDGE - 44) & (YY < EDGE)
    sc.put(tower, mix(hx("#FFF6E8"), hx("#BFA890"), np.clip((XX - cx) / 7, 0, 1)[..., None] * np.ones((1, 1, 3))), 0.1)
    bell = (XX >= cx + 2) & (XX < cx + 5) & (YY >= EDGE - 38) & (YY < EDGE - 33)
    sc.put(bell, hx("#4A3A30"), 0.1)
    for k in range(5):
        r_ = (np.abs(YY - (EDGE - 45 - k)) < 0.5) & (XX >= cx - 1 + k) & (XX < cx + 8 - k)
        sc.put(r_, hx("#C4553E"), 0.1)
    pal = ("#9CD47A", "#4A944E", "#22573A", "#5A3622")
    for cx in (0, 126, 352, 470):
        tree_round(sc, cx, EDGE - 1, rng.randint(30, 40), rng.randint(11, 14), cx + 5, 0.06, pal)
    return sc


def city(name="centro"):
    """La calle porteña (PXL, 0.7) con la luz de la 14: sol de la izquierda, sombra
    bajo balcones, toldos y cornisas, oclusión, vidrios con cielo y vereda con degradé."""
    src = Image.open(os.path.join(R.ROOT, "assets", "pixel_art", "locations", "street_%s.png" % name))
    a = np.asarray(R.restyle(src, selective=False).convert("RGBA")).astype(np.float64)
    rgb = a[..., :3]
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    line = lum < 70
    lf = line.astype(np.float64)
    under = line & ~np.roll(line, -1, axis=0)                       # borde inferior de salientes
    cast = np.zeros((H, W))
    for k, wgt in ((1, 0.6), (2, 0.5), (3, 0.36), (4, 0.2)):
        sh = np.roll(np.roll(under.astype(np.float64), k, axis=0), (k + 1) // 3, axis=1)
        cast = np.maximum(cast, sh * wgt)
    cast[:4] = 0
    up = YY < EDGE
    v = np.ones((H, W))
    v += np.where(up, 0.10 * (1 - YY / EDGE) - 0.12 * (YY / EDGE) ** 2, 0)
    v += 0.07 * (1 - XX / W) - 0.07 * (XX / W)
    v -= np.where(up & ~line, 0.72 * cast, 0)
    v -= np.where(up, 0.10 * fbm2(1, 5, 1) * 0 + 0.12 * np.clip((YY - (EDGE - 10)) / 10, 0, 1), 0)
    v += np.where(up, (fbm2(12, 3, 2) - 0.5) * 0.08, 0)
    v -= 0.22 * np.clip(1 - (YY - EDGE - 1) / 5, 0, 1) * (YY > EDGE)
    v -= 0.10 * np.clip((YY - 176) / 6, 0, 1) * (YY < 182) * (YY > EDGE)
    v -= 0.14 * np.clip((YY - 186) / 14, 0, 1)
    q = v / 0.05
    fr = q - np.floor(q)
    vq = np.where((fr > 0.35) & (fr < 0.65), np.floor(q) + (BY < (fr - 0.35) / 0.3), np.round(q)) * 0.05
    sun, shade = hx("#FFE6BC"), hx("#4A3C6A")
    c = np.where((vq > 1)[..., None], rgb + (sun - rgb) * np.clip((vq - 1) * 1.4, 0, 0.5)[..., None],
                 rgb * (1 - np.clip(1 - vq, 0, 1) * 0.9)[..., None] + shade * np.clip((1 - vq) * 0.5, 0, 0.3)[..., None])
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    mx, mn = rgb.max(-1), rgb.min(-1)
    glass = up & (b > r + 28) & (b >= g - 6) & ((mx - mn) / np.maximum(mx, 1) > 0.22)
    import facade_light as FL
    lab, n = FL.components(glass)
    sizes = np.bincount(lab.ravel(), minlength=n + 1)
    glass &= (sizes[lab] < 260)                                  # vidrios, no fachadas pintadas de celeste
    streak = ((XX + YY) % 12 < 2) | ((XX + YY) % 12 == 4)
    gl = mix(rgb, mix(hx("#CFEFF8"), hx("#3A78A8"), np.clip((YY % 14) / 14, 0, 1)), 0.45)
    gl = np.where(streak[..., None], gl + (255 - gl) * 0.35, gl) * (1 - 0.5 * cast)[..., None]
    c = np.where(glass[..., None], gl, c)
    c = np.where(line[..., None], rgb * (1 - 0.2 * cast)[..., None], c)
    # la calle de enfrente ya no tiene cielo: un velo de aire cálido arriba da profundidad
    c = mix(c, hx("#F6E2C6"), np.clip(1 - YY / 60, 0, 1) * 0.16 * up)
    c = mix(c, hx("#E8DCCB"), 0.14 * up)                          # el fondo retrocede: el negocio manda
    # cada edificio del fondo: más luz en su borde izquierdo, sombra en el derecho
    edges = (np.abs(np.diff(rgb.mean(-1), axis=1, prepend=0)) > 40) & up
    colsum = edges.sum(0)
    bounds = [0] + [x for x in range(1, W) if colsum[x] > 60] + [W]
    for a_, b_ in zip(bounds[:-1], bounds[1:]):
        if b_ - a_ < 20:
            continue
        u = np.clip((XX - a_) / (b_ - a_), 0, 1)
        f = np.where(up & (XX >= a_) & (XX < b_), 1.08 - 0.24 * u, 1.0)
        c = c * f[..., None]
    out = np.dstack([np.clip(c, 0, 255), a[..., 3]])
    grade(out)
    out = np.clip(out, 0, 255)
    return Image.fromarray(out.astype(np.uint8), "RGBA")


VERGE = {   # pasto claro, pasto oscuro, tierra del borde
    "noa": ("#D9B565", "#9C7A3E", "#A9734A"), "nea": ("#6DB04E", "#2F6A38", "#9A3C28"),
    "cuyo": ("#9CBF5E", "#557E3A", "#9E6E4A"), "patagonia": ("#E2C67A", "#9A7E46", "#8E7050"),
    "pampeana": ("#86C266", "#3F8040", "#6E5236"), "centro_sierras": ("#8CC562", "#3E7A40", "#8A6446"),
}


def clean_orphans(sc, passes=2):
    """Limpieza de cúmulos: un píxel del paisaje sin vecino de su color toma el color
    más común de sus vecinos (el cielo, con sus franjas tramadas, no se toca)."""
    land = sc.depth < 0.99
    for _ in range(passes):
        c = sc.rgb.astype(np.int64)
        key = (c[..., 0] << 16) | (c[..., 1] << 8) | c[..., 2]
        nb = [np.roll(np.roll(key, dy, 0), dx, 1) for dy in (-1, 0, 1) for dx in (-1, 0, 1) if dy or dx]
        same = np.zeros(key.shape, dtype=bool)
        for n in nb:
            same |= n == key
        orphan = land & ~same
        if not orphan.any():
            break
        st = np.stack(nb[:])
        ys, xs = np.nonzero(orphan)
        for y, x in zip(ys, xs):
            vals, cnt = np.unique(st[:, y, x], return_counts=True)
            k = vals[cnt.argmax()]
            sc.rgb[y, x] = [(k >> 16) & 255, (k >> 8) & 255, k & 255]


def verge(sc, name):
    """Borde entre el paisaje y la vereda: tierra con matas de pasto y la sombra de
    apoyo de cada cosa que llega al piso (que nada quede flotando)."""
    gl, gd, soil = (hx(c) for c in VERGE[name])
    n = fbm2(2, 400 + len(name), 2)
    hgt = 2 + (n * 5).astype(int)                      # alto de cada mata
    tuft = (YY >= EDGE - hgt) & (YY < EDGE) & ~sc.near
    lt = np.clip(0.75 - (XX % 3 == 2) * 0.35 - (EDGE - 1 - YY) * -0.08, 0, 1)
    sc.put(tuft & (YY < EDGE - 1), mix(gd, gl, lt), 0.03)
    base = (YY >= EDGE - 2) & (YY < EDGE)
    sc.put(base & ~sc.near, mix(soil, gd, 0.3 + 0.3 * (YY == EDGE - 2)), 0.02)
    # sombra de apoyo de árboles, cactus y casas: hacia la derecha, sobre el borde
    feet = sc.near & (np.roll(~sc.near, -1, axis=0) | (YY >= EDGE - 1)) & (YY >= EDGE - 6)
    sh = np.zeros((H, W), dtype=bool)
    for k in range(1, 7):
        sh |= np.roll(feet, k, axis=1) & (YY >= EDGE - 3)
    sh &= ~sc.near & (YY < EDGE)
    sc.rgb[sh] = sc.rgb[sh] * 0.62 + hx("#2A1E36") * 0.38 * 0.4


REGIONS = {"noa": noa, "nea": nea, "cuyo": cuyo, "patagonia": patagonia,
           "pampeana": pampeana, "centro_sierras": centro_sierras}
OLD = {"noa": L.noa, "nea": L.nea, "cuyo": L.cuyo, "patagonia": L.patagonia,
       "pampeana": L.pampeana, "centro_sierras": L.centro}


# ------------------------------------------------------------------ vereda

BUNT = []


def _bunting(cv, x1, x2, y):
    """Banderines con caída y altura propias de cada lado (antes eran calcados)."""
    rr = random.Random(x1 * 31 + x2 + VAR * 7)
    y = y + rr.randint(-6, 3)
    x1 = x1 + rr.randint(-14, 6)
    x2 = x2 + rr.randint(-6, 14)
    sag = rr.uniform(3.0, 8.0)
    cols = rr.choice([("C3", "W"), ("C3", "W", "Y2"), ("R2", "W", "C3")])
    BUNT.append((x1, x2, y))
    for x in range(x1, x2):
        yy = y + int(sag * math.sin(math.pi * (x - x1) / max(1, x2 - x1)))
        cv.put(x, yy, "x")
        if (x - x1) % 5 == 2:
            c = cols[((x - x1) // 5) % len(cols)]
            cv.put(x, yy + 1, c); cv.put(x - 1, yy + 1, c); cv.put(x + 1, yy + 1, c); cv.put(x, yy + 2, c)


def _trace_fg(name):
    """Corre el paisaje viejo y separa lo que pintaron ground/props/road/bunting."""
    fn = OLD[name]
    code = fn.__code__
    keep = np.zeros((H, W), dtype=bool)
    props = np.zeros((H, W), dtype=bool)
    stack = []

    def arr(cv):
        return np.asarray(cv.img).copy()

    def prof(frame, event, arg):
        if event == "call" and frame.f_back is not None and frame.f_back.f_code is code:
            cv = frame.f_back.f_locals.get("cv")
            if cv is not None:
                stack.append((frame, frame.f_code.co_name, arr(cv), cv))
        elif event == "return" and stack and stack[-1][0] is frame:
            _, nm, before, cv = stack.pop()
            ch = (arr(cv) != before).any(-1)
            if nm in ("ground", "road", "props", "bunting"):
                keep[ch] = True
                if nm == "props":
                    props[ch] = True
            else:
                keep[ch] = False
                props[ch] = False
    BUNT.clear()
    real_b = L.bunting
    L.bunting = _bunting
    sys.setprofile(prof)
    try:
        cv = fn(random.Random(name + str(VAR)))
    finally:
        sys.setprofile(None)
    img = R.restyle(cv.img.copy(), selective=False)
    # máscara exacta de la utilería: el mismo paisaje sin props() (un píxel del banco
    # del mismo color que la laja también es banco, no vereda)
    real = L.props
    L.props = lambda *a, **k: None
    try:
        bare = np.asarray(fn(random.Random(name + str(VAR))).img).copy()
    finally:
        L.props = real
        L.bunting = real_b
    withp = np.asarray(cv.img)
    diff = (withp != bare).any(-1)
    pm = diff.copy()
    for y in range(H):
        xs = np.nonzero(diff[y])[0]
        if len(xs) > 1:
            for x0, g in zip(xs[:-1], np.diff(xs)):
                if 1 < g <= 4:
                    pm[y, x0:x0 + g] = True
    props = pm & (YY > 100)
    keep |= props
    return np.asarray(img.convert("RGBA")).astype(np.float64), keep, props


def _h(a, b):
    return ((a * 73856093) ^ (b * 19349663)) % 1000 / 1000.0


def paver_relief():
    """Lajas de la vereda y adoquines de la calle con bisel: tono propio por pieza,
    filo de luz arriba-izquierda y sombra abajo-derecha (misma grilla que landscapes.ground/road)."""
    v = np.zeros((H, W))
    rows = [EDGE + 1, EDGE + 8, EDGE + 16, EDGE + 25, 182]
    for j in range(4):
        y0, y1 = rows[j], rows[j + 1]
        off = (j % 2) * 11
        for x0 in range(-off, W, 22):
            tid = _h(j, x0 + 100)
            v[y0 + 1:y1, max(0, x0):max(0, x0 + 21)] += (tid - 0.5) * 0.16
            v[y0 + 1, max(0, x0 + 1):max(0, x0 + 21)] += 0.13
            v[y1 - 1, max(0, x0):max(0, x0 + 21)] -= 0.13
            if _h(j + 7, x0) < 0.35:                       # laja gastada: mancha más oscura
                wx = x0 + 4 + int(_h(j, x0 + 3) * 10)
                v[y0 + 2:y1 - 2, max(0, wx):max(0, wx + 4)] -= 0.07
            if 0 <= x0 + 20 < W:
                v[y0 + 1:y1, x0 + 20] -= 0.07
            if 0 <= x0 + 1 < W:
                v[y0 + 1:y1, x0 + 1] += 0.04
    for j, y in enumerate(range(187, H, 4)):
        for x0 in range((j % 2) * 4, W, 8):
            tid = _h(j + 50, x0)
            v[y:y + 3, x0:x0 + 7] += (tid - 0.5) * 0.12
            v[y, x0:x0 + 7] += 0.08
            if y + 2 < H:
                v[y + 2, x0:x0 + 7] -= 0.07
    return v


def light_ground(rgb, keep, props):
    """Vereda y calle: degradé de sol, oclusión contra el fondo, sombras de la utilería."""
    out = rgb.copy()
    walk = keep & ~props & (YY > EDGE)
    v = np.ones((H, W))
    v += 0.10 * (1 - XX / W) - 0.06 * (XX / W)
    v -= 0.22 * np.clip(1 - (YY - EDGE - 1) / 5, 0, 1) * (YY > EDGE)     # contacto con el fondo
    v -= 0.10 * np.clip((YY - 176) / 6, 0, 1) * (YY < 182)               # cordón proyecta borde
    v += np.where((YY >= 182) & (YY < 184), 0.10, 0)                     # filo del cordón con luz
    v -= 0.14 * np.clip((YY - 186) / 14, 0, 1)                           # calle: más honda adelante
    v -= np.where((YY >= 186) & (YY < 189), 0.16 - (YY - 186) * 0.05, 0)  # el cordón tapa la luz
    v -= 0.08 * np.clip(1 - (YY - EDGE) / 31, 0, 1) * (YY > EDGE) * (YY < 182)  # vereda más oscura junto a los edificios
    v += (fbm2(7, 91, 2) - 0.5) * 0.06
    v += paver_relief()
    q = v / 0.05
    fr = q - np.floor(q)
    vq = np.where((fr > 0.35) & (fr < 0.65), np.floor(q) + (BY < (fr - 0.35) / 0.3), np.round(q)) * 0.05
    sun, shade = hx("#FFE6BC"), hx("#4A3C6A")
    c = out[..., :3]
    c = np.where((vq > 1)[..., None], c + (sun - c) * np.clip((vq - 1) * 1.4, 0, 0.5)[..., None],
                 c * (1 - np.clip(1 - vq, 0, 1) * 0.9)[..., None] + shade * np.clip((1 - vq) * 0.5, 0, 0.3)[..., None])
    out[..., :3] = np.where((keep & (YY > EDGE))[..., None], c, out[..., :3])
    # sombra de cada objeto de utilería: hacia atrás-derecha sobre la vereda
    sh = np.zeros((H, W), dtype=bool)
    ys, xs = np.nonzero(props)
    if len(ys):
        lab = np.zeros((H, W), dtype=np.int32)
        n = 0
        for y0, x0 in zip(ys, xs):
            if lab[y0, x0]:
                continue
            n += 1
            st = [(y0, x0)]
            lab[y0, x0] = n
            pts = []
            while st:
                y, x = st.pop()
                pts.append((y, x))
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        yy, xx = y + dy, x + dx
                        if 0 <= yy < H and 0 <= xx < W and props[yy, xx] and not lab[yy, xx]:
                            lab[yy, xx] = n
                            st.append((yy, xx))
            yb = max(p[0] for p in pts)
            if yb < EDGE + 4:
                continue
            for y, x in pts:
                hgt = yb - y
                sx = int(x + 1 + hgt * 0.55)
                sy = int(yb - hgt * 0.22)
                for k in (0, 1):
                    if 0 <= sx + k < W and EDGE < sy <= 181:
                        sh[sy, sx + k] = True
    sh &= ~props
    dark = hx("#2A1E36")
    out[..., :3] = np.where(sh[..., None], out[..., :3] * 0.58 + dark * 0.42 * 0.5, out[..., :3])
    # volumen de cada objeto: degradé arriba-claro/abajo-oscuro y izquierda-cálida/derecha-fría
    if props.any():
        import facade_light as FL
        labp, np_ = FL.components(props)
        for i in range(1, np_ + 1):
            mm = labp == i
            ys_, xs_ = np.nonzero(mm)
            if len(ys_) < 8:
                continue
            uy = (YY - ys_.min()) / max(1, ys_.max() - ys_.min())
            ux = (XX - xs_.min()) / max(1, xs_.max() - xs_.min())
            f = 1.10 - 0.24 * uy - 0.12 * ux
            q = np.floor(f / 0.06 + BY * 0.6) * 0.06
            pc = out[..., :3] * q[..., None]
            pc = np.where((q > 1)[..., None], pc + (hx("#FFE6BC") - pc) * 0.15, pc)
            out[..., :3] = np.where(mm[..., None], pc, out[..., :3])
    # la utilería: luz de costado (izquierda cálida, derecha fría)
    if props.any():
        lt = np.zeros((H, W))
        left_open = props & ~np.roll(props, 1, axis=1)
        right_open = props & ~np.roll(props, -1, axis=1)
        pc = out[..., :3]
        pc = np.where(left_open[..., None], pc + (sun - pc) * 0.25, pc)
        pc = np.where(right_open[..., None], pc * 0.78, pc)
        out[..., :3] = np.where(props[..., None], pc, out[..., :3])
    return out


ROADS = {"noa": "ripio", "patagonia": "ripio", "pampeana": "tierra",
         "nea": "asfalto", "cuyo": "asfalto", "centro_sierras": "adoquin"}


def street(out, name):
    """Cordón con canto de luz y cara en sombra, y calle con material propio de la región
    (asfalto gastado, ripio, tierra con huellas o adoquín), más oscura bajo el cordón."""
    rr = random.Random(VAR * 17 + len(name))
    curb_top, curb_face = 182, 183
    c = out[..., :3]
    c[182] = c[182] * 1.18 + 12
    c[183:186] = c[183:186] * np.array([0.78, 0.70, 0.64])[:, None, None]
    kind = ROADS.get(name, "asfalto")
    y0 = 186
    ry = (YY[y0:] - y0) / (H - y0)
    n1 = fbm2(5, 900 + VAR, 2)[y0:]
    n2 = fbm2(1.5, 901 + VAR, 1)[y0:]
    if kind == "asfalto":
        ramp = [hx(x) for x in ("#3E3836", "#4C4542", "#5A524E", "#69605B", "#787069")]
        val = 0.55 + (n1 - 0.5) * 0.4 + (n2 > 0.8) * 0.12 - ry * 0.1
    elif kind == "ripio":
        ramp = [hx(x) for x in ("#7A5E48", "#94765C", "#AD8E70", "#C4A584", "#D8BC9A")]
        val = 0.55 + (n1 - 0.5) * 0.35 + (n2 > 0.72) * 0.2 - (n2 < 0.2) * 0.2 - ry * 0.12
    elif kind == "tierra":
        ramp = [hx(x) for x in ("#5E4030", "#77523C", "#8E6448", "#A47656", "#B88966")]
        rut = (np.abs(YY[y0:] - 190) < 1.2) | (np.abs(YY[y0:] - 196) < 1.2)
        val = 0.6 + (n1 - 0.5) * 0.3 - rut * 0.25 + (np.abs(YY[y0:] - 192) < 1) * 0.12
    else:
        ramp = [hx(x) for x in ("#5E5550", "#756B64", "#8C8178", "#A3978C", "#B8ACA0")]
        row = (YY[y0:] - y0) // 4
        off = (row % 2) * 4
        cx = (XX[y0:] + off) % 8
        cy = (YY[y0:] - y0) % 4
        val = 0.55 + (n1 - 0.5) * 0.3 + (cy == 0) * 0.18 - (cy == 3) * 0.25 - (cx == 7) * 0.25
    val = val - np.where(YY[y0:] < y0 + 3, 0.28 - (YY[y0:] - y0) * 0.09, 0)    # sombra del cordón
    rp = np.array(ramp)
    idx = np.clip(np.round(np.clip(val, 0, 1) * (len(rp) - 1)), 0, len(rp) - 1).astype(int)
    road = rp[idx]
    if kind == "asfalto":                       # rayas de carril gastadas
        dash = (YY[y0:] >= 192) & (YY[y0:] < 194) & (((XX[y0:] + 6) % 32) < 16) & (n2 < 0.82)
        road = np.where(dash[..., None], hx("#E9D9A8") * (0.9 + 0.1 * (n1[..., None] > 0.5)), road)
        for _ in range(6):                      # grietas
            x = rr.randrange(W); y = rr.randrange(y0 + 3, H)
            for k in range(rr.randint(4, 9)):
                if 0 <= x < W and y0 <= y < H:
                    road[y - y0, x] = rp[0]
                x += 1; y += rr.choice((-1, 0, 0, 1))
    c[y0:] = road
    # vereda: manchas y grietas sueltas
    for _ in range(10):
        x = rr.randrange(4, W - 4); y = rr.randrange(EDGE + 4, 180)
        if rr.random() < 0.5:
            for k in range(rr.randint(3, 6)):
                if EDGE < y < 181:
                    c[y, x] *= 0.8
                x += 1; y += rr.choice((-1, 0, 1))
        else:
            st = (np.hypot((XX - x) / 4, (YY - y) / 1.6) < 1)
            c[st] *= 0.93
    out[..., :3] = c


def render(name):
    sc = REGIONS[name]()
    verge(sc, name)
    near = sc.depth < 0.16
    g = sc.rgb.mean(-1, keepdims=True)
    warm = (sc.rgb - g) * 1.12 + g + np.array([6, 2, -6.0])     # +saturación y calidez en lo cercano
    sc.rgb = np.where(near[..., None], warm, sc.rgb)
    sc.quantize(48, rows=EDGE)
    clean_orphans(sc)
    fg, keep, props = _trace_fg(name)
    out = np.dstack([sc.rgb, np.full((H, W), 255.0)])
    fgl = light_ground(fg, keep, props)
    m = keep & (fg[..., 3] > 0)
    if name == "pampeana":                          # vereda de ladrillo terroso (no verde)
        walk = keep & ~props & (YY > EDGE) & (YY < 182)
        lum = fgl[..., :3] @ np.array([0.299, 0.587, 0.114])
        t = np.clip((lum - 60) / 150, 0, 1)
        tan = mix(hx("#7A4A32"), hx("#E8C49A"), t)
        fgl[..., :3] = np.where(walk[..., None], tan, fgl[..., :3])
    out[m] = fgl[m]
    # postes de los banderines (antes colgaban del aire)
    posts = []
    for x1, x2, y in BUNT[:2]:
        posts += [(x1, y), (x2, y)]
    for x, yt in posts:
        for y in range(yt - 2, EDGE + 8):
            out[y, x, :3] = hx("#7A4A30")
            out[y, x + 1, :3] = hx("#4E2C1C")
            out[y, x - 1, :3] = mix(out[y, x - 1, :3], hx("#B07A4E"), 0.6)
        out[yt - 3, x - 1:x + 2, :3] = hx("#3D1B0B")
        for k in range(2, 7):                        # sombrita del poste hacia atrás-derecha
            out[EDGE + 7 - k // 3, x + k, :3] *= 0.7
    # oclusión del paisaje justo sobre la línea de vereda (los pies de todo)
    for k, f in ((1, 0.72), (2, 0.82), (3, 0.9)):
        y = EDGE - k
        row = ~m[y]
        out[y, row, :3] *= f
    # la línea de fondo de la vereda: medio tono (no un trazo negro) y una fila de aire claro arriba
    out[EDGE, :, :3] = mix(out[EDGE, :, :3], out[EDGE + 2, :, :3], 0.45)
    out[EDGE - 1, ~m[EDGE - 1], :3] = mix(out[EDGE - 1, ~m[EDGE - 1], :3], hx("#F2E4CC"), 0.12)
    # sombra de apoyo elíptica bajo cada objeto de la vereda
    import facade_light as FL
    labp, np_ = FL.components(props & (YY > EDGE))
    for i in range(1, np_ + 1):
        ys_, xs_ = np.nonzero(labp == i)
        if len(ys_) < 8:
            continue
        cx_, yb = xs_.mean(), ys_.max()
        rx_ = max(3, (xs_.max() - xs_.min()) * 0.6)
        ell = (np.hypot((XX - cx_ - 1) / rx_, (YY - yb - 0.5) / 1.6) < 1) & ~props
        out[ell, :3] = out[ell, :3] * 0.62 + hx("#3A2E52") * 0.38 * 0.5
    street(out, name)
    grade(out)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def lamp_glow(out, props):
    """Faroles de la vereda: halo cálido en dos anillos netos y charco de luz en la vereda."""
    rgb = out[..., :3]
    yel = props & (rgb[..., 0] > 220) & (rgb[..., 1] > 170) & (rgb[..., 2] < 150)
    import facade_light as FL
    lab, n = FL.components(yel)
    warm = hx("#FFD98C")
    for i in range(1, n + 1):
        ys, xs = np.nonzero(lab == i)
        if len(ys) < 6 or len(ys) > 40 or ys.mean() > EDGE - 10:     # sólo cabezas de farol
            continue
        cx, cy = xs.mean(), ys.mean()
        d = np.hypot(XX - cx, (YY - cy) * 1.1)
        r1 = (d < 7) & ~props
        r2 = (d >= 7) & (d < 11) & ~props & (BY < 0.5)
        out[r1, :3] = mix(out[r1, :3], warm, 0.30)
        out[r2, :3] = mix(out[r2, :3], warm, 0.18)
        # charco de luz al pie
        pool = (np.hypot((XX - cx) / 12, (YY - 179) / 2.5) < 1) & ~props & (YY > EDGE)
        out[pool, :3] = mix(out[pool, :3], warm, 0.22)


def grade(out):
    """Gradación única de la escena (la misma que fachadas e interiores): luces que
    tiran al ámbar, sombras al violeta frío, un poco más de saturación."""
    c = out[..., :3]
    lum = c @ np.array([0.299, 0.587, 0.114]) / 255
    g = c.mean(-1, keepdims=True)
    c = (c - g) * 1.06 + g
    hi = np.clip((lum - 0.6) / 0.4, 0, 1)[..., None]
    lo = np.clip((0.4 - lum) / 0.4, 0, 1)[..., None]
    c = c + (hx("#FFE2B0") - c) * hi * 0.10
    c = c + (hx("#3E3870") - c) * lo * 0.14
    out[..., :3] = c


def cloud_sprite(w, h, seed):
    """Nube suelta para SceneAmbient (cruza el cielo): mismo volumen que las pintadas,
    sin contorno, borde tramado sobre transparente."""
    rng = random.Random(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    cx, cy, sx, sy = w / 2, h * 0.58, w * 0.36, h * 0.42
    f = np.zeros((h, w))
    for _ in range(6):
        px = cx + rng.uniform(-0.85, 0.85) * sx
        py = cy + rng.uniform(-0.55, 0.05) * sy
        r = rng.uniform(0.38, 0.6) * sx
        f += np.exp(-(((xx - px) / r) ** 2 + ((yy - py) / (r * sy / sx * 1.3)) ** 2))
    f += 0.6 * np.exp(-(((xx - cx) / (sx * 1.25)) ** 2 + ((yy - cy - sy * 0.3) / (sy * 0.32)) ** 2))
    f[-2:] = 0
    gy, gx = np.gradient(f)
    lit = np.clip(0.55 + (-gy * 0.9 - gx * 0.5) * -6, 0, 1)
    lit = np.clip(lit - np.clip((yy - cy) / (sy * 1.2), 0, 1) * 0.5, 0, 1)
    top_c, mid_c, bel_c = hx("#FFF8EA"), hx("#F0E4D8"), hx("#B9B4CE")
    c = np.where((lit > 0.5)[..., None], mix(mid_c, top_c, (lit - 0.5) * 2), mix(bel_c, mid_c, lit * 2))
    B = BAYER[yy.astype(int) % 4, xx.astype(int) % 4]
    q = np.floor(lit * 5 + B * 0.8) / 5
    c = np.where((q > 0.5)[..., None], mix(mid_c, top_c, (q - 0.5) * 2), mix(bel_c, mid_c, q * 2))
    edge = np.clip((f - 0.5) / 0.3, 0, 1)
    keep = edge > B * 0.9 + 0.05
    out = np.zeros((h, w, 4))
    out[..., :3] = c
    out[..., 3] = np.where(keep, 255, 0)
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")


def main(only=None):
    global VAR
    d = os.path.join(R.ROOT, "assets", "escenarios", "locations")
    import json
    world = json.load(open(os.path.join(R.ROOT, "data", "world.json"), encoding="utf8"))
    for i, z in enumerate(world["zones"]):
        reg = z.get("street", z["id"])
        if reg not in REGIONS or (only and z["id"] not in only and reg not in only):
            continue
        VAR = 1 + i
        render(reg).save(os.path.join(d, "street_%s.png" % z["id"]))
        print("provincia:", z["id"])
    VAR = 0
    for name in REGIONS:
        if only and name not in only:
            continue
        render(name).save(os.path.join(d, "street_%s.png" % name))
        print("paisaje:", name)
    if not only or "nubes" in only:
        e = os.path.join(R.ROOT, "assets", "escenarios", "effects")
        for i, (w, h) in enumerate(((40, 16), (56, 20), (72, 26))):
            cloud_sprite(w, h, 300 + i).save(os.path.join(e, "amb_cloud_%d.png" % i))
        print("nubes sueltas: 3")
    if not only or "centro" in only:
        city("centro").save(os.path.join(d, "street_centro.png"))
        print("ciudad: centro")


if __name__ == "__main__":
    main(sys.argv[1:] or None)
