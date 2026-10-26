class_name EmployeeSystem
extends RefCounted
## Candidatos, contratación, despidos, sueldos y experiencia.
##
## Costos y sueldos escalan con la "escala" del negocio (su ganancia por
## segundo a nivel 10). El sueldo queda fijo al contratar: a medida que el
## negocio crece, el empleado se vuelve relativamente más barato.
## Si no alcanza para pagar sueldos, se acumula deuda (nunca saldo negativo)
## y todos trabajan "a reglamento" (50 %) hasta saldarla.


static func xp_level(m: GameModel, e: Dictionary) -> int:
	var levels: Array = m.data.employees_cfg["xp_levels"]
	var lvl := 1
	for i in levels.size():
		if float(e.get("xp", 0.0)) >= float(levels[i]):
			lvl = i + 1
	return lvl


static func available_roles(m: GameModel, bid: String) -> Array:
	var out := []
	var level := int(m.biz[bid]["level"])
	for r in m.data.roles:
		if level >= int(r["min_level"]) and m.stage >= int(r["min_stage"]):
			out.append(r["id"])
	return out


static func _make_candidate(m: GameModel, bid: String, role_id: String) -> Dictionary:
	var cfg: Dictionary = m.data.employees_cfg
	var role: Dictionary = m.data.role_by_id[role_id]
	var def: Dictionary = m.data.business_by_id[bid]
	var eff := snappedf(m.rng.randf_range(float(cfg["efficiency_min"]), float(cfg["efficiency_max"])), 0.01)
	var quality := (eff - float(cfg["efficiency_min"])) / (float(cfg["efficiency_max"]) - float(cfg["efficiency_min"]))
	var scale: float = def["scale"]
	var hire_discount := 1.0 - float(m.data.perk_by_id["reclutadora"]["effects"]["hire_cost"]) * m.perk_level("reclutadora")
	var first: Array = cfg["first_names"]
	var last: Array = cfg["last_names"]
	return {
		"name": "%s %s" % [first[m.rng.randi() % first.size()], last[m.rng.randi() % last.size()]],
		"role": role_id,
		"eff": eff,
		"hire": Economy.to_int_ceil(float(role["hire"]) * scale * (0.8 + 0.4 * quality) * maxf(0.3, hire_discount)),
		"salary": snappedf(float(role["salary"]) * scale * (0.85 + 0.3 * quality) * m.income_rate(), 0.01),
		"variant": m.rng.randi() % 8,
	}


## Arma la lista de candidatos priorizando lo que el negocio necesita:
## primero alguien que venda solo, después alguien que reponga.
static func generate_candidates(m: GameModel, bid: String) -> void:
	var s: Dictionary = m.biz[bid]
	var roles := available_roles(m, bid)
	var d := m.derive(bid)
	var wanted := []
	if not d["auto_sell"] and roles.has("vendedor"):
		wanted.append("vendedor")
	if not d["auto_restock"] and roles.has("repositor"):
		wanted.append("repositor")
	var count := int(m.data.employees_cfg["candidates_per_business"])
	while wanted.size() < count and not roles.is_empty():
		# Los roles más avanzados aparecen con más frecuencia cuanto más crece el negocio.
		var pick: String = roles[m.rng.randi() % roles.size()]
		if m.rng.randf() < 0.5:
			pick = roles[-1]
		wanted.append(pick)
	var list := []
	for r in wanted.slice(0, count):
		list.append(_make_candidate(m, bid, r))
	s["candidates"] = list
	s["cand_timer"] = float(m.data.employees_cfg["candidate_refresh_seconds"])


static func ensure_candidates(m: GameModel, bid: String) -> void:
	var s: Dictionary = m.biz[bid]
	if s["owned"] and (s["candidates"] as Array).is_empty():
		generate_candidates(m, bid)


static func reroll(m: GameModel, bid: String) -> Dictionary:
	var s: Dictionary = m.biz[bid]
	if float(s["reroll_cd"]) > 0.0:
		return GameModel.fail("Esperá %s para buscar otros candidatos." % Fmt.duration(s["reroll_cd"]))
	generate_candidates(m, bid)
	s["reroll_cd"] = float(m.data.employees_cfg["reroll_cooldown_seconds"])
	m.business_changed.emit(bid)
	return GameModel.ok()


static func hire(m: GameModel, bid: String, index: int) -> Dictionary:
	var s: Dictionary = m.biz[bid]
	if not s["owned"]:
		return GameModel.fail("No tenés este negocio.")
	var cands: Array = s["candidates"]
	if index < 0 or index >= cands.size():
		return GameModel.fail("Ese candidato ya no está disponible.")
	var d := m.derive(bid)
	if int(d["team_size"]) >= int(d["slots"]):
		return GameModel.fail("No hay puestos libres. Mejorá el negocio para sumar lugares.")
	var c: Dictionary = cands[index]
	if not m.economy.spend(int(c["hire"]), "contrataciones"):
		return GameModel.fail("No te alcanza para contratar.")
	var eid := "e%d" % m.next_employee_id
	m.next_employee_id += 1
	m.employees[eid] = {
		"id": eid, "name": c["name"], "role": c["role"], "eff": c["eff"],
		"salary": c["salary"], "business": bid, "xp": 0.0, "variant": c["variant"],
		"hired_at": m.now(),
	}
	cands.remove_at(index)
	cands.append(_make_candidate(m, bid, available_roles(m, bid)[m.rng.randi() % available_roles(m, bid).size()]))
	m._count("hires_total", 1)
	m.invalidate()
	var role_name: String = m.data.role_by_id[c["role"]]["name"]
	m.celebrate.emit("hire", {"business": bid, "employee": eid})
	m.notify.emit("%s se suma como %s." % [c["name"], role_name.to_lower()], "good")
	if m.counter("hires_total") == 1.0:
		m.add_milestone("Contrataste a tu primer empleado: %s." % c["name"])
	m.business_changed.emit(bid)
	return GameModel.ok()


static func severance(m: GameModel, eid: String) -> int:
	var e: Dictionary = m.employees[eid]
	return Economy.to_int_ceil(float(e["salary"]) * float(m.data.employees_cfg["fire_severance_seconds"]))


static func fire(m: GameModel, eid: String) -> Dictionary:
	if not m.employees.has(eid):
		return GameModel.fail("Ese empleado ya no trabaja con vos.")
	var e: Dictionary = m.employees[eid]
	var pay := severance(m, eid)
	if not m.economy.spend(pay, "indemnizaciones"):
		return GameModel.fail("No te alcanza para la indemnización (%s)." % Fmt.cost(pay))
	m.employees.erase(eid)
	m.invalidate()
	m.notify.emit("%s dejó la empresa." % e["name"], "info")
	m.business_changed.emit(e["business"])
	return GameModel.ok()


## Sueldos (gasto continuo), experiencia y rotación de candidatos.
static func advance(m: GameModel, dt: float, offline: bool) -> void:
	var total := m.salaries_per_sec()
	if total > 0.0 or m.salary_debt > 0:
		m.salary_due += total * dt
		var due := Economy.to_int_floor(m.salary_due)
		m.salary_due -= due
		var owed := due + m.salary_debt
		if owed > 0:
			var paid := m.economy.spend_up_to(owed, "sueldos")
			var had_debt := m.salary_debt > 0
			m.salary_debt = owed - paid
			if m.salary_debt > 0 and not had_debt:
				m.invalidate()
				m.notify.emit("No alcanza para los sueldos: tu equipo trabaja a reglamento (50 %) hasta que se pague.", "bad")
			elif m.salary_debt == 0 and had_debt:
				m.invalidate()
				m.notify.emit("Sueldos al día. El equipo vuelve a rendir al 100 %.", "good")

	var leveled := false
	for e in m.employees.values():
		var before := xp_level(m, e)
		e["xp"] = float(e["xp"]) + dt
		if xp_level(m, e) > before:
			leveled = true
			if not offline:
				m.notify.emit("%s ganó experiencia (nivel %d)." % [e["name"], xp_level(m, e)], "good")
	if leveled:
		m.invalidate()

	for id in m.owned_ids():
		var s: Dictionary = m.biz[id]
		if float(s["reroll_cd"]) > 0.0:
			s["reroll_cd"] = maxf(0.0, float(s["reroll_cd"]) - dt)
		s["cand_timer"] = float(s["cand_timer"]) - dt
		if s["cand_timer"] <= 0.0:
			generate_candidates(m, id)
