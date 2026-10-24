class_name BusinessScene
extends Control
## Escena pixel art del negocio seleccionado. Dos vistas:
##
## - INTERIOR (por defecto): corte del local hecho con PXL (pared, piso y
##   muebles según el rubro y el nivel), empleados en sus puestos de trabajo
##   (data/interiors.json), mostradores en primer plano, animaciones del
##   ambiente (humo, vapor, neón, TV...) y clientes que entran y hacen fila.
## - FACHADA: la calle de la zona con el edificio del negocio y peatones.
##
## Todo es DECORATIVO: la cantidad de clientes sigue las ventas reales, pero
## nada de esto calcula la economía. Con calidad baja o "animaciones del
## escenario" desactivadas se reducen los personajes y se congelan los efectos.

const H := 170
## Fachada: el arte de la calle mide 480x200 y se recorta el cielo.
const ART_H := 200
const BG_W := 480
const BUILDING_BASE_Y := 168
const WALK_Y := 178
## Calzada de la calle (asfalto entre y=186 y 200 del arte): el colectivo apoya
## las ruedas acá y se dibuja DELANTE del negocio y de los peatones.
const ROAD_Y := 198
const BUS_SPEED := 110.0
const WORKER_Y := 171
## Interior: lienzo 400x170.
const INT_W := 400
const CHAR_W := 32
const CHAR_FEET := 46
const MAX_WALKERS := [2, 5, 8]

static var _interiors := {}

var bid := ""
## Vista elegida en Configuración; `view` es la que se muestra de verdad
## (los niveles sin local cerrado siempre se ven desde la calle).
var preferred_view := "interior"
var view := "interior"
var _world: Node2D
var _bg: Sprite2D
var _building: Sprite2D
var _int_back: Sprite2D
var _int_front: Sprite2D
var _fx_layer: Node2D
var _people: Node2D
var _customers: Node2D
var _workers: Array = []          ## [{sprite, station}]
var _walkers: Array = []
var _fx: Array = []               ## [{sprite, durations, t}]
var _bus: Sprite2D
var _bus_t := 12.0
var _spawn_t := 0.0
var _anim_t := 0.0
var _last_tier := -1
var _last_float := 0
var _closed: Label


func _init() -> void:
	custom_minimum_size.y = H
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	_world = Node2D.new()
	add_child(_world)
	_bg = _sprite(_world)
	_building = _sprite(_world)
	_int_back = _sprite(_world)
	_fx_layer = Node2D.new()
	_world.add_child(_fx_layer)
	_people = Node2D.new()
	_world.add_child(_people)
	_int_front = _sprite(_world)
	_customers = Node2D.new()
	_world.add_child(_customers)
	_bus = _sprite(_world)
	_bus.texture = U.tex("effects/colectivo_anim.png")
	if _bus.texture:
		_bus.hframes = 2
	_bus.visible = false
	resized.connect(_layout)
	preferred_view = str(Settings.get_value("scene_view"))
	view = preferred_view
	var m := Game.m
	m.business_changed.connect(_on_business_changed)
	m.sale.connect(_on_sale)
	m.businesses_changed.connect(refresh)
	Settings.changed.connect(_on_setting)


func _sprite(parent: Node) -> Sprite2D:
	var s := Sprite2D.new()
	s.centered = false
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	parent.add_child(s)
	return s


func _on_business_changed(id: String) -> void:
	if id == bid:
		refresh()


func _on_setting(key: String, _v: Variant) -> void:
	if key == "scene_view":
		set_view(str(Settings.get_value("scene_view")))


## ¿El nivel visual tiene local con interior? La mesita, el carrito y el
## lavadero a cielo abierto no: ahí no se puede cambiar a "adentro".
static func has_interior(id: String, tier: int) -> bool:
	var tiers: Array = interiors_data().get("businesses", {}).get(id, [])
	if tier < 0 or tier >= tiers.size():
		return true
	return bool(tiers[tier].get("has_interior", true))


static func interiors_data() -> Dictionary:
	if _interiors.is_empty():
		var f := FileAccess.open("res://data/interiors.json", FileAccess.READ)
		if f:
			var d = JSON.parse_string(f.get_as_text())
			if d is Dictionary:
				_interiors = d
	return _interiors


func set_business(id: String) -> void:
	if id == bid:
		return
	bid = id
	_last_tier = -1
	_clear_walkers()
	refresh()


func set_view(v: String) -> void:
	preferred_view = v
	refresh()


func _clear_walkers() -> void:
	for w in _walkers:
		w["sprite"].queue_free()
	_walkers.clear()


func refresh() -> void:
	if bid == "" or not is_inside_tree():
		return
	var m := Game.m
	var s: Dictionary = m.biz[bid]
	var d := m.derive(bid)
	var tier: int = d["tier"]
	var shown := preferred_view if has_interior(bid, tier) else "fachada"
	if shown != view:
		view = shown
		_clear_walkers()
	var interior := view == "interior"
	_bg.visible = not interior
	_building.visible = not interior
	_int_back.visible = interior
	_int_front.visible = interior
	_bus.visible = false
	if interior:
		_int_back.texture = U.tex("interiors/%s_%d_back.png" % [bid, tier])
		_int_front.texture = U.tex("interiors/%s_%d_front.png" % [bid, tier])
	else:
		var loc := "locations/street_%s.png" % s["zone"]
		_bg.texture = U.tex(loc) if ResourceLoader.exists(U.PA + loc) else U.tex("backgrounds/street_%s.png" % s["zone"])
		_building.texture = U.tex("businesses/%s_%d.png" % [bid, tier])
		_building.hframes = 2 if _building.texture and _building.texture.get_width() >= 384 else 1
	if _last_tier >= 0 and tier > _last_tier:
		_tier_flash()
	_last_tier = tier
	_rebuild_fx(tier)
	_rebuild_workers(tier)
	_closed_sign(s.get("closed", false))
	_layout()


func _tier_info(tier: int) -> Dictionary:
	var all: Dictionary = interiors_data().get("businesses", {})
	var tiers: Array = all.get(bid, [])
	return tiers[tier] if tier < tiers.size() else {"stations": [], "queue": [], "fx": []}


func _origin_x() -> float:
	return floor((size.x - INT_W) / 2.0)


func _layout() -> void:
	var w := size.x
	if view == "interior":
		_world.position = Vector2.ZERO
		_int_back.position = Vector2(_origin_x(), 0)
		_int_front.position = _int_back.position
	else:
		_world.position = Vector2(0, H - ART_H)
		_bg.position = Vector2(floor((w - BG_W) / 2.0), 0)
		_building.position = Vector2(floor(w / 2.0) - 96, BUILDING_BASE_Y - 149)
	_place_workers()
	_place_fx()


# ---------------------------------------------------------------- empleados

func _rebuild_workers(tier: int) -> void:
	for wk in _workers:
		wk["sprite"].queue_free()
	_workers.clear()
	var team := Game.m.employees_of(bid)
	var shown := []
	if team.is_empty():
		shown.append({"variant": 0})          # sin empleados atiende el dueño (vos)
	else:
		for e in team:
			shown.append({"variant": int(e["variant"]), "role": e["role"]})
	var stations: Array = _tier_info(tier).get("stations", [])
	var limit: int = stations.size() if view == "interior" else 4
	for i in mini(shown.size(), maxi(1, limit)):
		var sp := _sprite(_people)
		sp.texture = U.tex("characters/worker_%d.png" % shown[i]["variant"])
		sp.hframes = 10
		sp.frame = 4
		var st: Dictionary = stations[i] if i < stations.size() else {}
		sp.flip_h = bool(st.get("flip", false))
		_workers.append({"sprite": sp, "station": st, "index": i})
	_place_workers()


func _place_workers() -> void:
	var w := size.x
	for wk in _workers:
		var sp: Sprite2D = wk["sprite"]
		if view == "interior" and not wk["station"].is_empty():
			var st: Dictionary = wk["station"]
			sp.position = Vector2(_origin_x() + float(st["x"]) - CHAR_W / 2, float(st["y"]) - CHAR_FEET)
		else:
			var off: int = [-44, 40, -78, 74][int(wk["index"]) % 4]
			sp.position = Vector2(floor(w / 2.0) + off - CHAR_W / 2, WORKER_Y - CHAR_FEET)


# ---------------------------------------------------------------- efectos

func _rebuild_fx(tier: int) -> void:
	for f in _fx:
		f["sprite"].queue_free()
	_fx.clear()
	if view != "interior":
		return
	for e in _tier_info(tier).get("fx", []):
		var path := "effects/%s.png" % e["anim"]
		var tex := U.tex(path)
		if tex == null:
			continue
		var meta := {"frames": 1, "durations_ms": [100]}
		var jf := FileAccess.open(U.PA + "effects/%s.json" % e["anim"], FileAccess.READ)
		if jf:
			var parsed = JSON.parse_string(jf.get_as_text())
			if parsed is Dictionary:
				meta = parsed
		var sp := _sprite(_fx_layer)
		sp.texture = tex
		sp.hframes = maxi(1, int(meta["frames"]))
		_fx.append({"sprite": sp, "x": float(e["x"]), "y": float(e["y"]), "durations": meta["durations_ms"], "t": randf() * 0.5, "frame": 0})
	_place_fx()


func _place_fx() -> void:
	for f in _fx:
		f["sprite"].position = Vector2(_origin_x() + f["x"], f["y"])


func _animate_fx(delta: float) -> void:
	if Settings.fx_level() == 0 or not Settings.get_value("scene_anim"):
		return
	for f in _fx:
		var durs: Array = f["durations"]
		f["t"] = float(f["t"]) + delta
		var cur: int = f["frame"]
		if f["t"] * 1000.0 >= float(durs[cur % durs.size()]):
			f["t"] = 0.0
			f["frame"] = (cur + 1) % maxi(1, durs.size())
			f["sprite"].frame = f["frame"]


# ---------------------------------------------------------------- bucle

func _process(delta: float) -> void:
	if bid == "" or not is_visible_in_tree():
		return
	var m := Game.m
	var d := m.derive(bid)
	var s: Dictionary = m.biz[bid]
	_anim_t += delta
	var tick := int(_anim_t / 0.25)
	var anim_on := Settings.fx_level() > 0 and bool(Settings.get_value("scene_anim"))
	if _building.visible and _building.hframes > 1:
		_building.frame = int(_anim_t * 2.5) % 2 if anim_on else 0
	var busy: bool = s["running"] or (d["auto_sell"] and m.has_stock(bid))
	for wk in _workers:
		var i: int = wk["index"]
		wk["sprite"].frame = (6 + (tick + i) % 2) if busy else (4 + int(_anim_t / 0.8 + i) % 2)
	_animate_fx(delta)
	_update_bus(delta, anim_on)

	# Clientes: frecuencia según ventas reales por segundo (sólo visual).
	var level := Settings.fx_level()
	var max_w: int = MAX_WALKERS[level] if anim_on else 1
	var rate := 0.08
	if s.get("closed", false):
		rate = 0.0
	elif d["auto_sell"] and m.has_stock(bid):
		rate = clampf(1.0 / float(d["cycle"]), 0.15, 0.8)
	elif s["running"]:
		rate = 0.6
	_spawn_t += delta * rate
	if _spawn_t >= 1.0 and _walkers.size() < max_w:
		_spawn_t = 0.0
		_spawn_walker()
	_update_walkers(delta)


func _spawn_walker() -> void:
	var w := size.x
	var parent: Node2D = _customers if view == "interior" else _people
	var sp := _sprite(parent)
	sp.texture = U.tex("characters/customer_%d.png" % (randi() % 8))
	sp.hframes = 10
	var dir := 1.0 if randf() < 0.5 else -1.0
	var y: float
	var stop_x: float
	if view == "interior":
		var q: Array = _tier_info(_last_tier).get("queue", [[INT_W / 2, 164]])
		var spot: Array = q[randi() % q.size()]
		y = float(spot[1]) - CHAR_FEET + randi() % 3
		stop_x = _origin_x() + float(spot[0]) - CHAR_W / 2 + randf_range(-10, 10)
	else:
		y = WALK_Y - CHAR_FEET + randi() % 3
		stop_x = floor(w / 2.0) + randf_range(-30, 30) - CHAR_W / 2
	sp.position = Vector2(-float(CHAR_W) if dir > 0 else w, y)
	sp.flip_h = dir < 0
	_walkers.append({"sprite": sp, "dir": dir, "speed": randf_range(26, 40), "state": "walk", "stop_x": stop_x, "t": 0.0, "shop": randf() < 0.8})


func _update_walkers(delta: float) -> void:
	var w := size.x
	for i in range(_walkers.size() - 1, -1, -1):
		var wk: Dictionary = _walkers[i]
		var sp: Sprite2D = wk["sprite"]
		wk["t"] = float(wk["t"]) + delta
		match wk["state"]:
			"walk":
				sp.position.x += float(wk["dir"]) * float(wk["speed"]) * delta
				sp.frame = int(float(wk["t"]) * 8.0) % 4
				var passed: bool = (wk["dir"] > 0 and sp.position.x >= wk["stop_x"]) or (wk["dir"] < 0 and sp.position.x <= wk["stop_x"])
				if wk["shop"] and passed:
					wk["state"] = "shop"
					wk["t"] = 0.0
					sp.flip_h = false if view == "interior" else sp.flip_h
			"shop":
				sp.frame = 4 + int(float(wk["t"]) * 2.0) % 2
				if float(wk["t"]) > randf_range(1.0, 2.0):
					wk["state"] = "leave"
					wk["shop"] = false
					sp.flip_h = float(wk["dir"]) < 0
			"leave":
				sp.position.x += float(wk["dir"]) * float(wk["speed"]) * delta
				sp.frame = int(float(wk["t"]) * 8.0) % 4
		sp.position.x = round(sp.position.x)
		if sp.position.x < -CHAR_W - 4 or sp.position.x > w + 4:
			sp.queue_free()
			_walkers.remove_at(i)


## Colectivo que pasa por la calle cada tanto (sólo en la vista de fachada).
func _update_bus(delta: float, anim_on: bool) -> void:
	if view == "interior" or not anim_on or _bus.texture == null:
		_bus.visible = false
		return
	if not _bus.visible:
		_bus_t -= delta
		if _bus_t <= 0.0:
			_bus.visible = true
			_bus.position = Vector2(size.x + 10, ROAD_Y - _bus.texture.get_height())
		return
	_bus.position.x = round(_bus.position.x - BUS_SPEED * delta)
	_bus.frame = int(_anim_t * 6.0) % 2
	if _bus.position.x < -float(_bus.texture.get_width()) / _bus.hframes - 10:
		_bus.visible = false
		_bus_t = randf_range(20.0, 40.0)


func _on_sale(id: String, revenue: int) -> void:
	if id != bid or not is_visible_in_tree() or Main.instance == null:
		return
	var center := get_global_rect().position + Vector2(size.x / 2.0, 60)
	if view == "interior":
		var q: Array = _tier_info(_last_tier).get("queue", [])
		if not q.is_empty():
			center = get_global_rect().position + Vector2(_origin_x() + float(q[0][0]), 96)
	var now := Time.get_ticks_msec()
	if now - _last_float > 350:
		_last_float = now
		Main.instance.fx.coin_burst(center, 2)
		Main.instance.fx.float_text(center + Vector2(randf_range(-20, 20), -10), "+" + Fmt.money(revenue))
		# Las monedas vuelan al saldo; el "clinc" suena cuando llegan.
		var bar := Main.instance.top_bar
		Main.instance.fx.coin_fly(center, bar.money_anchor(), 2, bar.coin_landed)


func _tier_flash() -> void:
	if Main.instance == null:
		return
	var center := get_global_rect().position + Vector2(size.x / 2.0, 70)
	Main.instance.fx.sparkle_burst(center, 10)
	for n in [_building, _int_back, _int_front]:
		n.modulate = Color(2, 2, 2)
		var tw := create_tween()
		tw.tween_property(n, "modulate", Color.WHITE, 0.4)


## Cartel "CERRADO" mientras el puesto no se abrió (misión guiada, paso 1).
func _closed_sign(on: bool) -> void:
	if _closed == null:
		_closed = U.label("CERRADO", U.SIZE_TITLE, Color.WHITE, true, HORIZONTAL_ALIGNMENT_CENTER)
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color("b83a3f")
		sb.border_color = Color("1b1a2e")
		sb.set_border_width_all(2)
		sb.content_margin_left = 8
		sb.content_margin_right = 8
		_closed.add_theme_stylebox_override("normal", sb)
		add_child(_closed)
	_closed.visible = on
	_closed.position = Vector2(floor(size.x / 2.0) - 44, 54)
	var dim := Color(0.6, 0.6, 0.7) if on else Color.WHITE
	_building.modulate = dim
	_int_back.modulate = dim
	_int_front.modulate = dim
