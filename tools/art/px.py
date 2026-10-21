"""Paleta y utilidades de dibujo pixel art para Tycoon Argentina.

Todo el arte del juego se genera con estos scripts (python3 tools/art/generate.py).
Reglas: paleta cerrada (PAL), píxeles enteros, sin antialiasing, contornos
oscuros de 1 px, luz desde arriba a la izquierda.
"""
from PIL import Image

# Paleta "Tycoon Argentina" (32 colores). Clave de una letra -> RGB.
PAL = {
    "o": (27, 24, 48),      # contorno
    "u": (43, 39, 70),      # azul noche
    "x": (61, 58, 85),      # pizarra
    "d": (93, 91, 122),     # gris oscuro
    "g": (140, 138, 168),   # gris
    "l": (194, 192, 214),   # gris claro
    "w": (242, 240, 230),   # blanco cálido
    "h": (255, 250, 240),   # brillo
    "e": (244, 227, 193),   # crema
    "E": (224, 199, 154),   # crema sombra
    "y": (255, 216, 92),    # amarillo
    "Y": (245, 184, 46),    # amarillo oscuro
    "L": (255, 241, 168),   # amarillo pálido
    "r": (217, 74, 74),     # rojo
    "R": (168, 50, 58),     # rojo oscuro
    "p": (240, 124, 108),   # salmón
    "B": (122, 38, 56),     # bordó
    "c": (117, 196, 242),   # celeste
    "C": (79, 164, 224),    # celeste oscuro
    "b": (185, 228, 255),   # celeste claro
    "A": (52, 101, 164),    # azul
    "n": (76, 175, 92),     # verde
    "G": (47, 125, 74),     # verde oscuro
    "N": (143, 212, 122),   # verde claro
    "k": (90, 58, 42),      # marrón oscuro
    "m": (138, 90, 58),     # marrón
    "M": (185, 132, 88),    # marrón claro
    "t": (224, 184, 138),   # madera clara
    "q": (245, 154, 69),    # naranja
    "Q": (217, 112, 43),    # naranja oscuro
    "v": (155, 107, 201),   # violeta
    "V": (107, 63, 143),    # violeta oscuro
    "s": (242, 201, 160),   # piel 1
    "S": (217, 160, 116),   # piel 1 sombra
    "z": (168, 106, 72),    # piel 2
    "Z": (110, 70, 48),     # piel 2 sombra
}

# Familias de color con 3 tonos (luz, base, sombra) para objetos.
RAMPS = {
    "celeste": ("b", "c", "C"),
    "azul": ("c", "A", "u"),
    "amarillo": ("L", "y", "Y"),
    "rojo": ("p", "r", "R"),
    "bordo": ("r", "B", "o"),
    "naranja": ("y", "q", "Q"),
    "verde": ("N", "n", "G"),
    "marron": ("M", "m", "k"),
    "crema": ("h", "e", "E"),
    "blanco": ("h", "w", "l"),
    "gris": ("l", "g", "d"),
    "violeta": ("l", "v", "V"),
    "madera": ("t", "M", "m"),
}


def rgb(c):
    if c is None:
        return None
    if isinstance(c, tuple):
        return c
    return PAL[c]


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.px = self.img.load()

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h and c is not None:
            r = rgb(c)
            self.px[x, y] = (r[0], r[1], r[2], 255)

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[x, y]
        return (0, 0, 0, 0)

    def clear(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = (0, 0, 0, 0)

    def rect(self, x, y, w, h, c):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, c)

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def frame(self, x, y, w, h, c):
        self.hline(x, y, w, c)
        self.hline(x, y + h - 1, w, c)
        self.vline(x, y, h, c)
        self.vline(x + w - 1, y, h, c)

    def box(self, x, y, w, h, ramp, outline="o"):
        """Caja sombreada: contorno, luz arriba/izquierda, sombra abajo/derecha."""
        light, base, dark = RAMPS[ramp] if isinstance(ramp, str) and ramp in RAMPS else ramp
        self.rect(x, y, w, h, base)
        self.hline(x + 1, y + 1, w - 2, light)
        self.vline(x + 1, y + 1, h - 2, light)
        self.hline(x + 1, y + h - 2, w - 2, dark)
        self.vline(x + w - 2, y + 1, h - 2, dark)
        if outline:
            self.frame(x, y, w, h, outline)

    def dither(self, x, y, w, h, c1, c2, phase=0):
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.put(xx, yy, c1 if (xx + yy + phase) % 2 == 0 else c2)

    def ellipse(self, cx, cy, rx, ry, c, outline=None):
        for yy in range(cy - ry, cy + ry + 1):
            for xx in range(cx - rx, cx + rx + 1):
                dx = (xx - cx) / (rx + 0.5)
                dy = (yy - cy) / (ry + 0.5)
                if dx * dx + dy * dy <= 1.0:
                    self.put(xx, yy, c)
        if outline:
            self.outline_color_region(cx - rx - 1, cy - ry - 1, rx * 2 + 3, ry * 2 + 3, rgb(c), outline)

    def outline_color_region(self, x, y, w, h, color_rgb, outline):
        pts = []
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                if self.get(xx, yy)[:3] == color_rgb and self.get(xx, yy)[3] > 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = xx + dx, yy + dy
                        p = self.get(nx, ny)
                        if p[3] == 0 or p[:3] != color_rgb:
                            if p[3] == 0:
                                pts.append((nx, ny))
        for p in pts:
            self.put(p[0], p[1], outline)

    def outline_all(self, c="o"):
        """Contorno exterior de 1 px alrededor de todo lo dibujado."""
        pts = []
        for yy in range(self.h):
            for xx in range(self.w):
                if self.get(xx, yy)[3] == 0:
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        if self.get(xx + dx, yy + dy)[3] > 0:
                            pts.append((xx, yy))
                            break
        for p in pts:
            self.put(p[0], p[1], c)

    def blit(self, other, x, y, flip=False):
        for yy in range(other.h):
            for xx in range(other.w):
                p = other.get(other.w - 1 - xx if flip else xx, yy)
                if p[3] > 0:
                    self.px_set(x + xx, y + yy, p)

    def px_set(self, x, y, p):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = p

    def stamp(self, rows, x, y, mapping=None, flip=False):
        """Dibuja un mapa de caracteres (lista de strings). '.' = transparente."""
        for j, row in enumerate(rows):
            n = len(row)
            for i, ch in enumerate(row):
                if ch in ". ":
                    continue
                c = (mapping or {}).get(ch, ch)
                xx = x + (n - 1 - i if flip else i)
                self.put(xx, y + j, c)

    def save(self, path, scale=1):
        img = self.img
        if scale != 1:
            img = img.resize((self.w * scale, self.h * scale), Image.NEAREST)
        img.save(path)


def from_rows(rows, mapping=None):
    h = len(rows)
    w = max(len(r) for r in rows)
    cv = Canvas(w, h)
    cv.stamp(rows, 0, 0, mapping)
    return cv
