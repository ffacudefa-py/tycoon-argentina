class_name FriendsModal
extends RefCounted
## Amigos: tu código, agregar por código, solicitudes, mates recibidos y el
## ranking por plata ganada en la historia. Necesita cuenta con el email
## verificado (si no, lleva a iniciar sesión o a verificar).


static func open() -> void:
	if not Auth.signed_in():
		LoginModal.open()
		Main.instance.toast("Creá una cuenta o iniciá sesión para tener amigos.", "info")
		return
	if not Auth.email_verified:
		VerifyEmailModal.open()
		return
	var body := U.vbox(6)
	var content := U.vbox(6)
	body.add_child(content)
	var w_ref := []
	var rebuild := func() -> void:
		if is_instance_valid(content):
			_build(content)
	Friends.changed.connect(rebuild)
	body.tree_exiting.connect(func() -> void: Friends.changed.disconnect(rebuild))
	_build(content)
	w_ref.append(Main.instance.modal_host.open("Amigos", body))
	Friends.refresh()


static func _build(col: VBoxContainer) -> void:
	U.clear(col)
	# --- Mi código
	var code_card := U.panel("Card")
	var cc := U.vbox(4)
	code_card.add_child(cc)
	cc.add_child(U.label("Tu código de amigo", U.SIZE_BODY, U.TEXT, true))
	var row := U.hbox(6)
	var code := U.label(Friends.my_code if Friends.my_code != "" else "······", U.SIZE_TITLE, U.GREEN, true)
	code.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(code)
	var copy := U.button("Copiar", "crema", "", 28, U.SIZE_SMALL)
	copy.disabled = Friends.my_code == ""
	U.on_press(copy, func() -> void:
		DisplayServer.clipboard_set(Friends.my_code)
		Main.instance.toast("Código copiado: pasáselo a tus amigos.", "good"))
	row.add_child(copy)
	cc.add_child(row)
	cc.add_child(U.para("Pasale este código a quien quieras sumar; o escribí el suyo acá abajo.", U.SIZE_SMALL, U.TEXT_SOFT))
	var add_row := U.hbox(4)
	var input := LineEdit.new()
	input.placeholder_text = "Código (6 letras)"
	input.max_length = 8
	input.custom_minimum_size.y = 34
	input.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	add_row.add_child(input)
	var add := U.button("Agregar", "verde", "mas", 34, U.SIZE_SMALL)
	var submit := func() -> void:
		add.disabled = true
		var r: Dictionary = await Friends.add_by_code(input.text)
		if is_instance_valid(add):
			add.disabled = false
			if r["ok"]:
				input.text = ""
		Main.instance.result(r, "unlock")
	U.on_press(add, submit, "")
	input.text_submitted.connect(func(_t: String) -> void: submit.call())
	add_row.add_child(add)
	cc.add_child(add_row)
	col.add_child(code_card)

	if Friends.status == "error":
		col.add_child(U.para(Friends.last_error, U.SIZE_SMALL, U.RED))
	elif Friends.status == "loading" and Friends.friends.is_empty():
		col.add_child(U.para("Cargando amigos…", U.SIZE_SMALL, U.TEXT_SOFT))

	# --- Solicitudes
	if not Friends.requests.is_empty():
		var card := _card(col, "Solicitudes (%d)" % Friends.requests.size(), "persona")
		for rq in Friends.requests:
			var r := _person_row(rq["avatar"], rq["company"], "Quiere ser tu amigo")
			var fid: String = rq["uid"]
			var ok := U.button("Aceptar", "verde", "", 26, U.SIZE_SMALL)
			U.on_press(ok, func() -> void: Main.instance.result(await Friends.accept(fid), "unlock"), "")
			r.add_child(ok)
			var no := U.icon_button("cerrar", "rojo", 26)
			U.on_press(no, func() -> void: Main.instance.result(await Friends.reject(fid)))
			r.add_child(no)
			card.add_child(r)

	# --- Mates recibidos
	if not Friends.gifts.is_empty():
		var left := FriendLogic.gifts_left_today(Game.m)
		var card := _card(col, "Mates recibidos (%d)" % Friends.gifts.size(), "yerba")
		card.add_child(U.para("Cada mate te da %s. Podés abrir %d más hoy." % [ProgressionSystem.describe(Game.m, Game.data.friends_cfg["gift_reward"]), left], U.SIZE_SMALL, U.TEXT_SOFT))
		for g in Friends.gifts:
			var r := _person_row("mate", g["company"], "Te convidó un mate")
			var fid: String = g["uid"]
			var open_b := U.button("Abrir", "amarillo", "regalo", 26, U.SIZE_SMALL)
			open_b.disabled = left <= 0
			U.on_press(open_b, func() -> void: Main.instance.result(await Friends.claim_gift(fid), "register"), "")
			r.add_child(open_b)
			card.add_child(r)

	# --- Ranking
	var rank_card := _card(col, "Ranking de amigos", "trofeo")
	if Friends.friends.is_empty():
		rank_card.add_child(U.para("Todavía no tenés amigos agregados. Cuando acepten tu solicitud, compiten acá por quién ganó más plata en la historia.", U.SIZE_SMALL, U.TEXT_SOFT))
	var pos := 0
	for p in FriendLogic.ranking(Friends.me(), Friends.friends):
		pos += 1
		var mine: bool = p["uid"] == Auth.uid
		var r := _person_row(p["avatar"], "%d. %s%s" % [pos, p["company"], " (vos)" if mine else ""],
			"Etapa %d · %s ganados" % [int(p["stage"]), Fmt.money(int(p["lifetime"]))], mine)
		if not mine:
			var fid: String = p["uid"]
			var gift := U.icon_button("yerba", "verde", 28)
			gift.disabled = Friends.sent_today(fid)
			gift.tooltip_text = "Convidar un mate"
			U.on_press(gift, func() -> void: Main.instance.result(await Friends.send_gift(fid), "coin"), "")
			r.add_child(gift)
			var del := U.icon_button("cerrar", "crema", 28)
			var name: String = p["company"]
			U.on_press(del, func() -> void:
				Main.instance.confirm("¿Sacar a %s?" % name, "Deja de estar en tu ranking y vos en el suyo. Se pueden volver a agregar con el código.", "Sacar",
					func() -> void: Main.instance.result(await Friends.remove(fid))))
			r.add_child(del)
		rank_card.add_child(r)
	rank_card.add_child(U.para("Mate: convidale uno por día a cada amigo; al abrirlo gana un premio chico.", U.SIZE_SMALL, U.TEXT_SOFT))


static func _card(col: VBoxContainer, title: String, icon_name: String) -> VBoxContainer:
	var card := U.panel("Card")
	var c := U.vbox(4)
	card.add_child(c)
	var head := U.hbox(4)
	head.add_child(U.icon(icon_name))
	head.add_child(U.label(title, U.SIZE_BODY, U.TEXT, true))
	c.add_child(head)
	col.add_child(card)
	return c


static func _person_row(avatar_id: String, title: String, sub: String, highlight := false) -> HBoxContainer:
	var r := U.hbox(6)
	var av: TextureRect
	if avatar_id == "mate":
		av = U.icon32("mate")
	else:
		av = U.avatar(avatar_id if Game.data.avatar_by_id.has(avatar_id) else "emprendedor")
	av.custom_minimum_size = Vector2(28, 28)
	r.add_child(av)
	var txt := U.vbox(0)
	txt.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var t := U.label(title, U.SIZE_SMALL, U.GREEN if highlight else U.TEXT, true)
	t.clip_text = true
	t.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	t.custom_minimum_size.x = 1
	txt.add_child(t)
	var s := U.label(sub, U.SIZE_SMALL, U.TEXT_SOFT)
	s.clip_text = true
	s.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	s.custom_minimum_size.x = 1
	txt.add_child(s)
	r.add_child(txt)
	return r
