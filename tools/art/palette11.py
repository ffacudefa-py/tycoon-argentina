"""Paleta 11 (docs/style-guide.md): cálida y saturada, contornos marrones.

Se suma a px2.PAL con prefijo "i" para no pisar la paleta anterior. Rampas
(sombra, medio, luz, brillo) por material.
"""
from px2 import PAL

COLORS = {
    "iO": "#3D1B0B", "iS": "#8E461F", "iW": "#94552A", "iM": "#C88555", "iA": "#E4AD69",
    "iG": "#F2D173", "iGh": "#F7EDA4", "iC": "#F6EFE2", "iCs": "#E4D7C7",
    "iSky1": "#3DB4FE", "iSky2": "#60CAFE", "iSky3": "#AFE6F2", "iWat": "#287AB2", "iWat2": "#4F9FD0",
    "iGr1": "#2E7D4F", "iGr2": "#3F9E5E", "iGr3": "#67D08E", "iGr4": "#A8E6A0",
    "iK1": "#F3D2B6", "iK2": "#E3A988", "iK3": "#B87259", "iBl": "#EE8F86", "iMo": "#B8323C", "iTo": "#F08C8F",
    "iEye": "#2A1A14", "iWh": "#FFFFFF", "iSw": "#9FDCFF",
}

RAMPS = {
    "rojo": ("#953730", "#D5576E", "#F08C8F", "#FFC4C4"),
    "azul": ("#2F5FA0", "#4E8FD8", "#8FC4FF", "#D0E8FF"),
    "celeste": ("#3E86C4", "#74ACDF", "#BDE2FF", "#FFFFFF"),
    "verde": ("#2E7D4F", "#3F9E5E", "#67D08E", "#B6F0B0"),
    "amarillo": ("#C07A12", "#F6B40E", "#FFE07A", "#FFF6C8"),
    "naranja": ("#B5541F", "#E8823A", "#FFB070", "#FFE0B8"),
    "violeta": ("#5E3D8C", "#8A63C2", "#B99BE6", "#E6D8FF"),
    "blanco": ("#C9BFB0", "#EDE6DA", "#FFFFFF", "#FFFFFF"),
    "marron": ("#6D432B", "#94552A", "#C88555", "#E4AD69"),
    "noche": ("#3B3560", "#575089", "#7C75B0", "#A8A2D6"),
    "gris": ("#6E6B8C", "#9B98B5", "#C9C7DA", "#F0EEE6"),
    "pelo_negro": ("#20130E", "#3A2418", "#5A3A28", "#7A5440"),
    "pelo_castano": ("#5A3520", "#8A5630", "#B87A48", "#D8A070"),
    "pelo_rubio": ("#B07A28", "#E0B050", "#FFE090", "#FFF4C8"),
    "pelo_rojo": ("#8A3020", "#C25A34", "#E8905A", "#FFC090"),
    "pelo_canoso": ("#8E8AA8", "#C2BFD6", "#E8E6F2", "#FFFFFF"),
}


def install():
    PAL.update(COLORS)
    for name, tones in RAMPS.items():
        for i, h in enumerate(tones):
            PAL["i_%s%d" % (name, i)] = h


def ramp(name):
    return tuple("i_%s%d" % (name, i) for i in range(4))


install()
