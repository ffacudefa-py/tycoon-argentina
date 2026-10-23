#!/usr/bin/env python3
"""Vista previa de interiores con personajes reales (para revisar el arte)."""
import json, os, sys
from PIL import Image
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
meta = json.load(open(os.path.join(ROOT, "data", "interiors.json")))
CH = os.path.join(ROOT, "assets", "pixel_art", "characters")
def frame(sheet, i):
    im = Image.open(os.path.join(CH, sheet)); fw = im.width // 10
    return im.crop((i * fw, 0, (i + 1) * fw, im.height))
def compose(bid, t):
    d = os.path.join(HERE, "out", "scenes", f"int_{bid}_{t}")
    back = Image.open(os.path.join(d, "back.png")).convert("RGBA"); front = Image.open(os.path.join(d, "front.png")).convert("RGBA")
    info = meta["businesses"][bid][t]; img = back.copy()
    for i, s in enumerate(info["stations"]):
        f = frame(f"worker_{i % 8}.png", 6); f = f.transpose(Image.FLIP_LEFT_RIGHT) if s.get("flip") else f
        img.alpha_composite(f, (s["x"] - f.width // 2, s["y"] - 46))
    img.alpha_composite(front)
    for j, q in enumerate(info["queue"]):
        f = frame(f"customer_{(j + 3) % 8}.png", 4).transpose(Image.FLIP_LEFT_RIGHT)
        img.alpha_composite(f, (q[0] - 16, q[1] - 46))
    return img
ids = sys.argv[1].split(",") if len(sys.argv) > 1 else list(meta["businesses"])
tiers = [int(x) for x in sys.argv[2].split(",")] if len(sys.argv) > 2 else [0, 2, 4]
out = Image.new("RGBA", (400 * len(tiers) + 8 * (len(tiers) - 1), 170 * len(ids) + 6 * (len(ids) - 1)), (255, 255, 255, 255))
for r, b in enumerate(ids):
    for k, t in enumerate(tiers): out.alpha_composite(compose(b, t), (k * 408, r * 176))
out.save(sys.argv[3] if len(sys.argv) > 3 else "/tmp/interiors_preview.png")
