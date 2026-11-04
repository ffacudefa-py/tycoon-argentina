"""12.2: manos del asalto con volumen real (vol_art), más realistas que las de 12.1.

Guante táctico de cuero negro sin dedos (las últimas falanges son piel, con
uña), nudillera acolchada, abrojo en la muñeca, puño elástico acanalado y la
manga de la campera, que llega hasta el borde del cuadro (nunca se ve cortada).
Las mismas medidas y puntos de anclaje que 12.1 (la vista no cambia):
  pistol_hand: cuadros de 96x96, muñeca en (80,80), boca del caño en (12,36)
  bag_hand:    cuadros de 88x100, boca de la bolsa en (45,11)
"""
import math

import numpy as np
from PIL import Image

import vol_art as V


def _sleeve_folds(cx, cy, ang, period=11.0, amp=1.8):
    """Pliegues de la manga: ondas perpendiculares al brazo."""
    ca, sa = math.cos(ang), math.sin(ang)

    def f(X, Y):
        u = (X - cx) * ca + (Y - cy) * sa
        v = -(X - cx) * sa + (Y - cy) * ca
        return amp * np.sin(u / period * 2 * math.pi + np.sin(v / 9.0) * 1.3) ** 2
    return f


def pistol_hand_layers(frame):
    """Devuelve (atrás, adelante): la mano sin el índice y el índice (va sobre la pistola)."""
    # --------- atrás de la pistola: manga, puño, dorso, mayor/anular/meñique
    sc = V.Scene(96, 96)
    # puño elástico corto en la muñeca; la manga lo tapa con su dobladillo
    sc.capsule((77, 81), (70, 73), 9.4, 8.6, "knit", z=-1)
    sc.poly([(64, 97), (66.5, 89), (72, 82), (81, 76), (97, 70), (97, 97)], "sleeve", z=1.5, dome=7, soft=4)
    sc.push(_sleeve_folds(84, 86, -0.65), "sleeve")
    sc.capsule((66.2, 90.5), (82.5, 74.8), 2.6, 2.6, "sleeve", z=6.2, flat=0.8)    # dobladillo
    sc.capsule((64.5, 74), (77, 63.5), 2.6, 2.6, "velcro", z=3.5, flat=0.6)  # abrojo
    # dorso: ancho en los nudillos, se angosta hacia la muñeca
    sc.capsule((60, 52), (69.5, 70), 12.5, 8.2, "glove", z=-2, flat=0.62)
    sc.ellipsoid(61.5, 41.6, 6.6, 4.2, -0.35, "glove", z=0.5, depth=3.5)        # membrana contra la cola de la corredera
    sc.ellipsoid(58.2, 58.2, 4.0, 10.0, -0.29, "glove_pad", z=2.6, depth=2.4)  # nudillera, paralela a la empuñadura
    # Agarre real visto desde la derecha: el dorso tapa la cacha, los nudillos van en
    # fila paralela al frente de la empuñadura (x = 47 + (y - 44) * 0.3) y unos 6 px
    # detrás; la primera falange avanza hasta apenas pasar el frente y la segunda se
    # curva hacia abajo y atrás, envolviéndolo: las yemas quedan del otro lado (no
    # se ven). Mayor bajo el guardamonte, anular y meñique más cortos hacia abajo.
    fingers = [   # nudillos escalonados (cada uno un poco más atrás) y dos falanges que se curvan
        ([(60.2, 65.0), (55.0, 66.8), (52.2, 68.8), (52.4, 71.4)], [2.8, 2.55, 2.3, 2.0]),     # meñique (bajan ~18°)
        ([(58.2, 58.6), (52.2, 60.6), (49.2, 62.8), (49.4, 65.8)], [3.2, 2.95, 2.65, 2.3]),    # anular
        ([(56.0, 52.0), (49.6, 54.0), (46.6, 56.2), (46.8, 59.4)], [3.4, 3.1, 2.8, 2.45]),     # mayor
    ]
    for i, (pts, rad) in enumerate(fingers):
        sc.chain(pts, rad, ["glove", "glove", "glove"], z=1.0 + i * 0.7)   # alturas distintas: se separan
        sc.ellipsoid(pts[1][0], pts[1][1] - 0.4, 1.6, 1.4, 0, "glove_pad", z=4.2 + i * 0.7, depth=1.0)
    # costura del dorso (pespunte claro que sigue el borde de la nudillera)
    sc.push(lambda X, Y: -0.5 * ((np.abs((X - 62.5) * 0.95 + (Y - 56) * -0.3) < 0.35) & (Y > 46) & (Y < 66)), "glove")
    back = sc.render(outline=None, warm=(12, 36, 40, 0.15) if frame == 1 else None)
    back = back.copy()
    _stitch(back, [(63.5, 47), (65, 52), (66, 57), (66.5, 62), (66.5, 66)])

    # --------- adelante: el índice (estirado sobre el armazón o en el gatillo)
    fi = V.Scene(96, 96)
    if frame == 1:
        pts = [(56, 45), (47.5, 46.6), (41.6, 49.6), (39.8, 53.2)]
    else:
        pts = [(56, 45), (46.5, 45.4), (37.5, 45.9), (31, 46.4)]
    fi.chain(pts, [3.3, 2.95, 2.6, 2.3], ["glove", "glove", "glove"], z=1.0)   # misma luz que los otros dedos
    fi.ellipsoid(56, 45, 3.2, 3.0, 0, "glove_pad", z=3.2, depth=1.8)          # nudillo del índice
    # (el pulgar va del lado izquierdo del arma: desde este lado no se ve)
    front = fi.render(outline=None, warm=(12, 36, 40, 0.18) if frame == 1 else None)
    return back, front


def _stitch(img, pts, col=(150, 112, 86, 255)):
    """Pespunte: puntos claros cada 2 px sobre el cuero."""
    px = img.load()
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0)))
        for i in range(0, n, 2):
            x = int(round(x0 + (x1 - x0) * i / max(1, n)))
            y = int(round(y0 + (y1 - y0) * i / max(1, n)))
            if 0 <= x < img.width and 0 <= y < img.height and px[x, y][3]:
                px[x, y] = col


def bag_body(ox, full):
    """Bolsa de arpillera: cuerpo redondo con pliegues radiales desde el cuello,
    cuello fruncido (pasa por adentro del puño) y volado de la boca cerrada arriba."""
    sc = V.Scene(88, 100)
    if full:
        rx, ry, cy = 39, 24, 76
        sc.ellipsoid(ox + 2, cy, rx, ry, 0.0, "burlap", z=-4, depth=12)
    else:
        # vacía: flácida, angosta, colgando, con la base arrugada
        sc.poly([(ox - 7, 50), (ox + 9, 50), (ox + 17, 70), (ox + 19, 92), (ox + 12, 99), (ox - 9, 99),
                 (ox - 16, 92), (ox - 15, 70)], "burlap", z=-4, dome=6, soft=4)
        sc.push(lambda X, Y: -1.6 * (np.sin((X - ox) * 0.55) ** 2) * np.clip((Y - 54) / 20, 0, 1), "burlap")
        sc.push(lambda X, Y: -1.2 * (np.sin((X - ox) * 1.3 + Y * 0.4) ** 2) * (Y > 90), "burlap")
    sc.capsule((ox + 1, 18), (ox + 1, 58), 6.0, 8.5, "burlap", z=-2, flat=0.8)
    # pliegues que salen del cuello y se abren hacia abajo
    def folds(X, Y):  # noqa: E306
        ang = np.arctan2(X - (ox + 1), np.maximum(1.0, Y - 46))
        dist = np.hypot(X - (ox + 1), Y - 46)
        k = np.clip(1 - dist / (ry * 1.6), 0, 1) * np.clip((Y - 48) / 6, 0, 1)
        return -1.6 * (np.sin(ang * 9) ** 2) * k
    if full:
        sc.push(folds, "burlap")
    if full:                                                             # tela tirante sobre el contenido
        sc.ellipsoid(ox + 14, cy - 6, 11, 8, 0.4, "burlap", z=3, depth=3)
        sc.ellipsoid(ox - 13, cy - 1, 10, 8, -0.3, "burlap", z=3, depth=3)
        sc.ellipsoid(ox + 1, cy + 6, 12, 7, 0, "burlap", z=3.5, depth=3)
    # volado de la boca cerrada: fruncido arriba del puño
    # volado irregular: tela fruncida que se abre en abanico, puntas de largo distinto
    sc.ellipsoid(ox + 1, 16, 10.5, 5.2, 0, "burlap", z=-2, depth=4)           # tela fruncida
    sc.push(lambda X, Y: -0.9 * (np.sin((X - ox) * 1.6) ** 2) * (np.abs(Y - 16) < 5.5), "burlap")
    # soga atada justo debajo del puño, con las dos puntas colgando
    sc.capsule((ox - 8, 47), (ox + 10, 46), 1.8, 1.8, "rope", z=7)
    sc.capsule((ox + 3, 47.5), (ox - 1, 57), 1.3, 1.1, "rope", z=6.5)
    sc.capsule((ox + 5, 47.5), (ox + 10, 56), 1.3, 1.1, "rope", z=6.5)
    sc.ellipsoid(ox + 4, 47.2, 2.4, 2.2, 0, "rope", z=7.5, depth=2)
    img = sc.render(outline=None, inner=0.6, inner_col="#3A1F12", ao=0.45)
    return img


def bag_fist_layers(ox):
    """Puño izquierdo sobre el cuello de la bolsa, el dorso hacia el jugador.
    (brazo, puño): el brazo va detrás de la bolsa; el puño, adelante."""
    arm = V.Scene(88, 100)
    arm.capsule((15, 47), (24, 38), 8.6, 7.2, "knit", z=-1)
    arm.poly([(-1, 47), (6, 43.5), (12.5, 49.5), (18, 56), (10, 80), (3, 101), (-1, 101)], "sleeve", z=1.5, dome=7, soft=4)
    arm.push(_sleeve_folds(6, 70, -1.2, period=5.0), "sleeve")
    arm.capsule((5.5, 43.5), (18.5, 56.5), 2.6, 2.6, "sleeve", z=6.2, flat=0.8)       # dobladillo
    arm_img = arm.render(outline=None)

    fs = V.Scene(88, 100)
    fs.capsule((ox - 20, 38), (ox - 9, 33), 9.0, 9.6, "glove", z=-1, flat=0.7)       # dorso
    fs.capsule((ox - 25, 43), (ox - 19, 37), 6.6, 7.5, "glove", z=-2.5, flat=0.7)     # muñeca
    fs.capsule((ox - 26, 44.5), (ox - 15, 35), 2.5, 2.5, "velcro", z=4.5, flat=0.55)  # abrojo
    fs.ellipsoid(ox - 5.2, 35, 3.6, 9.4, 0.05, "glove_pad", z=2.5, depth=2.4)         # nudillera
    fingers = [
        ([(ox - 5, 41.6), (ox + 3.2, 41.8), (ox + 8.4, 43.0), (ox + 10.8, 45.0)], [2.6, 2.35, 2.1, 1.8]),   # meñique
        ([(ox - 5, 37.2), (ox + 4.5, 36.8), (ox + 10.2, 38.0), (ox + 12.6, 40.2)], [2.95, 2.65, 2.35, 2.0]),  # anular
        ([(ox - 5, 32.6), (ox + 4.8, 32.0), (ox + 10.6, 33.2), (ox + 13.0, 35.4)], [3.05, 2.75, 2.45, 2.1]),  # mayor
        ([(ox - 5, 28.0), (ox + 4.0, 27.4), (ox + 9.6, 28.6), (ox + 12.0, 30.8)], [2.95, 2.65, 2.35, 2.0]),   # índice
    ]
    for i, (pts, rad) in enumerate(fingers):
        fs.chain(pts, [r * 1.08 for r in rad], ["glove", "glove", "glove"], z=0.6 + (i % 2) * 0.4)
    # pulgar: sale del costado del dorso, cruza por arriba y apoya sobre el índice
    fs.chain([(ox - 17, 29), (ox - 9, 24.4), (ox - 0.5, 23.6), (ox + 4.6, 25.2)], [3.5, 3.0, 2.7, 2.35],
             ["glove", "glove", "glove"], z=4.2)
    fist_img = fs.render(outline=None)
    return arm_img, fist_img
