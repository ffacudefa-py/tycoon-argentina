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
	# 10.0: conquistas. La primera provincia en 8-20 min; tres antes de 1 h.
	var z: Array = data().zones
	var c0: float = tl.get("conquer_" + z[0]["id"], INF)
	check(c0 < 1200.0, "primera conquista antes de 20 min (fue %s)" % Fmt.duration(c0))
	check(c0 > 480.0, "la primera conquista no llega antes de 8 min (fue %s)" % Fmt.duration(c0))
	check(tl.get("conquer_" + z[2]["id"], INF) < 3600.0, "tres provincias antes de 1 h")
	check(tl.get("conquer_" + z[1]["id"], INF) - c0 > 600.0, "la segunda conquista tarda más de 10 min")
	check(not tl.has("stage_2") or tl["stage_2"] > 5400.0, "el NOA completo no llega antes de 1 h 30 min")
	check(m.economy.money >= 0, "nunca negativo")
	# Ningún negocio nuevo debe ser peor que el anterior en ganancia por nivel.
	var prev := 0.0
	for def in data().businesses:
		var per_level: float = float(def["profit_per_unit"]) / float(def["cycle"])
		check(per_level > prev, "%s rinde más por nivel que el anterior" % def["id"])
		prev = per_level


## 11.0: todas las provincias se pueden conquistar y la economía no se dispara.
## Con el negocio a nivel 100 y todas las mejoras (sin empleados ni bonos) tiene
## que alcanzar para ganar el mercado con el rival en su poder inicial, y el
## costo de los niveles tiene que pagarse en un tiempo razonable.
func test_toda_la_argentina_es_conquistable() -> void:
	var m := make_model(1, false)
	for z in data().zones:
		var bid: String = z["business"]
		m.biz[bid]["owned"] = true
		m.biz[bid]["level"] = 100
		for u in data().upgrades:
			m.biz[bid]["upgrades"][u["id"]] = int(u["max_level"])
		m.invalidate()
		var top := float(m.derive(bid)["profit_sec"])
		var need := ConquestSystem.market_needed(m, z["id"])
		check(need < top * 0.8, "%s se puede conquistar (hace falta %d %% del máximo)" % [z["name"], int(need / top * 100.0)])
		m.biz[bid]["level"] = 1
		var cost := float(m.level_cost(bid, 99))
		check(cost < 1e18, "%s: los niveles no tocan el tope de los enteros" % z["name"])
		check(cost / top < 30.0 * 3600.0, "%s: los 100 niveles se pagan en menos de 30 h al máximo (%d h)" % [z["name"], int(cost / top / 3600.0)])
