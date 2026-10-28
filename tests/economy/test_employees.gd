extends TestCase


func _ready_model() -> GameModel:
	var m := make_model(7)
	m.economy.reset_run(100_000)
	EmployeeSystem.ensure_candidates(m, B0)
	return m


func _hire_role(m: GameModel, bid: String, role: String) -> Dictionary:
	var cands: Array = m.biz[bid]["candidates"]
	for i in cands.size():
		if cands[i]["role"] == role:
			return EmployeeSystem.hire(m, bid, i)
	return GameModel.fail("no hay candidato " + role)


func test_candidates_include_seller_first() -> void:
	var m := _ready_model()
	var cands: Array = m.biz[B0]["candidates"]
	check(cands.size() > 0, "hay candidatos")
	eq(cands[0]["role"], "vendedor", "el primero que hace falta es un vendedor")
	for c in cands:
		check(c["name"] is String and c["hire"] > 0 and c["salary"] > 0.0, "candidato completo")


func test_hire_enables_automation_and_costs() -> void:
	var m := _ready_model()
	var c: Dictionary = m.biz[B0]["candidates"][0]
	var money0 := m.economy.money
	check(_hire_role(m, B0, "vendedor")["ok"], "contrata vendedor")
	eq(m.economy.money, money0 - int(c["hire"]), "cobra la contratación")
	check(m.derive(B0)["auto_sell"], "automatiza ventas")
	eq(m.derive(B0)["automation"], 1, "nivel de automatización 1")
	var sales0 := m.counter("sales_total")
	run(m, 5.0)
	check(m.counter("sales_total") > sales0 + 3, "vende solo")


func test_slots_limit() -> void:
	var m := _ready_model()
	check(_hire_role(m, B0, "vendedor")["ok"], "primer empleado")
	EmployeeSystem.generate_candidates(m, B0)
	var r := EmployeeSystem.hire(m, B0, 0)
	check(not r["ok"], "a nivel 1 sólo hay un puesto")


func test_cannot_hire_without_money() -> void:
	var m := _ready_model()
	m.economy.reset_run(0)
	check(not EmployeeSystem.hire(m, B0, 0)["ok"], "sin plata no contrata")
	eq(m.employees.size(), 0, "nadie contratado")


func test_salaries_are_paid_and_never_negative() -> void:
	var m := _ready_model()
	_hire_role(m, B0, "vendedor")
	var salary: float = m.derive(B0)["salary_sec"]
	check(salary > 0.0, "tiene sueldo")
	# Sin stock: no vende, sólo paga sueldos.
	for pid in m.biz[B0]["stock"]:
		m.biz[B0]["stock"][pid] = 0.0
	var paid0 := int(m.economy.expense_by_reason.get("sueldos", 0))
	run(m, 20.0)
	near(float(int(m.economy.expense_by_reason.get("sueldos", 0)) - paid0), salary * 20.0, salary + 1.0, "descuenta sueldos")
	m.economy.reset_run(0)
	run(m, 10.0)
	eq(m.economy.money, 0, "nunca negativo")
	check(m.salary_debt > 0, "acumula deuda")
	m.economy.earn(100000, "test")
	run(m, 0.2)
	eq(m.salary_debt, 0, "la deuda se paga al entrar plata")


func test_repositor_auto_restock() -> void:
	var m := _ready_model()
	m.biz[B0]["level"] = 10
	m.invalidate()
	EmployeeSystem.generate_candidates(m, B0)
	check(_hire_role(m, B0, "vendedor")["ok"], "vendedor")
	EmployeeSystem.generate_candidates(m, B0)
	check(_hire_role(m, B0, "repositor")["ok"], "repositor (nivel 10 tiene 2 puestos)")
	eq(m.derive(B0)["automation"], 2, "vende y repone solo")
	run(m, 300.0)
	check(m.stock_ratio(B0) > 0.2, "nunca se queda sin stock")
	check(m.counter("restock_count") >= 1, "repuso solo")


func test_employee_effects_apply_to_their_business_only() -> void:
	var m := _ready_model()
	m.biz[B0]["level"] = 10
	m.economy.reset_run(10_000_000)
	m.invalidate()
	m.buy_business(B1)
	var kiosco_cycle: float = m.derive(B1)["cycle"]
	EmployeeSystem.generate_candidates(m, B0)
	_hire_role(m, B0, "vendedor")
	var cands: Array = m.biz[B0]["candidates"]
	var found := false
	for i in cands.size():
		if cands[i]["role"] == "cajero":
			found = true
			var c0: float = m.derive(B0)["cycle"]
			EmployeeSystem.hire(m, B0, i)
			check(m.derive(B0)["cycle"] < c0, "el cajero acelera el puesto")
			break
	near(m.derive(B1)["cycle"], kiosco_cycle, 0.0001, "el kiosco no cambia")
	if not found:
		check(true, "")


func test_fire_pays_severance() -> void:
	var m := _ready_model()
	_hire_role(m, B0, "vendedor")
	var eid: String = m.employees.keys()[0]
	var sev := EmployeeSystem.severance(m, eid)
	var money0 := m.economy.money
	check(EmployeeSystem.fire(m, eid)["ok"], "despide")
	eq(m.economy.money, money0 - sev, "indemnización")
	check(not m.derive(B0)["auto_sell"], "deja de vender solo")
