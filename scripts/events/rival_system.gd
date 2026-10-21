class_name RivalSystem
extends RefCounted
## Empresas rivales simuladas (sin economía propia en tiempo real).
##
## Cada rival tiene un poder 1..10 en ciertas zonas y rubros. Le quita
## clientes a tus negocios de ese rubro en esas zonas. Crece más cuando
## tenés presencia en su terreno; podés frenarlo con campañas.


static func competition_for(m: GameModel, bid: String) -> float:
	var s: Dictionary = m.biz[bid]
	var zone: Dictionary = m.data.zone_by_id.get(s["zone"], m.data.zones[0])
	var comp := float(zone["competition"])
	var tags: Array = m.data.business_by_id[bid]["tags"]
	for r in m.data.rivals:
		if not (r["zones"] as Array).has(s["zone"]):
			continue
		for t in r["tags"]:
			if tags.has(t):
				comp += float(m.data.world["competition_per_power"]) * int(m.rivals[r["id"]]["power"])
				break
	return minf(comp, float(m.data.world["max_competition"]))


static func presence(m: GameModel, rid: String) -> int:
	var r: Dictionary = m.data.rival_by_id[rid]
	var n := 0
	for id in m.owned_ids():
		if not (r["zones"] as Array).has(m.biz[id]["zone"]):
			continue
		for t in r["tags"]:
			if (m.data.business_by_id[id]["tags"] as Array).has(t):
				n += 1
				break
	return n


static func advance(m: GameModel, dt: float) -> void:
	var period := float(m.data.world["rival_update_seconds"])
	var changed := false
	for r in m.data.rivals:
		var st: Dictionary = m.rivals[r["id"]]
		st["timer"] = float(st.get("timer", 0.0)) + dt
		if float(st.get("cooldown", 0.0)) > 0.0:
			st["cooldown"] = maxf(0.0, float(st["cooldown"]) - dt)
		if st["timer"] < period:
			continue
		st["timer"] = 0.0
		var grow := 0.1
		if presence(m, r["id"]) > 0:
			grow = {"Agresivo": 0.45, "Expansivo": 0.35, "Conservador": 0.2}.get(r["behavior"], 0.25)
		var roll := m.rng.randf()
		var lines: Dictionary = m.data.world["rival_lines"]
		var zone_name: String = m.data.zone_by_id[r["zones"][m.rng.randi() % r["zones"].size()]]["name"]
		if roll < grow and int(st["power"]) < 10:
			st["power"] = int(st["power"]) + 1
			st["trend"] = 1
			st["last"] = _line(m, lines["grow"], r["name"], zone_name)
			_log(m, st["last"])
			changed = true
		elif roll > 0.85 and int(st["power"]) > 1:
			st["power"] = int(st["power"]) - 1
			st["trend"] = -1
			st["last"] = _line(m, lines["shrink"], r["name"], zone_name)
			_log(m, st["last"])
			changed = true
		else:
			st["trend"] = 0
	if changed:
		m.invalidate()
		m.world_changed.emit()


static func campaign_cost(m: GameModel) -> int:
	var w: Dictionary = m.data.world
	return maxi(int(w["campaign_min_cost"]), Economy.to_int_ceil(m.income_per_sec() * float(w["campaign_income_seconds"])))


static func campaign(m: GameModel, rid: String) -> Dictionary:
	if not m.rivals.has(rid):
		return GameModel.fail("Rival desconocido.")
	var st: Dictionary = m.rivals[rid]
	if float(st.get("cooldown", 0.0)) > 0.0:
		return GameModel.fail("Tu equipo de marketing descansa: %s." % Fmt.duration(st["cooldown"]))
	if int(st["power"]) <= 1:
		return GameModel.fail("Este rival ya está en su mínimo.")
	var cost := campaign_cost(m)
	if not m.economy.spend(cost, "marketing"):
		return GameModel.fail("No te alcanza (%s)." % Fmt.cost(cost))
	var r: Dictionary = m.data.rival_by_id[rid]
	st["power"] = maxi(1, int(st["power"]) - int(m.data.world["campaign_power_reduction"]))
	st["cooldown"] = float(m.data.world["campaign_cooldown_seconds"])
	st["trend"] = -1
	st["last"] = _line(m, m.data.world["rival_lines"]["campaign"], r["name"], "")
	_log(m, st["last"])
	m._count("campaigns", 1)
	m.invalidate()
	m.celebrate.emit("campaign", {"rival": rid})
	m.notify.emit(st["last"], "good")
	m.world_changed.emit()
	return GameModel.ok()


static func _line(m: GameModel, options: Array, rname: String, zname: String) -> String:
	return (options[m.rng.randi() % options.size()] as String).replace("{r}", rname).replace("{z}", zname)


static func _log(m: GameModel, text: String) -> void:
	m.rival_log.append({"t": m.now(), "text": text})
	while m.rival_log.size() > 20:
		m.rival_log.pop_front()
