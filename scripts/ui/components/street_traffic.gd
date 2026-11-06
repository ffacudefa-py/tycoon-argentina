class_name StreetTraffic
extends Node2D
## El tránsito de una calle (15.0): dos carriles por sentido contrario, autos que
## respetan la distancia, frenan detrás del que va más lento y lo pasan por el otro
## carril, y un colectivo que para, abre las puertas y arranca largando humo.
## Lo usan BusinessScene (la calle del negocio) y la postal de la pantalla de inicio.
## Es sólo decorado: pocos nodos, se vacía fuera de pantalla y con "Reducir movimiento".

const MARGIN := 150.0
const MAX_PUFFS := 26
const GAP := 16.0
const BUSES := ["bus60", "bus160", "bus103", "bus59"]
const CARS := ["sedan_rojo", "sedan_celeste", "sedan_crema", "rural_verde", "rural_gris", "chata_azul", "chata_roja", "furgon", "moto"]
const CITY := ["taxi", "taxi", "sedan_rojo", "sedan_celeste", "sedan_crema", "rural_gris", "furgon", "moto", "moto"]
const RURAL := ["chata_azul", "chata_roja", "rural_verde", "sedan_crema", "camion", "camion", "moto"]

var width := 480.0
var near_y := 198.0                 ## carril de adelante (va a la derecha)
var far_y := 190.0                  ## carril de atrás (va a la izquierda)
var rough := 0.0                    ## 0 asfalto, 0.5 ripio, 1 tierra
var kinds: Array = CARS
var headlights := false
var bus_stops := true               ## el colectivo para en la mitad de la calle
var active := true
var max_cars := 4
var car_every := Vector2(2.0, 5.5)
var bus_every := Vector2(14.0, 26.0)

var _cars: Array = []
var _puffs: Array = []
var _car_t := 0.6
var _bus_t := 5.0


func _init() -> void:
	y_sort_enabled = true


func clear() -> void:
	for c in _cars:
		c.queue_free()
	_cars.clear()
	for p in _puffs:
		p["node"].queue_free()
	_puffs.clear()
	_bus_t = randf_range(3.0, 9.0)
	_car_t = randf_range(0.3, 1.5)


## Calle según la región: tipos de vehículo y si levanta tierra.
func set_street(street: String) -> void:
	match street:
		"noa", "patagonia":
			rough = 0.5
			kinds = RURAL
		"pampeana":
			rough = 1.0
			kinds = RURAL
		"centro":
			rough = 0.0
			kinds = CITY
		_:
			rough = 0.0
			kinds = CARS


func prefill() -> void:
	for i in 2:
		var x := randf_range(40.0, width - 40.0)
		if i % 2 == 0:
			_add(kinds[randi() % kinds.size()], 1.0, x, near_y)
		else:
			_add(kinds[randi() % kinds.size()], -1.0, x, far_y)


func _add(kind: String, dir: float, x: float, lane: float) -> StreetVehicle:
	var v := StreetVehicle.new()
	add_child(v)
	var cruise := randf_range(62.0, 92.0)
	if kind == "moto":
		cruise = randf_range(95.0, 120.0)
	elif kind == "camion":
		cruise = randf_range(48.0, 60.0)
	elif kind.begins_with("bus"):
		cruise = randf_range(70.0, 82.0)
	v.setup(kind, dir, x, lane, cruise, self, rough, headlights)
	_cars.append(v)
	return v


func _process(delta: float) -> void:
	if not active or not is_visible_in_tree():
		return
	_spawn(delta)
	_drive(delta)
	_tick_puffs(delta)


func _spawn(delta: float) -> void:
	_bus_t -= delta
	if _bus_t <= 0.0:
		_bus_t = randf_range(bus_every.x, bus_every.y)
		if _lane_free(-MARGIN, near_y, 180.0):
			var b := _add(BUSES[randi() % BUSES.size()], 1.0, -MARGIN, near_y)
			if bus_stops and randf() < 0.75:
				b.state = "stopping"
				b.set_meta("stop_x", width * randf_range(0.17, 0.22))   # a un costado: no tapa el negocio
	_car_t -= delta
	if _car_t <= 0.0:
		_car_t = randf_range(car_every.x, car_every.y)
		if _cars.size() >= max_cars:
			return
		var k: String = kinds[randi() % kinds.size()]
		var right := randf() < 0.5
		var x := -MARGIN if right else width + MARGIN
		var lane := near_y if right else far_y
		if _lane_free(x, lane, 110.0):
			_add(k, 1.0 if right else -1.0, x, lane)


func _lane_free(x: float, lane: float, room: float) -> bool:
	for c in _cars:
		if absf(c.lane_y - lane) < 1.0 and absf(c.exact_x() - x) < room:
			return false
	return true


func _drive(delta: float) -> void:
	for i in range(_cars.size() - 1, -1, -1):
		var c: StreetVehicle = _cars[i]
		if c.meta.has("bus") and c.state != "drive":
			_bus_stop(c, delta)
		else:
			c.target_speed = _follow(c)
		c.tick(delta)
		var x := c.exact_x()
		if (c.dir > 0.0 and x > width + MARGIN) or (c.dir < 0.0 and x < -MARGIN):
			c.queue_free()
			_cars.remove_at(i)


## Velocidad deseada según el de adelante. Si está parado o muy lento, intenta pasarlo.
func _follow(c: StreetVehicle) -> float:
	var lead: StreetVehicle = null
	var gap := INF
	for o in _cars:
		if o == c or absf(o.lane_y - c.lane_y) > 3.0:
			continue
		var d: float = (o.exact_x() - c.exact_x()) * c.dir - o.half_len() - c.half_len()
		if d > -4.0 and d < gap:
			gap = d
			lead = o
	if c.overtaking:
		# Vuelve a su carril cuando ya dejó atrás al que pasó.
		if _lane_free(c.exact_x() - c.dir * 40.0, _home(c), 70.0) and _lane_free(c.exact_x() + c.dir * 40.0, _home(c), 70.0):
			c.lane_y = _home(c)
			c.overtaking = false
	if lead == null or gap > 110.0:
		return c.cruise
	if lead.speed < 28.0 and gap < 95.0 and not c.meta.has("bus") and not c.overtaking and c.dir > 0.0:
		var other := far_y
		var clear_ahead := true
		for o in _cars:
			if absf(o.lane_y - other) < 3.0 and (o.exact_x() - c.exact_x()) * c.dir > -80.0 and (o.exact_x() - c.exact_x()) * c.dir < 260.0:
				clear_ahead = false
		if clear_ahead:
			c.lane_y = other
			c.overtaking = true
			return c.cruise
	if gap < GAP:
		return minf(lead.speed * 0.7, c.cruise)
	return minf(c.cruise, lerpf(lead.speed, c.cruise, clampf((gap - GAP) / 90.0, 0.0, 1.0)))


func _home(c: StreetVehicle) -> float:
	return near_y if c.dir > 0.0 else far_y


## El colectivo llega a la parada, abre, espera y arranca con su bocanada de humo.
func _bus_stop(c: StreetVehicle, delta: float) -> void:
	match c.state:
		"stopping":
			var stop_x: float = c.get_meta("stop_x")
			var d := stop_x - c.exact_x()
			var want := sqrt(maxf(0.0, 2.0 * StreetVehicle.BRAKE * 0.5 * d))
			c.target_speed = minf(c.cruise, want)
			if d < 1.0 or c.speed < 1.5 and d < 8.0:
				c.state = "stopped"
				c.target_speed = 0.0
				c.hold = randf_range(2.0, 3.2)
				c.set_meta("opened", false)
		"stopped":
			c.target_speed = 0.0
			c.hold -= delta
			if c.speed < 1.0 and not c.get_meta("opened", false):
				c.set_meta("opened", true)
				c.set_doors(true)
			if c.hold < 0.45:
				c.set_doors(false)
			if c.hold <= 0.0:
				c.state = "drive"
				c.target_speed = c.cruise
				c.kick(-14.0)
				var ex: Array = c.meta.get("exhaust", [0, 0])
				var at := c.position + Vector2(float(ex[0]) - float(c.meta.get("fw", 0)) / 2.0, float(ex[1]) - float(c.meta.get("gy", 0)))
				for i in 5:
					puff(at + Vector2(randf_range(-2.0, 2.0), 0), Vector2(-randf_range(10.0, 30.0), randf_range(-12.0, -3.0)), false)


func puff(at: Vector2, vel: Vector2, dust: bool) -> void:
	if _puffs.size() >= MAX_PUFFS or at.x < -30.0 or at.x > width + 30.0:
		return
	var s := Sprite2D.new()
	s.texture = load(StreetVehicle.EFFECTS + ("veh_dust.png" if dust else "veh_puff.png"))
	s.hframes = 6
	s.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	s.z_index = 2
	s.position = at
	s.flip_h = randf() < 0.5
	add_child(s)
	_puffs.append({"node": s, "t": 0.0, "life": randf_range(0.7, 1.1) * (1.5 if dust else 1.0), "vel": vel})


func _tick_puffs(delta: float) -> void:
	for i in range(_puffs.size() - 1, -1, -1):
		var p: Dictionary = _puffs[i]
		var s: Sprite2D = p["node"]
		p["t"] = float(p["t"]) + delta
		var k := float(p["t"]) / float(p["life"])
		if k >= 1.0:
			s.queue_free()
			_puffs.remove_at(i)
			continue
		var vel: Vector2 = p["vel"]
		vel *= 1.0 - 1.4 * delta
		p["vel"] = vel
		s.position += vel * delta
		s.frame = mini(5, int(k * 6.0))
