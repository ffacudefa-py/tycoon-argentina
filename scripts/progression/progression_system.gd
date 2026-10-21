class_name ProgressionSystem
extends RefCounted
## Misiones principales, desafíos, misiones diarias, logros, recompensa
## diaria por entrar y entrega de recompensas.
##
## - El progreso se registra solo (update() corre una vez por segundo y
##   después de las acciones). Completar ≠ reclamar: la recompensa queda
##   esperando y se puede reclamar UNA vez (dict "claimed").
## - Los logros entregan su recompensa automáticamente al desbloquearse
##   (también una sola vez: quedan registrados con su fecha).


static func update(m: GameModel) -> void:
	var changed := false
	# Principales (en cadena: al completar una se activa la siguiente)
	var idx := int(m.missions["main_index"])
	while idx < m.data.missions_main.size():
		var mis: Dictionary = m.data.missions_main[idx]
		if m.metric(mis["metric"]) >= float(mis["target"]):
			m.missions["completed"][mis["id"]] = true
			idx += 1
			changed = true
			m.notify.emit("Misión cumplida: %s" % mis["title"], "reward")
			m.celebrate.emit("mission", {"id": mis["id"]})
		else:
			break
	m.missions["main_index"] = idx
	# Desafíos
	for c in m.data.challenges:
		if m.missions["completed"].has(c["id"]):
			continue
		if m.metric(c["metric"]) >= float(c["target"]):
			m.missions["completed"][c["id"]] = true
			changed = true
			m.notify.emit("Desafío cumplido: %s" % c["title"], "reward")
			m.celebrate.emit("mission", {"id": c["id"]})
	# Diarias
	ensure_daily(m)
	for dm in m.daily_missions["list"]:
		if m.daily_missions["completed"].has(dm["id"]):
			continue
		if daily_progress(m, dm) >= float(dm["target"]):
			m.daily_missions["completed"][dm["id"]] = true
			changed = true
			m.notify.emit("Diaria cumplida: %s" % dm["title"], "reward")
			m.celebrate.emit("mission", {"id": dm["id"]})
	# Logros
	for a in m.data.achievements:
		if m.achievements.has(a["id"]):
			continue
		if m.metric(a["metric"]) >= float(a["target"]):
			m.achievements[a["id"]] = m.now()
			changed = true
			m.notify.emit("¡Logro desbloqueado! %s" % a["name"], "reward")
			m.celebrate.emit("achievement", {"id": a["id"]})
			grant(m, a["reward"], "logros")
			m.add_milestone("Logro: %s." % a["name"])
	if changed:
		m.progress_changed.emit()


# ---------------------------------------------------------------------------
# Recompensas
# ---------------------------------------------------------------------------

static func reward_money(m: GameModel, r: Dictionary) -> int:
	if r.has("money"):
		return int(r["money"])
	if r.has("income_seconds"):
		return maxi(int(r.get("min", 0)), Economy.to_int_floor(m.income_per_sec() * float(r["income_seconds"])))
	return 0


static func describe(m: GameModel, r: Dictionary) -> String:
	var parts := []
	var money := reward_money(m, r)
	if money > 0:
		parts.append(Fmt.money(money))
	if r.has("boost"):
		parts.append("Turbo x%s (%s)" % [str(r["boost"]["mult"]).trim_suffix(".0"), Fmt.duration(r["boost"]["seconds"])])
	if r.has("icon"):
		var a = m.data.avatar_by_id.get(r["icon"])
		parts.append("Avatar: %s" % (a["name"] if a else r["icon"]))
	return " + ".join(parts)


static func grant(m: GameModel, r: Dictionary, category: String) -> void:
	if r.has("icon"):
		var got := m.unlock_avatar(r["icon"])
		if not got and r.has("fallback"):
			grant(m, r["fallback"], category)
	var money := reward_money(m, r)
	if money > 0:
		m.economy.earn(money, category)
	if r.has("boost"):
		m.add_boost(float(r["boost"]["mult"]), float(r["boost"]["seconds"]))
		m.notify.emit("¡Turbo de ingresos x%s activado!" % str(r["boost"]["mult"]).trim_suffix(".0"), "reward")


## Reclamo de misión principal o desafío. Imposible reclamar dos veces.
static func claim_mission(m: GameModel, mid: String) -> Dictionary:
	if not m.missions["completed"].has(mid):
		return GameModel.fail("Todavía no completaste esta misión.")
	if m.missions["claimed"].has(mid):
		return GameModel.fail("Ya reclamaste esta recompensa.")
	var mis: Dictionary = m.data.mission_by_id[mid]
	m.missions["claimed"][mid] = true
	grant(m, mis["reward"], "misiones")
	m.celebrate.emit("claim", {"id": mid})
	m.progress_changed.emit()
	return GameModel.ok()


static func claim_daily_mission(m: GameModel, mid: String) -> Dictionary:
	if not m.daily_missions["completed"].has(mid):
		return GameModel.fail("Todavía no completaste esta diaria.")
	if m.daily_missions["claimed"].has(mid):
		return GameModel.fail("Ya reclamaste esta recompensa.")
	m.daily_missions["claimed"][mid] = true
	grant(m, m.data.daily_cfg["reward"], "misiones")
	m.celebrate.emit("claim", {"id": mid})
	m.progress_changed.emit()
	return GameModel.ok()


static func unclaimed_count(m: GameModel) -> int:
	var n := 0
	for mid in m.missions["completed"]:
		if not m.missions["claimed"].has(mid):
			n += 1
	for mid in m.daily_missions["completed"]:
		if not m.daily_missions["claimed"].has(mid):
			n += 1
	if can_claim_daily_reward(m)["ok"]:
		n += 1
	return n


# ---------------------------------------------------------------------------
# Días (hora local) y validación de reloj
# ---------------------------------------------------------------------------

static func day_index(m: GameModel) -> int:
	return int(floor((m.now() + m.tz_bias_minutes * 60.0) / 86400.0))


## El reloj del celular se atrasó respecto del máximo visto: algo raro.
static func clock_suspicious(m: GameModel) -> bool:
	return m.now() + float(m.data.balance["clock_tolerance_seconds"]) < float(m.time_state.get("max_seen", 0.0))


# ---------------------------------------------------------------------------
# Misiones diarias
# ---------------------------------------------------------------------------

static func ensure_daily(m: GameModel) -> void:
	var today := day_index(m)
	if int(m.daily_missions["day"]) >= today:
		return  # mismo día, o el reloj fue para atrás: se conserva la lista actual
	var pool: Array = m.data.daily_cfg["pool"].duplicate()
	var r := RandomNumberGenerator.new()
	r.seed = hash("tycoon-daily-%d" % today)
	var picks := []
	while picks.size() < int(m.data.daily_cfg["count"]) and not pool.is_empty():
		var i := r.randi() % pool.size()
		var p: Dictionary = pool[i]
		pool.remove_at(i)
		var item := {"id": p["id"], "title": p["title"], "metric": p["metric"], "money_label": p.get("money_label", false)}
		if p.has("target_income_seconds"):
			item["target"] = maxf(float(p.get("min", 0)), floorf(m.income_per_sec() * float(p["target_income_seconds"])))
		else:
			item["target"] = float(p["target"])
		var t_label := Fmt.money(item["target"]) if item["money_label"] else Fmt.integer(item["target"])
		item["description"] = (p["description"] as String).replace("{t}", t_label)
		picks.append(item)
	var baseline := {}
	for it in picks:
		baseline[it["metric"]] = _daily_metric(m, it["metric"])
	m.daily_missions = {"day": today, "list": picks, "baseline": baseline, "completed": {}, "claimed": {}}
	m.progress_changed.emit()


static func _daily_metric(m: GameModel, metric: String) -> float:
	# Las ganancias diarias se miden con el histórico (no se reinicia con prestigio).
	if metric == "run_earnings":
		return m.metric("lifetime_earnings")
	return m.metric(metric)


static func daily_progress(m: GameModel, dm: Dictionary) -> float:
	return maxf(0.0, _daily_metric(m, dm["metric"]) - float(m.daily_missions["baseline"].get(dm["metric"], 0.0)))


# ---------------------------------------------------------------------------
# Recompensa diaria por entrar (ciclo de 7 días, sin castigo por faltar)
# ---------------------------------------------------------------------------

static func can_claim_daily_reward(m: GameModel) -> Dictionary:
	if clock_suspicious(m):
		return GameModel.fail("La fecha del teléfono parece haber cambiado. Volvé a intentar más tarde.")
	if day_index(m) <= int(m.daily_reward["last_day"]):
		return GameModel.fail("Ya reclamaste la recompensa de hoy. ¡Volvé mañana!")
	return GameModel.ok()


static func current_daily_reward(m: GameModel) -> Dictionary:
	return m.data.daily_rewards[int(m.daily_reward["index"]) % m.data.daily_rewards.size()]


static func claim_daily_reward(m: GameModel) -> Dictionary:
	var can := can_claim_daily_reward(m)
	if not can["ok"]:
		return can
	var entry := current_daily_reward(m)
	m.daily_reward["last_day"] = day_index(m)
	m.daily_reward["index"] = (int(m.daily_reward["index"]) + 1) % m.data.daily_rewards.size()
	m._count("daily_claims", 1)
	grant(m, entry["reward"], "recompensas")
	m.celebrate.emit("daily", {"day": entry["day"]})
	m.progress_changed.emit()
	return GameModel.ok(entry["label"])
