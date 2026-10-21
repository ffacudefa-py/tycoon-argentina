class_name Migrations
extends RefCounted
## Migraciones del formato de guardado.
##
## Para cambiar el formato: subir CURRENT_VERSION y agregar una función
## _vN_to_vN1(payload) que transforme el diccionario. migrate() las aplica
## en cadena, así un guardado viejo siempre llega al formato actual.
## Los campos que falten después se completan con valores por defecto en
## GameModel.from_dict(), así que agregar campos nuevos no requiere migración.

const CURRENT_VERSION := 1


static func migrate(payload: Dictionary, from_version: int) -> Dictionary:
	var p := payload
	var v := from_version
	while v < CURRENT_VERSION:
		match v:
			# 1: p = _v1_to_v2(p)   (ejemplo para la próxima versión)
			_:
				pass
		v += 1
	return p
