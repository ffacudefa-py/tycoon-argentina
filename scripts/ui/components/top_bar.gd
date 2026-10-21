class_name TopBar
extends PanelContainer
## Barra superior: empresa y etapa, dinero (animado), ingresos por segundo,
## accesos a estadísticas y configuración.

var _money_label: Label
var _income_label: Label
var _company: Label
var _stage: Label
var _avatar: TextureRect
var _shown_money := 0.0
var _target_money := 0.0
var _timer := 0.0
var _boost: Label


func _ready() -> void:
	theme_type_variation = "DarkCard"
	custom_minimum_size.y = 46
	var row := U.hbox(4)
	add_child(row)
	_avatar = U.avatar(Game.m.profile["avatar"])
	var av_btn := Button.new()
	av_btn.flat = true
	av_btn.focus_mode = Control.FOCUS_NONE
	av_btn.custom_minimum_size = Vector2(26, 26)
	av_btn.add_child(_avatar)
	_avatar.position = Vector2(1, 1)
	U.on_press(av_btn, func() -> void: Main.instance.go_to(4))
	row.add_child(av_btn)
	var names := U.vbox(0)
	names.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	names.custom_minimum_size.x = 60
	_company = U.label("", U.SIZE_SMALL, U.TEXT_LIGHT, true)
	_company.clip_text = true
	_stage = U.label("", 9, Color("c2c0d6"))
	_stage.clip_text = true
	names.add_child(_company)
	names.add_child(_stage)
	row.add_child(names)

	var money_box := U.vbox(0)
	money_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	money_box.custom_minimum_size.x = 120
	var mrow := U.hbox(3)
	mrow.alignment = BoxContainer.ALIGNMENT_CENTER
	mrow.add_child(U.icon("moneda"))
	_money_label = U.label("$0", U.SIZE_BIG, U.GOLD, true)
	mrow.add_child(_money_label)
	money_box.add_child(mrow)
	var irow := U.hbox(3)
	irow.alignment = BoxContainer.ALIGNMENT_CENTER
	_income_label = U.label("", U.SIZE_SMALL, Color("8fd47a"), false, HORIZONTAL_ALIGNMENT_CENTER)
	irow.add_child(_income_label)
	_boost = U.label("", U.SIZE_SMALL, U.GOLD, true)
	irow.add_child(_boost)
	money_box.add_child(irow)
	row.add_child(money_box)

	var stats := U.icon_button("grafico", "crema", 26)
	U.on_press(stats, func() -> void: StatsModal.open())
	row.add_child(stats)
	var gear := U.icon_button("engranaje", "crema", 26)
	U.on_press(gear, func() -> void: SettingsModal.open())
	row.add_child(gear)

	var m := Game.m
	m.money_changed.connect(func(money: int, _d: int) -> void: _target_money = float(money))
	m.profile_changed.connect(_refresh_names)
	m.stage_changed.connect(func(_s: int) -> void: _refresh_names())
	Game.model_reset.connect(_refresh_names)
	_shown_money = float(m.economy.money)
	_target_money = _shown_money
	_refresh_names()
	_refresh_income()


func _refresh_names() -> void:
	var m := Game.m
	_company.text = m.profile["company"]
	_stage.text = "Etapa %d · %s" % [m.stage, m.data.stage_name(m.stage)]
	_avatar.texture = U.tex("avatars/%s.png" % m.profile["avatar"])


func _refresh_income() -> void:
	var m := Game.m
	var inc := m.income_per_sec()
	_income_label.text = ("+" + Fmt.per_sec(inc)) if inc > 0.0 else "Vendé a mano o contratá"
	_boost.text = (" x%s" % str(m.boost_multiplier()).trim_suffix(".0")) if m.boost_multiplier() > 1.0 else ""


## El saldo "corre" hasta el valor real en vez de saltar (sólo visual).
func _process(delta: float) -> void:
	var target := float(Game.m.economy.money)
	_target_money = target
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
