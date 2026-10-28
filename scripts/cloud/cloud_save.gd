extends Node
## Autoload "Cloud": progreso en la nube (Firestore, API REST) para quien
## inició sesión. La partida se sigue guardando primero en el teléfono; la
## nube es una copia que permite cambiar de teléfono o reinstalar el juego.
##
## - Al iniciar sesión (o al abrir el juego con sesión) compara la partida del
##   teléfono con la de la nube y decide con CloudSync.decide(): sube, baja
##   o le pregunta al jugador cuál conservar.
## - Después sube una copia cada UPLOAD_EVERY segundos si hubo cambios y al
##   pasar la app a segundo plano. Cada subida lleva como condición el
##   updateTime de la nube que vimos: si otro teléfono subió algo mientras
##   tanto, el servidor la rechaza y se vuelve a comparar (no se pisa).
## - La partida del teléfono es de la última cuenta que entró. Si entra otra,
##   esa partida se aparta (CloudSync.stash_path) y se usa la de la cuenta nueva.
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
var _cloud_update_time := ""       ## updateTime de la partida en la nube ("" = no hay)
var _cloud_seen := false           ## ya se consultó la nube en esta sesión
var _stash := {}                   ## uid -> {saved_at, update_time} de partidas apartadas
var _held := false                 ## en pausa mientras se borra la cuenta
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
	Auth.account_deleted.connect(_on_account_deleted)
	Game.saved.connect(func() -> void: _dirty = true)
	# Primera sincronización cuando la interfaz ya está armada.
	await get_tree().process_frame
	if enabled():
		_check_account()
		sync_now()


## Sólo con el juego de verdad corriendo (no en pruebas ni herramientas -s).
func enabled() -> bool:
	return project_id != "" and Auth.verified() and Main.instance != null and not _dev_mode() and not _held


## Pausa la nube (Auth.delete_account): que no se vuelva a subir la partida
## mientras se borra. Espera a que termine lo que esté en curso.
func hold(on: bool) -> void:
	_held = on
	while on and _inflight:
		await get_tree().process_frame


## La cuenta se borró: la partida del teléfono pasa a ser de invitado.
func _on_account_deleted(old_uid: String) -> void:
	_stash.erase(old_uid)
	SaveSystem.new(CloudSync.stash_path(old_uid)).delete_all()
	_synced_uid = ""
	_synced_saved_at = 0.0
	_cloud_update_time = ""
	_cloud_seen = false
	last_sync_wall = 0.0
	_dirty = false
	_save_state()


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
		upload() if _cloud_seen else sync_now()


func _notification(what: int) -> void:
	if what in [NOTIFICATION_APPLICATION_PAUSED, NOTIFICATION_APPLICATION_FOCUS_OUT, NOTIFICATION_WM_CLOSE_REQUEST]:
		if enabled() and _dirty and not _inflight and status != "conflict" and _cloud_seen:
			upload()


## Si cambió la cuenta, lo sincronizado antes no cuenta para esta; y si la
## partida del teléfono era de otra cuenta, se aparta en vez de subirla acá.
func _check_account() -> void:
	match CloudSync.account_action(_synced_uid, Auth.uid):
		"same":
			return
		"switch":
			_switch_local_game(_synced_uid, Auth.uid)
			return
	_synced_uid = Auth.uid
	_synced_saved_at = 0.0
	_cloud_update_time = ""
	_cloud_seen = false
	last_sync_wall = 0.0
	_save_state()


func _switch_local_game(from_uid: String, to_uid: String) -> void:
	Game.save()
	DirAccess.make_dir_recursive_absolute(CloudSync.stash_path(from_uid).get_base_dir())
	if not SaveSystem.new(CloudSync.stash_path(from_uid)).save(Game.m):
		push_warning("Cloud: no se pudo apartar la partida de la cuenta anterior")
	_stash[from_uid] = {"saved_at": _synced_saved_at, "update_time": _cloud_update_time}
	var back: Dictionary = _stash.get(to_uid, {})
	var stashed := SaveSystem.new(CloudSync.stash_path(to_uid))
	var payload := stashed.load_payload(Game.data) if stashed.exists() else {}
	_synced_uid = to_uid
	_cloud_seen = false
	last_sync_wall = 0.0
	if payload.is_empty():
		_synced_saved_at = 0.0
		_cloud_update_time = ""
		Game.reset_everything()
	else:
		_synced_saved_at = float(back.get("saved_at", 0.0))
		_cloud_update_time = str(back.get("update_time", ""))
		Game.replace_with(payload)
		stashed.delete_all()
	_stash.erase(to_uid)
	_save_state()
	if Main.instance:
		Main.instance.toast("Cambiaste de cuenta: tu partida anterior quedó guardada para esa cuenta.", "info")


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
	_cloud_update_time = str(doc.get("updateTime", "")) if ok else ""
	_cloud_seen = true
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
	var commit := CloudSync.commit_body(project_id, Auth.uid, body, _cloud_update_time)
	_request(HTTPClient.METHOD_POST, JSON.stringify(commit), func(ok: bool, code: int, resp: Dictionary) -> void:
		if ok:
			_synced_saved_at = float(doc["saved_at"])
			_cloud_update_time = CloudSync.committed_time(resp)
			_dirty = false
			_mark_synced()
		elif CloudSync.is_stale_write(code, resp):
			# Otro teléfono subió su partida: se compara de nuevo (y se pregunta).
			_cloud_seen = false
			sync_now.call_deferred()
		else:
			_fail(code, resp)
		if done.is_valid():
			done.call(ok), CloudSync.docs_root(project_id) + ":commit")


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

## `url` vacío = el documento saves/<uid> de esta cuenta.
func _request(method: int, body: String, cb: Callable, url := "") -> void:
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
		var err := http.request(url if url != "" else CloudSync.docs_root(project_id) + "/saves/" + Auth.uid, headers, method, body)
		if err != OK:
			http.queue_free()
			_inflight = false
			cb.call(false, 0, {}))


func _save_state() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("cloud", "uid", _synced_uid)
	cfg.set_value("cloud", "saved_at", _synced_saved_at)
	cfg.set_value("cloud", "last_sync", last_sync_wall)
	cfg.set_value("cloud", "update_time", _cloud_update_time)
	cfg.set_value("cloud", "stash", _stash)
	cfg.save(STATE_PATH)


func _load_state() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(STATE_PATH) != OK:
		return
	_synced_uid = str(cfg.get_value("cloud", "uid", ""))
	_synced_saved_at = float(cfg.get_value("cloud", "saved_at", 0.0))
	last_sync_wall = float(cfg.get_value("cloud", "last_sync", 0.0))
	_cloud_update_time = str(cfg.get_value("cloud", "update_time", ""))
	var st = cfg.get_value("cloud", "stash", {})
	_stash = st if st is Dictionary else {}
