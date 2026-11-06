#!/usr/bin/env python3
"""Importa los SFX exportados de FL Studio a assets/audio/<nombre>.wav.

Conserva la mezcla (estéreo y niveles). Sólo recorta el silencio del principio
(el retardo del mp3 atrasaría el sonido respecto del toque) y el del final, con
un fundido corto. Después hay que correr `godot --headless --path . --import`.

Uso: python tools/audio/import_sfx.py [carpeta]
"""
import os
import sys

import numpy as np
import soundfile as sf

SRC = r"D:/Users/Family/Documents/Image-Line/FL Studio/Projects/sfx tap - CDG"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "audio")
# Sonido del juego -> nombre del export. "buy" suena al subir de nivel un negocio.
MAP = {
    "tap": "tap",
    "buy": "lvl up",
    "upgrade": "upgrade",
    "unlock": "unlock",
    "hire": "hire",
    "mission": "mission",
    "event": "event",
    "register": "register",
    "tier": "tier",
    "whoosh": "whoosh",
}
THRESHOLD_DB = -60.0
PRE_ROLL = 0.002
FADE_OUT = 0.03


def find_export(folder: str, name: str) -> str:
    """FL Studio dejó nombres con uno o dos espacios después de "sfx"."""
    for spaces in (" ", "  "):
        path = os.path.join(folder, "sfx%s%s - CDG.mp3" % (spaces, name))
        if os.path.exists(path):
            return path
    raise FileNotFoundError(name)


def clean(audio: np.ndarray, rate: int) -> np.ndarray:
    level = np.abs(audio).max(axis=1)
    audible = np.nonzero(level > level.max() * 10 ** (THRESHOLD_DB / 20))[0]
    start = max(0, audible[0] - int(PRE_ROLL * rate))
    fade = int(FADE_OUT * rate)
    end = min(len(audio), audible[-1] + fade)
    out = audio[start:end].copy()
    n = min(fade, len(out))
    out[-n:] *= np.linspace(1.0, 0.0, n)[:, None]
    return out


def main() -> None:
    folder = sys.argv[1] if len(sys.argv) > 1 else SRC
    for game_name, export_name in MAP.items():
        audio, rate = sf.read(find_export(folder, export_name), always_2d=True)
        out = clean(audio, rate)
        sf.write(os.path.join(OUT, game_name + ".wav"), out, rate, subtype="PCM_16")
        print("%-9s <- %-9s %.2f s (de %.2f s)" % (game_name, export_name, len(out) / rate, len(audio) / rate))


if __name__ == "__main__":
    main()
