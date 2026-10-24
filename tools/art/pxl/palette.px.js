// Paleta 2.0 de Tycoon Argentina (32 colores) para PXL. Ver docs/GUIA_PIXEL_ART.md
pal({
  o: "#1B1A2E", u: "#2E2B48", x: "#4A4766", d: "#6E6B8C", g: "#9B98B5", l: "#C9C7DA", w: "#F0EEE6", W: "#FFFFFF",
  A: "#2F6EA8", B: "#4E8FC9", C: "#74ACDF", c: "#A9D2F2",
  Y: "#B5700A", y: "#F6B40E", Z: "#FFD458", z: "#FFF0A8",
  R: "#7E2230", r: "#B83A3F", p: "#E2665A",
  G: "#2D6A3E", n: "#4C9A4F", N: "#8CCB6C",
  m: "#4A2E22", M: "#7A4B30", t: "#A8714A", T: "#D9A877",
  S: "#8A5A40", s: "#C98E66", f: "#F2C6A0",
  E: "#D8BD8C", e: "#F3E1BC", q: "#E0802F",
  V: "#4E3A7A", v: "#7B5BB5",
})
// Rampas oscuro -> claro: shade() baja un paso, light() sube.
ramps("ouxdglwW", "ABCc", "YqyZz", "Rrp", "GnN", "mMtT", "SsfW", "MEe")

// Cartel con texto (fuente 3x5 de PXL, 4 px por letra): la caja se mide según
// el texto para que ninguna letra quede afuera. Se usa dentro de (c) => {...}.
// cx = centro horizontal; y = borde superior de la caja.
function textWidth(str) { return str.length * 4 - 1 }
function signbox(c, cx, y, str, fg, bg, border, padX = 2, padY = 1) {
  const w = textWidth(str) + padX * 2 + (border ? 2 : 0)
  const h = 5 + padY * 2 + (border ? 2 : 0)
  const x = Math.round(cx - w / 2)
  c.rect(x, y, w, h, bg)
  if (border) c.box(x, y, w, h, border)
  const b = border ? 1 : 0
  c.text(x + b + padX, y + b + padY, str, fg)
  return { x, y, w, h }
}
