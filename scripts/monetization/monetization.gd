extends Node
## Autoload "Monetization": capa separada de la lógica del juego.
##
## Anuncios recompensados: voluntarios, nunca bloquean el progreso.
## - Configuración: data/ads.json (entornos development / test / production).
## - Proveedor: AdMobAdProvider en Android si el plugin nativo está en el APK;
##   si no, NotConfiguredAdProvider con el motivo (jamás se simula un anuncio).
## - Recompensas: AdRewards. Se entregan SÓLO con la confirmación del SDK,
##   una vez por anuncio, y quedan registradas en el guardado.
## Compras: siguen sin proveedor (ver docs/MONETIZACION.md).

signal ads_changed                       ## cambió el estado (para la interfaz)
signal rewarded_result(offer_id: String, result: Dictionary)

## Catálogo previsto de compras opcionales (cosméticas o de comodidad).
const PRODUCTS := [
	{"id": "tema_noche", "title": "Tema visual 'Noche porteña'", "kind": "cosmético"},
	{"id": "pack_avatares", "title": "Pack de avatares del barrio", "kind": "cosmético"},
	{"id": "pack_inicial", "title": "Paquete inicial opcional", "kind": "comodidad"},
]

var cfg: AdConfig
var ads: AdProvider = NotConfiguredAdProvider.new()
var purchases: PurchaseProvider = NotConfiguredPurchaseProvider.new()
var busy := false                        ## hay un anuncio en curso (evita toques dobles)
var _retry_index := 0
var _retry_timer: Timer


func _ready() -> void:
	_retry_timer = Timer.new()
	_retry_timer.one_shot = true
	_retry_timer.timeout.connect(_retry)
	add_child(_retry_timer)
	cfg = AdConfig.load_default()
	if not cfg.enabled:
		use_provider(NotConfiguredAdProvider.new(cfg.disabled_reason))
	elif not OS.has_feature("android"):
		use_provider(NotConfiguredAdProvider.new("Los anuncios sólo están disponibles en la app de Android."))
	elif not (Engine.has_singleton("PoingGodotAdMob") and Engine.has_singleton("PoingGodotAdMobRewardedAd")):
		use_provider(NotConfiguredAdProvider.new("Falta el módulo de anuncios en esta compilación."))
	else:
		# Se carga por ruta: las clases del plugin sólo existen con el SDK nativo.
		use_provider(load("res://scripts/monetization/admob_ad_provider.gd").new())
	print("[Anuncios] entorno=%s beta=%s proveedor=%s %s" % [cfg.environment, OS.has_feature("beta"), ads.provider_name(), ads.last_error])


func use_provider(p: AdProvider) -> void:
	if ads:
		if ads.state_changed.is_connected(_on_state):
			ads.state_changed.disconnect(_on_state)
		ads.destroy()
	ads = p
	busy = false
	AdRewards.cancel_session()
	ads.state_changed.connect(_on_state)
	ads.setup(cfg if cfg else AdConfig.load_default())
	ads_changed.emit()


func _on_state() -> void:
	if ads.state == "ready":
		_retry_index = 0
	elif ads.state == "error" and _retry_timer.is_inside_tree():
		var waits := cfg.retry_seconds() if cfg else [30]
		_retry_timer.start(float(waits[mini(_retry_index, waits.size() - 1)]))
		_retry_index += 1
	ads_changed.emit()


func _retry() -> void:
	if ads.state == "error":
		ads.load_ad()


func _notification(what: int) -> void:
	# Al volver a la app (p. ej. después de recuperar internet) se reintenta ya.
	if what == NOTIFICATION_APPLICATION_RESUMED and ads.state == "error" and not busy:
		_retry_timer.stop()
		ads.load_ad()


func privacy_options_required() -> bool:
	return ads != null and ads.privacy_options_required()


func show_privacy_options() -> void:
	ads.show_privacy_options(func() -> void: pass)


## "ready", "loading", "error" u "off" (sin anuncios en esta versión).
func ad_state() -> String:
	if ads is NotConfiguredAdProvider or ads.state == "off":
		return "off"
	if ads.state in ["initializing", "loading", "idle"]:
		return "loading"
	return ads.state


func unavailable_reason() -> String:
	match ad_state():
		"off":
			return ads.last_error
		"loading":
			return "Cargando anuncio…"
		"error":
			return ads.last_error + " Se reintenta solo."
		"showing":
			return "Mostrando anuncio…"
	return ""


func rewarded_available() -> bool:
	return ad_state() == "ready" and not busy


func status_text() -> String:
	if ad_state() == "off":
		return "Anuncios: %s Todo el juego se puede jugar gratis." % ads.last_error
	return "Anuncios recompensados opcionales (%s%s)." % [ads.provider_name(), ", modo prueba" if cfg.environment == "test" else ""]


## El jugador inicia voluntariamente. Devuelve el resultado por la señal
## rewarded_result y por `on_result` (si se pasa).
func watch(offer_id: String, params := {}, on_result := Callable()) -> void:
	var reply := func(r: Dictionary) -> void:
		rewarded_result.emit(offer_id, r)
		if on_result.is_valid():
			on_result.call(r)
	if busy:
		reply.call({"ok": false, "msg": "Ya hay un anuncio en curso.", "granted": false})
		return
	if not rewarded_available():
		reply.call({"ok": false, "msg": unavailable_reason(), "granted": false})
		return
	var game := get_node_or_null("/root/Game")
	var m: GameModel = game.m if game else null
	if m == null:
		return
	var b := AdRewards.begin(m, cfg, offer_id, params)
	if not b["ok"]:
		reply.call({"ok": false, "msg": b["msg"], "granted": false})
		return
	busy = true
	ads_changed.emit()
	var token: String = b["token"]
	var answered := [false]
	ads.show_rewarded(offer_id, func(earned: bool, err: String) -> void:
		if answered[0]:
			return                       # aviso repetido del SDK: se ignora
		answered[0] = true
		busy = false
		var r := AdRewards.complete(m, token, earned)
		if err != "" and not r["granted"]:
			r["msg"] = err
		if r["granted"] and game:
			game.save()                  # el registro de la recompensa queda guardado ya
		ads_changed.emit()
		reply.call(r))
