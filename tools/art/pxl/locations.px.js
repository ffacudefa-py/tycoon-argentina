// Escenarios urbanos por zona (480x200) y fondo de la pantalla de inicio.
// Medidas que usa el juego (scripts/ui/components/business_scene.gd):
//   fachadas apoyadas en y=150, vereda 150..182, cordón 182..186, calle 186..200,
//   base de los negocios en y=168, peatones con los pies en y=178.
include("street.px.js")

const SIDE = 150, CURB = 182, ROAD = 186

function sidewalkAndStreet(c, w, opts = {}) {
  c.pattern("baldosas", 0, SIDE, w, CURB - SIDE, { reseed: true })
  c.hline(0, SIDE, w, "o")
  c.noise(0, SIDE + 1, w, CURB - SIDE - 1, "E", 0.03, 9)              // mugre y desgaste
  c.rect(0, CURB, w, 4, "l"); c.hline(0, CURB, w, "W"); c.hline(0, CURB + 3, w, "d")
  c.rect(0, ROAD, w, 200 - ROAD, "x"); c.noise(0, ROAD, w, 200 - ROAD, "ud", 0.18, 5)
  c.hline(0, ROAD, w, "u")
  for (let x = 12; x < w; x += 44) c.rect(x, ROAD + 8, 20, 2, opts.lane || "w")
  if (opts.zebra) for (let x = opts.zebra; x < opts.zebra + 60; x += 8) c.rect(x, ROAD + 1, 4, 13, "w")
}

function sky(c, w, top, bottom, clouds = true) {
  c.grad(0, 0, w, SIDE, top, "v", 0.6)
  if (clouds) for (const [x, y, r] of [[60, 20, 8], [74, 16, 11], [90, 21, 7], [300, 34, 7], [314, 30, 10], [330, 35, 6], [420, 14, 6]]) {
    c.ellipse(x, y, r * 2, r, "W"); c.ellipse(x + 2, y + 3, r * 2 - 2, Math.max(1, r - 4), bottom)
  }
}

function zone(name, o) {
  scene(name, { w: 480, h: 200, bg: "c" },
    layer("cielo", (c) => sky(c, 480, o.sky, o.cloudShade || "l", o.clouds !== false)),
    layer("horizonte", o.far || ((c) => {})),
    layer("fachadas", (c) => {
      let x = -8
      const pool = o.facades
      let i = 0
      while (x < 480) {
        const n = pool[i % pool.length]
        const sz = { _fac_a: 64, _fac_b: 56, _fac_c: 72, _fac_d: 60, _fac_e: 48, _fac_f: 80, _fac_g: 64, _fac_h: 56, _fac_i: 70, _fac_j: 52, _fac_k: 90, _fac_l: 60 }[n]
        const hh = { _fac_a: 2, _fac_b: 3, _fac_c: 2, _fac_d: 3, _fac_e: 1, _fac_f: 4, _fac_g: 2, _fac_h: 2, _fac_i: 5, _fac_j: 1, _fac_k: 6, _fac_l: 2 }[n]
        const h = 18 + hh * 34 + 40 + 2
        c.stamp(n, x, SIDE - h + 1)
        x += sz + 1; i++
      }
    }),
    layer("cables", stamp("_cables", 0, 52)),
    layer("vereda", (c) => sidewalkAndStreet(c, 480, o)),
    layer("objetos", ...(o.props || [])),
    layer("sombras", { shade: true, density: 0.5 }, rect(0, SIDE + 1, 480, 5, "o")))
}

const PROPS_BARRIO = [stamp("_tree", 18, 90), stamp("_lamp_post", 112, 80), stamp("_trash", 150, 156), stamp("_tree", 396, 90), stamp("_lamp_post", 360, 80),
  stamp("_bench", 300, 158), stamp("_hydrant", 250, 168), stamp("_manhole", 210, 190)]

zone("loc_barrio", { sky: "Cc", facades: ["_fac_c", "_fac_a", "_fac_e", "_fac_h", "_fac_g", "_fac_j", "_fac_l", "_fac_d"], props: PROPS_BARRIO })
zone("loc_centro", { sky: "BCc", facades: ["_fac_f", "_fac_b", "_fac_i", "_fac_k", "_fac_d", "_fac_f"], zebra: 200, lane: "y",
  far: (c) => { c.stamp("_obelisco", 232, 54); c.stamp("_tower", 40, 10); c.stamp("_tower", 420, 0) },
  props: [stamp("_bus_stop", 120, 112), stamp("_kiosk_news", 330, 136), stamp("_lamp_post", 60, 80), stamp("_lamp_post", 400, 80), stamp("_trash", 300, 156), stamp("_manhole", 150, 190)] })
zone("loc_universidad", { sky: "Cc", facades: ["_fac_g", "_fac_g", "_fac_a", "_fac_l", "_fac_g"],
  far: (c) => { c.stamp("_clocktower", 220, 40) },
  props: [stamp("_tree", 30, 90), stamp("_tree", 250, 90), stamp("_bench", 100, 158), stamp("_bench", 330, 158), stamp("_lamp_post", 200, 80), stamp("_trash", 420, 156)] })
zone("loc_costanera", { sky: "cW", facades: ["_fac_j", "_fac_e"], clouds: true,
  far: (c) => { c.rect(0, 96, 480, 54, "C"); c.noise(0, 96, 480, 54, "Bc", 0.08, 3); c.hline(0, 96, 480, "B"); c.stamp("_boat", 300, 88); c.stamp("_boat", 120, 100) },
  props: [stamp("_palm", 40, 84), stamp("_palm", 210, 84), stamp("_palm", 400, 84), stamp("_bench", 120, 158), stamp("_bench", 320, 158), stamp("_lamp_post", 280, 80)] })
zone("loc_industrial", { sky: "ZTc", facades: ["_fac_l", "_fac_e", "_fac_b", "_fac_j"], cloudShade: "E",
  far: (c) => { c.stamp("_chimney", 80, 40); c.stamp("_chimney", 300, 30); c.stamp("_chimney", 420, 50) },
  props: [stamp("_lamp_post", 140, 80), stamp("_trash", 260, 156), stamp("_manhole", 330, 190), stamp("_hydrant", 60, 168)] })
zone("loc_puerto", { sky: "BCc", facades: ["_fac_i", "_fac_b", "_fac_l"],
  far: (c) => { c.stamp("_crane", 40, 40); c.stamp("_crane", 330, 30); for (let i = 0; i < 6; i++) c.stamp("_container", 150 + i * 30, 120 - (i % 2) * 16, { swap: [{}, { r: "B", R: "A" }, { r: "n", R: "G" }][i % 3] }) },
  props: [stamp("_lamp_post", 100, 80), stamp("_lamp_post", 380, 80), stamp("_trash", 220, 156)] })
zone("loc_financiero", { sky: "AB", facades: ["_fac_k", "_fac_i", "_fac_f"], lane: "y",
  far: (c) => { c.stamp("_tower", 20, 0); c.stamp("_tower", 120, -10); c.stamp("_tower", 340, 4); c.stamp("_tower", 440, -6) },
  props: [stamp("_lamp_post", 60, 80), stamp("_lamp_post", 300, 80), stamp("_bench", 180, 158), stamp("_trash", 400, 156)] })

// Fondo de la pantalla de inicio: atardecer porteño con ventanas encendidas.
scene("start_bg", { w: 400, h: 720, bg: "u" },
  layer("cielo", grad(0, 0, 400, 520, "uxApqZ", "v", 0.7)),
  layer("estrellas", (c) => { const r = c.rng(3); for (let i = 0; i < 40; i++) c.px(Math.floor(r() * 400), Math.floor(r() * 220), "w") }),
  layer("horizonte", stamp("_obelisco", 222, 300), stamp("_tower", 20, 340, { swap: { c: "z", Z: "Z", A: "u", B: "x" } }), stamp("_tower", 350, 330, { swap: { c: "z", A: "u", B: "x" } })),
  layer("fachadas", (c) => {
    const row = ["_fac_f", "_fac_c", "_fac_b", "_fac_a", "_fac_k", "_fac_h"], ws = [80, 72, 56, 64, 90, 56], fl = [4, 2, 3, 2, 6, 2]
    let x = -10
    for (let i = 0; i < row.length; i++) { const h = 18 + fl[i] * 34 + 42; c.stamp(row[i], x, 560 - h + 1); x += ws[i] + 1 }
  }),
  shade([0, 380, 400, 181], 1),
  recolor({ c: "z", C: "Z" }, [0, 380, 400, 181], 0.55),
  layer("cables", stamp("_cables", 0, 300)),
  layer("vereda", (c) => {
    c.pattern("baldosas", 0, 560, 400, 60, { reseed: true }); c.hline(0, 560, 400, "o")
    c.rect(0, 620, 400, 5, "l"); c.hline(0, 620, 400, "W"); c.rect(0, 625, 400, 95, "x"); c.noise(0, 625, 400, 95, "ud", 0.18, 5)
    for (let x = 10; x < 400; x += 46) c.rect(x, 668, 22, 3, "w")
  }),
  layer("objetos", stamp("_lamp_post", 40, 462), stamp("_lamp_post", 330, 462), stamp("_tree", 120, 470), stamp("_bench", 220, 540), stamp("_trash", 300, 536)),
  shade([0, 561, 400, 159], 1),
  glow("z", { r: 10, strength: 0.6, where: [0, 440, 400, 140] }))
