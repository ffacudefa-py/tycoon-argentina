// Mapa de Ciudad del Plata (360x540) visto desde arriba en 3/4: avenidas
// con veredas y autos, río con orilla y reflejos, y cada zona con identidad
// propia. Los rectángulos de las zonas son los de data/world.json (el juego
// dibuja el marco y la etiqueta encima), así que el contenido de cada zona
// queda dentro de su rectángulo.
include("palette.px.js")

const MW = 360, MH = 540
const ZONES = {
  financiero: [120, 28, 124, 116], costanera: [252, 90, 90, 150], universidad: [28, 158, 130, 104],
  centro: [174, 276, 118, 100], barrio: [28, 300, 140, 116], industrial: [28, 430, 160, 92], puerto: [200, 392, 142, 130],
}
const AV_X = [[20, 4], [166, 5], [196, 5], [248, 5]]      // avenidas verticales [x, ancho]
const AV_Y = [150, 268, 380, 424]                         // avenidas horizontales (alto 5)
const RIVER_X = (y) => 334 + ((y >> 4) % 3 === 1 ? 1 : 0) - (y < 372 ? 0 : Math.min(16, (y - 372) >> 2))

// ------------------------------------------------------------------ piezas
sprite("_tree", { outline: "G" }, `
  .nNn.
  nNNnn
  nnnnG
  .GnG.`)
sprite("_tree_b", { outline: "G" }, `
  .Nn.
  nnnG
  .GG.`)
sprite("_palm", `
  N..n..N
  .nNNNn.
  n.nMn.n
  ...M...
  ...M...
  ...m...`)
sprite("_bush", "nN\nGn")
group("_trees", ["_tree", "_tree", "_tree_b"])
// Autos vistos desde arriba (horizontal / vertical)
for (const [k, c] of [["r", "r"], ["b", "B"], ["y", "y"], ["w", "w"], ["g", "n"]]) {
  sprite("_car_h_" + k, { w: 6, h: 3, outline: "o" }, rect(0, 0, 6, 3, c), rect(2, 0, 2, 3, "c"), px(0, 1, "z"))
  sprite("_car_v_" + k, { w: 3, h: 6, outline: "o" }, rect(0, 0, 3, 6, c), rect(0, 2, 3, 2, "c"), px(1, 0, "z"))
}
group("_cars_h", ["_car_h_r", "_car_h_b", "_car_h_y", "_car_h_w", "_car_h_g"])
group("_cars_v", ["_car_v_r", "_car_v_b", "_car_v_y", "_car_v_w", "_car_v_g"])
sprite("_umbrella_r", { outline: "o" }, `
  .rWr.
  rWrWr
  ..m..`)
sprite("_umbrella_b", { outline: "o" }, `
  .BWB.
  BWBWB
  ..m..`)
group("_umbrellas", ["_umbrella_r", "_umbrella_b"])

// Edificio en 3/4: techo (arriba) + frente con ventanas. (x, y) = esquina
// superior izquierda del techo; d = profundidad del techo; h = alto del frente.
function building(c, x, y, w, d, h, wall, roof, win = "c", opts = {}) {
  const [rs, rm, rl] = roof
  c.rect(x, y, w, d, rm); c.hline(x, y, w, rl); c.vline(x, y, d, rl)
  if (opts.ac) { c.rect(x + 2, y + 2, 2, 2, "l"); c.px(x + 2, y + 2, "W") }       // equipo en la azotea
  c.rect(x, y + d, w, h, wall[1]); c.vline(x + w - 1, y + d, h, wall[0])
  c.hline(x, y + d, w, wall[0])
  for (let wy = y + d + 2; wy < y + d + h - 2; wy += opts.floor || 3)
    for (let wx = x + 1; wx < x + w - 2; wx += opts.col || 3) c.px(wx + 1, wy, (wx + wy) % 7 === 0 ? "z" : win)
  c.box(x - 1, y - 1, w + 2, d + h + 2, "o")
}
// Casa con techo a dos aguas de tejas.
function house(c, x, y, w, roof, wall) {
  c.rect(x, y, w, 3, roof[1]); c.hline(x, y, w, roof[2]); c.hline(x, y + 3, w, roof[0])
  c.rect(x, y + 4, w, 3, wall); c.px(x + 1, y + 5, "c"); c.px(x + w - 2, y + 5, "c"); c.px(x + (w >> 1), y + 6, "M")
  c.box(x - 1, y - 1, w + 2, 9, "o")
}

// ------------------------------------------------------------------ zonas
function financiero(c, [x, y, w, h]) {
  c.rect(x + 2, y + 2, w - 4, h - 4, "g"); c.box(x + 2, y + 2, w - 4, h - 4, "d")          // explanada de baldosas
  for (let yy = y + 6; yy < y + h - 4; yy += 6) c.hline(x + 4, yy, w - 8, "l")
  const rng = c.rng(11)
  const towers = [[8, 16, 46], [30, 18, 70], [54, 14, 56], [74, 20, 80], [100, 16, 50]]
  for (const [dx, tw, th] of towers) {
    const tx = x + dx, base = y + h - 12, top = base - th
    // sombra proyectada hacia la derecha-abajo
    c.poly([tx + tw, top + 6, tx + tw + 6, top + 10, tx + tw + 6, base + 4, tx + tw, base], "d")
    c.rect(tx, top, tw, 5, "B"); c.hline(tx, top, tw, "c"); c.rect(tx + 2, top + 1, 3, 2, "l")      // azotea
    c.rect(tx, top + 5, tw, th - 5, "A")
    for (let wy = top + 7; wy < base - 1; wy += 3) { c.hline(tx + 1, wy, tw - 2, "C"); c.hline(tx + 1, wy + 1, tw - 2, "B") }
    c.line(tx + 2, base - 8, tx + Math.min(tw - 2, 12), top + 10, "c")                                // reflejo del cielo
    for (let k = 0; k < 4; k++) c.px(tx + 2 + Math.floor(rng() * (tw - 4)), top + 8 + Math.floor(rng() * (th - 14)), "z")
    c.vline(tx + tw - 1, top + 5, th - 5, "u")
    c.box(tx - 1, top - 1, tw + 2, th + 2, "o")
  }
  // helipuerto en la torre más alta
  c.circ(x + 82, y + h - 12 - 80 + 2, 2, "y"); c.px(x + 82, y + h - 90, "o")
  for (const tx of [x + 6, x + 28, x + 52, x + 72, x + 98, x + 116]) c.stamp("_tree_b", tx, y + h - 9)
}

// stamp() dentro de funciones: se usa el método del canvas.
function trees(c, list) { for (const [n, tx, ty] of list) c.stamp(n, tx, ty) }

function costanera(c, [x, y, w, h]) {
  // pasto, rambla (vereda ancha) y arena hasta el río
  c.rect(x + 2, y + 2, 38, h - 4, "n")
  c.rect(x + 40, y + 2, 14, h - 4, "l"); for (let yy = y + 4; yy < y + h - 2; yy += 4) c.hline(x + 40, yy, 14, "g")
  c.vline(x + 53, y + 2, h - 4, "x")                                                              // baranda
  c.rect(x + 54, y + 2, w - 56, h - 4, "e"); c.dither(x + 54, y + 2, w - 56, h - 4, "e", "E", 0.15)
  for (let yy = y + 10; yy < y + h - 10; yy += 18) {
    c.stamp("_palm", x + 44, yy)
    c.stamp(yy % 36 ? "_umbrella_r" : "_umbrella_b", x + 62 + (yy % 20), yy + 6)
    c.stamp("_umbrella_b", x + 72, yy + 12)
    house(c, x + 8, yy, 14, ["t", "M", "T"], "w")                                                 // paradores
    c.stamp("_tree_b", x + 28, yy + 2)
  }
  // muelle de pesca con faro
  c.rect(x + 66, y + 74, w - 66, 3, "M"); c.hline(x + 66, y + 74, w - 66, "t")
  c.rect(x + 60, y + 20, 5, 9, "W"); c.hline(x + 60, y + 22, 5, "r"); c.hline(x + 60, y + 25, 5, "r"); c.rect(x + 61, y + 18, 3, 2, "y")
  c.box(x + 59, y + 17, 7, 13, "o")
}

function universidad(c, [x, y, w, h]) {
  c.rect(x + 2, y + 2, w - 4, h - 4, "N"); c.dither(x + 2, y + 2, w - 4, h - 4, "N", "n", 0.12)
  // caminos de ladrillo en cruz
  c.rect(x + 2, y + 50, w - 4, 4, "T"); c.rect(x + 60, y + 2, 4, h - 4, "T")
  // edificio principal con torre del reloj
  building(c, x + 14, y + 10, 40, 6, 18, ["R", "r"], ["R", "r", "p"], "z", { col: 4, floor: 4 })
  c.rect(x + 30, y + 2, 8, 12, "r"); c.box(x + 29, y + 1, 10, 14, "o"); c.circ(x + 33, y + 6, 2, "W"); c.px(x + 33, y + 6, "o")
  building(c, x + 72, y + 12, 44, 6, 14, ["E", "e"], ["M", "t", "T"], "c", { col: 4 })
  // cancha de fútbol
  c.rect(x + 74, y + 62, 46, 30, "G"); c.box(x + 74, y + 62, 46, 30, "W"); c.vline(x + 97, y + 62, 30, "W"); c.ring(x + 97, y + 77, 4, "W")
  c.rect(x + 74, y + 72, 3, 10, "w"); c.rect(x + 117, y + 72, 3, 10, "w")
  // bancos y árboles del parque
  trees(c, [["_tree", x + 8, y + 60], ["_tree", x + 22, y + 72], ["_tree_b", x + 40, y + 62], ["_tree", x + 10, y + 84], ["_tree_b", x + 44, y + 86], ["_tree", x + 30, y + 90]])
  c.rect(x + 22, y + 58, 6, 2, "M"); c.rect(x + 36, y + 80, 6, 2, "M")
}

function centro(c, [x, y, w, h]) {
  const rng = c.rng(5)
  const roofs = [["R", "r", "p"], ["x", "d", "g"], ["Y", "y", "Z"], ["A", "B", "C"], ["M", "t", "T"], ["d", "g", "l"]]
  const walls = [["E", "e"], ["d", "g"], ["r", "p"], ["B", "C"], ["t", "T"]]
  // manzanas entre las avenidas que cruzan el centro (x=196 y x=248)
  const blocks = [[x + 2, 20], [x + 27, 46], [x + 79, 37]]
  for (const [bx, bw] of blocks) {
    for (let by = y + 4; by < y + h - 18; by += 24) {
      let cx = bx
      while (cx < bx + bw - 6) {
        const bw2 = Math.min(bx + bw - cx - 1, 8 + Math.floor(rng() * 7))
        const hh = 8 + Math.floor(rng() * 8)
        building(c, cx + 1, by + (16 - hh), bw2 - 1, 3, hh, walls[Math.floor(rng() * walls.length)], roofs[Math.floor(rng() * roofs.length)], "z", { col: 2, floor: 3, ac: rng() < 0.4 })
        cx += bw2 + 1
      }
    }
  }
  // Obelisco en la plaza de la avenida
  c.rect(x + 60, y + h - 14, 12, 10, "l"); c.box(x + 59, y + h - 15, 14, 12, "g")
  c.poly([x + 64, y + h - 6, x + 68, y + h - 6, x + 67, y + h - 30, x + 65, y + h - 30], "W"); c.px(x + 66, y + h - 31, "W")
  c.vline(x + 67, y + h - 30, 24, "l")
}

function barrio(c, [x, y, w, h]) {
  const rng = c.rng(3)
  const roofs = [["R", "r", "p"], ["R", "r", "p"], ["M", "t", "T"], ["x", "d", "g"]]
  const walls = ["e", "w", "T", "p", "c", "N", "z"]
  for (let yy = y + 4; yy < y + h - 8; yy += 13) {
    if (yy >= 376 && yy <= 384) continue
    c.hline(x + 2, yy + 10, w - 4, "g")                                                           // vereda de la cuadra
    for (let xx = x + 4; xx < x + w - 10; xx += 12) {
      house(c, xx + Math.floor(rng() * 2), yy, 8, roofs[Math.floor(rng() * roofs.length)], walls[Math.floor(rng() * walls.length)])
      if (rng() < 0.45) c.stamp("_tree_b", xx + 9, yy + 1)                                         // patio con árbol
    }
  }
  // canchita de barrio y almacén de la esquina
  c.rect(x + w - 30, y + h - 22, 26, 16, "n"); c.box(x + w - 30, y + h - 22, 26, 16, "W"); c.vline(x + w - 17, y + h - 22, 16, "W")
}

function industrial(c, [x, y, w, h]) {
  c.rect(x + 2, y + 2, w - 4, h - 4, "g"); c.dither(x + 2, y + 2, w - 4, h - 4, "g", "d", 0.1)
  // galpones con techo en diente de sierra
  for (const [gx, gy, gw] of [[8, 8, 40], [56, 8, 44], [108, 8, 44], [8, 50, 56], [72, 52, 40]]) {
    const X = x + gx, Y = y + gy
    c.rect(X, Y, gw, 14, "l")
    for (let k = 0; k < gw; k += 6) { c.rect(X + k, Y, 3, 14, "g"); c.vline(X + k + 3, Y, 14, "W") }
    c.rect(X, Y + 14, gw, 8, "d"); c.rect(X + 4, Y + 16, 8, 6, "x"); c.rect(X + gw - 12, Y + 16, 8, 6, "x")
    c.hline(X + 4, Y + 16, 8, "u"); c.hline(X + gw - 12, Y + 16, 8, "u")
    c.box(X - 1, Y - 1, gw + 2, 24, "o")
  }
  // chimeneas con humo, tanques y camiones
  for (const cx of [x + 52, x + 104]) {
    c.rect(cx, y + 2, 3, 18, "R"); c.hline(cx, y + 4, 3, "W"); c.box(cx - 1, y + 1, 5, 20, "o")
    c.circ(cx + 4, y + 2, 2, "l"); c.circ(cx + 7, y + 1, 1, "w")
  }
  for (const tx of [x + 124, x + 138]) { c.circ(tx, y + 62, 6, "w"); c.ring(tx, y + 62, 6, "o"); c.ring(tx, y + 62, 3, "l") }
  c.rect(x + 120, y + 76, 14, 5, "W"); c.rect(x + 134, y + 76, 5, 5, "r"); c.box(x + 119, y + 75, 21, 7, "o")
  c.rect(x + 8, y + 80, 14, 5, "y"); c.rect(x + 22, y + 80, 5, 5, "B"); c.box(x + 7, y + 79, 21, 7, "o")
}

function puerto(c, [x, y, w, h]) {
  const water = (yy) => RIVER_X(yy) - x
  c.rect(x + 2, y + 2, w - 4, h - 4, "d"); c.dither(x + 2, y + 2, w - 4, h - 4, "d", "x", 0.08)  // playa de hormigón
  // contenedores apilados (con la sombra de la pila)
  const cols = [["R", "r"], ["Y", "y"], ["A", "B"], ["G", "n"], ["q", "Z"], ["M", "t"]]
  let i = 0
  for (let yy = y + 8; yy < y + h - 34; yy += 10)
    for (let xx = x + 6; xx < x + 84; xx += 13) {
      const [s, m] = cols[(i++ * 7 + (yy >> 3)) % cols.length]
      c.rect(xx, yy, 11, 7, m); c.hline(xx, yy + 6, 11, s); for (let k = 2; k < 11; k += 2) c.vline(xx + k, yy + 1, 5, s)
      c.box(xx - 1, yy - 1, 13, 9, "o")
    }
  // muelle y grúas pórtico sobre el agua
  const qx = x + 92
  c.rect(qx, y + 2, 16, h - 4, "l"); c.vline(qx + 15, y + 2, h - 4, "o")
  for (const cy of [y + 14, y + 58]) {
    c.rect(qx - 2, cy, 34, 3, "q"); c.rect(qx + 2, cy - 6, 3, 18, "Y"); c.rect(qx + 12, cy - 6, 3, 18, "Y")
    c.box(qx - 3, cy - 1, 36, 5, "o"); c.vline(qx + 26, cy + 3, 6, "o"); c.rect(qx + 24, cy + 9, 5, 3, "r")
  }
  // barco portacontenedores amarrado
  const sx = qx + 20, sy = y + 30
  c.poly([sx, sy, sx + 20, sy, sx + 20, sy + 70, sx + 10, sy + 80, sx, sy + 70], "R")
  c.rect(sx + 2, sy + 4, 16, 56, "u")
  for (let yy = sy + 6; yy < sy + 56; yy += 6) { c.rect(sx + 3, yy, 7, 4, ["r", "y", "B", "n"][(yy >> 2) % 4]); c.rect(sx + 11, yy, 6, 4, ["B", "n", "r", "y"][(yy >> 2) % 4]) }
  c.rect(sx + 4, sy + 60, 12, 8, "W"); c.hline(sx + 4, sy + 62, 12, "c")
  // depósito de la aduana vieja
  building(c, x + 8, y + h - 30, 70, 6, 14, ["R", "r"], ["x", "d", "g"], "z", { col: 5 })
}

// ------------------------------------------------------------------ mapa
scene("city_map", { w: MW, h: MH, bg: "n" },
  // pasto con matas (no ruido): matas sueltas y arbustos
  layer("grass", scatter("_bush", 0, 0, MW, MH, 260, { on: "n", below: true })),
  // río y bahía
  layer("river", (c) => {
    for (let y = 0; y < MH; y++) {
      const left = RIVER_X(y)
      c.rect(left - 3, y, 3, 1, "E")                       // orilla de arena
      c.rect(left, y, MW - left, 1, "C")
      c.px(left, y, "c")
    }
    for (let y = 4; y < MH; y += 7) for (let x = 340 + (y * 5) % 9; x < MW - 2; x += 11) c.hline(x, y, 3, "c")   // oleaje
    for (let y = 12; y < MH; y += 23) c.hline(346 + (y % 6), y, 5, "B")
  }),
  // avenidas: asfalto, veredas, líneas, sendas peatonales
  layer("roads", (c) => {
    for (const y of AV_Y) {
      c.rect(0, y - 1, 332, 7, "g"); c.rect(0, y, 332, 5, "x")
      for (let x = 2; x < 332; x += 8) c.hline(x, y + 2, 4, "y")
    }
    for (const [x, w] of AV_X) {
      c.rect(x - 1, 0, w + 2, MH, "g"); c.rect(x, 0, w, MH, "x")
      if (w >= 5) for (let y = 2; y < MH; y += 8) c.vline(x + 2, y, 4, "W")
    }
    for (const [x, w] of AV_X) for (const y of AV_Y) {
      c.rect(x - 1, y - 1, w + 2, 7, "x")
      for (let k = 0; k < w; k += 2) { c.vline(x + k, y - 4, 2, "W"); c.vline(x + k, y + 7, 2, "W") }   // sendas
    }
  }),
  layer("cars", (c) => {
    const rng = c.rng(9)
    for (const y of AV_Y) for (let x = 8; x < 320; x += 30 + Math.floor(rng() * 30)) c.stamp("_cars_h", x, y + (rng() < 0.5 ? 0 : 2), { seed: x })
    for (const [x, w] of AV_X) if (w >= 5) for (let y = 10; y < MH; y += 40 + Math.floor(rng() * 40)) c.stamp("_cars_v", x + (rng() < 0.5 ? 0 : 2), y, { seed: y })
  }),
  // plaza central con fuente
  layer("plaza", (c) => {
    c.ellipse(182, 401, 11, 9, "T"); c.ellipse(182, 401, 8, 6, "n"); c.circ(182, 401, 3, "l"); c.circ(182, 401, 2, "c"); c.px(182, 400, "W")
  }),
  layer("zones", (c) => {
    financiero(c, ZONES.financiero); costanera(c, ZONES.costanera); universidad(c, ZONES.universidad)
    centro(c, ZONES.centro); barrio(c, ZONES.barrio); industrial(c, ZONES.industrial); puerto(c, ZONES.puerto)
  }),
  // árboles en el pasto fuera de las zonas
  layer("park_trees", scatter("_trees", 0, 0, MW, MH, 140, { on: "n", below: true })),
)
