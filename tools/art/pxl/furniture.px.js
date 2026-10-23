// Mobiliario y equipamiento de los negocios (pixel art 2.0, PXL).
// Escala 1 m = 24 px. Luz arriba-izquierda, contorno "o".
// Todas las piezas son partes ("_"): las usan las escenas de interiores.
include("palette.px.js")

const GOODS = ["r", "y", "n", "B", "q", "p", "N", "Z", "c", "R", "G", "A"]

// Fila de mercadería sobre un estante (alturas y anchos variados, con brillo).
function goodsRow(c, x0, x1, base, seed, maxH = 9) {
  let x = x0, i = seed
  while (x < x1 - 2) {
    const w = 2 + (i % 3), h = Math.max(4, maxH - ((i * 7) % 5)), col = GOODS[(i * 5 + seed) % GOODS.length]
    if (x + w > x1) break
    c.rect(x, base - h, w, h, col)
    c.vline(x, base - h, h, "W")
    if (w > 2) c.hline(x, base - h, w, "W")
    if (h > 6 && w > 2) c.hline(x, base - h + 3, w, "w")        // etiqueta
    x += w + 1; i++
  }
}

// ---------------------------------------------------------------- mostradores

sprite("_counter_wood", { w: 72, h: 32, outline: "o" },
  rect(0, 0, 72, 5, "T"), hline(0, 0, 72, "e"), hline(0, 4, 72, "t"),
  rect(1, 5, 70, 27, "M"), vline(1, 5, 27, "t"), vline(70, 5, 27, "m"),
  (c) => { for (let x = 5; x < 66; x += 16) { c.rect(x, 9, 12, 18, "t"); c.box(x, 9, 12, 18, "m"); c.vline(x + 1, 10, 16, "T"); c.hline(x + 1, 10, 10, "T") } },
  rect(1, 29, 70, 3, "m"))

// Vitrina de vidrio con productos (kiosco, panadería, fiambrería)
sprite("_counter_glass", { w: 72, h: 32, outline: "o" },
  rect(0, 0, 72, 3, "l"), hline(0, 0, 72, "W"),
  rect(1, 3, 70, 16, "c"), (c) => { goodsRow(c, 3, 69, 12, 2, 7); goodsRow(c, 3, 69, 18, 5, 5); c.hline(1, 12, 70, "l") },
  dither(1, 3, 70, 16, ".", "W", 0.06), line(4, 17, 14, 4, "W"),
  rect(1, 19, 70, 13, "d"), hline(1, 19, 70, "g"), vline(70, 19, 13, "x"),
  (c) => { for (let x = 6; x < 66; x += 12) c.rect(x, 23, 8, 6, "x") })

// Mostrador de chapa/acero (taller, lavadero, depósito)
sprite("_counter_metal", { w: 64, h: 30, outline: "o" },
  rect(0, 0, 64, 4, "l"), hline(0, 0, 64, "W"),
  rect(1, 4, 62, 26, "g"), (c) => { for (let x = 3; x < 62; x += 4) c.vline(x, 5, 24, "d") },
  vline(62, 4, 26, "x"), rect(1, 27, 62, 3, "x"))

sprite("_register", { w: 22, h: 18, outline: "o" },
  poly([2, 6, 20, 6, 22, 18, 0, 18], "d"), rect(3, 8, 16, 6, "x"),
  (c) => { for (let i = 0; i < 4; i++) for (let j = 0; j < 2; j++) c.rect(4 + i * 4, 9 + j * 3, 3, 2, "l") },
  rect(5, 0, 12, 6, "u"), rect(6, 1, 10, 4, "N"), px(9, 2, "G"), px(10, 2, "G"), px(12, 2, "G"), hline(0, 17, 22, "x"))

sprite("_scale", { w: 18, h: 14, outline: "o" },
  ellipse(9, 3, 8, 2, "l"), rect(7, 5, 4, 3, "g"), rect(1, 8, 16, 6, "W"), rect(3, 10, 7, 2, "u"), px(4, 10, "N"), px(6, 10, "N"), hline(1, 13, 16, "l"))

sprite("_slicer", { w: 22, h: 16, outline: "o" },  // cortadora de fiambre
  rect(0, 10, 22, 6, "p"), hline(0, 10, 22, "W"), circ(10, 7, 6, "l"), ring(10, 7, 6, "g"), circ(10, 7, 2, "d"),
  rect(16, 4, 5, 6, "r"), rect(2, 12, 4, 2, "r"))

sprite("_mate_set", { w: 16, h: 12, outline: "o" },   // termo + mate sobre el mostrador
  rect(0, 0, 5, 12, "l"), rect(0, 0, 5, 2, "d"), vline(0, 2, 10, "W"),
  ellipse(11, 8, 4, 4, "M"), ellipse(10, 7, 2, 2, "t"), rect(8, 4, 6, 2, "y"), hline(8, 3, 6, "n"), vline(12, 0, 4, "l"))

// ---------------------------------------------------------------- estanterías

sprite("_shelf_wood", { w: 50, h: 70, outline: "o" },
  rect(0, 0, 50, 70, "M"), rect(2, 3, 46, 65, "m"), hline(0, 0, 50, "t"),
  (c) => { for (let r = 0; r < 4; r++) { const y = 17 + r * 16; c.rect(2, y, 46, 2, "t"); c.hline(2, y, 46, "T"); goodsRow(c, 3, 47, y, r * 4 + 1, 12) } })

sprite("_shelf_metal", { w: 50, h: 72, outline: "o" },
  rect(0, 0, 3, 72, "g"), rect(47, 0, 3, 72, "g"), vline(0, 0, 72, "l"),
  rect(3, 0, 44, 72, "l"), (c) => { for (let y = 2; y < 72; y += 3) c.hline(3, y, 44, "w") },
  (c) => { for (let r = 0; r < 4; r++) { const y = 16 + r * 17; c.rect(0, y, 50, 3, "d"); c.hline(0, y, 50, "g"); goodsRow(c, 4, 46, y, r * 3 + 7, 13) } })

// Estantería de almacén: frascos, latas y yerba
sprite("_shelf_almacen", { w: 56, h: 74, outline: "o" },
  rect(0, 0, 56, 74, "M"), rect(2, 3, 52, 69, "m"), rect(0, 0, 56, 3, "t"),
  (c) => {
    for (let r = 0; r < 4; r++) {
      const y = 18 + r * 17
      c.rect(2, y, 52, 2, "t"); c.hline(2, y, 52, "T")
      for (let x = 4, i = 0; x < 50; i++) {
        const kind = (i + r) % 3
        if (kind === 0) { c.rect(x, y - 10, 6, 10, "c"); c.rect(x, y - 11, 6, 2, "r"); c.rect(x + 1, y - 7, 4, 5, ["y", "q", "R", "N"][i % 4]); c.vline(x, y - 10, 9, "W"); x += 7 }      // frasco
        else if (kind === 1) { c.rect(x, y - 7, 5, 7, ["l", "y", "r"][i % 3]); c.hline(x, y - 4, 5, "o"); c.vline(x, y - 7, 7, "W"); x += 6 }     // lata
        else { c.rect(x, y - 12, 7, 12, "n"); c.rect(x + 1, y - 9, 5, 5, "y"); c.hline(x, y - 12, 7, "N"); x += 8 }                               // paquete de yerba
      }
    }
  })

// Góndola de supermercado (doble faz, con cenefa de precio)
sprite("_gondola", { w: 70, h: 64, outline: "o" },
  rect(0, 0, 70, 64, "l"), rect(0, 0, 70, 5, "r"), hline(0, 0, 70, "p"), text(26, 0, "OFERTA", "W"),
  (c) => { for (let r = 0; r < 3; r++) { const y = 22 + r * 17; c.rect(0, y, 70, 3, "g"); c.hline(0, y, 70, "W"); goodsRow(c, 2, 68, y, r * 5 + 3, 14); for (let x = 6; x < 64; x += 18) c.rect(x, y + 1, 5, 2, "y") } },
  rect(0, 58, 70, 6, "d"))

sprite("_fridge_drinks", { w: 32, h: 70, outline: "o" },
  rect(0, 0, 32, 70, "r"), vline(0, 0, 70, "p"), vline(31, 0, 70, "R"),
  rect(0, 0, 32, 10, "W"), text(5, 2, "FRIO", "r"),
  rect(3, 12, 26, 52, "c"),
  (c) => { for (let r = 0; r < 4; r++) { const y = 15 + r * 12; c.hline(3, y + 10, 26, "l")
    for (let x = 4; x < 28; x += 4) { const col = ["r", "n", "y", "q", "B", "R"][(x + r * 2) % 6]; c.rect(x, y + 2, 3, 8, col); c.px(x + 1, y, "x"); c.px(x + 1, y + 1, col); c.px(x, y + 3, "W") } } },
  dither(3, 12, 26, 52, ".", "W", 0.07), rect(28, 32, 2, 10, "l"), rect(0, 64, 32, 6, "R"))

sprite("_freezer", { w: 46, h: 30, outline: "o" },   // freezer de helados horizontal
  rect(0, 6, 46, 24, "W"), vline(0, 6, 24, "W"), vline(45, 6, 24, "l"), rect(0, 26, 46, 4, "l"),
  rect(2, 0, 42, 7, "c"), dither(2, 0, 42, 7, ".", "W", 0.2), (c) => { for (let x = 4; x < 42; x += 6) c.rect(x, 2, 4, 4, ["p", "N", "Z", "T", "c"][x % 5]) },
  rect(4, 12, 38, 8, "C"), text(9, 13, "HELADOS", "W"))

// ---------------------------------------------------------------- comida

sprite("_grill", { w: 64, h: 40, outline: "o" },   // parrilla con chorizos y brasas
  rect(0, 14, 64, 26, "x"), hline(0, 14, 64, "d"), rect(2, 34, 60, 6, "u"),
  rect(2, 8, 60, 6, "o"), (c) => { for (let x = 3; x < 62; x += 3) c.vline(x, 8, 6, "g") },
  (c) => { for (let i = 0; i < 6; i++) { const x = 4 + i * 10; c.rect(x, 5, 8, 4, i % 2 ? "R" : "q"); c.hline(x, 5, 8, i % 2 ? "p" : "Z") } },
  rect(4, 18, 56, 10, "Y"), dither(4, 18, 56, 10, "r", "y", 0.5), dither(4, 22, 56, 6, "p", "R", 0.4))

sprite("_stove", { w: 60, h: 46, outline: "o" },   // cocina industrial con ollas
  rect(0, 12, 60, 34, "l"), hline(0, 12, 60, "W"), rect(0, 12, 60, 4, "g"),
  (c) => { for (let x = 4; x < 56; x += 18) { c.rect(x, 22, 14, 12, "x"); c.box(x, 22, 14, 12, "d"); c.rect(x + 5, 37, 4, 3, "d") } },
  ellipse(14, 9, 10, 4, "g"), rect(5, 4, 18, 8, "l"), hline(5, 4, 18, "W"), ellipse(14, 4, 9, 2, "p"),
  rect(34, 6, 18, 6, "d"), hline(34, 6, 18, "l"), rect(50, 7, 8, 2, "x"))

sprite("_prep_table", { w: 56, h: 36, outline: "o" },
  rect(0, 6, 56, 4, "l"), hline(0, 6, 56, "W"), rect(2, 10, 3, 26, "g"), rect(51, 10, 3, 26, "g"), rect(2, 24, 52, 3, "d"),
  rect(8, 0, 14, 6, "T"), hline(8, 0, 14, "e"), rect(28, 1, 10, 5, "r"), circ(46, 3, 3, "n"), px(45, 2, "N"))

sprite("_coffee_machine", { w: 40, h: 34, outline: "o" },
  rect(0, 6, 40, 28, "l"), rect(0, 6, 40, 4, "W"), rect(0, 0, 40, 7, "d"), hline(0, 0, 40, "g"),
  (c) => { for (let x = 6; x < 34; x += 14) { c.rect(x, 12, 8, 6, "x"); c.rect(x + 2, 18, 4, 3, "u"); c.rect(x + 1, 24, 6, 6, "W"); c.rect(x + 1, 25, 6, 2, "M") } },
  circ(33, 14, 3, "B"), px(32, 13, "c"), rect(0, 30, 40, 4, "g"))

sprite("_pastry_case", { w: 60, h: 34, outline: "o" },   // vitrina de medialunas y facturas
  rect(0, 0, 60, 18, "c"), poly([0, 0, 60, 0, 56, 18, 4, 18], "c"), line(5, 15, 15, 2, "W"),
  (c) => { for (let r = 0; r < 2; r++) for (let x = 6; x < 54; x += 8) { const y = 6 + r * 7; c.ellipse(x + 2, y, 3, 2, r ? "Z" : "q"); c.px(x + 1, y - 1, "z") } },
  rect(0, 18, 60, 16, "M"), hline(0, 18, 60, "t"), rect(4, 22, 52, 9, "m"))

sprite("_dining_table", { w: 40, h: 30, outline: "o" },   // mesa con mantel y 2 sillas
  rect(4, 8, 32, 5, "W"), poly([2, 13, 38, 13, 36, 20, 4, 20], "w"), (c) => { for (let x = 4; x < 36; x += 6) c.rect(x, 13, 3, 7, "r") },
  rect(18, 20, 4, 10, "M"), rect(0, 12, 4, 18, "M"), rect(0, 4, 4, 9, "t"), rect(36, 12, 4, 18, "M"), rect(36, 4, 4, 9, "t"),
  rect(10, 5, 4, 3, "W"), rect(22, 3, 3, 5, "R"), px(23, 2, "n"))

sprite("_cafe_table", { w: 34, h: 28, outline: "o" },
  ellipse(17, 8, 13, 3, "T"), hline(5, 6, 24, "e"), rect(16, 11, 3, 14, "x"), rect(10, 25, 15, 3, "x"),
  rect(0, 10, 4, 18, "u"), rect(0, 4, 5, 7, "x"), rect(30, 10, 4, 18, "u"), rect(29, 4, 5, 7, "x"),
  rect(10, 3, 5, 3, "W"), rect(11, 4, 3, 1, "M"), ellipse(22, 4, 3, 1, "q"))

sprite("_chalkboard", { w: 34, h: 26, outline: "o" },
  rect(0, 0, 34, 26, "M"), rect(2, 2, 30, 22, "u"), text(5, 4, "MENU", "W"),
  hline(5, 12, 16, "l"), hline(24, 12, 5, "Z"), hline(5, 16, 13, "l"), hline(24, 16, 5, "Z"), hline(5, 20, 18, "l"), hline(26, 20, 4, "Z"))

sprite("_wine_rack", { w: 30, h: 56, outline: "o" },
  rect(0, 0, 30, 56, "M"), rect(2, 2, 26, 52, "m"),
  (c) => { for (let r = 0; r < 6; r++) for (let k = 0; k < 4; k++) { const x = 4 + k * 6, y = 5 + r * 8; c.circ(x + 2, y + 2, 2, ["R", "G", "R", "Y"][(r + k) % 4]); c.px(x + 1, y + 1, "p") } })

// ---------------------------------------------------------------- autos y talleres

sprite("_car", { w: 64, h: 30, outline: "o" },
  poly([14, 0, 44, 0, 52, 11, 6, 11], "r"), poly([17, 2, 29, 2, 29, 10, 11, 10], "c"), poly([32, 2, 43, 2, 49, 10, 32, 10], "c"),
  line(18, 3, 22, 9, "W"), rect(0, 11, 64, 12, "r"), hline(0, 11, 64, "p"), hline(0, 22, 64, "R"),
  rect(58, 13, 6, 3, "Z"), rect(0, 13, 4, 3, "p"), hline(30, 16, 6, "R"),
  circ(14, 23, 6, "o"), circ(14, 23, 3, "g"), circ(50, 23, 6, "o"), circ(50, 23, 3, "g"))

sprite("_car_lift", { w: 84, h: 64, outline: "o" },   // elevador de dos columnas con auto arriba
  rect(0, 0, 8, 64, "y"), rect(76, 0, 8, 64, "y"), vline(0, 0, 64, "Z"), vline(76, 0, 64, "Z"),
  (c) => { for (let y = 4; y < 60; y += 6) { c.hline(1, y, 6, "Y"); c.hline(77, y, 6, "Y") } },
  rect(8, 30, 68, 4, "d"), hline(8, 30, 68, "g"), stamp("_car", 10, 2), rect(0, 60, 84, 4, "x"))

sprite("_tool_wall", { w: 60, h: 40, outline: "o" },
  rect(0, 0, 60, 40, "t"), (c) => { for (let y = 3; y < 40; y += 4) for (let x = 3; x < 60; x += 4) c.px(x, y, "M") },
  rect(4, 4, 3, 16, "g"), rect(3, 4, 5, 4, "d"), rect(12, 4, 2, 18, "r"), rect(11, 4, 4, 5, "o"),
  rect(20, 6, 14, 3, "l"), rect(20, 9, 3, 8, "l"), ring(42, 12, 6, "x"), rect(52, 4, 3, 20, "q"),
  rect(4, 26, 22, 10, "r"), hline(4, 26, 22, "p"), rect(30, 28, 26, 8, "d"), (c) => { for (let x = 31; x < 56; x += 3) c.vline(x, 29, 6, "g") })

sprite("_tires", { w: 24, h: 36, outline: "o" },
  (c) => { for (let i = 0; i < 4; i++) { const y = 28 - i * 8; c.ellipse(12, y, 11, 4, "u"); c.ellipse(12, y, 6, 2, "x"); c.hline(3, y - 2, 18, "x") } })

sprite("_drums", { w: 32, h: 28, outline: "o" },
  rect(0, 4, 14, 24, "A"), ellipse(7, 4, 7, 2, "B"), hline(0, 12, 14, "u"), hline(0, 20, 14, "u"), rect(3, 13, 6, 6, "y"),
  rect(16, 6, 14, 22, "r"), ellipse(23, 6, 7, 2, "p"), hline(16, 14, 14, "R"), hline(16, 21, 14, "R"))

sprite("_workbench", { w: 60, h: 34, outline: "o" },
  rect(0, 10, 60, 5, "M"), hline(0, 10, 60, "t"), rect(2, 15, 4, 19, "m"), rect(54, 15, 4, 19, "m"), rect(2, 26, 56, 3, "m"),
  rect(6, 2, 12, 8, "r"), hline(6, 2, 12, "p"), rect(24, 5, 16, 5, "d"), circ(48, 6, 4, "g"), rect(10, 18, 14, 8, "A"), rect(32, 19, 16, 7, "q"))

// Lavadero: bahía con espuma y manguera
sprite("_wash_bay", { w: 96, h: 60, outline: "o" },
  rect(0, 0, 96, 6, "B"), hline(0, 0, 96, "C"), rect(0, 6, 5, 54, "g"), rect(91, 6, 5, 54, "g"),
  stamp("_car", 16, 26, { swap: { r: "A", p: "B", R: "u" } }),
  (c) => { const pts = [[18, 30], [30, 26], [44, 28], [58, 25], [70, 30], [26, 40], [62, 42]]; for (const [x, y] of pts) { c.circ(x, y, 4, "W"); c.circ(x - 1, y - 1, 2, "w") } },
  rect(8, 8, 3, 30, "x"), line(9, 38, 18, 50, "n", 2), rect(0, 56, 96, 4, "c"))

sprite("_vacuum", { w: 16, h: 34, outline: "o" },
  rect(0, 10, 16, 24, "q"), hline(0, 10, 16, "Z"), rect(3, 14, 10, 6, "u"), text(4, 15, "$", "Z"),
  line(14, 10, 14, 0, "x", 2), line(14, 0, 4, 2, "x", 2))

// ---------------------------------------------------------------- gimnasio

sprite("_treadmill", { w: 50, h: 40, outline: "o" },
  poly([4, 30, 46, 30, 50, 38, 0, 38], "u"), hline(4, 30, 42, "x"), rect(6, 32, 38, 3, "o"),
  line(40, 30, 40, 4, "d", 3), rect(32, 0, 16, 8, "x"), rect(34, 2, 10, 4, "N"))

sprite("_weight_rack", { w: 46, h: 46, outline: "o" },
  rect(0, 0, 4, 46, "x"), rect(42, 0, 4, 46, "x"), rect(0, 14, 46, 3, "d"), rect(0, 32, 46, 3, "d"),
  (c) => { for (let k = 0; k < 2; k++) for (let i = 0; i < 4; i++) { const y = 6 + k * 18; c.rect(6 + i * 9, y, 7, 8, ["o", "r", "A", "o"][i]); c.vline(6 + i * 9, y, 8, "g") } })

sprite("_bench_press", { w: 54, h: 34, outline: "o" },
  rect(14, 20, 26, 5, "r"), hline(14, 20, 26, "p"), rect(16, 25, 3, 9, "x"), rect(36, 25, 3, 9, "x"),
  rect(2, 4, 4, 30, "x"), rect(48, 4, 4, 30, "x"), rect(0, 6, 54, 2, "l"), rect(0, 1, 6, 12, "o"), rect(48, 1, 6, 12, "o"))

sprite("_punching_bag", { w: 18, h: 50, outline: "o" },
  vline(9, 0, 8, "d"), rect(2, 8, 14, 38, "r"), vline(2, 8, 38, "p"), vline(15, 8, 38, "R"), rect(2, 20, 14, 3, "o"), rect(4, 46, 10, 4, "R"))

sprite("_mirror", { w: 70, h: 46, outline: "o" },
  rect(0, 0, 70, 46, "g"), rect(2, 2, 66, 42, "c"), dither(2, 2, 66, 42, ".", "W", 0.08), line(8, 40, 30, 4, "W"), line(14, 40, 36, 4, "W"))

// ---------------------------------------------------------------- oficina, depósito, fábrica

sprite("_desk_pc", { w: 52, h: 38, outline: "o" },
  rect(0, 16, 52, 4, "T"), hline(0, 16, 52, "e"), rect(2, 20, 4, 18, "M"), rect(46, 20, 4, 18, "M"), rect(30, 20, 16, 14, "t"), rect(32, 24, 12, 2, "M"),
  rect(8, 0, 22, 14, "u"), rect(10, 2, 18, 9, "B"), dither(10, 2, 18, 9, ".", "c", 0.3), rect(17, 14, 4, 2, "x"), rect(8, 13, 18, 3, "l"),
  rect(36, 10, 8, 6, "W"), rect(37, 11, 6, 2, "M"))

sprite("_filing", { w: 22, h: 46, outline: "o" },
  rect(0, 0, 22, 46, "g"), vline(0, 0, 46, "l"), (c) => { for (let k = 0; k < 4; k++) { const y = 2 + k * 11; c.rect(2, y, 18, 9, "l"); c.rect(8, y + 3, 6, 2, "x") } })

sprite("_water_cooler", { w: 16, h: 44, outline: "o" },
  rect(3, 0, 10, 14, "c"), rect(4, 1, 3, 10, "W"), rect(0, 14, 16, 30, "W"), vline(15, 14, 30, "l"), rect(5, 20, 3, 3, "B"), rect(9, 20, 3, 3, "r"))

sprite("_parcel_shelf", { w: 60, h: 66, outline: "o" },
  rect(0, 0, 3, 66, "x"), rect(57, 0, 3, 66, "x"),
  (c) => { for (let r = 0; r < 3; r++) { const y = 20 + r * 22; c.rect(0, y, 60, 3, "d"); c.hline(0, y, 60, "g")
    for (let x = 4, i = 0; x < 54; i++) { const w = 9 + ((i + r) % 3) * 3, h = 10 + ((i * 3 + r) % 3) * 3; if (x + w > 56) break
      c.rect(x, y - h, w, h, "t"); c.hline(x, y - h, w, "T"); c.vline(x + Math.floor(w / 2), y - h, h, "E"); c.rect(x + 1, y - h + 2, 3, 2, "W"); x += w + 1 } } })

sprite("_pallet_rack", { w: 80, h: 80, outline: "o" },
  rect(0, 0, 4, 80, "A"), rect(76, 0, 4, 80, "A"), rect(38, 0, 4, 80, "A"),
  (c) => { for (let r = 0; r < 3; r++) { const y = 24 + r * 27; c.rect(0, y, 80, 4, "q"); c.hline(0, y, 80, "Z")
    for (let k = 0; k < 2; k++) { const x = 6 + k * 38; c.rect(x, y - 3, 30, 3, "t"); c.rect(x + 1, y - 21, 28, 18, ["t", "W", "n"][(r + k) % 3] === "W" ? "l" : "t")
      c.hline(x + 1, y - 21, 28, "T"); c.vline(x + 14, y - 21, 18, "E"); c.rect(x + 3, y - 18, 6, 4, "W") } } })

sprite("_forklift", { w: 50, h: 42, outline: "o" },
  rect(14, 14, 28, 20, "y"), hline(14, 14, 28, "Z"), rect(16, 2, 20, 3, "x"), rect(16, 2, 3, 14, "x"), rect(33, 2, 3, 14, "x"),
  rect(20, 18, 12, 10, "u"), rect(4, 4, 4, 34, "d"), rect(0, 34, 18, 3, "g"), rect(40, 20, 8, 12, "Y"),
  circ(20, 36, 6, "o"), circ(20, 36, 2, "g"), circ(40, 37, 5, "o"), circ(40, 37, 2, "g"))

sprite("_dock_door", { w: 70, h: 72, outline: "o" },
  rect(0, 0, 70, 72, "x"), rect(4, 4, 62, 68, "g"), (c) => { for (let y = 6; y < 72; y += 5) c.hline(4, y, 62, "d") },
  rect(4, 46, 62, 26, "u"), rect(26, 4, 18, 6, "y"), text(29, 4, "D1", "o"))

sprite("_pallet_boxes", { w: 34, h: 30, outline: "o" },
  rect(0, 26, 34, 4, "t"), (c) => { for (let k = 0; k < 2; k++) for (let j = 0; j < 2; j++) { const x = 1 + k * 16, y = 2 + j * 12; c.rect(x, y, 15, 12, "t"); c.hline(x, y, 15, "T"); c.vline(x + 7, y, 12, "E"); c.box(x, y, 15, 12, "M") } })

sprite("_scooter", { w: 40, h: 32, outline: "o" },
  circ(8, 26, 6, "o"), circ(8, 26, 2, "g"), circ(33, 26, 6, "o"), circ(33, 26, 2, "g"),
  poly([8, 18, 30, 18, 36, 26, 4, 26], "r"), hline(8, 18, 22, "p"), rect(26, 6, 3, 14, "x"), rect(22, 4, 10, 3, "x"),
  rect(4, 6, 14, 12, "q"), hline(4, 6, 14, "Z"), text(6, 9, "EX", "W"))

// ---------------------------------------------------------------- decoración argentina

sprite("_clock", { w: 16, h: 16, outline: "o" }, circ(8, 8, 7, "W"), ring(8, 8, 7, "r"), vline(8, 3, 6, "o"), hline(8, 8, 4, "o"))
sprite("_pennant", { w: 40, h: 14 },   // guirnalda de banderines celeste y blanco
  (c) => { c.line(0, 1, 40, 3, "x"); for (let i = 0; i < 6; i++) { const x = 2 + i * 6, y = 2 + (i > 2 ? 1 : 0); c.poly([x, y, x + 5, y, x + 2, y + 7], i % 2 ? "W" : "C") } })
sprite("_jersey", { w: 22, h: 22, outline: "o" },   // camiseta celeste y blanca colgada
  poly([5, 0, 17, 0, 22, 5, 18, 8, 18, 22, 4, 22, 4, 8, 0, 5], "W"), (c) => { for (let x = 5; x < 18; x += 4) c.rect(x, 2, 2, 20, "C") }, rect(8, 0, 6, 2, "C"), text(8, 8, "10", "o"))
sprite("_fileteado_sign", { w: 70, h: 18, outline: "o" },
  rect(0, 0, 70, 18, "u"), box(2, 2, 66, 14, "y"),
  (c) => { for (const x of [4, 63]) { c.circ(x + 1, 9, 3, "r"); c.px(x + 1, 9, "Z") } c.line(8, 4, 14, 9, "N"); c.line(62, 4, 56, 9, "N") })
sprite("_plant", { w: 18, h: 28, outline: "o" },
  rect(4, 18, 10, 10, "q"), hline(4, 18, 10, "Z"), vline(13, 18, 10, "Y"),
  circ(9, 10, 7, "n"), circ(6, 7, 4, "N"), circ(13, 12, 3, "G"), px(8, 4, "N"))
sprite("_poster", { w: 20, h: 26, outline: "o" }, rect(0, 0, 20, 26, "y"), rect(2, 2, 16, 14, "r"), circ(10, 9, 4, "Z"), text(3, 18, "50%", "o"))
sprite("_lamp_hanging", { w: 16, h: 18 }, vline(8, 0, 8, "x"), poly([2, 14, 14, 14, 11, 8, 5, 8], "A"), hline(2, 14, 13, "o"), rect(6, 15, 4, 2, "z"))
sprite("_neon_open", { w: 46, h: 14, outline: "o" }, rect(0, 0, 46, 14, "u"), text(4, 4, "ABIERTO", "p"))
sprite("_tv", { w: 34, h: 22, outline: "o" }, rect(0, 0, 34, 20, "o"), rect(2, 2, 30, 16, "G"), rect(2, 12, 30, 6, "n"), rect(15, 6, 4, 4, "W"), rect(14, 20, 6, 2, "x"))
sprite("_crate", { w: 20, h: 14, outline: "o" }, rect(0, 2, 20, 12, "t"), hline(0, 2, 20, "T"), hline(0, 7, 20, "M"),
  (c) => { for (let i = 0; i < 5; i++) c.circ(2 + i * 4, 2, 2, ["r", "N", "y", "q", "n"][i]) })
sprite("_salames", { w: 30, h: 22 }, hline(0, 0, 30, "M"), (c) => { for (let i = 0; i < 5; i++) { const x = 3 + i * 6; c.vline(x + 1, 0, 3, "e"); c.rect(x, 3, 4, 12 + (i % 2) * 4, i % 2 ? "R" : "p"); c.px(x + 1, 6, "e") } })
sprite("_checkout", { w: 66, h: 42, outline: "o" },   // caja de súper con cinta
  rect(0, 18, 66, 24, "l"), hline(0, 18, 66, "W"), rect(0, 14, 44, 4, "u"), (c) => { for (let x = 1; x < 44; x += 4) c.vline(x, 14, 4, "x") },
  rect(4, 8, 8, 6, "y"), rect(14, 10, 6, 4, "r"), rect(24, 9, 5, 5, "n"), stamp("_register", 44, 0), rect(2, 22, 62, 4, "r"), rect(2, 38, 62, 4, "g"))

sprite("_cart", { w: 28, h: 28, outline: "o" },
  poly([0, 4, 24, 4, 22, 18, 3, 18], "l"), (c) => { for (let x = 3; x < 22; x += 3) c.vline(x, 5, 13, "g"); c.hline(2, 11, 21, "g") },
  rect(4, 20, 18, 2, "d"), circ(6, 25, 2, "o"), circ(20, 25, 2, "o"), rect(24, 0, 3, 6, "r"))

sprite("_conveyor", { w: 110, h: 36, outline: "o" },   // cinta transportadora (fábrica / depósito)
  rect(0, 10, 110, 8, "u"), (c) => { for (let x = 2; x < 108; x += 6) c.vline(x, 11, 6, "x") }, rect(0, 18, 110, 4, "d"),
  (c) => { for (let x = 6; x < 104; x += 20) c.rect(x, 22, 4, 14, "x"); for (let x = 8; x < 100; x += 22) { c.rect(x, 0, 14, 10, "t"); c.hline(x, 0, 14, "T"); c.vline(x + 7, 0, 10, "E") } })

sprite("_machine", { w: 50, h: 56, outline: "o" },   // máquina envasadora
  rect(0, 10, 50, 46, "B"), hline(0, 10, 50, "C"), vline(49, 10, 46, "A"), rect(6, 16, 22, 16, "u"), rect(8, 18, 18, 12, "N"),
  circ(38, 22, 5, "y"), circ(38, 22, 2, "Y"), rect(32, 34, 12, 4, "r"), rect(6, 38, 38, 12, "A"), rect(14, 0, 22, 10, "l"), rect(18, 2, 14, 6, "c"))

scene("muestrario", { w: 700, h: 560, bg: "e" },
  (c) => {
    const names = ["_counter_wood", "_counter_glass", "_counter_metal", "_register", "_scale", "_slicer", "_mate_set", "_shelf_wood", "_shelf_metal", "_shelf_almacen",
      "_gondola", "_fridge_drinks", "_freezer", "_grill", "_stove", "_prep_table", "_coffee_machine", "_pastry_case", "_dining_table", "_cafe_table", "_chalkboard", "_wine_rack",
      "_car", "_car_lift", "_tool_wall", "_tires", "_drums", "_workbench", "_wash_bay", "_treadmill", "_weight_rack", "_bench_press", "_punching_bag", "_mirror",
      "_desk_pc", "_filing", "_water_cooler", "_parcel_shelf", "_pallet_rack", "_forklift", "_dock_door", "_pallet_boxes", "_scooter", "_clock", "_pennant", "_jersey",
      "_fileteado_sign", "_plant", "_poster", "_lamp_hanging", "_neon_open", "_tv", "_crate", "_salames", "_checkout", "_cart", "_conveyor", "_machine"]
    let x = 4, y = 14, rowH = 0
    for (const n of names) { const w = 116; if (x + w > 700) { x = 4; y += rowH + 8; rowH = 0 } c.stamp(n, x, y); x += w; rowH = Math.max(rowH, 84) }
  })

// ---------------------------------------------------------------- puesto callejero
sprite("_stall_table", { w: 80, h: 34, outline: "o" },   // mesa con mantel a cuadros y mercadería
  (c) => { for (let y = 10; y < 24; y++) for (let x = 0; x < 80; x++) c.px(x, y, ((x >> 2) + (y >> 2)) % 2 ? "W" : (y > 21 ? "B" : "C")) },
  rect(4, 24, 3, 10, "M"), rect(73, 24, 3, 10, "M"),
  (c) => { const items = ["alf", "bot", "snk", "alf", "jar", "bot", "snk", "bot", "alf", "snk"]; let x = 3
    for (let i = 0; i < items.length && x < 74; i++) { const k = items[i]
      if (k === "alf") { c.rect(x, 4, 8, 6, i % 2 ? "A" : "M"); c.hline(x, 4, 8, i % 2 ? "B" : "t"); c.rect(x + 2, 6, 4, 2, "W"); x += 9 }
      else if (k === "bot") { const col = ["r", "n", "y"][i % 3]; c.rect(x + 1, -2 + 1, 3, 11, col); c.px(x + 2, 0, "x"); c.rect(x + 1, 5, 3, 2, "W"); x += 5 }
      else if (k === "snk") { const col = ["y", "p"][i % 2]; c.rect(x, 1, 6, 9, col); c.hline(x, 1, 6, "W"); c.rect(x + 1, 4, 4, 3, i % 2 ? "Z" : "r"); x += 7 }
      else { c.rect(x, 0, 8, 10, "l"); c.hline(x, 0, 8, "r"); for (let k2 = 0; k2 < 6; k2++) c.px(x + 1 + (k2 * 3) % 6, 2 + k2, ["r", "y", "n", "B", "p", "Z"][k2]); x += 9 } } })
sprite("_umbrella", { w: 90, h: 70 },
  rect(44, 18, 2, 52, "x"),
  (c) => { for (let y = 0; y < 18; y++) { const half = Math.round(44 * Math.sqrt((y + 1) / 18)); for (let x = -half; x <= half; x++) c.px(45 + x, y + 2, Math.floor((x + 60) / 8) % 2 ? (y > 15 ? "l" : "W") : (y > 15 ? "B" : "C")) } },
  rect(43, 0, 4, 3, "y"))
sprite("_cooler", { w: 30, h: 22, outline: "o" }, rect(0, 4, 30, 18, "B"), hline(0, 4, 30, "c"), rect(0, 0, 30, 5, "W"), rect(11, 1, 8, 2, "l"), rect(3, 10, 24, 4, "C"))
sprite("_price_board", { w: 18, h: 30, outline: "o" }, rect(0, 0, 18, 16, "u"), box(0, 0, 18, 16, "M"), text(3, 3, "$5", "W"), hline(3, 11, 11, "Z"), rect(2, 16, 2, 14, "M"), rect(14, 16, 2, 14, "M"))
sprite("_string_lights", { w: 200, h: 16 }, wire(0, 2, 200, 2, 8, "o", { hang: "_bulb", every: 9 }))
sprite("_bulb", "Z\nY")

// ---------------------------------------------------------------- animaciones (las ubica el juego)
anim("fx_smoke", { w: 24, h: 34, frames: 4, fps: 5 }, (c) => {
  const k = c.phase * Math.PI * 2
  for (let i = 0; i < 4; i++) { const y = 30 - i * 8 - Math.round(c.phase * 8) % 8, x = 12 + Math.round(Math.sin(k + i) * 3), r = 3 + Math.floor(i / 2)
    if (y > 2) { c.circ(x, y, r, i % 2 ? "l" : "w"); c.px(x - 1, y - 1, "W") } } })
anim("fx_steam", { w: 12, h: 18, frames: 3, fps: 4 }, (c) => {
  for (let i = 0; i < 3; i++) { const y = 15 - i * 5 - c.frame * 2; const x = 5 + ((i + c.frame) % 2) * 2; if (y > 1) { c.px(x, y, "w"); c.px(x + 1, y - 1, "W"); c.px(x, y - 2, "l") } } })
anim("fx_neon", { fps: 2, base: "_neon_open" }, frame({ ms: 1800 }), frame({ ms: 200 }, recolor({ p: "R" })))
anim("fx_tv", { fps: 3, base: "_tv" }, frame(), frame(rect(4, 4, 26, 8, "B"), rect(12, 5, 10, 6, "W")), frame(rect(2, 2, 30, 10, "c"), rect(6, 9, 22, 6, "n")))
anim("fx_foam", { w: 30, h: 16, frames: 4, fps: 6 }, (c) => { for (let i = 0; i < 5; i++) { const x = 3 + i * 6, y = 10 - ((i + c.frame) % 4) * 2; c.circ(x, y, 2 + ((i + c.frame) % 2), "W"); c.px(x - 1, y - 1, "c") } })
anim("fx_conveyor", { w: 110, h: 10, frames: 4, fps: 8 }, (c) => { c.rect(0, 0, 110, 8, "u"); for (let x = 2 + c.frame * 2 % 6; x < 108; x += 6) c.vline(x, 1, 6, "x") })

sprite("_wall_shelf", { w: 68, h: 20, outline: "o" },   // repisa de pared con mercadería
  rect(0, 16, 68, 4, "t"), hline(0, 16, 68, "T"), rect(4, 20, 3, 0, "M"), (c) => goodsRow(c, 2, 66, 16, 9, 13))
