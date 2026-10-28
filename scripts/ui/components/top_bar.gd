class_name TopBar
extends PanelContainer
## Barra superior: la plata es lo más grande de la pantalla; debajo, la
## ganancia por segundo en verde. Avatar (→ Perfil) y ajustes a los costados.
##
## El saldo es un contador de tragamonedas (SlotCounter): las monedas de cada
## venta vuelan hasta acá, el número da un saltito al recibirlas y los
## premios grandes (misiones, anuncios, ganancias offline...) hacen girar
## todos los rodillos con lluvia de monedas. Todo es sólo visual.
##
## Muestra el saldo NETO (efectivo − sueldos atrasados): si se deben sueldos
## queda en rojo y con un "-" adelante del total.

## Un ingreso que no es una venta común cuenta como "premio grande" si suma
## al menos esta fracción del saldo anterior (y un mínimo absoluto).
const JACKPOT_RATIO := 0.2
const JACKPOT_MIN := 100
## Cada cuánto se actualizan los rodillos con las ventas automáticas.
const ROLL_EVERY := 0.3
const NEGATIVE := Color("ff5a4f")

var _money: SlotCounter
var _coin: TextureRect
var _income_label: Label
var _company: Label
var _avatar: TextureRect
var _timer := 0.0
var _roll_t := 0.0
var _combo := 0
var _last_land := 0
var _jackpot_until := 0


func _ready() -> void:
	theme_type_variation = "DarkCard"
	custom_minimum_size.y = 56
	var row := U.hbox(6)
	add_child(row)
	var av_btn := Button.new()
	av_btn.flat = true
	av_btn.focus_mode = Control.FOCUS_NONE
	av_btn.custom_minimum_size = Vector2(36, 36)
	_avatar = U.avatar(Game.m.profile["avatar"])
	_avatar.position = Vector2(2, 2)
	_avatar.size = Vector2(32, 32)
	av_btn.add_child(_avatar)
	U.on_press(av_btn, func() -> void: Main.instance.go_to(4))
	row.add_child(av_btn)

	var center := U.vbox(0)
	center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_company = U.label("", U.SIZE_SMALL, Color("f0dcc0"))
	_company.clip_text = true
	_company.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	center.add_child(_company)
	var mrow := U.hbox(4)
	_coin = U.icon("moneda")
	mrow.add_child(_coin)
	_money = SlotCounter.new()
	_money.font_size = U.SIZE_BIG
	_money.reel_stopped.connect(_on_reel_stopped)
	# Caja dorada de ancho fijo (§8): el contador animado nunca se encima.
	var box := PanelContainer.new()
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color("6d432b")
	sb.border_color = Color("f2d173")
	sb.set_border_width_all(3)
	sb.border_width_top = 4
	sb.set_corner_radius_all(4)
	sb.set_content_margin_all(2)
	sb.content_margin_left = 6
	sb.content_margin_right = 6
	box.add_theme_stylebox_override("panel", sb)
	box.custom_minimum_size.x = 132
	box.add_child(_money)
	mrow.add_child(box)
	_income_label = U.label("", U.SIZE_SMALL, Color("9cf0b0"), true)
	_income_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_income_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_income_label.clip_text = true
	mrow.add_child(_income_label)
	center.add_child(mrow)
	row.add_child(center)

	var gear := U.icon_button("engranaje", "crema", 36)
	U.on_press(gear, func() -> void: SettingsModal.open())
	row.add_child(gear)

	var m := Game.m
	m.profile_changed.connect(_refresh_names)
	m.money_changed.connect(_on_money_changed)
	Game.model_reset.connect(_on_reset)
	Game.model_loaded.connect(_on_reset)
	_show_balance(false)
	_refresh_names()
	_refresh_income()


func _on_reset() -> void:
	_show_balance(false)
	_refresh_names()


func _refresh_names() -> void:
	var m := Game.m
	_company.text = "%s · Etapa %d" % [m.profile["company"], m.stage]
	ProfileWidgets.apply_avatar(_avatar)


func _refresh_income() -> void:
	var m := Game.m
	var inc := m.income_per_sec()
	# Modo bien argentino: en rojo, cuenta regresiva hasta el juicio laboral.
	var eta := HardMode.lawsuit_eta(m)
	if eta >= 0.0:
		var secs := int(ceilf(eta))
		_income_label.text = "JUICIO EN %d:%02d" % [secs / 60, secs % 60]
		var blink := secs <= 30 and int(Time.get_ticks_msec() / 500) % 2 == 0
		_income_label.add_theme_color_override("font_color", Color("ffd458") if blink else Color("e2665a"))
		_refresh_names()
		return
	if inc > 0.0:
		_income_label.text = "+%s%s" % [Fmt.per_sec(inc), "  x2" if m.boost_multiplier() > 1.0 else ""]
		_income_label.add_theme_color_override("font_color", Color("9cf0b0"))
	else:
		_income_label.text = "vendé a mano"
		_income_label.add_theme_color_override("font_color", Color("f0dcc0"))
	_refresh_names()


## Saldo neto en los rodillos: blanco si es positivo; rojo y con "-" si se
## deben más sueldos de lo que hay en caja.
func _show_balance(animate: bool, big := false) -> void:
	var net := Game.m.net_balance()
	_money.set_color(NEGATIVE if net < 0 else Color.WHITE)
	_money.set_text(Fmt.money(net), animate, big)


func is_negative() -> bool:
	return _money.color == NEGATIVE


## Centro del saldo en pantalla: ahí van a parar las monedas que vuelan.
func money_anchor() -> Vector2:
	return _coin.get_global_rect().get_center()


func _animations_on() -> bool:
	return not Settings.get_value("reduce_motion")


func _process(delta: float) -> void:
	_roll_t += delta
	var now := Time.get_ticks_msec()
	if _roll_t >= ROLL_EVERY and now >= _jackpot_until:
		_roll_t = 0.0
		_show_balance(_animations_on())
	_timer += delta
	if _timer > 0.5:
		_timer = 0.0
		_refresh_income()


func _on_money_changed(money: int, delta: int) -> void:
	if delta <= 0:
		return
	var ledger: Array = Game.m.economy.ledger
	var cat: String = ledger[-1]["cat"] if not ledger.is_empty() else ""
	var before := money - delta
	if cat != "ventas" and delta >= JACKPOT_MIN and float(delta) >= float(before) * JACKPOT_RATIO:
		jackpot(delta)


## Una moneda de una venta llegó al saldo: saltito y "clinc" que sube de tono
## si llegan varias seguidas (como las fichas que caen en la bandeja).
func coin_landed() -> void:
	var now := Time.get_ticks_msec()
	_combo = mini(_combo + 1, 8) if now - _last_land < 600 else 0
	_last_land = now
	Sfx.play("coin", 1.0 + _combo * 0.06, 0.04)
	_bump(1.12, 0.18)


## Premio grande: todos los rodillos giran varias vueltas, lluvia de monedas
## sobre el saldo y caja registradora.
func jackpot(_amount: int) -> void:
	var anim := _animations_on()
	_jackpot_until = Time.get_ticks_msec() + int(SlotCounter.SPIN_TIME * 1000) + 300
	_show_balance(anim, anim)
	Sfx.play("register")
	Sfx.vibrate(40)
	if not anim or Main.instance == null:
		return
	_bump(1.3, 0.35)
	Main.instance.fx.coin_shower(_money.get_global_rect().get_center(), 14)
	Main.instance.fx.sparkle_burst(_money.get_global_rect().get_center(), 8)


func _on_reel_stopped(_i: int) -> void:
	if Time.get_ticks_msec() < _jackpot_until:
		Sfx.play("tap", 1.2 + randf() * 0.3, 0.03)


func _bump(peak: float, time: float) -> void:
	if not _animations_on():
		return
	for n in [_money, _coin]:
		var c: Control = n
		c.pivot_offset = c.size / 2.0
		var tw := c.create_tween()
		tw.tween_property(c, "scale", Vector2(peak, peak), time * 0.35).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tw.tween_property(c, "scale", Vector2.ONE, time * 0.65).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN_OUT)
