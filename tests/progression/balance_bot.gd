class_name BalanceBot
extends RefCounted
## Jugador simulado para probar el ritmo de progresión.
## Juega "razonablemente": mantiene apretado VENDER en negocios manuales,
## repone, reclama recompensas y compra lo que mejor rinde (costo / mejora
## de ganancia por segundo). No usa el prestigio.

var m: GameModel
var clock_holder: Dictionary
var timeline := {}        ## hito -> segundos
var t := 0.0
var _decide_timer := 0.0


func _init(model: GameModel, holder: Dictionary) -> void:
	m = model
	clock_holder = holder
	m.open_business(m.first_business())


func mark(key: String) -> void:
	if not timeline.has(key):
		timeline[key] = t


func play(seconds: float, tick := 0.1) -> void:
	var steps := int(seconds / tick)
	for i in steps:
		clock_holder["t"] = float(clock_holder["t"]) + tick
		t += tick
		for id in m.owned_ids():
			if not m.derive(id)["auto_sell"] and not m.biz[id]["running"]:
				m.tap_sell(id)
		m.simulate(tick)
		_decide_timer += tick
		if _decide_timer >= 0.5:
			_decide_timer = 0.0
			_decide()


func _profit_with(id: String, change: Callable) -> float:
	var snapshot: Dictionary = m.biz[id].duplicate(true)
	var before: float = _effective_profit(id)
	change.call()
	m.invalidate()
	var after: float = _effective_profit(id)
	m.biz[id] = snapshot
	m.invalidate()
	return after - before


## Ganancia por segundo que realmente produce (manual cuenta igual:
## el bot mantiene apretado el botón).
func _effective_profit(id: String) -> float:
	var d := m.derive(id)
	return d["profit_sec"] - d["salary_sec"]


func _decide() -> void:
	# Reclamar todo lo reclamable
	for mid in m.missions["completed"].keys():
		if not m.missions["claimed"].has(mid):
			ProgressionSystem.claim_mission(m, mid)
	for mid in m.daily_missions["completed"].keys():
		if not m.daily_missions["claimed"].has(mid):
			ProgressionSystem.claim_daily_mission(m, mid)
	if ProgressionSystem.can_claim_daily_reward(m)["ok"]:
		ProgressionSystem.claim_daily_reward(m)
	# Reponer
	for id in m.owned_ids():
		var d := m.derive(id)
		if not d["auto_restock"] and m.stock_ratio(id) < 0.4 and m.biz[id]["orders"].is_empty():
			if m.restock(id)["ok"]:
				mark("first_restock")
	# Eventos: resolver fallas si conviene
	for i in range(m.events["active"].size() - 1, -1, -1):
		if m.events["active"][i]["id"] == "falla_suministro":
			if EventSystem.resolve_cost(m, i, "flete") < m.economy.money * 0.2:
				EventSystem.resolve(m, i, "flete")
	# Reserva para reponer lo manual y metas de ahorro (contratar / abrir negocio).
	var reserve := 0
	for id in m.owned_ids():
		if not m.derive(id)["auto_restock"]:
			reserve += int(m.restock_quote(id)["total"] * 0.5)
	var goal_cost := -1
	var goal := Callable()
	for id in m.owned_ids():
		var d := m.derive(id)
		if d["team_size"] >= d["slots"]:
			continue
		var cands: Array = m.biz[id]["candidates"]
		for i in cands.size():
			var role: String = cands[i]["role"]
			var need: bool = (role == "vendedor" and not d["auto_sell"]) or (role == "repositor" and d["auto_sell"] and not d["auto_restock"])
			if need and (goal_cost < 0 or int(cands[i]["hire"]) < goal_cost):
				goal_cost = int(cands[i]["hire"])
				var bid: String = id
				var idx := i
				var r: String = role
				goal = func() -> bool:
					var ok: bool = EmployeeSystem.hire(m, bid, idx)["ok"]
					if ok:
						mark("first_hire")
						if r == "repositor":
							mark("first_repositor")
					return ok
	for def in m.data.businesses:
		if m.biz[def["id"]]["owned"]:
			continue
		var st := m.unlock_status(def["id"])
		if st["available"] and (goal_cost < 0 or st["cost"] < goal_cost * 3):
			goal_cost = st["cost"]
			var nb: String = def["id"]
			goal = func() -> bool: return m.buy_business(nb)["ok"]
		break
	if goal.is_valid() and m.economy.money - reserve >= goal_cost:
		goal.call()
	# Compra por mejor retorno (si no se está ahorrando para una meta cercana)
	for _k in 6:
		if not _buy_best(reserve, goal_cost):
			break
	# Campaña contra el rival de una provincia en disputa cuando es barata
	for zid in m.zones:
		if ConquestSystem.is_conquered(m, zid):
			continue
		var rid: String = m.data.zone_by_id[zid]["rival"]
		if int(m.rivals[rid]["power"]) >= 4 and RivalSystem.campaign_cost(m) < m.economy.money * 0.05:
			RivalSystem.campaign(m, rid)
	m.update_progress()
	mark("stage_%d" % m.stage)
	for id in m.owned_ids():
		mark("own_" + id)
	for zid in m.zones:
		if ConquestSystem.is_conquered(m, zid):
			mark("conquer_" + zid)


func _buy_best(reserve: int, goal_cost: int) -> bool:
	var best_score := INF
	var best_action := Callable()
	var best_cost := 0
	for id in m.owned_ids():
		var s: Dictionary = m.biz[id]
		# Nivel
		if int(s["level"]) < int(m.data.business_by_id[id]["max_level"]):
			var cost := m.level_cost(id, 1)
			var gain := _profit_with(id, func() -> void: s["level"] = int(s["level"]) + 1)
			if gain > 0.0:
				var score := float(cost) / gain
				if score < best_score:
					best_score = score
					best_cost = cost
					best_action = func() -> bool: return m.buy_levels(id, 1)["ok"]
		# Mejoras
		for u in m.data.upgrades:
			var st := m.upgrade_status(id, u["id"])
			if st["maxed"] or st["locked"]:
				continue
			var uid: String = u["id"]
			var gain2 := _profit_with(id, func() -> void: s["upgrades"][uid] = int(s["upgrades"].get(uid, 0)) + 1)
			# Las mejoras de capacidad/eficiencia no suben la ganancia directa: se valoran igual un poco.
			gain2 = maxf(gain2, _effective_profit(id) * 0.04)
			var score2 := float(st["cost"]) / maxf(gain2, 0.0001)
			if score2 < best_score:
				best_score = score2
				best_cost = st["cost"]
				best_action = func() -> bool:
					var ok: bool = m.buy_upgrade(id, uid)["ok"]
					if ok:
						mark("first_upgrade")
					return ok
		# Otras contrataciones (cajero, encargado, gerente...)
		var d := m.derive(id)
		if d["team_size"] < d["slots"] and d["auto_sell"]:
			var cands: Array = s["candidates"]
			for i in cands.size():
				var c: Dictionary = cands[i]
				var role: Dictionary = m.data.role_by_id[c["role"]]
				var g: float = (float(role["effects"].get("speed", 0.0)) + float(role["effects"].get("revenue", 0.0))) * float(c["eff"]) * float(d["profit_sec"]) - float(c["salary"])
				if g > 0.0:
					var score3 := float(c["hire"]) / g
					if score3 < best_score:
						best_score = score3
						best_cost = int(c["hire"])
						var idx := i
						best_action = func() -> bool: return EmployeeSystem.hire(m, id, idx)["ok"]
	# Con una meta de ahorro a la vista, sólo compra lo que se paga rápido.
	var spendable := m.economy.money - reserve
	if goal_cost > 0 and best_score > 60.0 and spendable < goal_cost * 4:
		return false
	if best_action.is_valid() and spendable >= best_cost:
		return best_action.call()
	return false
