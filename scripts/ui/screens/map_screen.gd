class_name MapScreen
extends Control
## Sección MAPA (10.0): la Argentina en dos niveles.
##   PAÍS    las 6 regiones con su avance de conquista; tocá una para entrar
##   REGIÓN  sus provincias con producto estrella y cuota; tocá una para su ficha
## Las regiones se abren en orden (NOA primero); las provincias, en cadena.

const TAG_NAMES := {
	"agro": "agro", "campo": "campo", "fabrica": "fábricas", "bebida": "bebidas", "vino": "vino",
	"turismo": "turismo", "fruta": "frutas", "ganaderia": "ganadería", "industria": "industria",
	"lacteo": "lácteos", "comida": "comida", "panaderia": "panadería", "infusion": "infusiones",
}

var m: GameModel
var region := ""                 ## "" = vista país
var _col: VBoxContainer
var _timer := 0.0
var _refreshers: Array[Callable] = []


func _ready() -> void:
	m = Game.m
	_col = U.vbox(6)
	var sc := U.scroll(U.margin(_col, 6, 6, 6, 8))
	sc.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(sc)
	m.world_changed.connect(rebuild)
	m.stage_changed.connect(func(_s: int) -> void: rebuild())
	m.businesses_changed.connect(rebuild)
	rebuild()


func on_shown() -> void:
	rebuild()


func _process(delta: float) -> void:
	_timer += delta
	if _timer >= 0.5 and is_visible_in_tree():
		_timer = 0.0
		for r in _refreshers:
			r.call()


func open_region(rid: String) -> void:
	region = rid
	rebuild()


func rebuild() -> void:
	if m != Game.m:
		m = Game.m
	U.clear(_col)
	_refreshers.clear()
	if region == "":
		_build_country()
	else:
		_build_region(m.data.region_by_id[region])


## Una región está abierta cuando la anterior está completa (la primera siempre).
func region_open(rid: String) -> bool:
	var idx := m.data.regions.find(m.data.region_by_id[rid])
	return idx <= 0 or ConquestSystem.region_complete(m, m.data.regions[idx - 1]["id"])


# ------------------------------------------------------------------- PAÍS

func _build_country() -> void:
	var head := U.hbox(4)
	head.add_child(U.icon("mapa"))
	var t := U.label("Conquistá la Argentina", U.SIZE_TITLE, U.TEXT_LIGHT, true)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(t)
	head.add_child(U.label("%d/%d" % [ConquestSystem.conquered_count(m), m.data.zones.size()], U.SIZE_BODY, U.GOLD, true))
	_col.add_child(head)
	_col.add_child(U.para("Dominá el mercado de cada provincia para conquistarla. Con la región completa ganás su producto estrella y se abre la siguiente.", U.SIZE_SMALL, Color("c2c0d6")))
	for r in m.data.regions:
		_col.add_child(_region_card(r))


func _region_card(r: Dictionary) -> Control:
	var rid: String = r["id"]
	var open := region_open(rid)
	var total := m.data.zones_in_region(rid).size()
	var done := ConquestSystem.conquered_in_region(m, rid)
	var card := U.panel("Card" if open else "InsetDark")
	var col := U.vbox(3)
	card.add_child(col)
	var top := U.hbox(6)
	top.add_child(U.icon("bandera" if open else "candado"))
	var n := U.label(r["long_name"], U.SIZE_BODY, U.TEXT if open else U.TEXT_LIGHT, true)
	n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	top.add_child(n)
	top.add_child(U.label("%d/%d" % [done, total], U.SIZE_SMALL, U.GOLD if done == total else (U.TEXT_SOFT if open else U.TEXT_LIGHT), true))
	col.add_child(top)
	col.add_child(U.para("Estrella: %s · +%d %% a todo al completarla" % [r["star_product"], int(round(float(r["bonus"]) * 100))], U.SIZE_SMALL, UiColors.GAIN if open else Color("c9c7da")))
	var bar := U.progress("verde", 6)
	bar.value = float(done) / maxf(1.0, float(total))
	col.add_child(bar)
	if not open:
		col.add_child(U.para("Se abre al conquistar la región anterior.", U.SIZE_SMALL, UiColors.LOSS_LIGHT))
	var b := Button.new()
	b.flat = true
	b.set_anchors_preset(Control.PRESET_FULL_RECT)
	b.mouse_filter = Control.MOUSE_FILTER_PASS
	b.disabled = not open
	U.on_press(b, open_region.bind(rid))
	var holder := Control.new()
	holder.add_child(card)
	card.set_anchors_preset(Control.PRESET_FULL_RECT)
	holder.custom_minimum_size.y = card.get_combined_minimum_size().y
	card.minimum_size_changed.connect(func() -> void: holder.custom_minimum_size.y = card.get_combined_minimum_size().y)
	holder.add_child(b)
	if Main.instance:
		Main.instance.register_target("region_" + rid, b)
	return holder


# ----------------------------------------------------------------- REGIÓN

func _build_region(r: Dictionary) -> void:
	var head := U.hbox(6)
	var back := U.icon_button("izquierda", "crema", 32)
	U.on_press(back, open_region.bind(""))
	head.add_child(back)
	var t := U.label(r["long_name"], U.SIZE_TITLE, U.TEXT_LIGHT, true)
	t.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	t.clip_text = true
	head.add_child(t)
	_col.add_child(head)
	_col.add_child(U.para("Estrella de la región: %s. Tocá una provincia para ver su mercado." % r["star_product"], U.SIZE_SMALL, Color("c2c0d6")))
	for z in m.data.zones_in_region(r["id"]):
		_col.add_child(_province_card(z))


func _province_card(z: Dictionary) -> Control:
	var zid: String = z["id"]
	var st := m.zone_status(zid)
	var unlocked: bool = st["unlocked"]
	var card := U.panel("Card" if unlocked or st["available"] else "InsetDark")
	var row := U.hbox(8)
	card.add_child(row)
	var badge := U.icon("", "businesses/%s_badge.png" % z["business"])
	badge.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(badge)
	var col := U.vbox(2)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(col)
	var top := U.hbox(4)
	var n := U.label(z["name"], U.SIZE_BODY, U.TEXT, true)
	n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	n.clip_text = true
	top.add_child(n)
	var tag := U.label("", U.SIZE_SMALL, U.TEXT_SOFT, true)
	top.add_child(tag)
	col.add_child(top)
	col.add_child(U.label(z["star_product"], U.SIZE_SMALL, UiColors.INFO, true))
	var bar := U.progress("amarillo", 6)
	col.add_child(bar)
	var upd := func() -> void:
		var sh := ConquestSystem.share(m, zid)
		bar.value = sh
		if ConquestSystem.is_conquered(m, zid):
			tag.text = "¡Conquistada!"
			tag.add_theme_color_override("font_color", UiColors.GAIN)
			bar.theme_type_variation = "Bar_verde"
		elif m.zones.has(zid):
			tag.text = "%d %%" % int(floorf(sh * 100.0))
		else:
			tag.text = "Disponible" if m.zone_status(zid)["available"] else "Bloqueada"
	upd.call()
	_refreshers.append(upd)
	var b := Button.new()
	b.flat = true
	b.mouse_filter = Control.MOUSE_FILTER_PASS
	U.on_press(b, func() -> void: ZoneModal.open(zid))
	var holder := Control.new()
	holder.add_child(card)
	card.set_anchors_preset(Control.PRESET_FULL_RECT)
	holder.custom_minimum_size.y = card.get_combined_minimum_size().y
	card.minimum_size_changed.connect(func() -> void: holder.custom_minimum_size.y = card.get_combined_minimum_size().y)
	b.set_anchors_preset(Control.PRESET_FULL_RECT)
	holder.add_child(b)
	return holder


## Ficha corta del rival de una provincia, con el botón de campaña.
static func rival_card(rid: String) -> Control:
	var m := Game.m
	var r: Dictionary = m.data.rival_by_id[rid]
	var st: Dictionary = m.rivals[rid]
	var card := U.panel("Inset")
	var col := U.vbox(3)
	card.add_child(col)
	var top := U.hbox(4)
	var n := U.label(r["name"], U.SIZE_SMALL, U.TEXT, true)
	n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	n.clip_text = true
	top.add_child(n)
	top.add_child(U.label("Poder %d/10" % int(st["power"]), U.SIZE_SMALL, U.RED if int(st["power"]) >= 6 else U.TEXT_SOFT, true))
	col.add_child(top)
	if str(st.get("last", "")) != "":
		col.add_child(U.para(st["last"], U.SIZE_SMALL, U.TEXT_SOFT))
	var cd := float(st.get("cooldown", 0.0))
	var b := UiColors.buy_button("CAMPAÑA", RivalSystem.campaign_cost(m), func() -> void: Main.instance.result(RivalSystem.campaign(m, rid)), 36)
	var why := ""
	if cd > 0.0:
		why = "Marketing descansa: " + Fmt.duration(cd)
	elif int(st["power"]) <= 1:
		why = "Ya está en su mínimo"
	UiColors.set_cost(b, RivalSystem.campaign_cost(m), why)
	col.add_child(b)
	return card
