class_name CropScreen
extends CanvasLayer
## Pantalla de recorte a pantalla completa (foto de perfil o banner).
##
## Gestos: arrastrar con un dedo mueve la imagen; pellizcar con dos dedos
## acerca/aleja (en escritorio: rueda del mouse). Además hay botones y un
## deslizador de zoom (accesibilidad). Arriba se ve la previsualización con la
## forma final. CONFIRMAR guarda la versión optimizada; CANCELAR no toca nada.

signal finished(saved: bool)

var kind := "photo"
var image: Image
var _root: Control
var _stage: Control           ## zona donde se dibuja la imagen y el marco
var _img_rect: TextureRect
var _frame := Vector2.ZERO
var _frame_pos := Vector2.ZERO
var _scale := 1.0
var _offset := Vector2.ZERO
var _zoom_slider: HSlider
var _preview: TextureRect
var _touches := {}            ## índice -> posición
var _pinch_dist := 0.0
var _mask: Control


static func open(p_kind: String, p_image: Image, on_done := Callable()) -> CropScreen:
	var c := CropScreen.new()
	c.kind = p_kind
	c.image = p_image
	if on_done.is_valid():
		c.finished.connect(on_done)
	Main.instance.add_child(c)
	return c


func _init() -> void:
	layer = 60


func _ready() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.theme = Main.instance.theme
	add_child(_root)
	var bg := ColorRect.new()
	bg.color = Color("1b1a2e")
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(bg)
	var col := U.vbox(8)
	col.set_anchors_preset(Control.PRESET_FULL_RECT)
	col.offset_left = 10
	col.offset_right = -10
	col.offset_top = 10 + _safe("top")
	col.offset_bottom = -10 - _safe("bottom")
	_root.add_child(col)
	var title := U.label("Recortá tu foto de perfil" if kind == "photo" else "Recortá tu banner", U.SIZE_TITLE, Color.WHITE, true, HORIZONTAL_ALIGNMENT_CENTER)
	col.add_child(title)
	# Previsualización con la forma final
	var prow := U.hbox(8)
	prow.alignment = BoxContainer.ALIGNMENT_CENTER
	_preview = TextureRect.new()
	_preview.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_preview.stretch_mode = TextureRect.STRETCH_SCALE
	_preview.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_preview.custom_minimum_size = Vector2(64, 64) if kind == "photo" else Vector2(192, 64)
	if kind == "photo":
		_preview.material = circle_material()
	prow.add_child(_preview)
	prow.add_child(U.label("Vista previa", U.SIZE_SMALL, Color("c9c7da")))
	col.add_child(prow)
	# Escenario del recorte
	_stage = Control.new()
	_stage.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_stage.clip_contents = true
	_stage.mouse_filter = Control.MOUSE_FILTER_STOP
	_stage.gui_input.connect(_on_stage_input)
	col.add_child(_stage)
	_img_rect = TextureRect.new()
	_img_rect.texture = ImageTexture.create_from_image(image)
	_img_rect.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_img_rect.stretch_mode = TextureRect.STRETCH_SCALE
	_img_rect.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_img_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stage.add_child(_img_rect)
	_mask = CropMask.new()
	_mask.owner_screen = self
	_mask.set_anchors_preset(Control.PRESET_FULL_RECT)
	_mask.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stage.add_child(_mask)
	col.add_child(U.label("Arrastrá para mover · pellizcá para acercar", U.SIZE_SMALL, Color("c9c7da"), false, HORIZONTAL_ALIGNMENT_CENTER))
	# Zoom accesible
	var zrow := U.hbox(6)
	var minus := U.button("−", "crema", "", 40, U.SIZE_TITLE)
	minus.custom_minimum_size.x = 44
	U.on_press(minus, func() -> void: _zoom(1.0 / 1.25, _frame_center()))
	zrow.add_child(minus)
	_zoom_slider = HSlider.new()
	_zoom_slider.min_value = 0.0
	_zoom_slider.max_value = 1.0
	_zoom_slider.step = 0.001
	_zoom_slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_zoom_slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_zoom_slider.custom_minimum_size.y = 24
	_zoom_slider.value_changed.connect(_on_slider)
	zrow.add_child(_zoom_slider)
	var plus := U.button("+", "crema", "", 40, U.SIZE_TITLE)
	plus.custom_minimum_size.x = 44
	U.on_press(plus, func() -> void: _zoom(1.25, _frame_center()))
	zrow.add_child(plus)
	col.add_child(zrow)
	var brow := U.hbox(8)
	var cancel := U.button("CANCELAR", "crema", "", 44, U.SIZE_BODY)
	cancel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	U.on_press(cancel, func() -> void: _finish(false))
	brow.add_child(cancel)
	var ok := U.button("CONFIRMAR", "celeste", "check", 44, U.SIZE_BODY)
	ok.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	U.on_press(ok, _confirm, "")
	brow.add_child(ok)
	col.add_child(brow)
	_stage.resized.connect(_layout_stage)
	_layout_stage.call_deferred()


func _safe(side: String) -> int:
	return Main.instance._safe.get_theme_constant("margin_" + side) if Main.instance and Main.instance._safe else 0


static func circle_material() -> ShaderMaterial:
	var sh := Shader.new()
	sh.code = """shader_type canvas_item;
void fragment() {
	vec2 d = UV - vec2(0.5);
	float r = length(d);
	vec4 c = texture(TEXTURE, UV);
	COLOR = vec4(c.rgb, c.a * (1.0 - smoothstep(0.49, 0.5, r)));
}"""
	var m := ShaderMaterial.new()
	m.shader = sh
	return m


func _layout_stage() -> void:
	var sz := _stage.size
	if sz.x <= 0 or sz.y <= 0:
		return
	if kind == "photo":
		var d := floorf(minf(sz.x - 20, sz.y - 20))
		_frame = Vector2(d, d)
	else:
		var w := floorf(sz.x - 8)
		_frame = Vector2(w, floorf(w / 3.0))
	_frame_pos = ((sz - _frame) / 2.0).floor()
	var init := CropMath.initial(Vector2(image.get_size()), _frame)
	_scale = init["scale"]
	_offset = init["offset"]
	_apply()


func _apply() -> void:
	var isz := Vector2(image.get_size())
	_img_rect.position = _frame_pos + _offset
	_img_rect.size = isz * _scale
	var lo := CropMath.min_scale(isz, _frame)
	_zoom_slider.set_value_no_signal(log(_scale / lo) / log(CropMath.MAX_ZOOM))
	_mask.queue_redraw()
	_update_preview()


func _update_preview() -> void:
	var r := CropMath.source_rect(_scale, _offset, Vector2(image.get_size()), _frame)
	if r.size.x <= 0 or r.size.y <= 0:
		return
	var at := AtlasTexture.new()
	at.atlas = _img_rect.texture
	at.region = Rect2(r)
	_preview.texture = at


func _frame_center() -> Vector2:
	return _frame / 2.0


func _zoom(factor: float, pivot_in_frame: Vector2) -> void:
	var r := CropMath.zoom_at(_scale, _offset, factor, pivot_in_frame, Vector2(image.get_size()), _frame)
	_scale = r["scale"]
	_offset = r["offset"]
	_apply()


func _on_slider(v: float) -> void:
	var lo := CropMath.min_scale(Vector2(image.get_size()), _frame)
	var target := lo * pow(CropMath.MAX_ZOOM, v)
	_zoom(target / _scale, _frame_center())


func _pan(delta: Vector2) -> void:
	_offset = CropMath.clamp_offset(_offset + delta, _scale, Vector2(image.get_size()), _frame)
	_apply()


func _on_stage_input(ev: InputEvent) -> void:
	if ev is InputEventScreenTouch:
		if ev.pressed:
			_touches[ev.index] = ev.position
		else:
			_touches.erase(ev.index)
		_pinch_dist = 0.0
	elif ev is InputEventScreenDrag:
		var prev: Vector2 = _touches.get(ev.index, ev.position)
		_touches[ev.index] = ev.position
		if _touches.size() >= 2:
			var pts: Array = _touches.values()
			var dist := (pts[0] as Vector2).distance_to(pts[1])
			var mid: Vector2 = ((pts[0] as Vector2) + (pts[1] as Vector2)) / 2.0
			if _pinch_dist > 0.0:
				_zoom(dist / _pinch_dist, mid - _frame_pos)
			_pinch_dist = dist
		else:
			_pan(ev.position - prev)
	elif ev is InputEventMouseMotion and (ev.button_mask & MOUSE_BUTTON_MASK_LEFT) and _touches.is_empty():
		_pan(ev.relative)
	elif ev is InputEventMouseButton and ev.pressed:
		if ev.button_index == MOUSE_BUTTON_WHEEL_UP:
			_zoom(1.1, ev.position - _frame_pos)
		elif ev.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_zoom(1.0 / 1.1, ev.position - _frame_pos)
	elif ev is InputEventMagnifyGesture:
		_zoom(ev.factor, ev.position - _frame_pos)


func _confirm() -> void:
	var r := CropMath.source_rect(_scale, _offset, Vector2(image.get_size()), _frame)
	var ok := ProfileImages.save_cropped(kind, image, r)
	if ok:
		Game.m.set_profile_image(kind, true)
		Sfx.play("upgrade")
		Main.instance.toast("¡Foto de perfil actualizada!" if kind == "photo" else "¡Banner actualizado!", "good")
	else:
		Main.instance.toast("No se pudo guardar la imagen. Probá con otra.", "bad")
	_finish(ok)


func _finish(saved: bool) -> void:
	finished.emit(saved)
	queue_free()


## Máscara: oscurece afuera del marco y dibuja su borde (círculo o 3:1).
class CropMask extends Control:
	var owner_screen: CropScreen

	func _draw() -> void:
		var s := owner_screen
		var r := Rect2(s._frame_pos, s._frame)
		var shade := Color(0.06, 0.05, 0.12, 0.7)
		draw_rect(Rect2(0, 0, size.x, r.position.y), shade)
		draw_rect(Rect2(0, r.end.y, size.x, size.y - r.end.y), shade)
		draw_rect(Rect2(0, r.position.y, r.position.x, r.size.y), shade)
		draw_rect(Rect2(r.end.x, r.position.y, size.x - r.end.x, r.size.y), shade)
		if s.kind == "photo":
			# esquinas del cuadrado también oscuras: queda el círculo
			var c := r.get_center()
			var rad := r.size.x / 2.0
			var pts := PackedVector2Array()
			for k in 65:
				var a := TAU * k / 64.0
				pts.append(c + Vector2(cos(a), sin(a)) * rad)
			for q in 4:
				var corner := PackedVector2Array()
				var a0 := q * PI / 2.0
				var cx := r.position.x + (r.size.x if q in [0, 3] else 0.0)
				var cy := r.position.y + (r.size.y if q in [0, 1] else 0.0)
				corner.append(Vector2(cx, cy))
				for k in 17:
					var a := a0 + (PI / 2.0) * k / 16.0
					corner.append(c + Vector2(cos(a), sin(a)) * rad)
				draw_colored_polygon(corner, shade)
			draw_polyline(pts, Color("74acdf"), 2.0)
		else:
			draw_rect(r, Color("74acdf"), false, 2.0)
