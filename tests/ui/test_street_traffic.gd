extends TestCase
## 15.0: StreetTraffic: el colectivo para y sigue, los autos pasan al que está
## parado por el otro carril y nadie se lleva puesto a nadie.

const DT := 1.0 / 60.0


func _traffic() -> StreetTraffic:
	var t := StreetTraffic.new()
	t.width = 360.0
	return t


func _step(t: StreetTraffic, secs: float, each := Callable()) -> void:
	for i in int(secs / DT):
		t._drive(DT)
		if each.is_valid():
			each.call()


func test_colectivo_para_abre_y_arranca() -> void:
	var t := _traffic()
	var b := t._add("bus60", 1.0, -100.0, t.near_y)
	b.state = "stopping"
	b.set_meta("stop_x", 70.0)
	var abrio := [false]
	var freno := [false]
	_step(t, 3.5, func() -> void:
		abrio[0] = abrio[0] or b.doors_open()
		freno[0] = freno[0] or b.braking)
	check(freno[0], "frena antes de la parada, con la luz de freno")
	check(absf(b.exact_x() - 70.0) < 6.0, "para en la parada (x=%s)" % b.exact_x())
	check(b.speed < 1.0, "queda detenido")
	check(abrio[0], "abre las puertas parado")
	_step(t, 6.0)
	eq(b.state, "drive", "termina la parada")
	check(not b.doors_open(), "cierra las puertas antes de salir")
	check(b.exact_x() > 150.0, "arranca y sigue viaje (x=%s)" % b.exact_x())
	t.free()


func test_auto_pasa_al_colectivo_parado_y_vuelve() -> void:
	var t := _traffic()
	var b := t._add("bus59", 1.0, 200.0, t.near_y)
	b.state = "stopped"
	b.hold = 99.0
	b.speed = 0.0
	b.target_speed = 0.0
	var c := t._add("sedan_rojo", 1.0, 20.0, t.near_y)
	var cambio := [false]
	var choco := [false]
	_step(t, 6.0, func() -> void:
		cambio[0] = cambio[0] or c.lane_y == t.far_y
		var overlap: bool = absf(c.exact_x() - b.exact_x()) < c.half_len() + b.half_len()
		if overlap and absf(c.position.y - t.near_y) < 3.0:
			choco[0] = true)
	check(cambio[0], "sale al otro carril para pasar")
	check(not choco[0], "no atraviesa al colectivo")
	check(c.exact_x() > 230.0, "lo pasa (x=%s)" % c.exact_x())
	eq(c.lane_y, t.near_y, "vuelve a su carril")
	t.free()


func test_espera_si_viene_alguien_de_frente() -> void:
	var t := _traffic()
	var b := t._add("bus103", 1.0, 200.0, t.near_y)
	b.state = "stopped"
	b.hold = 99.0
	b.speed = 0.0
	b.target_speed = 0.0
	var c := t._add("rural_gris", 1.0, 40.0, t.near_y)
	var o := t._add("camion", -1.0, 300.0, t.far_y)
	o.cruise = 10.0
	o.speed = 10.0
	_step(t, 3.0)
	eq(c.lane_y, t.near_y, "no se abre con uno de frente")
	check(c.speed < 30.0, "frena detrás del colectivo (v=%s)" % c.speed)
	check(c.exact_x() + c.half_len() < b.exact_x() - b.half_len() + 2.0, "no se lo lleva puesto")
	t.free()


func test_el_rapido_no_atraviesa_al_lento() -> void:
	var t := _traffic()
	t.width = 2000.0
	var lento := t._add("camion", 1.0, 200.0, t.near_y)
	lento.cruise = 45.0
	var rapido := t._add("moto", 1.0, 20.0, t.near_y)
	rapido.cruise = 120.0
	var min_gap := [INF]
	_step(t, 8.0, func() -> void:
		var gap: float = lento.exact_x() - lento.half_len() - rapido.exact_x() - rapido.half_len()
		min_gap[0] = minf(min_gap[0], gap))
	check(min_gap[0] > -1.0, "mantiene distancia (mínima %s)" % min_gap[0])
	t.free()
