class_name TutorialOverlay
extends CanvasLayer
## Tutorial guiado con foco iluminado. En los primeros pasos oscurece todo y
## sólo deja tocar el botón del paso (4 paneles alrededor del objetivo
## bloquean el resto); después sólo señala. Avanza cuando el jugador HACE
## la acción y siempre se puede saltear.

const MASCOT := "kiosquero"

var _root: Control
var _shade: Array[ColorRect] = []
var _ring: ReferenceRect
var _hand: TextureRect
var _bubble: PanelContainer
var _title: Label
var _text: Label
var _timer := 0.0
var _anim := 0.0


func _init() -> void:
	layer = 30


func _ready() -> void:
	_root = Control.new()
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.theme = Main.instance.theme
	add_child(_root)
	for i in 4:
		var r := ColorRect.new()
		r.color = Color(0.06, 0.05, 0.12, 0.72)
		r.mouse_filter = Control.MOUSE_FILTER_STOP
		r.visible = false
		_root.add_child(r)
		_shade.append(r)
	_ring = ReferenceRect.new()
	_ring.border_color = Color("ffd458")
	_ring.border_width = 2
	_ring.editor_only = false
	_ring.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_ring)
	_hand = U.icon("", "ui/pointer_0.png")
	_root.add_child(_hand)
	_bubble = PanelContainer.new()
	_bubble.theme_type_variation = "WhiteCard"
	_bubble.mouse_filter = Control.MOUSE_FILTER_STOP
	var row := U.hbox(8)
	row.add_child(U.avatar(MASCOT))
	var col := U.vbox(4)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var name_row := U.hbox(4)
	_title = U.label("", U.SIZE_SMALL, U.TEXT_SOFT, true)
	_title.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_row.add_child(_title)
	var skip := U.button("Saltar", "crema", "", 32, U.SIZE_SMALL)
	U.on_press(skip, _skip)
	name_row.add_child(skip)
	col.add_child(name_row)
	_text = U.para("", U.SIZE_BODY, U.TEXT)
	col.add_child(_text)
	row.add_child(col)
	_bubble.add_child(row)
	_root.add_child(_bubble)
	_hide()


func restart() -> void:
	Game.m.tutorial = {"step": 0, "done": false}


func _skip() -> void:
	Game.m.tutorial["done"] = true
	_hide()
	Main.instance.toast("Tutorial salteado. La franja de OBJETIVO te va guiando.", "info")


func _hide() -> void:
	for r in _shade:
		r.visible = false
	_ring.visible = false
	_hand.visible = false
	_bubble.visible = false


func _process(delta: float) -> void:
	var m := Game.m
	_anim += delta
	_timer += delta
	if _timer >= 0.2:
		_timer = 0.0
		if TutorialSteps.update(m):
			Sfx.play("mission")
			Main.instance.fx.sparkle_burst(Vector2(_root.size.x / 2, 90), 6)
	if not TutorialSteps.active(m):
		if _bubble.visible:
			_hide()
		return
	var step := int(m.tutorial["step"])
	var st: Dictionary = TutorialSteps.current(m)
	var modal_open := Main.instance.modal_host.has_open()
	# Los pasos se muestran en IMPERIO sin ventanas abiertas, salvo el de
	# contratar (acompaña dentro de Administrar) y el del kiosco (Negocios).
	var show := Main.instance.section == 0 and not modal_open
	if step == 4 and modal_open:
		show = true
	if step == 5:
		show = Main.instance.section in [0, 1] and not modal_open
	if not show:
		_hide()
		return
	_title.text = "Tito · paso %d de %d" % [step + 1, TutorialSteps.STEPS.size()]
	_text.text = st["text"] if not (step == 4 and modal_open) else "Elegí la pestaña EMPLEADOS y tocá CONTRATAR en un vendedor."
	var target: Control = null
	if not modal_open:
		target = Main.instance.targets.get(st["target"])
	if target and not (is_instance_valid(target) and target.is_visible_in_tree()):
		target = null
	_place(target, bool(st["block"]) and target != null)


func _place(target: Control, block: bool) -> void:
	var vp := _root.get_viewport_rect().size
	var w := minf(vp.x - 16.0, 340.0)
	_bubble.visible = true
	_bubble.custom_minimum_size.x = w
	_bubble.size = Vector2(w, 0)
	var bh := _bubble.get_combined_minimum_size().y
	var bubble_y := vp.y * 0.35
	if target:
		var r := target.get_global_rect().grow(4)
		if block:
			_shade[0].position = Vector2.ZERO
			_shade[0].size = Vector2(vp.x, r.position.y)
			_shade[1].position = Vector2(0, r.end.y)
			_shade[1].size = Vector2(vp.x, vp.y - r.end.y)
			_shade[2].position = Vector2(0, r.position.y)
			_shade[2].size = Vector2(r.position.x, r.size.y)
			_shade[3].position = Vector2(r.end.x, r.position.y)
			_shade[3].size = Vector2(vp.x - r.end.x, r.size.y)
		for s in _shade:
			s.visible = block
		var pulse := 1.0 if fmod(_anim, 0.8) < 0.4 else 0.0
		_ring.visible = true
		_ring.position = (r.position - Vector2(pulse, pulse)).round()
		_ring.size = (r.size + Vector2(pulse, pulse) * 2).round()
		_hand.visible = true
		_hand.texture = U.tex("ui/pointer_%d.png" % int(pulse))
		_hand.position = Vector2(r.position.x + r.size.x * 0.5 - 6, r.end.y - 6 + pulse * 2).round()
		if _hand.position.y + 16 > vp.y - 4:
			_hand.position.y = r.position.y - 18
		if block:
			bubble_y = r.position.y - bh - 12
			if bubble_y < 50:
				bubble_y = r.end.y + 22
		else:
			# Sin bloqueo el jugador sigue usando la pantalla: el globo va
			# arriba, sobre la escena decorativa, para no tapar botones.
			bubble_y = 112
	else:
		for s in _shade:
			s.visible = false
		_ring.visible = false
		_hand.visible = false
	_bubble.position = Vector2((vp.x - w) / 2.0, clampf(bubble_y, 50.0, vp.y - bh - 70.0)).round()
