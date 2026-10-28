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
const KEEP := ["user://session.cfg", "user://friends.cfg", "user://cloud.cfg"]

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


## Escribe campos crudos con la sesión actual (para probar que las reglas rechazan basura).
func _raw_doc(path: String, fields: Dictionary) -> int:
	var token: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	var r := await _http(HTTPClient.METHOD_PATCH, CloudSync.docs_root(project) + "/" + path, JSON.stringify({"fields": fields}), token)
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
	_check(await _raw_doc("saves/" + a["uid"], {"save": {"stringValue": "{}"}, "hack": {"booleanValue": true}}) == 403,
		"partida con campos de más: rechazada (403)")
	_check(await _raw_doc("saves/" + a["uid"], {"save": {"stringValue": "x".repeat(950000)}}) == 403,
		"partida de más de 900 KB: rechazada (403)")
	# Dos teléfonos con la misma cuenta: el segundo sube con la versión vieja.
	var root_saves: String = CloudSync.docs_root(project) + "/saves/" + a["uid"]
	var commit_url: String = CloudSync.docs_root(project) + ":commit"
	var tok: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	var first := await _http(HTTPClient.METHOD_GET, root_saves, "", tok)
	var seen := str(first[1].get("updateTime", ""))
	var f1 := {"fields": {"save": {"stringValue": "{\"telefono\":1}"}}}
	var up1 := await _http(HTTPClient.METHOD_POST, commit_url, JSON.stringify(CloudSync.commit_body(project, a["uid"], f1, seen)), tok)
	_check(up1[0] == 200 and CloudSync.committed_time(up1[1]) != "", "teléfono 1 sube con la versión que vio")
	var up2 := await _http(HTTPClient.METHOD_POST, commit_url, JSON.stringify(CloudSync.commit_body(project, a["uid"], f1, seen)), tok)
	_check(CloudSync.is_stale_write(up2[0], up2[1]), "teléfono 2 con versión vieja: rechazado, no pisa (%d)" % up2[0])
	var fresh := await _http(HTTPClient.METHOD_POST, commit_url, JSON.stringify(CloudSync.commit_body(project, a["uid"], f1, "")), tok)
	_check(CloudSync.is_stale_write(fresh[0], fresh[1]), "\"no había partida\" cuando sí hay: rechazado (%d)" % fresh[0])
	var other := await _http(HTTPClient.METHOD_POST, commit_url, JSON.stringify(CloudSync.commit_body(project, x["uid"], f1, "")), tok)
	_check(other[0] == 403, "por commit tampoco se escribe la partida de otro (403)")
	var prof := FriendLogic.profile_fields({"company": "Ana", "avatar": "perro", "stage": 2, "lifetime": 10, "prestige": 0, "code": "ABCDEF"}, 1.0)
	prof["fields"]["company"] = {"stringValue": "x".repeat(200)}
	_check(await _raw_doc("players/" + a["uid"], prof["fields"]) == 403, "perfil con nombre de 200 letras: rechazado (403)")
	prof["fields"]["company"] = {"stringValue": "Ana"}
	prof["fields"]["stage"] = {"integerValue": "999"}
	_check(await _raw_doc("players/" + a["uid"], prof["fields"]) == 403, "perfil con etapa imposible: rechazado (403)")
	_check(await _raw_doc("codes/ab", {"uid": {"stringValue": a["uid"]}}) == 403, "código con formato inválido: rechazado (403)")

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

	print("== Borrar la cuenta (Google Play)")
	var c := await _account("carla_%s@test.invalid" % stamp, true)
	friends._on_auth_changed()
	while friends._busy:
		await process_frame
	var code_c: String = friends.my_code
	_check(await _save_doc(c["uid"]) == 200, "Carla tiene partida en la nube")
	r = await friends.add_by_code(code_a)
	_check(r["ok"], "Carla le manda solicitud a Ana")
	await _sign_in(a["email"])
	r = await friends.accept(c["uid"])
	_check(r["ok"], "Ana acepta a Carla")
	await _sign_in(c["email"])
	r = await friends.send_gift(a["uid"])
	_check(r["ok"], "Carla le convida un mate a Ana")
	r = await auth.delete_account("contraseña-equivocada")
	_check(not r["ok"] and auth.signed_in(), "con la contraseña mal no se borra nada: " + r["msg"])
	r = await auth.delete_account("clave-segura-123")
	_check(r["ok"] and not auth.signed_in(), "Carla borra su cuenta: " + r["msg"])
	await _sign_in(a["email"])
	_check(not friends.is_friend(c["uid"]), "Carla ya no está en la lista de Ana")
	_check(friends.gifts.filter(func(g: Dictionary) -> bool: return g["uid"] == c["uid"]).is_empty(), "el mate de Carla se borró")
	var tok_a: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	var root_docs: String = CloudSync.docs_root(project)
	_check((await _http(HTTPClient.METHOD_GET, root_docs + "/players/" + c["uid"], "", tok_a))[0] == 404, "el perfil público de Carla no existe más")
	_check((await _http(HTTPClient.METHOD_GET, root_docs + "/codes/" + code_c, "", tok_a))[0] == 404, "el código de Carla quedó libre")
	var again: Dictionary = await _wait(func(cb: Callable) -> void:
		auth.sign_out()
		auth.sign_in(c["email"], "clave-segura-123", cb))
	_check(not again["ok"], "la cuenta de Carla ya no existe: " + str(again["msg"]))
	var admin := await _http(HTTPClient.METHOD_GET, root_docs + "/saves/" + c["uid"], "", "owner")
	_check(admin[0] == 404, "la partida de Carla en la nube se borró (vista de administrador)")

	auth.sign_out()
	for f in KEEP:
		if FileAccess.file_exists(f + ".check_bak"):
			DirAccess.copy_absolute(f + ".check_bak", f)
			DirAccess.remove_absolute(f + ".check_bak")
		elif FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
	print("RESULTADO social_check: %s (%d fallas)" % ["OK" if failures == 0 else "FALLÓ", failures])
	quit(1 if failures > 0 else 0)
