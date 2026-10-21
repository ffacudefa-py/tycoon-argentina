class_name BusinessScene
extends Control
## Diorama pixel art del negocio seleccionado: calle de su zona, edificio
## según su nivel visual, empleados trabajando y clientes que van y vienen.
##
## Todo es DECORATIVO: la cantidad de clientes refleja la actividad real
## (ventas por segundo) pero no calcula nada. Con calidad baja o ahorro de
## energía se reduce la cantidad de personajes.

const H := 170
const ART_H := 200          ## alto del arte; se recorta el cielo de arriba
const BG_W := 480
const BUILDING_BASE_Y := 163
const WALK_Y := 172
const MAX_WALKERS := [2, 5, 9]

var bid := ""
var _bg: Sprite2D
var _building: Sprite2D
var _people: Node2D
var _workers: Array[Sprite2D] = []
var _walkers: Array = []
var _spawn_t := 0.0
var _anim_t := 0.0
var _last_tier := -1
var _last_float := 0
var _dog: Sprite2D
var _dog_dir := 1.0
var _world: Node2D


func _init() -> void:
	custom_minimum_size.y = H
	clip_contents = true
	mouse_filter = Control.MOUSE_FILTER_IGNORE


func _ready() -> void:
	_world = Node2D.new()
	_world.position = Vector2(0, H - ART_H)
	add_child(_world)
	_bg = Sprite2D.new()
	_bg.centered = false
	_world.add_child(_bg)
	_building = Sprite2D.new()
	_building.centered = false
	_world.add_child(_building)
	_people = Node2D.new()
	_world.add_child(_people)
	_dog = Sprite2D.new()
	_dog.texture = U.tex("characters/dog.png")
	_dog.hframes = 4
	_dog.centered = false
	_dog.visible = false
	_world.add_child(_dog)
	resized.connect(_layout)
	var m := Game.m
	m.business_changed.connect(func(id: String) -> void:
		if id == bid:
			refresh())
	m.sale.connect(_on_sale)
	m.businesses_changed.connect(refresh)


func set_business(id: String) -> void:
	if id == bid:
		return
	bid = id
	_last_tier = -1
	for w in _walkers:
		w["sprite"].queue_free()
	_walkers.clear()
	refresh()


func refresh() -> void:
	if bid == "" or not is_inside_tree():
		return
	var m := Game.m
	var s: Dictionary = m.biz[bid]
	var d := m.derive(bid)
	_bg.texture = U.tex("backgrounds/street_%s.png" % s["zone"])
	var tier: int = d["tier"]
	_building.texture = U.tex("businesses/%s_%d.png" % [bid, tier])
	if _last_tier >= 0 and tier > _last_tier:
		_tier_flash()
	_last_tier = tier
	_closed_sign(s.get("closed", false))
	_rebuild_workers()
	_layout()


func _layout() -> void:
	var w := size.x
	_bg.position = Vector2(floor((w - BG_W) / 2.0), 0)
	_building.position = Vector2(floor(w / 2.0) - 100, BUILDING_BASE_Y - 149)
	var team := Game.m.employees_of(bid) if bid != "" else []
	for i in _workers.size():
		var off: int = [-28, 30, -56, 58, -84, 86][i % 6]
		_workers[i].position = Vector2(floor(w / 2.0) + off - 8, BUILDING_BASE_Y + 3 - 24)


func _rebuild_workers() -> void:
	for wk in _workers:
		wk.queue_free()
	_workers.clear()
	var team := Game.m.employees_of(bid)
	var shown := []
	if team.is_empty():
		# Sin empleados atiende el dueño (vos).
		shown.append({"variant": 0, "owner": true})
	else:
		for e in team.slice(0, 4):
			shown.append({"variant": int(e["variant"]), "owner": false})
	for info in shown:
		var sp := Sprite2D.new()
		sp.texture = U.tex("characters/worker_%d.png" % info["variant"])
		sp.hframes = 10
		sp.frame = 4
		sp.centered = false
		_people.add_child(sp)
		_workers.append(sp)
	_layout()


func _process(delta: float) -> void:
	if bid == "" or not is_visible_in_tree():
		return
	var m := Game.m
	var d := m.derive(bid)
	var s: Dictionary = m.biz[bid]
	_anim_t += delta
	var tick := int(_anim_t / 0.25)
	var busy: bool = s["running"]
	for i in _workers.size():
		_workers[i].frame = (6 + (tick + i) % 2) if busy else (4 + int(_anim_t / 0.8 + i) % 2)

	# Clientes: frecuencia según ventas reales por segundo (sólo visual).
	var level := Settings.fx_level()
	var max_w: int = MAX_WALKERS[level]
	var rate := 0.0
	if d["auto_sell"] and m.has_stock(bid):
		rate = clampf(1.0 / float(d["cycle"]), 0.15, 0.9)
	elif busy:
		rate = 0.6
	else:
		rate = 0.08
	_spawn_t += delta * rate
	if _spawn_t >= 1.0 and _walkers.size() < max_w:
		_spawn_t = 0.0
		_spawn_walker()
	_update_walkers(delta)
	_update_dog(delta, level)


func _spawn_walker() -> void:
	var sp := Sprite2D.new()
	sp.texture = U.tex("characters/customer_%d.png" % (randi() % 8))
	sp.hframes = 10
	sp.centered = false
	var dir := 1.0 if randf() < 0.5 else -1.0
	var w := size.x
	sp.position = Vector2(-16.0 if dir > 0 else w, WALK_Y - 24 + randi() % 3)
	sp.flip_h = dir < 0
	_people.add_child(sp)
	var stop_x: float = floor(w / 2.0) + randf_range(-20, 20) - 8
	_walkers.append({"sprite": sp, "dir": dir, "speed": randf_range(18, 28), "state": "walk", "stop_x": stop_x, "t": 0.0, "shop": randf() < 0.75})


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
			"shop":
				sp.frame = 4 + int(float(wk["t"]) * 2.0) % 2
				if float(wk["t"]) > randf_range(0.8, 1.6):
					wk["state"] = "leave"
					wk["shop"] = false
			"leave":
				sp.position.x += float(wk["dir"]) * float(wk["speed"]) * delta
				sp.frame = int(float(wk["t"]) * 8.0) % 4
		sp.position.x = round(sp.position.x * 1.0)
		if sp.position.x < -20 or sp.position.x > w + 4:
			sp.queue_free()
			_walkers.remove_at(i)


func _update_dog(delta: float, level: int) -> void:
	if level < 2 or Game.m.biz[bid]["zone"] not in ["barrio", "universidad", "costanera"]:
		_dog.visible = false
		return
	if not _dog.visible:
		if randf() < delta * 0.03:
			_dog.visible = true
			_dog_dir = 1.0 if randf() < 0.5 else -1.0
			_dog.position = Vector2(-16.0 if _dog_dir > 0 else size.x, WALK_Y + 6)
			_dog.flip_h = _dog_dir < 0
		return
	_dog.position.x = round(_dog.position.x + _dog_dir * 34.0 * delta)
	_dog.frame = int(_anim_t * 10.0) % 4
	if _dog.position.x < -20 or _dog.position.x > size.x + 4:
		_dog.visible = false


func _on_sale(id: String, revenue: int) -> void:
	if id != bid or not is_visible_in_tree() or Main.instance == null:
		return
	var center := get_global_rect().position + Vector2(size.x / 2.0, 90 - (ART_H - H))
	var now := Time.get_ticks_msec()
	if now - _last_float > 350:
		_last_float = now
		Main.instance.fx.coin_burst(center, 3)
		Main.instance.fx.float_text(center + Vector2(randf_range(-20, 20), -10), "+" + Fmt.money(revenue))
		Sfx.play("coin", randf_range(0.95, 1.1), 0.12)


func _tier_flash() -> void:
	if Main.instance == null:
		return
	var center := get_global_rect().position + Vector2(size.x / 2.0, 80)
	Main.instance.fx.sparkle_burst(center, 10)
	_building.modulate = Color(2, 2, 2)
	var tw := create_tween()
	tw.tween_property(_building, "modulate", Color.WHITE, 0.4)


var _closed: Label


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
	_building.modulate = Color(0.6, 0.6, 0.7) if on else Color.WHITE
