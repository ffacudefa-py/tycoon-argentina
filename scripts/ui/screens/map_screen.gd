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
var _region_holder: Control      ## mapa de la región (se escala en el zoom)
var _pins := {}                  ## bid -> BusinessPin
var _transitioning := false
var _quiet_pins := false         ## vuelta del zoom: los pines no repiten la entrada
const SHORT := {"santiago_del_estero": "Sgo. del Estero", "caba": "CABA", "tierra_del_fuego": "T. del Fuego",
	"buenos_aires": "Bs. As.", "entre_rios": "E. Ríos"}
const ZOOM := 3.0                ## escala entera: el pixel art queda nítido al final
static var _layout := {}
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
	var back := Main.instance != null and not Main.instance.zoom_return.is_empty()
	if back:
		region = Main.instance.zoom_return["region"]
		_quiet_pins = true                         # los pines ya están: sin entrada escalonada
	rebuild()
	_quiet_pins = false
	if back:
		_transitioning = true                      # nada rearma el mapa hasta el zoom inverso
		zoom_back.call_deferred()


func _process(delta: float) -> void:
	_timer += delta
	if _timer >= 0.5 and is_visible_in_tree():
		_timer = 0.0
		for r in _refreshers:
			r.call()


func open_region(rid: String) -> void:
	region = rid
	rebuild()


var _pending_rebuild := false


func rebuild() -> void:
	# Oculta no se rearma: on_shown() la reconstruye al mostrarla.
	if not is_visible_in_tree():
		return
	if _transitioning:
		_pending_rebuild = true
		return
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
	_col.add_child(U.para("Ganá el 100 % del mercado de cada provincia. Región completa → producto estrella y se abre la siguiente.", U.SIZE_SMALL, Color("f0dcc0")))
	var lay: Dictionary = layout()["country"]
	var shades := {}
	var labels := {}
	for r in m.data.regions:
		var rid: String = r["id"]
		var done := ConquestSystem.conquered_in_region(m, rid)
		var total := m.data.zones_in_region(rid).size()
		shades[rid] = _shade(not region_open(rid), done == total, false)
		labels[rid] = "%s %d/%d" % [r["name"], done, total]
	var groups := {}
	for i in (lay["ids"] as Array).size():
		groups[i + 1] = m.data.zone_by_id[lay["ids"][i]]["region"]
	_col.add_child(_map_view("map/argentina.png", "map/argentina_mask.png", "map/argentina_%s.png", shades, labels, lay["region_centers"], groups,
		func(rid: String) -> void:
			if region_open(rid):
				open_region(rid)
			else:
				Main.instance.toast("Se abre al conquistar la región anterior.", "info")))
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
	col.add_child(U.para("Estrella: %s · +%d %% a todo al completarla" % [r["star_product"], int(round(float(r["bonus"]) * 100))], U.SIZE_SMALL, UiColors.GAIN if open else Color("f0dcc0")))
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
	_col.add_child(U.label("Estrella: %s" % r["star_product"], U.SIZE_BODY, Color("fff6e6"), true))
	var lay: Dictionary = layout()["regions"][r["id"]]
	var shades := {}
	var labels := {}
	var groups := {}
	for i in (lay["ids"] as Array).size():
		var zid: String = lay["ids"][i]
		groups[i + 1] = zid
		var st := m.zone_status(zid)
		shades[zid] = _shade(not st["unlocked"] and not st["available"], st["conquered"], not st["unlocked"] and st["available"])
		# el estado lo dicen los pines; el rótulo es sólo el nombre (corto)
		labels[zid] = SHORT.get(zid, m.data.zone_by_id[zid]["name"])
	var holder := _map_view("map/region_%s.png" % r["id"], "map/region_%s_mask.png" % r["id"], "map/region_" + r["id"] + "_%s.png", shades, labels, lay["centers"], groups,
		func(zid: String) -> void: ZoneModal.open(zid))
	_col.add_child(holder)
	_region_holder = holder
	_add_route(holder, lay)
	_add_pins(holder, lay)
	var leg := _legend()                           # arriba del mapa: ningún aviso la tapa
	_col.add_child(leg)
	_col.move_child(leg, holder.get_index())
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


# ------------------------------------------------- negocios en el mapa (11)

func _pin_state(zid: String) -> int:
	var st := m.zone_status(zid)
	if st["unlocked"]:
		return BusinessPin.State.OPEN
	return BusinessPin.State.AVAILABLE if st["available"] else BusinessPin.State.LOCKED


## Leyenda de los tres estados (ícono + una palabra).
func _legend() -> Control:
	var row := U.hbox(10)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	for it in [["check", "Abierto", Color("9cf0b0")], ["mas", "Disponible", Color("9cf0b0")], ["candado", "Bloqueado", Color("f0dcc0")]]:
		var h := U.hbox(3)
		h.add_child(U.icon(it[0]))
		h.add_child(U.label(it[1], U.SIZE_SMALL, it[2], true))
		row.add_child(h)
	return row


## Ruta de conquista: puntitos animados entre las provincias en orden.
func _add_route(holder: Control, lay: Dictionary) -> void:
	var pts := []
	for zid in lay["ids"]:
		if lay["centers"].has(zid):
			var c: Array = lay["centers"][zid]
			pts.append(Vector2(float(c[0]), float(c[1]) - 26.0))
	var route := RouteDots.new()
	route.points = pts
	route.set_anchors_preset(Control.PRESET_FULL_RECT)
	route.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(route)
	for i in holder.get_child_count():             # debajo de rótulos y pines
		if holder.get_child(i) is Label:
			holder.move_child(route, i)
			break


func _add_pins(holder: Control, lay: Dictionary) -> void:
	_pins.clear()
	var seen: Dictionary = m.engage.get("seen_open", {})
	var i := 0
	for zid in lay["ids"]:
		if not lay["centers"].has(zid):
			continue
		var bid: String = m.data.zone_by_id[zid]["business"]
		var state := _pin_state(zid)
		var pin := BusinessPin.new()
		pin.setup(bid, zid, BusinessPin.State.LOCKED if (state != BusinessPin.State.LOCKED and not seen.has(zid)) else state)
		var c: Array = lay["centers"][zid]
		pin.position = Vector2(float(c[0]) - BusinessPin.SIZE / 2.0, float(c[1]) - BusinessPin.SIZE - 10.0)
		holder.add_child(pin)
		pin.picked.connect(_on_pin)
		_pins[bid] = pin
		if state != BusinessPin.State.LOCKED and not seen.has(zid):
			pin.play_unlock(state, 0.35 + i * 0.12)      # recién desbloqueado
			seen[zid] = true
		elif not _quiet_pins:
			pin.play_enter(i * 0.07)
		i += 1
	m.engage["seen_open"] = seen


func _on_pin(pin: BusinessPin) -> void:
	if _transitioning:
		return
	match pin.state:
		BusinessPin.State.OPEN:
			zoom_into(pin)
		BusinessPin.State.AVAILABLE:
			ZoneModal.open(pin.zid)
		_:
			var reqs := m.requirements_for_business(pin.bid)
			var why: String = "Todavía no está disponible."
			if not reqs.is_empty():
				var t: String = reqs[0]["text"]
				why = "Primero " + t.substr(0, 1).to_lower() + t.substr(1)
			pin.show_hint(why)


## Oscurecido de la transición: sólo sobre el contenido (la barra superior y la
## de pestañas quedan fijas) y bloquea los toques mientras dura.
func _fade() -> ColorRect:
	var layer := Control.new()
	layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(layer)
	# bloqueo transparente de TODA la pantalla (pestañas y barra superior incluidas)
	var block_layer := CanvasLayer.new()
	block_layer.layer = 30
	var block := ColorRect.new()
	block.color = Color(0, 0, 0, 0)
	block.set_anchors_preset(Control.PRESET_FULL_RECT)
	block.mouse_filter = Control.MOUSE_FILTER_STOP
	block_layer.add_child(block)
	layer.add_child(block_layer)
	var r := ColorRect.new()
	r.color = Color("2a160c")
	r.modulate.a = 0.0
	r.set_anchors_preset(Control.PRESET_FULL_RECT)
	r.mouse_filter = Control.MOUSE_FILTER_STOP        # nadie interrumpe la transición
	layer.add_child(r)
	return r


## Zoom al negocio (650 ms): la cámara se acerca, el resto se oscurece y
## aparece la fachada en Imperio con un leve acercamiento.
func zoom_into(pin: BusinessPin) -> void:
	var bid := pin.bid
	if BusinessPin.reduced() or _region_holder == null:
		Main.instance.select_business(bid)
		return
	_transitioning = true
	if is_instance_valid(BusinessPin._hint):          # el globito no viaja con el zoom
		BusinessPin._hint.queue_free()
	var fade := _fade()
	var h := _region_holder
	_set_labels(false)
	h.pivot_offset = pin.position + Vector2(BusinessPin.SIZE / 2.0, BusinessPin.SIZE / 2.0)
	Sfx.play("whoosh", 0.9)
	var base_pos := h.position
	var center_shift := h.size / 2.0 - h.pivot_offset       # el negocio termina en el centro
	var tw := h.create_tween().set_parallel(true)
	# escala en saltos enteros (1 → 2 → 3): el pixel art nunca se deforma
	tw.tween_method(func(v: float) -> void: h.scale = Vector2.ONE * minf(ZOOM, floorf(v)), 1.0, ZOOM + 0.99, 0.42)
	tw.tween_property(h, "position", base_pos + center_shift, 0.42).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(fade, "modulate:a", 0.85, 0.3).set_trans(Tween.TRANS_SINE)
	tw.chain().tween_callback(func() -> void:
		Main.instance.zoom_return = {"region": region, "bid": bid}
		Main.instance.select_business(bid)
		h.scale = Vector2.ONE
		h.position = base_pos
		_set_labels(true)
		var empire := Main.instance.find_children("*", "EmpireScreen", true, false)
		if not empire.is_empty():
			empire[0].play_arrive()
		var tw2 := fade.create_tween()
		tw2.tween_property(fade, "modulate:a", 0.0, 0.25).set_trans(Tween.TRANS_SINE)
		tw2.tween_callback(func() -> void:
			fade.get_parent().queue_free()
			_transitioning = false
			if _pending_rebuild:
				_pending_rebuild = false
				rebuild()))


## Vuelta de la fachada al mapa: zoom inverso desde el negocio.
func zoom_back() -> void:
	var ret: Dictionary = Main.instance.zoom_return
	Main.instance.zoom_return = {}
	if ret.is_empty():
		return
	var pin: BusinessPin = _pins.get(ret["bid"])
	if pin == null or BusinessPin.reduced() or _region_holder == null:
		_transitioning = false
		return
	_transitioning = true
	var fade := _fade()
	fade.modulate.a = 0.85
	var h := _region_holder
	h.pivot_offset = pin.position + Vector2(BusinessPin.SIZE / 2.0, BusinessPin.SIZE / 2.0)
	await get_tree().process_frame               # que el contenedor ubique el mapa
	h.pivot_offset = pin.position + Vector2(BusinessPin.SIZE / 2.0, BusinessPin.SIZE / 2.0)
	var base_pos := h.position
	h.scale = Vector2.ONE * ZOOM
	h.position = base_pos + (h.size / 2.0 - h.pivot_offset)
	_set_labels(false)
	var tw := h.create_tween().set_parallel(true)
	tw.tween_method(func(v: float) -> void: h.scale = Vector2.ONE * maxf(1.0, ceilf(v)), ZOOM, 0.01, 0.5)
	tw.tween_property(h, "position", base_pos, 0.5).set_trans(Tween.TRANS_CUBIC).set_ease(Tween.EASE_IN_OUT)
	tw.tween_property(fade, "modulate:a", 0.0, 0.45).set_trans(Tween.TRANS_SINE)
	tw.chain().tween_callback(func() -> void:
		_set_labels(true)
		fade.get_parent().queue_free()
		_transitioning = false
		if _pending_rebuild:
			_pending_rebuild = false
			rebuild())


func _set_labels(on: bool) -> void:
	if _region_holder == null:
		return
	for c in _region_holder.get_children():
		if c is Label:
			c.visible = on



static func layout() -> Dictionary:
	if _layout.is_empty():
		_layout = JSON.parse_string(FileAccess.get_file_as_string("res://data/map_layout.json"))
	return _layout


## Tinte de la silueta: bloqueada oscura, conquistada dorada, disponible clara.
func _shade(locked: bool, conquered: bool, available: bool) -> Color:
	if conquered:
		return Color(1.0, 0.82, 0.25, 0.45)
	if locked:
		return Color(0.04, 0.03, 0.1, 0.5)
	if available:
		return Color(1, 1, 1, 0.22)
	return Color(1, 1, 1, 0.0)


## Mapa tocable: base + siluetas teñidas + rótulos. Al tocar, la máscara
## (canal R = índice) dice qué región o provincia se tocó (groups: índice -> id).
func _map_view(base: String, mask_path: String, sil_fmt: String, shades: Dictionary, labels: Dictionary,
		centers: Dictionary, groups: Dictionary, on_pick: Callable) -> Control:
	var tex := U.tex(base)
	var holder := Control.new()
	holder.custom_minimum_size = tex.get_size()
	holder.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	var bg := TextureRect.new()
	bg.texture = tex
	bg.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	holder.add_child(bg)
	for id in shades:
		var sil := TextureRect.new()
		sil.texture = U.tex(sil_fmt % id)
		sil.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		sil.modulate = shades[id]
		sil.mouse_filter = Control.MOUSE_FILTER_IGNORE
		holder.add_child(sil)
	for id in labels:
		if not centers.has(id):
			continue
		var l := U.label(labels[id], U.SIZE_SMALL, Color("fff6e6"), true, HORIZONTAL_ALIGNMENT_CENTER)
		l.add_theme_color_override("font_outline_color", Color("3d1b0b"))
		l.add_theme_constant_override("outline_size", 4)
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var plate := StyleBoxFlat.new()                # plaquita: el nombre se lee siempre
		plate.bg_color = Color(0.24, 0.11, 0.04, 0.55)
		plate.set_corner_radius_all(3)
		plate.content_margin_left = 3
		plate.content_margin_right = 3
		l.add_theme_stylebox_override("normal", plate)
		holder.add_child(l)
		l.reset_size()
		var c: Array = centers[id]
		var w := l.get_combined_minimum_size().x
		l.position = Vector2(clampf(float(c[0]) - w / 2.0, 0.0, tex.get_width() - w), float(c[1]) - 9.0).round()
	_separate_labels(holder, tex.get_width())
	var mask_img: Image = U.tex(mask_path).get_image()
	var b := Button.new()
	b.flat = true
	b.focus_mode = Control.FOCUS_NONE
	b.mouse_filter = Control.MOUSE_FILTER_PASS
	b.set_anchors_preset(Control.PRESET_FULL_RECT)
	b.add_theme_stylebox_override("hover", StyleBoxEmpty.new())
	b.add_theme_stylebox_override("pressed", StyleBoxEmpty.new())
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	# La posición sale del propio evento de toque (en Android el mouse emulado
	# no siempre actualiza la posición antes del clic).
	var last := {"p": Vector2.ZERO}
	b.gui_input.connect(func(ev: InputEvent) -> void:
		if ev is InputEventMouseButton and ev.button_index == MOUSE_BUTTON_LEFT:
			last["p"] = ev.position)
	U.on_press(b, func() -> void:
		var id := pick(mask_img, last["p"], groups)
		if id != "":
			on_pick.call(id))
	holder.add_child(b)
	holder.set_meta("pick_button", b)
	return holder


## Pasada simple: si dos rótulos se pisan, baja el segundo; nunca fuera del mapa.
static func _separate_labels(holder: Control, width: int) -> void:
	var labels := holder.get_children().filter(func(n: Node) -> bool: return n is Label)
	for i in labels.size():
		var a: Label = labels[i]
		a.position.x = clampf(a.position.x, 2.0, width - a.size.x - 2.0)
		for j in i:
			var b: Label = labels[j]
			var ra := Rect2(a.position, a.size).grow(1)
			var rb := Rect2(b.position, b.size)
			if ra.intersects(rb):
				a.position.y = rb.end.y + 2.0


## Id de lo que hay en el punto p de la máscara ("" si es mar). Si se toca el
## borde, busca el píxel más cercano en un radio chico (dedos gordos).
static func pick(mask: Image, p: Vector2, groups: Dictionary) -> String:
	var w := mask.get_width()
	var h := mask.get_height()
	for r: int in [0, 2, 4, 6]:
		for off: Vector2i in [Vector2i(0, 0), Vector2i(r, 0), Vector2i(-r, 0), Vector2i(0, r), Vector2i(0, -r)]:
			var q: Vector2i = Vector2i(int(p.x), int(p.y)) + off
			if q.x < 0 or q.y < 0 or q.x >= w or q.y >= h:
				continue
			var idx := int(round(mask.get_pixelv(q).r * 255.0))
			if idx > 0 and groups.has(idx):
				return groups[idx]
	return ""


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
