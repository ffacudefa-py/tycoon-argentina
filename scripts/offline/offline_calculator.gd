class_name OfflineCalculator
extends RefCounted
## Progreso mientras la app estuvo cerrada (o en segundo plano).
##
## No hay procesos en segundo plano: al volver se mide el tiempo desde la
## última actividad y se simula con la MISMA lógica que online (pasos de 5 s).
## Por eso sólo producen los negocios realmente automatizados, se agota el
## stock si no hay repositor y se pagan los sueldos.
##
## Protecciones de reloj:
## - Se guarda el máximo instante visto (max_seen). Si el reloj vuelve atrás,
##   no se paga nada y tampoco se "recupera" ese tiempo al adelantarlo de nuevo.
## - Tope de 8 h (+ ventaja de prestigio "Caja fuerte").


static func cap_seconds(m: GameModel) -> float:
	var hours := float(m.data.balance["offline_cap_hours"]) + float(m.data.perk_by_id["caja_fuerte"]["effects"]["offline_hours"]) * m.perk_level("caja_fuerte")
	return hours * 3600.0


static func apply(m: GameModel) -> Dictionary:
	var now := m.now()
	var last := float(m.time_state.get("last_active", 0.0))
	var max_seen := float(m.time_state.get("max_seen", 0.0))
	var result := {"elapsed": 0.0, "credited": 0.0, "capped": false, "clock_issue": false,
		"earned": 0, "spent": 0, "per_business": {}, "stockouts": [], "salaries": 0}
	if last <= 0.0 or is_nan(now):
		m.time_state["last_active"] = now
		m.time_state["max_seen"] = maxf(max_seen, now)
		return result
	var base := maxf(last, max_seen)
	if now + 1.0 < base:
		# Reloj hacia atrás: nada que pagar. max_seen se conserva.
		result["clock_issue"] = now + float(m.data.balance["clock_tolerance_seconds"]) < base
		m.time_state["last_active"] = now
		return result
	var elapsed := now - base
	result["elapsed"] = elapsed
	var credited := minf(elapsed, cap_seconds(m))
	result["credited"] = credited
	result["capped"] = elapsed > credited
	if credited >= float(m.data.balance["offline_min_seconds"]) or credited > 0.0:
		_simulate(m, credited, result)
	m.time_state["last_active"] = now
	m.time_state["max_seen"] = maxf(max_seen, now)
	return result


static func _simulate(m: GameModel, seconds: float, result: Dictionary) -> void:
	var earned_before := m.economy.run_earned
	var spent_before := m.economy.run_spent
	var salaries_before := int(m.economy.expense_by_reason.get("sueldos", 0))
	var per_before := {}
	for id in m.owned_ids():
		per_before[id] = int(m.biz[id]["earned"])
	var step := float(m.data.balance["offline_step_seconds"])
	var t := 0.0
	var stockout_noted := {}
	while t < seconds:
		var dt := minf(step, seconds - t)
		m.simulate(dt, true)
		t += dt
		for id in m.owned_ids():
			if not stockout_noted.has(id) and m.derive(id)["auto_sell"] and not m.has_stock(id) and m.biz[id]["orders"].is_empty():
				stockout_noted[id] = t
	result["earned"] = m.economy.run_earned - earned_before
	result["spent"] = m.economy.run_spent - spent_before
	result["salaries"] = int(m.economy.expense_by_reason.get("sueldos", 0)) - salaries_before
	for id in per_before:
		var diff := int(m.biz[id]["earned"]) - int(per_before[id])
		if diff > 0:
			result["per_business"][id] = diff
	for id in stockout_noted:
		result["stockouts"].append({"business": id, "after": stockout_noted[id]})
	m.invalidate()
	m.update_progress()
