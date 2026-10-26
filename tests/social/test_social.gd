extends TestCase
## 0.7.0: amigos (sin red), saldo negativo y ritmo de ganancias al 80 %.
## La prueba contra Firebase (emuladores) está en tools/dev/social_check.gd.


func test_codigo_de_amigo() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = 7
	var seen := {}
	for i in 200:
		var c := FriendLogic.make_code(rng)
		eq(c.length(), FriendLogic.CODE_LEN, "largo del código")
		eq(FriendLogic.normalize_code(c), c, "un código generado es válido")
		seen[c] = true
	check(seen.size() > 195, "los códigos casi nunca se repiten")
	eq(FriendLogic.normalize_code(" k7m-2qx "), "K7M2QX", "minúsculas, espacios y guiones")
	eq(FriendLogic.normalize_code("K7M2Q0"), "", "el 0 no se usa (se confunde con la O)")
	eq(FriendLogic.normalize_code("K7M2Q"), "", "cortito no")
	eq(FriendLogic.normalize_code("K7M2QXZ"), "", "largo no")


func test_perfil_ida_y_vuelta() -> void:
	var m := make_model()
	m.set_company_name("Mates del Sur")
	m.economy.earn(9_000_000_000_000_123, "ventas")   # más que 2^53: sin perder dígitos
	var p := FriendLogic.profile_of(m, "uid-a", "K7M2QX")
	var doc: Dictionary = JSON.parse_string(JSON.stringify(FriendLogic.profile_fields(p, 1000.0)))
	doc["name"] = "projects/x/databases/(default)/documents/players/uid-a"
	var back := FriendLogic.profile_from_doc(doc)
	eq(back["uid"], "uid-a", "uid desde el nombre del documento")
	eq(back["company"], "Mates del Sur", "empresa")
	eq(back["lifetime"], m.economy.lifetime_earned, "ganado exacto")
	eq(back["code"], "K7M2QX", "código")
	check(FriendLogic.profile_from_doc({"name": "x/y"}).is_empty(), "documento vacío -> {}")


func test_ranking() -> void:
	var me := {"uid": "b", "lifetime": 500}
	var fr := [{"uid": "a", "lifetime": 900}, {"uid": "c", "lifetime": 100}, {"uid": "d", "lifetime": 500}]
	var r := FriendLogic.ranking(me, fr)
	eq(r.map(func(x: Dictionary) -> String: return x["uid"]), ["a", "b", "d", "c"], "orden por ganado; empate por uid")
	eq(fr.size(), 3, "no modifica la lista de amigos")


func test_regalos_con_cupo_diario() -> void:
	var m := make_model()
	var per_day := int(m.data.friends_cfg["gifts_per_day"])
	for i in per_day:
		var before := m.economy.money
		var r := FriendLogic.claim_gift(m, "Amigo")
		check(r["ok"], "regalo %d" % i)
		check(m.economy.money > before, "el regalo da plata")
	check(not FriendLogic.claim_gift(m, "Amigo")["ok"], "sin cupo después de %d" % per_day)
	clock_holder["t"] += 86400.0
	eq(FriendLogic.gifts_left_today(m), per_day, "al otro día vuelve el cupo")
	# El cupo se guarda con la partida.
	FriendLogic.claim_gift(m, "Amigo")
	var t: float = clock_holder["t"]
	var m2 := make_model()
	clock_holder["t"] = t
	m2.from_dict(JSON.parse_string(JSON.stringify(m.to_dict())))
	eq(FriendLogic.gifts_left_today(m2), per_day - 1, "cupo persistido")


func test_saldo_negativo() -> void:
	eq(Fmt.money(-1500), "-$1,5 mil", "signo adelante del $")
	eq(Fmt.money(-7), "-$7", "negativo chico")
	eq(Fmt.money(950), "$950", "positivo sin cambios")
	var m := make_model()
	m.economy.reset_run(0)
	m.salary_debt = 2_500
	eq(m.net_balance(), -2_500, "saldo neto = efectivo - sueldos atrasados")
	check(m.economy.money >= 0, "el efectivo nunca es negativo")
	m.economy.earn(1_000, "ventas")
	eq(m.net_balance(), -1_500, "sigue negativo hasta cubrir la deuda")


func test_ganancias_al_80() -> void:
	var m := make_model()
	eq(m.income_rate(), 0.8, "ritmo 0,8")
	var d := m.derive("puesto")
	var def: Dictionary = m.data.business_by_id["puesto"]
	var p0: Dictionary = def["products"][0]
	near(d["products"][0]["price"], float(p0["price"]) * 0.8 * float(d["zone_mult"]), 0.0001, "precio al 80 %")
	near(d["products"][0]["cost"], float(p0["cost"]) * 0.8, 0.0001, "mercadería al 80 % (el margen se mantiene)")
	# Premios fijos también.
	eq(ProgressionSystem.reward_money(m, {"money": 1000}), 800, "premio fijo al 80 %")


func test_migracion_v3_sueldos() -> void:
	var p := {"employees": {"1": {"salary": 10.0}}, "businesses": {"puesto": {"candidates": [{"salary": 5.0}]}}}
	var out := Migrations.migrate(p, 2)
	near(float(out["employees"]["1"]["salary"]), 8.0, 0.001, "sueldo de empleado al 80 %")
	near(float(out["businesses"]["puesto"]["candidates"][0]["salary"]), 4.0, 0.001, "sueldo de candidato al 80 %")
