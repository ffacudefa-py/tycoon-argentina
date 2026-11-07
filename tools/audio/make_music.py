"""15.0: prepara el tema principal para que loopee sin que se note.

El máster dura 32 compases exactos a 140 BPM, así que se repite entero. Pero termina
en otro valor que el que arranca (0,14 contra 0,52): sin tocarlo sonaría un click en
cada vuelta. Se empalman los últimos milisegundos hacia el principio dado vuelta, que
llega de forma continua a la primera muestra. La duración no cambia. Sale en PCM de
16 bits con dither: sin compresión, el loop es exacto a la muestra.

Godot 4.7 deja en 0,0 la muestra en la que salta el loop, cualquiera sea loop_begin
(medido con tools/dev/loop_check.gd): un tic en cada vuelta. Por eso el archivo lleva
al final una copia de sus primeras LOOP_HEAD muestras y el loop va de LOOP_HEAD a
N + LOOP_HEAD. Así la unión musical se reproduce de corrido, y el salto del motor cae
donde los dos canales ya pasan por cero (0,0008 y 0,0002): ese error no se oye.
Si cambia el máster, hay que volver a buscar ese punto.

  python tools/audio/make_music.py [ruta del máster]
"""
import os
import struct
import sys
import wave

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
MASTER = ("D:/Users/Family/Documents/Image-Line/FL Studio/Projects/CORONADOS DE GLORIA Main Theme/"
          "CORONADOS DE GLORIA Main Theme (mastered).wav")
OUT = os.path.join(ROOT, "assets", "audio", "music", "main_theme.wav")
SPLICE = 256      # 5,8 ms a 44,1 kHz: tapado por el golpe del primer compás
LOOP_HEAD = 29571  # debe coincidir con LOOP_HEAD en scripts/audio/music.gd


def read_float_wav(path):
    with open(path, "rb") as f:
        f.read(12)
        fmt, data = None, None
        while True:
            head = f.read(8)
            if len(head) < 8:
                break
            cid, n = head[:4], struct.unpack("<I", head[4:])[0]
            if cid == b"fmt ":
                fmt = struct.unpack("<HHIIHH", f.read(n)[:16])
            elif cid == b"data":
                data = f.read(n)
            else:
                f.seek(n + (n & 1), 1)
    tag, ch, sr, _, _, bits = fmt
    if tag != 3 or bits != 32:
        raise SystemExit("Se esperaba WAV flotante de 32 bits, llegó tag=%d bits=%d" % (tag, bits))
    return np.frombuffer(data, "<f4").reshape(-1, ch).astype(np.float64), sr


def seam_splice(x, n=SPLICE):
    """Lleva el final hacia el principio invertido, con fundido de potencia constante."""
    y = x.copy()
    t = (np.arange(n) + 1.0) / n
    fade_out = np.cos(t * np.pi / 2)[:, None]
    fade_in = np.sin(t * np.pi / 2)[:, None]
    head_rev = x[n:0:-1]                      # termina en x[1]: lo siguiente es x[0]
    y[-n:] = x[-n:] * fade_out + head_rev * fade_in
    return y


def write_pcm16(path, x, sr, head):
    rng = np.random.default_rng(15)
    dither = (rng.random(x.shape) - rng.random(x.shape)) / 32768.0     # TPDF de 1 LSB
    pcm = np.clip(np.round((x + dither) * 32767.0), -32768, 32767).astype("<i2")
    pcm = np.concatenate([pcm, pcm[:head]])             # copia exacta, muestra por muestra
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())


def main():
    x, sr = read_float_wav(sys.argv[1] if len(sys.argv) > 1 else MASTER)
    y = seam_splice(x)
    write_pcm16(OUT, y, sr, LOOP_HEAD)
    before = np.abs(x[0] - x[-1]).max()
    after = np.abs(y[0] - y[-1]).max()
    typical = np.percentile(np.abs(np.diff(y, axis=0)), 99.9)
    print("muestras %d (%.3f s), %d Hz" % (len(y), len(y) / sr, sr))
    print("salto en la unión: antes %.4f, ahora %.4f (paso normal de la música: %.4f)" % (before, after, typical))


if __name__ == "__main__":
    main()
