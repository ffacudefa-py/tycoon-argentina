extends TestCase
## 11.2: robos, coima y multa (Security) y la lógica de los minijuegos
## (TheftGame, BribeGame), con bots "humanos" que miden la dificultad.


func _stock(m: GameModel, bid: String, q := 100.0) -> String:
	var pid: String = m.data.business_by_id[bid]["products"][0]["id"]
	for p in m.data.business_by_id[bid]["products"]:
		m.biz[bid]["stock"][p["id"]] = q
	return pid


# ------------------------------------------------------------------ Security

func test_robos_en_los_dos_modos() -> void:
	Security.ui_attached = false
	Security.rng.seed = 77
	for hard in [false, true]:
		var m := make_model(7)
		HardMode.choose(m, hard)
		_stock(m, B0, 1e6)
		run(m, 1000.0)
		check(m.counter("thefts") >= 1.0, "hay robos en el modo %s" % ("bien argentino" if hard else "normal"))


func test_robo_pendiente_y_recuperacion() -> void:
	Security.ui_attached = true
	var m := make_model(3)
	HardMode.choose(m, false)
	var pid := _stock(m, B0, 100.0)
	check(Security.start_theft(m, B0)["ok"], "empieza el asalto")
	var frac := float(Security.pending_theft(m)["fraction"])
	check(frac >= 0.15 and frac <= 0.3, "fracción del modo normal")
	eq(float(m.biz[B0]["stock"][pid]), 100.0, "mientras se juega no se pierde nada")
	var theft_in := float(m.hard["theft_in"])
	Security.advance(m, 50.0, false)
	eq(float(m.hard["theft_in"]), theft_in, "el próximo robo espera a que termine este")
	Security.resolve_theft(m, 0.5)
	near(float(m.biz[B0]["stock"][pid]), 100.0 - floorf(100.0 * frac * 0.5), 0.001, "se pierde la mitad de lo robado")
	check(Security.pending_theft(m).is_empty(), "robo resuelto")
	# Defensa perfecta: nada perdido y un cofre.
	_stock(m, B0, 100.0)
	Security.start_theft(m, B0)
	var chests := int(m.engage.get("chests", 0))
	Security.resolve_theft(m, 1.0, true)
	eq(float(m.biz[B0]["stock"][pid]), 100.0, "sin pérdidas")
	eq(int(m.engage.get("chests", 0)), chests + 1, "cofre por defensa perfecta")
	eq(int(m.counter("thefts_defended")), 1, "cuenta la defensa")
	# El pendiente se guarda (si se cierra la app, se juega al volver).
	Security.start_theft(m, B0)
	var m2 := make_model(4)
	m2.from_dict(m.to_dict())
	eq(Security.pending_theft(m2).get("business", ""), B0, "el asalto pendiente se guarda")
	Security.ui_attached = false


func test_coima_exito_multa_y_limite_diario() -> void:
	Security.ui_attached = false
	var m := make_model(5)
	HardMode.choose(m, false)
	m.economy.reset_run(10_000_000)
	var cost := Security.bribe_cost(m)
	var money := m.economy.money
	check(Security.start_bribe(m, Z0)["ok"], "coima en el modo normal")
	eq(m.economy.money, money - cost, "se cobra al empezar")
	check(not Security.start_bribe(m, Z0)["ok"], "no dos a la vez")
	Security.resolve_bribe(m, true)
	near(Security.protected_left(m, Z0), 1800.0, 0.01, "30 min de protección")
	# Fracaso: multa del 20 % por 5 minutos.
	var p0 := float(m.derive(B0)["revenue_sec"])
	Security.start_bribe(m, Z0)
	Security.resolve_bribe(m, false)
	near(Security.fine_left(m), 300.0, 0.01, "multa de 5 min")
	near(float(m.derive(B0)["revenue_sec"]), p0 * 0.8, p0 * 0.001, "ingresos -20 %")
	advance_clock(301.0)
	Security.advance(m, 1.0, false)
	near(float(m.derive(B0)["revenue_sec"]), p0, p0 * 0.001, "al terminar vuelven")
	# Límite: 5 por día (ya se usaron 2).
	for i in 3:
		check(Security.start_bribe(m, Z0)["ok"], "coima %d" % (i + 3))
		Security.resolve_bribe(m, true)
	eq(Security.bribes_left_today(m), 0, "no quedan coimas hoy")
	check(not Security.start_bribe(m, Z0)["ok"], "la sexta no se puede")
	advance_clock(86400.0)
	eq(Security.bribes_left_today(m), 5, "al otro día se reinicia")


func test_coima_abandonada_es_multa() -> void:
	var m := make_model(6)
	m.economy.reset_run(10_000_000)
	Security.start_bribe(m, Z0)
	advance_clock(200.0)
	Security.advance(m, 1.0, false)
	check(Security.pending_bribe(m).is_empty(), "la coima a medias se cierra")
	check(Security.fine_left(m) > 0.0, "y cuenta como multa")


# ----------------------------------------------------------------- TheftGame

func _first_active(g: TheftGame) -> Dictionary:
	for th in g.thieves:
		if th["state"] in ["enter", "grab", "flee"]:
			return th
	return {}


func _run_until_active(g: TheftGame) -> Dictionary:
	for i in 400:
		g.step(1.0 / 60.0)
		var th := _first_active(g)
		if not th.is_empty():
			return th
	return {}


func test_asalto_disparo_caja_y_bolsa() -> void:
	var g := TheftGame.new(11, 0.0)
	eq(g.thief_count(), 4, "4 ladrones en la dificultad mínima")
	var th := _run_until_active(g)
	check(not th.is_empty(), "entra un ladrón")
	for i in 600:
		g.step(1.0 / 60.0)
		if int(th["carry"]) >= 0:
			break
	check(int(th["carry"]) >= 0, "el ladrón agarra una caja")
	var lid := int(th["carry"])
	eq(g.tap((th["pos"] as Vector2) - Vector2(0, TheftGame.BODY_OFFSET)), "hit", "disparo certero")
	eq(th["state"], "down", "el ladrón cae")
	eq(g.loot[lid]["state"], "floor", "la caja queda en el piso")
	eq(g.drag_start(g.loot[lid]["pos"]), lid, "se agarra la caja")
	check(g.drag_end(lid, g.bag.get_center() + Vector2(0, -60)), "la bolsa atrae la caja aunque no se acierte justo")
	eq(g.loot[lid]["state"], "bagged", "en la bolsa")
	eq(g.ammo, TheftGame.AMMO - 1, "gastó una bala")


func test_asalto_municion_casco_y_clientes() -> void:
	var g := TheftGame.new(2, 1.0)
	eq(g.thief_count(), 8, "8 ladrones en la máxima")
	for i in TheftGame.AMMO:
		g.tap(Vector2(-500, -500))
	eq(g.tap(Vector2(10, 10)), "empty", "sin balas")
	check(g.reload(), "recarga")
	eq(g.tap(Vector2(10, 10)), "reloading", "mientras recarga no dispara")
	g.step(TheftGame.RELOAD_TIME + 0.01)
	eq(g.ammo, TheftGame.AMMO, "tambor lleno")
	var helmeted := {}
	for th in g.thieves:
		if th["helmet"]:
			helmeted = th
			break
	check(not helmeted.is_empty(), "en la máxima hay ladrones con casco")
	helmeted["state"] = "enter"
	helmeted["pos"] = Vector2(180, 300)
	eq(g.tap(Vector2(180, 300 - TheftGame.BODY_OFFSET)), "armor", "el primer tiro rompe el casco")
	eq(g.tap(Vector2(180, 300 - TheftGame.BODY_OFFSET)), "hit", "el segundo lo baja")
	check(g.civilians.size() > 0, "en la máxima pasan clientes")
	var c: Dictionary = g.civilians[0]
	c["state"] = "walk"
	c["pos"] = Vector2(60, 400)
	eq(g.tap(Vector2(60, 400 - TheftGame.BODY_OFFSET)), "civilian", "le pegaste a un cliente")
	eq(g.tap(Vector2(60, 400 - TheftGame.BODY_OFFSET)), "stunned", "el revólver queda trabado")


func test_asalto_caja_en_el_piso_se_pierde() -> void:
	var g := TheftGame.new(5, 0.5)
	var l: Dictionary = g.loot[0]
	l["state"] = "floor"
	l["floor_t"] = 0.0
	l["pos"] = Vector2(-300, -300)        # lejos de los ladrones
	for i in int(g.floor_life() * 60.0) + 5:
		g.step(1.0 / 60.0)
	eq(l["state"], "lost", "se la lleva un cómplice")


func test_asalto_sin_hacer_nada_se_pierde_todo() -> void:
	var g := TheftGame.new(9, 0.4)
	while not g.finished:
		g.step(1.0 / 30.0)
	check(g.t <= TheftGame.DURATION + 0.05, "dura como mucho %d s" % int(TheftGame.DURATION))
	check(g.taken_count() > 0, "se llevaron algo")
	eq(g.recovered(), 0.0, "sin defensa no se recupera nada")
	check(not g.perfect(), "no es perfecto")


# ----------------------------------------------------------------- BribeGame

func test_coima_documentos() -> void:
	var g := BribeGame.new(4, 0.5)
	eq(g.doc_count(), 15, "15 documentos en dificultad media")
	check(g.limit_for(0) > g.limit_for(g.doc_count() - 1), "el tiempo se achica")
	var streak := 1
	for i in range(1, g.docs.size()):
		streak = streak + 1 if g.docs[i]["red"] == g.docs[i - 1]["red"] else 1
		check(streak <= 3, "nunca más de 3 del mismo color seguidos")
	var decoys := 0
	for d in g.docs:
		if d["decoy"]:
			decoys += 1
	check(decoys > 0, "hay papeles para confundir")
	while g.state == "play":
		g.step(BribeGame.REVEAL + 0.05)
		g.swipe(-1 if g.current()["red"] else 1)
	eq(g.state, "won", "pila completa")
	var g2 := BribeGame.new(4, 0.5)
	g2.swipe(1 if g2.current()["red"] else -1)
	eq(g2.state, "lost", "lado equivocado")
	eq(g2.fail_reason, "wrong", "motivo")
	var g3 := BribeGame.new(4, 0.5)
	for i in 120:
		g3.step(1.0 / 60.0)
	eq(g3.state, "lost", "se acabó el tiempo")
	eq(g3.fail_reason, "timeout", "motivo")


# ------------------------------------------------- bots que juegan como gente

## Jugador del asalto: ve con retraso (reaction), apunta con error (aim, px) y
## hace una acción cada act_every segundos. Prioriza recargar, salvar cajas
## que están por perderse y dispararle al ladrón que lleva una caja.
func _theft_bot(seed_value: int, diff: float, reaction: float, aim: float, act_every: float) -> TheftGame:
	var g := TheftGame.new(seed_value, diff, 380.0, 760.0)   # pantalla de teléfono típica
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value * 31 + 7
	var history: Array = []           ## posiciones vistas: [[t, {id: pos}]]
	var next_act := 0.4
	var dt := 1.0 / 60.0
	var dragging := -1
	var drag_until := 0.0
	while not g.finished:
		g.step(dt)
		var snap := {}
		for th in g.thieves:
			if th["state"] in ["enter", "grab", "flee"]:
				snap[th["id"]] = th["pos"]
		history.append([g.t, snap])
		while history.size() > 1 and float(history[1][0]) <= g.t - reaction:
			history.pop_front()
		if dragging >= 0:
			if g.t >= drag_until:
				g.drag_end(dragging, g.bag.get_center() + Vector2(rng.randf_range(-40, 40), rng.randf_range(-30, 10)))
				dragging = -1
				next_act = g.t + act_every
			continue
		if g.t < next_act:
			continue
		next_act = g.t + act_every * rng.randf_range(0.8, 1.25)
		if g.ammo <= 0 and g.reload_t <= 0.0:
			g.reload()
			continue
		var floor_l := {}
		for l in g.loot:
			if l["state"] == "floor":
				floor_l = l
				break
		var seen: Dictionary = history[0][1]
		if not floor_l.is_empty() and (seen.is_empty() or float(floor_l["floor_t"]) > g.floor_life() * 0.45):
			var lid := g.drag_start((floor_l["pos"] as Vector2) + Vector2(rng.randf_range(-8, 8), rng.randf_range(-8, 8)))
			if lid >= 0:
				dragging = lid
				drag_until = g.t + 0.15 + (floor_l["pos"] as Vector2).distance_to(g.bag.get_center()) / 900.0
			continue
		if seen.is_empty():
			continue
		var target_id: int = seen.keys()[0]
		for id in seen:
			if int(g.thieves[id]["carry"]) >= 0:
				target_id = id
				break
		var aim_at: Vector2 = (seen[target_id] as Vector2) - Vector2(0, TheftGame.BODY_OFFSET) + Vector2(rng.randfn(0.0, aim), rng.randfn(0.0, aim))
		g.tap(aim_at)
	return g


## Jugador de la coima: tarda reaction ± 25 % por papel y se equivoca con
## probabilidad err (el doble con los papeles que confunden).
func _bribe_bot(seed_value: int, diff: float, reaction: float, err: float) -> BribeGame:
	var g := BribeGame.new(seed_value, diff)
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value * 17 + 3
	var wait := BribeGame.REVEAL + reaction * rng.randf_range(0.75, 1.25)
	var dt := 1.0 / 60.0
	while g.state == "play":
		g.step(dt)
		if g.state != "play":
			break
		wait -= dt
		if wait <= 0.0:
			var d := g.current()
			var wrong := rng.randf() < err * (2.0 if d["decoy"] else 1.0)
			g.swipe((1 if d["red"] else -1) if wrong else (-1 if d["red"] else 1))
			wait = BribeGame.REVEAL + reaction * rng.randf_range(0.75, 1.25)
	return g


func test_dificultad_con_bots() -> void:
	var profiles := {
		"novato": {"reaction": 0.42, "aim": 14.0, "act": 0.42, "b_react": 0.85, "b_err": 0.06},
		"promedio": {"reaction": 0.3, "aim": 9.0, "act": 0.3, "b_react": 0.62, "b_err": 0.025},
		"hábil": {"reaction": 0.2, "aim": 5.0, "act": 0.2, "b_react": 0.45, "b_err": 0.008},
	}
	var rates := {}
	print("    perfil      dific  asalto: recupera  perfecto | coima: gana")
	for diff in [0.2, 0.6, 0.9]:
		for pname in profiles:
			var p: Dictionary = profiles[pname]
			var rec := 0.0
			var perfect := 0
			var won := 0
			var n := 40
			for s in n:
				var g := _theft_bot(1000 + s, diff, p["reaction"], p["aim"], p["act"])
				rec += g.recovered()
				if g.perfect():
					perfect += 1
				if _bribe_bot(2000 + s, diff, p["b_react"], p["b_err"]).state == "won":
					won += 1
			rates["%s@%.1f" % [pname, diff]] = {"rec": rec / n, "won": float(won) / n}
			print("    %-10s  %.1f        %3d %%      %3d %%  |       %3d %%" % [pname, diff, int(rec / n * 100), int(100.0 * perfect / n), int(100.0 * won / n)])
	# Complicado pero justo: el promedio recupera parte y gana la coima a
	# veces; el hábil casi siempre; el novato sufre en la máxima.
	check(float(rates["hábil@0.2"]["rec"]) > 0.8, "el hábil defiende bien al principio")
	check(float(rates["promedio@0.6"]["rec"]) > 0.35 and float(rates["promedio@0.6"]["rec"]) < 0.9, "el promedio recupera parte (%.2f)" % float(rates["promedio@0.6"]["rec"]))
	check(float(rates["novato@0.9"]["rec"]) < 0.6, "el novato sufre al final (%.2f)" % float(rates["novato@0.9"]["rec"]))
	check(float(rates["hábil@0.6"]["won"]) > 0.75, "el hábil suele ganar la coima")
	check(float(rates["promedio@0.6"]["won"]) > 0.3 and float(rates["promedio@0.6"]["won"]) < 0.85, "el promedio la gana a veces (%.2f)" % float(rates["promedio@0.6"]["won"]))
	check(float(rates["novato@0.9"]["won"]) < 0.3, "el novato casi nunca en la máxima")


# ------------------------------------------------- casos borde (revisión 11.2)

func test_pendientes_rotos_se_descartan_al_cargar() -> void:
	Security.ui_attached = false
	var m := make_model(8)
	var d := m.to_dict()
	d["hard"]["pending_theft"] = {"business": "no_existe", "fraction": 0.2}
	d["hard"]["pending_bribe"] = {"zone": 42}
	var m2 := make_model(9)
	m2.from_dict(d)
	check(Security.pending_theft(m2).is_empty(), "asalto con negocio desconocido descartado")
	check(Security.pending_bribe(m2).is_empty(), "coima con zona inválida descartada")
	d["hard"]["pending_theft"] = "basura"
	m2.from_dict(d)
	check(Security.pending_theft(m2).is_empty(), "asalto con tipo inválido descartado")


func test_coima_en_pantalla_no_se_abandona() -> void:
	Security.ui_attached = false
	var m := make_model(10)
	m.economy.reset_run(10_000_000)
	Security.start_bribe(m, Z0)
	Security.minigame_active = true
	advance_clock(600.0)
	Security.advance(m, 1.0, false)
	check(not Security.pending_bribe(m).is_empty(), "mientras se juega no se multa por abandono")
	Security.minigame_active = false
	Security.resolve_bribe(m, true)
	check(Security.fine_left(m) <= 0.0 and Security.protected_left(m, Z0) > 0.0, "gana y no hay multa")


func test_asalto_soltar_afuera_y_reescalar() -> void:
	var g := TheftGame.new(12, 0.3)
	var l: Dictionary = g.loot[0]
	l["state"] = "drag"
	g.drag_end(0, Vector2(5000, -300))     # lejos de la bolsa (abajo a la izquierda)
	eq(l["state"], "floor", "vuelve al piso")
	check((l["pos"] as Vector2).x >= 0.0 and (l["pos"] as Vector2).y <= g.h, "dentro del campo")
	eq(g.drag_start(l["pos"]), 0, "se puede volver a agarrar")
	g.drag_end(0, l["pos"])
	g.rescale(720.0, 1120.0)
	near(g.bag.end.y, 1120.0 - 4.0, 0.01, "la bolsa sigue abajo a la izquierda")
	check((l["pos"] as Vector2).x > 24.0, "las cajas se reescalan")


func test_salvado_cuenta_todo_el_estante() -> void:
	var g := TheftGame.new(13, 0.3)
	g.loot[0]["state"] = "lost"
	g.loot[1]["state"] = "bagged"
	near(g.recovered(), 0.5, 0.001, "de lo que salió, se recuperó la mitad")
	near(g.saved(), 1.0 - 1.0 / g.loot.size(), 0.001, "pero se salvó casi todo el estante")
