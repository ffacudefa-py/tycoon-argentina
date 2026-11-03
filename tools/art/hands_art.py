"""Manos antropomorfas para el minijuego del asalto (12.1).

Primitivas con volumen para pixel art: falanges como cápsulas con sombreado
cilíndrico (normal de esfera, luz arriba-izquierda y de frente), dorso de la
mano como elipsoide, nudillos, tendones, costuras y separación propia entre
dedos (borde oscuro de 1 px en cada pieza). Lo usan pistol_hand() y
bag_hand() de minigames_art2.py.
"""
import math

GLOVE = ["#17131D", "#211C29", "#2C2636", "#3A3346", "#4B4359", "#615873", "#7D7493"]
SKIN = ["#7A4234", "#9E5A45", "#C27A5E", "#E3A988", "#F3D2B6", "#FBE6D2"]
NAIL = "#F6D9CC"
LIGHT = (-0.42, -0.62, 0.66)          # arriba-izquierda y hacia el jugador
_L = math.sqrt(sum(c * c for c in LIGHT))
LIGHT = tuple(c / _L for c in LIGHT)


def _tone(ramp, nx, ny, bias=0.0):
    nz = math.sqrt(max(0.0, 1.0 - nx * nx - ny * ny))
    b = nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]       # -1..1
    v = (b * 0.5 + 0.5) * (len(ramp) - 1) + bias
    return ramp[max(0, min(len(ramp) - 1, int(round(v))))]


def capsule(cv, a, b, r, ramp, bias=0.0, knit=False, edge=True, r2=None):
    """Falange: cápsula de a a b con radio r (r2 en b: cono, p. ej. el dorso de
    la mano que se angosta hacia la muñeca), sombreada como un cilindro."""
    r1 = r
    r2 = r if r2 is None else r2
    r = max(r1, r2)
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy or 1e-6
    x0, x1 = int(min(ax, bx) - r - 1), int(max(ax, bx) + r + 2)
    y0, y1 = int(min(ay, by) - r - 1), int(max(ay, by) + r + 2)
    for y in range(y0, y1):
        for x in range(x0, x1):
            px, py = x + 0.5, y + 0.5
            u = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
            cx, cy = ax + dx * u, ay + dy * u
            ox, oy = px - cx, py - cy
            d = math.hypot(ox, oy)
            rl = r1 + (r2 - r1) * u
            if d > rl:
                continue
            nx, ny = ox / rl, oy / rl
            if edge and d > rl - 0.9:
                c = ramp[0]                       # separación con lo de atrás
            else:
                bb = bias - (1 if knit and (x + 2 * y) % 5 == 0 else 0)
                c = _tone(ramp, nx * 0.95, ny * 0.95, bb)
            cv.put(x, y, c)


def ellipsoid(cv, cx, cy, rx, ry, ang, ramp, bias=0.0, knit=False, edge=True):
    """Dorso de la mano: elipsoide rotado ang (radianes), con volumen."""
    ca, sa = math.cos(ang), math.sin(ang)
    R = int(max(rx, ry)) + 2
    for y in range(int(cy) - R, int(cy) + R + 1):
        for x in range(int(cx) - R, int(cx) + R + 1):
            px, py = x + 0.5 - cx, y + 0.5 - cy
            u = (px * ca + py * sa) / rx
            v = (-px * sa + py * ca) / ry
            q = u * u + v * v
            if q > 1.0:
                continue
            nx = (u * ca - v * sa) * 0.8
            ny = (u * sa + v * ca) * 0.8
            if edge and math.sqrt(q) > 1.0 - 1.0 / min(rx, ry):
                c = ramp[0]
            else:
                bb = bias - (1 if knit and (x + 2 * y) % 5 == 0 else 0)
                c = _tone(ramp, nx, ny, bb)
            cv.put(x, y, c)


def finger_chain(cv, pts, radii, skin_from, nail=True, knit=True):
    """Dedo de varias falanges (puntos articulados). Desde el segmento skin_from
    la piel queda al aire (guante sin dedos). Dibuja de la punta a la base para
    que la base (más cerca del nudillo) quede encima."""
    n = len(pts) - 1
    for i in reversed(range(n)):
        skin = i >= skin_from
        capsule(cv, pts[i], pts[i + 1], radii[i], SKIN if skin else GLOVE, bias=0.3 if skin else 0.0, knit=knit and not skin)
    # borde tejido donde termina el guante
    if 0 < skin_from <= n - 1:
        jx, jy = pts[skin_from]
        ax, ay = pts[skin_from - 1]
        r = radii[skin_from - 1]
        ang = math.atan2(jy - ay, jx - ax)
        nx, ny = -math.sin(ang), math.cos(ang)
        for t in range(-int(r) + 1, int(r)):
            cv.put(int(round(jx + nx * t)), int(round(jy + ny * t)), GLOVE[5] if t < 0 else GLOVE[3])
    for i in range(1, min(skin_from, n)):
        jx, jy = pts[i]
        cv.put(int(round(jx)), int(round(jy - radii[i] + 1.5)), GLOVE[6])     # brillo de la articulación
    if nail and skin_from <= n - 1:
        tx, ty = pts[-1]
        bx, by = pts[-2]
        ang = math.atan2(ty - by, tx - bx)
        r = radii[-1]
        fx, fy = math.cos(ang), math.sin(ang)
        px, py = -fy, fx
        if py > 0:
            px, py = -px, -py                     # la uña va del lado de la luz
        for k in range(2):
            cv.put(int(round(tx - fx * (k + 0.3) + px * (r - 1.3))), int(round(ty - fy * (k + 0.3) + py * (r - 1.3))), NAIL)


def knuckles(cv, pts, r=1.6):
    """Protector acolchado sobre los nudillos (guante táctico)."""
    for x, y in pts:
        capsule(cv, (x, y), (x, y), r + 0.6, GLOVE, bias=0.6)
        cv.put(int(x) - 1, int(y) - 1, GLOVE[6])


def stitches(cv, pts, color=GLOVE[5]):
    """Costura punteada a lo largo de una polilínea."""
    acc = 0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay) or 1.0
        steps = int(L)
        for s in range(steps):
            if (acc + s) % 3 == 0:
                cv.put(int(round(ax + (bx - ax) * s / L)), int(round(ay + (by - ay) * s / L)), color)
        acc += steps
