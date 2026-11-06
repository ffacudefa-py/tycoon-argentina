"""Animaciones de trabajo 15.0: qué hace cada empleado según el rubro del negocio.

8 cuadros (32x48) por acción y por empleado, con el mismo estilo que
chars3.py (lo reusa: piernas, torso, cabeza, pelo, cara, brazos). Pensadas
para leerse de lejos y entre mucha gente: brazos que suben por encima de la
cabeza, herramientas grandes y una partícula clara en el golpe (tierra,
chispa, chorro, harina).

Acciones (business_scene.gd elige según las etiquetas del negocio):
  cosechar  azada que sube y baja, tierra que salta       (campo, agro)
  martillo  martillazo sobre yunque, chispas               (fabrica, industria)
  servir    inclina la botella y llena el vaso             (bebida, vino, lacteo)
  amasar    empuja la masa con las dos manos, harina       (comida, panaderia)
  carnear   cuchillo que corta sobre la tabla              (ganaderia)
  cajon     levanta un cajón de fruta sobre la cabeza      (fruta)
  bolsa     carga una bolsa al hombro y la deja            (infusion: yerba)
  cobrar    entrega el vuelto: moneda que salta al cliente (el resto)

Salida: assets/personajes/work/worker_<n>_<acción>.png (256x48) y la variante
de mostrador worker_<n>_<acción>_c.png: sin mesa/yunque/tabla/caja propias (la
superficie es el mostrador; business_scene sube al empleado COUNTER_LIFT px
para que las manos queden por encima).
Uso: python3 tools/art/work_anims15.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from px2 import Canvas, sheet  # noqa: E402
import palette11  # noqa: E402,F401
from palette11 import ramp  # noqa: E402
import chars3 as C  # noqa: E402

FRAMES = 8
SURFACE = [True]          ## False al dibujar la variante de mostrador
ACTIONS = ["cosechar", "martillo", "servir", "amasar", "carnear", "cajon", "bolsa", "cobrar"]


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def wave(f, peak):
    """0 → 1 → 0 a lo largo de la vuelta, con el máximo en el cuadro `peak`."""
    if f <= peak:
        return ease(f / max(peak, 1))
    return ease(1.0 - (f - peak) / max(FRAMES - peak, 1))


def dust(cv, x, y, n, colors=("i_marron2", "i_marron3")):
    for k in range(n):
        cv.put(x + (k * 3) % 7 - 3, y - (k % 3), colors[k % len(colors)])


def sparks(cv, x, y, big):
    pts = [(-3, -2), (3, -3), (-2, -4), (4, 0), (-4, 1)] if big else [(-2, -2), (2, -2)]
    for dx, dy in pts:
        cv.put(x + dx, y + dy, "i_amarillo2")
    cv.put(x, y - 1, "iWh")


# ------------------------------------------------------------------ acciones
# Cada una devuelve (oy, brazo izq. (dx, dy) o None, brazo der. (dx, dy), dibujo
# del accesorio antes del brazo derecho, dibujo después).

def a_cosechar(f, x0, xr):
    up = wave(f, 3)                                 # sube la azada hasta el cuadro 3
    hit = f in (5, 6)
    oy = 1 if hit else 0
    hx = round(3 + 2 * up)                          # la mano va por el costado, no tapa la cara
    hy = round(5 - 15 * up)

    def prop(cv):
        sx, sy = xr + hx + 2, 28 + oy + hy + 1
        # arriba: la hoja apunta hacia atrás; abajo: clavada en la tierra adelante
        tx, ty = (sx + 2, sy - 8) if up > 0.5 else (sx + 5, sy + 9)
        steps = max(abs(tx - sx), abs(ty - sy), 1)
        for i in range(steps + 1):
            px, py = sx + round((tx - sx) * i / steps), sy + round((ty - sy) * i / steps)
            cv.put(px, py, "i_marron1")
            cv.put(px + 1, py, "i_marron2")
        if up > 0.5:
            cv.rect(tx - 3, ty - 2, 5, 3, "i_gris2")
            cv.hline(tx - 3, ty - 2, 5, "iWh")
        else:
            cv.rect(tx - 1, ty, 3, 4, "i_gris2")
            cv.vline(tx - 1, ty, 4, "iWh")
        if hit:
            dust(cv, 29, 44, 8 if f == 5 else 5)
    return oy, (2, 4), (hx, hy), None, prop


def a_martillo(f, x0, xr):
    up = wave(f, 3)
    hit = f in (5, 6)
    oy = 1 if hit else 0
    hx = round(4 - 2 * up)
    hy = round(3 - 15 * up)

    def under(cv):
        if not SURFACE[0]:
            return
        cv.rect(22, 38, 9, 3, "i_noche0")            # yunque
        cv.rect(23, 37, 7, 1, "i_gris1")
        cv.rect(25, 41, 3, 4, "i_noche0")

    def prop(cv):
        sx, sy = xr + hx + 1, 28 + oy + hy
        cv.vline(sx + 1, sy - 5, 6, "i_marron1")    # mango
        cv.rect(sx - 1, sy - 8, 6, 3, "i_gris1")    # cabeza del martillo
        cv.hline(sx - 1, sy - 8, 6, "i_gris3")
        if hit:
            sparks(cv, 26, 36, f == 5)
    return oy, (2, 6), (hx, hy), under, prop


def a_servir(f, x0, xr):
    tilt = wave(f, 4)                               # inclina la botella
    oy = 0

    def under(cv):
        # vaso en la mano izquierda, se va llenando
        gx, gy = 19, 33
        cv.rect(gx, gy, 4, 6, "iSw")
        level = round(tilt * 4)
        if level:
            cv.rect(gx, gy + 6 - level, 4, level, "i_rojo1")
        cv.vline(gx, gy, 6, "iWh")

    def prop(cv):
        bx, by = 23, 22 + round(tilt * 3)
        if tilt < 0.5:
            cv.rect(bx, by, 3, 9, "i_verde0")       # botella parada
            cv.rect(bx + 1, by - 3, 1, 3, "i_verde0")
            cv.put(bx, by + 1, "i_verde2")
        else:
            cv.rect(bx - 2, by + 2, 8, 3, "i_verde0")  # botella acostada
            cv.rect(bx - 4, by + 3, 2, 1, "i_verde0")
            cv.hline(bx - 1, by + 2, 6, "i_verde2")
            for k in range(round(tilt * 6)):        # chorro
                cv.put(bx - 4 - (k // 4), by + 4 + k, "i_rojo1")
    return oy, (4, 4), (4, -3 + round(tilt * 2)), under, prop


def a_amasar(f, x0, xr):
    push = wave(f, 4)
    oy = round(push)

    def under(cv):
        if SURFACE[0]:
            cv.rect(15, 38, 16, 3, "i_marron2")     # mesa
            cv.hline(15, 38, 16, "i_marron3")
            cv.vline(17, 41, 4, "i_marron0")
            cv.vline(29, 41, 4, "i_marron0")
        w = 10 + round(push * 4)                    # la masa se aplasta
        cv.ellipse(23, 36 + round(push), w // 2, 3 - round(push), "i_amarillo2")
        cv.ellipse(23, 35 + round(push), w // 2 - 1, 1, "i_amarillo3")
        cv.hline(23 - w // 2 + 2, 34 + round(push), w - 5, "iWh")

    def prop(cv):
        if f in (4, 5):
            for k in range(5):                      # nube de harina
                cv.put(19 + k * 2, 31 - (k % 2) * 2 - (f - 4), "iWh")
    return oy, (6, 5 + round(push * 2)), (2, 5 + round(push * 2)), under, prop


def a_carnear(f, x0, xr):
    up = wave(f, 3)
    hit = f in (5, 6)
    oy = 1 if hit else 0

    def under(cv):
        if SURFACE[0]:
            cv.rect(19, 38, 12, 3, "i_marron2")     # tabla
            cv.hline(19, 38, 12, "i_marron3")
        cv.ellipse(22, 36, 3, 2, "i_rojo1")         # pieza de carne
        cv.put(21, 35, "i_rojo3")

    def prop(cv):
        kx, ky = xr + 4, 28 + oy + round(5 - 14 * up)
        cv.rect(kx, ky - 7, 2, 7, "i_gris2")        # hoja grande
        cv.vline(kx, ky - 7, 7, "iWh")
        cv.rect(kx, ky, 2, 3, "i_marron0")
        if hit:
            cv.put(28, 35, "i_rojo1")
            cv.put(30, 34 - (f - 5), "i_rojo2")
    return oy, (4, 7), (3, round(4 - 14 * up)), under, prop


def a_cajon(f, x0, xr):
    lift = wave(f, 4)
    oy = 1 if f in (0, 7) else 0
    ly = round(6 - 16 * lift)

    def prop(cv):
        bx, by = 10, 30 + ly
        cv.rect(bx, by, 13, 7, "i_marron2")
        cv.hline(bx, by, 13, "i_marron3")
        cv.hline(bx, by + 3, 13, "i_marron1")
        for i in range(4):
            cv.ellipse(bx + 2 + i * 3, by - 1, 1, 1, ("i_rojo1", "i_amarillo1", "i_verde2", "i_naranja1")[i])
    return oy, (3, ly), (-3, ly), None, prop


def a_bolsa(f, x0, xr):
    up = wave(f, 4)
    oy = 1 if f in (0, 7) else 0

    def prop(cv):
        bx = 18 + round(up * 2)
        by = 34 - round(up * 14)
        cv.rect(bx, by, 10, 9, "iM")                  # bolsa de arpillera
        cv.rect(bx + 1, by + 1, 8, 7, "iA")
        cv.vline(bx + 9, by, 9, "iW")
        cv.hline(bx, by + 8, 10, "iW")
        cv.rect(bx + 3, by - 2, 4, 2, "iW")           # boca atada
        cv.rect(bx + 2, by + 3, 6, 3, "i_verde1")     # etiqueta de la yerba
        cv.hline(bx + 3, by + 4, 4, "i_amarillo1")
    return oy, None, (round(2 - up), round(5 - 13 * up)), None, prop


def a_cobrar(f, x0, xr):
    reach = wave(f, 3)
    oy = 0

    def prop(cv):
        if SURFACE[0]:
            cv.rect(19, 37, 12, 6, "i_noche1")      # caja registradora
            cv.rect(20, 35, 6, 2, "i_noche2")
            cv.rect(21, 38, 3, 2, "i_celeste2")
            cv.put(28, 38, "i_rojo1")
        # moneda: sale de la mano y salta hacia el cliente
        if 2 <= f <= 6:
            t = (f - 2) / 4.0
            cx = 25 + round(t * 6)
            cy = 30 - round(math.sin(t * math.pi) * 8)
            cv.ellipse(cx, cy, 2, 2, "i_amarillo1")
            cv.put(cx - 1, cy - 1, "i_amarillo3")
            if f == 4:
                C.star(cv, cx + 3, cy - 3)
    return oy, (5, 7), (round(3 + 3 * reach), round(4 - 6 * reach)), None, prop


ACTION_FN = {"cosechar": a_cosechar, "martillo": a_martillo, "servir": a_servir, "amasar": a_amasar,
             "carnear": a_carnear, "cajon": a_cajon, "bolsa": a_bolsa, "cobrar": a_cobrar}


def worker_action(spec, action, f):
    hair_r, style, cloth, pants, width, extra, skin_i, job = spec[:8]
    body = spec[8] if len(spec) > 8 else ""
    skin = C.SKINS[skin_i]
    cv = Canvas(C.FW, C.FH)
    x0 = 16 - width // 2
    xr = x0 + width - 1
    oy, left, right, under, prop = ACTION_FN[action](f, x0, xr)
    # brazo izquierdo detrás del cuerpo si cuelga; adelante si trabaja
    if left is None:
        C.arm(cv, x0 - 3, 28 + oy, -1, 7, cloth, skin)
    C.legs(cv, "idle", 0, pants, 0)
    C.torso(cv, cloth, extra, width, oy)
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
    C.head(cv, skin, oy)
    capped = C.hair(cv, hair_r, style, oy)
    C.face(cv, "work", f % 2, oy, extra, False)
    if capped:
        C.cap(cv, cloth if extra in ("delantal", "panuelo") else "rojo", oy)
    if under:
        under(cv)
    if left is not None:
        C.arm(cv, x0 - 1, 28 + oy, left[0], left[1], cloth, skin, True)
    C.arm(cv, xr, 28 + oy, right[0], right[1], cloth, skin, True)
    prop(cv)
    C.outline_pass(cv)
    C.shadow(cv, 0)
    return cv


def generate(out_root):
    d = os.path.join(out_root, "personajes", "work")
    os.makedirs(d, exist_ok=True)
    n = 0
    for i, spec in enumerate(C.WORKERS):
        for a in ACTIONS:
            for counter in (False, True):
                SURFACE[0] = not counter
                sheet([worker_action(spec, a, f) for f in range(FRAMES)]).save(
                    os.path.join(d, "worker_%d_%s%s.png" % (i, a, "_c" if counter else "")))
                n += 1
    SURFACE[0] = True
    print("animaciones de trabajo:", n, "en", d)


if __name__ == "__main__":
    generate(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets"))
