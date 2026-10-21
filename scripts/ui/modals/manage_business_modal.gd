class_name ManageBusinessModal
extends VBoxContainer
## "Administrar": todo lo del negocio agrupado en 4 categorías.
##   NEGOCIO      mercadería por producto, reponer, zona
##   EMPLEADOS    equipo actual y candidatos
##   MEJORAS      la próxima disponible primero; bloqueadas abajo con motivo
##   ESTADÍSTICAS números del negocio
## Colores: verde = ganancia, rojo = gasto/falta, amarillo = aviso,
## celeste = acción (ver UiColors).

const TABS := ["Negocio", "Empleados", "Mejoras", "Datos"]
const STAT_TEXT := {
	"capacity": "+%d %% capacidad de mercadería",
	"cost_reduction": "-%d %% costo de mercadería",
	"speed": "+%d %% velocidad",
	"units": "+%d %% clientes por venta",
	"revenue": "+%d %% precio de venta",
	"slots": "+%d puesto de empleado",
	"employee_eff": "+%d %% rendimiento del equipo",
	"salary_reduction": "-%d %% sueldos",
}

var m: GameModel
var bid: String
var tab := 0
var _content: VBoxContainer
var _refreshers: Array[Callable] = []
var _timer := 0.0
var _window: ModalHost.ModalWindow


## start_tab: 0 negocio, 1 empleados, 2 mejoras, 3 datos.
static func open(id: String, start_tab := 0) -> void:
	var v := ManageBusinessModal.new()
	v.bid = id
	v.tab = start_tab
	v._window = Main.instance.modal_host.open(Game.m.data.business_by_id[id]["name"], v)


func _ready() -> void:
	m = Game.m
	add_theme_constant_override("separation", 8)
	var tabs := U.tabs(TABS, func(i: int) -> void:
		tab = i
		_build(), tab)
	for b in tabs.get_children():
		(b as Button).custom_minimum_size.y = 40
	add_child(tabs)
	_content = U.vbox(8)
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
		0: _build_business()
		1: _build_employees()
		2: _build_upgrades()
		3: _build_data()


func _section(text: String) -> Label:
	return U.label(text, U.SIZE_BODY, U.TEXT, true)


# ------------------------------------------------------------------ NEGOCIO

func _build_business() -> void:
	var d := m.derive(bid)
	var s: Dictionary = m.biz[bid]
	_content.add_child(_section("Mercadería"))
	_content.add_child(U.para("Cada venta atiende %s clientes repartidos según lo que más se pide. Si un producto se acaba, esa venta se pierde." % Fmt.num(d["units"]), U.SIZE_SMALL, U.TEXT_SOFT))
	for p in d["products"]:
		var card := U.panel("Inset")
		var col := U.vbox(3)
		card.add_child(col)
		var top := U.hbox(6)
		top.add_child(U.icon(p["icon"]))
		var n := U.label(p["name"], U.SIZE_BODY, U.TEXT, true)
		n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		top.add_child(n)
		var margin_pct := (1.0 - float(p["cost"]) / float(p["price"])) * 100.0
		top.add_child(U.label("ganás %d %%" % int(margin_pct), U.SIZE_SMALL, UiColors.GAIN, true))
		col.add_child(top)
		var prices := U.hbox(8)
		prices.add_child(U.label("Vendés " + Fmt.money(p["price"]), U.SIZE_SMALL, UiColors.GAIN, true))
		prices.add_child(U.label("Comprás " + Fmt.money(p["cost"]), U.SIZE_SMALL, UiColors.LOSS, true))
		if float(p["demand_mult"]) > 1.0:
			prices.add_child(U.label("¡más demanda!", U.SIZE_SMALL, UiColors.WARN, true))
		col.add_child(prices)
		var bar_row := U.hbox(6)
		var bar := U.progress("amarillo", 8)
		bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		bar_row.add_child(bar)
		var lbl := U.label("", U.SIZE_SMALL, U.TEXT, true)
		bar_row.add_child(lbl)
		col.add_child(bar_row)
		var pid: String = p["id"]
		var upd := func() -> void:
			for pp in m.derive(bid)["products"]:
				if pp["id"] == pid:
					var hv := float(m.biz[bid]["stock"].get(pid, 0.0))
					var ratio := hv / maxf(float(pp["cap"]), 1.0)
					bar.value = ratio
					bar.theme_type_variation = "Bar_rojo" if ratio < 0.01 else ("Bar_amarillo" if ratio < 0.3 else "Bar_verde")
					var pe := float(m.biz[bid]["orders"].get(pid, {}).get("units", 0.0))
					lbl.text = "%s/%s%s" % [Fmt.num(floorf(hv)), Fmt.num(pp["cap"]), (" (+%s)" % Fmt.num(floorf(pe))) if pe > 0.0 else ""]
		upd.call()
		_refreshers.append(upd)
		_content.add_child(card)
	_content.add_child(U.para("El pedido tarda %s en llegar · reposición %s" % [Fmt.cycle(d["restock_time"]), "automática (empleado)" if d["auto_restock"] else "manual"], U.SIZE_SMALL, U.TEXT_SOFT))
	var b := U.button("", UiColors.BTN_WARN, "camion", 44, U.SIZE_BODY)
	U.on_press(b, func() -> void: Main.instance.result(m.restock(bid)), "whoosh")
	var upd_b := func() -> void:
		var q := m.restock_quote(bid)
		b.disabled = q["items"].is_empty() or m.economy.money <= 0
		b.text = "DEPÓSITO LLENO" if q["items"].is_empty() else ("REPONER TODO · " + Fmt.cost(q["total"]))
	upd_b.call()
	_refreshers.append(upd_b)
	_content.add_child(b)

	_content.add_child(U.separator())
	_content.add_child(_section("Zona"))
	_content.add_child(U.para("%s · clientes +%d %% · competencia -%d %%" % [m.data.zone_by_id[s["zone"]]["name"], int(round(float(d["zone_demand"]) * 100)), int(round(float(d["competition"]) * 100))], U.SIZE_SMALL, U.TEXT))
	if m.zones.size() > 1:
		var cost := m.relocate_cost(bid)
		for zid in m.zones:
			if zid == s["zone"]:
				continue
			var z: String = zid
			var mb := UiColors.buy_button("Mudar a " + m.data.zone_by_id[zid]["name"], cost, func() -> void:
				Main.instance.confirm("¿Mudar el negocio?", "Cuesta %s. La demanda y la competencia cambian según la zona." % Fmt.cost(cost), "Mudar",
					func() -> void: Main.instance.result(m.relocate(bid, z)), false))
			_refreshers.append(func() -> void: UiColors.refresh(mb))
			_content.add_child(mb)
	else:
		_content.add_child(U.para("Desbloqueá zonas en el MAPA para poder mudarte.", U.SIZE_SMALL, U.TEXT_SOFT))


# ---------------------------------------------------------------- EMPLEADOS

func _build_employees() -> void:
	var d := m.derive(bid)
	var team := m.employees_of(bid)
	var head := U.hbox(6)
	var hl := _section("Equipo %d/%d" % [team.size(), d["slots"]])
	hl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(hl)
	head.add_child(U.label("Sueldos -" + Fmt.per_sec(d["salary_sec"]), U.SIZE_SMALL, UiColors.LOSS, true))
	_content.add_child(head)
	if m.salary_debt > 0:
		_content.add_child(U.para("Hay sueldos atrasados (%s): el equipo rinde 50 %% hasta que se paguen." % Fmt.cost(m.salary_debt), U.SIZE_SMALL, UiColors.LOSS))
	for e in team:
		_content.add_child(_employee_row(e, true, -1))
	if team.is_empty():
		_content.add_child(U.para("Todavía atendés vos. Contratá a alguien y el negocio trabaja solo.", U.SIZE_SMALL, U.TEXT_SOFT))
	_content.add_child(U.separator())
	var ch := U.hbox(6)
	var cl := _section("Candidatos")
	cl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ch.add_child(cl)
	var reroll := U.button("Buscar otros", "crema", "", 36, U.SIZE_SMALL)
	U.on_press(reroll, func() -> void: Main.instance.result(EmployeeSystem.reroll(m, bid)))
	var upd_r := func() -> void:
		var cd := float(m.biz[bid]["reroll_cd"])
		reroll.disabled = cd > 0.0
		reroll.text = "Buscar otros" if cd <= 0.0 else "Esperá " + Fmt.duration(cd)
	upd_r.call()
	_refreshers.append(upd_r)
	ch.add_child(reroll)
	_content.add_child(ch)
	if team.size() >= int(d["slots"]):
		_content.add_child(U.para("No hay puestos libres. Se suman en los niveles 10, 50 y 100 y con la mejora de confianza.", U.SIZE_SMALL, UiColors.WARN))
	EmployeeSystem.ensure_candidates(m, bid)
	var cands: Array = m.biz[bid]["candidates"]
	for i in cands.size():
		_content.add_child(_employee_row(cands[i], false, i))


func _employee_row(e: Dictionary, hired: bool, index: int) -> Control:
	var role: Dictionary = m.data.role_by_id[e["role"]]
	var card := U.panel("Inset")
	var outer := U.vbox(6)
	card.add_child(outer)
	var row := U.hbox(8)
	outer.add_child(row)
	var at := AtlasTexture.new()
	at.atlas = U.tex("characters/worker_%d.png" % int(e["variant"]))
	var fw := at.atlas.get_width() / 10
	at.region = Rect2(4 * fw, 0, fw, at.atlas.get_height())
	var face := TextureRect.new()
	face.texture = at
	face.custom_minimum_size = Vector2(fw, at.atlas.get_height())
	face.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	row.add_child(face)
	var col := U.vbox(2)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var n := U.label(e["name"], U.SIZE_BODY, U.TEXT, true)
	n.clip_text = true
	col.add_child(n)
	col.add_child(U.label(role["name"], U.SIZE_SMALL, UiColors.INFO, true))
	col.add_child(U.para(_benefit(role, m.employee_efficiency(e) if hired else float(e["eff"])), U.SIZE_SMALL, UiColors.GAIN))
	var info := "Rinde %d %%" % int(round((m.employee_efficiency(e) if hired else float(e["eff"])) * 100))
	if hired:
		info += " · experiencia nv %d" % EmployeeSystem.xp_level(m, e)
	col.add_child(U.label(info, U.SIZE_SMALL, U.TEXT_SOFT))
	col.add_child(U.label("Sueldo -" + Fmt.per_sec(e["salary"]), U.SIZE_SMALL, UiColors.LOSS, true))
	row.add_child(col)
	if hired:
		var fire := U.button("Despedir", UiColors.BTN_DANGER, "", 32, U.SIZE_SMALL)
		var eid: String = e["id"]
		U.on_press(fire, func() -> void:
			Main.instance.confirm("¿Despedir a %s?" % e["name"],
				"Se paga una indemnización de %s y el negocio pierde lo que aporta." % Fmt.cost(EmployeeSystem.severance(m, eid)),
				"Despedir", func() -> void: Main.instance.result(EmployeeSystem.fire(m, eid))))
		outer.add_child(fire)
	else:
		var hire := UiColors.buy_button("CONTRATAR", int(e["hire"]), func() -> void: Main.instance.result(EmployeeSystem.hire(m, bid, index)), 40)
		hire.icon = U.icon_tex("persona")
		var upd := func() -> void:
			var dd := m.derive(bid)
			UiColors.set_cost(hire, int(e["hire"]), "Sin puestos libres" if int(dd["team_size"]) >= int(dd["slots"]) else "")
			if not hire.disabled:
				hire.icon = U.icon_tex("persona")
		upd.call()
		_refreshers.append(upd)
		outer.add_child(hire)
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
		parts.append("reposición +%d %% más rápida" % int(round(float(fx["restock_speed"]) * eff * 100)))
	if fx.has("team_eff"):
		parts.append("+%d %% rendimiento del resto" % int(round(float(fx["team_eff"]) * eff * 100)))
	if fx.has("zone_revenue"):
		parts.append("+%d %% a tus negocios de la zona" % int(round(float(fx["zone_revenue"]) * eff * 100)))
	if role.get("manager", false):
		parts.append("resuelve solo las fallas de suministro")
	var t := ", ".join(parts)
	return t.substr(0, 1).to_upper() + t.substr(1) + "."


# ------------------------------------------------------------------ MEJORAS

func _build_upgrades() -> void:
	_content.add_child(U.para("Cada mejora cambia los números del negocio. Arriba, las que podés comprar; abajo, las bloqueadas con lo que piden.", U.SIZE_SMALL, U.TEXT_SOFT))
	var items := []
	for u in m.data.upgrades:
		var st := m.upgrade_status(bid, u["id"])
		var order := 0 if (not st["locked"] and not st["maxed"]) else (1 if st["locked"] else 2)
		items.append([order, u, st])
	items.sort_custom(func(a, b): return a[0] < b[0])
	var last_group := -1
	for it in items:
		var group: int = it[0]
		if group != last_group:
			last_group = group
			if group == 1:
				_content.add_child(_section("Bloqueadas"))
			elif group == 2:
				_content.add_child(_section("Completas"))
		_content.add_child(_upgrade_card(it[1], it[2]))


func _upgrade_card(u: Dictionary, st: Dictionary) -> Control:
	var uid: String = u["id"]
	var locked: bool = st["locked"]
	var card := U.panel("InsetDark" if locked else "Inset")
	var col := U.vbox(3)
	card.add_child(col)
	var head := U.hbox(6)
	head.add_child(U.icon(u["icon"] if not locked else "candado"))
	var name := U.label(m.upgrade_name(bid, uid), U.SIZE_BODY, U.TEXT_LIGHT if locked else U.TEXT, true)
	name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name.clip_text = true
	head.add_child(name)
	head.add_child(U.label("Nv %d/%d" % [st["level"], st["max"]], U.SIZE_SMALL, U.GOLD if locked else U.TEXT_SOFT, true))
	col.add_child(head)
	col.add_child(U.para(u["description"], U.SIZE_SMALL, Color("c9c7da") if locked else U.TEXT_SOFT))
	col.add_child(U.para(_effect_text(u, int(st["level"])), U.SIZE_SMALL, UiColors.GAIN_LIGHT if locked else UiColors.GAIN))
	if locked:
		for r in st["reasons"]:
			var rr := U.hbox(4)
			rr.add_child(U.icon("candado"))
			rr.add_child(U.para(r, U.SIZE_SMALL, UiColors.LOSS_LIGHT))
			col.add_child(rr)
		var req_lvl := int(u["requires_level"])
		if int(m.biz[bid]["level"]) < req_lvl:
			col.add_child(UiColors.requirement_row({"text": "Nivel del negocio", "current": float(m.biz[bid]["level"]), "target": float(req_lvl), "met": false, "money": false}, true))
	elif not st["maxed"]:
		var gain := m.preview_profit_gain(bid, func(s: Dictionary) -> void: s["upgrades"][uid] = int(s["upgrades"].get(uid, 0)) + 1)
		if gain > 0.01:
			col.add_child(U.label("Suma +%s" % Fmt.per_sec(gain), U.SIZE_SMALL, UiColors.GAIN, true))
		var b := UiColors.buy_button("COMPRAR", int(st["cost"]), func() -> void: Main.instance.result(m.buy_upgrade(bid, uid)), 40)
		_refreshers.append(func() -> void:
			var s2 := m.upgrade_status(bid, uid)
			if not s2["maxed"]:
				UiColors.set_cost(b, int(s2["cost"])))
		col.add_child(b)
	return card


func _effect_text(u: Dictionary, level: int) -> String:
	var parts := []
	for e in u["effects"]:
		var mult := 1 if e["stat"] == "slots" else 100
		var per: String = STAT_TEXT[e["stat"]] % int(round(float(e["value"]) * mult))
		var now: String = STAT_TEXT[e["stat"]] % int(round(float(e["value"]) * level * mult))
		parts.append("%s por nivel (ahora: %s)" % [per, now if level > 0 else "nada"])
	return "; ".join(parts)


# ----------------------------------------------------------------- DATOS

func _build_data() -> void:
	var d := m.derive(bid)
	var s: Dictionary = m.biz[bid]
	var def: Dictionary = m.data.business_by_id[bid]
	_content.add_child(U.para(def["description"], U.SIZE_SMALL, U.TEXT))
	_content.add_child(_section("Por segundo"))
	_content.add_child(U.stat_row("Ingresos", "+" + Fmt.per_sec(d["revenue_sec"]), UiColors.GAIN))
	_content.add_child(U.stat_row("Mercadería", "-" + Fmt.per_sec(d["cost_cycle"] / d["cycle"]), UiColors.LOSS))
	_content.add_child(U.stat_row("Sueldos", "-" + Fmt.per_sec(d["salary_sec"]), UiColors.LOSS))
	var net := float(d["profit_sec"]) - float(d["salary_sec"])
	_content.add_child(U.stat_row("Ganancia neta", ("+" if net >= 0 else "") + Fmt.per_sec(net), UiColors.GAIN if net >= 0 else UiColors.LOSS))
	_content.add_child(_section("El negocio"))
	var rows := [
		["Nivel", "%d / %d" % [int(s["level"]), int(def["max_level"])]],
		["Clientes por venta", Fmt.num(d["units"])],
		["Cada venta tarda", Fmt.cycle(d["cycle"])],
		["Ingreso por venta", Fmt.money(d["revenue_cycle"])],
		["Automatización", ["Manual", "Vende solo", "Vende y repone solo", "Gestión total"][int(d["automation"])]],
		["Clientes extra por la zona", "+%d %%" % int(round(float(d["zone_demand"]) * 100))],
		["Competencia", "-%d %%" % int(round(float(d["competition"]) * 100))],
		["Eventos", "x%s" % str(snappedf(d["event_revenue"], 0.01))],
		["Prestigio y turbos", "x%s" % str(snappedf(m.prestige_multiplier() * m.boost_multiplier(), 0.01))],
		["Ventas realizadas", Fmt.integer(s["sales"])],
		["Ganado en total", Fmt.money(s["earned"])],
		["Invertido", Fmt.money(s["invested"])],
	]
	for r in rows:
		_content.add_child(U.stat_row(r[0], r[1]))
