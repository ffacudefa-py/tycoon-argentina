"""Marcos de interfaz pixel art (todos pensados como 9-slice)."""
from px import Canvas, PAL

BUTTON_COLORS = {
    # nombre: (luz, base, sombra/labio)
    "verde": ("N", "n", "G"),
    "amarillo": ("L", "y", "Y"),
    "rojo": ("p", "r", "R"),
    "celeste": ("b", "c", "C"),
    "crema": ("h", "e", "E"),
    "gris": ("l", "g", "d"),
    "violeta": ("l", "v", "V"),
}


def button(color, state):
    """16x16, márgenes 9-slice: izq/der 4, arriba 4, abajo 6.
    normal: labio de 2 px abajo; pressed: sin labio, desplazado; disabled: gris."""
    light, base, dark = BUTTON_COLORS["gris" if state == "disabled" else color]
    cv = Canvas(16, 16)
    top = 2 if state == "pressed" else 0
    # cuerpo
    cv.rect(1, top + 1, 14, 15 - top - 1, base)
    # labio inferior
    if state != "pressed":
        cv.rect(1, 12, 14, 3, dark)
    else:
        cv.rect(1, 14, 14, 1, dark)
    # brillo
    cv.hline(2, top + 1, 12, light)
    cv.vline(1, top + 2, 9 - top if state != "pressed" else 10, light)
    cv.put(2, top + 2, "h" if color not in ("crema",) else "w")
    # contorno con esquinas recortadas
    cv.hline(1, top, 14, "o")
    cv.hline(1, 15, 14, "o")
    cv.vline(0, top + 1, 15 - top - 1, "o")
    cv.vline(15, top + 1, 15 - top - 1, "o")
    if state == "disabled":
        cv.rect(2, top + 2, 12, 9, "g")
        cv.hline(2, top + 1, 12, "l")
    return cv


def panel(fill, light, shadow, border="o", inner=None):
    """24x24, 9-slice margen 6. Marco con esquinas redondeadas pixel."""
    cv = Canvas(24, 24)
    cv.rect(1, 1, 22, 22, fill)
    cv.hline(2, 1, 20, light)
    cv.vline(1, 2, 19, light)
    cv.hline(2, 22, 20, shadow)
    cv.vline(22, 2, 20, shadow)
    cv.hline(2, 0, 20, border)
    cv.hline(2, 23, 20, border)
    cv.vline(0, 2, 20, border)
    cv.vline(23, 2, 20, border)
    for x, y in ((1, 1), (22, 1), (1, 22), (22, 22)):
        cv.put(x, y, border)
    if inner:
        cv.hline(3, 3, 18, inner)
    return cv


def inset(fill, shadow, light):
    """Ranura hundida 12x12 (margen 3)."""
    cv = Canvas(12, 12)
    cv.rect(0, 0, 12, 12, fill)
    cv.hline(0, 0, 12, shadow)
    cv.vline(0, 0, 12, shadow)
    cv.hline(1, 11, 11, light)
    cv.vline(11, 1, 11, light)
    return cv


def bar_bg():
    cv = Canvas(8, 8)
    cv.rect(0, 0, 8, 8, "o")
    cv.rect(1, 1, 6, 6, "u")
    cv.hline(1, 1, 6, "o")
    return cv


def bar_fill(color):
    light, base, dark = BUTTON_COLORS[color]
    cv = Canvas(8, 8)
    cv.rect(0, 0, 8, 8, base)
    cv.hline(0, 0, 8, light)
    cv.hline(0, 7, 8, dark)
    return cv


def tabbar():
    cv = Canvas(8, 8)
    cv.rect(0, 0, 8, 8, "u")
    cv.hline(0, 0, 8, "o")
    cv.hline(0, 1, 8, "x")
    return cv


def tab_selected():
    cv = Canvas(16, 16)
    cv.rect(1, 1, 14, 15, "Y")
    cv.rect(1, 1, 14, 13, "y")
    cv.hline(2, 1, 12, "L")
    cv.hline(1, 0, 14, "o")
    cv.vline(0, 1, 15, "o")
    cv.vline(15, 1, 15, "o")
    cv.hline(0, 15, 16, "o")
    return cv


def badge():
    cv = Canvas(10, 10)
    cv.ellipse(4, 4, 4, 4, "r")
    cv.ellipse(4, 4, 3, 3, "r")
    cv.put(3, 2, "p")
    cv.put(2, 3, "p")
    cv.outline_all("o")
    return cv


def bubble():
    """Globo de diálogo 24x24 (margen 6), fondo blanco cálido."""
    return panel("w", "h", "l")


def bubble_tail():
    rows = [
        "ooooooooo",
        ".owwwwwwo",
        "..owwwwo.",
        "...owwo..",
        "....oo...",
    ]
    cv = Canvas(9, 5)
    cv.stamp(rows, 0, 0)
    return cv


def topbar_bg():
    cv = Canvas(8, 8)
    cv.rect(0, 0, 8, 8, "u")
    cv.hline(0, 6, 8, "x")
    cv.hline(0, 7, 8, "o")
    return cv


def toast_bg(kind):
    colors = {"info": ("x", "d", "u"), "good": ("G", "n", "o"), "bad": ("R", "r", "o"), "reward": ("Y", "y", "o")}
    fill, light, border = colors[kind]
    return panel(fill, light, "o", border)


def chip(color):
    light, base, dark = BUTTON_COLORS[color]
    cv = Canvas(12, 12)
    cv.rect(1, 1, 10, 10, base)
    cv.hline(2, 1, 8, light)
    cv.hline(2, 10, 8, dark)
    cv.hline(2, 0, 8, "o")
    cv.hline(2, 11, 8, "o")
    cv.vline(0, 2, 8, "o")
    cv.vline(11, 2, 8, "o")
    for x, y in ((1, 1), (10, 1), (1, 10), (10, 10)):
        cv.put(x, y, "o")
    return cv


def pointer_hand(frame):
    """Mano que señala (tutorial), 16x16, 2 cuadros."""
    rows = [
        "......oo........",
        ".....owwo.......",
        ".....owwo.......",
        ".....owwo.......",
        ".....owwooo.....",
        ".....owwowwoo...",
        "..oo.owwowwowo..",
        ".owwoowwwwwwwwo.",
        ".owwwowwwwwwwwo.",
        "..owwwwwwwwwwlo.",
        "...owwwwwwwwwlo.",
        "...owwwwwwwwlo..",
        "....owwwwwwllo..",
        "....olllllllo...",
        ".....ooooooo....",
        "................",
    ]
    cv = Canvas(16, 16)
    cv.stamp(rows, 0, 0 if frame == 0 else 1)
    return cv


def toggle(on):
    """Interruptor 26x14."""
    cv = Canvas(26, 14)
    track = "n" if on else "d"
    cv.rect(1, 2, 24, 10, track)
    cv.hline(2, 3, 22, "N" if on else "g")
    cv.hline(2, 1, 22, "o")
    cv.hline(2, 12, 22, "o")
    cv.vline(0, 3, 8, "o")
    cv.vline(25, 3, 8, "o")
    cv.put(1, 2, "o"); cv.put(24, 2, "o"); cv.put(1, 11, "o"); cv.put(24, 11, "o")
    kx = 13 if on else 1
    cv.rect(kx + 1, 1, 10, 12, "w")
    cv.hline(kx + 2, 2, 8, "h")
    cv.hline(kx + 1, 11, 10, "l")
    cv.frame(kx, 0, 12, 14, "o")
    return cv


def grabber():
    cv = Canvas(12, 16)
    cv.rect(1, 1, 10, 14, "y")
    cv.hline(2, 1, 8, "L")
    cv.rect(1, 12, 10, 3, "Y")
    cv.frame(0, 0, 12, 16, "o")
    return cv


def generate(out):
    import os
    d = os.path.join(out, "ui")
    os.makedirs(d, exist_ok=True)
    for color in BUTTON_COLORS:
        for state in ("normal", "pressed", "disabled", "hover"):
            st = "normal" if state == "hover" else state
            cv = button(color, st)
            cv.save(f"{d}/btn_{color}_{state}.png")
    panel("e", "h", "E").save(f"{d}/panel.png")
    panel("u", "x", "o").save(f"{d}/panel_dark.png")
    panel("w", "h", "l").save(f"{d}/panel_white.png")
    panel("y", "L", "Y").save(f"{d}/panel_gold.png")
    panel("x", "d", "u").save(f"{d}/panel_slate.png")
    inset("E", "M", "h").save(f"{d}/inset.png")
    inset("x", "o", "d").save(f"{d}/inset_dark.png")
    bar_bg().save(f"{d}/bar_bg.png")
    for c in ("verde", "amarillo", "celeste", "rojo", "violeta"):
        bar_fill(c).save(f"{d}/bar_{c}.png")
    tabbar().save(f"{d}/tabbar.png")
    tab_selected().save(f"{d}/tab_selected.png")
    badge().save(f"{d}/badge.png")
    bubble().save(f"{d}/bubble.png")
    bubble_tail().save(f"{d}/bubble_tail.png")
    topbar_bg().save(f"{d}/topbar.png")
    for k in ("info", "good", "bad", "reward"):
        toast_bg(k).save(f"{d}/toast_{k}.png")
    for c in ("verde", "amarillo", "rojo", "celeste", "gris", "violeta"):
        chip(c).save(f"{d}/chip_{c}.png")
    for f in range(2):
        pointer_hand(f).save(f"{d}/pointer_{f}.png")
    toggle(True).save(f"{d}/toggle_on.png")
    toggle(False).save(f"{d}/toggle_off.png")
    grabber().save(f"{d}/grabber.png")
