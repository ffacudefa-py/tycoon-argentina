extends TestCase
## Partida completa con el bot de balance (las 24 provincias). Es larga, así
## que sólo corre a pedido:
##   FULL_GAME=1 tools/run_tests.sh --only=full_game
## FULL_GAME_HOURS = tope de horas de juego simuladas (300 por defecto).
## Mide cuándo se completa cada región y vigila que la plata nunca alcance
## para comprar un negocio entero (apertura + 100 niveles + todas las mejoras)
## que todavía no se tiene.


## Costo de un negocio entero desde cero, con los precios de hoy.
func _full_cost(m: GameModel, id: String) -> float:
	var def: Dictionary = data().business_by_id[id]
	var mult := m.level_cost_multiplier()
	var g := float(def["level_cost_growth"])
	var total := float(def["unlock"]["cost"])
	total += float(def["level_cost_base"]) * mult * (pow(g, int(def["max_level"]) - 1) - 1.0) / (g - 1.0)
	for u in data().upgrades:
		for lvl in int(u["max_level"]):
			total += float(def["level_cost_base"]) * float(u["cost_factor"]) * pow(float(u["cost_growth"]), lvl) * mult
	return total


func test_juego_completo() -> void:
	if OS.get_environment("FULL_GAME") == "":
		print("    (salteada: FULL_GAME=1 para correrla)")
		return
	var cap_h := float(OS.get_environment("FULL_GAME_HOURS")) if OS.get_environment("FULL_GAME_HOURS") != "" else 300.0
	var m := make_model(42, false)
	var bot := BalanceBot.new(m, clock_holder)
	bot.decide_every = 2.0
	var region_done := {}
	var worst := {}          ## negocio -> {ratio, t, money}
	var next_report := 3600.0
	while bot.t < cap_h * 3600.0:
		bot.play(60.0, 0.25)
		var money := float(m.economy.money)
		for def in data().businesses:
			var id: String = def["id"]
			if m.biz[id]["owned"]:
				continue
			var r := money / _full_cost(m, id)
			if r > float(worst.get(id, {}).get("ratio", -1.0)):
				worst[id] = {"ratio": r, "t": bot.t, "money": money}
		for reg in data().regions:
			if not region_done.has(reg["id"]) and ConquestSystem.region_complete(m, reg["id"]):
				region_done[reg["id"]] = bot.t
				print("    ✓ %s completa a las %s" % [reg["name"], Fmt.duration(bot.t)])
		if bot.t >= next_report:
			next_report += 3600.0 * 5
			var conq := 0
			for z in data().zones:
				if ConquestSystem.is_conquered(m, z["id"]):
					conq += 1
			print("    · %s: %d/24 provincias · plata %s · ingreso %s" % [Fmt.duration(bot.t), conq, Fmt.money(m.economy.money), Fmt.per_sec(m.income_per_sec())])
		if region_done.size() == data().regions.size():
			break

	print("    --- regiones (juego activo continuo) ---")
	var prev := 0.0
	for reg in data().regions:
		if region_done.has(reg["id"]):
			var t: float = region_done[reg["id"]]
			print("    %-10s %10s   (+%s)" % [reg["name"], Fmt.duration(t), Fmt.duration(t - prev)])
			prev = t
		else:
			print("    %-10s sin completar en %d h" % [reg["name"], int(cap_h)])
	print("    --- provincias ---")
	for z in data().zones:
		print("    %-22s %s" % [z["name"], Fmt.duration(bot.timeline["conquer_" + z["id"]]) if bot.timeline.has("conquer_" + z["id"]) else "—"])
	print("    --- plata vs. negocio entero que todavía no tenías (máximo) ---")
	for def in data().businesses:
		var w: Dictionary = worst.get(def["id"], {})
		if not w.is_empty():
			print("    %-22s %6.1f %%  (a las %s)" % [def["name"], float(w["ratio"]) * 100.0, Fmt.duration(w["t"])])
	for def in data().businesses:
		var w: Dictionary = worst.get(def["id"], {})
		check(w.is_empty() or float(w["ratio"]) < 1.0,
			"nunca alcanza para comprar %s entero (%.0f %%)" % [def["name"], float(w.get("ratio", 0.0)) * 100.0])
	check(region_done.size() == data().regions.size(), "se completa toda la Argentina en menos de %d h" % int(cap_h))
