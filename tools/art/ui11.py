"""Interfaz 11 (docs/style-guide.md §8): texturas 9-slice con marcos dorados.

Paneles crema con marco dorado (#F2D173, brillo #F7EDA4) y borde marrón
(#94552A / #3D1B0B), esquinas redondeadas; botones vivos con brillo arriba y
sombra abajo (pressed = hundido 2 px). Se escriben en assets/iconos/ui/ con
los mismos nombres que usa ThemeBuilder (pisan las del re-estilo automático).
"""
import os
from PIL import Image

O, S, W_, G, GH, CR, CS = "#3D1B0B", "#8E461F", "#94552A", "#F2D173", "#F7EDA4", "#F6EFE2", "#E4D7C7"
BTN = {
    "verde": ("#2E7D4F", "#3FB06A", "#7EE09A"),
    "amarillo": ("#C07A12", "#F6B40E", "#FFE07A"),
    "rojo": ("#953730", "#E0566A", "#FF9AA0"),
    "celeste": ("#2F7FC0", "#4EB0F0", "#A8DCFF"),
    "crema": ("#C9A880", "#F6EFE2", "#FFFFFF"),
    "gris": ("#8E7A70", "#C2A898", "#E4D7C7"),
    "violeta": ("#5E3D8C", "#8A63C2", "#C6A8F0"),
}
BARS = {"verde": ("#3FB06A", "#7EE09A"), "amarillo": ("#F6B40E", "#FFE07A"), "rojo": ("#E0566A", "#FF9AA0"),
        "celeste": ("#4EB0F0", "#A8DCFF"), "violeta": ("#8A63C2", "#C6A8F0")}


def rgb(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def rounded(w, h, layers, radius=2):
    """layers: lista de (inset, color) de afuera hacia adentro, con esquinas recortadas."""
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = im.load()
    for inset, color in layers:
        r = max(0, radius - inset) if inset < radius else 0
        for y in range(inset, h - inset):
            for x in range(inset, w - inset):
                dx = min(x - inset, w - 1 - inset - x)
                dy = min(y - inset, h - 1 - inset - y)
                if dx + dy < radius - inset // 2 and dx < radius and dy < radius:
                    continue
                px[x, y] = rgb(color)
    return im


def panel(fill, frame=G, frame_hi=GH, border=W_):
    """Marco de "ventana" (§8): borde marrón, marco dorado de 4 px con brillo
    arriba y sombra abajo, filete interno marrón y relleno."""
    n = 21
    im = rounded(n, n, [(0, O), (1, border), (2, frame), (6, border), (7, fill)], radius=4)
    px = im.load()
    for x in range(4, n - 4):
        px[x, 2] = rgb(frame_hi)
        px[x, 3] = rgb(frame_hi)
        px[x, n - 3] = rgb(S if frame == G else border)
        px[x, n - 4] = rgb(S if frame == G else border)
    for y in range(4, n - 4):
        px[2, y] = rgb(frame_hi)
    for x in range(8, n - 8):
        px[x, 7] = rgb("#FFFFFF" if fill == CR else fill)
    return im


def inset(fill, shadow):
    im = rounded(9, 9, [(0, S), (1, fill)], radius=1)
    px = im.load()
    for x in range(1, 8):
        px[x, 1] = rgb(shadow)
    return im


def button(color, state):
    """Botón con volumen: brillo de 2 px arriba, cuerpo, sombra de 3 px abajo
    (al apretar se hunde 3 px y pierde la sombra)."""
    dark, mid, light = BTN[color]
    w, h = 16, 18
    off = 3 if state == "pressed" else 0
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    body = rounded(w, h - 3, [(0, O), (1, mid)], radius=3)
    if state != "pressed":
        shadow = rounded(w, h - 3, [(0, O), (1, dark)], radius=3)
        im.alpha_composite(shadow, (0, 3))
    im.alpha_composite(body, (0, off))
    px = im.load()
    for x in range(3, w - 3):
        px[x, 1 + off] = rgb(light)
        px[x, 2 + off] = rgb(light)
        px[x, h - 6 + off] = rgb(dark)
    px[2, 2 + off] = rgb(light)
    px[2, 3 + off] = rgb(light)
    if state == "disabled":
        g = im.convert("LA").convert("RGBA")
        gp, ip = g.load(), im.load()
        for y in range(h):
            for x in range(w):
                if ip[x, y][3]:
                    l = gp[x, y][0]
                    ip[x, y] = (int(l * 0.85 + 30), int(l * 0.78 + 25), int(l * 0.72 + 20), ip[x, y][3])
    return im


def bar_bg():
    return rounded(7, 7, [(0, O), (1, "#5A2E1E")], radius=1)


def bar_fill(color):
    base, hi = BARS[color]
    im = rounded(7, 7, [(0, O), (1, base)], radius=1)
    px = im.load()
    for x in range(1, 6):
        px[x, 1] = rgb(hi)
        px[x, 2] = rgb(hi)
    return im


def topbar():
    im = Image.new("RGBA", (16, 16), rgb("#6D432B"))
    px = im.load()
    for y in range(16):
        for x in range(16):
            if (x + y * 3) % 7 == 0:
                px[x, y] = rgb("#5A3520")
    for x in range(16):
        px[x, 15] = rgb(O)
        px[x, 14] = rgb(G)
        px[x, 13] = rgb(W_)
    return im


def tab_selected():
    return panel("#FFE07A", G, GH, W_)


def arrow(left):
    """Flecha gorda dorada con contorno, rampa y esquinas redondeadas (32x32)."""
    im = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    px = im.load()
    for y in range(4, 28):
        d = abs(y - 16)
        for x in range(8 + d // 2, 22 + d // 2):
            if x - (8 + d // 2) < 9:
                px[(31 - x) if left else x, y] = rgb("#F6B40E" if y < 16 else "#E09A0A")
    src = im.copy()
    sp = src.load()
    for y in range(32):
        for x in range(32):
            if sp[x, y][3] == 0 and any(0 <= x + dx < 32 and 0 <= y + dy < 32 and sp[x + dx, y + dy][3] for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                px[x, y] = rgb(O)
    for y in range(6, 15):
        x = (12 + abs(y - 16) // 2)
        px[(31 - x) if left else x, y] = rgb("#FFE07A")
    return im


def generate(out_root):
    d = os.path.join(out_root, "iconos", "ui")
    os.makedirs(d, exist_ok=True)
    for c in BTN:
        for st in ("normal", "hover", "pressed", "disabled"):
            button(c, st).save(os.path.join(d, "btn_%s_%s.png" % (c, st)))
    panel(CR).save(os.path.join(d, "panel.png"))
    panel("#6D432B", "#C88555", "#E4AD69", O).save(os.path.join(d, "panel_dark.png"))
    panel("#FFFFFF").save(os.path.join(d, "panel_white.png"))
    panel("#FFE07A", G, GH, W_).save(os.path.join(d, "panel_gold.png"))
    panel("#8E7A70", "#C2A898", "#E4D7C7", O).save(os.path.join(d, "panel_slate.png"))
    inset("#F7E7C4", CS).save(os.path.join(d, "inset.png"))
    inset("#7A4A32", "#5A2E1E").save(os.path.join(d, "inset_dark.png"))
    bar_bg().save(os.path.join(d, "bar_bg.png"))
    for c in BARS:
        bar_fill(c).save(os.path.join(d, "bar_%s.png" % c))
    topbar().save(os.path.join(d, "topbar.png"))
    tab_selected().save(os.path.join(d, "tab_selected.png"))
    d32 = os.path.join(out_root, "iconos", "icons32")
    os.makedirs(d32, exist_ok=True)
    arrow(True).save(os.path.join(d32, "izquierda.png"))
    arrow(False).save(os.path.join(d32, "derecha.png"))
    for k, col in (("info", "#4EB0F0"), ("good", "#3FB06A"), ("bad", "#E0566A"), ("reward", "#F6B40E")):
        panel(CR, col, "#FFFFFF", O).save(os.path.join(d, "toast_%s.png" % k))


if __name__ == "__main__":
    generate(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets"))
