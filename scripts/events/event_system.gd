class_name EventSystem
extends RefCounted
## Eventos económicos temporales e inflación ficticia (opcional).
##
## - Se sortean localmente con pesos, sólo con la app abierta.
## - Máximo 2 a la vez y como mucho uno negativo; nunca se repite el último.
## - Los multiplicadores combinados se acotan (multiplier_clamp) para que
##   varios eventos seguidos no rompan el equilibrio.
## - Offline sólo corre su duración (no aparecen eventos nuevos).


static func advance(m: GameModel, dt: float, offline: bool) -> void:
	var active: Array = m.events["active"]
	var ended := false
	for i in range(active.size() - 1, -1, -1):
		var ev: Dictionary = active[i]
		ev["remaining"] = float(ev["remaining"]) - dt
		if ev["remaining"] <= 0.0:
			active.remove_at(i)
			ended = true
			if not offline:
				m.notify.emit("Terminó: %s." % m.data.event_by_id[ev["id"]]["name"], "info")
	if ended:
		m.invalidate()
		m.events_changed.emit()
	if offline:
		return
	_advance_inflation(m, dt)
	m.events["next_in"] = float(m.events["next_in"]) - dt
	if m.events["next_in"] <= 0.0:
		var cfg: Dictionary = m.data.events_cfg
		m.events["next_in"] = m.rng.randf_range(float(cfg["interval_min"]), float(cfg["interval_max"]))
		try_spawn(m)


static func eligible(m: GameModel) -> Array:
	var cfg: Dictionary = m.data.events_cfg
	var active: Array = m.events["active"]
	var out := []
	if active.size() >= int(cfg["max_active"]) or m.owned_ids().size() < int(cfg["min_businesses"]):
		return out
	var bad_active := false
	var active_ids := []
	for a in active:
		active_ids.append(a["id"])
		if m.data.event_by_id[a["id"]]["kind"] == "bad":
			bad_active = true
	for e in cfg["events"]:
		if active_ids.has(e["id"]) or e["id"] == m.events.get("last_id", ""):
			continue
		if m.stage < int(e["stage"]):
			continue
		if e["kind"] == "bad" and bad_active:
			continue
		if not _has_target(m, e):
			continue
		out.append(e)
	return out


static func try_spawn(m: GameModel, forced_id := "") -> Dictionary:
	var pool := eligible(m)
	if forced_id != "":
		pool = pool.filter(func(e): return e["id"] == forced_id)
	if pool.is_empty():
		return {}
	var total := 0.0
	for e in pool:
		total += float(e["weight"])
	var roll := m.rng.randf() * total
	var chosen: Dictionary = pool[0]
	for e in pool:
		roll -= float(e["weight"])
		if roll <= 0.0:
			chosen = e
			break
	var inst := {"id": chosen["id"], "remaining": float(chosen["duration"]), "business": ""}
	if chosen["target"].get("businesses", "") == "random_owned":
		var owned := m.owned_ids()
		inst["business"] = owned[m.rng.randi() % owned.size()]
		# Un gerente lo resuelve solo.
		if m.derive(inst["business"])["manager"]:
			m.notify.emit("%s: tu gerente de %s lo resolvió al toque." % [chosen["name"], m.data.business_by_id[inst["business"]]["name"]], "good")
			m.events["last_id"] = chosen["id"]
			return {}
	m.events["active"].append(inst)
	m.events["last_id"] = chosen["id"]
	m.invalidate()
	var where := ""
	if inst["business"] != "":
		where = " (%s)" % m.data.business_by_id[inst["business"]]["name"]
	m.notify.emit("%s%s: %s" % [chosen["name"], where, chosen["description"]], "bad" if chosen["kind"] == "bad" else "good")
	m.celebrate.emit("event", {"event": chosen["id"]})
	m.events_changed.emit()
	return inst


static func _has_target(m: GameModel, e: Dictionary) -> bool:
	if e["target"].get("businesses", "") == "random_owned":
		return true
	for id in m.owned_ids():
		if _matches(m, e["target"], id) or not _product_targets(m, e["target"], id).is_empty():
			return true
	return false


static func _matches(m: GameModel, target: Dictionary, bid: String) -> bool:
	var tags: Array = m.data.business_by_id[bid]["tags"]
	for t in target.get("business_tags", []):
		if tags.has(t):
			return true
	return false


static func _product_targets(m: GameModel, target: Dictionary, bid: String) -> Array:
	var out := []
	var ptags: Array = target.get("product_tags", [])
	if ptags.is_empty():
		return out
	for p in m.data.business_by_id[bid]["products"]:
		for t in p["tags"]:
			if ptags.has(t):
				out.append(p["id"])
				break
	return out


## Lista de (target, effects) que aplica cada evento activo.
static func _parts(m: GameModel, inst: Dictionary) -> Array:
	var e: Dictionary = m.data.event_by_id[inst["id"]]
	var parts := [[e["target"], e["effects"]]]
	if e.has("secondary"):
		parts.append([e["secondary"]["target"], e["secondary"]["effects"]])
	return parts


static func modifiers_for(m: GameModel, bid: String) -> Dictionary:
	var out := {"revenue": 1.0, "speed": 1.0, "cost": 1.0, "demand": {}}
	for inst in m.events.get("active", []):
		for part in _parts(m, inst):
			var target: Dictionary = part[0]
			var eff: Dictionary = part[1]
			var hit := false
			if target.get("businesses", "") == "random_owned":
				hit = inst.get("business", "") == bid
			else:
				hit = _matches(m, target, bid)
			if hit:
				for k in ["revenue", "speed", "cost"]:
					if eff.has(k):
						out[k] *= float(eff[k])
			if eff.has("demand"):
				for pid in _product_targets(m, target, bid):
					out["demand"][pid] = float(out["demand"].get(pid, 1.0)) * float(eff["demand"])
	var clamp_range: Array = m.data.events_cfg["multiplier_clamp"]
	for k in ["revenue", "speed", "cost"]:
		out[k] = clampf(out[k], float(clamp_range[0]), float(clamp_range[1]))
	for pid in out["demand"]:
		out["demand"][pid] = clampf(out["demand"][pid], float(clamp_range[0]), float(clamp_range[1]))
	return out


static func affects(m: GameModel, bid: String) -> bool:
	var mods := modifiers_for(m, bid)
	return mods["revenue"] != 1.0 or mods["speed"] != 1.0 or mods["cost"] != 1.0 or not mods["demand"].is_empty()


## ¿Hay un efecto de este tipo activo? below=true busca descuentos (<1).
static func has_effect(m: GameModel, bid: String, key: String, below: bool) -> bool:
	var v: float = modifiers_for(m, bid)[key]
	return v < 1.0 if below else v > 1.0


static func resolve_cost(m: GameModel, index: int, choice_id: String) -> int:
	var inst: Dictionary = m.events["active"][index]
	var e: Dictionary = m.data.event_by_id[inst["id"]]
	for c in e.get("choices", []):
		if c["id"] == choice_id:
			var secs := float(c["cost_income_seconds"])
			if secs <= 0.0:
				return 0
			var base := m.income_per_sec()
			if inst["business"] != "":
				base = maxf(base, m.derive(inst["business"])["profit_sec"])
			return maxi(50, Economy.to_int_ceil(base * secs))
	return 0


static func resolve(m: GameModel, index: int, choice_id: String) -> Dictionary:
	var active: Array = m.events["active"]
	if index < 0 or index >= active.size():
		return GameModel.fail("Ese evento ya terminó.")
	var inst: Dictionary = active[index]
	var e: Dictionary = m.data.event_by_id[inst["id"]]
	var choice: Dictionary = {}
	for c in e.get("choices", []):
		if c["id"] == choice_id:
			choice = c
	if choice.is_empty():
		return GameModel.fail("Opción inválida.")
	if choice["result"] != "end":
		return GameModel.ok("Esperás a que se solucione.")
	var cost := resolve_cost(m, index, choice_id)
	if not m.economy.spend(cost, "imprevistos"):
		return GameModel.fail("No te alcanza (%s)." % Fmt.cost(cost))
	active.remove_at(index)
	m._count("events_resolved", 1)
	m.invalidate()
	m.notify.emit("¡Solucionado! %s vuelve a la normalidad." % m.data.business_by_id[inst["business"]]["name"] if inst["business"] != "" else "¡Solucionado!", "good")
	m.events_changed.emit()
	return GameModel.ok()


# ---------------------------------------------------------------------------
# Inflación ficticia (opcional, desactivada por defecto)
# ---------------------------------------------------------------------------

static func _advance_inflation(m: GameModel, dt: float) -> void:
	if not m.inflation_active():
		return
	var cfg: Dictionary = HardMode.inflation_cfg(m)
	var inf: Dictionary = m.inflation
	inf["next_in"] = float(inf["next_in"]) - dt
	if not inf["announced"] and inf["next_in"] <= float(cfg["warning"]):
		inf["announced"] = true
		m.notify.emit("Rumores de remarcación: en %s la mercadería sube %d %%. ¡Reponé antes!" % [Fmt.duration(cfg["warning"]), int(float(cfg["cost_step"]) * 100)], "bad")
	if inf["next_in"] <= 0.0:
		inf["next_in"] = float(cfg["period"])
		inf["announced"] = false
		var max_index := float(cfg["max_index"])
		if float(inf["cost_index"]) < max_index:
			inf["cost_index"] = minf(max_index, float(inf["cost_index"]) * (1.0 + float(cfg["cost_step"])))
			inf["price_in"] = float(cfg["price_lag"])
			m.invalidate()
			m.notify.emit("Remarcación: la mercadería subió. Tus precios se acomodan en %s." % Fmt.duration(cfg["price_lag"]), "bad")
	if float(inf.get("price_in", -1.0)) > 0.0:
		inf["price_in"] = float(inf["price_in"]) - dt
		if inf["price_in"] <= 0.0:
			inf["price_in"] = -1.0
			inf["price_index"] = minf(float(cfg["max_index"]), float(inf["price_index"]) * (1.0 + float(cfg["price_step"])))
			m.invalidate()
			m.notify.emit("Actualizaste la lista de precios.", "info")
