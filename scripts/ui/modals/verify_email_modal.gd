class_name VerifyEmailModal
extends RefCounted
## "Confirmá que el email es tuyo": se abre al crear la cuenta, al iniciar
## sesión con un email sin verificar y desde Configuración/Amigos. Hasta
## verificar, la nube y los amigos quedan en pausa (también lo exigen las
## reglas de Firestore).


static func open() -> void:
	if not Auth.signed_in():
		LoginModal.open()
		return
	var body := U.vbox(6)
	var w_ref := []
	body.add_child(U.icon32("persona"))
	body.add_child(U.para("Te mandamos un correo a:", U.SIZE_SMALL, U.TEXT_SOFT))
	body.add_child(U.label(Auth.email, U.SIZE_BODY, U.TEXT, true))
	body.add_child(U.para("Abrí el enlace del correo para confirmar que el email es tuyo y después tocá «Ya lo verifiqué». Mientras tanto podés jugar, pero tu progreso no se guarda en la nube y no podés agregar amigos.", U.SIZE_SMALL, U.TEXT_SOFT))
	var msg := U.para("", U.SIZE_SMALL, U.TEXT_SOFT)
	msg.visible = false
	body.add_child(msg)
	var show := func(text: String, bad: bool) -> void:
		if is_instance_valid(msg):
			msg.text = text
			msg.visible = text != ""
			msg.add_theme_color_override("font_color", U.RED if bad else U.GREEN)
	var check := U.button("YA LO VERIFIQUÉ", "verde", "check", 40, U.SIZE_BODY)
	U.on_press(check, func() -> void:
		check.disabled = true
		show.call("Consultando…", false)
		Auth.check_verified(func(r: Dictionary) -> void:
			if not is_instance_valid(check):
				return
			check.disabled = false
			if r["verified"]:
				w_ref[0].close()
				Main.instance.toast("¡Email verificado! Ya podés usar la nube y agregar amigos.", "good")
				Sfx.play("unlock")
			else:
				show.call(r["msg"], true)
				Sfx.play("error")), "")
	body.add_child(check)
	var resend := U.button("Reenviar el correo", "celeste", "", 32, U.SIZE_SMALL)
	U.on_press(resend, func() -> void:
		Auth.send_verification(func(r: Dictionary) -> void: show.call(r["msg"], not r["ok"])))
	body.add_child(resend)
	var other := U.button("Usar otra cuenta", "crema", "persona", 30, U.SIZE_SMALL)
	U.on_press(other, func() -> void:
		w_ref[0].close()
		Auth.sign_out()
		LoginModal.open())
	body.add_child(other)
	var later := U.button("Más tarde", "crema", "izquierda", 30, U.SIZE_SMALL)
	U.on_press(later, func() -> void: w_ref[0].close())
	body.add_child(later)
	w_ref.append(Main.instance.modal_host.open("Verificá tu email", body, true, 320))
