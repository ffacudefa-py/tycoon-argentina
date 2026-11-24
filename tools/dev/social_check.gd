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


## Campos de saves/<uid> como los arma el juego (las reglas exigen el resumen).
func _save_fields(text: String, money := 0) -> Dictionary:
	return CloudSync.to_fields(text, {"saved_at": 1.0, "stage": 1, "lifetime": 0, "money": money,
		"company": "Test", "prestige": 0, "play_time": 0.0}, "test")


func _save_doc(uid: String) -> int:
	var token: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	var body := JSON.stringify(_save_fields("{}"))
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
	_check(await _raw_doc("saves/" + a["uid"], {"save": {"stringValue": "{}"}}) == 403,
		"partida sin resumen (etapa, ganado…): rechazada (403)")
	_check(await _raw_doc("saves/" + a["uid"], _save_fields("{}", -5)["fields"]) == 403,
		"partida con plata negativa en el resumen: rechazada (403)")
	# Dos teléfonos con la misma cuenta: el segundo sube con la versión vieja.
	var root_saves: String = CloudSync.docs_root(project) + "/saves/" + a["uid"]
	var commit_url: String = CloudSync.docs_root(project) + ":commit"
	var tok: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	var first := await _http(HTTPClient.METHOD_GET, root_saves, "", tok)
	var seen := str(first[1].get("updateTime", ""))
	var f1 := _save_fields("{\"telefono\":1}")
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
	var stolen := FriendLogic.profile_fields({"company": "Beto", "avatar": "perro", "stage": 1, "lifetime": 0, "prestige": 0, "code": code_a}, 1.0)
	_check(await _raw_doc("players/" + b["uid"], stolen["fields"]) == 403, "perfil con el código de otro: rechazado (403)")
	var bad_av := FriendLogic.profile_fields({"company": "Beto", "avatar": "../logo", "stage": 1, "lifetime": 0, "prestige": 0, "code": code_b}, 1.0)
	_check(await _raw_doc("players/" + b["uid"], bad_av["fields"]) == 403, "perfil con avatar que es una ruta: rechazado (403)")
	var r: Dictionary = await friends.add_by_code(code_b)
	_check(not r["ok"], "no se puede agregar a uno mismo")
	r = await friends.add_by_code("ZZZZZZ")
	_check(not r["ok"], "código inexistente: %s" % r["msg"])
	var tok_b0: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	_check((await _http(HTTPClient.METHOD_GET, CloudSync.docs_root(project) + "/players/" + a["uid"], "", tok_b0))[0] == 403,
		"15.2: un desconocido no lee el perfil (ni la foto) de Ana (403)")
	var badges_ok := FriendLogic.profile_fields({"company": "Beto SRL", "avatar": "emprendedor", "stage": 1, "lifetime": 0, "prestige": 0, "code": code_b, "badges": ["pionero", "primera_venta"]}, 1.0)
	_check(await _raw_doc("players/" + b["uid"], badges_ok["fields"]) == 200, "15.2: perfil con insignias: aceptado")
	var badges_bad := FriendLogic.profile_fields({"company": "Beto SRL", "avatar": "emprendedor", "stage": 1, "lifetime": 0, "prestige": 0, "code": code_b, "badges": ["a", "b", "c"]}, 1.0)
	badges_bad["fields"]["badges"]["arrayValue"]["values"].append({"stringValue": "d"})
	_check(await _raw_doc("players/" + b["uid"], badges_bad["fields"]) == 403, "15.2: más de 3 insignias: rechazado (403)")
	badges_bad["fields"]["badges"] = {"arrayValue": {"values": [{"stringValue": "../hack"}]}}
	_check(await _raw_doc("players/" + b["uid"], badges_bad["fields"]) == 403, "15.2: insignia con id raro: rechazado (403)")
	var foto := badges_ok.duplicate(true)
	foto["fields"]["photo"] = {"stringValue": "PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg=="}
	_check(await _raw_doc("players/" + b["uid"], foto["fields"]) == 403, "15.2: foto que no es imagen (texto en base64): rechazada (403)")
	var px := Image.create(8, 8, false, Image.FORMAT_RGB8)
	px.fill(Color.RED)
	foto["fields"]["photo"] = {"stringValue": Marshalls.raw_to_base64(px.save_webp_to_buffer())}
	_check(await _raw_doc("players/" + b["uid"], foto["fields"]) == 403, "15.2: foto WEBP: rechazada (403)")
	foto["fields"]["photo"] = {"stringValue": Marshalls.raw_to_base64(px.save_png_to_buffer())}
	_check(await _raw_doc("players/" + b["uid"], foto["fields"]) == 200, "15.2: foto PNG: aceptada")
	foto["fields"]["photo"] = {"stringValue": Marshalls.raw_to_base64(px.save_jpg_to_buffer())}
	_check(await _raw_doc("players/" + b["uid"], foto["fields"]) == 200, "15.2: foto JPEG: aceptada")
	_check(await _raw_doc("players/" + b["uid"], badges_ok["fields"]) == 200, "(sin foto otra vez)")
	# Spam: una solicitud sin sumar al contador del día no pasa.
	var tok_spam: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	var bare := await _http(HTTPClient.METHOD_PATCH, CloudSync.docs_root(project) + "/players/%s/requests/%s" % [a["uid"], b["uid"]],
		JSON.stringify(FriendLogic.request_fields(b["uid"], {"company": "Beto", "avatar": "emprendedor"}, 1.0)), tok_spam)
	_check(bare[0] == 403, "15.2: solicitud sin contar en el tope diario: rechazada (403)")
	var day := FriendLogic.utc_day(Time.get_unix_time_from_system())
	_check(await _raw_doc("limits/" + b["uid"], {"day": {"integerValue": str(day)}, "count": {"integerValue": "5"}}) == 403,
		"15.2: el contador no se puede saltear (de 0 a 5): rechazado (403)")
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
	var tok_a0: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	_check((await _http(HTTPClient.METHOD_GET, CloudSync.docs_root(project) + "/players/" + b["uid"], "", tok_a0))[0] == 200,
		"15.2: Ana sí lee el perfil de quien le pidió amistad")
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

	print("== Bloquear y denunciar (15.2)")
	await _sign_in(b["email"])
	r = await friends.add_by_code(code_a)
	_check(r["ok"], "Beto vuelve a mandarle solicitud a Ana")
	await _sign_in(a["email"])
	_check(friends.requests.size() == 1, "Ana la ve")
	r = await friends.report(b["uid"], "Beto SRL", "nombre")
	_check(r["ok"], "Ana denuncia y bloquea a Beto: %s" % r["msg"])
	_check(friends.requests.is_empty() and friends.is_blocked(b["uid"]), "la solicitud desaparece y Beto queda bloqueado")
	await friends.refresh()
	_check(friends.blocked.size() == 1 and friends.requests.is_empty(), "sigue así al recargar")
	var tok_ab: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	_check((await _http(HTTPClient.METHOD_POST, CloudSync.docs_root(project) + "/reports", JSON.stringify(FriendLogic.report_fields(b["uid"], a["uid"], "otro", "x", 1.0)), tok_ab))[0] == 403,
		"no se puede denunciar a nombre de otro (403)")
	var admin_rep := await _http(HTTPClient.METHOD_POST, CloudSync.docs_root(project) + ":runQuery", JSON.stringify({"structuredQuery": {"from": [{"collectionId": "reports"}]}}), "owner")
	_check(admin_rep[0] == 200 and (admin_rep[1] as Array).filter(func(x) -> bool: return x is Dictionary and x.has("document")).size() >= 1, "la denuncia quedó para el equipo")
	await _sign_in(b["email"])
	r = await friends.add_by_code(code_a)
	_check(not r["ok"], "Beto bloqueado no puede mandarle otra solicitud")
	var tok_bb: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	_check((await _http(HTTPClient.METHOD_GET, CloudSync.docs_root(project) + "/players/" + a["uid"], "", tok_bb))[0] == 403, "ni leer el perfil de Ana (403)")
	_check((await _http(HTTPClient.METHOD_GET, CloudSync.docs_root(project) + "/players/%s/blocked/%s" % [a["uid"], b["uid"]], "", tok_bb))[0] == 403, "ni ver la lista de bloqueados de Ana (403)")
	await _sign_in(a["email"])
	r = await friends.unblock(b["uid"])
	_check(r["ok"] and friends.blocked.is_empty(), "Ana lo desbloquea")
	await _sign_in(b["email"])
	r = await friends.add_by_code(code_a)
	_check(r["ok"], "desbloqueado, Beto puede volver a pedirle amistad")
	await _sign_in(a["email"])
	r = await friends.block(b["uid"], "Beto SRL")
	_check(r["ok"] and friends.requests.is_empty(), "Ana lo vuelve a bloquear (queda bloqueado para la prueba de borrado)")

	print("== Tope de solicitudes por día (15.2)")
	var spam := await _account("spam_%s@test.invalid" % stamp, true)
	friends._on_auth_changed()
	while friends._busy:
		await process_frame
	var dday := FriendLogic.utc_day(Time.get_unix_time_from_system())
	var ok_inc := true
	for i in FriendLogic.REQUESTS_PER_DAY:
		ok_inc = ok_inc and await _raw_doc("limits/" + spam["uid"], {"day": {"integerValue": str(dday)}, "count": {"integerValue": str(i + 1)}}) == 200
	_check(ok_inc, "el contador sube de a 1 hasta %d" % FriendLogic.REQUESTS_PER_DAY)
	_check(await _raw_doc("limits/" + spam["uid"], {"day": {"integerValue": str(dday)}, "count": {"integerValue": str(FriendLogic.REQUESTS_PER_DAY + 1)}}) == 403,
		"no pasa de %d (403)" % FriendLogic.REQUESTS_PER_DAY)
	_check(await _raw_doc("limits/" + spam["uid"], {"day": {"integerValue": str(dday)}, "count": {"integerValue": "1"}}) == 403, "ni se reinicia el mismo día (403)")
	var tok_sp: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	_check((await _http(HTTPClient.METHOD_DELETE, CloudSync.docs_root(project) + "/limits/" + spam["uid"], "", tok_sp))[0] == 403, "ni se borra (403)")
	r = await friends.add_by_code(code_b)
	_check(not r["ok"], "con el tope lleno no manda más: " + r["msg"])
	var forced := await _http(HTTPClient.METHOD_POST, CloudSync.docs_root(project) + ":commit", JSON.stringify({"writes": [
		{"update": {"name": "projects/%s/databases/(default)/documents/players/%s/requests/%s" % [project, b["uid"], spam["uid"]], "fields": FriendLogic.request_fields(spam["uid"], {"company": "Spam", "avatar": "emprendedor"}, 1.0)["fields"]}},
		{"update": {"name": "projects/%s/databases/(default)/documents/limits/%s" % [project, spam["uid"]], "fields": {"day": {"integerValue": str(dday)}, "count": {"integerValue": str(FriendLogic.REQUESTS_PER_DAY + 1)}}}}]}), tok_sp)
	_check(forced[0] == 403, "ni salteándose el juego (commit a mano): 403")

	print("== Pioneros: inscripción, registro y planilla (15.2)")
	var docs_root: String = CloudSync.docs_root(project)
	var commit_u: String = docs_root + ":commit"
	var su_email := "pionera_%s@gmail.com" % stamp
	var su := func(email: String, name: String, extra := {}) -> int:
		var fields := {"name": {"stringValue": name}, "email": {"stringValue": email}, "consent": {"booleanValue": true}, "android": {"booleanValue": true}}
		fields.merge(extra, true)
		var res := await _http(HTTPClient.METHOD_POST, commit_u, JSON.stringify({"writes": [{
			"update": {"name": "projects/%s/databases/(default)/documents/signups/%s" % [project, email], "fields": fields},
			"updateTransforms": [{"fieldPath": "created", "setToServerValue": "REQUEST_TIME"}],
			"currentDocument": {"exists": false}}]}))
		return res[0]
	_check(await su.call(su_email, "Pionera") == 200, "inscripción sin cuenta: aceptada")
	_check(await su.call(su_email, "Otra vez") != 200, "el mismo email no se anota dos veces")
	_check(await su.call("no-es-un-email", "X") != 200, "email inválido: rechazado")
	_check(await su.call("otra_%s@gmail.com" % stamp, "X".repeat(60)) != 200, "nombre de 60 letras: rechazado")
	_check(await su.call("otra_%s@gmail.com" % stamp, "Ok", {"admin": {"booleanValue": true}}) != 200, "campos de más (\"admin\"): rechazado")
	_check((await _http(HTTPClient.METHOD_GET, docs_root + "/signups/" + su_email))[0] != 200, "sin cuenta no se leen las inscripciones")
	var tok_any: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	_check((await _http(HTTPClient.METHOD_GET, docs_root + "/signups/" + su_email, "", tok_any))[0] == 403, "un jugador común tampoco (403)")
	# Registro desde el juego (en el AAB de la prueba cerrada; acá se fuerza).
	var pr: Dictionary = await friends.register_pioneer(true)
	_check(pr["ok"] and int(pr["doc"]["days"]) == 1, "el juego anota al pionero (1 día)")
	pr = await friends.register_pioneer(true)
	_check(pr["ok"] and int(pr["doc"]["days"]) == 1, "el mismo día no suma otro")
	var tday := FriendLogic.utc_day(Time.get_unix_time_from_system())
	var cheat := PioneerRegistry.to_fields({"email": auth.email, "company": "X", "first_day": tday - 20, "last_day": tday, "days": 20, "version": "15.2"})
	_check(await _raw_doc("pioneers/" + auth.uid, cheat["fields"]) == 403, "no se puede inventar 20 días (403)")
	var other_mail := PioneerRegistry.to_fields({"email": "otro@gmail.com", "company": "X", "first_day": tday, "last_day": tday, "days": 1, "version": "15.2"})
	_check(await _raw_doc("pioneers/" + auth.uid, other_mail["fields"]) == 403, "ni registrarse con el email de otro (403)")
	_check((await _http(HTTPClient.METHOD_GET, docs_root + "/pioneers/" + a["uid"], "", tok_any))[0] == 403, "un jugador no lee el registro de otro (403)")
	var pioneer_uid: String = auth.uid
	# Administración (email de isAdmin en firestore.rules).
	var adm := await _account("facundo.n.defagot@gmail.com", true)
	var tok_adm: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	var ls := await _http(HTTPClient.METHOD_GET, docs_root + "/signups?pageSize=50", "", tok_adm)
	_check(ls[0] == 200 and str(ls[1]).contains(su_email), "la administración ve las inscripciones")
	var lp := await _http(HTTPClient.METHOD_GET, docs_root + "/pioneers?pageSize=50", "", tok_adm)
	_check(lp[0] == 200 and str(lp[1]).contains(pioneer_uid), "y el registro de pioneros")
	var mark := await _http(HTTPClient.METHOD_PATCH, docs_root + "/signups/%s?updateMask.fieldPaths=invited" % su_email, JSON.stringify({"fields": {"invited": {"booleanValue": true}}}), tok_adm)
	_check(mark[0] == 200, "marca a la inscripta como invitada")
	var hack := await _http(HTTPClient.METHOD_PATCH, docs_root + "/signups/%s?updateMask.fieldPaths=email" % su_email, JSON.stringify({"fields": {"email": {"stringValue": "x@y.com"}}}), tok_adm)
	_check(hack[0] == 403, "pero no le cambia el email (403)")
	var lr := await _http(HTTPClient.METHOD_POST, docs_root + ":runQuery", JSON.stringify({"structuredQuery": {"from": [{"collectionId": "reports"}]}}), tok_adm)
	_check(lr[0] == 200, "y puede revisar las denuncias")

	print("== Moderación (15.2, web/pioneros-admin.html)")
	var mod_fields := func(photo_off: bool, name_off: bool, banned: bool) -> String:
		return JSON.stringify({"fields": {"photo_off": {"booleanValue": photo_off}, "name_off": {"booleanValue": name_off},
			"banned": {"booleanValue": banned}, "reason": {"stringValue": "prueba"}, "at": {"doubleValue": 1.0}}})
	_check((await _http(HTTPClient.METHOD_GET, docs_root + "/players/" + b["uid"], "", tok_adm))[0] == 200, "la administración ve el perfil denunciado")
	_check((await _http(HTTPClient.METHOD_PATCH, docs_root + "/moderation/" + b["uid"], mod_fields.call(true, true, false), tok_adm))[0] == 200, "le saca foto y nombre a Beto")
	_check((await _http(HTTPClient.METHOD_PATCH, docs_root + "/players/%s?updateMask.fieldPaths=company" % b["uid"],
		JSON.stringify({"fields": {"company": {"stringValue": FriendLogic.MOD_NAME}}}), tok_adm))[0] == 200, "y pone el nombre moderado en su perfil")
	_check((await _http(HTTPClient.METHOD_PATCH, docs_root + "/players/%s?updateMask.fieldPaths=company" % b["uid"],
		JSON.stringify({"fields": {"company": {"stringValue": "Cualquier cosa"}}}), tok_adm))[0] == 403, "pero no le puede poner otro nombre (403)")
	_check((await _http(HTTPClient.METHOD_PATCH, docs_root + "/players/%s?updateMask.fieldPaths=stage" % b["uid"],
		JSON.stringify({"fields": {"stage": {"integerValue": "9"}}}), tok_adm))[0] == 403, "ni tocarle otros datos (403)")
	await _sign_in(b["email"])
	_check(friends.status == "ok" and str(friends.me()["company"]) == FriendLogic.MOD_NAME, "el juego de Beto publica el nombre moderado")
	_check(friends.moderation_note() != "", "y le avisa: " + friends.moderation_note())
	var bp := FriendLogic.profile_of(game.m, b["uid"], friends.my_code)
	bp["company"] = "Nombre feo"
	_check(await _raw_doc("players/" + b["uid"], FriendLogic.profile_fields(bp, 1.0)["fields"]) == 403, "Beto no puede volver a poner su nombre (403)")
	var tok_b: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	_check((await _http(HTTPClient.METHOD_DELETE, docs_root + "/moderation/" + b["uid"], "", tok_b))[0] == 403, "ni borrar la sanción (403)")
	await _sign_in("facundo.n.defagot@gmail.com")
	tok_adm = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	_check((await _http(HTTPClient.METHOD_PATCH, docs_root + "/moderation/" + b["uid"], mod_fields.call(true, true, true), tok_adm))[0] == 200, "expulsa a Beto de Amigos")
	_check((await _http(HTTPClient.METHOD_DELETE, docs_root + "/players/" + b["uid"], "", tok_adm))[0] == 200, "y borra su perfil público")
	await _sign_in(b["email"])
	_check(friends.status == "error" and friends.last_error.contains("denuncias"), "Beto expulsado: Amigos le muestra el aviso")
	_check(await _raw_doc("players/" + b["uid"], FriendLogic.profile_fields(FriendLogic.profile_of(game.m, b["uid"], friends.my_code), 1.0)["fields"]) == 403, "y no puede recrear su perfil (403)")
	await _sign_in("facundo.n.defagot@gmail.com")
	tok_adm = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	_check((await _http(HTTPClient.METHOD_DELETE, docs_root + "/moderation/" + b["uid"], "", tok_adm))[0] == 200, "la administración levanta la sanción")
	await _sign_in(b["email"])
	_check(friends.status == "ok" and friends.moderation_note() == "" and str(friends.me()["company"]) != FriendLogic.MOD_NAME, "Beto vuelve a Amigos con su nombre")

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
	r = await friends.add_by_code(code_b)
	_check(r["ok"], "Carla le manda solicitud a Beto (queda sin aceptar)")
	r = await auth.delete_account("contraseña-equivocada")
	_check(not r["ok"] and auth.signed_in(), "con la contraseña mal no se borra nada: " + r["msg"])
	r = await auth.delete_account("clave-segura-123")
	_check(r["ok"] and not auth.signed_in(), "Carla borra su cuenta: " + r["msg"])
	await _sign_in(a["email"])
	_check(not friends.is_friend(c["uid"]), "Carla ya no está en la lista de Ana")
	_check(friends.gifts.filter(func(g: Dictionary) -> bool: return g["uid"] == c["uid"]).is_empty(), "el mate de Carla se borró")
	await _sign_in(b["email"])
	_check(friends.requests.filter(func(q: Dictionary) -> bool: return q["uid"] == c["uid"]).is_empty(), "la solicitud que Carla le mandó a Beto se borró")
	await _sign_in(a["email"])
	var tok_a: String = await _wait(func(cb: Callable) -> void: auth.get_token(cb))
	var root_docs: String = CloudSync.docs_root(project)
	_check((await _http(HTTPClient.METHOD_GET, root_docs + "/players/" + c["uid"], "", "owner"))[0] == 404, "el perfil público de Carla no existe más (vista de administrador)")
	_check((await _http(HTTPClient.METHOD_GET, root_docs + "/codes/" + code_c, "", tok_a))[0] == 404, "el código de Carla quedó libre")
	var again: Dictionary = await _wait(func(cb: Callable) -> void:
		auth.sign_out()
		auth.sign_in(c["email"], "clave-segura-123", cb))
	_check(not again["ok"], "la cuenta de Carla ya no existe: " + str(again["msg"]))
	var admin := await _http(HTTPClient.METHOD_GET, root_docs + "/saves/" + c["uid"], "", "owner")
	_check(admin[0] == 404, "la partida de Carla en la nube se borró (vista de administrador)")

	print("== Borrar la cuenta con bloqueos y denuncias (15.2)")
	await _sign_in(a["email"])
	r = await auth.delete_account("clave-segura-123")
	_check(r["ok"], "Ana (que bloqueó y denunció) borra su cuenta: " + r["msg"])
	var left_rep := await _http(HTTPClient.METHOD_POST, root_docs + ":runQuery", JSON.stringify({"structuredQuery": {"from": [{"collectionId": "reports"}],
		"where": {"fieldFilter": {"field": {"fieldPath": "reporter"}, "op": "EQUAL", "value": {"stringValue": a["uid"]}}}}}), "owner")
	_check(left_rep[0] == 200 and (left_rep[1] as Array).filter(func(x) -> bool: return x is Dictionary and x.has("document")).is_empty(), "sus denuncias se borraron")
	_check((await _http(HTTPClient.METHOD_GET, root_docs + "/players/%s/blocked/%s" % [a["uid"], b["uid"]], "", "owner"))[0] == 404, "su lista de bloqueados se borró")

	auth.sign_out()
	for f in KEEP:
		if FileAccess.file_exists(f + ".check_bak"):
			DirAccess.copy_absolute(f + ".check_bak", f)
			DirAccess.remove_absolute(f + ".check_bak")
		elif FileAccess.file_exists(f):
			DirAccess.remove_absolute(f)
	print("RESULTADO social_check: %s (%d fallas)" % ["OK" if failures == 0 else "FALLÓ", failures])
	quit(1 if failures > 0 else 0)
