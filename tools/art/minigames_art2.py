"""Arte 12.1 de los minijuegos (asalto y coima): versión detallada.

Pintado a mano con polígonos sin antialias + rampas por material, luz
arriba-izquierda, contorno selectivo (más claro del lado de la luz).

Salida en assets/pixel_art/minigames/ (se dibuja a x2 en el juego):
  pistol_hand.png  mano derecha con guante tejido y pistola, 3 cuadros de 96x96
                   (0 quieta · 1 disparo: corredera atrás y luz del fogonazo ·
                   2 corredera trabada atrás = sin balas)
  bag_hand.png     mano izquierda que sostiene la bolsa, 2 cuadros de 88x100 (vacía, llena)
  muzzle.png       fogonazo de boca hacia la izquierda, 4 cuadros de 48x40
  impact.png       impacto (estrella + anillo + esquirlas), 4 cuadros de 32x32
  smoke.png        bocanada de humo, 5 cuadros de 16x16
  shell.png        vaina servida girando, 4 cuadros de 8x8
  hole2.png        agujero de bala en el piso con fisuras 12x10
  mag.png          cargador (recarga) 10x18
  floor_tiles.png  baldosas calcáreas del local, 4 variantes de 16x16 (en fila)
  rug.png          alfombra con guarda pampa 112x128
  shelf.png        tramo de estante de madera 32x14 (se repite)
  beacon.png       baliza de alarma de pared, 2 cuadros de 14x12
  plant.png        maceta con planta 22x34 · boxes.png pila de cajas 30x30
  office_wall.png  pared de la comisaría 240x86 (la ventana va aparte)
  street.png       la calle vista por la ventana 92x52
  window.png       marco, parante, persiana y reflejo de la ventana 100x60
  patrol_body.png  patrullero de costado 76x30, 2 cuadros (baliza roja / azul)
  wheel.png        rueda girando, 4 cuadros de 13x13
  desk.png         madera del escritorio (se repite) 64x48
  blotter.png      carpeta de escritorio de cuero con esquineros 116x140
  lamp.png         lámpara de banquero 30x30 · phone.png teléfono 28x18
  mug.png          taza de café 12x13 · stamp_pad.png sello y almohadilla 24x16
  doc_white_<k>.png / doc_red_<k>.png  documentos 96x120, k = 0..2
  shredder.png     trituradora 64x60 · folder.png bandeja con carpeta 64x56

Uso: python tools/art/minigames_art2.py  (después de minigames_art.py)
"""
import math
import os
import random

from PIL import Image, ImageDraw

import hands_art as H

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "pixel_art", "minigames")


def hx(c):
    if isinstance(c, tuple):
        return c if len(c) == 4 else c + (255,)
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


# ------------------------------------------------------------------ rampas
OUTL = "#3D1B0B"          # contorno de la guía de estilo
OUT_DK = "#1E1626"        # contorno de objetos oscuros (metal, guante)
STEEL = ["#262433", "#363347", "#4B4862", "#666283", "#8D89A8", "#C3C0D8", "#EEEDF7"]
GLOVE = ["#1F1B26", "#2A2533", "#363044", "#463F57", "#5C546F", "#7A7290"]
SKIN = ["#8A4E3C", "#B87259", "#E3A988", "#F3D2B6"]
SLEEVE = ["#1A1720", "#25212D", "#322C3D", "#433C52"]
BAG = ["#3A1F1B", "#6B3A22", "#9A5228", "#C96C2C", "#E8913A", "#F6B566", "#FCD9A0"]
ROPE = ["#7A5228", "#B08038", "#DDB050", "#F4D88A"]
BRASS = ["#7A4A12", "#B5700A", "#E8A82A", "#FFD86A", "#FFF4C0"]
WOOD = ["#4A2717", "#6D3A20", "#8E4E2A", "#A9643A", "#C2804E", "#DCA472"]


class Cv:
    def __init__(self, w, h):
        self.w, self.h = w, h
        self.img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.img)
        self.px = self.img.load()

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[x, y] = hx(c)

    def get(self, x, y):
        return self.px[x, y] if 0 <= x < self.w and 0 <= y < self.h else (0, 0, 0, 0)

    def clear(self, x0, y0, x1, y1):
        self.img.paste((0, 0, 0, 0), (x0, y0, x1, y1))

    def poly(self, pts, c):
        self.d.polygon([(round(x), round(y)) for x, y in pts], fill=hx(c))

    def rect(self, x, y, w, h, c):
        if w > 0 and h > 0:
            self.d.rectangle([x, y, x + w - 1, y + h - 1], fill=hx(c))

    def line(self, pts, c, width=1):
        self.d.line([(round(x), round(y)) for x, y in pts], fill=hx(c), width=width)

    def ell(self, cx, cy, rx, ry, c):
        for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
            for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
                if ((x - cx) / (rx + 0.5)) ** 2 + ((y - cy) / (ry + 0.5)) ** 2 <= 1:
                    self.put(x, y, c)

    def opaque(self, x, y):
        return self.get(x, y)[3] > 0

    def recolor_where(self, fn):
        """fn(x, y, rgba) -> color o None; sólo píxeles opacos."""
        ch = []
        for y in range(self.h):
            for x in range(self.w):
                p = self.px[x, y]
                if p[3]:
                    c = fn(x, y, p)
                    if c:
                        ch.append((x, y, c))
        for x, y, c in ch:
            self.put(x, y, c)

    def outline(self, dark, light=None):
        """Contorno exterior de 1 px; del lado de la luz (arriba-izquierda) más claro."""
        pts = []
        for y in range(self.h):
            for x in range(self.w):
                if self.px[x, y][3]:
                    continue
                right = self.opaque(x + 1, y)
                below = self.opaque(x, y + 1)
                left = self.opaque(x - 1, y)
                above = self.opaque(x, y - 1)
                if right or below or left or above:
                    lit = light and (right or below) and not (left or above)
                    pts.append((x, y, light if lit else dark))
        for x, y, c in pts:
            self.put(x, y, c)

    def paste(self, other, x, y):
        self.img.alpha_composite(other.img if isinstance(other, Cv) else other, (x, y))

    def save(self, name):
        self.img.save(os.path.join(OUT, name))


def sheet(frames):
    w, h = frames[0].w, frames[0].h
    s = Cv(w * len(frames), h)
    for i, f in enumerate(frames):
        s.paste(f, i * w, 0)
    return s


def inside(pts, x, y):
    """Punto dentro del polígono (paridad)."""
    n = len(pts)
    ins = False
    j = n - 1
    for i in range(n):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-9) + xi:
            ins = not ins
        j = i
    return ins


def shade_poly(cv, pts, ramp, base, light_dir=(-1, -1), knit=False):
    """Relleno sombreado por cercanía al borde: luz del lado arriba-izquierda,
    sombra del lado abajo-derecha. ramp de oscuro a claro; base = índice medio."""
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    for y in range(int(min(ys)), int(max(ys)) + 1):
        for x in range(int(min(xs)), int(max(xs)) + 1):
            if not inside(pts, x + 0.5, y + 0.5):
                continue
            dl = 0
            while dl < 4 and inside(pts, x + 0.5 + light_dir[0] * (dl + 1), y + 0.5 + light_dir[1] * (dl + 1)):
                dl += 1
            ds = 0
            while ds < 4 and inside(pts, x + 0.5 - light_dir[0] * (ds + 1), y + 0.5 - light_dir[1] * (ds + 1)):
                ds += 1
            i = base
            if dl == 0:
                i = base + 2
            elif dl == 1:
                i = base + 1
            if ds == 0:
                i = base - 2
            elif ds == 1:
                i = min(i, base - 1)
            if knit and (x + 2 * y) % 5 == 0:
                i -= 1
            i = max(0, min(len(ramp) - 1, i))
            cv.put(x, y, ramp[i])


# ================================================================== PISTOLA
def finger(cv, x0, y0, x1, y1, th, tip_len, glove=GLOVE, skin=SKIN):
    """Dedo como cápsula de (x0,y0) a (x1,y1); la punta (x0) con piel (guante sin dedos)."""
    ang = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(ang) * th / 2, math.cos(ang) * th / 2
    pts = [(x0 + nx, y0 + ny), (x1 + nx, y1 + ny), (x1 - nx, y1 - ny), (x0 - nx, y0 - ny)]
    shade_poly(cv, pts, glove, 3, knit=True)
    L = math.hypot(x1 - x0, y1 - y0)
    k = tip_len / max(1, L)
    tx, ty = x0 + (x1 - x0) * k, y0 + (y1 - y0) * k
    tip = [(x0 + nx, y0 + ny), (tx + nx, ty + ny), (tx - nx, ty - ny), (x0 - nx, y0 - ny)]
    shade_poly(cv, tip, skin, 2)
    cv.line([(tx + nx, ty + ny), (tx - nx, ty - ny)], glove[4])


def _gun(cv, frame):
    """Pistola (corredera, armazón, guardamonte, miras) apuntando a la izquierda."""
    back = 5 if frame in (1, 2) else 0
    fx = 12
    shade_poly(cv, [(16, 41), (50, 40), (52, 46), (16, 46)], STEEL, 2)   # armazón
    for x in range(20, 32, 3):                                            # riel
        cv.put(x, 44, STEEL[0])
    cv.line([(30, 46), (30, 50), (33, 54), (44, 54), (47, 50)], STEEL[1], 2)   # guardamonte
    cv.line([(31, 50), (34, 53), (43, 53)], STEEL[4])
    cv.line([(40, 47), (39, 51)], STEEL[0], 2)                                # cola del disparador
    if back:
        cv.rect(fx, 34, back + 4, 5, BRASS[1])                              # caño a la vista
        cv.line([(fx, 34), (fx + back + 3, 34)], BRASS[3])
        cv.line([(fx, 38), (fx + back + 3, 38)], BRASS[0])
    sx0 = fx + back
    shade_poly(cv, [(sx0, 31), (66 + back, 27), (67 + back, 40), (sx0, 41)], STEEL, 3)
    shade_poly(cv, [(sx0 + 2, 28), (68 + back, 24), (66 + back, 27), (sx0, 31)], STEEL, 5)
    cv.poly([(66 + back, 27), (69 + back, 25), (70 + back, 38), (67 + back, 40)], STEEL[1])
    for x in range(55, 64, 2):                                            # estrías
        cv.line([(x + back, 29), (x + back, 38)], STEEL[1])
        cv.line([(x + back + 1, 29), (x + back + 1, 38)], STEEL[4])
    cv.poly([(34 + back, 31), (46 + back, 30), (46 + back, 34), (34 + back, 35)], STEEL[0])   # ventana de expulsión
    if frame == 0:
        cv.rect(36 + back, 32, 8, 2, BRASS[2])
        cv.put(36 + back, 32, BRASS[4])
    cv.line([(sx0 + 2, 28), (68 + back, 24)], STEEL[6])
    cv.line([(sx0 + 1, 41), (66 + back, 40)], STEEL[0])
    cv.rect(sx0 + 3, 26, 3, 2, STEEL[4])                                  # miras
    cv.put(sx0 + 3, 26, STEEL[6])
    cv.rect(62 + back, 22, 2, 3, STEEL[3])
    cv.rect(66 + back, 21, 2, 3, STEEL[3])
    cv.put(64 + back, 23, "#FFFFFF")
    cv.rect(sx0, 32, 2, 9, STEEL[2])                                      # frente de la corredera
    cv.rect(sx0, 35, 1, 3, "#120E18")                                     # boca del caño
    cv.rect(44, 42, 4, 2, STEEL[1])
    cv.put(44, 42, STEEL[5])


def pistol_hand(frame):
    """Mano derecha con guante táctico sin dedos empuñando la pistola, vista del
    lado derecho: se ve el dorso, el índice estirado sobre el armazón (en el
    gatillo al disparar) y mayor, anular y meñique envolviendo el frente de la
    empuñadura, con las puntas de piel al aire. 0 quieta · 1 disparo · 2 sin balas."""
    cv = Cv(96, 96)
    # --- manga de campera con pliegues
    shade_poly(cv, [(60, 96), (66, 80), (80, 68), (96, 62), (96, 96)], SLEEVE, 2)
    for k in range(3):
        cv.line([(72 + k * 8, 96), (79 + k * 6, 78 + k * 2)], SLEEVE[0])
        cv.line([(73 + k * 8, 96), (80 + k * 6, 78 + k * 2)], SLEEVE[3])
    # --- muñeca y puño elastizado del guante
    H.capsule(cv, (78, 82), (69, 71), 7.5, H.GLOVE, bias=-0.3, r2=6.5)
    for k in range(5):                                    # elástico acanalado
        x, y = 70 + k * 3, 82 - k * 2.4
        cv.line([(x - 4, y - 3), (x + 2, y + 4)], H.GLOVE[1])
    # correa de abrojo
    H.capsule(cv, (63, 72), (75, 63), 2.6, H.GLOVE, bias=0.8)
    cv.line([(66, 69), (72, 65)], H.GLOVE[2])

    # --- empuñadura (asoma el talón del cargador abajo)
    shade_poly(cv, [(47, 44), (62, 42), (70, 70), (56, 74)], STEEL, 2)
    cv.poly([(54, 72), (66, 69), (67, 73), (55, 76)], STEEL[1])
    cv.line([(55, 72), (66, 69)], STEEL[4])

    # --- dorso de la mano: ancho en los nudillos, se angosta hacia la muñeca
    H.capsule(cv, (61, 52), (69, 69), 13, H.GLOVE, bias=0.3, knit=True, r2=8.5)
    # eminencia del pulgar / membrana sobre la cola del armazón
    H.ellipsoid(cv, 61, 42, 6, 4, -0.3, H.GLOVE, bias=0.4)
    # tendones extensores (de la muñeca a cada nudillo)
    for kx, ky in ((54, 49), (55, 56), (56, 63)):
        cv.line([(68, 70), ((kx + 68) / 2 + 1, (ky + 70) / 2)], H.GLOVE[2])
    H.stitches(cv, [(66, 45), (69, 54), (69, 63)])

    # --- mayor, anular y meñique envolviendo el frente de la empuñadura
    #     (nudillo -> falange proximal hacia adelante -> la media dobla y asoma la piel)
    fingers = [
        ([(58, 64), (51, 66), (47, 68.5)], [2.7, 2.4], 1),            # meñique
        ([(57, 57.5), (49, 59), (44.5, 61.5)], [3.1, 2.7], 1),        # anular
        ([(56, 51), (47, 52), (42.5, 54.5)], [3.3, 2.9], 1),          # mayor
    ]
    for pts, rad, sk in fingers:
        H.finger_chain(cv, pts, rad, sk, nail=False)
    H.knuckles(cv, [(56, 51), (57, 57.5), (58, 64)], 1.5)

    _gun(cv, frame)

    # --- índice: estirado sobre el armazón, o doblado en el gatillo al disparar
    if frame == 1:
        H.finger_chain(cv, [(56, 45), (47, 46.5), (41, 49.5), (39.5, 52)], [3.1, 2.8, 2.4], 2)
    else:
        H.finger_chain(cv, [(56, 45), (46, 45.5), (37, 46), (30.5, 46.5)], [3.1, 2.8, 2.5], 2)
    H.knuckles(cv, [(56, 45)], 1.6)

    if frame == 1:
        # luz cálida del fogonazo en los filos que miran arriba-izquierda
        snap = cv.img.copy()
        sp = snap.load()

        def warm(x, y, p):
            if x > 62:
                return None
            if x > 0 and y > 0 and sp[x - 1, y][3] and sp[x, y - 1][3]:
                return None
            r, g, b, a = p
            return (min(255, r + 110), min(255, g + 64), min(255, b + 8), a)
        cv.recolor_where(warm)

    cv.outline(OUT_DK, "#4B4862")
    return cv


def muzzle(f):
    """Fogonazo de boca: estrella con cono hacia la izquierda, núcleo blanco. Origen en (44, 20)."""
    cv = Cv(48, 40)
    ox, oy = 44, 20
    L = (34, 42, 30, 16)[f]
    W = (10, 14, 11, 6)[f]
    cols = ["#FFFFFF", "#FFF4C0", "#FFD86A", "#FFB070", "#E8823A", "#B5541F"]
    rnd = random.Random(7 + f)
    rays = [(-1, 0, L), (-0.7, -0.7, L * 0.45), (-0.7, 0.7, L * 0.45), (0, -1, L * 0.25), (0, 1, L * 0.25),
            (-0.92, -0.38, L * 0.7), (-0.92, 0.38, L * 0.7)]
    for dx, dy, ln in rays:
        for k in range(int(ln)):
            w = max(0.5, (W / 2) * (1 - k / ln) * (0.6 if dx > -0.9 else 1.0))
            px, py = ox + dx * k, oy + dy * k
            for t in range(-int(w), int(w) + 1):
                qx, qy = px - dy * t, py + dx * t
                ci = min(len(cols) - 1, int((k / ln) * 4 + abs(t) / max(1, w) * 2))
                if f == 3:
                    ci = min(len(cols) - 1, ci + 2)
                cv.put(int(qx), int(qy), cols[ci])
    if f < 3:
        cv.ell(ox - 3, oy, 4 - f, 4 - f, "#FFFFFF")
    for i in range(6 + f * 2):
        a = math.pi + rnd.uniform(-0.8, 0.8)
        r = rnd.uniform(L * 0.4, L * 1.05)
        cv.put(int(ox + math.cos(a) * r), int(oy + math.sin(a) * r), cols[rnd.randint(1, 3)])
    return cv


def impact(f):
    """Impacto: destello en estrella + anillo expansivo + esquirlas."""
    cv = Cv(32, 32)
    c = 16
    if f < 2:
        r = (9, 12)[f]
        for a in range(8):
            ang = a * math.pi / 4 + 0.39
            ln = r if a % 2 == 0 else r * 0.55
            for k in range(int(ln)):
                w = max(0, int(2 * (1 - k / ln)))
                for t in range(-w, w + 1):
                    cv.put(int(c + math.cos(ang) * k - math.sin(ang) * t), int(c + math.sin(ang) * k + math.cos(ang) * t),
                           "#FFFFFF" if k < ln * 0.4 else ("#FFE07A" if k < ln * 0.75 else "#FFB070"))
        cv.ell(c, c, 4 - f, 4 - f, "#FFFFFF")
    rr = (5, 9, 12, 14)[f]
    col = ("#FFF4C0", "#FFE07A", "#FFB070", "#E8823A")[f]
    for a in range(48):
        if f >= 2 and a % 3 == 0:
            continue
        ang = a / 48 * math.tau
        cv.put(int(round(c + math.cos(ang) * rr)), int(round(c + math.sin(ang) * rr)), col)
    rnd = random.Random(3)
    for i in range(10):
        ang = rnd.uniform(0, math.tau)
        d = rr * rnd.uniform(0.5, 1.15)
        if f >= 1:
            cv.put(int(c + math.cos(ang) * d), int(c + math.sin(ang) * d), "#FFE07A" if i % 2 else "#FFFFFF")
    return cv


def smoke(f):
    cv = Cv(16, 16)
    r = (2.5, 4, 5, 6, 6.5)[f]
    a = (230, 200, 160, 110, 60)[f]
    blobs = [(8, 8, 1.0), (6, 9, 0.7), (10, 7, 0.75), (8, 6, 0.6)]
    for bx, by, k in blobs:
        rr = r * k
        for y in range(16):
            for x in range(16):
                d = ((x - bx) ** 2 + (y - by) ** 2) ** 0.5
                if d <= rr:
                    shade = (232, 226, 234) if (x - bx) + (y - by) < 0 else (176, 168, 186)
                    if f >= 3 and (x + y) % 2 == 0 and d > rr * 0.6:
                        continue           # se deshace tramado
                    cv.px[x, y] = shade + (a,)
    return cv


def shell(f):
    cv = Cv(8, 8)
    ang = f * math.pi / 4
    for t in range(-2, 3):
        x = 4 + math.cos(ang) * t
        y = 4 + math.sin(ang) * t
        cv.put(int(round(x)), int(round(y)), BRASS[3] if t < 0 else BRASS[2])
        cv.put(int(round(x - math.sin(ang))), int(round(y + math.cos(ang))), BRASS[1])
    cv.put(int(round(4 + math.cos(ang) * 2)), int(round(4 + math.sin(ang) * 2)), BRASS[0])
    return cv


def hole():
    cv = Cv(12, 10)
    cv.ell(6, 5, 2.5, 2, "#2A1A20")
    cv.ell(6, 5, 1.2, 1, "#120A10")
    for dx, dy in ((-4, -2), (-5, -3), (4, 2), (5, 3), (3, -3), (4, -4), (-3, 3)):
        cv.put(6 + dx, 5 + dy, "#5A3A30")
    cv.put(4, 3, "#E8D8C0")
    cv.put(8, 7, "#E8D8C0")
    return cv


def mag():
    cv = Cv(10, 18)
    shade_poly(cv, [(2, 1), (8, 1), (8, 15), (2, 16)], STEEL, 3)
    cv.rect(3, 0, 4, 2, BRASS[2])
    cv.put(3, 0, BRASS[4])
    cv.rect(1, 15, 8, 3, STEEL[1])
    cv.outline(OUT_DK)
    return cv


# ================================================================== BOLSA
def bag_hand(full):
    """Mano izquierda (guante tejido) que levanta la bolsa por el cuello atado."""
    cv = Cv(88, 100)
    ox = 44
    if full:
        body = [(ox - 28, 98), (ox - 34, 86), (ox - 31, 70), (ox - 21, 56), (ox - 9, 49), (ox + 13, 49),
                (ox + 26, 56), (ox + 37, 70), (ox + 40, 86), (ox + 34, 98)]
    else:
        body = [(ox - 22, 98), (ox - 27, 88), (ox - 23, 74), (ox - 14, 61), (ox - 6, 53), (ox + 10, 53),
                (ox + 20, 61), (ox + 30, 74), (ox + 33, 88), (ox + 28, 98)]
    xs = [p[0] for p in body]
    cx = (min(xs) + max(xs)) / 2
    half = (max(xs) - min(xs)) / 2
    for y in range(40, 100):
        for x in range(0, 88):
            if not inside(body, x + 0.5, y + 0.5):
                continue
            # la mitad izquierda en sombra (como la referencia), luz a la derecha-arriba
            t = (x - cx) / half
            i = 4
            if t < -0.45:
                i = 2
            elif t < -0.05:
                i = 3
            if t > 0.25 and y < 82:
                i = 5
            if t > 0.45 and y < 72:
                i = 6 if (x + y) % 3 else 5
            if y > 93:
                i = max(1, i - 2)
            elif y > 89:
                i -= 1
            if (x * 3 + y * 5) % 11 == 0 and i > 2:
                i -= 1            # trama de arpillera
            cv.put(x, y, BAG[max(0, min(6, i))])
    if full:
        cv.line([(ox - 2, 56), (ox - 4, 76), (ox - 1, 96)], BAG[2])
        cv.poly([(ox + 12, 62), (ox + 24, 60), (ox + 28, 70), (ox + 16, 72)], BAG[5])     # esquina de caja
        cv.line([(ox + 12, 62), (ox + 24, 60), (ox + 28, 70)], BAG[6])
        cv.poly([(ox - 25, 74), (ox - 15, 70), (ox - 13, 80), (ox - 25, 82)], BAG[2])
        cv.line([(ox - 25, 74), (ox - 15, 70)], BAG[3])
    else:
        cv.line([(ox, 60), (ox - 2, 78), (ox + 1, 96)], BAG[2])
        for k in range(3):     # pliegues de bolsa vacía
            cv.line([(ox - 10 + k * 9, 58 + k), (ox - 14 + k * 11, 76 + k * 2)], BAG[3 if k else 2])
    # parche cosido
    cv.rect(ox + 8, 80, 12, 9, BAG[3])
    cv.rect(ox + 8, 80, 12, 1, BAG[5])
    for x in range(ox + 8, ox + 20, 2):
        cv.put(x, 81, BAG[6])
        cv.put(x + 1, 88, BAG[1])
    # cuello fruncido (largo: el puño lo agarra y la boca queda libre arriba)
    shade_poly(cv, [(ox - 8, 22), (ox + 10, 22), (ox + 10, 52), (ox - 8, 52)], BAG, 3)
    for x in range(ox - 6, ox + 9, 3):
        cv.line([(x, 23), (x + 1, 51)], BAG[1])
    # boca abierta (acampanada, como la referencia)
    mw = 16 if full else 14
    shade_poly(cv, [(ox - mw - 2, 16), (ox - mw + 2, 7), (ox + mw, 7), (ox + mw + 4, 16), (ox + 10, 24), (ox - 8, 24)], BAG, 4)
    cv.ell(ox + 1, 11, mw - 1, 3.5, BAG[1])
    cv.ell(ox + 1, 12, mw - 3, 2.5, "#22121A")
    cv.line([(ox - mw + 2, 7), (ox + mw, 7)], BAG[6])
    cv.line([(ox - mw - 1, 16), (ox - 8, 23)], BAG[1])
    if full:
        # mercadería asomando: una caja y billetes
        cv.poly([(ox - 9, 12), (ox - 2, 2), (ox + 6, 6), (ox - 1, 15)], "#C2804E")
        cv.line([(ox - 9, 12), (ox - 2, 2), (ox + 6, 6)], "#E4AD69")
        cv.line([(ox - 5, 7), (ox + 2, 11)], "#8E4E2A")
        cv.poly([(ox + 4, 11), (ox + 12, 1), (ox + 16, 4), (ox + 9, 13)], "#67D08E")
        cv.line([(ox + 4, 11), (ox + 12, 1)], "#B6F0B0")
        cv.put(ox + 10, 6, "#2E7D4F")
    # soga con moño debajo del puño
    ry = 47
    cv.line([(ox - 9, ry), (ox + 11, ry - 1)], ROPE[1], 3)
    cv.line([(ox - 9, ry - 1), (ox + 11, ry - 2)], ROPE[3])
    for side in (-1, 1):
        lx = ox + 3 + side * 8
        cv.poly([(ox + 3, ry), (lx, ry - 4), (lx + side * 2, ry + 3)], ROPE[2])
        cv.line([(ox + 3, ry), (lx, ry - 4)], ROPE[3])
    cv.line([(ox + 2, ry + 2), (ox - 1, ry + 11)], ROPE[1], 2)
    cv.line([(ox + 5, ry + 2), (ox + 10, ry + 10)], ROPE[1], 2)
    cv.put(ox - 1, ry + 11, ROPE[0])
    cv.put(ox + 10, ry + 10, ROPE[0])
    cv.ell(ox + 3, ry, 2, 2, ROPE[2])
    cv.put(ox + 2, ry - 1, ROPE[3])

    # brazo desde la esquina inferior izquierda hasta el puño (detrás de la bolsa)
    arm = Cv(88, 100)
    shade_poly(arm, [(0, 58), (12, 40), (26, 46), (12, 76), (0, 84)], SLEEVE, 2)
    arm.line([(2, 70), (14, 50)], SLEEVE[0])
    arm.line([(3, 70), (15, 50)], SLEEVE[3])
    H.capsule(arm, (14, 46), (24, 38), 8, H.GLOVE, bias=-0.3)          # muñeca con puño elastizado
    for k in range(5):
        x, y = 12 + k * 3, 48 - k * 2.4
        arm.line([(x - 3, y - 4), (x + 3, y + 3)], H.GLOVE[1])
    under = arm.img.copy()
    under.alpha_composite(cv.img)
    cv.img = under
    cv.d = ImageDraw.Draw(cv.img)
    cv.px = cv.img.load()
    # --- puño izquierdo cerrado sobre el cuello, el dorso hacia el jugador:
    #     dorso, 4 dedos que cruzan el cuello (la piel de las puntas asoma del
    #     otro lado del cuello) y el pulgar arriba, cerrando el puño.
    H.ellipsoid(cv, ox - 13, 34, 10, 9.5, -0.5, H.GLOVE, bias=0.2, knit=True)
    for ky in (27.5, 32.5, 37.5):
        cv.line([(ox - 22, ky + 9), (ox - 8, ky + 1)], H.GLOVE[2])          # tendones
    H.stitches(cv, [(ox - 21, 30), (ox - 14, 26), (ox - 8, 26)])
    fingers = [
        ([(ox - 5, 41.5), (ox + 5, 41.5), (ox + 10, 43)], [2.6, 2.3]),     # meñique
        ([(ox - 5, 37), (ox + 6, 36.5), (ox + 11.5, 38)], [2.9, 2.6]),     # anular
        ([(ox - 5, 32.5), (ox + 6, 32), (ox + 11.5, 33.5)], [3.0, 2.7]),   # mayor
        ([(ox - 5, 28), (ox + 5, 27.5), (ox + 10.5, 29)], [2.9, 2.6]),     # índice
    ]
    for pts, rad in fingers:
        H.finger_chain(cv, pts, rad, 1, nail=False)
    H.knuckles(cv, [(ox - 5, 28), (ox - 5, 32.5), (ox - 5, 37), (ox - 5, 41.5)], 1.4)
    # pulgar: sale del costado del dorso y se apoya sobre el índice
    H.finger_chain(cv, [(ox - 16, 28), (ox - 7, 23.5), (ox + 1, 23.5), (ox + 5.5, 25)], [3.2, 2.7, 2.4], 2)
    cv.outline(OUTL, "#8E461F")
    return cv


# ================================================================== ASALTO: fondo
def floor_tiles():
    """4 baldosas calcáreas (crema y terracota en damero) con biselado y desgaste."""
    cv = Cv(64, 16)
    rnd = random.Random(5)
    cream = ["#A98666", "#C2A07E", "#CFAF8C", "#DCC09E"]       # fondo: poco contraste,
    terra = ["#7E4632", "#8E543C", "#9A6046", "#A86E52"]       # que resalten los personajes
    for v in range(4):
        r = cream if v % 2 == 0 else terra
        x0 = v * 16
        cv.rect(x0, 0, 16, 16, r[2])
        cv.rect(x0, 0, 16, 1, r[3])
        cv.rect(x0, 0, 1, 16, r[3])
        cv.rect(x0, 15, 16, 1, "#5A3424")          # junta
        cv.rect(x0 + 15, 0, 1, 16, "#5A3424")
        cv.rect(x0 + 1, 14, 14, 1, r[1])
        cv.rect(x0 + 14, 1, 1, 14, r[1])
        if r is cream:                              # motivo calcáreo: rombo
            for k in range(4):
                cv.put(x0 + 7 - k, 4 + k, r[1])
                cv.put(x0 + 8 + k, 4 + k, r[1])
                cv.put(x0 + 7 - k, 11 - k, r[1])
                cv.put(x0 + 8 + k, 11 - k, r[1])
            cv.put(x0 + 7, 7, "#9A4E32")
            cv.put(x0 + 8, 8, "#9A4E32")
            cv.put(x0 + 8, 7, "#B4643F")
            cv.put(x0 + 7, 8, "#B4643F")
        for i in range(6):
            cv.put(x0 + rnd.randint(2, 12), rnd.randint(2, 12), r[1] if i % 2 else r[3])
        if v == 3:   # fisura
            cv.line([(x0 + 3, 3), (x0 + 6, 7), (x0 + 5, 10), (x0 + 9, 13)], r[0])
    return cv


def rug():
    cv = Cv(112, 128)
    red = ["#4A1C1E", "#66282A", "#7E3432", "#954440"]
    cre = ["#A48A68", "#BCA27E", "#CCB490"]
    cv.rect(0, 4, 112, 120, red[1])
    cv.rect(4, 8, 104, 112, cre[1])
    cv.rect(6, 10, 100, 108, red[2])
    for x in range(8, 104, 8):              # guarda pampa (escalonado)
        for y in (12, 110):
            cv.rect(x, y, 4, 2, cre[1])
            cv.rect(x + 2, y + 2, 4, 2, cre[1])
            cv.rect(x + 4, y + 4, 2, 2, red[0])
    for y in range(20, 108, 8):
        for x in (12, 94):
            cv.rect(x, y, 2, 4, cre[1])
            cv.rect(x + 2, y + 2, 2, 4, cre[1])
            cv.rect(x + 4, y + 4, 2, 2, red[0])
    cv.rect(22, 24, 68, 80, red[1])
    cv.rect(24, 26, 64, 76, red[2])
    for k in range(23):                     # medallón central
        w = k if k <= 11 else 22 - k
        cv.rect(56 - w * 2, 41 + k * 2, w * 4 + 1, 2, cre[1] if w > 2 else cre[2])
        if w > 4:
            cv.rect(56 - (w - 4) * 2, 41 + k * 2, (w - 4) * 4 + 1, 2, red[1])
        if w > 7:
            cv.rect(56 - (w - 7) * 2, 41 + k * 2, (w - 7) * 4 + 1, 2, "#B88A2C")
    for x in range(2, 110, 3):              # flecos
        cv.rect(x, 0, 1, 4, cre[2])
        cv.rect(x, 124, 1, 4, cre[0])
    rnd = random.Random(9)
    for i in range(160):                    # desgaste
        x, y = rnd.randint(6, 105), rnd.randint(10, 117)
        p = cv.get(x, y)
        if p[3]:
            cv.px[x, y] = tuple(max(0, v - 18) for v in p[:3]) + (255,)
    cv.rect(0, 122, 112, 2, red[0])
    return cv


def shelf_seg():
    cv = Cv(32, 14)
    cv.rect(0, 2, 32, 5, WOOD[3])
    cv.rect(0, 2, 32, 1, WOOD[5])
    cv.rect(0, 3, 32, 1, WOOD[4])
    cv.rect(0, 6, 32, 1, WOOD[1])
    cv.rect(0, 7, 32, 1, OUTL)
    for x in (5, 19, 27):
        cv.put(x, 4, WOOD[2])
    cv.rect(13, 7, 3, 5, STEEL[3])          # ménsula
    cv.line([(13, 7), (13, 11)], STEEL[5])
    cv.put(14, 11, STEEL[1])
    cv.rect(2, 8, 7, 4, "#FFF6E6")          # etiqueta de precio
    cv.rect(3, 9, 4, 1, "#D5576E")
    cv.rect(3, 10, 3, 1, "#8E461F")
    return cv


def beacon(on):
    cv = Cv(14, 12)
    cv.rect(2, 9, 10, 3, STEEL[2])
    cv.rect(2, 9, 10, 1, STEEL[4])
    r = ["#7A1E24", "#B8323C", "#E85060", "#FF9AA0", "#FFFFFF"] if on else ["#4A1418", "#6A1E24", "#8A2A30", "#A84048", "#C06060"]
    cv.ell(7, 6, 4.5, 4.5, r[1])
    cv.rect(2, 6, 11, 4, r[1])
    cv.ell(6, 5, 2.5, 2.5, r[2])
    cv.put(5, 3, r[4] if on else r[3])
    cv.put(5, 4, r[3])
    cv.line([(3, 8), (11, 8)], r[0])
    cv.outline(OUTL)
    return cv


def plant():
    cv = Cv(22, 34)
    g = ["#1E5A36", "#2E7D4F", "#3F9E5E", "#67D08E", "#A8E6A0"]
    leaves = [(11, 4, -0.2), (5, 9, -0.9), (17, 8, 0.8), (8, 14, -0.5), (15, 15, 0.6), (11, 12, 0.0), (3, 16, -1.2), (19, 17, 1.1)]
    for x, y, a in leaves:
        L = 9
        for k in range(L):
            w = 2.2 * math.sin(math.pi * k / L) + 0.3
            px, py = x + math.sin(a) * k * 0.6, y + k
            for t in range(-int(w), int(w) + 1):
                cv.put(int(px + t), int(py - abs(t) * 0.5), g[2] if t < 0 else g[1])
            cv.put(int(px), int(py), g[0] if k > 2 else g[3])
        cv.put(int(x - 1), int(y + 1), g[4])
    shade_poly(cv, [(4, 22), (18, 22), (16, 33), (6, 33)], ["#5A2A18", "#7A3A26", "#9A4E32", "#B4643F", "#CC7E55", "#E09A70"], 3)
    cv.rect(3, 21, 16, 3, "#B4643F")
    cv.rect(3, 21, 16, 1, "#E09A70")
    cv.outline(OUTL, "#8E461F")
    return cv


def boxes():
    cv = Cv(30, 30)

    def box(x, y, w, h):
        cv.rect(x, y, w, h, WOOD[4])
        cv.rect(x, y, w, 1, WOOD[5])
        cv.rect(x, y + h - 1, w, 1, WOOD[2])
        cv.rect(x + w - 1, y, 1, h, WOOD[2])
        cv.rect(x + w // 2 - 1, y, 3, h, "#E8D2A8")       # cinta
        cv.rect(x + 2, y + h - 5, 5, 3, "#FFF6E6")         # etiqueta
        cv.put(x + 3, y + h - 4, "#3D1B0B")
    box(1, 14, 14, 15)
    box(15, 14, 14, 15)
    box(6, 2, 17, 12)
    cv.outline(OUTL, "#8E461F")
    return cv


# ================================================================== COIMA: comisaría
def office_wall():
    """Pared de 240x86: yeso arriba, friso azul con paneles abajo, cuadro con escudo y bandera."""
    cv = Cv(240, 86)
    rnd = random.Random(12)
    plaster = ["#B9AE9C", "#CFC5B4", "#DDD4C4", "#E9E2D4"]
    blue = ["#1F3F6E", "#2F5FA0", "#3E74B8", "#5A8FD0", "#8FC4FF"]
    cv.rect(0, 0, 240, 86, plaster[2])
    for y in range(0, 64):
        for x in range(240):
            n = rnd.random()
            if n < 0.06:
                cv.put(x, y, plaster[1])
            elif n < 0.09:
                cv.put(x, y, plaster[3])
    for y in range(0, 4):
        cv.rect(0, y, 240, 1, plaster[0] if y < 2 else plaster[1])
    cv.rect(0, 4, 240, 1, plaster[3])          # cornisa
    rail = 64                                   # moldura (la ventana apoya el alféizar acá)
    cv.rect(0, rail, 240, 2, "#E9E2D4")
    cv.rect(0, rail + 2, 240, 2, WOOD[2])
    cv.rect(0, rail + 4, 240, 18, blue[1])
    for x0 in range(4, 240, 30):
        cv.rect(x0, rail + 7, 24, 10, blue[2])
        cv.rect(x0, rail + 7, 24, 1, blue[0])
        cv.rect(x0, rail + 7, 1, 10, blue[0])
        cv.rect(x0, rail + 16, 24, 1, blue[3])
        cv.rect(x0 + 23, rail + 7, 1, 10, blue[3])
    cv.rect(0, 82, 240, 4, blue[0])
    cv.rect(0, 82, 240, 1, blue[3])
    # cuadro con el escudo
    fx, fy = 162, 30
    cv.rect(fx - 1, fy + 1, 18, 21, plaster[0])   # sombra en la pared
    cv.rect(fx, fy, 16, 20, WOOD[1])
    cv.rect(fx + 1, fy + 1, 14, 18, "#F6EFE2")
    cv.ell(fx + 8, fy + 10, 4.5, 5.5, "#2F5FA0")
    cv.ell(fx + 8, fy + 10, 3.5, 4.5, "#74ACDF")
    cv.rect(fx + 5, fy + 10, 7, 3, "#FFFFFF")
    cv.ell(fx + 8, fy + 5, 2, 1.5, "#F6B40E")
    cv.rect(fx + 3, fy + 16, 10, 1, "#2E7D4F")
    cv.rect(fx, fy, 16, 1, WOOD[4])
    # bandera en asta (sólo se ve en pantallas anchas)
    bx = 222
    cv.rect(bx, 6, 2, 50, "#C9A64A")
    cv.ell(bx + 1, 5, 1.5, 1.5, "#F6B40E")
    for y in range(9, 27):
        for x in range(bx + 2, bx + 16):
            yy = y + int(math.sin((x - bx) * 0.5) * 1.2)
            col = "#74ACDF" if (y - 9) < 6 or (y - 9) >= 12 else "#FFFFFF"
            if (x - bx) > 12:
                col = "#5A92C8" if col == "#74ACDF" else "#E4E4EE"
            cv.put(x, yy, col)
    cv.ell(bx + 9, 18, 1.5, 1.5, "#F6B40E")
    return cv


def street():
    """Vista de la calle por la ventana: cielo, fachadas de enfrente, vereda y asfalto."""
    cv = Cv(92, 52)
    sky = ["#3DB4FE", "#60CAFE", "#AFE6F2"]
    for y in range(0, 30):
        cv.rect(0, y, 92, 1, sky[0] if y < 6 else (sky[1] if y < 16 else sky[2]))
    rnd = random.Random(21)
    x = -4
    cols = [("#C88555", "#94552A", "#E4AD69"), ("#E4D7C7", "#B5AB9C", "#F6EFE2"), ("#D5576E", "#953730", "#F08C8F"),
            ("#8FC4FF", "#4E8FD8", "#D0E8FF"), ("#F6B40E", "#C07A12", "#FFE07A")]
    i = 0
    while x < 92:
        w = rnd.randint(16, 24)
        top = rnd.randint(4, 12)
        m, s, l = cols[i % len(cols)]
        cv.rect(x, top, w, 32 - top, m)
        cv.rect(x, top, w, 2, s)              # cornisa
        cv.rect(x, top + 2, w, 1, l)
        cv.rect(x + w - 1, top, 1, 32 - top, s)
        for wy in range(top + 5, 27, 8):
            for wx in range(x + 3, x + w - 4, 6):
                cv.rect(wx, wy, 3, 5, "#3B3560")
                cv.put(wx, wy, "#AFE6F2")
                cv.rect(wx - 1, wy + 5, 5, 1, l)   # balconcito
        x += w
        i += 1
    cv.ell(12, 22, 7, 6, "#3F9E5E")         # árbol de vereda
    cv.ell(10, 20, 4, 3, "#67D08E")
    cv.rect(11, 26, 2, 8, "#6D432B")
    cv.rect(0, 32, 92, 5, "#C9BFB0")        # vereda
    for xx in range(0, 92, 7):
        cv.put(xx, 33, "#B5AB9C")
        cv.put(xx + 3, 35, "#B5AB9C")
    cv.rect(0, 37, 92, 1, "#EDE6DA")        # cordón
    cv.rect(0, 38, 92, 1, "#8A8494")
    cv.rect(0, 39, 92, 13, "#5E5A6E")       # asfalto
    for xx in range(0, 92, 3):
        cv.put(xx, 40 + (xx * 7) % 11, "#6E6A80")
    for xx in range(2, 92, 16):
        cv.rect(xx, 50, 8, 1, "#E8D8A0")
    cv.rect(80, 12, 1, 22, "#3B3560")       # farol
    cv.rect(78, 11, 5, 2, "#3B3560")
    cv.put(80, 13, "#FFE07A")
    return cv


def window():
    """Marco, parante, persiana enrollada arriba y reflejo (va encima del auto)."""
    cv = Cv(100, 60)
    W = WOOD
    cv.rect(0, 0, 100, 60, W[2])
    cv.clear(4, 4, 96, 56)
    cv.rect(0, 0, 100, 1, W[4])
    cv.rect(0, 0, 1, 60, W[4])
    cv.rect(99, 0, 1, 60, W[0])
    cv.rect(3, 3, 94, 1, W[0])
    cv.rect(3, 3, 1, 54, W[0])
    cv.rect(96, 3, 1, 54, W[4])
    cv.rect(3, 56, 94, 1, W[4])
    cv.rect(0, 57, 100, 3, W[3])            # alféizar
    cv.rect(0, 57, 100, 1, W[5])
    for y in range(4, 14, 2):               # persiana enrollada
        cv.rect(4, y, 92, 1, "#EDE6DA")
        cv.rect(4, y + 1, 92, 1, "#C9BFB0")
    cv.rect(4, 14, 92, 1, "#94552A")
    cv.rect(20, 15, 1, 5, "#C9BFB0")        # cordón
    cv.put(20, 20, "#94552A")
    cv.rect(48, 4, 4, 52, W[2])             # parante
    cv.rect(48, 4, 1, 52, W[4])
    cv.rect(51, 4, 1, 52, W[0])
    for k in range(12):                     # reflejo del vidrio
        for x0, wd in ((8, 3), (14, 1), (58, 3), (64, 1)):
            for t in range(wd):
                x, y = x0 + k + t, 54 - k * 3
                for yy in (y, y - 1, y - 2):
                    if 15 < yy < 56 and not (48 <= x <= 51):
                        cv.px[x, yy] = (255, 255, 255, 56)
    return cv


def patrol_body(f):
    """Patrullero de costado (frente a la izquierda): sedán blanco con franja azul y
    celeste, baliza roja/azul en el techo. 76x30."""
    cv = Cv(76, 30)
    white = ["#9A97AE", "#C9C7DA", "#EDEBF5", "#FFFFFF", "#FFFFFF"]
    body = [(2, 19), (4, 15), (16, 13), (24, 7), (50, 7), (60, 13), (72, 14), (74, 19), (73, 25), (2, 25)]
    shade_poly(cv, body, white, 2)
    glass = ["#2A3358", "#3E4F80", "#6F8CC0", "#BDE2FF"]
    cv.poly([(19, 13), (26, 8.5), (36, 8.5), (36, 13)], glass[1])
    cv.poly([(38, 8.5), (49, 8.5), (55, 13), (38, 13)], glass[1])
    cv.line([(20, 13), (26, 9)], glass[3])
    cv.line([(39, 12), (42, 9)], glass[2])
    cv.line([(41, 12), (44, 9)], glass[2])
    cv.rect(36, 8, 2, 6, white[1])             # parante B
    cv.rect(3, 17, 70, 3, "#2F5FA0")           # franja azul + celeste
    cv.rect(3, 17, 70, 1, "#4E8FD8")
    cv.rect(3, 20, 70, 1, "#74ACDF")
    for i, x in enumerate(range(26, 50, 3)):   # "POLICIA" sugerido
        cv.rect(x, 18, 2, 2, "#FFFFFF" if i % 2 == 0 else "#EDEBF5")
    cv.ell(31, 15, 1.2, 1.2, "#F6B40E")        # escudo en la puerta
    cv.line([(37, 14), (37, 24)], white[0])    # puertas
    cv.line([(55, 14), (56, 24)], white[0])
    cv.rect(33, 15, 3, 1, white[0])
    cv.rect(51, 15, 3, 1, white[0])
    cv.rect(21, 11, 3, 2, white[0])            # espejo
    cv.rect(1, 21, 6, 3, "#3B3560")            # paragolpes
    cv.rect(70, 21, 5, 3, "#3B3560")
    cv.rect(2, 15, 4, 2, "#FFF4C0")            # faro
    cv.put(2, 15, "#FFFFFF")
    cv.rect(71, 15, 3, 3, "#B8323C")           # luz trasera
    cv.put(71, 15, "#F08C8F")
    for wx in (15, 61):                        # pasarruedas
        for y in range(17, 30):
            for x in range(wx - 8, wx + 9):
                if ((x - wx) / 7.5) ** 2 + ((y - 25) / 7.5) ** 2 <= 1:
                    cv.px[x, y] = (0, 0, 0, 0)
        for a in range(0, 181, 6):
            ang = math.radians(180 + a)
            cv.put(int(round(wx + math.cos(ang) * 8)), int(round(25 + math.sin(ang) * 8)), white[0])
    cv.clear(0, 26, 76, 30)
    cv.rect(24, 24, 29, 1, "#3B3560")          # zócalo
    cv.rect(30, 4, 16, 3, "#3B3560")           # baliza
    red_on = f == 0
    cv.rect(31, 2, 7, 3, "#FF5060" if red_on else "#7A1E24")
    cv.rect(38, 2, 7, 3, "#5090FF" if not red_on else "#1F3F6E")
    if red_on:
        cv.rect(32, 2, 3, 1, "#FFC4C4")
    else:
        cv.rect(40, 2, 3, 1, "#D0E8FF")
    cv.rect(37, 2, 2, 3, "#C9C7DA")
    cv.line([(56, 7), (60, 0)], "#3B3560")     # antena
    cv.outline(OUTL, "#6E6B8C")
    return cv


def wheel(f):
    cv = Cv(13, 13)
    cv.ell(6, 6, 6, 6, "#1E1626")
    cv.ell(6, 6, 5, 5, "#2E2B48")
    cv.ell(6, 6, 3, 3, "#9B98B5")
    cv.ell(6, 6, 2, 2, "#C9C7DA")
    for k in range(5):
        a = f * (math.tau / 5 / 4) + k * math.tau / 5
        cv.put(int(round(6 + math.cos(a) * 2.6)), int(round(6 + math.sin(a) * 2.6)), "#4A4766")
    cv.put(6, 6, "#4A4766")
    cv.put(4, 4, "#F0EEE6")
    return cv


def desk():
    """Madera de escritorio (se repite en x cada 64): tablas con vetas largas y
    rectas, poco contraste (es fondo), un nudo por tabla."""
    cv = Cv(64, 48)
    W = ["#5E321C", "#6D3A20", "#784226", "#82492A", "#8E5230"]
    rnd = random.Random(8)
    for plank in range(4):
        y0 = plank * 12
        base = 2 if plank % 2 == 0 else 3
        cv.rect(0, y0, 64, 12, W[base])
        for k in range(7):                       # vetas: trazos horizontales largos
            yy = y0 + 2 + rnd.randint(0, 8)
            x0 = rnd.randint(0, 63)
            ln = rnd.randint(14, 40)
            col = W[base - 1] if k % 3 else W[base + 1]
            for i in range(ln):
                cv.put((x0 + i) % 64, yy + (1 if 8 < i < 14 else 0), col)
        kx = rnd.randint(8, 56)                  # nudo
        cv.ell(kx, y0 + 6, 2.5, 1.2, W[0])
        cv.put(kx, y0 + 6, W[1])
        cv.rect(0, y0, 64, 1, W[0])              # junta entre tablas
        cv.rect(0, y0 + 1, 64, 1, W[4])
    return cv


def blotter():
    cv = Cv(116, 140)
    g = ["#1E4A30", "#2E6A44", "#3A7E52", "#4E9466"]
    cv.rect(0, 0, 116, 140, g[1])
    rnd = random.Random(2)
    for i in range(500):
        cv.put(rnd.randint(0, 115), rnd.randint(0, 139), g[0] if i % 3 else g[2])
    cv.rect(2, 2, 112, 1, g[3])
    cv.rect(2, 137, 112, 1, g[0])
    for cx, cy, sx, sy in ((0, 0, 1, 1), (115, 0, -1, 1), (0, 139, 1, -1), (115, 139, -1, -1)):
        for k in range(18):
            for t in range(18 - k):
                cv.put(cx + sx * t, cy + sy * k, "#6D3A20" if (t + k) < 16 else "#94552A")
        for t in range(18):
            cv.put(cx + sx * t, cy + sy * (17 - t), "#C88555")
    for x in range(20, 96, 3):
        cv.put(x, 5, g[3])
        cv.put(x, 134, g[3])
    for y in range(20, 120, 3):
        cv.put(5, y, g[3])
        cv.put(110, y, g[3])
    cv.outline(OUTL)
    return cv


def lamp():
    cv = Cv(30, 30)
    shade_poly(cv, [(3, 10), (8, 4), (22, 4), (27, 10), (27, 12), (3, 12)], ["#123A24", "#1E5A36", "#2E7D4F", "#3F9E5E", "#67D08E", "#B6F0B0"], 3)
    cv.rect(3, 12, 25, 1, "#FFE07A")
    cv.line([(8, 5), (21, 5)], "#B6F0B0")
    cv.rect(13, 13, 2, 11, BRASS[2])
    cv.rect(13, 13, 1, 11, BRASS[3])
    cv.ell(14, 26, 8, 2.5, BRASS[1])
    cv.ell(13, 25, 5, 1.5, BRASS[3])
    cv.rect(20, 13, 1, 6, BRASS[1])
    cv.put(20, 19, BRASS[3])
    cv.outline(OUTL, "#8E461F")
    return cv


def phone():
    cv = Cv(28, 18)
    b = ["#1E1626", "#2E2B48", "#4A4766", "#6E6B8C"]
    cv.poly([(2, 8), (26, 8), (24, 17), (4, 17)], b[1])
    cv.line([(3, 8), (25, 8)], b[3])
    cv.poly([(1, 4), (6, 1), (22, 1), (27, 4), (26, 7), (21, 6), (7, 6), (2, 7)], b[2])
    cv.line([(6, 1), (22, 1)], b[3])
    for i in range(3):
        for j in range(3):
            cv.put(10 + i * 3, 10 + j * 2, "#C9C7DA")
    cv.rect(19, 10, 4, 3, "#D5576E")
    cv.outline(OUTL)
    return cv


def mug():
    cv = Cv(12, 13)
    cv.rect(1, 2, 8, 10, "#EDE6DA")
    cv.rect(1, 2, 2, 10, "#FFFFFF")
    cv.rect(7, 2, 2, 10, "#C9BFB0")
    cv.ell(5, 2, 3.5, 1, "#6D3A20")
    cv.rect(3, 5, 4, 3, "#2F5FA0")
    cv.rect(9, 4, 2, 1, "#C9BFB0")
    cv.rect(10, 4, 1, 5, "#C9BFB0")
    cv.rect(9, 8, 2, 1, "#C9BFB0")
    cv.outline(OUTL, "#8E461F")
    return cv


def stamp_pad():
    cv = Cv(24, 16)
    cv.rect(1, 9, 14, 6, "#3B3560")
    cv.rect(2, 10, 12, 4, "#B8323C")
    cv.rect(2, 10, 12, 1, "#E85060")
    cv.rect(16, 11, 7, 3, "#2E2B48")
    cv.rect(18, 4, 3, 7, WOOD[3])
    cv.ell(19, 3, 2.5, 2.5, WOOD[4])
    cv.put(18, 2, WOOD[5])
    cv.outline(OUTL, "#8E461F")
    return cv


# ================================================================== documentos
def paper_base(cv, red):
    if red:
        r = ["#7A2028", "#A8343E", "#C44A54", "#D5576E", "#E27482"]
    else:
        r = ["#B9AE9C", "#DDD4C4", "#F1EBDF", "#FAF6EE", "#FFFFFF"]
    cv.rect(2, 2, 92, 116, r[3])
    rnd = random.Random(31 if red else 17)
    for i in range(420):                         # fibras del papel
        cv.put(rnd.randint(3, 92), rnd.randint(3, 116), r[2] if i % 4 else r[4])
    cv.rect(2, 2, 92, 1, r[4])
    cv.rect(2, 2, 1, 116, r[4])
    cv.rect(2, 117, 92, 1, r[1])
    cv.rect(93, 2, 1, 116, r[1])
    for k in range(9):                           # esquina doblada
        cv.clear(85 + k, 109 + k, 94, 110 + k)
        cv.rect(85, 109 + k, k + 1, 1, r[1])
    cv.line([(85, 109), (93, 117)], r[0])
    return r


def text_lines(cv, x, y0, y1, w, col, step=5, seed=1, indent=True):
    rnd = random.Random(seed)
    y = y0
    while y < y1:
        x0 = x
        ln = w - rnd.randint(0, max(1, w // 3))
        if indent and rnd.random() < 0.18:
            x0 += 6
            ln -= 6
        xx = x0
        while xx < x0 + ln:
            wl = rnd.randint(3, 9)
            cv.rect(xx, y, min(wl, x0 + ln - xx), 1, col)
            xx += wl + 2
        y += step


def signature(cv, x, y, ink, seed):
    rnd = random.Random(seed)
    pts = [(x + i * 1.8, y + math.sin(i * 1.3 + seed) * 3 + rnd.uniform(-1, 1)) for i in range(16)]
    cv.line(pts, ink)
    cv.line([(x + 2, y + 4), (x + 28, y + 2)], ink)


def seal(cv, cx, cy, r, col, light):
    for a in range(60):
        ang = a / 60 * math.tau
        cv.put(int(round(cx + math.cos(ang) * r)), int(round(cy + math.sin(ang) * r)), col)
        cv.put(int(round(cx + math.cos(ang) * (r - 2))), int(round(cy + math.sin(ang) * (r - 2))), col)
    for k in range(12):
        ang = k / 12 * math.tau
        cv.put(int(round(cx + math.cos(ang) * (r - 1))), int(round(cy + math.sin(ang) * (r - 1))), light)
    cv.ell(cx, cy, r * 0.35, r * 0.35, col)


def crest(cv, x, y):
    """Escudo oficial chiquito (óvalo celeste y blanco con sol)."""
    cv.ell(x + 5, y + 6, 5, 6, "#2F5FA0")
    cv.ell(x + 5, y + 6, 4, 5, "#74ACDF")
    cv.rect(x + 1, y + 6, 9, 3, "#FFFFFF")
    cv.ell(x + 5, y + 1, 2, 1.5, "#F6B40E")


def document(red, kind):
    """kind 0 formulario · 1 factura/libro con tabla · 2 certificado/pagaré con sello y cinta.
    La franja de arriba (y 8-22, x 10-72) queda libre para el título que escribe el juego."""
    cv = Cv(96, 120)
    r = paper_base(cv, red)
    ink = "#4A1418" if red else "#4A4766"
    seed = kind * 7 + (100 if red else 0)
    if not red:
        crest(cv, 78, 7)
        cv.rect(6, 25, 84, 1, "#2F5FA0")
        cv.rect(6, 27, 84, 1, "#74ACDF")
    else:
        cv.rect(6, 25, 84, 1, r[0])
        cv.rect(6, 27, 84, 1, r[1])
    if kind == 0:
        for i, y in enumerate(range(36, 84, 10)):
            cv.rect(8, y, 14, 1, ink)
            fw = 60 - (i % 3) * 8
            cv.rect(26, y - 4, fw, 6, r[4] if not red else r[2])
            cv.rect(26, y + 1, fw, 1, r[1] if not red else r[0])
            text_lines(cv, 28, y - 2, y - 1, 30 - (i * 5) % 18, r[0] if not red else r[4], seed=seed + i)
        for j in range(3):            # casillas tildadas
            cv.rect(8 + j * 26, 88, 5, 5, ink)
            cv.rect(9 + j * 26, 89, 3, 3, r[3])
            if j != 1:
                cv.line([(9 + j * 26, 90), (10 + j * 26, 92), (13 + j * 26, 87)], "#2F5FA0" if not red else "#1E1626")
            cv.rect(15 + j * 26, 90, 8, 1, ink)
        signature(cv, 50, 104, "#2F5FA0" if not red else "#1E1626", seed)
        cv.rect(48, 110, 30, 1, ink)
        if not red:
            seal(cv, 22, 104, 8, "#4E8FD8", "#8FC4FF")
    elif kind == 1:
        cv.rect(6, 32, 84, 6, r[1] if not red else r[0])
        for x in (6, 50, 66, 89):
            cv.rect(x, 32, 1, 58, ink if not red else r[0])
        for i, y in enumerate(range(38, 88, 6)):
            cv.rect(6, y + 5, 84, 1, r[1] if not red else r[2])
            text_lines(cv, 9, y + 2, y + 3, 36 - (i * 7) % 14, ink, seed=seed + i)
            cv.rect(54, y + 2, 8, 1, ink)
            cv.rect(70, y + 2, 4 + (i * 5) % 14, 1, ink)
        cv.rect(54, 92, 36, 8, r[4] if not red else r[0])
        cv.rect(54, 92, 36, 1, ink)
        cv.rect(58, 95, 6, 2, ink)
        cv.rect(70, 95, 16, 2, ink)
        rnd = random.Random(seed)
        x = 8
        while x < 44:                 # código de barras
            w = rnd.choice((1, 1, 2))
            cv.rect(x, 102, w, 10, "#1E1626")
            x += w + rnd.choice((1, 1, 2))
    else:
        g = "#C9A64A" if not red else "#F6B40E"
        for x in range(5, 91, 2):     # guarda ornamental
            cv.put(x, 5 + (x // 2) % 2, g)
            cv.put(x, 113 - (x // 2) % 2, g)
        for y in range(5, 108, 2):
            cv.put(4 + (y // 2) % 2, y, g)
            cv.put(91 - (y // 2) % 2, y, g)
        text_lines(cv, 14, 34, 78, 68, ink, step=6, seed=seed, indent=False)
        cv.ell(70, 94, 9, 9, g)
        cv.ell(70, 94, 6, 6, "#FFE07A" if not red else "#FFF4C0")
        cv.ell(69, 93, 2, 2, "#FFFFFF")
        rib = "#D5576E" if not red else "#2F5FA0"
        cv.poly([(64, 102), (60, 114), (64, 111), (67, 114), (68, 102)], rib)
        cv.poly([(72, 102), (73, 114), (76, 111), (80, 114), (76, 102)], rib)
        signature(cv, 14, 98, ink, seed)
        cv.rect(12, 104, 34, 1, ink)
    if red:
        if kind != 1:                 # mancha de café
            for a in range(50):
                ang = a / 50 * math.tau
                cv.put(int(round(74 + math.cos(ang) * 8)), int(round(52 + math.sin(ang) * 7)), r[1])
        for k in range(44):           # sello "CONFIDENCIAL" cruzado
            x, y = 24 + k, (72 if kind == 0 else 84) - k * 0.45
            if k % 5:
                cv.put(int(x), int(y), "#1E1626")
                cv.put(int(x), int(y) - 6, "#1E1626")
            if k % 3 == 0:
                cv.put(int(x), int(y) - 3, "#1E1626")
    # clip metálico arriba a la derecha
    cv.line([(67, 0), (67, 9), (70, 9), (70, 2)], "#9B98B5")
    cv.line([(68, 1), (68, 7)], "#C9C7DA")
    cv.outline(OUTL, "#8E461F")
    return cv


def shredder():
    """Trituradora de oficina (papeles ROJOS): cabezal de acero con boca de
    alimentación y rodillos dentados, panel con perilla de 3 posiciones, LED y
    rejilla de ventilación; cesto rojo con ventana donde se ven las tiras
    enruladas, manija, etiqueta de advertencia, flecha <- en relieve y ruedas."""
    cv = Cv(64, 60)
    RED = ["#4A1418", "#6E1E26", "#953730", "#B8323C", "#D5576E", "#F08C8F", "#FFC4C4"]
    # --- cesto rojo (redondeado abajo)
    shade_poly(cv, [(7, 19), (57, 19), (57, 52), (54, 55), (10, 55), (7, 52)], RED, 3)
    cv.rect(8, 20, 48, 1, RED[5])
    cv.rect(9, 54, 46, 1, RED[1])
    # ventana con tiras enruladas (blancas y rojas) apiladas
    cv.rect(14, 24, 36, 17, "#2A1218")
    cv.rect(14, 24, 36, 1, RED[1])
    rnd = random.Random(6)
    for i in range(70):
        x = rnd.randint(15, 48)
        y = rnd.randint(31, 39) + (1 if x % 7 == 0 else 0)
        col = ["#EDE6DA", "#FFFFFF", "#F08C8F", "#D5576E", "#C9BFB0"][i % 5]
        cv.put(x, y, col)
        if i % 3 == 0:
            cv.put(x + 1, y - 1, col)
    for x in range(15, 49):
        cv.put(x, 40, ["#EDE6DA", "#D5576E", "#C9BFB0"][x % 3])
    for y in range(26, 30):                              # tiras que caen de la boca
        for x in (22, 29, 37, 43):
            cv.put(x + (y % 2), y, "#EDE6DA" if x != 37 else "#F08C8F")
    for k in range(4):                                   # brillo del acrílico (arriba-izq.)
        cv.put(15 + k, 29 - k, "#8A7A88")
        cv.put(16 + k, 29 - k, "#5A4A58")
    cv.rect(14, 41, 36, 1, RED[5])
    # flecha <- en relieve
    cv.rect(26, 45, 16, 4, RED[1])
    cv.rect(26, 44, 16, 4, "#FFFFFF")
    for k in range(5):
        cv.rect(21 + k, 46 - k, 1, 2 * k + 1, "#FFFFFF")
        cv.put(21 + k, 46 + k + 1, RED[1])
    # manija y etiqueta de advertencia
    cv.rect(46, 44, 7, 3, RED[0])
    cv.rect(46, 44, 7, 1, RED[1])
    cv.rect(10, 44, 7, 6, "#F6B40E")
    for k in range(4):
        cv.put(11 + k, 48 - k, "#3D1B0B")
        cv.put(12 + k, 49 - k, "#3D1B0B")
    for wx in (13, 51):                                  # ruedas
        cv.ell(wx, 57, 2.5, 2, "#2E2B48")
        cv.put(wx - 1, 56, "#6E6B8C")
    # --- cabezal de acero
    shade_poly(cv, [(3, 5), (61, 5), (61, 19), (3, 19)], STEEL, 4)
    cv.rect(3, 5, 58, 1, STEEL[6])
    cv.rect(4, 17, 56, 2, STEEL[1])
    cv.rect(8, 8, 40, 5, STEEL[2])                       # boca con labios
    cv.rect(9, 9, 38, 3, "#120E18")
    cv.rect(9, 9, 38, 1, STEEL[0])
    for x in range(10, 46, 2):                           # dientes del rodillo
        cv.put(x, 11, STEEL[4])
        cv.put(x + 1, 10, STEEL[3])
    cv.rect(8, 13, 40, 1, STEEL[5])
    cv.rect(50, 8, 9, 7, STEEL[2])                       # panel
    cv.rect(50, 8, 9, 1, STEEL[1])
    cv.rect(51, 10, 4, 3, "#2E2B48")
    cv.rect(51, 10, 2, 3, STEEL[5])                      # perilla en AUTO
    cv.put(56, 10, "#67D08E")
    cv.put(57, 10, "#B6F0B0")                            # LED encendido
    cv.put(56, 13, STEEL[4])
    cv.put(57, 13, STEEL[4])
    for x in range(10, 46, 3):
        cv.rect(x, 15, 2, 1, STEEL[1])                   # rejilla
    cv.rect(26, 6, 8, 1, STEEL[4])                       # chapita de marca
    cv.outline(OUTL, "#8E461F")
    return cv


def folder():
    """Bandeja de ENTRADA (papeles BLANCOS): bandeja de madera con encastres,
    pila de hojas con sello verde y clip, carpeta manila con pestaña rotulada,
    escudo azul con estrella dorada, flecha -> y portaetiqueta de bronce."""
    cv = Cv(64, 56)
    A = ["#8A5E14", "#A8781A", "#C99A2E", "#E8B84A", "#F6D27A", "#FFF0B8"]
    for i, (x, y, w) in enumerate(((10, 2, 44), (13, 4, 42), (8, 6, 46))):
        cv.rect(x, y, w, 10, "#FAF6EE" if i != 1 else "#F1EBDF")
        cv.rect(x, y, w, 1, "#FFFFFF")
        cv.rect(x + w - 1, y, 1, 10, "#DDD4C4")
    for y in (9, 11):
        cv.rect(12, y, 26, 1, "#C9BFB0")
    cv.rect(40, 8, 9, 4, "#67D08E")                      # sellito verde
    cv.rect(41, 9, 7, 2, "#B6F0B0")
    cv.line([(51, 3), (51, 9), (53, 9), (53, 4)], "#9B98B5")   # clip
    cv.rect(6, 10, 22, 6, A[3])                          # pestaña rotulada
    cv.rect(6, 10, 22, 1, A[5])
    cv.rect(9, 12, 14, 2, "#FFF6E6")
    cv.rect(10, 12, 9, 1, "#7A4A12")
    shade_poly(cv, [(4, 14), (60, 14), (60, 44), (4, 44)], A, 2)
    cv.rect(4, 14, 56, 1, A[5])
    cv.rect(5, 15, 1, 28, A[4])
    shade_poly(cv, [(20, 18), (44, 18), (44, 30), (32, 36), (20, 30)], ["#1F3F6E", "#2F5FA0", "#3E74B8", "#4E8FD8", "#8FC4FF", "#D0E8FF"], 3)
    for dx, dy in ((0, -2), (-2, 0), (2, 0), (-1, 1), (1, 1), (0, 0), (0, -1), (-1, 0), (1, 0)):
        cv.put(32 + dx, 22 + dy, "#F6B40E")              # estrella
    cv.put(32, 21, "#FFE07A")
    cv.rect(25, 27, 11, 3, "#FFFFFF")                    # flecha ->
    for k in range(4):
        cv.rect(39 - k, 28 - k, 1, 2 * k + 1, "#FFFFFF")
    shade_poly(cv, [(1, 36), (63, 36), (62, 54), (2, 54)], WOOD, 3)   # bandeja
    cv.rect(1, 36, 62, 1, WOOD[5])
    cv.rect(2, 37, 60, 1, WOOD[4])
    for y in range(40, 53, 4):                            # vetas
        cv.rect(6 + (y * 7) % 11, y, 14, 1, WOOD[2])
        cv.rect(38 - (y * 5) % 9, y + 1, 16, 1, WOOD[2])
    for y in (39, 44, 49):                                # encastres
        cv.rect(2, y, 3, 2, WOOD[1])
        cv.rect(59, y, 3, 2, WOOD[1])
    cv.rect(22, 42, 20, 8, "#7A4A12")                     # portaetiqueta de bronce
    cv.rect(23, 43, 18, 6, "#E8B84A")
    cv.rect(23, 43, 18, 1, "#FFE07A")
    cv.rect(25, 45, 14, 2, "#FFF6E6")
    for x in range(26, 38, 2):
        cv.put(x, 45, "#3D1B0B")
    cv.outline(OUTL, "#8E461F")
    return cv


# ================================================================== salida
def main():
    os.makedirs(OUT, exist_ok=True)
    sheet([pistol_hand(i) for i in range(3)]).save("pistol_hand.png")
    sheet([bag_hand(False), bag_hand(True)]).save("bag_hand.png")
    sheet([muzzle(i) for i in range(4)]).save("muzzle.png")
    sheet([impact(i) for i in range(4)]).save("impact.png")
    sheet([smoke(i) for i in range(5)]).save("smoke.png")
    sheet([shell(i) for i in range(4)]).save("shell.png")
    hole().save("hole2.png")
    mag().save("mag.png")
    floor_tiles().save("floor_tiles.png")
    rug().save("rug.png")
    shelf_seg().save("shelf.png")
    sheet([beacon(True), beacon(False)]).save("beacon.png")
    plant().save("plant.png")
    boxes().save("boxes.png")
    office_wall().save("office_wall.png")
    street().save("street.png")
    window().save("window.png")
    sheet([patrol_body(0), patrol_body(1)]).save("patrol_body.png")
    sheet([wheel(i) for i in range(4)]).save("wheel.png")
    desk().save("desk.png")
    blotter().save("blotter.png")
    lamp().save("lamp.png")
    phone().save("phone.png")
    mug().save("mug.png")
    stamp_pad().save("stamp_pad.png")
    for k in range(3):
        document(False, k).save("doc_white_%d.png" % k)
        document(True, k).save("doc_red_%d.png" % k)
    shredder().save("shredder.png")
    folder().save("folder.png")
    print("arte 12.1 de minijuegos en", os.path.normpath(OUT))


if __name__ == "__main__":
    main()
