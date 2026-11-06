"""Insignias de logros (15.0): 32x32, una por logro de data/missions.json.

Forma según la categoría del logro y borde según el rango:
  ventas    medalla redonda con cinta celeste y blanca
  dinero    Sol de Mayo (disco con rayos)
  negocios  escudo
  equipo    hexágono
  conquista medalla con laureles
  aventura  octógono con cinta
  rangos    bronce · plata · oro · diamante (celeste)
Adentro va el ícono de 16 px del logro (assets/iconos/icons/<icon>.png) con
sombra. Estilo de docs/style-guide.md: contorno 1 px #3D1B0B, luz desde arriba
a la izquierda, 3 tonos + brillo.

Escribe assets/iconos/badges/<id>.png y una versión bloqueada por categoría
(badges/locked_<categoría>.png).
Uso: python3 tools/art/badges15.py
"""
import json
import math
import os
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "assets", "iconos", "badges")
ICONS = os.path.join(ROOT, "assets", "iconos", "icons")
S = 32


def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


OUTLINE = hexc("3D1B0B")
# Rampas (sombra, medio, luz, brillo)
TIERS = {
    "bronce": [hexc(c) for c in ("6B3A1E", "B8743A", "E0A060", "F6D0A0")],
    "plata": [hexc(c) for c in ("5E6478", "A9B0C2", "D8DDE8", "FFFFFF")],
    "oro": [hexc(c) for c in ("8E5A10", "F6B40E", "F2D173", "F7EDA4")],
    "diamante": [hexc(c) for c in ("2F6EA8", "74ACDF", "A9D2F2", "E8F6FF")],
}
LOCKED = [hexc(c) for c in ("4A4766", "6E6B8C", "9B98B5", "C9C7DA")]
# Campo interior (oscuro, claro) por categoría
FIELDS = {
    "ventas": (hexc("953730"), hexc("D5576E")),
    "dinero": (hexc("2E7D4F"), hexc("3F9E5E")),
    "negocios": (hexc("23507E"), hexc("2F6EA8")),
    "equipo": (hexc("A8461A"), hexc("D86A2C")),
    "conquista": (hexc("4B2E78"), hexc("6F4BA8")),
    "aventura": (hexc("1F4E5A"), hexc("2B7286")),
}
LOCKED_FIELD = (hexc("2E2B48"), hexc("4A4766"))
CELESTE = hexc("74ACDF")
BLANCO = hexc("F0EEE6")
HOJA = (hexc("3F9E5E"), hexc("67D08E"))


# ------------------------------------------------------------------ máscaras

def circle(cx, cy, r):
    return lambda x, y: (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r


def polygon(cx, cy, r, n, rot):
    pts = [(cx + r * math.cos(rot + 2 * math.pi * i / n), cy + r * math.sin(rot + 2 * math.pi * i / n)) for i in range(n)]

    def inside(x, y):
        px, py = x + 0.5, y + 0.5
        c = False
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
                c = not c
            j = i
        return c
    return inside


def shield(x, y):
    px, py = x + 0.5, y + 0.5
    if py < 3 or py > 29.5:
        return False
    half = 12.5 if py <= 17 else 12.5 * (29.5 - py) / 12.5
    return abs(px - 16) <= half


def sun_disc(x, y):
    return circle(16, 16, 10.5)(x, y)


def sun_rays(x, y):
    px, py = x + 0.5 - 16, y + 0.5 - 16
    r = math.hypot(px, py)
    if r < 9 or r > 15.6:
        return False
    a = math.atan2(py, px) % (2 * math.pi / 12)
    a = min(a, 2 * math.pi / 12 - a)
    return a <= 0.22 * (15.6 - r) / 5.5


SHAPES = {
    "ventas": circle(16, 12.5, 11.5),
    "dinero": sun_disc,
    "negocios": shield,
    "equipo": polygon(16, 16, 15, 6, -math.pi / 2),
    "conquista": circle(16, 15, 10.5),
    "aventura": polygon(16, 13, 12.5, 8, math.pi / 8),
}
# Dónde va el centro del emblema (esquina sup. izq. del ícono de 16 px)
EMBLEM_AT = {"ventas": (8, 5), "dinero": (8, 8), "negocios": (8, 7), "equipo": (8, 8), "conquista": (8, 7), "aventura": (8, 5)}


# ------------------------------------------------------------------ dibujo

def depth_map(mask):
    """Profundidad de cada píxel dentro de la máscara (1 = borde)."""
    inside = [[mask(x, y) for x in range(S)] for y in range(S)]
    depth = [[0] * S for _ in range(S)]
    for y in range(S):
        for x in range(S):
            if inside[y][x]:
                depth[y][x] = 99
    changed = True
    level = 1
    while changed:
        changed = False
        for y in range(S):
            for x in range(S):
                if depth[y][x] != 99:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nx, ny = x + dx, y + dy
                    if not (0 <= nx < S and 0 <= ny < S) or depth[ny][nx] == level - 1 or (level == 1 and not inside[ny][nx]):
                        depth[y][x] = level
                        changed = True
                        break
        level += 1
        if level > 20:
            break
    return depth


def shade(ramp, x, y, cx, cy):
    """Tono del borde según la luz (arriba a la izquierda)."""
    dx, dy = x + 0.5 - cx, y + 0.5 - cy
    n = math.hypot(dx, dy) or 1.0
    d = (-dx * 0.7 - dy * 0.7) / n
    if d > 0.55:
        return ramp[3] if d > 0.85 else ramp[2]
    if d < -0.35:
        return ramp[0]
    return ramp[1]


def paint_shape(img, mask, ramp, field, cx, cy, rim=3):
    dm = depth_map(mask)
    for y in range(S):
        for x in range(S):
            d = dm[y][x]
            if d == 0:
                continue
            if d == 1:
                c = OUTLINE
            elif d <= rim:
                c = shade(ramp, x, y, cx, cy)
            elif d == rim + 1:
                c = ramp[0]                       # filete interior
            else:
                # campo: degradé (claro arriba, oscuro abajo) con brillo arriba a la izq.
                c = field[1] if y + 0.5 < cy - 2 else field[0]
                if y + 0.5 < cy - 2 and x + 0.5 < cx - 3 and d == rim + 2:
                    c = tuple(min(255, v + 40) for v in field[1][:3]) + (255,)
            img.putpixel((x, y), c)
    return dm


def outline_extra(img, mask_fn, fill_fn):
    """Pinta una pieza (cinta, rayos, hojas) con contorno de 1 px."""
    pts = [(x, y) for y in range(S) for x in range(S) if mask_fn(x, y)]
    sel = set(pts)
    for x, y in pts:
        edge = any((x + dx, y + dy) not in sel for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
        img.putpixel((x, y), OUTLINE if edge else fill_fn(x, y))


def _poly(pts):
    n = len(pts)

    def inside(x, y):
        px, py = x + 0.5, y + 0.5
        c = False
        j = n - 1
        for i in range(n):
            xi, yi = pts[i]
            xj, yj = pts[j]
            if (yi > py) != (yj > py) and px < (xj - xi) * (py - yi) / (yj - yi) + xi:
                c = not c
            j = i
        return c
    return inside


def ribbon(img, top):
    # Dos colas anchas que bajan abiertas, con el corte en V abajo: celeste
    # con una franja blanca al medio (como la bandera).
    left = _poly([(9, top), (16, top), (13, 32), (10.5, 29.5), (7, 31)])
    right = _poly([(16, top), (23, top), (25, 31), (21.5, 29.5), (19, 32)])

    def fill(x, y):
        # franja blanca en diagonal, paralela a cada cola
        if x < 16:
            mid = 12.5 - (y - top) * 0.14
        else:
            mid = 19.5 + (y - top) * 0.14
        return BLANCO if abs(x + 0.5 - mid) < 1.2 else (CELESTE if y < top + 8 else hexc("4E8FC9"))

    outline_extra(img, lambda x, y: left(x, y) or right(x, y), fill)


def sun_rays_paint(img, ramp):
    outline_extra(img, lambda x, y: sun_rays(x, y) and not sun_disc(x, y), lambda x, y: ramp[2] if y < 16 else ramp[1])


def laurels(img):
    # Corona de laurel: hojas alargadas que suben desde abajo por los dos
    # costados de la medalla y dejan arriba abierto; más chicas hacia la punta.
    leaves = []
    for side in (-1, 1):
        for i in range(6):
            t = i / 5.0
            th = math.radians(28 + 100 * t)          # 0° = abajo; 128° = arriba al costado
            r = 13.2
            lx = 16 + side * math.sin(th) * r
            ly = 15.5 + math.cos(th) * r
            ang = math.atan2(-math.sin(th), side * math.cos(th))   # tangente al arco
            leaves.append((lx, ly, ang, 3.1 - 0.9 * t, 1.7))

    def m(x, y):
        if circle(16, 15, 10.5)(x, y):
            return False
        px, py = x + 0.5, y + 0.5
        for lx, ly, ang, rx, ry in leaves:
            dx, dy = px - lx, py - ly
            u = dx * math.cos(ang) + dy * math.sin(ang)
            v = -dx * math.sin(ang) + dy * math.cos(ang)
            if (u / rx) ** 2 + (v / ry) ** 2 <= 1.0:
                return True
        return False

    outline_extra(img, m, lambda x, y: HOJA[1] if (x < 16) == (y < 22) else HOJA[0])


def paste_emblem(img, icon_name, at, field_dark, locked=False):
    p = os.path.join(ICONS, icon_name + ".png")
    if not os.path.exists(p):
        p = os.path.join(ICONS, "estrella.png")
    ic = Image.open(p).convert("RGBA")
    if locked:
        ic = Image.open(os.path.join(ICONS, "candado.png")).convert("RGBA")
    ax, ay = at
    shadow = tuple(max(0, v - 45) for v in field_dark[:3]) + (255,)
    for y in range(16):
        for x in range(16):
            if ic.getpixel((x, y))[3] > 128 and 0 <= ax + x + 1 < S and 0 <= ay + y + 1 < S:
                img.putpixel((ax + x + 1, ay + y + 1), shadow)
    for y in range(16):
        for x in range(16):
            c = ic.getpixel((x, y))
            if c[3] > 128:
                if locked:
                    g = int(0.3 * c[0] + 0.59 * c[1] + 0.11 * c[2])
                    c = (g, g, int(g * 1.08) if g < 236 else g, 255)
                img.putpixel((ax + x, ay + y), c[:3] + (255,))


def sparkle(img, x, y):
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        if 0 <= x + dx < S and 0 <= y + dy < S:
            img.putpixel((x + dx, y + dy), (255, 255, 255, 255))


def badge(category, tier, icon, locked=False):
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    ramp = LOCKED if locked else TIERS[tier]
    field = LOCKED_FIELD if locked else FIELDS[category]
    if category in ("ventas", "aventura"):
        ribbon(img, 19)
        if locked:
            img = Image.eval(img, lambda v: v)  # la cinta queda; se apaga abajo
    if category == "dinero":
        sun_rays_paint(img, ramp)
    if category == "conquista":
        laurels(img)
    cx, cy = {"ventas": (16, 12.5), "aventura": (16, 13), "conquista": (16, 15), "negocios": (16, 15)}.get(category, (16, 16))
    paint_shape(img, SHAPES[category], ramp, field, cx, cy, rim=3 if category != "dinero" else 2)
    paste_emblem(img, icon, EMBLEM_AT[category], field[0], locked)
    if not locked and tier in ("oro", "diamante"):
        sparkle(img, 7, 6 if category not in ("ventas", "aventura") else 4)
    if not locked and tier == "diamante":
        sparkle(img, 25, 23 if category not in ("ventas", "aventura") else 19)
    if locked:
        # Bloqueada: todo apagado (también la cinta y las hojas).
        px = img.load()
        for y in range(S):
            for x in range(S):
                r, g, b, a = px[x, y]
                if a:
                    l = int(0.3 * r + 0.59 * g + 0.11 * b)
                    px[x, y] = (int(l * 0.62), int(l * 0.6), int(l * 0.72), 255)
    return img


def main():
    os.makedirs(OUT, exist_ok=True)
    mis = json.load(open(os.path.join(ROOT, "data", "missions.json"), encoding="utf-8"))
    n = 0
    for a in mis["achievements"]:
        badge(a["category"], a["tier"], a["icon"]).save(os.path.join(OUT, a["id"] + ".png"))
        n += 1
    for cat in FIELDS:
        badge(cat, "bronce", "candado", locked=True).save(os.path.join(OUT, "locked_%s.png" % cat))
    print("insignias:", n, "+", len(FIELDS), "bloqueadas en", OUT)


if __name__ == "__main__":
    main()
