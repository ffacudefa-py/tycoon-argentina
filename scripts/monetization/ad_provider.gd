class_name AdProvider
extends RefCounted
## Interfaz de proveedor de anuncios recompensados.
##
## Estados: off (no hay anuncios), initializing, loading, ready, showing,
## error (falló la carga: Monetization reintenta con espera creciente).
## show_rewarded() llama a done(earned, error) UNA sola vez:
##   earned = true SÓLO cuando el SDK confirma que el anuncio se completó.
##   earned = false si se cerró antes, si falló o si no había anuncio.

signal state_changed

var state := "off"
var last_error := ""


func provider_name() -> String:
	return "ninguno"


func setup(_cfg: AdConfig) -> void:
	pass


func load_ad() -> void:
	pass


func is_available() -> bool:
	return state == "ready"


func show_rewarded(_placement: String, done: Callable) -> void:
	done.call(false, "No hay anuncios disponibles.")


func destroy() -> void:
	pass


## Consentimiento (UMP): si el jugador tiene que poder cambiar su elección
## desde el juego (UE/Reino Unido), Configuración muestra el botón.
func privacy_options_required() -> bool:
	return false


func show_privacy_options(done: Callable) -> void:
	done.call()


func _set_state(s: String, err := "") -> void:
	state = s
	last_error = err
	state_changed.emit()
