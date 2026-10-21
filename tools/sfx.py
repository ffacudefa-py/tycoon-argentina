#!/usr/bin/env python3
"""Efectos de sonido originales sintetizados (sin samples externos).
Uso: python3 tools/sfx.py  -> assets/audio/*.wav (22050 Hz, mono, 16 bit)."""
import math, os, random, struct, wave

RATE = 22050
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "audio")


def tone(freq, dur, vol=0.5, wave_kind="square", slide=0.0, decay=6.0, duty=0.5):
    n = int(RATE * dur)
    out = []
    phase = 0.0
    for i in range(n):
        t = i / RATE
        f = freq + slide * t
        phase += f / RATE
        p = phase % 1.0
        if wave_kind == "square":
            s = 1.0 if p < duty else -1.0
        elif wave_kind == "tri":
            s = 4 * abs(p - 0.5) - 1
        elif wave_kind == "noise":
            s = random.uniform(-1, 1)
        else:
            s = math.sin(2 * math.pi * p)
        env = math.exp(-decay * t) * min(1.0, i / 60.0)
        out.append(s * vol * env)
    return out


def seq(*parts):
    out = []
    for p in parts:
        out += p
    return out


def mix(a, b):
    n = max(len(a), len(b))
    return [(a[i] if i < len(a) else 0) + (b[i] if i < len(b) else 0) for i in range(n)]


def save(name, samples):
    os.makedirs(OUT, exist_ok=True)
    with wave.open(os.path.join(OUT, name + ".wav"), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(b"".join(struct.pack("<h", int(max(-1, min(1, s)) * 26000)) for s in samples))


random.seed(3)
save("tap", tone(880, 0.05, 0.25, "square", decay=40, duty=0.25))
save("coin", seq(tone(988, 0.06, 0.3, "square", decay=12, duty=0.25), tone(1319, 0.18, 0.3, "square", decay=10, duty=0.25)))
save("buy", seq(tone(523, 0.06, 0.3, "square", decay=15), tone(784, 0.12, 0.3, "square", decay=12)))
save("upgrade", seq(*[tone(f, 0.07, 0.28, "square", decay=10, duty=0.3) for f in (523, 659, 784, 1047)]))
save("unlock", seq(*[tone(f, 0.09, 0.3, "square", decay=6, duty=0.4) for f in (392, 523, 659, 784)], tone(1047, 0.35, 0.3, "tri", decay=4)))
save("hire", seq(tone(440, 0.08, 0.3, "tri", decay=8), tone(554, 0.08, 0.3, "tri", decay=8), tone(659, 0.2, 0.3, "tri", decay=6)))
save("mission", mix(seq(*[tone(f, 0.08, 0.25, "square", decay=6, duty=0.25) for f in (659, 784, 988, 1319)]), tone(330, 0.4, 0.15, "tri", decay=3)))
save("error", seq(tone(220, 0.08, 0.3, "square", decay=10), tone(165, 0.14, 0.3, "square", decay=8)))
save("event", seq(tone(784, 0.07, 0.25, "tri", decay=8), tone(784, 0.07, 0.0), tone(988, 0.15, 0.25, "tri", decay=6)))
save("register", mix(seq(tone(1568, 0.05, 0.25, "square", decay=20, duty=0.2), tone(2093, 0.25, 0.25, "square", decay=9, duty=0.2)), tone(0, 0.08, 0.2, "noise", decay=40)))
save("tier", seq(*[tone(f, 0.1, 0.28, "square", decay=5, duty=0.35) for f in (523, 659, 784, 659, 784, 1047)], tone(1047, 0.4, 0.25, "tri", decay=3)))
save("whoosh", tone(300, 0.18, 0.18, "noise", slide=-200, decay=12))
print("ok", sorted(os.listdir(OUT)))
