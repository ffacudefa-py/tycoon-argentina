class_name DeleteAccountDialog
extends RefCounted
## Borrar la cuenta desde el juego (requisito de Google Play para apps que
## permiten crear cuentas). Pide la contraseña y llama a Auth.delete_account().


static func open() -> void:
	var body := U.vbox(6)
	body.add_child(U.para("Se borran para siempre tu cuenta (%s), tu partida en la nube, tu perfil público, tu código de amigo y tus amigos, solicitudes y mates. No se puede deshacer." % Auth.email, U.SIZE_SMALL, U.TEXT))
	body.add_child(U.para("La partida de este teléfono no se borra: seguís jugando como invitado (si querés borrarla también, usá «Reiniciar partida»).", U.SIZE_SMALL, U.TEXT_SOFT))
	body.add_child(U.label("Contraseña", U.SIZE_SMALL, U.TEXT, true))
	var pw := LineEdit.new()
	pw.secret = true
	pw.placeholder_text = "tu contraseña"
	pw.virtual_keyboard_type = LineEdit.KEYBOARD_TYPE_PASSWORD
	pw.custom_minimum_size.y = 28
	pw.add_theme_font_size_override("font_size", U.SIZE_BODY)
	body.add_child(pw)
	var go := U.button("Borrar mi cuenta para siempre", "rojo", "alerta", 40, U.SIZE_SMALL)
	body.add_child(go)
	Main.instance.modal_host.open("Borrar cuenta", body, true, 300)
	U.on_press(go, func() -> void:
		go.disabled = true
		go.text = "Borrando…"
		var r: Dictionary = await Auth.delete_account(pw.text)
		if r["ok"]:
			Main.instance.modal_host.close_all()
			Main.instance.toast(r["msg"], "good")
		else:
			go.disabled = false
			go.text = "Borrar mi cuenta para siempre"
			Main.instance.result(r))
