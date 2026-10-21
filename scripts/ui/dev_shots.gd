class_name DevShots
extends Node
## Herramienta de QA visual (sólo se activa con -- --shots=<carpeta>).
## Recorre pantallas y estados del juego y guarda capturas reales del
## render. Usa un guardado aparte (--dev-save=...) para no tocar partidas.
## Ver tools/screenshots.sh.

var out_dir := "user://shots"


func _ready() -> void:
	DirAccess.make_dir_recursive_absolute(out_dir)
	_run.call_deferred()


var size := Vector2i.ZERO


func _shot(name: String, wait := 0.35) -> void:
	if DisplayServer.get_name() == "headless":
		# Prueba de humo sin ventana: recorre todo, sin guardar imágenes.
		await get_tree().process_frame
		await get_tree().process_frame
		print("visitado: ", name)
		return
	# El gestor de ventanas del escritorio a veces la agranda: se fuerza el tamaño.
	if size == Vector2i.ZERO:
		size = get_window().size
	get_window().size = size
	await get_tree().create_timer(wait).timeout
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	img.save_png("%s/%s.png" % [out_dir, name])
	print("captura: ", name, " ", img.get_size())


func _run() -> void:
	var main := Main.instance
	var m := Game.m
	Game.reset_everything()
	await get_tree().process_frame
	main.modal_host.close_all()
	await _shot("01_inicio_tutorial", 1.0)
	# Toque real (evento de entrada) sobre ¡VENDER!: debe producir una venta.
	var sell: Control = main.targets["sell"]
	var before := m.counter("sales_total")
	var center := sell.get_global_rect().get_center()
	for pressed in [true, false]:
		var ev := InputEventMouseButton.new()
		ev.button_index = MOUSE_BUTTON_LEFT
		ev.pressed = pressed
		ev.position = center
		ev.global_position = center
		get_viewport().push_input(ev)
		await get_tree().process_frame
	await get_tree().create_timer(1.3).timeout
	print("TOQUE_VENDER ", "OK" if m.counter("sales_total") > before else "FALLÓ")
	for i in 6:
		m.tap_sell("puesto")
		m.simulate(1.1)
	m.buy_levels("puesto", 1)
	await _shot("02_primeras_ventas", 0.6)
	# Partida avanzada para ver el resto de la interfaz
	m.economy.earn(3_000_000, "dev")
	m.update_progress()
	m.biz["puesto"]["level"] = 28
	m.invalidate()
	m.buy_business("kiosco")
	m.biz["kiosco"]["level"] = 12
	m.buy_business("comida")
	m.invalidate()
	for id in ["puesto", "kiosco"]:
		EmployeeSystem.generate_candidates(m, id)
		EmployeeSystem.hire(m, id, 0)
	m.buy_upgrade("puesto", "stock_ampliado")
	m.buy_upgrade("puesto", "caja_rapida")
	m.unlock_zone("centro")
	m.update_progress()
	EventSystem.try_spawn(m, "ola_calor")
	main.select_business("puesto")
	main.tutorial._skip()
	await _shot("03_imperio_automatizado", 1.2)
	main.select_business("comida")
	await _shot("04_imperio_comida", 1.0)
	main.select_business("puesto")
	for i in 5:
		main.go_to(i)
		await _shot("05_seccion_%d_%s" % [i, Main.SECTIONS[i].to_lower()], 0.6)
	main.go_to(0)
	ManageBusinessModal.open("puesto", 0)
	await _shot("06_admin_mejoras", 0.6)
	main.modal_host.close_all()
	ManageBusinessModal.open("puesto", 1)
	await _shot("07_admin_empleados", 0.6)
	main.modal_host.close_all()
	ManageBusinessModal.open("puesto", 2)
	await _shot("08_admin_mercaderia", 0.6)
	main.modal_host.close_all()
	SettingsModal.open()
	await _shot("09_ajustes", 0.5)
	main.modal_host.close_all()
	StatsModal.open()
	await _shot("10_estadisticas", 0.5)
	main.modal_host.close_all()
	main.go_to(2)
	ZoneModal.open("centro")
	await _shot("11_zona", 0.5)
	main.modal_host.close_all()
	OfflineReport.open({"elapsed": 12000.0, "credited": 12000.0, "capped": false, "clock_issue": false, "earned": 845000,
		"spent": 120000, "per_business": {"puesto": 600000, "kiosco": 245000}, "stockouts": [{"business": "comida", "after": 1500.0}], "salaries": 2000})
	await _shot("12_offline", 0.5)
	main.modal_host.close_all()
	main.go_to(0)
	await _shot("13_fx_venta", 0.2)
	get_tree().quit()
