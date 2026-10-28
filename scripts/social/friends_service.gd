extends Node
## Autoload "Friends": amigos con Firestore (API REST), para cuentas con el
## email verificado. Cada jugador tiene un código de 6 letras para que lo
## agreguen; los amigos aparecen en un ranking y se pueden convidar un mate
## por día (un premio chico al abrirlo). Reglas y formato: FriendLogic y
## docs/AMIGOS.md.
##
## Las acciones son corrutinas: `var r = await Friends.add_by_code("ABC123")`
## devuelve {ok, msg}. Sin internet no pasa nada grave: se avisa y listo.

signal changed

const STATE_PATH := "user://friends.cfg"
const TIMEOUT := 20.0
## Cada cuánto se actualizan solicitudes, regalos y el perfil público.
const REFRESH_EVERY := 300.0

var project_id := ""
## off (sin cuenta verificada) · loading · ok · error
var status := "off"
var last_error := ""
var my_code := ""
var friends: Array = []        ## perfiles de los amigos (FriendLogic.profile_from_doc)
var requests: Array = []       ## [{uid, company, avatar, at}]
var gifts: Array = []          ## [{uid, company, day}]

var _uid := ""
var _sent := {}                ## uid del amigo -> día en que le convidé un mate
var _timer := 0.0
var _busy := false
var _published := {}


func _ready() -> void:
	var f := FileAccess.open("res://data/firebase.json", FileAccess.READ)
	if f:
		var d = JSON.parse_string(f.get_as_text())
		if d is Dictionary:
			project_id = str(d.get("project_id", ""))
	Auth.changed.connect(_on_auth_changed)
	await get_tree().process_frame
	_on_auth_changed()


func enabled() -> bool:
	return project_id != "" and Auth.verified() and not _dev_mode()


## Las capturas y las pruebas nunca tocan la red (salvo contra el emulador).
func _dev_mode() -> bool:
	if Auth.emulator_host() != "":
		return false
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--dev-save=") or a.begins_with("--shots="):
			return true
	return false


func _process(delta: float) -> void:
	if not enabled() or _busy:
		return
	_timer += delta
	if _timer >= REFRESH_EVERY:
		refresh()


func _on_auth_changed() -> void:
	if enabled():
		if _uid != Auth.uid:
			_uid = Auth.uid
			_load_state()
		refresh()
	else:
		_uid = ""
		my_code = ""
		friends = []
		requests = []
		gifts = []
		_published = {}
		_set_status("off")


## Cosas para atender (solicitudes + regalos): el globito de la sección.
func pending_count() -> int:
	return requests.size() + gifts.size()


func is_friend(uid: String) -> bool:
	for p in friends:
		if p["uid"] == uid:
			return true
	return false


func sent_today(uid: String) -> bool:
	return int(_sent.get(uid, -1)) == ProgressionSystem.day_index(Game.m)


## Mi fila para el ranking.
func me() -> Dictionary:
	return FriendLogic.profile_of(Game.m, Auth.uid, my_code)


# ---------------------------------------------------------------- acciones

## Publica el perfil y trae amigos, solicitudes y regalos.
func refresh() -> Dictionary:
	if not enabled() or _busy:
		return {"ok": false, "msg": "Sin cuenta verificada."}
	_busy = true
	_timer = 0.0
	_set_status("loading")
	var r := await _refresh_inner()
	_busy = false
	if r["ok"]:
		last_error = ""
		_set_status("ok")
	else:
		last_error = r["msg"]
		_set_status("error")
	return r


func _refresh_inner() -> Dictionary:
	var r := await _ensure_profile()
	if not r["ok"]:
		return r
	var reqs := await _list("players/%s/requests" % Auth.uid)
	if not reqs["ok"]:
		return reqs
	requests = []
	for d in reqs["docs"]:
		var f: Dictionary = d.get("fields", {})
		requests.append({"uid": FriendLogic.doc_id(d), "company": FriendLogic.text(f, "company"), "avatar": FriendLogic.text(f, "avatar"), "at": FriendLogic.num(f, "at")})
	# Solicitudes de cuentas que se borraron (ya no tienen perfil): se descartan.
	if not requests.is_empty():
		var senders := await _batch_get(requests.map(func(q: Dictionary) -> String: return "players/" + q["uid"]))
		if senders["ok"]:
			var gone: Array = requests.filter(func(q: Dictionary) -> bool: return not senders["by_id"].has(q["uid"]))
			if not gone.is_empty():
				await _commit(gone.map(func(q: Dictionary) -> Dictionary: return {"delete": _name("players/%s/requests/%s" % [Auth.uid, q["uid"]])}))
				requests = requests.filter(func(q: Dictionary) -> bool: return senders["by_id"].has(q["uid"]))
	var gl := await _list("players/%s/gifts" % Auth.uid)
	if not gl["ok"]:
		return gl
	gifts = []
	for d in gl["docs"]:
		var f: Dictionary = d.get("fields", {})
		gifts.append({"uid": FriendLogic.doc_id(d), "company": FriendLogic.text(f, "company"), "day": FriendLogic.integer(f, "day")})
	var fl := await _list("players/%s/friends" % Auth.uid)
	if not fl["ok"]:
		return fl
	var ids: Array = []
	for d in fl["docs"]:
		ids.append(FriendLogic.doc_id(d))
	var profiles := await _batch_get(ids.map(func(id: String) -> String: return "players/" + id))
	if not profiles["ok"]:
		return profiles
	friends = []
	for id in ids:
		var p: Dictionary = profiles["by_id"].get(id, {})
		if p.is_empty():
			p = {"uid": id, "company": "(sin datos)", "avatar": "emprendedor", "stage": 1, "lifetime": 0, "prestige": 0, "code": ""}
		friends.append(p)
	return {"ok": true, "msg": ""}


## Perfil público + código propio (se crea la primera vez).
func _ensure_profile() -> Dictionary:
	if my_code == "":
		var got := await _call(HTTPClient.METHOD_GET, "players/" + Auth.uid)
		if got["code"] == 200:
			my_code = FriendLogic.profile_from_doc(got["data"]).get("code", "")
		elif got["code"] != 404:
			return _fail(got)
	if my_code == "":
		var rng := RandomNumberGenerator.new()
		rng.randomize()
		for attempt in 6:
			var code := FriendLogic.make_code(rng)
			# exists=false: si el código ya es de otro, falla y se prueba otro.
			var res := await _call(HTTPClient.METHOD_PATCH, "codes/%s?currentDocument.exists=false" % code,
				{"fields": {"uid": {"stringValue": Auth.uid}}})
			if res["code"] == 200:
				my_code = code
				break
			if res["code"] == 0 or res["code"] == 401:
				return _fail(res)
		if my_code == "":
			return {"ok": false, "msg": "No se pudo crear tu código de amigo. Probá más tarde."}
		_save_state()
	return await publish_profile(true)


func publish_profile(force := false) -> Dictionary:
	var p := me()
	if not force and p == _published:
		return {"ok": true, "msg": ""}
	var res := await _call(HTTPClient.METHOD_PATCH, "players/" + Auth.uid, FriendLogic.profile_fields(p, Time.get_unix_time_from_system()))
	if res["code"] != 200:
		return _fail(res)
	_published = p
	return {"ok": true, "msg": ""}


func add_by_code(text: String) -> Dictionary:
	if not enabled():
		return GameModel.fail("Verificá tu email para agregar amigos.")
	var code := FriendLogic.normalize_code(text)
	if code == "":
		return GameModel.fail("El código tiene %d letras y números (por ejemplo K7M2QX)." % FriendLogic.CODE_LEN)
	if code == my_code:
		return GameModel.fail("Ese es tu propio código: pasáselo a tus amigos.")
	if friends.size() >= int(Game.data.friends_cfg["max_friends"]):
		return GameModel.fail("Llegaste al máximo de %d amigos." % int(Game.data.friends_cfg["max_friends"]))
	var res := await _call(HTTPClient.METHOD_GET, "codes/" + code)
	if res["code"] == 404:
		return GameModel.fail("No hay nadie con el código %s." % code)
	if res["code"] != 200:
		return _fail(res)
	var fid := FriendLogic.text(res["data"].get("fields", {}), "uid")
	if fid == "" or fid == Auth.uid:
		return GameModel.fail("Ese código no sirve.")
	if is_friend(fid):
		return GameModel.fail("Ya son amigos.")
	for rq in requests:
		if rq["uid"] == fid:
			return await accept(fid)        # ya me había mandado una: se acepta
	var sent := await _call(HTTPClient.METHOD_PATCH, "players/%s/requests/%s" % [fid, Auth.uid],
		FriendLogic.request_fields(Auth.uid, me(), Time.get_unix_time_from_system()))
	if sent["code"] == 403:
		return GameModel.fail("Ya le mandaste una solicitud a ese código: falta que la acepte.")
	if sent["code"] != 200:
		return _fail(sent)
	return GameModel.ok("¡Solicitud enviada! Cuando la acepte, aparece en tu ranking.")


## Acepta una solicitud: los dos quedan en la lista del otro (un solo commit).
func accept(fid: String) -> Dictionary:
	var now := {"fields": {"since": {"doubleValue": Time.get_unix_time_from_system()}}}
	var res := await _commit([
		{"update": {"name": _name("players/%s/friends/%s" % [Auth.uid, fid]), "fields": now["fields"]}},
		{"update": {"name": _name("players/%s/friends/%s" % [fid, Auth.uid]), "fields": now["fields"]}},
		{"delete": _name("players/%s/requests/%s" % [Auth.uid, fid])},
	])
	if res["code"] != 200:
		return _fail(res)
	await refresh()
	return GameModel.ok("¡Ahora son amigos!")


func reject(fid: String) -> Dictionary:
	var res := await _call(HTTPClient.METHOD_DELETE, "players/%s/requests/%s" % [Auth.uid, fid])
	if res["code"] != 200 and res["code"] != 404:
		return _fail(res)
	requests = requests.filter(func(r: Dictionary) -> bool: return r["uid"] != fid)
	changed.emit()
	return GameModel.ok("Solicitud rechazada.")


func remove(fid: String) -> Dictionary:
	var res := await _commit([
		{"delete": _name("players/%s/friends/%s" % [Auth.uid, fid])},
		{"delete": _name("players/%s/friends/%s" % [fid, Auth.uid])},
	])
	if res["code"] != 200:
		return _fail(res)
	friends = friends.filter(func(p: Dictionary) -> bool: return p["uid"] != fid)
	changed.emit()
	return GameModel.ok("Lo sacaste de tus amigos.")


## Convida un mate a un amigo (uno por día por amigo).
func send_gift(fid: String) -> Dictionary:
	if sent_today(fid):
		return GameModel.fail("Hoy ya le convidaste un mate.")
	var day := ProgressionSystem.day_index(Game.m)
	var res := await _call(HTTPClient.METHOD_PATCH, "players/%s/gifts/%s" % [fid, Auth.uid],
		FriendLogic.gift_fields(Auth.uid, str(Game.m.profile["company"]), day, Time.get_unix_time_from_system()))
	if res["code"] != 200:
		return _fail(res)
	_sent[fid] = day
	_save_state()
	changed.emit()
	return GameModel.ok("¡Mate enviado! Mañana le podés convidar otro.")


## Abre un regalo recibido: se borra del servidor y después se da el premio.
func claim_gift(fid: String) -> Dictionary:
	var gift := {}
	for g in gifts:
		if g["uid"] == fid:
			gift = g
	if gift.is_empty():
		return GameModel.fail("Ese regalo ya no está.")
	if FriendLogic.gifts_left_today(Game.m) <= 0:
		return FriendLogic.claim_gift(Game.m, gift["company"])     # mensaje de cupo
	var res := await _call(HTTPClient.METHOD_DELETE, "players/%s/gifts/%s" % [Auth.uid, fid])
	if res["code"] != 200:
		return _fail(res)
	gifts = gifts.filter(func(g: Dictionary) -> bool: return g["uid"] != fid)
	var r := FriendLogic.claim_gift(Game.m, gift["company"])
	Game.save()
	changed.emit()
	return r


# ---------------------------------------------------------------- red

func _name(path: String) -> String:
	return "projects/%s/databases/(default)/documents/%s" % [project_id, path]


func _list(path: String) -> Dictionary:
	var res := await _call(HTTPClient.METHOD_GET, path + "?pageSize=100")
	if res["code"] != 200:
		return _fail(res)
	var docs = res["data"].get("documents", []) if res["data"] is Dictionary else []
	return {"ok": true, "docs": docs if docs is Array else []}


func _batch_get(paths: Array) -> Dictionary:
	var by_id := {}
	if paths.is_empty():
		return {"ok": true, "by_id": by_id}
	var res := await _call(HTTPClient.METHOD_POST, ":batchGet", {"documents": paths.map(_name)})
	if res["code"] != 200:
		return _fail(res)
	if res["data"] is Array:
		for item in res["data"]:
			if item is Dictionary and item.get("found") is Dictionary:
				var p := FriendLogic.profile_from_doc(item["found"])
				if not p.is_empty():
					by_id[p["uid"]] = p
	return {"ok": true, "by_id": by_id}


func _commit(writes: Array) -> Dictionary:
	return await _call(HTTPClient.METHOD_POST, ":commit", {"writes": writes})


## Borra todo lo de esta cuenta en Firestore (antes de borrar la cuenta):
## partida, perfil público, código de amigo, la lista de amigos de los dos
## lados, solicitudes y mates recibidos y los mates que mandé. Un solo commit:
## o se borra todo o nada.
func delete_my_data() -> Dictionary:
	if project_id == "" or not Auth.verified():
		return {"ok": true, "msg": ""}
	var me_uid := Auth.uid
	var writes := []
	for sub in ["friends", "requests", "gifts"]:
		var l := await _list("players/%s/%s" % [me_uid, sub])
		if not l["ok"]:
			return l
		for d in l["docs"]:
			var id := FriendLogic.doc_id(d)
			writes.append({"delete": _name("players/%s/%s/%s" % [me_uid, sub, id])})
			if sub == "friends":
				writes.append({"delete": _name("players/%s/friends/%s" % [id, me_uid])})
				writes.append({"delete": _name("players/%s/gifts/%s" % [id, me_uid])})
	var code := my_code
	if code == "":
		var got := await _call(HTTPClient.METHOD_GET, "players/" + me_uid)
		if got["code"] == 200:
			code = FriendLogic.profile_from_doc(got["data"]).get("code", "")
		elif got["code"] != 404:
			return _fail(got)
	if code != "":
		# Sólo si el código es mío (la regla de borrado mira el dueño).
		var c := await _call(HTTPClient.METHOD_GET, "codes/" + code)
		if c["code"] == 200 and FriendLogic.text(c["data"].get("fields", {}), "uid") == me_uid:
			writes.append({"delete": _name("codes/" + code)})
	writes.append({"delete": _name("players/" + me_uid)})
	writes.append({"delete": _name("saves/" + me_uid)})
	# Firestore acepta hasta 500 escrituras por commit; con 50 amigos son ~160.
	var res := await _commit(writes)
	if res["code"] != 200:
		return _fail(res)
	friends = []
	requests = []
	gifts = []
	my_code = ""
	_sent = {}
	if FileAccess.file_exists(STATE_PATH):
		DirAccess.remove_absolute(STATE_PATH)
	return {"ok": true, "msg": ""}


## Una petición a Firestore. Devuelve {code, data}; code 0 = sin conexión.
func _call(method: int, path: String, body: Variant = null) -> Dictionary:
	var box := [null]
	Auth.get_token(func(t: String) -> void: box[0] = t)
	while box[0] == null:
		await get_tree().process_frame
	var token: String = box[0]
	if token == "":
		return {"code": 401, "data": {}}
	var url := CloudSync.docs_root(project_id) + ("" if path.begins_with(":") else "/") + path
	var http := HTTPRequest.new()
	http.timeout = TIMEOUT
	add_child(http)
	var headers := PackedStringArray(["Authorization: Bearer " + token, "Content-Type: application/json"])
	var err := http.request(url, headers, method, "" if body == null else JSON.stringify(body))
	if err != OK:
		http.queue_free()
		return {"code": 0, "data": {}}
	var res: Array = await http.request_completed
	http.queue_free()
	if res[0] != HTTPRequest.RESULT_SUCCESS:
		return {"code": 0, "data": {}}
	var raw: PackedByteArray = res[3]
	var data = JSON.parse_string(raw.get_string_from_utf8()) if raw.size() > 0 else {}
	return {"code": int(res[1]), "data": data if data != null else {}}


func _fail(res: Dictionary) -> Dictionary:
	var code: int = res.get("code", 0)
	var msg := ""
	match code:
		0:
			msg = "Sin conexión. Probá de nuevo en un rato."
		401:
			msg = "La sesión venció. Volvé a iniciar sesión."
		403:
			msg = "El servidor no permitió la acción (¿email sin verificar?)."
		_:
			var d = res.get("data", {})
			var detail := str(d.get("error", {}).get("message", "")) if d is Dictionary and d.get("error") is Dictionary else ""
			msg = "No se pudo completar (%d). %s" % [code, detail]
	push_warning("Friends: " + msg)
	return {"ok": false, "msg": msg}


func _set_status(s: String) -> void:
	status = s
	changed.emit()


func _save_state() -> void:
	var cfg := ConfigFile.new()
	cfg.set_value("friends", "uid", _uid)
	cfg.set_value("friends", "code", my_code)
	cfg.set_value("friends", "sent", _sent)
	cfg.save(STATE_PATH)


func _load_state() -> void:
	my_code = ""
	_sent = {}
	var cfg := ConfigFile.new()
	if cfg.load(STATE_PATH) != OK or str(cfg.get_value("friends", "uid", "")) != _uid:
		return
	my_code = str(cfg.get_value("friends", "code", ""))
	var s = cfg.get_value("friends", "sent", {})
	_sent = s if s is Dictionary else {}
