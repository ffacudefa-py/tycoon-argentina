class_name HardMode
extends RefCounted
## "Modo bien argentino" (opcional, se elige al empezar la cuenta).
##
## Desde la 15.0 no tiene funciones propias: todo existe en los dos modos y
## este modo sólo lo hace MÁS DIFÍCIL (a cambio de +income_bonus en ingresos):
##   - inflación: en el normal es suave (precios suben la mitad que los costos) y arranca
##     después del tutorial; acá es reforzada desde el principio y los precios
##     quedan atrás de los costos
##   - juicios laborales: con sueldos atrasados más de lawsuit_after segundos,
##     un empleado te hace juicio, cobra la indemnización y se va (en el normal
##     hay más margen y la indemnización es menor: cfg.normal)
##   - robos más seguidos y más grandes, y minijuegos más difíciles (Security)
## Los juicios sólo pasan con la app abierta (nada de sorpresas offline).
## Estado en m.hard (se guarda con la partida). Balance en progression.json →
## hard_mode.


static func cfg(m: GameModel) -> Dictionary:
	return m.data.balance.get("hard_mode", {})


static func on(m: GameModel) -> bool:
	return bool(m.hard.get("enabled", false))


static func default_state() -> Dictionary:
	return {"enabled": false, "chosen": false, "protected": {}, "debt_time": 0.0, "lawsuit_cd": 0.0, "theft_in": -1.0, "warned": false,
		"pending_theft": {}, "pending_bribe": {}, "fine_until": 0.0, "bribe_day": -1, "bribe_count": 0}


## Se elige una sola vez por cuenta (el prestigio la conserva).
static func choose(m: GameModel, enabled: bool) -> void:
	m.hard["chosen"] = true
	m.hard["enabled"] = enabled
	m.hard["theft_in"] = -1.0       # Security elige el próximo robo según el modo
	m.invalidate()
	if enabled:
		m.add_milestone("Elegiste el modo bien argentino: +%d %% de ingresos, con inflación, juicios y robos más duros." % int(round(income_bonus(m) * 100)))
	m.profile_changed.emit()


## Reglas de juicios del modo actual (las del normal pisan a las de este modo).
static func lawsuit_cfg(m: GameModel) -> Dictionary:
	var c: Dictionary = cfg(m).duplicate()
	if not on(m):
		c.merge(cfg(m).get("normal", {}), true)
	return c


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


# -------------------------------------------------------------------- ciclo

static func advance(m: GameModel, dt: float, offline: bool) -> void:
	if offline:
		return
	_advance_lawsuits(m, dt)


## Segundos que faltan para el próximo juicio laboral (-1 si no hay riesgo:
## sin deuda de sueldos o sin empleados). Lo muestra la barra superior.
static func lawsuit_eta(m: GameModel) -> float:
	if m.salary_debt <= 0 or m.employees.is_empty():
		return -1.0
	var left := float(lawsuit_cfg(m).get("lawsuit_after", 120)) - float(m.hard.get("debt_time", 0.0))
	return maxf(0.0, maxf(left, float(m.hard.get("lawsuit_cd", 0.0))))


static func _advance_lawsuits(m: GameModel, dt: float) -> void:
	var c := lawsuit_cfg(m)
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
		if eid == "" or EmployeeSystem.salary_of(m, m.employees[k]) > EmployeeSystem.salary_of(m, m.employees[eid]):
			eid = k
	var e: Dictionary = m.employees[eid]
	var c := lawsuit_cfg(m)
	var cost := Economy.to_int_ceil(EmployeeSystem.salary_of(m, e) * float(c.get("lawsuit_salary_seconds", 900)))
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
