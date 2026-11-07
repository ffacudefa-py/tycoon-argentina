class_name DragScroll
extends ScrollContainer
## ScrollContainer que se arrastra con el dedo (o el mouse) desde cualquier
## punto, también encima de tarjetas y botones. Si el gesto pasa el umbral,
## el botón que se tocó no se activa. Al soltar sigue un poco por inercia.
## Si hay más contenido abajo, una flechita oscila en el borde inferior.

const THRESHOLD := 10.0
const FRICTION := 6.0
const HINT_SIZE := 24.0
const HINT_MARGIN := 6.0
const HINT_BOB := 4.0
## Cuánto contenido tiene que quedar abajo (px) para mostrar la flecha.
const HINT_MIN_LEFT := 8

var _tracking := false
var _dragging := false
var _start := Vector2.ZERO
var _start_scroll := 0
var _last_y := 0.0
var _last_t := 0
var _velocity := 0.0
var _coast := 0.0
## Mientras se inyecta el movimiento falso, ningún DragScroll lo procesa.
static var _fake := false
var _hint: PanelContainer
var _hint_t := 0.0


func _ready() -> void:
	# Ficha redonda crema con borde dorado: se lee encima de cualquier tarjeta.
	_hint = PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("fff1d6")
	sb.border_color = U.GOLD
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(int(HINT_SIZE / 2.0))
	sb.set_content_margin_all(3)
	_hint.add_theme_stylebox_override("panel", sb)
	_hint.custom_minimum_size = Vector2.ONE * HINT_SIZE
	var arrow := TextureRect.new()
	arrow.texture = U.icon_tex("flecha_arriba")
	arrow.flip_v = true
	arrow.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	arrow.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	arrow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hint.add_child(arrow)
	_hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hint.visible = false
	_hint.modulate.a = 0.0
	# Interno y al final: se dibuja encima del contenido y el ScrollContainer no lo acomoda.
	add_child(_hint, false, Node.INTERNAL_MODE_BACK)


## Queda contenido por ver más abajo.
func has_more_below() -> bool:
	var bar := get_v_scroll_bar()
	return bar.max_value - bar.page - scroll_vertical > HINT_MIN_LEFT


func _input(event: InputEvent) -> void:
	if _fake or not is_visible_in_tree():
		return
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_LEFT:
		if event.pressed:
			_tracking = get_global_rect().has_point(event.position)
			_dragging = false
			_velocity = 0.0
			_start = event.position
			_start_scroll = scroll_vertical
			_last_y = event.position.y
			_last_t = Time.get_ticks_usec()
		elif _tracking:
			_tracking = false
			# Si hubo arrastre, el botón ya recibió un "movimiento afuera": el
			# soltar le llega normal (libera el foco) pero no lo activa.
			if _dragging and Time.get_ticks_usec() - _last_t > 80000:
				_velocity = 0.0
			_coast = scroll_vertical
			_dragging = false
	elif event is InputEventMouseMotion and _tracking:
		if not _dragging:
			if absf(event.position.y - _start.y) < THRESHOLD or not _owns_hover():
				return
			_dragging = true
			_cancel_press(event)
		var dy: float = event.position.y - _last_y
		var now := Time.get_ticks_usec()
		var dt := maxf((now - _last_t) / 1000000.0, 0.004)
		_last_y = event.position.y
		_last_t = now
		_velocity = lerpf(_velocity, -dy / dt, 0.4)
		scroll_vertical = _start_scroll - int(event.position.y - _start.y)
		get_viewport().set_input_as_handled()


func _process(delta: float) -> void:
	_update_hint(delta)
	if _dragging or absf(_velocity) < 20.0:
		return
	_coast += _velocity * delta
	scroll_vertical = int(_coast)
	_velocity = lerpf(_velocity, 0.0, clampf(FRICTION * delta, 0.0, 1.0))
	var bar := get_v_scroll_bar()
	if scroll_vertical <= 0 or scroll_vertical >= int(bar.max_value - bar.page):
		_velocity = 0.0


func _update_hint(delta: float) -> void:
	var show := is_visible_in_tree() and has_more_below()
	_hint.visible = show
	if not show:
		_hint_t = 0.0
		return
	_hint_t += delta
	var bob := 0.0 if Settings.get_value("reduce_motion") else (0.5 + 0.5 * sin(_hint_t * 5.0)) * HINT_BOB
	_hint.position = Vector2(round((size.x - HINT_SIZE) / 2.0), round(size.y - HINT_SIZE - HINT_MARGIN - HINT_BOB + bob))
	# Aparece suave y se apaga mientras el dedo arrastra.
	_hint.modulate.a = move_toward(_hint.modulate.a, 0.35 if _dragging else 0.9, delta * 4.0)


## El gesto empezó sobre este scroll (y no sobre otro scroll interno, un
## modal o un overlay que esté encima).
func _owns_hover() -> bool:
	var c := get_viewport().gui_get_hovered_control()
	if c == null or not (c == self or is_ancestor_of(c)):
		return false
	var n := c
	while n != self:
		if n is DragScroll:
			return false
		n = n.get_parent()
	return true


## Simula que el dedo salió del control apretado, así el soltar no lo activa.
func _cancel_press(from: InputEventMouseMotion) -> void:
	var ev := InputEventMouseMotion.new()
	ev.position = Vector2(-10000, -10000)
	ev.global_position = ev.position
	ev.button_mask = from.button_mask
	_fake = true
	get_viewport().push_input(ev)
	_fake = false
