class_name AdProvider
extends RefCounted
## Interfaz de proveedor de anuncios recompensados.
## Una implementación real debe llamar a done.call(true) SÓLO cuando el SDK
## confirme que el anuncio se completó; ante error o cierre, done.call(false).


func provider_name() -> String:
	return "ninguno"


func is_available() -> bool:
	return false


func show_rewarded(_placement: String, done: Callable) -> void:
	done.call(false)
