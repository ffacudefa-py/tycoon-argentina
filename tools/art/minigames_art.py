"""Arte de los minijuegos 11.2 (asalto y coima), con la paleta 11.

Salida en assets/pixel_art/minigames/:
  thief_<n>.png / thief_casco_<n>.png  hoja de 8 cuadros de 48x48:
      0-3 correr · 4 agarrar · 5 golpeado · 6-7 en el piso (con estrellitas)
  cop.png        hoja de 4 cuadros de 32x48: 0-1 quieto · 2 mano estirada · 3 enojado
  crate.png      caja de mercadería 22x18 (el ícono del producto va encima)
  bag.png        bolsa de arpillera, 2 cuadros de 72x64 (vacía, llena)
  revolver.png   revólver, 2 cuadros de 56x36 (normal, retroceso)
  flash.png      fogonazo, 3 cuadros de 24x24
  hole.png       agujero de bala 8x8
  bullet.png     bala del tambor: llena y vacía (6x12 c/u)
  patrol.png     patrullero, 2 cuadros de 128x60 (balizas alternadas)
  doc_white.png / doc_red.png  documento 96x120
  stamp.png      sello rojo 40x24 · label.png etiqueta blanca 44x14
  shredder.png   trituradora 64x60 · folder.png carpeta del policía 64x52
  siren.png      resplandor radial 64x64 (blanco, se tiñe en el juego)

Uso: python tools/art/minigames_art.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402
from px2 import PAL, Canvas, sheet  # noqa: E402
import palette11  # noqa: F401,E402
from palette11 import ramp  # noqa: E402
import chars3  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "pixel_art", "minigames")
O = "iO"   # contorno
PAL.update({"i_bag0": "#8A6A3C", "i_bag1": "#B89058", "i_bag2": "#D8B47A", "i_bag3": "#F0D8A8"})


def balaclava(cv, color, oy):
    """Pasamontañas tejido sobre la cabeza, con la ranura de los ojos."""
    s, m, l, h = ramp(color)
    cy = chars3.HEAD_CY + oy
    for x in range(4, 29):
        for y in range(cy - 12, cy + 12):
            if not chars3.in_head(x, y, oy):
                continue
            if cy - 1 <= y <= cy + 4 and 8 <= x <= 23:
                continue            # ranura de los ojos
            c = m
            if x < 11 and y < cy - 3:
                c = l
            elif x > 21 or y > cy + 7:
                c = s
            if (x + y) % 4 == 0 and c == m:
                c = s               # punto tejido
            cv.put(x, y, c)
    cv.hline(8, cy - 2, 16, s)
    cv.hline(8, cy + 5, 16, s)
    cv.ellipse(16, cy - 12, 2, 2, l)  # pompón
    cv.put(15, cy - 13, h)


def helmet(cv, oy):
    """Casco de moto rojo con visera oscura (aguanta un tiro)."""
    s, m, l, h = ramp("rojo")
    cy = chars3.HEAD_CY + oy
    for x in range(4, 29):
        for y in range(cy - 12, cy + 2):
            if chars3.in_head(x, y + 1, oy) or chars3.in_head(x, y, oy):
                c = m
                if x < 12 and y < cy - 5:
                    c = l
                elif x > 22:
                    c = s
                cv.put(x, y, c)
    cv.hline(6, cy + 1, 21, s)
    for x in range(9, 24):
        cv.put(x, cy - 1, "i_noche0")
        cv.put(x, cy, "i_noche1")
    cv.put(10, cy - 1, "i_celeste3")
    cv.put(9, cy - 9, h)
    cv.put(10, cy - 10, h)


THIEVES = [
    # pelo, peinado, ropa, pantalón, ancho, extra, piel, oficio, cuerpo, color del pasamontañas
    ("pelo_negro", "pelado", "noche", "gris", 13, "", 0, "", "", "noche"),
    ("pelo_castano", "pelado", "verde", "noche", 12, "", 2, "", "", "rojo"),
    ("pelo_negro", "pelado", "gris", "azul", 14, "", 1, "", "panza", "verde"),
]


def thief_frame(spec, pose, f, casco):
    cv = chars3.person(spec[:9], pose, f)
    oy = (0, -1, 0, -1)[f] if pose == "walk" else 0
    if casco:
        helmet(cv, oy)
    else:
        balaclava(cv, spec[9], oy)
    chars3.outline_pass(cv)
    return cv


def to48(cv, dx=8, dy=0):
    big = Canvas(48, 48)
    big.paste(cv, dx, dy)
    return big


def down_frame(spec, casco, phase):
    lying = thief_frame(spec, "sad", 0, casco)
    img = lying.img.rotate(90, expand=True)          # acostado, cabeza a la izquierda
    cv = Canvas(48, 48)
    cv.img.alpha_composite(img, (0, 18))
    cv.px = cv.img.load()
    for i in range(3):
        a = phase + i * 2.1
        chars3.star(cv, 24 + int(10 * math.cos(a)), 18 + int(3 * math.sin(a)))
    return cv


def hit_frame(spec, casco):
    cv = thief_frame(spec, "sad", 0, casco)
    for x in range(cv.w):
        for y in range(cv.h):
            r, g, b, a = cv.get(x, y)
            if a and (r + g + b) < 200:
                cv.put(x, y, "iC")      # contorno blanco: destello de impacto
    return to48(cv, 10)


def thief_sheet(spec, casco):
    frames = [to48(thief_frame(spec, "walk", f, casco)) for f in range(4)]
    frames.append(to48(thief_frame(spec, "work", 0, casco)))
    frames.append(hit_frame(spec, casco))
    frames.append(down_frame(spec, casco, 0.0))
    frames.append(down_frame(spec, casco, 1.0))
    return sheet(frames)


def cop_sheet():
    spec = ("pelo_negro", "gorra", "azul", "noche", 14, "bigote", 2, "", "panza")
    frames = []
    for pose, f in (("idle", 0), ("idle", 1), ("happy", 0), ("sad", 0)):
        cv = chars3.person(spec, pose, f)
        oy = (0, 1)[min(f, 1)] if pose == "idle" else 0
        chars3.cap(cv, "azul", oy)
        cv.rect(19, 30 + oy, 3, 3, "i_amarillo1")    # chapa
        cv.put(20, 31 + oy, "i_amarillo3")
        chars3.outline_pass(cv)
        frames.append(cv)
    return sheet(frames)


def crate():
    cv = Canvas(22, 18)
    s, m, l, h = ramp("marron")
    cv.rect(1, 3, 20, 14, m)
    cv.hline(1, 3, 20, l)
    cv.hline(1, 9, 20, s)
    cv.hline(1, 16, 20, s)
    cv.vline(1, 3, 14, s)
    cv.vline(20, 3, 14, s)
    cv.vline(2, 4, 12, l)
    cv.rect(3, 1, 16, 3, "i_blanco1")             # papel de embalaje
    cv.hline(3, 1, 16, "iC")
    cv.outline(O)
    return cv


def bag(full):
    cv = Canvas(72, 64)
    rx, ry = (31, 21) if full else (27, 17)
    cy = 41 if full else 45
    cv.ellipse(36, cy, rx, ry, "i_bag1")
    for x in range(36 - rx, 36 + rx + 1):
        for y in range(cy - ry, cy + ry + 1):
            dx, dy = (x - 36) / rx, (y - cy) / ry
            d = dx * dx + dy * dy
            if d <= 1 and (dy > 0.25 and d > 0.5 or dx > 0.6):
                cv.put(x, y, "i_bag0")
    cv.ellipse(28, cy - 7, rx // 3, ry // 3, "i_bag2")
    cv.ellipse(25, cy - 10, 4, 3, "i_bag3")
    top = cy - ry
    cv.rect(28, top - 10, 16, 12, "i_bag1")        # cuello
    cv.vline(41, top - 10, 12, "i_bag0")
    cv.rect(26, top - 13, 20, 5, "i_bag2")         # boca abierta
    cv.hline(28, top - 12, 16, "i_marron0")
    cv.hline(27, top - 3, 18, "i_marron0")         # soga
    cv.hline(27, top - 2, 18, "i_amarillo1")
    for x in range(30, 44, 3):                     # trama de arpillera
        for y in range(cy - ry + 4, cy + ry - 2, 3):
            if cv.get(x, y)[3] and cv.get(x, y)[:3] != (0, 0, 0):
                cv.put(x, y, "i_bag0")
    cv.rect(31, cy - 4, 11, 9, "i_amarillo1")      # $ estampado
    cv.rect(32, cy - 3, 9, 7, "i_amarillo2")
    cv.vline(36, cy - 5, 11, "i_marron0")
    cv.hline(33, cy - 2, 6, "i_marron0")
    cv.hline(34, cy + 2, 6, "i_marron0")
    cv.outline(O)
    return cv


def revolver(recoil):
    cv = Canvas(56, 36)
    oy = -3 if recoil else 0
    ox = 3 if recoil else 0
    g = ramp("gris")
    cv.rect(18 + ox, 8 + oy, 34, 6, g[1])          # caño
    cv.hline(18 + ox, 8 + oy, 34, g[3])
    cv.hline(18 + ox, 13 + oy, 34, g[0])
    cv.rect(48 + ox, 6 + oy, 3, 2, g[2])           # mira
    cv.rect(12 + ox, 6 + oy, 14, 14, g[1])         # tambor
    cv.ellipse(19 + ox, 13 + oy, 6, 6, g[2])
    for a in range(6):
        x = 19 + ox + int(round(3.5 * math.cos(a * math.pi / 3)))
        y = 13 + oy + int(round(3.5 * math.sin(a * math.pi / 3)))
        cv.put(x, y, g[0])
    m = ramp("marron")
    for y in range(18, 34):                        # culata de madera
        w = 10 - (y - 18) // 4
        cv.hline(6 + ox - (y - 18) // 3, y + oy, w, m[1])
        cv.put(6 + ox - (y - 18) // 3, y + oy, m[2])
    cv.rect(16 + ox, 20 + oy, 8, 2, g[0])          # gatillo
    cv.vline(22 + ox, 20 + oy, 5, g[0])
    cv.outline(O)
    return cv


def flash(f):
    cv = Canvas(24, 24)
    r = (10, 8, 5)[f]
    for a in range(8):
        ang = a * math.pi / 4 + f * 0.3
        for k in range(r + (3 if a % 2 == 0 else 0)):
            x = 12 + int(round(k * math.cos(ang)))
            y = 12 + int(round(k * math.sin(ang)))
            cv.put(x, y, "i_amarillo2" if k < r // 2 else "i_naranja1")
    cv.ellipse(12, 12, max(2, r // 2), max(2, r // 2), "i_amarillo3")
    cv.ellipse(12, 12, max(1, r // 4), max(1, r // 4), "iWh")
    return cv


def hole():
    cv = Canvas(8, 8)
    cv.ellipse(4, 4, 3, 3, "i_noche1")
    cv.ellipse(4, 4, 2, 2, "i_noche0")
    cv.put(2, 2, "i_gris3")
    cv.put(6, 6, "i_gris1")
    return cv


def bullet():
    cv = Canvas(12, 12)
    for i, full in enumerate((True, False)):
        x = i * 6
        if full:
            cv.rect(x + 1, 4, 4, 7, "i_amarillo1")
            cv.vline(x + 1, 4, 7, "i_amarillo2")
            cv.rect(x + 1, 1, 4, 3, "i_naranja1")
            cv.put(x + 2, 1, "i_naranja2")
        else:
            cv.rect(x + 1, 4, 4, 7, "i_noche1")
            cv.vline(x + 1, 4, 7, "i_noche2")
    return cv


def patrol(f):
    cv = Canvas(128, 60)
    w = ramp("blanco")
    b = ramp("azul")
    cv.rect(6, 26, 116, 20, w[1])                  # carrocería
    cv.hline(6, 26, 116, w[2])
    cv.rect(6, 34, 116, 5, b[1])                   # franja azul
    cv.hline(6, 34, 116, b[2])
    for x in range(30, 98):                        # cabina con parabrisas inclinados
        top = 10 + max(0, 40 - x) if x < 40 else (10 if x < 88 else 10 + (x - 88))
        cv.vline(x, top, 26 - top, w[1])
    cv.rect(42, 13, 20, 11, "i_celeste2")          # ventanas
    cv.rect(66, 13, 20, 11, "i_celeste2")
    cv.hline(42, 13, 20, "i_celeste3")
    cv.hline(66, 13, 20, "i_celeste3")
    cv.rect(12, 30, 10, 3, "i_amarillo2")          # faros
    cv.rect(112, 30, 8, 3, "i_rojo1")
    for cx in (30, 98):                            # ruedas
        cv.ellipse(cx, 47, 9, 9, "i_noche0")
        cv.ellipse(cx, 47, 4, 4, "i_gris2")
        cv.put(cx - 1, 45, "i_gris3")
    cv.rect(52, 5, 10, 5, "i_rojo2" if f == 0 else "i_rojo0")     # balizas
    cv.rect(64, 5, 10, 5, "i_azul2" if f == 1 else "i_azul0")
    if f == 0:
        cv.rect(53, 6, 3, 2, "i_rojo3")
    else:
        cv.rect(65, 6, 3, 2, "i_azul3")
    cv.rect(50, 9, 26, 2, w[0])
    cv.outline(O)
    return cv


def document(red):
    cv = Canvas(96, 120)
    if red:
        s, m, l = "i_rojo0", "i_rojo1", "i_rojo2"
        line, title, ink = "i_rojo0", "i_rojo0", "i_noche0"
    else:
        s, m, l = "i_blanco0", "i_blanco1", "i_blanco2"
        line, title, ink = "i_gris1", "i_gris0", "i_noche1"
    cv.rect(2, 2, 92, 116, m)
    cv.rect(2, 2, 92, 3, l)
    cv.vline(2, 2, 116, l)
    cv.hline(2, 117, 92, s)
    cv.vline(93, 2, 116, s)
    for k in range(10):                            # esquina doblada
        cv.hline(84 + k, 2 + k, 10 - k, s)
    cv.rect(10, 12, 56, 6, title)                  # título
    for y in range(28, 100, 8):
        cv.hline(10, y, 76 - (y * 7) % 23, line)
    cv.hline(54, 108, 30, line)                    # firma
    for x in range(56, 82, 2):
        cv.put(x, 105 + (x % 3), ink)
    cv.outline(O)
    return cv


def stamp():
    cv = Canvas(40, 24)
    cv.frame(1, 1, 38, 22, "i_rojo1")
    cv.frame(3, 3, 34, 18, "i_rojo1")
    for x in range(7, 33, 3):                       # letras sugeridas
        cv.vline(x, 8, 8, "i_rojo1")
        cv.put(x + 1, 8, "i_rojo1")
    return cv


def label():
    cv = Canvas(44, 14)
    cv.rect(1, 1, 42, 12, "i_blanco2")
    cv.hline(1, 1, 42, "iWh")
    for x in range(5, 39, 4):
        cv.hline(x, 6, 2, "i_gris1")
    cv.outline(O)
    return cv


def shredder():
    cv = Canvas(64, 60)
    g = ramp("gris")
    cv.rect(4, 14, 56, 40, g[1])
    cv.hline(4, 14, 56, g[3])
    cv.vline(4, 14, 40, g[2])
    cv.rect(10, 6, 44, 10, g[0])                   # boca
    cv.rect(14, 9, 36, 3, "i_noche0")
    for x in range(14, 50, 4):
        cv.vline(x, 12, 3, g[2])
    cv.rect(12, 24, 40, 24, "i_rojo1")             # tacho rojo (desechar)
    cv.hline(12, 24, 40, "i_rojo2")
    for x in range(16, 50, 5):                     # tiritas de papel
        cv.vline(x, 26, 6 + x % 7, "i_blanco1")
    cv.rect(26, 38, 12, 4, "iWh")                  # flecha ←
    for dx, dy in ((-2, 1), (-1, 0), (-1, 3), (-1, 1), (-1, 2)):
        cv.put(26 + dx, 38 + dy, "iWh")
    cv.outline(O)
    return cv


def folder():
    cv = Canvas(64, 52)
    a = ramp("amarillo")
    cv.rect(4, 8, 24, 6, a[1])                     # pestaña
    cv.rect(4, 12, 56, 36, a[1])
    cv.hline(4, 12, 56, a[2])
    cv.vline(4, 12, 36, a[2])
    cv.hline(4, 47, 56, a[0])
    cv.rect(8, 4, 48, 10, "i_blanco2")             # papeles asomando
    cv.hline(8, 4, 48, "iWh")
    cv.rect(18, 24, 28, 14, "i_azul1")             # escudo azul (policía)
    cv.rect(20, 26, 24, 10, "i_azul2")
    cv.rect(26, 30, 10, 3, "iWh")                  # flecha →
    for dx, dy in ((10, -1), (10, 3), (11, 0), (11, 2), (12, 1), (10, 0), (10, 1), (10, 2), (11, 1)):
        cv.put(26 + dx, 30 + dy, "iWh")
    cv.outline(O)
    return cv


def siren_glow():
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    px = img.load()
    for x in range(64):
        for y in range(64):
            d = math.hypot(x - 31.5, y - 31.5) / 32.0
            if d < 1.0:
                a = (int(255 * (1.0 - d) ** 2) // 48) * 48   # escalones (look pixel)
                px[x, y] = (255, 255, 255, a)
    return img


def save(obj, name):
    (obj if isinstance(obj, Image.Image) else obj.img).save(os.path.join(OUT, name))


def main():
    os.makedirs(OUT, exist_ok=True)
    for i, spec in enumerate(THIEVES):
        save(thief_sheet(spec, False), "thief_%d.png" % i)
        save(thief_sheet(spec, True), "thief_casco_%d.png" % i)
    save(cop_sheet(), "cop.png")
    save(crate(), "crate.png")
    save(sheet([bag(False), bag(True)]), "bag.png")
    save(sheet([revolver(False), revolver(True)]), "revolver.png")
    save(sheet([flash(0), flash(1), flash(2)]), "flash.png")
    save(hole(), "hole.png")
    save(bullet(), "bullet.png")
    save(sheet([patrol(0), patrol(1)]), "patrol.png")
    save(document(False), "doc_white.png")
    save(document(True), "doc_red.png")
    save(stamp(), "stamp.png")
    save(label(), "label.png")
    save(shredder(), "shredder.png")
    save(folder(), "folder.png")
    save(siren_glow(), "siren.png")
    print("arte de minijuegos en", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
