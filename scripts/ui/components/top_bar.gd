class_name TopBar
extends PanelContainer
## Barra superior: la plata es lo más grande de la pantalla; debajo, la
## ganancia por segundo en verde. Avatar (→ Perfil) y ajustes a los costados.

var _money_label: Label
var _income_label: Label
var _company: Label
var _avatar: TextureRect
var _shown_money := 0.0
var _timer := 0.0


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
	_avatar.position = Vector2(4, 4)
	_avatar.size = Vector2(28, 28)
	av_btn.add_child(_avatar)
	U.on_press(av_btn, func() -> void: Main.instance.go_to(4))
	row.add_child(av_btn)

	var center := U.vbox(0)
	center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_company = U.label("", U.SIZE_SMALL, Color("c9c7da"))
	_company.clip_text = true
	center.add_child(_company)
	var mrow := U.hbox(4)
	mrow.add_child(U.icon("moneda"))
	_money_label = U.label("$0", U.SIZE_BIG, Color.WHITE, true)
	mrow.add_child(_money_label)
	_income_label = U.label("", U.SIZE_SMALL, Color("8ccb6c"), true)
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
	Game.model_reset.connect(_refresh_names)
	_shown_money = float(m.economy.money)
	_refresh_names()
	_refresh_income()


func _refresh_names() -> void:
	var m := Game.m
	_company.text = "%s · Etapa %d" % [m.profile["company"], m.stage]
	ProfileWidgets.apply_avatar(_avatar)


func _refresh_income() -> void:
	var m := Game.m
	var inc := m.income_per_sec()
	if inc > 0.0:
		_income_label.text = "+%s%s" % [Fmt.per_sec(inc), "  x2" if m.boost_multiplier() > 1.0 else ""]
		_income_label.add_theme_color_override("font_color", Color("8ccb6c"))
	else:
		_income_label.text = "vendé a mano"
		_income_label.add_theme_color_override("font_color", Color("9b98b5"))
	_refresh_names()


## El saldo "corre" hasta el valor real en vez de saltar (sólo visual).
func _process(delta: float) -> void:
	var target := float(Game.m.economy.money)
	if absf(_shown_money - target) > 0.5:
		_shown_money = lerpf(_shown_money, target, minf(1.0, delta * 10.0))
		if absf(_shown_money - target) < 1.0:
			_shown_money = target
	else:
		_shown_money = target
	_money_label.text = Fmt.money(_shown_money)
	_timer += delta
	if _timer > 0.5:
		_timer = 0.0
		_refresh_income()
