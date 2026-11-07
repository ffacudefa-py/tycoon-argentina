class_name StreetVehicle
extends Node2D
## Un vehículo de la calle (15.0), armado por capas sobre las hojas veh_<tipo>.png:
## sombra, ruedas, carrocería, puertas y luces. Las ruedas giran según lo que avanza
## de verdad, la carrocería rebota sobre una suspensión y cabecea al frenar o acelerar.
## La posición es el punto de la calzada debajo del centro del vehículo (ordena por Y).
## Lo maneja StreetTraffic: acá sólo está la física de cada uno.

const EFFECTS := "res://assets/escenarios/effects/"
const ACCEL := 46.0
const BRAKE := 96.0
const LANE_SPEED := 20.0
const SPRING := 150.0
const DAMP := 11.0
const IDLE_SHAKE := 0.16            ## segundos entre sacudones del motor en marcha lenta

static var _table := {}

var kind := ""
var meta := {}
var dir := 1.0
var speed := 0.0
var cruise := 80.0
var target_speed := 0.0
var lane_y := 0.0
var rough := 0.0                    ## 0 asfalto, 1 tierra: más rebote y más polvo
var traffic: Node2D                 ## el StreetTraffic dueño (humo y tierra)
var braking := false
var accelerating := false
var state := "drive"                ## drive / stopping / stopped (colectivo en la parada)
var hold := 0.0
var overtaking := false

var _shadow: Sprite2D
var _wheels: Sprite2D
var _body: Sprite2D
var _door: Sprite2D
var _tail: Sprite2D
var _beam: Sprite2D
var _dist := 0.0
var _x := 0.0
var _y := 0.0
var _sp := 0.0
var _sp_v := 0.0
var _bump_at := 0.0
var _smoke_t := 0.0
var _dust_t := 0.0
var _idle_t := 0.0
var _idle_up := false
var _pitch := 0
var _pitch_t := 0.0


static func table() -> Dictionary:
	if _table.is_empty():
		var f := FileAccess.open("res://data/vehicles.json", FileAccess.READ)
		if f:
			var parsed = JSON.parse_string(f.get_as_text())
			if parsed is Dictionary:
				_table = parsed
	return _table


func setup(p_kind: String, p_dir: float, x: float, p_lane: float, p_cruise: float, p_traffic: Node2D, p_rough: float, headlights: bool) -> void:
	kind = p_kind
	meta = table().get(kind, {})
	dir = p_dir
	cruise = p_cruise
	speed = p_cruise
	target_speed = p_cruise
	lane_y = p_lane
	traffic = p_traffic
	rough = p_rough
	_x = x
	_y = p_lane
	position = Vector2(round(x), round(p_lane))
	var tex: Texture2D = load(EFFECTS + "veh_%s.png" % kind)
	_shadow = _layer(tex, false)
	_wheels = _layer(tex, true)
	_body = _layer(tex, true)
	_door = _layer(tex, true)
	_door.frame = 11
	_door.visible = false
	_tail = _layer(tex, true)
	_tail.frame = 9
	_tail.visible = headlights
	_shadow.frame = 8
	_wheels.frame = 4
	_body.frame = 0
	if headlights:
		_beam = Sprite2D.new()
		_beam.texture = load(EFFECTS + "veh_beam.png")
		_beam.centered = false
		_beam.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		_beam.flip_h = dir < 0
		var hd: Array = meta.get("head", [0, 0])
		var bx := float(hd[0]) - float(meta.get("fw", 0)) / 2.0
		_beam.position = Vector2(bx if dir > 0 else -bx - 38.0, float(hd[1]) - float(meta.get("gy", 0)) - 7.0)
		add_child(_beam)
	_bump_at = randf_range(40.0, 160.0)


func _layer(tex: Texture2D, flip: bool) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = tex
	s.hframes = 4
	s.vframes = 3
	s.centered = false
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	s.offset = Vector2(-float(meta.get("fw", 0)) / 2.0, -float(meta.get("gy", 0)))
	s.flip_h = flip and dir < 0
	add_child(s)
	return s


func half_len() -> float:
	return float(meta.get("len", 60)) / 2.0


func exact_x() -> float:
	return _x


func kick(amount: float) -> void:
	_sp_v += amount


func set_doors(open: bool) -> void:
	_door.visible = open


func doors_open() -> bool:
	return _door.visible


func tick(delta: float) -> void:
	# Velocidad con inercia: no hay arranques ni frenadas instantáneas.
	var prev := speed
	if speed < target_speed:
		speed = minf(target_speed, speed + ACCEL * delta)
	elif speed > target_speed:
		speed = maxf(target_speed, speed - BRAKE * delta)
	var a := (speed - prev) / maxf(delta, 0.001)
	accelerating = a > 12.0
	braking = a < -18.0 or (speed < 1.0 and target_speed < 1.0)
	_x += dir * speed * delta
	_dist += speed * delta
	var dy := lane_y - _y
	if absf(dy) > 0.05:
		_y += signf(dy) * minf(absf(dy), LANE_SPEED * delta)
	_suspension(delta, a)
	_animate(delta)
	_fumes(delta)
	position = Vector2(round(_x), round(_y))


func _suspension(delta: float, a: float) -> void:
	if _dist > _bump_at:                                  # bache o junta de la calle
		_bump_at = _dist + randf_range(70.0, 190.0) * (1.0 - rough * 0.65)
		_sp_v -= randf_range(16.0, 30.0) * (1.0 + rough)
	_sp_v += (-SPRING * _sp - DAMP * _sp_v) * delta
	_sp += _sp_v * delta
	# El peso se va adelante o atrás: se ve en la carrocería unos instantes.
	var want := 0
	if a < -30.0:
		want = 1
	elif a > 22.0:
		want = 2
	if want != _pitch:
		_pitch_t += delta
		if _pitch_t > 0.05:
			_pitch = want
			_pitch_t = 0.0
			if want == 0:
				_sp_v -= 10.0                              # rebote al asentarse
	else:
		_pitch_t = 0.0


func _animate(delta: float) -> void:
	var r := float(meta.get("r", 5))
	_wheels.frame = 4 + (int(_dist / maxf(r * 0.5, 1.0)) % 4)  # la rueda gira lo que avanza
	var by: float = round(_sp)
	if speed < 2.0:                                       # motor en marcha lenta
		_idle_t += delta
		if _idle_t > IDLE_SHAKE:
			_idle_t = 0.0
			_idle_up = not _idle_up
		if _idle_up and meta.has("bus"):
			by -= 1.0
	_body.position.y = by
	_door.position.y = by
	_tail.position.y = by
	_body.frame = _pitch
	if braking:
		_tail.visible = true
		_tail.frame = 10
	else:
		_tail.frame = 9
		_tail.visible = _beam != null


func _fumes(delta: float) -> void:
	var ex: Array = meta.get("exhaust", [0, 0])
	var ox := float(ex[0]) - float(meta.get("fw", 0)) / 2.0
	var out := Vector2(_x + dir * ox, _y + float(ex[1]) - float(meta.get("gy", 0)))
	_smoke_t -= delta
	if _smoke_t <= 0.0:
		var rate := 0.12 if accelerating else (0.6 if speed > 2.0 else 0.9)
		if meta.has("bus") or kind == "camion":
			rate *= 0.6
		_smoke_t = rate * randf_range(0.8, 1.3)
		var drift := Vector2(-dir * clampf(speed * 0.25, 4.0, 22.0), randf_range(-9.0, -4.0))
		traffic.puff(out, drift, false)
	if rough > 0.0 and speed > 25.0:
		_dust_t -= delta
		if _dust_t <= 0.0:
			_dust_t = lerpf(0.2, 0.06, rough) * randf_range(0.8, 1.2)
			var back := Vector2(_x - dir * half_len() * 0.7, _y - 2.0)
			traffic.puff(back, Vector2(-dir * speed * 0.3, randf_range(-8.0, -2.0)), true)
