class_name Security
extends RefCounted
## 11.2: robos, coima de seguridad y multa, en el modo normal y en el bien
## argentino (este último roba más seguido y se lleva más).
##
## Robo: cada theft_interval segundos (sólo con la app abierta) una banda
## intenta robar un negocio con mercadería. Si la provincia tiene la seguridad
## arreglada, no pasa nada. Si no, queda un robo PENDIENTE que la interfaz
## juega como minijuego (TheftGame) y se resuelve con resolve_theft(recuperado):
## se pierde fracción × (1 - recuperado) del stock. Sin interfaz (pruebas,
## servidor) se resuelve al instante sin recuperar nada.
##
## Coima: start_bribe cobra la coima y gasta una de las bribe_daily del día;
## la interfaz juega el minijuego de documentos (BribeGame) y llama a
## resolve_bribe(éxito). Éxito: seguridad por bribe_minutes en la provincia.
## Fracaso: multa, los ingresos bajan fine_income por fine_minutes. Una coima
## que quedó a medias (se cerró la app) cuenta como fracaso.
##
## Estado en m.hard (se guarda con la partida). Balance en
## progression.json → balance.security.

## La interfaz lo pone en true: los robos esperan a jugarse como minijuego.
static var ui_attached := false
## Azar propio: no consume m.rng (eventos, rivales y candidatos siguen igual).
static var rng := RandomNumberGenerator.new()
## La interfaz lo pone en true mientras hay un minijuego en pantalla: una coima
## que se está jugando no se da por abandonada aunque el teléfono se suspenda.
static var minigame_active := false


static func cfg(m: GameModel) -> Dictionary:
	return m.data.balance.get("security", {})


static func _mode_cfg(m: GameModel, key: String, fallback: Array) -> Array:
	var k := key + ("_hard" if HardMode.on(m) else "_normal")
	return cfg(m).get(k, fallback)


# ------------------------------------------------------------------ seguridad

static func protected_left(m: GameModel, zid: String) -> float:
	return maxf(0.0, float(m.hard.get("protected", {}).get(zid, 0.0)) - m.now())


static func bribe_cost(m: GameModel) -> int:
	var c := cfg(m)
	return maxi(int(c.get("bribe_min", 200)), Economy.to_int_ceil(m.income_per_sec() * float(c.get("bribe_income_seconds", 120))))


static func bribe_daily(m: GameModel) -> int:
	return int(cfg(m).get("bribe_daily", 5))


## Coimas que quedan hoy (se reinicia a la medianoche local).
static func bribes_left_today(m: GameModel) -> int:
	if int(m.hard.get("bribe_day", -1)) != ProgressionSystem.day_index(m):
		return bribe_daily(m)
	return maxi(0, bribe_daily(m) - int(m.hard.get("bribe_count", 0)))


static func can_bribe(m: GameModel, zid: String) -> Dictionary:
	if not m.zones.has(zid):
		return GameModel.fail("No tenés negocios en esa provincia.")
	if not pending_bribe(m).is_empty():
		return GameModel.fail("Ya estás arreglando con la policía.")
	if bribes_left_today(m) <= 0:
		return GameModel.fail("La comisaría no atiende más por hoy: volvé mañana.")
	if m.economy.money < bribe_cost(m):
		return GameModel.fail("No te alcanza (%s)." % Fmt.cost(bribe_cost(m)))
	return GameModel.ok()


## Cobra la coima y gasta un intento del día. La interfaz juega el minijuego.
static func start_bribe(m: GameModel, zid: String) -> Dictionary:
	var chk := can_bribe(m, zid)
	if not chk["ok"]:
		return chk
	var cost := bribe_cost(m)
	if not m.economy.spend(cost, "coimas"):
		return GameModel.fail("No te alcanza (%s)." % Fmt.cost(cost))
	var today := ProgressionSystem.day_index(m)
	if int(m.hard.get("bribe_day", -1)) != today:
		m.hard["bribe_day"] = today
		m.hard["bribe_count"] = 0
	m.hard["bribe_count"] = int(m.hard.get("bribe_count", 0)) + 1
	m.hard["pending_bribe"] = {"zone": zid, "at": m.now()}
	m._count("bribes", 1)
	return GameModel.ok()


static func pending_bribe(m: GameModel) -> Dictionary:
	return m.hard.get("pending_bribe", {})


static func resolve_bribe(m: GameModel, success: bool) -> void:
	var p := pending_bribe(m)
	if p.is_empty():
		return
	m.hard["pending_bribe"] = {}
	var zid: String = str(p.get("zone", ""))
	var zname: String = m.data.zone_by_id[zid]["name"] if m.data.zone_by_id.has(zid) else zid
	if success:
		var until := maxf(m.now(), float(m.hard["protected"].get(zid, 0.0))) + float(cfg(m).get("bribe_minutes", 30)) * 60.0
		m.hard["protected"][zid] = until
		m._count("bribes_ok", 1)
		m.notify.emit("Arreglaste con la comisaría de %s: nadie te toca el depósito por %s." % [zname, Fmt.duration(until - m.now())], "good")
	else:
		fine(m)
		m.notify.emit("La policía de %s te labró una multa: tus ingresos bajan %d %% por %s." % [zname, int(round(fine_income(m) * 100)), Fmt.duration(fine_left(m))], "bad")
	m.invalidate()
	m.world_changed.emit()


# ---------------------------------------------------------------------- multa

static func fine_income(m: GameModel) -> float:
	return float(cfg(m).get("fine_income", 0.2))


static func fine(m: GameModel) -> void:
	m.hard["fine_until"] = m.now() + float(cfg(m).get("fine_minutes", 5)) * 60.0
	m._count("fines", 1)
	m.invalidate()


static func fine_left(m: GameModel) -> float:
	return maxf(0.0, float(m.hard.get("fine_until", 0.0)) - m.now())


## Multiplicador de ingresos (1 - fine_income mientras dura la multa).
static func income_mult(m: GameModel) -> float:
	return 1.0 - fine_income(m) if fine_left(m) > 0.0 else 1.0


# ---------------------------------------------------------------------- robos

static func _next_theft(m: GameModel) -> float:
	var r := _mode_cfg(m, "theft_interval", [480, 900])
	return rng.randf_range(float(r[0]), float(r[1]))


static func pending_theft(m: GameModel) -> Dictionary:
	return m.hard.get("pending_theft", {})


static func advance(m: GameModel, dt: float, offline: bool) -> void:
	if offline:
		return
	if float(m.hard.get("fine_until", 0.0)) > 0.0 and fine_left(m) <= 0.0:
		m.hard["fine_until"] = 0.0
		m.invalidate()        # terminó la multa: recalcular ingresos
	# Una coima a medias de una sesión anterior (se cerró la app) es una multa.
	var pb := pending_bribe(m)
	if not pb.is_empty() and not minigame_active and m.now() - float(pb.get("at", 0.0)) > float(cfg(m).get("bribe_abandon_seconds", 120)):
		resolve_bribe(m, false)
	if not pending_theft(m).is_empty():
		return                # el reloj del próximo robo espera al minijuego
	if float(m.hard.get("theft_in", -1.0)) < 0.0:
		m.hard["theft_in"] = _next_theft(m)
	m.hard["theft_in"] = float(m.hard["theft_in"]) - dt
	if float(m.hard["theft_in"]) > 0.0:
		return
	m.hard["theft_in"] = _next_theft(m)
	var targets := []
	for id in m.owned_ids():
		if m.has_stock(id):
			targets.append(id)
	if targets.is_empty():
		return
	start_theft(m, targets[rng.randi() % targets.size()])


## Una banda intenta robar en bid. Devuelve ok si quedó un robo pendiente.
static func start_theft(m: GameModel, bid: String) -> Dictionary:
	var zid: String = m.biz[bid]["zone"]
	var name: String = m.data.business_by_id[bid]["name"]
	if protected_left(m, zid) > 0.0:
		m._count("thefts_blocked", 1)
		m.notify.emit("Quisieron robar en %s, pero la seguridad estaba arreglada. 😎" % name, "good")
		return GameModel.fail("protegido")
	var r := _mode_cfg(m, "theft_fraction", [0.15, 0.3])
	m.hard["pending_theft"] = {"business": bid, "fraction": rng.randf_range(float(r[0]), float(r[1])),
		"seed": rng.randi(), "difficulty": difficulty(m), "at": m.now()}
	m.celebrate.emit("theft_alarm", {"business": bid})
	if not ui_attached:
		resolve_theft(m, 0.0)
	return GameModel.ok()


## Descarta pendientes rotos de una partida guardada (negocio o zona
## desconocidos): si no, la interfaz no podría abrirlos ni resolverlos.
static func sanitize(m: GameModel) -> void:
	var p_theft: Dictionary = m.hard.get("pending_theft", {})
	if not p_theft.is_empty():
		var bid = p_theft.get("business")
		if not (bid is String and m.biz.has(bid) and m.biz[bid]["owned"]):
			m.hard["pending_theft"] = {}
	var p_bribe: Dictionary = m.hard.get("pending_bribe", {})
	if not p_bribe.is_empty():
		var zid = p_bribe.get("zone")
		if not (zid is String and m.zones.has(zid)):
			m.hard["pending_bribe"] = {}


## Dificultad del asalto (0..1): crece con las provincias conquistadas.
static func difficulty(m: GameModel) -> float:
	var hard_extra := 0.15 if HardMode.on(m) else 0.0
	return clampf(0.1 + 0.035 * ConquestSystem.conquered_count(m) + hard_extra, 0.0, 1.0)


## Resuelve el robo pendiente: recovered = parte recuperada (0..1).
## perfect = se frenó a toda la banda sin perder nada (da un cofre).
static func resolve_theft(m: GameModel, recovered: float, perfect := false) -> Dictionary:
	var p := pending_theft(m)
	if p.is_empty():
		return GameModel.fail("No hay robo.")
	m.hard["pending_theft"] = {}
	var bid: String = str(p.get("business", ""))
	if not m.biz.has(bid):
		return GameModel.fail("Negocio desconocido.")
	var name: String = m.data.business_by_id[bid]["name"]
	recovered = clampf(recovered, 0.0, 1.0)
	var frac := float(p["fraction"]) * (1.0 - recovered)
	var lost := 0.0
	for pid in m.biz[bid]["stock"]:
		var q := float(m.biz[bid]["stock"][pid])
		var take := floorf(q * frac)
		m.biz[bid]["stock"][pid] = q - take
		lost += take
	if recovered >= 0.999:
		m._count("thefts_defended", 1)
		m.notify.emit("¡Frenaste el asalto en %s! No se llevaron nada." % name, "good")
		if perfect:
			Engagement.grant_chest(m, "Premio por defender %s sin perder nada." % name)
	else:
		m._count("thefts", 1)
		m.notify.emit("Robo en %s: recuperaste el %d %% y se llevaron %s unidades. Pagá la seguridad para que no vuelva a pasar." % [name, int(round(recovered * 100)), Fmt.num(lost)], "bad")
	m.celebrate.emit("theft", {"business": bid, "recovered": recovered})
	m.business_changed.emit(bid)
	return GameModel.ok()
