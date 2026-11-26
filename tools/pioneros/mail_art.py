"""Arte del mail de pioneros -> web/img/mail/ (se sirve desde coronadosdegloria.web.app).

Los clientes de correo no respetan image-rendering: pixelated, así que nada se escala con
filtro: recortes 1:1 y el logo a 2x exacto. Las imágenes miden el doble de lo que muestra
el mail (600 px de ancho) para que se vean nítidas en pantallas de alta densidad.

    python tools/pioneros/mail_art.py
"""
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / "web" / "img"
OUT = WEB / "mail"
OUT.mkdir(exist_ok=True)

pil = Image.open(WEB / "pilares.png").convert("RGBA")
logo = Image.open(WEB / "logo.png").convert("RGBA")

# Cabecera: pilares centrales (NEA a PAMPEANA, enteros) a 1:1.
head = pil.crop((322, 300, 1594, 790))
grad = Image.new("RGBA", head.size)
px = grad.load()
for y in range(head.height):                       # oscurece el cielo para leer el logo
    a = int(max(0, 190 * (1 - y / 260)))
    for x in range(head.width):
        px[x, y] = (26, 23, 48, a)
head = Image.alpha_composite(head, grad)
lg = logo.resize((logo.width * 2, logo.height * 2), Image.NEAREST)
head.alpha_composite(lg, ((head.width - lg.width) // 2, 28))
head.convert("RGB").save(OUT / "cabecera.png", optimize=True)

# Pie: la base dorada con rótulos de región, 1:1 (NEA a PAMPEANA).
pil.crop((322, 1005, 1594, 1080)).convert("RGB").save(OUT / "pie.png", optimize=True)

Image.open(WEB / "pionero.png").save(OUT / "pionero.png", optimize=True)
print("ok", sorted(p.name for p in OUT.iterdir()))
