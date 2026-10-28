class_name EmpireScreen
extends Control
## Sección IMPERIO: diorama del negocio + panel con UNA acción principal.
##
## Jerarquía (pensada para quien nunca jugó un tycoon):
##   1. Botón principal grande que cambia según el momento:
##      ABRIR → REPONER MERCADERÍA → ¡VENDER! → VENDE SOLO
##   2. Subir nivel (secundario, celeste) con cuánto suma por segundo.
##   3. Tres fichas: ganancia por venta, ciclo y mercadería (tocable: repone).
##   4. Administrar (todo lo demás, agrupado por categoría).

const BUY_MODES := [1, 10, -1]   ## -1 = máximo

var m: GameModel
var bid := ""
var _scene: BusinessScene
var _events_row: HBoxContainer
var _name: Label
var _level: Label
var _sub: Label
var _stars: HBoxContainer
var _chip_sale: Label
var _chip_cycle: Label
var _chip_stock: Button
var _cycle_bar: ProgressBar
var _main_btn: Button
var _goal_label: Label        ## próxima meta del negocio (Engagement.next_goal)
var _goal_bar: ProgressBar
var _combo_label: Label
var _chest_btn: Button
var _level_btn: Button
var _mode_btn: Button
var _manage_btn: Button
var _prev_btn: Button
var _next_btn: Button
var _buy_mode := 0
var _holding := false
var _timer := 0.0
var _event_timer := 0
var _main_action := ""
var _view_btn: Button


## El botón sólo aparece si el nivel actual tiene local por dentro.
func _update_view_btn() -> void:
	_view_btn.visible = BusinessScene.has_interior(bid, int(m.derive(bid)["tier"]))
	var inside: bool = Settings.get_value("scene_view") == "interior"
	_view_btn.icon = U.icon_tex("edificio" if inside else "mostrador")
	_view_btn.tooltip_text = "Ver la fachada" if inside else "Ver adentro del local"


func _ready() -> void:
	m = Game.m
	bid = Main.instance.selected_business
	var col := U.vbox(6)
	var sc := U.scroll(col)
	sc.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(sc)

	# --- Diorama con flechas y eventos ---
	var scene_wrap := Control.new()
	scene_wrap.custom_minimum_size.y = BusinessScene.H
	scene_wrap.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_scene = BusinessScene.new()
	_scene.set_anchors_preset(Control.PRESET_FULL_RECT)
	scene_wrap.add_child(_scene)
	_prev_btn = U.icon_button("izquierda", "crema", 30)
	_prev_btn.position = Vector2(6, 96)
	U.on_press(_prev_btn, func() -> void: _cycle_business(-1))
	scene_wrap.add_child(_prev_btn)
	_next_btn = U.icon_button("derecha", "crema", 30)
	_next_btn.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	_next_btn.position = Vector2(-36, 96)
	U.on_press(_next_btn, func() -> void: _cycle_business(1))
	scene_wrap.add_child(_next_btn)
	_events_row = U.hbox(4)
	_events_row.position = Vector2(6, 6)
	scene_wrap.add_child(_events_row)
	# Cofres ganados (se abren con premio variable) y combo de ventas a mano.
	_chest_btn = U.button("", "amarillo", "regalo", 30, U.SIZE_SMALL)
	_chest_btn.position = Vector2(6, 46)
	_chest_btn.visible = false
	U.on_press(_chest_btn, func() -> void: ChestModal.open(), "coin")
	scene_wrap.add_child(_chest_btn)
	_combo_label = U.label("", U.SIZE_TITLE, Color("ffd458"), true, HORIZONTAL_ALIGNMENT_CENTER)
	_combo_label.add_theme_color_override("font_outline_color", Color("3d1b0b"))
	_combo_label.add_theme_constant_override("outline_size", 6)
	_combo_label.set_anchors_preset(Control.PRESET_CENTER_TOP)
	_combo_label.position = Vector2(-60, 44)
	_combo_label.size = Vector2(120, 28)
	_combo_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	scene_wrap.add_child(_combo_label)
	# Cambiar entre ver el local por dentro y la fachada en la calle. Botones
	# de ícono chicos para tapar lo menos posible del escenario.
	_view_btn = U.icon_button("edificio", "crema", 34)
	_view_btn.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	_view_btn.position = Vector2(-40, 6)
	U.on_press(_view_btn, func() -> void:
		Settings.set_value("scene_view", "fachada" if Settings.get_value("scene_view") == "interior" else "interior")
		_update_view_btn())
	scene_wrap.add_child(_view_btn)
	_update_view_btn()
	# Bonos voluntarios por anuncio (siempre visible; el modal explica el estado).
	var ads_btn := U.icon_button("regalo", "amarillo", 34)
	ads_btn.tooltip_text = "Bonos por anuncio"
	ads_btn.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	ads_btn.position = Vector2(-40, 44)
	U.on_press(ads_btn, func() -> void: AdsModal.open(bid))
	scene_wrap.add_child(ads_btn)
	col.add_child(scene_wrap)

	# --- Panel ---
	var card := U.panel("Card")
	var body := U.vbox(8)
	card.add_child(body)
	col.add_child(U.margin(card, 8, 0, 8, 8))

	var head := U.hbox(6)
	var names := U.vbox(0)
	names.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_name = U.label("", U.SIZE_TITLE, U.TEXT, true)
	_name.clip_text = true
	names.add_child(_name)
	_sub = U.label("", U.SIZE_SMALL, U.TEXT_SOFT)
	_sub.clip_text = true
	names.add_child(_sub)
	head.add_child(names)
	_stars = U.hbox(0)
	_stars.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(_stars)
	var lvl_panel := U.panel("GoldCard")
	lvl_panel.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_level = U.label("", U.SIZE_BODY, U.TEXT, true)
	lvl_panel.add_child(_level)
	head.add_child(lvl_panel)
	body.add_child(head)

	var chips := U.hbox(6)
	# Anchos según lo que muestran: "$1,2 mil" y "$15,6 mil" son largos; "2,4 s", corto.
	_chip_sale = _chip(chips, "moneda", "por venta", 1.1)
	_chip_cycle = _chip(chips, "reloj", "cada venta", 0.8)
	_chip_stock = U.button("", "crema", "", 52, U.SIZE_BODY)
	_chip_stock.icon = U.icon32_tex("caja")
	_chip_stock.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_chip_stock.size_flags_stretch_ratio = 1.25
	_chip_stock.clip_text = true
	_chip_stock.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	U.on_press(_chip_stock, _on_restock, "")
	chips.add_child(_chip_stock)
	body.add_child(chips)
	Main.instance.register_target("restock", _chip_stock)

	# Próxima meta: siempre hay algo cerca.
	var goal_row := U.hbox(6)
	goal_row.add_child(U.icon("flecha_arriba"))
	var goal_col := U.vbox(1)
	goal_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_goal_label = U.label("", U.SIZE_SMALL, U.TEXT, true)
	_goal_label.clip_text = true
	_goal_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	goal_col.add_child(_goal_label)
	_goal_bar = U.progress("amarillo", 4)
	goal_col.add_child(_goal_bar)
	goal_row.add_child(goal_col)
	body.add_child(goal_row)

	_cycle_bar = U.progress("verde", 8)
	body.add_child(_cycle_bar)

	_main_btn = U.button("", "verde", "moneda", 48, U.SIZE_TITLE)
	_main_btn.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS
	_main_btn.button_down.connect(_on_main_down)
	_main_btn.button_up.connect(func() -> void: _holding = false)
	body.add_child(_main_btn)
	Main.instance.register_target("main", _main_btn)
	Main.instance.register_target("sell", _main_btn)

	var lvl_row := U.hbox(6)
	_level_btn = U.button("", "celeste", "", 44, U.SIZE_BODY)
	_level_btn.icon = U.icon32_tex("flecha_arriba")
	_level_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_level_btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
	U.on_press(_level_btn, _on_level, "")
	lvl_row.add_child(_level_btn)
	_mode_btn = U.button("x1", "crema", "", 44, U.SIZE_BODY)
	_mode_btn.custom_minimum_size.x = 56
	U.on_press(_mode_btn, func() -> void:
		_buy_mode = (_buy_mode + 1) % BUY_MODES.size()
		_update())
	lvl_row.add_child(_mode_btn)
	body.add_child(lvl_row)
	Main.instance.register_target("level", _level_btn)

	_manage_btn = U.button("ADMINISTRAR NEGOCIO", "crema", "engranaje", 40, U.SIZE_BODY)
	U.on_press(_manage_btn, func() -> void: ManageBusinessModal.open(bid))
	body.add_child(_manage_btn)
	Main.instance.register_target("manage", _manage_btn)

	Main.instance.business_selected.connect(func(id: String) -> void: _select(id))
	m.business_changed.connect(func(id: String) -> void:
		if id == bid:
			_update())
	m.businesses_changed.connect(_update)
	m.events_changed.connect(_update_events)
	m.money_changed.connect(func(_a: int, _b: int) -> void: _timer = 1.0)
	_select(bid)


func _chip(parent: HBoxContainer, icon_name: String, caption: String, ratio := 1.0) -> Label:
	var p := U.panel("Inset")
	p.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	p.size_flags_stretch_ratio = ratio
	p.custom_minimum_size.y = 52
	var v := U.vbox(0)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	var t := U.hbox(4)
	t.add_child(U.icon32(icon_name))
	var val := U.label("", U.SIZE_BODY, U.TEXT, true)
	val.clip_text = true
	val.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	t.add_child(val)
	v.add_child(t)
	v.add_child(U.label(caption, U.SIZE_SMALL, U.TEXT_SOFT))
	p.add_child(v)
	parent.add_child(p)
	return val


func on_shown() -> void:
	_update()
	_update_events()


## Llegada desde el mapa: la escena se acerca suave (parte del zoom mapa → fachada).
func play_arrive() -> void:
	if Settings.get_value("reduce_motion") or _scene == null:
		return
	_scene.pivot_offset = _scene.size / 2.0
	_scene.scale = Vector2(1.18, 1.18)
	_scene.modulate.a = 0.4
	var tw := _scene.create_tween().set_parallel(true)
	tw.tween_property(_scene, "scale", Vector2.ONE, 0.3).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_OUT)
	tw.tween_property(_scene, "modulate:a", 1.0, 0.25)


func rebuild() -> void:
	_select(m.first_business())


func _select(id: String) -> void:
	bid = id
	_scene.set_business(id)
	_scene.refresh()
	_update()
	_update_events()


func _cycle_business(step: int) -> void:
	var owned := m.owned_ids()
	var i := owned.find(bid)
	var next: String = owned[(i + step + owned.size()) % owned.size()]
	Main.instance.select_business(next, false)


func _on_main_down() -> void:
	match _main_action:
		"open":
			Main.instance.result(m.open_business(bid))
		"restock":
			_on_restock()
		"sell":
			_holding = true
			_sell()
	_update()


func _sell() -> void:
	var s: Dictionary = m.biz[bid]
	if m.derive(bid)["auto_sell"] or s["running"]:
		return
	var r := m.tap_sell(bid)
	if r["ok"]:
		Sfx.play("tap")
		Sfx.vibrate(12)
	else:
		_holding = false
		Main.instance.result(r)


func _on_restock() -> void:
	var r := m.restock(bid)
	if r["ok"]:
		Sfx.play("whoosh")
	else:
		Main.instance.result(r)
	_update()


func _levels_to_buy() -> int:
	var mode: int = BUY_MODES[_buy_mode]
	var room := int(m.data.business_by_id[bid]["max_level"]) - int(m.biz[bid]["level"])
	if mode == -1:
		return maxi(1, mini(m.max_affordable_levels(bid), room))
	return mini(mode, room)


func _on_level() -> void:
	if Main.instance.result(m.buy_levels(bid, _levels_to_buy())):
		_update()


func _process(delta: float) -> void:
	if not is_visible_in_tree():
		return
	var s: Dictionary = m.biz[bid]
	var d := m.derive(bid)
	_cycle_bar.value = float(s["progress"]) / float(d["cycle"]) if s["running"] else 0.0
	if _holding and not s["running"] and not d["auto_sell"]:
		if m.has_stock(bid):
			m.tap_sell(bid)
		else:
			_holding = false
	_timer += delta
	if _timer >= 0.25:
		_timer = 0.0
		_update()
		_event_timer += 1
		if _event_timer >= 4:
			_event_timer = 0
			_update_events()


func _update() -> void:
	if not is_inside_tree():
		return
	var def: Dictionary = m.data.business_by_id[bid]
	var s: Dictionary = m.biz[bid]
	var d := m.derive(bid)
	_name.text = def["name"]
	_update_view_btn()
	_level.text = "Nv %d" % int(s["level"])
	var goal := Engagement.next_goal(m, bid)
	_goal_label.text = goal["text"]
	_goal_bar.value = float(goal["value"])
	var cmb := Engagement.combo(m)
	_combo_label.visible = cmb >= 1.05 and not d["auto_sell"]
	_combo_label.text = "COMBO x%s" % str(snappedf(cmb, 0.1))
	_combo_label.scale = Vector2.ONE * (1.0 + (cmb - 1.0) * 0.3)
	_combo_label.pivot_offset = _combo_label.size / 2.0
	var chests := int(m.engage.get("chests", 0))
	_chest_btn.visible = chests > 0
	_chest_btn.text = "x%d" % chests
	_sub.text = ["Atendés vos", "Vende solo", "Vende y repone solo", "Gestión total"][int(d["automation"])] + " · " + m.data.zone_by_id[s["zone"]]["name"]
	if _stars.get_child_count() == 0:
		for i in 5:
			var st := U.icon("", "particles/star.png")
			st.custom_minimum_size = Vector2(6, 12)
			_stars.add_child(st)
	for i in 5:
		(_stars.get_child(i) as Control).modulate = Color.WHITE if i <= int(d["tier"]) else Color(0.2, 0.2, 0.3, 0.5)

	# Fichas
	_chip_sale.text = Fmt.money(d["revenue_cycle"])
	_chip_cycle.text = Fmt.cycle(d["cycle"])
	var ratio := m.stock_ratio(bid)
	var eta := m.pending_order_eta(bid)
	var q := m.restock_quote(bid)
	var pct := "%d %%" % int(round(ratio * 100))
	if eta > 0.0:
		_chip_stock.text = "%s\nllega en %s" % [pct, Fmt.cycle(eta)]
		_chip_stock.theme_type_variation = "Btn_crema"
	elif q["items"].is_empty():
		_chip_stock.text = "%s\nlleno" % pct
		_chip_stock.theme_type_variation = "Btn_crema"
	else:
		# El color y el ícono de la caja ya dicen "reponer"; acá va el costo entero.
		_chip_stock.text = "%s\n%s" % [pct, Fmt.cost(q["total"])]
		# amarillo = aviso (stock bajo), rojo = sin stock
		_chip_stock.theme_type_variation = "Btn_rojo" if ratio <= 0.001 else ("Btn_amarillo" if ratio < 0.3 else "Btn_crema")

	# Botón principal contextual
	var has := m.has_stock(bid)
	if s.get("closed", false):
		_set_main("open", "ABRIR EL PUESTO", "celeste", "tienda", false)
	elif not has and eta <= 0.0 and not d["auto_restock"]:
		_set_main("restock", "REPONER MERCADERÍA · " + Fmt.cost(q["total"]), "amarillo", "camion", q["items"].is_empty())
	elif not has:
		_set_main("", "MERCADERÍA EN CAMINO · %s" % Fmt.cycle(eta), "gris", "camion", true)
	elif d["auto_sell"]:
		_set_main("", "VENDE SOLO", "verde", "rayo", true)
	else:
		_set_main("sell", "Atendiendo…" if s["running"] else "¡VENDER!", "verde", "moneda", s["running"])

	# Subir nivel
	var maxed := int(s["level"]) >= int(def["max_level"])
	_mode_btn.text = ["x1", "x10", "MÁX"][_buy_mode]
	if maxed:
		_level_btn.text = "Nivel máximo"
		_level_btn.disabled = true
	else:
		var n := _levels_to_buy()
		var cost := m.level_cost(bid, n)
		var gain := m.preview_profit_gain(bid, func(st: Dictionary) -> void: st["level"] = int(st["level"]) + n)
		_level_btn.text = "SUBIR NIVEL +%d · %s\n+%s" % [n, Fmt.cost(cost), Fmt.per_sec(gain)]
		_level_btn.disabled = not m.economy.can_afford(cost) or s.get("closed", false)
	var multi := m.owned_ids().size() > 1
	_prev_btn.visible = multi
	_next_btn.visible = multi


func _set_main(action: String, text: String, style: String, icon_name: String, disabled: bool) -> void:
	_main_action = action
	_main_btn.text = text
	_main_btn.theme_type_variation = "Btn_" + style
	_main_btn.icon = U.icon32_tex(icon_name)
	# "Vende solo" se muestra como estado (verde), no como botón apagado gris.
	_main_btn.disabled = disabled and style != "verde"
	_main_btn.mouse_filter = Control.MOUSE_FILTER_IGNORE if disabled else Control.MOUSE_FILTER_STOP


func _update_events() -> void:
	if not is_inside_tree():
		return
	U.clear(_events_row)
	var active: Array = m.events["active"]
	for i in active.size():
		var inst: Dictionary = active[i]
		var e: Dictionary = m.data.event_by_id[inst["id"]]
		var b := U.button("%s · %s" % [e["name"], Fmt.duration(inst["remaining"])], "rojo" if e["kind"] == "bad" else "amarillo", e["icon"], 32, U.SIZE_SMALL)
		var idx := i
		U.on_press(b, func() -> void: EventModal.open(idx))
		_events_row.add_child(b)
