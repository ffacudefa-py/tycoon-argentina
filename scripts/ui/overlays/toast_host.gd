class_name ToastHost
extends CanvasLayer
## Avisos breves arriba de la pantalla. No bloquean toques ni la interfaz.

const MAX_VISIBLE := 2
const ICONS := {"info": "info", "good": "check", "bad": "alerta", "reward": "regalo"}
const COLORS := {"info": Color("f2f0e6"), "good": Color("f2f0e6"), "bad": Color("f2f0e6"), "reward": Color("2b2746")}

var _box: VBoxContainer
var _queue: Array = []
var _last_text := ""
var _last_time := 0


func _init() -> void:
	layer = 40


func _ready() -> void:
	var root := Control.new()
	root.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = Main.instance.theme
	add_child(root)
	_box = U.vbox(3)
	_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_box.set_anchors_preset(Control.PRESET_TOP_WIDE)
	_box.offset_left = 10
	_box.offset_right = -10
	_box.offset_top = 52
	root.add_child(_box)


func show_toast(text: String, kind := "info") -> void:
	# Mismo aviso repetido en ráfaga: se ignora.
	var now := Time.get_ticks_msec()
	if text == _last_text and now - _last_time < 1500:
		return
	_last_text = text
	_last_time = now
	if Main.instance and Main.instance._safe:
		_box.offset_top = 50 + Main.instance._safe.get_theme_constant("margin_top")
	while _box.get_child_count() >= MAX_VISIBLE:
		var old := _box.get_child(0)
		_box.remove_child(old)
		old.queue_free()
	var p := PanelContainer.new()
	p.theme_type_variation = "Toast_" + kind
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var row := U.hbox(4)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(U.icon(ICONS.get(kind, "info")))
	var l := U.para(text, U.SIZE_SMALL, COLORS.get(kind, Color.WHITE))
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(l)
	p.add_child(row)
	_box.add_child(p)
	p.modulate.a = 0.0
	var tw := p.create_tween()
	tw.tween_property(p, "modulate:a", 1.0, 0.12)
	tw.tween_interval(2.6 if kind != "bad" else 3.4)
	tw.tween_property(p, "modulate:a", 0.0, 0.25)
	tw.tween_callback(p.queue_free)
