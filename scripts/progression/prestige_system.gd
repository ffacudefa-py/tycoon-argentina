class_name PrestigeSystem
extends RefCounted
## "Fundar un nuevo grupo empresarial": vendés todo a cambio de puntos de
## prestigio permanentes. Siempre opcional y siempre con confirmación (la UI
## muestra qué se pierde y qué se conserva antes de llamar a perform()).
##
## Se pierde: dinero, negocios, niveles, mejoras, mercadería, empleados,
##            zonas, eventos activos, turbos y la etapa empresarial.
## Se conserva: puntos y ventajas de prestigio, logros, avatares, nombre,
##            estadísticas históricas, misiones cumplidas, recompensa diaria,
##            configuración y tutorial.


static func unlocked(m: GameModel) -> bool:
	return m.stage >= int(m.data.prestige_cfg["min_stage"]) or int(m.prestige.get("count", 0)) > 0


static func points_for(m: GameModel, run_earnings: float) -> int:
	return int(floor(2.0 * sqrt(maxf(0.0, run_earnings) / float(m.data.prestige_cfg["divisor"]))))


static func pending_points(m: GameModel) -> int:
	if m.stage < int(m.data.prestige_cfg["min_stage"]):
		return 0
	return points_for(m, float(m.economy.run_earned))


static func available_points(m: GameModel) -> int:
	return int(m.prestige["points"]) - int(m.prestige["spent"])


static func perform(m: GameModel) -> Dictionary:
	var gain := pending_points(m)
	if gain <= 0:
		return GameModel.fail("Todavía no ganarías puntos de prestigio.")
	m.prestige["points"] = int(m.prestige["points"]) + gain
	m.prestige["count"] = int(m.prestige.get("count", 0)) + 1
	var company: String = m.profile["company"]
	m._reset_run()
	# Las diarias de ganancias usan el histórico, así que siguen bien.
	m.add_milestone("Fundaste un nuevo grupo empresarial (+%d puntos de prestigio)." % gain)
	m.notify.emit("¡Nuevo grupo empresarial! +%d puntos de prestigio." % gain, "reward")
	m.celebrate.emit("prestige", {"points": gain})
	m.profile["company"] = company
	m.businesses_changed.emit()
	m.world_changed.emit()
	m.update_progress()
	return GameModel.ok()


static func perk_cost(m: GameModel, pid: String) -> int:
	var p: Dictionary = m.data.perk_by_id[pid]
	return int(p["cost"]) * (m.perk_level(pid) + 1)


static func buy_perk(m: GameModel, pid: String) -> Dictionary:
	if not m.data.perk_by_id.has(pid):
		return GameModel.fail("Ventaja desconocida.")
	var p: Dictionary = m.data.perk_by_id[pid]
	var lvl := m.perk_level(pid)
	if lvl >= int(p["max_level"]):
		return GameModel.fail("Ya está al máximo.")
	var cost := perk_cost(m, pid)
	if available_points(m) < cost:
		return GameModel.fail("Te faltan puntos de prestigio.")
	m.prestige["spent"] = int(m.prestige["spent"]) + cost
	m.prestige["perks"][pid] = lvl + 1
	m.invalidate()
	m.celebrate.emit("upgrade", {"perk": pid})
	m.notify.emit("%s nivel %d" % [p["name"], lvl + 1], "good")
	m.progress_changed.emit()
	return GameModel.ok()
