class_name BuyBusinessModal
extends RefCounted


static func open(id: String) -> void:
	var m := Game.m
	var def: Dictionary = m.data.business_by_id[id]
	var st := m.unlock_status(id)
	var body := U.vbox(6)
	body.add_child(U.para("Elegí dónde abrir %s. Cada zona tiene demanda y competencia distintas (podés mudarlo después)." % def["name"], U.SIZE_SMALL, U.TEXT))
	var w_ref := []
	for zid in m.zones:
		var z: Dictionary = m.data.zone_by_id[zid]
		var bonus := 0.0
		for t in def["tags"]:
			bonus = maxf(bonus, float(z["demand"].get(t, 0.0)))
		var row := U.panel("Inset")
		var h := U.hbox(4)
		var v := U.vbox(0)
		v.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		v.add_child(U.label(z["name"], U.SIZE_SMALL, U.TEXT, true))
		v.add_child(U.label("Demanda +%d %% · Competencia %d %%" % [int(bonus * 100), int(_comp(m, id, zid) * 100)], 9, U.TEXT_SOFT))
		h.add_child(v)
		var b := U.button("Abrir acá", "verde", "", 24, U.SIZE_SMALL)
		var z_id: String = zid
		U.on_press(b, func() -> void:
			if Main.instance.result(m.buy_business(id, z_id)):
				w_ref[0].close()
				Main.instance.select_business(id), "")
		h.add_child(b)
		row.add_child(h)
		body.add_child(row)
	body.add_child(U.label("Costo: " + Fmt.cost(st["cost"]), U.SIZE_BODY, U.TEXT, true))
	w_ref.append(Main.instance.modal_host.open("Abrir " + def["name"], body))

static func _comp(m: GameModel, id: String, zid: String) -> float:
	var old: String = m.biz[id]["zone"]
	m.biz[id]["zone"] = zid
	var c := RivalSystem.competition_for(m, id)
	m.biz[id]["zone"] = old
	return c
