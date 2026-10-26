class_name UnlockShow
extends CanvasLayer
## Festejo al comprar un negocio: la pantalla se oscurece, detrás del edificio
## giran rayos de luz dorados, cae confeti de fondo y aparece el cartel
## "¡NUEVO NEGOCIO!". Se cierra solo o con un toque. Sólo visual.

const DURATION := 4.0
const RAYS := 12
const CONFETTI_COLORS := [Color("d94a4a"), Color("ffd85c"), Color("75c4f2"), Color("4caf5c"), Color("9b6bc9"), Color("f59a45")]

static var current: UnlockShow

var bid := ""
var _root: Control
var _rays: Control
var _confetti: Control
var _bits: Array = []          ## [{rect, pos, vy, vx, phase}]
var _t := 0.0
var _spawn := 0.0
var _closing := false


static func play(id: String) -> void:
	if Main.instance == null:
		return
	if current and is_instance_valid(current):
		current.queue_free()
	var s := UnlockShow.new()
	s.bid = id
	current = s
	Main.instance.add_child(s)


## Cierra cualquier festejo abierto al instante (capturas automáticas).
static func dismiss_all() -> void:
	if current and is_instance_valid(current):
		current.queue_free()
	current = null


func _init() -> void:
	layer = 35          # arriba del tutorial (30), debajo de los avisos (40)


func _ready() -> void:
	var m := Game.m
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.theme = Main.instance.theme
	_root.mouse_filter = Control.MOUSE_FILTER_STOP
	_root.gui_input.connect(func(ev: InputEvent) -> void:
		if ev is InputEventMouseButton and ev.pressed and _t > 0.6:
			close())
	add_child(_root)
	var dim := ColorRect.new()
	dim.color = Color(0.06, 0.05, 0.12, 0.78)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(dim)
	_confetti = Control.new()
	_confetti.set_anchors_preset(Control.PRESET_FULL_RECT)
	_confetti.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_confetti)

	var vp := _root.get_viewport_rect().size
	var center := Vector2(vp.x / 2.0, vp.y * 0.42)
	_rays = Control.new()
	_rays.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_rays.size = Vector2(2, 2)
	_rays.position = center - Vector2.ONE
	_rays.pivot_offset = Vector2.ONE
	_rays.draw.connect(_draw_rays)
	_root.add_child(_rays)

	# El edificio en el nivel visual que tiene ahora (cuadro 0 si está animado).
	var tier: int = m.derive(bid)["tier"] if m.biz.has(bid) else 0
	var tex := U.tex("businesses/%s_%d.png" % [bid, tier])
	var pic := TextureRect.new()
	pic.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pic.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	if tex:
		var at := AtlasTexture.new()
		at.atlas = tex
		var fw := tex.get_width() / 2 if tex.get_width() >= 384 else tex.get_width()
		at.region = Rect2(0, 0, fw, tex.get_height())
		pic.texture = at
		pic.size = Vector2(fw, tex.get_height())
	pic.position = (center - pic.size / 2.0).round()
	pic.pivot_offset = pic.size / 2.0
	_root.add_child(pic)

	var title := U.label("¡NUEVO NEGOCIO!", U.SIZE_BIG, U.GOLD, true, HORIZONTAL_ALIGNMENT_CENTER)
	title.add_theme_color_override("font_outline_color", U.BG)
	title.add_theme_constant_override("outline_size", 4)
	title.size = Vector2(vp.x, 40)
	title.position = Vector2(0, center.y - pic.size.y / 2.0 - 58)
	title.pivot_offset = title.size / 2.0
	_root.add_child(title)
	var name := U.label(str(m.data.business_by_id.get(bid, {}).get("name", bid)), U.SIZE_TITLE, Color.WHITE, true, HORIZONTAL_ALIGNMENT_CENTER)
	name.add_theme_color_override("font_outline_color", U.BG)
	name.add_theme_constant_override("outline_size", 3)
	name.size = Vector2(vp.x, 30)
	name.position = Vector2(0, center.y + pic.size.y / 2.0 + 12)
	_root.add_child(name)
	var hint := U.label("Tocá para continuar", U.SIZE_SMALL, Color("c9c7da"), false, HORIZONTAL_ALIGNMENT_CENTER)
	hint.size = Vector2(vp.x, 20)
	hint.position = Vector2(0, name.position.y + 34)
	_root.add_child(hint)

	# Entrada: fondo que aparece, edificio con rebote, cartel que cae.
	_root.modulate.a = 0.0
	pic.scale = Vector2(0.2, 0.2)
	title.scale = Vector2(1.6, 1.6)
	var tw := create_tween().set_parallel(true)
	tw.tween_property(_root, "modulate:a", 1.0, 0.2)
	tw.tween_property(pic, "scale", Vector2.ONE, 0.5).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT).set_delay(0.1)
	tw.tween_property(title, "scale", Vector2.ONE, 0.35).set_trans(Tween.TRANS_BOUNCE).set_ease(Tween.EASE_OUT).set_delay(0.3)
	Main.instance.fx.sparkle_burst(center, 10)


func _draw_rays() -> void:
	var r := 420.0
	var step := TAU / RAYS
	for i in RAYS:
		var a := i * step
		var w := step * 0.32
		var col := Color(1.0, 0.85, 0.36, 0.30) if i % 2 == 0 else Color(1.0, 0.95, 0.75, 0.18)
		_rays.draw_colored_polygon(PackedVector2Array([Vector2.ONE, Vector2.ONE + Vector2.from_angle(a - w) * r, Vector2.ONE + Vector2.from_angle(a + w) * r]), col)
	# Halo central en anillos (pixelado, sin degradé suave).
	for k in 4:
		_rays.draw_circle(Vector2.ONE, 110.0 - k * 24.0, Color(1.0, 0.86, 0.4, 0.07 + k * 0.05))


func _process(delta: float) -> void:
	_t += delta
	var reduced := bool(Settings.get_value("reduce_motion"))
	_rays.rotation += delta * (0.15 if reduced else 0.55)
	# Confeti de fondo: cae desde arriba con vaivén mientras dura el festejo.
	var vp := _root.get_viewport_rect().size
	var rate: float = [25.0, 50.0, 80.0][Settings.fx_level()] * (0.3 if reduced else 1.0)
	_spawn += delta * rate
	while _spawn >= 1.0 and _t < DURATION - 0.8 and _bits.size() < 90:
		_spawn -= 1.0
		var c := ColorRect.new()
		c.mouse_filter = Control.MOUSE_FILTER_IGNORE
		c.color = CONFETTI_COLORS[randi() % CONFETTI_COLORS.size()]
		c.size = Vector2(2, 2 + (randi() % 2) * 2)
		c.position = Vector2(randf() * vp.x, -6).round()
		_confetti.add_child(c)
		_bits.append({"rect": c, "pos": c.position, "vy": randf_range(50, 110), "vx": randf_range(-12, 12), "phase": randf() * TAU})
	for i in range(_bits.size() - 1, -1, -1):
		var b: Dictionary = _bits[i]
		var c: ColorRect = b["rect"]
		b["phase"] = float(b["phase"]) + delta * 5.0
		b["pos"] += Vector2(float(b["vx"]) + sin(b["phase"]) * 18.0, float(b["vy"])) * delta
		c.position = (b["pos"] as Vector2).round()
		if c.position.y > vp.y + 4:
			c.queue_free()
			_bits.remove_at(i)
	if _t >= DURATION:
		close()


func close() -> void:
	if _closing:
		return
	_closing = true
	var tw := create_tween()
	tw.tween_property(_root, "modulate:a", 0.0, 0.25)
	tw.tween_callback(queue_free)
	if current == self:
		current = null
