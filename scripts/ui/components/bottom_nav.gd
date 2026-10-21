class_name BottomNav
extends PanelContainer
## Navegación inferior: 5 secciones con ícono, nombre y aviso de pendientes.

signal selected(index: int)

const ICONS := ["corona", "tienda", "mapa", "bandera", "persona"]

var _buttons: Array[Button] = []
var _badges: Array[Label] = []
var _timer := 0.0


func _ready() -> void:
	theme_type_variation = "DarkCard"
	custom_minimum_size.y = 50
	var row := U.hbox(2)
	add_child(row)
	for i in Main.SECTIONS.size():
		var b := Button.new()
		b.toggle_mode = true
		b.focus_mode = Control.FOCUS_NONE
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.custom_minimum_size = Vector2(56, 40)
		b.theme_type_variation = "Tab"
		var v := U.vbox(0)
		v.set_anchors_preset(Control.PRESET_FULL_RECT)
		v.alignment = BoxContainer.ALIGNMENT_CENTER
		v.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var ic := U.icon(ICONS[i])
		ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		v.add_child(ic)
		var l := U.label(Main.SECTIONS[i].to_upper(), 9, U.TEXT, true, HORIZONTAL_ALIGNMENT_CENTER)
		l.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(l)
		b.add_child(v)
		var badge := U.label("", 9, Color.WHITE, true, HORIZONTAL_ALIGNMENT_CENTER)
		badge.custom_minimum_size = Vector2(12, 10)
		var sb := StyleBoxFlat.new()
		sb.bg_color = Color("d94a4a")
		sb.border_color = Color("1b1830")
		sb.set_border_width_all(1)
		badge.add_theme_stylebox_override("normal", sb)
		badge.position = Vector2(40, 0)
		badge.visible = false
		b.add_child(badge)
		var idx := i
		U.on_press(b, func() -> void: selected.emit(idx))
		row.add_child(b)
		_buttons.append(b)
		_badges.append(badge)
		Main.instance.register_target("nav_%d" % i, b)
	_update_badges()


func set_selected(index: int) -> void:
	for i in _buttons.size():
		_buttons[i].set_pressed_no_signal(i == index)


func _process(delta: float) -> void:
	_timer += delta
	if _timer >= 1.0:
		_timer = 0.0
		_update_badges()


func _update_badges() -> void:
	var m := Game.m
	var pending := ProgressionSystem.unclaimed_count(m)
	_set_badge(3, pending)
	var buyable := 0
	for def in m.data.businesses:
		if not m.biz[def["id"]]["owned"]:
			var st := m.unlock_status(def["id"])
			if st["available"] and st["affordable"]:
				buyable += 1
			break
	_set_badge(1, buyable)


func _set_badge(i: int, n: int) -> void:
	_badges[i].visible = n > 0
	_badges[i].text = str(n) if n < 10 else "9+"
