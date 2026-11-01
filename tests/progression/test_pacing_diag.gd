extends TestCase
## Diagnóstico de ritmo de conquista (sólo a pedido: PACING_DIAG=1, PACING_HOURS=h).
## Por provincia mide cuándo se abre, cuándo la ganancia ya alcanza para el 100 %
## (desde ahí sólo espera el reloj), cuándo el negocio queda al máximo (nivel 100
## + todas las mejoras) y cuándo se conquista.


func _maxed(m: GameModel, bid: String) -> bool:
	if int(m.biz[bid]["level"]) < int(data().business_by_id[bid]["max_level"]):
		return false
	for u in data().upgrades:
		if int(m.biz[bid]["upgrades"].get(u["id"], 0)) < int(u["max_level"]):
			return false
	return true


func test_diagnostico_ritmo() -> void:
	if OS.get_environment("PACING_DIAG") == "":
		print("    (salteada: PACING_DIAG=1 para correrla)")
		return
	var hours := float(OS.get_environment("PACING_HOURS")) if OS.get_environment("PACING_HOURS") != "" else 12.0
	var m := make_model(42, false)
	var bot := BalanceBot.new(m, clock_holder)
	bot.decide_every = 1.0
	var info := {}   ## zid -> {open, ready, maxed, conq, idle}
	var step := 10.0
	while bot.t < hours * 3600.0:
		var money_before := float(m.economy.money)
		bot.play(step, 0.2)
		for z in data().zones:
			var zid: String = z["id"]
			var bid: String = z["business"]
			if not m.biz[bid]["owned"]:
				continue
			var e: Dictionary = info.get(zid, {"open": bot.t, "idle": 0.0})
			info[zid] = e
			if ConquestSystem.is_conquered(m, zid):
				if not e.has("conq"):
					e["conq"] = bot.t
				continue
			if not e.has("ready") and ConquestSystem.pace(m, zid) >= ConquestSystem.max_pace(m):
				e["ready"] = bot.t
				var d := m.derive(bid)
				var ups := 0
				for u in data().upgrades:
					ups += int(m.biz[bid]["upgrades"].get(u["id"], 0))
				print("    listo %s: nv %d mejoras %d/30 ganancia %s necesita %s · conquista x%.2f turbo x%.1f vel %.2f rev %.2f equipo %d ciclo %.2f" % [zid, m.biz[bid]["level"], ups, Fmt.per_sec(d["profit_sec"]), Fmt.per_sec(ConquestSystem.market_needed(m, zid)), ConquestSystem.income_mult(m, bid), m.boost_multiplier(), d["mods"]["speed"], d["mods"]["revenue"], d["team_size"], d["cycle"]])
			if not e.has("maxed") and _maxed(m, bid):
				e["maxed"] = bot.t
			# "sin nada que hacer": el negocio en disputa al máximo
			if _maxed(m, bid):
				e["idle"] = float(e["idle"]) + step
		if int(bot.t) % 300 < int(step) and OS.get_environment("PACING_TRACE") != "":
			for z in data().zones:
				var bid2: String = z["business"]
				if m.biz[bid2]["owned"] and not ConquestSystem.is_conquered(m, z["id"]):
					var ups2 := 0
					for u in data().upgrades:
						ups2 += int(m.biz[bid2]["upgrades"].get(u["id"], 0))
					var d2 := m.derive(bid2)
					print("    %s %s cuota %d%% ritmo %.2f nv %d mej %d neto %s mercado %s plata %s rival %d" % [Fmt.duration(bot.t), z["id"], int(ConquestSystem.share(m, z["id"]) * 100), ConquestSystem.pace(m, z["id"]), m.biz[bid2]["level"], ups2, Fmt.per_sec(float(d2["profit_sec"]) - float(d2["salary_sec"])), Fmt.per_sec(ConquestSystem.market_needed(m, z["id"])), Fmt.money(m.economy.money), m.rivals[z["rival"]]["power"]])
		if info.size() > 0 and m.owned_ids().size() == data().zones.size() and ConquestSystem.conquered_count(m) == data().zones.size():
			break
	print("    %-20s %9s %9s %9s %9s %9s %9s" % ["provincia", "abre", "listo", "máximo", "conquista", "espera", "al máx"])
	for z in data().zones:
		var e: Dictionary = info.get(z["id"], {})
		if e.is_empty():
			continue
		var o: float = e["open"]
		var c: float = e.get("conq", -1.0)
		var r: float = e.get("ready", -1.0)
		print("    %-20s %9s %9s %9s %9s %9s %9s" % [z["name"], Fmt.duration(o),
			"—" if r < 0 else "+" + Fmt.duration(r - o),
			"—" if not e.has("maxed") else "+" + Fmt.duration(float(e["maxed"]) - o),
			"—" if c < 0 else "+" + Fmt.duration(c - o),
			"—" if r < 0 or c < 0 else Fmt.duration(c - r),
			Fmt.duration(e["idle"])])
	print("    plata final %s · ingreso %s" % [Fmt.money(m.economy.money), Fmt.per_sec(m.income_per_sec())])


func test_mercado_vs_maximo() -> void:
	if OS.get_environment("PACING_DIAG") == "":
		return
	var m := make_model(1, false)
	print("    %-20s %12s %12s %12s %7s %7s %6s" % ["provincia", "nv25 s/mej", "máximo", "mercado", "%nv25", "%máx", "min"])
	for z in data().zones:
		var bid: String = z["business"]
		m.biz[bid]["owned"] = true
		m.biz[bid]["level"] = 25
		m.invalidate()
		var l25 := float(m.derive(bid)["profit_sec"])
		m.biz[bid]["level"] = 100
		for u in data().upgrades:
			m.biz[bid]["upgrades"][u["id"]] = int(u["max_level"])
		m.invalidate()
		var top := float(m.derive(bid)["profit_sec"])
		var need := ConquestSystem.market_needed(m, z["id"])
		print("    %-20s %12s %12s %12s %6d%% %6d%% %6.0f" % [z["name"], Fmt.per_sec(l25), Fmt.per_sec(top), Fmt.per_sec(need), int(need / l25 * 100), int(need / top * 100), float(z["conquest_minutes"])])
