class_name OfflineReport
extends RefCounted


static func open(r: Dictionary) -> void:
	var m := Game.m
	var body := U.vbox(5)
	if r.get("clock_issue", false):
		body.add_child(U.para("La fecha del teléfono parece haber ido para atrás. Por seguridad no se calcularon ganancias de ese período.", U.SIZE_SMALL, U.RED))
	else:
		body.add_child(U.label("Estuviste afuera %s" % Fmt.duration(r["elapsed"]), U.SIZE_BODY, U.TEXT, true))
		if r["capped"]:
			body.add_child(U.para("Se contaron %s (el máximo offline)." % Fmt.duration(r["credited"]), U.SIZE_SMALL, U.TEXT_SOFT))
		var earned: int = r["earned"]
		var box := U.panel("GoldCard")
		var bv := U.vbox(0)
		bv.add_child(U.label("Tus negocios vendieron", U.SIZE_SMALL, U.TEXT, false, HORIZONTAL_ALIGNMENT_CENTER))
		bv.add_child(U.label(Fmt.money(earned), 28, U.TEXT, true, HORIZONTAL_ALIGNMENT_CENTER))
		box.add_child(bv)
		body.add_child(box)
		if int(r["spent"]) > 0:
			body.add_child(U.stat_row("Gastos (mercadería y sueldos)", "-" + Fmt.money(r["spent"]), U.RED))
		for id in r["per_business"]:
			body.add_child(U.stat_row(m.data.business_by_id[id]["name"], "+" + Fmt.money(r["per_business"][id]), U.GREEN))
		if earned <= 0 and r["per_business"].is_empty():
			body.add_child(U.para("Ningún negocio vende solo todavía. Contratá un vendedor en Administrar para ganar mientras no jugás.", U.SIZE_SMALL, U.TEXT))
		for so in r["stockouts"]:
			body.add_child(U.para("%s se quedó sin mercadería a los %s. Un repositor lo evita." % [m.data.business_by_id[so["business"]]["name"], Fmt.duration(so["after"])], U.SIZE_SMALL, U.RED))
	var ok := U.button("¡A seguir!", "verde", "", 30)
	body.add_child(ok)
	var w := Main.instance.modal_host.open("Mientras no estabas", body, true, 300)
	U.on_press(ok, w.close, "coin")
