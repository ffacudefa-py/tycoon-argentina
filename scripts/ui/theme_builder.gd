class_name ThemeBuilder
extends RefCounted
## Construye el tema pixel art del juego a partir de los PNG generados
## (tools/art/ui_art.py). Todos los marcos son 9-slice para que escalen
## sin deformar los píxeles.

const BUTTON_STYLES := ["verde", "amarillo", "rojo", "celeste", "crema", "gris", "violeta"]


static func build() -> Theme:
	var th := Theme.new()
	# VT323 (OFL): letra de terminal pixelada, alta y muy legible. No trae
	# negrita: se engrosa el trazo con embolden.
	var font: FontFile = load("res://assets/fonts/VT323-Regular.ttf")
	font.antialiasing = TextServer.FONT_ANTIALIASING_NONE
	font.hinting = TextServer.HINTING_NONE
	font.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
	font.generate_mipmaps = false
	var regular := FontVariation.new()
	regular.base_font = font
	var bold := FontVariation.new()
	bold.base_font = font
	bold.variation_embolden = 0.35
	U.font_regular = regular
	U.font_bold = bold
	th.default_font = regular
	th.default_font_size = U.SIZE_BODY

	th.set_color("font_color", "Label", U.TEXT)

	# Botones
	for st in BUTTON_STYLES:
		var tv: String = "Btn_" + st
		th.set_type_variation(tv, "Button")
		th.set_stylebox("normal", tv, _btn_box(st, "normal"))
		th.set_stylebox("hover", tv, _btn_box(st, "normal"))
		th.set_stylebox("pressed", tv, _btn_box(st, "pressed"))
		th.set_stylebox("hover_pressed", tv, _btn_box(st, "pressed"))
		th.set_stylebox("disabled", tv, _btn_box(st, "disabled"))
		th.set_stylebox("focus", tv, StyleBoxEmpty.new())
		var fc := U.TEXT if st in ["crema", "amarillo"] else U.TEXT_LIGHT
		if st == "celeste":
			fc = U.TEXT
		th.set_color("font_color", tv, fc)
		th.set_color("font_hover_color", tv, fc)
		th.set_color("font_pressed_color", tv, fc)
		th.set_color("font_hover_pressed_color", tv, fc)
		th.set_color("font_disabled_color", tv, Color("c2c0d6"))
		th.set_color("icon_disabled_color", tv, Color(1, 1, 1, 0.5))
		th.set_font("font", tv, bold)
		th.set_constant("h_separation", tv, 3)
	th.set_stylebox("normal", "Button", _btn_box("crema", "normal"))
	th.set_stylebox("hover", "Button", _btn_box("crema", "normal"))
	th.set_stylebox("pressed", "Button", _btn_box("crema", "pressed"))
	th.set_stylebox("disabled", "Button", _btn_box("crema", "disabled"))
	th.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	th.set_color("font_color", "Button", U.TEXT)

	# Pestañas (botón con estado "seleccionado")
	th.set_type_variation("Tab", "Button")
	th.set_stylebox("normal", "Tab", _btn_box("crema", "normal"))
	th.set_stylebox("hover", "Tab", _btn_box("crema", "normal"))
	th.set_stylebox("pressed", "Tab", _btn_box("amarillo", "pressed"))
	th.set_stylebox("hover_pressed", "Tab", _btn_box("amarillo", "pressed"))
	th.set_stylebox("focus", "Tab", StyleBoxEmpty.new())
	th.set_color("font_color", "Tab", U.TEXT_SOFT)
	th.set_color("font_pressed_color", "Tab", U.TEXT)
	th.set_color("font_hover_pressed_color", "Tab", U.TEXT)
	th.set_font("font", "Tab", bold)

	# Paneles
	for pair in [["Card", "panel.png", 6], ["DarkCard", "panel_dark.png", 6], ["WhiteCard", "panel_white.png", 6],
			["GoldCard", "panel_gold.png", 6], ["SlateCard", "panel_slate.png", 6], ["Inset", "inset.png", 3], ["InsetDark", "inset_dark.png", 3]]:
		th.set_type_variation(pair[0], "PanelContainer")
		th.set_stylebox("panel", pair[0], _box("ui/" + pair[1], pair[2], pair[2] + 1))
	th.set_stylebox("panel", "PanelContainer", _box("ui/panel.png", 6, 7))
	for kind in ["info", "good", "bad", "reward"]:
		var tv: String = "Toast_" + kind
		th.set_type_variation(tv, "PanelContainer")
		th.set_stylebox("panel", tv, _box("ui/toast_%s.png" % kind, 6, 6))

	# Barras de progreso
	for c in ["verde", "amarillo", "celeste", "rojo", "violeta"]:
		var tv: String = "Bar_" + c
		th.set_type_variation(tv, "ProgressBar")
		th.set_stylebox("background", tv, _box("ui/bar_bg.png", 2, 0))
		th.set_stylebox("fill", tv, _box("ui/bar_%s.png" % c, 2, 0))

	# Scroll: barra finita y discreta (en el celular se arrastra con el dedo)
	var grab := StyleBoxFlat.new()
	grab.bg_color = Color(0.36, 0.35, 0.48, 0.7)
	grab.content_margin_left = 2
	grab.content_margin_right = 2
	var empty := StyleBoxEmpty.new()
	th.set_stylebox("scroll", "VScrollBar", empty)
	th.set_stylebox("grabber", "VScrollBar", grab)
	th.set_stylebox("grabber_highlight", "VScrollBar", grab)
	th.set_stylebox("grabber_pressed", "VScrollBar", grab)
	th.set_stylebox("panel", "ScrollContainer", StyleBoxEmpty.new())

	# Campo de texto
	th.set_stylebox("normal", "LineEdit", _box("ui/inset.png", 3, 4))
	th.set_stylebox("focus", "LineEdit", _box("ui/inset.png", 3, 4))
	th.set_color("font_color", "LineEdit", U.TEXT)
	th.set_color("caret_color", "LineEdit", U.TEXT)
	# El gris por defecto del placeholder casi no se ve sobre el beige.
	th.set_color("font_placeholder_color", "LineEdit", Color(U.TEXT_SOFT, 0.85))

	# Interruptores y deslizador
	th.set_icon("checked", "CheckButton", U.tex("ui/toggle_on.png"))
	th.set_icon("unchecked", "CheckButton", U.tex("ui/toggle_off.png"))
	th.set_icon("checked_disabled", "CheckButton", U.tex("ui/toggle_on.png"))
	th.set_icon("unchecked_disabled", "CheckButton", U.tex("ui/toggle_off.png"))
	for s in ["normal", "hover", "pressed", "hover_pressed", "focus", "disabled"]:
		th.set_stylebox(s, "CheckButton", StyleBoxEmpty.new())
	th.set_color("font_color", "CheckButton", U.TEXT)
	th.set_color("font_hover_color", "CheckButton", U.TEXT)
	th.set_color("font_pressed_color", "CheckButton", U.TEXT)
	th.set_color("font_hover_pressed_color", "CheckButton", U.TEXT)
	th.set_stylebox("slider", "HSlider", _box("ui/bar_bg.png", 2, 3))
	th.set_stylebox("grabber_area", "HSlider", _box("ui/bar_verde.png", 2, 3))
	th.set_stylebox("grabber_area_highlight", "HSlider", _box("ui/bar_verde.png", 2, 3))
	th.set_icon("grabber", "HSlider", U.tex("ui/grabber.png"))
	th.set_icon("grabber_highlight", "HSlider", U.tex("ui/grabber.png"))
	return th


static func _box(path: String, margin: int, content: int) -> StyleBoxTexture:
	var sb := StyleBoxTexture.new()
	sb.texture = U.tex(path)
	sb.texture_margin_left = margin
	sb.texture_margin_right = margin
	sb.texture_margin_top = margin
	sb.texture_margin_bottom = margin
	sb.content_margin_left = content
	sb.content_margin_right = content
	sb.content_margin_top = content
	sb.content_margin_bottom = content
	return sb


static func _btn_box(style: String, state: String) -> StyleBoxTexture:
	var sb := StyleBoxTexture.new()
	sb.texture = U.tex("ui/btn_%s_%s.png" % [style, state])
	sb.texture_margin_left = 4
	sb.texture_margin_right = 4
	sb.texture_margin_top = 4
	sb.texture_margin_bottom = 6
	sb.content_margin_left = 6
	sb.content_margin_right = 6
	sb.content_margin_top = 4 if state != "pressed" else 6
	sb.content_margin_bottom = 6 if state != "pressed" else 4
	return sb
