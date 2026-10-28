class_name AdsModal
extends RefCounted
## "Bonos por anuncio": ofertas voluntarias con anuncio recompensado.
## Cada tarjeta dice qué se gana, cuánto y por cuánto tiempo; el botón
## muestra el estado real (cargando, sin conexión, en espera, límite diario).
## Nada de esto es necesario para progresar.


static func open(business := "") -> void:
	var body := U.vbox(6)
	var holder := U.vbox(6)
	body.add_child(holder)
	var params := {"business": business if business != "" else _current_business()}
	var rebuild := func() -> void: _fill(holder, params)
	rebuild.call()
	# Se refresca solo mientras está abierto (estado del anuncio y esperas).
	var t := Timer.new()
	t.wait_time = 1.0
	t.autostart = true
	t.timeout.connect(rebuild)
	body.add_child(t)
	Monetization.ads_changed.connect(rebuild)
	body.tree_exiting.connect(func() -> void:
		if Monetization.ads_changed.is_connected(rebuild):
			Monetization.ads_changed.disconnect(rebuild))
	Main.instance.modal_host.open("Bonos por anuncio", body)


static func _current_business() -> String:
	return Main.instance.selected_business if Main.instance else Game.m.first_business()


static func _fill(holder: Control, params: Dictionary) -> void:
	U.clear(holder)
	var m := Game.m
	var cfg := Monetization.cfg
	var state := Monetization.ad_state()
	var s := AdRewards.state(m)
	holder.add_child(U.para("Opcional: mirá un anuncio corto y llevate un bono. Tu progreso nunca depende de esto.", U.SIZE_SMALL, U.TEXT_SOFT))
	if cfg.environment == "test" and state != "off":
		holder.add_child(U.para("Modo prueba: se muestran anuncios de prueba de Google.", U.SIZE_SMALL, Color("b5700a")))
	holder.add_child(U.stat_row("Anuncios vistos hoy", "%d / %d" % [int(s["today"]), cfg.daily_limit()]))
	if state != "ready":
		var info := U.panel("Card")
		var row := U.hbox(6)
		row.add_child(U.icon("info" if state == "loading" else "alerta"))
		row.add_child(U.para(Monetization.unavailable_reason(), U.SIZE_SMALL, U.TEXT))
		row.get_child(1).size_flags_horizontal = Control.SIZE_EXPAND_FILL
		info.add_child(row)
		holder.add_child(info)
	for offer in cfg.offers():
		holder.add_child(_card(m, cfg, offer, params, state))


static func _card(m: GameModel, cfg: AdConfig, offer: Dictionary, params: Dictionary, state: String) -> Control:
	var card := U.panel("Card")
	var col := U.vbox(4)
	card.add_child(col)
	var head := U.hbox(6)
	head.add_child(U.icon32(offer["icon"]))
	var d := AdRewards.describe(m, offer, params)
	var title := U.label(d["title"], U.SIZE_BODY, U.TEXT, true)
	title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(title)
	col.add_child(head)
	col.add_child(U.para(d["description"], U.SIZE_SMALL, U.TEXT_SOFT))
	var st := AdRewards.offer_status(m, cfg, offer, params)
	var text := "VER ANUNCIO"
	var style := "amarillo"
	var enabled := true
	if Monetization.busy:
		text = "MOSTRANDO ANUNCIO…"
		enabled = false
	elif not st["available"]:
		text = st["reason"]
		enabled = false
	elif state == "loading":
		text = "CARGANDO ANUNCIO…"
		enabled = false
	elif state != "ready":
		text = "NO DISPONIBLE"
		enabled = false
	var b := U.button(text, style if enabled else "crema", "regalo" if enabled else "", 36, U.SIZE_SMALL)
	b.disabled = not enabled
	b.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	var oid: String = offer["id"]
	U.on_press(b, func() -> void:
		if Monetization.busy:
			return
		b.disabled = true                 # evita el doble toque
		Monetization.watch(oid, params, func(r: Dictionary) -> void:
			if r["granted"]:
				Main.instance.toast(r["msg"], "good")
				Sfx.play("register")
			elif r["msg"] != "":
				Main.instance.toast(r["msg"], "bad")))
	col.add_child(b)
	return card
