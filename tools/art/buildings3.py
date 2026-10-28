"""Edificios 10.0: un negocio por provincia (192x150, 2 cuadros por nivel).

Cada provincia tiene su propia función que crece en 5 niveles (chacra →
industria) con un detalle que la identifica: los cerros de colores de Jujuy,
la tierra colorada de Misiones, la nieve de Tierra del Fuego, el fileteado
de CABA... Se apoyan en piezas rurales e industriales de este módulo y en las
de buildings2 (carteles, ventanas, autos). Los cerros y la cordillera de fondo
los pone el paisaje de la región (landscapes.py), no el edificio.
"""
from px2 import Canvas
from buildings2 import W, H, G, sign, glass, window_frame, car, smoke, plant, lamp, crate, awning, wall, text, text_width


# ------------------------------------------------------------------ piezas

def soil(cv, x, w, c1="M2", c2="M3", h=5):
    cv.rect(x, G - h + 1, w, h, c1)
    for xx in range(x, x + w, 4):
        cv.put(xx + (xx // 4) % 2, G - h + 2, c2)


def furrows(cv, x, w, n_rows, c1="M2", c2="M1"):
    for r in range(n_rows):
        yy = G - 2 - r * 4
        cv.hline(x + r * 3, yy, w - r * 6, c1)
        cv.hline(x + r * 3, yy + 1, w - r * 6, c2)


def crop(cv, x, w, kind, rows=2, f=0):
    """Hileras de cultivo sobre la tierra (kind: algodon, papa, arroz, trigo, yerba, quinoa, ajo)."""
    for r in range(rows):
        yy = G - 4 - r * 7
        for i, xx in enumerate(range(x + 2 + r * 2, x + w - 3, 7)):
            sway = (i + f) % 2 if kind in ("trigo", "arroz") else 0
            if kind == "algodon":
                cv.vline(xx + 1, yy - 5, 5, "G1")
                cv.rect(xx, yy - 7, 3, 3, "W")
                cv.put(xx + 2, yy - 4, "l")
            elif kind == "papa":
                cv.rect(xx - 1, yy - 4, 5, 4, "G2")
                cv.put(xx, yy - 5, "G3")
                cv.put(xx + 3, yy - 1, ["R2", "Y2", "Q", "x"][i % 4])
            elif kind == "quinoa":
                cv.vline(xx + 1, yy - 6, 6, "G1")
                cv.rect(xx, yy - 9, 3, 4, ["R2", "Q", "Y2"][i % 3])
            elif kind == "arroz":
                for k in range(3):
                    cv.vline(xx + k + sway, yy - 6 + k % 2, 6 - k % 2, "G3" if k != 1 else "G2")
            elif kind == "trigo":
                for k in range(3):
                    cv.vline(xx + k, yy - 7, 7, "Y2")
                    cv.put(xx + k + sway, yy - 8, "Y3")
            elif kind == "yerba":
                cv.ellipse(xx + 1, yy - 4, 3, 3, "G1")
                cv.put(xx, yy - 6, "G2")
                cv.put(xx + 2, yy - 5, "G2")
            elif kind == "ajo":
                cv.vline(xx + 1, yy - 6, 6, "G2")
                cv.rect(xx, yy - 2, 3, 2, "w")
            elif kind == "girasol":
                cv.vline(xx + 1, yy - 9, 9, "G1")
                cv.rect(xx - 1, yy - 12, 5, 4, "Y2")
                cv.put(xx + 1, yy - 10, "M1")


def water(cv, x, w, f=0):
    cv.rect(x, G - 3, w, 4, "C2")
    for xx in range(x + (f * 3) % 6, x + w - 2, 6):
        cv.hline(xx, G - 2, 2, "C4")


def tree(cv, x, kind, f=0, size=1.0):
    """Frutal o árbol: olivo, limon, naranja, pera, manzana, cerezo, banana, nogal, pino."""
    tr = int(16 * size)
    if kind == "banana":
        cv.rect(x - 1, G - tr - 6, 3, tr + 6, "G1")
        for k, dx in enumerate((-9, -6, 3, 6)):
            yy = G - tr - 10 + (k % 2) * 3
            cv.rect(x + min(0, dx), yy, abs(dx) + 1, 3, "G2" if k % 2 else "G3")
            cv.put(x + dx, yy + 3, "G1")
        cv.rect(x + 2, G - tr - 2, 4, 6, "Y3")
        cv.put(x + 2, G - tr + 3, "Y1")
        return
    if kind == "pino":
        cv.rect(x - 1, G - 6, 3, 6, "M2")
        for k in range(4):
            cv.hline(x - 2 - k * 2, G - 8 - (3 - k) * 5, 5 + k * 4, "G1")
            cv.hline(x - 1 - k * 2, G - 9 - (3 - k) * 5, 3 + k * 4, "G2")
        return
    trunk = "M2" if kind != "olivo" else "M1"
    cv.rect(x - 1, G - tr // 2, 3, tr // 2, trunk)
    leaf = {"olivo": ("G1", "g"), "nogal": ("G1", "G2")}.get(kind, ("G1", "G2"))
    r = int(8 * size)
    cv.ellipse(x, G - tr // 2 - r + 2, r, r - 1, leaf[0])
    cv.ellipse(x - 1, G - tr // 2 - r + 1, r - 2, r - 3, leaf[1])
    cv.put(x - r // 2, G - tr // 2 - r - 1, "G3")
    fruit = {"limon": "Y3", "naranja": "Q", "pera": "G3", "manzana": "R2", "cerezo": "R1", "olivo": "u", "nogal": "M3"}.get(kind)
    if fruit:
        for k, (dx, dy) in enumerate(((-4, -2), (3, -5), (5, 0), (-1, 2), (-6, -6), (1, -8))):
            if k < 4 + int(size * 2):
                cv.put(x + dx, G - tr // 2 - r + 3 + dy, fruit)
                if kind in ("limon", "naranja", "manzana"):
                    cv.put(x + dx + 1, G - tr // 2 - r + 3 + dy, fruit)


def vines(cv, x, w, rows=1, f=0, grape="u"):
    for r in range(rows):
        yy = G - 2 - r * 6
        for xx in range(x + r * 4, x + w - r * 4, 12):
            cv.vline(xx, yy - 14, 14, "M1")
        cv.hline(x + r * 4, yy - 13, w - r * 8, "l")
        for xx in range(x + r * 4 + 1, x + w - r * 4 - 1):
            h = 4 + ((xx * 7 + r) % 3)
            cv.vline(xx, yy - 12, h, "G2" if (xx + f) % 3 else "G1")
            if xx % 6 == 3:
                cv.rect(xx, yy - 8, 2, 3, grape)


def fence(cv, x, w, c="M3"):
    cv.hline(x, G - 7, w, c)
    cv.hline(x, G - 3, w, c)
    for xx in range(x, x + w, 6):
        cv.vline(xx, G - 9, 9, "M2")


def roof_gable(cv, x, y, w, c1="g", c2="l"):
    """Techo a dos aguas de chapa (y = cumbrera)."""
    half = w // 2
    for k in range(half // 2):
        cv.hline(x + half - k * 2, y + k, k * 4, c1 if k % 2 else c2)
    cv.hline(x - 2, y + half // 2, w + 4, "x")


def shed(cv, x, w, h, mat="blanco", roof="gris", door_c="M2", label=None, ramp="noche"):
    """Galpón con techo de chapa curvo y portón."""
    cv.rect(x, G - h + 1, w, h, {"blanco": "w", "gris": "d", "crema": "E1", "rojo": "R2", "verde": "G2", "celeste": "C3", "madera": "M3"}[mat])
    cv.vline(x, G - h + 1, h, "W" if mat in ("blanco", "crema") else "l")
    cv.vline(x + w - 1, G - h + 1, h, "x")
    rc = {"gris": ("d", "g", "l"), "rojo": ("R1", "R2", "R3"), "verde": ("G1", "G2", "G3"), "celeste": ("C1", "C2", "C3")}[roof]
    for k in range(6):
        cv.hline(x - 2 + k // 2, G - h - k, w + 4 - k, rc[k % 3])
    for xx in range(x, x + w, 5):
        cv.vline(xx, G - h - 3, 3, rc[0])
    dw = min(w - 8, max(14, w // 3))
    dx = x + (w - dw) // 2
    cv.rect(dx, G - min(h - 6, 30) + 1, dw, min(h - 6, 30), door_c)
    for yy in range(G - min(h - 6, 30) + 3, G, 4):
        cv.hline(dx, yy, dw, "M1" if door_c.startswith("M") else "x")
    if label:
        sign(cv, x + w // 2, G - h - 18, label, ramp)


def adobe(cv, x, w, h, label=None):
    """Casita de adobe con techo plano de barro y ventanita."""
    cv.rect(x, G - h + 1, w, h, "E2")
    for yy in range(G - h + 4, G, 5):
        for xx in range(x + (yy % 2) * 3, x + w - 2, 7):
            cv.hline(xx, yy, 3, "S2")
    cv.rect(x - 2, G - h - 2, w + 4, 3, "M3")
    cv.hline(x - 2, G - h - 2, w + 4, "M4")
    for xx in range(x + 3, x + w - 2, 8):
        cv.rect(xx, G - h + 1, 2, 2, "M2")
    cv.rect(x + 4, G - 22, 10, 22, "M2")
    cv.rect(x + w - 16, G - h + 8, 9, 8, "u")
    cv.frame(x + w - 17, G - h + 7, 11, 10, "M3")
    if label:
        sign(cv, x + w // 2, G - h - 16, label, "madera")


def factory(cv, x, w, h, mat="gris", label=None, ramp="noche", f=0, chimney=True, lit=False, saw=True):
    """Nave industrial con techo de dientes de sierra, ventanas y chimenea."""
    wall(cv, x, G - h + 1, w, h, mat)
    if saw:
        for xx in range(x, x + w, 16):
            for k in range(8):
                cv.hline(xx + k, G - h - 8 + k, 16 - k * 2 if k < 8 else 0, "d")
                cv.put(xx + k, G - h - 8 + k, "l")
            cv.vline(xx + 15, G - h - 8, 8, "C4")
    else:
        cv.rect(x - 2, G - h - 3, w + 4, 4, "x")
    for xx in range(x + 6, x + w - 12, 14):
        window_frame(cv, xx, G - h + 8, 8, 10, "gris")
        glass(cv, xx, G - h + 8, 8, 10, lit and (xx // 14 + f) % 2 == 0)
    cv.rect(x + w // 2 - 10, G - 24, 20, 24, "x")
    for yy in range(G - 22, G, 3):
        cv.hline(x + w // 2 - 10, yy, 20, "d")
    if chimney:
        cx = x + w - 10
        cv.rect(cx, G - h - 26, 6, 26, "R1")
        for yy in range(G - h - 24, G - h, 4):
            cv.hline(cx, yy, 6, "R2")
        smoke(cv, cx + 2, G - h - 30, f)
    if label:
        sign(cv, x + w // 2 - 4, G - h - 22, label, ramp, ornate=lit, lit_frame=f if lit else None)


def silo(cv, x, h, c="l"):
    cv.rect(x, G - h + 1, 14, h, c)
    cv.vline(x, G - h + 1, h, "W")
    cv.vline(x + 13, G - h + 1, h, "d")
    for yy in range(G - h + 5, G, 6):
        cv.hline(x, yy, 14, "g")
    cv.ellipse(x + 7, G - h, 7, 4, "d")
    cv.ellipse(x + 6, G - h - 1, 5, 2, "l")


def tank(cv, x, h, c="w", label_c=None):
    cv.rect(x, G - h + 1, 18, h, c)
    cv.vline(x, G - h + 1, h, "W")
    cv.vline(x + 17, G - h + 1, h, "g")
    cv.hline(x, G - h + 1, 18, "l")
    if label_c:
        cv.rect(x + 3, G - h + 6, 12, 4, label_c)
    for k in range(3):
        cv.vline(x + 2 + k * 6, G - 3, 3, "x")


def barrels(cv, x, n, stack=1):
    for s in range(stack):
        for i in range(n - s):
            bx = x + i * 11 + s * 5
            by = G - 9 - s * 9
            cv.ellipse(bx + 5, by + 4, 5, 4, "M2")
            cv.ellipse(bx + 5, by + 4, 3, 3, "M3")
            cv.put(bx + 5, by + 4, "M1")
            cv.vline(bx + 2, by + 1, 7, "x")
            cv.vline(bx + 8, by + 1, 7, "x")


def boxes(cv, x, n, fill, stack=2):
    for s in range(stack):
        for i in range(max(1, n - s)):
            crate(cv, x + i * 12 + s * 6, G - 9 - s * 9, fill)


def sheep(cv, x, f=0):
    cv.rect(x, G - 9, 12, 7, "w")
    cv.rect(x + 1, G - 10, 10, 2, "W")
    cv.rect(x + 11, G - 10 + f % 2, 4, 4, "o")
    for lx in (x + 2, x + 9):
        cv.vline(lx, G - 2, 3, "o")


def cow(cv, x, f=0, spots="o"):
    cv.rect(x, G - 13, 18, 9, "w")
    cv.rect(x + 4, G - 12, 5, 4, spots)
    cv.rect(x + 12, G - 10, 4, 3, spots)
    cv.rect(x + 17, G - 15 + f % 2, 6, 6, "w")
    cv.put(x + 21, G - 13 + f % 2, "o")
    cv.rect(x + 18, G - 16 + f % 2, 1, 2, "l")
    for lx in (x + 2, x + 6, x + 12, x + 16):
        cv.vline(lx, G - 4, 5, "x")


def llama(cv, x, f=0):
    cv.rect(x, G - 12, 10, 6, "E1")
    cv.rect(x + 8, G - 22 + f % 2, 3, 11, "E1")
    cv.rect(x + 8, G - 24 + f % 2, 5, 3, "E1")
    cv.put(x + 9, G - 25 + f % 2, "M2")
    cv.put(x + 12, G - 23 + f % 2, "o")
    cv.rect(x - 1, G - 11, 2, 3, "R2")
    for lx in (x + 1, x + 8):
        cv.vline(lx, G - 6, 7, "M3")


def windmill(cv, x, f=0):
    """Molino de viento pampeano (aspas que giran entre cuadros)."""
    for k in range(40):
        cv.put(x - k // 6, G - k, "d")
        cv.put(x + k // 6, G - k, "d")
    for yy in range(G - 36, G, 8):
        cv.hline(x - (G - yy) // 6, yy, ((G - yy) // 6) * 2, "x")
    hub = (x, G - 42)
    blades = [(-7, -7), (7, -7), (7, 7), (-7, 7)] if f % 2 == 0 else [(0, -9), (9, 0), (0, 9), (-9, 0)]
    for bx, by in blades:
        for k in range(1, 9):
            cv.put(hub[0] + bx * k // 8, hub[1] + by * k // 8, "l")
    cv.rect(hub[0] - 1, hub[1] - 1, 3, 3, "R2")
    cv.rect(x + 2, G - 44, 10, 4, "C2")


def truck(cv, x, ramp="rojo", f=0, cargo=None):
    car(cv, x, G - 22, ramp, False, f)
    if cargo:
        cv.rect(x + 2, G - 28, 26, 6, cargo)
        cv.hline(x + 2, G - 28, 26, "W")


def hills(cv, x, w, h, bands):
    """Cerros de fondo con bandas de color (Jujuy: los Siete Colores)."""
    for xx in range(x, x + w):
        top = G - h + abs(((xx - x) % 48) - 24) // 2 + 6
        for yy in range(top, G - 20):
            b = bands[((yy - top) // 3 + (xx // 9)) % len(bands)]
            cv.put(xx, yy, b)
        cv.put(xx, top, "o")


def snowcap(cv, x, w, h):
    """Cordillera de fondo: roca clara con nieve en las cumbres y luz a la izquierda."""
    for xx in range(x, x + w):
        ph = (xx - x) % 60
        top = G - h + abs(ph - 30) // 2
        for yy in range(top, G - 24):
            if yy <= top + 5 + (xx % 3 == 0):
                c = "W" if ph < 30 else "l"
            else:
                c = "g" if ph < 30 else "d"
            cv.put(xx, yy, c)
        cv.put(xx, top, "x")


def flag_ar(cv, x, y, f=0):
    cv.vline(x, y, 30, "x")
    for j, c in enumerate(("C3", "W", "C3")):
        for i in range(14):
            cv.put(x + 1 + i, y + 1 + j * 3 + (i + f) // 5 % 2, c)
            cv.put(x + 1 + i, y + 2 + j * 3 + (i + f) // 5 % 2, c)
    cv.put(x + 7, y + 5, "Y2")


def bunting(cv, x1, x2, y, f=0):
    cv.hline(x1, y, x2 - x1, "x")
    for i, xx in enumerate(range(x1 + 2, x2 - 2, 6)):
        c = ("C3", "W", "Y2")[(i + f) % 3]
        cv.rect(xx, y + 1, 4, 2, c)
        cv.put(xx + 1, y + 3, c)


def base_finish(cv):
    cv.outline()
    return cv


# -------------------------------------------------------- 24 provincias (NOA)

def algodonal(t, f):
    """Santiago del Estero: chacra de algodón → desmotadora con fardos."""
    cv = Canvas(W, H)
    soil(cv, 4, 184)
    crop(cv, 6, 70 + t * 10, "algodon", rows=1 + min(t, 2), f=f)
    if t == 0:
        adobe(cv, 112, 44, 30)
        sign(cv, 134, G - 52, "ALGODÓN", "madera")
    else:
        shed(cv, 104, 46 + t * 6, 34 + t * 6, "crema", "gris", label="ALGODÓN" if t < 3 else None)
        for i in range(min(t, 3)):
            cv.rect(160 + i * 10 - t * 2, G - 10, 9, 10, "W")
            cv.frame(160 + i * 10 - t * 2, G - 10, 9, 10, "l")
    if t >= 2:
        tree(cv, 92, "nogal", f, 1.1)
    if t >= 3:
        factory(cv, 20 if t == 4 else 6, 62, 46 + (t - 3) * 10, "blanco", "DESMOTADORA" if t == 4 else "ALGODONERA", "noche", f, lit=t == 4)
    if t == 4:
        truck(cv, 150, "celeste", f, "W")
    return base_finish(cv)


def papas_andinas(t, f):
    """Jujuy: papas andinas en la Quebrada, cerros de siete colores y llamas."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "M2", "M3", 8)
    for r in range(3 if t >= 1 else 2):
        crop(cv, 4 + r * 2, 80 + t * 6, "papa" if r != 2 else "quinoa", rows=1, f=f)
    adobe(cv, 108, 40 + t * 6, 30 + t * 4, "PAPAS ANDINAS" if t >= 2 else "PAPAS")
    if t >= 1:
        llama(cv, 92, f)
    if t >= 3:
        llama(cv, 168, f + 1)
        boxes(cv, 150, 2, ("M3", "Y2", "R2"), 2)
    if t == 4:
        cv.rect(4, G - 34, 30, 14, "E1")
        cv.frame(4, G - 34, 30, 14, "M2")
        text(cv, "FERIA", 6, G - 31, "R2")
        bunting(cv, 0, 100, G - 52, f)
    return base_finish(cv)


def almazara(t, f):
    """Catamarca: olivos y una almazara que embotella aceite."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "S2", "E2")
    for i in range(2 + t):
        tree(cv, 12 + i * 16, "olivo", f, 0.9 + 0.05 * t)
    if t < 2:
        adobe(cv, 112, 50, 34, "ACEITE")
    else:
        factory(cv, 98, 74 + (t - 2) * 8, 44 + (t - 2) * 8, "crema", "ALMAZARA", "verde", f, chimney=t >= 3, lit=t == 4, saw=False)
    if t >= 1:
        for i in range(2 + t):
            cv.rect(160 + i * 5 - t * 4, G - 12, 3, 12, "G1")
            cv.rect(160 + i * 5 - t * 4, G - 14, 3, 2, "Y2")
    if t >= 3:
        tank(cv, 76, 40, "l", "G2")
    if t == 4:
        truck(cv, 4, "verde", f, "Y2")
    return base_finish(cv)


def olivar(t, f):
    """La Rioja: hileras de olivos al sol, aceitunas en salmuera y un parral."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "E2", "S2")
    for r in range(1 + min(t, 2)):
        for i in range(3 + t):
            tree(cv, 10 + i * 20 + r * 8, "olivo", f, 0.8 + 0.1 * r)
    shed(cv, 126, 44 + t * 4, 30 + t * 6, "blanco", "rojo", label="OLIVAR" if t < 4 else "ACEITUNAS")
    if t >= 2:
        for i in range(2 + t):
            cv.rect(100 + i * 7, G - 12, 6, 12, "C3")
            cv.rect(100 + i * 7, G - 14, 6, 2, "G1")
            cv.put(101 + i * 7, G - 8, "G2")
    if t >= 3:
        vines(cv, 2, 58, 1, f)
    if t == 4:
        flag_ar(cv, 176, G - 70, f)
    return base_finish(cv)


def bodega_torrontes(t, f):
    """Salta: bodega de altura en Cafayate, viñedos de torrontés y cerros."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "M3", "S2", 6)
    vines(cv, 4, 74 + t * 8, 1 + min(t, 2), f, grape="Y3")
    if t == 0:
        adobe(cv, 120, 48, 32, "VINO")
    else:
        # casona colonial blanca con galería de arcos
        x, w, h = 104, 60 + t * 5, 38 + t * 6
        cv.rect(x, G - h + 1, w, h, "W")
        cv.vline(x + w - 1, G - h + 1, h, "l")
        cv.rect(x - 3, G - h - 3, w + 6, 4, "R2")
        cv.hline(x - 3, G - h - 3, w + 6, "R3")
        for xx in range(x + 4, x + w - 10, 14):
            cv.rect(xx, G - 24, 10, 24, "M1")
            cv.ellipse(xx + 5, G - 24, 5, 4, "M1")
        sign(cv, x + w // 2, G - h - 18, "TORRONTÉS" if t >= 2 else "BODEGA", "bordo", ornate=t == 4, lit_frame=f if t == 4 else None)
    if t >= 3:
        barrels(cv, 72, 3, 2)
    if t == 4:
        car(cv, 2, G - 22, "bordo", False, f)
    return base_finish(cv)


def citricola(t, f):
    """Tucumán: limoneros y la planta de jugos con cajones amarillos."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "G1", "G2")
    for i in range(3 + t):
        tree(cv, 10 + i * 15, "limon", f, 0.9 + 0.05 * t)
    if t < 2:
        shed(cv, 116, 50, 36, "verde", "gris", label="LIMONES")
    else:
        factory(cv, 104, 70 + (t - 2) * 6, 44 + (t - 2) * 10, "amarillo", "CITRUS" if t < 4 else "CITRÍCOLA", "verde", f, lit=t == 4)
    boxes(cv, 4 + t * 2, 1 + t, ("Y3", "Y2", "G3"), 1 + min(t, 2))
    if t >= 3:
        tank(cv, 80, 44, "Y4", "Y1")
    if t == 4:
        truck(cv, 152, "amarillo", f, "Y3")
    return base_finish(cv)


# ------------------------------------------------------------------- NEA

def bananal(t, f):
    """Formosa: bananal tropical junto al río y un galpón de empaque."""
    cv = Canvas(W, H)
    water(cv, 0, W, f)
    soil(cv, 0, 130, "G1", "G2")
    for i in range(3 + t):
        tree(cv, 10 + i * 14, "banana", f, 1.0 + 0.1 * (i % 2))
    shed(cv, 120 if t < 3 else 108, 46 + t * 8, 32 + t * 6, "madera", "verde", label="BANANAS")
    if t >= 2:
        boxes(cv, 92, 2, ("Y3", "Y2", "G3"), 2)
    if t == 4:
        cv.rect(150, G - 8, 36, 5, "M3")
        cv.hline(150, G - 8, 36, "M4")
    return base_finish(cv)


def desmotadora(t, f):
    """Chaco: la desmotadora que hila el algodón, entre quebrachos."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "M2", "S3")
    tree(cv, 10, "nogal", f, 1.2)
    if t < 2:
        shed(cv, 40, 70, 40, "gris", "gris", label="ALGODÓN")
        for i in range(3):
            cv.rect(120 + i * 12, G - 12, 10, 12, "W")
            cv.frame(120 + i * 12, G - 12, 10, 12, "g")
    else:
        factory(cv, 30, 90 + (t - 2) * 10, 48 + (t - 2) * 10, "celeste", "DESMOTADORA", "noche", f, lit=t == 4)
        silo(cv, 146, 50 + t * 6)
        silo(cv, 162, 44 + t * 6)
    if t >= 1:
        for i in range(t + 1):
            cv.rect(144 + (i % 3) * 13 - (6 if t >= 2 else 0), G - 10 - (i // 3) * 10, 11, 10, "W")
    if t == 4:
        truck(cv, 2, "celeste", f, "W")
    return base_finish(cv)


def arrocera(t, f):
    """Corrientes: arrozales inundados cerca del Iberá y una casa de campo."""
    cv = Canvas(W, H)
    water(cv, 0, W, f)
    crop(cv, 4, 100 + t * 6, "arroz", rows=2 + min(t, 2), f=f)
    shed(cv, 118, 50 + t * 4, 32 + t * 5, "blanco", "celeste", label="ARROZ")
    if t >= 2:
        silo(cv, 174, 46 + t * 4)
    if t >= 3:
        tree(cv, 108, "naranja", f, 1.0)
    if t == 4:
        cv.rect(2, G - 30, 8, 30, "M2")
        cv.rect(0, G - 34, 20, 4, "M3")
        text(cv, "IBERÁ", 2, G - 44, "G3")
    return base_finish(cv)


def molino_arrocero(t, f):
    """Entre Ríos: molino que pule el arroz, con quintas de mandarinas."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "G1", "G2")
    for i in range(2 + t // 2):
        tree(cv, 8 + i * 16, "naranja" if i % 2 else "limon", f, 0.9)
    if t < 2:
        shed(cv, 70, 60, 40, "crema", "rojo", label="MOLINO")
    else:
        factory(cv, 60, 80 + (t - 2) * 8, 50 + (t - 2) * 10, "ladrillo", "MOLINO ARROCERO" if t == 4 else "MOLINO", "noche", f, lit=t == 4)
    for i in range(min(t + 1, 3)):
        silo(cv, 150 + i * 14, 40 + t * 8 - i * 4)
    if t == 4:
        truck(cv, 4, "rojo", f, "w")
    return base_finish(cv)


def yerbatal(t, f):
    """Misiones: yerbatal en tierra colorada y el secadero con chimenea."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "R1", "R2", 8)
    crop(cv, 2, 90 + t * 8, "yerba", rows=2 + min(t, 2), f=f)
    if t >= 1:
        tree(cv, 100, "pino", f)
    if t < 2:
        shed(cv, 114, 56, 34, "madera", "verde", label="YERBA")
    else:
        factory(cv, 108, 72 + (t - 2) * 6, 44 + (t - 2) * 10, "verde", "YERBA MATE", "noche", f, lit=t == 4, saw=False)
    if t >= 3:
        for i in range(3):
            cv.rect(84 + i * 7, G - 14, 6, 14, "G2")
            cv.rect(84 + i * 7, G - 15, 6, 2, "Y2")
    if t == 4:
        text(cv, "MATE", 6, G - 44, "Y3")
    return base_finish(cv)


# ------------------------------------------------------------------ Cuyo

def frigorifico(t, f):
    """San Luis: corrales de vacas y un frigorífico de lácteos y carnes."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "G2", "G3")
    fence(cv, 2, 82)
    cow(cv, 10, f)
    if t >= 1:
        cow(cv, 44, f + 1, "M2")
    if t < 2:
        shed(cv, 104, 70, 40, "blanco", "rojo", label="CARNES")
    else:
        factory(cv, 98, 80 + (t - 2) * 6, 46 + (t - 2) * 10, "blanco", "FRIGORÍFICO", "rojo", f, lit=t == 4, saw=False)
        tank(cv, 166, 40 + t * 4, "w", "C2")
    if t == 4:
        truck(cv, 56, "celeste", f, "W")
    return base_finish(cv)


def pasas(t, f):
    """San Juan: uvas secándose al sol y un secadero con viento zonda."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "E2", "S2", 6)
    vines(cv, 4, 70 + t * 6, 1 + min(t, 1), f)
    for i in range(2 + t):
        cv.rect(86 + i * 16, G - 6, 14, 4, "M3")
        for k in range(5):
            cv.put(87 + i * 16 + k * 3, G - 7, "u")
    shed(cv, 132 - t * 2, 50 + t * 2, 30 + t * 6, "crema", "gris", label="PASAS")
    if t >= 3:
        boxes(cv, 4, 2, ("M3", "u", "M2"), 2)
    if t == 4:
        sign(cv, 60, G - 60, "SAN JUAN", "bordo", ornate=True, lit_frame=f)
    return base_finish(cv)


def bodega_malbec(t, f):
    """Mendoza: viñedo de Malbec al pie de los Andes y la bodega con barricas."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "M2", "M3", 6)
    vines(cv, 2, 80 + t * 8, 1 + min(t, 2), f)
    if t == 0:
        shed(cv, 120, 50, 32, "crema", "gris", label="PARRAL")
    else:
        x, w, h = 100, 64 + t * 6, 40 + t * 8
        wall(cv, x, G - h + 1, w, h, "ladrillo" if t >= 3 else "crema")
        cv.rect(x - 3, G - h - 4, w + 6, 5, "M2")
        cv.hline(x - 3, G - h - 4, w + 6, "M3")
        cv.rect(x + w // 2 - 12, G - 30, 24, 30, "M1")
        cv.ellipse(x + w // 2, G - 30, 12, 6, "M1")
        cv.vline(x + w // 2, G - 34, 34, "M2")
        for xx in (x + 6, x + w - 18):
            window_frame(cv, xx, G - h + 10, 12, 12)
            glass(cv, xx, G - h + 10, 12, 12, t == 4 and f == 0)
        sign(cv, x + w // 2, G - h - 20, "MALBEC" if t < 4 else "BODEGA MALBEC", "bordo", ornate=t >= 3, lit_frame=f if t == 4 else None)
    if t >= 2:
        barrels(cv, 64 - (8 if t >= 3 else 0), 2 + (t >= 3), 1 + (t >= 3))
    if t == 4:
        lamp(cv, 96, G - 60)
    return base_finish(cv)


# ------------------------------------------------------------- Patagonia

def estancia_ovina(t, f):
    """Santa Cruz: estepa con ovejas y el casco de estancia de chapa roja."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "E2", "Y1", 6)
    for i in range(2 + t):
        sheep(cv, 6 + i * 18, f + i)
    fence(cv, 0, 100)
    shed(cv, 112, 52 + t * 4, 32 + t * 6, "blanco", "rojo", label="ESTANCIA" if t >= 1 else "OVEJAS")
    if t >= 2:
        for i in range(2):
            cv.rect(170 + i * 9 - t, G - 9, 8, 9, "E1")
    if t >= 3:
        windmill(cv, 98, f)
    if t == 4:
        smoke(cv, 180, G - 60, f)
        text(cv, "CORDERO", 4, G - 46, "W")
    return base_finish(cv)


def lanera(t, f):
    """Chubut: lavadero y peinaduría de lana frente a la meseta."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "E2", "S2")
    for i in range(1 + t // 2):
        sheep(cv, 4 + i * 16, f + i)
    if t < 2:
        shed(cv, 60, 70, 38, "celeste", "gris", label="LANA")
    else:
        factory(cv, 50, 92 + (t - 2) * 8, 46 + (t - 2) * 10, "celeste", "LANERA" if t < 4 else "LANERA DEL SUR", "noche", f, lit=t == 4)
    for i in range(min(2 + t, 5)):
        cv.rect(150 + (i % 3) * 13, G - 10 - (i // 3) * 10, 12, 10, "w")
        cv.frame(150 + (i % 3) * 13, G - 10 - (i // 3) * 10, 12, 10, "g")
    if t == 4:
        cv.rect(4, G - 40, 10, 40, "l")
        cv.rect(2, G - 44, 14, 4, "R2")
    return base_finish(cv)


def chacra_peras(t, f):
    """Río Negro: chacra del Alto Valle con perales, álamos y cerezos."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "G1", "G2")
    for i in range(3):
        cv.rect(2 + i * 6, G - 70, 4, 70, "G1")
        cv.rect(3 + i * 6, G - 74, 2, 6, "G2")
    for i in range(2 + t):
        tree(cv, 30 + i * 15, "pera" if i % 3 else "cerezo", f, 0.9)
    shed(cv, 120 + (t >= 3) * 4, 50 + t * 4, 30 + t * 6, "madera", "rojo", label="PERAS")
    if t >= 2:
        boxes(cv, 100, 2, ("G3", "G2", "Y3"), 2)
    if t == 4:
        truck(cv, 150, "verde", f, "G3")
    return base_finish(cv)


def manzanas(t, f):
    """Neuquén: manzanares, galpón de empaque y una torre petrolera a lo lejos."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "G1", "G2")
    for i in range(2 + t):
        tree(cv, 10 + i * 15, "manzana", f, 0.9 + 0.05 * t)
    if t < 2:
        shed(cv, 110, 60, 36, "rojo", "gris", label="MANZANAS")
    else:
        factory(cv, 100, 70 + (t - 2) * 8, 42 + (t - 2) * 10, "rojo", "EMPAQUE", "noche", f, chimney=False, lit=t == 4, saw=True)
    if t >= 3:
        # torre de petróleo (Vaca Muerta)
        bx = 176
        for k in range(50):
            cv.put(bx - k // 8, G - k, "o")
            cv.put(bx + k // 8, G - k, "o")
        for yy in range(G - 48, G, 10):
            cv.hline(bx - (G - yy) // 8, yy, ((G - yy) // 8) * 2, "x")
        cv.rect(bx - 2, G - 54 + f, 5, 4, "Y2")
    boxes(cv, 70 - t, 1 + t // 2, ("R2", "R3", "G3"), 1 + (t >= 2))
    return base_finish(cv)


def electronica(t, f):
    """Tierra del Fuego: planta de electrónica en Río Grande, con nieve."""
    cv = Canvas(W, H)
    cv.rect(0, G - 4, W, 5, "W")
    if t < 2:
        shed(cv, 50, 70 + t * 10, 40, "gris", "celeste", label="ELECTRÓNICA")
    else:
        factory(cv, 30, 100 + (t - 2) * 12, 50 + (t - 2) * 10, "gris", "TECNOFUEGO" if t == 4 else "ELECTRÓNICA", "celeste", f, chimney=False, lit=True, saw=True)
    for i in range(1 + t):
        crate(cv, 150 + (i % 3) * 12, G - 13 - (i // 3) * 9, ("C3", "C2", "W"))
    if t >= 3:
        cv.rect(10, G - 60, 3, 60, "x")
        cv.rect(4, G - 62, 15, 3, "x")
        cv.put(11, G - 66 + f, "R2")
    if t == 4:
        truck(cv, 4, "celeste", f, "C3")
    for xx in range(3 + f, W, 11):
        cv.put(xx, 20 + (xx * 7) % 50, "W")
    return base_finish(cv)


# --------------------------------------------------------------- Pampeana

def estancia_ganadera(t, f):
    """La Pampa: hacienda, molino, trigo y girasol hasta el horizonte."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "G2", "G3")
    crop(cv, 120, 70, "girasol" if t % 2 else "trigo", rows=1, f=f)
    fence(cv, 0, 110)
    cow(cv, 8, f)
    if t >= 1:
        cow(cv, 40, f + 1, "M2")
    if t >= 3:
        cow(cv, 72, f, "o")
    windmill(cv, 100 if t < 2 else 172, f)
    if t >= 2:
        x, w, h = 100, 60 + (t - 2) * 6, 34 + (t - 2) * 8
        cv.rect(x, G - h + 1, w, h, "W")
        cv.vline(x + w - 1, G - h + 1, h, "l")
        roof_gable(cv, x, G - h - w // 4, w, "R1", "R2")
        cv.rect(x + w // 2 - 6, G - 22, 12, 22, "M2")
        sign(cv, x + w // 2, G - h - w // 4 - 18, "HACIENDA", "madera", ornate=t == 4)
    else:
        shed(cv, 112, 46, 30, "blanco", "rojo", label="CAMPO")
    return base_finish(cv)


# ------------------------------------------------------------------ Centro

def salames(t, f):
    """Córdoba: fábrica de salames de Colonia Caroya entre las sierras."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "G2", "G3", 6)
    if t < 2:
        adobe(cv, 60, 60, 36, "SALAMES")
    else:
        factory(cv, 50, 90 + (t - 2) * 8, 46 + (t - 2) * 10, "ladrillo", "SALAMES CAROYA" if t == 4 else "CHACINADOS", "bordo", f, lit=t == 4, saw=False)
    for i in range(3 + t):
        cv.vline(8 + i * 6, G - 40, 4, "x")
        cv.rect(7 + i * 6, G - 36, 3, 10, "R1")
        cv.put(8 + i * 6, G - 33, "W")
    cv.hline(4, G - 40, 6 * (3 + t) + 4, "M2")
    if t >= 3:
        boxes(cv, 158, 2, ("M3", "R2", "Y2"), 2)
    if t == 4:
        truck(cv, 4, "bordo", f, "R2")
    return base_finish(cv)


def usina_lactea(t, f):
    """Santa Fe: tambo con vacas holando y la usina láctea con tanques."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "G2", "G3")
    cow(cv, 4, f)
    if t >= 1:
        cow(cv, 30, f + 1)
    if t < 2:
        shed(cv, 70, 60, 38, "blanco", "celeste", label="TAMBO")
    else:
        factory(cv, 62, 80 + (t - 2) * 8, 46 + (t - 2) * 10, "blanco", "USINA LÁCTEA" if t == 4 else "LÁCTEOS", "celeste", f, lit=t == 4)
    for i in range(min(t, 3)):
        tank(cv, 150 + i * 13 - (t - 1) * 6, 50 + i * 6, "W", "C2")
    if t == 4:
        truck(cv, 4, "celeste", f, "W")
    return base_finish(cv)


def molino_harinero(t, f):
    """Buenos Aires: trigo de la pampa húmeda, silos gigantes y el molino."""
    cv = Canvas(W, H)
    soil(cv, 0, W, "Y1", "Y2")
    crop(cv, 2, 80, "trigo", rows=2 + min(t, 2), f=f)
    if t < 2:
        shed(cv, 96, 60, 40, "crema", "gris", label="HARINA")
    else:
        factory(cv, 70, 70 + (t - 2) * 6, 56 + (t - 2) * 12, "crema", "HARINERA" if t == 4 else "MOLINO", "madera", f, lit=t == 4, saw=False)
    for i in range(min(t + 1, 4)):
        silo(cv, 150 + i * 10 - (t >= 3) * 4, 60 + t * 10 - i * 5)
    if t == 4:
        truck(cv, 6, "amarillo", f, "Y3")
    return base_finish(cv)


def panaderia(t, f):
    """CABA: confitería porteña con fileteado, medialunas y café."""
    cv = Canvas(W, H)
    cx = W // 2
    if t == 0:
        # carrito de medialunas en la vereda
        cv.rect(cx - 26, G - 30, 52, 22, "W")
        cv.frame(cx - 26, G - 30, 52, 22, "M2")
        for i in range(4):
            cv.rect(cx - 20 + i * 11, G - 26, 8, 4, "Y2")
            cv.put(cx - 20 + i * 11, G - 27, "Y3")
        for wx in (cx - 18, cx + 14):
            cv.ellipse(wx, G - 4, 4, 4, "o")
        awning(cv, cx - 30, G - 44, 60, "bordo", f, 8)
        sign(cv, cx, G - 56, "MEDIALUNAS", "bordo", ornate=True)
        return base_finish(cv)
    w = 96 + t * 18
    x = cx - w // 2
    h = 64 + t * 12
    wall(cv, x, G - h + 1, w, h, "ladrillo" if t < 3 else "crema")
    cv.rect(x - 4, G - h - 4, w + 8, 6, "w")
    cv.hline(x - 4, G - h - 4, w + 8, "W")
    for xx in range(x, x + w - 20, 26):
        window_frame(cv, xx + 6, G - h + 10, 16, 18)
        glass(cv, xx + 6, G - h + 10, 16, 18, t >= 3 and (xx // 26 + f) % 2 == 0)
    # vidriera con medialunas y alfajores
    vx, vw = x + 8, w - 16
    window_frame(cv, vx, G - 40, vw, 28)
    glass(cv, vx, G - 40, vw, 28, t == 4)
    for i, xx in enumerate(range(vx + 4, vx + vw - 8, 9)):
        cv.rect(xx, G - 18, 7, 4, "Y2" if i % 2 else "M2")
        cv.put(xx + 1, G - 19, "Y3" if i % 2 else "M3")
    awning(cv, x + 2, G - 50, w - 4, "bordo", f, 10)
    # fileteado porteño: cartel con borde y volutas
    label = "CONFITERÍA" if t >= 2 else "PANADERÍA"
    sy = G - h - 22
    tw = text_width(label)
    cv.rect(cx - tw // 2 - 8, sy - 3, tw + 16, 13, "o")
    cv.frame(cx - tw // 2 - 7, sy - 2, tw + 14, 11, "Y2")
    for k in range(3):
        cv.put(cx - tw // 2 - 5 + k, sy + 6 - k, "R2")
        cv.put(cx + tw // 2 + 5 - k, sy + 6 - k, "R2")
    text(cv, label, cx - tw // 2, sy, "Y3" if not (t == 4 and f) else "Y4")
    if t >= 3:
        for tx in (x - 22, x + w + 6):
            if 0 <= tx < W - 16:
                cv.rect(tx, G - 14, 16, 3, "W")
                cv.rect(tx + 7, G - 11, 2, 12, "x")
    if t == 4:
        lamp(cv, x - 8 if x > 12 else x + w + 4, G - 64)
    return base_finish(cv)


ARCH3 = {
    "algodonal": algodonal, "papas_andinas": papas_andinas, "almazara": almazara, "olivar": olivar,
    "bodega_torrontes": bodega_torrontes, "citricola": citricola, "bananal": bananal, "desmotadora": desmotadora,
    "arrocera": arrocera, "molino_arrocero": molino_arrocero, "yerbatal": yerbatal, "frigorifico": frigorifico,
    "pasas": pasas, "bodega_malbec": bodega_malbec, "estancia_ovina": estancia_ovina, "lanera": lanera,
    "chacra_peras": chacra_peras, "manzanas": manzanas, "electronica": electronica, "estancia_ganadera": estancia_ganadera,
    "salames": salames, "usina_lactea": usina_lactea, "molino_harinero": molino_harinero, "panaderia": panaderia,
}
