"""Moneda 2.1: cara con aro claro y canaleta, canto 3D a la derecha, brillos
en diagonal y signo $ en relieve. Contorno marrón cálido (no el #1B1A2E
general) para que se lea como metal dorado.

Genera icons32/moneda.png, icons/moneda.png y particles/coin_spin.png.
"""
import math
import os
from px2 import Canvas, PAL

PAL.update({
    "K1": "#8A421F",  # contorno marrón
    "K2": "#C25F27",  # canaleta / relieve oscuro
    "K3": "#D98F2B",  # canto
    "K4": "#F5B731",  # cara
    "K5": "#FFD98A",  # brillo diagonal
})

# Signos $ por tamaño de radio (X = trazo, h = luz del relieve a la derecha)
DOLLAR = {
    11: [
        "....X....",
        "..XXXXXh.",
        ".XXh.X...",
        ".XXh.X...",
        "..XXXXX..",
        "....X.XXh",
        "....X.XXh",
        ".XXXXXXh.",
        "....X....",
    ],
    6: [
        ".XX",
        "Xh.",
        ".X.",
        "..X",
        "XX.",
    ],
}


def draw_coin(cv, cx, cy, r, thick, sx=1.0, side=1, symbol=True):
    """Moneda de radio r centrada en (cx, cy). sx < 1 la achata (giro) y
    side (+1/-1) indica de qué lado asoma el canto."""
    sx = max(sx, 0.01)
    rx = r * sx
    face = set()
    for y in range(cv.h):
        for x in range(cv.w):
            dx, dy = (x + 0.5 - cx) / sx, y + 0.5 - cy
            if dx * dx + dy * dy <= (r + 0.15) ** 2:
                face.add((x, y))
    # Canto: la cara desplazada hacia el lado visible
    body = set(face)
    for k in range(1, thick + 1):
        body |= {(x + side * k, y) for x, y in face}
    for x, y in body - face:
        c = ("K2", "K3", "Y2", "K3")[y % 4]
        if (x, y - 1) not in body or (x, y + 1) not in body:
            c = "K2"
        cv.put(x, y, c)
    # Borde de la cara contra el canto
    for x, y in face:
        if (x + side, y) in body - face:
            cv.put(x, y, "K1")

    if rx < 1.6:
        # De canto: una franja de metal
        for x, y in face:
            if (x + side, y) not in body - face:
                cv.put(x, y, "Y3" if x == min(px for px, py in face if py == y) else "K3")
        return body

    for x, y in face:
        if cv.get(x, y) == (138, 66, 31, 255):
            continue
        dx, dy = (x + 0.5 - cx) / sx, y + 0.5 - cy
        d = math.hypot(dx, dy)
        ang = math.degrees(math.atan2(dy, dx)) % 360
        lit = 150 <= ang <= 300          # arriba-izquierda
        rim = max(1.0, r * 0.13)
        if d > r - rim:
            c = "Y3" if lit or ang > 300 or ang < 20 else "Y2"
            if 200 <= ang <= 250 and r >= 6:
                c = "Y4"
        elif d > r - rim - max(1.0, r * 0.1):
            c = "Q" if lit else "K2"
        else:
            u = (dx + dy) / r          # diagonal "/"
            c = "K4"
            if -0.75 <= u <= -0.35 or 0.3 <= u <= 0.45:
                c = "K5"
        cv.put(x, y, c)

    rows = DOLLAR.get(r) if symbol and sx > 0.9 else None
    if rows:
        ox = round(cx - len(rows[0]) / 2)
        oy = round(cy - len(rows) / 2)
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch == "X":
                    cv.put(ox + i, oy + j, "K2")
                elif ch == "h":
                    cv.put(ox + i, oy + j, "Y3")
    elif 2.5 <= rx and sx < 0.9:
        # Moneda girando: el relieve se ve como una raya
        for y in range(round(cy - r * 0.45), round(cy + r * 0.45)):
            cv.put(int(cx), y, "K2")
    return body


def icon32():
    cv = Canvas(32, 32)
    draw_coin(cv, 14, 16, 11, 4)
    cv.outline("K1")
    return cv


def icon16():
    cv = Canvas(16, 16)
    draw_coin(cv, 7.5, 8, 6, 1)
    cv.outline("K1")
    return cv


def spin_sheet():
    """Moneda girando: 4 cuadros de 12x12 (frente, 3/4, canto, 3/4)."""
    sheet = Canvas(48, 12)
    for f, (sx, side) in enumerate(((1.0, 1), (0.6, 1), (0.15, 1), (0.6, -1))):
        c = Canvas(12, 12)
        draw_coin(c, 5.5 + (0.5 if side < 0 else 0), 6, 4, 1, sx, side, symbol=False)
        c.outline("K1")
        sheet.paste(c, f * 12, 0)
    return sheet


def generate(out):
    for sub, cv in (("icons32", icon32()), ("icons", icon16()), ("particles", spin_sheet())):
        os.makedirs(os.path.join(out, sub), exist_ok=True)
        name = "coin_spin" if sub == "particles" else "moneda"
        cv.save(os.path.join(out, sub, f"{name}.png"))
