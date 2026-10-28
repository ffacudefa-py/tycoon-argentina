#!/usr/bin/env python3
"""Compila todo el arte hecho con PXL y lo copia a assets/pixel_art/.

Requiere Node >= 22.18 (en esta PC: ~/.local/opt/node22/bin/node) y la skill
pxl-pixel-art (~/.claude/skills/pxl-pixel-art). Uso:
  python3 tools/art/pxl/build.py
Salidas:
  assets/pixel_art/interiors/<negocio>_<nivel>_back.png / _front.png
  assets/pixel_art/locations/street_<zona>.png y start_bg.png
  assets/pixel_art/avatars/<id>.png (32x32)
  assets/pixel_art/effects/<anim>.png (+ .json con la duración de cada cuadro)
"""
import glob
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ART = os.path.join(ROOT, "assets", "pixel_art")
NODE = os.environ.get("PXL_NODE", os.path.expanduser("~/.local/opt/node22/bin/node"))
PXL = os.environ.get("PXL_BIN", os.path.expanduser("~/.claude/skills/pxl-pixel-art/bin/pxl.js"))


def pxl(fname):
    r = subprocess.run([NODE, PXL, "build", fname, "--no-preview"], cwd=HERE, capture_output=True, text=True)
    if r.returncode != 0 or "error" in (r.stdout + r.stderr).lower():
        print(r.stdout, r.stderr)
        sys.exit(f"PXL falló en {fname}")


def main():
    subprocess.run([sys.executable, os.path.join(HERE, "gen_interiors.py")], check=True)
    for f in ("furniture.px.js", "locations.px.js", "interiors.px.js", "avatars.px.js"):
        pxl(f)
    out = os.path.join(HERE, "out")
    d = os.path.join(ART, "interiors"); os.makedirs(d, exist_ok=True)
    n = 0
    for sc in glob.glob(os.path.join(out, "scenes", "int_*")):
        if not os.path.isdir(sc):
            continue
        name = os.path.basename(sc)[4:]
        for layer in ("back", "front"):
            shutil.copy(os.path.join(sc, f"{layer}.png"), os.path.join(d, f"{name}_{layer}.png"))
            n += 1
    d = os.path.join(ART, "locations"); os.makedirs(d, exist_ok=True)
    for f in glob.glob(os.path.join(out, "scenes", "loc_*.png")):
        shutil.copy(f, os.path.join(d, "street_" + os.path.basename(f)[4:]))
    shutil.copy(os.path.join(out, "scenes", "start_bg.png"), os.path.join(d, "start_bg.png"))
    # 10.0: el mapa de la ciudad ficticia se reemplazó por el de la Argentina
    # (tools/art/map_art.py).
    d = os.path.join(ART, "avatars"); os.makedirs(d, exist_ok=True)
    for f in glob.glob(os.path.join(out, "sprites", "av_*.png")):
        shutil.copy(f, os.path.join(d, os.path.basename(f)[3:]))
    d = os.path.join(ART, "effects"); os.makedirs(d, exist_ok=True)
    for f in glob.glob(os.path.join(out, "anims", "*.png")):
        base = os.path.basename(f)[:-4]
        shutil.copy(f, os.path.join(d, base + ".png"))
        js = f[:-4] + ".json"
        if os.path.exists(js):
            meta = json.load(open(js))
            frames = meta.get("frames", {})
            durs = [v.get("duration", 100) for v in (frames.values() if isinstance(frames, dict) else frames)]
            json.dump({"frames": len(durs), "durations_ms": durs}, open(os.path.join(d, base + ".json"), "w"))
    print(f"PXL: {n} capas de interiores, escenarios y efectos copiados a {ART}")


if __name__ == "__main__":
    main()
