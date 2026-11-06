class_name DevTrailer
extends RefCounted
## Grabación para el trailer (sólo con -- --shots=<carpeta> --shots-set=trailer).
## Juega a ritmo humano y deja marcas en la salida para cortar los clips:
##   TRAILER_MARK <nombre> <cuadro>   y   TRAILER_TAP <cuadro> <x> <y>
## Pensado para usarse con --write-movie y --fixed-fps 30.

var d: DevShots


func _init(shots: DevShots) -> void:
	d = shots


func _frame() -> int:
	return Engine.get_frames_drawn()


func mark(name: String) -> void:
	print("TRAILER_MARK ", name, " ", _frame())


func wait(s: float) -> void:
	await d.get_tree().create_timer(s).timeout


func tap(target: Control) -> void:
	var c := target.get_global_rect().get_center()
	print("TRAILER_TAP ", _frame(), " ", int(c.x), " ", int(c.y))
	await d._tap(target)


func tap_at(p: Vector2) -> void:
	print("TRAILER_TAP ", _frame(), " ", int(p.x), " ", int(p.y))
	await d._tap_at(p)


func run() -> void:
	var main := Main.instance
	var m := Game.m
	print("TRAILER_VIEWPORT ", d.get_viewport().get_visible_rect().size)
	Game.reset_everything()
	await d.get_tree().process_frame
	main.modal_host.close_all()
	main.start.open(false)
	await wait(1.0)
	mark("inicio")
	await wait(1.4)
	var jugar := d._find_button(main.start, "JUGAR")
	if jugar:
		await tap(jugar)
	else:
		main.start.enter_game()
	await wait(0.6)
	main.modal_host.close_all()
	await wait(0.5)
	# Tutorial con toques reales
	mark("tuto")
	await wait(1.4)
	await tap(main.targets["main"])
	await wait(1.6)
	await tap(main.targets["main"])
	await wait(3.9)
	for i in 4:
		await tap(main.targets["main"])
		await wait(0.7)
	await wait(1.2)
	mark("tuto_fin")
	main.tutorial._skip()
	await wait(3.5)

	# Cofre
	m.engage["chests"] = 2
	ChestModal.open()
	mark("cofre")
	await wait(1.0)
	var abrir := d._find_button(main.modal_host, "ABRIR")
	if abrir:
		await tap(abrir)
	await wait(ChestModal.SPIN_TIME + 1.8)
	mark("cofre_fin")
	main.modal_host.close_all()
	await wait(0.6)

	# Subir de nivel tocando y comprar un negocio nuevo
	m.economy.earn(2_000_000, "dev")
	m.update_progress()
	m.invalidate()
	await wait(1.0)
	mark("nivel")
	for i in 6:
		var subir := d._find_button(main, "SUBIR NIVEL")
		if subir:
			await tap(subir)
		await wait(0.35)
	await wait(0.8)
	mark("nivel_fin")
	ConquestSystem.conquer(m, m.data.zone_for_business(d.B0))
	await wait(0.4)
	UnlockShow.dismiss_all()
	main.modal_host.close_all()
	await wait(3.2)
	mark("nuevo")
	m.buy_business(d.B1)
	await wait(3.0)
	mark("nuevo_fin")
	UnlockShow.dismiss_all()
	main.modal_host.close_all()
	await wait(3.5)

	# Negocios vivos en otras provincias
	m.economy.earn(1_000_000_000, "dev")
	for i in [13, 23]:
		var b: String = m.data.businesses[i]["id"]
		if not m.biz[b]["owned"]:
			m._own_business(b, 1.0)
		m.biz[b]["level"] = 50
		m.biz[b]["closed"] = false
		m.invalidate()
		UnlockShow.dismiss_all()
		main.modal_host.close_all()
		main.select_business(b)
		Settings.set_value("scene_view", "fachada")
		await wait(3.6)
		mark("viva_" + b)
		var vender := main.targets["main"] as Control
		for k in 5:
			await tap(vender)
			await wait(0.55)
		await wait(0.6)
		mark("viva_fin_" + b)
	await wait(0.5)

	# Asalto: se deja ver a cada ladrón antes de dispararle
	await d._prepare_minigames()
	main.select_business(d.B0)
	await wait(3.6)
	Security.start_theft(m, d.B0)
	for i in 30:
		await d.get_tree().process_frame
		if MinigameHost.is_open():
			break
	mark("asalto")
	await _play_theft_slow()
	mark("asalto_fin")
	await wait(1.0)

	# Coima bien jugada
	var zid: String = m.data.zone_for_business(d.B0)
	MinigameHost.play_bribe(zid)
	await d.get_tree().process_frame
	mark("coima")
	await _play_bribe_calm()
	mark("coima_fin")
	await wait(1.0)
	d.get_tree().quit()


func _play_theft_slow() -> void:
	var view: TheftView = MinigameHost.current._view
	var seen := {}
	var last_shot := -999
	var t0 := Time.get_ticks_msec()
	while is_instance_valid(view) and not view._dismissed and Time.get_ticks_msec() - t0 < 90000:
		var o := view.get_global_rect().position
		var now := _frame()
		if view.phase == "intro" and view._waiting:
			await wait(1.4)
			await tap_at(o + view.size / 2.0)
		elif view.phase == "play":
			var g := view.game
			if g.ammo <= 0 and g.reload_t <= 0.0:
				await wait(0.3)
				await tap_at(o + view._gun_rect().get_center())
			else:
				var floor_l := {}
				for l in g.loot:
					if l["state"] == "floor":
						floor_l = l
						break
				if not floor_l.is_empty() and now - last_shot > 10:
					var a: Vector2 = o + (floor_l["pos"] as Vector2)
					var b: Vector2 = o + g.bag.get_center()
					print("TRAILER_TAP ", now, " ", int(a.x), " ", int(a.y))
					d._press(a, true)
					await d.get_tree().process_frame
					for i in 14:
						d._move(a.lerp(b, (i + 1) / 14.0))
						await d.get_tree().process_frame
					d._press(b, false)
				else:
					for k in g.thieves.size():
						var th: Dictionary = g.thieves[k]
						if th["state"] in ["enter", "grab", "flee"]:
							if not seen.has(k):
								seen[k] = now
							# Se dispara recién cuando el ladrón ya se vio un rato.
							if now - int(seen[k]) >= 38 and now - last_shot >= 16:
								last_shot = now
								await tap_at(o + (th["pos"] as Vector2) - Vector2(0, TheftGame.BODY_OFFSET))
								break
		elif view.phase == "result" and view.pt > 2.6 and view._result_btn:
			await tap(view._result_btn)
		await d.get_tree().process_frame


func _play_bribe_calm() -> void:
	var view: BribeView = MinigameHost.current._view
	var t0 := Time.get_ticks_msec()
	while is_instance_valid(view) and not view._dismissed and Time.get_ticks_msec() - t0 < 90000:
		var o := view.get_global_rect().position
		if view.phase == "intro" and view._waiting:
			await wait(1.2)
			await tap_at(o + view.size / 2.0)
		elif view.phase == "play" and view.game.state == "play" and view.game.reveal_t <= 0.0:
			await wait(0.08)
			if not (view.phase == "play" and view.game.state == "play" and view.game.reveal_t <= 0.0):
				continue
			var dd := view.game.current()
			var dir := -1 if dd["red"] else 1
			var a := o + view._stack_center()
			print("TRAILER_TAP ", _frame(), " ", int(a.x), " ", int(a.y))
			d._press(a, true)
			await d.get_tree().process_frame
			for i in 5:
				d._move(a + Vector2(dir * 32.0 * (i + 1), 0))
				await d.get_tree().process_frame
			d._press(a + Vector2(dir * 160.0, 0), false)
		elif view.phase == "result" and view.pt > 2.6 and view._result_btn:
			await tap(view._result_btn)
		await d.get_tree().process_frame
