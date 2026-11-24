"""15.2: la chancleta de la abuela (reemplaza la pistola del asalto).

Para bajar la clasificación por edades (Play / IARC): en vez de dispararle a
los ladrones con un arma realista, el jugador les revolea chancletas de goma.

Salida en assets/pixel_art/minigames:
  chancla_hand.png  mano derecha (mismo guante y manga que la pistola) con la
                    chancleta levantada; 3 cuadros de 96x96, muñeca en (80,80)
                    como pistol_hand: 0 con chancleta · 1 recién tirada · 2 sin chancletas
  chancla.png       la chancleta volando (de costado, talón a la izquierda), 34x18
  chancla_icon.png  ícono del contador: 2 cuadros de 9x15 (llena / gastada)

Uso: python tools/art/chancla_art.py   (no toca los demás PNG del minijuego)
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import vol_art as V                # noqa: E402
import hands_vol as HV             # noqa: E402
import minigames_art2 as MA        # noqa: E402

# Ojota de goma celeste con tiras blancas (la clásica de la abuela).
V.MATS["rubber"] = dict(ramp=["#173A57", "#1F4E73", "#2A6692", "#3A80AE", "#5299C6", "#74B4DA", "#9CCDEA", "#C9E6F6"],
                        spec=0.35, pw=10, tex=None)
V.MATS["rubber_edge"] = dict(ramp=["#5E6670", "#7C858F", "#9AA3AC", "#B8C0C8", "#D6DCE2", "#EEF2F5"],
                             spec=0.2, pw=8, tex=None)
V.MATS["strap"] = dict(ramp=["#7E8794", "#A2ABB7", "#C4CCD6", "#DEE4EA", "#F2F5F8", "#FFFFFF"],
                       spec=0.6, pw=18, tex=None)


def _half_width(t):
    """Media anchura de la suela a lo largo (0 = talón, 1 = punta)."""
    keys = [(0.0, 0.0), (0.04, 0.72), (0.14, 0.86), (0.42, 0.66), (0.72, 1.0), (0.92, 0.86), (1.0, 0.0)]
    for (t0, w0), (t1, w1) in zip(keys, keys[1:]):
        if t <= t1:
            k = (t - t0) / (t1 - t0)
            k = k * k * (3 - 2 * k)
            return w0 + (w1 - w0) * k
    return 0.0


def _sole(heel, toe, width, n=28):
    """Contorno de la suela entre talón y punta (en coordenadas del cuadro)."""
    hx, hy = heel
    tx, ty = toe
    ax, ay = tx - hx, ty - hy
    ln = math.hypot(ax, ay)
    ux, uy = ax / ln, ay / ln
    px, py = -uy, ux
    left, right = [], []
    for i in range(n + 1):
        t = i / n
        w = _half_width(t) * width
        cx, cy = hx + ax * t, hy + ay * t
        left.append((cx + px * w, cy + py * w))
        right.append((cx - px * w, cy - py * w))
    return left + right[::-1], (ux, uy), (px, py)


def chancla_scene(sc, heel, toe, width, z=0.0, thick=(1.6, 2.2)):
    """Suela con canto blanco (el grosor de la goma) y las tiras en Y."""
    pts, (ux, uy), (px, py) = _sole(heel, toe, width)
    # canto: la misma suela corrida hacia abajo-derecha (se ve el espesor)
    dx, dy = thick
    sc.poly([(x + dx, y + dy) for x, y in pts], "rubber_edge", z=z, dome=1.5, soft=1.5)
    sc.poly(pts, "rubber", z=z + 1.2, dome=2.2, soft=2.0)
    hx, hy = heel
    ax, ay = toe[0] - hx, toe[1] - hy

    def at(t, side):
        w = _half_width(t) * width * side * 0.86
        return (hx + ax * t + px * w, hy + ay * t + py * w)
    post = (hx + ax * 0.8, hy + ay * 0.8)                       # el "dedo" entre los dedos del pie
    for side in (1, -1):                                        # tiras: del dedo a los costados
        a = at(0.58, side)
        mid = ((post[0] + a[0]) / 2 + ux * 1.0, (post[1] + a[1]) / 2 + uy * 1.0)
        sc.chain([post, mid, a], [1.25, 1.35, 1.25], ["strap", "strap"], z=z + 3.4)
    sc.ellipsoid(post[0], post[1], 1.6, 1.6, 0, "strap", z=z + 4.0, depth=1.2)


def chancla_hand(frame):
    """Mano con guante (la de la pistola, con el puño cerrado) y la chancleta
    agarrada del talón, levantada, con la punta hacia arriba a la izquierda."""
    cv = MA.Cv(96, 96)
    back, front = HV.pistol_hand_layers(frame, index_curled=True, warm=False)
    if frame == 0:
        sc = V.Scene(96, 96)
        # El talón queda dentro del puño (las falanges lo tapan); el eje sigue
        # la inclinación de la antigua empuñadura y sigue hacia arriba.
        chancla_scene(sc, (59.0, 63.0), (30.0, 6.0), 12.0)
        img = sc.render(outline=("#0E2236", "#3A80AE"))
        cv.paste(img, 0, 0)
    cv.paste(back, 0, 0)
    cv.paste(front, 0, 0)
    cv.outline("#120C0A", "#52607A")
    return cv


def chancla_fly():
    sc = V.Scene(34, 18)
    chancla_scene(sc, (2.5, 9.5), (31.5, 7.5), 6.6, thick=(0.9, 1.4))
    img = sc.render(outline=("#0E2236", "#3A80AE"))
    cv = MA.Cv(34, 18)
    cv.paste(img, 0, 0)
    return cv


def chancla_icon(full):
    """Ícono plano de 9x15 (vista de arriba): suela, canto y tiras."""
    cv = MA.Cv(9, 15)
    pts, _, _ = _sole((4.5, 14.0), (4.5, 1.0), 4.1, n=14)
    ramp = ["#2A6692", "#5299C6", "#9CCDEA"] if full else ["#4A4852", "#66646E", "#86848E"]
    strap = "#FFFFFF" if full else "#A8A6B0"
    cv.poly(pts, ramp[1])
    cv.poly([(x + 0.6, y + 0.6) for x, y in pts[len(pts) // 2:]], ramp[0])
    cv.line([(3, 3), (3, 6)], ramp[2])
    cv.line([(4, 4), (2, 7)], strap)
    cv.line([(4, 4), (6, 7)], strap)
    cv.put(4, 4, strap)
    cv.outline("#0E2236" if full else "#2A2830")
    return cv


def main():
    os.makedirs(MA.OUT, exist_ok=True)
    MA.sheet([chancla_hand(i) for i in range(3)]).save("chancla_hand.png")
    chancla_fly().save("chancla.png")
    MA.sheet([chancla_icon(True), chancla_icon(False)]).save("chancla_icon.png")
    print("chancletas en", os.path.normpath(MA.OUT))


if __name__ == "__main__":
    main()
