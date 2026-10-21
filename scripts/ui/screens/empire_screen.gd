class_name EmpireScreen
extends Control
## Sección IMPERIO: diorama del negocio seleccionado + panel de gestión.

const BUY_MODES := [1, 10, -1]   ## -1 = máximo

var m: GameModel
var bid := "puesto"
var _scene: BusinessScene
var _events_row: HBoxContainer
var _name: Label
var _level: Label
var _zone: Label
var _stars: HBoxContainer
var _rev_cycle: Label
var _cycle_time: Label
var _per_sec: Label
var _auto: Label
var _cycle_bar: ProgressBar
var _cycle_label: Label
var _stock_bar: ProgressBar
var _stock_label: Label
var _restock_btn: Button
var _sell_btn: Button
var _level_btn: Button
var _mode_btn: Button
var _milestone: Label
var _manage_btn: Button
var _prev_btn: Button
var _next_btn: Button
var _buy_mode := 0
var _holding := false
var _timer := 0.0
var _event_timer := 0


func _ready() -> void:
	m = Game.m
	bid = Main.instance.selected_business
	var col := U.vbox(4)
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
	_prev_btn = U.icon_button("izquierda", "crema", 26)
	_prev_btn.position = Vector2(4, 80)
	U.on_press(_prev_btn, func() -> void: _cycle_business(-1))
	scene_wrap.add_child(_prev_btn)
	_next_btn = U.icon_button("derecha", "crema", 26)
	_next_btn.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	_next_btn.position = Vector2(-30, 80)
	U.on_press(_next_btn, func() -> void: _cycle_business(1))
	scene_wrap.add_child(_next_btn)
	_events_row = U.hbox(3)
	_events_row.position = Vector2(4, 4)
	scene_wrap.add_child(_events_row)
	col.add_child(scene_wrap)

	# --- Panel del negocio ---
	var card := U.panel("Card")
	var body := U.vbox(5)
	card.add_child(body)
	col.add_child(U.margin(card, 6, 0, 6, 6))

	var head := U.hbox(4)
	_name = U.label("", U.SIZE_TITLE, U.TEXT, true)
	_name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_name.clip_text = true
	head.add_child(_name)
	_stars = U.hbox(0)
	head.add_child(_stars)
	var lvl_panel := U.panel("GoldCard")
	_level = U.label("", U.SIZE_SMALL, U.TEXT, true)
	lvl_panel.add_child(_level)
	head.add_child(lvl_panel)
	body.add_child(head)
	_zone = U.label("", 9, U.TEXT_SOFT)
	body.add_child(_zone)

	var stats := U.hbox(3)
	_rev_cycle = _stat_box(stats, "Por ciclo", "moneda")
	_cycle_time = _stat_box(stats, "Ciclo", "reloj")
	_per_sec = _stat_box(stats, "Ganancia/s", "grafico")
	body.add_child(stats)

	var cyc := U.hbox(4)
	_cycle_bar = U.progress("verde", 10)
	cyc.add_child(_cycle_bar)
	_cycle_label = U.label("", U.SIZE_SMALL, U.TEXT_SOFT)
	_cycle_label.custom_minimum_size.x = 92
	_cycle_label.clip_text = true
	cyc.add_child(_cycle_label)
	body.add_child(cyc)

	var stock := U.hbox(4)
	stock.add_child(U.icon("caja"))
	var stock_col := U.vbox(1)
	stock_col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_stock_label = U.label("", U.SIZE_SMALL, U.TEXT_SOFT)
	_stock_label.clip_text = true
	stock_col.add_child(_stock_label)
	_stock_bar = U.progress("amarillo", 8)
	stock_col.add_child(_stock_bar)
	stock.add_child(stock_col)
	_restock_btn = U.button("Reponer", "celeste", "camion", 28, U.SIZE_SMALL)
	_restock_btn.custom_minimum_size.x = 112
	U.on_press(_restock_btn, _on_restock, "")
	stock.add_child(_restock_btn)
	body.add_child(stock)
	Main.instance.register_target("restock", _restock_btn)

	_auto = U.label("", U.SIZE_SMALL, U.GREEN, true)
	_auto.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	body.add_child(_auto)

	_sell_btn = U.button("¡VENDER!", "verde", "moneda", 40, U.SIZE_TITLE)
	_sell_btn.action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS
	_sell_btn.button_down.connect(func() -> void:
		_holding = true
		_sell())
	_sell_btn.button_up.connect(func() -> void: _holding = false)
	body.add_child(_sell_btn)
	Main.instance.register_target("sell", _sell_btn)

	var lvl_row := U.hbox(4)
	_level_btn = U.button("", "amarillo", "flecha_arriba", 40, U.SIZE_BODY)
	_level_btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_level_btn.alignment = HORIZONTAL_ALIGNMENT_LEFT
	U.on_press(_level_btn, _on_level, "")
	lvl_row.add_child(_level_btn)
	_mode_btn = U.button("x1", "crema", "", 40, U.SIZE_BODY)
	_mode_btn.custom_minimum_size.x = 50
	U.on_press(_mode_btn, func() -> void:
		_buy_mode = (_buy_mode + 1) % BUY_MODES.size()
		_update())
	lvl_row.add_child(_mode_btn)
	body.add_child(lvl_row)
	Main.instance.register_target("level", _level_btn)

	var foot := U.hbox(4)
	_milestone = U.para("", 9, U.TEXT_SOFT)
	foot.add_child(_milestone)
	_manage_btn = U.button("Administrar", "celeste", "persona", 30, U.SIZE_SMALL)
	U.on_press(_manage_btn, func() -> void: ManageBusinessModal.open(bid))
	foot.add_child(_manage_btn)
	body.add_child(foot)
	Main.instance.register_target("manage", _manage_btn)

	Main.instance.business_selected.connect(func(id: String) -> void: _select(id))
	m.business_changed.connect(func(id: String) -> void:
		if id == bid:
			_update())
	m.businesses_changed.connect(_update)
	m.events_changed.connect(_update_events)
	m.money_changed.connect(func(_a: int, _b: int) -> void: _timer = 1.0)
	_select(bid)


func _stat_box(parent: HBoxContainer, title: String, icon_name: String) -> Label:
	var p := U.panel("Inset")
	p.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var v := U.vbox(0)
	var t := U.hbox(2)
	t.add_child(U.icon(icon_name))
	t.add_child(U.label(title, 9, U.TEXT_SOFT))
	v.add_child(t)
	var val := U.label("", U.SIZE_BODY, U.TEXT, true)
	val.clip_text = true
	v.add_child(val)
	p.add_child(v)
	parent.add_child(p)
	return val


func on_shown() -> void:
	_update()
	_update_events()


func rebuild() -> void:
	_select("puesto")


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
	_update()


func _on_restock() -> void:
	if Main.instance.result(m.restock(bid)):
		_update()


func _levels_to_buy() -> int:
	var mode: int = BUY_MODES[_buy_mode]
	var room := int(m.data.business_by_id[bid]["max_level"]) - int(m.biz[bid]["level"])
	if mode == -1:
		return maxi(1, mini(m.max_affordable_levels(bid), room))
	return mini(mode, room)


func _on_level() -> void:
	var n := _levels_to_buy()
	if Main.instance.result(m.buy_levels(bid, n)):
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
	_level.text = "Nv %d" % int(s["level"])
	_zone.text = "%s · %s" % [m.data.zone_by_id[s["zone"]]["name"], _automation_name(d)]
	if _stars.get_child_count() == 0:
		for i in 5:
			var st := U.icon("", "particles/star.png")
			st.custom_minimum_size = Vector2(6, 12)
			_stars.add_child(st)
	for i in 5:
		(_stars.get_child(i) as Control).modulate = Color.WHITE if i <= int(d["tier"]) else Color(0.2, 0.2, 0.3, 0.5)
	_rev_cycle.text = Fmt.money(d["revenue_cycle"])
	_cycle_time.text = Fmt.cycle(d["cycle"])
	_per_sec.text = Fmt.per_sec(d["profit_sec"])

	# Ciclo
	var has := m.has_stock(bid)
	if s["running"]:
		_cycle_label.text = "Atendiendo…"
	elif not has:
		_cycle_label.text = "¡Sin mercadería!"
	elif d["auto_sell"]:
		_cycle_label.text = "Vende solo"
	else:
		_cycle_label.text = "Esperando clientes"

	# Mercadería
	var ratio := m.stock_ratio(bid)
	_stock_bar.value = ratio
	_stock_bar.theme_type_variation = "Bar_rojo" if ratio < 0.2 else "Bar_amarillo"
	var eta := m.pending_order_eta(bid)
	var stock_txt := "Mercadería %d %%" % int(round(ratio * 100))
	if eta > 0.0:
		stock_txt += " · pedido llega en %s" % Fmt.cycle(eta)
	if d["event_cost"] < 1.0:
		stock_txt += " · ¡DESCUENTO!"
	_stock_label.text = stock_txt
	var q := m.restock_quote(bid)
	if q["items"].is_empty():
		_restock_btn.text = "Lleno" if eta <= 0.0 else "En camino"
		_restock_btn.disabled = true
	else:
		_restock_btn.text = "Reponer " + Fmt.cost(q["total"])
		_restock_btn.disabled = m.economy.money <= 0 and m.has_stock(bid)

	# Automatización / vender
	if d["auto_sell"]:
		_sell_btn.visible = false
		_auto.text = "Automático: %s" % ("vende y repone solo" if d["auto_restock"] else "vende solo. Contratá un repositor para no quedarte sin stock.")
		_auto.add_theme_color_override("font_color", U.GREEN)
	else:
		_sell_btn.visible = true
		_sell_btn.disabled = s["running"] or not has
		_sell_btn.text = "Atendiendo…" if s["running"] else ("¡VENDER!" if has else "Sin mercadería")
		_auto.text = "Manual: tocá o mantené ¡VENDER!. Un vendedor lo hace solo."
		_auto.add_theme_color_override("font_color", U.TEXT_SOFT)

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
		_level_btn.text = "Subir +%d · %s\n+%s" % [n, Fmt.cost(cost), Fmt.per_sec(gain)]
		_level_btn.disabled = not m.economy.can_afford(cost)
	var nm: int = d["next_milestone"]
	if nm > 0:
		var ms_text := ""
		for ms in m.data.balance["milestones"]:
			if int(ms["level"]) == nm:
				var parts := []
				if float(ms["speed"]) > 1.0:
					parts.append("velocidad x%s" % str(ms["speed"]).trim_suffix(".0"))
				if int(ms["slots"]) > 0:
					parts.append("+1 puesto de empleado")
				if m.data.balance["visual_tiers"].has(nm):
					parts.append("local nuevo")
				ms_text = ", ".join(parts)
		_milestone.text = "Nivel %d: %s" % [nm, ms_text]
	else:
		_milestone.text = "¡Todos los hitos alcanzados!"
	var multi := m.owned_ids().size() > 1
	_prev_btn.visible = multi
	_next_btn.visible = multi


func _automation_name(d: Dictionary) -> String:
	return ["Manual", "Ventas automáticas", "Automatizado", "Gestión total"][int(d["automation"])]


func _update_events() -> void:
	if not is_inside_tree():
		return
	U.clear(_events_row)
	var active: Array = m.events["active"]
	for i in active.size():
		var inst: Dictionary = active[i]
		var e: Dictionary = m.data.event_by_id[inst["id"]]
		var b := U.button("%s %s" % [e["name"], Fmt.duration(inst["remaining"])], "rojo" if e["kind"] == "bad" else "amarillo", e["icon"], 22, 9)
		var idx := i
		U.on_press(b, func() -> void: EventModal.open(idx))
		_events_row.add_child(b)
