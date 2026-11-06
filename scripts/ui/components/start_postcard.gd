class_name StartPostcard
extends Control
## La postal viva de la pantalla de inicio (15.0): el Noroeste a la hora dorada.
## Capas en parallax (tools/art/postal15.py) con todo lo que se mueve intercalado:
## tren en el viaducto, cóndores, llamas, humo del pueblo, ventanas que se encienden,
## río, sombra de nubes y la ruta con el tránsito de StreetTraffic.
## Con "Reducir movimiento" queda la postal quieta.

const ART_W := 480.0
const ART_H := 900.0
## Capa, cuánto se corre con la cámara (0 a 1) y cuánto sube en la entrada.
const DEPTHS := {"sky": [0.0, 0.0], "andes": [0.07, 26.0], "hills": [0.14, 56.0], "bridge": [0.2, 84.0],
	"valley": [0.3, 116.0], "road": [0.55, 170.0], "fore": [1.0, 250.0]}
const CAM_SWAY := 10.0
const TRAIN_SPEED := 34.0
const TRAIN_CARS := 4
const CAR_W := 42.0
const MAX_SMOKE := 14

var data := {}
var _stage: Node2D
var _top_fill: ColorRect
var _fade: ColorRect
var _layers := {}
var _road_screen_y := 500.0
var _t := 0.0
var _intro := 9.0                       ## tiempo desde que arrancó la entrada
var _traffic: StreetTraffic
var _anim := true

var _train: Array = []
var _train_x := -120.0
var _train_dir := 1.0
var _train_wait := 0.0
var _train_on := false
var _condors: Array = []
var _llamas: Array = []
var _river: Sprite2D
var _windows: Array = []
var _flag: Sprite2D
var _tufts: Array = []
var _stars: Array = []
var _far: Sprite2D
var _far_d := 0.0
var _far_dir := 1.0
var _far_len := 0.0
var _smoke: Array = []
var _smoke_t := 0.0
var _motes: Array = []


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	clip_contents = true
	var f := FileAccess.open("res://data/postal.json", FileAccess.READ)
	if f:
		var parsed = JSON.parse_string(f.get_as_text())
		if parsed is Dictionary:
			data = parsed
	_top_fill = ColorRect.new()
	_top_fill.color = Color(str(data.get("sky_top", "#232A63")))
	_top_fill.set_anchors_preset(Control.PRESET_FULL_RECT)
	_top_fill.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_top_fill)
	_stage = Node2D.new()
	add_child(_stage)
	_build()
	_fade = ColorRect.new()
	_fade.color = Color("#141030")
	_fade.set_anchors_preset(Control.PRESET_FULL_RECT)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fade.modulate.a = 0.0
	add_child(_fade)
	resized.connect(_place)
	_place()


func _sp(parent: Node, path: String, hf := 1, vf := 1) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = U.tex(path)
	s.hframes = hf
	s.vframes = vf
	s.centered = false
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	parent.add_child(s)
	return s


func _layer(id: String) -> Node2D:
	var n := Node2D.new()
	_stage.add_child(n)
	_layers[id] = n
	return n


func _light(s: Sprite2D, strength: float) -> void:
	var m := ShaderMaterial.new()
	m.shader = load("res://shaders/postal_light.gdshader")
	m.set_shader_parameter("strength", strength)
	s.material = m


func _build() -> void:
	var sky := _layer("sky")
	_sp(sky, "start/start_sky.png")
	for i in 16:                                       # estrellas que titilan, arriba de todo
		var st := _sp(sky, "start/start_star.png", 3)
		st.position = Vector2(randf_range(0.0, ART_W), randf_range(4.0, 190.0))
		_stars.append({"node": st, "t": randf() * 6.0, "rate": randf_range(0.6, 1.8)})
	_condors.append(_new_condor(sky, 0.55, Vector2(150, 372), Vector2(90, 14), 0.16, 1.8))
	var andes := _layer("andes")
	_light(_sp(andes, "start/start_andes.png"), 0.16)
	var hills := _layer("hills")
	_light(_sp(hills, "start/start_hills.png"), 0.26)
	_far = _sp(hills, "start/start_far_car.png")
	var serp: Array = data.get("serp", [])
	for i in range(1, serp.size()):
		_far_len += Vector2(serp[i][0], serp[i][1]).distance_to(Vector2(serp[i - 1][0], serp[i - 1][1]))
	_condors.append(_new_condor(hills, 1.0, Vector2(300, 452), Vector2(120, 22), 0.22, 0.0))
	var bridge := _layer("bridge")
	_sp(bridge, "start/start_viaduct.png")
	for i in TRAIN_CARS:
		var c := _sp(bridge, "start/start_train.png", 2, 2)
		c.visible = false
		_train.append(c)
	var valley := _layer("valley")
	_sp(valley, "start/start_valley.png")
	_river = _sp(valley, "start/start_river.png", 4)
	_river.position.y = float(data.get("river_y", 0))
	for i in 3:
		var w := _sp(valley, "start/start_windows.png", 3)
		w.frame = i
		w.position.y = float(data.get("windows_y", 0))
		w.modulate.a = 0.0
		_windows.append({"node": w, "t": 1.2 + i * 1.6, "seed": randf() * 6.0})
	var fl: Array = data.get("flag", [0, 0])
	_flag = _sp(valley, "start/start_flag.png", 4)
	_flag.position = Vector2(fl[0], fl[1])
	for e in data.get("llamas", []):
		var l := _sp(valley, "start/start_llama.png", 4, 2)
		l.position = Vector2(e[0], float(e[1]) - 29.0)
		l.flip_h = randf() < 0.5
		_llamas.append({"node": l, "row": int(e[2]), "t": randf() * 3.0, "base": 0})
	var road := _layer("road")
	_sp(road, "start/start_road.png")
	var under := ColorRect.new()                       # debajo del arte, en pantallas muy altas
	under.color = Color(str(data.get("ground", "#2e2a50")))
	under.position = Vector2(-60, ART_H)
	under.size = Vector2(ART_W + 120.0, 700.0)
	under.mouse_filter = Control.MOUSE_FILTER_IGNORE
	road.add_child(under)
	_traffic = StreetTraffic.new()
	_traffic.width = ART_W
	_traffic.near_y = float(data.get("lane_near", 674))
	_traffic.far_y = float(data.get("lane_far", 660))
	_traffic.headlights = true
	_traffic.rough = 0.25
	_traffic.bus_stops = false
	_traffic.kinds = StreetTraffic.RURAL
	_traffic.max_cars = 3
	_traffic.car_every = Vector2(2.5, 6.5)
	_traffic.bus_every = Vector2(9.0, 17.0)
	road.add_child(_traffic)
	var fore := _layer("fore")
	_sp(fore, "start/start_fore.png")
	for e in data.get("tufts", []):
		var t := _sp(fore, "start/start_tuft.png", 3)
		t.position = Vector2(e[0], float(e[1]) - 15.0)
		_tufts.append({"node": t, "phase": randf() * 6.0})
	for i in 12:                                       # motas de polvo en la luz rasante
		var m := ColorRect.new()
		m.size = Vector2.ONE
		m.color = Color("ffe9b0")
		m.mouse_filter = Control.MOUSE_FILTER_IGNORE
		fore.add_child(m)
		_motes.append({"node": m, "x": randf_range(0.0, ART_W), "y": randf_range(480.0, 640.0), "t": randf() * 8.0})


func _new_condor(parent: Node, sc: float, center: Vector2, radius: Vector2, rate: float, phase: float) -> Dictionary:
	var s := _sp(parent, "start/start_condor.png", 4)
	s.scale = Vector2.ONE * sc
	s.centered = true
	return {"node": s, "center": center, "radius": radius, "rate": rate, "a": phase, "flap": 2.0}


## Dónde cae el borde de abajo de la ruta en pantalla (justo arriba del menú).
func set_road_screen_y(y: float) -> void:
	_road_screen_y = y
	_place()


func _place() -> void:
	var sc := maxf(1.0, size.x / 460.0)
	_stage.scale = Vector2.ONE * sc
	_stage.position = Vector2(floor((size.x - ART_W * sc) / 2.0), floor(_road_screen_y - float(data.get("road_bot", 678)) * sc))


## Entrada: amanece la postal y las capas suben a su lugar, primero lo lejano.
func intro() -> void:
	_intro = 0.0
	if not _animated():
		_intro = 9.0
		return
	_fade.modulate.a = 1.0
	_fade.create_tween().tween_property(_fade, "modulate:a", 0.0, 0.9)
	_train_x = -150.0
	_train_on = true
	_train_dir = 1.0
	_show_train(true)
	_traffic.clear()
	_traffic.prefill()


func _animated() -> bool:
	return Settings.fx_level() > 0 and not Settings.get_value("reduce_motion")


func _process(delta: float) -> void:
	if not is_visible_in_tree():
		return
	_anim = _animated()
	_traffic.active = _anim
	_traffic.visible = _anim
	if not _anim:
		_set_layers(0.0)
		return
	_t += delta
	_intro += delta
	_set_layers(sin(_t * 0.21) * 0.7 + sin(_t * 0.09 + 1.0) * 0.3)
	_tick_sky(delta)
	_tick_train(delta)
	_tick_village(delta)
	_tick_animals(delta)


func _set_layers(sway: float) -> void:
	var idx := 0
	for id in DEPTHS:
		var cfg: Array = DEPTHS[id]
		var n: Node2D = _layers[id]
		var k := clampf((_intro - float(idx) * 0.09) / 1.25, 0.0, 1.0)
		var e := 1.0 - pow(1.0 - k, 3.0)
		n.position = Vector2(round(sway * CAM_SWAY * float(cfg[0])), round((1.0 - e) * float(cfg[1])))
		idx += 1


func _tick_sky(delta: float) -> void:
	for s in _stars:
		s["t"] = float(s["t"]) + delta * float(s["rate"])
		var v := sin(float(s["t"]))
		(s["node"] as Sprite2D).frame = 1 if v > 0.86 else 0
		(s["node"] as Sprite2D).modulate.a = 0.35 + 0.65 * maxf(v, 0.0)
	for c in _condors:
		c["a"] = float(c["a"]) + delta * float(c["rate"])
		var a := float(c["a"])
		var cen: Vector2 = c["center"]
		var rad: Vector2 = c["radius"]
		var n: Sprite2D = c["node"]
		n.position = Vector2(round(cen.x + cos(a) * rad.x), round(cen.y + sin(a) * rad.y))
		n.flip_h = -sin(a) * rad.x < 0.0
		# Planea casi siempre; de vez en cuando bate las alas.
		c["flap"] = float(c["flap"]) - delta
		if float(c["flap"]) < -1.1:
			c["flap"] = randf_range(5.0, 11.0)
		n.frame = int(_t * 5.0) % 4 if float(c["flap"]) < 0.0 else 1
	# autito con los faros prendidos por el camino de cornisa
	var serp: Array = data.get("serp", [])
	if serp.size() > 1:
		_far_d += _far_dir * 6.0 * delta
		if _far_d > _far_len or _far_d < 0.0:
			_far_dir = -_far_dir
			_far_d = clampf(_far_d, 0.0, _far_len)
		var left := _far_d
		for i in range(1, serp.size()):
			var a2 := Vector2(serp[i - 1][0], serp[i - 1][1])
			var b2 := Vector2(serp[i][0], serp[i][1])
			var seg := a2.distance_to(b2)
			if left <= seg:
				var p := a2.lerp(b2, left / maxf(seg, 0.01))
				_far.position = Vector2(round(p.x) - 2.0, round(p.y) - 2.0)
				_far.flip_h = (b2.x - a2.x) * _far_dir < 0.0
				break
			left -= seg


func deck_y(x: float) -> float:
	var u := (x - 240.0) / 240.0
	return float(data.get("deck_a", 500.0)) + u * u * float(data.get("deck_b", 22.0))


func _show_train(on: bool) -> void:
	for c in _train:
		c.visible = on


func _tick_train(delta: float) -> void:
	if not _train_on:
		_train_wait -= delta
		if _train_wait <= 0.0:
			_train_on = true
			_train_dir = 1.0 if randf() < 0.5 else -1.0
			_train_x = -150.0 if _train_dir > 0.0 else ART_W + 150.0
			_show_train(true)
		return
	_train_x += _train_dir * TRAIN_SPEED * delta
	var rock := int(_t * 7.0) % 2
	for i in _train.size():
		var c: Sprite2D = _train[i]
		var x := _train_x - _train_dir * float(i) * CAR_W
		c.frame = (0 if i == 0 else 2) + rock
		c.flip_h = _train_dir < 0.0
		c.position = Vector2(round(x), round(deck_y(x + CAR_W / 2.0)) - 18.0)
	var loco_x := _train_x + (6.0 if _train_dir > 0.0 else 30.0)
	if randf() < delta * 7.0:
		_add_smoke(Vector2(loco_x, deck_y(loco_x) - 18.0), "bridge", Vector2(-_train_dir * 12.0, -7.0))
	if (_train_dir > 0.0 and _train_x > ART_W + 190.0) or (_train_dir < 0.0 and _train_x < -190.0):
		_train_on = false
		_show_train(false)
		_train_wait = randf_range(9.0, 16.0)


func _add_smoke(at: Vector2, layer_id: String, vel: Vector2) -> void:
	if _smoke.size() >= MAX_SMOKE:
		return
	var s := _sp(_layers[layer_id], "effects/veh_puff.png", 6)
	s.position = at
	s.modulate = Color(1.0, 0.9, 0.82, 0.85)
	_smoke.append({"node": s, "t": 0.0, "life": randf_range(1.8, 2.8), "vel": vel})


func _tick_village(delta: float) -> void:
	_smoke_t -= delta
	if _smoke_t <= 0.0:
		_smoke_t = randf_range(0.5, 1.0)
		var ch: Array = data.get("chimneys", [])
		if not ch.is_empty():
			var e: Array = ch[randi() % ch.size()]
			_add_smoke(Vector2(float(e[0]) - 5.0, float(e[1]) - 10.0), "valley", Vector2(randf_range(2.0, 6.0), randf_range(-7.0, -4.0)))
	for i in range(_smoke.size() - 1, -1, -1):
		var p: Dictionary = _smoke[i]
		var s: Sprite2D = p["node"]
		p["t"] = float(p["t"]) + delta
		var k := float(p["t"]) / float(p["life"])
		if k >= 1.0:
			s.queue_free()
			_smoke.remove_at(i)
			continue
		s.position += (p["vel"] as Vector2) * delta
		s.frame = mini(5, int(k * 6.0))
	_river.frame = int(_t * 3.5) % 4
	_flag.frame = int(_t * 6.0) % 4
	for w in _windows:                                 # se encienden de a grupos al caer la tarde
		var n: Sprite2D = w["node"]
		if _t > float(w["t"]):
			var b := clampf((_t - float(w["t"])) / 1.5, 0.0, 1.0)
			n.modulate.a = b * (0.86 + 0.14 * sin(_t * 2.3 + float(w["seed"])))


func _tick_animals(delta: float) -> void:
	for l in _llamas:
		l["t"] = float(l["t"]) - delta
		var n: Sprite2D = l["node"]
		if float(l["t"]) <= 0.0:
			var roll := randf()
			l["base"] = 0 if roll < 0.3 else (1 if roll < 0.85 else 3)
			l["t"] = randf_range(1.5, 4.5)
			if roll < 0.1:
				n.flip_h = not n.flip_h
		var f: int = l["base"]
		if f == 1 and int(_t * 2.0) % 2 == 0:             # masca: la cabeza y la cola se mueven
			f = 2
		n.frame = int(l["row"]) * 4 + f
	for t in _tufts:
		var v := sin(_t * 1.6 + float(t["phase"])) + sin(_t * 0.7 + float(t["phase"]) * 2.0) * 0.6
		(t["node"] as Sprite2D).frame = clampi(int(round(v + 1.0)), 0, 2)
	for m in _motes:
		m["t"] = float(m["t"]) + delta
		var mt := float(m["t"])
		var r: ColorRect = m["node"]
		r.position = Vector2(round(float(m["x"]) + mt * 5.0 + sin(mt) * 5.0), round(float(m["y"]) - mt * 3.0))
		r.modulate.a = sin(clampf(mt / 7.0, 0.0, 1.0) * PI) * 0.7
		if mt > 7.0:
			m["t"] = 0.0
			m["x"] = randf_range(0.0, ART_W)
			m["y"] = randf_range(480.0, 640.0)
