class_name FriendLogic
extends RefCounted
## Amigos: reglas y formato de Firestore, sin red (se prueban en tests/social).
##
## Documentos (reglas en firestore.rules, detalle en docs/AMIGOS.md):
##   players/<uid>                 perfil público: empresa, avatar, etapa, ganado
##                                 y, si la compartió, la miniatura de la foto
##   codes/<CÓDIGO>                {uid}: para encontrar a alguien por su código
##   players/<uid>/requests/<de>   solicitudes recibidas
##   players/<uid>/friends/<uid2>  lista de amigos (se escribe de los dos lados)
##   players/<uid>/gifts/<de>      regalos recibidos sin abrir (uno por amigo)
##   players/<uid>/blocked/<uid2>  (15.2) a quién bloqueó: no le puede mandar nada
##   reports/<auto>                (15.2) denuncias; sólo las lee el equipo (consola)

## 15.2: solicitudes de amistad por día y por cuenta (firestore.rules: limits/{uid}, mismo número).
const REQUESTS_PER_DAY := 20


## Día UTC (el mismo que usan las reglas: request.time / 86400000).
static func utc_day(unix: float) -> int:
	return floori(unix / 86400.0)


## Contador después de mandar una solicitud ({day, count} de limits/<uid>).
static func next_limit(current: Dictionary, now: float) -> Dictionary:
	var day := utc_day(now)
	var count := int(current.get("count", 0)) + 1 if int(current.get("day", -1)) == day else 1
	return {"day": day, "count": count}


## Motivos de denuncia (firestore.rules acepta sólo estos).
const REPORT_REASONS := {"nombre": "Nombre ofensivo", "foto": "Foto inapropiada", "acoso": "Spam o acoso", "otro": "Otro motivo"}

## Sin letras ni números que se confundan (O/0, I/1, L).
const CODE_CHARS := "ABCDEFGHJKMNPQRSTUVWXYZ23456789"
const CODE_LEN := 6


static func cfg(m: GameModel) -> Dictionary:
	return m.data.friends_cfg


static func make_code(rng: RandomNumberGenerator) -> String:
	var s := ""
	for i in CODE_LEN:
		s += CODE_CHARS[rng.randi() % CODE_CHARS.length()]
	return s


## "abc-12 3" -> "ABC123". Devuelve "" si no puede ser un código.
static func normalize_code(text: String) -> String:
	var s := ""
	for ch in text.to_upper():
		if ch == " " or ch == "-":
			continue
		if not CODE_CHARS.contains(ch):
			return ""
		s += ch
	return s if s.length() == CODE_LEN else ""


# ------------------------------------------------------------ regalos

## Estado diario de regalos abiertos (se guarda en la partida: m.social).
static func gifts_left_today(m: GameModel) -> int:
	_roll_day(m)
	return maxi(0, int(cfg(m)["gifts_per_day"]) - int(m.social["gifts_claimed"]))


## Abre un regalo recibido: da el premio si queda cupo hoy.
static func claim_gift(m: GameModel, from_name: String) -> Dictionary:
	if gifts_left_today(m) <= 0:
		return GameModel.fail("Ya abriste %d regalos hoy. Mañana podés abrir más." % int(cfg(m)["gifts_per_day"]))
	var reward: Dictionary = cfg(m)["gift_reward"]
	var desc := ProgressionSystem.describe(m, reward)
	m.social["gifts_claimed"] = int(m.social["gifts_claimed"]) + 1
	ProgressionSystem.grant(m, reward, "amigos")
	m._count("gifts_claimed", 1)
	m.celebrate.emit("claim", {"id": "gift"})
	return GameModel.ok("%s te convidó un mate: %s." % [from_name, desc])


static func _roll_day(m: GameModel) -> void:
	var today := ProgressionSystem.day_index(m)
	if int(m.social.get("day", -1)) != today:
		m.social["day"] = today
		m.social["gifts_claimed"] = 0


# ------------------------------------------------------------ ranking

## Amigos + uno mismo, de más a menos ganado en la historia.
static func ranking(me: Dictionary, friends: Array) -> Array:
	var all := friends.duplicate()
	all.append(me)
	all.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		if int(a["lifetime"]) != int(b["lifetime"]):
			return int(a["lifetime"]) > int(b["lifetime"])
		return str(a["uid"]) < str(b["uid"]))
	return all


# ------------------------------------------------------------ Firestore

static func profile_of(m: GameModel, uid: String, code: String) -> Dictionary:
	return {
		"uid": uid,
		"company": str(m.profile["company"]),
		"avatar": str(m.profile["avatar"]),
		"stage": m.stage,
		"lifetime": m.economy.lifetime_earned,
		"prestige": int(m.prestige.get("count", 0)),
		"code": code,
		"photo": "",
		"badges": Badges.shown(m),
	}


## (15.2) Nombre que se muestra si la administración sacó el nombre de empresa
## por una denuncia. Tiene que coincidir con firestore.rules (modName).
const MOD_NAME := "Empresa moderada"


## Documento moderation/{uid} -> {photo_off, name_off, banned}.
static func moderation_from_doc(doc: Dictionary) -> Dictionary:
	var f: Dictionary = doc.get("fields", {})
	var out := {}
	for k in ["photo_off", "name_off", "banned"]:
		var v = f.get(k)
		out[k] = v is Dictionary and v.get("booleanValue", false) == true
	return out


static func moderation_note(mod: Dictionary) -> String:
	if mod.get("banned", false):
		return "Por denuncias de otros jugadores, tu cuenta ya no puede usar Amigos. Si creés que es un error, escribinos al contacto de la política de privacidad."
	var parts: Array = []
	if mod.get("name_off", false):
		parts.append("tu nombre de empresa se muestra como \"%s\"" % MOD_NAME)
	if mod.get("photo_off", false):
		parts.append("tu foto ya no se muestra")
	if parts.is_empty():
		return ""
	return "Por una denuncia, %s a tus amigos." % " y ".join(parts)


## Hasta cuánto texto (base64) puede ocupar la miniatura de la foto (reglas: 24000).
const PHOTO_MAX := 20000


static func profile_fields(p: Dictionary, now: float) -> Dictionary:
	var out := {"fields": {
		"company": {"stringValue": str(p["company"]).left(40)},
		"avatar": {"stringValue": str(p["avatar"])},
		"stage": {"integerValue": str(p["stage"])},
		"lifetime": {"integerValue": str(p["lifetime"])},
		"prestige": {"integerValue": str(p["prestige"])},
		"code": {"stringValue": str(p["code"])},
		"updated": {"doubleValue": now},
	}}
	var photo := str(p.get("photo", ""))
	if photo != "" and photo.length() <= PHOTO_MAX:
		out["fields"]["photo"] = {"stringValue": photo}
	# 15.2: insignias que muestra (ids cortos, hasta Badges.MAX_SHOWN).
	var badges: Array = p.get("badges", [])
	if not badges.is_empty():
		var vals: Array = []
		for id in badges.slice(0, Badges.MAX_SHOWN):
			vals.append({"stringValue": str(id)})
		out["fields"]["badges"] = {"arrayValue": {"values": vals}}
	return out


## Perfil a partir de un documento players/<uid> ({} si no tiene datos).
static func profile_from_doc(doc: Dictionary) -> Dictionary:
	var f: Dictionary = doc.get("fields", {}) if doc.get("fields") is Dictionary else {}
	if not f.has("company"):
		return {}
	return {
		"uid": doc_id(doc),
		"company": text(f, "company"),
		"avatar": text(f, "avatar"),
		"stage": integer(f, "stage"),
		"lifetime": integer(f, "lifetime"),
		"prestige": integer(f, "prestige"),
		"code": text(f, "code"),
		"updated": num(f, "updated"),
		"photo": text(f, "photo"),
		"badges": strings(f, "badges"),
	}


static func report_fields(reporter: String, target: String, reason: String, company: String, now: float) -> Dictionary:
	return {"fields": {
		"reporter": {"stringValue": reporter},
		"target": {"stringValue": target},
		"reason": {"stringValue": reason if REPORT_REASONS.has(reason) else "otro"},
		"company": {"stringValue": company.left(40)},
		"at": {"doubleValue": now},
	}}


static func block_fields(company: String, now: float) -> Dictionary:
	return {"fields": {"company": {"stringValue": company.left(40)}, "at": {"doubleValue": now}}}


static func request_fields(from_uid: String, p: Dictionary, now: float) -> Dictionary:
	return {"fields": {
		"from": {"stringValue": from_uid},
		"company": {"stringValue": str(p["company"]).left(40)},
		"avatar": {"stringValue": str(p["avatar"])},
		"at": {"doubleValue": now},
	}}


static func gift_fields(from_uid: String, company: String, day: int, now: float) -> Dictionary:
	return {"fields": {
		"from": {"stringValue": from_uid},
		"company": {"stringValue": company.left(40)},
		"day": {"integerValue": str(day)},
		"at": {"doubleValue": now},
	}}


## Último tramo del nombre del documento (".../friends/<uid>" -> uid).
static func doc_id(doc: Dictionary) -> String:
	return str(doc.get("name", "")).get_file()


## Lista de textos (arrayValue) -> Array de String.
static func strings(f: Dictionary, key: String) -> Array:
	var v = f.get(key)
	var out: Array = []
	if v is Dictionary and v.get("arrayValue") is Dictionary:
		for item in v["arrayValue"].get("values", []):
			if item is Dictionary and item.has("stringValue"):
				out.append(str(item["stringValue"]))
	return out


static func text(f: Dictionary, key: String) -> String:
	var v = f.get(key)
	return str(v.get("stringValue", "")) if v is Dictionary else ""


## Enteros grandes: Firestore los manda como texto; se leen sin pasar por float.
static func integer(f: Dictionary, key: String) -> int:
	var v = f.get(key)
	if v is Dictionary and v.has("integerValue"):
		return str(v["integerValue"]).to_int()
	return int(num(f, key))


static func num(f: Dictionary, key: String) -> float:
	var v = f.get(key)
	if not v is Dictionary:
		return 0.0
	if v.has("integerValue"):
		return float(str(v["integerValue"]).to_int())
	return float(v.get("doubleValue", 0.0))
