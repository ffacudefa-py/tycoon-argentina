class_name SettingsModal
extends RefCounted
## Configuración. Todo se aplica al instante y se guarda en
## user://settings.cfg (sobrevive a cerrar la app y al prestigio).


static func open() -> void:
	var body := U.vbox(6)
	var w_ref := []
	# --- Sonido
	body.add_child(_section("Sonido", "volumen"))
	body.add_child(_slider("Volumen general", "master_volume"))
	body.add_child(_toggle("Silenciar todo", "mute", "volumen"))
	body.add_child(_toggle("Efectos de sonido", "sfx_enabled", "volumen"))
	body.add_child(_slider("Volumen de efectos", "sfx_volume"))
	body.add_child(U.para("Música: esta versión no tiene música, sólo efectos de sonido.", U.SIZE_SMALL, U.TEXT_SOFT))
	# --- Gráficos y rendimiento
	body.add_child(_section("Gráficos y rendimiento", "chispa"))
	body.add_child(U.label("Calidad de efectos visuales", U.SIZE_SMALL, U.TEXT, true))
	body.add_child(U.tabs(["Baja", "Media", "Alta"], func(i: int) -> void: Settings.set_value("fx_quality", i), int(Settings.get_value("fx_quality"))))
	body.add_child(_toggle("Animaciones del escenario (clientes, humo, neón)", "scene_anim", "persona"))
	body.add_child(_toggle("Ahorro de energía (30 FPS, menos animaciones)", "power_saver", "rayo"))
	body.add_child(U.label("Vista del negocio", U.SIZE_SMALL, U.TEXT, true))
	body.add_child(U.para("Los puestos al aire libre (mesita, carrito, lavadero abierto) se ven siempre desde la calle.", U.SIZE_SMALL, U.TEXT_SOFT))
	body.add_child(U.tabs(["Adentro del local", "Fachada"], func(i: int) -> void: Settings.set_value("scene_view", ["interior", "fachada"][i]), 0 if Settings.get_value("scene_view") == "interior" else 1))
	# --- Juego y accesibilidad
	body.add_child(_section("Juego y accesibilidad", "estrella"))
	body.add_child(_toggle("Vibración", "vibration", "vibrar"))
	body.add_child(_toggle("Reducir movimiento (sin rebotes ni partículas extra)", "reduce_motion", "info"))
	body.add_child(_toggle("Confirmar acciones irreversibles", "confirm_irreversible", "alerta"))
	body.add_child(_toggle("Inflación ficticia (experimental)", "inflation", "fuego"))
	body.add_child(U.para("Con inflación activada, cada 10 minutos se anuncia una remarcación: la mercadería sube y tus precios acompañan un rato después. Los costos de niveles y mejoras no cambian.", U.SIZE_SMALL, U.TEXT_SOFT))
	body.add_child(U.stat_row("Idioma", "Español (Argentina)"))
	body.add_child(U.para("Notificaciones: todavía no hay avisos fuera del juego. Al volver ves el resumen de lo que ganaste.", U.SIZE_SMALL, U.TEXT_SOFT))
	# --- Cuenta
	body.add_child(_section("Cuenta", "persona"))
	if Auth.signed_in():
		body.add_child(U.stat_row("Sesión iniciada", Auth.email))
		var cloud_l := U.para(Cloud.status_text(), U.SIZE_SMALL, U.RED if Cloud.status == "error" else U.TEXT_SOFT)
		body.add_child(cloud_l)
		var sync := U.button("Sincronizar ahora", "verde", "check", 32, U.SIZE_SMALL)
		U.on_press(sync, func() -> void: Cloud.sync_now())
		body.add_child(sync)
		var on_status := func() -> void:
			if is_instance_valid(cloud_l):
				cloud_l.text = Cloud.status_text()
				cloud_l.add_theme_color_override("font_color", U.RED if Cloud.status == "error" else U.TEXT_SOFT)
		Cloud.status_changed.connect(on_status)
		cloud_l.tree_exiting.connect(func() -> void: Cloud.status_changed.disconnect(on_status))
		var prof := U.button("Ver perfil", "celeste", "persona", 32, U.SIZE_SMALL)
		U.on_press(prof, func() -> void:
			w_ref[0].close()
			if Main.instance.start.is_open():
				Main.instance.start.enter_game()
			Main.instance.go_to(4))
		body.add_child(prof)
		var out := U.button("Cerrar sesión", "rojo", "cerrar", 32, U.SIZE_SMALL)
		U.on_press(out, func() -> void:
			ConfirmDialog.open("¿Cerrar sesión?", "Tu partida queda guardada en este teléfono y en la nube; podés seguir jugando como invitado.", "Cerrar sesión",
				func() -> void:
					Auth.sign_out()
					w_ref[0].close()
					Main.instance.toast("Cerraste sesión. Tu partida sigue en este teléfono.", "info"), false))
		body.add_child(out)
	else:
		body.add_child(U.para("Jugás como invitado. Con una cuenta tu partida se guarda también en la nube: si cambiás de teléfono o reinstalás el juego, no perdés nada.", U.SIZE_SMALL, U.TEXT_SOFT))
		var login := U.button("Iniciar sesión o crear cuenta", "celeste", "persona", 32, U.SIZE_SMALL)
		U.on_press(login, func() -> void:
			w_ref[0].close()
			LoginModal.open())
		body.add_child(login)
	# --- Partida
	body.add_child(_section("Partida", "caja"))
	body.add_child(U.para("Tu progreso se guarda automáticamente en este teléfono (cada 30 s y al salir).", U.SIZE_SMALL, U.TEXT_SOFT))
	if not Main.instance.start.is_open():
		var menu := U.button("Volver al menú principal", "crema", "izquierda", 32, U.SIZE_SMALL)
		U.on_press(menu, func() -> void:
			w_ref[0].close()
			Game.save()
			Main.instance.start.open())
		body.add_child(menu)
	var reset := U.button("Reiniciar partida", "rojo", "alerta", 28, U.SIZE_SMALL)
	U.on_press(reset, func() -> void:
		ConfirmDialog.open("¿Reiniciar TODO?", "Se borra la partida completa: dinero, negocios, logros, prestigio y perfil. No se puede deshacer.", "Borrar todo",
			func() -> void:
				Main.instance.modal_host.close_all()
				Game.reset_everything()
				Main.instance.toast("Partida nueva. ¡Suerte con el puestito!", "info")))
	body.add_child(reset)
	w_ref.append(Main.instance.modal_host.open("Configuración", body))


static func _section(text: String, icon_name: String) -> Control:
	var row := U.hbox(4)
	row.add_child(U.icon(icon_name))
	row.add_child(U.label(text, U.SIZE_BODY, U.TEXT, true))
	var v := U.vbox(2)
	v.add_child(U.separator())
	v.add_child(row)
	return v


static func _slider(text: String, key: String) -> Control:
	var row := U.hbox(6)
	var l := U.label(text, U.SIZE_SMALL, U.TEXT)
	l.custom_minimum_size.x = 120
	row.add_child(l)
	var slider := HSlider.new()
	slider.min_value = 0.0
	slider.max_value = 1.0
	slider.step = 0.05
	slider.value = float(Settings.get_value(key))
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	slider.custom_minimum_size.y = 28
	var pct := U.label("%d%%" % int(slider.value * 100), U.SIZE_SMALL, U.TEXT_SOFT)
	pct.custom_minimum_size.x = 36
	slider.value_changed.connect(func(v: float) -> void:
		Settings.set_value(key, v)
		pct.text = "%d%%" % int(v * 100)
		Sfx.play("coin", 1.0, 0.15))
	row.add_child(slider)
	row.add_child(pct)
	return row


static func _toggle(text: String, key: String, icon_name: String) -> Control:
	var row := U.hbox(6)
	row.add_child(U.icon(icon_name))
	var cb := CheckButton.new()
	cb.text = text
	cb.focus_mode = Control.FOCUS_NONE
	cb.button_pressed = bool(Settings.get_value(key))
	cb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	cb.add_theme_font_size_override("font_size", U.SIZE_SMALL)
	cb.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	cb.custom_minimum_size.y = 32
	cb.toggled.connect(func(on: bool) -> void:
		Settings.set_value(key, on)
		Sfx.play("tap"))
	row.add_child(cb)
	return row
