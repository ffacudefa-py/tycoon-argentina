class_name U
extends RefCounted
## Fábrica de widgets pixel art y utilidades de interfaz.
## Mantiene un único estilo en todo el juego (lección de PassIdle: un kit de
## UI compartido en vez de estilos sueltos por pantalla).

const PA := "res://assets/pixel_art/"
const TEXT := Color("2b2746")
const TEXT_SOFT := Color("5d5b7a")
const TEXT_LIGHT := Color("f2f0e6")
const GOLD := Color("ffd85c")
const GREEN := Color("2f7d4a")
const RED := Color("a8323a")
const BG := Color("1b1830")

const SIZE_SMALL := 12
const SIZE_BODY := 14
const SIZE_TITLE := 18
const SIZE_BIG := 24

static var _tex_cache := {}
static var font_regular: Font
static var font_bold: Font


static func tex(path: String) -> Texture2D:
	if not _tex_cache.has(path):
		var full := path if path.begins_with("res://") else PA + path
		_tex_cache[path] = load(full) if ResourceLoader.exists(full) else null
	return _tex_cache[path]


static func icon_tex(name: String) -> Texture2D:
	var t := tex("icons/%s.png" % name)
	return t if t else tex("icons/estrella.png")


## Ícono 2.0 de 32x32 (navegación, fichas, botones grandes). Si no existe
## la versión grande, usa la de 16x16.
static func icon32_tex(name: String) -> Texture2D:
	var t := tex("icons32/%s.png" % name)
	return t if t else icon_tex(name)


static func icon32(name: String) -> TextureRect:
	var r := icon("")
	r.texture = icon32_tex(name)
	r.custom_minimum_size = r.texture.get_size()
	return r


static func label(text: String, size := SIZE_BODY, color := TEXT, bold := false, align := HORIZONTAL_ALIGNMENT_LEFT) -> Label:
	var l := Label.new()
	l.text = text
	# Nunca por debajo del mínimo legible (12 px virtuales ≈ 14 sp a ×3).
	l.add_theme_font_size_override("font_size", maxi(size, SIZE_SMALL))
	l.add_theme_color_override("font_color", color)
	if bold and font_bold:
		l.add_theme_font_override("font", font_bold)
	l.horizontal_alignment = align
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	return l


## Texto largo que hace salto de línea (descripciones).
static func para(text: String, size := SIZE_SMALL, color := TEXT_SOFT) -> Label:
	var l := label(text, size, color)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.custom_minimum_size.x = 40
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return l


static func icon(name: String, path := "") -> TextureRect:
	var r := TextureRect.new()
	r.texture = tex(path) if path != "" else icon_tex(name)
	r.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
	r.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if r.texture:
		r.custom_minimum_size = r.texture.get_size()
	return r


## Botón con estilo de color. style: verde, amarillo, rojo, celeste, crema, gris, violeta.
static func button(text: String, style := "crema", icon_name := "", min_h := 26, size := SIZE_BODY) -> Button:
	var b := Button.new()
	b.text = text
	b.theme_type_variation = "Btn_" + style
	b.custom_minimum_size.y = maxi(min_h, 32)   # objetivo táctil cómodo
	b.add_theme_font_size_override("font_size", maxi(size, SIZE_SMALL))
	if icon_name != "":
		b.icon = icon_tex(icon_name)
		b.expand_icon = false
	b.focus_mode = Control.FOCUS_NONE
	b.mouse_filter = Control.MOUSE_FILTER_STOP
	b.action_mode = BaseButton.ACTION_MODE_BUTTON_RELEASE
	press_feedback(b)
	return b


## Feedback al tocar: el botón se achica un instante (además del "hundido"
## del estilo) y vibra apenas. Sólo visual: no cambia el área táctil.
static func press_feedback(b: BaseButton) -> void:
	b.button_down.connect(func() -> void:
		if Settings.get_value("reduce_motion"):
			Sfx.vibrate(10)
			return
		b.pivot_offset = b.size / 2.0
		var tw := b.create_tween()
		tw.tween_property(b, "scale", Vector2(0.95, 0.95), 0.05)
		Sfx.vibrate(10))
	b.button_up.connect(func() -> void:
		var tw := b.create_tween()
		tw.tween_property(b, "scale", Vector2.ONE, 0.08))


## Conecta una acción protegida contra dobles toques accidentales.
static func on_press(b: BaseButton, fn: Callable, sound := "tap") -> void:
	b.pressed.connect(func() -> void:
		var now := Time.get_ticks_msec()
		if now - int(b.get_meta("last_press", 0)) < 120:
			return
		b.set_meta("last_press", now)
		if sound != "":
			Sfx.play(sound)
		fn.call())


static func icon_button(icon_name: String, style := "crema", min_size := 28) -> Button:
	var b := button("", style, icon_name, min_size)
	b.custom_minimum_size = Vector2(min_size, min_size)
	b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return b


static func panel(style := "Card", pad := 6) -> PanelContainer:
	var p := PanelContainer.new()
	p.theme_type_variation = style
	return p


static func vbox(sep := 4) -> VBoxContainer:
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", sep)
	return v


static func hbox(sep := 4) -> HBoxContainer:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", sep)
	return h


static func margin(node: Control, l: int, t: int, r: int, b: int) -> MarginContainer:
	var m := MarginContainer.new()
	m.add_theme_constant_override("margin_left", l)
	m.add_theme_constant_override("margin_top", t)
	m.add_theme_constant_override("margin_right", r)
	m.add_theme_constant_override("margin_bottom", b)
	m.add_child(node)
	return m


static func spacer(expand := true) -> Control:
	var c := Control.new()
	if expand:
		c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


static func progress(color := "verde", h := 8) -> ProgressBar:
	var p := ProgressBar.new()
	p.show_percentage = false
	p.min_value = 0.0
	p.max_value = 1.0
	p.step = 0.0
	p.custom_minimum_size.y = h
	p.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	p.theme_type_variation = "Bar_" + color
	p.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return p


static func scroll(child: Control) -> ScrollContainer:
	var s := ScrollContainer.new()
	# SHOW_NEVER (no DISABLED): el ancho mínimo del contenido no empuja la pantalla.
	s.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_SHOW_NEVER
	s.vertical_scroll_mode = ScrollContainer.SCROLL_MODE_AUTO
	s.size_flags_vertical = Control.SIZE_EXPAND_FILL
	s.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.follow_focus = false
	child.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	s.add_child(child)
	return s


## Fila "etiqueta ...... valor".
static func stat_row(key: String, value: String, value_color := TEXT) -> HBoxContainer:
	var h := hbox(4)
	var k := label(key, SIZE_SMALL, TEXT_SOFT)
	k.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	k.clip_text = true
	h.add_child(k)
	var v := label(value, SIZE_SMALL, value_color, true, HORIZONTAL_ALIGNMENT_RIGHT)
	k.custom_minimum_size.x = 40
	v.name = "Value"
	h.add_child(v)
	return h


static func separator() -> ColorRect:
	var c := ColorRect.new()
	c.color = Color("e0c79a")
	c.custom_minimum_size.y = 1
	c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return c


static func clear(node: Node) -> void:
	for c in node.get_children():
		node.remove_child(c)
		c.queue_free()


## Segmento de pestañas propio (botones). Devuelve el HBox; on_change(index).
static func tabs(names: Array, on_change: Callable, selected := 0) -> HBoxContainer:
	var h := hbox(2)
	var group := ButtonGroup.new()
	for i in names.size():
		var b := button(names[i], "crema", "", 24, SIZE_SMALL)
		b.toggle_mode = true
		b.button_group = group
		b.button_pressed = i == selected
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		b.theme_type_variation = "Tab"
		var idx: int = i
		b.toggled.connect(func(on: bool) -> void:
			if on:
				Sfx.play("tap")
				on_change.call(idx))
		h.add_child(b)
	return h


static func rich(text: String, size := SIZE_SMALL) -> RichTextLabel:
	var r := RichTextLabel.new()
	r.bbcode_enabled = true
	r.fit_content = true
	r.scroll_active = false
	r.text = text
	r.add_theme_font_size_override("normal_font_size", size)
	r.add_theme_font_size_override("bold_font_size", size)
	r.add_theme_color_override("default_color", TEXT)
	r.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if font_bold:
		r.add_theme_font_override("bold_font", font_bold)
	return r


static func avatar(aid: String) -> TextureRect:
	return icon("", "avatars/%s.png" % aid)


static func badge_for(business_id: String) -> TextureRect:
	return icon("", "businesses/%s_badge.png" % business_id)
