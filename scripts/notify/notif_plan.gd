class_name NotifPlan
extends RefCounted
## Qué notificaciones locales agendar al salir del juego (sin red: se prueba en
## tests/notify). PushNotifications las manda al plugin de Android.
##
##   - Caja llena: cuando se llena el tope de ganancias sin conexión; o, si
##     antes se queda sin mercadería un negocio que vende solo pero no repone,
##     "te quedaste sin mercadería" a esa hora (ahí dejan de entrar ganancias).
##   - Eventos: hasta EVENTS_PER_DAY por día, en horario razonable. Cada una
##     lleva el evento que va a estar pasando: al volver, si no hay ninguno
##     activo, se dispara ese (así el aviso nunca miente).
## Las sociales (versión nueva, solicitudes de amistad) las chequea el plugin
## en segundo plano.

const ID_IDLE := 1
const ID_EVENTS := [2, 3]
const EVENTS_PER_DAY := 2
## Cuánto después de salir van los avisos de evento (segundos).
const EVENT_DELAYS := [3.0 * 3600.0, 9.0 * 3600.0]
## Horario permitido (hora local): ni de madrugada ni muy tarde.
const DAY_START := 10
const DAY_END := 21


## Día local (AAAA-MM-DD) de un instante unix.
static func day_key(unix: float, tz_minutes: int) -> String:
	var d := Time.get_datetime_dict_from_unix_time(int(unix) + tz_minutes * 60)
	return "%04d-%02d-%02d" % [d["year"], d["month"], d["day"]]


static func local_hour(unix: float, tz_minutes: int) -> float:
	var d := Time.get_datetime_dict_from_unix_time(int(unix) + tz_minutes * 60)
	return float(d["hour"]) + float(d["minute"]) / 60.0


## Corre un instante al horario permitido (si cae de noche, a las DAY_START + algo).
static func into_daytime(unix: float, tz_minutes: int) -> float:
	var h := local_hour(unix, tz_minutes)
	if h >= DAY_START and h < DAY_END:
		return unix
	var to_start := (DAY_START + 24.0 - h) if h >= DAY_END else (DAY_START - h)
	return unix + to_start * 3600.0 + 15.0 * 60.0


## state: {"delivered": {día: n}} (avisos de evento que ya salieron).
## Devuelve [{id, at, title, text, event?}] para agendar a partir de `now`.
static func plan(m: GameModel, now: float, tz_minutes: int, state: Dictionary, rng: RandomNumberGenerator) -> Array:
	var out := []
	var idle := idle_stop(m)
	if idle["seconds"] > 0.0:
		var name := str(idle.get("business", ""))
		if idle["reason"] == "stock":
			out.append({"id": ID_IDLE, "at": now + float(idle["seconds"]), "title": "Te quedaste sin mercadería",
				"text": "%s vendió todo y dejó de ganar. Entrá a reponer para que siga vendiendo." % name})
		else:
			out.append({"id": ID_IDLE, "at": now + float(idle["seconds"]), "title": "¡Caja llena!",
				"text": "Tus negocios ya juntaron todo lo que pueden ganar sin vos. Entrá a cobrar y que sigan vendiendo."})
	var delivered: Dictionary = state.get("delivered", {})
	var per_day := {}
	var pool := EventSystem.eligible(m)
	for i in EVENT_DELAYS.size():
		if pool.is_empty():
			break
		var at := into_daytime(now + float(EVENT_DELAYS[i]), tz_minutes)
		var day := day_key(at, tz_minutes)
		var used := int(delivered.get(day, 0)) + int(per_day.get(day, 0))
		if used >= EVENTS_PER_DAY:
			continue
		per_day[day] = int(per_day.get(day, 0)) + 1
		var e: Dictionary = pool[rng.randi() % pool.size()]
		out.append({"id": ID_EVENTS[i], "at": at, "event": e["id"],
			"title": "%s en tus negocios" % e["name"],
			"text": "%s Entrá a resolverlo antes de que termine." % str(e["description"])})
	return out


## Cuándo dejan de entrar ganancias sin conexión: {seconds, reason: "cap"|"stock",
## business}. seconds = 0 si no entra nada (ningún negocio vende solo).
static func idle_stop(m: GameModel) -> Dictionary:
	var cap := OfflineCalculator.cap_seconds(m)
	var any_full := false
	var first_out := INF
	var first_name := ""
	for id in m.owned_ids():
		var d := m.derive(id)
		if not d["auto_sell"] or not m.has_stock(id):
			continue
		if d["auto_restock"]:
			any_full = true
			continue
		# Sin repositor: cuánto dura el stock a este ritmo.
		var per_cycle := 0.0
		var units := 0.0
		for p in d["products"]:
			per_cycle += float(p["u"])
			units += float(m.biz[id]["stock"].get(p["id"], 0.0))
		if per_cycle <= 0.0:
			continue
		var secs := units / per_cycle * float(d["cycle"])
		if secs < first_out:
			first_out = secs
			first_name = str(m.data.business_by_id[id]["name"])
	if any_full or first_out >= cap:
		return {"seconds": cap if (any_full or first_out < INF) else 0.0, "reason": "cap"}
	if first_out < INF:
		return {"seconds": maxf(60.0, first_out), "reason": "stock", "business": first_name}
	return {"seconds": 0.0, "reason": "cap"}


## Al volver: los avisos de evento que ya salieron cuentan para su día; devuelve
## el evento que hay que disparar (el último que salió) o "".
static func on_return(now: float, tz_minutes: int, scheduled: Array, state: Dictionary) -> String:
	var delivered: Dictionary = state.get("delivered", {})
	var fire := ""
	var last := -1.0
	for n in scheduled:
		if not n.has("event") or float(n["at"]) > now:
			continue
		var day := day_key(float(n["at"]), tz_minutes)
		delivered[day] = int(delivered.get(day, 0)) + 1
		if float(n["at"]) > last:
			last = float(n["at"])
			fire = str(n["event"])
	# Sólo se guardan los últimos días.
	var keys := delivered.keys()
	keys.sort()
	while keys.size() > 7:
		delivered.erase(keys.pop_front())
	state["delivered"] = delivered
	return fire
