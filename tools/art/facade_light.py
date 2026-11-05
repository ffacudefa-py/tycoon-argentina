"""14.0: luz y acabado de las fachadas (assets/escenarios/businesses/<bid>_<n>.png).

Va DESPUÉS de restyle11.py (paleta cálida + volumen 3/4). Parte siempre del arte
fuente (assets/pixel_art/businesses), así que se puede correr cuantas veces haga
falta sin acumular efectos. Misma luz que los interiores (rooms_art.py): sol
arriba a la izquierda, sombras con corrimiento de tono hacia el violeta frío y
luces hacia el ámbar, valor cuantizado con tramado Bayer sólo en franjas angostas.

facade_tags.py dice qué pieza pintó cada píxel (pared, techo, ventana, toldo,
cartel, cajones...). Con eso:
  - cada saliente (toldo, cartel, alero, farol, utilería) tira su sombra
    abajo-derecha SOLO sobre lo que tiene detrás, con largo según cuánto sobresale
  - ventanas, puertas y arcos quedan hundidos: sombra interior arriba-izquierda
    y alféizar con luz
  - silos y tanques con sombreado cilíndrico; techos con degradé de pendiente
  - vidrios con cielo reflejado, reflejo diagonal y brillo especular
  - ventanas encendidas y carteles luminosos con halo cálido
  - degradé de sol en toda la masa, contacto oscuro en la base, luz de borde
  - sombra del edificio sobre la vereda, hacia la derecha y atrás

Uso:  python tools/art/facade_light.py            (todas)
      python tools/art/facade_light.py panaderia  (sólo esos negocios)
"""
import json
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import restyle11 as R  # noqa: E402
import facade_tags  # noqa: E402
import facade_materials as FM  # noqa: E402

SRC = os.path.join(R.ROOT, "assets", "pixel_art", "businesses")
DST = os.path.join(R.ROOT, "assets", "escenarios", "businesses")
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0

SUN = np.array([255, 228, 182], dtype=np.float64)      # luz cálida de la tarde
SHADE = np.array([52, 46, 92], dtype=np.float64)       # sombra violácea (luz de cielo)
SHADOW_RGB = (58, 42, 86)                              # violeta cálido (multiplica la vereda)                              # sombra sobre la vereda

# cuánto sobresale cada pieza (px de sombra); 0 = superficie de fondo
DEPTH = {
    "awning": 8, "stall": 6, "roof": 6, "snow_roof": 4,
    "sign": 7, "neon_sign": 7, "fileteado": 6, "post_sign": 4,
    "lamp": 4, "flag": 3, "lights": 2, "chimney": 3, "antenna": 2, "solar": 2,
    "arches": 2, "planter": 3, "bench": 3, "crates": 3, "sacks": 3, "bales": 3,
    "barrels": 3, "bottles": 2, "fruit_pile": 2, "tractor": 4, "pickup": 4, "truck": 4,
    "horse": 3, "sheep": 2, "cow": 3, "llama": 3, "tree": 4, "cactus": 3, "windmill": 3,
    "fence": 2, "water_tower": 4, "silo": 4, "tank": 4, "greenhouse": 3, "vines": 2,
    "smoke": 0, "put": 1, "hline": 2, "vline": 1, "rect": 2, "ellipse": 2, "text": 1,
    "paste": 3,
}
OPEN = {"window", "door"}
CYL = {"silo", "tank", "water_tower"}
PLANE = {"wall", "soil", "water", "crop", "done"}


def hx_(r, g, b):
    return np.array([r, g, b], dtype=np.float64)


def box_blur(a, r):
    if r <= 0:
        return a.copy()
    p = np.pad(a, r, mode="edge")
    c = p.cumsum(0).cumsum(1)
    c = np.pad(c, ((1, 0), (1, 0)))
    k = 2 * r + 1
    return (c[k:, k:] - c[:-k, k:] - c[k:, :-k] + c[:-k, :-k]) / (k * k)


def shift(a, dx, dy):
    out = np.zeros_like(a)
    h, w = a.shape
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = a[ys, xs]
    return out


def vnoise(h, w, scale, seed):
    rng = np.random.default_rng(seed)
    g = rng.random((h // scale + 2, w // scale + 2))
    yy, xx = np.mgrid[0:h, 0:w] / scale
    y0, x0 = yy.astype(int), xx.astype(int)
    fy, fx = yy - y0, xx - x0
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx
    b = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def components(mask):
    h, w = mask.shape
    lab = np.zeros((h, w), dtype=np.int32)
    n = 0
    for y0, x0 in zip(*np.nonzero(mask)):
        if lab[y0, x0]:
            continue
        n += 1
        st = [(y0, x0)]
        lab[y0, x0] = n
        while st:
            y, x = st.pop()
            for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not lab[ny, nx]:
                    lab[ny, nx] = n
                    st.append((ny, nx))
    return lab, n


def own_outlines(seq, kinds):
    """El contorno general (done) pasa a la pieza vecina de más adelante."""
    s = seq.copy()
    out_ids = [k for k, v in kinds.items() if v == "done"]
    if not out_ids:
        return s
    m = np.isin(s, out_ids)
    s[m] = 0
    nb = np.maximum.reduce([shift(s, 1, 0), shift(s, -1, 0), shift(s, 0, 1), shift(s, 0, -1)])
    s[m] = nb[m]
    return s


PRIM = {"put", "hline", "vline", "rect", "ellipse", "text", "frame", "shaded"}


def group_strokes(seq, kinds):
    """Trazos sueltos seguidos (hline, put, rect...) arman UNA pieza: no se hacen
    sombra entre ellos (si no, una cúpula hecha de líneas se raya sola)."""
    remap, out, cur = {}, {}, None
    for sid in sorted(kinds):
        name = kinds[sid]
        if name in PRIM and cur is not None and kinds.get(cur) in PRIM:
            remap[sid] = cur
        else:
            remap[sid] = sid
            out[sid] = name
            cur = sid
        if name not in PRIM:
            cur = sid
    lut = np.arange(max(kinds) + 1 if kinds else 1)
    for a, b in remap.items():
        lut[a] = b
    return lut[seq], out


def light(img, seq, kinds, seed=0, args=None):
    a = np.asarray(img.convert("RGBA")).astype(np.float64)
    h, w = a.shape[:2]
    rgb, al = a[..., :3], a[..., 3]
    solid = al > 0
    full = al >= 255
    lum = rgb @ np.array([0.299, 0.587, 0.114])
    mx, mn = rgb.max(-1), rgb.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    line = solid & (lum < 62)
    body = full & ~line
    seq = np.where(solid, seq, 0)
    side = full & (seq == 0)                      # caras 3/4 que agregó restyle11.extrude

    ys, xs = np.nonzero(full)
    if len(ys) == 0:
        return img
    top, bot = ys.min(), ys.max()
    left, right = xs.min(), xs.max()
    YY, XX = np.mgrid[0:h, 0:w].astype(np.float64)
    ny = np.clip((YY - top) / max(1, bot - top), 0, 1)
    nx = np.clip((XX - left) / max(1, right - left), 0, 1)
    BY = BAYER[YY.astype(int) % 4, XX.astype(int) % 4]
    kind_of = np.vectorize(lambda s: kinds.get(int(s), ""), otypes=[object])(seq)

    # ---------------------------------------------------------------- valor
    v = np.ones((h, w))
    v += 0.06 * (1 - ny) - 0.06 * ny
    v += 0.10 * (1 - nx) - 0.10 * nx            # apenas: la luz la dan las superficies, no un filtro

    # sombras proyectadas: cada pieza sobre lo que se dibujó antes (está detrás)
    cast = np.zeros((h, w))
    for sid, name in kinds.items():
        d = DEPTH.get(name, 0)
        if d <= 0:
            continue
        m = (seq == sid).astype(np.float64)
        if not m.any():
            continue
        acc = np.zeros((h, w))
        for k in range(1, d + 1):
            wgt = 0.95 * (1 - (k - 1) / (d + 2)) ** 0.5
            acc = np.maximum(acc, shift(m, int(round(k * 0.8)), k) * wgt)
        recv = (seq > 0) & (seq < sid) | side
        cast = np.maximum(cast, np.where(recv & (seq != sid), acc, 0))
    cast = np.maximum(cast, box_blur(cast, 1) * 0.8)
    v -= 0.62 * cast

    # aberturas hundidas: sombra interior arriba-izquierda, alféizar con luz abajo
    for sid, name in kinds.items():
        if name not in OPEN and name != "arches":
            continue
        m = seq == sid
        if not m.any():
            continue
        outside = ~m
        inner = np.zeros((h, w))
        for k, wgt in ((1, 0.75), (2, 0.6), (3, 0.32), (4, 0.12)):
            inner = np.maximum(inner, (m & (shift(outside, k, 0) | shift(outside, 0, k))) * wgt)
        v -= 0.55 * inner
        sill = shift(m, 0, 1) & ~m & body & (seq < sid)
        v += np.where(sill, 0.24, 0)
        sill2 = shift(m, 0, 2) & ~m & ~sill & body & (seq < sid)
        v -= np.where(sill2, 0.12, 0)                 # el alféizar tira su sombrita

    # cilindros: silo, tanque, tanque de agua
    for sid, name in kinds.items():
        if name not in CYL:
            continue
        m = seq == sid
        if not m.any():
            continue
        cx = XX[m]
        u = np.clip((XX - cx.min()) / max(1, cx.max() - cx.min()), 0, 1)
        shade = 0.26 * np.cos((u - 0.28) * np.pi * 1.15) - 0.16     # cilindro: brillo a 1/4, núcleo de sombra a la derecha
        v += np.where(m, shade, 0)

    # techos: más luz arriba (de cara al sol), alero oscuro
    for sid, name in kinds.items():
        if name not in ("roof", "snow_roof"):
            continue
        m = seq == sid
        if not m.any():
            continue
        ry = YY[m]
        u = np.clip((YY - ry.min()) / max(1, ry.max() - ry.min()), 0, 1)
        v += np.where(m, 0.12 * (1 - u) - 0.10 * u ** 2, 0)

    # contacto: la base oscurece hacia el piso
    v -= 0.22 * np.clip((YY - (bot - 4)) / 4, 0, 1)             # contacto: sólo los últimos 4 px
    corner = np.clip(1 - np.minimum(XX - left, right - XX) / 10, 0, 1)
    v -= np.where(YY >= bot - 3, 0.16 + 0.10 * corner, 0) * np.clip((YY - (bot - 4)) / 4, 0, 1)
    # oclusión en rincones
    v -= 0.10 * box_blur((~full).astype(np.float64), 2)
    # pátina: manchas grandes y suaves en paredes
    plane = np.isin(kind_of, list(PLANE))
    v += np.where(plane, (vnoise(h, w, 13, seed) - 0.5) * 0.08, 0)
    # caras laterales: un poco más de sombra fría
    v -= np.where(side, 0.30, 0)                 # cara 3/4: dos tonos más oscura
    # luz de borde del lado del sol
    rim = body & (shift(~full, 1, 0) | shift(~full, 0, 1)) & (nx < 0.8)
    v += np.where(rim, 0.12, 0)
    # filo de luz en el canto superior de cada pieza (cornisas, alféizares, aleros, carteles)
    above = shift(seq, 0, 1)
    lip = body & (seq > 0) & (above != seq) & ((above < seq) | ~shift(full, 0, 1)) & (cast < 0.2)
    v += np.where(lip, 0.16, 0)

    step = 0.06
    q = v / step
    frac = q - np.floor(q)
    band = (frac > 0.35) & (frac < 0.65)
    vq = np.where(band, np.floor(q) + (BY < (frac - 0.35) / 0.3), np.round(q)) * step

    # ---------------------------------------------------------------- color
    lit = np.clip(vq - 1, 0, None)
    drk = np.clip(1 - vq, 0, None)
    out = rgb + (SUN - rgb) * np.clip(lit * 1.3, 0, 0.6)[..., None]
    out = out * (1 - drk * 0.95)[..., None] + SHADE * np.clip(drk * 0.7, 0, 0.42)[..., None]

    # paredes con material propio (ladrillo, piedra, madera...) y la misma luz
    if args:
        FM.paint_walls(out, v, seq, kinds, args, body, seed)
        FM.paint_roofs(out, v, seq, kinds, args, body, seed)
    # lo que está en sombra proyectada se enfría (luz de cielo), lo iluminado se entibia
    cst = np.clip(cast * 1.4, 0, 1)
    out = np.where(body[..., None], out * (1 - 0.18 * cst[..., None]) + SHADE * 0.18 * cst[..., None], out)

    # vidrios
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    glass = body & (b > r + 28) & (b >= g - 6) & (sat > 0.22)
    if glass.any():
        lab, n = components(glass)
        gy = np.zeros((h, w))
        for i in range(1, n + 1):
            m = lab == i
            yy = YY[m]
            gy[m] = (yy - yy.min()) / max(1, yy.max() - yy.min())
        sky_top = np.array([200, 236, 248.0])
        sky_bot = np.array([40, 84, 132.0])
        tint = sky_top * (1 - gy[..., None]) + sky_bot * gy[..., None]
        gl = rgb * 0.35 + tint * 0.65
        gl = gl * (1 - 0.55 * np.clip(cast, 0, 1))[..., None]
        # reflejo distinto en cada vidrio: fase propia y sólo en ~4 de cada 10
        ph = np.zeros((h, w))
        on = np.zeros((h, w), dtype=bool)
        for i in range(1, n + 1):
            hsh = (i * 2654435761 + seed * 97) % 1000 / 1000.0
            m_ = lab == i
            ph[m_] = hsh * 12
            on[m_] = hsh < 0.25 and m_.sum() > 30
        # un solo reflejo diagonal que cruza toda la fachada (continuo de paño a paño)
        dg = (XX - YY * 0.9) - (left + (right - left) * 0.35)
        band = (np.abs(dg) < 5) | (np.abs(dg - 9) < 1.5)
        gl = np.where(band[..., None], gl + (255 - gl) * 0.38, gl)
        # el tercio de abajo de cada paño: interior en penumbra
        gl = np.where((gy > 0.66)[..., None], gl * 0.82, gl)
        q_ = (XX + YY + ph) % 12
        streak = on & (q_ < 1)
        gl = np.where(streak[..., None], gl + (255 - gl) * 0.3, gl)
        out = np.where(glass[..., None], gl, out)
        spec = glass & ~shift(glass, 1, 0) & ~shift(glass, 0, 1)
        out[spec] = [255, 252, 236]

    # emisivos: ventanas encendidas y neón, sin sombra y con halo
    glow = body & (r > 215) & (g > 165) & (b < 175) & (r - b > 70)
    neon = body & (sat > 0.55) & (mx > 225) & ~glass & np.isin(kind_of, ["neon_sign", "lights", "sign", "fileteado", "lamp"])
    emis = glow | neon
    if emis.any():
        lab_e = emis & np.isin(kind_of, list(OPEN) + ["neon_sign", "lights", "lamp", "sign", "fileteado"])
        ef = lab_e.astype(np.float64)
        # dentro de la ventana: más claro arriba (lámpara) y cálido abajo
        wy = np.clip((YY - top) / max(1, bot - top), 0, 1)
        solid_cast = np.where(cast > 0.22, 0.42, 0.0)          # sombra del toldo: plana, sin ruido
        lit_px = rgb * 0.9 + hx_(255, 214, 140) * 0.1
        lit_px = lit_px * (1 - solid_cast)[..., None] + SHADE * (solid_cast * 0.9)[..., None]
        refl = (((XX + YY + seed) % 17) < 2) & (XX % 3 != 0)
        lit_px = np.where(refl[..., None], lit_px + (255 - lit_px) * 0.35, lit_px)
        out = np.where(lab_e[..., None], lit_px, out)
        halo = box_blur(ef, 2) * 0.55 + box_blur(ef, 5) * 0.45
        halo = np.where(lab_e, 0, halo)
        hq = np.floor(halo * 6 + BY * 0.9) / 6
        warm = np.array([255, 200, 112.0])
        out = np.where((body & (hq > 0))[..., None], out + (warm - out) * np.clip(hq * 0.6, 0, 0.45)[..., None], out)
        spill = body & ~lab_e & (shift(lab_e, 0, 1) | shift(lab_e, 0, 2)) & ~glass
        out = np.where(spill[..., None], out + (warm - out) * 0.5, out)       # luz que cae al alféizar

    # humo de chimenea: bollos con volumen (tapa clara, panza gris lila), sin contorno marrón
    smk = np.isin(kind_of, ["chimney", "smoke"]) & solid & (sat < 0.2) & (lum > 120)
    if smk.any():
        sf = smk.astype(np.float64)
        up_ = shift(box_blur(sf, 1), 1, 2)
        lt_ = np.clip(1.1 - up_, 0, 1)
        sc_ = np.where((lt_ > 0.5)[..., None], np.array([252, 248, 240.0]), np.array([196, 190, 208.0]))
        out = np.where(smk[..., None], sc_, out)
        ring = line & np.isin(kind_of, ["chimney", "smoke"]) & (box_blur(sf, 1) > 0.25)
        out = np.where(ring[..., None], np.array([150, 142, 160.0]), out)
    out = np.where(rim[..., None], out + (SUN - out) * 0.28, out)    # filo de sol cálido a la izquierda
    g_ = out.mean(-1, keepdims=True)
    out = (out - g_) * 1.08 + g_ + np.array([5, 2, -5.0])      # gradación cálida (como los interiores)
    out = np.where(body[..., None], out, rgb)
    lin_v = np.clip(1 + 0.08 * (1 - ny) - 0.12 * ny - 0.25 * cast, 0.7, 1.1)
    keep_line = line & ~(np.isin(kind_of, ["chimney", "smoke"]) & (box_blur(((sat < 0.2) & (lum > 120) & solid).astype(np.float64), 1) > 0.25))
    out = np.where(keep_line[..., None], rgb * lin_v[..., None], out)
    out = np.clip(out, 0, 255)

    # contacto: oclusión en la base, a lo largo de todo el frente
    res = np.dstack([out, al])
    # carteles de azotea: dos soportes de hierro hasta el techo (antes flotaban)
    for sid, name in kinds.items():
        if name not in ("sign", "neon_sign", "fileteado"):
            continue
        sm = seq == sid
        if not sm.any():
            continue
        ys_, xs_ = np.nonzero(sm)
        sb = ys_.max()
        for px_ in (xs_.min() + 4, xs_.max() - 5):
            y = sb + 1
            run = []
            while y < h and al[y, px_] == 0 and len(run) < 16:
                run.append(y)
                y += 1
            if run and y < h and al[y, px_] > 0 and len(run) < 16:
                for yy in run:
                    res[yy, px_] = [92, 72, 66, 255]
                    res[yy, px_ + 1] = [48, 34, 36, 255]
                res[run[0], px_ - 1:px_ + 3] = [40, 28, 30, 255]
    # partículas sueltas (copos, chispas): sin contorno oscuro, se leen claras
    lab, n = components(solid)
    if n > 1:
        sizes = np.bincount(lab.ravel(), minlength=n + 1)
        tiny = (sizes[lab] <= 9) & solid
        if tiny.any():
            core = tiny & ~line
            res[tiny & line, :3] = [190, 210, 236]
            res[tiny & line, 3] = 150
            res[core, :3] = [250, 252, 255]
    cols = np.nonzero(full.any(0))[0]
    for x in range(max(0, cols.min() - 3), min(w, cols.max() + 4)):
        for y, aa in ((bot, 150), (bot - 1, 90)):
            if al[y, x] == 0 and res[y, x, 3] < aa:
                res[y, x, :3] = SHADOW_RGB
                res[y, x, 3] = aa
    return Image.fromarray(res.astype(np.uint8), "RGBA")


SHADOW_TOP = 130      # = business_scene.gd SHADOW_TOP
SHADOW_W, SHADOW_H = 192 + 88, 26


def ground_shadow(frame):
    """Sombra del edificio sobre la vereda: el sol (adelante-izquierda) la tira
    hacia atrás-derecha. Cada columna de la silueta proyecta un segmento desde su
    base hasta (x + alto*0.46, base - alto*0.11); borde tramado que se abre al alejarse.
    Va en su propia imagen (el cuadro del edificio no tiene lugar a la derecha)."""
    a = np.asarray(frame)
    full = a[..., 3] >= 255
    ys = np.nonzero(full.any(1))[0]
    out = np.zeros((SHADOW_H, SHADOW_W, 4), dtype=np.uint8)
    if not len(ys):
        return Image.fromarray(out, "RGBA")
    bot = ys.max()
    dens = np.zeros((SHADOW_H, SHADOW_W))
    for x in np.nonzero(full.any(0))[0]:
        top = np.nonzero(full[:, x])[0].min()
        hgt = bot - top
        if hgt < 3:
            continue
        n = int(hgt * 0.5) + 2
        for k in range(n + 1):
            t = k / n
            sx = x + hgt * 0.50 * t
            sy = max(bot - hgt * 0.12 * t, bot - 17) - SHADOW_TOP     # no pasa de la línea de fondo de la vereda
            ix, iy = int(round(sx)), int(round(sy))
            if 0 <= ix < SHADOW_W and 0 <= iy < SHADOW_H:
                dens[iy, ix] = 1
                if iy + 1 < SHADOW_H:
                    dens[iy + 1, ix] = 1
    core = dens > 0
    # distancia al núcleo (0..3 px): el tramado se abre con la distancia, no en un damero fijo
    dist = np.full(dens.shape, 9.0)
    dist[core] = 0
    for k in range(1, 4):
        grown = box_blur(core.astype(np.float64), k) > 0
        dist = np.where(grown & (dist > k), k, dist)
    dens = np.where(core, 1.0, np.where(dist <= 3, 1 - dist / 4, 0))
    # adelante del frente: un par de filas de contacto que se desvanecen
    by = bot - SHADOW_TOP
    colh = np.array([bot - np.nonzero(full[:, x])[0].min() if full[:, x].any() else 0 for x in range(full.shape[1])])
    xs = np.nonzero(colh >= 20)[0]
    if len(xs):
        front = [(by + k, a_) for k, a_ in ((1, 118), (2, 62), (3, 26)) if by + k < SHADOW_H]
        fx0, fx1 = max(0, xs.min() - 2), xs.max() + 3
    YY, XX = np.mgrid[0:SHADOW_H, 0:SHADOW_W]
    B = BAYER[YY % 4, XX % 4]
    # núcleo sólido; borde en 3 escalones de alfa (sin damero)
    # dos tonos de borde neto: núcleo oscuro pegado a la pared, banda exterior más clara,
    # y una sola fila tramada de transición
    near = np.zeros_like(core)
    rx = np.nonzero(full.any(0))[0].max()
    near[:, :rx + 6] = True
    near &= core
    outer = core & ~near
    trans = (dist == 1) & ~core & (B < 0.5)
    out[outer | trans, 0], out[outer | trans, 1], out[outer | trans, 2] = SHADOW_RGB
    far_ = XX > rx + 26
    out[(outer | trans) & ~far_, 3] = 92
    out[(outer | trans) & far_, 3] = 64                     # se aclara con la distancia (escalón)
    out[near, 0], out[near, 1], out[near, 2] = SHADOW_RGB
    out[near, 3] = 118
    core2 = core & (XX <= rx + 2)
    out[core2, 3] = 150                                     # núcleo pegado a la pared
    if len(xs):
        for fy, fa in front:                      # contacto adelante: sólido, se aclara por alfa
            seg = out[fy, fx0:fx1]
            seg[:, :3] = SHADOW_RGB
            seg[:, 3] = np.maximum(seg[:, 3], fa)
    return Image.fromarray(out, "RGBA")


def drop_soil(im, tg, fw):
    """Saca la tarima de pasto/tierra (soil) que quedaba como un escalón: el edificio
    apoya directo en la vereda. Sólo donde se ve la tarima (no lo que está encima)."""
    a = np.array(im.convert("RGBA"))
    for k, (seq, kinds, _, _a) in enumerate(tg):
        ids = [i for i, n in kinds.items() if n in ("soil", "water")]
        if not ids:
            continue
        m = np.isin(seq, ids)
        # el contorno que dejó done() alrededor de la tarima también se va
        out_ids = [i for i, n in kinds.items() if n == "done"]
        edge = np.isin(seq, out_ids)
        near = box_blur(m.astype(np.float64), 1) > 0
        other = (seq > 0) & ~m & ~edge
        kill = m | (edge & near & ~(box_blur(other.astype(np.float64), 1) > 0.34))
        sl = a[:, k * fw:(k + 1) * fw]
        sl[kill, 3] = 0
    return Image.fromarray(a, "RGBA")


def base_frames(fname, noext, tg=None):
    im = Image.open(os.path.join(SRC, fname))
    if tg is not None:
        fw0 = im.width // 2 if im.width >= 384 else im.width
        im = drop_soil(im, tg, fw0)
    out = R.restyle(im, selective=True)
    fw = out.width // 2 if out.width >= 384 else out.width
    skips = noext.get(fname, [[], []])
    frames = []
    for k in range(out.width // fw):
        fr = R.volume(R.extrude(out.crop((k * fw, 0, (k + 1) * fw, out.height)),
                                skip=skips[k] if k < len(skips) else ()))
        frames.append(fr)
    return frames, fw, out.height


def process(fname, noext):
    bid, t = fname[:-4].rsplit("_", 1)
    tg = facade_tags.tags(bid, int(t))
    frames, fw, fh = base_frames(fname, noext, tg)
    sheet = Image.new("RGBA", (fw * len(frames), fh), (0, 0, 0, 0))
    seed = sum(map(ord, fname))
    for k, fr in enumerate(frames):
        seq, kinds, _, args = tg[min(k, len(tg) - 1)]
        seq, kinds = group_strokes(seq, kinds)
        sheet.paste(light(fr, own_outlines(seq, kinds), kinds, seed, args), (k * fw, 0))
    sheet.save(os.path.join(DST, fname))
    ground_shadow(frames[0]).save(os.path.join(DST, fname[:-4] + "_shadow.png"))


def main(only=None):
    noext = json.load(open(R.NOEXT)) if os.path.exists(R.NOEXT) else {}
    n = 0
    for f in sorted(os.listdir(SRC)):
        if not f.endswith(".png") or "_badge" in f:
            continue
        bid = f.rsplit("_", 1)[0]
        if only and bid not in only:
            continue
        process(f, noext)
        n += 1
    print("fachadas con luz:", n)


if __name__ == "__main__":
    main(sys.argv[1:] or None)
