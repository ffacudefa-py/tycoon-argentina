class_name ProfileWidgets
extends RefCounted
## Foto y banner del perfil en la interfaz (barra superior, perfil, inicio).
## Si el jugador no eligió foto (o el archivo no está en este teléfono) se
## muestra su avatar pixel art; el banner por defecto es la calle del barrio.

static var _circle: ShaderMaterial


static func has_photo() -> bool:
	return bool(Game.m.profile.get("photo", false)) and ProfileImages.has("photo")


static func has_banner() -> bool:
	return bool(Game.m.profile.get("banner", false)) and ProfileImages.has("banner")


## Ajusta un TextureRect para mostrar la foto (círculo, suavizada) o el
## avatar pixel (nítido, sin máscara). Nunca deforma: KEEP_ASPECT_COVERED.
static func apply_avatar(tr: TextureRect) -> void:
	if has_photo():
		tr.texture = ProfileImages.texture("photo")
		tr.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		if _circle == null:
			_circle = CropScreen.circle_material()
		tr.material = _circle
	else:
		tr.texture = U.tex("avatars/%s.png" % Game.m.profile["avatar"])
		tr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		tr.material = null
	# Centrado (nunca recortado): la foto es cuadrada, así el círculo queda entero.
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED


static func apply_banner(tr: TextureRect) -> void:
	if has_banner():
		tr.texture = ProfileImages.texture("banner")
		tr.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	else:
		tr.texture = U.tex("locations/street_barrio.png")
		tr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED


## Menú de la foto: galería, avatar pixel o quitar la foto.
static func photo_menu() -> void:
	var body := U.vbox(6)
	var w_ref := []
	var gal := U.button("Elegir foto de la galería", "celeste", "persona", 36, U.SIZE_SMALL)
	U.on_press(gal, func() -> void:
		w_ref[0].close()
		pick("photo"))
	body.add_child(gal)
	var px := U.button("Usar avatar pixel art", "crema", "estrella", 36, U.SIZE_SMALL)
	U.on_press(px, func() -> void:
		w_ref[0].close()
		if has_photo():
			ProfileImages.clear("photo")
			Game.m.set_profile_image("photo", false)
		AvatarPicker.open())
	body.add_child(px)
	if has_photo():
		var rm := U.button("Quitar foto", "rojo", "cerrar", 32, U.SIZE_SMALL)
		U.on_press(rm, func() -> void:
			w_ref[0].close()
			ProfileImages.clear("photo")
			Game.m.set_profile_image("photo", false)
			Game.save_soon())
		body.add_child(rm)
	body.add_child(U.para("La foto se guarda sólo en este teléfono, en tamaño reducido (256x256).", U.SIZE_SMALL, U.TEXT_SOFT))
	w_ref.append(Main.instance.modal_host.open("Foto de perfil", body, true, 300))


static func banner_menu() -> void:
	var body := U.vbox(6)
	var w_ref := []
	var gal := U.button("Elegir banner de la galería", "celeste", "mapa", 36, U.SIZE_SMALL)
	U.on_press(gal, func() -> void:
		w_ref[0].close()
		pick("banner"))
	body.add_child(gal)
	if has_banner():
		var rs := U.button("Restaurar banner por defecto", "crema", "flecha_arriba", 32, U.SIZE_SMALL)
		U.on_press(rs, func() -> void:
			w_ref[0].close()
			ProfileImages.clear("banner")
			Game.m.set_profile_image("banner", false)
			Game.save_soon()
			Main.instance.toast("Banner restaurado.", "info"))
		body.add_child(rs)
	body.add_child(U.para("Formato horizontal 3:1 (768x256). Se guarda sólo en este teléfono.", U.SIZE_SMALL, U.TEXT_SOFT))
	w_ref.append(Main.instance.modal_host.open("Banner del perfil", body, true, 300))


## Abre el selector y, si el jugador elige una imagen, la pantalla de recorte.
static func pick(kind: String) -> void:
	ImagePicker.pick(Main.instance, func(img: Image, err: String) -> void:
		if err != "":
			Main.instance.toast(err, "bad")
			return
		if img == null:
			return                         # canceló el selector
		CropScreen.open(kind, img, func(saved: bool) -> void:
			if saved:
				Game.save_soon()))
