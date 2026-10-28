class_name SceneAmbient
extends Node2D
## Vida ambiental de BusinessScene (estilo 11): nubes en dos capas de parallax,
## pájaros, autos, destellos en las ventanas y, adentro, motas de luz.
## Sólo decora: no captura toques, no tapa la interfaz (vive en el "mundo" de la
## escena, debajo de los botones) y se pausa fuera de pantalla o con
## "Reducir movimiento". Pocos sprites reutilizados y movidos por transform.

enum Layer { SKY, ROAD, SPARKS }

var layer := Layer.SKY
var scene: Control                    ## la BusinessScene (para el ancho y la vista)
var _items: Array = []                ## {node, vx, vy, t, phase, kind, life}
var _spawn_t := 0.0
var _rng := RandomNumberGenerator.new()

const SKY_MAX := 6
const ROAD_MAX := 3
const SPARK_MAX := 5


func setup(p_scene: Control, p_layer: int) -> void:
	scene = p_scene
	layer = p_layer
	_rng.randomize()
	_spawn_t = _rng.randf_range(0.1, 0.6)          # que enseguida haya algo en movimiento


static func enabled() -> bool:
	return Settings.fx_level() > 0 and bool(Settings.get_value("scene_anim")) and not Settings.get_value("reduce_motion")


func _process(delta: float) -> void:
	if scene == null or not scene.is_visible_in_tree():
		return
	var on := enabled()
	visible = on
	if not on:
		return
	var interior: bool = scene.view == "interior"
	if layer == Layer.SKY and _items.is_empty() and not interior and _has_sky():
		_prefill_clouds()
	_spawn_t -= delta
	if _spawn_t <= 0.0:
		_spawn(interior)
	var w: float = scene.size.x
	for i in range(_items.size() - 1, -1, -1):
		var it: Dictionary = _items[i]
		var n: Node2D = it["node"]
		it["t"] = float(it["t"]) + delta
		n.position.x += float(it["vx"]) * delta
		match it["kind"]:
			"bird":
				n.position.y = float(it["y0"]) + sin(float(it["t"]) * float(it["phase"])) * 4.0
				(n as Sprite2D).frame = int(float(it["t"]) * 7.0 + float(it["phase"])) % 2
			"car":
				(n as Sprite2D).frame = int(float(it["t"]) * 10.0) % 2
			"spark", "mote":
				var life: float = it["life"]
				var k := float(it["t"]) / life
				n.modulate.a = sin(clampf(k, 0.0, 1.0) * PI)
				n.position.y += float(it["vy"]) * delta
				if n is Sprite2D and (n as Sprite2D).hframes > 1:
					(n as Sprite2D).frame = mini(3, int(k * 4.0))
				if k >= 1.0:
					n.queue_free()
					_items.remove_at(i)
					continue
		if (float(it["vx"]) > 0.0 and n.position.x > w + 90.0) or (float(it["vx"]) < 0.0 and n.position.x < -90.0):
			n.queue_free()
			_items.remove_at(i)
	# en el interior no hay cielo ni calle
	if interior and layer != Layer.SPARKS:
		for it in _items:
			it["node"].queue_free()
		_items.clear()


func _sprite(path: String, frames := 1) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = U.tex(path)
	s.hframes = frames
	s.centered = true
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(s)
	return s


## La calle porteña (CABA) tapa el cielo con edificios: ahí no van nubes.
func _has_sky() -> bool:
	var g := Game.m
	if scene == null or scene.bid == "" or not g.biz.has(scene.bid):
		return true
	return str(g.data.zone_by_id[g.biz[scene.bid]["zone"]].get("street", "")) != "centro"


func _count(kind: String) -> int:
	var n := 0
	for it in _items:
		if it["kind"] == kind:
			n += 1
	return n


func _prefill_clouds() -> void:
	for i in 3:
		_add_cloud(_rng.randf_range(0.0, scene.size.x))


func _add_cloud(x: float) -> void:
	var size := _rng.randi() % 3
	var far := _rng.randf() < 0.5
	var s := _sprite("effects/amb_cloud_%d.png" % size)
	s.position = Vector2(x, _rng.randf_range(10.0, 28.0 if far else 44.0))   # sólo en la franja de cielo
	s.modulate = Color(1, 1, 1, 0.75 if far else 0.95)
	s.scale = Vector2.ONE * (0.8 if far else 1.0)
	# parallax: las lejanas se mueven más lento
	var vx := _rng.randf_range(3.0, 5.0) if far else _rng.randf_range(10.0, 16.0)
	_items.append({"node": s, "vx": vx, "t": 0.0, "kind": "cloud", "phase": 0.0})


func _spawn(interior: bool) -> void:
	var w: float = scene.size.x
	match layer:
		Layer.SKY:
			_spawn_t = _rng.randf_range(2.5, 6.0)
			if interior:
				return
			if _has_sky() and _count("cloud") < 4 and _rng.randf() < 0.6:
				_add_cloud(-60.0)
			elif _count("bird") < 3:
				var dir := 1.0 if _rng.randf() < 0.5 else -1.0
				var flock := 1 + _rng.randi() % 3
				for k in flock:
					var b := _sprite("effects/amb_bird.png", 2)
					var y0 := _rng.randf_range(18.0, 60.0) + k * 5.0
					b.position = Vector2(-20.0 - k * 12.0 if dir > 0 else w + 20.0 + k * 12.0, y0)
					b.flip_h = dir < 0
					b.scale = Vector2.ONE * 2.0
					_items.append({"node": b, "vx": dir * _rng.randf_range(22.0, 34.0), "t": _rng.randf() * 3.0, "kind": "bird",
						"phase": _rng.randf_range(4.0, 7.0), "y0": y0})
		Layer.ROAD:
			_spawn_t = _rng.randf_range(2.5, 7.0)
			if interior or _count("car") >= ROAD_MAX:
				return
			var dir2 := 1.0 if _rng.randf() < 0.55 else -1.0
			var c := _sprite("effects/amb_car_%d.png" % (_rng.randi() % 5), 2)
			c.flip_h = dir2 < 0
			c.position = Vector2(-40.0 if dir2 > 0 else w + 40.0, BusinessScene.ROAD_Y - 9.0)   # en su carril
			_items.append({"node": c, "vx": dir2 * _rng.randf_range(55.0, 95.0), "t": 0.0, "kind": "car", "phase": 0.0})
		Layer.SPARKS:
			_spawn_t = _rng.randf_range(0.5, 1.4)
			if _count("spark") + _count("mote") >= SPARK_MAX:
				return
			if interior:
				var m := ColorRect.new()
				m.size = Vector2(1, 1)
				m.color = Color("fff6c8")
				m.mouse_filter = Control.MOUSE_FILTER_IGNORE
				var holder := Node2D.new()
				holder.add_child(m)
				add_child(holder)
				holder.position = Vector2(_rng.randf_range(20.0, w - 20.0), _rng.randf_range(70.0, 160.0))
				_items.append({"node": holder, "vx": _rng.randf_range(-3.0, 3.0), "vy": _rng.randf_range(-6.0, -2.0), "t": 0.0,
					"kind": "mote", "life": _rng.randf_range(2.0, 3.5), "phase": 0.0})
			else:
				var sp := _sprite("particles/sparkle.png", 4)
				sp.position = Vector2(w / 2.0 + _rng.randf_range(-80.0, 80.0), _rng.randf_range(60.0, 150.0))
				_items.append({"node": sp, "vx": 0.0, "vy": 0.0, "t": 0.0, "kind": "spark", "life": _rng.randf_range(0.6, 1.0), "phase": 0.0})
