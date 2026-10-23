// Paredes y pisos de los interiores (400x170: pared 0..110, piso 110..170).
// room(pared, piso, exterior, nivel) devuelve una función de dibujo para PXL.
include("street.px.js")

function wallPaint(c, base, light, dark, wains) {
  c.rect(0, 0, 400, 110, base)
  c.noise(0, 8, 400, 102, light + dark, 0.025, 7)
  if (wains) { c.rect(0, 78, 400, 32, wains[0]); c.hline(0, 78, 400, wains[1]); c.hline(0, 80, 400, wains[2]) }
}

function room(wall, floor, outdoor, tier) {
  return (c) => {
    if (outdoor) {
      // Vereda vista de cerca: fachadas detrás y baldosas en el piso.
      c.grad(0, 0, 400, 114, "Cc", "v", 0.6)
      const row = ["_fac_c", "_fac_a", "_fac_h", "_fac_g", "_fac_d", "_fac_e"]
      const ws = [72, 64, 56, 64, 60, 48], fl = [2, 2, 2, 2, 3, 1]
      let x = -10
      for (let i = 0; i < row.length; i++) { const h = 18 + fl[i] * 34 + 42; c.stamp(row[i], x, 114 - h); x += ws[i] + 1 }
      c.pattern("baldosas", 0, 114, 400, 56, { reseed: true })
      c.hline(0, 114, 400, "o")
      c.shade([0, 115, 400, 4], 1)
      return
    }
    // ----- pared
    switch (wall) {
      case "azulejo": {   // azulejos blancos con guarda celeste (kiosco, almacén)
        c.rect(0, 0, 400, 110, "w")
        for (let y = 8; y < 110; y += 10) c.hline(0, y, 400, "l")
        for (let y = 8, r = 0; y < 110; y += 10, r++) for (let x = (r % 2) * 5; x < 400; x += 10) c.vline(x, y, 10, "l")
        c.rect(0, 60, 400, 6, "C"); c.hline(0, 60, 400, "c"); c.hline(0, 65, 400, "B")
        for (let x = 4; x < 400; x += 12) c.px(x, 62, "W")
        break
      }
      case "ladrillo": {   // ladrillo visto (parrilla, restaurante)
        c.rect(0, 0, 400, 110, "r")
        for (let y = 6, r = 0; y < 110; y += 6, r++) { c.hline(0, y, 400, "R"); for (let x = (r % 2) * 7; x < 400; x += 14) c.vline(x, y + 1, 5, "R") }
        c.noise(0, 0, 400, 110, "pR", 0.04, 11)
        c.rect(0, 102, 400, 8, "M"); c.hline(0, 102, 400, "t")
        break
      }
      case "madera_pared":   // boiserie de madera (cafetería)
        c.rect(0, 0, 400, 110, "e"); c.noise(0, 0, 400, 64, "E", 0.03, 2)
        c.rect(0, 62, 400, 48, "M"); c.hline(0, 62, 400, "T"); c.hline(0, 63, 400, "t")
        for (let x = 0; x < 400; x += 20) { c.vline(x, 64, 46, "m"); c.box(x + 4, 68, 12, 36, "t") }
        break
      case "chapa":   // chapa acanalada (taller, lavadero, depósito)
        c.rect(0, 0, 400, 110, "g")
        for (let x = 0; x < 400; x += 4) { c.vline(x, 0, 110, "d"); c.vline(x + 1, 0, 110, "l") }
        c.noise(0, 0, 400, 110, "M", 0.008, 5)   // óxido
        c.rect(0, 0, 400, 6, "x")
        break
      case "pintura_super": wallPaint(c, "W", "w", "l", ["r", "p", "R"]); break
      case "pintura_gym": wallPaint(c, "u", "x", "o", ["y", "Z", "Y"]); break
      case "pintura_celeste": wallPaint(c, "c", "W", "C", ["B", "C", "A"]); break
      default: wallPaint(c, "e", "w", "E", null)
    }
    // ventana a la calle en la pared (luz natural) a partir del nivel 2
    if (tier >= 2 && wall !== "chapa") {
      const wx = 340, wy = 14
      c.rect(wx - 2, wy - 2, 44, 40, "M"); c.rect(wx, wy, 40, 36, "c"); c.rect(wx, wy + 22, 40, 14, "C")
      c.rect(wx + 4, wy + 14, 32, 8, "e"); c.vline(wx + 20, wy, 36, "M"); c.line(wx + 4, wy + 30, wx + 14, wy + 4, "W")
    }
    // ----- techo
    c.rect(0, 0, 400, 5, "u"); c.hline(0, 5, 400, "o")
    // ----- piso
    switch (floor) {
      case "damero":
        for (let y = 110; y < 170; y += 6) for (let x = 0; x < 400; x += 10) c.rect(x, y, 10, 6, ((x / 10) + ((y - 110) / 6)) % 2 ? "d" : "w")
        break
      case "madera":
        c.rect(0, 110, 400, 60, "t")
        for (let y = 110, r = 0; y < 170; y += 5, r++) { c.hline(0, y, 400, "M"); for (let x = (r * 23) % 40; x < 400; x += 40) c.vline(x, y + 1, 4, "M") }
        c.noise(0, 110, 400, 60, "T", 0.03, 3)
        break
      case "ceramica":
        c.rect(0, 110, 400, 60, "w")
        for (let y = 110; y < 170; y += 12) c.hline(0, y, 400, "l")
        for (let x = 0; x < 400; x += 16) c.vline(x, 110, 60, "l")
        c.noise(0, 110, 400, 60, "W", 0.04, 4)
        break
      case "goma":
        c.rect(0, 110, 400, 60, "x"); c.noise(0, 110, 400, 60, "du", 0.12, 8)
        for (let x = 0; x < 400; x += 40) c.vline(x, 110, 60, "u")
        break
      default:   // cemento con manchas de aceite y grietas
        c.rect(0, 110, 400, 60, "g"); c.noise(0, 110, 400, 60, "dl", 0.06, 6)
        for (const [x, y, r] of [[70, 152, 9], [210, 136, 6], [330, 162, 11], [150, 164, 5]]) c.ellipse(x, y, r, Math.max(2, r / 3), "d")
        c.line(20, 126, 60, 146, "d"); c.line(260, 118, 290, 134, "d")
        for (let x = 0; x < 400; x += 80) c.vline(x, 110, 60, "d")
    }
    c.rect(0, 108, 400, 3, "M"); c.hline(0, 108, 400, "t")          // zócalo
    c.shade([0, 111, 400, 6], 1)                                   // sombra contra la pared
  }
}
