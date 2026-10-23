class_name ImagePicker
extends RefCounted
## Selector de imágenes de la galería.
##
## - Android: selector nativo del sistema (Storage Access Framework). No pide
##   permisos de almacenamiento: el usuario elige un archivo puntual y el juego
##   recibe acceso sólo a ese archivo (URI content://).
## - Escritorio (y como alternativa): el diálogo de archivos de Godot.
##
## done(image: Image, error: String). Si el usuario cancela: (null, "").

const FILTERS := ["*.png, *.jpg, *.jpeg, *.webp ; Imágenes"]


static func pick(host: Node, done: Callable) -> void:
	var use_native := DisplayServer.has_feature(DisplayServer.FEATURE_NATIVE_DIALOG_FILE) and OS.has_feature("android")
	if use_native:
		var start_dir := OS.get_system_dir(OS.SYSTEM_DIR_PICTURES)
		var err := DisplayServer.file_dialog_show("Elegí una imagen", start_dir, "", false,
			DisplayServer.FILE_DIALOG_MODE_OPEN_FILE, PackedStringArray(FILTERS),
			func(status: bool, paths: PackedStringArray, _filter: int) -> void:
				# El resultado llega cuando Android devuelve el control al juego.
				_on_picked.call_deferred(status, paths, done))
		if err == OK:
			return
	_godot_dialog(host, done)


static func _on_picked(status: bool, paths: PackedStringArray, done: Callable) -> void:
	if not status or paths.is_empty():
		done.call(null, "")
		return
	load_path(paths[0], done)


static func load_path(path: String, done: Callable) -> void:
	var bytes := FileAccess.get_file_as_bytes(path)
	if bytes.is_empty():
		done.call(null, "No se pudo leer la imagen (%s)." % error_string(FileAccess.get_open_error()))
		return
	var img := ProfileImages.decode(bytes)
	if img == null:
		done.call(null, "Ese archivo no es una imagen compatible (PNG, JPG o WEBP).")
		return
	done.call(img, "")


static func _godot_dialog(host: Node, done: Callable) -> void:
	var dlg := FileDialog.new()
	dlg.file_mode = FileDialog.FILE_MODE_OPEN_FILE
	dlg.access = FileDialog.ACCESS_FILESYSTEM
	dlg.use_native_dialog = false
	dlg.filters = PackedStringArray(FILTERS)
	dlg.title = "Elegí una imagen"
	dlg.current_dir = OS.get_system_dir(OS.SYSTEM_DIR_PICTURES)
	var vp := host.get_viewport().get_visible_rect().size
	dlg.size = Vector2i(int(vp.x), int(vp.y * 0.8))
	var finished := [false]
	dlg.file_selected.connect(func(p: String) -> void:
		finished[0] = true
		dlg.queue_free()
		load_path(p, done))
	dlg.canceled.connect(func() -> void:
		if not finished[0]:
			dlg.queue_free()
			done.call(null, ""))
	host.add_child(dlg)
	dlg.popup_centered()
