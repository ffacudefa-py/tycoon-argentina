"""Elementos ambientales 11 (docs/style-guide.md): nubes y pájaros (autos: vehicles15.py).

Sprites chicos y reutilizables que BusinessScene mueve a distintas velocidades
y capas (parallax). Paleta cálida, contorno marrón.
  assets/escenarios/effects/amb_cloud_<0..2>.png
  assets/escenarios/effects/amb_bird.png        (2 cuadros de 9x6, aleteo)
"""
import os
from PIL import Image
from px2 import Canvas, sheet
import palette11  # noqa: F401


def cloud(size):
    w, h = [(40, 16), (56, 20), (72, 26)][size]
    cv = Canvas(w, h)
    cv.ellipse(w // 2, h - 6, w // 2 - 2, 5, "iSky3")
    for dx, r in ((-w // 4, h // 3), (0, h // 2 - 1), (w // 4, h // 3 + 1)):
        cv.ellipse(w // 2 + dx, h // 2 + 1, r + 2, r, "iWh")
    cv.hline(4, h - 3, w - 8, "iSky3")
    cv.outline("i_celeste0")
    return cv


def bird(f):
    cv = Canvas(9, 6)
    cv.rect(3, 2, 3, 2, "i_marron1")              # cuerpo
    if f == 0:
        for i in range(4):
            cv.put(i, 1 + i // 2, "iO")
            cv.put(8 - i, 1 + i // 2, "iO")
    else:
        for i in range(4):
            cv.put(i, 4 - i // 2, "iO")
            cv.put(8 - i, 4 - i // 2, "iO")
    cv.rect(4, 3, 1, 2, "iS")
    return cv


def generate(out_root):
    d = os.path.join(out_root, "escenarios", "effects")
    os.makedirs(d, exist_ok=True)
    for i in range(3):
        cloud(i).save(os.path.join(d, "amb_cloud_%d.png" % i))
    sheet([bird(0), bird(1)]).save(os.path.join(d, "amb_bird.png"))


if __name__ == "__main__":
    generate(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets"))
