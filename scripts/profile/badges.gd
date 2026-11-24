class_name Badges
extends RefCounted
## Insignias del perfil (15.2): las de los logros (data/missions.json) y las
## especiales, que no salen de jugar sino de haber estado en un momento.
##
## El jugador elige hasta MAX_SHOWN insignias para mostrar en su perfil; se ven
## en la cabecera del Perfil y, con cuenta, también sus amigos (campo "badges"
## de players/<uid>, ver FriendLogic y firestore.rules).
##
## Guardado (en la partida, m.profile):
##   badges        id especial -> unix time en que la ganó
##   shown_badges  [ids] en el orden en que se muestran

const MAX_SHOWN := 3

## Especiales: no se pueden conseguir jugando, así que sólo se listan si se tienen.
const SPECIAL := {
	"pionero": {
		"name": "Pionero",
		"description": "Probó Coronados de Gloria en la prueba cerrada, antes del lanzamiento. ¡Gracias por ayudarnos a construirlo!",
		"icon": "bandera",
	},
}

## Etiqueta de exportación del build de la prueba cerrada (tools/build_play.sh con PRUEBA_CERRADA=1).
const CLOSED_TEST_FEATURE := "prueba_cerrada"


static func is_special(id: String) -> bool:
	return SPECIAL.has(id)


## ¿Existe esta insignia? (logro o especial)
static func exists(m: GameModel, id: String) -> bool:
	return is_special(id) or m.data.achievement_by_id.has(id)


static func owns(m: GameModel, id: String) -> bool:
	if is_special(id):
		var d = m.profile.get("badges", {})
		return d is Dictionary and d.has(id)
	return m.achievements.has(id)


## Especiales que tiene el jugador, en el orden de SPECIAL.
static func special_owned(m: GameModel) -> Array:
	return SPECIAL.keys().filter(func(id: String) -> bool: return owns(m, id))


static func grant(m: GameModel, id: String) -> bool:
	if not is_special(id) or owns(m, id):
		return false
	var d = m.profile.get("badges", {})
	if not d is Dictionary:
		d = {}
	d[id] = m.now()
	m.profile["badges"] = d
	m.add_milestone("Ganaste la insignia %s" % SPECIAL[id]["name"])
	# Una especial se muestra sola si hay lugar: es la que más luce.
	var list := shown(m)
	if list.size() < MAX_SHOWN:
		list.push_front(id)
		m.profile["shown_badges"] = list
	m.notify.emit("¡Nueva insignia: %s! Se muestra en tu perfil." % SPECIAL[id]["name"], "reward")
	m.profile_changed.emit()
	return true


## En el build de la prueba cerrada, quien juega se lleva la insignia Pionero.
static func grant_closed_test(m: GameModel) -> void:
	if OS.has_feature(CLOSED_TEST_FEATURE):
		grant(m, "pionero")


## Las que se muestran, sin repetidas ni ajenas (una partida editada a mano no las cuela).
static func shown(m: GameModel) -> Array:
	var out: Array = []
	var raw = m.profile.get("shown_badges", [])
	for id in (raw if raw is Array else []):
		var s := str(id)
		if out.size() < MAX_SHOWN and not out.has(s) and owns(m, s):
			out.append(s)
	return out


static func is_shown(m: GameModel, id: String) -> bool:
	return shown(m).has(id)


## Mostrar / dejar de mostrar. Con el cupo lleno no se reemplaza nada: se avisa.
static func toggle_shown(m: GameModel, id: String) -> Dictionary:
	if not owns(m, id):
		return GameModel.fail("Todavía no tenés esa insignia.")
	var list := shown(m)
	if list.has(id):
		list.erase(id)
		m.profile["shown_badges"] = list
		m.profile_changed.emit()
		return GameModel.ok("Ya no se muestra en tu perfil.")
	if list.size() >= MAX_SHOWN:
		return GameModel.fail("Podés mostrar hasta %d insignias. Sacá una para poner esta." % MAX_SHOWN)
	list.append(id)
	m.profile["shown_badges"] = list
	m.profile_changed.emit()
	return GameModel.ok("¡Ahora se muestra en tu perfil!")


static func display_name(m: GameModel, id: String) -> String:
	if is_special(id):
		return SPECIAL[id]["name"]
	return str(m.data.achievement_by_id.get(id, {}).get("name", id))


## Ids de otro jugador (vienen de la red): sólo los que existen, sin repetir.
static func filter_known(m: GameModel, ids: Array) -> Array:
	var out: Array = []
	for id in ids:
		var s := str(id)
		if out.size() < MAX_SHOWN and not out.has(s) and exists(m, s):
			out.append(s)
	return out
