extends Node
## Autoload "Cloud": progreso en la nube (Firestore, API REST) para quien
## inició sesión. La partida se sigue guardando primero en el teléfono; la
## nube es una copia que permite cambiar de teléfono o reinstalar el juego.
##
## - Al iniciar sesión (o al abrir el juego con sesión) compara la partida del
##   teléfono con la de la nube y decide con CloudSync.decide(): sube, baja
##   o le pregunta al jugador cuál conservar.
## - Después sube una copia cada UPLOAD_EVERY segundos si hubo cambios y al
##   pasar la app a segundo plano.
## - Sin internet no pasa nada: queda pendiente y se reintenta más tarde.
## - Desde la 0.7 hace falta el email verificado (Auth.verified()); las reglas
##   de Firestore lo exigen también del lado del servidor.
## Reglas de Firestore y configuración en docs/CUENTAS.md.

signal status_changed
signal conflict(local: Dictionary, cloud: Dictionary)

const STATE_PATH := "user://cloud.cfg"
const UPLOAD_EVERY := 90.0
const RETRY_EVERY := 120.0
const TIMEOUT := 20.0

var project_id := ""
## off (sin sesión) · syncing · ok · pending (hay cambios sin subir) · error · conflict
var status := "off"
var last_error := ""
var last_sync_wall := 0.0          ## cuándo se sincronizó por última vez (para la UI)

var _synced_uid := ""
var _synced_saved_at := 0.0        ## saved_at del documento que subimos/bajamos
var _dirty := false
var _timer := 0.0
var _inflight := false
var _conflict_doc := {}


func _ready() -> void:
	var f := FileAccess.open("res://data/firebase.json", FileAccess.READ)
	if f:
		var d = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			project_id = str(d.get("project_id", ""))
	_load_state()
	Auth.changed.connect(_on_auth_changed)
	Game.saved.connect(func() -> void: _dirty = true)
	# Primera sincronización cuando la interfaz ya está armada.
	await get_tree().process_frame
	if enabled():
		_check_account()
		sync_now()


## Sólo con el juego de verdad corriendo (no en pruebas ni herramientas -s).
func enabled() -> bool:
	return project_id != "" and Auth.verified() and Main.instance != null and not _dev_mode()


## Las capturas automáticas y las pruebas usan un guardado aparte: nunca tocan la nube.
func _dev_mode() -> bool:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--dev-save=") or a.begins_with("--shots="):
			return true
	return false


func _process(delta: float) -> void:
	if not enabled() or _inflight or status == "conflict":
		return
	_timer += delta
	if status == "error" and _timer >= RETRY_EVERY:
		sync_now()
	elif _dirty and _timer >= UPLOAD_EVERY:
		upload()


func _notification(what: int) -> void:
	if what in [NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_APPLICATION_FOCUS_OUT, NOTIFICATION_WM_CLOSE_REQUEST]:
		if enabled() and _dirty and not _inflight and status != "conflict":
			upload()


## Si cambió la cuenta, lo sincronizado antes no cuenta para esta.
func _check_account() -> void:
	if _synced_uid != Auth.uid:
		_synced_uid = Auth.uid
		_synced_saved_at = 0.0
		last_sync_wall = 0.0
		_save_state()


func _on_auth_changed() -> void:
	if Auth.verified():
		_check_account()
		sync_now()
	else:
		_conflict_doc = {}
		_set_status("off")


## Compara con la nube y decide (al conectarse).
func sync_now() -> void:
	if not enabled() or _inflight:
		return
	_set_status("syncing")
	_request(HTTPClient.METHOD_GET, "", _on_fetched)


func _on_fetched(ok: bool, code: int, doc: Dictionary) -> void:
	if not ok and code != 404:
		_fail(code, doc)
		return
	var cloud := CloudSync.summary_from_doc(doc) if ok else {}
	var local := CloudSync.summary_of(Game.m, Game.m.now())
	match CloudSync.decide(local, cloud, _synced_saved_at):
		"upload":
			upload()
		"download":
			_apply(doc, false)
		"ask":
			_conflict_doc = doc
			_set_status("conflict")
			conflict.emit(local, cloud)


## Sube la partida actual (reemplaza la de la nube).
func upload(done := Callable()) -> void:
	if not enabled() or _inflight:
		return
	Game.save()
	var doc := Game.saver.make_doc(Game.m)
	if doc.is_empty():
		_fail(0, {"msg": Game.saver.last_error})
		return
	var summary := CloudSync.summary_of(Game.m, float(doc["saved_at"]))
	var body := CloudSync.to_fields(JSON.stringify(doc, "", false), summary, str(ProjectSettings.get_setting("application/config/version")))
	_set_status("syncing")
	_request(HTTPClient.METHOD_PATCH, JSON.stringify(body), func(ok: bool, code: int, resp: Dictionary) -> void:
		if ok:
			_synced_saved_at = float(doc["saved_at"])
			_dirty = false
			_mark_synced()
		else:
			_fail(code, resp)
		if done.is_valid():
			done.call(ok))


## El jugador eligió en el aviso de conflicto.
func resolve(use_cloud: bool) -> void:
	if status != "conflict":
		return
	var doc := _conflict_doc
	_conflict_doc = {}
	if use_cloud:
		_apply(doc, true)
	else:
		_set_status("ok")
		upload()


func _apply(doc: Dictionary, chosen: bool) -> void:
	var payload := Game.saver.payload_from_text(CloudSync.save_text(doc), Game.data)
	if payload.is_empty():
		last_error = "La partida de la nube está dañada; se conserva la del teléfono."
		_set_status("error")
		upload()
		return
	Game.replace_with(payload)
	_synced_saved_at = CloudSync.summary_from_doc(doc)["saved_at"]
	_dirty = false
	_mark_synced()
	if Main.instance:
		Main.instance.toast("Partida recuperada de la nube." if not chosen else "Listo: seguís con la partida de la nube.", "good")


func _mark_synced() -> void:
	last_sync_wall = Time.get_unix_time_from_system()
	last_error = ""
	_timer = 0.0
	_save_state()
	_set_status("ok")


func _fail(code: int, resp: Dictionary) -> void:
	_timer = 0.0
	var msg := ""
	if resp.get("error") is Dictionary:
		msg = str(resp["error"].get("message", ""))
	elif resp.has("msg"):
		msg = str(resp["msg"])
	match code:
		0:
			last_error = "Sin conexión. Se reintenta más tarde."
		401:
			last_error = "La sesión venció. Volvé a iniciar sesión."
		403:
			last_error = "La nube no está habilitada para esta cuenta."
		_:
			last_error = "No se pudo sincronizar (%d). %s" % [code, msg]
	push_warning("Cloud: " + last_error)
	_set_status("error")


func _set_status(s: String) -> void:
	status = s
	status_changed.emit()


## Texto para Configuración y Perfil.
func status_text() -> String:
	match status:
		"off":
			if Auth.signed_in() and not Auth.email_verified:
				return "Verificá tu email para guardar tu progreso en la nube."
			return "Iniciá sesión para guardar tu progreso en la nube."
		"syncing":
			return "Sincronizando con la nube…"
		"conflict":
			return "Hay dos partidas distintas: elegí cuál conservar."
		"error":
			return last_error
	if last_sync_wall <= 0.0:
		return "Progreso en la nube activado."
	var ago := int(Time.get_unix_time_from_system() - last_sync_wall)
	var when := "recién" if ago < 60 else ("hace %d min" % (ago / 60) if ago < 3600 else "hace %d h" % (ago / 3600))
	return "Guardado en la nube %s%s." % [when, " (hay cambios por subir)" if _dirty else ""]


# ---------------------------------------------------------------- red

func _request(method: int, body: String, cb: Callable) -> void:
	_inflight = true
	Auth.get_token(func(token: String) -> void:
		if token == "":
			_inflight = false
			cb.call(false, 401, {})
			return
		var http := HTTPRequest.new()
		http.timeout = TIMEOUT
		add_child(http)
		http.request_completed.connect(func(result: int, code: int, _h: PackedStringArray, raw: PackedByteArray) -> void:
			http.queue_free()
			_inflight = false
			var d = JSON.parse_string(raw.get_string_from_utf8()) if raw.size() > 0 else {}
			if result != HTTPRequest.RESULT_SUCCESS:
				cb.call(false, 0, {})
			else:
				cb.call(code >= 200 and code < 300, code, d if d is Dictionary else {}))
		var headers := PackedStringArray(["Authorization: Bearer " + token, "Content-Type: application/json"])
		var err := http.request(CloudSync.docs_root(project_id) + "/saves/" + Auth.uid, headers, method, body)
		if err != OK:
			http.queue_free()
			_inflight = false
			cb.call(false, 0, {}))


func _save_state() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("cloud", "uid", _synced_uid)
	cfg.set_value("cloud", "saved_at", _synced_saved_at)
	cfg.set_value("cloud", "last_sync", last_sync_wall)
	cfg.save(STATE_PATH)


func _load_state() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(STATE_PATH) != OK:
		return
	_synced_uid = str(cfg.get_value("cloud", "uid", ""))
	_synced_saved_at = float(cfg.get_value("cloud", "saved_at", 0.0))
	last_sync_wall = float(cfg.get_value("cloud", "last_sync", 0.0))
