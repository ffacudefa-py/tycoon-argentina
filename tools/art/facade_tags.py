"""14.0: mapa de elementos de cada fachada (qué pieza pintó cada píxel).

Vuelve a correr el dibujante de buildings4.py del negocio y anota, por cada
llamada que hace el dibujante (wall, roof, window, awning, sign, crates...), los
píxeles que cambió esa llamada. Devuelve, ya encuadrado igual que fit():
  seq[y, x]  orden de dibujo del elemento (0 = vacío; más alto = más adelante)
  kinds      {seq: "nombre de la función"}
Lo usa facade_light.py para que cada saliente tire sombra sobre lo que tiene
detrás y las aberturas (ventanas, puertas, arcos) queden hundidas en la pared.
"""
import sys

import numpy as np

import buildings4 as B4


def _arr(cv):
    return np.asarray(cv.img, dtype=np.uint8).copy()


def _trace(fn, t, f):
    code = fn.__code__
    seq = None
    kinds = {}
    args = {}
    stack = []
    state = {"cv": None, "n": 0}

    def prof(frame, event, arg):
        nonlocal seq
        if event == "call" and frame.f_back is not None and frame.f_back.f_code is code:
            cv = frame.f_back.f_locals.get("cv")
            if cv is None:
                return
            if state["cv"] is not cv:
                state["cv"] = cv
                seq = np.zeros((cv.h, cv.w), dtype=np.int32)
            loc = {k: v for k, v in frame.f_locals.items() if isinstance(v, (int, float, str))}
            stack.append((frame, frame.f_code.co_name, _arr(cv), loc))
        elif event == "return" and stack and stack[-1][0] is frame:
            _, name, before, loc = stack.pop()
            cv = state["cv"]
            after = _arr(cv)
            ch = (after != before).any(-1)
            if ch.any():
                state["n"] += 1
                seq[ch] = state["n"]
                kinds[state["n"]] = name
                args[state["n"]] = loc
            # pixeles que la pieza dejó transparentes vuelven a 0
            seq[after[..., 3] == 0] = 0

    old = sys.getprofile()
    sys.setprofile(prof)
    try:
        cv = fn(t, f)
    finally:
        sys.setprofile(old)
    return cv, seq, kinds, args


def _dx(frames):
    xs = set().union(*[B4._cols(cv) for cv in frames])
    dx = 0
    if xs:
        x0, x1 = min(xs), max(xs)
        for side in (B4.SIDE, 1):
            if x1 - x0 <= B4.W - side - 1:
                if x1 > B4.W - side:
                    dx = (B4.W - side) - x1
                if x0 + dx < 1:
                    dx = 1 - x0
                break
    return dx


def tags(bid, t):
    """[(seq, kinds, rgba, args)] por cuadro, en el encuadre final W x H.
    args[sid] = argumentos de la llamada (wall: x, y, w, h, kind), x ya corrido por fit."""
    fn = B4._RAW[bid]
    runs = [_trace(fn, t, f) for f in (0, 1)]
    dx = _dx([r[0] for r in runs])
    out = []
    P = B4.PAD
    for cv, seq, kinds, args in runs:
        args = {k: dict(v, x=v["x"] + dx) if "x" in v else v for k, v in args.items()}
        s = np.zeros((B4.H, B4.W), dtype=np.int32)
        img = _arr(cv)
        rg = np.zeros((B4.H, B4.W, 4), dtype=np.uint8)
        for x in range(B4.W):
            sx = x - dx + P
            if 0 <= sx < cv.w:
                s[:, x] = seq[P:P + B4.H, sx]
                rg[:, x] = img[P:P + B4.H, sx]
        out.append((s, kinds, rg, args))
    return out
