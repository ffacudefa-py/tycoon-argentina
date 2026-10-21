#!/usr/bin/env python3
"""Logo de Tycoon Argentina (pixel art 128x128) y variante de ícono (64x64).

Bandera argentina flameando en primer plano con el Sol de Mayo; detrás un
almacén de barrio con toldo celeste y blanco, vidriera, persiana y cartel
con fileteado. Paleta 2.0 de 32 colores (docs/GUIA_PIXEL_ART.md).
Uso: python3 tools/art/logo.py -> assets/pixel_art/logo/
"""
import math
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "assets", "pixel_art", "logo")

P = {  # Paleta 2.0 (32 colores)
    "o": "#1B1A2E", "u": "#2E2B48", "x": "#4A4766", "d": "#6E6B8C", "g": "#9B98B5", "l": "#C9C7DA",
    "w": "#F0EEE6", "W": "#FFFFFF",
    "C1": "#2F6EA8", "C2": "#4E8FC9", "C3": "#74ACDF", "C4": "#A9D2F2",
    "Y1": "#B5700A", "Y2": "#F6B40E", "Y3": "#FFD458", "Y4": "#FFF0A8",
    "R1": "#7E2230", "R2": "#B83A3F", "R3": "#E2665A",
    "G1": "#2D6A3E", "G2": "#4C9A4F", "G3": "#8CCB6C",
    "M1": "#4A2E22", "M2": "#7A4B30", "M3": "#A8714A", "M4": "#D9A877",
    "S1": "#F2C6A0", "S2": "#C98E66", "S3": "#8A5A40",
    "E1": "#F3E1BC", "E2": "#D8BD8C", "Q": "#E0802F",
}


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


class Layer:
    def __init__(self, n):
        self.n = n
        self.im = Image.new("RGBA", (n, n), (0, 0, 0, 0))
        self.px = self.im.load()

    def put(self, x, y, c):
        if 0 <= x < self.n and 0 <= y < self.n and c:
            self.px[x, y] = hexrgb(P[c])

    def get(self, x, y):
        return self.px[x, y] if 0 <= x < self.n and 0 <= y < self.n else (0, 0, 0, 0)

    def rect(self, x, y, w, h, c):
        for j in range(y, y + h):
            for i in range(x, x + w):
                self.put(i, j, c)

    def outline(self, c="o"):
        pts = []
        for y in range(self.n):
            for x in range(self.n):
                if self.get(x, y)[3] == 0 and any(self.get(x + dx, y + dy)[3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    pts.append((x, y))
        for x, y in pts:
            self.put(x, y, c)

    def over(self, other):
        self.im.alpha_composite(other.im)
        self.px = self.im.load()


# Letras 5x7 para el cartel
FONT = {
    "A": ["01110", "10001", "10001", "11111", "10001", "10001", "10001"],
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "C": ["01111", "10000", "10000", "10000", "10000", "10000", "01111"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "K": ["10001", "10010", "10100", "11000", "10100", "10010", "10001"],
    "I": ["111", "010", "010", "010", "010", "010", "111"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
}


def text(layer, s, x, y, c, shadow=None):
    for ch in s:
        g = FONT[ch]
        for j, row in enumerate(g):
            for i, b in enumerate(row):
                if b == "1":
                    if shadow:
                        layer.put(x + i + 1, y + j + 1, shadow)
                    layer.put(x + i, y + j, c)
        x += len(g[0]) + 1


def sky(L, n, clouds=True):
    bands = ["C3", "C3", "C4", "C4", "W"]
    bh = n // len(bands) + 1
    for y in range(n):
        b = min(y // bh, len(bands) - 1)
        c = bands[b]
        # tramado de 2 filas en el borde de cada banda
        if y % bh >= bh - 2 and b + 1 < len(bands) and (y + (y // bh)) % 1 == 0:
            for x in range(n):
                L.put(x, y, bands[b + 1] if (x + y) % 2 else c)
        else:
            L.rect(0, y, n, 1, c)
    if clouds:
        for cx, cy, r in ((100, 14, 5), (110, 12, 7), (119, 15, 4), (8, 30, 3)):
            for y in range(cy - r, cy + r):
                for x in range(cx - 2 * r, cx + 2 * r):
                    if ((x - cx) / (2 * r)) ** 2 + ((y - cy) / r) ** 2 <= 1:
                        L.put(x, y, "W" if y < cy + r // 2 else "l")


def almacen(n=128):
    B = Layer(n)
    x0, x1, top, base = 36, 124, 52, 112
    w = x1 - x0
    # fachada con textura de revoque y ladrillos asomando
    B.rect(x0, top, w, base - top, "E1")
    for y in range(top + 4, base, 6):
        for x in range(x0 + (y // 6 % 2) * 4, x1, 9):
            B.put(x, y, "E2")
            B.put(x + 1, y, "E2")
    B.rect(x1 - 3, top, 3, base - top, "E2")  # sombra lateral
    # cornisa
    B.rect(x0 - 3, top - 4, w + 6, 4, "w")
    B.rect(x0 - 3, top - 1, w + 6, 1, "g")
    for x in range(x0 - 2, x1 + 3, 4):
        B.put(x, top, "d")
    # cartel con fileteado
    sx, sy, sw, sh = x0 + 6, top + 3, w - 12, 14
    B.rect(sx, sy, sw, sh, "C1")
    B.rect(sx, sy, sw, 1, "C2")
    B.rect(sx + 1, sy + 1, sw - 2, 1, "Y2")
    B.rect(sx + 1, sy + sh - 2, sw - 2, 1, "Y2")
    B.rect(sx + 1, sy + 1, 1, sh - 2, "Y2")
    B.rect(sx + sw - 2, sy + 1, 1, sh - 2, "Y2")
    word = "ALMACEN"
    tw = sum(len(FONT[c][0]) + 1 for c in word) - 1
    tx = sx + (sw - tw) // 2
    text(B, word, tx, sy + 4, "Y3", "o")
    # tilde de la É
    ex = tx + sum(len(FONT[c][0]) + 1 for c in "ALMAC")
    B.put(ex + 3, sy + 2, "Y3")
    B.put(ex + 2, sy + 3, "Y3")
    # volutas de fileteado en los extremos
    for cx, flip in ((sx - 1, -1), (sx + sw, 1)):
        for i, (dx, dy) in enumerate(((0, 2), (flip, 3), (flip * 2, 5), (flip * 2, 7), (flip, 9), (0, 10), (flip, 11))):
            B.put(cx + dx, sy + dy, "Y2" if i % 2 else "R2")
    # toldo celeste y blanco con festón
    ay = top + 19
    for x in range(x0 - 2, x1 + 2):
        stripe = ((x - x0) // 5) % 2 == 0
        for y in range(ay, ay + 8):
            if stripe:
                c = "C4" if y == ay else ("C2" if y == ay + 7 else "C3")
            else:
                c = "W" if y == ay else ("l" if y == ay + 7 else "w")
            B.put(x, y, c)
    for x in range(x0 - 2, x1 + 2, 5):
        stripe = ((x - x0) // 5) % 2 == 0
        for i in range(1, 4):
            B.put(x + i, ay + 8, "C2" if stripe else "l")
        B.put(x + 2, ay + 9, "C2" if stripe else "l")
    # sombra del toldo sobre la pared
    B.rect(x0, ay + 10, w - 3, 2, "E2")
    # vidriera con estantes y mercadería
    vx, vy, vw, vh = x0 + 6, ay + 14, 42, 25
    B.rect(vx - 2, vy - 2, vw + 4, vh + 4, "M2")
    B.rect(vx - 2, vy - 2, vw + 4, 1, "M3")
    B.rect(vx, vy, vw, vh, "C4")
    for i in range(vh):
        B.put(vx + 3 + i // 2, vy + vh - 1 - i, "W") if i < vh - 4 else None
    goods = [["Y2", "R2", "G2", "C2", "Q", "R3"], ["G3", "Y3", "M3", "R2", "C3", "Y2"], ["E1", "R3", "G2", "Y2", "M4", "C2"]]
    for row in range(2):
        y = vy + 3 + row * 10
        B.rect(vx, y + 6, vw, 1, "M2")
        for i, x in enumerate(range(vx + 2, vx + vw - 4, 6)):
            c = goods[row][i % 6]
            B.rect(x, y + 1, 4, 5, c)
            B.put(x, y + 1, "W")
            B.rect(x, y + 5, 4, 1, "M1" if row == 2 else "x")
    # frasco de golosinas en la vidriera
    B.rect(vx + vw - 9, vy + vh - 9, 7, 8, "l")
    for (dx, dy, c) in ((1, 3, "R2"), (3, 4, "Y2"), (5, 3, "G2"), (2, 6, "C2"), (4, 6, "R3")):
        B.put(vx + vw - 9 + dx, vy + vh - 9 + dy, c)
    # puerta con persiana a medio bajar
    dx0, dw = x0 + 58, 24
    B.rect(dx0 - 2, vy - 2, dw + 4, base - vy + 2, "M2")
    B.rect(dx0, vy, dw, base - vy, "u")
    for y in range(vy, vy + 14):
        B.rect(dx0, y, dw, 1, "g" if y % 2 == 0 else "d")
    B.rect(dx0, vy + 14, dw, 1, "x")
    B.rect(dx0 + 3, vy + 17, dw - 6, base - vy - 17, "C3")
    B.rect(dx0 + 3, vy + 17, dw - 6, 1, "C4")
    B.put(dx0 + dw - 6, vy + 25, "Y3")
    # cartelito "SE VENDE"/ofertas en la persiana -> "KIOSCO" chico no entra: oferta roja
    B.rect(dx0 + 5, vy + 4, 14, 9, "W")
    B.rect(dx0 + 5, vy + 4, 14, 1, "R2")
    for i, c in enumerate(["R2", "R2", "o", "R2"]):
        B.rect(dx0 + 7 + i * 3, vy + 7, 2, 4, c)
    # macetas y canasto de facturas en la vereda
    for px in (x0 + 1, x1 - 7):
        B.rect(px, base - 6, 6, 6, "Q")
        B.rect(px, base - 6, 6, 1, "Y3")
        B.rect(px - 1, base - 11, 8, 5, "G2")
        B.put(px + 1, base - 11, "G3")
        B.put(px + 5, base - 8, "G1")
    B.outline("o")
    return B


def vereda(L, n, y0):
    L.rect(0, y0, n, n - y0, "E2")
    for y in range(y0, n, 5):
        L.rect(0, y, n, 1, "M4")
        for x in range((y // 5 % 2) * 5, n, 10):
            L.put(x, y + 1, "M4")
            L.put(x, y + 2, "M4")
            L.put(x + 3, y + 3, "M3")
    L.rect(0, y0, n, 1, "o")


def bandera(n, fx0, fy0, fw, fh, amp, waves, pole_top, pole_bottom, pole_x, sun_r):
    F = Layer(n)
    band = fh / 3.0
    for i in range(fw):
        t = i / fw
        phase = 2 * math.pi * waves * t
        dy = amp * math.sin(phase) * (0.35 + 0.65 * t)  # flamea más lejos del mástil
        slope = math.cos(phase)
        shade = 1 if slope > 0.45 else (-1 if slope < -0.45 else 0)
        x = fx0 + i
        for j in range(fh):
            y = int(round(fy0 + j + dy))
            if j < band or j >= 2 * band:
                c = {1: "C4", 0: "C3", -1: "C2"}[shade]
            else:
                c = {1: "W", 0: "W", -1: "l"}[shade]
                if shade == 0 and i % 7 == 3:
                    c = "w"
            F.put(x, y, c)
        # brillo en la cresta de cada onda
        if 0.9 < slope:
            F.put(x, int(round(fy0 + dy)) + 1, "W")
    # Sol de Mayo (centro de la franja blanca, siguiendo la onda)
    sx = fx0 + int(fw * 0.47)
    t = (sx - fx0) / fw
    sdy = amp * math.sin(2 * math.pi * waves * t) * (0.35 + 0.65 * t)
    cy = fy0 + fh / 2.0 + sdy
    cx = sx
    rays = 16
    for k in range(rays):
        a = 2 * math.pi * k / rays
        length = sun_r + (3 if k % 2 == 0 else 2)
        for s in range(sun_r, length + 1):
            px_, py_ = cx + math.cos(a) * s, cy + math.sin(a) * s
            if k % 2 == 1 and s == length:  # rayos ondulados: punta desplazada
                px_ += math.cos(a + 1.3) * 0.8
                py_ += math.sin(a + 1.3) * 0.8
            F.put(int(round(px_)), int(round(py_)), "Y2")
    for y in range(int(cy - sun_r), int(cy + sun_r) + 1):
        for x in range(int(cx - sun_r), int(cx + sun_r) + 1):
            d = math.hypot(x - cx, y - cy)
            if d <= sun_r - 0.2:
                F.put(x, y, "Y3" if d < sun_r - 1.2 else "Y2")
    if sun_r >= 4:  # carita del sol
        F.put(int(cx - 1.5), int(round(cy - 1)), "Y1")
        F.put(int(cx + 1.5), int(round(cy - 1)), "Y1")
        F.put(int(cx), int(round(cy + 1)), "Y1")
        if sun_r >= 5:
            F.put(int(cx - 1), int(round(cy + 2)), "Y1")
            F.put(int(cx + 1), int(round(cy + 2)), "Y1")
    F.outline("o")
    # mástil con remate dorado
    M = Layer(n)
    for y in range(pole_top, pole_bottom):
        M.put(pole_x, y, "M4")
        M.put(pole_x + 1, y, "M3")
        M.put(pole_x + 2, y, "M2")
    for y in range(pole_top - 4, pole_top):
        for x in range(pole_x - 1, pole_x + 4):
            if abs(x - (pole_x + 1)) + abs(y - (pole_top - 2)) <= 2:
                M.put(x, y, "Y3" if x <= pole_x + 1 and y < pole_top - 2 else "Y2")
    M.outline("o")
    M.over(F)
    return M


def make_logo():
    n = 128
    L = Layer(n)
    sky(L, n)
    vereda(L, n, 112)
    L.over(almacen(n))
    # sombra de la bandera sobre la pared (tramada)
    flag = bandera(n, 18, 10, 70, 39, 4.0, 1.6, 6, 124, 13, 6)
    L.over(flag)
    # base del mástil
    for x in range(9, 20):
        L.put(x, 123, "x")
        L.put(x, 124, "u")
    return L


def make_icon():
    n = 64
    L = Layer(n)
    sky(L, n, clouds=False)
    # almacén simplificado: toldo + vidriera abajo a la derecha
    B = Layer(n)
    B.rect(26, 34, 36, 30, "E1")
    B.rect(59, 34, 3, 30, "E2")
    for x in range(24, 64):
        stripe = ((x - 24) // 4) % 2 == 0
        for y in range(36, 42):
            B.put(x, y, ("C3" if y < 41 else "C2") if stripe else ("W" if y < 41 else "l"))
    for x in range(24, 64, 4):
        stripe = ((x - 24) // 4) % 2 == 0
        B.put(x + 1, 42, "C2" if stripe else "l")
        B.put(x + 2, 42, "C2" if stripe else "l")
    B.rect(30, 46, 18, 14, "M2")
    B.rect(31, 47, 16, 12, "C4")
    for i, c in enumerate(["Y2", "R2", "G2", "Q"]):
        B.rect(32 + i * 4, 49, 3, 4, c)
        B.rect(32 + i * 4, 55, 3, 3, ["G2", "Y2", "R3", "C2"][i])
    B.rect(31, 53, 16, 1, "M2")
    B.rect(51, 46, 8, 18, "u")
    for y in range(46, 54, 2):
        B.rect(51, y, 8, 1, "g")
    B.rect(26, 28, 36, 6, "C1")
    B.rect(27, 29, 34, 1, "Y2")
    B.rect(27, 32, 34, 1, "Y2")
    B.outline("o")
    L.over(B)
    L.over(bandera(n, 7, 7, 40, 27, 2.5, 1.3, 5, 63, 3, 4))
    return L


def main():
    os.makedirs(OUT, exist_ok=True)
    logo = make_logo()
    icon = make_icon()
    logo.im.save(os.path.join(OUT, "logo_128.png"))
    icon.im.save(os.path.join(OUT, "icono_64.png"))
    logo.im.resize((512, 512), Image.NEAREST).save(os.path.join(OUT, "logo_512.png"))
    icon.im.resize((192, 192), Image.NEAREST).save(os.path.join(OUT, "icono_192.png"))
    icon.im.resize((512, 512), Image.NEAREST).save(os.path.join(OUT, "icono_512.png"))
    # Ícono adaptativo Android 432x432: frente con margen seguro (zona central 66 %)
    fg = Image.new("RGBA", (432, 432), (0, 0, 0, 0))
    fg.paste(icon.im.resize((256, 256), Image.NEAREST), (88, 88))
    fg.save(os.path.join(OUT, "icono_adaptativo_frente.png"))
    Image.new("RGBA", (432, 432), hexrgb(P["C3"])).save(os.path.join(OUT, "icono_adaptativo_fondo.png"))
    # Hoja de prueba: logo grande + ícono en tamaños reales de launcher
    sheet = Image.new("RGBA", (512 + 16 + 260, 512), hexrgb(P["u"]))
    sheet.alpha_composite(logo.im.resize((512, 512), Image.NEAREST), (0, 0))
    y = 0
    for s in (192, 96, 48, 24):
        sheet.alpha_composite(icon.im.resize((s, s), Image.NEAREST if s % 64 == 0 or s >= 64 else Image.BOX), (528, y))
        y += s + 8
    sheet.save(os.path.join(OUT, "preview_logo.png"))
    used = set(c for c in logo.im.getdata() if c[3]) | set(c for c in icon.im.getdata() if c[3])
    print("colores usados:", len(used), "(paleta de", len(P), ")")


if __name__ == "__main__":
    main()
