class_name PurchaseProvider
extends RefCounted
## Interfaz para compras dentro de la app (p. ej. Google Play Billing).
## purchase() debe llamar a done.call(true) sólo con la compra confirmada
## y verificada.


func is_available() -> bool:
	return false


func purchase(_product_id: String, done: Callable) -> void:
	done.call(false)
