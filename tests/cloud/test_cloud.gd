extends TestCase
## Guardado en la nube: decisiones de sincronización y formato del documento
## (sin red; la prueba con las reglas reales está en tools/dev/social_check.gd).


func _summary(lifetime: int, saved_at: float, prestige := 0) -> Dictionary:
	return {"saved_at": saved_at, "stage": 1, "lifetime": lifetime, "money": 0, "company": "X", "prestige": prestige, "play_time": 0.0}


func test_decisiones() -> void:
	var local := _summary(50_000, 2000.0)
	eq(CloudSync.decide(local, {}, 0.0), "upload", "nube vacía: se sube")
	eq(CloudSync.decide(_summary(10, 2000.0), _summary(90_000, 1500.0), 0.0), "download", "partida nueva en el teléfono: se baja la de la nube")
	eq(CloudSync.decide(local, _summary(90_000, 1500.0), 1500.0), "upload", "la nube es lo último que subió este teléfono")
	eq(CloudSync.decide(local, _summary(90_000, 1800.0), 1500.0), "ask", "se jugó en otro lado: se pregunta")
	eq(CloudSync.decide(_summary(10, 2000.0, 1), _summary(90_000, 1800.0), 0.0), "ask", "con prestigio no es una partida nueva")


func test_documento_ida_y_vuelta() -> void:
	var m := make_model()
	m.economy.earn(123_456_789, "ventas")
	m.set_company_name("Empanadas de la Nube")
	var saver := SaveSystem.new("user://test_cloud_save.json")
	var doc := saver.make_doc(m)
	check(not doc.is_empty(), "documento armado")
	var s := CloudSync.summary_of(m, float(doc["saved_at"]))
	var body := CloudSync.to_fields(JSON.stringify(doc), s, "0.6.0")
	# Firestore devuelve los campos tal cual (integerValue como texto).
	var back: Dictionary = JSON.parse_string(JSON.stringify(body))
	var s2 := CloudSync.summary_from_doc(back)
	eq(s2["company"], "Empanadas de la Nube")
	eq(int(s2["lifetime"]), m.economy.lifetime_earned, "enteros grandes sin perder precisión")
	near(float(s2["saved_at"]), float(doc["saved_at"]), 0.001)
	var payload := saver.payload_from_text(CloudSync.save_text(back), data())
	check(not payload.is_empty(), "payload válido: " + saver.last_error)
	var m2 := make_model()
	m2.from_dict(payload)
	eq(m2.economy.money, m.economy.money, "la plata llega igual")
	eq(m2.profile["company"], "Empanadas de la Nube")


func test_rechaza_documentos_danados() -> void:
	var m := make_model()
	var saver := SaveSystem.new("user://test_cloud_save.json")
	var doc := saver.make_doc(m)
	doc["payload"] = (doc["payload"] as String).replace("\"money\"", "\"plata\"")
	check(saver.payload_from_text(JSON.stringify(doc), data()).is_empty(), "checksum distinto: se rechaza")
	check(saver.payload_from_text("no es json", data()).is_empty(), "texto inválido: se rechaza")
	check(CloudSync.summary_from_doc({}).is_empty(), "documento sin partida")


func test_cambio_de_cuenta() -> void:
	eq(CloudSync.account_action("abc", "abc"), "same", "misma cuenta")
	eq(CloudSync.account_action("", "abc"), "adopt", "partida de invitado: pasa a la cuenta")
	eq(CloudSync.account_action("abc", "xyz"), "switch", "partida de otra cuenta: se aparta, no se sube")
	eq(CloudSync.stash_path("a/b"), "user://accounts/a_b.json", "el uid no escapa de la carpeta")


func test_subida_condicionada() -> void:
	var f := {"fields": {"save": {"stringValue": "{}"}}}
	var nueva := CloudSync.commit_body("p", "u1", f, "")
	eq(nueva["writes"][0]["currentDocument"], {"exists": false}, "sin partida en la nube: sólo si sigue sin haber")
	var w: Dictionary = CloudSync.commit_body("p", "u1", f, "2026-10-28T10:00:00.1Z")["writes"][0]
	eq(w["currentDocument"], {"updateTime": "2026-10-28T10:00:00.1Z"}, "con partida: sólo si nadie la cambió")
	eq(w["update"]["name"], "projects/p/databases/(default)/documents/saves/u1")
	eq(CloudSync.committed_time({"writeResults": [{"updateTime": "T1"}]}), "T1")
	check(CloudSync.is_stale_write(400, {"error": {"status": "FAILED_PRECONDITION"}}), "otro teléfono subió antes")
	check(CloudSync.is_stale_write(409, {"error": {"status": "ALREADY_EXISTS"}}), "apareció una partida mientras tanto")
	check(not CloudSync.is_stale_write(403, {"error": {"status": "PERMISSION_DENIED"}}), "un 403 es otro error")
