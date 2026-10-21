class_name StatsModal
extends RefCounted
## Estadísticas empresariales: todo sale del estado real del juego.


static func open() -> void:
	var m := Game.m
	var body := U.vbox(2)
	var best := m.most_profitable()
	var rows := [
		["Capital actual", Fmt.money(m.economy.money)],
		["Patrimonio estimado", Fmt.money(m.net_worth())],
		["Ingresos por segundo", Fmt.per_sec(m.revenue_per_sec())],
		["Gastos por segundo (mercadería)", "-" + Fmt.per_sec(m.stock_cost_per_sec())],
		["Gastos por segundo (sueldos)", "-" + Fmt.per_sec(m.salaries_per_sec())],
		["Beneficio neto por segundo", Fmt.per_sec(m.income_per_sec())],
		["Negocios", "%d/%d" % [m.owned_ids().size(), m.data.businesses.size()]],
		["Empleados", str(m.employees.size())],
		["Negocio más rentable", m.data.business_by_id[best]["name"] if best != "" else "-"],
		["Mejoras compradas", str(m.total_upgrades())],
		["Zonas", "%d/%d" % [m.zones.size(), m.data.zones.size()]],
		["Ventas realizadas", Fmt.integer(m.counter("sales_total"))],
		["Reposiciones", Fmt.integer(m.counter("restock_count"))],
		["Tiempo de juego", Fmt.duration(float(m.stats.get("play_time", 0.0)))],
		["Ganado en esta partida", Fmt.money(m.economy.run_earned)],
		["Dinero acumulado históricamente", Fmt.money(m.economy.lifetime_earned)],
		["Gastado en esta partida", Fmt.money(m.economy.run_spent)],
		["Récord de ganancia por segundo", Fmt.per_sec(float(m.stats.get("best_income", 0.0)))],
		["Grupos fundados (prestigio)", str(int(m.prestige.get("count", 0)))],
	]
	for r in rows:
		body.add_child(U.stat_row(r[0], r[1]))
	body.add_child(U.separator())
	body.add_child(U.para("Patrimonio = efectivo + 50 % de lo invertido en cada negocio + mercadería en stock a costo + 50 % de lo pagado por zonas. Cada activo se cuenta una sola vez.", 9, U.TEXT_SOFT))
	if not m.economy.income_by_source.is_empty():
		body.add_child(U.label("De dónde vino la plata (esta partida)", U.SIZE_SMALL, U.TEXT, true))
		for k in m.economy.income_by_source:
			body.add_child(U.stat_row(k.capitalize(), Fmt.money(m.economy.income_by_source[k]), U.GREEN))
	if not m.economy.expense_by_reason.is_empty():
		body.add_child(U.label("En qué se gastó", U.SIZE_SMALL, U.TEXT, true))
		for k in m.economy.expense_by_reason:
			body.add_child(U.stat_row(k.capitalize(), "-" + Fmt.money(m.economy.expense_by_reason[k]), U.RED))
	Main.instance.modal_host.open("Estadísticas", body)
