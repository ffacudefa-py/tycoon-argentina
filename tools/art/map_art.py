"""Mapas pixel art de la 10.0: la Argentina por regiones y cada región ampliada.

Fuente: tools/art/map_data/argentina_provincias.json (polígonos simplificados
de las provincias del IGN). Se proyectan (equirectangular con cos de la
latitud media), se rasterizan a escala de pantalla y se pintan con la paleta
px2: cada región con su rampa, provincias alternando tonos, borde 1 px.

Genera en assets/pixel_art/map/:
  argentina.png                 mapa del país (base)
  argentina_<region>.png        silueta blanca de cada región (se tiñe en el juego)
  region_<region>.png           la región ampliada (base)
  region_<region>_<prov>.png    silueta blanca de cada provincia en esa vista
  *_mask.png                    canal R = índice (1..n) para saber qué se tocó
y data/map_layout.json con tamaños, índices de máscara y centros para rótulos.
"""
import json
import math
import os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

REGION_RAMP = {
    "noa": ("#8A4A1F", "#C8752F", "#E39A4F"),
    "nea": ("#2D6A3E", "#4C9A4F", "#6DB35C"),
    "cuyo": ("#6B2335", "#9C3A4E", "#BE5A68"),
    "patagonia": ("#2F6EA8", "#5A93CC", "#86B6E0"),
    "pampeana": ("#9C6A12", "#D4A22A", "#E8C25A"),
    "centro": ("#4A3F7A", "#6E62A8", "#9288C6"),
}
SEA = ("#1F3D66", "#26497A")
OUTLINE = "#1B1A2E"
LAT0 = -38.0


def hex2rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def project(lon, lat):
    return lon * math.cos(math.radians(LAT0)), -lat


def load():
    polys = json.load(open(os.path.join(HERE, "map_data", "argentina_provincias.json")))
    out = {}
    for pid, rings in polys.items():
        keep = []
        for r in rings:
            # Las islas lejanas del Atlántico Sur (Georgias, Sandwich) no entran
            # en el mapa; Malvinas sí.
            if max(p[0] for p in r) > -53.0:
                continue
            keep.append([project(*p) for p in r])
        out[pid] = keep
    return out


def bounds(polys, ids):
    xs, ys = [], []
    for pid in ids:
        for r in polys[pid]:
            xs += [p[0] for p in r]
            ys += [p[1] for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def render(polys, ids, owner, max_w, max_h, pad=8, caba_dot=False):
    """Rasteriza las provincias ids. owner: pid -> (región, índice de color)."""
    x0, y0, x1, y1 = bounds(polys, ids)
    k = min((max_w - 2 * pad) / (x1 - x0), (max_h - 2 * pad) / (y1 - y0))
    w = int(math.ceil((x1 - x0) * k)) + 2 * pad
    h = int(math.ceil((y1 - y0) * k)) + 2 * pad
    mask = Image.new("L", (w, h), 0)
    dr = ImageDraw.Draw(mask)
    centers = {}
    for n, pid in enumerate(ids, start=1):
        pts_all = []
        for r in polys[pid]:
            pts = [((x - x0) * k + pad, (y - y0) * k + pad) for x, y in r]
            dr.polygon(pts, fill=n)
            pts_all += pts
        if pid == "caba" and caba_dot:
            cx = sum(p[0] for p in pts_all) / len(pts_all)
            cy = sum(p[1] for p in pts_all) / len(pts_all)
            dr.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=n)
    px = mask.load()
    # Centros por área rasterizada (más estables que el centroide del polígono).
    acc = {}
    for y in range(h):
        for x in range(w):
            v = px[x, y]
            if v:
                a = acc.setdefault(v, [0, 0, 0])
                a[0] += x
                a[1] += y
                a[2] += 1
    for n, pid in enumerate(ids, start=1):
        if n in acc:
            a = acc[n]
            centers[pid] = [round(a[0] / a[2]), round(a[1] / a[2])]
    # Color: rampa de la región; provincias vecinas de la misma región con
    # tonos distintos (coloreo goloso con hasta 4 tonos).
    adj = {}
    for y in range(h - 1):
        for x in range(w - 1):
            v = px[x, y]
            for nv in (px[x + 1, y], px[x, y + 1]):
                if v and nv and nv != v:
                    adj.setdefault(v, set()).add(nv)
                    adj.setdefault(nv, set()).add(v)
    tone = {}
    for v in sorted(acc, key=lambda q: -len(adj.get(q, ()))):
        used = {tone[u] for u in adj.get(v, ()) if u in tone and owner[ids[u - 1]][0] == owner[ids[v - 1]][0]}
        tone[v] = next(t for t in range(4) if t not in used)
    img = Image.new("RGBA", (w, h))
    ip = img.load()
    for y in range(h):
        for x in range(w):
            v = px[x, y]
            if v == 0:
                ip[x, y] = hex2rgb(SEA[(x // 2 + y) % 7 == 0])
                continue
            region, _idx = owner[ids[v - 1]]
            ramp = REGION_RAMP[region]
            t = tone.get(v, 0)
            if t < 2:
                ip[x, y] = hex2rgb(ramp[1 + t])
            elif t == 2:
                a, b = hex2rgb(ramp[1]), hex2rgb(ramp[0])
                ip[x, y] = tuple((a[i] * 2 + b[i]) // 3 for i in range(3)) + (255,)
            else:
                a = hex2rgb(ramp[2])
                ip[x, y] = tuple((a[i] * 3 + 255) // 4 for i in range(3)) + (255,)
    # Bordes: entre provincias de la misma región el tono oscuro de la rampa;
    # costa y límites entre regiones, contorno general.
    out = img.copy()
    op = out.load()
    for y in range(h):
        for x in range(w):
            v = px[x, y]
            if v == 0:
                continue
            for dx, dy in ((1, 0), (0, 1), (-1, 0), (0, -1)):
                nx, ny = x + dx, y + dy
                nv = px[nx, ny] if 0 <= nx < w and 0 <= ny < h else 0
                if nv != v:
                    if nv == 0 or owner[ids[nv - 1]][0] != owner[ids[v - 1]][0]:
                        op[x, y] = hex2rgb(OUTLINE)
                    elif dx > 0 or dy > 0:
                        op[x, y] = hex2rgb(REGION_RAMP[owner[ids[v - 1]][0]][0])
                    break
    return out, mask, centers, k


def silhouettes(mask, groups):
    """groups: nombre -> conjunto de índices de máscara. Silueta blanca por grupo."""
    w, h = mask.size
    px = mask.load()
    out = {}
    for name, idxs in groups.items():
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        ip = im.load()
        for y in range(h):
            for x in range(w):
                if px[x, y] in idxs:
                    ip[x, y] = (255, 255, 255, 255)
        out[name] = im
    return out


def mask_png(mask):
    """Máscara como RGBA (R = índice) para leerla con Image.get_pixel en Godot."""
    w, h = mask.size
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ip = im.load()
    px = mask.load()
    for y in range(h):
        for x in range(w):
            if px[x, y]:
                ip[x, y] = (px[x, y], 0, 0, 255)
    return im


def generate(out_dir, data_dir):
    world = json.load(open(os.path.join(data_dir, "world.json"), encoding="utf-8"))
    polys = load()
    regions = [r["id"] for r in world["regions"]]
    zones = world["zones"]
    owner = {}
    by_region = {r: [] for r in regions}
    for z in zones:
        by_region[z["region"]].append(z["id"])
    for r, pids in by_region.items():
        for i, pid in enumerate(pids):
            owner[pid] = (r, i)
    d = os.path.join(out_dir, "map")
    os.makedirs(d, exist_ok=True)
    layout = {"_doc": "Generado por tools/art/map_art.py. mask: canal R = índice (1..n) del orden de 'ids'.", "regions": {}}
    ids = [z["id"] for z in zones]
    img, mask, centers, _ = render(polys, ids, owner, 360, 540, pad=6)
    img.save(os.path.join(d, "argentina.png"))
    mask_png(mask).save(os.path.join(d, "argentina_mask.png"))
    groups = {r: {ids.index(p) + 1 for p in by_region[r]} for r in regions}
    for r, im in silhouettes(mask, groups).items():
        im.save(os.path.join(d, "argentina_%s.png" % r))
    # Centro de cada región en el mapa del país (promedio de sus provincias).
    rc = {}
    mp = mask.load()
    for r in regions:
        xs, ys, n = 0, 0, 0
        for y in range(mask.size[1]):
            for x in range(mask.size[0]):
                if mp[x, y] in groups[r]:
                    xs += x
                    ys += y
                    n += 1
        rc[r] = [round(xs / n), round(ys / n)]
    layout["country"] = {"size": list(img.size), "ids": ids, "region_centers": rc}
    for r in regions:
        rids = by_region[r]
        rimg, rmask, rcent, _ = render(polys, rids, owner, 344, 460, pad=10, caba_dot=True)
        rimg.save(os.path.join(d, "region_%s.png" % r))
        mask_png(rmask).save(os.path.join(d, "region_%s_mask.png" % r))
        for pid, im in silhouettes(rmask, {p: {i + 1} for i, p in enumerate(rids)}).items():
            im.save(os.path.join(d, "region_%s_%s.png" % (r, pid)))
        layout["regions"][r] = {"size": list(rimg.size), "ids": rids, "centers": rcent}
    json.dump(layout, open(os.path.join(data_dir, "map_layout.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return layout


if __name__ == "__main__":
    lay = generate(os.path.join(ROOT, "assets", "pixel_art"), os.path.join(ROOT, "data"))
    print("país", lay["country"]["size"], {r: v["size"] for r, v in lay["regions"].items()})
