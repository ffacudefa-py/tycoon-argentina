"""12.2: pintor "volumétrico" para pixel art (manos de los minijuegos).

Cada pieza se arma con volúmenes (cápsulas cónicas, elipsoides y polígonos
abombados) en un campo de alturas a 4x de resolución: el volumen de adelante
gana, la normal sale del gradiente de la altura y la luz es la de la guía de
estilo (arriba-izquierda, un poco de frente). Después se baja a 1x y cada píxel
se cuantiza a la rampa de su material (tonos planos de paleta, con un tramado
ordenado leve sólo en las transiciones). Encima se marcan:
  - contornos internos donde un volumen pasa por delante de otro (separa los
    dedos, la muñeca del dorso, el pliegue de la manga);
  - oclusión ambiental en los rincones (entre dedos, bajo los nudillos);
  - contorno exterior de 1 px, más claro del lado de la luz.
Así las formas tienen volumen creíble pero siguen siendo pixel art legible.

    sc = Scene(96, 96)
    sc.capsule((60, 52), (69, 69), 13, 8.5, "glove", z=2)
    img = sc.render()            # PIL RGBA 96x96
"""
import math

import numpy as np
from PIL import Image, ImageDraw

SS = 4
LIGHT = np.array([-0.55, -0.62, 0.56])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
HALF = LIGHT + np.array([0, 0, 1.0])
HALF = HALF / np.linalg.norm(HALF)
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def hx(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


# material: rampa (oscuro -> claro), brillo especular, potencia, textura
MATS = {
    # cuero negro de guante táctico: brillo marcado y frío
    "glove": dict(ramp=["#140C09", "#1F130E", "#2C1B13", "#3B2519", "#4E3121", "#66412C", "#88593E", "#B88866"],
                  spec=0.7, pw=16, tex="leather"),
    # cuero mate de los paneles acolchados (nudillera): brillo más chico y puntual
    "glove_pad": dict(ramp=["#140C09", "#1C110C", "#271810", "#342116", "#452C1E", "#5C3D2A", "#7E5640", "#B08870"],
                      spec=0.9, pw=28, tex="leather"),
    "knit": dict(ramp=["#120E0E", "#1B1515", "#251D1C", "#302725", "#3D3330", "#4E423E"], spec=0.0, pw=1, tex="rib"),
    "burlap": dict(ramp=["#3A1F12", "#5A3018", "#7A4320", "#9A5828", "#B86E32", "#D08A44", "#E4A862", "#F2C88A"],
                   spec=0.05, pw=4, tex="weave"),
    "rope": dict(ramp=["#5A3A18", "#7A5228", "#9E6E34", "#C08E44", "#DDB05A", "#F0D080"], spec=0.2, pw=8, tex="rib"),
    "skin": dict(ramp=["#5E2E22", "#86493A", "#AE6A52", "#CF8C6C", "#E5AC8A", "#F3CBAE", "#FBE4D0"],
                 spec=0.2, pw=12, tex=None),
    "nail": dict(ramp=["#8A5A50", "#B98478", "#DCAEA2", "#F2D4CA", "#FFF0EA"], spec=0.5, pw=20, tex=None),
    # campera de nailon/lona azul petróleo
    "sleeve": dict(ramp=["#0D1216", "#141D24", "#1C2932", "#253643", "#304555", "#3D5668", "#506E82"],
                   spec=0.14, pw=6, tex=None),
    "brass": dict(ramp=["#4A2C08", "#6E4210", "#965C16", "#BC7A1E", "#DCA034", "#F2C45A", "#FFE69A", "#FFF8DA"],
                  spec=0.9, pw=22, tex=None),
    "glass_green": dict(ramp=["#0A2416", "#103420", "#18482C", "#22603A", "#2E7A4A", "#46985E", "#78C08A", "#C6F0CE"],
                        spec=1.0, pw=30, tex=None),
    "ceramic": dict(ramp=["#7A7276", "#9C9498", "#BAB2B4", "#D2CCCC", "#E6E2E0", "#F4F2F0", "#FFFFFF"],
                    spec=0.8, pw=26, tex=None),
    "plastic": dict(ramp=["#0E0C12", "#16131C", "#201C28", "#2B2636", "#383146", "#4A4258", "#655C76", "#9890AC"],
                    spec=0.75, pw=20, tex=None),
    "coffee": dict(ramp=["#1E0E08", "#2E160C", "#40200F", "#562C16"], spec=0.6, pw=30, tex=None),
    "velcro": dict(ramp=["#120B08", "#1B120D", "#251912", "#302118", "#3E2B20"], spec=0.05, pw=2, tex="velcro"),
}


def blur(a, r, valid=None):
    """Desenfoque de caja separable (3 pasadas ~ gaussiano), ignorando lo vacío."""
    r = max(1, int(r))
    w = np.ones(2 * r + 1)
    if valid is None:
        valid = np.ones_like(a, dtype=bool)
    num = np.where(valid, a, 0.0)
    den = valid.astype(np.float64)
    for _ in range(3):
        for ax in (0, 1):
            num = np.apply_along_axis(lambda v: np.convolve(v, w, mode="same"), ax, num)
            den = np.apply_along_axis(lambda v: np.convolve(v, w, mode="same"), ax, den)
    return num / np.maximum(den, 1e-6)


def _boxblur_fast(a, r):
    """Desenfoque de caja rápido con sumas acumuladas (2 pasadas)."""
    out = a.astype(np.float64)
    for _ in range(2):
        for ax in (0, 1):
            c = np.cumsum(np.pad(out, [(r + 1, r) if i == ax else (0, 0) for i in (0, 1)], mode="edge"), axis=ax)
            if ax == 0:
                out = (c[2 * r + 1:, :] - c[:-2 * r - 1, :]) / (2 * r + 1)
            else:
                out = (c[:, 2 * r + 1:] - c[:, :-2 * r - 1]) / (2 * r + 1)
    return out


class Scene:
    def __init__(self, w, h):
        self.w, self.h = w, h
        W, H = w * SS, h * SS
        self.H = np.full((H, W), -1e9, dtype=np.float64)       # altura (frente = mayor)
        self.M = np.full((H, W), -1, dtype=np.int32)           # material
        self.P = np.full((H, W), -1, dtype=np.int32)           # id de pieza (contornos internos)
        self.U = np.zeros((H, W), dtype=np.float64)            # coordenada a lo largo (texturas)
        self.mats = []
        self.n = 0
        ys, xs = np.mgrid[0:H, 0:W]
        self.X = (xs + 0.5) / SS
        self.Y = (ys + 0.5) / SS

    def _mat(self, name):
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def _apply(self, mask, height, mat, u=None, group=None):
        win = mask & (height > self.H)
        self.H[win] = height[win]
        self.M[win] = self._mat(mat)
        pid = self.n if group is None else group
        self.P[win] = pid
        if u is not None:
            self.U[win] = u[win]
        self.n += 1
        return pid

    def capsule(self, a, b, ra, rb, mat, z=0.0, flat=1.0, group=None, bulge=0.0):
        """Cápsula cónica de a (radio ra) a b (radio rb). flat < 1 la aplasta.
        bulge: radio extra en el medio (yema, músculo)."""
        ax, ay = a
        bx, by = b
        dx, dy = bx - ax, by - ay
        L2 = max(1e-6, dx * dx + dy * dy)
        t = ((self.X - ax) * dx + (self.Y - ay) * dy) / L2
        tc = np.clip(t, 0, 1)
        px = ax + dx * tc
        py = ay + dy * tc
        d = np.hypot(self.X - px, self.Y - py)
        r = ra + (rb - ra) * tc + bulge * np.sin(np.pi * tc)
        m = d < r
        h = z + np.sqrt(np.clip(r * r - d * d, 0, None)) * flat
        return self._apply(m, h, mat, u=tc * math.sqrt(L2), group=group)

    def chain(self, pts, radii, mats, z=0.0, group=None, flat=1.0):
        """Dedo: falanges encadenadas (pts[i] -> pts[i+1], radios[i] -> radios[i+1])."""
        g = group
        for i in range(len(pts) - 1):
            mat = mats[i] if isinstance(mats, (list, tuple)) else mats
            pid = self.capsule(pts[i], pts[i + 1], radii[i], radii[i + 1], mat, z=z + i * 0.15, group=g, flat=flat)
            if g is None:
                g = pid
        return g

    def ellipsoid(self, cx, cy, rx, ry, ang, mat, z=0.0, depth=None, group=None):
        ca, sa = math.cos(ang), math.sin(ang)
        lx = (self.X - cx) * ca + (self.Y - cy) * sa
        ly = -(self.X - cx) * sa + (self.Y - cy) * ca
        q = (lx / rx) ** 2 + (ly / ry) ** 2
        m = q < 1
        dz = depth if depth is not None else min(rx, ry)
        h = z + np.sqrt(np.clip(1 - q, 0, None)) * dz
        return self._apply(m, h, mat, u=lx, group=group)

    def poly(self, pts, mat, z=0.0, dome=4.0, group=None, soft=3.0):
        """Polígono con relieve suave (abombado hacia adentro): mangas, telas."""
        im = Image.new("L", (self.w * SS, self.h * SS), 0)
        ImageDraw.Draw(im).polygon([(x * SS, y * SS) for x, y in pts], fill=255)
        m = np.array(im) > 127
        dist = _boxblur_fast(m.astype(np.float64), int(SS * soft))
        dist = np.clip((dist - 0.5) * 2.0, 0, 1)
        h = z + np.sqrt(dist) * dome
        return self._apply(m, h, mat, u=self.X * 0.7 + self.Y * 0.7, group=group)

    def push(self, fn, mat=None):
        """Suma a la altura fn(X, Y) (pliegues, costuras) donde hay material (o sólo `mat`)."""
        m = self.M >= 0 if mat is None else self.M == self._mat(mat)
        d = fn(self.X, self.Y)
        self.H[m] += d[m]

    # ---------------------------------------------------------------- render
    def render(self, outline=("#0C0A10", "#3A3448"), inner=0.85, inner_col="#0C0A10", ao=0.6, rim=0.35, warm=None, gain=1.0):
        valid = self.M >= 0
        Hf = np.where(valid, self.H, 0.0)
        gy, gx = np.gradient(Hf * SS)
        # en los bordes entre piezas el gradiente es un salto: se limita
        gx = np.clip(np.where(valid, gx, 0), -3, 3)
        gy = np.clip(np.where(valid, gy, 0), -3, 3)
        nx, ny, nz = -gx, -gy, np.ones_like(gx)
        nl = np.sqrt(nx * nx + ny * ny + nz * nz)
        nx, ny, nz = nx / nl, ny / nl, nz / nl
        diff = np.clip(nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2], 0, 1)
        nh = np.clip(nx * HALF[0] + ny * HALF[1] + nz * HALF[2], 0, 1)
        # oclusión: cuánto más alto está el entorno
        hb = _boxblur_fast(np.where(valid, Hf, np.nan_to_num(Hf.min())), int(SS * 2.5))
        occ = np.clip((hb - Hf) / 5.0, 0, 1)
        rimv = np.clip(-(nx * LIGHT[0] + ny * LIGHT[1]) * 1.6 - 0.35, 0, 1) * (1 - nz)
        lum = (0.14 + 0.86 * diff) * (1 - ao * occ)
        spec = np.zeros_like(lum)
        texture = np.zeros_like(lum)
        for i, name in enumerate(self.mats):
            mt = MATS[name]
            sel = self.M == i
            if mt["spec"]:
                spec[sel] = mt["spec"] * nh[sel] ** mt["pw"]
            if mt["tex"] == "leather":
                texture[sel] = (_noise(self.X, self.Y, 1.5, 11)[sel] - 0.5) * 0.035
            elif mt["tex"] == "rib":
                texture[sel] = np.sin(self.U[sel] * 2.4) * 0.09
            elif mt["tex"] == "canvas":
                texture[sel] = (_noise(self.X, self.Y, 2.0, 5)[sel] - 0.5) * 0.025
            elif mt["tex"] == "weave":
                wv = ((np.floor(self.X * 1.0) + np.floor(self.Y * 1.0)) % 2) * 0.05
                texture[sel] = wv[sel] + (_noise(self.X, self.Y, 1.0, 21)[sel] - 0.5) * 0.06
            elif mt["tex"] == "velcro":
                texture[sel] = ((np.floor(self.X[sel] * 1.0) + np.floor(self.Y[sel] * 1.0)) % 2) * 0.06
        val = (lum + spec + texture + rim * rimv * 0.3) * gain
        if warm is not None:
            wx, wy, wr, wk = warm
            dd = np.hypot(self.X - wx, self.Y - wy)
            val = val + np.clip(1 - dd / wr, 0, 1) * wk * (0.3 + diff)
        # --- bajar a 1x: media de valor, material y pieza mayoritarios, cobertura
        W, H = self.w, self.h

        def down(a):
            return a.reshape(H, SS, W, SS).mean(axis=(1, 3))

        cov = down(valid.astype(np.float64))
        v1 = down(np.where(valid, val, 0)) / np.maximum(cov, 1e-6)
        h1 = down(np.where(valid, self.H, 0)) / np.maximum(cov, 1e-6)
        m1 = np.full((H, W), -1, dtype=np.int32)
        best = np.zeros((H, W))
        for i in range(len(self.mats)):
            c = down((self.M == i).astype(np.float64))
            win = c > best
            m1[win] = i
            best[win] = c[win]
        p1 = np.full((H, W), -1, dtype=np.int32)
        bestp = np.zeros((H, W))
        for pid in np.unique(self.P[self.P >= 0]):
            c = down((self.P == pid).astype(np.float64))
            win = c > bestp
            p1[win] = pid
            bestp[win] = c[win]
        alpha = cov >= 0.5
        out = np.zeros((H, W, 4), dtype=np.uint8)
        yy, xx = np.mgrid[0:H, 0:W]
        dith = BAYER4[yy % 4, xx % 4]
        for i, name in enumerate(self.mats):
            ramp = [hx(c) for c in MATS[name]["ramp"]]
            n = len(ramp)
            sel = alpha & (m1 == i)
            f = np.clip(v1, 0, 1.1) / 1.1 * (n - 1)
            base = np.floor(f)
            frac = f - base
            up = (frac > 0.6) | ((frac > 0.4) & (dith < (frac - 0.4) / 0.2 * 0.55))
            idx = np.clip(base + up, 0, n - 1).astype(int)
            for k in range(n):
                s = sel & (idx == k)
                out[s, 0:3] = ramp[k]
                out[s, 3] = 255
        # contornos internos: el píxel de la pieza de ATRÁS junto a una de adelante
        if inner:
            dark = np.array(hx(inner_col), dtype=np.float64)
            edge = np.zeros((H, W), dtype=bool)
            for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
                p2 = np.roll(p1, (dy, dx), axis=(0, 1))
                h2 = np.roll(h1, (dy, dx), axis=(0, 1))
                a2 = np.roll(alpha, (dy, dx), axis=(0, 1))
                edge |= alpha & a2 & (p2 != p1) & (p2 >= 0) & (h2 > h1 + 0.8)
            col = out[edge, 0:3].astype(np.float64)
            out[edge, 0:3] = (col * (1 - inner) + dark * inner).astype(np.uint8)
        img = Image.fromarray(out, "RGBA")
        if outline:
            img = outline_img(img, outline[0], outline[1])
        return img


def _noise(X, Y, scale, seed):
    rng = np.random.default_rng(seed)
    gw = int(X.max() / scale) + 3
    gh = int(Y.max() / scale) + 3
    g = rng.random((gh, gw))
    xi = np.clip((X / scale).astype(int), 0, gw - 1)
    yi = np.clip((Y / scale).astype(int), 0, gh - 1)
    return g[yi, xi]


def outline_img(img, dark, light):
    """Contorno exterior de 1 px; del lado de la luz (arriba-izquierda) más claro."""
    a = np.array(img)
    al = a[:, :, 3] > 0
    pad = np.pad(al, 1)
    right = pad[1:-1, 2:]
    left = pad[1:-1, :-2]
    below = pad[2:, 1:-1]
    above = pad[:-2, 1:-1]
    ring = ~al & (right | left | below | above)
    lit = ring & (right | below) & ~(left | above)
    a[ring & ~lit] = hx(dark) + (255,)
    a[lit] = hx(light or dark) + (255,)
    return Image.fromarray(a, "RGBA")
