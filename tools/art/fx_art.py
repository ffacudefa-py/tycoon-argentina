"""Partículas y efectos pixelados."""
import os
from px import Canvas


def coin_sheet():
    """Moneda girando: 4 cuadros de 8x8."""
    sheet = Canvas(32, 8)
    widths = [3, 2, 1, 2]
    for f, w in enumerate(widths):
        c = Canvas(8, 8)
        c.ellipse(3, 3, w, 3, "y")
        if w >= 2:
            c.vline(3, 1, 5, "Y")
            c.put(2, 1, "L")
        c.outline_all("o")
        sheet.blit(c, f * 8, 0)
    return sheet


def sparkle_sheet():
    sheet = Canvas(32, 8)
    shapes = [
        ["........", "........", "...y....", "..yLy...", "...y....", "........", "........", "........"],
        ["........", "...y....", "...y....", ".yyLyy..", "...y....", "...y....", "........", "........"],
        ["...y....", "...y....", "..yLy...", "yyLhLyy.", "..yLy...", "...y....", "...y....", "........"],
        ["........", "...L....", "........", ".L.h.L..", "........", "...L....", "........", "........"],
    ]
    for f, rows in enumerate(shapes):
        c = Canvas(8, 8)
        c.stamp(rows, 0, 0)
        sheet.blit(c, f * 8, 0)
    return sheet


def bill():
    c = Canvas(10, 7)
    c.rect(0, 0, 10, 7, "n")
    c.frame(0, 0, 10, 7, "G")
    c.rect(4, 2, 2, 3, "N")
    c.put(1, 1, "N")
    return c


def smoke_sheet():
    sheet = Canvas(24, 8)
    for f in range(3):
        c = Canvas(8, 8)
        r = 1 + f
        c.ellipse(3, 4, r, r, "l" if f < 2 else "g")
        sheet.blit(c, f * 8, 0)
    return sheet


def confetti():
    c = Canvas(12, 4)
    for i, col in enumerate(["r", "y", "c", "n", "v", "q"]):
        c.rect(i * 2, 0, 2, 2 + (i % 2) * 2, col)
    return c


def star_small():
    c = Canvas(5, 5)
    c.stamp([".....", "..y..", ".yLy.", "..y..", "....."], 0, 0)
    return c


def generate(out):
    d = os.path.join(out, "particles")
    os.makedirs(d, exist_ok=True)
    coin_sheet().save(f"{d}/coin_spin.png")
    sparkle_sheet().save(f"{d}/sparkle.png")
    bill().save(f"{d}/bill.png")
    smoke_sheet().save(f"{d}/smoke.png")
    confetti().save(f"{d}/confetti.png")
    star_small().save(f"{d}/star.png")
