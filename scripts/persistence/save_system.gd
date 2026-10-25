class_name SaveSystem
extends RefCounted
## Guardado local confiable.
##
## Formato (JSON):
##   {"format": "tycoon_argentina_save", "version": N, "saved_at": unix,
##    "checksum": sha256(payload), "payload": "<JSON del estado>"}
## El payload va como texto para que el checksum sea exacto.
##
## Escritura atómica: se escribe <archivo>.tmp, se relee y verifica, el
## guardado anterior pasa a <archivo>.bak y recién ahí el .tmp ocupa su lugar.
## Si algo falla en el medio, al cargar se prueban en orden: principal, .tmp, .bak.
## Un archivo dañado se aparta como .corrupt-<fecha> (nunca se borra a ciegas)
## y el juego arranca igual con el último estado válido o con una partida nueva.

const FORMAT := "tycoon_argentina_save"
const DEFAULT_PATH := "user://tycoon_save.json"

var path: String
var last_error := ""
var last_load_source := ""   ## "main", "tmp", "bak", "new"


func _init(p_path := DEFAULT_PATH) -> void:
	path = p_path


## Documento de guardado (el mismo formato en el teléfono y en la nube).
## Devuelve {} si el estado no es válido (last_error dice por qué).
func make_doc(model: GameModel) -> Dictionary:
	var payload := model.to_dict()
	var problem := validate_payload(payload, model.data)
	if problem != "":
		last_error = "estado inválido, no se guarda: " + problem
		push_warning(last_error)
		return {}
	var payload_text := JSON.stringify(payload, "", true, true)
	return {
		"format": FORMAT,
		"version": Migrations.CURRENT_VERSION,
		"saved_at": model.now(),
		"checksum": payload_text.sha256_text(),
		"payload": payload_text,
	}


## Payload válido y migrado de un documento (texto JSON), o {} si está
## dañado, es de otra versión o no pasa los controles.
func payload_from_text(text: String, data: GameData) -> Dictionary:
	var doc := _check_doc(JSON.parse_string(text), "nube")
	if doc.is_empty():
		return {}
	var payload = JSON.parse_string(doc["payload"])
	if not payload is Dictionary:
		last_error = "nube: payload inválido"
		return {}
	payload = Migrations.migrate(payload, int(doc["version"]))
	var problem := validate_payload(payload, data)
	if problem != "":
		last_error = "nube: " + problem
		return {}
	return payload


## Serializa y guarda. Devuelve false (sin tocar el archivo bueno) si algo falla.
func save(model: GameModel) -> bool:
	var doc := make_doc(model)
	if doc.is_empty():
		return false
	var text := JSON.stringify(doc, "", false)
	var tmp := path + ".tmp"
	var f := FileAccess.open(tmp, FileAccess.WRITE)
	if f == null:
		last_error = "no se pudo escribir %s (%s)" % [tmp, error_string(FileAccess.get_open_error())]
		push_warning(last_error)
		return false
	f.store_string(text)
	f.flush()
	f.close()
	# Verificación: lo escrito se puede leer y el checksum coincide.
	if _read_doc(tmp).is_empty():
		last_error = "verificación del guardado falló"
		push_warning(last_error)
		return false
	var bak := path + ".bak"
	if FileAccess.file_exists(path):
		if FileAccess.file_exists(bak):
			DirAccess.remove_absolute(bak)
		DirAccess.rename_absolute(path, bak)
	var err := DirAccess.rename_absolute(tmp, path)
	if err != OK:
		last_error = "no se pudo reemplazar el guardado (%s)" % error_string(err)
		push_warning(last_error)
		return false
	last_error = ""
	return true


## Devuelve el payload válido más reciente (ya migrado) o {} si no hay ninguno.
func load_payload(data: GameData) -> Dictionary:
	for candidate in [[path, "main"], [path + ".tmp", "tmp"], [path + ".bak", "bak"]]:
		var p: String = candidate[0]
		if not FileAccess.file_exists(p):
			continue
		var doc := _read_doc(p)
		if doc.is_empty():
			_quarantine(p)
			continue
		var payload = JSON.parse_string(doc["payload"])
		if not payload is Dictionary:
			_quarantine(p)
			continue
		payload = Migrations.migrate(payload, int(doc["version"]))
		var problem := validate_payload(payload, data)
		if problem != "":
			last_error = "%s: %s" % [p, problem]
			_quarantine(p)
			continue
		last_load_source = candidate[1]
		return payload
	last_load_source = "new"
	return {}


func exists() -> bool:
	return FileAccess.file_exists(path) or FileAccess.file_exists(path + ".bak") or FileAccess.file_exists(path + ".tmp")


## Borra todo (sólo desde "Reiniciar partida" con confirmación).
func delete_all() -> void:
	for p in [path, path + ".tmp", path + ".bak"]:
		if FileAccess.file_exists(p):
			DirAccess.remove_absolute(p)


func _read_doc(p: String) -> Dictionary:
	var f := FileAccess.open(p, FileAccess.READ)
	if f == null:
		return {}
	var text := f.get_as_text()
	f.close()
	return _check_doc(JSON.parse_string(text), p)


## Controles del sobre: formato, versión soportada y checksum del payload.
func _check_doc(doc: Variant, p: String) -> Dictionary:
	if not doc is Dictionary:
		last_error = "%s: JSON inválido" % p
		return {}
	if doc.get("format", "") != FORMAT or not doc.get("payload") is String:
		last_error = "%s: formato desconocido" % p
		return {}
	var version := int(doc.get("version", 0))
	if version < 1 or version > Migrations.CURRENT_VERSION:
		last_error = "%s: versión %d no soportada" % [p, version]
		return {}
	if (doc["payload"] as String).sha256_text() != doc.get("checksum", ""):
		last_error = "%s: checksum incorrecto (archivo dañado)" % p
		return {}
	return doc


func _quarantine(p: String) -> void:
	var stamp := Time.get_datetime_string_from_system().replace(":", "-")
	var dest := "%s.corrupt-%s" % [path, stamp]
	DirAccess.rename_absolute(p, dest)
	push_warning("Guardado dañado apartado en %s (%s)" % [dest, last_error])


## Controles mínimos de coherencia. "" = válido.
static func validate_payload(payload: Dictionary, data: GameData) -> String:
	for key in ["economy", "businesses", "profile", "time"]:
		if not payload.get(key) is Dictionary:
			return "falta '%s'" % key
	var money := Economy.s2i(payload["economy"].get("money", -1))
	if money < 0:
		return "dinero inválido"
	var b: Dictionary = payload["businesses"]
	if not b.get("puesto") is Dictionary:
		return "falta el puesto inicial"
	for id in b:
		if not b[id] is Dictionary:
			return "negocio %s dañado" % id
		var lvl := int(b[id].get("level", 0))
		if lvl < 0 or (data.business_by_id.has(id) and lvl > int(data.business_by_id[id]["max_level"])):
			return "nivel inválido en %s" % id
	return ""
