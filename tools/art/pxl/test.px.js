include("palette.px.js")
// Mostrador de madera con frente de vitrina
sprite("_counter", { w: 64, h: 30, outline: "o" },
  rect(0, 0, 64, 4, "T"), hline(0, 0, 64, "e"), hline(0, 3, 64, "t"),      // tapa
  rect(1, 4, 62, 26, "M"), vline(1, 4, 26, "t"), vline(62, 4, 26, "m"),
  (c) => { for (let x = 6; x < 60; x += 14) { c.rect(x, 8, 10, 18, "t"); c.box(x, 8, 10, 18, "m"); c.vline(x + 1, 9, 16, "T") } },
  rect(1, 27, 62, 3, "m"))
// Estantería con mercadería variada
sprite("_shelf", { w: 48, h: 64, outline: "o" },
  rect(0, 0, 48, 64, "M"), rect(2, 2, 44, 60, "m"),
  (c) => {
    const goods = ["r", "y", "n", "B", "q", "p", "N", "Z", "c", "R"]
    for (let row = 0; row < 4; row++) {
      const y = 4 + row * 15
      c.rect(2, y + 11, 44, 2, "t"); c.hline(2, y + 11, 44, "T")
      let x = 4, i = row * 3
      while (x < 42) {
        const w = 3 + (i % 3), h = 6 + ((i * 7) % 4), col = goods[i % goods.length]
        c.rect(x, y + 11 - h, w, h, col); c.vline(x, y + 11 - h, h, "W"); c.hline(x, y + 11 - h, w, "W")
        x += w + 1; i++
      }
    }
  })
// Heladera de bebidas con luz interior
sprite("_fridge", { w: 30, h: 66, outline: "o" },
  rect(0, 0, 30, 66, "r"), vline(0, 0, 66, "p"), vline(29, 0, 66, "R"),
  rect(0, 0, 30, 9, "W"), text(3, 2, "FRIO", "r"),
  rect(3, 11, 24, 50, "c"), rect(3, 11, 24, 50, "c"),
  (c) => { for (let r = 0; r < 4; r++) { const y = 14 + r * 12; c.hline(3, y + 9, 24, "l")
    for (let x = 4; x < 26; x += 4) { const col = ["r", "n", "y", "q", "B"][(x + r) % 5]; c.rect(x, y + 2, 3, 7, col); c.px(x, y + 1, "x"); c.px(x, y + 3, "W") } } },
  dither(3, 11, 24, 50, ".", "W", 0.08), rect(26, 30, 2, 10, "l"))
// Caja registradora
sprite("_register", { w: 22, h: 18, outline: "o" },
  poly([2, 6, 20, 6, 22, 18, 0, 18], "d"), rect(3, 8, 16, 6, "x"),
  (c) => { for (let i = 0; i < 4; i++) for (let j = 0; j < 2; j++) c.rect(4 + i * 4, 9 + j * 3, 3, 2, "l") },
  rect(5, 0, 12, 6, "u"), rect(6, 1, 10, 4, "N"), text(7, 1, "$", "G"), hline(0, 17, 22, "x"))

scene("prueba", { w: 200, h: 90, bg: "e" },
  rect(0, 70, 200, 20, "E"),
  stamp("_shelf", 4, 6), stamp("_fridge", 56, 4), stamp("_counter", 100, 50), stamp("_register", 120, 32))
