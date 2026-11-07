extends TestCase


func test_missions_progress_automatically_and_claim_once() -> void:
	var m := make_model()
	for i in 10:
		m.tap_sell(B0)
		run(m, 1.1)
	ProgressionSystem.update(m)
	check(m.missions["completed"].has("m_ventas"), "10 ventas completan la misión sin reclamar")
	check(int(m.missions["main_index"]) >= 1, "la cadena avanza sola")
	var money0 := m.economy.money
	check(ProgressionSystem.claim_mission(m, "m_ventas")["ok"], "reclama")
	eq(m.economy.money, money0 + 24, "recompensa exacta ($30 al 80 %)")
	check(not ProgressionSystem.claim_mission(m, "m_ventas")["ok"], "no se reclama dos veces")
	eq(m.economy.money, money0 + 24, "sin doble pago")
	check(not ProgressionSystem.claim_mission(m, "m_doce")["ok"], "no se reclama sin completar")


func test_achievement_reward_once() -> void:
	var m := make_model()
	m.tap_sell(B0)
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
	m.economy.earn(5_000_000, "test")
	m.update_progress()
	eq(m.stage, 1, "la plata sola no sube de etapa")
	conquer_first(m, 5)
	eq(m.stage, 1, "falta una provincia del NOA")
	conquer_first(m, 6)
	eq(m.stage, 2, "NOA completo: etapa 2")
	eq(int(m.metric("regions_conquered")), 1)
	eq(int(m.metric("conquered")), 6)


func test_zone_unlock() -> void:
	var m := make_model()
	m.economy.earn(1_000_000, "test")
	check(not m.unlock_zone(Z1)["ok"], "la segunda provincia requiere conquistar la primera")
	conquer(m, B0)
	check(m.unlock_zone(Z1)["ok"], "conquistada la primera, se abre la segunda")
	check(not m.unlock_zone(Z1)["ok"], "no dos veces")
	check(m.zones.has(Z1) and m.biz[B1]["owned"], "provincia y negocio registrados")


func test_conquest_share_grows_and_conquers() -> void:
	var m := make_model()
	var zid := Z0
	eq(ConquestSystem.share(m, zid), 0.0, "arranca en 0 %")
	var p_low := ConquestSystem.pace(m, zid)
	check(p_low > 0.0 and p_low < 1.0, "recién abierto avanza lento (ritmo %.2f)" % p_low)
	m.biz[B0]["level"] = 100
	for u in m.data.upgrades:
		m.biz[B0]["upgrades"][u["id"]] = int(u["max_level"])
	m.invalidate()
	var p_max := ConquestSystem.pace(m, zid)
	check(p_max > p_low, "invertir acelera la conquista")
	check(p_max > 1.5, "con el negocio al máximo va rápido (ritmo %.2f)" % p_max)
	m.biz[B0]["stock"] = {}
	for p in m.data.business_by_id[B0]["products"]:
		m.biz[B0]["stock"][p["id"]] = 1e9
	# Tarda conquest_minutes / ritmo (ni antes ni mucho después).
	var need_s := float(m.data.zone_by_id[zid]["conquest_minutes"]) * 60.0 / p_max
	var t := 0.0
	while not ConquestSystem.is_conquered(m, zid) and t < need_s * 2.0:
		ConquestSystem.advance(m, 5.0)
		t += 5.0
	check(ConquestSystem.is_conquered(m, zid), "conquistada (cuota %s)" % str(ConquestSystem.share(m, zid)))
	check(absf(t - need_s) <= 10.0, "tarda lo previsto para su ritmo (%d s, esperado %d s)" % [int(t), int(need_s)])
	eq(int(m.rivals[m.data.zone_by_id[zid]["rival"]]["power"]), 1, "el rival cae")
	check(m.derive(B0)["price_mult"] > 0.0 and ConquestSystem.income_mult(m, B0) > 1.0, "bonus de provincia")


func test_cuota_no_baja_y_eta() -> void:
	var m := make_model()
	m.zones[Z0]["share"] = 0.5
	m.biz[B0]["level"] = 30
	m.invalidate()
	var e1 := ConquestSystem.eta(m, Z0)
	check(e1 > 0.0 and e1 < INF, "hay tiempo estimado")
	m.biz[B0]["level"] = 80
	m.invalidate()
	check(ConquestSystem.eta(m, Z0) < e1, "con más nivel se conquista antes")
	m.rivals[m.data.zone_by_id[Z0]["rival"]]["power"] = 10
	m.invalidate()
	ConquestSystem.advance(m, 1.0)
	check(ConquestSystem.share(m, Z0) >= 0.5, "la cuota no baja aunque el rival crezca")


func test_competition_and_campaign() -> void:
	var m := make_model()
	var rid: String = m.data.zone_by_id[Z0]["rival"]
	var comp0 := RivalSystem.competition_for(m, B0)
	check(comp0 > 0.0, "hay competencia local")
	m.economy.earn(10_000, "test")
	m.rivals[rid]["power"] = 6
	m.invalidate()
	var comp1 := RivalSystem.competition_for(m, B0)
	check(comp1 > comp0, "rival más fuerte, más competencia")
	var share0 := ConquestSystem.share(m, Z0)
	check(RivalSystem.campaign(m, rid)["ok"], "campaña")
	eq(int(m.rivals[rid]["power"]), 4, "baja el poder")
	check(ConquestSystem.share(m, Z0) > share0, "la campaña suma cuota")
	check(not RivalSystem.campaign(m, rid)["ok"], "cooldown")


func test_events_spawn_and_clamp() -> void:
	var m := make_model(3)
	m.economy.reset_run(10_000)
	conquer(m, B0)
	m.buy_business(B1)
	# Un negocio con bebidas (la bodega de torrontés) vende más bebidas.
	var wine := ""
	var other := ""
	for b in m.data.businesses:
		for p in b["products"]:
			if (p["tags"] as Array).has("bebida") and wine == "":
				wine = b["id"]
	m._own_business(wine, 1.0)
	var inst := EventSystem.try_spawn(m, "ola_calor")
	check(not inst.is_empty(), "spawnea ola de calor")
	var mods := EventSystem.modifiers_for(m, wine)
	var hit := false
	for p in m.data.business_by_id[wine]["products"]:
		if (p["tags"] as Array).has("bebida"):
			hit = hit or is_equal_approx(float(mods["demand"].get(p["id"], 1.0)), 1.8)
		else:
			other = p["id"]
	check(hit, "más demanda de bebidas")
	check(not mods["demand"].has(other), "el resto igual")
	run(m, 200.0)
	eq(m.events["active"].size() > 0 and m.events["active"][0]["id"] == "ola_calor", false, "terminó la ola de calor")


func test_supply_failure_resolution() -> void:
	var m := make_model(5)
	m.economy.reset_run(100_000)
	conquer(m, B0)
	m.buy_business(B1)
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
	var c0: float = m.derive(B0)["products"][0]["cost"]
	run(m, 700.0)
	near(m.derive(B0)["products"][0]["cost"], c0, 0.0001, "modo normal: sin inflación")
	HardMode.choose(m, true)
	m.inflation["next_in"] = 10.0
	run(m, 30.0)
	check(m.derive(B0)["products"][0]["cost"] > c0, "activa: sube el costo")
	run(m, 150.0)
	check(float(m.inflation["price_index"]) > 1.0, "los precios acompañan")


func test_prestige_flow() -> void:
	var m := make_model()
	check(not PrestigeSystem.unlocked(m), "bloqueado al inicio")
	eq(PrestigeSystem.pending_points(m), 0)
	m.economy.earn(20_000_000_000, "test")
	conquer_first(m, 14)
	check(PrestigeSystem.unlocked(m), "conquistar Cuyo (etapa 4) lo habilita")
	var pts := PrestigeSystem.pending_points(m)
	check(pts > 0, "puntos pendientes")
	m.achievements["primera_venta"] = 1.0
	m.profile["company"] = "La Gran Empresa"
	var lifetime := m.economy.lifetime_earned
	check(PrestigeSystem.perform(m)["ok"], "prestigio")
	eq(int(m.prestige["points"]), pts, "acredita puntos")
	eq(int(m.biz[B0]["level"]), 1, "reinicia negocios")
	check(not m.biz[B1]["owned"], "sin el segundo negocio")
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
	conquer_first(m, 14)
	PrestigeSystem.perform(m)
	check(m.biz[B1]["owned"], "franquicia: arranca con el segundo negocio")
	eq(m.economy.money, 2000, "capital semilla")


func test_onboarding_start_closed_and_affordable_first_stock() -> void:
	var m := make_model(1, false)
	check(m.biz[B0]["closed"], "arranca cerrado")
	check(not m.has_stock(B0), "arranca sin mercadería")
	check(not m.tap_sell(B0)["ok"], "cerrado no vende")
	check(m.open_business(B0)["ok"], "abre")
	var q := m.restock_quote(B0)
	check(q["total"] <= m.economy.money, "la primera mercadería completa se puede pagar (%d de %d)" % [q["total"], m.economy.money])
	check(m.restock(B0)["ok"], "compra mercadería")
	run(m, 3.5)
	check(m.tap_sell(B0)["ok"], "con mercadería vende")


func test_guided_tutorial_rewards_once() -> void:
	var m := make_model(1, false)
	m.open_business(B0)
	TutorialSteps.update(m)
	eq(int(m.tutorial["step"]), 1, "paso 1 cumplido")
	m.restock(B0)
	var money := m.economy.money
	TutorialSteps.update(m)
	eq(int(m.tutorial["step"]), 2, "paso 2 cumplido")
	eq(m.economy.money, money + 8, "premio del paso 2 ($10 al 80 %)")
	check(not m.grant_tutorial_reward(1, {"money": 10}), "no se paga dos veces")
	eq(m.economy.money, money + 8, "sin doble pago")


func test_reclamar_todo() -> void:
	var m := make_model()
	var had := ProgressionSystem.unclaimed_count(m) > 0
	eq(ProgressionSystem.claim_all(m)["ok"], had, "sólo reclama si había algo pendiente")
	m.economy.earn(5_000_000, "dev")
	for i in 30:
		m.tap_sell(B0)
		run(m, 1.1)
	ProgressionSystem.update(m)
	var pending := ProgressionSystem.unclaimed_count(m)
	check(pending >= 1, "hay premios pendientes (%d)" % pending)
	var before := m.economy.money
	var r := ProgressionSystem.claim_all(m)
	check(r["ok"], "reclama todo")
	eq(r["count"], pending, "reclama exactamente lo pendiente")
	check(m.economy.money >= before, "suma plata")
	eq(ProgressionSystem.unclaimed_count(m), 0, "no queda nada")
	check(not ProgressionSystem.claim_all(m)["ok"], "no se cobra dos veces")


## 10.0: modo bien argentino (+25 %, juicios, robos y coimas).
func test_hard_mode_bonus_lawsuit_theft_bribe() -> void:
	var m := make_model()
	check(not m.hard["chosen"], "se pregunta al empezar")
	var p0: float = m.derive(B0)["revenue_sec"]
	HardMode.choose(m, true)
	near(m.derive(B0)["revenue_sec"], p0 * 1.25, p0 * 0.001, "+25 % de ingresos")
	# Juicio: sueldos impagos más de lawsuit_after segundos.
	m.economy.reset_run(1_000_000)
	EmployeeSystem.ensure_candidates(m, B0)
	EmployeeSystem.hire(m, B0, 0)
	eq(m.employees.size(), 1, "contratado")
	# Sueldos atrasados más de lawsuit_after segundos (sin plata para pagar).
	m.economy.reset_run(0)
	m.salary_debt = 50
	near(HardMode.lawsuit_eta(m), 120.0, 0.01, "la cuenta regresiva arranca en 2 min")
	for i in 60:
		HardMode.advance(m, 1.0, false)
	near(HardMode.lawsuit_eta(m), 60.0, 0.01, "y baja con el tiempo")
	for i in 80:
		HardMode.advance(m, 1.0, false)
	eq(m.employees.size(), 0, "el empleado hizo juicio y se fue")
	eq(int(m.counter("lawsuits")), 1, "un juicio")
	check(m.salary_debt > 0, "la indemnización queda como deuda")
	# Robo: se lleva parte de la mercadería.
	var pid: String = m.data.business_by_id[B0]["products"][0]["id"]
	m.biz[B0]["stock"][pid] = 100.0
	check(Security.start_theft(m, B0)["ok"], "robo (sin interfaz se resuelve al toque)")
	check(float(m.biz[B0]["stock"][pid]) <= 80.0, "en este modo se llevan al menos 20 %")
	# Coima: protege la provincia.
	m.salary_debt = 0
	m.economy.reset_run(1_000_000)
	check(Security.start_bribe(m, Z0)["ok"], "paga la coima")
	Security.resolve_bribe(m, true)
	m.biz[B0]["stock"][pid] = 100.0
	check(not Security.start_theft(m, B0)["ok"], "con seguridad no roban")
	eq(float(m.biz[B0]["stock"][pid]), 100.0, "stock intacto")
	# Se guarda con la partida.
	var m2 := make_model(2)
	m2.from_dict(m.to_dict())
	check(HardMode.on(m2) and m2.hard["chosen"], "el modo se guarda")
	check(Security.protected_left(m2, Z0) > 0.0, "la seguridad paga se guarda")


## 15.0: el modo normal tiene todo (robos, inflación, juicios), sólo más suave.
func test_normal_mode_tiene_todo_mas_suave() -> void:
	var m := make_model()
	HardMode.choose(m, false)
	var pid: String = m.data.business_by_id[B0]["products"][0]["id"]
	m.biz[B0]["stock"][pid] = 100.0
	run(m, 400.0)
	eq(int(m.counter("thefts")), 0, "el primer robo no llega antes de 8 min")
	check(not m.inflation_active(), "sin inflación durante el tutorial")
	m.tutorial["done"] = true
	check(m.inflation_active(), "inflación después del tutorial")
	var normal_inf := HardMode.inflation_cfg(m)
	var hard_m := make_model(3)
	HardMode.choose(hard_m, true)
	check(hard_m.inflation_active(), "en el bien argentino, desde el principio")
	var hard_inf := HardMode.inflation_cfg(hard_m)
	check(float(hard_inf["period"]) < float(normal_inf["period"]), "en el bien argentino remarcan más seguido")
	check(float(hard_inf["max_index"]) > float(normal_inf["max_index"]), "en el bien argentino la inflación llega más alto")
	m.economy.reset_run(1_000_000)
	EmployeeSystem.ensure_candidates(m, B0)
	EmployeeSystem.hire(m, B0, 0)
	m.economy.reset_run(0)
	m.salary_debt = 50
	var eta := HardMode.lawsuit_eta(m)
	check(eta > 120.0, "también hay juicios, con más margen (%s)" % Fmt.duration(eta))
	check(Security.difficulty(m) < Security.difficulty(hard_m), "minijuegos más fáciles que en el bien argentino")


## 10.3: ciclo de enganche (combo, cofres, próxima meta, desafíos de evento).
func test_engagement_combo_chests_goals() -> void:
	var m := make_model()
	eq(Engagement.combo(m), 1.0, "sin combo al empezar")
	var before := m.economy.money
	var extra := Engagement.on_manual_sale(m, 100)
	eq(extra, 0, "la primera venta no tiene extra")
	near(Engagement.combo(m), 1.1, 0.001, "sube el combo")
	for i in 20:
		Engagement.on_manual_sale(m, 100)
	near(Engagement.combo(m), 2.0, 0.001, "tope x2")
	check(m.economy.money > before, "el combo paga extra")
	for i in 10:
		Engagement.advance(m, 1.0)
	check(Engagement.combo(m) < 2.0, "si parás, baja")
	# Cofres: por conquista y al abrirlos dan algo.
	conquer(m, B0)
	eq(int(m.engage["chests"]), 1, "cofre por conquistar")
	var r := Engagement.open_chest(m)
	check(r["ok"] and str(r["text"]) != "", "el cofre da un premio")
	eq(int(m.engage["chests"]), 0, "se consumió")
	check(not Engagement.open_chest(m)["ok"], "sin cofres no se abre")
	# Hito de nivel 25.
	m.biz[B0]["level"] = 25
	Engagement.check_level_marks(m)
	eq(int(m.engage["chests"]), 1, "cofre por nivel 25")
	Engagement.check_level_marks(m)
	eq(int(m.engage["chests"]), 1, "una sola vez")
	# Próxima meta siempre tiene texto.
	check(str(Engagement.next_goal(m, B0)["text"]) != "", "hay próxima meta")
	# Se guarda.
	var m2 := make_model(2)
	m2.from_dict(m.to_dict())
	eq(int(m2.engage["chests"]), 1, "cofres guardados")


func test_rival_no_crece_sin_techo() -> void:
	var m := make_model(5)
	var rid: String = m.data.zone_by_id[Z0]["rival"]
	var top: int = int(m.data.rival_by_id[rid]["start_power"]) + int(m.data.world["rival_max_growth"])
	for i in 400:
		RivalSystem.advance(m, float(m.data.world["rival_update_seconds"]))
	check(int(m.rivals[rid]["power"]) <= top, "el rival no pasa de %d (está en %d)" % [top, int(m.rivals[rid]["power"])])


## 15.0: cada logro tiene rango, categoría, insignia y una métrica que existe.
func test_logros_con_insignia() -> void:
	var tiers := ["bronce", "plata", "oro", "diamante"]
	var cats := ["ventas", "dinero", "negocios", "equipo", "conquista", "aventura"]
	check(data().achievements.size() >= 60, "hay al menos 60 logros (%d)" % data().achievements.size())
	for a in data().achievements:
		check(tiers.has(a.get("tier", "")), "%s tiene rango" % a["id"])
		check(cats.has(a.get("category", "")), "%s tiene categoría" % a["id"])
		check(ResourceLoader.exists("res://assets/iconos/badges/%s.png" % a["id"]), "%s tiene insignia" % a["id"])
	for c in cats:
		check(ResourceLoader.exists("res://assets/iconos/badges/locked_%s.png" % c), "insignia bloqueada de %s" % c)
	# Las métricas responden (no se escribió mal ninguna).
	var m := make_model()
	m.economy.earn(1_000_000_000_000, "dev")
	ProgressionSystem.update(m)
	check(m.achievements.has("billonario"), "se desbloquea un logro nuevo (billonario)")
