extends Node
## Autoload "Auth": cuentas reales con Firebase Authentication (email y
## contraseña) por la API REST. No usa SDK nativo: funciona igual en Android
## y en escritorio.
##
## - La sesión (uid, email, nombre y refresh token) se guarda en
##   user://session.cfg; al abrir el juego se restaura sin pedir contraseña
##   y se renueva el token en segundo plano cuando hay internet.
## - Cerrar sesión NO toca la partida guardada en el teléfono.
## - Todavía no hay datos del juego en la nube: la cuenta queda lista para
##   asociar el progreso y la foto en una versión futura (docs/CUENTAS.md).

signal changed                              ## entró, salió o cambió el nombre
signal busy_changed(busy: bool)

const SESSION_PATH := "user://session.cfg"
const TIMEOUT := 15.0
const IDT := "https://identitytoolkit.googleapis.com/v1/accounts:%s?key=%s"
const STS := "https://securetoken.googleapis.com/v1/token?key=%s"

var api_key := ""
var uid := ""
var email := ""
var display_name := ""
var busy := false
var _refresh_token := ""
var _id_token := ""
var _id_expires := 0.0


func _ready() -> void:
	var f := FileAccess.open("res://data/firebase.json", FileAccess.READ)
	if f:
		var d = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			api_key = str(d.get("api_key", ""))
	_load_session()
	if signed_in():
		refresh_session.call_deferred()


func signed_in() -> bool:
	return uid != ""


func configured() -> bool:
	return api_key != ""


# ---------------------------------------------------------------- acciones
# Todas llaman a done({ok: bool, msg: String}).

func sign_up(p_email: String, password: String, done: Callable) -> void:
	var err := _validate(p_email, password)
	if err != "":
		done.call({"ok": false, "msg": err})
		return
	_post(IDT % ["signUp", api_key], {"email": p_email.strip_edges(), "password": password, "returnSecureToken": true},
		func(ok: bool, d: Dictionary, code: String) -> void:
			if ok:
				_accept(d)
				done.call({"ok": true, "msg": "¡Cuenta creada! Ya iniciaste sesión."})
			else:
				done.call({"ok": false, "msg": AuthErrors.message(code)}))


func sign_in(p_email: String, password: String, done: Callable) -> void:
	var err := _validate(p_email, password)
	if err != "":
		done.call({"ok": false, "msg": err})
		return
	_post(IDT % ["signInWithPassword", api_key], {"email": p_email.strip_edges(), "password": password, "returnSecureToken": true},
		func(ok: bool, d: Dictionary, code: String) -> void:
			if ok:
				_accept(d)
				done.call({"ok": true, "msg": "¡Hola de nuevo!"})
			else:
				done.call({"ok": false, "msg": AuthErrors.message(code)}))


func send_password_reset(p_email: String, done: Callable) -> void:
	var err := AuthErrors.validate_email(p_email)
	if err != "":
		done.call({"ok": false, "msg": err})
		return
	_post(IDT % ["sendOobCode", api_key], {"requestType": "PASSWORD_RESET", "email": p_email.strip_edges()},
		func(ok: bool, _d: Dictionary, code: String) -> void:
			# Por privacidad no se dice si el email existe o no.
			if ok or code.begins_with("EMAIL_NOT_FOUND"):
				done.call({"ok": true, "msg": "Si hay una cuenta con ese email, te llegó un correo para cambiar la contraseña."})
			else:
				done.call({"ok": false, "msg": AuthErrors.message(code)}))


func sign_out() -> void:
	uid = ""
	email = ""
	display_name = ""
	_refresh_token = ""
	_id_token = ""
	if FileAccess.file_exists(SESSION_PATH):
		DirAccess.remove_absolute(SESSION_PATH)
	changed.emit()


## Renueva el token. Si el servidor dice que la sesión ya no vale (cuenta
## borrada o deshabilitada) se cierra; si no hay internet se mantiene.
func refresh_session(done := Callable()) -> void:
	if _refresh_token == "" or not configured():
		return
	_request(STS % api_key, "grant_type=refresh_token&refresh_token=" + _refresh_token.uri_encode(),
		["Content-Type: application/x-www-form-urlencoded"],
		func(ok: bool, d: Dictionary, code: String) -> void:
			if ok:
				_id_token = str(d.get("id_token", ""))
				_refresh_token = str(d.get("refresh_token", _refresh_token))
				_id_expires = Time.get_unix_time_from_system() + float(d.get("expires_in", 3600))
				_save_session()
			elif code in ["TOKEN_EXPIRED", "INVALID_REFRESH_TOKEN", "USER_NOT_FOUND", "USER_DISABLED"]:
				sign_out()
				if Main.instance:
					Main.instance.toast(AuthErrors.message(code), "bad")
			if done.is_valid():
				done.call({"ok": ok, "msg": "" if ok else AuthErrors.message(code)}), true)


# ---------------------------------------------------------------- interno

func _validate(p_email: String, password: String) -> String:
	if not configured():
		return "Las cuentas no están configuradas en esta versión."
	var e := AuthErrors.validate_email(p_email)
	return e if e != "" else AuthErrors.validate_password(password)


func _accept(d: Dictionary) -> void:
	uid = str(d.get("localId", ""))
	email = str(d.get("email", ""))
	display_name = str(d.get("displayName", ""))
	_id_token = str(d.get("idToken", ""))
	_refresh_token = str(d.get("refreshToken", ""))
	_id_expires = Time.get_unix_time_from_system() + float(d.get("expiresIn", 3600))
	_save_session()
	changed.emit()


func _post(url: String, body: Dictionary, cb: Callable) -> void:
	_request(url, JSON.stringify(body), ["Content-Type: application/json"], cb)


## Una petición a la vez (evita dobles toques en "Ingresar").
func _request(url: String, body: String, headers: Array, cb: Callable, background := false) -> void:
	if busy and not background:
		cb.call(false, {}, "BUSY")
		return
	var http := HTTPRequest.new()
	http.timeout = TIMEOUT
	add_child(http)
	if not background:
		busy = true
		busy_changed.emit(true)
	http.request_completed.connect(func(result: int, status: int, _h: PackedStringArray, raw: PackedByteArray) -> void:
		http.queue_free()
		if not background:
			busy = false
			busy_changed.emit(false)
		var text := raw.get_string_from_utf8()
		if result == HTTPRequest.RESULT_TIMEOUT:
			cb.call(false, {}, "TIMEOUT")
		elif result != HTTPRequest.RESULT_SUCCESS:
			cb.call(false, {}, "NETWORK")
		elif status >= 200 and status < 300:
			var d = JSON.parse_string(text)
			cb.call(true, d if d is Dictionary else {}, "")
		else:
			cb.call(false, {}, AuthErrors.code_from_body(text)))
	var err := http.request(url, PackedStringArray(headers), HTTPClient.METHOD_POST, body)
	if err != OK:
		http.queue_free()
		if not background:
			busy = false
			busy_changed.emit(false)
		cb.call(false, {}, "NETWORK")


func _save_session() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("session", "uid", uid)
	cfg.set_value("session", "email", email)
	cfg.set_value("session", "name", display_name)
	cfg.set_value("session", "refresh_token", _refresh_token)
	cfg.save(SESSION_PATH)


func _load_session() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SESSION_PATH) != OK:
		return
	uid = str(cfg.get_value("session", "uid", ""))
	email = str(cfg.get_value("session", "email", ""))
	display_name = str(cfg.get_value("session", "name", ""))
	_refresh_token = str(cfg.get_value("session", "refresh_token", ""))
	if _refresh_token == "":
		uid = ""
