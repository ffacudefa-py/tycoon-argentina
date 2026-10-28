class_name EventModal
extends RefCounted


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
