class_name Migrations
extends RefCounted
## Migraciones del formato de guardado.
##
## Para cambiar el formato: subir CURRENT_VERSION y agregar una función
## _vN_to_vN1(payload) que transforme el diccionario. migrate() las aplica
## en cadena, así un guardado viejo siempre llega al formato actual.
## Los campos que falten después se completan con valores por defecto en
## GameModel.from_dict(), así que agregar campos nuevos no requiere migración.

const CURRENT_VERSION := 2


static func migrate(payload: Dictionary, from_version: int) -> Dictionary:
	var p := payload
	var v := from_version
	while v < CURRENT_VERSION:
		match v:
			1:
				p = _v1_to_v2(p)
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
