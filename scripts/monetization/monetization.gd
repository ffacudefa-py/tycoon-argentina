extends Node
## Autoload "Monetization": capa separada de la lógica del juego.
##
## Hoy NO hay proveedores reales configurados: los proveedores por defecto
## informan "no disponible" y jamás entregan recompensas. Para integrar
## anuncios o compras reales, ver docs/MONETIZACION.md: se implementa un
## AdProvider / PurchaseProvider (p. ej. con un plugin Android) y se asigna
## acá. El juego completo se puede jugar sin pagar.

signal rewarded_result(placement: String, success: bool)

## Ofertas previstas para anuncios recompensados (voluntarios).
const REWARDED_PLACEMENTS := {
	"turbo": {"title": "Turbo x2 por 10 minutos", "boost": {"mult": 2.0, "seconds": 600}},
	"caja_extra": {"title": "Caja extra: 5 minutos de ingresos", "income_seconds": 300, "min": 200},
}

## Catálogo previsto de compras opcionales (cosméticas o de comodidad).
const PRODUCTS := [
	{"id": "tema_noche", "title": "Tema visual 'Noche porteña'", "kind": "cosmético"},
	{"id": "pack_avatares", "title": "Pack de avatares del barrio", "kind": "cosmético"},
	{"id": "pack_inicial", "title": "Paquete inicial opcional", "kind": "comodidad"},
]

var ads: AdProvider = NotConfiguredAdProvider.new()
var purchases: PurchaseProvider = NotConfiguredPurchaseProvider.new()


func rewarded_available() -> bool:
	return ads.is_available()


func status_text() -> String:
	if ads.is_available():
		return "Anuncios recompensados disponibles (%s)." % ads.provider_name()
	return "En desarrollo: anuncios y compras todavía no están configurados. Todo el juego se puede jugar gratis."


## El jugador inicia voluntariamente. La recompensa SÓLO se entrega cuando
## el proveedor confirma que el anuncio se vio completo.
func show_rewarded(placement: String) -> void:
	if not REWARDED_PLACEMENTS.has(placement) or not ads.is_available():
		rewarded_result.emit(placement, false)
		return
	ads.show_rewarded(placement, func(completed: bool) -> void:
		if completed:
			_grant(placement)
		rewarded_result.emit(placement, completed))


func _grant(placement: String) -> void:
	var game := get_node_or_null("/root/Game")
	if game == null or game.m == null:
		return
	var offer: Dictionary = REWARDED_PLACEMENTS[placement]
	ProgressionSystem.grant(game.m, offer, "bonos")
