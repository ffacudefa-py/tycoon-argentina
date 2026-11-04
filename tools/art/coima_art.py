"""12.2: el escritorio de la coima, con más detalle y volumen.

Reemplaza (mismos nombres de archivo en assets/pixel_art/minigames/):
  desk.png      madera del escritorio 256x192: tablas largas con cabezas
                escalonadas, veta, nudos y canto; cubre todo el ancho del
                teléfono sin repetirse en x (antes 64x48, se veían las costuras)
  blotter.png   carpeta de cuero verde 116x140 con esquineros de cuero cosidos
                (antes triángulos planos que "cortaban" las esquinas)
  lamp.png      lámpara de banquero 36x36: base de bronce, pantalla de vidrio
                verde con brillo, cadenita y luz cálida debajo
  mug.png       taza de café 16x17 con café, asa y reflejo
  phone.png     teléfono de escritorio 36x24 con tubo, cable en espiral y teclado
  stamp_pad.png sello de goma y almohadilla abierta 30x20
Cada objeto trae su sombra de contacto (semitransparente) para que apoye en la
madera en vez de "flotar". Uso: python tools/art/coima_art.py (después de minigames_art2.py)
"""
import math
import os
import random

from PIL import Image

from minigames_art2 import Cv, shade_poly, OUT, OUTL, BRASS
import props_art as P

WOOD = ["#4A2717", "#5A301C", "#6A3A22", "#784328", "#864D2E", "#945836", "#A3643E"]


def shadow(cv, cx, cy, rx, ry, a=90):
    """Sombra de contacto tramada (alfa) bajo un objeto."""
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if d <= 1 and not cv.opaque(x, y):
                k = a if d < 0.55 else a * 0.55
                if d >= 0.55 and (x + y) % 2:
                    continue
                cv.px[x, y] = (30, 12, 6, int(k))


def desk():
    w, h = 256, 384
    cv = Cv(w, h)
    rnd = random.Random(31)
    rows = 16                                 # 16 tablas de 24 px (cubre la pantalla sin repetirse)
    for r in range(rows):
        y0 = r * 24
        off = rnd.randint(0, 200)
        ln = rnd.choice([150, 170, 190])
        for x in range(w):
            seg = (x + off) // ln
            tone = 2 + (seg * 7 + r * 3) % 3
            for yy in range(y0, y0 + 24):
                cv.put(x, yy, WOOD[tone])
        # veta: trazos largos ondulados
        for k in range(16):
            yy = y0 + 3 + rnd.randint(0, 18)
            x0 = rnd.randint(0, w - 1)
            L = rnd.randint(30, 110)
            ph = rnd.random() * 6
            for i in range(L):
                x = (x0 + i) % w
                y = yy + int(round(math.sin(i / 17.0 + ph) * 1.2))
                base = cv.get(x, y)
                if base[3]:
                    idx = WOOD.index("#%02X%02X%02X" % base[:3]) if "#%02X%02X%02X" % base[:3] in WOOD else 3
                    cv.put(x, y, WOOD[max(0, idx - 1)] if k % 3 else WOOD[min(6, idx + 1)])
        for k in range(2):                                            # nudos
            kx, ky = rnd.randint(10, w - 10), y0 + rnd.randint(7, 17)
            cv.ell(kx, ky, 3, 1.6, WOOD[1])
            cv.ell(kx, ky, 1.5, 0.8, WOOD[0])
            cv.put(kx - 2, ky - 2, WOOD[5])
        cv.rect(0, y0, w, 1, WOOD[0])                                 # junta entre tablas
        cv.rect(0, y0 + 1, w, 1, WOOD[5])
        for x in range(w):                                            # cabezas de tabla
            if (x + off) % ln == 0:
                cv.rect(x, y0 + 1, 1, 23, WOOD[0])
                cv.rect(x + 1, y0 + 1, 1, 23, WOOD[5])
    return cv


def blotter():
    """Carpeta de escritorio de paño verde con ribete de cuero en todo el borde,
    esquinas redondeadas y pespunte (12.2: sin esquineros triangulares)."""
    w, h = 116, 140
    cv = Cv(w, h)
    g = ["#173A26", "#1E4A30", "#265A3A", "#2E6A44", "#3A7E52", "#4E9466"]
    L = ["#3E1E10", "#5A2E1A", "#6D3A20", "#84482A", "#9A5A36", "#C88555"]
    rnd = random.Random(2)
    for y in range(h):
        for x in range(w):
            cx = min(x, w - 1 - x)
            cy = min(y, h - 1 - y)
            if cx < 3 and cy < 3 and (3 - cx) ** 2 + (3 - cy) ** 2 > 10:
                continue                                              # esquina redondeada
            edge = cx < 5 or cy < 5
            if edge:
                t = 4 if (x < 5 or y < 5) else 2
                if cx == 0 or cy == 0:
                    t = 1
                cv.put(x, y, L[t])
            else:
                cv.put(x, y, g[3] if (x + y * 0.6) > 50 else g[4])
    for i in range(700):
        cv.put(rnd.randint(6, w - 7), rnd.randint(6, h - 7), g[2] if i % 3 else g[4])
    for x in range(8, w - 8, 3):                                      # pespunte del ribete
        cv.put(x, 2, L[5])
        cv.put(x, h - 3, L[3])
    for y in range(8, h - 8, 3):
        cv.put(2, y, L[5])
        cv.put(w - 3, y, L[3])
    for x in range(5, w - 5):                                         # sombra del ribete sobre el paño
        cv.put(x, 5, g[1])
    for y in range(5, h - 5):
        cv.put(5, y, g[1])
    cv.outline(OUTL, "#8E461F")
    return cv


def _vol_shadow(img, cx, cy, rx, ry, a=70):
    """Sombra de contacto sólida (sin damero), misma dirección para todos: abajo-derecha."""
    px = img.load()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if not (0 <= x < img.width and 0 <= y < img.height):
                continue
            d = ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2
            if d <= 1 and px[x, y][3] == 0:
                px[x, y] = (30, 12, 6, a if d < 0.6 else a // 2)


def _finish(img, out="#2A1408", light="#8E461F"):
    from vol_art import outline_img
    return outline_img(img, out, light).copy()


def lamp():
    """Lámpara de banquero 42x42 con volumen: base de bronce, columna, pantalla de
    vidrio verde (3 tonos + brillo) con el borde dorado grueso y cadenita."""
    import vol_art as V
    w, h = 42, 42
    sc = V.Scene(w, h)
    sc.ellipsoid(21, 36, 15, 3.8, 0, "brass", z=0, depth=3)              # base
    sc.ellipsoid(21, 34.6, 9, 2.2, 0, "brass", z=2.6, depth=1.6)
    sc.capsule((21, 34), (21, 17), 1.7, 1.5, "brass", z=3)               # columna
    sc.ellipsoid(21, 24, 2.6, 1.6, 0, "brass", z=4, depth=1.5)           # anillo
    sc.ellipsoid(21, 12, 18, 7.2, 0, "glass_green", z=4, depth=7)        # pantalla
    sc.capsule((3.8, 17.6), (38.2, 17.6), 1.5, 1.5, "brass", z=9)        # borde dorado
    sc.ellipsoid(21, 4.4, 3.2, 1.8, 0, "brass", z=9, depth=1.6)          # remate
    img = sc.render(outline=None, inner=0.6, inner_col="#1A0E06", ao=0.4)
    img = img.copy()
    px = img.load()
    for y in range(19, 32):                                              # cadenita
        if y % 2 == 0:
            px[30, y] = (232, 168, 42, 255)
        else:
            px[30, y] = (150, 92, 22, 255)
    px[30, 32] = (255, 216, 106, 255)
    for y in range(12, 19):                                              # recorta la mitad de abajo de la pantalla
        pass
    for y in range(18, h):
        for x in range(w):
            p = px[x, y]
            if p[3] and (p[1] > p[0] + 20 and p[1] > p[2]):                # verde debajo del borde: afuera
                px[x, y] = (0, 0, 0, 0)
    img = _finish(img)
    _vol_shadow(img, 23, 39.4, 15, 2.2)          # la luz sobre la madera la hornea el juego (óvalo)
    return img


def mug():
    """Taza de café 20x21: cilindro de cerámica con borde, café, asa y franja azul."""
    w, h = 24, 25
    cv = Cv(w, h)
    Wt = P.R["white"]
    for a in range(-90, 91, 12):                                      # asa redonda con hueco
        import math as _m
        for r, col in ((4.2, Wt[2]), (3.2, Wt[4])):
            cv.put(int(round(16 + _m.cos(_m.radians(a)) * r)), int(round(11.5 + _m.sin(_m.radians(a)) * r)), col)
    P.cylinder_v(cv, 9.5, 4, 19, 7.4, Wt, ry=2.1)
    cv.ell(9.5, 4, 6.0, 1.5, "#40200F")                               # café
    cv.ell(8, 3.8, 2.6, 0.6, "#6A3A1E")
    cv.rect(2, 12, 16, 2, "#2F5FA0")                                  # franja
    cv.rect(2, 12, 16, 1, "#5A8FD0")
    cv.outline(OUTL, "#8E461F")
    _vol_shadow(cv.img, 12, 22.6, 9, 1.8)
    return cv.img


def phone():
    """Teléfono de escritorio 44x30: cuerpo de plástico con volumen, tubo en la
    horquilla, teclado y cable en espiral prolijo (con contorno, sin dentado)."""
    import vol_art as V
    w, h = 44, 30
    sc = V.Scene(w, h)
    sc.poly([(5, 13), (35, 13), (39, 24), (1, 24)], "plastic", z=0, dome=5, soft=2)          # cuerpo
    sc.capsule((6, 9.5), (34, 9.5), 2.6, 2.6, "plastic", z=8)                                 # tubo (más alto: se separa)
    sc.ellipsoid(6, 9.5, 4.2, 3.2, 0, "plastic", z=8.5, depth=3)                              # auricular
    sc.ellipsoid(34, 9.5, 4.2, 3.2, 0, "plastic", z=8.5, depth=3)                             # micrófono
    for i in range(7):                                                                        # cable en espiral hasta el escritorio
        sc.ellipsoid(38.5 + (i % 2) * 0.8 + i * 0.4, 12 + i * 2.2, 1.7, 1.1, 0, "plastic", z=3, depth=1)
    img = sc.render(outline=None, inner=0.9, inner_col="#7A7290").copy()      # filo claro entre tubo y base
    px = img.load()
    for r in range(3):                                                                        # teclado 3x4
        for c in range(4):
            x, y = 11 + c * 4, 16 + r * 2
            for dx in range(3):
                px[x + dx, y] = (196, 192, 214, 255) if r == 0 else (150, 144, 170, 255)
    for dx in range(4):
        for dy in range(3):
            px[29 + dx, 16 + dy] = (213, 87, 110, 255) if dy else (255, 196, 196, 255)       # botón rojo
    img = _finish(img)
    _vol_shadow(img, 21, 26.6, 19, 2.2)
    return img


def stamp_pad():
    """Almohadilla abierta (tinta a la vista, tapa con bisagra atrás) y, separado, el
    sello de goma parado con mango torneado y cuello claro; los dos con su sombra."""
    w, h = 40, 26
    cv = Cv(w, h)
    P.box(cv, 1, 11, 22, 11, 5, P.R["steel"], top_tone=3, front_tone=2)
    cv.rect(3, 12, 17, 4, "#962A2E")                                  # tinta roja (almohadilla abierta)
    cv.rect(3, 12, 17, 1, "#D5576E")
    cv.put(5, 13, "#FFC4C4")
    cv.poly([(1, 11), (19, 11), (21, 4), (3, 4)], P.R["steel"][4])    # tapa abierta hacia atrás
    cv.line([(3, 4), (21, 4)], P.R["steel"][6])
    P.cylinder_v(cv, 32, 7, 16, 2.8, P.R["oak"])                      # mango torneado
    cv.rect(30, 12, 5, 1, P.R["oak"][6])                              # cuello claro
    P.disk(cv, 32, 4, 3.6, P.R["oak"])
    P.box(cv, 26, 16, 13, 5, 1, P.R["dark"], top_tone=4, front_tone=2)
    cv.rect(27, 20, 11, 1, "#962A2E")
    cv.outline(OUTL, "#8E461F")
    _vol_shadow(cv.img, 13, 23.6, 12, 1.8)
    _vol_shadow(cv.img, 33.5, 23.8, 7.5, 1.6)
    return cv


def shredder():
    """La trituradora de 12.1 con tiras de papel verticales que caen (en vez de
    ruido) y ruedas con eje y brillo."""
    import minigames_art2 as M
    cv = M.shredder()
    rnd = random.Random(12)
    # cesto translúcido: el rojo del cesto se ve atenuado detrás y abajo el papel picado amontonado
    cv.rect(14, 25, 36, 16, "#5A2A30")
    for y in range(25, 41):
        for x in range(14, 50):
            if (x + y) % 5 == 0:
                cv.put(x, y, "#6E3A40")
    pile = [int(34 + 3.5 * (1 - ((x - 32) / 18.0) ** 2)) for x in range(14, 50)]
    for i, x in enumerate(range(14, 50)):
        for y in range(41 - (41 - pile[i]) - 1, 41):
            cv.put(x, max(30, 41 - (y - pile[i]) - 1), ["#EDE6DA", "#FFFFFF", "#F08C8F", "#D5576E", "#C9BFB0"][rnd.randint(0, 4)])
    for k in range(9):                                                # tiras cayendo de la boca
        x = rnd.randint(18, 46)
        for y in range(25, 25 + rnd.randint(3, 7)):
            cv.put(x, y, "#EDE6DA" if k % 3 else "#F08C8F")
    for k in range(5):                                                # reflejo del acrílico
        cv.put(16 + k, 32 - k, "#8A7A88")
    # calcomanía: la flecha blanca de 12.1 queda dentro de una etiqueta pegada
    cv.rect(19, 43, 26, 8, "#F4ECDA")
    cv.rect(19, 43, 26, 1, "#FFFFFF")
    cv.rect(19, 50, 26, 1, "#C9BFAE")
    cv.line([(23, 47), (41, 47)], "#B8323C", 2)
    for k in range(4):
        cv.put(23 + k, 46 - k, "#B8323C")
        cv.put(23 + k, 48 + k, "#B8323C")
    cv.clear(0, 55, 64, 60)                                           # ruedas enteras dentro del sprite
    cv.rect(9, 54, 46, 1, "#6E1E26")
    for wx in (13, 51):
        cv.ell(wx, 56.5, 2.6, 2.0, "#1E1A26")
        cv.ell(wx, 56.5, 1.2, 0.9, "#4A4259")
        cv.put(wx - 1, 56, "#9890AC")
    cv.outline(OUTL, "#8E461F")
    return cv


def folder():
    """La bandeja de 12.1 con el escudo de UI cambiado por una etiqueta de papel
    pegada con cinta y una flecha a mano en tinta azul (objeto, no ícono)."""
    import minigames_art2 as M
    cv = M.folder()
    px = cv.img.load()
    # busca el escudo azul y lo tapa con la etiqueta
    xs, ys = [], []
    for y in range(cv.h):
        for x in range(cv.w):
            r, g, b, a = px[x, y]
            if a and b > 150 and b > r + 40:
                xs.append(x)
                ys.append(y)
    if xs:
        x0, x1, y0, y1 = min(xs) - 1, max(xs) + 1, min(ys), max(ys)
        cv.rect(x0, y0, x1 - x0 + 1, y1 - y0 + 1, "#F4ECDA")
        cv.rect(x0, y0, x1 - x0 + 1, 1, "#FFFFFF")
        cv.rect(x0, y1, x1 - x0 + 1, 1, "#C9BFAE")
        cv.rect(x0 + 2, y0 - 1, 6, 2, "#E8DCA0")                       # cinta
        cv.rect(x1 - 7, y0 - 1, 6, 2, "#E8DCA0")
        my = (y0 + y1) // 2
        cv.line([(x0 + 4, my), (x1 - 5, my)], "#2F5FA0", 2)           # flecha en tinta
        for k in range(4):
            cv.put(x1 - 5 - k, my - k - 1, "#2F5FA0")
            cv.put(x1 - 5 - k, my + k + 1, "#2F5FA0")
    return cv


def main():
    for name, fn in (("desk", desk), ("blotter", blotter), ("lamp", lamp), ("mug", mug), ("phone", phone),
                     ("stamp_pad", stamp_pad), ("shredder", shredder), ("folder", folder)):
        im = fn()
        (im if isinstance(im, Image.Image) else im.img).save(os.path.join(OUT, name + ".png"))
    print("escritorio de la coima 12.2 en", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
