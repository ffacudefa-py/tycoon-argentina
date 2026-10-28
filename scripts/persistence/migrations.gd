class_name Migrations
extends RefCounted
## Migraciones del formato de guardado.
##
## Para cambiar el formato: subir CURRENT_VERSION y agregar una función
## _vN_to_vN1(payload) que transforme el diccionario. migrate() las aplica
## en cadena, así un guardado viejo siempre llega al formato actual.
## Los campos que falten después se completan con valores por defecto en
## GameModel.from_dict(), así que agregar campos nuevos no requiere migración.

const CURRENT_VERSION := 4


static func migrate(payload: Dictionary, from_version: int) -> Dictionary:
	var p := payload
	var v := from_version
	while v < CURRENT_VERSION:
		match v:
			1:
				p = _v1_to_v2(p)
			2:
				p = _v2_to_v3(p)
			3:
				p = _v3_to_v4(p)
			_:
				pass
		v += 1
	return p


## v1 -> v2 (0.5.0): perfil con foto y banner propios y registro de
## recompensas por anuncios. Las partidas viejas arrancan sin foto/banner
## y con el registro vacío.
static func _v1_to_v2(p: Dictionary) -> Dictionary:
	var prof: Dictionary = p.get("profile", {}) if p.get("profile") is Dictionary else {}
	prof["photo"] = bool(prof.get("photo", false))
	prof["banner"] = bool(prof.get("banner", false))
	p["profile"] = prof
	if not p.get("ads") is Dictionary:
		p["ads"] = {"granted": [], "day": -1, "today": 0, "cooldowns": {}}
	return p


## v2 -> v3 (0.7.0): las ganancias pasan a ser 80 % (balance.income_rate) y
## los sueldos acompañan. Los empleados y candidatos de partidas viejas
## cobraban el sueldo anterior: se ajusta igual que los nuevos.
const V3_SALARY_RATE := 0.8

static func _v2_to_v3(p: Dictionary) -> Dictionary:
	var emps = p.get("employees")
	if emps is Dictionary:
		for e in emps.values():
			if e is Dictionary and e.has("salary"):
				e["salary"] = snappedf(float(e["salary"]) * V3_SALARY_RATE, 0.01)
	var bdict = p.get("businesses")
	if bdict is Dictionary:
		for s in bdict.values():
			if s is Dictionary and s.get("candidates") is Array:
				for c in s["candidates"]:
					if c is Dictionary and c.has("salary"):
						c["salary"] = snappedf(float(c["salary"]) * V3_SALARY_RATE, 0.01)
	return p


## v3 -> v4 (10.0 "Sigma Deza"): el juego pasa a ser conquistar la Argentina
## con negocios provinciales nuevos. Las partidas viejas empiezan de cero sin
## premio (decisión de diseño); sólo se conserva lo que no es progreso:
## perfil (nombre, avatar, foto, banner), recompensa diaria, anuncios, amigos
## y la fecha de creación. GameModel.from_dict() lo detecta por fresh_start.
const V4_KEEP := ["profile", "daily_reward", "ads", "social", "time"]

static func _v3_to_v4(p: Dictionary) -> Dictionary:
	var out := {"fresh_start": true, "economy": {"money": "0"}, "businesses": {}}
	for k in V4_KEEP:
		if p.has(k):
			out[k] = p[k]
	if p.get("stats") is Dictionary and p["stats"].has("created"):
		out["stats"] = {"created": p["stats"]["created"]}
	if not out.get("profile") is Dictionary:
		out["profile"] = {}
	if not out.get("time") is Dictionary:
		out["time"] = {}
	return out
