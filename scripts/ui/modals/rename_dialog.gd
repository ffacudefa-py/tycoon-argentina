class_name RenameDialog
extends RefCounted


static func open() -> void:
	var m := Game.m
	var body := U.vbox(6)
	body.add_child(U.para("¿Cómo se llama tu empresa? (2 a 24 letras)", U.SIZE_SMALL, U.TEXT))
	var le := LineEdit.new()
	le.text = m.profile["company"]
	le.max_length = 24
	le.custom_minimum_size.y = 28
	le.add_theme_font_size_override("font_size", U.SIZE_BODY)
	le.virtual_keyboard_enabled = true
	le.select_all_on_focus = true
	body.add_child(le)
	var ok := U.button("Guardar", "celeste", "check", 40)
	body.add_child(ok)
	var w := Main.instance.modal_host.open("Nombre de la empresa", body, true, 290)
	var save := func() -> void:
		if Main.instance.result(m.set_company_name(le.text)):
			w.close()
	U.on_press(ok, save)
	le.text_submitted.connect(func(_t: String) -> void: save.call())
