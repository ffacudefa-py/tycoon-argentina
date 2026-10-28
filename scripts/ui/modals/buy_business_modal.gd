class_name BuyBusinessModal
extends RefCounted
## 10.0: cada negocio se abre en su provincia, así que "abrir" muestra la
## ficha de la provincia (producto, mercado y el botón ABRIR).


static func open(id: String) -> void:
	ZoneModal.open(Game.m.data.zone_for_business(id))
