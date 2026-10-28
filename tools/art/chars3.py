"""Personajes 11 (docs/style-guide.md §5): chibi de 32x48, 12 cuadros por hoja.

Cuadros: 0-3 caminar · 4-5 idle (respira y parpadea) · 6-7 trabajar ·
8-9 festejar · 10 feliz · 11 triste leve. Pies en la fila 46. La cara mira
casi de frente (como en la referencia) aunque el cuerpo camine de costado.
Cabeza ~45 % de la altura, ojos 2x3 con brillo, bocas grandes y expresivas,
pelo con mechones en zigzag, ropa con rampa de 3 tonos y detalles, contorno
marrón (#3D1B0B) aclarado (#8E461F) en la cara de luz, sombra de apoyo.
Salida: assets/personajes/worker_<n>.png y customer_<n>.png (384x48).
"""
import os
from px2 import Canvas, sheet, rgba
import palette11  # noqa: F401  (instala la paleta 11)
from palette11 import ramp

FW, FH, FEET = 32, 48, 46
SKINS = [("iK1", "iK2", "iK3"), ("iK1", "iK2", "iK3"), ("iK2", "iK3", "i_marron0"), ("i_naranja3", "iK2", "iK3")]

# pelo, peinado, ropa, pantalón, contextura (ancho del torso), accesorio, piel, oficio
CUSTOMERS = [
    ("pelo_castano", "flequillo", "celeste", "noche", 12, "", 0, ""),
    ("pelo_negro", "largo", "rojo", "azul", 11, "", 1, "", "pollera"),
    ("pelo_rubio", "rulos", "verde", "marron", 12, "", 0, ""),
    ("pelo_negro", "boina", "blanco", "noche", 13, "mate", 2, ""),
    ("pelo_canoso", "pelado", "amarillo", "marron", 14, "bigote", 0, "", "panza"),
    ("pelo_rojo", "rodete", "violeta", "noche", 11, "", 3, "", "pollera"),
    ("pelo_castano", "gorra", "naranja", "azul", 12, "panuelo", 2, ""),
    ("pelo_negro", "parado", "celeste", "marron", 12, "camiseta", 1, ""),
]
WORKERS = [
    ("pelo_castano", "gorra", "celeste", "noche", 12, "delantal", 0, "cobrar"),
    ("pelo_negro", "rodete", "rojo", "noche", 11, "delantal", 1, "cajon"),
    ("pelo_rubio", "gorra", "verde", "marron", 13, "delantal", 0, "mate"),
    ("pelo_negro", "boina", "amarillo", "noche", 12, "panuelo", 2, "cortar"),
    ("pelo_rojo", "largo", "naranja", "azul", 11, "delantal", 3, "cobrar"),
    ("pelo_castano", "gorra", "violeta", "noche", 14, "delantal", 0, "cajon", "panza"),
    ("pelo_canoso", "pelado", "celeste", "marron", 13, "bigote", 1, "mate", "panza"),
    ("pelo_negro", "parado", "rojo", "azul", 12, "delantal", 2, "cortar"),
]

HEAD_CX, HEAD_CY, HEAD_R = 16, 16, 10


def shadow(cv, jump=0):
    rx = 8.0 - abs(jump) * 1.2
    for x in range(8, 25):
        for y in (FEET, FEET + 1):
            dx = (x - 16) / rx
            if dx * dx <= 1.0 and not cv.get(x, y)[3]:
                cv.img.putpixel((x, y), (61, 27, 11, 85))


# ------------------------------------------------------------------ cuerpo

def legs(cv, pose, f, pants, oy):
    s, m, l, _ = ramp(pants)
    spread = [(-4, 3), (-1, 1), (3, -4), (1, -1)][f] if pose == "walk" else (0, 0)
    base = FEET - 1 + min(0, oy)
    for i, (lx, off) in enumerate(((12, spread[0]), (17, spread[1]))):
        top = 38 + oy
        for y in range(top, base):
            x = lx + round(off * (y - top) / max(1, base - top))
            cv.rect(x, y, 3, 1, m if i else s)
            cv.put(x, y, l if i else m)
        fx = lx + off
        cv.rect(fx - 1, base, 5, 2, "i_marron0")
        cv.hline(fx, base, 3, "i_marron1")
        cv.put(fx + 3, base + 1, "i_marron2")


def torso(cv, cloth, extra, width, oy):
    s, m, l, h = ramp(cloth)
    x0 = 16 - width // 2
    y0 = 27 + oy
    hgt = 12
    cv.rect(x0, y0, width, hgt, m)
    cv.rect(x0 + 1, y0, 2, hgt - 1, l)
    cv.rect(x0 + width - 3, y0, 3, hgt, s)
    cv.hline(x0, y0 + hgt - 1, width, s)
    cv.hline(x0 + 2, y0, width - 4, s)
    cv.hline(x0 + 3, y0 + 1, width - 6, s)
    for c in ((x0, y0), (x0 + width - 1, y0)):
        cv.img.putpixel(c, (0, 0, 0, 0))
    cv.put(x0 + 1, y0 + 1, h)                       # brillo en el hombro
    cv.put(x0 + 2, y0 + 1, h)
    cv.put(x0 + 3, y0 + 7, s)                       # pliegues de la cintura
    cv.put(x0 + width - 5, y0 + 8, s)
    cv.hline(x0, y0 + hgt - 2, width, "i_marron0")
    cv.put(16, y0 + hgt - 2, "i_amarillo2")
    cv.put(15, y0 + 1, "iK2")
    cv.put(16, y0 + 1, "iK2")
    cv.put(16, y0 + 2, "iK2")
    if extra == "camiseta":
        for x in range(x0 + 2, x0 + width - 1, 3):
            cv.vline(x, y0 + 2, hgt - 4, "i_blanco2")
    elif extra in ("delantal", ""):
        for yy in (y0 + 4, y0 + 7):
            cv.put(17, yy, h)
    if extra == "delantal":
        cv.rect(13, y0 + 3, 7, hgt + 1, "iC")
        cv.vline(13, y0 + 3, hgt + 1, "iWh")
        cv.vline(19, y0 + 3, hgt + 1, "iCs")
        cv.hline(13, y0 + hgt + 3, 7, "iCs")
        cv.rect(15, y0 + 7, 3, 2, "iCs")
        cv.vline(14, y0, 3, "iC")
        cv.vline(19, y0, 3, "iC")
    if extra == "panuelo":
        cv.rect(13, y0 - 1, 7, 3, "i_rojo1")
        cv.hline(13, y0 - 1, 7, "i_rojo2")
        cv.rect(15, y0 + 2, 3, 3, "i_rojo0")
        cv.put(16, y0 + 3, "i_rojo1")


def arm(cv, x, y, dx, dy, cloth, skin, fist=False):
    s, m, l, _ = ramp(cloth)
    if dy > 0:                                      # separación del torso
        for i in range(min(dy, 6)):
            if not cv.get(x + (3 if x < 16 else -1), y + i)[3]:
                cv.put(x + (3 if x < 16 else -1), y + i, "iS")
    steps = max(abs(dx), abs(dy), 1)
    for i in range(steps):
        px = x + round(dx * i / steps)
        py = y + round(dy * i / steps)
        cv.rect(px, py, 3, 2, m)
        cv.put(px, py, l)
        cv.put(px + 2, py + 1, s)
    hx, hy = x + dx, y + dy
    size = 3
    cv.rect(hx, hy, size + 1, size, skin[0])
    cv.put(hx + size, hy + size - 1, skin[1])
    if fist:
        cv.hline(hx, hy + 1, size, skin[1])


# ------------------------------------------------------------------ cabeza

def in_head(x, y, oy):
    dx, dy = (x - HEAD_CX) / (HEAD_R + 0.4), (y - (HEAD_CY + oy)) / (HEAD_R + 0.4)
    return dx * dx + dy * dy <= 1.0


def head(cv, skin, oy):
    k1, k2, k3 = skin
    cy = HEAD_CY + oy
    cv.ellipse(HEAD_CX, cy, HEAD_R, HEAD_R, k1)
    for x in range(6, 27):
        for y in range(cy + 5, cy + 11):
            if in_head(x, y, oy) and not in_head(x - 1, y + 2, oy):
                cv.put(x, y, k2)
    for x in range(22, 27):
        for y in range(cy - 2, cy + 9):
            if in_head(x, y, oy) and not in_head(x + 2, y, oy):
                cv.put(x, y, k2)
    cv.rect(13, cy + 10, 7, 2, k3)
    for x in range(10, 23):                         # sombra bajo el mentón
        if in_head(x, cy + 9, oy) and not in_head(x, cy + 10, oy):
            cv.put(x, cy + 9, k3)
    for ex in (5, 26):
        cv.rect(ex, cy + 1, 2, 4, k2)
        cv.put(ex + (1 if ex == 5 else 0), cy + 2, k3)


def hair(cv, hair_ramp, style, oy):
    hs, hm, hl, hh = ramp(hair_ramp)
    cy = HEAD_CY + oy
    for x in range(8, 25):                          # sombra del pelo sobre la frente
        if in_head(x, cy - 2, oy):
            cv.put(x, cy - 2, "iK2")
    if style == "pelado":
        for x in (5, 6, 25, 26):
            cv.vline(x, cy - 2, 5, hm)
        cv.put(9, cy - 7, "iWh")
        cv.put(10, cy - 8, "iWh")
        return False
    for x in range(4, 29):
        fringe = cy - 3 - (1 if (x // 2) % 2 else 0) - (2 if x in (8, 9, 16, 17, 23) else 0)
        if style == "parado":
            fringe -= 1
        for y in range(cy - 14, fringe + 1):
            if not in_head(x, y + (1 if style == "rulos" else 0), oy):
                continue
            c = hm
            if y >= fringe - 1 or x < 9 or x > 24:
                c = hs
            cv.put(x, y, c)
    for x, w in ((5, 3), (24, 3)):
        cv.rect(x, cy - 3, w, 6, hm)
        cv.vline(x if x < 16 else x + w - 1, cy - 3, 6, hs)
    for x in range(7, 20):
        y = cy - 9 + abs(x - 12) // 3
        cv.put(x, y, hl)
        cv.put(x, y + 1, hl if x < 17 else hm)
        if 9 <= x <= 14:
            cv.put(x, y + 2, hl)
    cv.put(10, cy - 9, hh)
    cv.put(11, cy - 9, hh)
    cv.put(13, cy - 10, hh)
    for x, h_ in ((12, 3), (16, 2), (20, 2)):        # mechones que se salen de la silueta
        if style in ("parado", "flequillo"):
            cv.vline(x, cy - 10 - h_, h_ + 1, hm)
            cv.put(x + 1, cy - 10 - h_ + 1, hs)
            cv.put(x, cy - 10 - h_, hl)
    if style == "parado":
        for x in range(7, 26, 3):
            cv.rect(x, cy - 13 - (x % 2), 2, 3, hm)
            cv.put(x, cy - 13 - (x % 2), hl)
    if style == "rulos":
        for x in range(5, 28, 3):
            for yy in (cy - 10, cy - 6):
                if in_head(x, yy + 2, oy) or yy == cy - 10:
                    cv.ellipse(x, yy + abs(x - 16) // 4, 2, 2, hm)
                    cv.put(x - 1, yy - 1 + abs(x - 16) // 4, hl)
    if style == "rodete":
        cv.ellipse(16, cy - 12, 4, 3, hm)
        cv.hline(14, cy - 14, 3, hl)
        cv.hline(13, cy - 10, 7, hs)
    if style == "largo":
        for x in (4, 5, 6, 26, 27):
            cv.vline(x, cy - 2, 14, hm if x not in (4, 27) else hs)
        cv.rect(7, cy + 6, 2, 5, hm)
        cv.rect(24, cy + 6, 2, 5, hm)
    if style == "boina":
        cv.ellipse(15, cy - 9, 12, 4, "i_noche1")
        cv.hline(4, cy - 7, 24, "i_noche0")
        cv.hline(7, cy - 11, 12, "i_noche2")
        cv.hline(8, cy - 12, 8, "i_noche3")
        cv.hline(9, cy - 10, 6, "i_noche2")
        cv.vline(15, cy - 15, 3, "i_noche0")
    return style == "gorra"


def cap(cv, color, oy):
    s, m, l, h = ramp(color)
    cy = HEAD_CY + oy
    cv.ellipse(16, cy - 8, 11, 6, m)
    cv.rect(6, cy - 3, 21, 2, s)
    cv.rect(18, cy - 3, 12, 2, s)
    cv.hline(18, cy - 3, 12, m)
    for x in range(8, 18):
        cv.put(x, cy - 11 + abs(x - 12) // 3, l)
    cv.put(10, cy - 12, h)
    for x in range(8, 16):
        cv.put(x, cy - 10 + abs(x - 11) // 3, l)
    cv.hline(19, cy - 3, 10, h)                     # brillo de la visera
    cv.rect(15, cy - 9, 3, 3, "i_amarillo1")       # sol de 3x3
    cv.put(16, cy - 8, "i_amarillo3")
    cv.put(16, cy - 10, "i_amarillo1")
    cv.put(16, cy - 6, "i_amarillo1")
    cv.put(14, cy - 8, "i_amarillo1")
    cv.put(18, cy - 8, "i_amarillo1")


def face(cv, mood, f, oy, extra, blink_ok=False):
    cy = HEAD_CY + oy
    eyes = (11, 19)
    ey = cy + 1
    if mood in ("happy", "celebrate"):
        thick = mood == "celebrate"
        for x in eyes:
            if thick:
                for i in range(3):
                    cv.put(x + i, ey - 1 + abs(1 - i), "iEye")
                    cv.put(x + i, ey + abs(1 - i), "iEye")
            else:
                cv.put(x, ey + 1, "iEye")
                cv.put(x + 1, ey, "iEye")
                cv.put(x + 2, ey + 1, "iEye")
                cv.put(x + 1, ey - 1, "iEye")
        w, h = (8, 6) if thick else (7, 5)
        mx = 16 - w // 2
        my = cy + 5
        cv.rect(mx, my, w, h, "iEye")
        cv.rect(mx + 1, my + 1, w - 2, h - 1, "iMo")
        cv.hline(mx + 1, my, w - 2, "iWh")
        cv.rect(mx + 2, my + h - 2, w - 4, 2, "iTo")
    elif mood == "sad":
        for x in eyes:
            cv.rect(x, ey, 2, 2, "iEye")
            cv.put(x, ey, "iWh")
        for (x1, y1), (x2, y2) in (((10, ey - 4), (12, ey - 2)), ((22, ey - 4), (20, ey - 2))):
            cv.put(x1, y1 + 1, "iO")
            cv.put((x1 + x2) // 2, y1 + 1 + (1 if x1 < 16 else 0), "iO")
            cv.put(x2, y2, "iO")
        cv.hline(14, cy + 7, 4, "iEye")
        cv.put(13, cy + 8, "iEye")
        cv.put(18, cy + 8, "iEye")
        cv.rect(25, cy - 7, 3, 4, "iSw")          # gotita con contorno y brillo
        cv.put(26, cy - 8, "iSw")
        for xx, yy in ((24, cy - 6), (28, cy - 6), (24, cy - 4), (28, cy - 4), (25, cy - 3), (27, cy - 3), (26, cy - 2), (25, cy - 8), (27, cy - 8), (26, cy - 9)):
            cv.put(xx, yy, "iWat")
        cv.put(25, cy - 6, "iWh")
    else:
        blink = blink_ok and f == 1
        for x in eyes:
            if blink:
                cv.hline(x, ey + 1, 2, "iEye")
            else:
                cv.rect(x, ey - 2, 2, 4, "iEye")
                cv.put(x, ey - 2, "iWh")
                cv.put(x, ey + 1, "i_marron1")
                cv.put(x + 1, ey + 1, "i_marron1")
            cv.hline(x - (1 if x == eyes[0] else 0), ey - 4, 3, "iO")
        if mood == "work":
            cv.rect(14, cy + 6, 4, 3, "iEye")
            cv.rect(15, cy + 7, 2, 2, "iMo")
        else:
            cv.hline(14, cy + 6, 5, "iEye")         # sonrisa ancha con comisuras
            cv.put(13, cy + 5, "iEye")
            cv.put(19, cy + 5, "iEye")
            cv.hline(15, cy + 7, 3, "iK3")
    cv.put(16, cy + 3, "iK2")
    cv.hline(8, cy + 4, 2, "iBl")
    cv.hline(22, cy + 4, 2, "iBl")
    if extra == "bigote":
        cv.rect(12, cy + 4, 8, 2, "i_pelo_canoso1")
        cv.hline(12, cy + 5, 8, "i_pelo_canoso0")


def outline_pass(cv):
    cv.outline("iO")
    o = rgba("iO")
    for y in range(cv.h):
        for x in range(cv.w):
            if cv.get(x, y) != o:
                continue
            right, below = cv.get(x + 1, y), cv.get(x, y + 1)
            light_side = (below[3] and below != o and y < 30) or (right[3] and right != o and x < 16)
            if light_side and x + y < 46:
                cv.put(x, y, "iS")


# ------------------------------------------------------------------- poses

CLIENT_PROPS = ["bolsa", "celular", "termo", "changuito", "bolsa"]


def work_prop(cv, job, f, oy):
    y = 28 + oy
    if job == "bolsa":                              # bolsa de compras que se balancea
        bx = 22 + f
        cv.rect(bx, y + 2, 7, 7, "iC")
        cv.vline(bx, y + 2, 7, "iWh")
        cv.vline(bx + 6, y + 2, 7, "iCs")
        cv.hline(bx + 2, y, 3, "i_marron1")
        cv.put(bx + 2, y + 1, "i_marron1")
        cv.put(bx + 4, y + 1, "i_marron1")
        cv.rect(bx + 2, y + 4, 3, 3, "i_verde2")      # verdura asomando
        return
    if job == "celular":                            # mira el celular (pantalla que titila)
        cv.rect(23, y - 1, 5, 8, "i_noche0")
        cv.rect(24, y, 3, 5, "i_celeste2" if f else "i_celeste1")
        cv.put(24, y, "iWh")
        return
    if job == "termo":                              # termo + mate
        cv.rect(23, y - 2, 4, 10, "i_rojo1")
        cv.vline(23, y - 2, 10, "i_rojo2")
        cv.rect(23, y - 4, 4, 2, "i_gris2")
        if f:
            cv.put(28, y - 5, "iWh")
        return
    if job == "changuito":                          # empuja un changuito
        cv.rect(22, y + 3, 9, 6, "i_gris1")
        for xx in range(23, 31, 2):
            cv.vline(xx, y + 3, 6, "i_gris2")
        cv.ellipse(23, y + 11, 1, 1, "iEye")
        cv.ellipse(29, y + 11, 1, 1, "iEye")
        cv.put(24 + f, y + 2, "i_rojo1")
        cv.put(27, y + 2, "i_amarillo1")
        return
    if job == "mate":                               # mate de calabaza con bombilla, se ceba
        cv.ellipse(25, y + 5 - f, 3, 4, "i_marron1")
        cv.ellipse(24, y + 4 - f, 2, 2, "i_marron2")
        cv.hline(23, y + 1 - f, 5, "i_verde2")
        cv.vline(26, y - 4 - f, 5, "i_gris2")
        cv.put(26, y - 4 - f, "iWh")
        if f:
            for k in range(3):
                cv.put(28 + k % 2, y - 6 - k * 2, "iWh")
    elif job == "cajon":                            # levanta un cajón de fruta
        bx, by = 19, y - 1 - f * 3
        cv.rect(bx, by, 11, 8, "i_marron2")
        cv.hline(bx, by, 11, "i_marron3")
        cv.hline(bx, by + 4, 11, "i_marron1")
        for i in range(4):
            cv.ellipse(bx + 1 + i * 3, by - 1, 1, 1, ("i_rojo1", "i_amarillo1", "i_verde2", "i_naranja1")[i])
    elif job == "cortar":                           # cuchillo grande sobre tabla
        cv.rect(20, y + 7, 10, 3, "i_marron2")
        cv.hline(20, y + 7, 10, "i_marron3")
        kx, ky = 24, y - 2 + f * 4
        cv.rect(kx, ky, 2, 7, "i_gris2")
        cv.vline(kx, ky, 7, "iWh")
        cv.rect(kx, ky + 7, 2, 3, "i_marron0")
        if f:
            cv.put(28, y + 5, "i_verde2")
            cv.put(29, y + 6, "i_rojo1")
    else:                                           # cobra: billete y moneda que salta
        cv.rect(22, y + 2, 7, 4, "i_verde2")
        cv.rect(23, y + 3, 5, 2, "i_verde1")
        cx, cy2 = 26, y - 3 - f * 3
        cv.ellipse(cx, cy2, 2, 2, "i_amarillo1")
        cv.put(cx - 1, cy2 - 1, "i_amarillo3")
        if f:
            star(cv, 29, cy2 - 2)


def star(cv, x, y):
    """Destello de 3x3 en cruz con centro brillante."""
    for dx, dy in ((0, -2), (0, -1), (-2, 0), (-1, 0), (1, 0), (2, 0), (0, 1), (0, 2)):
        cv.put(x + dx, y + dy, "i_amarillo1")
    cv.put(x, y, "iGh")


def person(spec, pose, f):
    hair_r, style, cloth, pants, width, extra, skin_i, job = spec[:8]
    body = spec[8] if len(spec) > 8 else ""
    skin = SKINS[skin_i]
    cv = Canvas(FW, FH)
    oy = {"idle": (0, 1)[min(f, 1)], "celebrate": (-4, -2)[min(f, 1)], "walk": (0, -1, 0, -1)[f]}.get(pose, 0)
    mood = {"walk": "idle", "idle": "idle", "work": "work", "celebrate": "celebrate", "happy": "happy", "sad": "sad"}[pose]
    x0 = 16 - width // 2
    if pose == "celebrate":
        arm(cv, x0 - 3, 26 + oy, -2, -20 if f == 0 else -17, cloth, skin, True)
    elif pose == "walk":
        arm(cv, x0 - 3, 28 + oy, (2, 0, -3, 0)[f] - 1, 7, cloth, skin)
    else:
        arm(cv, x0 - 3, 28 + oy, -1, 7, cloth, skin)
    legs(cv, pose, f, pants, oy if pose == "celebrate" else 0)
    torso(cv, cloth, extra, width, oy)
    if body == "pollera":
        ps, pm, pl, _ = ramp(pants)
        for k in range(6):
            cv.hline(16 - width // 2 - k // 2, 38 + oy + k, width + k, pm)
            cv.put(16 - width // 2 - k // 2, 38 + oy + k, pl)
            cv.put(16 + width // 2 + k // 2 - 1, 38 + oy + k, ps)
    if body == "panza":
        cs, cm, cl, _ = ramp(cloth)
        cv.ellipse(17, 34 + oy, width // 2 + 1, 4, cm)
        cv.hline(13, 37 + oy, 9, cs)
        cv.put(12, 32 + oy, cl)
    head(cv, skin, oy)
    capped = hair(cv, hair_r, style, oy)
    face(cv, mood, f, oy, extra, pose == "idle")
    if capped:
        cap(cv, cloth if extra in ("delantal", "panuelo") else "rojo", oy)
    xr = x0 + width - 1
    if pose == "celebrate":
        arm(cv, xr + 1, 26 + oy, 2, -20 if f == 0 else -17, cloth, skin, True)
        for sx, sy in (((1, 14), (29, 18)) if f == 0 else ((2, 20), (28, 12))):
            star(cv, sx, sy)
    elif pose == "work":
        if job == "cajon":
            arm(cv, xr - 1, 29 + oy, 2, 2, cloth, skin)
        else:
            arm(cv, xr, 28 + oy, 4, 2 if job != "cortar" else 1, cloth, skin)
        work_prop(cv, job or CLIENT_PROPS[(sum(map(ord, hair_r + style)) + width) % len(CLIENT_PROPS)], f, oy)
    elif pose == "happy":
        arm(cv, xr, 27 + oy, 3, -6, cloth, skin, True)
    elif pose == "walk":
        arm(cv, xr + 1, 28 + oy, (-3, 0, 2, 0)[f] + 1, 7, cloth, skin)
    else:
        arm(cv, xr + 1, 28 + oy, 1, 7, cloth, skin)
    if extra == "mate" and pose in ("idle", "walk", "happy"):
        cv.rect(xr + 1, 35 + oy, 4, 5, "i_marron1")
        cv.hline(xr + 1, 35 + oy, 4, "i_verde2")
        cv.vline(xr + 3, 31 + oy, 4, "i_gris2")
    outline_pass(cv)
    shadow(cv, oy if pose == "celebrate" else 0)
    return cv


POSES = [("walk", 0), ("walk", 1), ("walk", 2), ("walk", 3), ("idle", 0), ("idle", 1),
         ("work", 0), ("work", 1), ("celebrate", 0), ("celebrate", 1), ("happy", 0), ("sad", 0)]


def make_sheet(spec):
    return sheet([person(spec, p, f) for p, f in POSES])


def generate(out_root):
    d = os.path.join(out_root, "personajes")
    os.makedirs(d, exist_ok=True)
    for i, spec in enumerate(CUSTOMERS):
        make_sheet(spec).save(os.path.join(d, "customer_%d.png" % i))
    for i, spec in enumerate(WORKERS):
        make_sheet(spec).save(os.path.join(d, "worker_%d.png" % i))


if __name__ == "__main__":
    generate(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets"))
