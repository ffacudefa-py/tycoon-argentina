class_name PioneerRegistry
extends RefCounted
## 15.2: registro de pioneros (prueba cerrada) en Firestore: pioneers/<uid> =
## {email, company, first_day, last_day, days, version}. Lo escribe el AAB de la
## prueba cerrada (etiqueta "prueba_cerrada") cuando el jugador tiene cuenta
## verificada; la planilla web/pioneros-admin.html lo cruza con las
## inscripciones. Días = días UTC distintos en que abrió el juego (las reglas
## sólo dejan sumar uno por día real). Ver docs/PIONEROS.md.


static func active() -> bool:
	return OS.has_feature(Badges.CLOSED_TEST_FEATURE)


## Documento que hay que escribir hoy, o {} si no hace falta (ya contó hoy).
## current: el documento actual ({} si no existe).
static func next_doc(current: Dictionary, email: String, company: String, version: String, now: float) -> Dictionary:
	var today := FriendLogic.utc_day(now)
	if current.is_empty():
		return {"email": email, "company": company.left(40), "first_day": today, "last_day": today, "days": 1, "version": version.left(20)}
	if int(current["last_day"]) >= today and str(current.get("company", "")) == company.left(40) and str(current.get("version", "")) == version.left(20):
		return {}
	var out := current.duplicate()
	out["email"] = email
	out["company"] = company.left(40)
	out["version"] = version.left(20)
	if int(current["last_day"]) < today:
		out["last_day"] = today
		out["days"] = int(current["days"]) + 1
	return out


static func to_fields(d: Dictionary) -> Dictionary:
	return {"fields": {
		"email": {"stringValue": str(d["email"])},
		"company": {"stringValue": str(d["company"])},
		"first_day": {"integerValue": str(d["first_day"])},
		"last_day": {"integerValue": str(d["last_day"])},
		"days": {"integerValue": str(d["days"])},
		"version": {"stringValue": str(d["version"])},
	}}


static func from_fields(doc: Dictionary) -> Dictionary:
	var f: Dictionary = doc.get("fields", {}) if doc.get("fields") is Dictionary else {}
	if not f.has("first_day"):
		return {}
	return {"email": FriendLogic.text(f, "email"), "company": FriendLogic.text(f, "company"),
		"first_day": FriendLogic.integer(f, "first_day"), "last_day": FriendLogic.integer(f, "last_day"),
		"days": FriendLogic.integer(f, "days"), "version": FriendLogic.text(f, "version")}
