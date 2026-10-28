class_name CloudSync
extends RefCounted
## Decisiones del guardado en la nube, sin red (se prueban en tests/cloud).
##
## Cada cuenta tiene un documento saves/<uid> en Firestore con el mismo sobre
## que el guardado local (formato, versión, checksum y payload) más un
## resumen legible para comparar partidas sin descargarlas enteras.

## Una partida "recién empezada" se reemplaza sin preguntar por la de la nube.
const FRESH_EARNED := 500


## Resumen de una partida para comparar y mostrar.
static func summary_of(m: GameModel, saved_at: float) -> Dictionary:
	return {
		"saved_at": saved_at,
		"stage": m.stage,
		"lifetime": m.economy.lifetime_earned,
		"money": m.economy.money,
		"company": str(m.profile["company"]),
		"prestige": int(m.prestige.get("count", 0)),
		"play_time": float(m.stats.get("play_time", 0.0)),
	}


static func is_fresh(s: Dictionary) -> bool:
	return int(s.get("lifetime", 0)) < FRESH_EARNED and int(s.get("prestige", 0)) == 0


## Qué hacer al conectarse:
##   "upload"   la nube no tiene partida, o no cambió desde la última vez que
##              este teléfono sincronizó (lo de acá es la continuación)
##   "download" la partida de este teléfono recién empieza
##   "ask"      las dos tienen progreso distinto: elige el jugador
static func decide(local: Dictionary, cloud: Dictionary, last_synced_saved_at: float) -> String:
	if cloud.is_empty():
		return "upload"
	if last_synced_saved_at > 0.0 and absf(float(cloud["saved_at"]) - last_synced_saved_at) < 1.0:
		return "upload"
	if is_fresh(local):
		return "download"
	return "ask"


## Qué hacer con la partida del teléfono al entrar con la cuenta `uid`, si la
## última cuenta que la usó fue `owner` ("" = nunca hubo sesión):
##   "same"    es la misma cuenta
##   "adopt"   se jugó como invitado: la partida pasa a ser de esta cuenta
##   "switch"  es de otra cuenta: se aparta y se usa la de esta cuenta
static func account_action(owner: String, uid: String) -> String:
	if owner == uid:
		return "same"
	return "adopt" if owner == "" else "switch"


## Copia local apartada de la partida de cada cuenta (al cambiar de cuenta).
static func stash_path(uid: String) -> String:
	return "user://accounts/%s.json" % uid.validate_filename()


## El servidor rechazó la escritura porque la partida de la nube cambió desde
## la última vez que la vimos (otro teléfono subió la suya).
static func is_stale_write(code: int, resp: Dictionary) -> bool:
	var st := ""
	if resp.get("error") is Dictionary:
		st = str(resp["error"].get("status", ""))
	return code in [400, 404, 409] and st in ["FAILED_PRECONDITION", "ALREADY_EXISTS", "NOT_FOUND"]


## Subida condicionada (documents:commit): sólo si la nube sigue como la vimos
## (updateTime de Firestore) o, si no había partida, que siga sin haberla.
## La condición va en el cuerpo: como parámetro de la URL el emulador la ignora.
static func commit_body(project: String, uid: String, fields: Dictionary, update_time: String) -> Dictionary:
	var cond := {"exists": false} if update_time == "" else {"updateTime": update_time}
	return {"writes": [{
		"update": {"name": "projects/%s/databases/(default)/documents/saves/%s" % [project, uid], "fields": fields["fields"]},
		"currentDocument": cond,
	}]}


## updateTime de la escritura confirmada (respuesta de documents:commit).
static func committed_time(resp: Dictionary) -> String:
	var wr = resp.get("writeResults")
	if wr is Array and not wr.is_empty() and wr[0] is Dictionary:
		return str(wr[0].get("updateTime", ""))
	return ""


# ------------------------------------------------------------ Firestore

## Raíz de documentos de Firestore, o del emulador local si está definida
## TYCOON_EMULATOR (sólo tools/dev/social_check.gd).
static func docs_root(project: String) -> String:
	var host := OS.get_environment("TYCOON_EMULATOR")
	var base := ("http://%s:8080/v1" % host) if host != "" else "https://firestore.googleapis.com/v1"
	return "%s/projects/%s/databases/(default)/documents" % [base, project]

# Los campos van tipados ({"stringValue": ...}); los enteros grandes como
# texto (Firestore los recibe así en JSON).

static func to_fields(doc_text: String, s: Dictionary, app_version: String) -> Dictionary:
	return {"fields": {
		"save": {"stringValue": doc_text},
		"saved_at": {"doubleValue": float(s["saved_at"])},
		"stage": {"integerValue": str(s["stage"])},
		"lifetime": {"integerValue": str(s["lifetime"])},
		"money": {"integerValue": str(s["money"])},
		"company": {"stringValue": str(s["company"])},
		"prestige": {"integerValue": str(s["prestige"])},
		"play_time": {"doubleValue": float(s["play_time"])},
		"app_version": {"stringValue": app_version},
	}}


## Resumen a partir de un documento de Firestore ({} si no hay partida).
static func summary_from_doc(doc: Dictionary) -> Dictionary:
	var f: Dictionary = doc.get("fields", {})
	if not f.has("save"):
		return {}
	return {
		"saved_at": _num(f.get("saved_at")),
		"stage": int(_num(f.get("stage"))),
		"lifetime": int(_num(f.get("lifetime"))),
		"money": int(_num(f.get("money"))),
		"company": str(f.get("company", {}).get("stringValue", "")),
		"prestige": int(_num(f.get("prestige"))),
		"play_time": _num(f.get("play_time")),
	}


static func save_text(doc: Dictionary) -> String:
	return str(doc.get("fields", {}).get("save", {}).get("stringValue", ""))


static func _num(v: Variant) -> float:
	if not v is Dictionary:
		return 0.0
	for k in ["doubleValue", "integerValue"]:
		if v.has(k):
			return float(v[k])
	return 0.0
