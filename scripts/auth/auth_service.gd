extends Node
## Autoload "Auth": cuentas reales con Firebase Authentication (email y
## contraseña) por la API REST. No usa SDK nativo: funciona igual en Android
## y en escritorio.
##
## - La sesión (uid, email, nombre y refresh token) se guarda en
##   user://session.cfg; al abrir el juego se restaura sin pedir contraseña
##   y se renueva el token en segundo plano cuando hay internet.
## - Cerrar sesión NO toca la partida guardada en el teléfono.
## - Desde la 0.6 la partida se copia en la nube (autoload Cloud, Firestore);
##   la foto de perfil sigue sólo en el teléfono (docs/CUENTAS.md).
## - Desde la 0.7 el email se verifica: al crear la cuenta llega un correo con
##   un enlace y, hasta tocarlo, la nube y los amigos quedan en pausa (las
##   reglas de Firestore exigen email_verified en el token).
## - TYCOON_EMULATOR=127.0.0.1 usa los emuladores locales de Firebase
##   (Auth 9099); sólo para tools/dev/social_check.gd.

signal changed                              ## entró, salió o cambió el nombre
signal busy_changed(busy: bool)
signal verified_changed(verified: bool)

const SESSION_PATH := "user://session.cfg"
const TIMEOUT := 15.0
const IDT := "https://identitytoolkit.googleapis.com/v1/accounts:%s?key=%s"
const STS := "https://securetoken.googleapis.com/v1/token?key=%s"
## Tiempo mínimo entre dos correos de verificación (Firebase también limita).
const RESEND_EVERY := 60.0

var api_key := ""
var uid := ""
var email := ""
var display_name := ""
var email_verified := false
var busy := false
var last_verification_sent := 0.0
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
		refresh_session.call_deferred(func(r: Dictionary) -> void:
			if r["ok"] and not email_verified:
				check_verified())


func signed_in() -> bool:
	return uid != ""


## Sesión iniciada Y email confirmado: lo que piden la nube y los amigos.
func verified() -> bool:
	return signed_in() and email_verified


## Emuladores locales de Firebase (sólo herramientas de prueba).
static func emulator_host() -> String:
	return OS.get_environment("TYCOON_EMULATOR")


func _idt(action: String) -> String:
	var url := IDT % [action, api_key]
	return url.replace("https://", "http://%s:9099/" % emulator_host()) if emulator_host() != "" else url


func _sts() -> String:
	var url := STS % api_key
	return url.replace("https://", "http://%s:9099/" % emulator_host()) if emulator_host() != "" else url


func configured() -> bool:
	return api_key != ""


# ---------------------------------------------------------------- acciones
# Todas llaman a done({ok: bool, msg: String}).

func sign_up(p_email: String, password: String, done: Callable) -> void:
	var err := _validate(p_email, password)
	if err != "":
		done.call({"ok": false, "msg": err})
		return
	_post(_idt("signUp"), {"email": p_email.strip_edges(), "password": password, "returnSecureToken": true},
		func(ok: bool, d: Dictionary, code: String) -> void:
			if ok:
				_accept(d)
				send_verification(func(r: Dictionary) -> void:
					done.call({"ok": true, "verify": true, "msg": ("¡Cuenta creada! Te mandamos un correo a %s: tocá el enlace para confirmar que es tuyo." % email) if r["ok"] else "¡Cuenta creada! " + r["msg"]}))
			else:
				done.call({"ok": false, "msg": AuthErrors.message(code)}))


func sign_in(p_email: String, password: String, done: Callable) -> void:
	var err := _validate(p_email, password)
	if err != "":
		done.call({"ok": false, "msg": err})
		return
	_post(_idt("signInWithPassword"), {"email": p_email.strip_edges(), "password": password, "returnSecureToken": true},
		func(ok: bool, d: Dictionary, code: String) -> void:
			if ok:
				_accept(d)
				# signInWithPassword no dice si el email está verificado: se consulta.
				check_verified(func(_r: Dictionary) -> void:
					done.call({"ok": true, "verify": not email_verified, "msg": "¡Hola de nuevo!" if email_verified else "¡Hola! Falta confirmar tu email para usar la nube y los amigos."}))
			else:
				done.call({"ok": false, "msg": AuthErrors.message(code)}))


func send_password_reset(p_email: String, done: Callable) -> void:
	var err := AuthErrors.validate_email(p_email)
	if err != "":
		done.call({"ok": false, "msg": err})
		return
	_post(_idt("sendOobCode"), {"requestType": "PASSWORD_RESET", "email": p_email.strip_edges()},
		func(ok: bool, _d: Dictionary, code: String) -> void:
			# Por privacidad no se dice si el email existe o no.
			if ok or code.begins_with("EMAIL_NOT_FOUND"):
				done.call({"ok": true, "msg": "Si hay una cuenta con ese email, te llegó un correo para cambiar la contraseña."})
			else:
				done.call({"ok": false, "msg": AuthErrors.message(code)}))


## Manda (o reenvía) el correo con el enlace de verificación.
func send_verification(done := Callable()) -> void:
	var finish := func(r: Dictionary) -> void:
		if done.is_valid():
			done.call(r)
	if not signed_in():
		finish.call({"ok": false, "msg": "Iniciá sesión primero."})
		return
	var wait := RESEND_EVERY - (Time.get_unix_time_from_system() - last_verification_sent)
	if wait > 0.0:
		finish.call({"ok": false, "msg": "Esperá %d s para pedir otro correo." % ceili(wait)})
		return
	get_token(func(token: String) -> void:
		if token == "":
			finish.call({"ok": false, "msg": AuthErrors.message("NETWORK")})
			return
		_request(_idt("sendOobCode"), JSON.stringify({"requestType": "VERIFY_EMAIL", "idToken": token}), ["Content-Type: application/json"],
			func(ok: bool, _d: Dictionary, code: String) -> void:
				if ok:
					last_verification_sent = Time.get_unix_time_from_system()
					finish.call({"ok": true, "msg": "Te mandamos el correo a %s. Si no aparece, revisá spam." % email})
				else:
					finish.call({"ok": false, "msg": AuthErrors.message(code)}), true))


## Pregunta al servidor si el email ya se verificó. Si se verificó, renueva el
## token para que Firestore vea email_verified=true. done({ok, verified, msg}).
func check_verified(done := Callable()) -> void:
	var finish := func(r: Dictionary) -> void:
		if done.is_valid():
			done.call(r)
	get_token(func(token: String) -> void:
		if token == "":
			finish.call({"ok": false, "verified": email_verified, "msg": AuthErrors.message("NETWORK")})
			return
		_request(_idt("lookup"), JSON.stringify({"idToken": token}), ["Content-Type: application/json"],
			func(ok: bool, d: Dictionary, code: String) -> void:
				if not ok:
					finish.call({"ok": false, "verified": email_verified, "msg": AuthErrors.message(code)})
					return
				var users: Array = d.get("users", []) if d.get("users") is Array else []
				var now_verified: bool = not users.is_empty() and bool(users[0].get("emailVerified", false))
				if now_verified and not email_verified:
					# El token anterior dice email_verified=false: hace falta uno nuevo.
					_id_token = ""
					refresh_session(func(_r: Dictionary) -> void:
						_set_verified(true)
						finish.call({"ok": true, "verified": true, "msg": "¡Email verificado!"}))
					return
				_set_verified(now_verified)
				finish.call({"ok": true, "verified": now_verified, "msg": "" if now_verified else "Todavía no confirmaste el email: abrí el enlace del correo y volvé a tocar este botón."}), true))


func _set_verified(v: bool) -> void:
	if v == email_verified:
		return
	email_verified = v
	_save_session()
	verified_changed.emit(v)
	changed.emit()


func sign_out() -> void:
	uid = ""
	email = ""
	display_name = ""
	email_verified = false
	last_verification_sent = 0.0         # el límite de reenvío es por cuenta
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
	_request(_sts(), "grant_type=refresh_token&refresh_token=" + _refresh_token.uri_encode(),
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


## Token de acceso vigente para la API de Firestore. Si está por vencer lo
## renueva primero. done(token) recibe "" si no hay sesión o no hay internet.
func get_token(done: Callable) -> void:
	if not signed_in() or _refresh_token == "":
		done.call("")
		return
	if _id_token != "" and Time.get_unix_time_from_system() < _id_expires - 60.0:
		done.call(_id_token)
		return
	refresh_session(func(r: Dictionary) -> void: done.call(_id_token if r["ok"] else ""))


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
	email_verified = bool(d.get("emailVerified", false))
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
	cfg.set_value("session", "verified", email_verified)
	cfg.set_value("session", "refresh_token", _refresh_token)
	cfg.save(SESSION_PATH)


func _load_session() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(SESSION_PATH) != OK:
		return
	uid = str(cfg.get_value("session", "uid", ""))
	email = str(cfg.get_value("session", "email", ""))
	display_name = str(cfg.get_value("session", "name", ""))
	email_verified = bool(cfg.get_value("session", "verified", false))
	_refresh_token = str(cfg.get_value("session", "refresh_token", ""))
	if _refresh_token == "":
		uid = ""
