extends TestCase
## Simulación automatizada de ritmo de progresión (bot razonable).
## Imprime la línea de tiempo y verifica ventanas de tiempo deseadas.
## Para una corrida larga: tools/run_tests.sh --only=balance -- (ver BALANCE_HOURS)


func test_early_game_pacing() -> void:
	var m := make_model(42, false)
	var bot := BalanceBot.new(m, clock_holder)
	var hours := float(OS.get_environment("BALANCE_HOURS")) if OS.get_environment("BALANCE_HOURS") != "" else 1.5
	bot.play(hours * 3600.0)
	var tl := bot.timeline
	var keys := tl.keys()
	keys.sort_custom(func(a, b): return tl[a] < tl[b])
	print("    --- línea de tiempo del bot (%.1f h) ---" % hours)
	for k in keys:
		print("    %-22s %s" % [k, Fmt.duration(tl[k])])
	print("    dinero final %s · ingreso %s · etapa %d · negocios %d · empleados %d" % [
		Fmt.money(m.economy.money), Fmt.per_sec(m.income_per_sec()), m.stage, m.owned_ids().size(), m.employees.size()])
	for id in m.owned_ids():
		var d := m.derive(id)
		print("      %-13s nv %3d  %s  auto %d  stock %d%%" % [id, m.biz[id]["level"], Fmt.per_sec(d["profit_sec"]), d["automation"], int(m.stock_ratio(id) * 100)])
	check(tl.has("first_upgrade") or m.total_upgrades() > 0, "compró mejoras")
	check(tl.get("first_hire", INF) < 240.0, "primer empleado antes de 4 min (fue %s)" % Fmt.duration(tl.get("first_hire", -1)))
	check(tl.get("own_kiosco", INF) < 420.0, "kiosco antes de 7 min (fue %s)" % Fmt.duration(tl.get("own_kiosco", -1)))
	check(tl.get("stage_2", INF) < 300.0, "etapa 2 antes de 5 min")
	check(tl.get("own_comida", INF) < 1500.0, "tercer negocio antes de 25 min")
	check(tl.get("stage_3", INF) < 3600.0, "etapa 3 antes de 1 h")
	# Cotas inferiores: si algo explota (cascadas de recompensas, bugs de dinero) se nota acá.
	check(tl.get("own_kiosco", 0.0) > 45.0, "el kiosco no llega en menos de 45 s (fue %s)" % Fmt.duration(tl.get("own_kiosco", 0.0)))
	check(tl.get("own_lavadero", INF) > 150.0, "el lavadero no llega antes de 2,5 min")
	check(tl.get("stage_4", INF) > 300.0, "la etapa 4 no llega antes de 5 min")
	check(tl.get("stage_5", INF) > 1800.0, "el prestigio no se habilita antes de 30 min")
	check(m.economy.money >= 0, "nunca negativo")
	# Ningún negocio nuevo debe ser peor que el anterior en ganancia por nivel.
	var prev := 0.0
	for def in data().businesses:
		var per_level: float = float(def["profit_per_unit"]) / float(def["cycle"])
		check(per_level > prev, "%s rinde más por nivel que el anterior" % def["id"])
		prev = per_level
