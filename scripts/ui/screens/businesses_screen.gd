class_name BusinessesScreen
extends Control
## Sección NEGOCIOS: tus negocios (con su rendimiento) y el catálogo de los
## que podés abrir, con requisitos claros.

var m: GameModel
var _list: VBoxContainer
var _rows := {}      ## id -> {per_sec, bar, level, buy}
var _timer := 0.0


func _ready() -> void:
	m = Game.m
	_list = U.vbox(5)
	var sc := U.scroll(U.margin(_list, 6, 6, 6, 8))
	sc.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(sc)
	m.businesses_changed.connect(rebuild)
	m.stage_changed.connect(func(_s: int) -> void: rebuild())
	m.world_changed.connect(rebuild)
	rebuild()


func on_shown() -> void:
	rebuild()


func rebuild() -> void:
	U.clear(_list)
	_rows.clear()
	var owned := m.owned_ids()
	var head := U.hbox(4)
	head.add_child(U.icon("tienda"))
	var t := U.label("Tus negocios (%d/%d)" % [owned.size(), m.data.businesses.size()], U.SIZE_TITLE, U.TEXT_LIGHT, true)
	head.add_child(t)
	_list.add_child(head)
	for id in owned:
		_list.add_child(_owned_card(id))
	var locked_shown := 0
	var hidden := 0
	for def in m.data.businesses:
		if m.biz[def["id"]]["owned"]:
			continue
		if locked_shown < 3:
			if locked_shown == 0:
				_list.add_child(U.label("Próximos negocios", U.SIZE_TITLE, U.TEXT_LIGHT, true))
			_list.add_child(_locked_card(def["id"]))
			locked_shown += 1
		else:
			hidden += 1
	if hidden > 0:
		_list.add_child(U.para("Y %d negocios más que se revelan a medida que crece tu imperio." % hidden, U.SIZE_SMALL, Color("c2c0d6")))
	_refresh()


func _owned_card(id: String) -> Control:
	var def: Dictionary = m.data.business_by_id[id]
	var card := U.panel("Card")
	var row := U.hbox(6)
	card.add_child(row)
	row.add_child(U.badge_for(id))
	var col := U.vbox(2)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var top := U.hbox(4)
	var name := U.label(def["name"], U.SIZE_BODY, U.TEXT, true)
	name.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name.clip_text = true
	top.add_child(name)
	var lvl := U.label("", U.SIZE_SMALL, U.TEXT_SOFT, true)
	top.add_child(lvl)
	col.add_child(top)
	var info := U.label("", U.SIZE_SMALL, U.TEXT_SOFT)
	info.clip_text = true
	col.add_child(info)
	var bar := U.progress("verde", 6)
	col.add_child(bar)
	row.add_child(col)
	var btns := U.vbox(2)
	var see := U.button("Ver", "amarillo", "", 22, U.SIZE_SMALL)
	U.on_press(see, func() -> void: Main.instance.select_business(id))
	btns.add_child(see)
	var mg := U.button("Admin.", "celeste", "", 22, U.SIZE_SMALL)
	U.on_press(mg, func() -> void: ManageBusinessModal.open(id))
	btns.add_child(mg)
	row.add_child(btns)
	_rows[id] = {"level": lvl, "info": info, "bar": bar}
	return card


func _locked_card(id: String) -> Control:
	var def: Dictionary = m.data.business_by_id[id]
	var st := m.unlock_status(id)
	var card := U.panel("Card" if st["available"] else "SlateCard")
	var col := U.vbox(4)
	card.add_child(col)
	var row := U.hbox(6)
	var badge := U.badge_for(id)
	if not st["available"]:
		badge.modulate = Color(0.45, 0.45, 0.55)
	row.add_child(badge)
	var txt := U.vbox(1)
	txt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var dark: bool = not st["available"]
	txt.add_child(U.label(def["name"], U.SIZE_BODY, U.TEXT_LIGHT if dark else U.TEXT, true))
	txt.add_child(U.para(def["description"], 9, Color("c2c0d6") if dark else U.TEXT_SOFT))
	row.add_child(txt)
	col.add_child(row)
	var products := []
	for p in def["products"]:
		products.append(p["name"])
	col.add_child(U.para("Vende: " + ", ".join(products) + ". Ciclo de %s." % Fmt.cycle(def["cycle"]), 9, Color("c2c0d6") if dark else U.TEXT_SOFT))
	for r in st["reasons"]:
		var rr := U.hbox(3)
		rr.add_child(U.icon("candado"))
		rr.add_child(U.label("Requiere: " + r, U.SIZE_SMALL, Color("f07c6c"), true))
		col.add_child(rr)
	var buy := U.button("Abrir por " + Fmt.cost(st["cost"]), "verde", "tienda", 30)
	buy.disabled = not st["available"] or not st["affordable"]
	U.on_press(buy, func() -> void: BuyBusinessModal.open(id), "")
	col.add_child(buy)
	_rows[id] = {"buy": buy}
	return card


func _process(delta: float) -> void:
	if not is_visible_in_tree():
		return
	_timer += delta
	if _timer >= 0.5:
		_timer = 0.0
		_refresh()


func _refresh() -> void:
	for id in _rows:
		var r: Dictionary = _rows[id]
		if r.has("buy"):
			var st := m.unlock_status(id)
			r["buy"].disabled = not st["available"] or not st["affordable"]
			continue
		var d := m.derive(id)
		var s: Dictionary = m.biz[id]
		r["level"].text = "Nv %d" % int(s["level"])
		var state := "auto" if d["auto_sell"] else "manual"
		if not m.has_stock(id) and s["orders"].is_empty():
			state = "¡sin stock!"
		r["info"].text = "%s · %s · %s" % [Fmt.per_sec(d["profit_sec"]), state, m.data.zone_by_id[s["zone"]]["name"]]
		r["bar"].value = float(s["progress"]) / float(d["cycle"]) if s["running"] else 0.0
