class_name ZoneModal
extends RefCounted


## 10.0: ficha de provincia. Producto, mercado (cuota contra el rival local)
## y la acción que toque: abrir el negocio, hacer campaña o ir a verlo.
static func open(zid: String) -> void:
	var m := Game.m
	var z: Dictionary = m.data.zone_by_id[zid]
	var bid: String = z["business"]
	var def: Dictionary = m.data.business_by_id[bid]
	var st := m.zone_status(zid)
	var body := U.vbox(6)
	body.add_child(U.para(z["description"], U.SIZE_SMALL, U.TEXT))
	var card := U.panel("Inset")
	var info := U.vbox(4)
	card.add_child(info)
	info.add_child(_row("estrella", "Producto estrella", z["star_product"], UiColors.GAIN))
	info.add_child(_row("caja", "También", ", ".join(z["secondary_products"]), U.TEXT))
	info.add_child(_row("tienda", "Tu negocio", def["name"], U.TEXT))
	body.add_child(card)
	var w_ref := []
	if st["unlocked"]:
		body.add_child(U.label("Mercado", U.SIZE_BODY, U.TEXT, true))
		var row := U.hbox(6)
		var bar := U.progress("amarillo", 10)
		bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(bar)
		var pct := U.label("", U.SIZE_BODY, U.TEXT, true)
		row.add_child(pct)
		body.add_child(row)
		var hint := U.para("", U.SIZE_SMALL, U.TEXT_SOFT)
		body.add_child(hint)
		var upd := func() -> void:
			var sh := ConquestSystem.share(m, zid)
			bar.value = sh
			pct.text = "%d %%" % int(floorf(sh * 100.0))
			if ConquestSystem.is_conquered(m, zid):
				hint.text = "¡Provincia conquistada! Tus negocios de la región ganan +%d %%." % int(round(float(m.data.world["province_bonus"]) * 100))
			else:
				hint.text = "Llegá al 100 %% ganando %s neto. Ahora vas hacia el %d %%." % [
					Fmt.per_sec(ConquestSystem.market_needed(m, zid)), int(floorf(ConquestSystem.target_share(m, zid) * 100.0))]
		upd.call()
		var t := Timer.new()
		t.wait_time = 0.5
		t.autostart = true
		t.timeout.connect(upd)
		body.add_child(t)
		if not ConquestSystem.is_conquered(m, zid) and m.rivals.has(z["rival"]):
			body.add_child(U.label("Rival local", U.SIZE_BODY, U.TEXT, true))
			body.add_child(MapScreen.rival_card(z["rival"]))
		var go := U.button("VER NEGOCIO", "celeste", "tienda", 40)
		U.on_press(go, func() -> void:
			w_ref[0].close()
			Main.instance.select_business(bid))
		body.add_child(go)
	else:
		for req in m.requirements_for_business(bid):
			body.add_child(UiColors.requirement_row(req))
		var b := UiColors.buy_button("ABRIR " + def["name"].to_upper(), st["cost"], func() -> void:
			if Main.instance.result(m.buy_business(bid)):
				w_ref[0].close(), 44)
		UiColors.set_cost(b, st["cost"], "" if st["available"] else "Conquistá la provincia anterior")
		body.add_child(b)
	w_ref.append(Main.instance.modal_host.open(z["name"], body))


## Fila "ícono  Título: valor" con salto de línea si el valor es largo.
static func _row(icon: String, title: String, value: String, color: Color) -> Control:
	var h := U.hbox(6)
	var ic := U.icon(icon)
	ic.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	h.add_child(ic)
	var col := U.vbox(0)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.add_child(U.label(title, U.SIZE_SMALL, U.TEXT_SOFT))
	col.add_child(U.para(value, U.SIZE_SMALL, color))
	h.add_child(col)
	return h
