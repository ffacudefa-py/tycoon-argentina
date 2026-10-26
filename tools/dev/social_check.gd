extends SceneTree
## Prueba de punta a punta de cuentas verificadas, nube y amigos contra los
## EMULADORES de Firebase (no toca el proyecto real). Ver docs/AMIGOS.md:
##   firebase emulators:exec --only auth,firestore --project coronadosdegloria \
##     "godot --headless --path . -s res://tools/dev/social_check.gd"
## con TYCOON_EMULATOR=127.0.0.1 en el entorno. Usa el código real de los
## autoloads Auth y Friends; las reglas son las de firestore.rules.
## Agregar -- --dev-save=user://social_check_save.json para no tocar la partida.
## La sesión y el estado de amigos de este equipo se respaldan y se restauran.

const AUTH_EMU := "http://127.0.0.1:9099"
const KEEP := ["user://session.cfg", "user://friends.cfg"]

var auth: Node
var friends: Node
var project := ""
var failures := 0


func _initialize() -> void:
	_run.call_deferred()


func _check(cond: bool, what: String) -> void:
	print(("  ok    " if cond else "  FALLA ") + what)
	if not cond:
		failures += 1


func _wait(fn: Callable) -> Variant:
	var box := [null]
	fn.call(func(r) -> void: box[0] = r if r != null else {})
	while box[0] == null:
		await process_frame
	return box[0]


func _http(method: int, url: String, body := "", token := "") -> Array:
	var http := HTTPRequest.new()
	root.add_child(http)
	var headers := ["Content-Type: application/json"]
	if token != "":
		headers.append("Authorization: Bearer " + token)
	http.request(url, PackedStringArray(headers), method, body)
	var res = await http.request_completed
	http.queue_free()
	var text: String = (res[3] as PackedByteArray).get_string_from_utf8()
	return [res[1], JSON.parse_string(text) if text != "" else {}]


## Abre el enlace del último correo de verificación de ese email (emulador).
func _click_verification_link(email: String) -> bool:
	var r := await _http(HTTPClient.METHOD_GET, "%s/emulator/v1/projects/%s/oobCodes" % [AUTH_EMU, project])
	var link := ""
	for c in r[1].get("oobCodes", []):
		if c.get("email", "") == email and c.get("requestType", "") == "VERIFY_EMAIL":
			link = c["oobLink"]
	if link == "":
		print("    sin enlace de verificación para %s: %s" % [email, str(r)])
		return false
	var done := await _http(HTTPClient.METHOD_GET, link)
	if done[0] != 200:
		print("    el enlace respondió %d: %s" % [done[0], str(done[1]).left(300)])
	return done[0] == 200


## Crea una cuenta, verifica el correo y deja la sesión iniciada en Auth.
func _account(email: String, verify: bool) -> Dictionary:
	auth.sign_out()
	var r: Dictionary = await _wait(func(cb: Callable) -> void: auth.sign_up(email, "clave-segura-123", cb))
	_check(r["ok"] and r.get("verify", false), "alta de %s pide verificar" % email)
	_check(not auth.verified(), "recién creada no está verificada")
	if verify:
		var c: Dictionary = await _wait(func(cb: Callable) -> void: auth.check_verified(cb))
		_check(not c["verified"], "antes de abrir el enlace sigue sin verificar")
		_check(await _click_verification_link(email), "se abre el enlace del correo")
		c = await _wait(func(cb: Callable) -> void: auth.check_verified(cb))
		_check(c["verified"] and auth.verified(), "después del enlace queda verificada")
	return {"uid": auth.uid, "email": email}


func _sign_in(email: String) -> void:
	auth.sign_out()
	await _wait(func(cb: Callable) -> void: auth.sign_in(email, "clave-segura-123", cb))
	friends._on_auth_changed()
	while friends._busy:
		await process_frame


func _save_doc(uid: String) -> int:
	var token: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	var body := JSON.stringify({"fields": {"save": {"stringValue": "{}"}}})
	var r := await _http(HTTPClient.METHOD_PATCH, CloudSync.docs_root(project) + "/saves/" + uid, body, token)
	return r[0]


func _run() -> void:
	if OS.get_environment("TYCOON_EMULATOR") == "":
		print("Definí TYCOON_EMULATOR=127.0.0.1 y corré dentro de firebase emulators:exec.")
		quit(2)
		return
	auth = root.get_node("Auth")
	friends = root.get_node("Friends")
	project = str(JSON.parse_string(FileAccess.get_file_as_string("res://data/firebase.json"))["project_id"])
	var game: Node = root.get_node("Game")
	if game.m == null:
		game.m = GameModel.new(GameData.load_default())
	var stamp := str(Time.get_ticks_usec())
	for f in KEEP:
		if FileAccess.file_exists(f):
			DirAccess.copy_absolute(f, f + ".check_bak")

	print("== Verificación de email y nube")
	var x := await _account("sinverificar_%s@test.invalid" % stamp, false)
	_check(await _save_doc(x["uid"]) == 403, "sin verificar: la nube rechaza la partida (403)")
	_check(not friends.enabled(), "sin verificar: amigos deshabilitado")
	var a := await _account("ana_%s@test.invalid" % stamp, true)
	_check(await _save_doc(a["uid"]) == 200, "verificada: la nube acepta su partida")
	_check(await _save_doc(x["uid"]) == 403, "verificada: no puede escribir la partida de otro")

	print("== Amigos")
	friends._on_auth_changed()
	while friends._busy:
		await process_frame
	_check(friends.status == "ok" and friends.my_code.length() == 6, "Ana tiene código (%s)" % friends.my_code)
	var code_a: String = friends.my_code
	var b := await _account("beto_%s@test.invalid" % stamp, true)
	game.m.set_company_name("Beto SRL")
	friends._on_auth_changed()
	while friends._busy:
		await process_frame
	var code_b: String = friends.my_code
	_check(code_b != "" and code_b != code_a, "Beto tiene otro código")
	var r: Dictionary = await friends.add_by_code(code_b)
	_check(not r["ok"], "no se puede agregar a uno mismo")
	r = await friends.add_by_code("ZZZZZZ")
	_check(not r["ok"], "código inexistente: %s" % r["msg"])
	r = await friends.add_by_code(code_a.to_lower())
	_check(r["ok"], "Beto le manda solicitud a Ana: %s" % r["msg"])
	r = await friends.add_by_code(code_a)
	_check(not r["ok"], "no se duplica la solicitud")
	# Beto no puede meterse solo en la lista de Ana sin solicitud de ella.
	var token_b: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	var forged := await _http(HTTPClient.METHOD_PATCH, CloudSync.docs_root(project) + "/players/%s/friends/%s" % [a["uid"], b["uid"]],
		JSON.stringify({"fields": {"since": {"doubleValue": 1.0}}}), token_b)
	_check(forged[0] == 403, "no se puede forzar una amistad (403)")
	var gift_early := await _http(HTTPClient.METHOD_PATCH, CloudSync.docs_root(project) + "/players/%s/gifts/%s" % [a["uid"], b["uid"]],
		JSON.stringify(FriendLogic.gift_fields(b["uid"], "Beto", 1, 1.0)), token_b)
	_check(gift_early[0] == 403, "sin ser amigos no se mandan mates (403)")

	await _sign_in(a["email"])
	_check(friends.requests.size() == 1 and friends.requests[0]["company"] == "Beto SRL", "Ana ve la solicitud de Beto")
	r = await friends.accept(b["uid"])
	_check(r["ok"], "Ana acepta: %s" % r["msg"])
	_check(friends.is_friend(b["uid"]) and friends.requests.is_empty(), "Beto en la lista de Ana y sin solicitudes")
	r = await friends.send_gift(b["uid"])
	_check(r["ok"], "Ana le convida un mate a Beto")
	r = await friends.send_gift(b["uid"])
	_check(not r["ok"], "un mate por día")

	await _sign_in(b["email"])
	_check(friends.is_friend(a["uid"]), "Ana en la lista de Beto (recíproco)")
	_check(friends.gifts.size() == 1, "Beto tiene el mate de Ana")
	var before: int = game.m.economy.money
	r = await friends.claim_gift(a["uid"])
	_check(r["ok"] and game.m.economy.money > before, "Beto abre el mate y gana plata: %s" % r["msg"])
	await friends.refresh()
	_check(friends.gifts.is_empty(), "el mate abierto ya no está en el servidor")
	r = await friends.remove(a["uid"])
	_check(r["ok"], "Beto saca a Ana")

	await _sign_in(a["email"])
	_check(not friends.is_friend(b["uid"]), "Ana tampoco lo tiene (se borró de los dos lados)")

	auth.sign_out()
	for f in KEEP:
		if FileAccess.file_exists(f + ".check_bak"):
			DirAccess.copy_absolute(f + ".check_bak", f)
			DirAccess.remove_absolute(f + ".check_bak")
		elif FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
	print("RESULTADO social_check: %s (%d fallas)" % ["OK" if failures == 0 else "FALLÓ", failures])
	quit(1 if failures > 0 else 0)
