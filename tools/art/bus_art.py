"""Colectivos porteños 11 (vista de costado, el frente a la derecha): techo
blanco con equipo de aire, ventanas polarizadas con parantes negros, puertas
vidriadas, cartel LED ámbar con el número de línea y los colores de cada
línea (60, 160, 103 y 59), según la referencia ~/Descargas/colec.webp.

Genera effects/colectivo_anim.png: 2 cuadros por fila (ruedas girando) y una
fila por línea. business_scene.gd elige una fila al azar en cada pasada.
Uso: python3 tools/art/bus_art.py (escribe pixel_art/ y la versión 11 re-estilada).
"""
import os
from PIL import Image

import restyle11

W, H = 128, 50
FRAMES = 2

INK = (24, 20, 28)
GLASS = (62, 110, 170)
GLASS_D = (48, 86, 138)
GLASS_L = (140, 190, 215)
ROOF = (236, 234, 228)
ROOF_D = (196, 194, 190)
TIRE = (30, 28, 34)
HUB = (150, 150, 160)
HUB_L = (205, 205, 215)
LED = (255, 168, 40)
BLUE = (40, 96, 210)
HEAD = (255, 244, 200)
TAIL = (230, 40, 40)

RED = ((140, 24, 32), (200, 40, 40), (236, 86, 72))
YELLOW = ((214, 140, 18), (250, 192, 40), (255, 226, 120))
WHITE = ((190, 186, 182), (238, 234, 228), (255, 255, 250))
CREAM = ((214, 184, 130), (245, 222, 172), (255, 242, 210))
GREEN = ((38, 98, 34), (70, 150, 52), (120, 196, 90))
BLACK = ((20, 18, 24), (44, 40, 48), (70, 66, 76))

# Cada línea: color de arriba (franja del techo y marcos), color de abajo,
# franja (color, y0, y1) y adorno opcional.
LINES = [
    {"num": "60", "top": RED, "low": YELLOW, "stripe": (RED, 27, 28), "deco": "curva"},
    {"num": "160", "top": RED, "low": RED, "stripe": (WHITE, 35, 39), "deco": "rayas"},
    {"num": "103", "top": RED, "low": RED, "stripe": (CREAM, 30, 33), "deco": None},
    {"num": "59", "top": RED, "low": GREEN, "stripe": (YELLOW, 27, 27), "deco": "filete"},
]

DIGITS = {
    "0": ["111", "101", "101", "101", "111"], "1": ["010", "110", "010", "010", "111"],
    "3": ["111", "001", "011", "001", "111"], "5": ["111", "100", "111", "001", "111"],
    "6": ["111", "100", "111", "101", "111"], "9": ["111", "101", "111", "001", "111"],
}

REAR_X, FRONT_X = 28, 88    # ejes
WHEEL_Y, WHEEL_R = 42, 7


def bus(line, frame):
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    p = im.load()

    def put(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            p[x, y] = c + (255,) if len(c) == 3 else c

    def rect(x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                put(x, y, c)

    top, low = line["top"], line["low"]
    # Carrocería: x 1..125, y 3..42, con el frente apenas inclinado arriba.
    for y in range(3, 43):
        x1 = 125 - (1 if y < 6 else 0)
        rect(1, y, x1, y, low[1] if y >= 26 else top[1])
    rect(1, 3, 124, 6, ROOF)                  # techo blanco
    rect(1, 6, 124, 6, ROOF_D)
    rect(2, 3, 123, 3, (255, 255, 255))
    rect(8, 0, 44, 2, ROOF_D)                 # equipo de aire
    rect(9, 0, 43, 0, ROOF)
    rect(1, 7, 125, 8, top[1])
    rect(1, 7, 125, 7, top[2])
    # Franja inferior / adornos
    sc, s0, s1 = line["stripe"]
    rect(1, s0, 125, s1, sc[1])
    rect(1, s0, 125, s0, sc[2])
    if line["deco"] == "curva":                # trazo curvo rojo de la 60
        for i in range(30):
            x = 34 + i
            y = 39 - int(10 * (i / 30) ** 1.6)
            put(x, y, RED[1]); put(x, y - 1, RED[1])
    elif line["deco"] == "rayas":              # rayas rojas sobre la pollera blanca
        for x in range(4, 122, 9):
            for k in range(5):
                put(x + k, 39 - k, RED[0])
    elif line["deco"] == "filete":             # pinceladas amarillas
        for x in range(4, 122, 6):
            put(x, 31, YELLOW[1]); put(x + 1, 30, YELLOW[2])
    # Pollera oscura y paragolpes
    rect(1, 40, 125, 42, BLACK[1])
    rect(1, 40, 125, 40, BLACK[2])
    rect(118, 38, 126, 42, BLACK[0])          # paragolpes delantero
    rect(0, 38, 4, 42, BLACK[0])              # trasero

    # Banda de ventanas: marco negro, vidrio polarizado con reflejos.
    rect(3, 9, 98, 25, INK)
    for seg in [(5, 48), (64, 96)]:
        x0, x1 = seg
        rect(x0, 10, x1, 24, GLASS)
        rect(x0, 19, x1, 24, GLASS_D)
        for x in range(x0 + 10, x1, 11):       # parantes
            rect(x, 10, x + 1, 24, INK)
        for x in range(x0 + 3, x1 - 4, 11):    # reflejos diagonales
            for k in range(6):
                put(x + k, 17 - k, GLASS_L)
                put(x + k + 1, 17 - k, GLASS_L)
    # Cartel LED lateral (número de línea y el cuadradito azul).
    rect(66, 10, 94, 16, INK)
    rect(68, 11, 71, 15, BLUE)
    put(69, 12, (255, 255, 255)); put(69, 13, (255, 255, 255)); put(70, 13, (255, 255, 255))
    x = 74
    for ch in line["num"]:
        for dy, row in enumerate(DIGITS[ch]):
            for dx, v in enumerate(row):
                if v == "1":
                    put(x + dx, 11 + dy, LED)
        x += 4
    for k in range(x + 1, 93, 2):              # texto del recorrido
        put(k, 12, (200, 120, 30)); put(k, 14, (200, 120, 30))

    # Puertas vidriadas (del medio y delantera, adelante del eje).
    for d0 in (50, 100):
        rect(d0, 9, d0 + 11, 39, INK)
        rect(d0 + 1, 10, d0 + 4, 38, GLASS)
        rect(d0 + 7, 10, d0 + 10, 38, GLASS)
        rect(d0 + 1, 24, d0 + 4, 38, GLASS_D)
        rect(d0 + 7, 24, d0 + 10, 38, GLASS_D)
        put(d0 + 2, 14, GLASS_L); put(d0 + 8, 14, GLASS_L)
        put(d0 + 2, 15, GLASS_L); put(d0 + 8, 15, GLASS_L)
        rect(d0 + 5, 9, d0 + 6, 39, INK)
    # Parabrisas de costado y espejo.
    rect(113, 8, 124, 31, INK)
    rect(114, 9, 123, 30, GLASS)
    rect(114, 22, 123, 30, GLASS_D)
    for k in range(5):
        put(116 + k, 18 - k, GLASS_L)
    rect(125, 9, 127, 10, INK)
    rect(126, 11, 127, 16, INK)
    # Luces
    rect(122, 33, 125, 35, HEAD)
    put(125, 36, LED); put(124, 36, LED)
    rect(1, 27, 2, 33, TAIL)

    # Pasaruedas y ruedas (el cubo gira entre cuadros).
    for cx in (REAR_X, FRONT_X):
        for y in range(WHEEL_Y - 9, H):
            for x in range(cx - 9, cx + 10):
                if (x - cx) ** 2 + (y - WHEEL_Y) ** 2 <= 81 and y <= 42:
                    put(x, y, INK)
        for y in range(WHEEL_Y - WHEEL_R, WHEEL_Y + WHEEL_R + 1):
            for x in range(cx - WHEEL_R, cx + WHEEL_R + 1):
                d = (x - cx) ** 2 + (y - WHEEL_Y) ** 2
                if d <= WHEEL_R ** 2:
                    put(x, y, HUB if d <= 9 else TIRE)
        put(cx, WHEEL_Y, HUB_L)
        for dx, dy in ([(-2, -2), (2, 2)] if frame == 0 else [(2, -2), (-2, 2)]):
            put(cx + dx, WHEEL_Y + dy, HUB_L)

    # Contorno de 1 px por fuera de la silueta.
    src = im.copy()
    sp = src.load()
    for y in range(H):
        for x in range(W):
            if sp[x, y][3]:
                continue
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < W and 0 <= ny < H and sp[nx, ny][3]:
                    p[x, y] = INK + (255,)
                    break
    return im


def sheet():
    out = Image.new("RGBA", (W * FRAMES, H * len(LINES)), (0, 0, 0, 0))
    for r, line in enumerate(LINES):
        for f in range(FRAMES):
            out.paste(bus(line, f), (f * W, r * H))
    return out


if __name__ == "__main__":
    root = restyle11.ROOT
    img = sheet()
    src = os.path.join(restyle11.SRC, "effects", "colectivo_anim.png")
    img.save(src)
    dst = os.path.join(root, "assets", "escenarios", "effects", "colectivo_anim.png")
    restyle11.restyle(Image.open(src), selective=True).save(dst)
    print(src, dst, img.size)
