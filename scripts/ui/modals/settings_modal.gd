class_name SettingsModal
extends RefCounted


static func open() -> void:
	var body := U.vbox(6)
	body.add_child(_toggle("Efectos de sonido", "sfx_enabled", "volumen"))
	var vol_row := U.hbox(6)
	vol_row.add_child(U.label("Volumen", U.SIZE_SMALL, U.TEXT))
	var slider := HSlider.new()
	slider.min_value = 0.0
	slider.max_value = 1.0
	slider.step = 0.05
	slider.value = float(Settings.get_value("sfx_volume"))
	slider.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	slider.custom_minimum_size.y = 20
	slider.value_changed.connect(func(v: float) -> void:
		Settings.set_value("sfx_volume", v)
		Sfx.play("coin", 1.0, 0.15))
	vol_row.add_child(slider)
	body.add_child(vol_row)
	body.add_child(_toggle("Vibración", "vibration", "vibrar"))
	body.add_child(U.label("Calidad de efectos visuales", U.SIZE_SMALL, U.TEXT, true))
	body.add_child(U.tabs(["Baja", "Media", "Alta"], func(i: int) -> void: Settings.set_value("fx_quality", i), int(Settings.get_value("fx_quality"))))
	body.add_child(_toggle("Ahorro de energía (30 FPS, menos animaciones)", "power_saver", "rayo"))
	body.add_child(_toggle("Confirmar acciones irreversibles", "confirm_irreversible", "alerta"))
	body.add_child(_toggle("Inflación ficticia (experimental)", "inflation", "fuego"))
	body.add_child(U.para("Con inflación activada, cada 10 minutos se anuncia una remarcación: la mercadería sube y tus precios acompañan un rato después. Reponer antes del aumento conviene. Los costos de niveles y mejoras no cambian.", 9, U.TEXT_SOFT))
	body.add_child(U.para("Música: esta versión no tiene música, sólo efectos de sonido.", 9, U.TEXT_SOFT))
	body.add_child(U.separator())
	body.add_child(U.para("Tu progreso se guarda automáticamente en este teléfono (cada 30 s y al salir). No hay sincronización en la nube todavía.", 9, U.TEXT_SOFT))
	var reset := U.button("Reiniciar partida", "rojo", "alerta", 28, U.SIZE_SMALL)
	U.on_press(reset, func() -> void:
		ConfirmDialog.open("¿Reiniciar TODO?", "Se borra la partida completa: dinero, negocios, logros, prestigio y perfil. No se puede deshacer.", "Borrar todo",
			func() -> void:
				Main.instance.modal_host.close_all()
				Game.reset_everything()
				Main.instance.toast("Partida nueva. ¡Suerte con el puestito!", "info")))
	body.add_child(reset)
	Main.instance.modal_host.open("Ajustes", body)

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
	cb.toggled.connect(func(on: bool) -> void:
		Settings.set_value(key, on)
		Sfx.play("tap"))
	row.add_child(cb)
	return row
