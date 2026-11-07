extends Node
## Autoload "PushNotifications": notificaciones locales para volver al juego
## (plugin addons/coronados_notif, sólo en Android; en otras plataformas no hace nada).
##
## Al salir del juego agenda lo que arma NotifPlan (caja llena y hasta 2 eventos
## por día) y le pasa al plugin lo que necesita para el chequeo en segundo plano
## (versión nueva y solicitudes de amistad). Al volver cancela lo pendiente y,
## si salió un aviso de evento, se asegura de que ese evento esté pasando.
## Se apaga en Configuración ("notifications").

const STATE_PATH := "user://notifications.cfg"
const RELEASES_URL := "https://api.github.com/repos/ffacudefa-py/tycoon-argentina-descargas/releases/latest"

var _plugin: Object
var _scheduled: Array = []
var _state := {}
var _away := false


func _ready() -> void:
	if Engine.has_singleton("CoronadosNotif"):
		_plugin = Engine.get_singleton("CoronadosNotif")
	_load_state()
	Settings.changed.connect(func(key: String, _v: Variant) -> void:
		if key == "notifications" and not Settings.get_value("notifications"):
			_cancel_all()
			_configure_check(false))


func available() -> bool:
	return _plugin != null and not _dev_mode()


## Pide el permiso de Android 13+ (una vez, cuando el jugador ya entró al juego).
func ask_permission() -> void:
	if not available() or not Settings.get_value("notifications") or _state.get("asked", false):
		return
	_state["asked"] = true
	_save_state()
	OS.request_permission("android.permission.POST_NOTIFICATIONS")


func _notification(what: int) -> void:
	match what:
		NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_WM_CLOSE_REQUEST:
			_on_leave()
		NOTIFICATION_APPLICATION_RESUMED:
			_on_return()


func _on_leave() -> void:
	if not available() or _away:
		return
	_away = true
	_cancel_all()
	if not Settings.get_value("notifications"):
		_configure_check(false)
		return
	var now := Time.get_unix_time_from_system()
	var rng := RandomNumberGenerator.new()
	rng.randomize()
	_scheduled = NotifPlan.plan(Game.m, now, _tz(), _state, rng)
	for n in _scheduled:
		_plugin.schedule(int(n["id"]), str(n["title"]), str(n["text"]), int(float(n["at"]) * 1000.0))
	_state["scheduled"] = _scheduled
	_save_state()
	_configure_check(true)


func _on_return() -> void:
	if not available():
		return
	_away = false
	var now := Time.get_unix_time_from_system()
	var fire := NotifPlan.on_return(now, _tz(), _state.get("scheduled", []), _state)
	_cancel_all()
	_state["scheduled"] = []
	_save_state()
	# El aviso dijo que había un evento: que lo haya.
	var m := Game.m
	if fire != "" and (m.events["active"] as Array).is_empty() and m.data.event_by_id.has(fire):
		EventSystem.try_spawn(m, fire)


func _cancel_all() -> void:
	if _plugin == null:
		return
	_plugin.cancel(NotifPlan.ID_IDLE)
	for id in NotifPlan.ID_EVENTS:
		_plugin.cancel(id)


func _configure_check(on: bool) -> void:
	if _plugin == null:
		return
	var cfg := {"on": on and Settings.get_value("notifications"), "releases_url": RELEASES_URL,
		"version": str(ProjectSettings.get_setting("application/config/version"))}
	if Auth.verified():
		cfg.merge({"api_key": Auth.api_key, "refresh_token": Auth.background_token(), "uid": Auth.uid, "project": Friends.project_id})
	_plugin.configureCheck(JSON.stringify(cfg, "", false))


func _tz() -> int:
	return int(Time.get_time_zone_from_system().get("bias", -180))


func _dev_mode() -> bool:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--shots=") or a.begins_with("--dev-save="):
			return true
	return false


func _save_state() -> void:
	var f := FileAccess.open(STATE_PATH, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(_state))


func _load_state() -> void:
	var f := FileAccess.open(STATE_PATH, FileAccess.READ)
	if f:
		var d = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			_state = d
