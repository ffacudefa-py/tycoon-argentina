// Muebles de la 10.0 para los interiores provinciales (ver gen_interiors.py).
// Misma paleta y estilo que furniture.px.js: luz arriba-izquierda, contorno "o".

sprite("_bales", { w: 40, h: 26, outline: "o" },   // fardos de algodón o lana
  (c) => { for (let i = 0; i < 3; i++) { const x = i * 13, y = i === 1 ? 0 : 8; c.rect(x, y, 13, 26 - y, "w"); c.vline(x, y, 26 - y, "W"); c.hline(x, y + 6, 13, "g"); c.hline(x, y + 13, 13, "g"); c.px(x + 4, y + 3, "l"); c.px(x + 9, y + 9, "l") } })

sprite("_sacks", { w: 36, h: 26, outline: "o" },   // bolsas de arroz, harina o yerba
  (c) => { for (let i = 0; i < 3; i++) { const x = i * 12, y = i === 1 ? 0 : 6; c.rect(x, y + 3, 12, 23 - y, "e"); c.rect(x + 2, y, 8, 4, "e"); c.hline(x + 2, y + 3, 8, "M"); c.vline(x, y + 3, 20 - y, "W"); c.rect(x + 3, y + 10, 6, 5, i === 1 ? "n" : "r") } })

sprite("_barrels_wood", { w: 44, h: 30, outline: "o" },   // barricas de roble con duelas y aros
  (c) => { const pos = [[0, 15], [15, 15], [30, 15], [7, 0], [22, 0]]; for (const [x, y] of pos) { c.circ(x + 7, y + 7, 7, "M"); c.circ(x + 7, y + 7, 6, "t"); for (let k = -4; k <= 4; k += 2) c.vline(x + 7 + k, y + 2, 11, "M"); c.ring(x + 7, y + 7, 5, "d"); c.circ(x + 7, y + 7, 2, "m"); c.px(x + 6, y + 6, "T"); c.px(x + 3, y + 3, "W") } })

sprite("_steel_tank", { w: 28, h: 68, outline: "o" },   // tanque de acero (vino, leche, aceite)
  rect(0, 6, 28, 56, "l"), vline(1, 6, 56, "W"), vline(26, 6, 56, "g"), (c) => { c.ellipse(14, 6, 13, 5, "w"); c.ellipse(14, 6, 9, 3, "l") },
  rect(10, 30, 8, 6, "d"), circ(14, 33, 2, "x"), rect(2, 62, 4, 6, "x"), rect(22, 62, 4, 6, "x"), hline(0, 20, 28, "g"), hline(0, 46, 28, "g"))

sprite("_olive_press", { w: 46, h: 48, outline: "o" },   // prensa / molino de aceite
  rect(0, 30, 46, 18, "d"), hline(0, 30, 46, "g"), circ(23, 22, 14, "x"), circ(23, 22, 10, "g"), circ(23, 22, 3, "o"),
  rect(21, 0, 4, 10, "x"), rect(36, 36, 10, 8, "y"), rect(38, 38, 6, 4, "Z"), rect(4, 38, 8, 8, "n"))

sprite("_citrus_crates", { w: 40, h: 28, outline: "o" },   // cajones de limones / naranjas
  (c) => { for (let k = 0; k < 2; k++) for (let i = 0; i < 2; i++) { const x = i * 20, y = 14 - k * 14; c.rect(x, y, 20, 14, "t"); c.hline(x, y, 20, "T"); c.hline(x, y + 7, 20, "M"); for (let j = 0; j < 4; j++) c.circ(x + 3 + j * 5, y + 1, 2, k ? "Z" : "q") } })

sprite("_drying_rack", { w: 60, h: 40, outline: "o" },   // secadero (yerba, pasas)
  rect(0, 0, 4, 40, "M"), rect(56, 0, 4, 40, "M"),
  (c) => { for (let r = 0; r < 3; r++) { const y = 4 + r * 12; c.rect(4, y, 52, 5, "t"); c.hline(4, y, 52, "T"); for (let x = 6; x < 54; x += 4) c.rect(x, y - 2, 3, 2, r === 1 ? "V" : "n") } })

sprite("_oven", { w: 52, h: 56, outline: "o" },   // horno de panadería
  rect(0, 10, 52, 46, "r"), (c) => { for (let y = 12; y < 56; y += 5) for (let x = (y % 2) * 4; x < 52; x += 8) c.hline(x, y, 6, "R") },
  rect(10, 22, 32, 20, "o"), rect(12, 24, 28, 16, "q"), rect(14, 32, 24, 4, "y"), rect(20, 0, 12, 10, "x"), hline(8, 44, 36, "x"))

sprite("_meat_hooks", { w: 42, h: 34, outline: "o" },   // carnes colgadas del riel
  hline(0, 0, 42, "x"), (c) => { for (let i = 0; i < 4; i++) { const x = 3 + i * 10; c.vline(x + 3, 1, 4, "g"); c.rect(x, 5, 7, 16 + (i % 2) * 6, "r"); c.rect(x + 1, 7, 5, 4, "p"); c.px(x + 3, 13, "W") } })

sprite("_cheese_shelf", { w: 44, h: 50, outline: "o" },   // estante de quesos / lácteos
  rect(0, 0, 44, 50, "M"), rect(2, 2, 40, 46, "m"),
  (c) => { for (let r = 0; r < 3; r++) { const y = 14 + r * 15; c.hline(2, y, 40, "t"); for (let k = 0; k < 3; k++) { c.circ(9 + k * 13, y - 5, 5, "Z"); c.hline(4 + k * 13, y - 5, 10, "y"); c.px(7 + k * 13, y - 8, "z") } } })

sprite("_electronics_bench", { w: 70, h: 40, outline: "o" },   // línea de armado de electrónica
  rect(0, 14, 70, 6, "l"), hline(0, 14, 70, "W"), rect(2, 20, 4, 20, "x"), rect(64, 20, 4, 20, "x"),
  rect(6, 0, 18, 13, "x"), rect(8, 2, 14, 9, "B"), rect(28, 4, 14, 9, "o"), rect(30, 6, 10, 5, "C"),
  rect(48, 8, 16, 6, "n"), (c) => { for (let x = 49; x < 63; x += 3) c.px(x, 10, "Z") })

sprite("_potato_bins", { w: 46, h: 26, outline: "o" },   // canastos de papas andinas de colores
  (c) => { const cols = [["t", "M"], ["r", "R"], ["v", "V"]]; for (let i = 0; i < 3; i++) { const x = i * 15; c.rect(x, 8, 15, 18, "S"); c.hline(x, 8, 15, "s"); for (let j = 0; j < 3; j++) c.circ(x + 3 + j * 4, 7, 2, cols[i][j % 2]) } })

sprite("_banana_hooks", { w: 40, h: 40, outline: "o" },   // racimos de banana colgados
  hline(0, 0, 40, "M"), (c) => { for (let i = 0; i < 3; i++) { const x = 2 + i * 13; c.vline(x + 5, 1, 6, "m"); for (let r = 0; r < 4; r++) c.rect(x + (r % 2), 7 + r * 7, 10, 5, r < 2 ? "n" : "Z"); c.px(x + 2, 9, "N") } })

sprite("_apple_bins", { w: 46, h: 28, outline: "o" },   // bins de manzanas y peras
  (c) => { for (let i = 0; i < 2; i++) { const x = i * 23; c.rect(x, 8, 23, 20, "t"); c.hline(x, 8, 23, "T"); c.hline(x, 17, 23, "M"); for (let j = 0; j < 5; j++) c.circ(x + 3 + j * 4, 7, 2, i ? "N" : "r") } })
