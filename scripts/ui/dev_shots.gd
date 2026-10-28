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
	for a in OS.get_cmdline_user_args():
		# --shots-scale=2: dibuja a x2 dentro de la misma ventana (como un
		# teléfono de alta densidad) para revisar la nitidez de la letra.
		if a.begins_with("--shots-scale="):
			get_window().content_scale_factor = float(a.get_slice("=", 1))
	for a in OS.get_cmdline_user_args():
		if a == "--shots-set=escenas":
			await _run_scenes()
			return
	var main := Main.instance
	var m := Game.m
	Game.reset_everything()
	await get_tree().process_frame
	main.modal_host.close_all()
	main.start.open(false)
	await _shot("00_inicio", 1.2)
	LoginModal.open()
	await _shot("00b_login", 0.5)
	main.modal_host.close_all()
	SettingsModal.open()
	await _shot("00c_configuracion_inicio", 0.5)
	main.modal_host.close_all()
	main.start.enter_game()
	await get_tree().create_timer(0.5).timeout
	print("ENTRAR_JUEGO ", "OK" if not main.start.is_open() else "FALLÓ")
	main.modal_host.close_all()          # resumen de "mientras no estabas"
	await get_tree().create_timer(0.4).timeout   # que termine la animación de cierre
	await _shot("01_paso1_abrir", 1.0)
	# Misión guiada con TOQUES REALES (eventos de entrada) sobre el botón principal.
	await _tap(main.targets["main"])
	await _shot("02_paso2_reponer", 0.6)
	print("TOQUE_ABRIR ", "OK" if not m.biz["puesto"]["closed"] else "FALLÓ")
	await _tap(main.targets["main"])
	await get_tree().create_timer(3.6).timeout
	await _shot("03_paso3_vender", 0.3)
	var before := m.counter("sales_total")
	await _tap(main.targets["main"])
	await get_tree().create_timer(1.3).timeout
	print("TOQUE_VENDER ", "OK" if m.counter("sales_total") > before else "FALLÓ")
	await _shot("04_paso4_subir", 0.4)
	# Partida avanzada para ver el resto de la interfaz
	m.economy.earn(3_000_000, "dev")
	m.update_progress()
	m.biz["puesto"]["level"] = 28
	m.invalidate()
	m.buy_business("kiosco")
	m.biz["kiosco"]["level"] = 12
	m.buy_business("comida")
	await _shot("05a_festejo_negocio", 1.2)
	UnlockShow.dismiss_all()
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
	await _shot("03b_imperio_automatizado", 1.2)
	main.select_business("comida")
	await _shot("04b_imperio_comida", 1.0)
	main.select_business("kiosco")
	await _shot("04c_imperio_kiosco_interior", 1.5)
	Settings.set_value("scene_view", "fachada")
	await _shot("04d_imperio_kiosco_fachada", 1.0)
	Settings.set_value("scene_view", "interior")
	main.select_business("puesto")
	for i in 5:
		main.go_to(i)
		await _shot("05_seccion_%d_%s" % [i, Main.SECTIONS[i].to_lower()], 0.6)
	main.go_to(0)
	await _bus_check()
	ManageBusinessModal.open("puesto", 0)
	await _shot("06_admin_negocio", 0.6)
	main.modal_host.close_all()
	ManageBusinessModal.open("puesto", 1)
	await _shot("07_admin_empleados", 0.6)
	await _drag_check()
	main.modal_host.close_all()
	ManageBusinessModal.open("puesto", 2)
	await _shot("08_admin_mejoras", 0.6)
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
	m.economy.earn(m.economy.money, "misiones")      # premio grande: rodillos girando
	await _shot("13b_jackpot_girando", 0.2)
	await _shot("13c_jackpot_final", 1.4)
	AdsModal.open("puesto")
	await _shot("14_bonos_anuncio", 0.5)
	main.modal_host.close_all()
	# Recorte con una imagen sintética (degradé + cuadrícula, 1200x800)
	var img := Image.create(1200, 800, false, Image.FORMAT_RGBA8)
	for y in 800:
		for x in 1200:
			img.set_pixel(x, y, Color.from_hsv(float(x) / 1200.0, 0.5, 0.6 + 0.4 * float(y) / 800.0) if (x / 100 + y / 100) % 2 == 0 else Color(0.95, 0.93, 0.9))
	var crop := CropScreen.open("photo", img)
	await _shot("15_recorte_foto", 0.6)
	crop._zoom(1.6, crop._frame_center())
	crop._confirm()
	var crop2 := CropScreen.open("banner", img)
	await _shot("16_recorte_banner", 0.6)
	crop2._confirm()
	main.go_to(4)
	await _shot("17_perfil_con_foto", 0.6)
	print("FOTO_GUARDADA ", "OK" if ProfileWidgets.has_photo() and ProfileWidgets.has_banner() else "FALLÓ")
	m.set_company_name("Distribuidora Hermanos Fernández")
	await _shot("17b_perfil_nombre_largo", 0.6)
	RenameDialog.open()
	await _shot("17c_renombrar", 0.5)
	main.modal_host.close_all()
	ProfileImages.clear("photo")
	ProfileImages.clear("banner")
	m.set_profile_image("photo", false)
	m.set_profile_image("banner", false)
	await _juice_shots()
	await _social_shots()
	await _account_switch_check()
	main.go_to(0)
	main.start.open(false)
	await _shot("18_volver_al_inicio", 0.6)
	get_tree().quit()


## 0.8: mejora que brilla en dorado y misión que se reclama (verde, tick y
## salida hacia la izquierda), con toques reales sobre los botones.
func _juice_shots() -> void:
	var main := Main.instance
	var m := Game.m
	m.economy.earn(50_000_000, "dev", false)
	ManageBusinessModal.open("puesto", 2)
	await get_tree().create_timer(0.4).timeout
	var buy := _find_button(main.modal_host, "COMPRAR")
	if buy:
		await _tap(buy)
	await _shot("23_mejora_brillo_a", 0.5)
	await _shot("23_mejora_brillo_b", 0.4)
	main.modal_host.close_all()
	main.go_to(3)
	await get_tree().create_timer(0.4).timeout
	var screen: ObjectivesScreen = main.find_children("*", "ObjectivesScreen", true, false)[0]
	var claim: Button = null
	for t in 3:
		screen.tab = t
		screen._build_list()
		await get_tree().process_frame
		claim = _find_button(screen, "RECLAMAR")
		if claim:
			break
	print("MISION_RECLAMABLE ", "OK" if claim else "FALLÓ")
	if claim:
		await _tap(claim)
		await _shot("24_mision_llenando", 0.25)
		await _shot("24_mision_tick", 0.35)
		await _shot("24_mision_saliendo", 0.55)
		await _shot("24_mision_lista", 0.8)
	# Premios esperando: dos desafíos completos y la recompensa diaria.
	var n := 0
	for c in m.data.challenges:
		if n < 2 and not m.missions["claimed"].has(c["id"]):
			m.missions["completed"][c["id"]] = true
			n += 1
	m.daily_reward["last_day"] = -1
	screen.tab = 1
	m.progress_changed.emit()
	await get_tree().process_frame
	var all := _find_button(main, "RECLAMAR TODO")
	print("RECLAMAR_TODO ", "OK" if all else "FALLÓ")
	if all:
		var before := ProgressionSystem.unclaimed_count(m)
		await _shot("25_reclamar_todo", 0.3)
		await _tap(all)
		await _shot("25b_reclamar_todo_animando", 0.5)
		await _shot("25c_reclamar_todo_listo", 1.6)
		print("RECLAMAR_TODO_COBRO ", "OK" if before > 0 and ProgressionSystem.unclaimed_count(m) == 0 else "FALLÓ")
	main.go_to(0)


## 0.7.1: entrar con otra cuenta en el mismo teléfono aparta la partida de la
## anterior (no se sube a la cuenta nueva) y volver la recupera. Usa cuentas
## ficticias y deja el estado de la nube (user://cloud.cfg) como estaba.
func _account_switch_check() -> void:
	var cloud := get_node("/root/Cloud")
	var cfg_path: String = cloud.STATE_PATH
	var cfg_bak := cfg_path + ".devshots_bak"
	var had_cfg := FileAccess.file_exists(cfg_path)
	if had_cfg:
		DirAccess.copy_absolute(cfg_path, cfg_bak)
	var keep := [cloud._synced_uid, cloud._synced_saved_at, cloud._cloud_update_time, cloud._stash.duplicate()]
	var m := Game.m
	cloud._synced_uid = "devshots_a"
	m.set_company_name("Empresa de A")
	cloud._switch_local_game("devshots_a", "devshots_b")
	await get_tree().process_frame
	var fresh := str(m.profile["company"]) != "Empresa de A" and FileAccess.file_exists(CloudSync.stash_path("devshots_a"))
	m.set_company_name("Empresa de B")
	cloud._switch_local_game("devshots_b", "devshots_a")
	await get_tree().process_frame
	var back := str(m.profile["company"]) == "Empresa de A" and FileAccess.file_exists(CloudSync.stash_path("devshots_b"))
	print("CAMBIO_CUENTA ", "OK" if fresh and back else "FALLÓ (nueva=%s vuelta=%s)" % [fresh, back])
	for uid in ["devshots_a", "devshots_b"]:
		SaveSystem.new(CloudSync.stash_path(uid)).delete_all()
	cloud._synced_uid = keep[0]
	cloud._synced_saved_at = keep[1]
	cloud._cloud_update_time = keep[2]
	cloud._stash = keep[3]
	if had_cfg:
		DirAccess.rename_absolute(cfg_bak, cfg_path)
	else:
		DirAccess.remove_absolute(cfg_path)


func _find_button(root_node: Node, text: String) -> Button:
	for b in root_node.find_children("*", "Button", true, false):
		if (b as Button).text.begins_with(text) and b.is_visible_in_tree() and not (b as Button).disabled:
			return b
	return null


## 0.7: saldo negativo, verificación de email y amigos. La cuenta y los
## amigos son de mentira (no se emite Auth.changed: nada toca la red).
func _social_shots() -> void:
	var main := Main.instance
	var m := Game.m
	main.go_to(0)
	var cash := m.economy.money
	m.economy.spend(cash, "dev")
	m.salary_debt = 48_500
	main.top_bar._show_balance(false)      # sin esperar el refresco de 0,3 s (humo headless)
	await _shot("19_saldo_negativo", 0.8)
	print("SALDO_NEGATIVO ", "OK" if main.top_bar.is_negative() else "FALLÓ")
	m.salary_debt = 0
	m.economy.earn(cash, "dev", false)
	var saved := [Auth.uid, Auth.email, Auth.email_verified]
	Auth.uid = "dev-uid"
	Auth.email = "jugador@ejemplo.com"
	Auth.email_verified = false
	VerifyEmailModal.open()
	await _shot("20_verificar_email", 0.5)
	main.modal_host.close_all()
	Auth.email_verified = true
	Friends.my_code = "K7M2QX"
	Friends.status = "ok"
	Friends.requests = [{"uid": "r1", "company": "Kiosco La Esquina", "avatar": "gorra", "at": 0.0}]
	Friends.gifts = [{"uid": "f1", "company": "Parrilla Don Tito", "day": 0}]
	Friends.friends = [
		{"uid": "f1", "company": "Parrilla Don Tito", "avatar": "perro", "stage": 5, "lifetime": 5_400_000_000, "prestige": 1, "code": "AB3CDE"},
		{"uid": "f2", "company": "Lavadero Burbujas", "avatar": "vecina", "stage": 3, "lifetime": 820_000, "prestige": 0, "code": "ZX9QWE"},
	]
	FriendsModal.open()
	await _shot("21_amigos", 0.6)
	main.modal_host.close_all()
	main.go_to(4)
	await _shot("22_perfil_amigos", 0.6)
	main.modal_host.close_all()
	SettingsModal.open()
	await get_tree().process_frame
	var sc := main.modal_host.find_children("*", "ScrollContainer", true, false)
	if not sc.is_empty():
		(sc[-1] as ScrollContainer).scroll_vertical = 100000
	await _shot("26_ajustes_cuenta_privacidad", 0.5)
	print("BORRAR_CUENTA_BOTON ", "OK" if _find_button(main, "Borrar mi cuenta") else "FALLÓ")
	main.modal_host.close_all()
	DeleteAccountDialog.open()
	await _shot("27_borrar_cuenta", 0.5)
	main.modal_host.close_all()
	Friends.friends = []
	Friends.requests = []
	Friends.gifts = []
	Friends.my_code = ""
	Friends.status = "off"
	Auth.uid = saved[0]
	Auth.email = saved[1]
	Auth.email_verified = saved[2]


## Set "escenas": los 12 negocios en sus 5 niveles visuales, de frente con el
## colectivo pasando por la calle, y el interior si lo tienen. Sirve para
## revisar carteles, superposiciones y el botón FACHADA/ADENTRO.
func _run_scenes() -> void:
	var main := Main.instance
	var m := Game.m
	Game.reset_everything()
	await get_tree().process_frame
	main.modal_host.close_all()
	main.start.enter_game()
	await get_tree().create_timer(0.4).timeout
	main.modal_host.close_all()
	main.tutorial._skip()
	m.economy.earn(10_000_000_000, "dev")
	for b in m.data.businesses:
		if not m.biz[b["id"]]["owned"]:
			m._own_business(b["id"], "barrio", 1.0)
		m.biz[b["id"]]["closed"] = false
	m.businesses_changed.emit()
	var scene: BusinessScene = main.find_children("*", "BusinessScene", true, false)[0]
	var tiers: Array = m.data.balance["visual_tiers"]
	for b in m.data.businesses:
		var id: String = b["id"]
		for t in tiers.size():
			m.biz[id]["level"] = int(tiers[t])
			m.invalidate()
			main.select_business(id)
			Settings.set_value("scene_view", "fachada")
			await get_tree().process_frame
			scene._bus.visible = true
			scene._bus.position = Vector2(scene.size.x / 2.0 - 140, BusinessScene.ROAD_Y - scene._bus.texture.get_height())
			scene._bus_t = 999.0
			await _shot("esc_%s_%d_fachada" % [id, t], 0.1)
			scene._bus.visible = false
			Settings.set_value("scene_view", "interior")
			await _shot("esc_%s_%d_%s" % [id, t, "interior" if BusinessScene.has_interior(id, t) else "sin_interior"], 0.2)
	get_tree().quit()


func _tap(target: Control) -> void:
	var center := target.get_global_rect().get_center()
	for pressed in [true, false]:
		var ev := InputEventMouseButton.new()
		ev.button_index = MOUSE_BUTTON_LEFT
		ev.pressed = pressed
		ev.position = center
		ev.global_position = center
		get_viewport().push_input(ev)
		await get_tree().process_frame


## Arrastrar empezando encima de un botón scrollea el modal y no lo activa.
func _drag_check() -> void:
	var main := Main.instance
	var m := Game.m
	var hire := _find_button(main.modal_host, "CONTRATAR")
	var sc: Array = main.modal_host.find_children("*", "DragScroll", true, false)
	if hire == null or sc.is_empty():
		print("ARRASTRE_SCROLL FALLÓ (sin botón o scroll)")
		return
	var scroll: DragScroll = sc[-1]
	var team := m.employees_of("puesto").size()
	var p := hire.get_global_rect().get_center()
	var press := InputEventMouseButton.new()
	press.button_index = MOUSE_BUTTON_LEFT
	press.pressed = true
	press.position = p
	press.global_position = p
	get_viewport().push_input(press)
	await get_tree().process_frame
	for i in 12:
		var mv := InputEventMouseMotion.new()
		p.y -= 15
		mv.position = p
		mv.global_position = p
		mv.relative = Vector2(0, -15)
		mv.button_mask = MOUSE_BUTTON_MASK_LEFT
		get_viewport().push_input(mv)
		await get_tree().process_frame
	var rel := press.duplicate() as InputEventMouseButton
	rel.pressed = false
	rel.position = p
	rel.global_position = p
	get_viewport().push_input(rel)
	await get_tree().process_frame
	var ok := scroll.scroll_vertical > 0 and m.employees_of("puesto").size() == team
	print("ARRASTRE_SCROLL ", "OK" if ok else "FALLÓ (scroll=%d equipo %d->%d)" % [scroll.scroll_vertical, team, m.employees_of("puesto").size()])
	scroll.scroll_vertical = 0


## Las ventas no reinician el colectivo y avanza hacia donde mira (derecha).
func _bus_check() -> void:
	var main := Main.instance
	var m := Game.m
	var scene: BusinessScene = main.find_children("*", "BusinessScene", true, false)[0]
	var prev_view = Settings.get_value("scene_view")
	var prev_anim = Settings.get_value("scene_anim")
	Settings.set_value("scene_view", "fachada")
	Settings.set_value("scene_anim", true)
	await get_tree().process_frame
	scene._bus.visible = true
	scene._bus.position.x = 40.0
	for i in 3:
		m.business_changed.emit(scene.bid)
		await get_tree().process_frame
	var x := scene._bus.position.x
	var ok := scene._bus.visible and x > 40.0 and x < 120.0
	print("COLECTIVO_SIGUE ", "OK" if ok else "FALLÓ (visible=%s x=%s)" % [scene._bus.visible, x])
	scene._bus.visible = false
	Settings.set_value("scene_view", prev_view)
	Settings.set_value("scene_anim", prev_anim)
