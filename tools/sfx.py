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
# "coin" ya no se sintetiza (15.0): son los 5 golpes de coin.mp3, ver tools/audio/split_coin.sh.
# tap, buy, upgrade, unlock, hire, mission, event, register, tier y whoosh vienen de FL Studio: ver tools/audio/import_sfx.py.
save("error", seq(tone(220, 0.08, 0.3, "square", decay=10), tone(165, 0.14, 0.3, "square", decay=8)))
# 11.2: minijuegos (asalto y coima).
save("shot", mix(tone(0, 0.16, 0.55, "noise", decay=22), tone(140, 0.12, 0.45, "square", slide=-90, decay=18, duty=0.5)))
save("hit", mix(tone(90, 0.14, 0.5, "square", slide=-40, decay=14), tone(0, 0.08, 0.3, "noise", decay=30)))
save("ricochet", seq(tone(2400, 0.04, 0.25, "square", decay=20, duty=0.2), tone(1800, 0.16, 0.22, "tri", slide=-1200, decay=8)))
save("empty", tone(1800, 0.03, 0.3, "square", decay=60, duty=0.15))
save("reload", seq(tone(900, 0.03, 0.25, "square", decay=50, duty=0.2), tone(0, 0.08, 0.0), tone(700, 0.03, 0.25, "square", decay=50, duty=0.2), tone(0, 0.1, 0.0), tone(1200, 0.06, 0.3, "square", decay=30, duty=0.3)))
save("bag", mix(tone(0, 0.12, 0.3, "noise", slide=-100, decay=16), seq(tone(988, 0.05, 0.22, "square", decay=14, duty=0.25), tone(1319, 0.14, 0.22, "square", decay=10, duty=0.25))))
save("alarm", seq(*[tone(f, 0.16, 0.3, "square", decay=2, duty=0.5) for f in (880, 660, 880, 660)]))
save("siren", seq(tone(600, 0.45, 0.28, "tri", slide=500, decay=1.5), tone(1100, 0.45, 0.28, "tri", slide=-500, decay=1.5)))
save("swipe", tone(500, 0.12, 0.22, "noise", slide=900, decay=14))
save("shred", mix(tone(0, 0.28, 0.25, "noise", decay=6), tone(70, 0.28, 0.25, "square", decay=6, duty=0.3)))
save("stamp", mix(tone(110, 0.12, 0.5, "square", slide=-50, decay=20), tone(0, 0.06, 0.35, "noise", decay=40)))
save("buzzer", tone(110, 0.5, 0.4, "square", decay=3, duty=0.45))
save("tick", tone(1400, 0.03, 0.25, "square", decay=50, duty=0.3))
print("ok", sorted(os.listdir(OUT)))
