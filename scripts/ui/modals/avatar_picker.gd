class_name AvatarPicker
extends RefCounted


static func open() -> void:
	var m := Game.m
	var grid := GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 6)
	grid.add_theme_constant_override("v_separation", 6)
	var w_ref := []
	for a in m.data.avatars:
		var got: bool = m.profile["avatars"].has(a["id"])
		var v := U.vbox(1)
		var b := Button.new()
		b.theme_type_variation = "Btn_" + ("amarillo" if a["id"] == m.profile["avatar"] else ("crema" if got else "gris"))
		b.focus_mode = Control.FOCUS_NONE
		b.custom_minimum_size = Vector2(44, 40)
		b.icon = U.tex("avatars/%s.png" % a["id"]) if got else U.icon_tex("candado")
		b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		var aid: String = a["id"]
		var hint: String = a.get("hint", "")
		U.on_press(b, func() -> void:
			if got:
				Main.instance.result(m.set_avatar(aid))
				w_ref[0].close()
			else:
				Main.instance.toast("Bloqueado. " + hint, "info"))
		v.add_child(b)
		var l := U.label(a["name"] if got else "???", 9, U.TEXT, false, HORIZONTAL_ALIGNMENT_CENTER)
		l.custom_minimum_size.x = 44
		l.clip_text = true
		v.add_child(l)
		grid.add_child(v)
	w_ref.append(Main.instance.modal_host.open("Elegí tu avatar", grid, true, 260))
