class_name ModalHost
extends CanvasLayer
## Ventanas emergentes apilables, siempre centradas y dentro del área
## visible: el alto máximo se ajusta a la pantalla y el contenido scrollea.

var _stack: Array[ModalWindow] = []


func _init() -> void:
	layer = 10


func open(title: String, body: Control, dismissable := true, width := 340) -> ModalWindow:
	var w := ModalWindow.new()
	w.setup(title, body, dismissable, width)
	add_child(w)
	_stack.append(w)
	w.closed.connect(func() -> void: _stack.erase(w))
	Sfx.play("whoosh", 1.3)
	return w


func close_top() -> bool:
	if _stack.is_empty():
		return false
	var w: ModalWindow = _stack[-1]
	if w.dismissable:
		w.close()
	return true


func close_all() -> void:
	for w in _stack.duplicate():
		w.close()


func has_open() -> bool:
	return not _stack.is_empty()


class ModalWindow extends Control:
	signal closed

	var dismissable := true
	var body: Control
	var _panel: PanelContainer
	var _scroll: ScrollContainer
	var _title: Label
	var _width := 340
	var _closing := false

	func setup(title: String, p_body: Control, p_dismissable: bool, width: int) -> void:
		dismissable = p_dismissable
		body = p_body
		_width = width
		set_anchors_preset(Control.PRESET_FULL_RECT)
		mouse_filter = Control.MOUSE_FILTER_STOP
		# Los CanvasLayer cortan la herencia del tema: se asigna explícitamente.
		theme = Main.instance.theme
		var dim := ColorRect.new()
		dim.color = Color(0.05, 0.04, 0.1, 0.62)
		dim.set_anchors_preset(Control.PRESET_FULL_RECT)
		dim.gui_input.connect(func(ev: InputEvent) -> void:
			if dismissable and ev is InputEventMouseButton and ev.pressed:
				close())
		add_child(dim)
		var center := CenterContainer.new()
		center.set_anchors_preset(Control.PRESET_FULL_RECT)
		center.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(center)
		_panel = PanelContainer.new()
		_panel.theme_type_variation = "Card"
		center.add_child(_panel)
		var col := U.vbox(4)
		_panel.add_child(col)
		var head := U.hbox(4)
		_title = U.label(title, U.SIZE_TITLE, U.TEXT, true)
		_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_title.clip_text = true
		head.add_child(_title)
		if dismissable:
			var x := U.icon_button("cerrar", "crema", 24)
			U.on_press(x, close)
			head.add_child(x)
		col.add_child(head)
		col.add_child(U.separator())
		_scroll = DragScroll.new()
		_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
		body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_scroll.add_child(body)
		col.add_child(_scroll)
		body.minimum_size_changed.connect(_fit)
		resized.connect(_fit)

	func _ready() -> void:
		_fit()
		_panel.pivot_offset = _panel.size / 2
		_panel.scale = Vector2(0.92, 0.92)
		modulate.a = 0.0
		var tw := create_tween().set_parallel(true)
		tw.tween_property(_panel, "scale", Vector2.ONE, 0.12).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tw.tween_property(self, "modulate:a", 1.0, 0.1)

	func set_title(t: String) -> void:
		_title.text = t

	func _fit() -> void:
		if not is_inside_tree():
			return
		var vp := get_viewport_rect().size
		var w := mini(_width, int(vp.x) - 12)
		var safe_top := 0
		var safe_bottom := 0
		if Main.instance and Main.instance._safe:
			safe_top = Main.instance._safe.get_theme_constant("margin_top")
			safe_bottom = Main.instance._safe.get_theme_constant("margin_bottom")
		var max_h := int(vp.y) - 24 - safe_top - safe_bottom - 44
		_panel.custom_minimum_size.x = w
		_scroll.custom_minimum_size.x = w - 14
		_scroll.size.x = w - 14
		body.custom_minimum_size.x = w - 24
		var want := body.get_combined_minimum_size().y
		_scroll.custom_minimum_size.y = clampf(want, 20.0, float(max_h))
		_panel.pivot_offset = _panel.size / 2

	func close() -> void:
		if _closing:
			return
		_closing = true
		closed.emit()
		var tw := create_tween()
		tw.tween_property(self, "modulate:a", 0.0, 0.08)
		tw.tween_callback(queue_free)
