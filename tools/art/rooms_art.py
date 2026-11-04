"""12.2: habitaciones de los interiores (pared, techo, piso, ventana y luz).

Reemplaza la habitación plana de PXL (rooms.px.js) por una pintada con luz:
  - cada superficie tiene su rampa de paleta (6-8 tonos cálidos de la guía) y
    un mapa de valor: luz general, oclusión bajo la cornisa y contra la pared,
    charcos de luz de cada lámpara del techo (en la pared y en el piso), la luz
    de la ventana que cae al piso y una viñeta suave hacia los costados (la
    habitación "se cierra" en vez de cortarse en seco en el borde);
  - el valor se cuantiza a la rampa con tramado Bayer sólo en franjas angostas
    (pixel art limpio, sin degradés);
  - el piso tiene perspectiva: las filas crecen hacia adelante y las juntas
    fugan hacia el centro, con contacto oscuro contra el zócalo;
  - texturas por material: revoque a la cal, adobe con paja, ladrillo visto con
    junta, azulejo con brillo, chapa acanalada con óxido, tablas rústicas,
    boiserie, pintura con friso; pisos de cemento, cerámica, madera, damero y goma.

render(wall, floor, tier, lamps=[x...], window_rect=(x, y, w, h) | None) -> PIL RGBA 400x170
Lo llama tools/art/pxl/compose_interiors.py.
"""
import math

import numpy as np
from PIL import Image

W, H = 400, 170
WALL = 110
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
YY, XX = np.mgrid[0:H, 0:W].astype(np.float64)
BY = BAYER[YY.astype(int) % 4, XX.astype(int) % 4]


def hx(c):
    c = c.lstrip("#")
    return np.array([int(c[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.uint8)


RAMPS = {
    "cal": ["#5E5047", "#7A6A5E", "#958372", "#AE9C88", "#C5B49E", "#D8C9B2", "#E7DBC6", "#F2EADA"],
    "adobe": ["#4E2C1E", "#683C29", "#7F4D35", "#966043", "#AB7352", "#BE8763", "#CF9B77", "#DEB08E"],
    "brick": ["#3C1812", "#56231A", "#6E2E21", "#86392A", "#9D4733", "#B2573E", "#C46B4E", "#D48563"],
    "mortar": ["#6A5C50", "#857566", "#9E8D7C", "#B4A391", "#C7B7A4"],
    "tile_w": ["#6E7A80", "#8A969C", "#A3AFB4", "#BAC5C9", "#CED8DA", "#DEE6E7", "#EBF1F1", "#F7FAFA"],
    "tile_c": ["#1D4A66", "#24607F", "#2E7698", "#3E8DB0", "#58A6C6", "#7BBFD8"],
    "steel": ["#2E343A", "#3C444B", "#4C555D", "#5D6770", "#6F7A84", "#838E98", "#98A3AC", "#B0BAC2"],
    "rust": ["#4A2414", "#62301B", "#7A3E22", "#94502C", "#A9643A"],
    "plank": ["#2E1A10", "#3E2416", "#50301D", "#623C25", "#74492D", "#875837", "#9A6842", "#AD7A50"],
    "panel": ["#3A2012", "#4C2A18", "#5F361F", "#734327", "#875131", "#9B613B", "#AE7247"],
    "cream": ["#6A5A48", "#84725C", "#9C8970", "#B29E84", "#C6B398", "#D7C6AC", "#E5D7C0", "#F0E6D3"],
    "celeste": ["#2E4C5C", "#3B5E70", "#4A7284", "#5A8698", "#6C9AAC", "#80AEBF", "#96C1D0", "#AED4E0"],
    "celeste_low": ["#1E3644", "#284654", "#335666", "#3F6778", "#4C788A"],
    "green_low": ["#1C3A2A", "#244A35", "#2D5B41", "#386C4E", "#447E5C"],
    "beam": ["#22130C", "#2F1A10", "#3E2416", "#4F2F1C", "#623C24", "#764A2E"],
    "cement": ["#45413F", "#544F4C", "#635D59", "#736C67", "#837B75", "#948B84", "#A59C94", "#B6ADA4"],
    "ceram": ["#77695C", "#8E7F70", "#A49483", "#B8A895", "#CABAA6", "#D9CBB8", "#E6DACA", "#F1E8DB"],
    "floor_wood": ["#3A2012", "#4B2A18", "#5D351F", "#704127", "#834E30", "#975C39", "#AA6B43", "#BC7B4E"],
    "check_w": ["#8C8174", "#A49888", "#BAAE9D", "#CEC3B1", "#DFD5C4", "#ECE4D5"],
    "check_d": ["#1E1A1E", "#282327", "#332D31", "#3F383C", "#4C4448"],
    "rubber": ["#18171B", "#201F24", "#29282E", "#333238", "#3E3C43", "#4A4850"],
    "base_wood": ["#2A170E", "#3B2114", "#4E2C1B", "#623823", "#77452C", "#8C5436"],
    "frame": ["#2A170E", "#3B2114", "#4E2C1B", "#623823", "#77452C", "#8C5436", "#A0663F"],
    "sky": ["#5E9CC8", "#73B0D8", "#8AC3E4", "#A3D4EE", "#BEE3F4"],
    "city": ["#6E7F96", "#8293A8", "#98A8BA", "#AEBCCB"],
    "leaf": ["#2E5A3A", "#3B7048", "#4C8758", "#62A06A"],
}
R = {k: np.array([hx(c) for c in v]) for k, v in RAMPS.items()}


def vnoise(scale, seed, octaves=2):
    """Ruido de valor suave (0..1) del tamaño del lienzo."""
    rng = np.random.default_rng(seed)
    out = np.zeros((H, W))
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        s = max(1.0, scale / (2 ** o))
        gw, gh = int(W / s) + 3, int(H / s) + 3
        g = rng.random((gh, gw))
        fx, fy = XX / s, YY / s
        x0, y0 = np.floor(fx).astype(int), np.floor(fy).astype(int)
        tx, ty = fx - x0, fy - y0
        tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)
        a = g[y0, x0] * (1 - tx) + g[y0, x0 + 1] * tx
        b = g[y0 + 1, x0] * (1 - tx) + g[y0 + 1, x0 + 1] * tx
        out += (a * (1 - ty) + b * ty) * amp
        tot += amp
        amp *= 0.5
    return out / tot


def speck(seed, p):
    return np.random.default_rng(seed).random((H, W)) < p


class Canvas:
    def __init__(self):
        self.rgb = np.zeros((H, W, 3), dtype=np.uint8)

    def fill(self, mask, ramp, value, band=0.3):
        """Cuantiza value (0..1) a la rampa; tramado Bayer sólo en la franja de transición."""
        rp = R[ramp]
        n = len(rp)
        value = np.broadcast_to(value, (H, W))
        f = np.clip(value, 0, 0.999) * n
        base = np.floor(f)
        frac = f - base
        lo = 1.0 - band
        t = np.clip((frac - lo) / band, 0, 1)
        idx = np.clip(base + (BY < t), 0, n - 1).astype(int)
        self.rgb[mask] = rp[idx[mask]]

    @staticmethod
    def rect(x0, y0, x1, y1):
        return (XX >= x0) & (XX < x1) & (YY >= y0) & (YY < y1)

    def darken(self, mask, k):
        self.rgb[mask] = (self.rgb[mask] * k).astype(np.uint8)


# ------------------------------------------------------------------ luz
def light_map(lamps, window):
    """Valor de luz base para pared (y < 110) y piso."""
    v = np.zeros((H, W))
    wall = YY < WALL
    v[wall] = 0.58 - 0.2 * np.exp(-(YY[wall] - 8) / 16.0) - 0.05 * np.clip((YY[wall] - 92) / 18, 0, 1)
    fl = ~wall
    s = (YY[fl] - WALL) / (H - WALL)
    v[fl] = 0.5 + 0.12 * s - 0.24 * np.exp(-(YY[fl] - WALL) / 4.5)
    for lx in lamps:
        cone = np.exp(-((XX - lx) / 28.0) ** 2 - ((YY - 30) / 40.0) ** 2) * 0.27
        pool = np.exp(-((XX - lx) / 40.0) ** 2 - ((YY - 138) / 15.0) ** 2) * 0.3
        v += np.where(wall, cone, pool)
    if window:
        wx, wy, ww, wh = window
        cx = wx + ww / 2
        glow = np.exp(-((XX - cx) / (ww * 0.9)) ** 2 - ((YY - (wy + wh / 2)) / (wh * 1.1)) ** 2) * 0.09
        t = np.clip((YY - WALL) / 40.0, 0, 1)
        half = ww * 0.5 + t * 10
        patch = (np.abs(XX - (cx + t * 14)) < half) & (YY >= WALL + 2) & (YY < WALL + 40)
        v += np.where(wall, glow, 0) + patch * 0.1 * (1 - t * 0.6)
    v -= 0.16 * ((XX - W / 2) / (W / 2)) ** 4
    return v


# ------------------------------------------------------------------ paredes
def wall_kind(cv, kind, v, seed):
    wall = YY < WALL
    n1 = vnoise(22, seed, 3)
    n2 = vnoise(5, seed + 1, 2)
    if kind == "cal":
        val = v + (n1 - 0.5) * 0.015 + (n2 - 0.5) * 0.012
        cv.fill(wall, "cal", val)
        _wainscot(cv, "green_low", 84, v)
    elif kind == "adobe":
        straw = speck(seed + 3, 0.05)
        val = v + (n1 - 0.5) * 0.03 + (n2 - 0.5) * 0.02 - straw * 0.05 + speck(seed + 4, 0.03) * 0.06
        cv.fill(wall, "adobe", val)
    elif kind == "ladrillo":
        rows = (YY // 6).astype(int)
        off = (rows % 2) * 7
        bx = ((XX + off) // 14).astype(int)
        mortar = ((YY % 6) == 5) | (((XX + off) % 14) == 13)
        tone = np.random.default_rng(seed).random((40, 40))[rows % 40, bx % 40]
        local = np.where(((YY % 6) == 0) & ~mortar, 0.06, 0) - np.where(((YY % 6) == 4) & ~mortar, 0.05, 0)
        cv.fill(wall & ~mortar, "brick", v + (tone - 0.5) * 0.16 + local + (n2 - 0.5) * 0.05)
        cv.fill(wall & mortar, "mortar", v - 0.05 + (n2 - 0.5) * 0.08)
    elif kind == "azulejo":
        tile = 10
        lx, ly = XX % tile, YY % tile
        grout = (lx == 0) | (ly == 0)
        gloss = ((lx + ly) > 2) & ((lx + ly) < 5) & (lx > 0) & (ly > 0)
        bev = np.where((lx == 1) | (ly == 1), 0.05, 0) - np.where((lx == tile - 1) | (ly == tile - 1), 0.06, 0)
        cv.fill(wall & ~grout, "tile_w", v + 0.05 + bev + gloss * 0.12)
        cv.fill(wall & grout, "mortar", v + 0.02)
        band = cv.rect(0, 60, W, 70)
        cv.fill(band & ~grout, "tile_c", v + 0.05 + bev + gloss * 0.12)
    elif kind == "chapa":
        ph = (XX % 8) / 8.0
        ridge = np.sin(ph * 2 * math.pi) * 0.16
        cv.fill(wall, "steel", v + ridge + (n2 - 0.5) * 0.04)
        rng = np.random.default_rng(seed + 5)
        rust = np.zeros((H, W), dtype=bool)
        rust2 = np.zeros((H, W), dtype=bool)
        bolts = [(bx, y) for y in (24, 64) for bx in range(6, W, 16)]
        for i in rng.choice(len(bolts), 6, replace=False):         # 6 chorreaduras irregulares
            bx, y = bolts[int(i)]
            ln = int(rng.integers(8, 30))
            for yy in range(y + 1, min(WALL - 8, y + ln)):
                wob = int(round(math.sin(yy * 0.35 + bx) * 0.6))
                wid = 2 if yy < y + ln * 0.4 else 1
                m = (YY == yy) & (XX >= bx + wob) & (XX < bx + wob + wid)
                if yy < y + ln * 0.5:
                    rust2[m] = True
                else:
                    rust[m] = True
        # (12.2: sin chorreaduras de óxido: quedaban cortadas por los muebles)
        for y in (24, 64, 98):
            cv.rgb[(YY == y) & ((XX % 16) == 6)] = R["steel"][1]
            cv.rgb[(YY == y - 1) & ((XX % 16) == 5)] = R["steel"][6]
    elif kind == "madera_rustica":
        pw = 13
        px = (XX // pw).astype(int)
        rng = np.random.default_rng(seed)
        tone = rng.random(64)[px % 64]
        lx = XX % pw
        grain = (vnoise(2.5, seed + 30, 1)[:, :] - 0.5) * 0.06 * (np.sin(YY * 0.18 + px * 5.0) > -0.2)
        val = v + (tone - 0.5) * 0.16 + grain + np.where(lx == 1, 0.07, 0) - np.where(lx == pw - 2, 0.06, 0)
        seam = lx == pw - 1
        cv.fill(wall & ~seam, "plank", val)
        cv.fill(wall & seam, "plank", v - 0.32)
        for i in range(10):
            kx, ky = int(rng.integers(4, W - 4)), int(rng.integers(14, WALL - 10))
            cv.rgb[(np.hypot(XX - kx, (YY - ky) * 1.6) < 1.8) & wall] = R["plank"][1]
        for y in (18, 96):
            cv.rgb[(YY == y) & ((XX % pw) == 6)] = R["steel"][2]
    elif kind == "madera_pared":
        upper = YY < 62
        cv.fill(wall & upper, "cream", v + 0.05 + (n1 - 0.5) * 0.06)
        lx = XX % 20
        frame_ = (lx < 3) | (lx > 16) | (YY < 67) | (YY > 101)
        bevel = np.where(((lx == 3) | (YY == 67)) & ~frame_, -0.12, 0) + np.where(((lx == 16) | (YY == 101)) & ~frame_, 0.1, 0)
        cv.fill(wall & ~upper, "panel", v - 0.02 + np.where(frame_, 0.06, -0.04) + bevel + (n2 - 0.5) * 0.04)
        cv.fill(cv.rect(0, 60, W, 63), "panel", v + 0.2)
        cv.fill(cv.rect(0, 63, W, 64), "panel", v - 0.25)
    else:  # pintura_celeste y cualquier otra pintura
        cv.fill(wall, "celeste", v + (n1 - 0.5) * 0.015 + (n2 - 0.5) * 0.01)
        _wainscot(cv, "celeste_low", 80, v)


def _wainscot(cv, ramp, y0, v):
    """Friso pintado desde y0 hasta el zócalo, con filete de luz arriba."""
    n = vnoise(18, 77, 2)
    cv.fill(cv.rect(0, y0, W, WALL), ramp, v - 0.08 + (n - 0.5) * 0.06)
    cv.fill(cv.rect(0, y0, W, y0 + 1), ramp, v + 0.35)
    cv.fill(cv.rect(0, y0 + 1, W, y0 + 2), ramp, v - 0.25)


def _cracks(cv, seed, ramp, starts, n):
    rng = np.random.default_rng(seed + 9)
    col = R[ramp][1]
    for sx, sy in starts:
        x, y = float(sx + rng.integers(-30, 30)), float(sy)
        for i in range(n * 3):
            xi, yi = int(x), int(y)
            if 0 <= xi < W and 10 < yi < WALL - 6:
                cv.rgb[yi, xi] = col
            x += rng.choice([-1, 0, 1])
            y += 1 if rng.random() < 0.7 else 0


# ------------------------------------------------------------------ pisos
ROWS = [4, 5, 7, 8, 10, 12, 14]            # alto de cada fila, crece hacia adelante (suma 60)
VP = (200.0, -260.0)                      # punto de fuga de las juntas


def floor_kind(cv, kind, v, seed):
    fl = YY >= WALL
    edges = np.cumsum([0] + ROWS) + WALL
    ri = np.clip(np.searchsorted(edges, YY, side="right") - 1, 0, len(ROWS) - 1)
    ly = YY - edges[ri]
    rh = np.array(ROWS)[ri]
    k = (YY - VP[1]) / (WALL - VP[1])
    fx = VP[0] + (XX - VP[0]) / k               # x "sobre el piso" (deshace la fuga)
    n1 = vnoise(16, seed + 20, 3)
    n2 = vnoise(4, seed + 21, 2)
    if kind in ("ceramica", "damero"):
        tw = 22.0
        col = np.floor(fx / tw).astype(int)
        joint = ((fx - col * tw) < 1.0 / k) | (ly < 1)
        bev = np.where(ly == 1, 0.05, 0) - np.where(ly == rh - 1, 0.05, 0)
        if kind == "ceramica":
            cv.fill(fl & ~joint, "ceram", v + 0.06 + bev + (n1 - 0.5) * 0.05 + (n2 - 0.5) * 0.03)
            cv.fill(fl & joint, "mortar", v - 0.02)
        else:
            dark = ((col + ri) % 2) == 1
            cv.fill(fl & ~dark & ~joint, "check_w", v + 0.04 + bev + (n2 - 0.5) * 0.04)
            cv.fill(fl & dark & ~joint, "check_d", v + 0.12 + bev)
            cv.fill(fl & joint, "check_d", v - 0.2)
    elif kind == "madera":
        rng = np.random.default_rng(seed + 22)
        offs = rng.integers(0, 60, len(ROWS))[ri]
        ln = 64.0
        head = ((fx + offs) % ln) < 1.0 / k
        tone = rng.random((len(ROWS), 32))[ri, (((fx + offs) // ln).astype(int)) % 32]
        grain = np.sin(fx * 0.25 + np.sin(fx * 0.05 + ri * 1.7) * 3 + ly * 1.3) * 0.04
        gap = ly < 1
        cv.fill(fl & ~(gap | head), "floor_wood", v + (tone - 0.5) * 0.14 + grain + np.where(ly == 1, 0.06, 0))
        cv.fill(fl & (gap | head), "floor_wood", v - 0.34)
    elif kind == "goma":
        dots = (np.round(fx) % 5 == 2) & (ly == rh // 2)
        cv.fill(fl, "rubber", v - 0.05 + (n2 - 0.5) * 0.06 + dots * 0.12)
        cv.fill(fl & (np.abs(fx % 80) < 1.0 / k), "rubber", v - 0.3)
    else:  # cemento alisado con juntas de dilatación, manchas y desgaste
        stain = vnoise(26, seed + 23, 3)
        val = v + (n1 - 0.5) * 0.04 + (n2 - 0.5) * 0.02 - np.clip(stain - 0.8, 0, 1) * 0.9
        val += speck(seed + 25, 0.015) * 0.06 - speck(seed + 24, 0.03) * 0.05
        joints = (np.abs(fx % 100) < 1.0 / k) | ((ri == 3) & (ly < 1))
        cv.fill(fl & ~joints, "cement", val)
        cv.fill(fl & joints, "cement", v - 0.24)


# ------------------------------------------------------------------ techo, zócalo, ventana
def ceiling(cv, kind="cal"):
    """Cielorraso: viga de 8 px + cornisa de 3 px con luz arriba y sombra abajo; en los
    galpones (chapa, madera rústica) además vigas que bajan cada 100 px."""
    val = 0.4 + np.where(YY <= 1, -0.15, 0) + np.where(YY == 5, 0.28, 0) + np.where(YY == 6, 0.12, 0) + np.where(YY == 7, -0.32, 0)
    val = val + np.where((XX % 50) == 0, -0.25, 0) * (YY < 5)
    cv.fill(cv.rect(0, 0, W, 8), "beam", val)
    corn = "steel" if kind == "chapa" else ("cream" if kind not in ("ladrillo", "madera_rustica", "madera_pared") else "panel")
    cv.fill(cv.rect(0, 8, W, 11), corn, 0.62 + np.where(YY == 8, 0.25, 0) + np.where(YY == 10, -0.3, 0))
    sh = cv.rect(0, 11, W, 15)
    dark = BY < np.where(YY < 12, 0.95, np.where(YY < 13, 0.6, np.where(YY < 14, 0.3, 0.12)))
    cv.darken(sh & dark, 0.74)
    if kind in ("chapa", "madera_rustica"):
        for bx in range(50, W, 100):
            m = cv.rect(bx, 0, bx + 6, 20)
            cv.fill(m, "beam", 0.4 + np.where(XX == bx, 0.25, 0) + np.where(XX == bx + 5, -0.3, 0) + 0 * YY)
            cv.darken(cv.rect(bx + 6, 11, bx + 8, 20), 0.8)


def baseboard(cv, v, kind):
    """Zócalo de 7 px: canto superior iluminado, cara, sombra al pie y AO en el piso."""
    ramp = "steel" if kind == "chapa" else "base_wood"
    val = (v + 0.02 + np.where(YY == WALL - 7, 0.36, 0) + np.where(YY == WALL - 6, 0.16, 0)
           + np.where(YY == WALL - 1, -0.18, 0) + np.where(YY == WALL, -0.34, 0))
    cv.fill(cv.rect(0, WALL - 7, W, WALL + 1), ramp, val)
    cv.darken(cv.rect(0, WALL - 9, W, WALL - 7) & (BY < 0.5), 0.86)            # sombra del canto en la pared
    m = cv.rect(0, WALL + 1, W, WALL + 4)
    cv.darken(m & (YY < WALL + 2), 0.66)
    cv.darken(m & (YY == WALL + 2), 0.8)
    cv.darken(m & (YY == WALL + 3) & (BY < 0.5), 0.88)


WINDOW = (44, 36)     # vidrio; con marco, vano y alféizar ocupa window_box()


def window_box(x, y=14):
    """Rectángulo total (x, y, w, h) que ocupa la ventana: lo usa el validador."""
    w, h = WINDOW
    return (x - 5, y - 3, w + 10, h + 10)


def window(cv, x, y, seed, view="ciudad"):
    """Ventana con marco de madera con espesor, alféizar, vista y reflejo."""
    w, h = WINDOW
    glass = cv.rect(x, y, x + w, y + h)
    cv.fill(glass, "sky", 0.9 - (YY - y) / h * 0.55)
    rng = np.random.default_rng(seed)
    hz = y + int(h * 0.62)                                    # horizonte
    if view == "ciudad":
        bx = x
        while bx < x + w:
            bw = int(rng.integers(5, 10))
            bh = int(rng.integers(6, int(h * 0.55)))
            m = cv.rect(bx, y + h - bh, min(x + w, bx + bw), y + h)
            cv.fill(m, "city", 0.45 + np.where(XX == bx, 0.3, 0) + rng.random() * 0.2)
            cv.rgb[m & ((YY - (y + h - bh)) % 4 == 2) & ((XX - bx) % 3 == 1)] = R["city"][3]
            bx += bw + 1
        tx, ty = x + int(w * (0.2 + 0.6 * rng.random())), y + h * 0.7
        tree = (np.hypot(XX - tx, (YY - ty) * 1.1) < h * 0.2) & glass
        cv.fill(tree, "leaf", 0.75 - (YY - ty + h * 0.2) / h * 1.2 + (vnoise(2, seed, 1) - 0.5) * 0.4)
    else:
        amp = 0.32 if view in ("cerros", "vinedo") else 0.12
        ridge_y = hz - (np.sin((XX - x) / w * 5.0 + seed) * 0.5 + 0.5) * h * amp - 1
        hills = glass & (YY >= ridge_y) & (YY < hz)
        cv.fill(hills, "city", 0.42 + (YY - ridge_y) / h * 0.8)
        if view in ("cerros", "vinedo"):
            snow = glass & (YY >= ridge_y) & (YY < ridge_y + 2) & (ridge_y < hz - h * 0.2)
            cv.rgb[snow] = R["tile_w"][6]
        ground = glass & (YY >= hz)
        cv.fill(ground, "leaf", 0.75 - (YY - hz) / h * 0.9)
        if view == "vinedo":                                 # hileras de vides que fugan
            rows_ = glass & (YY > hz + 1) & ((((XX - (x + w / 2)) / np.maximum(1, YY - hz + 2) * 4).astype(int) % 2) == 0)
            cv.fill(rows_, "leaf", 0.25 + 0 * XX)
        elif view == "huerto":                               # copas de frutales en fila
            for i in range(5):
                tx = x + 4 + i * (w - 8) / 4
                cr = (np.hypot(XX - tx, (YY - (hz - 2)) * 1.2) < 4.5) & glass
                cv.fill(cr, "leaf", 0.6 - (YY - hz + 6) / 12)
        else:                                                # campo: alambrado y un molino
            post = glass & (YY >= hz + 2) & (YY < hz + 6) & (((XX - x) % 9) == 0)
            cv.rgb[post] = R["frame"][2]
            cv.rgb[glass & (YY == hz + 3)] = R["frame"][3]
            mx = x + int(w * 0.7)
            cv.rgb[glass & (XX == mx) & (YY > hz - 12) & (YY < hz + 2)] = R["steel"][3]
            cv.rgb[glass & ((np.abs(XX - mx) + np.abs(YY - (hz - 12))) < 3) & (((XX + YY) % 2) == 0)] = R["steel"][5]
    d = (XX - x) + (YY - y) * 0.8                             # reflejo
    refl = glass & (((d > w * 0.25) & (d < w * 0.25 + 3)) | ((d > w * 0.25 + 6) & (d < w * 0.25 + 7)))
    cv.rgb[refl] = (cv.rgb[refl] * 0.55 + 255 * 0.45).astype(np.uint8)
    mx, my = x + w // 2, y + h // 2
    cv.fill(cv.rect(mx - 1, y, mx + 1, y + h), "frame", np.where(XX == mx - 1, 0.75, 0.45))
    cv.fill(cv.rect(x, my - 1, x + w, my + 1), "frame", np.where(YY == my - 1, 0.75, 0.45))
    outer = cv.rect(x - 3, y - 3, x + w + 3, y + h + 2)
    inner = cv.rect(x - 1, y - 1, x + w + 1, y + h)
    cv.fill(outer & ~inner, "frame", 0.5 + np.where((YY < y - 1) | (XX < x - 1), 0.2, -0.1))
    cv.fill(inner & ~glass & ((YY < y) | (XX < x)), "frame", 0.12)            # sombra del vano
    cv.fill(inner & ~glass & ~((YY < y) | (XX < x)), "frame", 0.35)
    cv.fill(cv.rect(x - 5, y + h + 2, x + w + 5, y + h + 5), "frame",
            0.5 + np.where(YY == y + h + 2, 0.32, 0) + np.where(YY == y + h + 4, -0.3, 0))   # alféizar
    cv.darken(cv.rect(x - 4, y + h + 5, x + w + 6, y + h + 7), 0.8)


def lamp_glow(cv, lamps, kind):
    """Charco de luz de cada lámpara sobre CUALQUIER pared (también ladrillo, madera,
    chapa y azulejo, donde la textura tapaba la luz del mapa de valor) y en el piso:
    aclara el color en 2 escalones tramados (no es un degradé)."""
    k = 0.16 if kind in ("ladrillo", "madera_rustica", "chapa", "azulejo", "madera_pared") else 0.09
    glow = np.zeros((H, W))
    for lx in lamps:
        glow = np.maximum(glow, np.exp(-((XX - lx) / 26.0) ** 2 - ((YY - 30) / 34.0) ** 2) * (YY < WALL - 7))
        glow = np.maximum(glow, np.exp(-((XX - lx) / 34.0) ** 2 - ((YY - 136) / 12.0) ** 2) * 0.8 * (YY > WALL + 3))
    step = np.floor(glow * 2 + BY * 0.999) / 2.0
    f = 1.0 + k * step
    cv.rgb[:] = np.clip(cv.rgb * f[:, :, None] + 6 * step[:, :, None], 0, 255).astype(np.uint8)


def render(wall, floor, tier, lamps=(), window_x=None, seed=1, view="ciudad"):
    cv = Canvas()
    wr = None
    if window_x is not None:
        wr = (window_x, 14, WINDOW[0], WINDOW[1])
    v = light_map(lamps, wr)
    wall_kind(cv, wall, v, seed)
    floor_kind(cv, floor, v, seed)
    lamp_glow(cv, lamps, wall)
    ceiling(cv, wall)
    baseboard(cv, v, wall)
    if wr:
        window(cv, window_x, 14, seed + 3, view)
    return Image.fromarray(np.dstack([cv.rgb, np.full((H, W), 255, dtype=np.uint8)]), "RGBA")
