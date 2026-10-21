extends TestCase


func test_missions_progress_automatically_and_claim_once() -> void:
	var m := make_model()
	for i in 10:
		m.tap_sell("puesto")
		run(m, 1.1)
	ProgressionSystem.update(m)
	check(m.missions["completed"].has("m_ventas"), "10 ventas completan la misión sin reclamar")
	check(int(m.missions["main_index"]) >= 1, "la cadena avanza sola")
	var money0 := m.economy.money
	check(ProgressionSystem.claim_mission(m, "m_ventas")["ok"], "reclama")
	eq(m.economy.money, money0 + 30, "recompensa exacta")
	check(not ProgressionSystem.claim_mission(m, "m_ventas")["ok"], "no se reclama dos veces")
	eq(m.economy.money, money0 + 30, "sin doble pago")
	check(not ProgressionSystem.claim_mission(m, "m_doce")["ok"], "no se reclama sin completar")


func test_achievement_reward_once() -> void:
	var m := make_model()
	m.tap_sell("puesto")
	run(m, 1.2)
	ProgressionSystem.update(m)
	check(m.achievements.has("primera_venta"), "logro primera venta")
	var money := m.economy.money
	ProgressionSystem.update(m)
	ProgressionSystem.update(m)
	eq(m.economy.money, money, "no vuelve a pagar")


func test_achievement_unlocks_avatar() -> void:
	var m := make_model()
	m.economy.earn(10_000, "test")
	ProgressionSystem.update(m)
	check(m.profile["avatars"].has("gorra"), "logro Emprendedor da la gorra")
	check(m.set_avatar("gorra")["ok"], "se puede usar")
	check(not m.set_avatar("corona")["ok"], "bloqueado no")


func test_daily_reward_once_per_day_and_clock_guard() -> void:
	var m := make_model()
	check(ProgressionSystem.claim_daily_reward(m)["ok"], "primer día")
	check(not ProgressionSystem.claim_daily_reward(m)["ok"], "no dos veces el mismo día")
	advance_clock(86400.0)
	m.update_progress()
	check(ProgressionSystem.claim_daily_reward(m)["ok"], "al otro día sí")
	eq(int(m.daily_reward["index"]), 2, "avanza el ciclo")
	# Saltear días no reinicia la racha.
	advance_clock(86400.0 * 5)
	m.update_progress()
	check(ProgressionSystem.claim_daily_reward(m)["ok"], "después de faltar sigue")
	eq(int(m.daily_reward["index"]), 3, "sin castigo por faltar")
	# Reloj hacia atrás: se niega.
	advance_clock(-86400.0 * 3)
	check(not ProgressionSystem.claim_daily_reward(m)["ok"], "reloj atrasado: no reclama")


func test_daily_missions_generated_and_tracked() -> void:
	var m := make_model()
	ProgressionSystem.ensure_daily(m)
	eq(m.daily_missions["list"].size(), 3, "tres diarias")
	var day := int(m.daily_missions["day"])
	ProgressionSystem.ensure_daily(m)
	eq(int(m.daily_missions["day"]), day, "estables en el día")
	for dm in m.daily_missions["list"]:
		eq(ProgressionSystem.daily_progress(m, dm), 0.0, "arrancan en cero")


func test_stage_progression() -> void:
	var m := make_model()
	eq(m.stage, 1)
	m.economy.earn(5000, "test")
	m.update_progress()
	eq(m.stage, 2, "etapa 2 con $5.000 ganados")


func test_zone_unlock() -> void:
	var m := make_model()
	m.economy.earn(100_000, "test")
	m.update_progress()
	check(not m.unlock_zone("universidad")["ok"], "universidad requiere etapa 3")
	check(m.unlock_zone("centro")["ok"], "centro disponible en etapa 2")
	check(not m.unlock_zone("centro")["ok"], "no dos veces")
	check(m.zones.has("centro"), "zona registrada")


func test_competition_and_campaign() -> void:
	var m := make_model()
	var comp0 := RivalSystem.competition_for(m, "puesto")
	check(comp0 > 0.0, "hay competencia en el barrio")
	m.economy.earn(10_000, "test")
	m.rivals["ramon"]["power"] = 6
	m.invalidate()
	var comp1 := RivalSystem.competition_for(m, "puesto")
	check(comp1 > comp0, "rival más fuerte, más competencia")
	check(RivalSystem.campaign(m, "ramon")["ok"], "campaña")
	eq(int(m.rivals["ramon"]["power"]), 3, "baja el poder")
	check(not RivalSystem.campaign(m, "ramon")["ok"], "cooldown")


func test_events_spawn_and_clamp() -> void:
	var m := make_model(3)
	m.biz["puesto"]["level"] = 10
	m.economy.reset_run(10_000)
	m.invalidate()
	m.buy_business("kiosco")
	var inst := EventSystem.try_spawn(m, "ola_calor")
	check(not inst.is_empty(), "spawnea ola de calor")
	var mods := EventSystem.modifiers_for(m, "puesto")
	near(float(mods["demand"].get("bebida", 1.0)), 1.8, 0.001, "más demanda de bebidas")
	check(not mods["demand"].has("alfajor"), "alfajores igual")
	run(m, 200.0)
	eq(m.events["active"].size() > 0 and m.events["active"][0]["id"] == "ola_calor", false, "terminó la ola de calor")


func test_supply_failure_resolution() -> void:
	var m := make_model(5)
	m.biz["puesto"]["level"] = 10
	m.economy.reset_run(100_000)
	m.invalidate()
	m.buy_business("kiosco")
	var inst := EventSystem.try_spawn(m, "falla_suministro")
	check(not inst.is_empty(), "falla")
	var bid: String = inst["business"]
	near(m.derive(bid)["event_speed"], 0.5, 0.001, "media máquina")
	var cost := EventSystem.resolve_cost(m, 0, "flete")
	var money0 := m.economy.money
	check(EventSystem.resolve(m, 0, "flete")["ok"], "se resuelve pagando")
	eq(m.economy.money, money0 - cost, "cobra el flete")
	near(m.derive(bid)["event_speed"], 1.0, 0.001, "normal")
	eq(m.counter("events_resolved"), 1.0)


func test_inflation_optional_and_bounded() -> void:
	var m := make_model()
	var c0: float = m.derive("puesto")["products"][0]["cost"]
	run(m, 700.0)
	near(m.derive("puesto")["products"][0]["cost"], c0, 0.0001, "desactivada: sin cambios")
	m.inflation_enabled = true
	m.invalidate()
	run(m, 610.0)
	check(m.derive("puesto")["products"][0]["cost"] > c0, "activa: sube el costo")
	run(m, 100.0)
	check(float(m.inflation["price_index"]) > 1.0, "los precios acompañan")


func test_prestige_flow() -> void:
	var m := make_model()
	check(not PrestigeSystem.unlocked(m), "bloqueado al inicio")
	eq(PrestigeSystem.pending_points(m), 0)
	m.economy.earn(20_000_000_000, "test")
	m.update_progress()
	check(PrestigeSystem.unlocked(m), "etapa 5 lo habilita")
	var pts := PrestigeSystem.pending_points(m)
	check(pts > 0, "puntos pendientes")
	m.achievements["primera_venta"] = 1.0
	m.profile["company"] = "La Gran Empresa"
	var lifetime := m.economy.lifetime_earned
	check(PrestigeSystem.perform(m)["ok"], "prestigio")
	eq(int(m.prestige["points"]), pts, "acredita puntos")
	eq(int(m.biz["puesto"]["level"]), 1, "reinicia negocios")
	check(not m.biz["kiosco"]["owned"], "sin kiosco")
	check(m.achievements.has("primera_venta"), "conserva logros")
	eq(m.profile["company"], "La Gran Empresa", "conserva nombre")
	eq(m.economy.lifetime_earned, lifetime, "conserva histórico")
	check(m.prestige_multiplier() > 1.0, "bonificación permanente")
	check(PrestigeSystem.buy_perk(m, "inversores")["ok"], "compra ventaja")
	eq(m.perk_level("inversores"), 1)


func test_prestige_franchise_and_seed_capital() -> void:
	var m := make_model()
	m.prestige["points"] = 100
	PrestigeSystem.buy_perk(m, "franquicia")
	PrestigeSystem.buy_perk(m, "capital_semilla")
	m.economy.earn(20_000_000_000, "test")
	m.update_progress()
	PrestigeSystem.perform(m)
	check(m.biz["kiosco"]["owned"], "franquicia: arranca con kiosco")
	eq(m.economy.money, 2000, "capital semilla")


func test_onboarding_start_closed_and_affordable_first_stock() -> void:
	var m := make_model(1, false)
	check(m.biz["puesto"]["closed"], "arranca cerrado")
	check(not m.has_stock("puesto"), "arranca sin mercadería")
	check(not m.tap_sell("puesto")["ok"], "cerrado no vende")
	check(m.open_business("puesto")["ok"], "abre")
	var q := m.restock_quote("puesto")
	check(q["total"] <= m.economy.money, "la primera mercadería completa se puede pagar (%d de %d)" % [q["total"], m.economy.money])
	check(m.restock("puesto")["ok"], "compra mercadería")
	run(m, 3.5)
	check(m.tap_sell("puesto")["ok"], "con mercadería vende")


func test_guided_tutorial_rewards_once() -> void:
	var m := make_model(1, false)
	m.open_business("puesto")
	TutorialSteps.update(m)
	eq(int(m.tutorial["step"]), 1, "paso 1 cumplido")
	m.restock("puesto")
	var money := m.economy.money
	TutorialSteps.update(m)
	eq(int(m.tutorial["step"]), 2, "paso 2 cumplido")
	eq(m.economy.money, money + 10, "premio del paso 2")
	check(not m.grant_tutorial_reward(1, {"money": 10}), "no se paga dos veces")
	eq(m.economy.money, money + 10, "sin doble pago")
