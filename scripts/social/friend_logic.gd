class_name FriendLogic
extends RefCounted
## Amigos: reglas y formato de Firestore, sin red (se prueban en tests/social).
##
## Documentos (reglas en firestore.rules, detalle en docs/AMIGOS.md):
##   players/<uid>                 perfil público: empresa, avatar, etapa, ganado
##   codes/<CÓDIGO>                {uid}: para encontrar a alguien por su código
##   players/<uid>/requests/<de>   solicitudes recibidas
##   players/<uid>/friends/<uid2>  lista de amigos (se escribe de los dos lados)
##   players/<uid>/gifts/<de>      regalos recibidos sin abrir (uno por amigo)

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
	}


static func profile_fields(p: Dictionary, now: float) -> Dictionary:
	return {"fields": {
		"company": {"stringValue": str(p["company"]).left(40)},
		"avatar": {"stringValue": str(p["avatar"])},
		"stage": {"integerValue": str(p["stage"])},
		"lifetime": {"integerValue": str(p["lifetime"])},
		"prestige": {"integerValue": str(p["prestige"])},
		"code": {"stringValue": str(p["code"])},
		"updated": {"doubleValue": now},
	}}


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
	}


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
