class_name ChestModal
extends RefCounted
## Abrir cofres (Engagement.open_chest): el premio se revela con un rebote.


static func open() -> void:
	var m := Game.m
	var body := U.vbox(8)
	var icon := U.icon32("regalo")
	icon.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	icon.custom_minimum_size = Vector2(64, 64)
	icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	body.add_child(icon)
	var prize := U.label("Tocá ABRIR", U.SIZE_TITLE, U.TEXT, true, HORIZONTAL_ALIGNMENT_CENTER)
	body.add_child(prize)
	var left := U.label("", U.SIZE_SMALL, U.TEXT_SOFT, false, HORIZONTAL_ALIGNMENT_CENTER)
	body.add_child(left)
	body.add_child(U.para("Se ganan con conquistas de provincias y regiones, logros, niveles 25/50/100 y desafíos de eventos.", U.SIZE_SMALL, U.TEXT_SOFT))
	var b := U.button("ABRIR", "amarillo", "regalo", 44)
	var refresh := func() -> void:
		var n := int(m.engage.get("chests", 0))
		left.text = "Te quedan %d cofre%s" % [n, "" if n == 1 else "s"]
		b.disabled = n <= 0
	refresh.call()
	U.on_press(b, func() -> void:
		var r := Engagement.open_chest(m)
		if not r["ok"]:
			Main.instance.result(r)
			return
		prize.text = r["text"]
		prize.pivot_offset = prize.size / 2.0
		prize.scale = Vector2(0.4, 0.4)
		var tw := prize.create_tween()
		tw.tween_property(prize, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		Main.instance.fx.coin_shower(icon.get_global_rect().get_center(), 12)
		Sfx.play("unlock")
		refresh.call(), "")
	body.add_child(b)
	Main.instance.modal_host.open("Cofres", body)
