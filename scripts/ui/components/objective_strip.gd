class_name ObjectiveStrip
extends PanelContainer
## Franja fija "OBJETIVO" bajo la barra superior: siempre responde
## "¿qué hago ahora?". Muestra el paso del tutorial guiado, o la misión
## principal en curso, o los premios pendientes de reclamar.
## Tocarla lleva a OBJETIVOS.

var _title: Label
var _bar: ProgressBar
var _progress: Label
var _reward: Label
var _icon: TextureRect
var _timer := 0.0


func _ready() -> void:
	theme_type_variation = "GoldCard"
	custom_minimum_size.y = 44
	mouse_filter = Control.MOUSE_FILTER_STOP
	var row := U.hbox(6)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(row)
	_icon = U.icon32("bandera")
	row.add_child(_icon)
	var col := U.vbox(2)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_title = U.label("", U.SIZE_BODY, U.TEXT, true)
	_title.clip_text = true
	col.add_child(_title)
	var prow := U.hbox(6)
	prow.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_bar = U.progress("verde", 8)
	_bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	prow.add_child(_bar)
	_progress = U.label("", U.SIZE_SMALL, U.TEXT, true)
	prow.add_child(_progress)
	_reward = U.label("", U.SIZE_SMALL, U.GREEN, true)
	prow.add_child(_reward)
	col.add_child(prow)
	row.add_child(col)
	gui_input.connect(func(ev: InputEvent) -> void:
		if ev is InputEventMouseButton and ev.pressed and ev.button_index == MOUSE_BUTTON_LEFT:
			if not TutorialSteps.active(Game.m):
				Sfx.play("tap")
				Main.instance.go_to(3))
	_refresh()


func _process(delta: float) -> void:
	_timer += delta
	if _timer >= 0.3:
		_timer = 0.0
		_refresh()


func _refresh() -> void:
	var m := Game.m
	if TutorialSteps.active(m):
		var step := int(m.tutorial["step"])
		var st := TutorialSteps.current(m)
		_title.text = "OBJETIVO: " + st["goal"]
		_bar.value = float(step) / TutorialSteps.STEPS.size()
		_progress.text = "Paso %d/%d" % [step + 1, TutorialSteps.STEPS.size()]
		_reward.text = ("Premio: " + ProgressionSystem.describe(m, st["reward"])) if not st["reward"].is_empty() else ""
		_icon.texture = U.icon32_tex("bandera")
		return
	var pending := ProgressionSystem.unclaimed_count(m)
	if pending > 0:
		_title.text = "¡Tenés %d premio%s para reclamar!" % [pending, "" if pending == 1 else "s"]
		_bar.value = 1.0
		_progress.text = "Tocá acá"
		_reward.text = ""
		_icon.texture = U.icon32_tex("regalo")
		return
	var idx := int(m.missions["main_index"])
	if idx >= m.data.missions_main.size():
		_title.text = "OBJETIVO: ¡expandí tu imperio!"
		_bar.value = 1.0
		_progress.text = ""
		_reward.text = ""
		return
	var mis: Dictionary = m.data.missions_main[idx]
	var v := m.metric(mis["metric"])
	var target := float(mis["target"])
	_title.text = "OBJETIVO: " + mis["title"]
	_bar.value = clampf(v / target, 0.0, 1.0)
	var money: bool = mis["metric"] in ["money", "net_worth"]
	_progress.text = ("%s/%s" % [Fmt.money(minf(v, target)), Fmt.money(target)]) if money else ("%s/%s" % [Fmt.num(floorf(minf(v, target))), Fmt.num(target)])
	_reward.text = "Premio: " + ProgressionSystem.describe(m, mis["reward"])
	_icon.texture = U.icon32_tex("bandera")
