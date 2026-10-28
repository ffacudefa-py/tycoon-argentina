"""Elementos ambientales 11 (docs/style-guide.md): nubes, pájaros y autos.

Sprites chicos y reutilizables que BusinessScene mueve a distintas velocidades
y capas (parallax). Paleta cálida, contorno marrón.
  assets/escenarios/effects/amb_cloud_<0..2>.png
  assets/escenarios/effects/amb_bird.png        (2 cuadros de 9x6, aleteo)
  assets/escenarios/effects/amb_car_<0..2>.png   (2 cuadros de 40x22, ruedas)
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


def car(color, f):
    s, m, l, h = ("i_%s%d" % (color, i) for i in range(4))
    cv = Canvas(40, 22)
    cv.rect(10, 2, 18, 8, m)
    cv.rect(12, 4, 6, 5, "iSky3")
    cv.rect(20, 4, 6, 5, "iSky3")
    cv.put(13, 4, "iWh")
    cv.rect(2, 9, 36, 8, m)
    cv.hline(2, 9, 36, l)
    cv.hline(2, 16, 36, s)
    cv.rect(36, 11, 2, 2, "i_amarillo2")      # faro
    cv.rect(2, 11, 2, 2, "i_rojo1")           # luz trasera
    for wx in (10, 30):
        cv.ellipse(wx, 17, 4, 4, "iO")
        cv.ellipse(wx, 17, 2, 2, "i_gris1")
        cv.put(wx + (1 if f else -1), 17, "i_gris3")
    cv.outline("iO")
    return cv


def pickup(f):
    cv = Canvas(40, 22)
    s, m, l = "i_verde0", "i_verde1", "i_verde2"
    cv.rect(22, 3, 12, 7, m)
    cv.rect(24, 5, 8, 4, "iSky3")
    cv.rect(2, 9, 36, 8, m)
    cv.hline(2, 9, 36, l)
    cv.rect(4, 6, 16, 3, "i_marron2")             # caja con fardos
    cv.rect(5, 4, 6, 3, "i_amarillo1")
    cv.rect(12, 4, 6, 3, "i_amarillo1")
    cv.rect(36, 11, 2, 2, "i_amarillo2")
    for wx in (10, 30):
        cv.ellipse(wx, 17, 4, 4, "iO")
        cv.ellipse(wx, 17, 2, 2, "i_gris1")
        cv.put(wx + (1 if f else -1), 17, "i_gris3")
    cv.outline("iO")
    return cv


def moto(f):
    cv = Canvas(40, 22)
    for wx in (12, 28):
        cv.ellipse(wx, 17, 4, 4, "iO")
        cv.ellipse(wx, 17, 2, 2, "i_gris1")
        cv.put(wx + (1 if f else -1), 17, "i_gris3")
    cv.rect(12, 11, 16, 4, "i_rojo1")
    cv.hline(12, 11, 16, "i_rojo2")
    cv.rect(18, 4, 5, 7, "i_azul1")               # motoquero
    cv.rect(18, 0, 5, 4, "i_amarillo1")           # casco
    cv.put(22, 1, "iSky3")
    cv.rect(27, 8, 2, 4, "i_gris1")
    cv.rect(8, 9, 6, 4, "i_marron2")              # caja de delivery
    cv.outline("iO")
    return cv


def generate(out_root):
    d = os.path.join(out_root, "escenarios", "effects")
    os.makedirs(d, exist_ok=True)
    for i in range(3):
        cloud(i).save(os.path.join(d, "amb_cloud_%d.png" % i))
    sheet([bird(0), bird(1)]).save(os.path.join(d, "amb_bird.png"))
    for i, c in enumerate(("rojo", "celeste", "amarillo")):
        sheet([car(c, 0), car(c, 1)]).save(os.path.join(d, "amb_car_%d.png" % i))
    sheet([pickup(0), pickup(1)]).save(os.path.join(d, "amb_car_3.png"))
    sheet([moto(0), moto(1)]).save(os.path.join(d, "amb_car_4.png"))


if __name__ == "__main__":
    generate(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets"))
