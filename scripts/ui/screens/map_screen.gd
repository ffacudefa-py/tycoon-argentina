class_name MapScreen
extends Control
## Sección MAPA: ciudad ficticia pixel art con zonas seleccionables y el
## panorama de las empresas rivales.

const TAG_NAMES := {
	"minorista": "comercio", "calle": "venta callejera", "comida": "comida", "bebida": "bebidas",
	"escolar": "escolar", "estudiantes": "estudiantes", "turismo": "turismo", "autos": "autos",
	"servicio": "servicios", "logistica": "logística", "salud": "salud",
}

var m: GameModel
var _map_holder: Control
var _zone_layer: Control
var _rivals_box: VBoxContainer
var _timer := 0.0


func _ready() -> void:
	m = Game.m
	var col := U.vbox(6)
	var sc := U.scroll(col)
	sc.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(sc)
	var head := U.hbox(4)
	head.add_child(U.icon("mapa"))
	head.add_child(U.label("Ciudad del Plata (ficticia)", U.SIZE_TITLE, U.TEXT_LIGHT, true))
	col.add_child(U.margin(head, 6, 6, 6, 0))
	col.add_child(U.margin(U.para("Tocá una zona para ver su demanda, competencia y negocios recomendados.", U.SIZE_SMALL, Color("c2c0d6")), 6, 0, 6, 0))
	_map_holder = Control.new()
	_map_holder.custom_minimum_size = Vector2(360, 540)
	_map_holder.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	var map := TextureRect.new()
	map.texture = U.tex("map/city_map.png")
	map.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	map.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_map_holder.add_child(map)
	_zone_layer = Control.new()
	_zone_layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	_zone_layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_map_holder.add_child(_zone_layer)
	col.add_child(_map_holder)
	_rivals_box = U.vbox(4)
	col.add_child(U.margin(_rivals_box, 6, 0, 6, 8))
	m.world_changed.connect(rebuild)
	m.stage_changed.connect(func(_s: int) -> void: rebuild())
	m.businesses_changed.connect(rebuild)
	rebuild()


func on_shown() -> void:
	rebuild()


func rebuild() -> void:
	U.clear(_zone_layer)
	for z in m.data.zones:
		_zone_layer.add_child(_zone_button(z))
	_build_rivals()


func _zone_button(z: Dictionary) -> Control:
	var r: Dictionary = z["map"]
	var holder := Control.new()
	holder.position = Vector2(r["x"], r["y"])
	holder.size = Vector2(r["w"], r["h"])
	holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var st := m.zone_status(z["id"])
	if not st["unlocked"]:
		var shade := ColorRect.new()
		shade.color = Color(0.1, 0.09, 0.17, 0.55)
		shade.set_anchors_preset(Control.PRESET_FULL_RECT)
		shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
		holder.add_child(shade)
	var frame := ReferenceRect.new()
	frame.border_color = Color("ffd85c") if st["unlocked"] else Color("8c8aa8")
	frame.border_width = 1
	frame.editor_only = false
	frame.set_anchors_preset(Control.PRESET_FULL_RECT)
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(frame)
	var b := Button.new()
	b.flat = true
	b.focus_mode = Control.FOCUS_NONE
	b.set_anchors_preset(Control.PRESET_FULL_RECT)
	for s in ["normal", "hover", "pressed", "focus", "hover_pressed"]:
		b.add_theme_stylebox_override(s, StyleBoxEmpty.new())
	var zid: String = z["id"]
	U.on_press(b, func() -> void: ZoneModal.open(zid))
	holder.add_child(b)
	var tag := U.panel("DarkCard" if st["unlocked"] else "SlateCard")
	tag.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var row := U.hbox(2)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if not st["unlocked"]:
		row.add_child(U.icon("candado"))
	var count := m.businesses_in_zone(zid).size()
	var short_name: String = (z["name"] as String).split(" ")[0] if (z["name"] as String).length() > 16 else z["name"]
	var l := U.label(short_name + ((" · %d" % count) if count > 0 else ""), 9, U.TEXT_LIGHT, true)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(l)
	tag.add_child(row)
	tag.position = Vector2(2, 2)
	holder.add_child(tag)
	return holder


func _build_rivals() -> void:
	U.clear(_rivals_box)
	var head := U.hbox(4)
	head.add_child(U.icon("bandera"))
	head.add_child(U.label("Empresas rivales", U.SIZE_TITLE, U.TEXT_LIGHT, true))
	_rivals_box.add_child(head)
	_rivals_box.add_child(U.para("Les quitan clientes a tus negocios de su rubro en sus zonas. Crecen más si competís en su terreno.", U.SIZE_SMALL, Color("c2c0d6")))
	for r in m.data.rivals:
		_rivals_box.add_child(rival_card(r["id"]))
	if not m.rival_log.is_empty():
		var log_card := U.panel("Card")
		var lv := U.vbox(2)
		log_card.add_child(lv)
		lv.add_child(U.label("Novedades del mercado", U.SIZE_SMALL, U.TEXT, true))
		for i in range(m.rival_log.size() - 1, maxi(-1, m.rival_log.size() - 6), -1):
			lv.add_child(U.para("• " + m.rival_log[i]["text"], 9, U.TEXT_SOFT))
		_rivals_box.add_child(log_card)


static func rival_card(rid: String) -> Control:
	var m := Game.m
	var r: Dictionary = m.data.rival_by_id[rid]
	var st: Dictionary = m.rivals[rid]
	var card := U.panel("Card")
	var col := U.vbox(2)
	card.add_child(col)
	var top := U.hbox(4)
	var n := U.label(r["name"], U.SIZE_SMALL, U.TEXT, true)
	n.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	n.clip_text = true
	top.add_child(n)
	var trend: String = ["▼", "=", "▲"][int(st.get("trend", 0)) + 1]
	top.add_child(U.label("Poder %d/10 %s" % [int(st["power"]), "baja" if trend == "▼" else ("sube" if trend == "▲" else "estable")], U.SIZE_SMALL, U.RED if int(st["power"]) >= 6 else U.TEXT_SOFT, true))
	col.add_child(top)
	var zones := []
	for z in r["zones"]:
		zones.append(m.data.zone_by_id[z]["name"])
	col.add_child(U.para("%s · %s · %s" % [r["sector"], r["behavior"], ", ".join(zones)], 9, U.TEXT_SOFT))
	var bar := U.progress("rojo", 6)
	bar.value = float(st["power"]) / 10.0
	col.add_child(bar)
	if str(st.get("last", "")) != "":
		col.add_child(U.para("Último movimiento: " + st["last"], 9, U.TEXT_SOFT))
	var presence := RivalSystem.presence(m, rid)
	var cd := float(st.get("cooldown", 0.0))
	var b := U.button("Campaña de marketing · " + Fmt.cost(RivalSystem.campaign_cost(m)), "violeta", "bandera", 24, 9)
	b.disabled = cd > 0.0 or int(st["power"]) <= 1
	if cd > 0.0:
		b.text = "Marketing descansa: " + Fmt.duration(cd)
	U.on_press(b, func() -> void: Main.instance.result(RivalSystem.campaign(m, rid)), "")
	col.add_child(b)
	if presence == 0:
		col.add_child(U.para("Hoy no compite con ninguno de tus negocios.", 9, U.TEXT_SOFT))
	return card
