class_name LoginModal
extends RefCounted
## Iniciar sesión / crear cuenta / recuperar contraseña (Firebase Auth real).
## Los errores se muestran en rojo debajo del formulario; mientras se espera
## al servidor el botón queda deshabilitado ("Conectando…").


static func open(mode := "login") -> void:
	var body := U.vbox(6)
	var w_ref := []
	var tabs := U.tabs(["Ingresar", "Crear cuenta"], func(i: int) -> void:
		w_ref[0].close()
		open("login" if i == 0 else "signup"), 0 if mode == "login" else 1)
	body.add_child(tabs)
	body.add_child(U.label("Email", U.SIZE_SMALL, U.TEXT, true))
	var email := LineEdit.new()
	email.placeholder_text = "tu@email.com"
	email.virtual_keyboard_type = LineEdit.KEYBOARD_TYPE_EMAIL_ADDRESS
	email.custom_minimum_size.y = 36
	email.text = Auth.email
	body.add_child(email)
	body.add_child(U.label("Contraseña", U.SIZE_SMALL, U.TEXT, true))
	var prow := U.hbox(4)
	var pw := LineEdit.new()
	pw.secret = true
	pw.placeholder_text = "mínimo %d caracteres" % AuthErrors.MIN_PASSWORD
	pw.virtual_keyboard_type = LineEdit.KEYBOARD_TYPE_PASSWORD
	pw.custom_minimum_size.y = 36
	pw.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	prow.add_child(pw)
	var reveal := U.button("Ver", "crema", "", 36, U.SIZE_SMALL)
	U.on_press(reveal, func() -> void:
		pw.secret = not pw.secret
		reveal.text = "Ver" if pw.secret else "Ocultar")
	prow.add_child(reveal)
	body.add_child(prow)
	var error := U.para("", U.SIZE_SMALL, Color("b83a3f"))
	error.visible = false
	body.add_child(error)
	var main_text := "INGRESAR" if mode == "login" else "CREAR CUENTA"
	var go := U.button(main_text, "verde", "check", 44, U.SIZE_BODY)
	body.add_child(go)
	var on_busy := func(b: bool) -> void:
		if is_instance_valid(go):
			go.disabled = b
			go.text = "CONECTANDO…" if b else main_text
	Auth.busy_changed.connect(on_busy)
	body.tree_exiting.connect(func() -> void: Auth.busy_changed.disconnect(on_busy))
	var show_error := func(msg: String) -> void:
		error.text = msg
		error.visible = msg != ""
	var submit := func() -> void:
		if Auth.busy:
			return
		show_error.call("")
		var cb := func(r: Dictionary) -> void:
			if r["ok"]:
				if w_ref.size() > 0 and is_instance_valid(w_ref[0]):
					w_ref[0].close()
				Main.instance.toast(r["msg"], "good")
				Sfx.play("unlock")
			elif is_instance_valid(error):
				show_error.call(r["msg"])
				Sfx.play("error")
		if mode == "login":
			Auth.sign_in(email.text, pw.text, cb)
		else:
			Auth.sign_up(email.text, pw.text, cb)
	U.on_press(go, submit, "")
	pw.text_submitted.connect(func(_t: String) -> void: submit.call())
	email.text_submitted.connect(func(_t: String) -> void: pw.grab_focus())
	if mode == "login":
		var forgot := U.button("¿Olvidaste tu contraseña?", "crema", "", 32, U.SIZE_SMALL)
		U.on_press(forgot, func() -> void:
			show_error.call("")
			Auth.send_password_reset(email.text, func(r: Dictionary) -> void:
				if r["ok"]:
					Main.instance.toast(r["msg"], "info")
				elif is_instance_valid(error):
					show_error.call(r["msg"])))
		body.add_child(forgot)
	else:
		body.add_child(U.para("La cuenta sirve para identificarte. Tu partida sigue guardada en este teléfono (todavía no se sube a la nube).", U.SIZE_SMALL, U.TEXT_SOFT))
	var back := U.button("Volver", "crema", "izquierda", 32, U.SIZE_SMALL)
	U.on_press(back, func() -> void: w_ref[0].close())
	body.add_child(back)
	w_ref.append(Main.instance.modal_host.open("Iniciar sesión" if mode == "login" else "Crear cuenta", body, true, 320))
