class_name Engagement
extends RefCounted
## Ciclo de enganche (10.3): que siempre haya algo cerca y que todo responda.
##   - COMBO: vender a mano seguido sube un multiplicador (x1,1 … x2) sobre esas
##     ventas; si parás, baja de a poco.
##   - COFRES: se ganan jugando (conquistas, regiones, logros, hitos de nivel,
##     desafíos de eventos) y dan un premio variable. Nunca se compran.
##   - PRÓXIMA META: la meta más cercana del negocio, con barra.
##   - DESAFÍOS DE EVENTO: algunos eventos traen una meta propia con cofre.
## Estado en m.engage (se guarda). Balance en progression.json → engagement.

const LEVEL_MARKS := [25, 50, 100]


static func default_state() -> Dictionary:
	return {"combo": 1.0, "combo_t": 0.0, "best_combo": 1.0, "chests": 0, "opened": 0, "marks": {}}


static func cfg(m: GameModel) -> Dictionary:
	return m.data.balance.get("engagement", {})


# --------------------------------------------------------------------- combo

static func combo(m: GameModel) -> float:
	return float(m.engage.get("combo", 1.0))


## Venta manual: cobra el extra del combo y lo sube. Devuelve el extra.
static func on_manual_sale(m: GameModel, credited: int) -> int:
	var c := cfg(m)
	var cur := combo(m)
	var extra := Economy.to_int_floor(float(credited) * (cur - 1.0))
	if extra > 0:
		extra = m.economy.earn(extra, "combo")
	m.engage["combo"] = minf(float(c.get("combo_max", 2.0)), cur + float(c.get("combo_step", 0.1)))
	m.engage["combo_t"] = float(c.get("combo_window", 3.0))
	m.engage["best_combo"] = maxf(float(m.engage.get("best_combo", 1.0)), float(m.engage["combo"]))
	return extra


static func advance(m: GameModel, dt: float) -> void:
	var t := float(m.engage.get("combo_t", 0.0)) - dt
	m.engage["combo_t"] = t
	if t <= 0.0 and combo(m) > 1.0:
		m.engage["combo"] = maxf(1.0, combo(m) - float(cfg(m).get("combo_decay", 0.25)) * dt)


# -------------------------------------------------------------------- cofres

static func grant_chest(m: GameModel, reason: String, n := 1) -> void:
	m.engage["chests"] = int(m.engage.get("chests", 0)) + n
	m.notify.emit("¡%s cofre%s! %s" % ["Un" if n == 1 else str(n), "" if n == 1 else "s", reason], "reward")
	m.celebrate.emit("chest", {"n": n})
	m.progress_changed.emit()


## Abre un cofre: premio variable con pesos de progression.json → engagement.chest.
## Devuelve {ok, kind, text}.
static func open_chest(m: GameModel) -> Dictionary:
	if int(m.engage.get("chests", 0)) <= 0:
		return {"ok": false, "msg": "No tenés cofres. Se ganan conquistando, con logros y en los eventos."}
	m.engage["chests"] = int(m.engage["chests"]) - 1
	m.engage["opened"] = int(m.engage.get("opened", 0)) + 1
	var table: Array = cfg(m).get("chest", [])
	var locked := []
	for a in m.data.avatars:
		if not (m.profile["avatars"] as Array).has(a["id"]):
			locked.append(a["id"])
	var total := 0.0
	for e in table:
		if e["kind"] != "avatar" or not locked.is_empty():
			total += float(e["weight"])
	var roll := m.rng.randf() * total
	var pick: Dictionary = table[0]
	for e in table:
		if e["kind"] == "avatar" and locked.is_empty():
			continue
		roll -= float(e["weight"])
		if roll <= 0.0:
			pick = e
			break
	var text := ""
	match pick["kind"]:
		"money":
			var secs := m.rng.randf_range(float(pick["seconds"][0]), float(pick["seconds"][1]))
			var amount := maxi(int(pick.get("min", 100)), Economy.to_int_floor(m.income_per_sec() * secs))
			m.economy.earn(amount, "cofres")
			text = Fmt.money(amount)
		"boost":
			var secs2 := float(pick["seconds"][m.rng.randi() % (pick["seconds"] as Array).size()])
			m.add_boost(float(pick["mult"]), secs2)
			text = "Turbo x%s por %s" % [str(pick["mult"]).trim_suffix(".0"), Fmt.duration(secs2)]
		"avatar":
			var av: String = locked[m.rng.randi() % locked.size()]
			m.unlock_avatar(av)
			text = "Avatar: %s" % m.data.avatar_by_id[av]["name"]
	m._count("chests_opened", 1)
	m.celebrate.emit("chest_open", {"kind": pick["kind"]})
	m.progress_changed.emit()
	return {"ok": true, "kind": pick["kind"], "text": text, "msg": "¡Cofre abierto! " + text}


## Hitos de nivel de cada negocio (25, 50, 100): un cofre por cada uno, una vez.
static func check_level_marks(m: GameModel) -> void:
	var marks: Dictionary = m.engage["marks"]
	for id in m.owned_ids():
		var lvl := int(m.biz[id]["level"])
		var got := int(marks.get(id, 0))
		for mk in LEVEL_MARKS:
			if lvl >= mk and got < mk:
				marks[id] = mk
				got = mk
				grant_chest(m, "%s llegó al nivel %d." % [m.data.business_by_id[id]["name"], mk])


# ------------------------------------------------------- desafíos de evento

static func check_event_goals(m: GameModel) -> void:
	for inst in m.events["active"]:
		var e: Dictionary = m.data.event_by_id[inst["id"]]
		if not e.has("goal") or inst.get("goal_done", false):
			continue
		var g: Dictionary = e["goal"]
		if event_goal_progress(m, inst) >= float(g["target"]):
			inst["goal_done"] = true
			grant_chest(m, "Cumpliste el desafío de %s." % e["name"], int(g.get("chests", 1)))


static func event_goal_progress(m: GameModel, inst: Dictionary) -> float:
	var e: Dictionary = m.data.event_by_id[inst["id"]]
	if not e.has("goal"):
		return 0.0
	return maxf(0.0, m.metric(e["goal"]["metric"]) - float(inst.get("goal_base", 0.0)))


# --------------------------------------------------------- próxima meta

## La meta más cercana del negocio: {text, value (0..1)}.
static func next_goal(m: GameModel, bid: String) -> Dictionary:
	var d := m.derive(bid)
	var s: Dictionary = m.biz[bid]
	var goals := []
	var zid: String = s["zone"]
	if not ConquestSystem.is_conquered(m, zid):
		var sh := ConquestSystem.share(m, zid)
		goals.append({"text": "Cuota %d %%: al 100 %% conquistás %s" % [int(floorf(sh * 100.0)), m.data.zone_by_id[zid]["name"]], "value": sh})
	var nm := int(d["next_milestone"])
	if nm > 0:
		var lvl := int(s["level"])
		var prev := 0
		for ms in m.data.balance["milestones"]:
			if int(ms["level"]) <= lvl:
				prev = int(ms["level"])
		goals.append({"text": "Nivel %d: hito de velocidad (faltan %d)" % [nm, nm - lvl], "value": float(lvl - prev) / maxf(1.0, float(nm - prev))})
	var best_cost := -1
	var best_name := ""
	for u in m.data.upgrades:
		var st := m.upgrade_status(bid, u["id"])
		if st["locked"] or st["maxed"]:
			continue
		if best_cost < 0 or int(st["cost"]) < best_cost:
			best_cost = int(st["cost"])
			best_name = m.upgrade_name(bid, u["id"])
	if best_cost > 0:
		var money := float(maxi(0, m.economy.money))
		var txt := ("Ya podés comprar: %s" % best_name) if money >= best_cost else ("Mejora \"%s\": %s" % [best_name, Fmt.cost(best_cost)])
		goals.append({"text": txt, "value": clampf(money / float(best_cost), 0.0, 1.0)})
	if goals.is_empty():
		return {"text": "¡Este negocio está al máximo!", "value": 1.0}
	goals.sort_custom(func(a, b): return float(a["value"]) > float(b["value"]))
	# Lo que ya se puede hacer (valor 1) va primero; si no, lo más avanzado.
	return goals[0]
