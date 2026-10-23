class_name ProfileImages
extends RefCounted
## Foto de perfil y banner: decodificación, corrección de orientación,
## versiones optimizadas y almacenamiento local.
##
## Se guardan en el almacenamiento interno de la app (user://profile/), que en
## Android no necesita permisos y sobrevive a cerrar la app. Tamaños:
##   foto 256x256 (se muestra en un círculo), banner 768x256 (3:1).
## Integración futura con la nube: subir estos mismos PNG asociados al uid de
## Firebase (hoy el proyecto está en plan Spark, sin Storage). No hay
## sincronización implementada: todo queda en el teléfono.

const DIR := "user://profile"
const SIZES := {"photo": Vector2i(256, 256), "banner": Vector2i(768, 256)}
const MAX_SOURCE := 2048     ## lado máximo con el que se trabaja al recortar

static var _cache := {}       ## kind -> Texture2D


static func path_for(kind: String, dir := DIR) -> String:
	return "%s/%s.png" % [dir, kind]


## Decodifica PNG / JPEG / WEBP según su firma (no según la extensión: en
## Android el selector devuelve URIs content:// sin extensión).
static func decode(bytes: PackedByteArray) -> Image:
	if bytes.size() < 12:
		return null
	var img := Image.new()
	var err := ERR_FILE_UNRECOGNIZED
	if bytes[0] == 0x89 and bytes[1] == 0x50:
		err = img.load_png_from_buffer(bytes)
	elif bytes[0] == 0xFF and bytes[1] == 0xD8:
		err = img.load_jpg_from_buffer(bytes)
		if err == OK:
			apply_orientation(img, jpeg_orientation(bytes))
	elif bytes.slice(0, 4).get_string_from_ascii() == "RIFF" and bytes.slice(8, 12).get_string_from_ascii() == "WEBP":
		err = img.load_webp_from_buffer(bytes)
	if err != OK or img.is_empty():
		return null
	# Trabajar con imágenes enormes gasta memoria al pedo: se achican.
	var big := maxi(img.get_width(), img.get_height())
	if big > MAX_SOURCE:
		var k := float(MAX_SOURCE) / big
		img.resize(int(img.get_width() * k), int(img.get_height() * k), Image.INTERPOLATE_BILINEAR)
	if img.get_format() != Image.FORMAT_RGBA8:
		img.convert(Image.FORMAT_RGBA8)
	return img


## Lee la etiqueta EXIF de orientación (0x0112) de un JPEG. 1 = normal.
static func jpeg_orientation(b: PackedByteArray) -> int:
	var i := 2
	while i + 4 < b.size() and b[i] == 0xFF:
		var marker := b[i + 1]
		var seg_len := (b[i + 2] << 8) | b[i + 3]
		if marker == 0xE1 and i + 10 < b.size() and b.slice(i + 4, i + 8).get_string_from_ascii() == "Exif":
			var t := i + 10                      # inicio del encabezado TIFF
			var le := b[t] == 0x49               # "II" = little endian
			var rd16 := func(p: int) -> int: return (b[p] | (b[p + 1] << 8)) if le else ((b[p] << 8) | b[p + 1])
			var rd32 := func(p: int) -> int: return (b[p] | (b[p + 1] << 8) | (b[p + 2] << 16) | (b[p + 3] << 24)) if le else ((b[p] << 24) | (b[p + 1] << 16) | (b[p + 2] << 8) | b[p + 3])
			var ifd: int = t + rd32.call(t + 4)
			if ifd + 2 > b.size():
				return 1
			var n: int = rd16.call(ifd)
			for k in n:
				var e := ifd + 2 + k * 12
				if e + 10 > b.size():
					break
				if rd16.call(e) == 0x0112:
					return clampi(rd16.call(e + 8), 1, 8)
			return 1
		if marker == 0xDA:
			break
		i += 2 + seg_len
	return 1


static func apply_orientation(img: Image, o: int) -> void:
	match o:
		2: img.flip_x()
		3: img.rotate_180()
		4: img.flip_y()
		5:
			img.rotate_90(CLOCKWISE)
			img.flip_x()
		6: img.rotate_90(CLOCKWISE)
		7:
			img.rotate_90(COUNTERCLOCKWISE)
			img.flip_x()
		8: img.rotate_90(COUNTERCLOCKWISE)


## Recorta, genera la versión optimizada y la guarda (escritura atómica).
static func save_cropped(kind: String, src: Image, rect: Rect2i, dir := DIR) -> bool:
	if rect.size.x <= 0 or rect.size.y <= 0:
		return false
	var out := src.get_region(rect)
	var target: Vector2i = SIZES[kind]
	out.resize(target.x, target.y, Image.INTERPOLATE_LANCZOS)
	DirAccess.make_dir_recursive_absolute(dir)
	var final_path := path_for(kind, dir)
	var tmp := final_path.get_basename() + ".tmp.png"   # la extensión define el formato al releer
	if out.save_png(tmp) != OK:
		return false
	# Verificación: se puede volver a leer.
	var check := Image.load_from_file(tmp)
	if check == null or check.get_size() != target:
		DirAccess.remove_absolute(tmp)
		return false
	if FileAccess.file_exists(final_path):
		DirAccess.remove_absolute(final_path)
	if DirAccess.rename_absolute(tmp, final_path) != OK:
		return false
	_cache.erase(kind)
	return true


static func texture(kind: String, dir := DIR) -> Texture2D:
	if _cache.has(kind):
		return _cache[kind]
	var p := path_for(kind, dir)
	if not FileAccess.file_exists(p):
		return null
	var img := Image.load_from_file(p)
	if img == null:
		return null
	var tex := ImageTexture.create_from_image(img)
	_cache[kind] = tex
	return tex


static func clear(kind: String, dir := DIR) -> void:
	var p := path_for(kind, dir)
	if FileAccess.file_exists(p):
		DirAccess.remove_absolute(p)
	_cache.erase(kind)


static func has(kind: String, dir := DIR) -> bool:
	return FileAccess.file_exists(path_for(kind, dir))
