class_name ManageBusinessModal
extends VBoxContainer
## "Administrar": mejoras, empleados, mercadería y datos de un negocio.

const STAT_TEXT := {
	"capacity": "+%d %% capacidad de mercadería",
	"cost_reduction": "-%d %% costo de mercadería",
	"speed": "+%d %% velocidad",
	"units": "+%d %% clientes por ciclo",
	"revenue": "+%d %% precio de venta",
	"slots": "+%d puesto de empleado",
	"employee_eff": "+%d %% eficiencia del equipo",
	"salary_reduction": "-%d %% sueldos",
}

var m: GameModel
var bid: String
var tab := 0
var _content: VBoxContainer
var _refreshers: Array[Callable] = []
var _timer := 0.0
var _window: ModalHost.ModalWindow


static func open(id: String, start_tab := 0) -> void:
	var v := ManageBusinessModal.new()
	v.bid = id
	v.tab = start_tab
	v._window = Main.instance.modal_host.open("Administrar " + Game.m.data.business_by_id[id]["name"], v)


func _ready() -> void:
	m = Game.m
	add_theme_constant_override("separation", 6)
	add_child(U.tabs(["Mejoras", "Empleados", "Mercadería", "Datos"], func(i: int) -> void:
		tab = i
		_build(), tab))
	_content = U.vbox(5)
	add_child(_content)
	m.business_changed.connect(_on_changed)
	_build()


func _on_changed(id: String) -> void:
	if id == bid and is_inside_tree():
		_build.call_deferred()


func _process(delta: float) -> void:
	_timer += delta
	if _timer >= 0.4:
		_timer = 0.0
		for r in _refreshers:
			r.call()


func _build() -> void:
	U.clear(_content)
	_refreshers.clear()
	match tab:
		0: _build_upgrades()
		1: _build_employees()
		2: _build_stock()
		3: _build_data()


# ------------------------------------------------------------------ mejoras

func _build_upgrades() -> void:
	_content.add_child(U.para("Cada mejora cambia de verdad los números del negocio. Las más avanzadas piden nivel y otras mejoras.", 9, U.TEXT_SOFT))
	for u in m.data.upgrades:
		var uid: String = u["id"]
		var st := m.upgrade_status(bid, uid)
		var card := U.panel("Inset" if not st["locked"] else "InsetDark")
		var col := U.vbox(2)
		card.add_child(col)
		var head := U.hbox(4)
		head.add_child(U.icon(u["icon"]))
		var light: bool = st["locked"]
		var name := U.label(m.upgrade_name(bid, uid), U.SIZE_SMALL, U.TEXT_LIGHT if light else U.TEXT, true)
		name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		name.clip_text = true
		head.add_child(name)
		head.add_child(U.label("Nv %d/%d" % [st["level"], st["max"]], U.SIZE_SMALL, U.GOLD if light else U.TEXT_SOFT, true))
		col.add_child(head)
		col.add_child(U.para(u["description"], 9, Color("c2c0d6") if light else U.TEXT_SOFT))
		col.add_child(U.para(_effect_text(u, int(st["level"])), 9, Color("8fd47a") if light else U.GREEN))
		for r in st["reasons"]:
			col.add_child(U.label(r, 9, Color("f07c6c"), true))
		if not st["maxed"]:
			var row := U.hbox(4)
			var gain := m.preview_profit_gain(bid, func(s: Dictionary) -> void: s["upgrades"][uid] = int(s["upgrades"].get(uid, 0)) + 1)
			var gl := U.label(("+%s" % Fmt.per_sec(gain)) if gain > 0.01 else "", 9, U.GREEN if not light else Color("8fd47a"), true)
			gl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			row.add_child(gl)
			var b := U.button("Comprar " + Fmt.cost(st["cost"]), "verde", "", 24, U.SIZE_SMALL)
			b.disabled = st["locked"] or not st["affordable"]
			U.on_press(b, func() -> void: Main.instance.result(m.buy_upgrade(bid, uid)), "")
			_refreshers.append(func() -> void:
				var s2 := m.upgrade_status(bid, uid)
				b.disabled = s2["locked"] or not s2["affordable"])
			row.add_child(b)
			col.add_child(row)
		else:
			col.add_child(U.label("¡Al máximo!", U.SIZE_SMALL, U.GREEN, true))
		_content.add_child(card)


func _effect_text(u: Dictionary, level: int) -> String:
	var parts := []
	for e in u["effects"]:
		var v := float(e["value"])
		var per: String = STAT_TEXT[e["stat"]] % int(round(v * (1 if e["stat"] == "slots" else 100)))
		var now: String = STAT_TEXT[e["stat"]] % int(round(v * level * (1 if e["stat"] == "slots" else 100)))
		parts.append("%s por nivel (ahora %s)" % [per, now if level > 0 else "nada"])
	return "Efecto: " + "; ".join(parts)


# ---------------------------------------------------------------- empleados

func _build_employees() -> void:
	var d := m.derive(bid)
	var team := m.employees_of(bid)
	_content.add_child(U.label("Equipo: %d/%d puestos · Sueldos %s" % [team.size(), d["slots"], Fmt.per_sec(d["salary_sec"])], U.SIZE_SMALL, U.TEXT, true))
	if m.salary_debt > 0:
		_content.add_child(U.para("Hay sueldos atrasados (%s): el equipo rinde 50 %% hasta que se paguen." % Fmt.cost(m.salary_debt), U.SIZE_SMALL, U.RED))
	for e in team:
		_content.add_child(_employee_row(e, true, -1))
	if team.is_empty():
		_content.add_child(U.para("Todavía atendés vos. Contratá a alguien para automatizar.", U.SIZE_SMALL, U.TEXT_SOFT))
	_content.add_child(U.separator())
	var head := U.hbox(4)
	var hl := U.label("Candidatos", U.SIZE_BODY, U.TEXT, true)
	hl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(hl)
	var reroll := U.button("Buscar otros", "crema", "", 22, U.SIZE_SMALL)
	U.on_press(reroll, func() -> void: Main.instance.result(EmployeeSystem.reroll(m, bid)))
	_refreshers.append(func() -> void:
		var cd := float(m.biz[bid]["reroll_cd"])
		reroll.disabled = cd > 0.0
		reroll.text = "Buscar otros" if cd <= 0.0 else "Esperá %s" % Fmt.duration(cd))
	head.add_child(reroll)
	_content.add_child(head)
	if team.size() >= int(d["slots"]):
		_content.add_child(U.para("No hay puestos libres. Se suman en los niveles 10, 50 y 100 y con la mejora 'Empleado de confianza'.", 9, U.RED))
	EmployeeSystem.ensure_candidates(m, bid)
	var cands: Array = m.biz[bid]["candidates"]
	for i in cands.size():
		_content.add_child(_employee_row(cands[i], false, i))


func _employee_row(e: Dictionary, hired: bool, index: int) -> Control:
	var role: Dictionary = m.data.role_by_id[e["role"]]
	var card := U.panel("Inset")
	var row := U.hbox(6)
	card.add_child(row)
	var at := AtlasTexture.new()
	at.atlas = U.tex("characters/worker_%d.png" % int(e["variant"]))
	at.region = Rect2(4 * 16, 0, 16, 24)
	var face := TextureRect.new()
	face.texture = at
	face.custom_minimum_size = Vector2(16, 24)
	face.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	row.add_child(face)
	var col := U.vbox(1)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var top := U.hbox(4)
	var n := U.label(e["name"], U.SIZE_SMALL, U.TEXT, true)
	n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	n.clip_text = true
	top.add_child(n)
	top.add_child(U.label(role["name"], U.SIZE_SMALL, U.GREEN, true))
	col.add_child(top)
	var eff := m.employee_efficiency(e) if hired else float(e["eff"])
	var info := "Eficiencia %d %%" % int(round(eff * 100))
	if hired:
		info += " · Experiencia nv %d" % EmployeeSystem.xp_level(m, e)
	info += " · Sueldo %s" % Fmt.per_sec(e["salary"])
	col.add_child(U.label(info, 9, U.TEXT_SOFT))
	col.add_child(U.para(_benefit(role, eff), 9, U.TEXT))
	row.add_child(col)
	if hired:
		var fire := U.button("Despedir", "rojo", "", 22, 9)
		var eid: String = e["id"]
		U.on_press(fire, func() -> void:
			Main.instance.confirm("¿Despedir a %s?" % e["name"],
				"Se paga una indemnización de %s. El negocio pierde los beneficios de este empleado." % Fmt.cost(EmployeeSystem.severance(m, eid)),
				"Despedir", func() -> void: Main.instance.result(EmployeeSystem.fire(m, eid))))
		row.add_child(fire)
	else:
		var hire := U.button("Contratar\n" + Fmt.cost(e["hire"]), "verde", "", 30, 9)
		U.on_press(hire, func() -> void: Main.instance.result(EmployeeSystem.hire(m, bid, index)), "")
		var cost: int = e["hire"]
		_refreshers.append(func() -> void:
			var dd := m.derive(bid)
			hire.disabled = not m.economy.can_afford(cost) or int(dd["team_size"]) >= int(dd["slots"]))
		row.add_child(hire)
	return card


func _benefit(role: Dictionary, eff: float) -> String:
	var parts := []
	if role.get("auto_sell", false):
		parts.append("vende solo")
	if role.get("auto_restock", false):
		parts.append("repone solo")
	var fx: Dictionary = role["effects"]
	if fx.has("speed"):
		parts.append("+%d %% velocidad" % int(round(float(fx["speed"]) * eff * 100)))
	if fx.has("revenue"):
		parts.append("+%d %% ingresos" % int(round(float(fx["revenue"]) * eff * 100)))
	if fx.has("restock_speed"):
		parts.append("+%d %% velocidad de reposición" % int(round(float(fx["restock_speed"]) * eff * 100)))
	if fx.has("team_eff"):
		parts.append("+%d %% eficiencia del resto" % int(round(float(fx["team_eff"]) * eff * 100)))
	if fx.has("zone_revenue"):
		parts.append("+%d %% a todos tus negocios de la zona" % int(round(float(fx["zone_revenue"]) * eff * 100)))
	if role.get("manager", false):
		parts.append("resuelve solo las fallas de suministro")
	return "Aporta: " + ", ".join(parts) + "."


# --------------------------------------------------------------- mercadería

func _build_stock() -> void:
	var d := m.derive(bid)
	var s: Dictionary = m.biz[bid]
	_content.add_child(U.para("Cada ciclo atiende %s clientes repartidos según la demanda. Si un producto se agota, esa venta se pierde." % Fmt.num(d["units"]), 9, U.TEXT_SOFT))
	for p in d["products"]:
		var card := U.panel("Inset")
		var col := U.vbox(2)
		card.add_child(col)
		var top := U.hbox(4)
		top.add_child(U.icon(p["icon"]))
		var n := U.label(p["name"], U.SIZE_SMALL, U.TEXT, true)
		n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		top.add_child(n)
		var margin_pct := (1.0 - float(p["cost"]) / float(p["price"])) * 100.0
		top.add_child(U.label("Margen %d %%" % int(margin_pct), U.SIZE_SMALL, U.GREEN, true))
		col.add_child(top)
		var dem_txt := "Demanda %d %%" % int(round(float(p["u"]) / maxf(float(d["units"]), 0.0001) * 100))
		if float(p["demand_mult"]) != 1.0:
			dem_txt += " (evento x%s)" % str(snappedf(p["demand_mult"], 0.1))
		col.add_child(U.label("Venta %s · Compra %s · %s" % [Fmt.money(p["price"]), Fmt.money(p["cost"]), dem_txt], 9, U.TEXT_SOFT))
		var bar_row := U.hbox(4)
		var bar := U.progress("amarillo", 6)
		var have := float(s["stock"].get(p["id"], 0.0))
		bar.value = have / maxf(float(p["cap"]), 1.0)
		bar_row.add_child(bar)
		var pend := float(s["orders"].get(p["id"], {}).get("units", 0.0))
		var lbl := U.label("%s/%s%s" % [Fmt.num(floorf(have)), Fmt.num(p["cap"]), (" (+%s)" % Fmt.num(floorf(pend))) if pend > 0.0 else ""], 9, U.TEXT, true)
		bar_row.add_child(lbl)
		col.add_child(bar_row)
		var pid: String = p["id"]
		_refreshers.append(func() -> void:
			var dd := m.derive(bid)
			for pp in dd["products"]:
				if pp["id"] == pid:
					var hv := float(m.biz[bid]["stock"].get(pid, 0.0))
					bar.value = hv / maxf(float(pp["cap"]), 1.0)
					var pe := float(m.biz[bid]["orders"].get(pid, {}).get("units", 0.0))
					lbl.text = "%s/%s%s" % [Fmt.num(floorf(hv)), Fmt.num(pp["cap"]), (" (+%s)" % Fmt.num(floorf(pe))) if pe > 0.0 else ""])
		_content.add_child(card)
	_content.add_child(U.label("Reposición: tarda %s%s" % [Fmt.cycle(d["restock_time"]), " · automática" if d["auto_restock"] else " · manual"], U.SIZE_SMALL, U.TEXT, true))
	var b := U.button("Reponer todo", "celeste", "camion", 30)
	U.on_press(b, func() -> void: Main.instance.result(m.restock(bid)), "")
	_refreshers.append(func() -> void:
		var q := m.restock_quote(bid)
		b.disabled = q["items"].is_empty()
		b.text = "Depósito lleno" if q["items"].is_empty() else "Reponer todo · " + Fmt.cost(q["total"]))
	_content.add_child(b)


# -------------------------------------------------------------------- datos

func _build_data() -> void:
	var d := m.derive(bid)
	var s: Dictionary = m.biz[bid]
	var def: Dictionary = m.data.business_by_id[bid]
	_content.add_child(U.para(def["description"], U.SIZE_SMALL, U.TEXT))
	var rows := [
		["Nivel", "%d / %d" % [int(s["level"]), int(def["max_level"])]],
		["Clientes por ciclo", Fmt.num(d["units"])],
		["Duración del ciclo", Fmt.cycle(d["cycle"])],
		["Ingresos por ciclo", Fmt.money(d["revenue_cycle"])],
		["Ingresos por segundo", Fmt.per_sec(d["revenue_sec"])],
		["Mercadería por segundo", "-" + Fmt.per_sec(d["cost_cycle"] / d["cycle"])],
		["Sueldos por segundo", "-" + Fmt.per_sec(d["salary_sec"])],
		["Ganancia neta por segundo", Fmt.per_sec(float(d["profit_sec"]) - float(d["salary_sec"]))],
		["Automatización", ["Manual", "Ventas automáticas", "Vende y repone", "Gestión total"][int(d["automation"])]],
		["Demanda de la zona", "+%d %%" % int(round(float(d["zone_demand"]) * 100))],
		["Competencia", "-%d %%" % int(round(float(d["competition"]) * 100))],
		["Eventos", "x%s ingresos" % str(snappedf(d["event_revenue"], 0.01))],
		["Prestigio y turbos", "x%s" % str(snappedf(m.prestige_multiplier() * m.boost_multiplier(), 0.01))],
		["Ventas realizadas", Fmt.integer(s["sales"])],
		["Ganado en total", Fmt.money(s["earned"])],
		["Invertido", Fmt.money(s["invested"])],
	]
	for r in rows:
		_content.add_child(U.stat_row(r[0], r[1]))
	_content.add_child(U.separator())
	_content.add_child(U.label("Zona: " + m.data.zone_by_id[s["zone"]]["name"], U.SIZE_SMALL, U.TEXT, true))
	if m.zones.size() > 1:
		var cost := m.relocate_cost(bid)
		for zid in m.zones:
			if zid == s["zone"]:
				continue
			var b := U.button("Mudar a %s · %s" % [m.data.zone_by_id[zid]["name"], Fmt.cost(cost)], "crema", "mudanza", 24, 9)
			var z: String = zid
			U.on_press(b, func() -> void:
				Main.instance.confirm("¿Mudar el negocio?", "Cuesta %s. La demanda y la competencia cambian según la zona." % Fmt.cost(cost), "Mudar",
					func() -> void: Main.instance.result(m.relocate(bid, z)), false))
			_content.add_child(b)
	else:
		_content.add_child(U.para("Desbloqueá zonas en el Mapa para poder mudarte.", 9, U.TEXT_SOFT))
