extends TestCase
## Recorte de foto/banner, decodificación, guardado optimizado y migración.

const DIR := "user://test_profile"


func test_cover_inicial_centrado() -> void:
	var img := Vector2(1000, 500)
	var frame := Vector2(200, 200)
	var i := CropMath.initial(img, frame)
	near(i["scale"], 0.4, 0.0001, "cubre el alto")
	near(i["offset"].x, -100.0, 0.001, "centrado")
	near(i["offset"].y, 0.0, 0.001)
	var r := CropMath.source_rect(i["scale"], i["offset"], img, frame)
	eq(r, Rect2i(250, 0, 500, 500), "recorte cuadrado central sin deformar")


func test_no_deja_bordes_vacios() -> void:
	var img := Vector2(800, 600)
	var frame := Vector2(300, 100)
	var s := CropMath.clamp_scale(0.01, img, frame)
	near(s, CropMath.min_scale(img, frame), 0.0001, "zoom mínimo = cubrir")
	var off := CropMath.clamp_offset(Vector2(50, 50), s, img, frame)
	check(off.x <= 0.0 and off.y <= 0.0, "no se puede correr dejando hueco")
	off = CropMath.clamp_offset(Vector2(-99999, -99999), s, img, frame)
	check(off.x >= frame.x - img.x * s - 0.001, "límite derecho")
	near(CropMath.clamp_scale(999.0, img, frame), CropMath.min_scale(img, frame) * CropMath.MAX_ZOOM, 0.0001, "zoom máximo")


func test_zoom_mantiene_el_punto() -> void:
	var img := Vector2(1000, 1000)
	var frame := Vector2(200, 200)
	var i := CropMath.initial(img, frame)
	var pivot := Vector2(100, 100)
	var before: Vector2 = (pivot - i["offset"]) / i["scale"]
	var z := CropMath.zoom_at(i["scale"], i["offset"], 2.0, pivot, img, frame)
	var after: Vector2 = (pivot - z["offset"]) / z["scale"]
	near(before.distance_to(after), 0.0, 0.01, "el punto bajo los dedos queda quieto")
	var r := CropMath.source_rect(z["scale"], z["offset"], img, frame)
	eq(r.size, Vector2i(500, 500), "con zoom x2 se toma la mitad")


func _sample_png(w: int, h: int) -> PackedByteArray:
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	img.fill(Color.RED)
	img.fill_rect(Rect2i(0, 0, w / 2, h), Color.BLUE)
	return img.save_png_to_buffer()


func test_decodifica_por_firma() -> void:
	var png := ProfileImages.decode(_sample_png(40, 20))
	check(png != null, "PNG")
	eq(png.get_size(), Vector2i(40, 20))
	var jimg := Image.create(30, 30, false, Image.FORMAT_RGB8)
	jimg.fill(Color.GREEN)
	var jpg := ProfileImages.decode(jimg.save_jpg_to_buffer())
	check(jpg != null, "JPEG")
	check(ProfileImages.decode(PackedByteArray([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13])) == null, "basura rechazada")
	check(ProfileImages.decode(PackedByteArray()) == null, "vacío rechazado")


func test_achica_imagenes_enormes() -> void:
	var big := ProfileImages.decode(_sample_png(4096, 1024))
	eq(maxi(big.get_width(), big.get_height()), ProfileImages.MAX_SOURCE, "lado máximo")
	eq(big.get_width() / big.get_height(), 4, "sin deformar")


func test_orientacion_exif() -> void:
	# JPEG mínimo con APP1 Exif big-endian y orientación 6.
	var b := PackedByteArray([0xFF, 0xD8, 0xFF, 0xE1, 0x00, 0x22])
	b.append_array("Exif".to_ascii_buffer())
	b.append_array([0, 0, 0x4D, 0x4D, 0, 0x2A, 0, 0, 0, 8, 0, 1, 0x01, 0x12, 0, 3, 0, 0, 0, 1, 0, 6, 0, 0, 0, 0, 0, 0])
	eq(ProfileImages.jpeg_orientation(b), 6)
	var img := Image.create(40, 20, false, Image.FORMAT_RGBA8)
	ProfileImages.apply_orientation(img, 6)
	eq(img.get_size(), Vector2i(20, 40), "rotada")


func test_guarda_versiones_optimizadas() -> void:
	var src := ProfileImages.decode(_sample_png(900, 600))
	check(ProfileImages.save_cropped("photo", src, Rect2i(150, 0, 600, 600), DIR), "foto guardada")
	check(ProfileImages.save_cropped("banner", src, Rect2i(0, 150, 900, 300), DIR), "banner guardado")
	var p := Image.load_from_file(ProfileImages.path_for("photo", DIR))
	eq(p.get_size(), Vector2i(256, 256), "foto 256x256")
	var bn := Image.load_from_file(ProfileImages.path_for("banner", DIR))
	eq(bn.get_size(), Vector2i(768, 256), "banner 3:1")
	check(not FileAccess.file_exists(ProfileImages.path_for("photo", DIR).get_basename() + ".tmp.png"), "sin temporales")
	check(not ProfileImages.save_cropped("photo", src, Rect2i(0, 0, 0, 0), DIR), "rectángulo vacío rechazado")
	ProfileImages.clear("banner", DIR)
	check(not ProfileImages.has("banner", DIR), "restaurar banner por defecto")
	ProfileImages.clear("photo", DIR)


func test_migracion_v1_a_v2() -> void:
	var m := make_model()
	var d := m.to_dict()
	d.erase("ads")
	(d["profile"] as Dictionary).erase("photo")
	(d["profile"] as Dictionary).erase("banner")
	var migrated := Migrations.migrate(JSON.parse_string(JSON.stringify(d)), 1)
	check(migrated["ads"] is Dictionary, "registro de anuncios creado")
	eq(migrated["profile"]["photo"], false)
	var m2 := make_model()
	m2.from_dict(migrated)
	eq(m2.profile["company"], m.profile["company"], "el resto del perfil se conserva")
	eq(m2.economy.money, m.economy.money, "la economía se conserva")
	eq(m2.profile["banner"], false)


func test_settings_nuevos_persisten() -> void:
	var path := "user://test_settings.cfg"
	var s := SettingsData.new(path)
	s.values["master_volume"] = 0.3
	s.values["scene_view"] = "fachada"
	s.values["reduce_motion"] = true
	s.save()
	var s2 := SettingsData.new(path)
	s2.load()
	near(float(s2.values["master_volume"]), 0.3, 0.001)
	eq(s2.values["scene_view"], "fachada")
	eq(s2.values["reduce_motion"], true)
	DirAccess.remove_absolute(path)


func test_nombre_de_empresa_largo() -> void:
	var m := make_model()
	var largo := "Distribuidora Hermanos Fernández"   # 32 letras
	eq(largo.length(), 32)
	check(m.set_company_name(largo)["ok"], "acepta 32 letras")
	eq(m.profile["company"], largo, "se guarda completo")
	m.set_company_name(largo + " y Asociados del Sur")
	eq(m.profile["company"].length(), GameModel.COMPANY_MAX, "se recorta al máximo")
	check(not m.set_company_name(" a ")["ok"], "muy corto")


func test_niveles_sin_interior() -> void:
	# 10.0: BusinessScene.has_interior da false para los negocios que no están
	# en data/interiors.json (sin interior dibujado: sólo fachada).
	var d: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/interiors.json"))["businesses"]
	check(not d.has(B0), "el primer negocio todavía no tiene interior dibujado")
