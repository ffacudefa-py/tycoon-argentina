class_name StartScreen
extends CanvasLayer
## Pantalla de inicio (punto de entrada).
##
## Fondo pixel art animado (avenida al atardecer, colectivo que pasa), logo y
## menú según el estado REAL de la cuenta (Auth):
##   sin sesión: JUGAR / CONTINUAR (como invitado), INICIAR SESIÓN, CONFIGURACIÓN
##   con sesión: tarjeta de perfil, CONTINUAR, CONFIGURACIÓN
## Va en la capa 9: los modales (10), avisos (40) y diálogos se ven encima;
## mientras está abierta se ocultan el tutorial y los efectos del juego.
## El juego sigue corriendo detrás (es un idle): no se pierde nada.

signal entered

const BG_W := 400
const BG_H := 720
const ROAD_Y := 640                     ## línea del asfalto dentro del fondo

var _root: Control
var _sky: ColorRect
var _bg: TextureRect
var _bus: Sprite2D
var _bus_t := 1.5
var _anim := 0.0
var _logo_box: Control
var _menu: VBoxContainer
var _status: Label
var _closing := false


func _init() -> void:
	layer = 9


func _ready() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.theme = Main.instance.theme
	_root.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_root)
	_sky = ColorRect.new()
	_sky.color = Color("2e2b48")
	_sky.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.add_child(_sky)
	_bg = TextureRect.new()
	_bg.texture = U.tex("locations/start_bg.png")
	_bg.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_bg)
	_bus = Sprite2D.new()
	_bus.texture = U.tex("effects/colectivo_anim.png")
	_bus.hframes = 2
	_bus.centered = false
	_bus.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_bus.visible = false
	_bg.add_child(_bus)

	var col := U.vbox(10)
	col.set_anchors_preset(Control.PRESET_FULL_RECT)
	col.offset_left = 18
	col.offset_right = -18
	col.offset_top = 22
	col.offset_bottom = -18
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(col)
	_logo_box = U.vbox(2)
	_logo_box.alignment = BoxContainer.ALIGNMENT_CENTER
	var emblem := U.icon("", "logo/logo_128.png")
	emblem.custom_minimum_size = Vector2(96, 96)
	emblem.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	emblem.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	emblem.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_logo_box.add_child(emblem)
	_logo_box.add_child(_title("TYCOON", 32, Color("ffd458")))
	_logo_box.add_child(_title("ARGENTINA", 24, Color("a9d2f2")))
	col.add_child(_logo_box)
	col.add_child(U.spacer())
	var card := U.panel("Card")
	var inner := U.vbox(6)
	card.add_child(inner)
	_menu = U.vbox(8)
	inner.add_child(_menu)
	# La versión va dentro de la tarjeta: sobre el fondo tapaba los edificios.
	inner.add_child(U.label("v%s" % ProjectSettings.get_setting("application/config/version"), U.SIZE_SMALL, U.TEXT_SOFT, false, HORIZONTAL_ALIGNMENT_RIGHT))
	col.add_child(card)
	_status = U.label("", U.SIZE_SMALL, Color("f0eee6"), false, HORIZONTAL_ALIGNMENT_CENTER)
	_status.add_theme_constant_override("outline_size", 4)
	_status.add_theme_color_override("font_outline_color", Color("1b1a2e"))
	col.add_child(_status)

	_root.resized.connect(_layout)
	Auth.changed.connect(rebuild)
	Auth.busy_changed.connect(func(_b: bool) -> void: _update_status())
	Game.m.profile_changed.connect(rebuild)
	rebuild()
	_layout()
	open(false)


func _title(text: String, size: int, color: Color) -> Label:
	var l := U.label(text, size, color, true, HORIZONTAL_ALIGNMENT_CENTER)
	l.add_theme_constant_override("outline_size", 8)
	l.add_theme_color_override("font_outline_color", Color("1b1a2e"))
	l.add_theme_constant_override("shadow_offset_y", 3)
	l.add_theme_color_override("font_shadow_color", Color("1b1a2e"))
	return l


## Fondo a escala 1 (píxeles enteros), pegado abajo y centrado; arriba se
## completa con el color del cielo.
func _layout() -> void:
	var sz := _root.size
	_bg.size = Vector2(BG_W, BG_H)
	_bg.position = Vector2(floor((sz.x - BG_W) / 2.0), floor(sz.y - BG_H))


func is_open() -> bool:
	return visible and not _closing


func open(animated := true) -> void:
	_closing = false
	visible = true
	rebuild()
	_set_game_layers(false)
	if animated:
		_root.modulate.a = 0.0
		_root.create_tween().tween_property(_root, "modulate:a", 1.0, 0.25)
	else:
		_root.modulate.a = 1.0


func enter_game() -> void:
	if _closing or not visible:
		return
	_closing = true
	Sfx.play("whoosh")
	var tw := _root.create_tween()
	tw.tween_property(_root, "modulate:a", 0.0, 0.25)
	tw.tween_callback(func() -> void:
		visible = false
		_closing = false
		_set_game_layers(true)
		entered.emit())


func _set_game_layers(on: bool) -> void:
	var main := Main.instance
	if main.tutorial:
		main.tutorial.visible = on
	if main.fx:
		main.fx.visible = on


func rebuild() -> void:
	if _menu == null:
		return
	U.clear(_menu)
	var m := Game.m
	var has_progress := float(m.stats.get("play_time", 0.0)) > 20.0 or m.economy.lifetime_earned > 0
	if Auth.signed_in():
		_menu.add_child(_profile_card())
	var play := U.button("CONTINUAR" if has_progress else "JUGAR", "verde", "derecha", 48, U.SIZE_TITLE)
	U.on_press(play, enter_game, "")
	_menu.add_child(play)
	if not Auth.signed_in():
		_menu.add_child(U.para("Jugás como invitado: tu progreso se guarda en este teléfono." if has_progress else "Arrancás con un campo de algodón en Santiago del Estero y vas conquistando la Argentina. El tutorial te guía.", U.SIZE_SMALL, U.TEXT_SOFT))
		var login := U.button("INICIAR SESIÓN", "celeste", "persona", 40, U.SIZE_BODY)
		U.on_press(login, LoginModal.open)
		_menu.add_child(login)
	var cfg := U.button("CONFIGURACIÓN", "crema", "engranaje", 40, U.SIZE_BODY)
	U.on_press(cfg, SettingsModal.open)
	_menu.add_child(cfg)
	_update_status()


func _profile_card() -> Control:
	var b := Button.new()
	b.theme_type_variation = "Btn_crema"
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size.y = 52
	var row := U.hbox(8)
	row.set_anchors_preset(Control.PRESET_FULL_RECT)
	row.offset_left = 6
	row.offset_right = -6
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var av := TextureRect.new()
	ProfileWidgets.apply_avatar(av)
	av.custom_minimum_size = Vector2(32, 32)
	av.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	av.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(av)
	var info := U.vbox(0)
	info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	info.alignment = BoxContainer.ALIGNMENT_CENTER
	info.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var n := U.label(Game.m.profile["company"], U.SIZE_BODY, U.TEXT, true)
	n.clip_text = true
	n.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	info.add_child(n)
	var e := U.label(Auth.email, U.SIZE_SMALL, U.TEXT_SOFT)
	e.clip_text = true
	info.add_child(e)
	row.add_child(info)
	row.add_child(U.label("PERFIL", U.SIZE_SMALL, Color("2f6ea8"), true))
	b.add_child(row)
	U.on_press(b, func() -> void:
		enter_game()
		Main.instance.go_to(4))
	return b


func _update_status() -> void:
	if _status == null:
		return
	if Auth.busy:
		_status.text = "Conectando…"
	elif Auth.signed_in():
		_status.text = "Sesión iniciada"
	else:
		_status.text = ""


func _process(delta: float) -> void:
	if not visible:
		return
	_anim += delta
	_logo_box.position.y = round(sin(_anim * 1.6) * 2.0)
	if Auth.busy:
		_status.text = "Conectando" + ".".repeat(1 + int(_anim * 3.0) % 3)
	if Settings.fx_level() == 0:
		_bus.visible = false
		return
	if not _bus.visible:
		_bus_t -= delta
		if _bus_t <= 0.0:
			_bus.visible = true
			_bus.flip_h = randf() < 0.5
			# El sprite mira a la derecha; con flip_h mira a la izquierda.
			_bus.position = Vector2(-126 if not _bus.flip_h else BG_W + 4, ROAD_Y - 22)
		return
	_bus.position.x = round(_bus.position.x + (-70.0 if _bus.flip_h else 70.0) * delta)
	_bus.frame = int(_anim * 6.0) % 2
	if _bus.position.x < -130 or _bus.position.x > BG_W + 10:
		_bus.visible = false
		_bus_t = randf_range(3.0, 7.0)
