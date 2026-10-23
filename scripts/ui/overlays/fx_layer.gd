class_name FxLayer
extends CanvasLayer
## Efectos decorativos pixelados: monedas, destellos, confeti y textos
## flotantes. No calculan nada ni capturan toques. La cantidad de partículas
## depende de la calidad de efectos (Ajustes) y tiene un tope global.

const MAX_PARTICLES := 40

var _root: Control
var _alive := 0


func _init() -> void:
	layer = 20


func _ready() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.theme = Main.instance.theme
	add_child(_root)


func _budget(n: int) -> int:
	var q := Settings.fx_level()
	var scaled: int = [n / 3, n * 2 / 3, n][q]
	if Settings.get_value("reduce_motion"):
		scaled = mini(scaled, 2)
	return mini(scaled, MAX_PARTICLES - _alive)


func _sprite(tex_path: String, frames: int, pos: Vector2) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = U.tex(tex_path)
	s.hframes = frames
	s.centered = true
	s.position = pos.round()
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_root.add_child(s)
	_alive += 1
	s.tree_exited.connect(func() -> void: _alive -= 1)
	return s


func coin_burst(pos: Vector2, count := 5) -> void:
	for i in _budget(count):
		var s := _sprite("particles/coin_spin.png", 4, pos)
		var target := pos + Vector2(randf_range(-26, 26), randf_range(-34, -14))
		var tw := s.create_tween().set_parallel(true)
		tw.tween_property(s, "position", target.round(), 0.35).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_OUT)
		tw.tween_method(func(v: float) -> void: s.frame = int(v) % 4, 0.0, 8.0, 0.6)
		tw.chain().tween_property(s, "position:y", target.y + 12, 0.25).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
		tw.parallel().tween_property(s, "modulate:a", 0.0, 0.25)
		tw.chain().tween_callback(s.queue_free)


func sparkle_burst(pos: Vector2, count := 6) -> void:
	for i in _budget(count):
		var s := _sprite("particles/sparkle.png", 4, pos + Vector2(randf_range(-40, 40), randf_range(-14, 14)))
		var tw := s.create_tween()
		tw.tween_interval(randf() * 0.2)
		tw.tween_method(func(v: float) -> void: s.frame = clampi(int(v), 0, 3), 0.0, 3.9, 0.4)
		tw.tween_callback(s.queue_free)


func confetti_burst(pos: Vector2, count := 18) -> void:
	var cols := [Color("d94a4a"), Color("ffd85c"), Color("75c4f2"), Color("4caf5c"), Color("9b6bc9"), Color("f59a45")]
	for i in _budget(count):
		var r := ColorRect.new()
		r.color = cols[i % cols.size()]
		r.size = Vector2(2, 2 + (i % 2) * 2)
		r.position = pos.round()
		r.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_root.add_child(r)
		_alive += 1
		r.tree_exited.connect(func() -> void: _alive -= 1)
		var end := pos + Vector2(randf_range(-120, 120), randf_range(40, 160))
		var tw := r.create_tween().set_parallel(true)
		tw.tween_property(r, "position:x", end.x, 1.1)
		tw.tween_property(r, "position:y", pos.y - randf_range(20, 60), 0.35).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_QUAD)
		tw.chain().tween_property(r, "position:y", end.y, 0.75).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_QUAD)
		tw.parallel().tween_property(r, "modulate:a", 0.0, 0.75)
		tw.chain().tween_callback(r.queue_free)


## Texto flotante "+$123" que sube y se desvanece.
func float_text(pos: Vector2, text: String, color := U.GOLD) -> void:
	if Settings.fx_level() == 0 and _alive > MAX_PARTICLES / 2:
		return
	var l := U.label(text, U.SIZE_BODY, color, true)
	l.add_theme_color_override("font_outline_color", U.BG)
	l.add_theme_constant_override("outline_size", 3)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(l)
	l.position = (pos - Vector2(l.get_combined_minimum_size().x / 2, 8)).round()
	_alive += 1
	l.tree_exited.connect(func() -> void: _alive -= 1)
	var tw := l.create_tween().set_parallel(true)
	tw.tween_property(l, "position:y", l.position.y - 22, 0.8).set_ease(Tween.EASE_OUT)
	tw.tween_property(l, "modulate:a", 0.0, 0.8).set_delay(0.35)
	tw.chain().tween_callback(l.queue_free)
