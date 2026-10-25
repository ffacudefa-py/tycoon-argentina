extends SceneTree
## Verificación manual del guardado en la nube contra el Firestore real:
##   godot --headless --path . -s res://tools/dev/cloud_check.gd
## Crea una cuenta descartable, sube una partida, la vuelve a leer, prueba
## que otra cuenta NO pueda leerla (reglas) y borra todo al final.

const URL := "https://firestore.googleapis.com/v1/projects/%s/databases/(default)/documents/saves/%s"

var auth: Node
var project := ""


func _initialize() -> void:
	_run.call_deferred()


func _wait(fn: Callable) -> Variant:
	var box := [null]
	fn.call(func(r) -> void: box[0] = r if r != null else {})
	while box[0] == null:
		await process_frame
	return box[0]


func _http(method: int, uid: String, token: String, body := "") -> Array:
	var http := HTTPRequest.new()
	root.add_child(http)
	http.request(URL % [project, uid], ["Authorization: Bearer " + token, "Content-Type: application/json"], method, body)
	var res = await http.request_completed
	http.queue_free()
	var text: String = (res[3] as PackedByteArray).get_string_from_utf8()
	return [res[1], JSON.parse_string(text) if text != "" else {}]


func _new_account() -> Dictionary:
	var email := "nube_%d@tycoon-test.invalid" % Time.get_ticks_usec()
	var r: Dictionary = await _wait(func(cb: Callable) -> void: auth.sign_up(email, "clave-segura-123", cb))
	return {"ok": r["ok"], "uid": auth.uid, "token": auth._id_token}


func _delete_account(token: String) -> void:
	var http := HTTPRequest.new()
	root.add_child(http)
	http.request("https://identitytoolkit.googleapis.com/v1/accounts:delete?key=" + auth.api_key, ["Content-Type: application/json"], HTTPClient.METHOD_POST, JSON.stringify({"idToken": token}))
	await http.request_completed
	http.queue_free()


func _run() -> void:
	auth = root.get_node("Auth")
	project = str(JSON.parse_string(FileAccess.get_file_as_string("res://data/firebase.json"))["project_id"])
	var a: Dictionary = await _new_account()
	auth.sign_out()
	var b: Dictionary = await _new_account()
	auth.sign_out()
	print("cuentas de prueba -> ", a["ok"], " ", b["ok"])

	var m := GameModel.new(GameData.load_default())
	m.economy.earn(987_654_321, "ventas")
	m.set_company_name("Prueba Nube")
	var saver := SaveSystem.new("user://cloud_check.json")
	var doc := saver.make_doc(m)
	var body := CloudSync.to_fields(JSON.stringify(doc), CloudSync.summary_of(m, float(doc["saved_at"])), "check")

	var r: Array = await _http(HTTPClient.METHOD_GET, a["uid"], a["token"])
	print("leer antes de subir (espera 404) -> HTTP ", r[0])
	r = await _http(HTTPClient.METHOD_PATCH, a["uid"], a["token"], JSON.stringify(body))
	print("subir -> HTTP ", r[0], "" if r[0] == 200 else " " + str(r[1]))
	r = await _http(HTTPClient.METHOD_GET, a["uid"], a["token"])
	var s := CloudSync.summary_from_doc(r[1]) if r[1] is Dictionary else {}
	var payload := saver.payload_from_text(CloudSync.save_text(r[1]), m.data) if r[1] is Dictionary else {}
	print("leer -> HTTP ", r[0], " empresa=", s.get("company", "?"), " plata=", s.get("money", "?"), " payload_ok=", not payload.is_empty())
	r = await _http(HTTPClient.METHOD_GET, a["uid"], b["token"])
	print("otra cuenta lee (espera 403) -> HTTP ", r[0])
	r = await _http(HTTPClient.METHOD_PATCH, a["uid"], b["token"], JSON.stringify(body))
	print("otra cuenta escribe (espera 403) -> HTTP ", r[0])
	r = await _http(HTTPClient.METHOD_GET, a["uid"], "")
	print("sin sesión lee (espera 401/403) -> HTTP ", r[0])

	r = await _http(HTTPClient.METHOD_DELETE, a["uid"], a["token"])
	print("borrar partida de prueba -> HTTP ", r[0])
	await _delete_account(a["token"])
	await _delete_account(b["token"])
	print("cuentas de prueba borradas")
	quit()
