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


# ------------------------------------------------------------ Firestore
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
