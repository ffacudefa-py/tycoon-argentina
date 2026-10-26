class_name ObjectivesScreen
extends Control
## Sección OBJETIVOS: recompensa diaria, misiones principales, desafíos y
## misiones diarias. El progreso se registra solo; reclamar entrega el premio
## una única vez.

var m: GameModel
var tab := 0
var _daily_box: VBoxContainer
var _list: VBoxContainer
var _bars: Array = []        ## [ProgressBar, Label, Callable progreso]
var _timer := 0.0
## Mientras sale la tarjeta de una misión reclamada, la lista no se rearma.
var _hold := false
var _pending := false


func _ready() -> void:
	m = Game.m
	var col := U.vbox(6)
	var sc := U.scroll(U.margin(col, 6, 6, 6, 8))
	sc.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(sc)
	_daily_box = U.vbox(4)
	col.add_child(_daily_box)
	col.add_child(U.tabs(["Principales", "Desafíos", "Diarias"], func(i: int) -> void:
		tab = i
		_build_list(), 0))
	_list = U.vbox(5)
	col.add_child(_list)
	m.progress_changed.connect(rebuild)
	rebuild()


func on_shown() -> void:
	rebuild()


func rebuild() -> void:
	if not is_inside_tree():
		return
	if _hold:
		_pending = true
		return
	_build_daily()
	_build_list()


func _build_daily() -> void:
	U.clear(_daily_box)
	var card := U.panel("GoldCard")
	var col := U.vbox(4)
	card.add_child(col)
	var head := U.hbox(4)
	head.add_child(U.icon("calendario"))
	head.add_child(U.label("Recompensa diaria", U.SIZE_TITLE, U.TEXT, true))
	col.add_child(head)
	var strip := U.hbox(2)
	var idx := int(m.daily_reward["index"])
	var can := ProgressionSystem.can_claim_daily_reward(m)
	for i in m.data.daily_rewards.size():
		var dr: Dictionary = m.data.daily_rewards[i]
		var cell := U.panel("Inset" if i != idx else "WhiteCard")
		cell.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		var v := U.vbox(0)
		v.add_child(U.label("Día %d" % int(dr["day"]), U.SIZE_SMALL, U.TEXT, i == idx, HORIZONTAL_ALIGNMENT_CENTER))
		var r: Dictionary = dr["reward"]
		var ic := "regalo"
		if r.has("boost"):
			ic = "rayo"
		elif r.has("icon"):
			ic = "estrella"
		elif r.has("income_seconds"):
			ic = "billete"
		var icn := U.icon(ic)
		icn.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		if i < idx:
			icn.modulate = Color(1, 1, 1, 0.35)
		v.add_child(icn)
		cell.add_child(v)
		strip.add_child(cell)
	col.add_child(strip)
	var cur := ProgressionSystem.current_daily_reward(m)
	col.add_child(U.para("Hoy: %s — %s" % [cur["label"], ProgressionSystem.describe(m, cur["reward"])], U.SIZE_SMALL, U.TEXT))
	var b := U.button("¡Reclamar!" if can["ok"] else "Volvé mañana", "verde" if can["ok"] else "gris", "regalo", 30)
	b.disabled = not can["ok"]
	U.on_press(b, func() -> void:
		Main.instance.result(ProgressionSystem.claim_daily_reward(m))
		rebuild(), "")
	col.add_child(b)
	if not can["ok"] and ProgressionSystem.clock_suspicious(m):
		col.add_child(U.para(can["msg"], U.SIZE_SMALL, U.RED))
	col.add_child(U.para("Si faltás algunos días no perdés la racha: seguís desde donde quedaste.", U.SIZE_SMALL, U.TEXT_SOFT))
	_daily_box.add_child(card)


func _build_list() -> void:
	U.clear(_list)
	_bars.clear()
	match tab:
		0:
			var idx := int(m.missions["main_index"])
			# Primero lo que se puede reclamar
			for i in idx:
				var mis: Dictionary = m.data.missions_main[i]
				if not m.missions["claimed"].has(mis["id"]):
					_list.add_child(_mission_card(mis, "main"))
			if idx < m.data.missions_main.size():
				_list.add_child(_mission_card(m.data.missions_main[idx], "main"))
				for j in range(idx + 1, mini(idx + 3, m.data.missions_main.size())):
					_list.add_child(_upcoming_card(m.data.missions_main[j]))
			else:
				_list.add_child(U.para("¡Completaste todas las misiones principales!", U.SIZE_BODY, U.TEXT_LIGHT))
			var done := 0
			for mis in m.data.missions_main:
				if m.missions["claimed"].has(mis["id"]):
					done += 1
			_list.add_child(U.label("Reclamadas: %d/%d" % [done, m.data.missions_main.size()], U.SIZE_SMALL, Color("c2c0d6")))
		1:
			var items := m.data.challenges.duplicate()
			items.sort_custom(func(a, b): return _order(a) < _order(b))
			for c in items:
				_list.add_child(_mission_card(c, "challenge"))
		2:
			ProgressionSystem.ensure_daily(m)
			_list.add_child(U.para("Se renuevan cada día. Premio: %s cada una." % ProgressionSystem.describe(m, m.data.daily_cfg["reward"]), U.SIZE_SMALL, Color("c2c0d6")))
			for dm in m.daily_missions["list"]:
				_list.add_child(_mission_card(dm, "daily"))
	_refresh()


func _order(c: Dictionary) -> int:
	var done: bool = m.missions["completed"].has(c["id"])
	var claimed: bool = m.missions["claimed"].has(c["id"])
	return 0 if (done and not claimed) else (2 if claimed else 1)


func _mission_card(mis: Dictionary, kind: String) -> Control:
	var completed: bool
	var claimed: bool
	if kind == "daily":
		completed = m.daily_missions["completed"].has(mis["id"])
		claimed = m.daily_missions["claimed"].has(mis["id"])
	else:
		completed = m.missions["completed"].has(mis["id"])
		claimed = m.missions["claimed"].has(mis["id"])
	var card := U.panel("WhiteCard" if completed and not claimed else "Card")
	var col := U.vbox(3)
	card.add_child(col)
	var head := U.hbox(4)
	head.add_child(U.icon("check" if completed else "bandera"))
	var t := U.label(mis["title"], U.SIZE_BODY, U.TEXT, true)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	t.clip_text = true
	head.add_child(t)
	col.add_child(head)
	col.add_child(U.para(mis["description"], U.SIZE_SMALL, U.TEXT_SOFT))
	var reward: Dictionary = mis.get("reward", m.data.daily_cfg["reward"]) if kind != "daily" else m.data.daily_cfg["reward"]
	var row := U.hbox(4)
	var bar := U.progress("verde" if not completed else "amarillo", 8)
	row.add_child(bar)
	var pl := U.label("", U.SIZE_SMALL, U.TEXT, true)
	pl.custom_minimum_size.x = 70
	pl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	row.add_child(pl)
	col.add_child(row)
	var target := float(mis["target"])
	var metric: String = mis["metric"]
	var money_label: bool = mis.get("money_label", false) or metric in ["money", "net_worth", "run_earnings", "lifetime_earnings"]
	var prog := func() -> float:
		if kind == "daily":
			return ProgressionSystem.daily_progress(m, mis)
		return m.metric(metric)
	_bars.append([bar, pl, prog, target, money_label, completed])
	var foot := U.hbox(4)
	var rl := U.label("Premio: " + ProgressionSystem.describe(m, reward), U.SIZE_SMALL, U.GREEN, true)
	rl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	rl.clip_text = true
	foot.add_child(rl)
	if claimed:
		foot.add_child(U.label("Reclamada", U.SIZE_SMALL, U.TEXT_SOFT, true))
	elif completed:
		var b := U.button("RECLAMAR", "verde", "regalo", 40, U.SIZE_BODY)
		var mid: String = mis["id"]
		var claim := func() -> void:
			if _hold:
				return
			_hold = true
			var r := ProgressionSystem.claim_daily_mission(m, mid) if kind == "daily" else ProgressionSystem.claim_mission(m, mid)
			if not Main.instance.result(r):
				_release()
				return
			b.disabled = true
			Juice.mission_done(card, _release)
		U.on_press(b, claim, "")
		foot.add_child(b)
	else:
		foot.add_child(U.label("En progreso", U.SIZE_SMALL, U.TEXT_SOFT))
	col.add_child(foot)
	return card


func _release() -> void:
	_hold = false
	if _pending:
		_pending = false
		rebuild()


func _upcoming_card(mis: Dictionary) -> Control:
	var card := U.panel("SlateCard")
	var row := U.hbox(4)
	row.add_child(U.icon("candado"))
	var v := U.vbox(0)
	v.add_child(U.label("Próxima: " + mis["title"], U.SIZE_SMALL, U.TEXT_LIGHT, true))
	v.add_child(U.para(mis["description"], U.SIZE_SMALL, Color("c2c0d6")))
	v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(v)
	card.add_child(row)
	return card


func _process(delta: float) -> void:
	if not is_visible_in_tree():
		return
	_timer += delta
	if _timer >= 0.5:
		_timer = 0.0
		_refresh()


func _refresh() -> void:
	for b in _bars:
		var v: float = b[2].call()
		var target: float = b[3]
		var done: bool = b[5]
		if done:
			v = maxf(v, target)
		b[0].value = clampf(v / target, 0.0, 1.0)
		if b[4]:
			b[1].text = "%s/%s" % [Fmt.money(minf(v, target)), Fmt.money(target)]
		else:
			b[1].text = "%s/%s" % [Fmt.num(floorf(minf(v, target))), Fmt.num(target)]
