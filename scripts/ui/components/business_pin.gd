class_name BusinessPin
extends Control
## Negocio en el mapa de la región (estilo 11), con tres estados sin texto:
##   OPEN      a color; entra con rebote (escalonado) y respira con un brillo
##   AVAILABLE a color con un "+" dorado que late: se puede abrir
##   LOCKED    desaturado y oscuro con candado; al tocarlo el candado tiembla
## play_unlock(): el candado salta y se va, el negocio se ilumina y pasa a color.

signal picked(pin: BusinessPin)

enum State { OPEN, AVAILABLE, LOCKED }

const SIZE := 44                 ## área táctil (el dibujo es de 32 px, centrado)
static var _shader: Shader

var bid := ""
var zid := ""
var state := State.LOCKED
var _badge: TextureRect
var _lock: TextureRect
var _plus: Label
var _mat: ShaderMaterial
var _t := 0.0
var _busy := false
var _last_glow := 0.0
var _lock_bg: Panel
var _halo: Panel


static func shader() -> Shader:
	if _shader == null:
		_shader = Shader.new()
		_shader.code = """shader_type canvas_item;
uniform float gray = 0.0;
uniform float dark = 0.0;
uniform float glow = 0.0;
void fragment() {
	vec4 c = texture(TEXTURE, UV) * COLOR;
	float l = dot(c.rgb, vec3(0.299, 0.587, 0.114));
	c.rgb = mix(c.rgb, vec3(l), gray) * (1.0 - dark);
	c.rgb = mix(c.rgb, vec3(1.0, 0.96, 0.75), glow);
	COLOR = c;
}"""
	return _shader


func setup(p_bid: String, p_zid: String, p_state: int) -> void:
	bid = p_bid
	zid = p_zid
	state = p_state
	custom_minimum_size = Vector2(SIZE, SIZE)
	size = Vector2(SIZE, SIZE)
	pivot_offset = Vector2(SIZE / 2.0, SIZE)
	mouse_filter = Control.MOUSE_FILTER_STOP
	# plato crema con borde marrón debajo (como la base de los íconos de la referencia)
	var plate := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("dff6d8") if p_state == State.AVAILABLE else Color("f6efe2")
	if p_state == State.AVAILABLE:
		sb.border_color = Color("2e7d4f")
	# halo crema detrás de toda la casa (los bloqueados contrastan sobre provincias oscuras)
	_halo = Panel.new()
	var hsb := StyleBoxFlat.new()
	hsb.bg_color = Color(0.96, 0.94, 0.89, 0.55)
	hsb.set_corner_radius_all(14)
	_halo.add_theme_stylebox_override("panel", hsb)
	_halo.position = Vector2(4, 2)
	_halo.size = Vector2(SIZE - 8, SIZE - 8)
	_halo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_halo)
	sb.border_color = Color("3d1b0b")
	sb.set_border_width_all(1)
	sb.set_corner_radius_all(6)
	plate.add_theme_stylebox_override("panel", sb)
	plate.position = Vector2(5, SIZE - 14)
	plate.size = Vector2(SIZE - 10, 10)
	plate.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(plate)
	_badge = TextureRect.new()
	_badge.texture = U.tex("businesses/%s_badge.png" % bid)
	_badge.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_badge.position = Vector2(6, 4)
	_badge.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_mat = ShaderMaterial.new()
	_mat.shader = shader()
	_badge.material = _mat
	add_child(_badge)
	_lock_bg = Panel.new()                         # círculo crema detrás del candado
	var lsb := StyleBoxFlat.new()
	lsb.bg_color = Color("f6efe2")
	lsb.border_color = Color("3d1b0b")
	lsb.set_border_width_all(1)
	lsb.set_corner_radius_all(10)
	_lock_bg.add_theme_stylebox_override("panel", lsb)
	_lock_bg.size = Vector2(20, 20)
	_lock_bg.position = Vector2(SIZE - 22, SIZE - 24)
	_lock_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_lock_bg)
	_lock = U.icon("candado")
	_lock.position = Vector2(SIZE - 20, SIZE - 22)
	_lock.scale = Vector2.ONE
	_lock.pivot_offset = Vector2(8, 8)
	add_child(_lock)
	# insignia "+" dorada (disponible para abrir): círculo de 14 px con borde oscuro
	_plus = U.label("+", U.SIZE_SMALL, Color.WHITE, true, HORIZONTAL_ALIGNMENT_CENTER)
	var psb := StyleBoxFlat.new()
	psb.bg_color = Color("3fb06a")
	psb.border_color = Color("3d1b0b")
	psb.set_border_width_all(2)
	psb.set_corner_radius_all(6)
	psb.content_margin_left = 2
	psb.content_margin_right = 2
	psb.content_margin_top = 0
	psb.content_margin_bottom = 0
	_plus.add_theme_stylebox_override("normal", psb)
	_plus.add_theme_color_override("font_outline_color", Color("3d1b0b"))
	_plus.add_theme_constant_override("outline_size", 4)
	_plus.position = Vector2(SIZE - 14, -2)      # insignia chica, siempre arriba a la derecha
	_plus.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_plus)
	_apply()
	gui_input.connect(_on_input)


func _apply() -> void:
	var locked := state == State.LOCKED
	_mat.set_shader_parameter("gray", 0.75 if locked else 0.0)
	_mat.set_shader_parameter("dark", 0.12 if locked else 0.0)
	_lock.visible = locked
	_lock_bg.visible = locked
	_halo.visible = locked
	_plus.visible = state == State.AVAILABLE
	set_process(not locked)


func _on_input(ev: InputEvent) -> void:
	if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT and not ev.pressed:
		if get_global_rect().has_point(ev.global_position) or Rect2(Vector2.ZERO, size).has_point(ev.position):
			if state == State.LOCKED:
				shake()
			picked.emit(self)
			accept_event()


static func reduced() -> bool:
	return bool(Settings.get_value("reduce_motion"))


## Entrada con rebote (escala 0 → 1,15 → 1), escalonada por delay.
func play_enter(delay: float) -> void:
	if reduced():
		return
	scale = Vector2.ZERO
	var tw := create_tween()
	tw.tween_interval(delay)
	tw.tween_property(self, "scale", Vector2(1.15, 1.15), 0.18).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(self, "scale", Vector2.ONE, 0.1)


static var _hint: Control                   ## un solo globito a la vez


## Globito anclado al pin con lo que falta (1,5 s), con colita hacia el pin.
func show_hint(text: String) -> void:
	if is_instance_valid(_hint):
		_hint.queue_free()
	var l := U.label(text, U.SIZE_SMALL, Color("3d1b0b"), true, HORIZONTAL_ALIGNMENT_CENTER)
	_hint = l
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("f6efe2")
	sb.border_color = Color("94552a")
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(4)
	sb.content_margin_left = 6
	sb.content_margin_right = 6
	l.add_theme_stylebox_override("normal", sb)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	l.z_index = 10
	add_child(l)
	l.reset_size()
	# arriba del pin; abajo si no entra o si tapa a otro pin
	var up_rect := Rect2(get_global_rect().position + Vector2(SIZE / 2.0 - l.size.x / 2.0, -l.size.y - 6), l.size)
	var below := up_rect.position.y < 120.0
	for other in get_parent().get_children():
		if other != self and other is BusinessPin and up_rect.intersects((other as BusinessPin).get_global_rect()):
			below = true
	l.position = Vector2(SIZE / 2.0 - l.size.x / 2.0, SIZE + 6 if below else -l.size.y - 6)
	var tail := Panel.new()                        # colita del mismo color, con borde
	var tsb := StyleBoxFlat.new()
	tsb.bg_color = Color("f6efe2")
	tsb.border_color = Color("94552a")
	tsb.set_border_width_all(2)
	tail.add_theme_stylebox_override("panel", tsb)
	tail.size = Vector2(8, 8)
	tail.pivot_offset = Vector2(4, 4)
	tail.rotation = PI / 4.0
	tail.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tail.z_index = 11
	tail.position = Vector2(SIZE / 2.0 - 4, SIZE + 2 if below else -10)
	add_child(tail)
	var tw0 := tail.create_tween()
	tw0.tween_interval(2.5)
	tw0.tween_property(tail, "modulate:a", 0.0, 0.25)
	tw0.tween_callback(tail.queue_free)
	var gx := get_global_rect().position.x + l.position.x
	var vw := get_viewport_rect().size.x
	if gx < 4:
		l.position.x += 4 - gx
	elif gx + l.size.x > vw - 4:
		l.position.x -= gx + l.size.x - (vw - 4)
	var tw := l.create_tween()
	tw.tween_interval(2.5)
	tw.tween_property(l, "modulate:a", 0.0, 0.25)
	tw.tween_callback(l.queue_free)


func shake() -> void:
	Sfx.play("error")
	if reduced() or _busy:
		return
	_busy = true
	var tw := _lock.create_tween()
	for k in 4:
		tw.tween_property(_lock, "rotation", 0.35 if k % 2 == 0 else -0.35, 0.05)
	tw.tween_property(_lock, "rotation", 0.0, 0.05)
	tw.tween_callback(func() -> void: _busy = false)


## Recién desbloqueado: el candado salta y desaparece, flash y pasa a color.
func play_unlock(new_state: int, delay := 0.2) -> void:
	state = new_state
	if reduced():
		_apply()
		return
	_busy = true                                  # el idle no pisa el brillo durante la animación
	_lock.visible = true
	_plus.visible = false
	var tw := create_tween()
	tw.tween_interval(delay)
	for k in 3:
		tw.tween_property(_lock, "rotation", 0.4 if k % 2 == 0 else -0.4, 0.06)
	tw.tween_property(_lock, "rotation", 0.0, 0.05)
	tw.tween_callback(func() -> void: Sfx.play("unlock"))
	tw.tween_property(_lock, "position:y", _lock.position.y - 16, 0.3).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
	tw.parallel().tween_property(_lock, "modulate:a", 0.0, 0.3)
	tw.parallel().tween_property(_lock, "scale", Vector2(1.6, 1.6), 0.3)
	tw.parallel().tween_method(func(v: float) -> void:
		_mat.set_shader_parameter("gray", 0.85 * (1.0 - v))
		_mat.set_shader_parameter("dark", 0.45 * (1.0 - v))
		_mat.set_shader_parameter("glow", sin(v * PI) * 0.8), 0.0, 1.0, 0.45)
	tw.parallel().tween_property(self, "scale", Vector2(1.25, 1.25), 0.2).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(self, "scale", Vector2.ONE, 0.15)
	tw.tween_callback(func() -> void:
		_lock.position.y += 16
		_lock.modulate.a = 1.0
		_lock.scale = Vector2.ONE
		_apply()
		_busy = false
		if Main.instance and Main.instance.fx:
			Main.instance.fx.sparkle_burst(get_global_rect().get_center(), 6))


func _process(delta: float) -> void:
	if not is_visible_in_tree() or reduced() or _busy:
		return
	_t += delta
	if state == State.OPEN:
		# idle sutil: respira 1 px y brilla de vez en cuando (fase propia por negocio)
		var ph := float(hash(bid) % 100) / 16.0
		_badge.position.y = round(sin(_t * 2.2 + ph) * 1.0)
		var g := maxf(0.0, sin(_t * 0.9 + ph) - 0.92) * 2.0
		if g > 0.0 or _last_glow > 0.0:          # sólo se envía al shader cuando cambia
			_mat.set_shader_parameter("glow", g)
			_last_glow = g
	elif state == State.AVAILABLE:
		_plus.scale = Vector2.ONE * (1.0 + sin(_t * 5.0) * 0.12)
		_plus.pivot_offset = _plus.size / 2.0
