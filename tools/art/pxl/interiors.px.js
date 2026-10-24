// GENERADO por gen_interiors.py — no editar a mano.
include("furniture.px.js")
include("rooms.px.js")

scene("int_puesto_0", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("vereda", "vereda", true, 0), stamp("_umbrella", 150, 42), stamp("_price_board", 120, 108)),
  layer("front", stamp("_stall_table", 154, 112)))
scene("int_puesto_1", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("vereda", "vereda", true, 1), stamp("_umbrella", 150, 42), stamp("_price_board", 120, 108), stamp("_cooler", 246, 116), stamp("_crate", 280, 130), stamp("_crate", 96, 130)),
  layer("front", stamp("_stall_table", 154, 112)))
scene("int_puesto_2", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("vereda", "vereda", true, 2), stamp("_umbrella", 150, 42), stamp("_price_board", 120, 108), stamp("_cooler", 246, 116), stamp("_crate", 280, 130), stamp("_crate", 96, 130), stamp("_string_lights", 100, 20)),
  layer("front", stamp("_stall_table", 154, 112), stamp("_register", 208, 95)))
scene("int_puesto_3", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("azulejo", "damero", false, 3), stamp("_shelf_wood", 40, 38), stamp("_fridge_drinks", 96, 38), stamp("_fileteado_sign", 164, 14), stamp("_pennant", 250, 10), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 360, 4)),
  layer("front", stamp("_counter_wood", 150, 114), stamp("_register", 196, 97), stamp("_mate_set", 178, 103)))
scene("int_puesto_4", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("azulejo", "damero", false, 4), stamp("_shelf_wood", 40, 38), stamp("_fridge_drinks", 96, 38), stamp("_fileteado_sign", 164, 14), stamp("_pennant", 250, 10), stamp("_shelf_wood", 300, 38), stamp("_clock", 140, 40), stamp("_plant", 360, 110), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 200, 4), stamp("_lamp_hanging", 360, 4)),
  layer("front", stamp("_counter_wood", 150, 114), stamp("_register", 196, 97), stamp("_mate_set", 178, 103), stamp("_counter_glass", 236, 114)))
scene("int_kiosco_0", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("azulejo", "damero", false, 0), stamp("_shelf_wood", 30, 38), stamp("_poster", 100, 24), stamp("_lamp_hanging", 40, 4), stamp("_wall_shelf", 132, 40)),
  layer("front", stamp("_counter_glass", 150, 114), stamp("_register", 196, 97)))
scene("int_kiosco_1", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("azulejo", "damero", false, 1), stamp("_shelf_wood", 30, 38), stamp("_poster", 100, 24), stamp("_fridge_drinks", 86, 38), stamp("_shelf_metal", 230, 36), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 360, 4), stamp("_wall_shelf", 132, 40)),
  layer("front", stamp("_counter_glass", 150, 114), stamp("_register", 196, 97)))
scene("int_kiosco_2", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("azulejo", "damero", false, 2), stamp("_shelf_wood", 30, 38), stamp("_poster", 100, 24), stamp("_fridge_drinks", 86, 38), stamp("_shelf_metal", 230, 36), stamp("_clock", 132, 30), stamp("_shelf_wood", 290, 38), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 200, 4), stamp("_lamp_hanging", 360, 4)),
  layer("front", stamp("_counter_glass", 150, 114), stamp("_register", 196, 97), stamp("_mate_set", 178, 103)))
scene("int_kiosco_3", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("azulejo", "damero", false, 3), stamp("_shelf_wood", 30, 38), stamp("_poster", 100, 24), stamp("_fridge_drinks", 86, 38), stamp("_shelf_metal", 230, 36), stamp("_clock", 132, 30), stamp("_shelf_wood", 290, 38), stamp("_freezer", 330, 118), stamp("_pennant", 160, 8), stamp("_jersey", 200, 30), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_glass", 150, 114), stamp("_register", 196, 97), stamp("_mate_set", 178, 103), stamp("_counter_glass", 230, 114)))
scene("int_kiosco_4", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("azulejo", "damero", false, 4), stamp("_shelf_wood", 30, 38), stamp("_poster", 100, 24), stamp("_fridge_drinks", 86, 38), stamp("_shelf_metal", 230, 36), stamp("_clock", 132, 30), stamp("_shelf_wood", 290, 38), stamp("_freezer", 330, 118), stamp("_pennant", 160, 8), stamp("_jersey", 200, 30), stamp("_plant", 10, 120), stamp("_cart", 360, 120), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_glass", 150, 114), stamp("_register", 196, 97), stamp("_mate_set", 178, 103), stamp("_counter_glass", 230, 114)))
scene("int_comida_0", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("vereda", "vereda", true, 0), stamp("_prep_table", 60, 82)),
  layer("front", stamp("_grill", 160, 106)))
scene("int_comida_1", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("vereda", "vereda", true, 1), stamp("_prep_table", 60, 82), stamp("_umbrella", 140, 26), stamp("_cafe_table", 280, 120), stamp("_chalkboard", 110, 122)),
  layer("front", stamp("_grill", 160, 106)))
scene("int_comida_2", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("vereda", "vereda", true, 2), stamp("_prep_table", 60, 82), stamp("_umbrella", 140, 26), stamp("_cafe_table", 280, 120), stamp("_chalkboard", 110, 122), stamp("_string_lights", 60, 18), stamp("_cafe_table", 330, 126)),
  layer("front", stamp("_grill", 160, 106)))
scene("int_comida_3", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("ladrillo", "madera", false, 3), stamp("_grill", 30, 68), stamp("_wine_rack", 110, 52), stamp("_dining_table", 240, 120), stamp("_dining_table", 300, 126), stamp("_fileteado_sign", 150, 12), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 200, 4), stamp("_lamp_hanging", 360, 4)),
  layer("front", stamp("_counter_wood", 150, 114), stamp("_register", 196, 97)))
scene("int_comida_4", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("ladrillo", "madera", false, 4), stamp("_grill", 30, 68), stamp("_wine_rack", 110, 52), stamp("_dining_table", 240, 120), stamp("_dining_table", 300, 126), stamp("_fileteado_sign", 150, 12), stamp("_dining_table", 350, 114), stamp("_stove", 250, 62), stamp("_jersey", 200, 40), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_wood", 150, 114), stamp("_register", 196, 97)))
scene("int_lavadero_0", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 0), stamp("_wash_bay", 40, 78)),
  layer("front", px(0, 0, ".")))
scene("int_lavadero_1", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 1), stamp("_wash_bay", 40, 78), stamp("_vacuum", 150, 104), stamp("_drums", 360, 110)),
  layer("front", px(0, 0, ".")))
scene("int_lavadero_2", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 2), stamp("_wash_bay", 40, 78), stamp("_vacuum", 150, 104), stamp("_drums", 360, 110), stamp("_wash_bay", 180, 78)),
  layer("front", px(0, 0, ".")))
scene("int_lavadero_3", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 3), stamp("_wash_bay", 40, 78), stamp("_vacuum", 150, 104), stamp("_drums", 360, 110), stamp("_wash_bay", 180, 78), stamp("_desk_pc", 296, 70), stamp("_poster", 300, 20)),
  layer("front", stamp("_counter_metal", 300, 116)))
scene("int_lavadero_4", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 4), stamp("_wash_bay", 40, 78), stamp("_vacuum", 150, 104), stamp("_drums", 360, 110), stamp("_wash_bay", 180, 78), stamp("_desk_pc", 296, 70), stamp("_poster", 300, 20), stamp("_fileteado_sign", 150, 6), stamp("_plant", 376, 120), stamp("_clock", 260, 10)),
  layer("front", stamp("_counter_metal", 300, 116)))
scene("int_almacen_0", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("azulejo", "madera", false, 0), stamp("_shelf_almacen", 30, 34), stamp("_salames", 150, 30), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 360, 4), stamp("_wall_shelf", 186, 40)),
  layer("front", stamp("_counter_wood", 140, 114), stamp("_scale", 190, 101)))
scene("int_almacen_1", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("azulejo", "madera", false, 1), stamp("_shelf_almacen", 30, 34), stamp("_salames", 150, 30), stamp("_shelf_almacen", 92, 34), stamp("_crate", 240, 136), stamp("_crate", 262, 136), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 360, 4), stamp("_wall_shelf", 186, 40)),
  layer("front", stamp("_counter_wood", 140, 114), stamp("_scale", 190, 101)))
scene("int_almacen_2", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("azulejo", "madera", false, 2), stamp("_shelf_almacen", 30, 34), stamp("_salames", 150, 30), stamp("_shelf_almacen", 92, 34), stamp("_crate", 240, 136), stamp("_crate", 262, 136), stamp("_clock", 210, 18), stamp("_shelf_almacen", 290, 34), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 200, 4), stamp("_lamp_hanging", 360, 4)),
  layer("front", stamp("_counter_wood", 140, 114), stamp("_scale", 190, 101), stamp("_slicer", 162, 99)))
scene("int_almacen_3", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("azulejo", "madera", false, 3), stamp("_shelf_almacen", 30, 34), stamp("_salames", 150, 30), stamp("_shelf_almacen", 92, 34), stamp("_crate", 240, 136), stamp("_crate", 262, 136), stamp("_clock", 210, 18), stamp("_shelf_almacen", 290, 34), stamp("_fridge_drinks", 30, 38), stamp("_fileteado_sign", 150, 8), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 200, 4), stamp("_lamp_hanging", 360, 4)),
  layer("front", stamp("_counter_wood", 140, 114), stamp("_scale", 190, 101), stamp("_slicer", 162, 99), stamp("_mate_set", 168, 103), stamp("_counter_glass", 220, 114)))
scene("int_almacen_4", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("azulejo", "madera", false, 4), stamp("_shelf_almacen", 30, 34), stamp("_salames", 150, 30), stamp("_shelf_almacen", 92, 34), stamp("_crate", 240, 136), stamp("_crate", 262, 136), stamp("_clock", 210, 18), stamp("_shelf_almacen", 290, 34), stamp("_fridge_drinks", 30, 38), stamp("_fileteado_sign", 150, 8), stamp("_pennant", 240, 6), stamp("_plant", 6, 120), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_wood", 140, 114), stamp("_scale", 190, 101), stamp("_slicer", 162, 99), stamp("_mate_set", 168, 103), stamp("_counter_glass", 220, 114)))
scene("int_cafeteria_0", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("madera_pared", "damero", false, 0), stamp("_counter_wood", 40, 82), stamp("_coffee_machine", 54, 52), stamp("_chalkboard", 140, 20), stamp("_cafe_table", 240, 124), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 360, 4), stamp("_wall_shelf", 186, 40)),
  layer("front", stamp("_pastry_case", 140, 112), stamp("_register", 174, 95)))
scene("int_cafeteria_1", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("madera_pared", "damero", false, 1), stamp("_counter_wood", 40, 82), stamp("_coffee_machine", 54, 52), stamp("_chalkboard", 140, 20), stamp("_cafe_table", 240, 124), stamp("_cafe_table", 300, 128), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 200, 4), stamp("_lamp_hanging", 360, 4), stamp("_wall_shelf", 222, 40)),
  layer("front", stamp("_pastry_case", 140, 112), stamp("_register", 174, 95)))
scene("int_cafeteria_2", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("madera_pared", "damero", false, 2), stamp("_counter_wood", 40, 82), stamp("_coffee_machine", 54, 52), stamp("_chalkboard", 140, 20), stamp("_cafe_table", 240, 124), stamp("_cafe_table", 300, 128), stamp("_cafe_table", 350, 120), stamp("_clock", 250, 20), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4), stamp("_wall_shelf", 276, 40)),
  layer("front", stamp("_pastry_case", 140, 112), stamp("_register", 174, 95)))
scene("int_cafeteria_3", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("madera_pared", "damero", false, 3), stamp("_counter_wood", 40, 82), stamp("_coffee_machine", 54, 52), stamp("_chalkboard", 140, 20), stamp("_cafe_table", 240, 124), stamp("_cafe_table", 300, 128), stamp("_cafe_table", 350, 120), stamp("_clock", 250, 20), stamp("_shelf_wood", 330, 38), stamp("_poster", 290, 22), stamp("_plant", 214, 120), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_pastry_case", 140, 112), stamp("_register", 174, 95)))
scene("int_cafeteria_4", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("madera_pared", "damero", false, 4), stamp("_counter_wood", 40, 82), stamp("_coffee_machine", 54, 52), stamp("_chalkboard", 140, 20), stamp("_cafe_table", 240, 124), stamp("_cafe_table", 300, 128), stamp("_cafe_table", 350, 120), stamp("_clock", 250, 20), stamp("_shelf_wood", 330, 38), stamp("_poster", 290, 22), stamp("_plant", 214, 120), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_pastry_case", 140, 112), stamp("_register", 174, 95), stamp("_counter_glass", 16, 114)))
scene("int_restaurante_0", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("ladrillo", "madera", false, 0), stamp("_stove", 30, 62), stamp("_prep_table", 100, 80), stamp("_dining_table", 260, 120), stamp("_fileteado_sign", 170, 10), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 360, 4), stamp("_wall_shelf", 252, 40)),
  layer("front", stamp("_counter_wood", 170, 114)))
scene("int_restaurante_1", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("ladrillo", "madera", false, 1), stamp("_stove", 30, 62), stamp("_prep_table", 100, 80), stamp("_dining_table", 260, 120), stamp("_fileteado_sign", 170, 10), stamp("_dining_table", 320, 126), stamp("_wine_rack", 360, 52), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 200, 4), stamp("_lamp_hanging", 360, 4), stamp("_wall_shelf", 252, 40)),
  layer("front", stamp("_counter_wood", 170, 114)))
scene("int_restaurante_2", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("ladrillo", "madera", false, 2), stamp("_stove", 30, 62), stamp("_prep_table", 100, 80), stamp("_dining_table", 260, 120), stamp("_fileteado_sign", 170, 10), stamp("_dining_table", 320, 126), stamp("_wine_rack", 360, 52), stamp("_clock", 250, 20), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4), stamp("_wall_shelf", 276, 40)),
  layer("front", stamp("_counter_wood", 170, 114)))
scene("int_restaurante_3", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("ladrillo", "madera", false, 3), stamp("_stove", 30, 62), stamp("_prep_table", 100, 80), stamp("_dining_table", 260, 120), stamp("_fileteado_sign", 170, 10), stamp("_dining_table", 320, 126), stamp("_wine_rack", 360, 52), stamp("_clock", 250, 20), stamp("_dining_table", 300, 100), stamp("_jersey", 300, 24), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_wood", 170, 114)))
scene("int_restaurante_4", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("ladrillo", "madera", false, 4), stamp("_stove", 30, 62), stamp("_prep_table", 100, 80), stamp("_dining_table", 260, 120), stamp("_fileteado_sign", 170, 10), stamp("_dining_table", 320, 126), stamp("_wine_rack", 360, 52), stamp("_clock", 250, 20), stamp("_dining_table", 300, 100), stamp("_jersey", 300, 24), stamp("_stove", 230, 62), stamp("_plant", 6, 120), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_wood", 170, 114)))
scene("int_supermercado_0", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_super", "ceramica", false, 0), stamp("_gondola", 20, 44), stamp("_cart", 100, 126), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 360, 4), stamp("_wall_shelf", 102, 40)),
  layer("front", stamp("_checkout", 140, 104)))
scene("int_supermercado_1", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_super", "ceramica", false, 1), stamp("_gondola", 20, 44), stamp("_cart", 100, 126), stamp("_gondola", 96, 44), stamp("_fridge_drinks", 300, 38), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 200, 4), stamp("_lamp_hanging", 360, 4), stamp("_wall_shelf", 222, 40)),
  layer("front", stamp("_checkout", 140, 104)))
scene("int_supermercado_2", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_super", "ceramica", false, 2), stamp("_gondola", 20, 44), stamp("_cart", 100, 126), stamp("_gondola", 96, 44), stamp("_fridge_drinks", 300, 38), stamp("_freezer", 330, 116), stamp("_gondola", 214, 44), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_checkout", 140, 104)))
scene("int_supermercado_3", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_super", "ceramica", false, 3), stamp("_gondola", 20, 44), stamp("_cart", 100, 126), stamp("_gondola", 96, 44), stamp("_fridge_drinks", 300, 38), stamp("_freezer", 330, 116), stamp("_gondola", 214, 44), stamp("_poster", 180, 10), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_checkout", 140, 104), stamp("_checkout", 230, 104)))
scene("int_supermercado_4", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_super", "ceramica", false, 4), stamp("_gondola", 20, 44), stamp("_cart", 100, 126), stamp("_gondola", 96, 44), stamp("_fridge_drinks", 300, 38), stamp("_freezer", 330, 116), stamp("_gondola", 214, 44), stamp("_poster", 180, 10), stamp("_fridge_drinks", 40, 38), stamp("_cart", 370, 130), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_checkout", 140, 104), stamp("_checkout", 230, 104)))
scene("int_gimnasio_0", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_gym", "goma", false, 0), stamp("_mirror", 30, 22), stamp("_treadmill", 30, 98), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 360, 4)),
  layer("front", stamp("_counter_metal", 160, 116)))
scene("int_gimnasio_1", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_gym", "goma", false, 1), stamp("_mirror", 30, 22), stamp("_treadmill", 30, 98), stamp("_weight_rack", 240, 64), stamp("_water_cooler", 120, 64), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 200, 4), stamp("_lamp_hanging", 360, 4)),
  layer("front", stamp("_counter_metal", 160, 116)))
scene("int_gimnasio_2", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_gym", "goma", false, 2), stamp("_mirror", 30, 22), stamp("_treadmill", 30, 98), stamp("_weight_rack", 240, 64), stamp("_water_cooler", 120, 64), stamp("_bench_press", 250, 114), stamp("_punching_bag", 350, 40), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_metal", 160, 116)))
scene("int_gimnasio_3", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_gym", "goma", false, 3), stamp("_mirror", 30, 22), stamp("_treadmill", 30, 98), stamp("_weight_rack", 240, 64), stamp("_water_cooler", 120, 64), stamp("_bench_press", 250, 114), stamp("_punching_bag", 350, 40), stamp("_treadmill", 90, 106), stamp("_mirror", 250, 20), stamp("_poster", 140, 22), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_metal", 160, 116)))
scene("int_gimnasio_4", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_gym", "goma", false, 4), stamp("_mirror", 30, 22), stamp("_treadmill", 30, 98), stamp("_weight_rack", 240, 64), stamp("_water_cooler", 120, 64), stamp("_bench_press", 250, 114), stamp("_punching_bag", 350, 40), stamp("_treadmill", 90, 106), stamp("_mirror", 250, 20), stamp("_poster", 140, 22), stamp("_plant", 376, 120), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_metal", 160, 116)))
scene("int_taller_0", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 0), stamp("_car_lift", 30, 74), stamp("_tool_wall", 140, 30)),
  layer("front", stamp("_counter_metal", 290, 116)))
scene("int_taller_1", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 1), stamp("_car_lift", 30, 74), stamp("_tool_wall", 140, 30), stamp("_tires", 220, 102), stamp("_drums", 254, 110)),
  layer("front", stamp("_counter_metal", 290, 116)))
scene("int_taller_2", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 2), stamp("_car_lift", 30, 74), stamp("_tool_wall", 140, 30), stamp("_tires", 220, 102), stamp("_drums", 254, 110), stamp("_workbench", 140, 80)),
  layer("front", stamp("_counter_metal", 290, 116)))
scene("int_taller_3", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 3), stamp("_car_lift", 30, 74), stamp("_tool_wall", 140, 30), stamp("_tires", 220, 102), stamp("_drums", 254, 110), stamp("_workbench", 140, 80), stamp("_car", 200, 126), stamp("_poster", 290, 20), stamp("_clock", 340, 20)),
  layer("front", stamp("_counter_metal", 290, 116)))
scene("int_taller_4", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 4), stamp("_car_lift", 30, 74), stamp("_tool_wall", 140, 30), stamp("_tires", 220, 102), stamp("_drums", 254, 110), stamp("_workbench", 140, 80), stamp("_car", 200, 126), stamp("_poster", 290, 20), stamp("_clock", 340, 20), stamp("_fileteado_sign", 20, 4)),
  layer("front", stamp("_counter_metal", 290, 116)))
scene("int_mensajeria_0", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_celeste", "ceramica", false, 0), stamp("_parcel_shelf", 20, 42), stamp("_scooter", 300, 116), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 360, 4)),
  layer("front", stamp("_counter_wood", 150, 114), stamp("_scale", 200, 101)))
scene("int_mensajeria_1", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_celeste", "ceramica", false, 1), stamp("_parcel_shelf", 20, 42), stamp("_scooter", 300, 116), stamp("_desk_pc", 90, 74), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 200, 4), stamp("_lamp_hanging", 360, 4)),
  layer("front", stamp("_counter_wood", 150, 114), stamp("_scale", 200, 101)))
scene("int_mensajeria_2", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_celeste", "ceramica", false, 2), stamp("_parcel_shelf", 20, 42), stamp("_scooter", 300, 116), stamp("_desk_pc", 90, 74), stamp("_parcel_shelf", 240, 42), stamp("_filing", 312, 62), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_wood", 150, 114), stamp("_scale", 200, 101)))
scene("int_mensajeria_3", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_celeste", "ceramica", false, 3), stamp("_parcel_shelf", 20, 42), stamp("_scooter", 300, 116), stamp("_desk_pc", 90, 74), stamp("_parcel_shelf", 240, 42), stamp("_filing", 312, 62), stamp("_conveyor", 30, 118), stamp("_scooter", 296, 122), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_wood", 150, 114), stamp("_scale", 200, 101)))
scene("int_mensajeria_4", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("pintura_celeste", "ceramica", false, 4), stamp("_parcel_shelf", 20, 42), stamp("_scooter", 300, 116), stamp("_desk_pc", 90, 74), stamp("_parcel_shelf", 240, 42), stamp("_filing", 312, 62), stamp("_conveyor", 30, 118), stamp("_scooter", 296, 122), stamp("_clock", 200, 16), stamp("_water_cooler", 360, 64), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_wood", 150, 114), stamp("_scale", 200, 101)))
scene("int_distribuidora_0", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 0), stamp("_pallet_rack", 20, 38), stamp("_pallet_boxes", 120, 118), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 360, 4)),
  layer("front", stamp("_counter_metal", 300, 116)))
scene("int_distribuidora_1", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 1), stamp("_pallet_rack", 20, 38), stamp("_pallet_boxes", 120, 118), stamp("_forklift", 160, 102), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 200, 4), stamp("_lamp_hanging", 360, 4)),
  layer("front", stamp("_counter_metal", 300, 116)))
scene("int_distribuidora_2", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 2), stamp("_pallet_rack", 20, 38), stamp("_pallet_boxes", 120, 118), stamp("_forklift", 160, 102), stamp("_dock_door", 262, 32), stamp("_pallet_rack", 176, 38), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_metal", 300, 116)))
scene("int_distribuidora_3", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 3), stamp("_pallet_rack", 20, 38), stamp("_pallet_boxes", 120, 118), stamp("_forklift", 160, 102), stamp("_dock_door", 262, 32), stamp("_pallet_rack", 176, 38), stamp("_conveyor", 110, 118), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_metal", 300, 116)))
scene("int_distribuidora_4", { w: 400, h: 170, bg: "u", layers: true },
  layer("back", room("chapa", "cemento", false, 4), stamp("_pallet_rack", 20, 38), stamp("_pallet_boxes", 120, 118), stamp("_forklift", 160, 102), stamp("_dock_door", 262, 32), stamp("_pallet_rack", 176, 38), stamp("_conveyor", 110, 118), stamp("_machine", 100, 62), stamp("_poster", 230, 6), stamp("_lamp_hanging", 40, 4), stamp("_lamp_hanging", 146, 4), stamp("_lamp_hanging", 252, 4), stamp("_lamp_hanging", 358, 4)),
  layer("front", stamp("_counter_metal", 300, 116)))
