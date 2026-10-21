class_name TutorialOverlay
extends CanvasLayer
## Tutorial interactivo breve: una mano señala el control importante y
## Tito (el asesor del barrio) explica en un globo. Avanza solo cuando el
## jugador HACE la acción. No bloquea la pantalla y se puede saltear.

const MASCOT := "kiosquero"

var _root: Control
var _hand: TextureRect
var _bubble: PanelContainer
var _text: Label
var _timer := 0.0
var _anim := 0.0
var _target := ""
var _final_timer := 0.0


func _init() -> void:
	layer = 30


func _ready() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.theme = Main.instance.theme
	add_child(_root)
	_hand = U.icon("", "ui/pointer_0.png")
	_root.add_child(_hand)
	_bubble = PanelContainer.new()
	_bubble.theme_type_variation = "WhiteCard"
	_bubble.mouse_filter = Control.MOUSE_FILTER_PASS
	var row := U.hbox(6)
	row.add_child(U.avatar(MASCOT))
	var col := U.vbox(2)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var name_row := U.hbox(4)
	var who := U.label("Tito, tu asesor", U.SIZE_SMALL, U.TEXT, true)
	who.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_row.add_child(who)
	var skip := U.button("Saltar", "crema", "", 18, 9)
	U.on_press(skip, _skip)
	name_row.add_child(skip)
	col.add_child(name_row)
	_text = U.para("", U.SIZE_SMALL, U.TEXT)
	col.add_child(_text)
	row.add_child(col)
	_bubble.add_child(row)
	_root.add_child(_bubble)
	_set_visible(false)


func restart() -> void:
	Game.m.tutorial = {"step": 0, "done": false}


func _skip() -> void:
	Game.m.tutorial["done"] = true
	_set_visible(false)
	Main.instance.toast("Tutorial salteado. Las misiones en OBJETIVOS te guían.", "info")


func _set_visible(v: bool) -> void:
	_hand.visible = v and _target != ""
	_bubble.visible = v


func _process(delta: float) -> void:
	var tut: Dictionary = Game.m.tutorial
	if tut.get("done", false):
		if _bubble.visible:
			_set_visible(false)
		return
	_timer += delta
	_anim += delta
	if _timer >= 0.25:
		_timer = 0.0
		_evaluate(tut)
	if _bubble.visible:
		_place()


## Pasos: cada uno define condición para terminar y cuándo mostrarse.
func _evaluate(tut: Dictionary) -> void:
	var m := Game.m
	var step := int(tut.get("step", 0))
	var show := true
	var text := ""
	_target = ""
	match step:
		0:
			if m.counter("sales_total") >= 1:
				_advance(tut)
				return
			text = "¡Bienvenido/a al barrio! Este puestito es el comienzo de tu imperio. Tocá ¡VENDER! (o mantenelo apretado) para atender clientes."
			_target = "sell"
		1:
			if int(m.biz["puesto"]["level"]) >= 2:
				_advance(tut)
				return
			text = "¡Primera venta! Con esa plata subí de nivel el puesto: cada nivel atiende a más clientes por venta."
			_target = "level"
		2:
			if m.counter("restock_count") >= 1:
				_advance(tut)
				return
			show = m.stock_ratio("puesto") < 0.45
			text = "Cada venta gasta mercadería. Cuando baje, tocá REPONER: el pedido tarda unos segundos en llegar."
			_target = "restock"
		3:
			if m.counter("hires_total") >= 1:
				_advance(tut)
				return
			show = int(m.biz["puesto"]["level"]) >= 6 or m.economy.money >= 150
			text = "¿Cansado de tocar? En ADMINISTRAR contratá un vendedor: el puesto vende solo, incluso con el juego cerrado (hasta 8 h)."
			_target = "manage"
			if Main.instance.modal_host.has_open():
				_target = ""
		4:
			_final_timer += 0.25
			if _final_timer > 9.0:
				_advance(tut)
				return
			text = "¡Ahora vende solo! Contratá un repositor para no quedarte sin mercadería. En OBJETIVOS tenés misiones con premios."
			_target = "nav_3"
		_:
			tut["done"] = true
			_set_visible(false)
			return
	if Main.instance.section != 0 and step < 4:
		show = false
	_text.text = text
	_set_visible(show)


func _advance(tut: Dictionary) -> void:
	tut["step"] = int(tut.get("step", 0)) + 1
	_final_timer = 0.0
	Sfx.play("coin")


func _place() -> void:
	var vp := _root.get_viewport_rect().size
	var w := minf(vp.x - 16.0, 330.0)
	_bubble.custom_minimum_size.x = w
	_bubble.size = Vector2(w, 0)
	var target: Control = Main.instance.targets.get(_target)
	var bubble_y := vp.y * 0.5
	if target and is_instance_valid(target) and target.is_visible_in_tree():
		var r := target.get_global_rect()
		var bob := 2.0 if fmod(_anim, 0.6) < 0.3 else 0.0
		_hand.texture = U.tex("ui/pointer_%d.png" % (0 if bob == 0.0 else 1))
		_hand.position = Vector2(r.position.x + r.size.x * 0.5 - 6, r.end.y - 4 + bob).round()
		if _hand.position.y + 16 > vp.y - 4:
			_hand.position.y = r.position.y - 16
		_hand.visible = true
		# El globo va donde no tape el objetivo.
		bubble_y = r.position.y - _bubble.get_combined_minimum_size().y - 8
		if bubble_y < 60:
			bubble_y = r.end.y + 20
	else:
		_hand.visible = false
	var h := _bubble.get_combined_minimum_size().y
	_bubble.position = Vector2((vp.x - w) / 2.0, clampf(bubble_y, 56.0, vp.y - h - 56.0)).round()
