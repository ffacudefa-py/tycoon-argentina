class_name ChestModal
extends RefCounted
## Abrir cofres (Engagement.open_chest) con una ruleta: una tira de premios
## posibles pasa por una ventana, frena de a poco y se para sobre el premio
## que tocó (marcado por la flecha dorada del centro).
##
## El premio se decide y se aplica al tocar ABRIR (si se cierra la app a mitad
## de la vuelta no se pierde); la ruleta es sólo la forma de mostrarlo. Mientras
## gira, el saldo de arriba queda congelado para no adelantar el resultado.
## Las tarjetas de relleno salen de la misma tabla de premios con un azar
## propio, así que nunca muestran algo que el cofre no pueda dar.

const CARD_W := 84
const CARD_H := 84
const CARD_GAP := 6
const CARDS := 36
const WIN_AT := 30          ## posición de la tarjeta ganadora en la tira
const SPIN_TIME := 3.4
const RARE_CHANCE := 0.2    ## un premio con menos probabilidad que esto es "raro"

const TIER_COMMON := Color("c8963e")
const TIER_RARE := Color("b04ad8")
const TIER_BOOST := Color("3fa7d6")


static func open() -> void:
	var m := Game.m
	var rng := RandomNumberGenerator.new()
	var body := U.vbox(8)

	# Ventana de la ruleta: marco dorado, flecha arriba y abajo, bordes en sombra.
	var frame := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("2e1b10")
	sb.border_color = U.GOLD
	sb.set_border_width_all(3)
	sb.set_corner_radius_all(4)
	frame.add_theme_stylebox_override("panel", sb)
	var window := Control.new()
	window.clip_contents = true
	window.custom_minimum_size = Vector2(0, CARD_H + 16)
	window.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.add_child(window)
	var strip := Control.new()
	strip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	strip.position.y = 8
	window.add_child(strip)
	window.add_child(_edge_shade(true))
	window.add_child(_edge_shade(false))
	var arrows := [_arrow(true), _arrow(false)]
	for a in arrows:
		window.add_child(a)
	window.resized.connect(func() -> void:
		var cx := window.size.x / 2.0
		arrows[0].position = Vector2(cx - 8, 0)
		arrows[1].position = Vector2(cx - 8, window.size.y - 8))
	body.add_child(frame)

	var prize := U.label("Tocá ABRIR", U.SIZE_TITLE, U.TEXT, true, HORIZONTAL_ALIGNMENT_CENTER)
	body.add_child(prize)
	var left := U.label("", U.SIZE_SMALL, U.TEXT_SOFT, false, HORIZONTAL_ALIGNMENT_CENTER)
	body.add_child(left)
	body.add_child(U.para("Se ganan con conquistas de provincias y regiones, logros, niveles 25/50/100 y desafíos de eventos.", U.SIZE_SMALL, U.TEXT_SOFT))
	var b := U.button("ABRIR", "amarillo", "regalo", 44)
	var spinning := [false]
	var refresh := func() -> void:
		var n := int(m.engage.get("chests", 0))
		left.text = "Te quedan %d cofre%s" % [n, "" if n == 1 else "s"]
		b.disabled = n <= 0 or spinning[0]
	refresh.call()

	# Antes de abrir, la tira ya muestra premios posibles, quieta.
	_fill(strip, m, rng, {})
	window.resized.connect(func() -> void:
		if not spinning[0] and strip.get_child_count() > 0:
			strip.position.x = _offset_for(window, 3, 0.0), CONNECT_ONE_SHOT)

	# Si se cierra la ventana a mitad de la vuelta, el saldo no queda congelado.
	body.tree_exiting.connect(func() -> void:
		if spinning[0] and Main.instance:
			Main.instance.top_bar.hold_balance(false))

	U.on_press(b, func() -> void:
		var top := Main.instance.top_bar
		top.hold_balance(true)
		var r := Engagement.open_chest(m)
		if not r["ok"]:
			top.hold_balance(false)
			Main.instance.result(r)
			return
		spinning[0] = true
		refresh.call()
		prize.text = "..."
		var cards := _fill(strip, m, rng, r)
		var finish := func() -> void:
			spinning[0] = false
			top.hold_balance(false)
			_reveal(cards[WIN_AT], prize, r)
			refresh.call()
		if Settings.get_value("reduce_motion"):
			strip.position.x = _offset_for(window, WIN_AT, 0.0)
			finish.call()
			return
		# Arranca con la tarjeta 2 al centro y frena sobre la ganadora, no
		# siempre en su centro exacto (como una ruleta de verdad); al final se
		# acomoda al medio.
		var from := _offset_for(window, 2, 0.0)
		var to := _offset_for(window, WIN_AT, rng.randf_range(-0.38, 0.38))
		var last := [_card_under(window, from)]
		var tw := strip.create_tween()
		tw.tween_method(func(k: float) -> void:
			strip.position.x = lerpf(from, to, 1.0 - pow(1.0 - k, 4))
			var idx := _card_under(window, strip.position.x)
			if idx != last[0]:
				last[0] = idx
				Sfx.play("tap", 1.0 + 0.4 * k, 0.02), 0.0, 1.0, SPIN_TIME)
		tw.tween_interval(0.15)
		tw.tween_property(strip, "position:x", _offset_for(window, WIN_AT, 0.0), 0.25) \
			.set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tw.tween_callback(finish), "")
	body.add_child(b)
	Main.instance.modal_host.open("Cofres", body)


## Arma la tira de tarjetas. Con un resultado (won no vacío) la tarjeta WIN_AT
## es el premio que tocó y la siguiente un premio raro, para el "casi".
static func _fill(strip: Control, m: GameModel, rng: RandomNumberGenerator, won: Dictionary) -> Array:
	for c in strip.get_children():
		c.queue_free()
	var options := Engagement.chest_options(m)
	var total := 0.0
	for o in options:
		total += float(o["weight"])
	var cards := []
	for i in CARDS:
		var p: Dictionary
		var chance: float
		if not won.is_empty() and i == WIN_AT:
			p = won
			chance = float(won["chance"])
		else:
			var o: Dictionary = options[0]
			if not won.is_empty() and i == WIN_AT + 1:
				o = _rarest(options)
			else:
				var roll := rng.randf() * total
				for e in options:
					roll -= float(e["weight"])
					if roll <= 0.0:
						o = e
						break
			chance = float(o["weight"]) / total
			p = Engagement.roll_prize(m, o, rng)
		var card := _card(p, chance)
		card.position = Vector2(i * (CARD_W + CARD_GAP), 0)
		strip.add_child(card)
		cards.append(card)
	return cards


static func _rarest(options: Array) -> Dictionary:
	var best: Dictionary = options[0]
	for o in options:
		if float(o["weight"]) < float(best["weight"]):
			best = o
	return best


static func _card(p: Dictionary, chance: float) -> PanelContainer:
	var tier := TIER_COMMON
	if p["kind"] == "boost":
		tier = TIER_BOOST
	if chance < RARE_CHANCE:
		tier = TIER_RARE
	var card := PanelContainer.new()
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.size = Vector2(CARD_W, CARD_H)
	card.custom_minimum_size = card.size
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("fff1d6")
	sb.border_color = tier
	sb.set_border_width_all(3)
	sb.border_width_bottom = 6
	sb.set_corner_radius_all(4)
	sb.set_content_margin_all(3)
	card.add_theme_stylebox_override("panel", sb)
	var v := U.vbox(2)
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	var icon: TextureRect
	match p["kind"]:
		"money":
			icon = U.icon32("moneda")
		"boost":
			icon = U.icon32("rayo")
		_:
			icon = U.avatar(p["avatar"])
			icon.custom_minimum_size = Vector2(32, 32)
			icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	icon.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(icon)
	var text: String = p["text"]
	match p["kind"]:
		"boost":
			text = "Turbo x%s\n%s" % [str(p["mult"]).trim_suffix(".0"), Fmt.duration(float(p["secs"]))]
		"avatar":
			text = "Avatar"
	var l := U.label(text, U.SIZE_SMALL, U.TEXT, true, HORIZONTAL_ALIGNMENT_CENTER)
	l.clip_text = true
	l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	l.custom_minimum_size.x = CARD_W - 8
	v.add_child(l)
	card.add_child(v)
	return card


## Posición x de la tira que deja la tarjeta idx centrada bajo la flecha
## (bias corre el punto de frenado dentro de la tarjeta, en fracción del ancho).
static func _offset_for(window: Control, idx: int, bias: float) -> float:
	return window.size.x / 2.0 - (idx * (CARD_W + CARD_GAP) + CARD_W / 2.0 + bias * CARD_W)


static func _card_under(window: Control, strip_x: float) -> int:
	return int(floorf((window.size.x / 2.0 - strip_x) / (CARD_W + CARD_GAP)))


static func _reveal(card: Control, prize: Label, r: Dictionary) -> void:
	prize.text = r["text"]
	prize.pivot_offset = prize.size / 2.0
	prize.scale = Vector2(0.4, 0.4)
	var tw := prize.create_tween()
	tw.tween_property(prize, "scale", Vector2.ONE, 0.25).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	if is_instance_valid(card):
		card.pivot_offset = card.size / 2.0
		var tc := card.create_tween()
		tc.tween_property(card, "scale", Vector2(1.12, 1.12), 0.12)
		tc.tween_property(card, "scale", Vector2.ONE, 0.2).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		var c := card.get_global_rect().get_center()
		Main.instance.fx.coin_shower(c, 12)
		Main.instance.fx.sparkle_burst(c, 8)
	Sfx.play("unlock")
	Sfx.vibrate(30)


## Sombra en los bordes de la ventana: las tarjetas aparecen y se van en penumbra.
static func _edge_shade(left_side: bool) -> TextureRect:
	var g := Gradient.new()
	g.colors = PackedColorArray([Color(0.1, 0.05, 0.02, 0.85), Color(0.1, 0.05, 0.02, 0.0)])
	var t := GradientTexture2D.new()
	t.gradient = g
	t.width = 32
	t.height = 4
	if not left_side:
		t.fill_from = Vector2(1, 0)
		t.fill_to = Vector2(0, 0)
	var r := TextureRect.new()
	r.texture = t
	r.stretch_mode = TextureRect.STRETCH_SCALE
	r.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	r.anchor_bottom = 1.0
	r.offset_right = 36
	if not left_side:
		r.anchor_left = 1.0
		r.anchor_right = 1.0
		r.offset_left = -36
		r.offset_right = 0
	return r


## Triangulito dorado que marca el premio (arriba apunta hacia abajo).
static func _arrow(top: bool) -> Polygon2D:
	var p := Polygon2D.new()
	p.color = U.GOLD
	p.polygon = PackedVector2Array([Vector2(0, 0), Vector2(16, 0), Vector2(8, 8)]) if top \
		else PackedVector2Array([Vector2(0, 8), Vector2(16, 8), Vector2(8, 0)])
	return p
