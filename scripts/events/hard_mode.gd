class_name HardMode
extends RefCounted
## "Modo bien argentino" (opcional, se elige al empezar la cuenta). Es la
## única forma de jugar con inflación: reemplaza al viejo ajuste de inflación ficticia.
##
## A cambio de +income_bonus en todos los ingresos:
##   - inflación reforzada siempre activa (remarcaciones más seguidas y grandes)
##   - juicios laborales: con sueldos atrasados más de lawsuit_after segundos,
##     un empleado te hace juicio, cobra la indemnización y se va
##   - robos: cada tanto roban parte de la mercadería de un negocio
##   - coima de seguridad: pagás por provincia y no te roban por un rato
## Juicios y robos sólo pasan con la app abierta (nada de sorpresas offline).
## Estado en m.hard (se guarda con la partida). Balance en progression.json →
## hard_mode.


static func cfg(m: GameModel) -> Dictionary:
	return m.data.balance.get("hard_mode", {})


static func on(m: GameModel) -> bool:
	return bool(m.hard.get("enabled", false))


static func default_state() -> Dictionary:
	return {"enabled": false, "chosen": false, "protected": {}, "debt_time": 0.0, "lawsuit_cd": 0.0, "theft_in": -1.0, "warned": false}


## Se elige una sola vez por cuenta (el prestigio la conserva).
static func choose(m: GameModel, enabled: bool) -> void:
	m.hard["chosen"] = true
	m.hard["enabled"] = enabled
	m.hard["theft_in"] = _next_theft(m)
	m.invalidate()
	if enabled:
		m.add_milestone("Elegiste el modo bien argentino: +%d %% de ingresos, con inflación, juicios y robos." % int(round(income_bonus(m) * 100)))
	m.profile_changed.emit()


static func income_bonus(m: GameModel) -> float:
	return float(cfg(m).get("income_bonus", 0.25))


static func income_mult(m: GameModel) -> float:
	return 1.0 + income_bonus(m) if on(m) else 1.0


## Configuración de inflación: la normal, pisada por la reforzada en este modo.
static func inflation_cfg(m: GameModel) -> Dictionary:
	var base: Dictionary = m.data.events_cfg["inflation"].duplicate()
	if on(m):
		base.merge(cfg(m).get("inflation", {}), true)
	return base


# ------------------------------------------------------------------ seguridad

static func bribe_cost(m: GameModel) -> int:
	var c := cfg(m)
	return maxi(int(c.get("bribe_min", 200)), Economy.to_int_ceil(m.income_per_sec() * float(c.get("bribe_income_seconds", 120))))


static func protected_left(m: GameModel, zid: String) -> float:
	return maxf(0.0, float(m.hard.get("protected", {}).get(zid, 0.0)) - m.now())


static func pay_bribe(m: GameModel, zid: String) -> Dictionary:
	if not on(m):
		return GameModel.fail("Sólo en el modo bien argentino.")
	if not m.zones.has(zid):
		return GameModel.fail("No tenés negocios en esa provincia.")
	var cost := bribe_cost(m)
	if not m.economy.spend(cost, "coimas"):
		return GameModel.fail("No te alcanza (%s)." % Fmt.cost(cost))
	var until := maxf(m.now(), float(m.hard["protected"].get(zid, 0.0))) + float(cfg(m).get("bribe_minutes", 30)) * 60.0
	m.hard["protected"][zid] = until
	m._count("bribes", 1)
	m.notify.emit("Arreglaste con la seguridad de %s: nadie te toca el depósito por %s." % [m.data.zone_by_id[zid]["name"], Fmt.duration(until - m.now())], "info")
	m.world_changed.emit()
	return GameModel.ok()


# -------------------------------------------------------------------- ciclo

static func advance(m: GameModel, dt: float, offline: bool) -> void:
	if not on(m) or offline:
		return
	_advance_lawsuits(m, dt)
	_advance_theft(m, dt)


static func _advance_lawsuits(m: GameModel, dt: float) -> void:
	var c := cfg(m)
	m.hard["lawsuit_cd"] = maxf(0.0, float(m.hard.get("lawsuit_cd", 0.0)) - dt)
	if m.salary_debt <= 0 or m.employees.is_empty():
		m.hard["debt_time"] = 0.0
		m.hard["warned"] = false
		return
	m.hard["debt_time"] = float(m.hard.get("debt_time", 0.0)) + dt
	var after := float(c.get("lawsuit_after", 120))
	if not m.hard.get("warned", false):
		m.hard["warned"] = true
		m.notify.emit("Ojo: si no pagás los sueldos en %s, alguien te va a hacer juicio." % Fmt.duration(after), "bad")
	if float(m.hard["debt_time"]) < after or float(m.hard["lawsuit_cd"]) > 0.0:
		return
	lawsuit(m)


## Un empleado (el de mayor sueldo) hace juicio: indemnización agravada que se
## cobra aunque no haya plata (queda como deuda) y el empleado se va.
static func lawsuit(m: GameModel) -> Dictionary:
	if m.employees.is_empty():
		return GameModel.fail("No hay empleados.")
	var eid := ""
	for k in m.employees:
		if eid == "" or float(m.employees[k]["salary"]) > float(m.employees[eid]["salary"]):
			eid = k
	var e: Dictionary = m.employees[eid]
	var c := cfg(m)
	var cost := Economy.to_int_ceil(float(e["salary"]) * float(c.get("lawsuit_salary_seconds", 900)))
	var paid := m.economy.spend_up_to(cost, "juicios")
	m.salary_debt += cost - paid
	m.employees.erase(eid)
	m.hard["lawsuit_cd"] = float(c.get("lawsuit_cooldown", 300))
	m.hard["debt_time"] = 0.0
	m._count("lawsuits", 1)
	m.invalidate()
	m.notify.emit("%s te hizo juicio laboral por sueldos impagos: pagás %s y se va de la empresa." % [e["name"], Fmt.cost(cost)], "bad")
	m.celebrate.emit("lawsuit", {"business": e["business"]})
	m.business_changed.emit(e["business"])
	return GameModel.ok()


static func _next_theft(m: GameModel) -> float:
	var r: Array = cfg(m).get("theft_interval", [240, 480])
	return m.rng.randf_range(float(r[0]), float(r[1]))


static func _advance_theft(m: GameModel, dt: float) -> void:
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
	theft(m, targets[m.rng.randi() % targets.size()])


## Roban entre theft_fraction[0] y [1] del stock del negocio, salvo que la
## provincia tenga la seguridad paga.
static func theft(m: GameModel, bid: String) -> Dictionary:
	var zid: String = m.biz[bid]["zone"]
	var name: String = m.data.business_by_id[bid]["name"]
	if protected_left(m, zid) > 0.0:
		m._count("thefts_blocked", 1)
		m.notify.emit("Quisieron robar en %s, pero la seguridad estaba arreglada. 😎" % name, "good")
		return GameModel.fail("protegido")
	var r: Array = cfg(m).get("theft_fraction", [0.2, 0.4])
	var frac := m.rng.randf_range(float(r[0]), float(r[1]))
	var stolen := 0.0
	for pid in m.biz[bid]["stock"]:
		var q := float(m.biz[bid]["stock"][pid])
		var take := floorf(q * frac)
		m.biz[bid]["stock"][pid] = q - take
		stolen += take
	m._count("thefts", 1)
	m.notify.emit("¡Robo en %s! Una banda se llevó el %d %% de la mercadería (%s unidades). Pagá la seguridad para que no vuelva a pasar." % [name, int(round(frac * 100)), Fmt.num(stolen)], "bad")
	m.celebrate.emit("theft", {"business": bid})
	m.business_changed.emit(bid)
	return GameModel.ok()
