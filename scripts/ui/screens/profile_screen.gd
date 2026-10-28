class_name ProfileScreen
extends Control
## Sección PERFIL: identidad de la empresa, nivel empresarial, logros,
## hitos, prestigio, tienda (en desarrollo) y accesos a ajustes/estadísticas.

var m: GameModel
var _col: VBoxContainer
var _stage_bar: ProgressBar
var _stage_label: Label
var _timer := 0.0


func _ready() -> void:
	m = Game.m
	_col = U.vbox(6)
	var sc := U.scroll(U.margin(_col, 6, 6, 6, 8))
	sc.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(sc)
	m.profile_changed.connect(rebuild)
	m.progress_changed.connect(rebuild)
	m.stage_changed.connect(func(_s: int) -> void: rebuild())
	Friends.changed.connect(_on_friends_changed)
	Auth.changed.connect(rebuild)
	rebuild()


func on_shown() -> void:
	rebuild()


func rebuild() -> void:
	if not is_inside_tree():
		return
	U.clear(_col)
	_col.add_child(_header())
	_col.add_child(_summary())
	_col.add_child(_friends())
	_col.add_child(_achievements())
	_col.add_child(_prestige())
	_col.add_child(_milestones())
	_col.add_child(_store())
	var row := U.hbox(4)
	var st := U.button("Estadísticas", "celeste", "grafico", 30)
	st.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	U.on_press(st, func() -> void: StatsModal.open())
	row.add_child(st)
	var se := U.button("Ajustes", "crema", "engranaje", 30)
	se.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	U.on_press(se, func() -> void: SettingsModal.open())
	row.add_child(se)
	_col.add_child(row)
	_col.add_child(U.para("Tycoon Argentina v%s · %s Fuente VT323 (licencia OFL). Arte, sonidos y nombres originales y ficticios." % [ProjectSettings.get_setting("application/config/version"), Cloud.status_text() if Auth.signed_in() else "Progreso guardado en este teléfono (con una cuenta, también en la nube)."], U.SIZE_SMALL, Color("8c8aa8")))
	_refresh()


func _header() -> Control:
	var card := U.panel("Card", 0)
	var outer := U.vbox(0)
	card.add_child(outer)
	# Banner 3:1 con botón para cambiarlo
	var banner_box := Control.new()
	banner_box.custom_minimum_size.y = 96
	banner_box.clip_contents = true
	var banner := TextureRect.new()
	ProfileWidgets.apply_banner(banner)
	banner.set_anchors_preset(Control.PRESET_FULL_RECT)
	banner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	banner_box.add_child(banner)
	var bbtn := U.button("Cambiar banner", "crema", "", 26, U.SIZE_SMALL)
	bbtn.set_anchors_preset(Control.PRESET_TOP_RIGHT)
	bbtn.position = Vector2(-112, 6)
	bbtn.custom_minimum_size.x = 106
	U.on_press(bbtn, ProfileWidgets.banner_menu)
	banner_box.add_child(bbtn)
	outer.add_child(banner_box)
	var row := U.hbox(8)
	outer.add_child(U.margin(row, 6, 6, 6, 6))
	# Foto circular (o avatar pixel) que se toca para cambiar
	var av := Button.new()
	av.flat = true
	av.focus_mode = Control.FOCUS_NONE
	av.custom_minimum_size = Vector2(70, 70)
	av.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	var ring := Panel.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("2e2b48")
	sb.set_corner_radius_all(35)
	sb.border_color = Color("f0eee6")
	sb.set_border_width_all(2)
	ring.add_theme_stylebox_override("panel", sb)
	ring.set_anchors_preset(Control.PRESET_FULL_RECT)
	ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	av.add_child(ring)
	var big := TextureRect.new()
	ProfileWidgets.apply_avatar(big)
	big.set_anchors_preset(Control.PRESET_FULL_RECT)
	big.offset_left = 3
	big.offset_top = 3
	big.offset_right = -3
	big.offset_bottom = -3
	big.mouse_filter = Control.MOUSE_FILTER_IGNORE
	av.add_child(big)
	U.on_press(av, ProfileWidgets.photo_menu)
	row.add_child(av)
	var col := U.vbox(2)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var name_row := U.hbox(4)
	# Nombres largos: hasta dos líneas y, si igual no entra, "…". Ninguna
	# etiqueta de esta columna fija un ancho mínimo (si no, empujaban el botón
	# Editar fuera de la tarjeta).
	var n := U.label(m.profile["company"], U.SIZE_TITLE, U.TEXT, true)
	n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	n.custom_minimum_size.x = 1
	n.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	n.max_lines_visible = 2
	n.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	name_row.add_child(n)
	var edit := U.button("Editar", "crema", "", 22, U.SIZE_SMALL)
	edit.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	U.on_press(edit, RenameDialog.open)
	name_row.add_child(edit)
	col.add_child(name_row)
	col.add_child(_fit(U.label("Etapa %d de 8 · %s" % [m.stage, m.data.stage_name(m.stage)], U.SIZE_SMALL, U.GREEN, true)))
	_stage_bar = U.progress("violeta", 8)
	col.add_child(_stage_bar)
	_stage_label = _fit(U.label("", U.SIZE_SMALL, U.TEXT_SOFT))
	col.add_child(_stage_label)
	row.add_child(col)
	return card


## Etiqueta de una línea que se recorta con "…" en vez de ensanchar la tarjeta.
func _fit(l: Label) -> Label:
	l.clip_text = true
	l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	l.custom_minimum_size.x = 1
	return l


func _summary() -> Control:
	var card := U.panel("Card")
	var col := U.vbox(2)
	card.add_child(col)
	col.add_child(U.label("Resumen", U.SIZE_BODY, U.TEXT, true))
	col.add_child(U.stat_row("Patrimonio", Fmt.money(m.net_worth())))
	col.add_child(U.stat_row("Ganancia neta", Fmt.per_sec(m.net_per_sec())))
	col.add_child(U.stat_row("Negocios", "%d/%d" % [m.owned_ids().size(), m.data.businesses.size()]))
	col.add_child(U.stat_row("Empleados", str(m.employees.size())))
	col.add_child(U.stat_row("Ganado en la historia", Fmt.money(m.economy.lifetime_earned)))
	return card


## Amigos: resumen y acceso. Sin cuenta verificada explica qué falta.
func _friends() -> Control:
	var card := U.panel("Card")
	var col := U.vbox(4)
	card.add_child(col)
	var head := U.hbox(4)
	head.add_child(U.icon("trofeo"))
	var pending := Friends.pending_count()
	head.add_child(U.label("Amigos" + (" (%d nuevos)" % pending if pending > 0 else ""), U.SIZE_BODY, U.TEXT, true))
	col.add_child(head)
	var text := ""
	var btn_text := "Ver amigos"
	var style := "celeste"
	if not Auth.signed_in():
		text = "Con una cuenta podés sumar amigos, competir en un ranking y convidarse mates (premios diarios)."
		btn_text = "Crear cuenta o ingresar"
	elif not Auth.email_verified:
		text = "Confirmá que el email %s es tuyo para agregar amigos." % Auth.email
		btn_text = "Verificar email"
		style = "amarillo"
	else:
		var n := Friends.friends.size()
		text = ("Tenés %d amigo%s. Tu código: %s" % [n, "" if n == 1 else "s", Friends.my_code]) if Friends.my_code != "" else "Compartí tu código y competí en el ranking."
		if pending > 0:
			style = "verde"
	col.add_child(U.para(text, U.SIZE_SMALL, U.TEXT_SOFT))
	var b := U.button(btn_text, style, "persona", 30, U.SIZE_SMALL)
	U.on_press(b, FriendsModal.open)
	col.add_child(b)
	return card


## Los amigos se actualizan solos cada tanto: sólo se rearma si se ve el perfil.
func _on_friends_changed() -> void:
	if is_visible_in_tree():
		rebuild()


func _achievements() -> Control:
	var card := U.panel("Card")
	var col := U.vbox(4)
	card.add_child(col)
	col.add_child(U.label("Logros (%d/%d)" % [m.achievements.size(), m.data.achievements.size()], U.SIZE_BODY, U.TEXT, true))
	var grid := GridContainer.new()
	grid.columns = 8
	grid.add_theme_constant_override("h_separation", 3)
	grid.add_theme_constant_override("v_separation", 3)
	for a in m.data.achievements:
		var got := m.achievements.has(a["id"])
		var b := Button.new()
		b.theme_type_variation = "Btn_" + ("amarillo" if got else "gris")
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(34, 32)
		b.icon = U.icon_tex(a["icon"] if got else "candado")
		b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		var aa: Dictionary = a
		U.on_press(b, func() -> void: _achievement_info(aa))
		grid.add_child(b)
	col.add_child(grid)
	return card


func _achievement_info(a: Dictionary) -> void:
	var body := U.vbox(4)
	var got := m.achievements.has(a["id"])
	body.add_child(U.para(a["description"], U.SIZE_BODY, U.TEXT))
	body.add_child(U.label("Premio: " + ProgressionSystem.describe(m, a["reward"]), U.SIZE_SMALL, U.GREEN, true))
	var v := m.metric(a["metric"])
	var bar := U.progress("amarillo", 8)
	bar.value = 1.0 if got else clampf(v / float(a["target"]), 0.0, 1.0)
	body.add_child(bar)
	if got:
		body.add_child(U.label("Desbloqueado el " + Time.get_date_string_from_unix_time(int(m.achievements[a["id"]])), U.SIZE_SMALL, U.TEXT_SOFT))
	Main.instance.modal_host.open(a["name"], body, true, 280)


func _prestige() -> Control:
	var card := U.panel("Card")
	var col := U.vbox(4)
	card.add_child(col)
	var head := U.hbox(4)
	head.add_child(U.icon("corona"))
	head.add_child(U.label("Nuevo grupo empresarial", U.SIZE_BODY, U.TEXT, true))
	col.add_child(head)
	var pts := int(m.prestige["points"])
	col.add_child(U.stat_row("Puntos de prestigio", "%d (%d disponibles)" % [pts, PrestigeSystem.available_points(m)]))
	col.add_child(U.stat_row("Bonificación permanente", "x%s ingresos" % str(snappedf(m.prestige_multiplier(), 0.01))))
	if PrestigeSystem.unlocked(m):
		var gain := PrestigeSystem.pending_points(m)
		col.add_child(U.para("Vendés todo y fundás un grupo nuevo: ganás %d puntos ahora. Es opcional: podés seguir jugando sin hacerlo." % gain, U.SIZE_SMALL, U.TEXT_SOFT))
		var b := U.button("Fundar nuevo grupo (+%d)" % gain, "violeta", "corona", 30)
		b.disabled = gain <= 0
		U.on_press(b, PrestigeModal.open)
		col.add_child(b)
	else:
		col.add_child(U.para("Se habilita en la etapa 5 (%s). Es una opción de largo plazo, no una obligación." % m.data.stage_name(5), U.SIZE_SMALL, U.TEXT_SOFT))
	if pts > 0:
		col.add_child(U.label("Ventajas permanentes", U.SIZE_SMALL, U.TEXT, true))
		for p in m.data.prestige_cfg["perks"]:
			var row := U.hbox(4)
			row.add_child(U.icon(p["icon"]))
			var v := U.vbox(0)
			v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			v.add_child(U.label("%s (%d/%d)" % [p["name"], m.perk_level(p["id"]), int(p["max_level"])], U.SIZE_SMALL, U.TEXT, true))
			v.add_child(U.para(p["description"], U.SIZE_SMALL, U.TEXT_SOFT))
			row.add_child(v)
			var maxed := m.perk_level(p["id"]) >= int(p["max_level"])
			var b2 := U.button("Máx." if maxed else "%d pts" % PrestigeSystem.perk_cost(m, p["id"]), "violeta", "", 24, U.SIZE_SMALL)
			b2.disabled = maxed or PrestigeSystem.available_points(m) < PrestigeSystem.perk_cost(m, p["id"])
			var pid: String = p["id"]
			U.on_press(b2, func() -> void: Main.instance.result(PrestigeSystem.buy_perk(m, pid)), "")
			row.add_child(b2)
			col.add_child(row)
	return card


func _milestones() -> Control:
	var card := U.panel("Card")
	var col := U.vbox(2)
	card.add_child(col)
	col.add_child(U.label("Hitos de tu historia", U.SIZE_BODY, U.TEXT, true))
	var list: Array = m.profile.get("milestones", [])
	for i in range(list.size() - 1, maxi(-1, list.size() - 9), -1):
		var it: Dictionary = list[i]
		col.add_child(U.para("%s · %s" % [Time.get_date_string_from_unix_time(int(it["t"])), it["text"]], 9, U.TEXT_SOFT))
	return card


func _store() -> Control:
	var card := U.panel("SlateCard")
	var col := U.vbox(3)
	card.add_child(col)
	var head := U.hbox(4)
	head.add_child(U.icon("regalo"))
	head.add_child(U.label("Tienda y bonos", U.SIZE_BODY, U.TEXT_LIGHT, true))
	col.add_child(head)
	col.add_child(U.para(Monetization.status_text(), U.SIZE_SMALL, Color("c2c0d6")))
	var b := U.button("Bonos por anuncio", "amarillo", "regalo", 32, U.SIZE_SMALL)
	U.on_press(b, func() -> void: AdsModal.open())
	col.add_child(b)
	return card


func _process(delta: float) -> void:
	if not is_visible_in_tree():
		return
	_timer += delta
	if _timer >= 0.5:
		_timer = 0.0
		_refresh()


func _refresh() -> void:
	if _stage_bar == null or not is_instance_valid(_stage_bar):
		return
	# 10.0: la etapa avanza con cada región conquistada.
	if m.stage >= m.data.stages.size():
		_stage_bar.value = 1.0
		_stage_label.text = "¡Toda la Argentina es tuya!"
	else:
		var region: Dictionary = m.data.regions[m.stage - 1]
		var total := m.data.zones_in_region(region["id"]).size()
		var done := ConquestSystem.conquered_in_region(m, region["id"])
		_stage_bar.value = float(done) / maxf(1.0, float(total))
		_stage_label.text = "%s: %d/%d provincias para la etapa %d" % [region["name"], done, total, m.stage + 1]
