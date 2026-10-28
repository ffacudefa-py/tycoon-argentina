extends TestCase


func test_data_loads_without_errors() -> void:
	eq(data().errors.size(), 0, "errores de datos: %s" % str(data().errors))
	check(data().businesses.size() >= 5, "al menos cinco negocios")


func test_spend_rejects_and_never_negative() -> void:
	var e := Economy.new()
	e.reset_run(100)
	check(not e.spend(101, "x"), "no debe gastar más de lo que hay")
	eq(e.money, 100, "saldo intacto")
	check(e.spend(100, "x"), "gasto exacto")
	eq(e.money, 0, "saldo cero")
	check(not e.spend(-5, "x"), "monto negativo rechazado")
	eq(e.spend_up_to(50, "x"), 0, "spend_up_to sin plata")
	eq(e.money, 0, "nunca negativo")


func test_earn_caps_at_max() -> void:
	var e := Economy.new()
	e.max_money = 1000
	e.reset_run(990)
	eq(e.earn(50, "x"), 10, "acredita hasta el tope")
	eq(e.money, 1000, "tope")
	eq(e.earn(5, "x"), 0, "nada más allá del tope")


func test_big_numbers_exact() -> void:
	var e := Economy.new()
	e.reset_run(0)
	e.earn(900_000_000_000_000_001, "x")
	e.earn(1, "x")
	eq(e.money, 900_000_000_000_000_002, "suma exacta en enteros grandes")
	var d := e.to_dict()
	var e2 := Economy.new()
	e2.from_dict(JSON.parse_string(JSON.stringify(d)))
	eq(e2.money, 900_000_000_000_000_002, "sobrevive a JSON sin perder precisión")


func test_format() -> void:
	eq(Fmt.money(950), "$950")
	eq(Fmt.money(12500), "$12,5 mil")
	eq(Fmt.money(3_400_000), "$3,4 M")
	eq(Fmt.money(2_100_000_000), "$2,1 mil M")
	eq(Fmt.money(7_000_000_000_000), "$7 B")
	eq(Fmt.money(999.9), "$999")
	eq(Fmt.cost(12_460), "$12,5 mil", "costo redondea hacia arriba")
	eq(Fmt.money(12_460), "$12,4 mil", "saldo redondea hacia abajo")
	eq(Fmt.money(2.5), "$2,5")
	eq(Fmt.money(0.96), "$0,9", "precio chico no se muestra como $0")
	eq(Fmt.money(3.0), "$3")
	eq(Fmt.money(2.9999999), "$3", "ruido de coma flotante")
	eq(Fmt.per_sec(-6.5), "-$6,5/s", "neto negativo con el signo adelante")
	eq(Fmt.integer(1234567), "1.234.567")
	eq(Fmt.duration(3725), "1 h 2 min")


func test_manual_sale_once_per_tap() -> void:
	var m := make_model()
	check(m.tap_sell(B0)["ok"], "primer toque vende")
	check(not m.tap_sell(B0)["ok"], "segundo toque mientras atiende no duplica")
	run(m, 1.2)
	var d := m.derive(B0)
	var expected := 0.0
	for p in d["products"]:
		expected += p["u"] * p["price"]
	near(float(m.economy.income_by_source.get("ventas", 0)), expected, 1.0, "ingreso de un ciclo (sólo ventas)")
	eq(int(m.counter("sales_total")), 1, "una venta")
	run(m, 3.0)
	eq(int(m.counter("sales_total")), 1, "sin automatización no vende solo")


func test_level_purchase() -> void:
	var m := make_model()
	m.economy.reset_run(1000)
	var c1 := m.level_cost(B0, 1)
	var c10 := m.level_cost(B0, 10)
	check(c10 > c1 * 10, "10 niveles cuestan más que 10 veces el primero")
	var n := m.max_affordable_levels(B0)
	check(m.level_cost(B0, n) <= 1000 and m.level_cost(B0, n + 1) > 1000, "máximo comprable correcto")
	check(m.buy_levels(B0, 1)["ok"], "compra")
	eq(m.economy.money, 1000 - c1, "descuenta exacto")
	eq(int(m.biz[B0]["level"]), 2, "nivel 2")
	m.economy.reset_run(0)
	check(not m.buy_levels(B0, 1)["ok"], "sin plata no compra")
	eq(int(m.biz[B0]["level"]), 2, "nivel intacto")


func test_milestone_speed_and_units() -> void:
	var m := make_model()
	var c1: float = m.derive(B0)["cycle"]
	m.biz[B0]["level"] = 10
	m.invalidate()
	var d := m.derive(B0)
	near(d["cycle"], c1, 0.001, "el hito 10 no cambia la velocidad")
	eq(d["slots"], 2, "el hito 10 suma un puesto de empleado")
	near(d["units"], 10.0, 0.001, "10 clientes por ciclo")


func test_upgrades_have_real_effects() -> void:
	var m := make_model()
	m.biz[B0]["level"] = 60
	m.invalidate()
	var before := m.derive(B0).duplicate(true)
	for uid in data().upgrade_by_id:
		var u: Dictionary = data().upgrade_by_id[uid]
		for req in u["requires"]:
			m.biz[B0]["upgrades"][req] = maxi(int(m.biz[B0]["upgrades"].get(req, 0)), int(u["requires"][req]))
	m.biz[B0]["upgrades"] = {}
	m.invalidate()
	# Cada mejora debe cambiar al menos una variable del juego.
	for uid in data().upgrade_by_id:
		var m2 := make_model()
		m2.biz[B0]["level"] = 60
		var u: Dictionary = data().upgrade_by_id[uid]
		for req in u["requires"]:
			m2.biz[B0]["upgrades"][req] = int(u["requires"][req])
		m2.invalidate()
		var a := m2.derive(B0).duplicate(true)
		m2.economy.reset_run(10_000_000_000)
		var r := m2.buy_upgrade(B0, uid)
		check(r["ok"], "%s se puede comprar: %s" % [uid, r["msg"]])
		var b := m2.derive(B0)
		var changed: bool = a["cycle"] != b["cycle"] or a["units"] != b["units"] or a["price_mult"] != b["price_mult"] \
			or a["cost_mult"] != b["cost_mult"] or a["slots"] != b["slots"] or a["products"][0]["cap"] != b["products"][0]["cap"] \
			or a["mods"]["employee_eff"] != b["mods"]["employee_eff"] or a["mods"]["salary_reduction"] != b["mods"]["salary_reduction"]
		check(changed, "la mejora %s cambia algo" % uid)
	check(before["cycle"] > 0.0, "ciclo positivo")


func test_upgrade_requirements() -> void:
	var m := make_model()
	m.economy.reset_run(1_000_000_000)
	var st := m.upgrade_status(B0, "sucursal")
	check(st["locked"], "sucursal bloqueada al inicio")
	check(not m.buy_upgrade(B0, "sucursal")["ok"], "no se compra bloqueada")
	m.biz[B0]["level"] = 2
	check(m.buy_upgrade(B0, "stock_ampliado")["ok"], "stock ampliado a nivel 2")
	for i in 10:
		m.buy_upgrade(B0, "stock_ampliado")
	eq(int(m.biz[B0]["upgrades"]["stock_ampliado"]), 5, "respeta el máximo")


func test_restock_and_delivery() -> void:
	var m := make_model()
	m.economy.reset_run(10_000)
	var q := m.restock_quote(B0)
	check(q["total"] > 0, "hay algo para reponer al empezar a medio stock")
	var money0 := m.economy.money
	check(m.restock(B0)["ok"], "repone")
	eq(m.economy.money, money0 - q["total"], "cobra lo cotizado")
	check(not m.biz[B0]["orders"].is_empty(), "pedido en camino")
	run(m, float(data().business_by_id[B0]["restock_time"]) + 0.2)
	check(m.biz[B0]["orders"].is_empty(), "llegó")
	near(m.stock_ratio(B0), 1.0, 0.01, "depósito lleno")
	check(not m.restock(B0)["ok"], "lleno: no repone de nuevo")


func test_restock_partial_when_short() -> void:
	var m := make_model()
	m.economy.reset_run(5)
	var r := m.restock(B0)
	check(r["ok"], "compra parcial con poca plata")
	eq(m.economy.money, 0, "usa lo que hay, sin negativos")


func test_no_stock_no_sale() -> void:
	var m := make_model()
	for pid in m.biz[B0]["stock"]:
		m.biz[B0]["stock"][pid] = 0.0
	check(not m.tap_sell(B0)["ok"], "sin stock no se vende")


func test_buy_business_requirements() -> void:
	var m := make_model()
	m.economy.reset_run(1_000_000)
	var r := m.buy_business(B1)
	check(not r["ok"], "el segundo negocio requiere conquistar la primera provincia")
	conquer(m, B0)
	r = m.buy_business(B1)
	check(r["ok"], "ahora sí: %s" % r["msg"])
	check(m.biz[B1]["owned"], "segundo negocio propio")
	near(m.stock_ratio(B1), 1.0, 0.01, "viene con stock lleno")
	check(not m.buy_business(B1)["ok"], "no se compra dos veces")
	check(not m.buy_business(B3)["ok"], "el cuarto sigue bloqueado")


func test_net_worth_rules() -> void:
	var m := make_model()
	m.economy.reset_run(1000)
	var nw0 := m.net_worth()
	var cost := m.level_cost(B0, 1)
	m.buy_levels(B0, 1)
	near(m.net_worth(), nw0 - cost + cost * 0.5, 0.01, "una inversión vale la mitad en el patrimonio")
