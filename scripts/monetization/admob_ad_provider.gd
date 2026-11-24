class_name AdMobAdProvider
extends AdProvider
## Anuncios recompensados reales con Google AdMob (plugin Poing Godot AdMob
## 5.1, addons/admob). Sólo funciona en Android con el export Gradle.
##
## Antes de iniciar el SDK se pide el consentimiento con UMP (User Messaging
## Platform): en la UE/Reino Unido muestra el formulario configurado en AdMob
## (Privacidad y mensajes); en el resto no muestra nada. Si falla se sigue
## igual: AdMob usa la última elección guardada. En el entorno de prueba se
## simula estar en la UE para poder ver el formulario.
##
## Ciclo: setup() inicializa el SDK -> load_ad() pide un anuncio -> ready ->
## show_rewarded() lo muestra; on_user_earned_reward confirma la recompensa;
## al cerrarse se destruye y se pide el siguiente.

const NETWORK_ERROR := 2
const NO_FILL := 3

var _unit := ""
var _ad: RewardedAd
var _loader: RewardedAdLoader
var _done: Callable
var _earned := false
var _sdk_started := false
var _debug_eea := false


static func native_available() -> bool:
	return Engine.has_singleton("PoingGodotAdMob") and Engine.has_singleton("PoingGodotAdMobRewardedAd")


func provider_name() -> String:
	return "Google AdMob"


func setup(cfg: AdConfig) -> void:
	_unit = cfg.rewarded_unit
	_debug_eea = cfg.environment == "test"
	_set_state("initializing")
	_gather_consent(_debug_eea, func() -> void: load_ad())


## Inicia el SDK una sola vez, y sólo con consentimiento.
func _start_sdk(then: Callable) -> void:
	if _sdk_started:
		then.call()
		return
	_sdk_started = true
	# Juego para 13+: anuncios con clasificación máxima T (adolescentes).
	var rc := RequestConfiguration.new()
	rc.max_ad_content_rating = RequestConfiguration.MAX_AD_CONTENT_RATING_T
	MobileAds.set_request_configuration(rc)
	var listener := OnInitializationCompleteListener.new()
	listener.on_initialization_complete = func(_status: InitializationStatus) -> void: then.call()
	MobileAds.initialize(listener)


func _gather_consent(debug_eea: bool, then: Callable) -> void:
	var params := ConsentRequestParameters.new()
	if debug_eea:
		var dbg := ConsentDebugSettings.new()
		dbg.debug_geography = DebugGeography.Values.EEA
		params.consent_debug_settings = dbg
	var info := UserMessagingPlatform.consent_information
	info.update(params, func() -> void:
		print("[Anuncios] consentimiento: estado=%d formulario=%s" % [info.get_consent_status(), info.get_is_consent_form_available()])
		if info.get_is_consent_form_available() and info.get_consent_status() == ConsentInformation.ConsentStatus.REQUIRED:
			UserMessagingPlatform.load_consent_form(func(form: ConsentForm) -> void:
				form.show(func(_e: FormError) -> void: then.call()),
				func(e: FormError) -> void:
					push_warning("UMP: no se pudo cargar el formulario: %s" % (e.message if e else "?"))
					then.call())
		else:
			then.call(),
		func(e: FormError) -> void:
			push_warning("UMP: no se pudo consultar el consentimiento: %s" % (e.message if e else "?"))
			then.call())


func can_request_ads() -> bool:
	var s := UserMessagingPlatform.consent_information.get_consent_status()
	return s == ConsentInformation.ConsentStatus.OBTAINED or s == ConsentInformation.ConsentStatus.NOT_REQUIRED


func privacy_options_required() -> bool:
	return UserMessagingPlatform.consent_information.get_privacy_options_requirement_status() == ConsentInformation.PrivacyOptionsRequirementStatus.REQUIRED


func show_privacy_options(done: Callable) -> void:
	UserMessagingPlatform.show_privacy_options_form(func(_e: FormError) -> void: done.call())


func load_ad() -> void:
	if state in ["loading", "ready", "showing"]:
		return
	# Sin consentimiento (UE/Reino Unido: formulario rechazado, cerrado o no se
	# pudo consultar) no se inicia el SDK ni se pide ningún anuncio, tampoco en
	# los reintentos. Equivale a canRequestAds() de UMP.
	if not can_request_ads():
		# Sin internet al abrir no se pudo consultar: se vuelve a consultar en el
		# reintento (y si hace falta se muestra el formulario).
		if UserMessagingPlatform.consent_information.get_consent_status() == ConsentInformation.ConsentStatus.UNKNOWN and state != "initializing":
			_set_state("initializing")
			_gather_consent(_debug_eea, func() -> void:
				if can_request_ads():
					load_ad()
				else:
					_set_state("error", "No se pudo consultar tu consentimiento para los anuncios. Se reintenta solo."))
			return
		_set_state("error", "Para ver anuncios hace falta tu consentimiento (Configuración → Privacidad de los anuncios).")
		return
	if not _sdk_started:
		_set_state("loading")
		_start_sdk(func() -> void:
			_set_state("initializing")
			load_ad())
		return
	_set_state("loading")
	_loader = RewardedAdLoader.new()
	var cb := RewardedAdLoadCallback.new()
	cb.on_ad_loaded = func(ad: RewardedAd) -> void:
		_ad = ad
		_set_state("ready")
	cb.on_ad_failed_to_load = func(err: LoadAdError) -> void:
		_ad = null
		_set_state("error", _describe(err.code if err else -1, err.message if err else ""))
	_loader.load(_unit, AdRequest.new(), cb)


func show_rewarded(_placement: String, done: Callable) -> void:
	if state != "ready" or _ad == null:
		done.call(false, "Todavía no hay un anuncio cargado.")
		return
	_done = done
	_earned = false
	_set_state("showing")
	var fs := FullScreenContentCallback.new()
	fs.on_ad_dismissed_full_screen_content = func() -> void:
		_notify(_earned, "")
		_release()
	fs.on_ad_failed_to_show_full_screen_content = func(err: AdError) -> void:
		_notify(false, "No se pudo mostrar el anuncio (%s)." % (err.message if err else "error"))
		_release()
	_ad.full_screen_content_callback = fs
	var reward := OnUserEarnedRewardListener.new()
	reward.on_user_earned_reward = func(_item: RewardedItem) -> void:
		# Confirmación del SDK: se entrega ya, aunque el anuncio siga abierto.
		_earned = true
		_notify(true, "")
	_ad.show(reward)


## Avisa el resultado una única vez por anuncio.
func _notify(earned: bool, err: String) -> void:
	if _done.is_valid():
		var d := _done
		_done = Callable()
		d.call(earned, err)


## Libera el anuncio ya usado y pide el siguiente.
func _release() -> void:
	if _ad:
		_ad.destroy()
		_ad = null
	_set_state("idle")
	load_ad()


func destroy() -> void:
	if _ad:
		_ad.destroy()
		_ad = null
	_set_state("off")


static func _describe(code: int, msg: String) -> String:
	match code:
		NETWORK_ERROR:
			return "Sin conexión a internet."
		NO_FILL:
			return "No hay anuncios disponibles en este momento."
	return "No se pudo cargar el anuncio%s." % ((" (" + msg + ")") if msg != "" else "")
