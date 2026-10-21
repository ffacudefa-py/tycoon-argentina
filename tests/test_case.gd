class_name TestCase
extends RefCounted
## Base mínima para las pruebas (sin dependencias externas).

var failures: PackedStringArray = []
var current := ""
var clock_holder := {"t": 1_800_000_000.0}


func fail(msg: String) -> void:
	failures.append("%s: %s" % [current, msg])


func check(cond: bool, msg: String) -> void:
	if not cond:
		fail(msg)


func eq(a: Variant, b: Variant, msg := "") -> void:
	if typeof(a) != typeof(b) and not ((a is int or a is float) and (b is int or b is float)):
		fail("%s esperado %s (%s), obtenido %s (%s)" % [msg, str(b), type_string(typeof(b)), str(a), type_string(typeof(a))])
	elif a != b:
		fail("%s esperado %s, obtenido %s" % [msg, str(b), str(a)])


func near(a: float, b: float, tol: float, msg := "") -> void:
	if absf(a - b) > tol:
		fail("%s esperado ≈%s, obtenido %s" % [msg, str(b), str(a)])


var _shared_data: GameData


func data() -> GameData:
	if _shared_data == null:
		_shared_data = GameData.load_default()
	return _shared_data


## Modelo nuevo con reloj controlable y semilla fija.
func make_model(seed_value := 1, open_shop := true) -> GameModel:
	clock_holder["t"] = 1_800_000_000.0
	var holder := clock_holder
	var m := GameModel.new(data(), func() -> float: return holder["t"])
	if m == null or m.data == null:
		fail("no se pudo crear el GameModel (¿error de compilación?)")
	m.rng.seed = seed_value
	m.tz_bias_minutes = -180
	if open_shop:
		m.open_business("puesto")
		for p in m.derive("puesto")["products"]:
			m.biz["puesto"]["stock"][p["id"]] = float(p["cap"]) * 0.5
	return m


func advance_clock(seconds: float) -> void:
	clock_holder["t"] = float(clock_holder["t"]) + seconds


## Simula online en pasos de 0,1 s (como el juego).
func run(m: GameModel, seconds: float) -> void:
	var steps := int(round(seconds / 0.1))
	for i in steps:
		advance_clock(0.1)
		m.simulate(0.1)
