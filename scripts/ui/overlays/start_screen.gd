class_name StartScreen
extends CanvasLayer
## Pantalla de inicio (punto de entrada).
##
## Fondo: la postal viva del Noroeste (StartPostcard). Logo y menú según el estado
## REAL de la cuenta (Auth):
##   sin sesión: JUGAR / CONTINUAR (como invitado), INICIAR SESIÓN, CONFIGURACIÓN
##   con sesión: tarjeta de perfil, CONTINUAR, CONFIGURACIÓN
## Va en la capa 9: los modales (10), avisos (40) y diálogos se ven encima;
## mientras está abierta se ocultan el tutorial y los efectos del juego.
## El juego sigue corriendo detrás (es un idle): no se pierde nada.

signal entered

var _root: Control
var _postcard: StartPostcard
var _anim := 0.0
var _logo_box: Control
var _logo: TextureRect
var _card: Control
var _spark: Sprite2D
var _spark_t := 3.0
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
	_postcard = StartPostcard.new()
	_root.add_child(_postcard)

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
	# Logo "Coronados de Gloria" (351x146): en 360 px de ancho entra apenas
	# achicado, por eso se filtra lineal en vez de píxel exacto.
	var logo := U.icon("", "logo/logo_coronados.png")
	logo.custom_minimum_size = Vector2(0, 136)
	logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	logo.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	logo.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_logo_box.add_child(logo)
	_logo = logo
	col.add_child(_logo_box)
	var gap := U.spacer()                      # el menú va abajo: la postal queda en el medio
	gap.size_flags_vertical = Control.SIZE_EXPAND_FILL
	col.add_child(gap)
	_spark = Sprite2D.new()                    # destello que recorre el logo cada tanto
	_spark.texture = U.tex("particles/sparkle.png")
	_spark.hframes = 4
	_spark.scale = Vector2.ONE * 2.0
	_spark.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_spark.visible = false
	logo.add_child(_spark)
	var card := U.panel("Card")
	var inner := U.vbox(6)
	card.add_child(inner)
	_menu = U.vbox(8)
	inner.add_child(_menu)
	# La versión va dentro de la tarjeta: sobre el fondo tapaba los edificios.
	inner.add_child(U.label("v%s" % ProjectSettings.get_setting("application/config/version"), U.SIZE_SMALL, U.TEXT_SOFT, false, HORIZONTAL_ALIGNMENT_RIGHT))
	col.add_child(card)
	_card = card
	_status = U.label("", U.SIZE_SMALL, Color("fff6e6"), false, HORIZONTAL_ALIGNMENT_CENTER)
	_status.add_theme_constant_override("outline_size", 4)
	_status.add_theme_color_override("font_outline_color", Color("3d1b0b"))
	col.add_child(_status)

	_root.resized.connect(_layout)
	card.resized.connect(_layout)
	Auth.changed.connect(rebuild)
	Auth.busy_changed.connect(func(_b: bool) -> void: _update_status())
	Game.m.profile_changed.connect(rebuild)
	rebuild()
	_layout()
	open(false)
	_play_intro()


## La ruta de la postal queda justo arriba del menú: en cualquier alto de pantalla
## lo que se mueve se ve, y lo que sobra de cielo o de cerro va detrás del logo.
func _layout() -> void:
	_postcard.set_road_screen_y(_root.size.y - 18.0 - _status.size.y - 10.0 - _card.size.y - 2.0)


## Entrada: amanece la postal, el logo cae con rebote y el menú sube.
func _play_intro() -> void:
	_postcard.intro()
	if Settings.fx_level() == 0 or Settings.get_value("reduce_motion"):
		return
	_logo.pivot_offset = Vector2(180, 68)
	_logo.scale = Vector2(0.6, 0.6)
	_logo.modulate.a = 0.0
	var tw := _logo.create_tween().set_parallel(true)
	tw.tween_property(_logo, "modulate:a", 1.0, 0.3).set_delay(0.55)
	tw.tween_property(_logo, "scale", Vector2.ONE, 0.6).set_delay(0.55).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	_card.modulate.a = 0.0
	var tc := _card.create_tween()
	tc.tween_interval(0.95)
	tc.tween_property(_card, "modulate:a", 1.0, 0.35)


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
	# 15.0: los dos botones en una fila, para dejarle más pantalla a la postal.
	var row := U.hbox(8)
	if not Auth.signed_in():
		var login := U.button("INICIAR SESIÓN", "celeste", "", 40, U.SIZE_SMALL)
		login.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		U.on_press(login, LoginModal.open)
		row.add_child(login)
	var cfg := U.button("CONFIGURACIÓN", "crema", "", 40, U.SIZE_SMALL)
	cfg.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	U.on_press(cfg, SettingsModal.open)
	row.add_child(cfg)
	_menu.add_child(row)
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
	if Settings.fx_level() == 0 or Settings.get_value("reduce_motion"):
		_spark.visible = false
		return
	_spark_t -= delta
	if _spark_t <= 0.0:
		_spark_t = randf_range(2.4, 5.0)
		_spark.position = Vector2(randf_range(60.0, _logo.size.x - 60.0), randf_range(30.0, _logo.size.y - 30.0))
		_spark.visible = true
		_spark.frame = 0
		var tw := _spark.create_tween()
		tw.tween_property(_spark, "frame", 3, 0.45)
		tw.tween_callback(func() -> void: _spark.visible = false)
