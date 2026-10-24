// Avatares de perfil (32x32): retratos de busto sobre un disco de color, con
// luz desde arriba a la izquierda, contorno oscuro y brillo. Se muestran a
// 32 px (barra superior, selector) y a 64 px (x2) en Perfil.
include("palette.px.js")

const DISC = [16, 16, 15]
// Fondo: disco con degradé suave (más claro arriba) y aro oscuro.
function disc(c, ramp) {
  const [dk, md, lt] = ramp
  c.circ(16, 16, 15, md)
  c.clip(DISC, () => { c.dither(0, 0, 32, 10, lt, md, 0.5); c.rect(0, 0, 32, 5, lt); c.dither(0, 24, 32, 8, md, dk, 0.5) })
}
function ring(c) { c.ring(16, 16, 15, "o") }

// Cabeza humana. sk = [sombra, medio, luz].
function head(c, sk, opts = {}) {
  const [sd, md, lt] = sk
  c.rect(13, 21, 6, 4, sd)                                  // cuello
  c.ellipse(16, 14, 7, 8, md)
  c.ellipse(8, 15, 1, 2, md); c.ellipse(24, 15, 1, 2, sd)   // orejas
  c.clip([19, 6, 6, 18], () => c.recolor({ [md]: sd }, (x, y) => (x - 16) * (x - 16) / 49 + (y - 14) * (y - 14) / 64 > 0.45))
  c.px(11, 10, lt); c.hline(12, 9, 3, lt)                   // brillo en la frente
  c.ellipse(16, 14, 7, 8, "o", true)
  c.px(8, 13, "o"); c.px(24, 13, "o")
  // ojos (2x2 con brillo), cejas, nariz, boca y cachetes
  const ey = opts.eyeY || 14
  for (const ex of [12, 19]) { c.rect(ex, ey, 2, 2, "o"); c.px(ex, ey, "W") }
  c.hline(11, ey - 2, 3, opts.brow || "m"); c.hline(19, ey - 2, 3, opts.brow || "m")
  c.px(16, ey + 2, sd); c.px(17, ey + 3, sd)
  if (opts.smile !== false) { c.hline(14, ey + 5, 4, "R"); c.px(13, ey + 4, "R"); c.px(18, ey + 4, "R") }
  c.px(11, ey + 3, "p"); c.px(21, ey + 3, "p")
}
// Torso/hombros recortados por el disco. col = [sombra, medio, luz].
function body(c, col, opts = {}) {
  c.clip(DISC, () => {
    c.ellipse(16, 31, 13, 7, col[1]); c.rect(3, 29, 26, 4, col[1])
    c.clip([17, 24, 14, 9], () => c.recolor({ [col[1]]: col[0] }))
    c.hline(6, 26, 6, col[2])
    c.ellipse(16, 31, 13, 7, "o", true)
  })
  if (opts.collar) { c.poly([13, 24, 16, 28, 19, 24], opts.collar); c.line(13, 24, 16, 28, "o"); c.line(19, 24, 16, 28, "o") }
}

sprite("av_emprendedor", { w: 32, h: 32 }, (c) => {
  disc(c, ["A", "B", "C"])
  body(c, ["A", "B", "C"], { collar: "W" })
  c.vline(16, 27, 4, "r"); c.px(16, 26, "R")                                 // corbata
  head(c, ["S", "s", "f"])
  // pelo castaño corto con jopo
  c.ellipse(16, 8, 8, 4, "M"); c.rect(8, 8, 3, 5, "M"); c.rect(22, 8, 2, 4, "m")
  c.hline(12, 5, 6, "t"); c.px(19, 6, "t"); c.hline(10, 7, 3, "t")
  c.ellipse(16, 8, 8, 4, "o", true); c.hline(11, 11, 10, "M")
  c.clip([0, 12, 32, 20], () => c.recolor({ o: "M" }, [8, 12, 2, 1]))
  ring(c)
})

sprite("av_vecina", { w: 32, h: 32 }, (c) => {
  disc(c, ["R", "p", "e"])
  body(c, ["R", "r", "p"], { collar: "w" })
  for (const bx of [14, 18]) c.px(bx, 29, "W")                                // botones del saco
  head(c, ["S", "s", "f"])
  // rulos grises con ruleros
  for (const [dx, dy] of [[-7, -3], [-4, -7], [0, -8], [4, -7], [7, -3], [-8, 1], [8, 1]]) { c.circ(16 + dx, 13 + dy, 3, "l"); c.px(15 + dx, 12 + dy, "W") }
  c.rect(10, 4, 4, 2, "p"); c.rect(18, 4, 4, 2, "C")
  c.hline(10, 9, 13, "g")
  // anteojos y aros
  c.box(11, 13, 4, 4, "y"); c.box(18, 13, 4, 4, "y"); c.hline(15, 14, 3, "y")
  c.px(8, 18, "Z"); c.px(24, 18, "Z")
  ring(c)
})

sprite("av_perro", { w: 32, h: 32 }, (c) => {
  disc(c, ["G", "n", "N"])
  c.clip(DISC, () => { c.ellipse(16, 31, 12, 6, "M"); c.ellipse(16, 31, 12, 6, "o", true) })
  c.ellipse(16, 16, 9, 8, "t")                                               // cabeza
  c.ellipse(19, 18, 5, 4, "M")
  c.ellipse(7, 15, 3, 7, "m"); c.ellipse(25, 15, 3, 7, "m")                  // orejas caídas
  c.ellipse(7, 15, 3, 7, "o", true); c.ellipse(25, 15, 3, 7, "o", true)
  c.ellipse(16, 20, 5, 4, "T")                                               // hocico claro
  c.ellipse(16, 16, 9, 8, "o", true)
  for (const ex of [12, 19]) { c.rect(ex, 13, 2, 2, "o"); c.px(ex, 13, "W") }
  c.hline(11, 11, 3, "m"); c.hline(19, 11, 3, "m")
  c.rect(15, 18, 3, 2, "o"); c.px(15, 18, "g")                               // nariz
  c.vline(16, 20, 2, "o"); c.hline(14, 22, 5, "o")
  c.rect(16, 23, 2, 3, "p"); c.px(17, 25, "r")                               // lengua
  c.hline(12, 26, 9, "r"); c.px(16, 27, "y")                                 // collar con chapita
  c.px(10, 10, "T"); c.hline(11, 9, 3, "T")
  ring(c)
})

sprite("av_gorra", { w: 32, h: 32 }, (c) => {
  disc(c, ["Y", "y", "Z"])
  body(c, ["u", "x", "d"])
  c.line(13, 25, 13, 29, "l"); c.line(19, 25, 19, 29, "l")                   // cordones del buzo
  head(c, ["m", "S", "s"], { brow: "o" })
  // gorra roja con visera hacia adelante
  c.ellipse(16, 8, 8, 4, "r"); c.rect(8, 8, 16, 3, "r")
  c.rect(6, 10, 14, 2, "R"); c.hline(6, 10, 14, "p")
  c.hline(12, 5, 4, "p"); c.px(16, 4, "W")
  c.clip([0, 0, 32, 13], () => { c.ellipse(16, 8, 8, 4, "o", true) })
  c.hline(6, 12, 15, "o"); c.px(5, 11, "o")
  c.rect(21, 10, 3, 3, "o")                                                   // pelo corto atrás
  ring(c)
})

sprite("av_mate", { w: 32, h: 32 }, (c) => {
  disc(c, ["G", "n", "N"])
  // calabaza del mate con virola de alpaca y bombilla
  c.ellipse(15, 21, 8, 8, "M"); c.rect(9, 12, 13, 5, "M")
  c.clip([15, 21, 8], () => c.recolor({ M: "m" }, [17, 13, 8, 18]))
  c.ellipse(11, 19, 2, 4, "t")
  c.rect(8, 11, 15, 3, "l"); c.hline(8, 11, 15, "W"); c.hline(8, 13, 15, "g")
  c.ellipse(15, 12, 6, 1, "G"); c.px(13, 12, "N"); c.px(17, 12, "n")          // yerba
  c.line(18, 12, 23, 2, "l", 2); c.px(23, 2, "W"); c.line(19, 12, 24, 3, "g")
  c.ellipse(15, 21, 8, 8, "o", true); c.box(7, 10, 17, 5, "o")
  // vapor y dibujo de fileteado en la calabaza
  c.px(9, 6, "W"); c.px(10, 5, "W"); c.px(10, 7, "w"); c.px(12, 3, "w")
  c.px(13, 22, "Z"); c.px(14, 23, "y"); c.px(15, 22, "Z"); c.px(16, 23, "y"); c.px(17, 22, "Z")
  ring(c)
})

sprite("av_gato", { w: 32, h: 32 }, (c) => {
  disc(c, ["V", "v", "p"])
  c.clip(DISC, () => { c.ellipse(16, 31, 11, 6, "d"); c.ellipse(16, 31, 11, 6, "o", true) })
  c.poly([8, 13, 9, 4, 14, 9], "d"); c.poly([24, 13, 23, 4, 18, 9], "d")    // orejas
  c.poly([9, 11, 10, 6, 12, 9], "p"); c.poly([23, 11, 22, 6, 20, 9], "p")
  c.ellipse(16, 16, 9, 8, "g")
  c.clip([7, 8, 18, 6], () => { for (const x of [13, 16, 19]) c.vline(x, 8, 4, "d") })   // rayas atigradas
  c.hline(7, 16, 3, "d"); c.hline(23, 16, 3, "d")
  c.ellipse(16, 20, 4, 3, "w")
  c.ellipse(16, 16, 9, 8, "o", true); c.line(8, 13, 9, 4, "o"); c.line(9, 4, 14, 9, "o"); c.line(24, 13, 23, 4, "o"); c.line(23, 4, 18, 9, "o")
  for (const ex of [11, 19]) { c.rect(ex, 14, 3, 3, "N"); c.vline(ex + 1, 14, 3, "o"); c.px(ex, 14, "W") }
  c.px(16, 19, "p"); c.px(15, 20, "o"); c.px(17, 20, "o")
  c.hline(4, 19, 5, "W"); c.hline(4, 21, 5, "l"); c.hline(24, 19, 5, "W"); c.hline(24, 21, 5, "l")   // bigotes
  ring(c)
})

sprite("av_alfajor", { w: 32, h: 32 }, (c) => {
  disc(c, ["Y", "y", "Z"])
  // Alfajor de chocolate asomando del envoltorio de papel metalizado (con la
  // franja roja de la marca); arriba el baño brillante, al costado el canto
  // con la capa de dulce de leche.
  c.ellipse(16, 13, 10, 5, "M")                                              // baño de arriba
  c.rect(6, 13, 21, 5, "m"); c.rect(6, 15, 21, 2, "t"); c.hline(6, 16, 21, "T")   // canto y dulce
  c.ellipse(16, 13, 10, 5, "M")
  c.ellipse(12, 11, 4, 2, "t"); c.hline(10, 10, 3, "T"); c.px(9, 11, "T")   // brillo
  c.ellipse(16, 13, 10, 5, "o", true); c.vline(6, 13, 5, "o"); c.vline(26, 13, 5, "o")
  // envoltorio: papel plateado arrugado con puntas abiertas
  c.poly([3, 18, 8, 16, 12, 18, 16, 16, 20, 18, 24, 16, 29, 18, 27, 27, 5, 27], "l")
  c.clip(DISC, () => { c.rect(5, 26, 22, 6, "l"); c.hline(5, 26, 22, "g") })
  c.rect(5, 21, 22, 3, "r"); c.hline(5, 21, 22, "p"); c.hline(5, 23, 22, "R")    // franja de la marca
  c.px(10, 22, "W"); c.px(13, 22, "W"); c.px(16, 22, "W")
  for (const x of [7, 12, 18, 23]) c.line(x, 18, x + 1, 20, "g")            // arrugas
  c.line(3, 18, 8, 16, "o"); c.line(8, 16, 12, 18, "o"); c.line(12, 18, 16, 16, "o"); c.line(16, 16, 20, 18, "o")
  c.line(20, 18, 24, 16, "o"); c.line(24, 16, 29, 18, "o"); c.line(3, 18, 5, 27, "o"); c.line(29, 18, 27, 27, "o")
  c.px(8, 17, "W"); c.px(24, 17, "W"); c.px(6, 19, "W")
  c.px(8, 6, "W"); c.px(9, 5, "W"); c.px(25, 7, "z")
  ring(c)
})

sprite("av_kiosquero", { w: 32, h: 32 }, (c) => {
  disc(c, ["q", "Z", "z"])
  body(c, ["l", "w", "W"])
  c.rect(12, 25, 9, 8, "B"); c.hline(12, 25, 9, "C"); c.vline(12, 25, 7, "o"); c.vline(20, 25, 7, "o")   // delantal
  head(c, ["S", "s", "f"], { smile: false, brow: "x" })
  c.hline(12, 19, 9, "x"); c.px(11, 20, "x"); c.px(21, 20, "x"); c.hline(13, 20, 7, "d")   // bigote canoso
  c.hline(15, 22, 3, "R")
  // pelado con costados canosos y lápiz en la oreja
  c.rect(8, 9, 3, 6, "g"); c.rect(22, 9, 3, 6, "g"); c.hline(10, 7, 3, "f")
  c.line(23, 9, 27, 14, "y"); c.px(27, 14, "o")
  // anteojos sobre la frente
  c.box(11, 8, 4, 3, "o"); c.box(18, 8, 4, 3, "o"); c.hline(15, 9, 3, "o")
  ring(c)
})

sprite("av_galera", { w: 32, h: 32 }, (c) => {
  disc(c, ["u", "x", "d"])
  body(c, ["o", "u", "x"], { collar: "W" })
  c.rect(14, 25, 5, 2, "r"); c.px(16, 25, "R")                               // moño
  c.px(20, 28, "W"); c.px(21, 28, "l")                                        // pañuelo
  head(c, ["S", "s", "f"], { smile: false })
  c.hline(11, 19, 11, "o"); c.px(10, 18, "o"); c.px(22, 18, "o"); c.px(9, 17, "o"); c.px(23, 17, "o")   // bigote enrulado
  c.hline(15, 21, 3, "R")
  c.box(18, 13, 4, 4, "y"); c.line(22, 15, 24, 21, "y")                        // monóculo
  // galera
  c.rect(10, 0, 13, 7, "o"); c.rect(11, 1, 3, 5, "u"); c.rect(10, 5, 13, 2, "r")
  c.rect(6, 7, 21, 2, "o"); c.hline(7, 7, 19, "u")
  ring(c)
})

sprite("av_corona", { w: 32, h: 32 }, (c) => {
  disc(c, ["V", "v", "p"])
  body(c, ["R", "r", "p"])
  c.clip(DISC, () => { c.rect(10, 24, 12, 3, "W"); for (let x = 11; x < 22; x += 3) c.px(x, 25, "o") })   // armiño
  head(c, ["S", "s", "f"])
  c.ellipse(16, 9, 8, 3, "M"); c.rect(8, 9, 3, 6, "M"); c.rect(22, 9, 2, 6, "m")
  // corona dorada con piedras
  c.rect(8, 5, 17, 4, "y"); c.hline(8, 8, 17, "Y")
  for (const px of [8, 12, 16, 20, 24]) { c.rect(px, 2, 1, 3, "y"); c.px(px, 1, "Z") }
  c.hline(9, 6, 15, "Z")
  c.px(12, 6, "r"); c.px(16, 6, "B"); c.px(20, 6, "n")
  c.box(7, 4, 19, 6, "o")
  ring(c)
})
