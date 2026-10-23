class_name NotConfiguredAdProvider
extends AdProvider
## Proveedor nulo: anuncios desactivados (entorno de desarrollo, falta de
## IDs en producción o plataforma sin SDK). Nunca simula un anuncio.

var reason := "Los anuncios no están configurados."


func _init(p_reason := "") -> void:
	if p_reason != "":
		reason = p_reason
	last_error = reason


func provider_name() -> String:
	return "no configurado"
