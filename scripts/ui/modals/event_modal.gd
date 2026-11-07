class_name EventModal
extends RefCounted
## Detalle de un evento activo y, si hay varios a la vez, la lista de todos.


static func any_bad(m: GameModel) -> bool:
	for inst in m.events["active"]:
		if m.data.event_by_id[inst["id"]]["kind"] == "bad":
			return true
	return false


## Todos los eventos en curso; tocar uno abre su detalle.
static func open_list() -> void:
	var m := Game.m
	var active: Array = m.events["active"]
	if active.is_empty():
		return
	if active.size() == 1:
		open(0)
		return
	var body := U.vbox(6)
	body.add_child(U.para("Tocá un evento para ver qué hace y cómo resolverlo.", U.SIZE_SMALL, U.TEXT_SOFT))
	var w_ref := []
	for i in active.size():
		var inst: Dictionary = active[i]
		var e: Dictionary = m.data.event_by_id[inst["id"]]
		var where := ""
		if inst["business"] != "":
			where = " · " + str(m.data.business_by_id[inst["business"]]["name"])
		var b := U.button("%s%s · %s" % [e["name"], where, Fmt.duration(inst["remaining"])], "rojo" if e["kind"] == "bad" else "amarillo", e["icon"], 40, U.SIZE_SMALL)
		b.clip_text = true
		b.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		b.custom_minimum_size.x = 0
		var idx := i
		U.on_press(b, func() -> void:
			w_ref[0].close()
			open(idx))
		body.add_child(b)
	w_ref.append(Main.instance.modal_host.open("%d eventos activos" % active.size(), body, true, 300))


static func open(index: int) -> void:
	var m := Game.m
	var active: Array = m.events["active"]
	if index >= active.size():
		return
	var inst: Dictionary = active[index]
	var e: Dictionary = m.data.event_by_id[inst["id"]]
	var body := U.vbox(5)
	body.add_child(U.para(e["description"], U.SIZE_SMALL, U.TEXT))
	if e.has("goal"):
		var done: bool = inst.get("goal_done", false)
		var prog := Engagement.event_goal_progress(m, inst)
		body.add_child(UiColors.requirement_row({"text": "Desafío: %d ventas → cofre" % int(e["goal"]["target"]), "current": prog,
			"target": float(e["goal"]["target"]), "met": done, "money": false}))
	if inst["business"] != "":
		body.add_child(U.stat_row("Afecta a", m.data.business_by_id[inst["business"]]["name"]))
	body.add_child(U.stat_row("Termina en", Fmt.duration(inst["remaining"])))
	var w_ref := []
	for c in e.get("choices", []):
		var cost := EventSystem.resolve_cost(m, index, c["id"])
		var label: String = c["label"] + ((" · " + Fmt.cost(cost)) if cost > 0 else "")
		var b := U.button(label, "celeste" if c["result"] == "end" else "crema", "", 40, U.SIZE_BODY)
		var cid: String = c["id"]
		U.on_press(b, func() -> void:
			if Main.instance.result(EventSystem.resolve(m, index, cid)):
				w_ref[0].close())
		body.add_child(b)
	w_ref.append(Main.instance.modal_host.open(e["name"], body, true, 300))
