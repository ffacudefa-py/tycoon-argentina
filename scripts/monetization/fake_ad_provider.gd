class_name FakeAdProvider
extends AdProvider
## Proveedor de PRUEBAS automatizadas (tests/): permite simular carga,
## anuncio completo, anuncio cerrado antes, error y avisos duplicados.
## Nunca se usa en el juego.

var pending: Callable
var shows := 0


func provider_name() -> String:
	return "prueba"


func setup(_cfg: AdConfig) -> void:
	_set_state("ready")


func load_ad() -> void:
	_set_state("ready")


func fail_load(msg := "Sin conexión a internet.") -> void:
	_set_state("error", msg)


func show_rewarded(_placement: String, done: Callable) -> void:
	if state != "ready":
		done.call(false, "Todavía no hay un anuncio cargado.")
		return
	shows += 1
	pending = done
	_set_state("showing")


## Simula la respuesta del SDK. `twice` repite el aviso (debe ignorarse).
func finish(earned: bool, twice := false) -> void:
	var d := pending
	pending = Callable()
	_set_state("idle")
	if d.is_valid():
		d.call(earned, "")
		if twice:
			d.call(earned, "")
