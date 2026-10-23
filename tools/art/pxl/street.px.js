// Piezas urbanas argentinas (pixel art 2.0, PXL): fachadas, vereda, calle,
// mobiliario urbano y elementos de cada zona. Escala 1 m = 24 px.
include("palette.px.js")

// ------------------------------------------------------------ fachadas porteñas
// Edificio de departamentos/casa con PB comercial. ramp = [sombra, medio, luz].
const WALLS = {
  crema: ["E", "e", "w"], celeste: ["B", "C", "c"], amarillo: ["Y", "y", "Z"], rosa: ["r", "p", "e"],
  verde: ["G", "n", "N"], gris: ["x", "d", "g"], ladrillo: ["R", "r", "p"], blanco: ["l", "w", "W"],
  naranja: ["Y", "q", "Z"], marron: ["m", "M", "t"],
}

function facade(name, w, floors, wall, opts = {}) {
  const h = 18 + floors * 34 + (opts.ground === false ? 0 : 40)
  sprite(name, { w, h, outline: "o" }, (c) => {
    const [sd, md, lt] = WALLS[wall]
    const rng = c.rng(opts.seed || 1)
    c.rect(0, 0, w, h, md)
    // textura de revoque / ladrillo
    if (wall === "ladrillo") {
      for (let y = 4, r = 0; y < h; y += 5, r++) { c.hline(0, y, w, sd); for (let x = (r % 2) * 6; x < w; x += 12) c.vline(x, y + 1, 4, sd) }
    } else c.noise(0, 0, w, h, sd + lt, 0.03, opts.seed || 1)
    c.vline(0, 0, h, lt); c.vline(w - 1, 0, h, sd); c.vline(w - 2, 0, h, sd)
    // cornisa con ménsulas y remate
    c.rect(0, 0, w, 6, lt); c.hline(0, 5, w, sd)
    for (let x = 3; x < w - 2; x += 6) c.rect(x, 6, 2, 2, sd)
    if (opts.dome) { c.circ(Math.floor(w / 2), 0, 8, "g"); c.ring(Math.floor(w / 2), 0, 8, "o"); c.vline(Math.floor(w / 2), -10, 4, "x") }
    // pisos con ventanas, persianas de madera y balcones de hierro
    for (let f = 0; f < floors; f++) {
      const y = 12 + f * 34
      const n = Math.max(1, Math.floor((w - 8) / 22))
      const span = Math.floor((w - 8) / n)
      for (let i = 0; i < n; i++) {
        const wx = 4 + i * span + Math.floor((span - 14) / 2)
        c.rect(wx - 1, y - 1, 16, 26, sd)
        c.rect(wx, y, 14, 24, "c"); c.rect(wx, y + 12, 14, 12, "C")
        const shut = rng() < 0.55
        if (shut) { const sh = 6 + Math.floor(rng() * 14); for (let yy = y; yy < y + sh; yy++) c.hline(wx, yy, 14, yy % 2 ? (opts.shutter || "n") : (opts.shutter2 || "G")) }
        else c.line(wx + 2, y + 21, wx + 9, y + 3, "W")
        c.vline(wx + 7, y, 24, "w")
        if (rng() < 0.3) { c.rect(wx + 2, y + 20, 10, 4, "n"); c.px(wx + 3, y + 19, "N"); c.px(wx + 8, y + 19, "p") }   // macetas
        if (rng() < 0.18 && f < floors) { c.rect(wx + 15, y + 6, 7, 6, "l"); c.hline(wx + 15, y + 6, 7, "W"); c.px(wx + 17, y + 9, "x"); c.px(wx + 19, y + 9, "x") }   // aire acondicionado
      }
      if (f > 0 || opts.ground === false || opts.balconyFirst) {   // balcón corrido
        c.rect(2, y + 25, w - 4, 3, sd); c.hline(2, y + 25, w - 4, lt)
        c.hline(2, y + 16, w - 4, "o"); for (let x = 2; x < w - 2; x += 3) c.vline(x, y + 16, 9, "o")
      }
    }
    // caño de lluvia
    c.rect(w - 6, 6, 2, h - 6, "x"); c.vline(w - 6, 6, h - 6, "d")
    // antena y tanque en la terraza
    if (opts.antenna !== false && rng() < 0.7) { const ax = 6 + Math.floor(rng() * (w - 20)); c.vline(ax, -14, 14, "x"); c.hline(ax - 5, -12, 11, "x"); c.hline(ax - 3, -9, 7, "x"); c.px(ax, -15, "r") }
    if (opts.tank) { c.rect(w - 20, -10, 12, 10, "l"); c.hline(w - 20, -10, 12, "W"); c.hline(w - 20, -6, 12, "g") }
    // planta baja comercial
    if (opts.ground !== false) {
      const gy = h - 40
      c.rect(0, gy, w, 40, opts.groundColor || sd)
      c.hline(0, gy, w, "o")
      const kind = opts.shop || ["persiana", "vidriera", "puerta"][Math.floor(rng() * 3)]
      const sw = w - 12
      if (kind === "persiana") {   // persiana metálica baja con firmas de colores
        c.rect(5, gy + 6, sw, 34, "g"); for (let yy = gy + 7; yy < h; yy += 2) c.hline(5, yy, sw, "d")
        const tags = ["r", "B", "n", "q"]; for (let i = 0; i < 3; i++) { const tx = 8 + Math.floor(rng() * (sw - 16)); c.line(tx, gy + 22, tx + 6, gy + 16 + i * 2, tags[i % 4], 2) }
        if (opts.forSale) { c.rect(Math.floor(w / 2) - 14, gy + 12, 28, 12, "W"); c.box(Math.floor(w / 2) - 14, gy + 12, 28, 12, "r"); c.text(Math.floor(w / 2) - 12, gy + 15, "SE VENDE", "r") }
      } else if (kind === "vidriera") {
        c.rect(5, gy + 6, sw, 34, "M"); c.rect(7, gy + 8, sw - 18, 26, "c"); c.rect(7, gy + 20, sw - 18, 14, "C")
        for (let x = 9; x < sw - 12; x += 5) c.rect(x, gy + 26, 3, 6, ["r", "y", "n", "B"][x % 4])
        c.rect(w - 15, gy + 8, 9, 32, "t"); c.px(w - 13, gy + 24, "Z")
        // toldo rayado
        const ac = opts.awning || "r"
        for (let x = 3; x < w - 3; x++) for (let yy = gy - 2; yy < gy + 5; yy++) c.px(x, yy, Math.floor((x - 3) / 4) % 2 ? "W" : ac)
        for (let x = 3; x < w - 3; x += 4) c.px(x + 1, gy + 5, Math.floor((x - 3) / 4) % 2 ? "l" : ac)
      } else {
        c.rect(Math.floor(w / 2) - 10, gy + 6, 20, 34, "M"); c.rect(Math.floor(w / 2) - 8, gy + 9, 7, 12, "c"); c.rect(Math.floor(w / 2) + 1, gy + 9, 7, 12, "c")
        c.rect(Math.floor(w / 2) - 10, gy + 2, 20, 4, "Y"); c.text(Math.floor(w / 2) - 5, gy + 1, String(100 + Math.floor(rng() * 900)), "o")
      }
    }
  })
}

facade("_fac_a", 64, 2, "crema", { seed: 3, shop: "vidriera", awning: "r", balconyFirst: true })
facade("_fac_b", 56, 3, "celeste", { seed: 7, shop: "persiana", tank: true })
facade("_fac_c", 72, 2, "rosa", { seed: 11, shop: "puerta", shutter: "M", shutter2: "m" })
facade("_fac_d", 60, 3, "amarillo", { seed: 5, shop: "vidriera", awning: "n" })
facade("_fac_e", 48, 1, "verde", { seed: 13, shop: "persiana", forSale: true })
facade("_fac_f", 80, 4, "blanco", { seed: 17, shop: "vidriera", awning: "A", tank: true })
facade("_fac_g", 64, 2, "ladrillo", { seed: 19, shop: "puerta" })
facade("_fac_h", 56, 2, "naranja", { seed: 23, shop: "vidriera", awning: "y" })
facade("_fac_i", 70, 5, "gris", { seed: 29, shop: "vidriera", awning: "u", tank: true })
facade("_fac_j", 52, 1, "crema", { seed: 31, shop: "persiana", dome: false })
facade("_fac_k", 90, 6, "blanco", { seed: 37, shop: "vidriera", awning: "B", dome: true })
facade("_fac_l", 60, 2, "marron", { seed: 41, shop: "puerta", shutter: "y", shutter2: "Y" })
group("barrio_casas", ["_fac_a", "_fac_c", "_fac_e", "_fac_g", "_fac_h", "_fac_j", "_fac_l", "_fac_d"])
group("centro_edif", ["_fac_b", "_fac_f", "_fac_i", "_fac_k", "_fac_d"])

// ------------------------------------------------------------------ vereda
// Baldosa "vainilla" porteña de 12x12 con sus puntitos.
sprite("_baldosa", { w: 12, h: 12 }, rect(0, 0, 12, 12, "e"), hline(0, 11, 12, "E"), vline(11, 0, 12, "E"),
  (c) => { for (let y = 2; y < 11; y += 3) for (let x = 2; x < 11; x += 3) c.px(x, y, "E") })
sprite("_baldosa_rota", { base: "_baldosa" }, line(2, 1, 6, 6, "M"), line(6, 6, 10, 9, "M"), px(7, 6, "E"))
sprite("_baldosa_mancha", { base: "_baldosa" }, ellipse(6, 7, 4, 2, "E"), px(5, 6, "T"))
group("baldosas", ["_baldosa", "_baldosa", "_baldosa", "_baldosa", "_baldosa", "_baldosa", "_baldosa_rota", "_baldosa_mancha"])

sprite("_tree", { w: 54, h: 92, outline: "o" },   // plátano con cazuela
  rect(23, 44, 8, 44, "M"), vline(23, 44, 44, "t"), vline(30, 44, 44, "m"), line(27, 54, 14, 40, "M", 3), line(27, 50, 40, 36, "M", 3),
  circ(27, 26, 22, "G"), circ(18, 30, 14, "n"), circ(36, 22, 14, "n"), circ(24, 16, 11, "N"), circ(40, 34, 9, "G"),
  noise(5, 4, 44, 44, "GN", 0.12, 4, "nG"), rect(14, 86, 26, 6, "m"), hline(14, 86, 26, "M"))
sprite("_lamp_post", { w: 22, h: 100 },
  rect(9, 10, 3, 88, "u"), vline(9, 10, 88, "x"), rect(7, 94, 7, 6, "u"), line(10, 12, 18, 8, "u", 2),
  rect(13, 2, 9, 6, "u"), rect(14, 7, 7, 3, "z"))
sprite("_trash", { w: 16, h: 26, outline: "o" },   // cesto naranja municipal
  rect(1, 4, 14, 16, "q"), hline(1, 4, 14, "Z"), vline(14, 4, 16, "Y"), rect(0, 2, 16, 3, "x"), rect(7, 20, 2, 6, "x"), rect(4, 9, 8, 3, "Y"))
sprite("_bench", { w: 40, h: 22, outline: "o" },
  rect(0, 0, 40, 4, "t"), rect(0, 6, 40, 4, "t"), hline(0, 0, 40, "T"), hline(0, 6, 40, "T"), rect(0, 12, 40, 4, "M"), hline(0, 12, 40, "t"),
  rect(3, 16, 3, 6, "x"), rect(34, 16, 3, 6, "x"))
sprite("_bus_stop", { w: 30, h: 70 },   // poste de parada de colectivo con números
  rect(13, 16, 3, 54, "x"), rect(2, 0, 26, 18, "y"), box(2, 0, 26, 18, "o"), text(5, 2, "60", "o"), text(16, 2, "152", "o"), text(5, 10, "39", "o"), text(18, 10, "29", "o"))
sprite("_hydrant", { w: 10, h: 14, outline: "o" }, rect(2, 2, 6, 12, "y"), rect(0, 5, 10, 3, "y"), rect(2, 0, 6, 3, "Y"))
sprite("_kiosk_news", { w: 40, h: 48, outline: "o" },   // puesto de diarios
  rect(0, 10, 40, 38, "n"), rect(0, 4, 40, 7, "G"), rect(3, 14, 34, 22, "w"),
  (c) => { for (let x = 5; x < 35; x += 8) c.rect(x, 16, 6, 9, ["r", "B", "y", "p"][x % 4]); for (let x = 5; x < 35; x += 8) c.rect(x, 26, 6, 8, ["W", "Z", "c", "N"][x % 4]) })
sprite("_cables", { w: 480, h: 20 }, wire(0, 2, 480, 4, 10, "o"), wire(0, 6, 480, 8, 8, "x"))
sprite("_manhole", { w: 18, h: 6 }, ellipse(9, 3, 8, 2, "x"), ellipse(9, 3, 6, 1, "u"), hline(4, 3, 10, "d"))

// ------------------------------------------------------------- vehículos
sprite("_colectivo", { w: 120, h: 48, outline: "o" },   // colectivo porteño fileteado
  rect(0, 4, 120, 36, "y"), rect(0, 4, 120, 4, "Z"), rect(0, 26, 120, 14, "r"), hline(0, 26, 120, "p"),
  (c) => { for (let x = 6; x < 100; x += 16) { c.rect(x, 10, 13, 13, "c"); c.rect(x, 17, 13, 6, "C"); c.line(x + 2, 21, x + 7, 12, "W") } },
  rect(104, 10, 14, 14, "c"), rect(104, 6, 14, 4, "u"), text(106, 6, "60", "Z"),
  (c) => { for (let x = 4; x < 116; x += 12) { c.px(x, 30, "Z"); c.px(x + 1, 31, "Z"); c.px(x + 2, 30, "W") } },   // fileteado
  rect(2, 36, 116, 4, "u"), circ(20, 40, 7, "o"), circ(20, 40, 3, "g"), circ(98, 40, 7, "o"), circ(98, 40, 3, "g"), rect(116, 28, 4, 4, "z"))
anim("colectivo_anim", { base: "_colectivo", fps: 6 }, frame(), frame(px(20, 37, "W"), px(98, 37, "W")))

// --------------------------------------------------------------- horizontes
sprite("_obelisco", { w: 16, h: 96 }, poly([5, 96, 11, 96, 9, 6, 7, 6], "l"), poly([7, 6, 9, 6, 8, 0], "l"), vline(7, 6, 90, "W"), rect(7, 30, 2, 2, "d"))
sprite("_crane", { w: 70, h: 90 }, rect(10, 10, 4, 80, "y"), line(12, 12, 66, 12, "y", 2), line(12, 12, 0, 18, "y", 2), rect(0, 16, 8, 6, "x"),
  vline(56, 12, 26, "x"), rect(52, 38, 9, 6, "r"), (c) => { for (let y = 14; y < 88; y += 6) c.line(10, y, 13, y + 4, "Y") })
sprite("_chimney", { w: 20, h: 70 }, rect(6, 10, 8, 60, "M"), vline(6, 10, 60, "t"), rect(4, 8, 12, 4, "x"), circ(10, 4, 4, "l"), circ(15, 0, 5, "w"))
sprite("_tower", { w: 34, h: 140 }, rect(0, 0, 34, 140, "A"), vline(0, 0, 140, "B"),
  (c) => { for (let y = 4; y < 136; y += 6) for (let x = 3; x < 31; x += 5) c.rect(x, y, 3, 3, (x + y) % 7 ? "c" : "Z") })
sprite("_palm", { w: 40, h: 70 }, line(20, 70, 22, 18, "M", 3), (c) => { for (const [dx, dy] of [[-16, 6], [-10, -6], [4, -10], [16, -2], [18, 8], [-18, 14]]) c.line(22, 18, 22 + dx, 18 + dy, "n", 3) }, circ(22, 18, 3, "G"))
sprite("_boat", { w: 40, h: 18, outline: "o" }, poly([0, 8, 40, 8, 34, 18, 6, 18], "W"), hline(0, 8, 40, "r"), rect(12, 0, 12, 8, "c"), vline(30, -10, 18, "x"))
sprite("_container", { w: 40, h: 16, outline: "o" }, rect(0, 0, 40, 16, "r"), (c) => { for (let x = 2; x < 40; x += 3) c.vline(x, 1, 14, "R") })
sprite("_clocktower", { w: 30, h: 90, outline: "o" }, rect(4, 20, 22, 70, "r"), (c) => { for (let y = 24; y < 90; y += 5) c.hline(4, y, 22, "R") },
  poly([2, 20, 28, 20, 15, 4], "R"), circ(15, 32, 6, "W"), ring(15, 32, 6, "o"), vline(15, 28, 4, "o"))
