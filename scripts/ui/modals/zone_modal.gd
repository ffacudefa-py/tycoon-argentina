class_name ZoneModal
extends RefCounted


static func open(zid: String) -> void:
	var m := Game.m
	var z: Dictionary = m.data.zone_by_id[zid]
	var st := m.zone_status(zid)
	var body := U.vbox(5)
	body.add_child(U.para(z["description"], U.SIZE_SMALL, U.TEXT))
	var dem := []
	for t in z["demand"]:
		dem.append("%s +%d %%" % [MapScreen.TAG_NAMES.get(t, t), int(round(float(z["demand"][t]) * 100))])
	body.add_child(U.label("Demanda fuerte", U.SIZE_SMALL, U.TEXT, true))
	body.add_child(U.para(", ".join(dem), U.SIZE_SMALL, U.GREEN))
	body.add_child(U.stat_row("Competencia base", "%d %%" % int(round(float(z["competition"]) * 100))))
	var rec := []
	for bid in z["recommended"]:
		rec.append(m.data.business_by_id[bid]["name"] if m.data.business_by_id.has(bid) else bid)
	body.add_child(U.stat_row("Recomendados", ""))
	body.add_child(U.para(", ".join(rec), U.SIZE_SMALL, U.TEXT))
	var mine := m.businesses_in_zone(zid)
	if not mine.is_empty():
		var names := []
		for bid in mine:
			names.append(m.data.business_by_id[bid]["name"])
		body.add_child(U.stat_row("Tus negocios acá", str(mine.size())))
		body.add_child(U.para(", ".join(names), U.SIZE_SMALL, U.TEXT))
	var rivals_here := []
	for r in m.data.rivals:
		if (r["zones"] as Array).has(zid):
			rivals_here.append(r["id"])
	if not rivals_here.is_empty():
		body.add_child(U.label("Rivales en la zona", U.SIZE_SMALL, U.TEXT, true))
		for rid in rivals_here:
			body.add_child(MapScreen.rival_card(rid))
	var w_ref := []
	if st["unlocked"]:
		body.add_child(U.para("Zona desbloqueada. Abrí o mudá negocios acá desde Negocios o Administrar.", U.SIZE_SMALL, U.GREEN))
	else:
		for req in m.requirements_for_zone(zid):
			body.add_child(UiColors.requirement_row(req))
		var b := UiColors.buy_button("DESBLOQUEAR", st["cost"], func() -> void:
			if Main.instance.result(m.unlock_zone(zid)):
				w_ref[0].close(), 44)
		UiColors.set_cost(b, st["cost"], "" if st["available"] else "Falta cumplir lo de arriba")
		body.add_child(b)
	w_ref.append(Main.instance.modal_host.open(z["name"], body))
