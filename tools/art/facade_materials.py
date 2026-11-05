"""14.0: materiales de las paredes de las fachadas (lo que en los interiores hace rooms_art.py).

facade_tags.py dice dónde está cada wall(cv, x, y, w, h, kind) y de qué material es.
Acá esa pared se vuelve a pintar con textura propia y la luz de la escena (el mapa de
valor de facade_light.light): una rampa de 8 tonos armada con los colores re-estilados
del material (sombra fría -> base -> luz cálida) y cuantizada con tramado Bayer sólo en
la franja de transición, igual que las paredes de adentro.

  ladrillo   hiladas de 4 px con traba, canto de luz arriba, junta hundida, tono por ladrillo
  adobe      bloques de 11x6 con paja y junta, bordes gastados
  piedra     piedras irregulares con volumen (luz arriba-izquierda, sombra abajo-derecha)
  madera     tablas verticales con veta, junta oscura y canto de luz
  chapa      acanalado de 3 px con brillo en la cresta
  revoques   (cal, colonial, crema, hormigón, pinturas) manchas suaves, paños del hormigón
"""
import numpy as np

import buildings4 as B4
import px2
import restyle11 as R

BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
SHADE = np.array([52, 46, 92.0])
SUN = np.array([255, 228, 182.0])


def _rgb(code):
    h = px2.PAL[code].lstrip("#")
    return np.array(R.remap(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))), dtype=np.float64)


def ramp(kind):
    b, s, l, d = (_rgb(c) for c in B4.WALLS[kind])
    deep = s * 0.55 + SHADE * 0.22
    tones = [deep, s * 0.78 + SHADE * 0.08, s, (s + b) / 2, b, (b * 2 + l) / 3, l, l + (SUN - l) * 0.35]
    return np.array(tones)


def _noise(h, w, scale, seed):
    rng = np.random.default_rng(abs(seed) % (2 ** 31))
    g = rng.random((h // scale + 3, w // scale + 3))
    yy, xx = np.mgrid[0:h, 0:w] / scale
    y0, x0 = yy.astype(int), xx.astype(int)
    fy, fx = yy - y0, xx - x0
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = g[y0, x0] * (1 - fx) + g[y0, x0 + 1] * fx
    b = g[y0 + 1, x0] * (1 - fx) + g[y0 + 1, x0 + 1] * fx
    return a * (1 - fy) + b * fy


def _hash(*k):
    v = 0
    for i in k:
        v = (v * 1000003 + int(i) * 2654435761 + 12345) % 1000003
    return v / 1000003.0


def texture(kind, lx, ly, ww, hh, seed):
    """Relieve del material (valor -0.4..+0.3) en coordenadas locales de la pared."""
    h, w = lx.shape
    n1 = _noise(h, w, 9, seed) - 0.5
    n2 = _noise(h, w, 3, seed + 1) - 0.5
    t = np.zeros_like(lx, dtype=np.float64)
    if kind == "ladrillo":
        row = (ly - 2) // 4
        off = np.where(row % 2 == 0, 0, 4)
        bx = (lx + off) // 8
        cy = (ly - 2) % 4
        cx = (lx + off) % 8
        tone = np.vectorize(_hash)(row, bx, seed) - 0.5
        mortar = (cy == 0) | (cx == 0)
        t = tone * 0.14 + np.where(cy == 1, 0.10, 0) - np.where(cy == 3, 0.06, 0) + np.where(cx == 1, 0.04, 0)
        t = np.where(mortar, -0.22, t)
        t = np.where(ly < 2, -0.05, t)
    elif kind == "adobe":
        row = (ly - 3) // 6
        off = np.where(row % 2 == 0, 0, 5)
        bx = (lx + off) // 11
        cy = (ly - 3) % 6
        cx = (lx + off) % 11
        tone = np.vectorize(_hash)(row, bx, seed) - 0.5
        joint = (cy == 0) | (cx == 0)
        straw = (_noise(h, w, 1, seed + 5) > 0.82) & ~joint
        t = tone * 0.10 + n1 * 0.06 + np.where(cy == 1, 0.07, 0) - np.where(cy == 5, 0.05, 0)
        t = np.where(joint, -0.16 + n2 * 0.06, t) + straw * 0.10
    elif kind == "piedra":
        row = (ly - 1) // 5
        off = (row * 5) % 9
        bx = (lx - off) // 9
        cy = (ly - 1) % 5
        cx = (lx - off) % 9
        tone = np.vectorize(_hash)(row, bx, seed) - 0.5
        joint = (cy == 4) | (cx >= 8)
        # piedra convexa: luz arriba-izquierda, sombra abajo-derecha
        conv = 0.10 - (cy / 3.0) * 0.12 - (cx / 7.0) * 0.08
        t = tone * 0.16 + conv
        t = np.where(joint, -0.30, t)
    elif kind == "madera":
        px = (lx - 3) // 5
        cx = (lx - 3) % 5
        tone = np.vectorize(_hash)(px, seed) - 0.5
        grain = np.sin(ly * 0.55 + px * 2.1 + n1 * 6) * 0.05
        t = tone * 0.16 + grain + np.where(cx == 1, 0.07, 0) - np.where(cx == 4, 0.05, 0)
        t = np.where(cx == 0, -0.30, t)
        knot = (_noise(h, w, 3, seed + 9) > 0.9) & (cx == 2)
        t = np.where(knot, t - 0.10, t)
    elif kind == "chapa":
        ph = (lx % 3)
        t = np.where(ph == 1, 0.14, np.where(ph == 2, -0.12, 0.0)) + n1 * 0.06
        rust = (_noise(h, w, 4, seed + 3) > 0.72) & (ly > hh * 0.55)
        t = np.where(rust, t - 0.10, t)
    elif kind == "hormigon":
        panel = lx % 24
        t = n1 * 0.06 + n2 * 0.03 + np.where(panel == 0, -0.22, 0) + np.where(panel == 1, 0.08, 0)
        t += np.where(ly % 16 == 0, -0.12, 0)
        t += (_noise(h, w, 2, seed + 4) > 0.8) * -0.05          # poros
    else:   # revoques y pinturas: cal, colonial, crema, rojo, verde, amarillo, celeste, bordo
        t = n1 * 0.07 + n2 * 0.025
        t = n1 * 0.025                                          # revoque liso: la luz hace el trabajo
    return t


def paint_walls(out, v, seq, kinds, args, body, seed):
    """Repinta in situ cada pared (sólo los píxeles que siguen siendo pared)."""
    h, w = seq.shape
    YY, XX = np.mgrid[0:h, 0:w]
    BY = BAYER[YY % 4, XX % 4]
    for sid, name in kinds.items():
        if name != "wall":
            continue
        a = args.get(sid, {})
        kind = a.get("kind")
        if kind not in B4.WALLS or kind == "vidrio":
            continue
        m = (seq == sid) & body
        if kind == "colonial":
            m &= YY < a["y"] + a["h"] - 8                      # el zócalo colonial queda como está
        if not m.any():
            continue
        lx = XX - a["x"]
        ly = YY - a["y"]
        tex = texture(kind, lx, ly, a["w"], a["h"], seed + sid * 7)
        # canto de luz a la izquierda, sombra en el borde derecho (como el dibujo original)
        tex = tex + np.where(lx <= 0, 0.14, 0) - np.where(lx >= a["w"] - 2, 0.14, 0)
        rp = ramp(kind)
        n = len(rp)
        p = np.clip(0.55 + (v - 1.0) * 1.15 + tex, 0, 0.999) * n
        base = np.floor(p)
        frac = p - base
        tb = np.clip((frac - 0.86) / 0.14, 0, 1)      # tramado sólo en una franja mínima
        idx = np.clip(base + (BY < tb), 0, n - 1).astype(int)
        out[m] = rp[idx[m]]
    return out


# ------------------------------------------------------------------ techos
ROOF_CODES = {          # sombra, base, luz (códigos de px2)
    "teja": ("R1", "R2", "R3"), "paja": ("Y1", "Y2", "Y3"),
    "chapa": ("d", "g", "l"), "curvo": ("d", "g", "l"),
}


def roof_ramp(kind):
    s, b, l = (_rgb(c) for c in ROOF_CODES[kind])
    deep = s * 0.55 + SHADE * 0.22
    return np.array([deep, s * 0.8 + SHADE * 0.06, s, (s + b) / 2, b, (b + l) / 2, l, l + (SUN - l) * 0.4])


def roof_texture(kind, lx, ly, seed):
    h, w = lx.shape
    n1 = _noise(h, w, 6, seed) - 0.5
    n2 = _noise(h, w, 2, seed + 1) - 0.5
    if kind == "teja":
        # tejas musleras: hiladas de 3 px, cada teja de 4 px con lomo claro y canal oscuro
        row = ly // 3
        cy = ly % 3
        cx = (lx + (row % 2) * 2) % 4
        lomo = np.where(cx == 1, 0.12, np.where(cx == 3, -0.12, 0.0))
        t = lomo + np.where(cy == 0, 0.08, 0) - np.where(cy == 2, 0.14, 0) + n1 * 0.06
        t += (np.vectorize(_hash)(row, (lx + (row % 2) * 2) // 4, seed) - 0.5) * 0.10
        return t
    if kind == "paja":
        strand = np.sin(lx * 1.9 + n1 * 5) * 0.08
        layer = np.where(ly % 2 == 1, -0.10, 0.04)
        return strand + layer + n2 * 0.10
    if kind == "chapa":
        ph = lx % 4
        return np.where(ph == 0, -0.18, np.where(ph == 1, 0.14, 0.0)) + n1 * 0.05
    if kind == "curvo":
        ph = lx % 4
        return np.where(ph == 0, -0.14, np.where(ph == 2, 0.08, 0.0)) + n1 * 0.05
    return np.zeros_like(lx, dtype=np.float64)


def paint_roofs(out, v, seq, kinds, args, body, seed):
    h, w = seq.shape
    YY, XX = np.mgrid[0:h, 0:w]
    BY = BAYER[YY % 4, XX % 4]
    for sid, name in kinds.items():
        if name != "roof":
            continue
        a = args.get(sid, {})
        kind = a.get("kind")
        if kind not in ROOF_CODES:
            continue
        m = (seq == sid) & body
        if not m.any():
            continue
        ys = YY[m]
        lx = XX - a.get("x", 0)
        ly = YY - ys.min()
        hh = max(1, ys.max() - ys.min())
        tex = roof_texture(kind, lx, ly, seed + sid * 5)
        # faldón: más luz arriba (de cara al cielo), alero en sombra
        tex = tex + 0.10 * (1 - ly / hh) - 0.12 * (ly / hh) ** 2
        rp = roof_ramp(kind)
        n = len(rp)
        p = np.clip(0.55 + (v - 1.0) * 1.1 + tex, 0, 0.999) * n
        base = np.floor(p)
        frac = p - base
        tb = np.clip((frac - 0.86) / 0.14, 0, 1)      # tramado sólo en una franja mínima
        idx = np.clip(base + (BY < tb), 0, n - 1).astype(int)
        out[m] = rp[idx[m]]
    return out
