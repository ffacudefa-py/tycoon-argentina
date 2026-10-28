#!/usr/bin/env python3
"""Re-estilo 11 (docs/style-guide.md): pasa el arte a la paleta cálida.

Cada color de la paleta 2.0 (contorno azul marino, grises fríos) se cambia por
su equivalente de la guía (contorno marrón #3D1B0B, grises cálidos, cielo y
pasto más saturados). Los tonos intermedios (degradés, ruido de PXL) se
corren con el mismo delta que su color de paleta más cercano. En los sprites
con transparencia, el contorno del lado de la luz (arriba/izquierda) se
aclara a #8E461F (contorno selectivo, §2).

  assets/pixel_art/{businesses,locations,interiors,backgrounds,map,effects}  -> assets/escenarios/...
  assets/pixel_art/{icons,icons32,particles,avatars,ui,logo,products}       -> assets/iconos/...

Uso:  python3 tools/art/restyle11.py
"""
import json
import os
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SRC = os.path.join(ROOT, "assets", "pixel_art")

MAP = {
    "#1B1A2E": "#3D1B0B", "#2E2B48": "#5A2E1E", "#4A4766": "#7A4A32", "#6E6B8C": "#A0786A",
    "#9B98B5": "#C2A898", "#C9C7DA": "#E4D7C7", "#F0EEE6": "#F6EFE2",
    "#2F6EA8": "#287AB2", "#4E8FC9": "#3DA6EE", "#74ACDF": "#5EC0F5", "#A9D2F2": "#AFE6F2",
    "#B5700A": "#C07A12", "#FFD458": "#FFD860", "#FFF0A8": "#F7EDA4",
    "#7E2230": "#953730", "#B83A3F": "#D5576E", "#E2665A": "#F08C8F",
    "#2D6A3E": "#2E7D4F", "#4C9A4F": "#4FB070", "#8CCB6C": "#7ED89A",
    "#4A2E22": "#694634", "#7A4B30": "#94552A", "#A8714A": "#C88555", "#D9A877": "#E4AD69",
    "#F2C6A0": "#F3D2B6", "#C98E66": "#E3A988", "#8A5A40": "#B87259",
    "#F3E1BC": "#F7E7C4", "#D8BD8C": "#E4C890", "#E0802F": "#E8823A",
    "#4E3A7A": "#6A4596", "#7B5BB5": "#8A63C2",
}
SCENES = ["businesses", "locations", "interiors", "backgrounds", "map", "effects", "buildings"]
ICONS = ["icons", "icons32", "particles", "avatars", "ui", "logo", "products"]


def hx(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


OLD = [hx(k) for k in MAP]
NEW = [hx(v) for v in MAP.values()]
EXACT = dict(zip(OLD, NEW))
OUT_DARK = hx("#3D1B0B")
OUT_LIGHT = hx("#8E461F")
_cache = {}


def remap(rgb):
    if rgb in EXACT:
        return EXACT[rgb]
    if rgb in _cache:
        return _cache[rgb]
    best, bd = 0, 1e9
    for i, o in enumerate(OLD):
        d = sum((a - b) ** 2 for a, b in zip(rgb, o))
        if d < bd:
            best, bd = i, d
    if bd > 45 ** 2:
        out = rgb
    else:
        out = tuple(max(0, min(255, c + n - o)) for c, n, o in zip(rgb, NEW[best], OLD[best]))
    _cache[rgb] = out
    return out


def restyle(img, selective=True):
    img = img.convert("RGBA")
    px = img.load()
    w, h = img.size
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            nr, ng, nb = remap((r, g, b))
            px[x, y] = (nr, ng, nb, a)
    if selective:
        src = img.copy()
        sp = src.load()
        for y in range(h):
            for x in range(w):
                p = sp[x, y]
                if p[3] == 0 or p[:3] != OUT_DARK:
                    continue
                left_out = x == 0 or sp[x - 1, y][3] == 0
                top_out = y == 0 or sp[x, y - 1][3] == 0
                inner = (x + 1 < w and sp[x + 1, y][3] and sp[x + 1, y][:3] != OUT_DARK) or \
                        (y + 1 < h and sp[x, y + 1][3] and sp[x, y + 1][:3] != OUT_DARK)
                if (left_out or top_out) and inner:
                    px[x, y] = OUT_LIGHT + (p[3],)
    return img


def volume(img):
    """Volumen y pista 3/4 para edificios: sombra a la derecha de cada tramo,
    tapa clara en los bordes superiores y sombra de apoyo en la base."""
    w, h = img.size
    px = img.load()
    src = img.copy()
    sp = src.load()
    out_d, out_l = OUT_DARK, OUT_LIGHT

    def solid(x, y):
        return 0 <= x < w and 0 <= y < h and sp[x, y][3] > 0

    def is_line(p):
        return p[:3] in (out_d, out_l)
    for y in range(h):
        x = 0
        while x < w:
            if not solid(x, y):
                x += 1
                continue
            x0 = x
            while x < w and solid(x, y):
                x += 1
            if x - x0 >= 16:
                for k in range(1, 4):
                    p = sp[x - 1 - k, y]
                    if not is_line(p):
                        px[x - 1 - k, y] = tuple(int(c * (0.78 + 0.04 * k)) for c in p[:3]) + (p[3],)
    for x in range(w):
        for y in range(1, h):
            if solid(x, y) and not solid(x, y - 1):
                for k in (1, 2):
                    if solid(x, y + k) and not is_line(sp[x, y + k]):
                        p = sp[x, y + k]
                        px[x, y + k] = tuple(min(255, int(c * 1.16 + 10)) for c in p[:3]) + (p[3],)
    for y in range(h - 10, h):                      # sombra de contacto: base más oscura
        f = 1.0 - (y - (h - 10)) * 0.018
        for x in range(w):
            p = px[x, y]
            if p[3] == 255 and p[:3] not in (out_d, out_l):
                px[x, y] = tuple(int(c * f) for c in p[:3]) + (255,)
    bottom = [x for x in range(w) if solid(x, h - 1)]
    if bottom:
        for x in range(max(0, bottom[0] - 5), min(w, bottom[-1] + 6)):
            for y in (h - 2, h - 1):
                if not solid(x, y):
                    px[x, y] = (61, 27, 11, 90)
    return img


def big_mask(img, min_area=500):
    """Píxeles opacos de las componentes conexas grandes (el edificio, no la utilería)."""
    w, h = img.size
    p = img.load()
    seen = [[False] * w for _ in range(h)]
    keep = set()
    for y0 in range(h):
        for x0 in range(w):
            if seen[y0][x0] or p[x0, y0][3] < 255:
                continue
            stack, comp = [(x0, y0)], []
            seen[y0][x0] = True
            while stack:
                x, y = stack.pop()
                comp.append((x, y))
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and p[nx, ny][3] == 255:
                        seen[ny][nx] = True
                        stack.append((nx, ny))
            if len(comp) >= min_area:
                keep.update(comp)
    return keep


def opened(mask, w, h, r=2):
    """Apertura morfológica: saca del volumen lo que mide menos de 2r+1 px de
    ancho (mástiles, postes, antenas), que extruidos quedan como cintas raras."""
    def box(m, keep_if_all):
        out = set()
        cand = m if keep_if_all else {(x + dx, y + dy) for x, y in m for dx in range(-r, r + 1) for dy in range(-r, r + 1)}
        for x, y in cand:
            if keep_if_all:
                if all((x + dx, y + dy) in m for dx in range(-r, r + 1) for dy in range(-r, r + 1)):
                    out.add((x, y))
            elif 0 <= x < w and 0 <= y < h:
                out.add((x, y))
        return out
    return box(box(mask, True), False) & mask


NOEXT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "noext_businesses.json")


def extrude(img, depth=7, skip=()):
    """Vista 3/4: tapa superior (más clara) y cara lateral derecha (más oscura)
    proyectando la silueta hacia arriba-derecha, con contorno marrón."""
    w, h = img.size
    src = img.copy()
    sp = src.load()
    px = img.load()

    mass = opened(big_mask(src), w, h)
    for x0, y0, x1, y1 in skip:          # banderas: sin volumen (si no, quedan como un bloque)
        mass = {(x, y) for x, y in mass if not (x0 <= x <= x1 and y0 <= y <= y1)}

    def solid(x, y):
        return (x, y) in mass
    added = set()
    for k in range(depth, 0, -1):
        for y in range(h):
            for x in range(w):
                sx, sy = x - k, y + k
                if solid(x, y) or not solid(sx, sy):
                    continue
                top_face = not solid(sx, sy - 1) or sp[sx, sy - 1][:3] in (OUT_DARK, OUT_LIGHT) and not solid(sx, sy - 2)
                # color liso del borde (no se copia el detalle: nada de carteles duplicados)
                if top_face:
                    yy = sy
                    while solid(sx, yy - 1):
                        yy -= 1
                    while solid(sx, yy + 1) and sp[sx, yy][:3] in (OUT_DARK, OUT_LIGHT):
                        yy += 1
                    p = sp[sx, min(h - 1, yy + 1)] if solid(sx, yy + 1) else sp[sx, yy]
                else:
                    xx = sx
                    while solid(xx + 1, sy):
                        xx += 1
                    while solid(xx - 1, sy) and sp[xx, sy][:3] in (OUT_DARK, OUT_LIGHT):
                        xx -= 1
                    p = sp[max(0, xx - 1), sy] if solid(xx - 1, sy) else sp[xx, sy]
                if top_face:
                    c = tuple(min(255, int(v * 1.12 + 14)) for v in p[:3])
                else:
                    c = tuple(int(v * 0.68) for v in p[:3])
                if px[x, y][3] < 255:
                    px[x, y] = c + (255,)
                    added.add((x, y))
    # contorno marrón alrededor de lo nuevo (sólo junto a la extrusión)
    cur = img.copy()
    cp = cur.load()
    for y in range(h):
        for x in range(w):
            if cp[x, y][3] == 255:
                continue
            if any((x + dx, y + dy) in added for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = OUT_DARK + (255,)
    return img


def calm_walls(img):
    """Interiores: pared un poco más oscura y desaturada que el piso (valores separados)."""
    px = img.load()
    for y in range(min(110, img.height)):
        for x in range(img.width):
            r, g, b, a = px[x, y]
            gray = (r + g + b) / 3
            px[x, y] = (int((r * 0.75 + gray * 0.25) * 0.9), int((g * 0.75 + gray * 0.25) * 0.9), int((b * 0.75 + gray * 0.25) * 0.9), a)
    return img


def icon_base(img, sparkle=False):
    """Íconos (§7): rampa automática de 3 tonos + brillo, blancos a crema,
    sombra de apoyo elíptica al 35 % y destellos dorados en las recompensas."""
    w, h = img.size
    px = img.load()
    src = img.copy()
    sp = src.load()

    def op(x, y):
        return 0 <= x < w and 0 <= y < h and sp[x, y][3] > 0

    def line(p):
        return p[:3] in (OUT_DARK, OUT_LIGHT)
    for y in range(h):
        for x in range(w):
            p = sp[x, y]
            if p[3] == 0 or line(p):
                continue
            if p[:3] == (255, 255, 255):
                p = (255, 248, 236, p[3])
            br = op(x + 1, y) and line(sp[x + 1, y]) or op(x, y + 1) and line(sp[x, y + 1])
            tl = op(x - 1, y) and line(sp[x - 1, y]) or op(x, y - 1) and line(sp[x, y - 1])
            c = p[:3]
            if br and not tl:
                c = tuple(int(v * 0.8) for v in c)
            elif tl and not br:
                c = tuple(min(255, int(v * 1.1 + 12)) for v in c)
            px[x, y] = c + (p[3],)
    # brillo especular: primer píxel interior arriba a la izquierda
    done = False
    for y in range(h):
        for x in range(w):
            if not done and op(x, y) and not line(sp[x, y]) and op(x - 1, y) and line(sp[x - 1, y]) and op(x, y - 1) and line(sp[x, y - 1]):
                px[x + (1 if w > 16 else 0), y + (1 if w > 16 else 0)] = (255, 250, 230, 255)
                done = True
    cols = [x for x in range(w) if any(sp[x, y][3] for y in range(h))]
    rows = [y for y in range(h) if any(sp[x, y][3] for x in range(w))]
    if cols and rows:
        cx, rx = (cols[0] + cols[-1]) / 2, max(2.0, (cols[-1] - cols[0]) * 0.42)
        yb = rows[-1]
        for y in (yb, yb + 1):
            if y >= h:
                continue
            ry = (y - yb + 0.5) / 1.5
            for x in range(w):
                if ((x - cx) / rx) ** 2 + ry * ry <= 1.0 and px[x, y][3] == 0:
                    px[x, y] = (61, 27, 11, 90)
    if sparkle:
        for sx, sy in ((w - 3, 2), (2, h // 3)):
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= sx + dx < w and 0 <= sy + dy < h and px[sx + dx, sy + dy][3] == 0:
                    px[sx + dx, sy + dy] = (247, 237, 164, 255) if (dx, dy) != (0, 0) else (255, 255, 255, 255)
    return img


def has_alpha(img):
    a = img.convert("RGBA").getchannel("A")
    return a.getextrema()[0] < 255


def run(groups, dest):
    n = 0
    noext = json.load(open(NOEXT)) if os.path.exists(NOEXT) else {}
    for g in groups:
        sdir = os.path.join(SRC, g)
        if not os.path.isdir(sdir):
            continue
        for base, _, files in os.walk(sdir):
            rel = os.path.relpath(base, SRC)
            odir = os.path.join(ROOT, "assets", dest, rel)
            os.makedirs(odir, exist_ok=True)
            for f in files:
                if not f.endswith(".png"):
                    if f.endswith(".json"):
                        with open(os.path.join(base, f), "rb") as a, open(os.path.join(odir, f), "wb") as b:
                            b.write(a.read())
                    continue
                im = Image.open(os.path.join(base, f))
                out = restyle(im, selective=has_alpha(im) and not g.startswith("map"))
                if g == "businesses" and "_badge" not in f:
                    # hojas de 2 cuadros: el volumen se aplica cuadro por cuadro
                    fw = out.width // 2 if out.width >= 384 else out.width
                    skips = noext.get(f, [[], []])
                    for k in range(out.width // fw):
                        fr = volume(extrude(out.crop((k * fw, 0, (k + 1) * fw, out.height)),
                                            skip=skips[k] if k < len(skips) else ()))
                        out.paste(fr, (k * fw, 0))
                if g in ("icons", "icons32", "products"):
                    out = icon_base(out, sparkle=g == "icons32" and f[:-4] in ("corona", "estrella", "regalo", "moneda", "rayo", "trofeo"))
                if g == "interiors" and f.endswith("_back.png"):
                    out = calm_walls(out)
                out.save(os.path.join(odir, f))
                n += 1
    return n


if __name__ == "__main__":
    print("escenarios:", run(SCENES, "escenarios"), "· íconos:", run(ICONS, "iconos"))
    import ui11  # la interfaz 11 (marcos, botones, flechas) va encima del re-estilo automático
    ui11.generate(os.path.join(ROOT, "assets"))
