"""Pixel art 2.0: paleta de 32 colores con rampas y lienzo con utilidades.

Reglas (docs/REDISENO.md): luz arriba-izquierda, contorno exterior #1B1A2E,
líneas internas con el tono más oscuro de la rampa, sin píxeles huérfanos,
tramado sólo en cielos/superficies grandes. 1 metro = 24 px.
"""
from PIL import Image

PAL = {
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

# Rampas (sombra, medio, luz, brillo) por material
RAMP = {
    "celeste": ("C1", "C2", "C3", "C4"),
    "amarillo": ("Y1", "Y2", "Y3", "Y4"),
    "rojo": ("R1", "R2", "R3", "R3"),
    "verde": ("G1", "G2", "G3", "G3"),
    "madera": ("M1", "M2", "M3", "M4"),
    "crema": ("E2", "E2", "E1", "w"),
    "blanco": ("l", "w", "W", "W"),
    "gris": ("x", "d", "g", "l"),
    "noche": ("o", "u", "x", "d"),
    "piel": ("S3", "S2", "S1", "S1"),
    "naranja": ("Y1", "Q", "Y3", "Y4"),
    "bordo": ("o", "R1", "R2", "R3"),
}

_cache = {}


def rgba(c):
    if c not in _cache:
        h = PAL[c].lstrip("#")
        _cache[c] = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
    return _cache[c]


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.px = self.img.load()

    def put(self, x, y, c):
        if c and 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = rgba(c)

    def get(self, x, y):
        return self.px[x, y] if 0 <= x < self.w and 0 <= y < self.h else (0, 0, 0, 0)

    def rect(self, x, y, w, h, c):
        for j in range(max(0, y), min(self.h, y + h)):
            for i in range(max(0, x), min(self.w, x + w)):
                self.px[i, j] = rgba(c)

    def hline(self, x, y, w, c):
        self.rect(x, y, w, 1, c)

    def vline(self, x, y, h, c):
        self.rect(x, y, 1, h, c)

    def frame(self, x, y, w, h, c):
        self.hline(x, y, w, c)
        self.hline(x, y + h - 1, w, c)
        self.vline(x, y, h, c)
        self.vline(x + w - 1, y, h, c)

    def shaded(self, x, y, w, h, ramp, outline=True):
        """Bloque con luz arriba-izquierda y sombra abajo-derecha."""
        s, m, l, hi = RAMP[ramp]
        self.rect(x, y, w, h, m)
        self.hline(x, y, w, l)
        self.vline(x, y, h, l)
        self.hline(x, y + h - 1, w, s)
        self.vline(x + w - 1, y, h, s)
        if w > 4 and h > 4:
            self.put(x + 1, y + 1, hi)
        if outline:
            self.frame(x - 1, y - 1, w + 2, h + 2, "o")

    def ellipse(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry), int(cy + ry) + 1):
            for x in range(int(cx - rx), int(cx + rx) + 1):
                if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1:
                    self.put(x, y, c)

    def dither(self, x, y, w, h, c1, c2):
        for j in range(y, y + h):
            for i in range(x, x + w):
                self.put(i, j, c1 if (i + j) % 2 else c2)

    def outline(self, c="o"):
        pts = []
        for y in range(self.h):
            for x in range(self.w):
                if self.px[x, y][3] == 0 and any(self.get(x + dx, y + dy)[3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    pts.append((x, y))
        for x, y in pts:
            self.put(x, y, c)

    def paste(self, other, x, y, flip=False):
        for j in range(other.h):
            for i in range(other.w):
                p = other.px[other.w - 1 - i if flip else i, j]
                if p[3] and 0 <= x + i < self.w and 0 <= y + j < self.h:
                    self.px[x + i, y + j] = p

    def stamp(self, rows, x, y, keys):
        """Mapa de caracteres -> colores de la paleta (keys: char -> clave)."""
        for j, row in enumerate(rows):
            for i, ch in enumerate(row):
                if ch in keys:
                    self.put(x + i, y + j, keys[ch])

    def clean_orphans(self):
        """Quita píxeles huérfanos: un píxel opaco sin ningún vecino del mismo
        color toma el color más común de sus vecinos (salvo contorno)."""
        changes = []
        for y in range(1, self.h - 1):
            for x in range(1, self.w - 1):
                p = self.px[x, y]
                if p[3] == 0 or p == rgba("o"):
                    continue
                nb = [self.px[x + dx, y + dy] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1))]
                if p in nb:
                    continue
                opaque = [n for n in nb[:4] if n[3] and n != rgba("o")]
                if len(opaque) >= 3:
                    changes.append((x, y, max(set(opaque), key=opaque.count)))
        for x, y, c in changes:
            self.px[x, y] = c
        return len(changes)

    def save(self, path, scale=1):
        im = self.img if scale == 1 else self.img.resize((self.w * scale, self.h * scale), Image.NEAREST)
        im.save(path)


def sheet(frames):
    """Une cuadros iguales en una tira horizontal."""
    w, h = frames[0].w, frames[0].h
    s = Canvas(w * len(frames), h)
    for i, f in enumerate(frames):
        s.paste(f, i * w, 0)
    return s
